from typing import Dict, List


class IncidentState:
    OPENED = "🟡 Incident Opened"
    ESCALATED = "🟠 Incident Escalated"
    CRITICAL = "🔴 Incident Critical"
    RESOLVED = "✅ Incident Resolved"


class IncidentManager:
    """
    State tracker to aggregate anomaly findings into ongoing incidents
    to prevent alert storms on bots.

    v2: Groups findings by block proximity instead of anomaly type.
    Multiple anomaly types on the same block = ONE incident with all signals.
    Users see ONE notification per event, not 4.
    """

    # How close in blocks do two findings need to be to belong to the same incident?
    BLOCK_PROXIMITY_THRESHOLD = 10

    def __init__(self, resolution_threshold_blocks: int = 60):
        self.resolution_threshold_blocks = resolution_threshold_blocks
        self.active_incidents: Dict[str, dict] = {}
        self.incident_counter = 0

    def process_finding(self, dashboard_card: dict, current_block: int) -> dict | None:
        """
        Process a new finding. Returns an Incident update dict if a bot notification
        should be sent, otherwise returns None.

        v2: Findings within BLOCK_PROXIMITY_THRESHOLD blocks of each other
        are grouped into the same incident regardless of anomaly type.
        So tx_spike + value_spike + multivariate on the same block = 1 incident.
        """
        anomaly_type = dashboard_card.get("type", "unknown")
        finding_block = dashboard_card.get("block", current_block)

        # Find an existing incident that's close in block proximity
        matching_incident_key = self._find_proximate_incident(finding_block)

        if matching_incident_key:
            # Merge into existing incident
            incident = self.active_incidents[matching_incident_key]
            return self._merge_finding(incident, dashboard_card, current_block)
        else:
            # Create new incident
            return self._create_incident(anomaly_type, dashboard_card, current_block)

    def _find_proximate_incident(self, block: int) -> str | None:
        """Find an active incident whose blocks are within proximity threshold."""
        for key, incident in self.active_incidents.items():
            latest = incident["latest_block"]
            if abs(block - latest) <= self.BLOCK_PROXIMITY_THRESHOLD:
                return key
        return None

    def _create_incident(self, anomaly_type: str, dashboard_card: dict,
                         current_block: int) -> dict:
        """Create a brand new incident from a single finding."""
        self.incident_counter += 1
        anomaly_types = {anomaly_type}
        insight = dashboard_card.get("insight", "")

        incident = {
            "id": self.incident_counter,
            "type": anomaly_type,  # primary type (first finding)
            "anomaly_types": anomaly_types,  # all types involved
            "start_block": current_block,
            "latest_block": current_block,
            "occurrences": 1,
            "peak_confidence": dashboard_card.get("confidence_pct", 0),
            "peak_zscore": self._extract_zscore(dashboard_card),
            "state": IncidentState.OPENED,
            "last_notified_state": IncidentState.OPENED,
            "last_notified_occurrences": 1,
            "findings": [dashboard_card],
            "insight_sample": insight,
            "reasons": set(dashboard_card.get("reasons", [])),
            "start_time": dashboard_card.get("timestamp", "N/A"),
            "latest_time": dashboard_card.get("timestamp", "N/A"),
        }
        # Use incident ID as key so multiple anomaly types can merge
        key = f"incident_{self.incident_counter}"
        self.active_incidents[key] = incident
        return self._format_incident_notification(incident)

    def _merge_finding(self, incident: dict, dashboard_card: dict,
                       current_block: int) -> dict | None:
        """Merge a new finding into an existing incident."""
        anomaly_type = dashboard_card.get("type", "unknown")

        # Add this anomaly type to the set
        incident["anomaly_types"].add(anomaly_type)
        # Update primary type label to show it's composite
        if len(incident["anomaly_types"]) > 1:
            incident["type"] = "composite"
            # Update insight_sample to reflect composite nature
            new_insight = dashboard_card.get("insight", "")
            if new_insight:
                incident["insight_sample"] = self._build_composite_insight(
                    incident, anomaly_type, new_insight)

        incident["latest_block"] = current_block
        incident["occurrences"] += 1
        incident["findings"].append(dashboard_card)
        incident["latest_time"] = dashboard_card.get(
            "timestamp", incident["latest_time"])
        for r in dashboard_card.get("reasons", []):
            incident["reasons"].add(r)

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
        # On first merge (occurrences=2), notify once to update with composite info
        # After that, only notify on escalation or every 3 additional occurrences
        should_notify = False
        if new_state != incident["last_notified_state"]:
            should_notify = True
        elif incident["occurrences"] == 2:
            # First merge — update the initial alert with composite info
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

        for key, incident in self.active_incidents.items():
            if (current_block - incident["latest_block"]) >= self.resolution_threshold_blocks:
                incident["state"] = IncidentState.RESOLVED
                resolved_notifications.append(
                    self._format_incident_notification(incident))
                to_remove.append(key)

        for key in to_remove:
            del self.active_incidents[key]

        return resolved_notifications

    def _build_composite_insight(self, incident: dict,
                               new_type: str, new_insight: str) -> str:
        """Build a composite insight summary when multiple signals merge."""
        existing = incident.get("insight_sample", "")
        # Extract the short anomaly label
        type_label = new_type.replace("_", " ").title()
        
        # If this is the first merge (becoming composite), prepend composite header
        if not existing.startswith("Composite"):
            # First merge — restructure: existing insight + new signal
            parts = [f"Composite on-chain anomaly detected. "
                     f"Multiple signals fired:"]
            # Add first signal type
            first_type = list(incident.get("anomaly_types", set()))[0] if incident.get("anomaly_types") else "anomaly"
            first_label = first_type.replace("_", " ").title()
            parts.append(f"• {first_label}")
            parts.append(f"• {type_label}")
            return "\n".join(parts)
        else:
            # Subsequent merge — just append the new signal type
            if f"• {type_label}" not in existing:
                existing += f"\n• {type_label}"
            return existing

    def _extract_zscore(self, dashboard_card: dict) -> float | None:
        metrics = dashboard_card.get("raw_metrics", {})
        if not metrics:
            return None
        return metrics.get("zscore")

    def _format_incident_notification(self, incident: dict) -> dict:
        """
        Returns an object designed to be consumed by the Bot layer.
        For composite incidents, shows all anomaly types involved.
        """
        duration = (incident["latest_block"] - incident["start_block"]) + 1
        anomaly_types = incident.get("anomaly_types", {incident["type"]})
        is_composite = len(anomaly_types) > 1

        return {
            "incident_id": incident["id"],
            "type": "composite" if is_composite else incident["type"],
            "anomaly_types": sorted(anomaly_types),
            "is_composite": is_composite,
            "state": incident["state"],
            "start_block": incident["start_block"],
            "latest_block": incident["latest_block"],
            "duration_blocks": duration,
            "occurrences": incident["occurrences"],
            "peak_confidence": incident["peak_confidence"],
            "peak_zscore": incident["peak_zscore"],
            "insight_sample": incident["insight_sample"],
            "latest_hash": incident["findings"][-1].get("hash") if incident["findings"] else None,
            "timestamp": incident["latest_time"],
            "detectors": list(incident.get("reasons", []))
        }
