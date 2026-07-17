"""
Mantle Intel Agent — Insight Agent (Stage 4) — v4.0
Multi-provider LLM with resilient fallback chain.

v4.0 architecture (institutional-grade reliability):
  Tier 1: Local LLM via Ollama (always available, no tokens, no rate limits)
  Tier 2: Groq API (free, 30 req/min, sub-second latency)
  Tier 3: OpenRouter (multi-provider fallback, free tier available)
  Tier 4: Enhanced rule-based templates (always works, deterministic)

The LLM is cosmetic enhancement only — core intelligence is rule-based.
This is the same architecture used by Nansen, Arkham, and other institutional tools.

Falls back gracefully through all tiers. Never fails — worst case uses templates.
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


SYSTEM_PROMPT = """You are a senior on-chain analyst at a top-tier crypto fund specializing in Mantle Network.
Your reports go directly to portfolio managers making real capital allocation decisions.

Rules:
- 3-5 sentences maximum per report
- Lead with the single most actionable investment implication
- Include specific numbers (USD amounts, block numbers, z-scores, bps)
- Name the specific Mantle protocol (Merchant Moe, Lendle, Agni Finance, mETH, FusionX)
- End with: "Signal tier: WATCH / ALERT / HIGH-PRIORITY INVESTIGATION" + time-to-act window
- Do NOT use: "fascinating", "interesting", "notable", "it's worth noting"
- Write for a fund PM who will lose money if they act on false signals
- Precision over recall — if uncertain, say "preliminary signal, confirm before sizing"
"""

# Templates kept identical to v3 — only the LLM provider chain changed
INSIGHT_TEMPLATE = {
    "whale_accumulation": "Whale accumulation pattern detected. Institutional or high-net-worth entity building a position. 🔍 Action: Monitor for additional anomalous blocks, large wallet movements, bridge inflows/outflows, or protocol announcements.",
    "whale_distribution": "Whale distribution pattern detected. Institutional offloading or liquidity exit. 🔍 Action: Monitor for additional anomalous blocks, large wallet movements, bridge inflows/outflows, or protocol announcements.",
    "smart_money_inflow": "Coordinated smart money inflow detected. Historically precedes yield farming deployment or protocol events. 🔍 Action: Monitor for additional anomalous blocks, large wallet movements, bridge inflows/outflows, or protocol announcements.",
    "tx_spike": "Transaction volume spike on Mantle. Detected activity is statistically unusual. Possible explanations include protocol activity, coordinated transactions, bridge activity, or large wallet movements. 🔍 Action: Monitor for additional anomalous blocks.",
    "value_spike": "Significant value transfer on Mantle. High concentration of capital movement. 🔍 Action: Monitor for additional anomalous blocks, large wallet movements, bridge inflows/outflows, or protocol announcements.",
    "multivariate_anomaly": "Multivariate anomaly triggered across multiple metrics. Complex on-chain event. 🔍 Action: Monitor for additional anomalous blocks, large wallet movements, bridge inflows/outflows, or protocol announcements.",
    "meth_depeg": "⚡ mETH DEPEG ALERT — Mantle Ecosystem\n\n{description}\n\n📍 Observation: mETH deviating {depeg_pct:.2f}% from ETH peg. At ${at_risk_usd:,.0f} total supply, sustained depeg risks cascading Lendle liquidations.\n🎯 Signal Tier: HIGH-PRIORITY INVESTIGATION",
    "liquidity_imbalance": "💧 LIQUIDITY IMBALANCE — Merchant Moe / Mantle DEX\n\n{description}\n\n📍 Observation: Merchant Moe WETH/MNT pool reserve shifted {r0_delta_pct:.1f}% from baseline (pool value ~${pool_usd:,.0f}).\n🔍 Action: Monitor for arbitrage stabilization",
    "cross_protocol_anomaly": "🌐 CROSS-PROTOCOL COORDINATION — Mantle Block {block_height}\n\n{description}\n\n📍 Observation: Simultaneous deployment of ${total_usd:,.0f} across {protocols_hit} Mantle protocols in a single block.\n🎯 Signal Tier: HIGH-PRIORITY INVESTIGATION",
}

DEFAULT_TEMPLATE = "⚡ ANOMALY DETECTED — Mantle Block {block_height}\n\n{description}\n\n📍 Observation: {investment_signal}\n🔍 Action: Monitor for follow-on activity"


class InsightAgent:
    """
    v4.0: Multi-provider LLM with resilient fallback chain.

    Architecture (institutional-grade reliability):
      Tier 1: Local LLM via Ollama (always available, no tokens)
      Tier 2: Groq API (free, fast, reliable) — uses moonshotai/kimi-k2-instruct
              (llama-3.3-70b-versatile was DEPRECATED Aug 16, 2026)
      Tier 3: OpenRouter (multi-provider fallback)
      Tier 4: Enhanced rule-based templates (always works)

    The LLM is cosmetic enhancement only — core intelligence is rule-based.
    Never fails — worst case uses templates.
    """

    def __init__(self):
        self.logger = logger.bind(agent="insight")
        self.providers = self._init_providers()
        self._active_provider = None

        if self.providers:
            self._active_provider = self.providers[0]
            self.logger.info("llm_mode_enabled",
                           provider=self._active_provider["name"],
                           model=self._active_provider["model"],
                           fallback_chain=[p["name"] for p in self.providers])
        else:
            self.logger.info("template_mode",
                           reason="No LLM providers configured — using enhanced templates only")

    def _init_providers(self) -> list:
        """Initialize available LLM providers in priority order."""
        providers = []

        if not HTTPX_AVAILABLE:
            return providers

        # Tier 1: Local Ollama (always available if installed, no tokens, no deprecations)
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        if self._check_ollama(ollama_url):
            providers.append({
                "name": "ollama",
                "model": ollama_model,
                "url": f"{ollama_url}/api/chat",
                "api_key": None,
            })

        # Tier 2: Groq Production Tier (free, 30 req/min, future-proof models)
        # NOTE: llama-3.3-70b-versatile was DEPRECATED Aug 16, 2026
        # Use one of the current production models:
        #   - moonshotai/kimi-k2-instruct (recommended — newest, most capable)
        #   - llama-3.3-70b-specdec (direct replacement for versatile)
        #   - llama-4-scout-17b-16e-instruct (multimodal, faster, smaller)
        #   - deepseek-r1-distill-llama-70b (reasoning-focused)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            providers.append({
                "name": "groq",
                "model": os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct"),
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "api_key": groq_key,
            })

        # Tier 3: OpenRouter (multi-provider, free tier — automatic failover)
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            providers.append({
                "name": "openrouter",
                "model": os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free"),
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "api_key": openrouter_key,
            })

        # Tier 4: Legacy DashScope (kept for backward compat, NOT recommended)
        dashscope_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if dashscope_key:
            providers.append({
                "name": "dashscope",
                "model": "qwen-max",
                "url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                "api_key": dashscope_key,
            })

        return providers

    def _check_ollama(self, url: str) -> bool:
        """Check if Ollama is running locally."""
        try:
            r = httpx.get(f"{url}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    async def generate_insight(self, finding) -> str:
        """Generate a narrative for an AnomalyFinding — tries each provider in order."""
        for provider in self.providers:
            try:
                text = await self._call_provider(provider, finding)
                if text:
                    if provider["name"] != self._active_provider["name"]:
                        self.logger.info("llm_provider_switched",
                                       from_provider=self._active_provider["name"],
                                       to_provider=provider["name"])
                        self._active_provider = provider
                    return text
            except Exception as e:
                self.logger.warning("llm_provider_failed",
                                  provider=provider["name"],
                                  error=str(e)[:100])
                continue
        return self._template_generate(finding)

    async def _call_provider(self, provider: dict, finding) -> str:
        """Call a specific LLM provider. Returns text or raises."""
        user_prompt = self._build_prompt(finding)

        if provider["name"] == "ollama":
            return await self._call_ollama(provider, user_prompt)
        elif provider["name"] == "dashscope":
            return await self._call_dashscope(provider, user_prompt)
        else:
            return await self._call_openai_compatible(provider, user_prompt)

    def _build_prompt(self, finding) -> str:
        """Build the user prompt for the LLM."""
        return f"""Generate an institutional intelligence report for this Mantle on-chain anomaly.
The reader is a portfolio manager at a professional crypto fund making real capital decisions.

Anomaly Type: {finding.anomaly_type}
Block Height: {finding.block_height}
Timestamp: {finding.timestamp}
Confidence: {finding.confidence * 100:.1f}%
Detection Method: {finding.method}
Observation: {getattr(finding, 'investment_signal', 'N/A')}
Affected Protocols: {getattr(finding, 'affected_protocols', [])}
Lead Time (blocks): {getattr(finding, 'lead_time_blocks', 0)}

Raw Description: {finding.description}

Raw Metrics: {json.dumps(finding.raw_metrics, indent=2)}

Large Transfers Involved: {json.dumps(finding.large_transfers[:3], indent=2) if finding.large_transfers else 'None'}

Write a 3-5 sentence investment intelligence report. Structure:
1. The single most actionable insight (lead with specific USD amounts and protocol names)
2. What this pattern historically precedes on Mantle (with probability if known)
3. Specific action recommendation with time window
4. End with: "Signal Tier: WATCH / ALERT / HIGH-PRIORITY INVESTIGATION"

Name specific Mantle protocols: Merchant Moe, Lendle, Agni Finance, mETH, FusionX, Aurelius."""

    async def _call_ollama(self, provider: dict, prompt: str) -> str:
        """Call local Ollama API."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                provider["url"],
                json={
                    "model": provider["model"],
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["message"]["content"]

        header = f"🤖 AI INTEL [{provider['model']}] — Local LLM\n\n"
        return header + text.strip()

    async def _call_openai_compatible(self, provider: dict, prompt: str) -> str:
        """Call OpenAI-compatible API (Groq, OpenRouter, etc.)."""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json",
        }
        if provider["name"] == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/sodiq-code/mantle-intel-agent"
            headers["X-Title"] = "Mantle Intel Agent"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                provider["url"],
                headers=headers,
                json={
                    "model": provider["model"],
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 350,
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]

        header = f"🤖 AI INTEL [{provider['name']}/{provider['model']}]\n\n"
        return header + text.strip()

    async def _call_dashscope(self, provider: dict, prompt: str) -> str:
        """Call legacy DashScope API (kept for backward compat)."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                provider["url"],
                headers={
                    "Authorization": f"Bearer {provider['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": provider["model"],
                    "input": {
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ]
                    },
                    "parameters": {
                        "result_format": "message",
                        "max_tokens": 350,
                        "temperature": 0.2,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["output"]["choices"][0]["message"]["content"]

        header = f"🤖 AI INTEL [{provider['name']}/{provider['model']}]\n\n"
        return header + text.strip()

    def _template_generate(self, finding) -> str:
        """Enhanced template-based insight generation (always works)."""
        m = finding.raw_metrics or {}
        template = INSIGHT_TEMPLATE.get(finding.anomaly_type, DEFAULT_TEMPLATE)

        value_usd = m.get("total_usd", 0)
        if value_usd == 0 and finding.large_transfers:
            value_usd = sum(t.get("value_usd", 0) for t in finding.large_transfers)

        protocol = "Mantle DeFi"
        if finding.large_transfers:
            label_to = finding.large_transfers[0].get("label_to", "unknown")
            if label_to != "unknown":
                protocol = label_to

        wallet_count = m.get("wallet_count", 0)
        avg_per_wallet = m.get("avg_per_wallet", value_usd / max(wallet_count, 1))

        try:
            return template.format(
                block_height=finding.block_height,
                description=finding.description,
                confidence_pct=int(finding.confidence * 100),
                anomaly_type=finding.anomaly_type,
                total_usd=value_usd,
                value_usd=value_usd,
                protocol=protocol,
                protocols_hit=m.get("protocols_hit", len(getattr(finding, "affected_protocols", []))),
                transfer_count=m.get("transfer_count", len(finding.large_transfers)),
                wallet_count=wallet_count,
                avg_per_wallet=avg_per_wallet,
                zscore=m.get("zscore", "N/A"),
                mean_tx=m.get("mean_tx", 65),
                tx_count=m.get("tx_count", 0),
                isolation_score=m.get("isolation_score", "N/A"),
                depeg_bps=m.get("depeg_bps", 0),
                depeg_pct=m.get("depeg_pct", 0.0),
                at_risk_usd=m.get("at_risk_usd", 0),
                r0_delta_pct=m.get("r0_delta_pct", 0.0),
                pool_usd=m.get("pool_usd", 0),
                investment_signal=getattr(finding, "investment_signal", "Monitor for follow-on activity."),
            )
        except KeyError as e:
            return DEFAULT_TEMPLATE.format(
                block_height=finding.block_height,
                description=finding.description,
                confidence_pct=int(finding.confidence * 100),
                anomaly_type=finding.anomaly_type,
                investment_signal=getattr(finding, "investment_signal", ""),
            )

    def format_telegram_alert(self, finding, insight_text: str) -> str:
        """Format for Telegram."""
        return insight_text

    def format_dashboard_card(self, finding, insight_text: str) -> dict:
        """Format for web dashboard JSON — v4.0 includes provider info."""
        return {
            "id": finding.finding_id,
            "type": finding.anomaly_type,
            "block": finding.block_height,
            "timestamp": finding.timestamp,
            "confidence": finding.confidence,
            "confidence_pct": int(finding.confidence * 100),
            "hash": finding.sha256_hash(),
            "hex_hash": finding.hex_bytes32(),
            "insight": insight_text,
            "insight_provider": self._active_provider["name"] if self._active_provider else "template",
            "raw_metrics": finding.raw_metrics,
            "method": finding.method,
            "transfers": finding.large_transfers[:5],
            "investment_signal": getattr(finding, "investment_signal", ""),
            "lead_time_blocks": getattr(finding, "lead_time_blocks", 0),
            "lead_time_hours": round(getattr(finding, "lead_time_blocks", 0) * 12 / 3600, 1),
            "affected_protocols": getattr(finding, "affected_protocols", []),
            "signal_tier": self._get_signal_tier(finding),
            "reasons": self._extract_evidence(finding)
        }

    def _extract_evidence(self, finding) -> list[str]:
        """Convert finding metrics into human-readable evidence points."""
        ev = []
        m = finding.raw_metrics or {}
        
        # Method / Base evidence
        if finding.method == "zscore":
            if "tx_count" in m and "mean_tx" in m:
                ev.append(f"Transaction count ({m['tx_count']}) exceeded recent baseline ({m['mean_tx']:.0f})")
            if "value_mnt" in m and "mean_val_mnt" in m:
                ev.append(f"MNT transfer value ({m['value_mnt']:,.0f}) exceeded baseline ({m['mean_val_mnt']:,.0f})")
        elif finding.method == "isolation_forest":
            ev.append("Multivariate outlier detected (tx volume + value + wallet diversity)")
        elif finding.method == "pattern_match":
            if finding.anomaly_type == "smart_money_inflow":
                ev.append(f"{m.get('wallet_count', 2)} unlabeled wallets accumulated positions")
            else:
                ev.append(f"{m.get('transfer_count', 2)} large institutional transfers detected")
        elif finding.method == "meth_oracle":
            ev.append(f"Oracle price deviation of {m.get('depeg_bps', 0)} bps")
        elif finding.method == "reserve_analysis":
            ev.append(f"Liquidity pool reserve shifted by {m.get('r0_delta_pct', 0)}%")
        elif finding.method == "cross_protocol":
            ev.append(f"Simultaneous deployment across {m.get('protocols_hit', 3)} protocols")
            
        # Z-score context
        z = m.get("zscore")
        if z and abs(z) >= 3.0:
            ev.append(f"Statistically significant spike (z={abs(z):.2f}σ)")
            
        if not ev:
            ev.append("Baseline Anomaly")
            
        return ev

    def _get_signal_tier(self, finding) -> str:
        """Map anomaly type + confidence to signal tier for dashboard."""
        high_priority = {"meth_depeg", "cross_protocol_anomaly", "multivariate_anomaly", "whale_accumulation"}
        medium_priority = {"smart_money_inflow", "value_spike", "whale_distribution", "liquidity_imbalance"}

        if finding.anomaly_type in high_priority and finding.confidence >= 0.85:
            return "HIGH-PRIORITY INVESTIGATION"
        elif finding.anomaly_type in high_priority or finding.anomaly_type in medium_priority:
            return "ANOMALY DETECTED - Awaiting confirmation"
        else:
            return "ANOMALY DETECTED - Awaiting confirmation"
