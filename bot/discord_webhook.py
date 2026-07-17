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
import urllib.request
import urllib.error
from datetime import datetime, timezone
import structlog

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
CONTRACT = os.getenv("AUDIT_CONTRACT_ADDRESS", "0x7fAb1E37d992109d3aA747703436ff4e261391b7")


class DiscordWebhook:
    """Sends finding alerts to Discord via webhook URL."""

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")
        self.log = logger.bind(component="discord_webhook")

    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("https://discord.com/api/webhooks/"))

    def push(self, incident: dict) -> bool:
        """Send an incident update to Discord. Returns True on success."""
        if not self.is_configured:
            self.log.debug("webhook_not_configured", msg="Set DISCORD_WEBHOOK_URL to enable Discord alerts")
            return False

        try:
            payload = self._build_payload(incident)
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
            self.log.error("discord_webhook_http_error", status=e.code, reason=e.reason)
        except Exception as e:
            self.log.error("discord_webhook_failed", error=str(e))
        return False

    def _build_payload(self, incident: dict) -> dict:
        """Build a Discord webhook payload for an incident update."""
        atype = incident.get("type", "anomaly")
        
        label_map = {
            "whale_accumulation":   "Whale Accumulation",
            "whale_distribution":   "Whale Distribution",
            "smart_money_inflow":   "Smart Money Inflow",
            "tx_spike":             "TX Volume Spike",
            "value_spike":          "Value Spike",
            "multivariate_anomaly": "Multivariate Anomaly",
        }
        
        icon_map = {
            "whale_accumulation":  "🐋",
            "smart_money_inflow":  "🧠",
            "tx_spike":            "📈",
            "value_spike":         "💰",
        }
        
        state = incident.get("state", "🟡 Incident")
        
        color_map = {
            "🟡 Incident Opened":    16776960,  # Yellow
            "🟠 Incident Escalated": 16744192,  # Orange
            "🔴 Incident Critical":  16711680,  # Red
            "✅ Incident Resolved":  3066993,   # Green
        }
        
        icon = icon_map.get(atype, "⚡")
        label = label_map.get(atype, atype.replace("_", " ").title())
        
        conf = incident.get("peak_confidence", 0)
        zscore = incident.get("peak_zscore")
        start = incident.get("start_block", 0)
        latest = incident.get("latest_block", 0)
        dur = incident.get("duration_blocks", 1)
        occ = incident.get("occurrences", 1)
        insight = incident.get("insight_sample", "")
        fhash = incident.get("latest_hash", "")
        timestamp = incident.get("timestamp", "N/A")
        detectors = incident.get("detectors", [])
        
        detectors_str = "\n".join(f"✓ {d}" for d in detectors) if detectors else "✓ Baseline Anomaly"
        
        desc = f"{insight}\n\n**Incident ID:** `{incident.get('incident_id', 'N/A')}`\n**Status:** {state}\n**Detection Confidence:** {conf}% (Anomaly Detection)"
        
        fields = [
            {"name": "Blocks", "value": f"`{start:,}` to `{latest:,}` (Duration: {dur} blocks)", "inline": False},
            {"name": "Occurrences", "value": str(occ), "inline": True},
            {"name": "Timestamp (UTC)", "value": f"`{timestamp}`", "inline": True},
        ]
            
        fields.append({"name": "Evidence", "value": detectors_str, "inline": False})
            
        if fhash:
            fields.append({
                "name": "Latest SHA-256 Hash",
                "value": f"`{fhash[:32]}...`",
                "inline": False
            })

        fields.append({"name": "Contract", "value": f"[{CONTRACT[:10]}...]({EXPLORER}/address/{CONTRACT})", "inline": False})

        return {
            "username": "Mantle Intel Agent",
            "avatar_url": "https://raw.githubusercontent.com/sodiq-code/mantle-intel-agent/main/docs/logo_480.png",
            "embeds": [{
                "title": label,
                "description": insight,
                "color": color,
                "fields": fields,
                "footer": {
                    "text": f"Mantle Intel Agent · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                },
                "url": f"{EXPLORER}/address/{CONTRACT}"
            }]
        }


# ── Singleton ────────────────────────────────────────────────────────────────
_webhook = DiscordWebhook()


def push_incident(incident: dict) -> bool:
    """Module-level helper. Call from pipeline."""
    return _webhook.push(incident)
