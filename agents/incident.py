from datetime import datetime, timezone
from typing import Dict, List

# Path for persisting incident counter across pipeline restarts
_INCIDENT_COUNTER_PATH = "data/incident_counter.txt"


class IncidentState:
    OPENED = "🟡 Incident Opened"
    ESCALATED = "🟠 Incident Escalated"
    CRITICAL = "🔴 Incident Critical"
    RESOLVED = "✅ Incident Resolved"


class IncidentManager:
    """
    State tracker to aggregate anomaly findings into ongoing incidents
    to prevent alert storms on bots.

    v5: Persistent, unique incident IDs.
    - IDs follow format: INC-YYYYMMDD-NNNN (e.g., INC-20260721-0001)
    - Counter persists to data/incident_counter.txt across pipeline restarts
    - Each new pipeline run continues from the last known counter

    v4: Signal Types vs Evidence Items distinction.
    - signal_type_count = len(anomaly_types) → distinct detectors that fired
    - evidence = deduplicated, impact-sorted summary (no repeated triggers)
    - occurrences = total findings (internal, drives state escalation)

    Composite Confidence Aggregation Rule:
    - For composite incidents, confidence = max(detector confidences).
      Rationale: each detector independently validates the anomaly;
      their agreement strengthens the signal but the most confident
      detector sets the ceiling.
    - Escalation: occurrences ≥ 3 → Escalated, ≥ 5 → Critical.
    """

    # How close in blocks do two findings need to be to belong to the same incident?
    BLOCK_PROXIMITY_THRESHOLD = 10

    def __init__(self, resolution_threshold_blocks: int = 60):
        self.resolution_threshold_blocks = resolution_threshold_blocks
        self.active_incidents: Dict[str, dict] = {}
        self._load_counter()

    def _load_counter(self):
        """Load incident counter from persistent storage.

        The file stores: date_str daily_counter total_counter
        If the date matches today, continue from daily_counter.
        If a new day, reset daily counter but keep total incrementing.
        """
        import os
        self.incident_counter = 0
        self._counter_date = datetime.now(tz=timezone.utc).strftime("%Y%m%d")

        try:
            if os.path.exists(_INCIDENT_COUNTER_PATH):
                with open(_INCIDENT_COUNTER_PATH) as f:
                    line = f.read().strip()
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            stored_date = parts[0]
                            stored_count = int(parts[1])
                            if stored_date == self._counter_date:
                                self.incident_counter = stored_count
        except (ValueError, OSError):
            self.incident_counter = 0

    def _save_counter(self):
        """Persist incident counter so next pipeline run continues from it."""
        import os
        try:
            os.makedirs(os.path.dirname(_INCIDENT_COUNTER_PATH), exist_ok=True)
            with open(_INCIDENT_COUNTER_PATH, "w") as f:
                f.write(f"{self._counter_date} {self.incident_counter}")
        except OSError:
            pass  # Non-critical — IDs may reset on next run

    def _generate_incident_id(self) -> str:
        """Generate a unique incident ID: INC-YYYYMMDD-NNNN."""
        self.incident_counter += 1
        self._save_counter()
        date_str = self._counter_date
        return f"INC-{date_str}-{self.incident_counter:04d}"

    def process_finding(self, dashboard_card: dict, current_block: int) -> dict | None:
        """
        Process a new finding. Returns an Incident update dict if a bot notification
        should be sent, otherwise returns None.

        v3: Findings within BLOCK_PROXIMITY_THRESHOLD blocks of each other
        are grouped into the same incident regardless of anomaly type.
        So tx_spike + value_spike + multivariate on the same block = 1 incident.

        DEDUPLICATION: If the same anomaly_type already exists in a proximate
        incident, the finding is absorbed as evidence (not a separate signal)
        to prevent duplicate incidents like two multivariate_anomaly for the
        same block.
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
        incident_id = self._generate_incident_id()
        anomaly_types = {anomaly_type}
        insight = dashboard_card.get("insight", "")

        incident = {
            "id": incident_id,
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
        self.active_incidents[incident_id] = incident
        return self._format_incident_notification(incident)

    def _merge_finding(self, incident: dict, dashboard_card: dict,
                       current_block: int) -> dict | None:
        """Merge a new finding into an existing incident.

        DEDUPLICATION: The anomaly_types set naturally deduplicates —
        adding an existing type is a no-op. Occurrences always increment
        because they track total findings (driving state escalation),
        while anomaly_types tracks distinct signal types (driving the
        composite label and signals list).
        """
        anomaly_type = dashboard_card.get("type", "unknown")
        type_is_new = anomaly_type not in incident["anomaly_types"]

        # Add this anomaly type to the set (no-op if already present)
        incident["anomaly_types"].add(anomaly_type)
        # Update primary type label to show it's composite
        if len(incident["anomaly_types"]) > 1:
            incident["type"] = "composite"
            # Update insight_sample to reflect composite nature
            new_insight = dashboard_card.get("insight", "")
            if new_insight and type_is_new:
                incident["insight_sample"] = self._build_composite_insight(
                    incident, anomaly_type, new_insight)

        incident["latest_block"] = current_block
        # Always increment — occurrences drives state escalation
        # (anomaly_types set handles dedup for signal labels)
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

    def _build_composite_insight(self, incident: dict, new_type: str,
                                 new_insight: str) -> str:
        """Build a composite insight summary when multiple signals merge."""
        # Collect all anomaly type labels
        all_types = incident.get("anomaly_types", set())
        type_labels = sorted(
            t.replace("_", " ").title() for t in all_types if t)

        # Always rebuild from scratch using the full set of types
        # This ensures consistency regardless of merge order
        parts = ["Composite on-chain anomaly detected. Multiple signals fired:"]
        for label in type_labels:
            parts.append(f"• {label}")

        # Append any additional insight text if meaningful
        if new_insight and len(new_insight) > 50:
            truncated = (new_insight[:200] + "..."
                         if len(new_insight) > 200 else new_insight)
            parts.append(truncated)

        return "\n".join(parts)

    def _extract_zscore(self, dashboard_card: dict) -> float | None:
        metrics = dashboard_card.get("raw_metrics", {})
        if not metrics:
            return None
        return metrics.get("zscore")

    def _summarize_evidence(self, incident: dict) -> list[str]:
        """Build deduplicated, impact-sorted evidence from incident findings.

        Instead of listing every raw evidence string (which produces
        duplicates when the same detector fires multiple times), this
        method processes the raw findings to extract peak metrics per
        detector type and sorts by impact.

        Impact order: Z-score → value → liquidity → multivariate → tx count
        """
        findings = incident.get("findings", [])
        if not findings:
            return ["Baseline Anomaly"]

        peak_zscore = 0.0
        peak_tx_count = 0
        baseline_tx = 0
        peak_value = 0
        baseline_value = 0
        has_liquidity = False
        liquidity_pct = 0
        has_multivariate = False
        has_smart_money = False
        sm_detail = ""
        has_whale = False
        whale_detail = ""
        has_depeg = False
        depeg_bps = 0

        for f in findings:
            m = f.get("raw_metrics", {}) or {}

            # Track peak Z-score across ALL findings
            z = m.get("zscore")
            if z and abs(z) >= 3.0 and abs(z) > peak_zscore:
                peak_zscore = abs(z)

            atype = f.get("type", "")
            if atype == "tx_spike":
                tx = m.get("tx_count", 0)
                if tx > peak_tx_count:
                    peak_tx_count = tx
                    baseline_tx = int(m.get("mean_tx", 1))

            elif atype == "value_spike":
                val = m.get("value_mnt", 0)
                if val > peak_value:
                    peak_value = val
                    baseline_value = int(m.get("mean_val_mnt", 1))

            elif atype == "liquidity_imbalance":
                has_liquidity = True
                delta = abs(m.get("r0_delta_pct", 0))
                if delta > liquidity_pct:
                    liquidity_pct = delta

            elif atype == "multivariate_anomaly":
                has_multivariate = True

            elif atype == "smart_money_inflow":
                has_smart_money = True
                wc = m.get("wallet_count", 0)
                if wc:
                    sm_detail = f"{wc} unlabeled wallets accumulated positions"

            elif atype in ("whale_accumulation", "whale_distribution"):
                has_whale = True
                tc = m.get("transfer_count", 0)
                if tc:
                    whale_detail = f"{tc} large transfers detected"

            elif atype == "meth_depeg":
                has_depeg = True
                bps = m.get("depeg_bps", 0)
                if abs(bps) > abs(depeg_bps):
                    depeg_bps = bps

        # Build evidence sorted by impact
        evidence = []

        # 1. Peak Z-score (strongest statistical signal)
        if peak_zscore > 0:
            evidence.append(
                f"Peak statistical deviation: z = {peak_zscore:.2f}σ")

        # 2. Value spike (largest financial impact)
        if peak_value > 0:
            evidence.append(
                f"MNT transfer value peaked at {peak_value:,.0f} "
                f"(baseline: {baseline_value:,.0f})")

        # 3. Liquidity imbalance (protocol risk)
        if has_liquidity:
            evidence.append(f"Liquidity reserve deviation: {liquidity_pct}%")

        # 4. Multivariate confirmation (corroborating signal)
        if has_multivariate:
            evidence.append(
                "Multivariate anomaly confirmed "
                "(tx volume + value + wallet diversity)")

        # 5. Transaction volume (operational signal)
        if peak_tx_count > 0:
            evidence.append(
                f"Transaction volume peaked at {peak_tx_count} "
                f"vs baseline {baseline_tx}")

        # 6. Smart money (intelligence signal)
        if has_smart_money:
            evidence.append(sm_detail or "Smart money inflow detected")

        # 7. Whale activity
        if has_whale:
            evidence.append(whale_detail or "Large whale activity detected")

        # 8. mETH depeg
        if has_depeg:
            evidence.append(
                f"mETH/ETH oracle deviation: {abs(depeg_bps)} bps "
                f"({abs(depeg_bps) / 100:.2f}% from peg)")

        if not evidence:
            evidence = ["Baseline Anomaly"]

        return evidence

    def _format_incident_notification(self, incident: dict) -> dict:
        """
        Returns an object designed to be consumed by the Bot layer.
        For composite incidents, shows all anomaly types involved.

        v4: Distinguishes signal_type_count (distinct detectors) from
        occurrences (total findings, internal). Evidence is deduplicated
        and impact-sorted via _summarize_evidence().
        """
        duration = (incident["latest_block"] - incident["start_block"]) + 1
        anomaly_types = incident.get("anomaly_types", {incident["type"]})
        is_composite = len(anomaly_types) > 1

        # Build deduplicated, impact-sorted evidence
        evidence = self._summarize_evidence(incident)

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
            "signal_type_count": len(anomaly_types),
            "peak_confidence": incident["peak_confidence"],
            "peak_zscore": incident["peak_zscore"],
            "insight_sample": incident["insight_sample"],
            "latest_hash": incident["findings"][-1].get("hash") if incident["findings"] else None,
            "timestamp": incident["latest_time"],
            "evidence": evidence,
            "detectors": list(incident.get("reasons", []))
        }
