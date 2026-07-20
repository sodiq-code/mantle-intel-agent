#!/usr/bin/env python3
"""
On-chain persistence utility — commits live pipeline findings to Mantle Sepolia.

The autonomous pipeline detects anomalies from live Mantle mainnet RPC blocks.
This script takes the initial seed findings (4 verified detections from the
Jun 11 2026 backtest run, blocks 96526083–96526552) and records their
SHA-256 hashes on MantleIntelAudit.sol, establishing the on-chain audit trail.

All findings listed are genuine pipeline detections — tx_spike and value_spike
events flagged by the AnomalyAgent with Multi-Confirm gate (2+ detectors agree).
This script is the testnet persistence layer; the pipeline itself runs on mainnet.

Usage:
    AGENT_PRIVATE_KEY=0x... python3 scripts/submit_findings_testnet.py
"""

import os
import json
import sys
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

# ── findings to submit ────────────────────────────────────────────────────────
# 4 real findings from the live backtest (mainnet blocks, Jun 11 2026)
# NOTE: Finding at block 96526517 (confidence=0.71) removed — below 0.75 threshold
FINDINGS_TO_SUBMIT = [
    {"block": 96526450, "type": "tx_spike",    "confidence": 0.90, "tx_count": 13},
    {"block": 96526083, "type": "tx_spike",    "confidence": 0.76, "tx_count": 6},
    {"block": 96526552, "type": "tx_spike",    "confidence": 0.76, "tx_count": 6},
    {"block": 96526386, "type": "tx_spike",    "confidence": 0.76, "tx_count": 6},
]

CONTRACT_ADDR = "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b"
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
    {
        "inputs": [
            {"internalType": "uint256", "name": "offset", "type": "uint256"},
            {"internalType": "uint256", "name": "limit",  "type": "uint256"},
        ],
        "name": "getPublicFindings",
        "outputs": [
            {
                "components": [
                    {"internalType": "bytes32", "name": "findingHash",    "type": "bytes32"},
                    {"internalType": "string",  "name": "anomalyType",    "type": "string"},
                    {"internalType": "uint8",   "name": "confidenceScore","type": "uint8"},
                    {"internalType": "uint256", "name": "blockHeight",    "type": "uint256"},
                    {"internalType": "uint256", "name": "timestamp",      "type": "uint256"},
                    {"internalType": "address", "name": "recorder",       "type": "address"},
                ],
                "internalType": "struct MantleIntelAudit.Finding[]",
                "name": "",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


def finding_hash(f: dict) -> bytes:
    """Hash must match AnomalyFinding.sha256_hash() — canonical JSON over core fields.

    P1-7 / P1-20 FIX: Both this script and the Python pipeline now hash the same
    4-field canonical JSON: {"block":int,"confidence":float,"tx_count":int,"type":str}.
    The JS Edge Function (api/shared.js) uses the same format via canonicalFindingHash().
    All three implementations produce identical hashes for the same finding.
    """
    canonical = json.dumps(f, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).digest()


def main():
    from web3 import Web3
    from eth_account import Account
    
    keystore_path = os.environ.get("KEYSTORE_PATH", "keystore.json")
    keystore_password = os.environ.get("KEYSTORE_PASSWORD")
    
    if not keystore_password:
        print("ERROR: KEYSTORE_PASSWORD not set — cannot decrypt keystore")
        print("Set it and re-run: KEYSTORE_PASSWORD=your_password python3 scripts/submit_findings_testnet.py")
        sys.exit(1)
        
    if not os.path.exists(keystore_path):
        print(f"ERROR: Keystore file not found at {keystore_path}")
        print("Generate one first with: python3 scripts/generate_keystore.py")
        sys.exit(1)
        
    try:
        with open(keystore_path) as f:
            encrypted_key = f.read()
        private_key = Account.decrypt(encrypted_key, keystore_password)
    except Exception as e:
        print(f"ERROR decrypting keystore: {e}")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))

    if not w3.is_connected():
        print(f"ERROR: Cannot connect to {RPC_URL}")
        sys.exit(1)

    account  = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDR),
        abi=CONTRACT_ABI,
    )

    before_count = contract.functions.findingCount().call()
    print(f"Wallet:  {account.address}")
    print(f"RPC:     {RPC_URL}")
    print(f"Contract:{CONTRACT_ADDR}")
    print(f"Finding count before: {before_count}")
    print()

    results = []
    nonce = w3.eth.get_transaction_count(account.address)

    for i, f in enumerate(FINDINGS_TO_SUBMIT):
        fhash      = finding_hash(f)
        confidence = int(f["confidence"] * 100)
        block_h    = f["block"]
        atype      = f["type"]

        print(f"[{i+1}/{len(FINDINGS_TO_SUBMIT)}] Submitting: block={block_h} type={atype} conf={confidence}%")

        try:
            tx = contract.functions.recordFinding(
                fhash, atype, confidence, block_h
            ).build_transaction({
                "chainId": CHAIN_ID,
                "gas": 500_000,
                "gasPrice": w3.eth.gas_price,
                "nonce": nonce,
                "from": account.address,
            })
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            status = "SUCCESS" if receipt.status == 1 else "FAILED"
            print(f"   {status} tx={tx_hash.hex()} gasUsed={receipt.gasUsed}")
            results.append({
                "block":    block_h,
                "type":     atype,
                "tx_hash":  tx_hash.hex(),
                "status":   "success" if receipt.status == 1 else "failed",
                "gas_used": receipt.gasUsed,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            })
            nonce += 1
            time.sleep(1)

        except Exception as e:
            print(f"   ERROR: {e}")
            results.append({"block": block_h, "type": atype, "error": str(e)})

    after_count = contract.functions.findingCount().call()
    print(f"\nFinding count after: {after_count} (added {after_count - before_count})")

    # save results
    out = ROOT / "data" / "onchain_submissions.json"
    out.write_text(json.dumps({
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "contract": CONTRACT_ADDR,
        "network": "mantle-sepolia",
        "chain_id": CHAIN_ID,
        "wallet": account.address,
        "findings_submitted": len(results),
        "count_before": before_count,
        "count_after": after_count,
        "transactions": results,
    }, indent=2))
    print(f"\nResults saved -> {out}")


if __name__ == "__main__":
    main()
