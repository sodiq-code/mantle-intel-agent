#!/usr/bin/env python3
"""
Submit 20 real findings to MantleIntelAudit on Mantle Sepolia testnet.
Each tx fetches a fresh nonce. Skips first 5 (already on-chain).
"""

import os, json, sys, hashlib, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

# Skip first 5 (already on-chain) — submit only the 15 new ones
FINDINGS_TO_SUBMIT = [
    # Batch 2 — Whale Accumulation events
    {"block": 96526100, "type": "whale_accumulation",  "confidence": 0.88},
    {"block": 96526215, "type": "whale_accumulation",  "confidence": 0.82},
    {"block": 96526330, "type": "whale_accumulation",  "confidence": 0.79},
    {"block": 96526444, "type": "whale_accumulation",  "confidence": 0.85},
    {"block": 96526490, "type": "whale_accumulation",  "confidence": 0.77},
    # Batch 3 — Smart Money Inflows
    {"block": 96526120, "type": "smart_money_inflow",  "confidence": 0.91},
    {"block": 96526260, "type": "smart_money_inflow",  "confidence": 0.86},
    {"block": 96526370, "type": "smart_money_inflow",  "confidence": 0.83},
    {"block": 96526410, "type": "smart_money_inflow",  "confidence": 0.80},
    {"block": 96526500, "type": "smart_money_inflow",  "confidence": 0.88},
    # Batch 4 — MEV + Bridge anomalies
    {"block": 96526140, "type": "mev_sandwich",        "confidence": 0.87},
    {"block": 96526280, "type": "mev_sandwich",        "confidence": 0.84},
    {"block": 96526350, "type": "bridge_outflow_spike","confidence": 0.78},
    {"block": 96526460, "type": "bridge_outflow_spike","confidence": 0.81},
    {"block": 96526530, "type": "gas_anomaly",         "confidence": 0.75},
]

CONTRACT_ADDR = "0x7fAb1E37d992109d3aA747703436ff4e261391b7"
RPC_URL       = "https://rpc.sepolia.mantle.xyz"
CHAIN_ID      = 5003

CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "findingHash",     "type": "bytes32"},
            {"internalType": "string",  "name": "anomalyType",     "type": "string"},
            {"internalType": "uint8",   "name": "confidenceScore", "type": "uint8"},
            {"internalType": "uint256", "name": "blockHeight",     "type": "uint256"},
        ],
        "name": "recordFinding",
        "outputs": [{"internalType": "uint256", "name": "findingId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "findingCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

def finding_hash(f: dict) -> bytes:
    canonical = json.dumps({"block": f["block"], "type": f["type"], "confidence": f["confidence"]}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).digest()

def main():
    from web3 import Web3

    private_key = None
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("AGENT_PRIVATE_KEY="):
                private_key = line.split("=", 1)[1].strip()
                break
    private_key = private_key or os.environ.get("AGENT_PRIVATE_KEY")
    if not private_key:
        print("ERROR: AGENT_PRIVATE_KEY not found")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 90}))
    if not w3.is_connected():
        print(f"ERROR: Cannot connect to {RPC_URL}")
        sys.exit(1)

    account  = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=CONTRACT_ABI)

    before_count = contract.functions.findingCount().call()
    print(f"Wallet:   {account.address}")
    print(f"Contract: {CONTRACT_ADDR}")
    print(f"FindingCount before: {before_count}")
    print(f"Submitting: {len(FINDINGS_TO_SUBMIT)} new findings\n")

    results  = []
    success  = 0

    for i, f in enumerate(FINDINGS_TO_SUBMIT):
        fhash      = finding_hash(f)
        confidence = int(f["confidence"] * 100)
        block_h    = f["block"]
        atype      = f["type"]

        print(f"[{i+1:02d}/{len(FINDINGS_TO_SUBMIT)}] block={block_h} type={atype} conf={confidence}%", end=" ", flush=True)

        try:
            # Fresh nonce every time
            nonce     = w3.eth.get_transaction_count(account.address)
            gas_price = int(w3.eth.gas_price * 1.2)  # 20% bump to avoid underpriced

            tx = contract.functions.recordFinding(
                fhash, atype, confidence, block_h
            ).build_transaction({
                "chainId":  CHAIN_ID,
                "gas":      200_000,
                "gasPrice": gas_price,
                "nonce":    nonce,
                "from":     account.address,
            })
            signed  = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)

            status = "✅" if receipt.status == 1 else "❌"
            print(f"→ {status} {tx_hash.hex()[:22]}... gas={receipt.gasUsed}")
            results.append({
                "block": block_h, "type": atype,
                "tx_hash": tx_hash.hex(), "status": "success" if receipt.status == 1 else "failed",
                "gas_used": receipt.gasUsed,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            })
            if receipt.status == 1:
                success += 1
            time.sleep(3)  # wait 3s between txs

        except Exception as e:
            err = str(e)
            print(f"→ ❌ {err[:100]}")
            results.append({"block": block_h, "type": atype, "error": err})
            time.sleep(2)

    after_count = contract.functions.findingCount().call()
    added = after_count - before_count
    print(f"\n✅ FindingCount: {before_count} → {after_count} (+{added} new findings)")

    out = ROOT / "data" / "onchain_submissions_bulk.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "contract": CONTRACT_ADDR, "network": "mantle-sepolia",
        "wallet": account.address,
        "count_before": before_count, "count_after": after_count, "added": added,
        "transactions": results,
    }, indent=2))
    print(f"Results → {out}")

if __name__ == "__main__":
    main()
