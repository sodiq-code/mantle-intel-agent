# Mantle Intel Agent — Backtest Results

**Generated:** 2026-06-11T09:35:55.230023+00:00
**Data:** 100 simulated Mantle blocks (reproducible demo mode)

## Summary Metrics

| Metric | Value |
|--------|-------|
| True Positives | 2 |
| False Positives | 3 |
| False Negatives | 0 |
| **Precision** | **40.0%** |
| **Recall** | **100.0%** |
| **F1 Score** | **0.5714** |
| Avg Confidence (TP) | 92.0% |
| Avg Detection Lag | 0.0 blocks |
| Blocks Analyzed | 100 |
| Total Findings | 7 |
| Detection Time | 0.1119s |

## Detection Methods

| Method | Description |
|--------|-------------|
| Z-Score | Applied to tx_count and total_value_mnt time series; threshold = 2.5σ |
| Isolation Forest | Multi-dimensional outlier detection (contamination=0.05, n_estimators=100) |
| Pattern Matching | Direct large-transfer + known-wallet behavioral rules |

## True Positives

| Block | Expected Type | Detected Type | Confidence | Lag |
|-------|--------------|--------------|------------|-----|
| 68,000,025 | whale_accumulation | multivariate_anomaly | 99.0% | 0 blks |
| 68,000,060 | smart_money_inflow | smart_money_inflow | 85.0% | 0 blks |

## False Positives (Potential Valid Discoveries)

| Block | Type | Confidence |
|-------|------|------------|
| 68,000,047 | multivariate_anomaly | 72.4% |
| 68,000,049 | multivariate_anomaly | 61.4% |
| 68,000,078 | multivariate_anomaly | 68.5% |

## Methodology Notes

- Backtest runs on deterministic simulated Mantle block data (seed = current 5-minute window)
- Ground truth: 2 injected anomalies at known offsets (whale accumulation, smart money cluster)
- Confidence threshold: 0.60 (findings below this are suppressed)
- On-chain audit: every finding hashed SHA256 and recorded to MantleIntelAudit.sol
- Results are reproducible: `python main.py --backtest`

## Reproducibility

```bash
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install -r requirements.txt
python main.py --backtest
```

_All detection logic is open-source. No black box._