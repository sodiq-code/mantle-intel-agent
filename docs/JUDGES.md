# Mantle Intel Agent — 5-Minute Verification Walkthrough

> **For Grant Judges & Reviewers**  
> This document provides step-by-step instructions to independently verify every claim in the Mantle Intel Agent grant application.  
> **Estimated time: 5 minutes.**  
> **No setup required** — all checks use public endpoints.

---

## Overview

| Claim | Verification Method | Time |
|-------|-------------------|------|
| Smart contract deployed & verified | Mantlescan + Sourcify | 30s |
| On-chain findings exist | Contract `findingCount()` call | 30s |
| Finding hashes are verifiable | `verifyFinding()` call | 30s |
| Live API serves real data | curl /api/live-feed | 30s |
| Dashboard is live | Open URL | 15s |
| Backtest results are reproducible | Review methodology | 60s |
| AI agent NFT exists on-chain | Mantlescan NFT | 30s |
| Contract has zero Slither findings | Review audit report | 30s |

---

## Step 1: Verify Contract Deployment (30s)

The `MantleIntelAudit.sol` contract is deployed on Mantle Sepolia testnet.

**Contract address:** `0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b`

### Option A: Mantlescan
Open in your browser:
```
https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b
```
✅ **Verify:** You see the contract page with code tab, showing verified Solidity source.

### Option B: Sourcify (independent verification)
```
https://sourcify.dev/#/lookup/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b
```
✅ **Verify:** Sourcify confirms "Full Match" — the deployed bytecode exactly matches the source code in our GitHub repo.

### Option C: RPC call (command line)
```bash
curl -s -X POST https://rpc.sepolia.mantle.xyz \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b","latest"],"id":1}' | python3 -c "import sys,json;r=json.load(sys.stdin);print('✅ Contract has code' if len(r['result'])>10 else '❌ No code found')"
```

---

## Step 2: Verify On-Chain Findings Exist (30s)

The contract should have at least 5 findings recorded (from our live pipeline runs).

### Using Mantlescan "Read Contract"
1. Go to: `https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b#readContract`
2. Click **`findingCount`**
3. ✅ **Verify:** The returned number is ≥ 5

### Using RPC (command line)
```bash
# Call findingCount() — function selector: 0x3e5548cd
curl -s -X POST https://rpc.sepolia.mantle.xyz \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_call","params":[{"to":"0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b","data":"0x3e5548cd"},"latest"],"id":1}' | python3 -c "import sys,json;r=json.load(sys.stdin);n=int(r['result'],16);print(f'✅ Finding count: {n}' if n>0 else '❌ No findings found')"
```

---

## Step 3: Verify a Specific Finding Hash (30s)

Every finding recorded on-chain has a SHA256 hash that can be independently verified.

### Using Mantlescan "Read Contract"
1. Go to the **Read Contract** tab (link above)
2. Click **`verifyFinding`**
3. Paste this finding hash: `0x0000000000000000000000000000000000000000000000000000000000000001`  
   *(Replace with an actual finding hash from Step 2's finding data)*
4. ✅ **Verify:** Returns `(verified: true, findingId, timestamp, confidence)`

### Using the API
```bash
curl -s https://mantle-intel-agent.vercel.app/api/audit-log | python3 -m json.tool | head -20
```
✅ **Verify:** You see finding records with `hash`, `confidence`, and `tx_hash` fields.

---

## Step 4: Verify Live API (30s)

### Live Feed
```bash
curl -s https://mantle-intel-agent.vercel.app/api/live-feed | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"demo_mode: {data.get('demo_mode', 'N/A')}\")
print(f\"Findings count: {len(data.get('latest_findings', []))}\")
if data.get('latest_findings'):
    f = data['latest_findings'][0]
    print(f\"Latest finding: type={f.get('type')}, block={f.get('block')}, confidence={f.get('confidence')}\")
print('✅ Live API serving real data' if data.get('demo_mode') == False else '⚠️ Running in demo mode')
"
```

### Protocol State
```bash
curl -s https://mantle-intel-agent.vercel.app/api/protocol-state | python3 -m json.tool | head -15
```
✅ **Verify:** Returns real mETH ratio, Merchant Moe reserves, and Lendle TVL data.

---

## Step 5: Verify Dashboard (15s)

Open in your browser:
```
https://mantle-intel-agent.vercel.app
```
✅ **Verify:**
- Dashboard loads with live data (not "Loading..." or errors)
- You see anomaly findings in the Live Feed tab
- Protocol state shows mETH ratio, Moe reserves, Lendle TVL
- "On-Chain" tab shows audit log entries with tx hashes

---

## Step 6: Verify Backtest Reproducibility (60s)

The backtest results (Precision=100%†, Recall=92.9%) are computed on real Mantle mainnet blocks and are deterministic.

1. **Review the data:** `backtest/results_live.json` in the repo
2. **Review the methodology:** `docs/RISK.md` Section 2
3. **Key facts to verify:**
   - Block range: 96,526,081 → 96,526,580 (395 blocks — verifiable on Mantlescan)
   - 14 ground-truth events, 13 detected, 0 false positives
   - Deterministic: seed=42 produces identical results every run

```bash
# Check backtest results in the repo
curl -s https://raw.githubusercontent.com/sodiq-code/mantle-intel-agent/main/backtest/results_live.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Precision: {data.get('precision', 'N/A')}%\")
print(f\"Recall: {data.get('recall', 'N/A')}%\")
print(f\"F1: {data.get('f1', 'N/A')}\")
print(f\"True Positives: {data.get('true_positives', 'N/A')}\")
print(f\"False Positives: {data.get('false_positives', 'N/A')}\")
"
```

---

## Step 7: Verify Agent NFT (30s)

The ERC-8004 agent identity NFT is minted on Mantle Sepolia.

**NFT contract:** `0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C`
**Minted at block:** 39815592

```
https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C
```
✅ **Verify:** You see the NFT contract with a token minted (tokenId = 1).

---

## Step 8: Review Security Audit (30s)

The contract has been analyzed with Slither v0.11.5.

1. Read: `docs/SECURITY.md`
2. **Result: 0 Critical / 0 High / 0 Medium findings**
3. The 1 LOW finding is a false positive (boolean `exists` field misidentified as timestamp)
4. 2 INFO findings are standard (solc version notes, gas optimization suggestion)

✅ **Verify:** No actionable security vulnerabilities.

---

## Quick One-Liner Verification

If you're short on time, run this single command to verify the most critical claims:

```bash
echo "=== Contract Code ===" && \
curl -s -X POST https://rpc.sepolia.mantle.xyz \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b","latest"],"id":1}' | python3 -c "import sys,json;r=json.load(sys.stdin);print('✅ Deployed' if len(r.get('result',''))>10 else '❌ Not found')" && \
echo "=== Finding Count ===" && \
curl -s -X POST https://rpc.sepolia.mantle.xyz \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_call","params":[{"to":"0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b","data":"0x3e5548cd"},"latest"],"id":1}' | python3 -c "import sys,json;r=json.load(sys.stdin);n=int(r['result'],16);print(f'✅ {n} findings on-chain' if n>0 else '❌ No findings')" && \
echo "=== Live API ===" && \
curl -s https://mantle-intel-agent.vercel.app/api/live-feed | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'✅ demo_mode={d.get(\"demo_mode\")}, {len(d.get(\"latest_findings\",[]))} findings')" && \
echo "=== Done ==="
```

---

## Summary Checklist

| # | Check | Method | Status |
|---|-------|--------|--------|
| 1 | Contract deployed | Mantlescan / Sourcify | ☐ |
| 2 | Findings on-chain | findingCount() ≥ 5 | ☐ |
| 3 | Hash verification works | verifyFinding() | ☐ |
| 4 | Live API operational | /api/live-feed | ☐ |
| 5 | Dashboard renders | Browser visit | ☐ |
| 6 | Backtest reproducible | results_live.json | ☐ |
| 7 | NFT identity exists | Mantlescan NFT | ☐ |
| 8 | No security vulnerabilities | SECURITY.md | ☐ |

**If all 8 checks pass, every material claim in the grant application is independently verified.**

---

## Additional Resources

| Resource | URL |
|----------|-----|
| GitHub Repository | https://github.com/sodiq-code/mantle-intel-agent |
| Live Dashboard | https://mantle-intel-agent.vercel.app |
| Audit Contract (Sepolia) | https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b |
| NFT Contract (Sepolia) | https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C |
| Sourcify Verification | https://sourcify.dev/#/lookup/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b |
| Security Audit | `docs/SECURITY.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Risk Model | `docs/RISK.md` |
| Investment Thesis | `docs/INVESTMENT_THESIS.md` |
| Model Card | `docs/MODEL_CARD.md` |

---

† Point estimate from 14-observation backtest. Wilson 95% CI: [0.782, 1.000]. True precision at production scale may differ.

*Mantle Intel Agent — Built for The Turing Test Hackathon 2026 (Mantle Network)*  
*All verification endpoints are public and require no API keys or authentication.*
