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
from typing import Optional, Callable
import structlog

from agents.collector.collector_agent import CollectorAgent
from agents.anomaly.anomaly_agent import AnomalyAgent, AnomalyFinding
from agents.smart_money.smart_money_agent import SmartMoneyAgent
from agents.insight.insight_agent import InsightAgent
from agents.audit.audit_agent import AuditAgent
from agents.incident import IncidentManager
from bot.discord_webhook import push_incident as discord_push

# P2-16: OpenTelemetry tracing
try:
    from agents.tracing import tracer as _otel_tracer
except ImportError:
    _otel_tracer = None

logger = structlog.get_logger(__name__)

os.makedirs("data", exist_ok=True)
FINDINGS_PATH = "data/findings.jsonl"
AUDIT_LOG_PATH = "data/audit_log.jsonl"
DASHBOARD_PATH = "data/dashboard.json"


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

        # Initialize agents
        self.collector = CollectorAgent(poll_interval=poll_interval)
        self.anomaly = AnomalyAgent()
        self.smart_money = SmartMoneyAgent()
        self.insight = InsightAgent()
        self.audit = AuditAgent()

        self.logger = logger.bind(component="pipeline")
        self.logger.info("pipeline_initialized",
                         demo_mode=self.collector.demo_mode,
                         audit_demo=self.audit.demo_mode)

    # ── Single cycle ──────────────────────────────────────────────────────────

    async def run_cycle(self) -> list[dict]:
        """Run one full pipeline cycle. Returns list of new finding dicts."""
        # P2-16: OpenTelemetry span for pipeline cycle
        span_cm = None
        span = None
        if _otel_tracer:
            span_cm = _otel_tracer.start_as_current_span("pipeline.run_cycle")
            span = span_cm.__enter__()
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
        for finding in anomalies:
            try:
                # Generate insight
                insight_text = await self.insight.generate_insight(finding)

                # Record on-chain
                audit_record = await self.audit.record_finding(finding)

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

                # Process Incident State for Bots
                incident_update = self.incident_manager.process_finding(
                    dashboard_card, latest_block)
                if incident_update:
                    await self._notify_incident(incident_update)

            except Exception as e:
                self.logger.error("finding_processing_failed",
                                  finding_id=finding.finding_id,
                                  error=str(e))

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
        if span_cm:
            if span:
                span.set_attribute("pipeline.new_findings", len(new_findings))
                span.set_attribute("pipeline.elapsed_s", round(elapsed, 2))
            span_cm.__exit__(None, None, None)

        return new_findings

    async def _notify_incident(self, incident: dict):
        """Push an incident update to the configured bots."""
        if self.on_incident:
            try:
                await self.on_incident(incident)
            except Exception as cb_e:
                self.logger.warning("callback_failed", error=str(cb_e))

        try:
            discord_push(incident)
        except Exception as dc_e:
            self.logger.warning("discord_webhook_failed", error=str(dc_e))

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
        self._rotate_if_needed(FINDINGS_PATH)
        with open(FINDINGS_PATH, "a") as f:
            f.write(json.dumps(finding, default=str) + "\n")

    def _update_dashboard(self):
        """Write latest state to dashboard.json for the web UI."""
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
