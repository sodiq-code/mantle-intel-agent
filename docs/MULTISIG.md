# Multi-Sig Setup Guide — MantleIntelAudit Agent Wallet

> **P3-32:** Currently, a single EOA (Externally Owned Account) holds the `authorizedAgent` role and can call `recordFinding()`. If this key is compromised, an attacker could flood the contract with fake findings, destroying audit trail integrity. This guide documents the recommended multi-sig upgrade path.

---

## Current Architecture

```
Single EOA (private key in keystore.json)
    │
    │ authorizedAgent = true
    ▼
MantleIntelAudit.sol
    └── recordFinding() — only authorized agents
```

**Risk:** Single point of failure. Key compromise = audit trail compromise.

---

## Recommended Architecture: Gnosis Safe (2-of-3)

```
┌──────────────────────────────────────┐
│  Gnosis Safe (2-of-3)                │
│  Signers:                            │
│    1. Deployer wallet (Jimoh Tech)   │
│    2. Operations wallet (team)       │
│    3. Emergency wallet (offline)     │
│                                      │
│  authorizedAgent = true              │
└───────────────┬──────────────────────┘
                │
                │ recordFinding() requires 2-of-3 signatures
                ▼
        MantleIntelAudit.sol
```

**Benefits:**
- No single key can compromise the audit trail
- 2-of-3 ensures team continuity even if one key is lost
- Emergency wallet kept offline for disaster recovery
- Full transaction history on-chain (Safe transparency)

---

## Setup Steps

### Step 1: Deploy Gnosis Safe on Mantle Sepolia

```bash
# Gnosis Safe is deployed at a deterministic address on most EVM chains
# Mantle Sepolia Safe factory: https://safe-transaction-sepolia.mantle.xyz
# Or use the Safe SDK:
```

```python
# Using safe-eth-py (Python SDK)
from gnosis.safe import Safe
from gnosis.eth import EthereumClient

ethereum_client = EthereumClient("https://rpc.sepolia.mantle.xyz")

# Deploy a new 2-of-3 Safe
owners = [
    "0x...",  # Deployer wallet
    "0x...",  # Operations wallet
    "0x...",  # Emergency wallet
]
threshold = 2

safe = Safe.create(
    ethereum_client=ethereum_client,
    owners=owners,
    threshold=threshold,
    deployer_account=deployer_account,  # Your current EOA
)
print(f"Safe deployed at: {safe.address}")
```

### Step 2: Transfer authorizedAgent Role to Safe

After deploying the Safe, call `authorizeAgent(safe_address, "GnosisSafe-2of3")` from the contract owner.

```javascript
// Using Hardhat console or script
const audit = await ethers.getContractAt("MantleIntelAudit", "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b");
await audit.authorizeAgent(safeAddress, "GnosisSafe-2of3");
```

### Step 3: Revoke Old EOA Authorization

```javascript
await audit.revokeAgent(oldEoaAddress);
```

### Step 4: Update Pipeline Configuration

In the pipeline, update `audit_agent.py` to submit transactions through the Safe:

```python
# Option A: Use Safe SDK for transaction batching
from gnosis.safe import Safe
from gnosis.safe.api import TransactionServiceApi

# Option B: Use Gelato Relay for gasless Safe transactions
# (Recommended — avoids needing to fund the Safe with MNT for gas)

# Option C: Simple approach — pre-approve EOA as Safe delegate
# The EOA can propose transactions, but 2-of-3 must confirm
```

---

## Gasless Option: Gelato Relay

Gnosis Safe + Gelato Relay enables **gasless `recordFinding()` calls**:

1. The pipeline submits a meta-transaction to Gelato Relay
2. Gelato pays gas and submits to the Safe
3. Safe executes `recordFinding()` as an auto-approved delegate
4. No MNT needed in the Safe — Gelato bills off-chain

This is the recommended production path.

---

## Security Checklist

| Check | Status |
|-------|--------|
| Safe deployed on Mantle Sepolia | ☐ |
| Safe is 2-of-3 (minimum) | ☐ |
| authorizedAgent transferred to Safe | ☐ |
| Old EOA revoked from authorizedAgents | ☐ |
| Emergency wallet stored offline | ☐ |
| Safe address documented in SECURITY.md | ☐ |
| Pipeline updated to submit via Safe | ☐ |
| Tested recordFinding() through Safe | ☐ |

---

## Timeline

| Phase | When | What |
|-------|------|------|
| Phase 0 (Now) | Hackathon | Single EOA with encrypted keystore |
| Phase 1 | Mainnet launch | Deploy 2-of-3 Gnosis Safe on Mantle mainnet |
| Phase 2 | Production | Add Gelato Relay for gasless Safe transactions |
| Phase 3 | Scale | Upgrade to 3-of-5 Safe with DAO governance |

---

*This document is a reference for the multi-sig upgrade. Implementation should be prioritized before mainnet deployment.*
