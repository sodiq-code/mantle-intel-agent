"""
Mantle Intel Agent — Main Pipeline Orchestrator
Runs all 5 agents in sequence:
  1. Collector  → ingest Mantle blocks
  2. Anomaly    → detect statistical anomalies
  3. SmartMoney → cluster wallets, identify smart money
  4. Insight    → generate LLM narratives
  5. Audit      → write finding hashes on-chain

Designed to run continuously or as a one-shot analysis.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable
import structlog

from agents.collector.collector_agent import CollectorAgent
from agents.anomaly.anomaly_agent import AnomalyAgent, AnomalyFinding
from agents.smart_money.smart_money_agent import SmartMoneyAgent
from agents.insight.insight_agent import InsightAgent
from agents.audit.audit_agent import AuditAgent
from agents.incident import IncidentManager
from bot.discord_webhook import push_incident as discord_push
from bot.telegram_bot import MantleIntelBot

# P2-16: OpenTelemetry tracing
try:
    from agents.tracing import tracer as _otel_tracer
except ImportError:
    _otel_tracer = None

logger = structlog.get_logger(__name__)

# P2-23 FIX: Removed module-level os.makedirs side effect.
# Directory creation is now lazy — only when first needed.
FINDINGS_PATH = "data/findings.jsonl"
AUDIT_LOG_PATH = "data/audit_log.jsonl"
DASHBOARD_PATH = "data/dashboard.json"


def _ensure_data_dir():
    """P2-23 FIX: Lazy data directory creation — no import-time side effect."""
    os.makedirs("data", exist_ok=True)


class MantleIntelPipeline:
    """
    Orchestrates the full 5-agent pipeline.
    Emits findings to callbacks (Telegram bot, dashboard, etc).
    """

    def __init__(
        self,
        on_incident: Optional[Callable] = None,
        poll_interval: int = 30,
        blocks_per_cycle: int = 50,
    ):
        self.on_incident = on_incident
        self.poll_interval = poll_interval
        self.blocks_per_cycle = blocks_per_cycle
        self._running = False
        self._findings: list[dict] = []
        self._consecutive_failures = 0       # P2-26: Circuit breaker counter
        self._circuit_open = False           # P2-26: Circuit breaker flag
        self._stats = {
            "cycles_run":      0,
            "blocks_processed": 0,
            "findings_total":   0,
            "started_at":       None,
            "last_cycle_success": None,      # P2-17: Timestamp of last successful cycle
        }
        self.incident_manager = IncidentManager()

        # Initialize logger first (needed by subsequent init)
        self.logger = logger.bind(component="pipeline")

        # Initialize agents
        self.collector = CollectorAgent(poll_interval=poll_interval)
        self.anomaly = AnomalyAgent()
        self.smart_money = SmartMoneyAgent()
        self.insight = InsightAgent()
        self.audit = AuditAgent()

        # Initialize Telegram bot for push notifications
        self.telegram_bot = MantleIntelBot()
        self.telegram_bot.set_pipeline(self)
        if self.telegram_bot.is_configured():
            self.logger.info("telegram_bot_configured",
                             chat_id=self.telegram_bot.chat_id)
        else:
            self.logger.warning("telegram_bot_not_configured",
                                msg="Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable Telegram alerts")

        # P0-FIX: Recover state from persistent JSONL on restart
        self._recover_state()

        self.logger.info("pipeline_initialized",
                         demo_mode=self.collector.demo_mode,
                         audit_demo=self.audit.demo_mode,
                         telegram=self.telegram_bot.is_configured(),
                         recovered_findings=len(self._findings))

    # ── State Recovery (P0-FIX) ─────────────────────────────────────────────────

    def _recover_state(self):
        """Reload findings from findings.jsonl on server restart.

        Without this, every server restart wipes in-memory findings, causing
        the dashboard to show empty data until the next anomaly is found.
        This reads the last 100 findings from JSONL to repopulate the
        in-memory list so the dashboard immediately has data.
        """
        if not Path(FINDINGS_PATH).exists():
            return

        try:
            with open(FINDINGS_PATH) as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                return

            # Load last 100 findings
            parsed = []
            for line in lines[-100:]:
                try:
                    parsed.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    pass

            if parsed:
                self._findings = parsed
                self._stats["findings_total"] = len(lines)  # total ever recorded
                self._stats["blocks_processed"] = max(
                    (f.get("block", 0) for f in parsed), default=0
                ) - min(
                    (f.get("block", 0) for f in parsed), default=0
                )
                self.logger.info("state_recovered",
                                 findings_loaded=len(parsed),
                                 total_in_jsonl=len(lines))

                # Also recover dashboard.json
                self._update_dashboard()

        except Exception as e:
            self.logger.warning("state_recovery_failed", error=str(e))

    # ── Single cycle ──────────────────────────────────────────────────────────

    async def run_cycle(self) -> list[dict]:
        """Run one full pipeline cycle. Returns list of new finding dicts."""
        # P2-16: OpenTelemetry span for pipeline cycle
        # Use start_span (not start_as_current_span) to avoid contextvars
        # issues when running inside asyncio.create_task or background threads.
        span = None
        if _otel_tracer:
            span = _otel_tracer.start_span("pipeline.run_cycle")
            span.set_attribute("pipeline.cycle_number",
                               self._stats["cycles_run"] + 1)

        cycle_start = time.time()
        new_findings = []

        self.logger.info("cycle_start", cycle=self._stats["cycles_run"] + 1)

        # Stage 1: Collect
        # P2-18: collect_blocks now uses asyncio.to_thread internally
        # to avoid blocking the event loop with synchronous web3.py HTTP calls
        blocks = await self.collector.collect_blocks(self.blocks_per_cycle)
        protocol_state = await self.collector.poll_protocol_state()

        if not blocks:
            self.logger.warning("no_blocks_collected")
            return []

        latest_block = max(getattr(b, 'block_num', 0) if not isinstance(b, dict) else b.get("number", 0) for b in blocks) if blocks else 0

        self._stats["blocks_processed"] += len(blocks)

        # Check resolutions
        resolved = self.incident_manager.check_resolutions(latest_block)
        for inc in resolved:
            await self._notify_incident(inc)

        # Stage 2: Anomaly detection
        anomalies: list[AnomalyFinding] = self.anomaly.detect(
            blocks, protocol_state=vars(protocol_state))

        if not anomalies:
            self.logger.info("no_anomalies_detected", blocks=len(blocks))
            self._stats["cycles_run"] += 1
            return []

        self.logger.info("anomalies_found", count=len(anomalies))

        # Stage 3: Smart money analysis
        clusters, sm_signals = self.smart_money.analyze(blocks)

        # Stage 4 & 5: Insight + Audit for each anomaly
        # P2-FIX: Raised from 3 → 6 — now that web3 calls use asyncio.to_thread,
        # we can safely write more findings per cycle without blocking the event loop.
        MAX_ONCHAIN_PER_CYCLE = 6
        onchain_count = 0
        # Collect incident notifications to batch at end of cycle
        # (prevents 4 notifications for same-block anomalies → 1 composite)
        _cycle_incident_ids = set()
        for finding in anomalies:
            try:
                # Generate insight
                insight_text = await self.insight.generate_insight(finding)

                # Record on-chain (limit per cycle to prevent event loop blocking)
                if onchain_count < MAX_ONCHAIN_PER_CYCLE:
                    audit_record = await self.audit.record_finding(finding)
                    onchain_count += 1
                else:
                    # Skip on-chain write for remaining findings in this cycle
                    from agents.audit.audit_agent import AuditRecord
                    audit_record = AuditRecord(
                        finding_id=finding.finding_id,
                        finding_hash=finding.sha256_hash(),
                        anomaly_type=finding.anomaly_type,
                        confidence=finding.confidence,
                        block_height=finding.block_height,
                        audit_status="deferred",
                        error=f"On-chain write deferred (max {MAX_ONCHAIN_PER_CYCLE}/cycle)",
                    )

                # Build full finding record
                dashboard_card = self.insight.format_dashboard_card(
                    finding, insight_text)
                dashboard_card["audit"] = {
                    "status":     audit_record.audit_status,
                    "tx_hash":    audit_record.on_chain_tx,
                    "on_chain_id": audit_record.on_chain_id,
                    "explorer":   audit_record.explorer_url(self.audit.network),
                    "demo_mode":  self.audit.demo_mode,
                }
                dashboard_card["smart_money"] = {
                    "clusters": len(clusters),
                    "signals":  [s.to_dict() for s in sm_signals if s.block_height == finding.block_height],
                }

                # Update dashboard state
                new_findings.append(dashboard_card)
                self._findings.append(dashboard_card)
                self._findings = self._findings[-100:]  # keep last 100
                self._append_finding(dashboard_card)

                # Process Incident State — collect incident IDs, don't notify yet
                incident_update = self.incident_manager.process_finding(
                    dashboard_card, latest_block)
                if incident_update:
                    inc_id = incident_update.get("incident_id")
                    _cycle_incident_ids.add(inc_id)

            except Exception as e:
                self.logger.error("finding_processing_failed",
                                  finding_id=finding.finding_id,
                                  error=str(e))
            # Yield to event loop between findings to prevent starvation
            await asyncio.sleep(0)

        # ── Send ONE composite notification per correlated event ──────────────
        # After all findings in this cycle are processed, send the final
        # composite state of each incident as a single notification.
        #
        # COMPOSITE SUPPRESSION: If multiple incidents cover the same block
        # range and one is composite, ONLY send the composite. Individual
        # detector alerts are internal evidence — not user-facing notifications.
        # This prevents the "4 alerts for 1 event" problem.
        _to_notify = self._select_notifications(_cycle_incident_ids)
        for notification in _to_notify:
            await self._notify_incident(notification)

        # Mark all cycle incidents as notified (even suppressed ones)
        for inc_id in _cycle_incident_ids:
            for key, inc in self.incident_manager.active_incidents.items():
                if inc["id"] == inc_id:
                    inc["last_notified_state"] = inc["state"]
                    inc["last_notified_occurrences"] = inc["occurrences"]
                    break

        # Save audit log
        self.audit.save_audit_log(AUDIT_LOG_PATH)

        # Update dashboard
        self._update_dashboard()

        self._stats["cycles_run"] += 1
        self._stats["findings_total"] += len(new_findings)
        self._stats["last_cycle_success"] = datetime.now(tz=timezone.utc).isoformat()  # P2-17

        # P2-26: Reset circuit breaker on successful cycle
        if self._consecutive_failures > 0:
            self.logger.info("circuit_breaker_reset",
                             previous_failures=self._consecutive_failures)
        self._consecutive_failures = 0
        self._circuit_open = False

        elapsed = time.time() - cycle_start
        self.logger.info("cycle_complete",
                         cycle=self._stats["cycles_run"],
                         new_findings=len(new_findings),
                         elapsed_s=round(elapsed, 2))

        # P2-16: End OpenTelemetry span
        if span:
            span.set_attribute("pipeline.new_findings", len(new_findings))
            span.set_attribute("pipeline.elapsed_s", round(elapsed, 2))
            span.end()

        return new_findings

    def _select_notifications(self, cycle_incident_ids: set) -> list[dict]:
        """Select which incidents to notify, applying composite suppression.

        Rules:
        1. Group incidents by block proximity (same event = same group).
        2. If a group has a composite incident, ONLY send the composite.
        3. If a group has only individual incidents, merge them into a
           synthetic composite and send that.
        4. Isolated incidents (no proximate neighbors) are sent as-is.

        This prevents the "4 alerts for 1 event" problem where a composite
        alert AND its constituent detector alerts are all sent.
        """
        # Collect incident objects for this cycle
        cycle_incidents = []
        for inc_id in cycle_incident_ids:
            for key, inc in self.incident_manager.active_incidents.items():
                if inc["id"] == inc_id:
                    cycle_incidents.append(inc)
                    break

        if not cycle_incidents:
            return []

        # Group incidents by block proximity
        groups = self._group_by_proximity(cycle_incidents)

        notifications = []
        for group in groups:
            if len(group) == 1:
                # Single incident — send as-is
                inc = group[0]
                notifications.append(
                    self.incident_manager._format_incident_notification(inc))
            else:
                # Multiple incidents in same block range — apply suppression
                composite_inc = None
                individual_incs = []
                for inc in group:
                    if len(inc.get("anomaly_types", set())) > 1:
                        composite_inc = inc
                    else:
                        individual_incs.append(inc)

                if composite_inc:
                    # Send ONLY the composite — suppress individuals
                    # But absorb their evidence into the composite first
                    for ind in individual_incs:
                        for atype in ind.get("anomaly_types", set()):
                            composite_inc["anomaly_types"].add(atype)
                        for r in ind.get("reasons", set()):
                            composite_inc["reasons"].add(r)
                        for f in ind.get("findings", []):
                            composite_inc["findings"].append(f)
                        composite_inc["occurrences"] += ind["occurrences"]
                    # Re-derive type as composite
                    composite_inc["type"] = "composite"
                    # Rebuild insight to include all signal types
                    composite_inc["insight_sample"] = \
                        self.incident_manager._build_composite_insight(
                            composite_inc, "", "")
                    notifications.append(
                        self.incident_manager._format_incident_notification(
                            composite_inc))
                else:
                    # No composite exists — merge individuals into one
                    # synthetic composite notification
                    merged = self._merge_into_composite(group)
                    notifications.append(
                        self.incident_manager._format_incident_notification(
                            merged))

        return notifications

    def _group_by_proximity(self, incidents: list[dict]) -> list[list[dict]]:
        """Group incidents whose block ranges overlap or are within proximity."""
        if not incidents:
            return []

        groups = []
        used = set()

        for i, inc_a in enumerate(incidents):
            if i in used:
                continue
            group = [inc_a]
            used.add(i)
            for j, inc_b in enumerate(incidents):
                if j in used:
                    continue
                # Check if inc_b is within proximity of any member of the group
                for member in group:
                    if abs(inc_b["latest_block"] - member["latest_block"]) \
                            <= self.incident_manager.BLOCK_PROXIMITY_THRESHOLD:
                        group.append(inc_b)
                        used.add(j)
                        break
            groups.append(group)

        return groups

    def _merge_into_composite(self, incidents: list[dict]) -> dict:
        """Merge multiple individual incidents into a single composite dict."""
        all_types = set()
        all_reasons = set()
        all_findings = []
        total_occurrences = 0
        peak_conf = 0
        peak_zs = None
        start_block = float('inf')
        latest_block = 0

        for inc in incidents:
            all_types.update(inc.get("anomaly_types", set()))
            all_reasons.update(inc.get("reasons", set()))
            all_findings.extend(inc.get("findings", []))
            total_occurrences += inc["occurrences"]
            if inc["peak_confidence"] > peak_conf:
                peak_conf = inc["peak_confidence"]
            zs = inc.get("peak_zscore")
            if zs and (not peak_zs or zs > peak_zs):
                peak_zs = zs
            if inc["start_block"] < start_block:
                start_block = inc["start_block"]
            if inc["latest_block"] > latest_block:
                latest_block = inc["latest_block"]

        merged = {
            "id": sorted(inc["id"] for inc in incidents)[0],  # earliest ID
            "type": "composite",
            "anomaly_types": all_types,
            "start_block": start_block,
            "latest_block": latest_block,
            "occurrences": total_occurrences,
            "peak_confidence": peak_conf,
            "peak_zscore": peak_zs,
            "state": incidents[0]["state"],
            "findings": all_findings,
            "insight_sample": self.incident_manager._build_composite_insight(
                {"anomaly_types": all_types, "insight_sample": ""},
                "", ""),
            "reasons": all_reasons,
            "start_time": min(
                (inc["start_time"] for inc in incidents), default="N/A"),
            "latest_time": max(
                (inc["latest_time"] for inc in incidents), default="N/A"),
        }
        return merged

    async def _notify_incident(self, incident: dict):
        """Push an incident update to the configured bots (Discord + Telegram)."""
        if self.on_incident:
            try:
                await self.on_incident(incident)
            except Exception as cb_e:
                self.logger.warning("callback_failed", error=str(cb_e))

        # Discord webhook notification
        try:
            discord_push(incident)
        except Exception as dc_e:
            self.logger.warning("discord_webhook_failed", error=str(dc_e))

        # Telegram push notification
        try:
            await self.telegram_bot.push_incident(incident)
        except Exception as tg_e:
            self.logger.warning("telegram_push_failed", error=str(tg_e))

    # ── Continuous loop ───────────────────────────────────────────────────────

    async def run_continuous(self):
        """Run pipeline continuously with poll_interval delay between cycles.

        P2-26: Implements circuit breaker pattern to prevent runaway failures.
        After 5 consecutive failures, the circuit opens and applies
        exponential backoff before retrying.
        """
        self._running = True
        self._stats["started_at"] = datetime.now(tz=timezone.utc).isoformat()
        self.logger.info("pipeline_started", interval=self.poll_interval)

        while self._running:
            try:
                await self.run_cycle()
            except Exception as e:
                # P2-26: Circuit breaker — count consecutive failures
                self._consecutive_failures += 1
                self.logger.error("cycle_error",
                                  error=str(e),
                                  consecutive_failures=self._consecutive_failures)

                if self._consecutive_failures >= 5:
                    self._circuit_open = True
                    backoff_seconds = 5 * self.poll_interval  # 5x normal interval
                    self.logger.critical(
                        "circuit_breaker_open",
                        consecutive_failures=self._consecutive_failures,
                        backoff_seconds=backoff_seconds,
                        msg=f"Pipeline has failed {self._consecutive_failures} times "
                            f"consecutively. Pausing for {backoff_seconds}s "
                            f"before retry.")
                    # Notify incident channels about circuit breaker
                    try:
                        await self._notify_incident({
                            "type": "circuit_breaker",
                            "consecutive_failures": self._consecutive_failures,
                            "backoff_seconds": backoff_seconds,
                            "message": f"Pipeline circuit breaker opened after "
                                       f"{self._consecutive_failures} failures. "
                                       f"Backing off for {backoff_seconds}s.",
                        })
                    except Exception as notify_err:
                        self.logger.warning("circuit_breaker_notify_failed",
                                            error=str(notify_err))
                    await asyncio.sleep(backoff_seconds)
                    continue

            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
        self.logger.info("pipeline_stopped")

    # ── Persistence ───────────────────────────────────────────────────────────

    def _append_finding(self, finding: dict):
        """Append finding to JSONL store with rotation (P2-27)."""
        _ensure_data_dir()  # P2-23: lazy dir creation
        self._rotate_if_needed(FINDINGS_PATH)
        with open(FINDINGS_PATH, "a") as f:
            f.write(json.dumps(finding, default=str) + "\n")

    def _update_dashboard(self):
        """Write latest state to dashboard.json for the web UI.

        Also syncs to dashboard/public/dashboard.json for Vercel static deployment,
        so the hosted dashboard always shows the latest data even when the
        FastAPI server is unreachable.
        """
        _ensure_data_dir()  # P2-23: lazy dir creation
        dashboard_data = {
            "last_updated":    datetime.now(tz=timezone.utc).isoformat(),
            "stats":           self._stats,
            "latest_findings": self._findings[-20:],
            "smart_money_summary": self.smart_money.summary(),
            "demo_mode":       self.collector.demo_mode,
            "audit_demo":      self.audit.demo_mode,
            "contract_address": self.audit.contract_address or "not_deployed",
            "network":         self.audit.network,
        }
        with open(DASHBOARD_PATH, "w") as f:
            json.dump(dashboard_data, f, default=str, indent=2)

        # P0-FIX: Also sync to Vercel public directory for static deployment
        vercel_public_path = Path("dashboard/public/dashboard.json")
        try:
            vercel_public_path.parent.mkdir(parents=True, exist_ok=True)
            with open(vercel_public_path, "w") as f:
                json.dump(dashboard_data, f, default=str, indent=2)
        except Exception as e:
            self.logger.warning("vercel_dashboard_sync_failed", error=str(e))

    def get_stats(self) -> dict:
        return {**self._stats, "latest_findings": len(self._findings),
                "circuit_open": self._circuit_open,
                "consecutive_failures": self._consecutive_failures}

    def get_latest_findings(self, n: int = 10) -> list[dict]:
        return self._findings[-n:]

    # ── File Rotation (P2-27) ──────────────────────────────────────────────────

    @staticmethod
    def _rotate_if_needed(file_path: str, max_age_days: int = 30) -> None:
        """P2-27: Rotate JSONL files if they are from a previous day.

        Strategy:
          - If the file's mtime is from a previous day, gzip the old file
            with a date suffix and start a fresh file.
          - Clean up gzipped files older than max_age_days.
          - Same logic can be applied to findings.jsonl and audit_log.jsonl.
        """
        from pathlib import Path as _Path
        import gzip

        p = _Path(file_path)
        if not p.exists():
            return

        # Check if file is from a previous day
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        now = datetime.now(tz=timezone.utc)

        if mtime.date() < now.date():
            # Rotate: gzip the old file with date suffix
            date_suffix = mtime.strftime("%Y-%m-%d")
            rotated_name = p.stem + f"-{date_suffix}" + p.suffix + ".gz"
            rotated_path = p.parent / rotated_name

            try:
                with open(p, "rb") as f_in:
                    with gzip.open(rotated_path, "wb") as f_out:
                        f_out.writelines(f_in)
                # Truncate original to start fresh
                p.write_text("")
                logger.info("file_rotated",
                            original=str(p),
                            rotated=str(rotated_path))
            except Exception as e:
                logger.warning("file_rotation_failed",
                               path=str(p), error=str(e))

        # Clean up old gzipped files
        try:
            for gz_file in p.parent.glob(p.stem + "-*.jsonl.gz"):
                gz_mtime = datetime.fromtimestamp(
                    gz_file.stat().st_mtime, tz=timezone.utc)
                age_days = (now - gz_mtime).days
                if age_days > max_age_days:
                    gz_file.unlink()
                    logger.info("old_rotated_file_cleaned",
                                path=str(gz_file), age_days=age_days)
        except Exception as e:
            logger.warning("rotation_cleanup_failed", error=str(e))
