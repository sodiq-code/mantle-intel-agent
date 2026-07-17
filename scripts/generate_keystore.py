#!/usr/bin/env python3
"""
Mantle Intel Agent — Institutional Security
Generates an EIP-2335 encrypted keystore JSON file from a raw private key.
This allows the agent to securely hold funds without exposing the key in plaintext.
"""
import os
import json
import getpass
from pathlib import Path
from eth_account import Account

def generate_keystore():
    print("==================================================")
    print("  Ethereum Encrypted Keystore Generator (EIP-2335)")
    print("==================================================")
    print("This will encrypt a raw private key with a password.")
    print("The result is a keystore.json file safe for servers.\n")
    
    private_key = getpass.getpass("Enter raw private key (0x...): ").strip()
    if not private_key.startswith("0x"):
        private_key = "0x" + private_key
        
    try:
        account = Account.from_key(private_key)
        print(f"\nAccount Address: {account.address}")
    except Exception as e:
        print(f"Error: Invalid private key. {e}")
        return

    password = getpass.getpass("Enter strong encryption password: ")
    confirm = getpass.getpass("Confirm password: ")
    
    if password != confirm:
        print("Passwords do not match!")
        return

    print("\nEncrypting key (this takes a few seconds)...")
    encrypted_keystore = Account.encrypt(private_key, password)
    
    out_path = Path("keystore.json")
    with open(out_path, "w") as f:
        json.dump(encrypted_keystore, f, indent=2)
        
    print(f"\n✅ Success! Keystore saved to {out_path.absolute()}")
    print("IMPORTANT: Store this password in your .env as KEYSTORE_PASSWORD.")
    print("Do NOT commit keystore.json to version control.")

if __name__ == "__main__":
    generate_keystore()
