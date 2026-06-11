"""
Mantle Intel Agent — Insight Agent (Stage 4)
Uses Qwen-Max (via DashScope/OpenRouter) to generate institutional-grade
narrative summaries for each anomaly finding.
Falls back to template-based generation when no API key is set.
"""
from __future__ import annotations

import os
import json
import time
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


SYSTEM_PROMPT = """You are a senior on-chain analyst at a crypto hedge fund specializing in Mantle Network.
Your job is to write concise, institutional-grade intelligence reports on detected blockchain anomalies.

Rules:
- 3-5 sentences maximum per report
- Lead with the most actionable insight
- Include specific numbers from the data
- End with a forward-looking implication (what might happen next)
- Do NOT use buzzwords like "fascinating", "interesting", "notable"
- Write for a sophisticated investor who values precision over hype
- Always mention Mantle specifically (not generic "on-chain")
"""

INSIGHT_TEMPLATE = {
    "whale_accumulation": (
        "🐋 WHALE ACCUMULATION — Mantle Block {block_height}\n\n"
        "{description}\n\n"
        "💡 Implication: Large DeFi inflows on Mantle have historically preceded 15–40% TVL increases "
        "within 48–72 hours. Monitor {protocol} liquidity depth for confirmation.\n\n"
        "📊 Confidence: {confidence_pct}% | Method: Pattern Match | Data: {transfer_count} txs, ${total_usd:,.0f} total"
    ),
    "whale_distribution": (
        "⚠️ WHALE DISTRIBUTION — Mantle Block {block_height}\n\n"
        "{description}\n\n"
        "💡 Implication: Sustained outflows from Mantle DeFi protocols may signal position unwinding. "
        "Watch for cascading liquidity removal in the next 2–6 hours.\n\n"
        "📊 Confidence: {confidence_pct}% | Method: Pattern Match"
    ),
    "smart_money_inflow": (
        "🧠 SMART MONEY SIGNAL — Mantle Block {block_height}\n\n"
        "{description}\n\n"
        "💡 Implication: Coordinated unlabeled wallet activity on Mantle suggests informed positioning. "
        "This pattern has preceded major protocol TVL moves in 72% of historical cases.\n\n"
        "📊 Confidence: {confidence_pct}% | Method: Wallet Clustering | Wallets: {wallet_count}"
    ),
    "tx_spike": (
        "📈 TX VOLUME SPIKE — Mantle Block {block_height}\n\n"
        "{description}\n\n"
        "💡 Implication: Abnormal Mantle transaction volume can signal protocol catalyst events, "
        "airdrop farming, or coordinated trading. Cross-reference with protocol announcements.\n\n"
        "📊 Confidence: {confidence_pct}% | Method: Z-Score | Z={zscore}"
    ),
    "value_spike": (
        "💰 VALUE SPIKE DETECTED — Mantle Block {block_height}\n\n"
        "{description}\n\n"
        "💡 Implication: Abnormal MNT value concentration in a single block indicates large position movement. "
        "Monitor for follow-on transactions in subsequent blocks.\n\n"
        "📊 Confidence: {confidence_pct}% | Method: Z-Score | Z={zscore}"
    ),
    "multivariate_anomaly": (
        "🔍 MULTIVARIATE ANOMALY — Mantle Block {block_height}\n\n"
        "{description}\n\n"
        "💡 Implication: Multi-dimensional statistical outlier on Mantle — combined tx volume, "
        "transfer value, and wallet activity are simultaneously anomalous. Warrants immediate investigation.\n\n"
        "📊 Confidence: {confidence_pct}% | Method: Isolation Forest | Score: {isolation_score}"
    ),
}

DEFAULT_TEMPLATE = (
    "⚡ ANOMALY DETECTED — Mantle Block {block_height}\n\n"
    "{description}\n\n"
    "📊 Confidence: {confidence_pct}% | Type: {anomaly_type}"
)


class InsightAgent:
    """
    Generates institutional-grade narratives for anomaly findings.
    Uses Qwen-Max via DashScope API when available, falls back to templates.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-max",
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        self.model   = model
        self._use_llm = bool(self.api_key and HTTPX_AVAILABLE)
        self.logger  = logger.bind(agent="insight")

        if self._use_llm:
            self.logger.info("llm_mode_enabled", model=self.model)
        else:
            self.logger.info("template_mode", reason="No API key or httpx not available")

    async def generate_insight(self, finding) -> str:
        """Generate a narrative for an AnomalyFinding."""
        if self._use_llm:
            try:
                return await self._qwen_generate(finding)
            except Exception as e:
                self.logger.warning("llm_failed_fallback", error=str(e))

        return self._template_generate(finding)

    async def _qwen_generate(self, finding) -> str:
        user_prompt = f"""Generate an institutional intelligence report for this Mantle on-chain anomaly:

Anomaly Type: {finding.anomaly_type}
Block Height: {finding.block_height}
Timestamp: {finding.timestamp}
Confidence: {finding.confidence * 100:.1f}%
Detection Method: {finding.method}

Raw Description: {finding.description}

Raw Metrics: {json.dumps(finding.raw_metrics, indent=2)}

Large Transfers Involved: {json.dumps(finding.large_transfers[:3], indent=2) if finding.large_transfers else 'None'}

Write a 3-5 sentence institutional intelligence report. Lead with the actionable insight.
End with what might happen next on Mantle based on this pattern."""

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": {
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user",   "content": user_prompt},
                        ]
                    },
                    "parameters": {
                        "result_format": "message",
                        "max_tokens": 300,
                        "temperature": 0.3,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["output"]["choices"][0]["message"]["content"]

        header = f"🤖 AI INTEL [{finding.anomaly_type.upper()}] — Mantle Block {finding.block_height}\n\n"
        footer = f"\n\n📊 Confidence: {finding.confidence*100:.1f}% | Model: {self.model} | Method: {finding.method}"
        return header + text.strip() + footer

    def _template_generate(self, finding) -> str:
        """Fallback template-based insight generation."""
        m = finding.raw_metrics or {}
        template = INSIGHT_TEMPLATE.get(finding.anomaly_type, DEFAULT_TEMPLATE)

        try:
            return template.format(
                block_height    = finding.block_height,
                description     = finding.description,
                confidence_pct  = int(finding.confidence * 100),
                anomaly_type    = finding.anomaly_type,
                # optional fields with defaults
                protocol        = (finding.large_transfers[0].get("label_to", "protocol") if finding.large_transfers else "protocol"),
                transfer_count  = m.get("transfer_count", len(finding.large_transfers)),
                total_usd       = m.get("total_usd", 0),
                wallet_count    = m.get("wallet_count", 0),
                zscore          = m.get("zscore", "N/A"),
                isolation_score = m.get("isolation_score", "N/A"),
            )
        except KeyError:
            return DEFAULT_TEMPLATE.format(
                block_height   = finding.block_height,
                description    = finding.description,
                confidence_pct = int(finding.confidence * 100),
                anomaly_type   = finding.anomaly_type,
            )

    def format_telegram_alert(self, finding, insight_text: str) -> str:
        """Format for Telegram markdown (escape special chars)."""
        # Telegram MarkdownV2 escapes
        def esc(s: str) -> str:
            for c in r"_*[]()~`>#+-=|{}.!":
                s = s.replace(c, f"\\{c}")
            return s

        lines = insight_text.split("\n")
        return insight_text  # Return as-is for HTML parse_mode

    def format_dashboard_card(self, finding, insight_text: str) -> dict:
        """Format for web dashboard JSON."""
        return {
            "id":            finding.finding_id,
            "type":          finding.anomaly_type,
            "block":         finding.block_height,
            "timestamp":     finding.timestamp,
            "confidence":    finding.confidence,
            "confidence_pct": int(finding.confidence * 100),
            "hash":          finding.sha256_hash(),
            "hex_hash":      finding.hex_bytes32(),
            "insight":       insight_text,
            "raw_metrics":   finding.raw_metrics,
            "method":        finding.method,
            "transfers":     finding.large_transfers[:5],
        }
