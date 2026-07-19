import os

# ── Single Source of Truth ──────────────────────────────
CONTRACT_ADDRESS = "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b"
MANTLE_RPC       = "https://rpc.mantle.xyz"
MANTLE_SEPOLIA   = "https://rpc.sepolia.mantle.xyz"
CHAIN_ID_MAINNET = 5000
CHAIN_ID_TESTNET = 5003

# Allow env overrides for custom deployments
CONTRACT_ADDRESS = os.getenv("AUDIT_CONTRACT_ADDRESS", CONTRACT_ADDRESS)
MANTLE_RPC       = os.getenv("MANTLE_RPC_URL", MANTLE_RPC)
MANTLE_SEPOLIA   = os.getenv("MANTLE_TESTNET_RPC", MANTLE_SEPOLIA)
