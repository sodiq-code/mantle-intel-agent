"""
Mantle Intel Agent — Audit Agent (Stage 5)
Writes each finding's SHA256 hash on-chain to MantleIntelAudit.sol.
This provides full verifiability and auditability — the core differentiator
of the project: every agent decision is permanently recorded and publicly
verifiable on-chain.

On-chain record = finding_hash + anomaly_type + confidence + block_height
Anyone can independently verify any agent decision against the contract.
"""
from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass, asdict
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

# Minimal ABI for MantleIntelAudit — only the functions we call
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
        "inputs": [{"internalType": "bytes32", "name": "findingHash", "type": "bytes32"}],
        "name": "verifyFinding",
        "outputs": [
            {"internalType": "bool",    "name": "verified",   "type": "bool"},
            {"internalType": "uint256", "name": "findingId",  "type": "uint256"},
            {"internalType": "uint256", "name": "timestamp",  "type": "uint256"},
            {"internalType": "uint8",   "name": "confidence", "type": "uint8"},
        ],
        "stateMutability": "view",
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
        "inputs": [{"internalType": "uint256", "name": "count", "type": "uint256"}],
        "name": "getRecentFindings",
        "outputs": [{"internalType": "uint256[]", "name": "ids", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass
class AuditRecord:
    finding_id:      str
    finding_hash:    str     # hex SHA256
    anomaly_type:    str
    confidence:      float
    block_height:    int
    on_chain_tx:     Optional[str] = None   # tx hash if recorded on-chain
    on_chain_id:     Optional[int] = None   # contract finding ID
    audit_status:    str = "pending"        # pending | recorded | failed | demo
    error:           Optional[str] = None
    timestamp:       float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return asdict(self)

    def explorer_url(self, network: str = "mainnet") -> str:
        if not self.on_chain_tx:
            return ""
        base = "https://mantlescan.xyz" if network == "mainnet" else "https://sepolia.mantlescan.xyz"
        return f"{base}/tx/{self.on_chain_tx}"


class AuditAgent:
    """
    Records finding hashes on-chain. Each finding gets:
      1. SHA256 hash computed from canonical JSON
      2. recordFinding() call on MantleIntelAudit.sol
      3. AuditRecord with tx hash + on-chain ID stored locally

    Falls back to demo mode (logs but doesn't write) when wallet not configured.
    """

    def __init__(
        self,
        contract_address: Optional[str] = None,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        network: str = None,
        keystore_path: Optional[str] = None,
        keystore_password: Optional[str] = None,
    ):
        self.contract_address = contract_address or os.getenv(
            "AUDIT_CONTRACT_ADDRESS", "")
        self.rpc_url = rpc_url or os.getenv(
            "AUDIT_RPC_URL", os.getenv(
            "MANTLE_TESTNET_RPC", "https://rpc.sepolia.mantle.xyz"))
        self.network = network or os.getenv("NETWORK", "testnet")
        self._w3: Optional[object] = None
        self._contract = None
        self._demo_mode = False
        self._audit_log: list[AuditRecord] = []
        self.logger = logger.bind(agent="audit")

        # ── Private key resolution: keystore first, env fallback ───────────
        # Priority:
        #   1. Explicit private_key parameter (for testing / programmatic use)
        #   2. Encrypted keystore (KEYSTORE_PATH + KEYSTORE_PASSWORD)
        #   3. AGENT_PRIVATE_KEY env var (legacy / CI fallback, deprecated)
        self.private_key = self._resolve_private_key(
            private_key, keystore_path, keystore_password)

        self._init_web3()

    def _resolve_private_key(
        self,
        explicit_key: Optional[str],
        keystore_path: Optional[str],
        keystore_password: Optional[str],
    ) -> str:
        """Resolve the private key from keystore or environment.

        Loads from encrypted EIP-2335 keystore by preference (the
        documented, secure path). Falls back to the AGENT_PRIVATE_KEY
        environment variable with a deprecation warning so existing CI
        configurations keep working.
        """
        # 1. Explicit parameter (e.g. unit tests passing a key directly)
        if explicit_key:
            return explicit_key

        # 2. Encrypted keystore (preferred — matches README / ARCHITECTURE)
        ks_path = keystore_path or os.getenv("KEYSTORE_PATH", "keystore.json")
        ks_pass = keystore_password or os.getenv("KEYSTORE_PASSWORD", "")

        if ks_pass and os.path.isfile(ks_path):
            try:
                from eth_account import Account
                with open(ks_path) as f:
                    encrypted_key = f.read()
                pk = Account.decrypt(encrypted_key, ks_pass)
                self.logger.info("keystore_loaded",
                                 path=ks_path,
                                 msg="Private key loaded from encrypted keystore")
                if isinstance(pk, bytes):
                    pk = "0x" + pk.hex()
                return pk
            except Exception as e:
                self.logger.warning("keystore_decrypt_failed",
                                    path=ks_path,
                                    error=str(e),
                                    msg="Falling back to AGENT_PRIVATE_KEY env var")

        # 3. Legacy: plaintext env var (still used in CI until keystore is set up)
        env_key = os.getenv("AGENT_PRIVATE_KEY", "")
        if env_key:
            self.logger.warning(
                "keystore_not_used",
                msg="AGENT_PRIVATE_KEY env var is deprecated. "
                    "Use encrypted keystore (KEYSTORE_PATH + KEYSTORE_PASSWORD) "
                    "for production. See scripts/generate_keystore.py.")
            return env_key

        # No key available — pipeline will fail in _init_web3 with clear error
        return ""

    def _init_web3(self):
        if not WEB3_AVAILABLE:
            self.logger.error("web3_not_installed", msg="Running in demo mode - no on-chain writes. PIP install web3 required.")
            raise ImportError("web3 is required for audit agent")

        if not self.contract_address or not self.private_key:
            self.logger.error("missing_config",
                              msg="CONTRACT_ADDRESS or private key not configured. "
                              "Set KEYSTORE_PATH + KEYSTORE_PASSWORD (preferred) or "
                              "AGENT_PRIVATE_KEY (legacy) environment variables.")
            raise ValueError(
                "Missing contract address or private key. "
                "Configure via KEYSTORE_PATH + KEYSTORE_PASSWORD (preferred) or "
                "AGENT_PRIVATE_KEY (legacy). See scripts/generate_keystore.py.")

        try:
            self._w3 = Web3(Web3.HTTPProvider(
                self.rpc_url, request_kwargs={"timeout": 30}))
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            if not self._w3.is_connected():
                raise ConnectionError("RPC not reachable")

            self._contract = self._w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=CONTRACT_ABI,
            )
            self._account = self._w3.eth.account.from_key(self.private_key)
            self.logger.info("audit_agent_ready",
                             contract=self.contract_address,
                             wallet=self._account.address,
                             network=self.network)
        except Exception as e:
            self.logger.error("web3_init_failed", error=str(e), msg="Failed to initialize web3 or contract")
            raise
    # ── Main audit function ───────────────────────────────────────────────────

    async def record_finding(self, finding) -> AuditRecord:
        """Record a single finding on-chain. Returns AuditRecord."""
        record = AuditRecord(
            finding_id=finding.finding_id,
            finding_hash=finding.sha256_hash(),
            anomaly_type=finding.anomaly_type,
            confidence=finding.confidence,
            block_height=finding.block_height,
        )

        if not self._contract:
            record.audit_status = "failed"
            record.error = "Contract not initialized"
            self.logger.error("audit_failed", finding_id=finding.finding_id, error="No contract")
            self._audit_log.append(record)
            return record

        try:
            tx_hash, on_chain_id = await self._submit_to_chain(finding, record.finding_hash)
            record.on_chain_tx = tx_hash
            record.on_chain_id = on_chain_id
            record.audit_status = "recorded"
            self.logger.info("finding_recorded_on_chain",
                             finding_id=finding.finding_id,
                             tx=tx_hash,
                             on_chain_id=on_chain_id)
        except Exception as e:
            record.audit_status = "failed"
            record.error = str(e)
            self.logger.error("audit_record_failed",
                              finding_id=finding.finding_id,
                              error=str(e))

        self._audit_log.append(record)
        return record

    async def _submit_to_chain(self, finding, finding_hash: str) -> tuple[str, int]:
        """Submit finding to MantleIntelAudit.sol. Returns (tx_hash, on_chain_id)."""
        hash_bytes = bytes.fromhex(finding_hash)
        confidence_int = int(finding.confidence * 100)

        # Use "pending" to include pending transactions in the nonce count
        # This prevents "nonce too low" errors when sending multiple txs quickly
        nonce = self._w3.eth.get_transaction_count(
            self._account.address, "pending")
        gas_price = self._w3.eth.gas_price

        txn = self._contract.functions.recordFinding(
            hash_bytes,
            finding.anomaly_type[:64],   # max 64 chars
            confidence_int,
            finding.block_height,
        ).build_transaction({
            "chainId":  5000 if self.network == "mainnet" else 5003,
            "from":     self._account.address,
            "nonce":    nonce,
            "gasPrice": gas_price,
        })

        # Estimate gas
        try:
            txn["gas"] = self._w3.eth.estimate_gas(txn)
        except Exception:
            txn["gas"] = 200_000  # safe default

        signed = self._w3.eth.account.sign_transaction(txn, self.private_key)
        tx_hash = self._w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = self._w3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=60)

        if receipt.status != 1:
            raise RuntimeError(f"Transaction reverted: {tx_hash.hex()}")

        # Parse FindingRecorded event to get on-chain ID
        try:
            events = self._contract.events.FindingRecorded().process_receipt(receipt)
            on_chain_id = events[0]["args"]["findingId"] if events else None
        except Exception:
            on_chain_id = None

        return tx_hash.hex(), on_chain_id

    # ── Verification ──────────────────────────────────────────────────────────

    async def verify_finding(self, finding_hash: str) -> dict:
        """Query contract to verify a finding hash."""
        if not self._contract:
            return {"verified": False, "error": "No contract"}

        try:
            hash_bytes = bytes.fromhex(finding_hash.lstrip("0x"))
            result = self._contract.functions.verifyFinding(hash_bytes).call()
            return {
                "verified":   result[0],
                "finding_id": result[1],
                "timestamp":  result[2],
                "confidence": result[3],
                "hash":       finding_hash,
                "explorer":   f"https://mantlescan.xyz/address/{self.contract_address}",
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def get_chain_stats(self) -> dict:
        """Get total findings count from contract."""
        if not self._contract:
            return {"total_findings": 0, "error": "No contract"}
        try:
            count = self._contract.functions.findingCount().call()
            return {"total_findings": count, "contract": self.contract_address}
        except Exception as e:
            return {"total_findings": 0, "error": str(e)}

    def save_audit_log(self, path: str = "data/audit_log.jsonl"):
        """Persist audit log to JSONL."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            for rec in self._audit_log:
                f.write(json.dumps(rec.to_dict()) + "\n")
        self._audit_log = []  # flush after save

    @property
    def demo_mode(self) -> bool:
        return self._demo_mode
