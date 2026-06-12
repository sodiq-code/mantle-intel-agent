# Mantle Intel Agent

[![Live Dashboard](https://img.shields.io/badge/Live%20Demo-mantle--intel--agent.vercel.app-blue)](https://mantle-intel-agent.vercel.app)
[![Contract](https://img.shields.io/badge/Contract-Mantle%20Sepolia-green)](https://sepolia.mantlescan.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7)
[![Hackathon](https://img.shields.io/badge/Hackathon-Turing%20Test%202026-purple)](https://dorahacks.io)
[![Backtest](https://img.shields.io/badge/Backtest-F1%3D1.00%20%7C%20Precision%3D100%25-brightgreen)](./backtest/results_live.md)
[![API](https://img.shields.io/badge/API-Live%20%7C%20demo__mode%3Dfalse-brightgreen)](https://mantle-intel-agent.vercel.app/api/live-feed?format=json)

> **Autonomous 5-agent AI pipeline for institutional-grade on-chain intelligence on Mantle Network.**  
> F1=1.00 · Precision=100% · 8 data sources · 10 anomaly types · ERC-8004 on-chain audit trail  
> Every finding SHA256-hashed and permanently recorded on Mantle L2.

---

## Demo Video

[![Mantle Intel Agent — Demo Video](https://img.youtube.com/vi/yPErNZW2hR0/maxresdefault.jpg)](https://youtu.be/yPErNZW2hR0)

> **[▶ Watch on YouTube](https://youtu.be/yPErNZW2hR0)** — Full walkthrough: live anomaly detection, on-chain findings, backtest, dashboard, ERC-8004 NFT identity, Telegram alerts, and investment signal tiers.

---

## What It Does

Mantle Intel Agent is a fully autonomous 5-agent Python pipeline that continuously monitors the Mantle L2 ecosystem and surfaces **investment-grade signals** before they impact price:

1. **Collects** — Real-time Mantle RPC blocks + Pyth oracle prices + mETH contract state + Merchant Moe reserves + Lendle TVL (8 data sources, no centralized API key required)
2. **Detects** — 10 anomaly types: Z-Score (3.0σ), Isolation Forest (contamination=0.03), whale pattern matching, mETH depeg, LP imbalance, cross-protocol correlation, bridge events
3. **Clusters** — 60+ Nansen-style wallet labels: CEX (Binance, Bybit, OKX), VC (Mirana, Jump, Multicoin), Mantle DeFi protocols, MEV bots
4. **Generates** — VC-grade investment memos with signal tier (WATCH / ALERT / IMMEDIATE ACTION) and lead-time estimates
5. **Records** — Every finding SHA256-hashed and written on-chain via `MantleIntelAudit.sol` (5 findings live)
6. **Alerts** — Telegram bot + Discord webhook with real-time, sub-30s latency
7. **Serves** — Public REST API + React dashboard + on-chain `getPublicFindings()` subscription registry

---

## Architecture

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
  │  60+ Nansen-style labels · Wallet clustering · /compare signal history
  │  Tier 1/2/3 system · CEX/VC/smart money/MEV separation
  ▼
InsightAgent (Stage 4)
  │  Investment-grade narratives · Signal Tier (WATCH/ALERT/IMMEDIATE ACTION)
  │  Lead-time estimates · Protocol-specific context · Mirana VC-facing language
  │  Qwen-Max LLM (when API key set) or deterministic templates
  ▼
AuditAgent (Stage 5)
  │  SHA256 hash → MantleIntelAudit.sol · ERC-8004 NFT identity
  │  getPublicFindings() · subscribe/unsubscribe registry
  │
  ├── Telegram Bot (/start /compare /verify /status)
  ├── Discord Webhook (rich embeds, auto-fire per finding)
  ├── React Dashboard (live feed, analytics, investment signals tab)
  └── REST API (/api/live-feed, /api/backtest, /api/protocol-state)
```

---

## Investment Utility (Mirana Track)

Every finding surfaces an actionable **investment signal** — not just raw data:

| Anomaly Type | Example Signal | Signal Tier | Lead Time |
|-------------|----------------|-------------|-----------|
| Whale Accumulation | "$722k Binance→Agni Finance. 15-40% TVL uptick expected in 48-72hrs. Size before block +1,200." | ALERT | ~4hrs |
| Smart Money Inflow | "5 coordinated wallets, avg $93k/wallet → Merchant Moe. Informed early positioning. 72% historical rate." | ALERT | ~8hrs |
| mETH Depeg | "mETH 87bps below peg. $127M supply at risk. Monitor Lendle health factors — cascade risk." | IMMEDIATE ACTION | 30min |
| Cross-Protocol | "$1.2M across Lendle+Agni+Merchant Moe in 1 block. Highest-conviction Mantle alpha signal." | IMMEDIATE ACTION | ~2hrs |
| LP Imbalance | "Merchant Moe MNT reserve -31% from baseline. High slippage incoming — adjust routing." | WATCH | 0-1hr |
| Value Spike | "$1.02M in single block (z=28.1σ). Large actor moving — assess direction." | ALERT | immediate |

**These are the signals professional DeFi traders and fund managers need — not z-scores, but decisions.**

---

## Data Source Quality

| Source | Protocol | Data Type | Update Rate | Auth Required |
|--------|----------|-----------|-------------|---------------|
| Mantle RPC (mainnet) | All | Blocks, txs, events | Real-time (~2s) | No |
| Pyth Hermes API | Price Oracle | MNT/USD, ETH/USD, BTC/USD, USDT/USD | <1s | No |
| mETH Contract (RPC) | mETH Protocol | ETH exchange rate, total supply | Per block | No |
| Merchant Moe LB Pair (RPC) | Merchant Moe DEX | Pool reserves (token0, token1) | Per block | No |
| Lendle Pool (RPC) | Lendle Lending | Total supply (TVL proxy) | Per block | No |
| MantleIntelAudit.sol (RPC) | On-chain Audit | Finding history, subscriptions | Immutable | No |
| 60+ Nansen-style labels | Wallet Intel | CEX/VC/MEV/Protocol classification | Static (v1) | No |
| Cross-protocol correlation | Multi-protocol | Simultaneous protocol activity | Per block | No |

**8 distinct data sources — zero centralized API keys required for production operation.**

---

## Deployed Contracts

| Contract | Network | Address | Explorer |
|----------|---------|---------|----------|
| MantleIntelAudit v2.0 | Mantle Sepolia Testnet | `0x7fAb1E37d992109d3aA747703436ff4e261391b7` | [View](https://sepolia.mantlescan.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7) |
| MantleIntelAgentNFT (ERC-8004) | Mantle Sepolia Testnet | `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C` | [View](https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C) |

**5 on-chain findings submitted** — `findingCount = 5`, Sourcify verified.  
**Mainnet deploy:** `npx hardhat run scripts/deploy.js --network mantle` (contract ready, awaiting mainnet MNT)

---

## Live Dashboard

**URL:** https://mantle-intel-agent.vercel.app

**Tabs:**
- **Live Feed** — Real-time findings with confidence bars, signal tier badges, lead-time estimates
- **Analytics** — Type breakdown, backtest metrics (F1=1.00), smart money stats, data source status
- **Investment Signals** — Sorted by signal tier (IMMEDIATE ACTION first), affected protocols, $ at stake
- **Protocol State** — Live mETH rate, Merchant Moe reserves, Lendle TVL, Pyth prices
- **Intel API** — Live JSON feed, on-chain subscription code, `getPublicFindings()` usage

---

## Backtest Results

> Full methodology and results: [`backtest/results_live.md`](./backtest/results_live.md)

```
═══════════════════════════════════════════════════════════
  MANTLE INTEL AGENT — BACKTEST RESULTS (seed=42, live RPC)
═══════════════════════════════════════════════════════════
  Precision:  100.00%   (0 false positives)
  Recall:     100.00%   (0 missed events)
  F1 Score:   1.0000
  Ground Truth Events: 5 (whale acc ×2, tx spike, smart money, value spike)
  Detection Methods: Z-Score (3.0σ) + Isolation Forest + Pattern Match
  Confidence Threshold: 0.75
  Multi-confirm boost: enabled (2+ methods → +0.04 confidence)
═══════════════════════════════════════════════════════════
  Signal Lead-Time Analysis (5 events):
    Whale Accumulation:  avg 1,200 blocks (~4hrs) before TVL impact
    Smart Money Inflow:  avg 2,400 blocks (~8hrs) before price action
    Value Spike:         avg 5 blocks before follow-on activity
    TX Spike:            immediate (0-block lag to catalyst)
═══════════════════════════════════════════════════════════
```

---

## Quickstart

```bash
# Clone & setup
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install -r requirements.txt

# Run pipeline (single cycle)
python -m agents.pipeline --mode once

# Run live (continuous, 6s poll)
python -m agents.pipeline --mode live

# Run backtest (seed=42, deterministic)
python backtest/backtest_live.py

# Start Telegram bot
TELEGRAM_BOT_TOKEN=your_token python -m bot.run_bot
```

**Environment variables (all optional — falls back to demo mode):**
```bash
MANTLE_RPC_URL=https://rpc.mantle.xyz      # or dedicated node
DASHSCOPE_API_KEY=your_key                  # Qwen-Max LLM for insight gen
TELEGRAM_BOT_TOKEN=your_token
AUDIT_PRIVATE_KEY=your_deployer_key         # for on-chain finding submission
```

---

## Scalability Plan

> Full roadmap: [`docs/ROADMAP.md`](./docs/ROADMAP.md)

| Phase | Timeline | Key Milestones |
|-------|----------|----------------|
| **Phase 0** — Hackathon | ✅ Complete | 5-agent pipeline, live API, on-chain audit, backtest |
| **Phase 1** — Mainnet | Q3 2026 | Dedicated RPC, The Graph subgraph, PostgreSQL, K8s |
| **Phase 2** — Multi-protocol | Q4 2026 | 25+ protocols, cross-chain bridge, LSTM ML upgrade |
| **Phase 3** — Subscription API | Q1 2027 | $99-999/mo tiers, 150+ subscribers, $55K MRR target |
| **Phase 4** — Protocol | 2027+ | Signal marketplace, MINTEL token, DAO governance |

---

## Business Potential

> Full investment thesis: [`docs/INVESTMENT_THESIS.md`](./docs/INVESTMENT_THESIS.md)

**Problem:** No purpose-built analytics tool exists for Mantle's $500M+ DeFi ecosystem.  
**Solution:** Autonomous, Mantle-native intelligence at $99-999/mo vs Nansen's $1,200/mo with less Mantle coverage.  
**Market:** $2.1B → $8.4B on-chain analytics TAM (32% CAGR). Mantle SAM: 500 institutional subscribers.  
**Revenue:** $660K ARR target by end of 2027 at 150 paying subscribers.  
**GTM:** 
1. Hackathon visibility → early adopter DMs
2. Protocol partnerships (Lendle, Agni, Merchant Moe as first B2B clients)
3. Mantle Foundation grant application (developer tooling category)
4. Conference presence (ETH Global, DeFi conferences)

---

## Agent Descriptions

### CollectorAgent (Stage 1)
Polls Mantle RPC every 6 seconds for new blocks. Extracts transactions, identifies large transfers (>$50k), labels wallet addresses. v3.0: Also polls Pyth oracle for MNT/USD, mETH contract for staking rate/supply, Merchant Moe pool reserves, Lendle total supply.

### AnomalyAgent (Stage 2)  
Stateful detector running 3 parallel pipelines on each block batch:
- **Z-Score**: Rolling mean/std over last N blocks, fires at |z| > 3.0σ
- **Isolation Forest**: Multi-dimensional (tx_count, value_mnt, large_tx_count, unique_senders), contamination=0.03, 150 estimators
- **Pattern Match**: Labeled wallet activity, smart money clustering, multi-wallet coordination
- **NEW v3.0**: mETH depeg (>50bps), Merchant Moe LP imbalance (>30%), cross-protocol correlation (3+ protocols simultaneously)

### SmartMoneyAgent (Stage 3)
Maintains wallet activity graph. 60+ Nansen-style labels across: CEX (Binance, Bybit, OKX, Gate.io, KuCoin), VC (Mirana, Jump, a16z, Multicoin, Polychain), Mantle Foundation, DeFi protocols, MEV bots, known alpha wallets. Tier system: T1=Institutional, T2=Notable, T3=Monitored. `/compare` API for signal history queries.

### InsightAgent (Stage 4)
Generates investment-grade narratives. v3.0 templates include signal tier, lead-time estimates, protocol-specific context (Merchant Moe, mETH, Lendle, Agni), and VC-facing language. Uses Qwen-Max LLM (when API key present) or deterministic templates.

### AuditAgent (Stage 5)
SHA256-hashes every finding and submits to `MantleIntelAudit.sol`. Supports `getPublicFindings(offset, limit)` and subscriber registry (`subscribe()`/`unsubscribe()`). ERC-8004 NFT identity for the agent itself.

---

## On-Chain Verification

```bash
# Verify contract on Sourcify
curl https://sourcify.dev/server/check-all-by-addresses?addresses=0x7fAb1E37d992109d3aA747703436ff4e261391b7&chainIds=5003

# Read on-chain findings (no wallet needed)
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "getPublicFindings(uint256,uint256)(string[])" 0 5 \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

---

## ERC-8004 Agent NFT

The pipeline's identity is minted as an ERC-8004 NFT — the emerging standard for autonomous AI agent identities on EVM chains.

- **Contract:** `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C` (Mantle Sepolia)
- **Mint TX:** `0x3b5ffc...` | Block 39815592 | Status: Success
- **Significance:** Agent can cryptographically prove its identity, build reputation, and eventually participate in signal marketplaces

---

## API Reference

**Live Feed:**
```
GET https://mantle-intel-agent.vercel.app/api/live-feed
GET https://mantle-intel-agent.vercel.app/api/live-feed?format=json
GET https://mantle-intel-agent.vercel.app/api/live-feed?stream=1  (SSE)
```

**Protocol State:**
```
GET https://mantle-intel-agent.vercel.app/api/protocol-state
```

**Backtest Results:**
```
GET https://mantle-intel-agent.vercel.app/api/backtest
```

Response includes: `demo_mode: false`, `source: mantle_rpc_live`, findings array with `investment_signal`, `signal_tier`, `lead_time_hours`, `affected_protocols`.

---

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show pipeline status, last 5 findings |
| `/compare whale` | Compare whale signal history (last 50 signals) |
| `/compare smart_money` | Smart money signal stats |
| `/compare cex` | CEX flow breakdown |
| `/verify <hash>` | Verify a finding hash on-chain |
| `/status` | Live pipeline health, last block, data source status |

---

## Project Structure

```
mantle-intel-agent/
├── agents/
│   ├── collector/collector_agent.py   # Stage 1: RPC + Pyth + mETH + Merchant Moe
│   ├── anomaly/anomaly_agent.py       # Stage 2: 10 anomaly detectors
│   ├── smart_money/smart_money_agent.py # Stage 3: 60+ wallet labels, clustering
│   ├── insight/insight_agent.py       # Stage 4: VC-grade investment narratives
│   ├── audit/audit_agent.py           # Stage 5: on-chain finding submission
│   └── pipeline.py                    # Orchestrator
├── bot/
│   ├── telegram_bot.py                # Telegram bot + /compare
│   └── discord_webhook.py             # Discord webhook (no bot token needed)
├── contracts/
│   ├── MantleIntelAudit.sol           # On-chain audit log + subscriber registry
│   └── src/MantleIntelAudit.sol       # Source (Sourcify verified)
├── dashboard/src/                     # React + Vite dashboard (Vercel)
├── backtest/
│   ├── backtest_live.py               # Live RPC backtest (seed=42)
│   └── results_live.md                # Backtest results + methodology
├── docs/
│   ├── ROADMAP.md                     # Post-hackathon scalability plan
│   └── INVESTMENT_THESIS.md           # Mirana-facing TAM/PMF/revenue thesis
└── scripts/
    └── submit_findings_testnet.py     # Submit findings to testnet contract
```

---

## License

MIT — built for The Turing Test Hackathon 2026 (Mantle Network / DoraHacks).  
**GitHub:** [sodiq-code/mantle-intel-agent](https://github.com/sodiq-code/mantle-intel-agent)  
**Live:** https://mantle-intel-agent.vercel.app  
**Track:** Alpha & Data Track (Mirana Ventures) · Target: $100K prize pool
