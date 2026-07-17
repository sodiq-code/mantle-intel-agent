#!/usr/bin/env python3
"""
Submit real pipeline findings to MantleIntelAudit.sol.

Reads findings from data/findings.jsonl (produced by the live pipeline)
and submits each finding's SHA-256 hash to the on-chain audit contract.
Automatically skips findings already recorded on-chain (resume-safe).

This is the honest replacement for the previous bulk-submit scripts.
Every finding submitted here was genuinely detected by the AnomalyAgent
from live Mantle mainnet RPC data — no fabricated blocks or random
confidence scores.

Usage:
    AGENT_PRIVATE_KEY=0x... python3 scripts/submit_pipeline_findings.py
    AGENT_PRIVATE_KEY=0x... python3 scripts/submit_pipeline_findings.py --limit 50
    AGENT_PRIVATE_KEY=0x... python3 scripts/submit_pipeline_findings.py --dry-run

Environment:
    AGENT_PRIVATE_KEY  — wallet authorized to call recordFinding() (required)
    AUDIT_CONTRACT_ADDRESS — override default contract address (optional)
    MANTLE_RPC_URL     — override default Sepolia RPC (optional)
"""
from __future__ import annotations

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
FINDINGS_FILE = ROOT / "data" / "findings.jsonl"

DEFAULT_CONTRACT = "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b"
DEFAULT_RPC = "https://rpc.sepolia.mantle.xyz"
CHAIN_ID = 5003

CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "findingHash", "type": "bytes32"},
            {"internalType": "string", "name": "anomalyType", "type": "string"},
            {"internalType": "uint8", "name": "confidenceScore", "type": "uint8"},
            {"internalType": "uint256", "name": "blockHeight", "type": "uint256"},
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
        "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "name": "hashToFindingId",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def load_findings(path: Path) -> list[dict]:
    """Load findings from the pipeline's JSONL output."""
    if not path.exists():
        print(f"ERROR: Findings file not found: {path}")
        print()
        print("Run the pipeline first to generate real findings:")
        print("  python -m agents.pipeline --mode once")
        print()
        print("Or for continuous live detection:")
        print("  python -m agents.pipeline --mode live")
        sys.exit(1)

    findings = []
    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"WARNING: Skipping malformed line {line_num}: {e}")
    return findings


def extract_finding_fields(f: dict) -> dict:
    """Extract on-chain submission fields from a pipeline finding dict."""
    # The pipeline writes 'hash' (hex SHA256 without 0x) and 'hex_hash' (with 0x)
    hex_hash = f.get("hex_hash") or f.get("hash", "")
    if hex_hash and not hex_hash.startswith("0x"):
        hex_hash = "0x" + hex_hash

    # Confidence is stored as 0.0-1.0 float; contract expects 0-100 uint8
    confidence_raw = f.get("confidence", 0)
    confidence_int = max(0, min(100, int(float(confidence_raw) * 100)))

    block = int(f.get("block", f.get("block_height", 0)))
    atype = str(f.get("type", f.get("anomaly_type", "unknown")))[:64]

    return {
        "hex_hash": hex_hash,
        "hash_bytes": bytes.fromhex(hex_hash[2:]) if hex_hash.startswith("0x") else b"",
        "confidence": confidence_int,
        "block": block,
        "anomaly_type": atype,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Submit real pipeline findings to MantleIntelAudit.sol on-chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Submit all findings (resume-safe — skips already on-chain)
  AGENT_PRIVATE_KEY=0x... python3 scripts/submit_pipeline_findings.py

  # Preview what would be submitted without sending transactions
  AGENT_PRIVATE_KEY=0x... python3 scripts/submit_pipeline_findings.py --dry-run

  # Submit only the first 20 findings
  AGENT_PRIVATE_KEY=0x... python3 scripts/submit_pipeline_findings.py --limit 20
        """,
    )
    parser.add_argument("--limit", type=int, default=0, help="Max findings to submit (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be submitted without sending txs")
    parser.add_argument("--rpc", default=None, help="RPC URL (default: env MANTLE_RPC_URL or Sepolia)")
    parser.add_argument("--contract", default=None, help="Contract address (default: env AUDIT_CONTRACT_ADDRESS or deployed)")
    args = parser.parse_args()

    contract_addr = args.contract or os.getenv("AUDIT_CONTRACT_ADDRESS", DEFAULT_CONTRACT)
    rpc_url = args.rpc or os.getenv("MANTLE_RPC_URL", DEFAULT_RPC)

    # Load private key from encrypted keystore ONLY
    if not args.dry_run:
        keystore_path = os.environ.get("KEYSTORE_PATH", "keystore.json")
        keystore_password = os.environ.get("KEYSTORE_PASSWORD")
        
        if not keystore_password:
            print("ERROR: KEYSTORE_PASSWORD environment variable not set")
            print()
            print("Set it before running:")
            print("  export KEYSTORE_PASSWORD=your_password")
            print()
            print("Or for a single run:")
            print("  KEYSTORE_PASSWORD=your_password python3 scripts/submit_pipeline_findings.py")
            sys.exit(1)
            
        if not os.path.exists(keystore_path):
            print(f"ERROR: Keystore file not found at {keystore_path}")
            print("Generate one first with: python3 scripts/generate_keystore.py")
            sys.exit(1)
            
        try:
            from eth_account import Account
            with open(keystore_path) as f:
                encrypted_key = f.read()
            pk = Account.decrypt(encrypted_key, keystore_password)
        except Exception as e:
            print(f"ERROR decrypting keystore: {e}")
            sys.exit(1)
    else:
        pk = None

    # Load findings from pipeline output
    findings = load_findings(FINDINGS_FILE)
    print(f"Loaded {len(findings)} findings from {FINDINGS_FILE}")

    if not findings:
        print("No findings to submit. Run the pipeline to generate detections first.")
        return

    if args.limit > 0:
        findings = findings[:args.limit]
        print(f"Limited to first {len(findings)} findings")

    # Extract fields
    parsed = []
    for f in findings:
        try:
            parsed.append(extract_finding_fields(f))
        except Exception as e:
            print(f"WARNING: Skipping unparseable finding: {e}")

    if not parsed:
        print("ERROR: No valid findings to submit after parsing.")
        sys.exit(1)

    if args.dry_run:
        print(f"\n{'='*70}")
        print(f"DRY RUN — {len(parsed)} findings would be submitted to:")
        print(f"  Contract: {contract_addr}")
        print(f"  RPC:      {rpc_url}")
        print(f"{'='*70}\n")
        for i, p in enumerate(parsed):
            print(f"  [{i+1:3d}] block={p['block']:>12}  type={p['anomaly_type']:<35}  conf={p['confidence']:>3}%  hash={p['hex_hash'][:18]}...")
        print(f"\nWould submit {len(parsed)} findings. Run without --dry-run to submit.")
        return

    # Connect to chain
    try:
        from web3 import Web3
    except ImportError:
        print("ERROR: web3 not installed. Run: pip install web3")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        print(f"ERROR: Cannot connect to RPC: {rpc_url}")
        sys.exit(1)

    account = w3.eth.account.from_key(pk)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_addr),
        abi=CONTRACT_ABI,
    )

    before_count = contract.functions.findingCount().call()

    print(f"\n{'='*70}")
    print(f"  Wallet:       {account.address}")
    print(f"  Contract:     {contract_addr}")
    print(f"  RPC:          {rpc_url}")
    print(f"  Chain ID:     {CHAIN_ID}")
    print(f"  Findings:     {len(parsed)} to process")
    print(f"  On-chain now: {before_count}")
    print(f"{'='*70}\n")

    submitted = 0
    skipped = 0
    failed = 0
    results = []

    for i, p in enumerate(parsed):
        label = f"[{i+1:3d}/{len(parsed)}] block={p['block']:>12} type={p['anomaly_type']:<35} conf={p['confidence']:>3}%"
        print(f"{label}", end=" ", flush=True)

        # Check if already on-chain (resume-safe — skip duplicates)
        try:
            existing_id = contract.functions.hashToFindingId(p["hash_bytes"]).call()
            if existing_id > 0:
                print(f"SKIP (already on-chain as #{existing_id})")
                skipped += 1
                results.append({"block": p["block"], "type": p["anomaly_type"], "status": "skipped", "on_chain_id": existing_id})
                continue
        except Exception:
            pass  # If the check fails, proceed with submission attempt

        try:
            nonce = w3.eth.get_transaction_count(account.address)
            gas_price = int(w3.eth.gas_price * 1.2)  # 20% bump to avoid underpriced

            tx = contract.functions.recordFinding(
                p["hash_bytes"],
                p["anomaly_type"],
                p["confidence"],
                p["block"],
            ).build_transaction({
                "chainId": CHAIN_ID,
                "gas": 350_000,
                "gasPrice": gas_price,
                "nonce": nonce,
                "from": account.address,
            })
            signed = w3.eth.account.sign_transaction(tx, pk)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)

            if receipt.status == 1:
                print(f"OK  tx={tx_hash.hex()[:18]}... gas={receipt.gasUsed}")
                submitted += 1
                results.append({
                    "block": p["block"], "type": p["anomaly_type"],
                    "status": "success", "tx_hash": tx_hash.hex(), "gas_used": receipt.gasUsed,
                })
            else:
                print(f"FAIL (tx reverted) tx={tx_hash.hex()[:18]}...")
                failed += 1
                results.append({"block": p["block"], "type": p["anomaly_type"], "status": "reverted", "tx_hash": tx_hash.hex()})

            time.sleep(0.5)

        except Exception as e:
            err_msg = str(e)[:80]
            print(f"ERR: {err_msg}")
            failed += 1
            results.append({"block": p["block"], "type": p["anomaly_type"], "status": "error", "error": err_msg})
            time.sleep(2)

    after_count = contract.functions.findingCount().call()

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"  Submitted:     {submitted}")
    print(f"  Skipped:       {skipped} (already on-chain)")
    print(f"  Failed:        {failed}")
    print(f"  FindingCount:  {before_count} -> {after_count} (+{after_count - before_count})")
    print(f"{'='*70}")

    # Save submission log
    log_path = ROOT / "data" / "onchain_submission_log.json"
    log_path.parent.mkdir(exist_ok=True)
    log_path.write_text(json.dumps({
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "contract": contract_addr,
        "network": "mantle-sepolia",
        "chain_id": CHAIN_ID,
        "wallet": account.address,
        "findings_processed": len(parsed),
        "submitted": submitted,
        "skipped": skipped,
        "failed": failed,
        "count_before": before_count,
        "count_after": after_count,
        "transactions": results,
    }, indent=2))
    print(f"\nLog saved -> {log_path}")


if __name__ == "__main__":
    main()
