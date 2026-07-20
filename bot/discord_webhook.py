"""
Mantle Intel Agent — Discord Webhook Notifier
Sends finding alerts to a Discord channel via webhook URL.
No bot token required — just set DISCORD_WEBHOOK_URL in .env

Usage:
  export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
  The pipeline calls DiscordWebhook.push(finding, insight_text) automatically.
"""
import os
import json
from datetime import datetime, timezone
import structlog

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

import urllib.request
import urllib.error

from config import CONTRACT_ADDRESS

logger = structlog.get_logger(__name__)

ANOMALY_COLORS = {
    "whale_accumulation":   0x22C55E,   # green
    "whale_distribution":   0xEF4444,   # red
    "smart_money_inflow":   0x3B82F6,   # blue
    "tx_spike":             0xF59E0B,   # amber
    "value_spike":          0xA855F7,   # purple
    "multivariate_anomaly": 0x06B6D4,   # cyan
}

ANOMALY_LABELS = {
    "whale_accumulation":   "🐋 Whale Accumulation",
    "whale_distribution":   "⚠️ Whale Distribution",
    "smart_money_inflow":   "🧠 Smart Money Inflow",
    "tx_spike":             "📈 TX Volume Spike",
    "value_spike":          "💰 Value Spike",
    "multivariate_anomaly": "🔍 Multivariate Anomaly",
}

EXPLORER = "https://sepolia.mantlescan.xyz"
CONTRACT = os.getenv("AUDIT_CONTRACT_ADDRESS", CONTRACT_ADDRESS)


class DiscordWebhook:
    """Sends finding alerts to Discord via webhook URL."""

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")
        self.log = logger.bind(component="discord_webhook")

    @property
    def is_configured(self) -> bool:
        return bool(
            self.webhook_url
            and self.webhook_url.startswith("https://discord.com/api/webhooks/")
        )

    def push(self, incident: dict) -> bool:
        """Send an incident update to Discord. Returns True on success.

        Uses httpx (preferred) with fallback to urllib.request.
        httpx handles proxies, redirects, and encoding better than urllib.
        """
        if not self.is_configured:
            self.log.debug(
                "webhook_not_configured",
                msg="Set DISCORD_WEBHOOK_URL to enable Discord alerts")
            return False

        payload = self._build_payload(incident)

        # Prefer httpx — handles proxies/encoding better than urllib
        if _HTTPX_AVAILABLE:
            return self._push_httpx(payload, incident)
        return self._push_urllib(payload, incident)

    def _push_httpx(self, payload: dict, incident: dict) -> bool:
        """Send via httpx (preferred path)."""
        try:
            resp = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            success = resp.status_code in (200, 204)
            if success:
                self.log.info("discord_alert_sent",
                              incident_id=incident.get("incident_id"))
            else:
                self.log.error("discord_webhook_http_error",
                               status=resp.status_code,
                               body=resp.text[:200])
            return success
        except Exception as e:
            self.log.error("discord_webhook_failed", error=str(e))
            # Fallback to urllib
            return self._push_urllib(payload, incident)

    def _push_urllib(self, payload: dict, incident: dict) -> bool:
        """Fallback: send via urllib.request."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                success = resp.status in (200, 204)
                if success:
                    self.log.info("discord_alert_sent",
                                  incident_id=incident.get("incident_id"))
                return success
        except urllib.error.HTTPError as e:
            self.log.error("discord_webhook_http_error",
                           status=e.code, reason=e.reason)
        except Exception as e:
            self.log.error("discord_webhook_failed", error=str(e))
        return False

    def _build_payload(self, incident: dict) -> dict:
        """Build a Discord webhook payload for an incident update."""
        atype = incident.get("type", "anomaly")
        is_composite = incident.get("is_composite", False)
        anomaly_types = incident.get("anomaly_types", [atype])

        label_map = {
            "whale_accumulation":   "Whale Accumulation",
            "whale_distribution":   "Whale Distribution",
            "smart_money_inflow":   "Smart Money Inflow",
            "tx_spike":             "TX Volume Spike",
            "value_spike":          "Value Spike",
            "multivariate_anomaly": "Multivariate Anomaly",
            "liquidity_imbalance":  "Liquidity Imbalance",
            "meth_depeg":           "mETH Depeg",
            "cross_protocol_anomaly": "Cross-Protocol Anomaly",
        }

        state = incident.get("state", "🟡 Incident")

        color_map = {
            "🟡 Incident Opened":    16776960,  # Yellow
            "🟠 Incident Escalated": 16744192,  # Orange
            "🔴 Incident Critical":  16711680,  # Red
            "✅ Incident Resolved":  3066993,   # Green
        }

        # Composite: generic title + signals listed in body (not title)
        signal_labels = []
        if is_composite:
            signal_labels = [label_map.get(t, t.replace("_", " ").title())
                             for t in anomaly_types]
            title = "Composite On-Chain Anomaly"
        else:
            title = label_map.get(atype, atype.replace("_", " ").title())

        conf = incident.get("peak_confidence", 0)
        start = incident.get("start_block", 0)
        latest = incident.get("latest_block", 0)
        dur = incident.get("duration_blocks", 1)
        signal_type_count = incident.get("signal_type_count", 1)
        insight = incident.get("insight_sample", "")
        fhash = incident.get("latest_hash", "")
        timestamp = incident.get("timestamp", "N/A")

        # Use deduplicated, impact-sorted evidence
        evidence_list = incident.get("evidence", [])
        evidence_count = len(evidence_list) or len(incident.get("detectors", []))
        evidence_str = (
            "\n".join(f"✓ {e}" for e in evidence_list)
            if evidence_list else "✓ Baseline Anomaly"
        )

        incident_id = incident.get('incident_id', 'N/A')

        # For composite: list all anomaly types detected
        signals_line = ""
        if is_composite and signal_labels:
            signals_line = f"**Signals Detected:** {', '.join(signal_labels)}\n"

        desc = (
            f"{insight}\n\n{signals_line}"
            f"**Incident ID:** `{incident_id}`\n"
            f"**Status:** {state}\n"
            f"**Detection Confidence:** {conf}% (Anomaly Detection)"
        )

        fields = [
            {"name": "Blocks",
             "value": f"`{start:,}` to `{latest:,}` "
                      f"(Duration: {dur} blocks)",
             "inline": False},
            {"name": "Signal Types", "value": str(signal_type_count), "inline": True},
            {"name": "Evidence Items", "value": str(evidence_count), "inline": True},
            {"name": "Timestamp (UTC)",
             "value": f"`{timestamp}`", "inline": True},
        ]

        fields.append(
            {"name": "Evidence", "value": evidence_str, "inline": False})

        if fhash:
            fields.append({
                "name": "Latest SHA-256 Hash",
                "value": f"`{fhash[:32]}...`",
                "inline": False
            })

        contract_link = (
            f"[{CONTRACT[:10]}...]({EXPLORER}/address/{CONTRACT})")
        fields.append(
            {"name": "Contract", "value": contract_link, "inline": False})

        color = color_map.get(state, 0x6B7280)  # Default gray

        return {
            "username": "Mantle Intel Agent",
            "avatar_url": (
                "https://raw.githubusercontent.com/sodiq-code/"
                "mantle-intel-agent/main/docs/logo_480.png"
            ),
            "embeds": [{
                "title": title,
                "description": desc,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": (
                        f"Mantle Intel Agent · "
                        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                    )
                },
                "url": f"{EXPLORER}/address/{CONTRACT}"
            }]
        }


# ── Singleton ────────────────────────────────────────────────────────────────
_webhook = DiscordWebhook()


def push_incident(incident: dict) -> bool:
    """Module-level helper. Call from pipeline."""
    return _webhook.push(incident)
