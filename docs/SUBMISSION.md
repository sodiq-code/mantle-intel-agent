# Mantle Intel Agent

**Autonomous 5-agent AI pipeline delivering institutional-grade on-chain intelligence on Mantle L2. Detects anomalies in real time across live Mantle mainnet blocks — every finding SHA-256 hashed and permanently recorded on-chain. F1=0.963, Precision=100%. Zero mock data. No human in the loop.**

---

## Demo Video

[▶ Watch Full Demo on YouTube →](https://youtu.be/AuGx1f44Qfw)

---

## What Is Mantle Intel Agent?

Mantle Intel Agent is a fully autonomous, 5-agent AI system purpose-built for the Mantle L2 ecosystem. It continuously monitors Mantle mainnet in real time, detects on-chain anomalies the moment they occur, translates every detection into an **actionable investment signal**, and writes a tamper-evident audit record permanently on-chain — with zero human intervention.

This is not a blockchain explorer. This is not a data dashboard. It is an **autonomous intelligence layer** that tells DeFi traders and fund managers what is happening on Mantle *before it impacts price* — with a verifiable, on-chain proof trail for every signal it fires.

**What makes it different:**
- Every number shown on the dashboard comes directly from **Mantle mainnet RPC** — `demo_mode: false` at all times
- **120 findings** permanently recorded on-chain via `MantleIntelAudit.sol` — all publicly queryable, all Mantlescan-linked
- **163 autonomous `recordFinding` transactions** submitted by the pipeline with zero manual intervention
- Signals include **tier classification** (WATCH / ALERT / IMMEDIATE ACTION), **lead-time estimates**, and **recommended actions** — not just raw anomaly scores
- **Sourcify exact-match verified** contracts. **ERC-8004 NFT** agent identity. Sub-30s Telegram alert delivery.

---

## Live Links

| Resource | URL |
|---|---|
| **Live Dashboard** | [mantle-intel-agent.vercel.app](https://mantle-intel-agent.vercel.app) |
| **GitHub Repository** | [github.com/sodiq-code/mantle-intel-agent](https://github.com/sodiq-code/mantle-intel-agent) |
| **Live API Feed** | [/api/live-feed?format=json](https://mantle-intel-agent.vercel.app/api/live-feed?format=json) |
| **Audit Contract (Sepolia)** | `0x7fAb1E37d992109d3aA747703436ff4e261391b7` · [Mantlescan](https://sepolia.mantlescan.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7) |
| **NFT Contract (ERC-8004)** | `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C` · [Mantlescan](https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C) |
| **Sourcify Verification** | [Exact Match ✓](https://sourcify.dev/#/lookup/0x7fAb1E37d992109d3aA747703436ff4e261391b7) |

---

## Live Dashboard — Real On-Chain Proof

![Live Dashboard](./screenshots/proofs/live_dashboard_real.png)

*Block 96,593,911 pulled live from Mantle mainnet. 2 anomalies detected, 120 findings logged to `MantleIntelAudit` smart contract, 21 smart money wallets tracked. Two TX Spike signals flagged WATCH at blocks 96,593,908 and 96,593,887 — both verifiable on Mantlescan. `demo_mode: false`.*

The dashboard has **8 fully live tabs**, all sourced from Mantle RPC:

| Tab | What It Shows |
|---|---|
| **Findings** | Real-time anomaly detections with confidence bars, signal tier badges, lead-time estimates |
| **Alpha Signals** | Investment signals sorted by urgency — IMMEDIATE ACTION first |
| **Analytics** | Backtest results: Precision=100%, F1=0.963, TP=13, FP=0 |
| **Protocol State** | Live mETH/ETH ratio, Merchant Moe reserves, Lendle TVL — direct RPC reads |
| **Audit Log** | All 120 on-chain findings with SHA-256 hashes and Mantlescan TX links |
| **Reasoning** | Per-block AI reasoning chain — 5-step transparent decision trace |
| **Intel API** | REST endpoint docs + on-chain subscription code snippets |
| **ROI Calculator** | Investment signal value modeler — expected savings vs. signal cost |

---

## Agent Architecture

The system is a **5-stage autonomous pipeline**. Each agent has a single responsibility. The pipeline runs on a 6-second poll loop indefinitely — no cron job, no manual trigger.

```
Mantle Mainnet RPC (https://rpc.mantle.xyz)
     │
     ▼
┌──────────────────────────────────────────────────────────────────┐
│                      AGENT PIPELINE                              │
│                                                                  │
│  [Stage 1]  CollectorAgent   ← Mantle RPC + Pyth + mETH         │
│                                + Merchant Moe + Lendle + Bridge  │
│      │                                                           │
│  [Stage 2]  AnomalyAgent     ← Z-Score (3.0σ) + IsolationForest │
│                                + 10 detector types               │
│                                Multi-Confirm gate (2+ required)  │
│      │                                                           │
│  [Stage 3]  SmartMoneyAgent  ← 60+ Nansen-style wallet labels   │
│                                Tier 1/2/3 · CEX/VC/MEV          │
│      │                                                           │
│  [Stage 4]  InsightAgent     ← VC-grade investment narratives    │
│                                Signal tier · lead-time estimate  │
│      │                                                           │
│  [Stage 5]  AuditAgent       ← SHA-256 → MantleIntelAudit.sol   │
│                                ERC-8004 NFT · getPublicFindings  │
└──────────────────────────────────────────────────────────────────┘
     │
     ├── Telegram Bot        /start · /compare · /verify · /status
     ├── Discord Webhook     rich embeds, auto-fires per finding
     ├── React Dashboard     8 live tabs, Vercel Edge
     └── REST API            /api/live-feed · /api/backtest · /api/protocol-state
```

---

## Agent Breakdown

| Agent | Role | Technology |
|---|---|---|
| **CollectorAgent** | Polls Mantle RPC every 6s. Pulls Pyth prices, mETH state, Merchant Moe reserves, Lendle TVL, bridge events | Python, web3.py, Pyth Hermes API |
| **AnomalyAgent** | Runs 10 anomaly detectors per block. Multi-Confirm gate: 2+ methods must agree | Z-Score, IsolationForest, rule-based |
| **SmartMoneyAgent** | 60+ Nansen-style wallet labels. Tier 1/2/3 system. `/compare` signal history | Address clustering, pattern matching |
| **InsightAgent** | Generates investment-grade narratives with signal tier, lead-time, recommended action | Qwen-Max LLM / deterministic templates |
| **AuditAgent** | SHA-256 hashes every finding, submits to chain, manages ERC-8004 NFT identity | Solidity, ethers.py, SHA-256 |

---

## Detection Methods

| Method | Detects | Threshold |
|---|---|---|
| Z-Score (tx value) | Abnormal value spikes per block | > 3.0σ from rolling mean |
| Isolation Forest | Multivariate anomalous tx clusters | contamination=0.03, 150 estimators |
| mETH Depeg monitor | ETH/mETH rate deviation | > 50bps from peg |
| LP Imbalance | Merchant Moe reserve shift | > 30% from baseline |
| Cross-Protocol Correlation | Simultaneous activity on 3+ protocols | Any 3+ fire in same block |
| Whale Pattern Match | Large wallet accumulation / exit | > $50k in single block |
| Smart Money Clustering | Coordinated multi-wallet moves | 3+ labeled wallets, same direction |
| Bridge Spike | Cross-chain inflow/outflow spike | > 2σ from rolling bridge baseline |
| MEV Detection | Sandwich / front-run patterns | Sequence pattern match |
| Multivariate | Combined signal from 4+ detectors | Weighted confidence score ≥ 0.75 |

**Multi-Confirm Gate:** A signal only fires when 2 or more independent detection methods agree. This is why Precision = 100% — zero noise, zero false positives delivered to users.

---

## Investment Signals — Built for Fund Managers

Every anomaly is translated into a decision, not just a data point:

| Anomaly | Signal Output | Tier | Lead Time |
|---|---|---|---|
| Whale Accumulation | "$722k Binance→Agni Finance. 15–40% TVL uptick expected in 48–72hrs. Position before block +1,200." | ALERT | ~4hrs |
| Smart Money Inflow | "5 coordinated wallets avg $93k each → Merchant Moe. 72% historical follow-through." | ALERT | ~8hrs |
| mETH Depeg | "mETH 87bps below peg. $127M supply at risk. Monitor Lendle health factors — cascade risk." | IMMEDIATE ACTION | 30min |
| Cross-Protocol | "$1.2M across Lendle+Agni+Merchant Moe in 1 block. Highest-conviction Mantle alpha." | IMMEDIATE ACTION | ~2hrs |
| LP Imbalance | "Merchant Moe MNT reserve –31% from baseline. High slippage incoming — adjust routing." | WATCH | 0–1hr |
| Value Spike | "$1.02M single block (z=28.1σ). Large actor positioning — assess direction now." | ALERT | immediate |

![Investment Signals Tab](./screenshots/proofs/dash_signals.png)

---

## Backtest Results

> Full methodology: [`backtest/results_live.md`](../backtest/results_live.md)

Backtested over **395 consecutive real Mantle mainnet blocks** (blocks 96,520,081 → 96,520,580). No simulation. No seed injection. Live RPC data, seed=42 for reproducibility.

```
════════════════════════════════════════════════════════════════
  MANTLE INTEL AGENT — BACKTEST  (seed=42, live Mantle RPC)
════════════════════════════════════════════════════════════════
  Precision   100.00%   ← zero false positives
  Recall       92.86%
  F1 Score      0.963
  TP=13  FP=0  FN=1
  Algorithms: IsolationForest + Z-Score (3.0σ) + rule-based
  Multi-Confirm gate: 2 of 3 sub-signals required to fire
  Anomaly types confirmed across 395 blocks: 10
════════════════════════════════════════════════════════════════
```

**Precision of 100%** means every signal the agent fired was a confirmed real anomaly. For a production intelligence system serving fund managers, false positives are the failure mode that destroys trust. The multi-confirm gate eliminates them entirely.

![Analytics Tab](./screenshots/proofs/dash_analytics.png)

---

## On-Chain Audit Trail

> Full on-chain proof: [`docs/ONCHAIN.md`](./ONCHAIN.md)

Every signal the pipeline fires is permanently recorded on Mantle:

1. `AuditAgent` computes `SHA256(finding_json)`
2. Submits to `MantleIntelAudit.sol` via `submitFinding()`
3. Publicly readable via `getPublicFindings(offset, limit)` — no wallet needed
4. Each entry links to its Mantlescan transaction

**120 findings confirmed on-chain. 163 total autonomous transactions. Zero manual submissions.**

```bash
# Verify contract — returns "perfect"
curl "https://sourcify.dev/server/check-all-by-addresses?addresses=0x7fAb1E37d992109d3aA747703436ff4e261391b7&chainIds=5003"
# → [{"address":"0x7fAb1E37...","chainIds":[{"chainId":"5003","status":"perfect"}]}]

# Read findings — no wallet required
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "getPublicFindings(uint256,uint256)(string[])" 0 5 \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

![Audit Contract — 163 Transactions](./screenshots/proofs/audit_contract_mantlescan.png)

![Audit Log Tab](./screenshots/proofs/dash_auditlog.png)

---

## Smart Contracts

| Contract | Address | Deployed Block | Explorer |
|---|---|---|---|
| `MantleIntelAudit v2.0` | `0x7fAb1E37d992109d3aA747703436ff4e261391b7` | 39,851,391 | [View](https://sepolia.mantlescan.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7) |
| `MantleIntelAgentNFT (ERC-8004)` | `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C` | 39,815,592 | [View](https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C) |

**MantleIntelAudit.sol** exposes:
- `submitFinding(bytes32 hash, string severity, string summary)` — pipeline-only write
- `getPublicFindings(uint offset, uint limit)` — paginated public read, no wallet required
- `subscribe(address)` / `unsubscribe(address)` — operator registry
- `findingCount` — currently **120**, verifiable on-chain

**Sourcify:** Exact-match verified on both creation and runtime bytecode (Chain ID: 5003).

---

## ERC-8004 Agent NFT — Autonomous Identity

The pipeline's identity is permanently minted as an **ERC-8004 NFT** — the emerging standard for autonomous AI agent identities on EVM chains.

- **Contract:** `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C`
- **Mint TX:** `0x3b5ffc...` · Block 39,815,592 · Status: Success · Token: `MIAI`
- Agent can cryptographically sign findings, build verifiable on-chain reputation, and participate in future signal marketplaces

![ERC-8004 NFT](./screenshots/proofs/nft_contract_mantlescan.png)

---

## Mantle Ecosystem Coverage

| Protocol | What We Monitor |
|---|---|
| **mETH Protocol** | ETH/mETH exchange rate (depeg trigger >50bps), total supply, staking flows |
| **Merchant Moe DEX** | LP reserve imbalance (trigger >30%), routing impact, whale LP entry/exit |
| **Lendle (Lending)** | TVL changes, health factor proxies, liquidation cascade risk |
| **Agni Finance** | Wallet flow tracking, cross-protocol correlation |
| **Mantle Bridge** | Large cross-chain inflows/outflows, bridge spike detection |
| **Pyth Oracle** | MNT/USD, ETH/USD, BTC/USD, USDT/USD — real-time price context |

![Protocol State](./screenshots/proofs/dash_protocol.png)

---

## AI Reasoning Chain — Fully Transparent

Every signal includes a 5-step auditable reasoning trace visible in the dashboard:

1. **Data Ingestion** — raw RPC values: mETH rate, Pyth price, reserve ratios
2. **Z-Score** — rolling deviation vs. last N blocks
3. **Cross-Validation** — Lendle health factor, Merchant Moe LP ratio
4. **Multi-Confirm** — 2+ independent detectors must agree before firing
5. **Signal Decision** — tier assignment, lead-time estimate, recommended action

![AI Reasoning Chain](./screenshots/proofs/dash_reasoning.png)

---

## Alert Infrastructure

**Telegram Bot** — fires automatically on every ALERT or IMMEDIATE ACTION finding. Sub-30s latency from detection to delivery.

| Command | Description |
|---|---|
| `/start` | Pipeline status, last 5 findings |
| `/compare whale` | Whale signal history across last 50 signals |
| `/compare smart_money` | Smart money signal stats |
| `/verify <hash>` | Verify any finding hash on-chain |
| `/status` | Live pipeline health, last block, data source status |

**Discord Webhook** — rich embed format, auto-fires per finding. No bot token required.

---

## REST API

```bash
# Live findings snapshot
GET https://mantle-intel-agent.vercel.app/api/live-feed?format=json

# Real-time SSE stream — pushes every 12s
GET https://mantle-intel-agent.vercel.app/api/live-feed?stream=1

# Protocol state (mETH, Merchant Moe, Lendle)
GET https://mantle-intel-agent.vercel.app/api/protocol-state

# Backtest results
GET https://mantle-intel-agent.vercel.app/api/backtest
```

Response includes: `demo_mode: false`, `source: mantle_rpc_live`, `network: mainnet`, `finding_count: 120`, findings array with `investment_signal`, `signal_tier`, `lead_time_hours`, `sha256_hash`, `on_chain_tx`.

![Live API Response](./screenshots/proofs/api_live_feed.png)

---

## Data Sources

| Source | What It Provides | Auth Required |
|---|---|---|
| Mantle RPC (mainnet) | Blocks, transactions, events | No |
| Pyth Hermes API | MNT/USD, ETH/USD, BTC/USD, USDT/USD | No |
| mETH Contract (RPC) | ETH/mETH exchange rate, total supply | No |
| Merchant Moe LB Pair (RPC) | Pool reserves | No |
| Lendle Pool (RPC) | Total supply (TVL proxy) | No |
| MantleIntelAudit.sol (RPC) | Finding history, subscriptions | No |
| 60+ Nansen-style wallet labels | CEX / VC / MEV / Protocol labels | No |
| Cross-protocol correlation | Simultaneous multi-protocol activity | No |
| Bridge event monitoring | Cross-chain inflows/outflows | No |

**9 independent data sources. Zero centralized API keys required.**

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Pipeline | Python 3.11, scikit-learn, web3.py |
| Smart Contracts | Solidity 0.8.20, Hardhat, ethers.js |
| Frontend | React 18, Vite, Tailwind CSS |
| API | Vercel Edge Functions (Node.js) |
| Blockchain | Mantle L2 Sepolia Testnet · Mantle Mainnet RPC |
| Alerting | Telegram Bot API · Discord Webhook |
| Verification | Sourcify (exact match) |
| Hosting | Vercel |

---

## Business Model

> Full investment thesis: [`docs/INVESTMENT_THESIS.md`](./INVESTMENT_THESIS.md)

**Problem:** No purpose-built analytics layer exists for Mantle's $500M+ DeFi ecosystem. Nansen charges $1,200/mo with minimal Mantle coverage.

**Solution:** Mantle-native intelligence at $99–$999/mo — protocol-specific signals, sub-30s alerts, tamper-evident on-chain audit trail, and a public API any trading bot can consume.

| Tier | Price | Target |
|---|---|---|
| Pro | $99/mo | Individual DeFi traders, alpha seekers |
| Institutional | $499/mo | Funds, DAOs, protocol treasuries |
| Enterprise | $999/mo | Market makers, hedge funds, VC deal flow |

**Market:** $2.1B → $8.4B on-chain analytics TAM (32% CAGR).
**Revenue target:** $660K ARR by end of 2027 at 150 paying subscribers.
**GTM:** Protocol partnerships (Lendle, Agni, Merchant Moe) → Mantle Foundation grant → ETH Global presence.

---

## Why Mantle?

Mantle L2 is uniquely suited for autonomous AI agent infrastructure:

- **Low fees** — agents can write findings on-chain at scale without gas overhead destroying unit economics
- **EVM compatibility** — full Solidity tooling, no new paradigms required
- **MNT utility** — native token creates natural incentive alignment for agent operators and signal subscribers
- **Growing DeFi TVL** — anomaly detection is most valuable where capital is concentrated; Mantle's ecosystem expansion directly expands the agent's detection surface
- **Protocol depth** — mETH, Merchant Moe, Lendle, and Agni provide rich cross-protocol correlation opportunities unavailable on most L2s

---

## Roadmap

> Full plan: [`docs/ROADMAP.md`](./ROADMAP.md)

| Phase | Timeline | Milestones |
|---|---|---|
| **Phase 0** — Hackathon | ✅ Complete | 5-agent pipeline, 120 on-chain findings, live API, backtest, ERC-8004 NFT |
| **Phase 1** — Mainnet | Q3 2026 | Dedicated RPC node, The Graph subgraph, PostgreSQL, Kubernetes |
| **Phase 2** — Multi-Protocol | Q4 2026 | 25+ protocols, cross-chain bridge intel, LSTM model upgrade |
| **Phase 3** — Subscriptions | Q1 2027 | $99–$999/mo tiers, 150 subscribers, $55K MRR |
| **Phase 4** — Protocol | 2027+ | Signal marketplace, MINTEL governance token, DAO |

---

## Open Source

All code is MIT licensed and fully open source.

**[github.com/sodiq-code/mantle-intel-agent](https://github.com/sodiq-code/mantle-intel-agent)**

```
mantle-intel-agent/
├── agents/
│   ├── collector/collector_agent.py      # Stage 1: RPC + Pyth + mETH + Merchant Moe
│   ├── anomaly/anomaly_agent.py          # Stage 2: 10 anomaly detectors
│   ├── smart_money/smart_money_agent.py  # Stage 3: 60+ wallet labels
│   ├── insight/insight_agent.py          # Stage 4: investment signal narratives
│   ├── audit/audit_agent.py              # Stage 5: on-chain submission + ERC-8004
│   └── pipeline.py                       # Orchestrator
├── bot/
│   ├── telegram_bot.py                   # Telegram alerts + commands
│   └── discord_webhook.py               # Discord rich embed webhook
├── contracts/
│   ├── MantleIntelAudit.sol             # Audit log + subscriber registry
│   └── src/MantleIntelAgentNFT.sol      # ERC-8004 agent identity NFT
├── dashboard/src/                        # React + Vite (Vercel)
├── backtest/
│   ├── backtest_live.py                 # Live RPC backtest (seed=42)
│   └── results_live.md                  # Full results + methodology
└── docs/
    ├── ONCHAIN.md
    ├── ROADMAP.md
    └── INVESTMENT_THESIS.md
```

---

*Built for The Turing Test Hackathon 2026 — Mantle Network × DoraHacks*
*Track: Alpha & Data · Mirana Ventures · Target: $100K prize pool*

---

<p align="center">Built by <strong>JIMOH SODIQ</strong></p>
