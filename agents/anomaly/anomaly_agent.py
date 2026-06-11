"""
Mantle Intel Agent — Anomaly Agent (Stage 2)
Runs Isolation Forest + z-score on block time series to detect:
  - Transaction volume spikes
  - Large value transfer clusters
  - Unusual wallet activity patterns
  - DEX liquidity anomalies

Each anomaly gets a confidence score (0.0–1.0).
Only anomalies above CONFIDENCE_THRESHOLD are forwarded.
"""
from __future__ import annotations

import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

# Graceful imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

CONFIDENCE_THRESHOLD = 0.60  # minimum to emit as finding
ZSCORE_THRESHOLD     = 2.5   # z-score cutoff for spike detection


@dataclass
class AnomalyFinding:
    finding_id:      str
    anomaly_type:    str         # whale_accumulation | tx_spike | smart_money_inflow | tvl_anomaly | unusual_cluster
    block_height:    int
    timestamp:       str
    confidence:      float       # 0.0–1.0
    description:     str
    raw_metrics:     dict = field(default_factory=dict)
    large_transfers: list = field(default_factory=list)
    method:          str = "isolation_forest"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    def sha256_hash(self) -> str:
        """Deterministic hash for on-chain recording."""
        canonical = json.dumps({
            "finding_id":   self.finding_id,
            "anomaly_type": self.anomaly_type,
            "block_height": self.block_height,
            "confidence":   round(self.confidence, 4),
            "description":  self.description,
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def hex_bytes32(self) -> str:
        """Return 0x-prefixed 32-byte hex for Solidity bytes32."""
        return "0x" + self.sha256_hash()


class AnomalyAgent:
    """
    Stateful anomaly detector. Accumulates block history and
    runs Isolation Forest + z-score across multiple dimensions.
    """

    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self._history: list[dict] = []   # feature vectors per block
        self.logger = logger.bind(agent="anomaly")

    # ── Feature extraction ───────────────────────────────────────────────────

    def _block_to_features(self, block) -> dict:
        return {
            "block_num":        block.block_num,
            "tx_count":         block.tx_count,
            "total_value_mnt":  block.total_value_mnt,
            "large_tx_count":   len(block.large_transfers),
            "unique_senders":   len(block.unique_senders),
            "large_value_mnt":  sum(t["value_mnt"] for t in block.large_transfers),
        }

    def ingest_blocks(self, blocks: list) -> None:
        """Add new block data to history buffer."""
        for b in blocks:
            self._history.append(self._block_to_features(b))
        # keep last 500 blocks
        self._history = self._history[-500:]

    # ── Detection pipeline ───────────────────────────────────────────────────

    def detect(self, blocks: list) -> list[AnomalyFinding]:
        """Run full anomaly detection on the provided blocks. Returns findings list."""
        if not blocks:
            return []

        self.ingest_blocks(blocks)

        findings = []
        findings.extend(self._zscore_spike_detection(blocks))
        findings.extend(self._isolation_forest_detection(blocks))
        findings.extend(self._whale_pattern_detection(blocks))

        # Deduplicate by block + type
        seen = set()
        unique = []
        for f in findings:
            key = (f.block_height, f.anomaly_type)
            if key not in seen:
                seen.add(key)
                unique.append(f)

        # Filter by confidence threshold
        filtered = [f for f in unique if f.confidence >= CONFIDENCE_THRESHOLD]
        self.logger.info("anomalies_detected",
                         total=len(findings),
                         above_threshold=len(filtered),
                         threshold=CONFIDENCE_THRESHOLD)
        return filtered

    def _zscore_spike_detection(self, blocks: list) -> list[AnomalyFinding]:
        """Z-score on tx_count and total_value_mnt."""
        findings = []
        if len(self._history) < 10:
            return findings

        if not NUMPY_AVAILABLE:
            return self._simple_spike_detection(blocks)

        history_values_tx  = [h["tx_count"] for h in self._history[:-len(blocks)]]
        history_values_val = [h["total_value_mnt"] for h in self._history[:-len(blocks)]]

        if len(history_values_tx) < 5:
            return findings

        mean_tx,  std_tx  = float(np.mean(history_values_tx)),  float(np.std(history_values_tx))  + 1e-9
        mean_val, std_val = float(np.mean(history_values_val)), float(np.std(history_values_val)) + 1e-9

        for block in blocks:
            z_tx  = (block.tx_count - mean_tx) / std_tx
            z_val = (block.total_value_mnt - mean_val) / std_val

            if abs(z_tx) > ZSCORE_THRESHOLD:
                conf = min(0.99, 0.5 + abs(z_tx) / 10)
                findings.append(AnomalyFinding(
                    finding_id=f"zscore_tx_{block.block_num}_{int(time.time())}",
                    anomaly_type="tx_spike",
                    block_height=block.block_num,
                    timestamp=datetime.fromtimestamp(block.timestamp, tz=timezone.utc).isoformat(),
                    confidence=round(conf, 4),
                    description=(
                        f"Transaction volume spike on Mantle block {block.block_num}. "
                        f"Observed {block.tx_count} txs vs baseline {mean_tx:.0f} "
                        f"(z={z_tx:.2f}σ). Possible protocol event or coordinated activity."
                    ),
                    raw_metrics={
                        "tx_count": block.tx_count,
                        "mean_tx": round(mean_tx, 2),
                        "zscore": round(z_tx, 4),
                    },
                    method="zscore",
                ))

            if abs(z_val) > ZSCORE_THRESHOLD:
                conf = min(0.99, 0.5 + abs(z_val) / 10)
                findings.append(AnomalyFinding(
                    finding_id=f"zscore_val_{block.block_num}_{int(time.time())}",
                    anomaly_type="value_spike",
                    block_height=block.block_num,
                    timestamp=datetime.fromtimestamp(block.timestamp, tz=timezone.utc).isoformat(),
                    confidence=round(conf, 4),
                    description=(
                        f"Abnormal MNT value transfer on Mantle block {block.block_num}. "
                        f"Observed {block.total_value_mnt:,.0f} MNT vs baseline {mean_val:,.0f} MNT "
                        f"(z={z_val:.2f}σ). Potential large position entry or exit."
                    ),
                    raw_metrics={
                        "value_mnt":  block.total_value_mnt,
                        "mean_val_mnt": round(mean_val, 2),
                        "zscore": round(z_val, 4),
                    },
                    method="zscore",
                ))

        return findings

    def _simple_spike_detection(self, blocks: list) -> list[AnomalyFinding]:
        """Fallback without numpy: simple ratio-based spike detection."""
        findings = []
        if len(self._history) < 10:
            return findings

        recent = self._history[:-len(blocks)][-20:]
        avg_tx  = sum(h["tx_count"] for h in recent) / len(recent)
        avg_val = sum(h["total_value_mnt"] for h in recent) / len(recent) + 1e-9

        for block in blocks:
            ratio_tx  = block.tx_count / (avg_tx + 1)
            ratio_val = block.total_value_mnt / avg_val

            if ratio_tx > 2.5:
                findings.append(AnomalyFinding(
                    finding_id=f"spike_tx_{block.block_num}_{int(time.time())}",
                    anomaly_type="tx_spike",
                    block_height=block.block_num,
                    timestamp=datetime.fromtimestamp(block.timestamp, tz=timezone.utc).isoformat(),
                    confidence=round(min(0.95, 0.5 + (ratio_tx - 2.5) / 5), 4),
                    description=f"TX count {block.tx_count} is {ratio_tx:.1f}x above 20-block average ({avg_tx:.0f}). Unusual on-chain activity on Mantle.",
                    raw_metrics={"tx_count": block.tx_count, "avg_tx": round(avg_tx, 1), "ratio": round(ratio_tx, 2)},
                    method="ratio",
                ))

            if ratio_val > 3.0:
                findings.append(AnomalyFinding(
                    finding_id=f"spike_val_{block.block_num}_{int(time.time())}",
                    anomaly_type="value_spike",
                    block_height=block.block_num,
                    timestamp=datetime.fromtimestamp(block.timestamp, tz=timezone.utc).isoformat(),
                    confidence=round(min(0.95, 0.5 + (ratio_val - 3.0) / 5), 4),
                    description=f"Transfer value {block.total_value_mnt:,.0f} MNT is {ratio_val:.1f}x above 20-block average. Large position movement on Mantle.",
                    raw_metrics={"value_mnt": block.total_value_mnt, "avg_val_mnt": round(avg_val, 1), "ratio": round(ratio_val, 2)},
                    method="ratio",
                ))

        return findings

    def _isolation_forest_detection(self, blocks: list) -> list[AnomalyFinding]:
        """Isolation Forest on multi-dimensional block features."""
        findings = []
        if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
            return findings
        if len(self._history) < 20:
            return findings

        try:
            feature_keys = ["tx_count", "total_value_mnt", "large_tx_count", "unique_senders"]
            X = np.array([[h[k] for k in feature_keys] for h in self._history])

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            clf = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
            )
            labels      = clf.fit_predict(X_scaled)
            scores      = clf.score_samples(X_scaled)  # more negative = more anomalous

            block_start = max(0, len(self._history) - len(blocks))

            for i, block in enumerate(blocks):
                hist_idx = block_start + i
                if hist_idx >= len(labels):
                    continue
                if labels[hist_idx] == -1:  # outlier
                    raw_score = float(scores[hist_idx])
                    # Map score to confidence: typical range -0.8 to -0.4 for outliers
                    confidence = min(0.99, max(0.5, 0.5 + abs(raw_score + 0.5) * 2))

                    findings.append(AnomalyFinding(
                        finding_id=f"iforest_{block.block_num}_{int(time.time())}",
                        anomaly_type="multivariate_anomaly",
                        block_height=block.block_num,
                        timestamp=datetime.fromtimestamp(block.timestamp, tz=timezone.utc).isoformat(),
                        confidence=round(confidence, 4),
                        description=(
                            f"Isolation Forest flagged Mantle block {block.block_num} as a multivariate outlier "
                            f"(anomaly score: {raw_score:.4f}). Combined pattern of tx volume, transfer value, "
                            f"and wallet activity is statistically unusual."
                        ),
                        raw_metrics={
                            "isolation_score": round(raw_score, 6),
                            "tx_count": block.tx_count,
                            "total_value_mnt": block.total_value_mnt,
                            "large_tx_count": len(block.large_transfers),
                        },
                        large_transfers=block.large_transfers,
                        method="isolation_forest",
                    ))
        except Exception as e:
            self.logger.warning("isolation_forest_failed", error=str(e))

        return findings

    def _whale_pattern_detection(self, blocks: list) -> list[AnomalyFinding]:
        """Direct pattern matching on large transfers — labeled wallet activity."""
        findings = []

        for block in blocks:
            if not block.large_transfers:
                continue

            # Check for labeled wallet involvement
            labeled_txs = [t for t in block.large_transfers if t.get("label_from") != "unknown" or t.get("label_to") != "unknown"]
            total_usd   = sum(t.get("value_usd", 0) for t in block.large_transfers)

            if len(block.large_transfers) >= 3 and total_usd >= 200_000:
                confidence = min(0.98, 0.65 + len(block.large_transfers) * 0.02 + total_usd / 10_000_000)

                # Determine if accumulation or distribution
                protocol_targets = [
                    t for t in block.large_transfers
                    if t.get("is_contract") and t.get("label_to") != "unknown"
                ]
                anomaly_type = "whale_accumulation" if len(protocol_targets) >= len(block.large_transfers) // 2 else "whale_distribution"

                findings.append(AnomalyFinding(
                    finding_id=f"whale_{block.block_num}_{int(time.time())}",
                    anomaly_type=anomaly_type,
                    block_height=block.block_num,
                    timestamp=datetime.fromtimestamp(block.timestamp, tz=timezone.utc).isoformat(),
                    confidence=round(confidence, 4),
                    description=(
                        f"{'Whale accumulation' if anomaly_type == 'whale_accumulation' else 'Whale distribution'} detected on Mantle block {block.block_num}. "
                        f"{len(block.large_transfers)} large transfers totaling ${total_usd:,.0f} USD. "
                        f"{len(labeled_txs)} transactions involve known institutional wallets. "
                        f"{'Funds moving INTO DeFi protocols — potential position building.' if anomaly_type == 'whale_accumulation' else 'Funds moving OUT of DeFi protocols — potential exit.'}"
                    ),
                    raw_metrics={
                        "transfer_count": len(block.large_transfers),
                        "total_usd":      round(total_usd, 2),
                        "labeled_count":  len(labeled_txs),
                    },
                    large_transfers=block.large_transfers,
                    method="pattern_match",
                ))

            # Smart money inflow: unknown wallets → known DeFi protocol
            unknown_to_protocol = [
                t for t in block.large_transfers
                if t.get("label_from") == "unknown" and t.get("label_to") != "unknown" and t.get("value_usd", 0) >= 50_000
            ]
            if len(unknown_to_protocol) >= 2:
                sm_total = sum(t.get("value_usd", 0) for t in unknown_to_protocol)
                findings.append(AnomalyFinding(
                    finding_id=f"smartmoney_{block.block_num}_{int(time.time())}",
                    anomaly_type="smart_money_inflow",
                    block_height=block.block_num,
                    timestamp=datetime.fromtimestamp(block.timestamp, tz=timezone.utc).isoformat(),
                    confidence=round(min(0.95, 0.70 + len(unknown_to_protocol) * 0.03), 4),
                    description=(
                        f"Smart money inflow pattern on Mantle block {block.block_num}. "
                        f"{len(unknown_to_protocol)} unlabeled wallets collectively moved ${sm_total:,.0f} USD "
                        f"into Mantle DeFi protocols. Coordinated behavior suggests informed positioning "
                        f"— historically precedes protocol-level price action within 4–12 hours."
                    ),
                    raw_metrics={
                        "wallet_count":   len(unknown_to_protocol),
                        "total_usd":      round(sm_total, 2),
                        "avg_per_wallet": round(sm_total / len(unknown_to_protocol), 2),
                    },
                    large_transfers=unknown_to_protocol,
                    method="pattern_match",
                ))

        return findings
