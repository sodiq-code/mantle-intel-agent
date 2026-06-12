# Mantle Intel Agent — Judge Verification Guide

> **5-minute verification checklist** for Turing Test Hackathon 2026 judges.  
> Alpha & Data Track · Mirana Ventures · $100k Prize Pool

---

## 1. Live Dashboard (30 seconds)

**URL:** https://mantle-intel-agent.vercel.app

Open it. You'll see:
- Real-time anomaly findings from Mantle mainnet blocks
- 6 tabs: Findings · Investment Signals · Protocol State · Analytics · Audit Log · Intel API
- Pipeline health panel (5 agents, all green)
- `AGENT v5.0` in top-right

---

## 2. Live API (1 minute)

```bash
# Real-time anomaly feed (demo_mode: false = live blocks)
curl "https://mantle-intel-agent.vercel.app/api/live-feed?format=json" | python3 -m json.tool

# Protocol state (mETH ratio, Moe reserves, Lendle TVL — all on-chain)
curl "https://mantle-intel-agent.vercel.app/api/protocol-state" | python3 -m json.tool
```

Expected: `"demo_mode": false`, real Mantle block numbers, live timestamps.

---

## 3. On-Chain Verification (2 minutes)

### Deployed Contracts (Mantle Sepolia Testnet)

| Contract | Address | Purpose |
|----------|---------|---------|
| **MantleIntelAudit** | `0x7fAb1E37d992109d3aA747703436ff4e261391b7` | Immutable audit trail (20 findings) |
| **MantleIntelAgentNFT** | see `contracts/` | ERC-8004 agent NFT |
| **SignalRegistry** | `0xdf07...` | On-chain signal subscriptions |
| **SmartMoneyTracker** | `0xB1ba...` | Smart money registry |
| **AlertLog** | `0x1Ce1...` | Alert log ledger |

### Verify 20 on-chain findings:

```bash
# Using Foundry cast
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "findingCount()(uint256)" \
  --rpc-url https://rpc.sepolia.mantle.xyz
# → 20

# Read finding #1
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "getPublicFindings(uint256,uint256)(tuple[])" 0 5 \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

**MantleScan Explorer:**  
https://explorer.sepolia.mantle.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7

### ERC-8004 NFT Mint TX (on-chain proof):
- TX: `0x3b5ffc...`  
- Block: `39815592`  
- Status: ✅ Success  
- Explorer: https://explorer.sepolia.mantle.xyz/tx/0x3b5ffc50e42b2ee4e13abe42e02b9e0b66a9e09f5f1e95e2ed31ab748dca59d5

---

## 4. Run Backtest Locally (2 minutes)

```bash
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install numpy scikit-learn scipy structlog

python scripts/run_backtest.py
```

Expected output:
```
Precision: 1.0000  (100%)
Recall:    1.0000  (100%)
F1:        1.0000
seed=42, deterministic — anti-gaming proof
```

---

## 5. Run Test Suite (1 minute)

```bash
pip install pytest
python -m pytest tests/ -v
# → 70 passed
```

Tests cover:
- Anomaly detection (30 tests) — z-score, Isolation Forest, whale, mETH depeg, Merchant Moe
- Hash integrity (15 tests) — tamper evidence, bytes32 encoding, pre-commit sealing
- Backtest (17 tests) — precision/recall, generalisation across 5 random seeds
- Smart money (4 tests) — labeled wallet registry, dict/object compat

---

## 6. Telegram Bot

**Bot:** @MantleIntelBot  
**Token:** `8261331880:AAEGeltCkbDhGPEs1lS4eAuRTo6HkTIcMPs`  
**Chat ID:** `6774697368`

Commands: `/status`, `/findings`, `/compare`, `/help`

---

## 7. What Makes This Stand Out

| Criterion | Evidence |
|-----------|---------|
| **On-chain verifiability** | 20 findings, 5 contracts, SHA256 tamper-evident hashing |
| **Real data, not mock** | `demo_mode: false`, live RPC calls to Mantle mainnet |
| **ML rigor** | Isolation Forest + z-score + blind holdout validation (seeds 7, 13, 31) |
| **Investment utility** | Investment signals tab, lead-time tracking, Mirana-grade UX |
| **Autonomous pipeline** | 5-agent Python pipeline, Telegram alerts, Vercel edge API |
| **Ecosystem depth** | mETH depeg, Merchant Moe LP, Lendle TVL, Pyth oracle, bridge events |

---

*Deployer wallet:* `0xB47Ba223B73980E69AEF53B0d202F9785698DAEa`  
*GitHub:* https://github.com/sodiq-code/mantle-intel-agent  
*Dashboard:* https://mantle-intel-agent.vercel.app
