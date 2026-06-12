# Mantle Intel Agent — On-Chain Proof Log

> Every transaction, every contract, every verifiable fact. Judges can reproduce all of this in under 5 minutes using only `cast` (Foundry) and a browser.

**Chain:** Mantle Sepolia Testnet (Chain ID: 5003)  
**RPC:** `https://rpc.sepolia.mantle.xyz`  
**Explorer:** https://explorer.sepolia.mantle.xyz  
**Deployer:** `0xB47Ba223B73980E69AEF53B0d202F9785698DAEa`

---

## Deployed Contracts

| Contract | Address | Block | Purpose |
|----------|---------|-------|---------|
| **MantleIntelAudit** | `0x7fAb1E37d992109d3aA747703436ff4e261391b7` | 39851391 | Immutable anomaly audit trail — 20 findings, SHA256 tamper-evident hashes |
| **MantleIntelAgentNFT** | `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C` | 39815592 | ERC-8004 agent identity NFT |
| **SignalRegistry** | `0xdf07...` | — | On-chain signal subscription registry |
| **SmartMoneyTracker** | `0xB1ba...` | — | Smart money wallet registry |
| **AlertLog** | `0x1Ce1...` | — | Agent alert ledger |

---

## ERC-8004 NFT Mint

The agent minted its on-chain identity as an ERC-8004 NFT before any findings were submitted, proving it is a registered autonomous agent — not a human manually submitting data.

| Field | Value |
|-------|-------|
| **TX Hash** | `0x3b5ffc50e42b2ee4e13abe42e02b9e0b66a9e09f5f1e95e2ed31ab748dca59d5` |
| **Block** | `39815592` |
| **Status** | ✅ Success |
| **Contract** | `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C` |
| **Explorer** | [View on MantleScan](https://explorer.sepolia.mantle.xyz/tx/0x3b5ffc50e42b2ee4e13abe42e02b9e0b66a9e09f5f1e95e2ed31ab748dca59d5) |

---

## On-Chain Findings (20 total)

All 20 anomaly findings from the autonomous pipeline are permanently recorded on `MantleIntelAudit.sol`. Each finding contains a SHA256 hash of the full finding data — any tampering (changing confidence, timestamp, description) produces a different hash.

### Verify with cast (Foundry)

```bash
# Check total finding count
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "findingCount()(uint256)" \
  --rpc-url https://rpc.sepolia.mantle.xyz
# Expected: 20

# Read first 5 findings (offset=0, limit=5)
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "getPublicFindings(uint256,uint256)(tuple[])" 0 5 \
  --rpc-url https://rpc.sepolia.mantle.xyz

# Read findings 5-10
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "getPublicFindings(uint256,uint256)(tuple[])" 5 5 \
  --rpc-url https://rpc.sepolia.mantle.xyz

# Read all 20 findings
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "getPublicFindings(uint256,uint256)(tuple[])" 0 20 \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

### Explorer Links
- **Contract:** https://explorer.sepolia.mantle.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7
- **Transactions:** https://explorer.sepolia.mantle.xyz/address/0x7fAb1E37d992109d3aA747703436ff4e261391b7?tab=txs

---

## Tamper-Evidence Verification

Every finding has a SHA256 hash that commits ALL fields: `finding_id`, `anomaly_type`, `confidence`, `block_height`, `timestamp`, `description`, `raw_metrics`, `investment_signal`. If any field changes, the hash changes.

**Verify independently:**

```python
import hashlib, json

# Example finding (read from chain, then verify locally)
finding = {
    "finding_id": "mantle-anomaly-...",
    "anomaly_type": "whale_accumulation",
    "confidence": 0.89,
    "block_height": 71234567,
    "timestamp": "2026-06-12T...",
    "description": "...",
    "raw_metrics": {...},
    "investment_signal": {...}
}

canonical = json.dumps(finding, sort_keys=True, separators=(",",":"))
sha256 = hashlib.sha256(canonical.encode()).hexdigest()
# Compare with hash stored on-chain — must match exactly
```

Run the full test suite to verify hash integrity:
```bash
python -m pytest tests/test_hash_integrity.py -v
# → 15 passed (tamper-evident, bytes32, pre-commit seal tests)
```

---

## Subscription Registry

The `MantleIntelAudit` contract supports on-chain signal subscriptions:

```bash
# Check if address is subscribed
cast call 0x7fAb1E37d992109d3aA747703436ff4e261391b7 \
  "isSubscribed(address)(bool)" 0xB47Ba223B73980E69AEF53B0d202F9785698DAEa \
  --rpc-url https://rpc.sepolia.mantle.xyz
```

---

## Live API Verification

```bash
# Real-time feed (demo_mode must be false = live Mantle blocks)
curl "https://mantle-intel-agent.vercel.app/api/live-feed?format=json" | python3 -m json.tool | grep demo_mode
# Expected: "demo_mode": false

# Protocol state (mETH ratio, Merchant Moe reserves, Lendle TVL — all on-chain)
curl "https://mantle-intel-agent.vercel.app/api/protocol-state" | python3 -m json.tool

# Backtest endpoint
curl "https://mantle-intel-agent.vercel.app/api/backtest" | python3 -m json.tool
# Expected: precision: 1.0, recall: 1.0, f1: 1.0
```

---

## Backtest Reproducibility

```bash
git clone https://github.com/sodiq-code/mantle-intel-agent
cd mantle-intel-agent
pip install numpy scikit-learn scipy structlog
python scripts/run_backtest.py
# → Precision: 1.0000 | Recall: 1.0000 | F1: 1.0000 | seed=42
```

Anti-gaming proof: backtest uses `seed=42` for deterministic splits. Holdout tested on seeds 7, 13, 31 — all pass (see `tests/test_backtest.py::test_generalises_across_seeds`).

---

## CI Pipeline

Every push to `main` triggers:
1. **70 Python tests** — anomaly, hash integrity, backtest, smart money
2. **Lint** — flake8 + ruff
3. **Integrity** — SHA256 hash audit verifying tamper-evidence
4. **Backtest** — live RPC backtest must pass F1 ≥ 0.9

[![CI](https://github.com/sodiq-code/mantle-intel-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/sodiq-code/mantle-intel-agent/actions)

---

*All transactions verifiable without any API key. No account required.*  
*Deployer wallet: `0xB47Ba223B73980E69AEF53B0d202F9785698DAEa`*
