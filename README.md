# Mantle Intel Agent

[![Live Demo](https://img.shields.io/badge/Live%20Demo-mantle--intel--agent.vercel.app-00ff88?style=for-the-badge)](https://mantle-intel-agent.vercel.app)
[![YouTube](https://img.shields.io/badge/Demo%20Video-YouTube-red?style=for-the-badge&logo=youtube)](https://youtu.be/AuGx1f44Qfw)
[![Contract](https://img.shields.io/badge/Audit%20Contract-Mantle%20Sepolia-green?style=for-the-badge)](https://sepolia.mantlescan.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7)
[![Sourcify](https://img.shields.io/badge/Sourcify-Exact%20Match%20✓-brightgreen?style=for-the-badge)](https://sourcify.dev/#/lookup/0x7fAb1E37d992109d3aA747703436ff4e261391b7)
[![F1 Score](https://img.shields.io/badge/F1%20Score-0.963-blue?style=for-the-badge)](./backtest/results_live.md)
[![On-Chain Findings](https://img.shields.io/badge/On--Chain%20Findings-120-orange?style=for-the-badge)](./docs/ONCHAIN.md)

> **Autonomous 5-agent AI pipeline for institutional-grade on-chain intelligence on Mantle Network.**
> Real-time anomaly detection · 120 on-chain findings · F1=0.963 · 9 data sources · 10 anomaly types · Telegram & Discord alerts · ERC-8004 NFT identity · zero mock data

---

## Demo Video

[![Mantle Intel Agent Demo](https://img.youtube.com/vi/AuGx1f44Qfw/maxresdefault.jpg)](https://youtu.be/AuGx1f44Qfw)

> **[▶ Watch on YouTube](https://youtu.be/AuGx1f44Qfw)** — Full walkthrough: live anomaly detection, on-chain findings, backtest results, ERC-8004 NFT agent identity, Telegram alerts, investment signal tiers, REST API, and real Mantle mainnet data throughout. `demo_mode: false` at all times.

---

## Live Dashboard — Real On-Chain Proof

> **No mock data. No seed data. Every number comes directly from Mantle mainnet RPC.**

![Live Dashboard](./docs/screenshots/proofs/live_dashboard_real.png)
*Block 96,593,911 — pulled live from Mantle mainnet. **2 anomalies detected**, 120 on-chain findings logged to `MantleIntelAudit` smart contract, 21 smart money wallets tracked. Two TX Spike signals flagged as WATCH at blocks 96,593,908 and 96,593,887 — both verifiable on Mantlescan. `demo_mode: false`.*

**[→ Open Live Dashboard](https://mantle-intel-agent.vercel.app)**

---

## Part A — Mantle General Track (50pts)

### ✅ A1. Built on Mantle Network

All contracts deployed to **Mantle Sepolia Testnet**. Pipeline polls **Mantle Mainnet RPC** (`https://rpc.mantle.xyz`) every 6 seconds for live blocks. Every finding is hashed and submitted to a Mantle contract. Mainnet deploy is ready (`npx hardhat run scripts/deploy.js --network mantle`) — awaiting mainnet MNT gas.

| Contract | Network | Address |
|----------|---------|---------|
| `MantleIntelAudit v2.0` | Mantle Sepolia | [`0x7fAb1E37d992109d3aA747703436ff4e261391b7`](https://sepolia.mantlescan.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7) |
| `MantleIntelAgentNFT (ERC-8004)` | Mantle Sepolia | [`0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C`](https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C) |

---

### ✅ A2. Smart Contracts — Deployed, Verified, Active

**MantleIntelAudit.sol** — 120 findings submitted. Sourcify-verified exact match.

```bash
# Verify on Sourcify — returns "perfect"
curl "https://sourcify.dev/server/check-all-by-addresses?addresses=0x7fAb1E37d992109d3aA747703436ff4e261391b7&chainIds=5003"
```

```json
[{"address":"0x7fAb1E37d992109d3aA747703436ff4e261391b7","chainIds":[{"chainId":"5003","status":"perfect"}]}]
```

```bash
# Read on-chain findings — no wallet needed
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "getPublicFindings(uint256,uint256)(string[])" 0 5 \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

![Audit Contract — 163 Transactions](./docs/screenshots/proofs/audit_contract_mantlescan.png)
*`MantleIntelAudit v2.0` on Mantlescan — **163 total transactions**, all `Record Finding` method calls from the autonomous pipeline. Source-verified (green badge). Latest tx: block 39,880,468.*

---

### ✅ A3. Real Working Product — Not a Prototype

- **Live URL:** https://mantle-intel-agent.vercel.app (always on, `demo_mode: false`)
- **Live REST API:** `GET /api/live-feed?format=json` returns real-time Mantle mainnet findings
- **SSE Stream:** `GET /api/live-feed?stream=1` — pushes new findings every 12s
- **120 on-chain findings** across 10 anomaly types — all verifiable on Mantlescan
- **Telegram bot** firing alerts sub-30s from detection to delivery
- **React dashboard** with 8 live tabs — all data sourced from Mantle RPC, not mocked

---

### ✅ A4. AI/Autonomous Agent Architecture — 5-Stage Pipeline

```
CollectorAgent (Stage 1)
  │  Mantle RPC · Pyth Oracle · mETH Contract · Merchant Moe · Lendle · Bridge Events
  ▼
AnomalyAgent (Stage 2)
  │  Z-Score (3.0σ) · Isolation Forest · Whale Pattern Match
  │  mETH Depeg · LP Imbalance · Cross-Protocol Correlation · Bridge Spike
  │  Multi-Confirm: 2+ methods fire → confidence boost
  ▼
SmartMoneyAgent (Stage 3)
  │  60+ Nansen-style wallet labels · Clustering · /compare signal history
  │  Tier 1/2/3 system · CEX / VC / smart money / MEV separation
  ▼
InsightAgent (Stage 4)
  │  Investment-grade narratives · Signal Tier (WATCH / ALERT / IMMEDIATE ACTION)
  │  Lead-time estimates · Protocol-specific context · Mirana VC-facing language
  │  Qwen-Max LLM (when API key set) or deterministic templates
  ▼
AuditAgent (Stage 5)
  │  SHA256 hash → MantleIntelAudit.sol · ERC-8004 NFT identity
  │  getPublicFindings() · subscribe / unsubscribe registry
  │
  ├── Telegram Bot (/start /compare /verify /status)
  ├── Discord Webhook (rich embeds, auto-fire per finding)
  ├── React Dashboard (8 live tabs)
  └── REST API (/api/live-feed · /api/backtest · /api/protocol-state)
```

Every agent is autonomous — no human trigger required. Pipeline runs on a 6s poll loop indefinitely.

---

### ✅ A5. Data Quality — 9 Real Sources, Zero Centralized API Keys Required

| Source | Protocol | Data Type | Update Rate |
|--------|----------|-----------|-------------|
| Mantle RPC (mainnet) | All | Blocks, txs, events | ~2s (real-time) |
| Pyth Hermes API | Price Oracle | MNT/USD, ETH/USD, BTC/USD, USDT/USD | <1s |
| mETH Contract (RPC) | mETH Protocol | ETH exchange rate, total supply | Per block |
| Merchant Moe LB Pair (RPC) | DEX | Pool reserves (token0, token1) | Per block |
| Lendle Pool (RPC) | Lending | Total supply (TVL proxy) | Per block |
| MantleIntelAudit.sol (RPC) | On-Chain Audit | Finding history, subscriptions | Immutable |
| 60+ Nansen-style labels | Wallet Intel | CEX/VC/MEV/Protocol classification | Static v1 |
| Cross-protocol correlation | Multi-protocol | Simultaneous activity across 3+ protocols | Per block |
| Bridge event monitoring | Mantle Bridge | Large cross-chain inflows/outflows | Per block |

---

### ✅ A6. Backtest — F1=0.963, Precision=100%, Zero False Positives

> Methodology: [`backtest/results_live.md`](./backtest/results_live.md)

```
═══════════════════════════════════════════════════════════════
  MANTLE INTEL AGENT — BACKTEST (seed=42, live Mantle RPC)
  Blocks: 96,520,081 → 96,520,580  |  395 blocks  |  real mainnet
═══════════════════════════════════════════════════════════════
  Precision:    100.00%  ← 0 false positives
  Recall:        92.86%
  F1 Score:       0.963
  TP=13  FP=0  FN=1
  Confidence Threshold: 0.75
  Multi-Confirm Gate: enabled (2+ of 3 sub-signals required)
  Anomaly Types Confirmed: 10 (whale, smart money, tx spike,
    value spike, mETH depeg, LP imbalance, MEV, cross-protocol,
    bridge spike, multivariate)
═══════════════════════════════════════════════════════════════
```

![Analytics Tab — Backtest Results](./docs/screenshots/proofs/dash_analytics.png)
*Analytics tab — backtest on 395 real Mantle mainnet blocks. Precision=100%, F1=0.963. IsolationForest + Z-Score + rule-based multi-confirm. Zero false positives because signals only fire when 2+ independent detection methods agree.*

---

### ✅ A7. Open Source & Reproducible

- **GitHub:** [github.com/sodiq-code/mantle-intel-agent](https://github.com/sodiq-code/mantle-intel-agent)
- Full pipeline source — agents, contracts, dashboard, backtest, bot
- Zero private API keys required to run in live mode
- One-command quickstart (see [Quickstart](#quickstart) below)

---

## Part B — Mirana Ventures Track (50pts)

### ✅ B1. Investment-Grade Alpha Signals

This is not a blockchain explorer. Every finding surfaces a decision, not just data:

| Anomaly Type | Example Signal Output | Tier | Lead Time |
|---|---|---|---|
| Whale Accumulation | "$722k Binance→Agni Finance. 15–40% TVL uptick expected in 48–72hrs. Size before block +1,200." | ALERT | ~4hrs |
| Smart Money Inflow | "5 coordinated wallets avg $93k each → Merchant Moe. 72% historical follow-through rate." | ALERT | ~8hrs |
| mETH Depeg | "mETH 87bps below peg. $127M supply at risk. Monitor Lendle health factors — cascade risk." | IMMEDIATE ACTION | 30min |
| Cross-Protocol | "$1.2M across Lendle+Agni+Merchant Moe in 1 block. Highest-conviction Mantle alpha signal." | IMMEDIATE ACTION | ~2hrs |
| LP Imbalance | "Merchant Moe MNT reserve –31% from baseline. High slippage incoming — adjust routing now." | WATCH | 0–1hr |
| Value Spike | "$1.02M single block (z=28.1σ). Large actor moving — assess direction before next block." | ALERT | immediate |

![Investment Signals Tab](./docs/screenshots/proofs/dash_signals.png)
*Signals tab — findings sorted by urgency tier. Each includes affected protocol, confidence %, recommended action (ACCUMULATE / HEDGE / MONITOR), and lead-time estimate. Built for fund managers, not analysts.*

---

### ✅ B2. Mantle Ecosystem Coverage — Every Major Protocol

| Protocol | What We Monitor |
|---|---|
| **mETH Protocol** | ETH/mETH exchange rate (depeg trigger: >50bps), total supply, staking flow |
| **Merchant Moe DEX** | LP reserve imbalance (trigger: >30%), routing impact, whale LP entry/exit |
| **Lendle (Lending)** | TVL changes, health factor proxies, liquidation cascade risk |
| **Agni Finance** | Wallet flow tracking, cross-protocol correlation with Lendle |
| **Mantle Bridge** | Large cross-chain inflows/outflows, bridge spike detection |
| **Pyth Oracle** | MNT/USD, ETH/USD, BTC/USD, USDT/USD — real-time price context |

![Protocol State Tab](./docs/screenshots/proofs/dash_protocol.png)
*Protocol State tab — live on-chain reads for mETH ratio (depeg monitor), Merchant Moe reserves, and Lendle TVL. Sourced directly via RPC — no third-party APIs.*

---

### ✅ B3. On-Chain Audit Trail — Tamper-Evident, Publicly Verifiable

Every finding is:
1. SHA256-hashed by `AuditAgent`
2. Submitted to `MantleIntelAudit.sol` via `submitFinding()`
3. Queryable by anyone via `getPublicFindings(offset, limit)` — no wallet needed
4. Linkable to Mantlescan for full transaction transparency

**120 findings live.** All anomaly types confirmed. All hashes verifiable.

![Audit Log Tab](./docs/screenshots/proofs/dash_auditlog.png)
*Audit Log tab — 120 findings in the on-chain contract. Each row: anomaly type, block number, confidence %, SHA256 hash, Mantlescan TX link. Fully public, fully verifiable.*

---

### ✅ B4. ERC-8004 Agent NFT — Autonomous Identity

The pipeline's identity is permanently minted as an **ERC-8004 NFT** — the emerging standard for AI agent identities on EVM chains.

- **Contract:** [`0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C`](https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C)
- **Mint TX:** `0x3b5ffc...` | Block 39,815,592 | Status: Success
- **Token:** `ERC20: Mantle Intel Agen... (MIAI)`
- **Significance:** Agent has a cryptographic identity it can use to sign findings, build reputation, and participate in future signal marketplaces

![NFT Contract](./docs/screenshots/proofs/nft_contract_mantlescan.png)
*ERC-8004 NFT contract on Mantlescan — mint confirmed at block 39,815,592. Token tracker shows MIAI token symbol. Agent identity permanently recorded on Mantle.*

---

### ✅ B5. Alert Infrastructure — Sub-30s Latency

**Telegram Bot** (`/start`, `/compare`, `/verify`, `/status`):
- Fires automatically on every ALERT or IMMEDIATE ACTION finding
- Message includes: anomaly type, block, confidence %, SHA256 hash, Mantlescan link
- `/compare whale` — signal history query across last 50 signals
- `/verify <hash>` — on-chain verification of any finding hash

**Discord Webhook:**
- Rich embed format, auto-fires per finding
- No bot token required — webhook URL only

Both channels tested live. Latency from detection to delivery: **<30 seconds**.

---

### ✅ B6. REST API — Consumable by Any Trading Bot

```bash
# Live findings snapshot
GET https://mantle-intel-agent.vercel.app/api/live-feed?format=json

# Real-time SSE stream (pushes every 12s)
GET https://mantle-intel-agent.vercel.app/api/live-feed?stream=1

# Protocol state (mETH, Merchant Moe, Lendle)
GET https://mantle-intel-agent.vercel.app/api/protocol-state

# Backtest results
GET https://mantle-intel-agent.vercel.app/api/backtest
```

Response shape includes: `demo_mode: false`, `source: mantle_rpc_live`, `network: mainnet`, findings array with `investment_signal`, `signal_tier`, `lead_time_hours`, `affected_protocols`, `sha256_hash`, `on_chain_tx`.

![API Live Feed](./docs/screenshots/proofs/api_live_feed.png)
*Live API response — `demo_mode: false`, `network: mainnet`, `finding_count: 120`, real block numbers, both contract addresses. Data sourced directly from Mantle RPC.*

---

### ✅ B7. Business Model — Built for Institutional DeFi Subscribers

**Problem:** No purpose-built analytics tool exists for Mantle's $500M+ DeFi ecosystem. Nansen costs $1,200/mo and has minimal Mantle-specific coverage.

**Solution:** Mantle-native intelligence at $99–$999/mo — protocol-specific signals, sub-30s alerts, verifiable on-chain audit trail.

| Tier | Price | Target |
|---|---|---|
| Pro | $99/mo | Individual DeFi traders, alpha seekers |
| Institutional | $499/mo | Funds, DAOs, protocol treasuries |
| Enterprise | $999/mo | Market makers, hedge funds, VC deal flow |

**Revenue target:** $660K ARR by end of 2027 at 150 paying subscribers.

**GTM:**
1. Hackathon visibility → early adopter pipeline (DMs already incoming)
2. Protocol partnerships — Lendle, Agni, Merchant Moe as first B2B clients
3. Mantle Foundation grant (developer tooling category)
4. ETH Global + DeFi conference presence

**Market:** $2.1B → $8.4B on-chain analytics TAM (32% CAGR). Mantle SAM: 500 institutional subscribers = $29.7M ARR ceiling.

> Full investment thesis: [`docs/INVESTMENT_THESIS.md`](./docs/INVESTMENT_THESIS.md)

---

### ✅ B8. AI Reasoning — Transparent, Auditable Decision Chain

Every signal includes a 5-step reasoning chain visible in the dashboard:

1. **Data Ingestion** — raw RPC values (mETH rate, Pyth price, reserve ratios)
2. **Z-Score** — rolling statistical deviation vs. last N blocks
3. **Cross-Validation** — Lendle health factor, Merchant Moe LP ratio
4. **Multi-Confirm** — 2+ independent detectors must agree before firing
5. **Signal Decision** — tier assignment, lead-time estimate, recommended action

![AI Reasoning Tab](./docs/screenshots/proofs/dash_reasoning.png)
*Reasoning tab — per-block agent thought stream. 91% confidence WATCH signal. Full 5-step chain shown: data ingestion → z-score (–2.27σ) → cross-validation (Lendle HF 1.12) → Merchant Moe LP check (48.7/51.3%) → signal decision.*

---

## Quickstart

```bash
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install -r requirements.txt

# Single cycle
python -m agents.pipeline --mode once

# Live continuous (6s poll)
python -m agents.pipeline --mode live

# Backtest (seed=42, real RPC)
python backtest/backtest_live.py

# Telegram bot
TELEGRAM_BOT_TOKEN=your_token python -m bot.run_bot
```

**All environment variables are optional** — system runs live without any API key:
```bash
MANTLE_RPC_URL=https://rpc.mantle.xyz       # default, no key needed
DASHSCOPE_API_KEY=your_key                   # Qwen-Max LLM (falls back to templates)
TELEGRAM_BOT_TOKEN=your_token                # for alerts
AUDIT_PRIVATE_KEY=your_deployer_key          # for on-chain submission
```

---

## Project Structure

```
mantle-intel-agent/
├── agents/
│   ├── collector/collector_agent.py      # Stage 1: RPC + Pyth + mETH + Merchant Moe
│   ├── anomaly/anomaly_agent.py          # Stage 2: 10 anomaly detectors
│   ├── smart_money/smart_money_agent.py  # Stage 3: 60+ wallet labels, clustering
│   ├── insight/insight_agent.py          # Stage 4: VC-grade investment narratives
│   ├── audit/audit_agent.py              # Stage 5: on-chain submission + ERC-8004
│   └── pipeline.py                       # Orchestrator
├── bot/
│   ├── telegram_bot.py                   # Telegram alerts + /compare /verify
│   └── discord_webhook.py               # Discord rich embed webhook
├── contracts/
│   ├── MantleIntelAudit.sol             # Audit log + subscriber registry
│   └── src/MantleIntelAgentNFT.sol      # ERC-8004 agent identity
├── dashboard/src/                        # React + Vite dashboard (Vercel)
├── backtest/
│   ├── backtest_live.py                 # Live RPC backtest (seed=42)
│   └── results_live.md                  # Full results + methodology
├── docs/
│   ├── ONCHAIN.md                       # On-chain proof documentation
│   ├── ROADMAP.md                       # Post-hackathon scalability plan
│   └── INVESTMENT_THESIS.md            # Mirana-facing TAM/PMF/revenue thesis
└── scripts/
    └── submit_findings_testnet.py       # Manual finding submission tool
```

---

## Scalability Roadmap

| Phase | Timeline | Milestones |
|---|---|---|
| **Phase 0** — Hackathon | ✅ Done | 5-agent pipeline, live API, on-chain audit, backtest, ERC-8004 |
| **Phase 1** — Mainnet | Q3 2026 | Dedicated RPC node, The Graph subgraph, PostgreSQL, K8s deploy |
| **Phase 2** — Multi-Protocol | Q4 2026 | 25+ protocols, cross-chain bridge intel, LSTM ML upgrade |
| **Phase 3** — Subscription API | Q1 2027 | $99–$999/mo tiers, 150 subscribers, $55K MRR |
| **Phase 4** — Protocol | 2027+ | Signal marketplace, MINTEL governance token, DAO |

> Full roadmap: [`docs/ROADMAP.md`](./docs/ROADMAP.md)

---

## Links

| | |
|---|---|
| **Live Dashboard** | https://mantle-intel-agent.vercel.app |
| **Demo Video** | https://youtu.be/AuGx1f44Qfw |
| **GitHub** | https://github.com/sodiq-code/mantle-intel-agent |
| **Audit Contract (Mantlescan)** | https://sepolia.mantlescan.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7 |
| **NFT Contract (Mantlescan)** | https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C |
| **Sourcify Verification** | https://sourcify.dev/#/lookup/0x7fAb1E37d992109d3aA747703436ff4e261391b7 |
| **Live API** | https://mantle-intel-agent.vercel.app/api/live-feed?format=json |

---

*MIT License · Turing Test Hackathon 2026 · Mantle Network / DoraHacks · Alpha & Data Track · Mirana Ventures · Target: $100K prize pool*
