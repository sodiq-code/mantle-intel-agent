"""
Mantle Intel Agent — Telegram Bot
Commands: /start, /status, /latest, /verify <hash>
Auto-pushes alerts when new findings are emitted by pipeline.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, ContextTypes
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import CONTRACT_ADDRESS


WELCOME_MSG = """
🔍 <b>Mantle Intel Agent v2.0</b>

Autonomous on-chain intelligence for Mantle Network.
5-agent AI pipeline — detects whale moves, smart money inflows, and anomalous patterns.
Every finding verified on-chain via MantleIntelAudit.sol.

<b>Commands:</b>
/start               — This message
/status              — Pipeline status + stats
/latest              — Last 5 findings
/verify &lt;hash&gt;  — Verify a finding hash on-chain
/compare &lt;type&gt; — Compare signal history (whale|smart_money|cex|mev|all)

<b>Contract:</b> <code>0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b</code>
<b>Network:</b> Mantle Sepolia Testnet

<i>Mantle Intel Agent — On-Chain Intelligence for the Mantle Ecosystem</i>
"""

STATUS_TEMPLATE = """
📊 <b>Pipeline Status</b>

🔗 Network: <code>{network}</code>
📦 Contract: <code>{contract}</code>
🔄 Cycles run: <b>{cycles}</b>
📈 Blocks processed: <b>{blocks}</b>
🚨 Findings total: <b>{findings}</b>
⏱ Running since: <code>{started}</code>

Demo mode: {demo_badge}
"""

INCIDENT_TEMPLATE = """
{icon} <b>{anomaly_type_label} Incident</b>

{insight}

<b>Incident ID:</b> <code>{incident_id}</code>
<b>Status:</b> {state}
<b>Detection Confidence:</b> <b>{conf}%</b> (Anomaly Detection)
<b>Blocks:</b> <code>{start}</code> to <code>{latest}</code> (Duration: {dur} blocks)
<b>Timestamp (UTC):</b> <code>{timestamp}</code>
<b>Signals:</b> {occ}

<b>Evidence:</b>
{evidence}

🔐 Latest Hash: <code>{hash_short}</code>
"""


def anomaly_icon(anomaly_type: str) -> str:
    icons = {
        "whale_accumulation":  "🐋",
        "whale_distribution":  "⚠️",
        "smart_money_inflow":  "🧠",
        "tx_spike":            "📈",
        "value_spike":         "💰",
        "multivariate_anomaly": "🔍",
        "liquidity_imbalance": "💧",
        "meth_depeg":          "⚡",
        "cross_protocol_anomaly": "🌐",
        "composite":           "🔥",
    }
    return icons.get(anomaly_type, "⚡")


def anomaly_label(anomaly_type: str) -> str:
    labels = {
        "whale_accumulation":   "Whale Accumulation",
        "whale_distribution":   "Whale Distribution",
        "smart_money_inflow":   "Smart Money Inflow",
        "tx_spike":             "TX Volume Spike",
        "value_spike":          "Value Spike",
        "multivariate_anomaly": "Multivariate Anomaly",
        "liquidity_imbalance":  "Liquidity Imbalance",
        "meth_depeg":           "mETH Depeg",
        "cross_protocol_anomaly": "Cross-Protocol Anomaly",
        "composite":            "Composite Anomaly",
    }
    return labels.get(anomaly_type, anomaly_type.replace("_", " ").title())


class MantleIntelBot:
    """Telegram bot that wraps the pipeline and surfaces findings."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token   = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self._app    = None
        self._bot    = None
        self._pipeline = None
        self.logger  = logger.bind(component="telegram_bot")

        if not TELEGRAM_AVAILABLE:
            self.logger.warning("python_telegram_bot_not_installed",
                                msg="pip install python-telegram-bot")
        if not self.token:
            self.logger.warning("no_telegram_token",
                                msg="Set TELEGRAM_BOT_TOKEN env var")

    def set_pipeline(self, pipeline):
        self._pipeline = pipeline

    def is_configured(self) -> bool:
        return bool(self.token and TELEGRAM_AVAILABLE)

    # ── Alert push ────────────────────────────────────────────────────────────

    async def push_incident(self, incident: dict):
        """Push a new incident alert to the configured chat."""
        if not self.is_configured() or not self.chat_id:
            self.logger.debug("push_skipped", reason="not configured")
            return

        try:
            bot = Bot(token=self.token)
            msg = self._format_incident_message(incident)
            await bot.send_message(
                chat_id=self.chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
            self.logger.info("alert_pushed", incident_id=incident.get("incident_id"), chat=self.chat_id)
        except Exception as e:
            self.logger.error("push_failed", error=str(e))

    def _format_incident_message(self, incident: dict) -> str:
        atype   = incident.get("type", "anomaly")
        is_composite = incident.get("is_composite", False)
        anomaly_types = incident.get("anomaly_types", [atype])
        state   = incident.get("state", "🟡 Incident")
        start   = incident.get("start_block", 0)
        latest  = incident.get("latest_block", 0)
        dur     = incident.get("duration_blocks", 1)
        occ     = incident.get("occurrences", 1)
        conf    = incident.get("peak_confidence", 0)
        fhash   = incident.get("latest_hash", "")
        insight = incident.get("insight_sample", "")

        insight_trimmed = insight[:800] + "..." if len(insight) > 800 else insight

        detectors_list = incident.get("detectors", [])
        if detectors_list:
            evidence_str = "\n".join(f"✓ {d}" for d in detectors_list)
        else:
            evidence_str = "✓ Baseline Anomaly"

        # Composite: show all signals in the label
        if is_composite:
            labels = [anomaly_label(t) for t in anomaly_types]
            short_labels = [l.replace("Accumulation", "Accum.").replace("Distribution", "Distrib.").replace("Anomaly", "").strip() for l in labels]
            type_label = "Composite Anomaly: " + " + ".join(short_labels[:3])
            if len(anomaly_types) > 3:
                type_label += f" +{len(anomaly_types) - 3} more"
            icon = "🔥"  # composite icon
            signals_line = f"<b>Signals:</b> {', '.join(labels)}\n"
        else:
            type_label = anomaly_label(atype)
            icon = anomaly_icon(atype)
            signals_line = ""

        return INCIDENT_TEMPLATE.format(
            icon=icon,
            anomaly_type_label=type_label,
            insight=insight_trimmed,
            incident_id=incident.get("incident_id", "N/A"),
            state=state,
            start=f"{start:,}",
            latest=f"{latest:,}",
            dur=dur,
            occ=occ,
            conf=conf,
            timestamp=incident.get("timestamp", "N/A"),
            evidence=evidence_str,
            hash_short=f"{fhash[:20]}..." if fhash else "N/A"
        ).strip()

    # ── Command handlers ──────────────────────────────────────────────────────

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_html(WELCOME_MSG)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._pipeline:
            await update.message.reply_text("Pipeline not running.")
            return

        stats = self._pipeline.get_stats()
        contract = self._pipeline.audit.contract_address or "not deployed"
        network  = self._pipeline.audit.network
        demo     = "✅ Live" if not self._pipeline.collector.demo_mode else "🟡 Demo Mode"

        msg = STATUS_TEMPLATE.format(
            network   = network,
            contract  = contract[:20] + "..." if len(contract) > 20 else contract,
            cycles    = stats.get("cycles_run", 0),
            blocks    = stats.get("blocks_processed", 0),
            findings  = stats.get("findings_total", 0),
            started   = stats.get("started_at", "N/A"),
            demo_badge = demo,
        )
        await update.message.reply_html(msg)

    async def cmd_latest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._pipeline:
            await update.message.reply_text("Pipeline not running.")
            return

        findings = self._pipeline.get_latest_findings(5)
        if not findings:
            await update.message.reply_text("No findings yet. Pipeline is running...")
            return

        for f in reversed(findings[-5:]):
            insight = f.get("insight", f.get("type", "anomaly"))
            msg = self._format_finding_message(f, insight)
            await update.message.reply_html(msg)
            await asyncio.sleep(0.3)

    async def cmd_verify(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /verify <finding_hash>")
            return

        finding_hash = context.args[0].lstrip("0x")
        if not self._pipeline:
            await update.message.reply_text("Pipeline not running.")
            return

        result = await self._pipeline.audit.verify_finding(finding_hash)
        if result.get("verified"):
            contract = self._pipeline.audit.contract_address
            network  = self._pipeline.audit.network
            explorer_base = "https://mantlescan.xyz" if network == "mainnet" else "https://sepolia.mantlescan.xyz"
            msg = (
                f"✅ <b>Finding Verified On-Chain</b>\n\n"
                f"Hash: <code>0x{finding_hash[:20]}...</code>\n"
                f"Finding ID: <b>{result.get('finding_id', 'N/A')}</b>\n"
                f"Confidence: <b>{result.get('confidence', 0)}%</b>\n"
                f"Recorded at: <code>{result.get('timestamp', 'N/A')}</code>\n\n"
                f'<a href="{explorer_base}/address/{contract}">View Contract on Mantle Explorer</a>'
            )
        else:
            msg = (
                f"❌ <b>Finding Not Found On-Chain</b>\n\n"
                f"Hash <code>0x{finding_hash[:20]}...</code> is not recorded in the audit contract.\n"
                f"This may be a demo-mode finding or an invalid hash."
            )
        await update.message.reply_html(msg)

    async def cmd_compare(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /compare <type> — compare signal history
        Types: whale | smart_money | cex | mev | all
        """
        valid_types = {"whale", "smart_money", "cex", "mev", "all"}
        signal_type = (context.args[0] if context.args else "all").lower()

        if signal_type not in valid_types:
            await update.message.reply_text(
                f"Usage: /compare &lt;type&gt;\n"
                f"Types: {' | '.join(sorted(valid_types))}"
            )
            return

        if not self._pipeline:
            await update.message.reply_text("Pipeline not running.")
            return

        sm_agent = self._pipeline.smart_money
        result   = sm_agent.compare_signals(signal_type)

        protocol_lines = "\n".join(
            f"  • <b>{p['protocol']}</b>: ${p['volume_usd']:,.0f}"
            for p in result.get("top_protocols", [])[:5]
        ) or "  <i>No protocol data</i>"

        action_lines = "\n".join(
            f"  • {k}: {v}"
            for k, v in result.get("action_breakdown", {}).items()
        ) or "  <i>No action data</i>"

        msg = (
            f"📊 <b>Signal Compare — {signal_type.upper()}</b>\n\n"
            f"Count: <b>{result.get('count', 0)}</b> signals (last {result.get('lookback_count', 50)})\n"
            f"Total Flow: <b>${result.get('total_usd', 0):,.0f}</b>\n"
            f"Avg per Signal: <b>${result.get('avg_usd', 0):,.0f}</b>\n"
            f"Avg Confidence: <b>{result.get('avg_confidence', 0)*100:.1f}%</b>\n\n"
            f"<b>Top Protocols:</b>\n{protocol_lines}\n\n"
            f"<b>Actions:</b>\n{action_lines}\n\n"
            f"<i>{result.get('message', '')}</i>"
        )
        await update.message.reply_html(msg)

    # ── Bot runner ────────────────────────────────────────────────────────────

    def build_app(self):
        if not self.is_configured():
            return None
        self._app = (
            Application.builder()
            .token(self.token)
            .build()
        )
        self._app.add_handler(CommandHandler("start",   self.cmd_start))
        self._app.add_handler(CommandHandler("status",  self.cmd_status))
        self._app.add_handler(CommandHandler("latest",  self.cmd_latest))
        self._app.add_handler(CommandHandler("verify",  self.cmd_verify))
        self._app.add_handler(CommandHandler("compare", self.cmd_compare))
        return self._app

    async def run_polling(self):
        app = self.build_app()
        if not app:
            self.logger.warning("bot_not_started", reason="Not configured")
            return
        self.logger.info("bot_polling_started")
        await app.run_polling()
