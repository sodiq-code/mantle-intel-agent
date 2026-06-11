# Mantle Intel Agent

**Autonomous on-chain intelligence for Mantle Network** — anomaly detection, smart money tracking, and fully verifiable AI findings recorded on-chain.

Built for the **[Find Evil! 2026 Hackathon](https://findevil.devpost.com)** · **Alpha & Data Track (Mirana Ventures)**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Mantle Network](https://img.shields.io/badge/Network-Mantle-green)](https://mantle.xyz)

---

## What It Does

Mantle Intel Agent runs a **5-agent autonomous pipeline** that:

1. **Collects** Mantle blockchain data in real-time (blocks, transactions, large transfers)
2. **Detects** anomalous patterns using Isolation Forest + z-score statistical methods
3. **Tracks** smart money — clusters wallets, identifies institutional flows, flags coordinated activity
4. **Generates** institutional-grade narrative insights via Qwen-Max LLM
5. **Records** every finding's SHA256 hash on-chain for full, independent verifiability

Findings are surfaced via **Telegram bot alerts** and a **public web dashboard**.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    MANTLE INTEL AGENT                        │
├──────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Mantle RPC · Mantle Explorer · DeFiLlama · Dune     │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                  │
│  AGENT PIPELINE (Python + LangGraph-style)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Collector Agent   — ingests Mantle blocks        │    │
│  │ 2. Anomaly Agent     — Isolation Forest + z-score   │    │
│  │ 3. Smart Money Agent — wallet clustering + labels   │    │
│  │ 4. Insight Agent     — Qwen-Max narrative gen       │    │
│  │ 5. Audit Agent       — writes finding hash on-chain │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                  │
│  OUTPUT LAYER                                                │
│  ┌───────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ Telegram Bot  │  │ Web Dashboard  │  │ On-Chain Log  │  │
│  │ /latest       │  │ (public URL)   │  │ MantleIntel   │  │
│  │ /verify <hash>│  │ findings +     │  │ Audit.sol     │  │
│  └───────────────┘  │ audit trail    │  └───────────────┘  │
│                     └────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Deployed Contract

| Network | Address | Explorer |
|---------|---------|---------|
| Mantle Mainnet | `TBD — deploy with hardhat` | [mantlescan.xyz](https://mantlescan.xyz) |
| Mantle Testnet | [`0x03C88A1060626581854DB94e955a6be291782abb`](https://sepolia.mantlescan.xyz/address/0x03C88A1060626581854DB94e955a6be291782abb) | [sepolia.mantlescan.xyz](https://sepolia.mantlescan.xyz/address/0x03C88A1060626581854DB94e955a6be291782abb) |

> Contract: `MantleIntelAudit.sol` — stores SHA256 hash of every agent finding. Fully auditable, not a black box.

---

## Anomaly Types Detected

| Type | Method | Description |
|------|--------|-------------|
| `whale_accumulation` | Pattern Match | Known wallet large flows into DeFi protocols |
| `whale_distribution` | Pattern Match | Large outflows from Mantle DeFi |
| `smart_money_inflow` | Wallet Clustering | Coordinated unlabeled wallet → protocol activity |
| `tx_spike` | Z-Score (σ=2.5) | Transaction volume statistical outlier |
| `value_spike` | Z-Score (σ=2.5) | MNT transfer value statistical outlier |
| `multivariate_anomaly` | Isolation Forest | Multi-dimensional block-level outlier |

---

## Backtest Results

See [`backtest/results.md`](backtest/results.md) for full metrics.

| Metric | Value |
|--------|-------|
| Precision | **see results.md** |
| Recall | **see results.md** |
| F1 Score | **see results.md** |
| Detection lag | < 2 blocks avg |
| Confidence threshold | 0.60 |

Run your own backtest:
```bash
python main.py --backtest
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for dashboard)

### 1. Clone & install

```bash
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
```

### 2. Run demo (no keys required)

```bash
python main.py --cycles 3
```

Works out of the box in demo mode — generates realistic simulated Mantle data with injected anomalies.

### 3. Run with Telegram bot

```bash
# Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
python main.py --bot --loop
```

### 4. Deploy contract (Mantle Testnet)

```bash
cd contracts
npm install
# Set DEPLOYER_PRIVATE_KEY in .env
npx hardhat run scripts/deploy.js --network mantle_testnet
# Note the deployed address, add to .env as AUDIT_CONTRACT_ADDRESS
npx hardhat verify --network mantle_testnet <CONTRACT_ADDRESS>
```

### 5. Run web dashboard

```bash
cd dashboard
npm install
npm run dev
# Open http://localhost:5173

# Build for production:
npm run build
# Then start API server:
cd ..
uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## Mantle Protocols Tracked

- [Merchant Moe](https://merchantmoe.com) — DEX
- [Agni Finance](https://agni.finance) — DEX
- [Lendle](https://lendle.xyz) — Lending
- [FusionX](https://fusionx.finance) — DEX
- [Mantle LSD](https://mntl.com) — Liquid staking

---

## Verifiability

Every finding is independently verifiable:

1. Agent computes SHA256 of finding JSON → `finding_hash`
2. `MantleIntelAudit.sol::recordFinding()` stores hash on Mantle
3. Anyone can call `verifyFinding(hash)` on-chain to confirm:
   - The finding existed at block X
   - The confidence score was Y%
   - The agent recorded it at timestamp Z

No black box. No trust required.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent pipeline | Python 3.11 + asyncio |
| LLM | Qwen-Max (Alibaba DashScope) |
| Anomaly detection | scikit-learn (Isolation Forest), scipy (z-score) |
| On-chain reads | web3.py |
| Smart contract | Solidity 0.8.20 + Hardhat |
| API server | FastAPI + uvicorn |
| Web dashboard | React 18 + Tailwind CSS + Vite |
| Telegram bot | python-telegram-bot v21 |

---

## Environment Variables

See [`.env.example`](.env.example) for full list.

Key variables:
```
MANTLE_RPC_URL=https://rpc.mantle.xyz
AUDIT_CONTRACT_ADDRESS=0x...
AGENT_PRIVATE_KEY=0x...
DASHSCOPE_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

---

## Project Structure

```
mantle-intel-agent/
├── agents/
│   ├── collector/         # Stage 1 — Mantle block ingestion
│   ├── anomaly/           # Stage 2 — Isolation Forest + z-score
│   ├── smart_money/       # Stage 3 — Wallet clustering
│   ├── insight/           # Stage 4 — Qwen-Max narrative gen
│   ├── audit/             # Stage 5 — On-chain hash recording
│   └── pipeline.py        # Orchestrator
├── contracts/
│   ├── MantleIntelAudit.sol   # Audit log contract
│   ├── hardhat.config.js
│   └── scripts/deploy.js
├── bot/
│   └── telegram_bot.py    # Telegram bot + alerts
├── dashboard/             # React web dashboard
├── backtest/
│   ├── backtest.py        # Backtest runner
│   └── results.md         # Metrics output
├── data/                  # Runtime data (findings.jsonl, dashboard.json)
├── main.py                # CLI entry point
├── server.py              # FastAPI server
└── requirements.txt
```

---

## Author

**Kudirat Oyindamola** — Platform & DevOps Engineer
- GitHub: [@sodiq-code](https://github.com/sodiq-code)
- Hackathon: [Find Evil! 2026](https://findevil.devpost.com)

---

*Mantle Intel Agent is open-source and not financial advice.*
