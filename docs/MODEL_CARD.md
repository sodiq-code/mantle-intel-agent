# Model Card — Mantle Intel Agent

> **Following the Model Card framework** (Mitchell et al., 2019 — Google/HuggingFace standard)  
> **Version:** 2.0 · July 2026  
> **Last updated:** 2026-07-19

---

## 1. Model Details

### Overview

Mantle Intel Agent is an **autonomous 5-agent AI pipeline** for on-chain anomaly detection on Mantle Network. The system uses a combination of statistical methods (Z-Score), machine learning (Isolation Forest), rule-based pattern matching, and optional LLM-generated narrative reports.

**Key distinction:** The LLM component is **cosmetic enhancement only** — core detection intelligence is entirely rule-based and statistical. The system operates correctly without any LLM provider (falls back to deterministic templates).

### Model Type

| Component | Type | Purpose |
|-----------|------|---------|
| Isolation Forest | Unsupervised ML (scikit-learn) | Multivariate outlier detection |
| Z-Score | Statistical | Univariate spike detection (3.5σ threshold) |
| Pattern Matching | Rule-based | Whale, smart money, depeg, imbalance detection |
| LLM (optional) | Generative AI | Narrative report formatting only |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 2026 | Initial hackathon release |
| 2.0 | July 2026 | P2 fixes: prompt sanitisation, circuit breaker, health checks, OTel tracing, rate limiting |

---

## 2. Intended Use

### Primary Use Case
Real-time on-chain anomaly detection and alerting for Mantle Network DeFi ecosystem participants — traders, fund managers, protocol teams, and risk analysts.

### Intended Users
- Professional crypto fund managers monitoring Mantle positions
- DeFi protocol teams tracking TVL risk and whale movements
- Retail traders seeking smart money flow intelligence
- Grant reviewers evaluating system capabilities

### Out-of-Scope Uses
- ❌ **Financial advice** — The system surfaces probabilistic signals, not investment recommendations
- ❌ **Compliance/sanctions screening** — Not designed for AML/KYC purposes
- ❌ **Predictive price modeling** — Detects current anomalies, not future prices
- ❌ **Cross-chain analysis** — Mantle Network only (Phase 2 adds cross-chain)

---

## 3. LLM Provider Disclosure

### Provider Architecture (Tiered Fallback)

The LLM is used **only for narrative report generation** — it does not influence detection, classification, or confidence scoring. If no LLM is available, the system uses deterministic templates with zero quality degradation for core functionality.

| Tier | Provider | Model | Purpose | Data Sent | Cost |
|------|----------|-------|---------|-----------|------|
| 1 | Ollama (local) | llama3.2:3b | Narrative formatting | Anomaly metadata only | Free |
| 2 | Groq API | moonshotai/kimi-k2-instruct | Narrative formatting | Anomaly metadata only | Free tier |
| 3 | OpenRouter | meta-llama/llama-3.2-3b-instruct:free | Narrative formatting | Anomaly metadata only | Free tier |
| 4 | Templates (rule-based) | N/A | Fallback formatting | None (local) | Free |

### Data Sent to LLM Providers

The following data is included in LLM prompts for narrative generation:

| Field | Example | Sensitivity |
|-------|---------|-------------|
| Anomaly type | `whale_accumulation` | Low (categorical) |
| Block height | `96526123` | Low (public on-chain) |
| Confidence | `0.85` | Low (computed metric) |
| Sanitised description | Truncated to 500 chars, injection patterns stripped | Low |
| Sanitised metrics | Numeric values only; `input_data`/hex fields removed | Low |
| Sanitised transfers | Limited to 3 transfers; hex `input` fields stripped | Low |

**No user data is sent to LLM providers.** All data in prompts originates from public blockchain state.

### Prompt Injection Protection (P2-25)

All user-influenced data is sanitised before inclusion in LLM prompts:
- **String truncation:** Max 500 characters per field
- **Injection pattern stripping:** Known attack vectors (e.g., "ignore previous", "system:", "[INST]") replaced with `[REDACTED]`
- **Hex field removal:** `input_data`, `input`, `inputData` fields stripped entirely
- **List truncation:** Large transfers limited to 3 items; metrics lists limited to 5 items

---

## 4. Training Data

### ML Model (Isolation Forest)

| Property | Value |
|----------|-------|
| Training method | Unsupervised (no labels required) |
| Training data | Rolling window of last 500 blocks from Mantle mainnet |
| Contamination parameter | 0.02 (2% expected anomaly rate) |
| Feature count | 7 (tx_count, total_value_mnt, unique_senders, large_transfer_count, meth_ratio, moe_reserve_ratio, lendle_tvl) |
| Retraining | Automatic — model adapts as new blocks are processed |
| No fine-tuning | The Isolation Forest is trained from scratch each cycle using the rolling window |

### No External Training Data

The system does **not** use any external datasets, purchased data, or user-generated training data. All training data comes from public Mantle blockchain state via RPC.

### LLM: No Training or Fine-Tuning

The LLM providers are used in **prompt-only mode** (zero-shot inference). No fine-tuning, no LoRA, no RAG, no custom training on any dataset. The system sends a structured prompt and receives a text response.

---

## 5. Performance Metrics

### Backtest Results (Live Mantle Mainnet Data)

Evaluated on **395 real blocks** (96,526,081 → 96,526,580), no simulation, no seeded data.

| Metric | Value |
|--------|-------|
| **Precision** | **100.0%**† (0 FP, Wilson 95% CI: [0.782, 1.000]) |
| **Recall** | **92.9%** (13/14 true events caught) |
| **F1 Score** | **0.9630** |
| True Positives | 13 |
| False Positives | 0 |
| False Negatives | 1 |

Wilson 95% CI: Precision [0.782, 1.000], Recall [0.697, 0.985]

The single missed event (FN=1) was a sub-threshold `meth_depeg_risk` at z=1.94σ (below the 3.5σ cutoff). It resolved without incident — the conservative threshold prevented a false alarm.

### Confidence Calibration

| Confidence Band | Range | Action |
|----------------|-------|--------|
| HIGH | ≥ 0.85 | Immediate alert, on-chain log, Telegram push |
| MEDIUM | 0.80 – 0.84 | On-chain log, dashboard only |
| DETECTED-BUT-SUPPRESSED | 0.72 – 0.79 | Detected by per-type method, but below global 0.80 pipeline filter — not emitted |
| SUPPRESSED | < 0.72 | Not surfaced |

### Detection Thresholds by Anomaly Type

> **Note:** These are per-method initial detection thresholds. All findings must also pass the **global pipeline confidence threshold of 0.80** before being emitted. A finding detected at 0.75 by a per-type method is boosted by multi-method corroboration (+0.04) and then filtered — only findings reaching ≥0.80 are recorded on-chain.

| Anomaly Type | Threshold | Method |
|-------------|-----------|--------|
| `whale_accumulation` | 0.72 | Pattern match |
| `smart_money_inflow` | 0.75 | Pattern match |
| `meth_depeg` | 0.65 | Oracle diff (lower = early warning) |
| `oracle_manipulation` | 0.85 | Cross-source divergence ⚠️ **unimplemented** — no detection code exists for this type |
| `tx_spike` | 0.75 (3.5σ) | Z-Score |
| `isolation_forest` | 0.75 | IF outlier (score < 0) |

### On-Chain Contract Threshold

The Solidity contract (`MantleIntelAudit.sol`) enforces `confidenceScore >= 80` at the contract level, ensuring only findings meeting the pipeline's confidence threshold (0.80) are permanently recorded on-chain.

---

## 6. Known Limitations

### Detection Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Recall is 92.9%, not 100% | 1 in 14 events may be missed | Conservative threshold prioritises zero false positives — less damaging than false alarms for investment decisions |
| Isolation Forest adapts to recent distribution | May miss anomalies in changing regimes | Rolling 500-block window keeps model current without full retrain |
| Oracle prices subject to Pyth latency (~400ms) | Brief price discrepancies may be flagged or missed | Dual-source cross-check: on-chain contract ratio + Pyth price; neither alone is trusted |
| Smart money labels lag real-world wallet changes | New smart wallets not immediately tracked | Labels sourced from 3 providers; confidence degraded (not zeroed) for unlabeled wallets |
| Contract on testnet | On-chain audit trail not on mainnet | Same contract deploys to mainnet with one address swap — architecture is production-ready |
| No cross-chain signals | Ethereum L1 → Mantle flows not tracked | Phase 2 roadmap includes cross-chain bridge monitoring |

### LLM Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| LLM may generate inaccurate claims | Reports could contain hallucinated protocol names or amounts | LLM output is supplementary; core data (confidence, type, block) is from deterministic pipeline |
| LLM is prompt-only, no domain fine-tuning | May not understand Mantle-specific context deeply | System prompt constrains output format; templates ensure minimum quality |
| LLM availability varies | Provider rate limits, outages | 4-tier fallback chain; worst case = rule-based templates (always available) |
| LLM adds latency (~2-5s) | Finding delivery delayed | LLM formatting is async; finding hash recorded on-chain immediately, narrative added after |

### Data Dependency Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| RPC latency > 2s | Block processing delayed | Confidence capped at 0.80; pipeline reports degradation |
| Missing oracle data | mETH depeg module disabled | Module disabled, not guessed — prevents false signals |
| Block gap > 5 | Pipeline lag | Findings held until catch-up confirmed |
| Low tx volume (< 10 tx/block) | Statistical detection unreliable | Block skipped; no finding emitted |

---

## 7. Data Retention & Privacy

### Data Storage

| Data | Storage | Retention | Access |
|------|---------|-----------|--------|
| Anomaly findings | `data/findings.jsonl` + on-chain | Indefinite (on-chain) / Daily rotation (JSONL) | Public (on-chain) / Server-only (JSONL) |
| Audit log | `data/audit_log.jsonl` + on-chain | Indefinite (on-chain) / Daily rotation (JSONL) | Public (on-chain) / Server-only (JSONL) |
| Pipeline metrics | In-memory + `data/dashboard.json` | Rolling (last 100 findings) | Public API |
| LLM prompts | Not stored | N/A | N/A |
| LLM responses | Not stored separately | N/A | N/A |
| User data | **None collected** | N/A | N/A |

### Privacy Commitments

- **No user data collection** — The system monitors public blockchain state, not individual user behavior
- **No cookies or tracking** — Dashboard serves static React app; no client-side analytics
- **No wallet tracking** — Smart money labels are for public whale wallets, not user wallets
- **No LLM prompt storage** — Prompts are generated, sent, and discarded; never logged or stored
- **On-chain data is public** — Finding hashes and metadata on Mantle Sepolia are publicly viewable by design

### File Rotation (P2-27)

JSONL files are rotated daily:
- Files from previous days are gzipped with date suffix (e.g., `findings-2026-07-18.jsonl.gz`)
- Gzipped files older than 30 days are automatically deleted
- Original files are truncated to start fresh each day

---

## 8. Ethical Considerations

### Fairness
- The system does not profile or target individual users
- Smart money labels are applied to publicly known institutional wallets (CEXs, funds, MEV bots), not retail users
- Anomaly detection is based on statistical deviation, not demographic or behavioral profiling

### Misuse Potential
- **Front-running:** Signals could theoretically be used for front-running whale transactions. Mitigation: signals are available to all subscribers simultaneously; no preferential access.
- **Panic selling:** Alerts could trigger panic. Mitigation: confidence bands clearly indicate signal strength; all alerts include "preliminary signal, confirm before sizing" disclaimer.
- **False confidence:** High precision (100%†) may create over-reliance. Mitigation: Wilson CI [0.782, 1.000] disclosed; past performance disclaimer in every report.

### Transparency
- Every agent decision is hashed and recorded on-chain (SHA256, `MantleIntelAudit.sol`)
- Finding hashes are independently verifiable by anyone
- Source code is open-source (GitHub)
- This model card discloses all LLM usage, data sources, and limitations

---

## 9. Maintenance & Updates

### Model Retraining
- Isolation Forest is retrained automatically every pipeline cycle using the rolling 500-block window
- No manual retraining or model versioning required
- Z-Score thresholds are configurable via environment variables

### LLM Provider Updates
- LLM provider priority is configurable via environment variables
- New providers can be added without code changes (just env config)
- Template fallback ensures zero dependency on any external LLM

### Contract Updates
- Contract is immutable (no proxy pattern)
- New contract deployment requires new address configuration
- All findings on old contract remain permanently verifiable

---

## 10. Citation

If you reference this system, please cite:

```bibtex
@software{mantle_intel_agent_2026,
  title={Mantle Intel Agent: Autonomous On-Chain Anomaly Detection for Mantle Network},
  author={Jimoh Tech (sodiq-code)},
  year={2026},
  url={https://github.com/sodiq-code/mantle-intel-agent},
  note={Turing Test Hackathon — Alpha \& Data Track}
}
```

### References

- Mitchell, M., Wu, S., Zaldivar, A., et al. (2019). *Model Cards for Model Reporting.* ACM FAT*.
- Isolation Forest: Liu, F.T., Ting, K.M., Zhou, Z.H. (2008). *Isolation Forest.* IEEE ICDM.
- Z-Score methodology: Standard statistical process control (3σ threshold).

---

† Point estimate from 14-observation backtest. Wilson 95% CI: [0.782, 1.000]. True precision at production scale may differ.

*Mantle Intel Agent — Built for The Turing Test Hackathon 2026 (Mantle Network / DoraHacks)*
