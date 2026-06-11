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

from agents.collector.collector_agent   import CollectorAgent
from agents.anomaly.anomaly_agent       import AnomalyAgent, AnomalyFinding
from agents.smart_money.smart_money_agent import SmartMoneyAgent
from agents.insight.insight_agent       import InsightAgent
from agents.audit.audit_agent           import AuditAgent

logger = structlog.get_logger(__name__)

os.makedirs("data", exist_ok=True)
FINDINGS_PATH  = "data/findings.jsonl"
AUDIT_LOG_PATH = "data/audit_log.jsonl"
DASHBOARD_PATH = "data/dashboard.json"


class MantleIntelPipeline:
    """
    Orchestrates the full 5-agent pipeline.
    Emits findings to callbacks (Telegram bot, dashboard, etc).
    """

    def __init__(
        self,
        on_finding: Optional[Callable] = None,
        poll_interval: int = 30,
        blocks_per_cycle: int = 50,
    ):
        self.on_finding      = on_finding
        self.poll_interval   = poll_interval
        self.blocks_per_cycle = blocks_per_cycle
        self._running        = False
        self._findings: list[dict] = []
        self._stats = {
            "cycles_run":      0,
            "blocks_processed": 0,
            "findings_total":   0,
            "started_at":       None,
        }

        # Initialize agents
        self.collector   = CollectorAgent(poll_interval=poll_interval)
        self.anomaly     = AnomalyAgent()
        self.smart_money = SmartMoneyAgent()
        self.insight     = InsightAgent()
        self.audit       = AuditAgent()

        self.logger = logger.bind(component="pipeline")
        self.logger.info("pipeline_initialized",
                         demo_mode=self.collector.demo_mode,
                         audit_demo=self.audit.demo_mode)

    # ── Single cycle ──────────────────────────────────────────────────────────

    async def run_cycle(self) -> list[dict]:
        """Run one full pipeline cycle. Returns list of new finding dicts."""
        cycle_start = time.time()
        new_findings = []

        self.logger.info("cycle_start", cycle=self._stats["cycles_run"] + 1)

        # Stage 1: Collect
        blocks = await self.collector.collect_blocks(self.blocks_per_cycle)
        if not blocks:
            self.logger.warning("no_blocks_collected")
            return []

        self._stats["blocks_processed"] += len(blocks)

        # Stage 2: Anomaly detection
        anomalies: list[AnomalyFinding] = self.anomaly.detect(blocks)

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
                dashboard_card = self.insight.format_dashboard_card(finding, insight_text)
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

                new_findings.append(dashboard_card)
                self._findings.append(dashboard_card)
                self._findings = self._findings[-100:]  # keep last 100

                # Persist
                self._append_finding(dashboard_card)

                # Notify callback (Telegram, etc.)
                if self.on_finding:
                    try:
                        await self.on_finding(dashboard_card, insight_text)
                    except Exception as cb_e:
                        self.logger.warning("callback_failed", error=str(cb_e))

            except Exception as e:
                self.logger.error("finding_processing_failed",
                                  finding_id=finding.finding_id,
                                  error=str(e))

        # Save audit log
        self.audit.save_audit_log(AUDIT_LOG_PATH)

        # Update dashboard
        self._update_dashboard()

        self._stats["cycles_run"]    += 1
        self._stats["findings_total"] += len(new_findings)

        elapsed = time.time() - cycle_start
        self.logger.info("cycle_complete",
                         cycle=self._stats["cycles_run"],
                         new_findings=len(new_findings),
                         elapsed_s=round(elapsed, 2))

        return new_findings

    # ── Continuous loop ───────────────────────────────────────────────────────

    async def run_continuous(self):
        """Run pipeline continuously with poll_interval delay between cycles."""
        self._running = True
        self._stats["started_at"] = datetime.now(tz=timezone.utc).isoformat()
        self.logger.info("pipeline_started", interval=self.poll_interval)

        while self._running:
            try:
                await self.run_cycle()
            except Exception as e:
                self.logger.error("cycle_error", error=str(e))
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
        self.logger.info("pipeline_stopped")

    # ── Persistence ───────────────────────────────────────────────────────────

    def _append_finding(self, finding: dict):
        """Append finding to JSONL store."""
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
        return {**self._stats, "latest_findings": len(self._findings)}

    def get_latest_findings(self, n: int = 10) -> list[dict]:
        return self._findings[-n:]
