"""
Mantle Intel Agent — Discord Bot v1.0
Mirrors the Telegram bot: alerts, /compare command, live findings.
Uses discord.py (pip install discord.py).

Commands:
  !status    — pipeline status
  !latest    — last 5 findings
  !compare <type>  — compare signal types (whale | smart_money | cex | mev | all)
  !verify <hash>   — verify finding on-chain

Auto-pushes alerts to configured channel when pipeline emits findings.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


INCIDENT_TEMPLATE = """
**{icon} {anomaly_type_label} Incident**

{insight}

**Incident ID:** `{incident_id}`
**Status:** {state}
**Detection Confidence:** **{conf}%** (Anomaly Detection)
**Blocks:** `{start}` to `{latest}` (Duration: {dur} blocks)
**Timestamp (UTC):** `{timestamp}`
**Signals:** {occ}

**Evidence:**
{evidence}

🔐 Latest Hash: `{hash_short}`
"""

COMPARE_TEMPLATE = """
📊 **Signal Comparison — {signal_type}**

Count:          **{count}** signals (last {lookback})
Total Flow:     **${total_usd:,}**
Avg per Signal: **${avg_usd:,}**
Avg Confidence: **{avg_conf_pct}%**

**Top Protocols:**
{protocol_lines}

**Action Breakdown:**
{action_lines}
"""


def anomaly_icon(anomaly_type: str) -> str:
    icons = {
        "whale_accumulation":   "🐋",
        "whale_distribution":   "⚠️",
        "smart_money_inflow":   "🧠",
        "tx_spike":             "📈",
        "value_spike":          "💰",
        "multivariate_anomaly": "🔍",
        "liquidity_imbalance":  "💧",
        "meth_depeg":           "⚡",
        "cross_protocol_anomaly": "🌐",
        "lp_imbalance":         "🫧",
        "composite":            "🔥",
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
        "lp_imbalance":         "LP Imbalance",
        "composite":            "Composite Anomaly",
    }
    return labels.get(anomaly_type, anomaly_type.replace("_", " ").title())


class MantleIntelDiscordBot:
    """Discord bot that mirrors Telegram functionality + /compare command."""

    def __init__(self, token: Optional[str] = None, channel_id: Optional[int] = None):
        self.token      = token or os.getenv("DISCORD_BOT_TOKEN", "")
        self.channel_id = channel_id or int(os.getenv("DISCORD_CHANNEL_ID", "0") or "0")
        self._pipeline  = None
        self._client    = None
        self.logger     = logger.bind(component="discord_bot")

        if not DISCORD_AVAILABLE:
            self.logger.warning("discord_py_not_installed", msg="pip install discord.py")
        if not self.token:
            self.logger.warning("no_discord_token", msg="Set DISCORD_BOT_TOKEN env var")

    def set_pipeline(self, pipeline):
        self._pipeline = pipeline

    def is_configured(self) -> bool:
        return bool(self.token and DISCORD_AVAILABLE)

    # ── Alert push ──────────────────────────────────────────────────────────

    async def push_incident(self, incident: dict):
        """Push an incident update to the configured Discord channel."""
        if not self.is_configured() or not self.channel_id or not self._client:
            self.logger.debug("push_skipped_discord", reason="not configured or client not ready")
            return

        try:
            channel = self._client.get_channel(self.channel_id)
            if not channel:
                channel = await self._client.fetch_channel(self.channel_id)

            embed = self._make_embed(incident)
            await channel.send(embed=embed)
            self.logger.info("discord_alert_pushed", incident_id=incident.get("incident_id"), channel=self.channel_id)
        except Exception as e:
            self.logger.error("discord_push_failed", error=str(e))

    def _make_embed(self, incident: dict) -> "discord.Embed":
        """Build a Discord embed for an incident."""
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

        color_map = {
            "whale_accumulation":   0x3B82F6,
            "whale_distribution":   0xF97316,
            "smart_money_inflow":   0xA855F7,
            "tx_spike":             0x22C55E,
            "value_spike":          0xEAB308,
            "multivariate_anomaly": 0xEF4444,
            "liquidity_imbalance":  0x06B6D4,
            "meth_depeg":           0xF43F5E,
            "cross_protocol_anomaly": 0xEC4899,
            "lp_imbalance":         0x14B8A6,
        }
        color = color_map.get(atype, 0x6B7280)
        if "Critical" in state:
            color = 0xEF4444
        elif "Resolved" in state:
            color = 0x22C55E

        detectors_list = incident.get("detectors", [])
        if detectors_list:
            evidence_str = "\n".join(f"✓ {d}" for d in detectors_list)
        else:
            evidence_str = "✓ Baseline Anomaly"

        # Composite: generic title + signals listed in body (not title)
        if is_composite:
            labels = [anomaly_label(t) for t in anomaly_types]
            type_label = "Composite On-Chain Anomaly"
            icon = "🔥"
            signals_line = f"**Signals:** {', '.join(labels)}\n"
        else:
            type_label = anomaly_label(atype)
            icon = anomaly_icon(atype)
            signals_line = ""

        desc = INCIDENT_TEMPLATE.format(
            icon=icon,
            anomaly_type_label=type_label,
            insight=signals_line + insight[:1600],
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
        )

        embed = discord.Embed(
            title=type_label,
            description=desc,
            color=color,
        )
        return embed

    # ── Build bot with commands ──────────────────────────────────────────────

    def build_client(self) -> Optional["commands.Bot"]:
        if not self.is_configured():
            return None

        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        pipeline_ref = self
        self._client = bot

        @bot.event
        async def on_ready():
            logger.info("discord_bot_ready", user=str(bot.user), guilds=len(bot.guilds))
            print(f"Discord bot ready: {bot.user}")

        @bot.command(name="status")
        async def cmd_status(ctx):
            if not pipeline_ref._pipeline:
                await ctx.send("❌ Pipeline not running.")
                return

            stats    = pipeline_ref._pipeline.get_stats()
            contract = pipeline_ref._pipeline.audit.contract_address or "not deployed"
            network  = pipeline_ref._pipeline.audit.network
            demo     = "🟢 Live" if not pipeline_ref._pipeline.collector.demo_mode else "🟡 Demo Mode"

            embed = discord.Embed(title="📊 Pipeline Status", color=0x22C55E)
            embed.add_field(name="Network",        value=network,           inline=True)
            embed.add_field(name="Mode",           value=demo,              inline=True)
            embed.add_field(name="Cycles Run",     value=stats.get("cycles_run", 0), inline=True)
            embed.add_field(name="Blocks Scanned", value=f"{stats.get('blocks_processed', 0):,}", inline=True)
            embed.add_field(name="Findings",       value=stats.get("findings_total", 0), inline=True)
            embed.add_field(name="Contract",       value=f"`{contract[:20]}...`", inline=False)
            await ctx.send(embed=embed)

        @bot.command(name="latest")
        async def cmd_latest(ctx):
            if not pipeline_ref._pipeline:
                await ctx.send("❌ Pipeline not running.")
                return

            findings = pipeline_ref._pipeline.get_latest_findings(5)
            if not findings:
                await ctx.send("No findings yet. Pipeline is running...")
                return

            for f in reversed(findings[-5:]):
                insight = f.get("insight", f.get("type", "anomaly"))
                embed = pipeline_ref._make_embed(f, insight)
                await ctx.send(embed=embed)
                await asyncio.sleep(0.3)

        @bot.command(name="compare")
        async def cmd_compare(ctx, signal_type: str = "all"):
            """
            !compare <type> — compare signal history
            Types: whale | smart_money | cex | mev | all
            """
            valid_types = {"whale", "smart_money", "cex", "mev", "all"}
            signal_type = signal_type.lower()

            if signal_type not in valid_types:
                await ctx.send(f"❓ Unknown type. Use: {', '.join(sorted(valid_types))}")
                return

            if not pipeline_ref._pipeline:
                await ctx.send("❌ Pipeline not running.")
                return

            sm_agent = pipeline_ref._pipeline.smart_money
            result   = sm_agent.compare_signals(signal_type)

            protocol_lines = "\n".join(
                f"  • {p['protocol']}: ${p['volume_usd']:,.0f}"
                for p in result.get("top_protocols", [])
            ) or "  _No protocol data_"

            action_lines = "\n".join(
                f"  • {k}: {v}"
                for k, v in result.get("action_breakdown", {}).items()
            ) or "  _No action data_"

            embed = discord.Embed(
                title=f"📊 Signal Compare — {signal_type.upper()}",
                color=0xA855F7,
            )
            embed.add_field(name="Count",          value=result.get("count", 0), inline=True)
            embed.add_field(name="Total Flow",     value=f"${result.get('total_usd', 0):,}", inline=True)
            embed.add_field(name="Avg Confidence", value=f"{result.get('avg_confidence', 0)*100:.1f}%", inline=True)
            embed.add_field(name="Top Protocols",  value=protocol_lines, inline=False)
            embed.add_field(name="Actions",        value=action_lines,   inline=False)
            embed.set_footer(text=f"Last {result.get('lookback_count', 50)} signals · Mantle Intel Agent")
            await ctx.send(embed=embed)

        @bot.command(name="verify")
        async def cmd_verify(ctx, finding_hash: str = ""):
            if not finding_hash:
                await ctx.send("Usage: `!verify <finding_hash>`")
                return

            if not pipeline_ref._pipeline:
                await ctx.send("❌ Pipeline not running.")
                return

            result = await pipeline_ref._pipeline.audit.verify_finding(finding_hash.lstrip("0x"))
            if result.get("verified"):
                contract = pipeline_ref._pipeline.audit.contract_address
                network  = pipeline_ref._pipeline.audit.network
                explorer_base = "https://mantlescan.xyz" if network == "mainnet" else "https://sepolia.mantlescan.xyz"

                embed = discord.Embed(title="✅ Finding Verified On-Chain", color=0x22C55E)
                embed.add_field(name="Hash",       value=f"`{finding_hash[:20]}...`", inline=False)
                embed.add_field(name="Finding ID", value=result.get("finding_id", "N/A"), inline=True)
                embed.add_field(name="Confidence", value=f"{result.get('confidence', 0)}%", inline=True)
                embed.add_field(name="Explorer",   value=f"[View Contract]({explorer_base}/address/{contract})", inline=False)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Finding Not Found On-Chain",
                    description=f"Hash `{finding_hash[:20]}...` not in audit contract. May be demo-mode finding.",
                    color=0xEF4444,
                )
                await ctx.send(embed=embed)

        return bot

    async def run(self):
        client = self.build_client()
        if not client:
            self.logger.warning("discord_not_started", reason="not configured")
            return
        self.logger.info("discord_bot_starting")
        await client.start(self.token)


# ── Standalone runner ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot = MantleIntelDiscordBot()
    if not bot.is_configured():
        print("DISCORD_BOT_TOKEN not set — skipping Discord bot")
    else:
        asyncio.run(bot.run())
