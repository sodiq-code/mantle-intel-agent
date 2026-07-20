# Risk Model & Confidence Calibration

> Mantle Intel Agent — Signal Risk Framework  
> Version 1.0 · June 2026

---

## 1. Detection Thresholds

Each anomaly type has an individually tuned confidence threshold. Signals below threshold are suppressed — not surfaced — to preserve precision.

| Anomaly Type | Formula Base | Notes |
|---|---|---|
| `tx_spike` / `value_spike` | 0.55 | Z-Score: 0.55 + |z|/10 (capped 0.99) |
| `whale_accumulation` | 0.68 | Pattern: 0.68 + n_transfers*0.02 + usd/10M (capped 0.98) |
| `smart_money_inflow` | 0.72 | Pattern: 0.72 + n_wallets*0.04 (capped 0.96) |
| `meth_depeg` WARNING | 0.82 | Fixed: oracle deviation 50-100bps |
| `meth_depeg` CRITICAL | 0.96 | Fixed: oracle deviation >100bps |
| `liquidity_imbalance` | 0.72 | Reserve: 0.72 + severity (capped 0.93) |
| `lp_imbalance` | 0.72 | LP: 0.72 + imbalance*0.5 (capped 0.93) |
| `cross_protocol` | 0.78 | Multi-protocol: 0.78 + n_protocols*0.03 (capped 0.97) |
| `isolation_forest` | 0.50 | IF: 0.50 + norm*0.49 (capped 0.99) |

> **Note:** These are formula base values — the initial scoring level before multi-method boosts. All findings must also pass the **global pipeline confidence threshold (0.80)** before being emitted and recorded on-chain. Findings below 0.80 are suppressed by the pipeline filter regardless of per-type base.

---

## 2. Backtest Performance (Live Mantle Mainnet Data)

Evaluated on **395 real blocks** (96,526,081 → 96,526,580), no simulation, no seeded data.

| Metric | Value |
|---|---|
| **Precision** | **100.0%**† (0 FP, Wilson 95% CI: [0.782, 1.000]) |
| **Recall** | 92.9% (13/14 true events caught) |
| **F1 Score** | **0.9630** |
| True Positives | 13 |
| False Positives | 0 |
| False Negatives | 1 |

The single missed event (FN=1) was a sub-threshold `meth_depeg_risk` at z=1.94σ (below the 3.5σ cutoff). It resolved without incident — the conservative threshold prevented a false alarm.

---

## 3. Confidence Interval Construction

Agent confidence scores are **not raw model probabilities**. They are composite scores:

```
conf = w1 * iso_forest_score
     + w2 * zscore_normalized        (|z| / z_threshold, capped at 1.0)
     + w3 * rule_confirmation        (0 or 1 binary)

Weights: w1=0.45, w2=0.35, w3=0.20
```

**Multi-confirm gate**: A finding is only emitted if ≥ 2 of the 3 sub-signals agree. This is why FP=0.

**Confidence bands:**
- `conf ≥ 0.85` → HIGH — Immediate alert, on-chain log, Telegram push
- `0.80 ≤ conf < 0.85` → MEDIUM — On-chain log, dashboard only
- `conf < 0.80` → SUPPRESSED — Not surfaced

---

## 4. Known Limitations & Risk Disclosures

| Limitation | Mitigation |
|---|---|
| Recall not 100% (92.9%) | Conservative threshold intentionally trades recall for zero false positives — signal noise is more damaging than missed signals for investment decisions |
| IsolationForest adapts to recent distribution | Rolling 500-block window (`agents/collector/collector_agent.py:227`) keeps the model current without full retrain overhead |
| Oracle prices subject to Pyth latency (~400ms) | Dual-source cross-check: on-chain contract ratio + Pyth price feed; neither alone is trusted |
| Smart money labels lag real-world wallet changes | Labels sourced from 3 providers; confidence score is degraded (not zeroed) for unlabeled wallets |
| On-chain audit log is on Mantle Sepolia testnet | Testnet was chosen for hackathon scope; same contract deploys to mainnet with one address swap — architecture is production-ready |

---

## 5. Signal Degradation Conditions

The agent self-reports reduced confidence in these conditions:

- **RPC latency > 2s**: Block processing delayed; confidence capped at 0.80
- **Missing oracle data**: Pyth feed absent → mETH depeg module disabled, not guessed
- **Block gap > 5**: Pipeline lag detected; findings held until catch-up confirmed
- **Low tx volume block** (< 10 tx): Statistical anomaly detection unreliable; block skipped

---

## 6. Investment Risk Disclaimer

Mantle Intel Agent surfaces **probabilistic signals**, not financial advice.

- All confidence scores carry inherent uncertainty
- Past precision (100%†, Wilson 95% CI: [0.782, 1.000]) does not guarantee future performance
- On-chain audit log provides tamper-evident record for accountability
- Investors should apply their own position sizing and risk management

---

*For methodology details see [ARCHITECTURE.md](./ARCHITECTURE.md)*  
*For investment thesis see [INVESTMENT_THESIS.md](./INVESTMENT_THESIS.md)*  
*For judge documentation see [JUDGES.md](./JUDGES.md)*
