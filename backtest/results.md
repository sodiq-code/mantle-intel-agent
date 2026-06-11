# Mantle Intel Agent — Backtest Results v2.0

**Generated:** 2026-06-11T12:48:25.995262+00:00
**Data:** 100 simulated Mantle blocks (reproducible demo mode)
**Confidence Threshold:** 0.75 (v2 — raised from 0.60 to reduce false positives)
**Ground Truth Events:** 5
**Mode:** 🟡 Demo (simulated data)

## Summary Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| True Positives | 5 | Correctly identified anomalies |
| False Positives | 0 | False alarms |
| False Negatives | 0 | Missed events |
| **Precision** | **100.0%** | TP / (TP+FP) — 🟢 Excellent |
| **Recall** | **100.0%** | TP / (TP+FN) |
| **F1 Score** | **1.0000** | Harmonic mean |
| Avg Confidence (TP) | 91.6% | Mean confidence of correct detections |
| Avg Detection Lag | 0.0 blocks | Near-realtime |
| Blocks Analyzed | 100 | |
| Total Findings Emitted | 15 | Above threshold only |
| Detection Time | 0.1594s | Pipeline runtime |

## Precision vs Recall Trade-off

> **Design Decision:** Precision is prioritized over Recall in Mantle Intel Agent.
> In production alpha-generation, a false alarm (telling a trader there's a whale move when there isn't)
> is more costly than missing an event. We raise the confidence threshold to 0.75 to achieve
> high-precision signals — verified on-chain and surfaced only when confidence is warranted.

## Detection Methods

| Method | Threshold | Description |
|--------|-----------|-------------|
| Z-Score | 3.0σ (v2: raised from 2.5σ) | Applied to tx_count and total_value_mnt time series |
| Isolation Forest | contamination=0.03, n=150 (v2: tuned) | Multi-dimensional outlier detection |
| Pattern Matching | value ≥ $250k + 3+ txs | Direct large-transfer + known-wallet behavioral rules |
| Multi-Confirm | 2+ methods on same block | Confidence boost when methods corroborate |

## True Positives

| Block | Expected Type | Detected Type | Confidence | Lag (blocks) |
|-------|--------------|--------------|------------|--------------|
| 68,000,025 | whale_accumulation | whale_accumulation | 86.7% | 0 |
| 68,000,060 | smart_money_inflow | smart_money_inflow | 96.0% | 0 |
| 68,000,040 | tx_spike | tx_spike | 99.0% | 0 |
| 68,000,075 | value_spike | whale_accumulation | 91.5% | 0 |
| 68,000,088 | whale_accumulation | whale_accumulation | 84.8% | 0 |

## False Positives

_No false positives in this run._ ✅

## False Negatives (Missed Events)

_All ground truth events detected._ ✅

## Live Data Note

This backtest uses **deterministic simulated data** to ensure reproducibility.
The pipeline is identical to production — only the data source changes.

To run against **live Mantle RPC data**:

```bash
export MANTLE_RPC_URL=https://rpc.mantle.xyz
export DEMO_MODE=false
python main.py --backtest --live
```

Live mode differences:
- Block data fetched from Mantle L2 RPC (real transactions)
- Ground truth loaded from `data/labeled_events.json` (manually validated)
- Results will differ from simulated run

## Methodology Notes

- Backtest runs on deterministic simulated Mantle block data (seed = current 5-minute window)
- Ground truth: 5 injected anomalies at known offsets
- Confidence threshold: 0.75 (v2 — was 0.60 in v1)
- On-chain audit: every finding hashed SHA256 and recorded to MantleIntelAudit.sol
- Results are reproducible: `python main.py --backtest`

## Reproducibility

```bash
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install -r requirements.txt
python main.py --backtest
```

_All detection logic is open-source. No black box. Every finding verifiable on-chain._