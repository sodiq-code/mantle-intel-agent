# Mantle Intel Agent

[![Live Demo](https://img.shields.io/badge/Live%20Demo-mantle--intel--agent.vercel.app-00ff88?style=for-the-badge)](https://mantle-intel-agent.vercel.app)
[![Audit Contract](https://img.shields.io/badge/Audit%20Contract-Mantle%20Sepolia-green?style=for-the-badge)](https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b)
[![Sourcify Verified](https://img.shields.io/badge/Sourcify-Exact%20Match%20✓-brightgreen?style=for-the-badge)](https://sourcify.dev/#/lookup/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b)
[![On-Chain](https://img.shields.io/badge/On--Chain-Live%20Feed-orange?style=for-the-badge)](https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b)
[![Backtest](https://img.shields.io/badge/Backtest-Methodology%20In%20Development-blue?style=for-the-badge)](./backtest/results_live.md)

> **Autonomous 5-agent AI pipeline delivering real-time on-chain intelligence and automated incident response for the Mantle Network ecosystem.**
>
> Real-time anomaly detection across live Mantle mainnet blocks · SHA-256 hashed findings permanently recorded on-chain · 10 anomaly detection methods · Multi-Confirm consensus gate · Encrypted Keystore architecture · Incident Lifecycle Management (Opened → Escalated → Resolved) · `demo_mode: false` at all times.

---

## Live Dashboard

**[mantle-intel-agent.vercel.app](https://mantle-intel-agent.vercel.app)** — Always live. Always real data.

![Mantle Intel Agent — Live Dashboard](./docs/screenshots/proofs/live_dashboard_real.png)

*Real-time anomaly detection with findings logged to the `MantleIntelAudit` smart contract. The `MantleIntelAudit` contract address is displayed inline and linkable on-chain. Finding count updates live as the pipeline runs — check the contract on Mantlescan for the current total.*

---

## Core Capabilities

Mantle Intel Agent is a fully autonomous 5-agent Python pipeline that continuously monitors the Mantle L2 ecosystem and surfaces **professional-grade security and trading signals**:

1. **Collects** — Polls Mantle mainnet RPC every 6 seconds. Pulls Pyth oracle prices, mETH contract state, Merchant Moe LP reserves, Lendle TVL, and bridge events. Zero centralized API keys required.
2. **Detects** — Runs 10 anomaly detectors per block: Z-Score (3.0σ), Isolation Forest (contamination=0.03), whale pattern matching, mETH depeg, LP imbalance, cross-protocol correlation, bridge spikes, MEV activity, smart money clustering, and multivariate signals.
3. **Labels** — 60+ Nansen-style wallet classifications: CEX, VC, Mantle DeFi protocols, MEV bots, and known alpha wallets.
4. **Manages Incidents** — Correlates related anomalies into a unified Incident ID. Tracks state across `OPENED`, `ESCALATED`, and `RESOLVED` to eliminate alert fatigue.
5. **Records** — Every finding is SHA256-hashed and submitted on-chain to `MantleIntelAudit.sol` using an encrypted keystore for maximum security.
6. **Alerts** — Telegram bot and Discord webhook utilizing evidence-based reporting structures (✓) and Anomaly Confidence scores. Sub-30 second latency.

---

## Architecture

> **Security Note:** The on-chain pipeline relies entirely on a locally encrypted `keystore.json` file. Plaintext private keys are never exposed in environment variables.

```text
CollectorAgent (Stage 1)
  │  Mantle RPC · Pyth Oracle · mETH Contract · Merchant Moe · Lendle · Bridge
  ▼
AnomalyAgent (Stage 2)
  │  Z-Score (3.0σ) · Isolation Forest · Whale Pattern Matching
  │  mETH Depeg · LP Imbalance · Cross-Protocol Correlation · Bridge Spike
  ▼
SmartMoneyAgent (Stage 3)
  │  60+ Nansen-style wallet labels · Tier 1/2/3 system
  ▼
InsightAgent & IncidentManager (Stage 4)
  │  Evidence-backed Incident Reports · State tracking (Escalated/Resolved)
  │  Lead-time estimates · Protocol-specific context
  ▼
AuditAgent (Stage 5)
  │  SHA256 hash → MantleIntelAudit.sol (via Encrypted Keystore)
  │  ERC-8004 NFT identity
  │
  ├── Telegram Bot   /start · /compare · /verify · /status
  ├── Discord Webhook   Rich incident reporting
  ├── React Dashboard   Live Findings UI (Syncs with onchain_submissions.json)
  └── REST API   /api/live-feed · /api/protocol-state
```

---

## Deployed Contracts

| Contract | Network | Address | Explorer |
|---|---|---|---|
| `MantleIntelAudit v2.0` | Mantle Sepolia | `0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b` | [View on Mantlescan](https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b) |
| `MantleIntelAgentNFT` | Mantle Sepolia | `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C` | [View on Mantlescan](https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C) |

Sourcify-verified with exact-match status on both creation and runtime bytecode.

```bash
# Verify on Sourcify — returns "perfect"
curl "https://sourcify.dev/server/check-all-by-addresses?addresses=0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b&chainIds=5003"

# Read on-chain findings — no wallet required
cast call 0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b \
  "getPublicFindings(uint256,uint256)(string[])" 0 5 \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

---

## On-Chain Audit Trail

Every signal the system fires is permanently recorded:

1. `AuditAgent` computes `SHA256(finding_json)`
2. Automatically pushes to `MantleIntelAudit.sol` using the encrypted keystore.
3. Dashboard synchronizes real-time off-chain data with the immutable `onchain_submissions.json` log.
4. Each entry links directly to its Mantlescan transaction.

---

## Automated Incident Reports

Instead of raw alerts, the bot formats data into professional Incident Reports emphasizing evidence and data confidence:

```text
🚨 MANTLE INTEL INCIDENT 🚨

Title: Elevated transaction activity detected on Mantle.
Incident ID: TX-20260717-001
Status: 🟠 Escalated
Timeframe: Block 41387000 to 41387006 (Duration: 6 blocks)

Evidence
✓ Transaction count (12) exceeded recent baseline (2)
✓ Statistically significant spike (z=4.38σ)
✓ Multivariate outlier detected (tx volume + value + wallet diversity)

Detection Confidence: 98% (Anomaly Detection)

Action: Monitor for additional anomalous blocks.
Trace: 0x5394e08779f1...
```

---

## Quickstart

```bash
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install -r requirements.txt

# 1. Generate Encrypted Keystore for Secure Submission
python scripts/generate_keystore.py
# (This creates keystore.json. Set your KEYSTORE_PASSWORD in .env)

# 2. Run Single Pipeline Cycle
python -m agents.pipeline --mode once

# 3. Live Continuous Mode (6s poll)
python -m agents.pipeline --mode live

# 4. Telegram Bot Monitoring
python -m bot.run_bot
```

### Environment Configuration (`.env`)

All keys are optional except for the Keystore configuration if you wish to write to the blockchain.

```bash
MANTLE_RPC_URL=https://rpc.mantle.xyz
TELEGRAM_BOT_TOKEN=your_token
KEYSTORE_PATH=keystore.json
KEYSTORE_PASSWORD=your_secure_password
```

---

## REST API & Composable On-Chain Subscriptions

Any trading bot, protocol, or dashboard can subscribe to Mantle Intel Agent's signal feed directly on-chain — no API key, no centralized gatekeeping.

```solidity
// Subscribe your contract or wallet to the intel feed
interface IMantleIntelAudit {
    function subscribe(string calldata subscriptionType) external;
    function getPublicFindings(uint256 offset, uint256 limit) external view returns (string[] memory);
}

IMantleIntelAudit intel = IMantleIntelAudit(0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b);
intel.subscribe("all");
```

**Live API Endpoints:**
```bash
# Live findings snapshot
GET https://mantle-intel-agent.vercel.app/api/live-feed?format=json

# Real-time SSE stream
GET https://mantle-intel-agent.vercel.app/api/live-feed?stream=1
```

---

*MIT License · Built for the Mantle Network ecosystem*

<p align="center">Built by <strong>JIMOH SODIQ</strong></p>
