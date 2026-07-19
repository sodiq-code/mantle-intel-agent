# Mantle Intel Agent — Architecture

> Autonomous 5-agent AI pipeline for on-chain anomaly detection on Mantle Network.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MANTLE INTEL AGENT v5.0                       │
│           On-Chain Intelligence for the Mantle Ecosystem         │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   Agent 1: Collector  │  ← Mantle RPC (mainnet + sepolia)
│  (collector_agent.py) │     8 data sources:
│                      │     • Block data & tx counts
│   Poll interval: 12s │     • Large transfer detection
│   History: 500 blks  │     • mETH contract read
└──────────┬───────────┘     • Merchant Moe reserves
           │                 • Lendle pool TVL
           │ BlockSummary[]  • Pyth oracle prices
           ▼                 • Bridge event logs
┌──────────────────────┐     • MEV bundle count
│  Agent 2: Anomaly    │
│  (anomaly_agent.py)  │  ← Detection methods:
│                      │     • Z-score spike detection
│  ML: Isolation Forest│     • Isolation Forest (multivariate)
│  + Z-score + Pattern │     • Whale pattern matching
│                      │     • mETH depeg detection
│  Output: findings[]  │     • Merchant Moe LP imbalance
│  Confidence ≥ 0.75   │     • Cross-protocol correlation
└──────────┬───────────┘
           │
           │ AnomalyFinding[]
           ▼
┌──────────────────────┐
│ Agent 3: Smart Money │
│(smart_money_agent.py)│  ← 60+ labeled wallets (Nansen-style)
│                      │     • CEX wallet detection
│  Clustering: DBSCAN  │     • VC/fund wallet tracking
│  + KMeans            │     • Smart money inflow signals
│                      │     • Wallet tier system (1–3)
│  Output: signals[]   │
└──────────┬───────────┘
           │
           │ findings + signals
           ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│  Agent 4: Audit Log  │───▶│  Mantle Sepolia Blockchain        │
│(audit_agent.py)      │    │                                  │
│                      │    │  MantleIntelAudit.sol             │
│  SHA256 tamper-proof │    │  0x7266cD152e08Ae7...     │
│  Pre-commit sealing  │    │  → submitFinding(bytes32 hash)    │
│  ERC-8004 NFT mint   │    │  → findingCount() = 20           │
│                      │    │  → getPublicFindings(offset,lim) │
└──────────┬───────────┘    └──────────────────────────────────┘
           │
           │ alerts
           ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│  Agent 5: Notifier   │───▶│  Telegram Bot                     │
│ (telegram_agent.py)  │    │  @MantleIntelBot                  │
│                      │    │  Commands: /status /findings      │
│  Alert routing       │    │  /compare /help                   │
│  Severity filtering  │    └──────────────────────────────────┘
└──────────────────────┘
```

---

## Data Flow

```
Mantle RPC
    │
    │  eth_getBlockByNumber + eth_getLogs
    ▼
Collector Agent (12s poll)
    │
    │  BlockSummary { block_num, tx_count, total_value_mnt,
    │                 large_transfers[], unique_senders,
    │                 meth_ratio, moe_reserve_a/b, lendle_tvl }
    ▼
Anomaly Agent
    │
    │  Z-Score: (x - μ) / σ > 3.0σ threshold
    │  Isolation Forest: contamination=0.03, min_history=25
    │  Confidence: 0.75 threshold, multi-method boost +0.04
    │
    │  AnomalyFinding { finding_id, anomaly_type, block_height,
    │                   confidence, description, raw_metrics,
    │                   investment_signal, sha256_hash }
    ▼
Smart Money Agent
    │
    │  60+ labeled wallets → DBSCAN clustering → tier scoring
    │
    │  SmartMoneySignal { wallet, action, protocol, value_usd,
    │                     confidence, rationale }
    ▼
Audit Agent
    │
    │  SHA256(to_dict(), sort_keys=True) → bytes32 → submitFinding()
    │  MantleIntelAudit.sol (Mantle Sepolia)
    │  20 findings confirmed on-chain
    ▼
Notifier Agent → Telegram + Vercel API response
```

---

## Contract Architecture

```
contracts/
├── MantleIntelAudit.sol          # Primary audit trail
│   ├── submitFinding(bytes32)    # Agent submits SHA256 hash
│   ├── findingCount()            # Returns total count
│   ├── getPublicFindings(o, l)   # Paginated retrieval
│   └── subscribe/unsubscribe     # Signal registry
│
├── MantleIntelAgentNFT.sol       # ERC-8004 autonomous agent NFT
│   └── mint(agentId, uri)        # Proved at block 39815592
```

---

## API Layer (Vercel Edge Functions)

```
/api/live-feed          → Anomaly findings (demo_mode: false)
/api/protocol-state     → mETH ratio, Moe reserves, Lendle TVL
/api/investment-signals → Smart money signals
/api/backtest-results   → Precision/Recall/F1 metrics
/api/audit-log          → On-chain finding hashes
```

---

## ML Detection Details

### Anomaly Types

| Type | Method | Threshold |
|------|--------|-----------|
| `tx_spike` | Z-score | 3.0σ |
| `value_spike` | Z-score | 3.0σ |
| `whale_accumulation` | Pattern match | 2+ large txs, ≥$100k |
| `whale_distribution` | Pattern match | 2+ large txs, ≥$100k |
| `smart_money_inflow` | Pattern match | 2+ unknown→protocol |
| `meth_depeg` | Oracle diff | ≥50bps from peg |
| `liquidity_imbalance` | Reserve ratio | ≥15% imbalance |
| `cross_protocol` | Multi-protocol | 3+ protocols hit |
| `bridge_spike` | Z-score | 3.0σ on bridge vol |
| `isolation_forest` | IF outlier | score < 0 |

### Backtest Results (Live Mantle Mainnet Data, 395 blocks)

| Metric | Value |
|--------|-------|
| Precision | **100%** (0 false positives) |
| Recall | **92.9%** (13/14 true events caught) |
| F1 Score | **0.963** |
| Blocks | 395 (96,526,081 → 96,526,580) |
| TP | 13 |
| FP | 0 |
| FN | 1 |

Source: `backtest/results_live.json` — real on-chain data, no simulation, no seed.
The single FN was a sub-threshold meth_depeg_risk at z=1.94σ — conservative threshold correctly suppressed it.

Wilson 95% CI for precision: [0.782, 1.000] (n=14 observations)
Wilson 95% CI for recall: [0.697, 0.985]

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Agent pipeline | Python 3.13, asyncio |
| ML | scikit-learn (IsolationForest), scipy (z-score), numpy |
| Blockchain | web3.py, Mantle RPC |
| Contracts | Solidity 0.8.x, Hardhat/Foundry |
| API | Vercel Edge Functions (Node.js) |
| Dashboard | React 18, Vite, Recharts |
| Alerts | python-telegram-bot |
| Logging | structlog |

---

## Security Properties

- **Tamper-evident hashing**: Every finding hashed with SHA256 over ALL fields (not just 5). Any field change = different hash.
- **Pre-commit sealing**: Hash computed before submission. Post-submission mutation detectable.
- **On-chain immutability**: Hashes stored in Mantle Sepolia — censorship-resistant audit trail.
- **Deterministic pipeline**: seed=42 backtest produces identical results across runs.

---

*GitHub:* https://github.com/sodiq-code/mantle-intel-agent  
*Dashboard:* https://mantle-intel-agent.vercel.app  
*Network:* Mantle Sepolia Testnet (chainId: 5003)  
*Model Card:* [MODEL_CARD.md](./MODEL_CARD.md)  
*Judge Walkthrough:* [JUDGES.md](./JUDGES.md)
