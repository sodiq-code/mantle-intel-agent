import time
from typing import Dict, List, Any

class IncidentState:
    OPENED = "🟡 Incident Opened"
    ESCALATED = "🟠 Incident Escalated"
    CRITICAL = "🔴 Incident Critical"
    RESOLVED = "✅ Incident Resolved"


class IncidentManager:
    """
    State tracker to aggregate anomaly findings into ongoing incidents
    to prevent alert storms on bots.
    """
    def __init__(self, resolution_threshold_blocks: int = 60):
        self.resolution_threshold_blocks = resolution_threshold_blocks
        self.active_incidents: Dict[str, dict] = {}
        self.incident_counter = 0

    def process_finding(self, dashboard_card: dict, current_block: int) -> dict | None:
        """
        Process a new finding. Returns an Incident update dict if a bot notification
        should be sent, otherwise returns None (if it's just a minor state update).
        """
        anomaly_type = dashboard_card.get("type", "unknown")
        
        # Check if we have an active incident of this type
        incident = self.active_incidents.get(anomaly_type)
        
        if not incident:
            # Create new incident
            self.incident_counter += 1
            incident = {
                "id": self.incident_counter,
                "type": anomaly_type,
                "start_block": current_block,
                "latest_block": current_block,
                "occurrences": 1,
                "peak_confidence": dashboard_card.get("confidence_pct", 0),
                "peak_zscore": self._extract_zscore(dashboard_card),
                "state": IncidentState.OPENED,
                "last_notified_state": IncidentState.OPENED,
                "last_notified_occurrences": 1,
                "findings": [dashboard_card],
                "insight_sample": dashboard_card.get("insight", "")
            }
            self.active_incidents[anomaly_type] = incident
            return self._format_incident_notification(incident)

        # Incident is active, update stats
        incident["latest_block"] = current_block
        incident["occurrences"] += 1
        incident["findings"].append(dashboard_card)
        
        conf = dashboard_card.get("confidence_pct", 0)
        if conf > incident["peak_confidence"]:
            incident["peak_confidence"] = conf
            
        zscore = self._extract_zscore(dashboard_card)
        if zscore and (not incident["peak_zscore"] or zscore > incident["peak_zscore"]):
            incident["peak_zscore"] = zscore

        # State escalation logic
        new_state = incident["state"]
        if incident["occurrences"] >= 5:
            new_state = IncidentState.CRITICAL
        elif incident["occurrences"] >= 3:
            new_state = IncidentState.ESCALATED
            
        incident["state"] = new_state

        # Determine if we should notify
        # Notify if state escalated, OR if we've had 3 more occurrences since last notification
        should_notify = False
        if new_state != incident["last_notified_state"]:
            should_notify = True
        elif (incident["occurrences"] - incident["last_notified_occurrences"]) >= 3:
            should_notify = True

        if should_notify:
            incident["last_notified_state"] = new_state
            incident["last_notified_occurrences"] = incident["occurrences"]
            return self._format_incident_notification(incident)

        return None

    def check_resolutions(self, current_block: int) -> List[dict]:
        """
        Check all active incidents. If current_block - latest_block > threshold, resolve them.
        Returns a list of incident notification dicts for resolved incidents.
        """
        resolved_notifications = []
        to_remove = []
        
        for atype, incident in self.active_incidents.items():
            if (current_block - incident["latest_block"]) >= self.resolution_threshold_blocks:
                incident["state"] = IncidentState.RESOLVED
                resolved_notifications.append(self._format_incident_notification(incident))
                to_remove.append(atype)
                
        for atype in to_remove:
            del self.active_incidents[atype]
            
        return resolved_notifications

    def _extract_zscore(self, dashboard_card: dict) -> float | None:
        metrics = dashboard_card.get("raw_metrics", {})
        if not metrics:
            return None
        return metrics.get("zscore")

    def _format_incident_notification(self, incident: dict) -> dict:
        """
        Returns an object designed to be consumed by the Bot layer.
        """
        duration = (incident["latest_block"] - incident["start_block"]) + 1
        
        return {
            "incident_id": incident["id"],
            "type": incident["type"],
            "state": incident["state"],
            "start_block": incident["start_block"],
            "latest_block": incident["latest_block"],
            "duration_blocks": duration,
            "occurrences": incident["occurrences"],
            "peak_confidence": incident["peak_confidence"],
            "peak_zscore": incident["peak_zscore"],
            "insight_sample": incident["insight_sample"],
            "latest_hash": incident["findings"][-1].get("hash") if incident["findings"] else None
        }
