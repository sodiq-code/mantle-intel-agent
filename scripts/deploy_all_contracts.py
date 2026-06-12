#!/usr/bin/env python3
"""
Deploy SignalRegistry + SmartMoneyTracker + AlertLog to Mantle Sepolia.
Appends deployed addresses to .env and data/deployed_contracts.json.
"""

import os, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

def load_env():
    env = {}
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def compile_contract(sol_file: Path):
    """Compile with solc — returns (abi, bytecode)"""
    result = subprocess.run(
        ["solc", "--abi", "--bin", "--optimize", "--overwrite", "-o", "/tmp/solc_out", str(sol_file)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Compile error:\n{result.stderr}")
        return None, None

    name = sol_file.stem
    abi_file  = Path(f"/tmp/solc_out/{name}.abi")
    bin_file  = Path(f"/tmp/solc_out/{name}.bin")
    if not abi_file.exists() or not bin_file.exists():
        print(f"Output files missing for {name}")
        return None, None

    abi      = json.loads(abi_file.read_text())
    bytecode = "0x" + bin_file.read_text().strip()
    return abi, bytecode

def deploy_contract(w3, account, abi, bytecode, name):
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce    = w3.eth.get_transaction_count(account.address)
    tx = contract.constructor().build_transaction({
        "chainId":  5003,
        "gas":      3_000_000,
        "gasPrice": w3.eth.gas_price,
        "nonce":    nonce,
        "from":     account.address,
    })
    signed  = w3.eth.account.sign_transaction(tx, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"  Deploying {name}... tx={tx_hash.hex()[:20]}...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    status  = "✅" if receipt.status == 1 else "❌"
    print(f"  {status} {name} → {receipt.contractAddress} (block {receipt.blockNumber})")
    return receipt.contractAddress, receipt.blockNumber, tx_hash.hex()

def main():
    from web3 import Web3

    env = load_env()
    private_key = env.get("AGENT_PRIVATE_KEY") or os.environ.get("AGENT_PRIVATE_KEY")
    if not private_key:
        print("ERROR: AGENT_PRIVATE_KEY not found")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider("https://rpc.sepolia.mantle.xyz", request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        print("ERROR: Cannot connect to Mantle Sepolia RPC")
        sys.exit(1)

    account = w3.eth.account.from_key(private_key)
    bal     = w3.from_wei(w3.eth.get_balance(account.address), "ether")
    print(f"Wallet:  {account.address}")
    print(f"Balance: {bal:.4f} MNT")
    print()

    contracts_to_deploy = [
        ROOT / "contracts" / "SignalRegistry.sol",
        ROOT / "contracts" / "SmartMoneyTracker.sol",
        ROOT / "contracts" / "AlertLog.sol",
    ]

    deployed = []
    for sol_file in contracts_to_deploy:
        print(f"Compiling {sol_file.name}...")
        abi, bytecode = compile_contract(sol_file)
        if not abi:
            print(f"  ❌ Skipping {sol_file.name}")
            continue

        addr, block, tx_hash = deploy_contract(w3, account, abi, bytecode, sol_file.stem)
        deployed.append({
            "name":     sol_file.stem,
            "address":  addr,
            "block":    block,
            "tx_hash":  tx_hash,
            "network":  "mantle-sepolia",
            "chain_id": 5003,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
        })
        time.sleep(2)

    # Save
    out_file = ROOT / "data" / "deployed_contracts.json"
    existing = []
    if out_file.exists():
        existing = json.loads(out_file.read_text())
    existing.extend(deployed)
    out_file.write_text(json.dumps(existing, indent=2))

    print(f"\n✅ Deployed {len(deployed)} contracts")
    for d in deployed:
        print(f"   {d['name']}: {d['address']}")
    print(f"\nSaved → {out_file}")

if __name__ == "__main__":
    main()
