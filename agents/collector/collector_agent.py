"""
Mantle Intel Agent — Collector Agent (Stage 1)
Ingests Mantle blockchain data: blocks, transactions, large transfers, DEX events.
Falls back to demo/simulation mode when no RPC is reachable.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Any, Optional
import structlog

logger = structlog.get_logger(__name__)

# Optional heavy deps — fail gracefully
try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# ── Mantle Protocol Addresses (Mainnet) ─────────────────────────────────────

MANTLE_PROTOCOLS = {
    "merchant_moe": "0x85f8628a0fa2A8C4A4a20A4c6432f57E45eF4E8e",
    "agni_finance":  "0x319B69888B0d11cEC22caA5034e25FfFBDc88421",
    "lendle":        "0x35b594f4cAba8B4D595c67F02fF4A619cc0e349F",
    "fusionx":       "0x530D2b6c4aE42e2Ab45EAe8B7cFAF0FBA8F3D2f7",
    "mantle_lsd":    "0xe3cBd06D7dadB3F4e6557bAb7EdD924CD1489E8f",
    "cleo_exchange": "0x1BbD33384869b30A323e15868Ce46013C82B86FB",
    "pendle_mantle": "0x888888888889758F76e7103c6CbF23ABbF58F946",
}

# Known whale/smart-money labels (expand from on-chain data)
KNOWN_WALLETS = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance Cold Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance14",
    "0x9696f59e4d72e237be84ffd425dcad154bf96976": "Bybit Hot Wallet",
    "0xe93381fb4c4f14bda253907b18fad305d799241a": "Bybit2",
    "0x1f9090aae28b8a3dceadf281b0f12828e676c326": "rsync-builder MEV",
}

LARGE_TRANSFER_THRESHOLD_USD = 50_000   # $50k+
ANOMALY_BLOCK_WINDOW = 100             # blocks to scan per cycle


class RawTransaction:
    """Structured tx extracted from block data."""
    def __init__(self, tx: dict, block_ts: int, block_num: int):
        self.hash        = tx.get("hash", "")
        self.from_addr   = tx.get("from", "").lower()
        self.to_addr     = (tx.get("to") or "").lower()
        self.value_wei   = int(tx.get("value", 0))
        self.value_mnt   = self.value_wei / 1e18
        self.gas_used    = int(tx.get("gas", 0))
        self.gas_price   = int(tx.get("gasPrice", 0))
        self.block_num   = block_num
        self.block_ts    = block_ts
        self.input_data  = tx.get("input", "0x")
        self.is_contract_call = len(self.input_data) > 10


class BlockSummary:
    """Aggregated summary of a single block."""
    def __init__(self, block_num: int, timestamp: int, tx_count: int,
                 total_value_mnt: float, large_transfers: list, unique_senders: set):
        self.block_num        = block_num
        self.timestamp        = timestamp
        self.tx_count         = tx_count
        self.total_value_mnt  = total_value_mnt
        self.large_transfers  = large_transfers
        self.unique_senders   = unique_senders


class CollectorAgent:
    """
    Polls Mantle RPC for new blocks, extracts structured tx data,
    tracks large transfers, DEX interactions, and new wallet activity.

    Falls back to simulation mode when RPC is unavailable.
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        mnt_price_usd: float = 0.85,
        poll_interval: int = 6,
    ):
        self.rpc_url       = rpc_url or os.getenv("MANTLE_RPC_URL", "https://rpc.mantle.xyz")
        self.mnt_price_usd = mnt_price_usd
        self.poll_interval = poll_interval
        self._w3: Optional[Any] = None
        self._demo_mode  = False
        self._last_block  = 0
        self._block_cache: list[BlockSummary] = []  # rolling 500 blocks
        self.logger = logger.bind(agent="collector")

        self._init_web3()

    def _init_web3(self):
        if not WEB3_AVAILABLE:
            self.logger.warning("web3_not_installed", msg="pip install web3 — running demo mode")
            self._demo_mode = True
            return
        try:
            self._w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 10}))
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if self._w3.is_connected():
                self._last_block = self._w3.eth.block_number - ANOMALY_BLOCK_WINDOW
                self.logger.info("rpc_connected", url=self.rpc_url, latest_block=self._last_block + ANOMALY_BLOCK_WINDOW)
            else:
                raise ConnectionError("RPC not reachable")
        except Exception as e:
            self.logger.warning("rpc_unavailable", error=str(e), msg="Switching to demo mode")
            self._demo_mode = True

    # ── Main data collection ──────────────────────────────────────────────────

    async def collect_blocks(self, num_blocks: int = 50) -> list[BlockSummary]:
        """Collect and summarize the last `num_blocks` blocks."""
        if self._demo_mode:
            return self._generate_demo_blocks(num_blocks)

        summaries = []
        try:
            latest = self._w3.eth.block_number
            start  = max(self._last_block, latest - num_blocks)

            for bn in range(start, latest + 1):
                try:
                    block = self._w3.eth.get_block(bn, full_transactions=True)
                    summary = self._summarize_block(block)
                    summaries.append(summary)
                except Exception as e:
                    self.logger.warning("block_fetch_error", block=bn, error=str(e))

            self._last_block = latest
            self._block_cache.extend(summaries)
            self._block_cache = self._block_cache[-500:]  # keep last 500

            self.logger.info("blocks_collected",
                             count=len(summaries),
                             from_block=start,
                             to_block=latest)
        except Exception as e:
            self.logger.error("collection_failed", error=str(e))
            return self._generate_demo_blocks(num_blocks)

        return summaries

    def _summarize_block(self, block) -> BlockSummary:
        large_transfers = []
        unique_senders  = set()
        total_value     = 0.0

        for tx in block.transactions:
            raw = RawTransaction(dict(tx), block.timestamp, block.number)
            total_value += raw.value_mnt
            unique_senders.add(raw.from_addr)

            usd_value = raw.value_mnt * self.mnt_price_usd
            if usd_value >= LARGE_TRANSFER_THRESHOLD_USD:
                large_transfers.append({
                    "tx_hash":    raw.hash.hex() if hasattr(raw.hash, "hex") else str(raw.hash),
                    "from":       raw.from_addr,
                    "to":         raw.to_addr,
                    "value_mnt":  round(raw.value_mnt, 4),
                    "value_usd":  round(usd_value, 2),
                    "label_from": KNOWN_WALLETS.get(raw.from_addr, "unknown"),
                    "label_to":   KNOWN_WALLETS.get(raw.to_addr, "unknown"),
                    "block":      block.number,
                    "is_contract": raw.is_contract_call,
                })

        return BlockSummary(
            block_num=block.number,
            timestamp=block.timestamp,
            tx_count=len(block.transactions),
            total_value_mnt=round(total_value, 4),
            large_transfers=large_transfers,
            unique_senders=unique_senders,
        )

    # ── Demo / simulation mode ────────────────────────────────────────────────

    def _generate_demo_blocks(self, num_blocks: int) -> list[BlockSummary]:
        """
        Generate deterministic Mantle block summaries for demo/backtest.
        ALL 5 ground truth anomaly events injected at known offsets:
          25  - whale_accumulation  (Binance->Agni, $722k, 3 large txs)
          40  - tx_spike            (4.1 sigma burst, 333 txs)
          60  - smart_money_inflow  (5 wallets->Merchant Moe)
          75  - value_spike         ($1.2M single-block transfer, 3 large txs)
          88  - whale_accumulation  (Bybit->Lendle, $550k, 3 large txs)
        Fixed seed=42 ensures fully reproducible backtest results.
        """
        import random
        rng = random.Random(42)  # FIXED SEED - fully deterministic
        base_block = 68_000_000
        base_ts    = int(time.time()) - num_blocks * 2
        BASELINE_TX  = 65    # mean tx/block
        BASELINE_VAL = 1200  # mean MNT/block

        summaries = []
        for i in range(num_blocks):
            block_num = base_block + i
            ts        = base_ts + i * 2
            tx_count  = int(rng.gauss(BASELINE_TX, 10))
            value_mnt = rng.gauss(BASELINE_VAL, 200)
            large_txs = []

            # Injection 1 - whale_accumulation @ offset 25
            if i == 25:
                tx_count  = 290
                value_mnt = 850_000.0
                large_txs = [
                    {"tx_hash": "0x"+hashlib.sha256(b"w25_0").hexdigest(), "from": "0x28c6c06298d514db089934071355e5743bf21d60", "to": "0x319b69888b0d11cec22caa5034e25fffbdc88421", "value_mnt": 850000.0, "value_usd": 722500.0, "label_from": "Binance Hot Wallet", "label_to": "Agni Finance", "block": block_num, "is_contract": True},
                    {"tx_hash": "0x"+hashlib.sha256(b"w25_1").hexdigest(), "from": "0x28c6c06298d514db089934071355e5743bf21d60", "to": "0x319b69888b0d11cec22caa5034e25fffbdc88421", "value_mnt": 95000.0, "value_usd": 80750.0, "label_from": "Binance Hot Wallet", "label_to": "Agni Finance", "block": block_num, "is_contract": True},
                    {"tx_hash": "0x"+hashlib.sha256(b"w25_2").hexdigest(), "from": "0x9696f59e4d72e237be84ffd425dcad154bf96976", "to": "0x319b69888b0d11cec22caa5034e25fffbdc88421", "value_mnt": 75000.0, "value_usd": 63750.0, "label_from": "Bybit Hot Wallet", "label_to": "Agni Finance", "block": block_num, "is_contract": True},
                ]
            # Injection 2 - tx_spike @ offset 40 (333 txs = ~26.8 sigma above baseline 65, std=10)
            elif i == 40:
                tx_count  = 333
                value_mnt = rng.gauss(BASELINE_VAL, 200)
            # Injection 3 - smart_money_inflow @ offset 60
            elif i == 60:
                tx_count  = 195
                value_mnt = 540_000.0
                large_txs = [
                    {"tx_hash": "0x"+hashlib.sha256(f"sm60_{j}".encode()).hexdigest(), "from": f"0xabababababababababababababababab{j:04x}", "to": "0x85f8628a0fa2a8c4a4a20a4c6432f57e45ef4e8e", "value_mnt": 110000.0+j*5000, "value_usd": 93500.0+j*4250, "label_from": "unknown", "label_to": "Merchant Moe", "block": block_num, "is_contract": True}
                    for j in range(5)
                ]
            # Injection 4 - value_spike @ offset 75 ($1.2M)
            elif i == 75:
                tx_count  = int(rng.gauss(BASELINE_TX, 10))
                value_mnt = 1_200_000.0
                large_txs = [
                    {"tx_hash": "0x"+hashlib.sha256(b"vs75_0").hexdigest(), "from": "0x1f9090aae28b8a3dceadf281b0f12828e676c326", "to": "0x35b594f4caba8b4d595c67f02ff4a619cc0e349f", "value_mnt": 1200000.0/0.85, "value_usd": 1200000.0, "label_from": "rsync-builder MEV", "label_to": "Lendle", "block": block_num, "is_contract": True},
                    {"tx_hash": "0x"+hashlib.sha256(b"vs75_1").hexdigest(), "from": "0x21a31ee1afc51d94c2efccaa2092ad1028285549", "to": "0x35b594f4caba8b4d595c67f02ff4a619cc0e349f", "value_mnt": 85000.0, "value_usd": 72250.0, "label_from": "Binance Cold Wallet", "label_to": "Lendle", "block": block_num, "is_contract": True},
                    {"tx_hash": "0x"+hashlib.sha256(b"vs75_2").hexdigest(), "from": "0xdfd5293d8e347dfe59e90efd55b2956a1343963d", "to": "0x35b594f4caba8b4d595c67f02ff4a619cc0e349f", "value_mnt": 90000.0, "value_usd": 76500.0, "label_from": "Binance14", "label_to": "Lendle", "block": block_num, "is_contract": True},
                ]
            # Injection 5 - whale_accumulation @ offset 88
            elif i == 88:
                tx_count  = 260
                value_mnt = 650_000.0
                large_txs = [
                    {"tx_hash": "0x"+hashlib.sha256(b"jm88_0").hexdigest(), "from": "0xe93381fb4c4f14bda253907b18fad305d799241a", "to": "0x35b594f4caba8b4d595c67f02ff4a619cc0e349f", "value_mnt": 550000.0/0.85, "value_usd": 550000.0, "label_from": "Bybit2", "label_to": "Lendle", "block": block_num, "is_contract": True},
                    {"tx_hash": "0x"+hashlib.sha256(b"jm88_1").hexdigest(), "from": "0xe93381fb4c4f14bda253907b18fad305d799241a", "to": "0x35b594f4caba8b4d595c67f02ff4a619cc0e349f", "value_mnt": 75000.0, "value_usd": 63750.0, "label_from": "Bybit2", "label_to": "Lendle", "block": block_num, "is_contract": True},
                    {"tx_hash": "0x"+hashlib.sha256(b"jm88_2").hexdigest(), "from": "0x9696f59e4d72e237be84ffd425dcad154bf96976", "to": "0x35b594f4caba8b4d595c67f02ff4a619cc0e349f", "value_mnt": 80000.0, "value_usd": 68000.0, "label_from": "Bybit Hot Wallet", "label_to": "Lendle", "block": block_num, "is_contract": True},
                ]

            summaries.append(BlockSummary(
                block_num=block_num,
                timestamp=ts,
                tx_count=max(1, tx_count),
                total_value_mnt=max(0.0, value_mnt),
                large_transfers=large_txs,
                unique_senders=set([f"0xaddr{j}" for j in range(min(max(1, tx_count), 80))]),
            ))

        return summaries
    def get_cached_blocks(self) -> list[BlockSummary]:
        return self._block_cache

    @property
    def demo_mode(self) -> bool:
        return self._demo_mode
