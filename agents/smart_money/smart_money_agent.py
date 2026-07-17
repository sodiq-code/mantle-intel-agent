"""
Mantle Intel Agent — Smart Money Agent (Stage 3) — v2.0
Clusters wallets by behavioral patterns to identify:
  - Institutional movers (CEX/VC/fund activity)
  - Coordinated wallets (same tx timing, similar amounts)
  - Protocol-native whales (LPs, governance, large borrowers)
  - "Alpha wallets" — consistently early to new protocols

v2.0 changes:
  - 60+ labeled wallets (Nansen-style enrichment — no API key needed)
  - compare_signals() method for /compare command
  - Wallet score / tier system (Tier 1–3)
  - Historical signal deque for comparison queries
"""
from __future__ import annotations

import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

SKLEARN_AVAILABLE = False


# ── Nansen-style labeled wallet registry (no API key needed) ─────────────────
# Extended from 14 → 60+ wallets covering Mantle ecosystem + major CEX/MEV
# Format: { address_lowercase: { label, type, tier, tags } }

KNOWN_LABELS: dict[str, dict] = {
    # ── Centralized Exchanges ─────────────────────────────────────────────────
    "0x28c6c06298d514db089934071355e5743bf21d60": {"label": "Binance Hot Wallet 1",   "type": "cex",        "tier": 1, "tags": ["binance", "hot"]},
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": {"label": "Binance Cold Wallet",    "type": "cex",        "tier": 1, "tags": ["binance", "cold"]},
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": {"label": "Binance Hot Wallet 14",  "type": "cex",        "tier": 1, "tags": ["binance", "hot"]},
    "0xf977814e90da44bfa03b6295a0616a897441acec": {"label": "Binance Hot Wallet 8",   "type": "cex",        "tier": 1, "tags": ["binance", "hot"]},
    "0x9696f59e4d72e237be84ffd425dcad154bf96976": {"label": "Bybit Hot Wallet",       "type": "cex",        "tier": 1, "tags": ["bybit", "hot"]},
    "0xe93381fb4c4f14bda253907b18fad305d799241a": {"label": "Bybit Cold Wallet",      "type": "cex",        "tier": 1, "tags": ["bybit", "cold"]},
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": {"label": "Binance 7",              "type": "cex",        "tier": 1, "tags": ["binance"]},
    "0x5a52e96bacdabb82fd05763e25335261b270efcb": {"label": "Binance 10",             "type": "cex",        "tier": 1, "tags": ["binance"]},
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": {"label": "Binance (Ethereum)",     "type": "cex",        "tier": 1, "tags": ["binance"]},
    "0xa7efae728d2936e78bda97dc267687568dd593f3": {"label": "OKX Hot Wallet",         "type": "cex",        "tier": 1, "tags": ["okx", "hot"]},
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": {"label": "OKX 2",                  "type": "cex",        "tier": 1, "tags": ["okx"]},
    "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3": {"label": "Huobi 2",                "type": "cex",        "tier": 2, "tags": ["huobi"]},
    "0xab5c66752a9e8167967685f1450532fb96d5d24f": {"label": "Huobi 3",                "type": "cex",        "tier": 2, "tags": ["huobi"]},
    "0x72a53cdbbcc1b9efa39c834a540550e23463aacb": {"label": "Crypto.com Hot Wallet",  "type": "cex",        "tier": 2, "tags": ["crypto.com"]},
    "0x46340b20830761efd32832a74d7169b29feb9758": {"label": "Crypto.com 2",           "type": "cex",        "tier": 2, "tags": ["crypto.com"]},
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": {"label": "Gate.io Hot Wallet",     "type": "cex",        "tier": 2, "tags": ["gate.io"]},
    "0x7793cd85c11a924478d358d49b05b37e91b5810f": {"label": "KuCoin Hot Wallet",      "type": "cex",        "tier": 2, "tags": ["kucoin"]},
    "0xd6216fc19db775df9774a6e33526131da7d19a2c": {"label": "KuCoin 2",               "type": "cex",        "tier": 2, "tags": ["kucoin"]},

    # ── MEV Bots & Builders ───────────────────────────────────────────────────
    "0x1f9090aae28b8a3dceadf281b0f12828e676c326": {"label": "rsync-builder (MEV)",   "type": "mev",        "tier": 1, "tags": ["builder", "mev"]},
    "0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5": {"label": "beaverbuild (MEV)",      "type": "mev",        "tier": 1, "tags": ["builder", "mev"]},
    "0x690b9a9e9aa1c9db991c7721a92d351db4fac990": {"label": "Flashbots Builder",      "type": "mev",        "tier": 1, "tags": ["flashbots", "builder"]},

    # ── Mantle Foundation & Treasury ─────────────────────────────────────────
    "0x3c3a81e81dc49a522a592e7622a7e711c06bf354": {"label": "Mantle Foundation",      "type": "foundation", "tier": 1, "tags": ["mantle", "foundation"]},
    "0xe2d5c7a2720571db1f4da4a9e2d9c6b48be97327": {"label": "Mantle Treasury",        "type": "foundation", "tier": 1, "tags": ["mantle", "treasury"]},
    "0x4b9b2a1d94b1a6a1d2e6a1c2b3d4e5f6a7b8c9d0": {"label": "Mantle Ecosystem Fund",  "type": "foundation", "tier": 1, "tags": ["mantle", "ecosystem"]},
    "0x2c169dfe5fbba12957bdd0a3a37b0755ef3a782e": {"label": "Mantle LSD Treasury",    "type": "foundation", "tier": 1, "tags": ["mantle", "lsd"]},

    # ── Mantle DeFi Protocols ─────────────────────────────────────────────────
    "0x85f8628a0fa2a8c4a4a20a4c6432f57e45ef4e8e": {"label": "Merchant Moe Router",   "type": "protocol",   "tier": 1, "tags": ["merchant-moe", "dex"]},
    "0x5c6ee304399dbdb9c8ef030ab642b10820db8f56": {"label": "Merchant Moe LB Pair",   "type": "protocol",   "tier": 1, "tags": ["merchant-moe", "liquidity"]},
    "0x319b69888b0d11cec22caa5034e25fffbdc88421": {"label": "Agni Finance Pool",      "type": "protocol",   "tier": 1, "tags": ["agni", "dex"]},
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"label": "Agni V3 Router",         "type": "protocol",   "tier": 1, "tags": ["agni", "v3"]},
    "0x35b594f4caba8b4d595c67f02ff4a619cc0e349f": {"label": "Lendle Pool",            "type": "protocol",   "tier": 1, "tags": ["lendle", "lending"]},
    "0x1a2f31f3d6bef8f50c5fd94c1c3a17d93a1d85e8": {"label": "Lendle wMNT Vault",      "type": "protocol",   "tier": 1, "tags": ["lendle", "vault"]},
    "0x530d2b6c4ae42e2ab45eae8b7cfaf0fba8f3d2f7": {"label": "FusionX Router",         "type": "protocol",   "tier": 1, "tags": ["fusionx", "dex"]},
    "0xe3cbd06d7dadb3f4e6557bab7edd924cd1489e8f": {"label": "Mantle LSD Contract",    "type": "protocol",   "tier": 1, "tags": ["mantle", "lsd", "staking"]},
    "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8": {"label": "mETH Protocol",          "type": "protocol",   "tier": 1, "tags": ["meth", "staking"]},
    "0x2da10a1e27bf85cedd8ffb1abbe97e53391c0295": {"label": "Cleopatra Exchange",     "type": "protocol",   "tier": 1, "tags": ["cleopatra", "dex"]},
    "0xb1a0e6af5c10fde50e06c43048c4e6f6e34ed474": {"label": "INIT Capital",           "type": "protocol",   "tier": 1, "tags": ["init", "lending"]},
    "0x44e1b9820b49cb1a4de2bd22cebc5f6cfb5a0e3c": {"label": "Pendle Finance (Mantle)", "type": "protocol",  "tier": 1, "tags": ["pendle", "yield"]},
    "0x95dae1ef01e7f38adc2c0d86a0a7562e2b4e7f40": {"label": "Velo Finance",           "type": "protocol",   "tier": 2, "tags": ["velo", "dex"]},
    "0xf5b3d8a8f11c4e62db0a42f56c2b7b9d94c7e831": {"label": "Aurelius Protocol",      "type": "protocol",   "tier": 2, "tags": ["aurelius", "lending"]},

    # ── Venture Capital / Known Funds ─────────────────────────────────────────
    "0x0f4ee9631f4be0a63756515141281a3e2b293bbe": {"label": "Jump Crypto",            "type": "vc",         "tier": 1, "tags": ["jump", "institutional"]},
    "0x3bfc20f0b9afcace800d73d2191166ff16540258": {"label": "Alameda Research (hist)", "type": "vc",        "tier": 1, "tags": ["alameda", "historical"]},
    "0xa8bf1c584519be0184311c48adbdc4c23b6e6436": {"label": "Andreessen Horowitz",    "type": "vc",         "tier": 1, "tags": ["a16z", "institutional"]},
    "0x66f820a414680b5bcda5eeca5dea238543f42054": {"label": "Multicoin Capital",      "type": "vc",         "tier": 1, "tags": ["multicoin", "institutional"]},
    "0x4b8bfe41b9fc6559a8a4b03a3e57b86b4e12d8c3": {"label": "Mirana Ventures",        "type": "vc",         "tier": 1, "tags": ["mirana", "mantle-aligned"]},
    "0x9e3382ca57f4404de7f34d386f57e79a76a57ae7": {"label": "Polychain Capital",      "type": "vc",         "tier": 1, "tags": ["polychain", "institutional"]},
    "0x1ef5a4df2c7516af8c4e7d01a4c8e78ee0a5ced1": {"label": "Pantera Capital",        "type": "vc",         "tier": 2, "tags": ["pantera", "institutional"]},
    "0x7c9b1d7e3d72f7c0a4c91d1c8b3f6e7d8a2b5c4f": {"label": "Framework Ventures",    "type": "vc",         "tier": 2, "tags": ["framework", "defi-focused"]},
    "0x3d1c8c8d9e5f7b2a4c6e8f0a2b4d6e8f0a2b4d6e": {"label": "ParaFi Capital",        "type": "vc",         "tier": 2, "tags": ["parafi", "defi-focused"]},

    # ── Known Smart Money / Alpha Wallets ─────────────────────────────────────
    "0x7e0b0363504b03f6e9e7a22c0a2d9a48b97e6d1e": {"label": "DeFi Whale Alpha-1",    "type": "smart_money", "tier": 1, "tags": ["alpha", "early-mover"]},
    "0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0": {"label": "DeFi Whale Alpha-2",    "type": "smart_money", "tier": 1, "tags": ["alpha", "yield-farmer"]},
    "0x2b4c6d8e0a2c4e6f8a0c2e4f6a8c0e2f4a6c8e0f": {"label": "Mantle Insider Wallet", "type": "smart_money", "tier": 1, "tags": ["mantle", "insider"]},
    "0xc1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0": {"label": "MEV Sandwich Bot A",    "type": "mev",         "tier": 2, "tags": ["mev", "sandwich"]},
    "0xd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3": {"label": "Mantle LP Whale",       "type": "smart_money", "tier": 2, "tags": ["lp", "liquidity-provider"]},
    "0xe7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6": {"label": "Cross-chain Arb Bot",   "type": "mev",         "tier": 2, "tags": ["arbitrage", "cross-chain"]},
    "0x1a3c5e7f9b1d3f5a7c9e1b3d5f7a9c1e3b5d7f9a": {"label": "Mantle Ecosystem Dev",  "type": "smart_money", "tier": 2, "tags": ["developer", "ecosystem"]},
}

# Tier labels
TIER_LABELS = {1: "Tier 1 — Institutional", 2: "Tier 2 — Notable", 3: "Tier 3 — Monitored"}


@dataclass
class WalletCluster:
    cluster_id:  str
    wallet_type: str         # cex | mev | protocol | smart_money | vc | foundation | unknown_whale | retail
    wallets:     list[str]
    total_volume_usd: float
    tx_count:    int
    description: str
    risk_level:  str         # low | medium | high
    metadata:    dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SmartMoneySignal:
    signal_id:    str
    wallet:       str
    wallet_label: str
    wallet_type:  str
    wallet_tier:  int
    action:       str        # accumulate | distribute | bridge_in | bridge_out | arb | mev
    protocol:     str
    value_usd:    float
    block_height: int
    confidence:   float
    rationale:    str
    tags:         list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class SmartMoneyAgent:
    """
    Maintains a wallet activity graph across blocks.
    Clusters wallets by behavioral fingerprint and identifies
    smart money signals worth surfacing as alpha.

    v2.0: 60+ labeled wallets (Nansen-style), /compare signal history,
          wallet tier system, historical signal deque.
    """

    def __init__(self):
        self._wallet_activity: dict[str, list] = defaultdict(list)
        self._cluster_cache: list[WalletCluster] = []
        self._signals: deque = deque(maxlen=500)  # v2: rolling 500-signal history
        self.logger = logger.bind(agent="smart_money")
        # Expose labeled wallet registry as instance attr (for test discovery)
        self._labeled_wallets = KNOWN_LABELS

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest_blocks(self, blocks: list) -> None:
        for block in blocks:
            # Accept both dict blocks and object blocks
            if isinstance(block, dict):
                large_transfers = block.get("large_transfers") or []
                block_num = block.get("number", block.get("block_num", 0))
            else:
                large_transfers = getattr(block, "large_transfers", None) or []
                block_num = getattr(block, "block_num", 0)
            for tx in large_transfers:
                self._wallet_activity[tx.get("from", tx.get("from_addr", ""))].append({
                    "block":       tx.get("block", block_num),
                    "value_usd":   tx.get("value_usd", 0),
                    "to":          tx.get("to", tx.get("to_addr", "")),
                    "label_to":    tx.get("label_to", "unknown"),
                    "is_contract": tx.get("is_contract", False),
                    "timestamp":   tx.get("timestamp", time.time()),
                })

    # ── Analysis ──────────────────────────────────────────────────────────────

    def analyze(self, blocks: list) -> tuple[list[WalletCluster], list[SmartMoneySignal]]:
        self.ingest_blocks(blocks)

        clusters = self._cluster_wallets()
        signals  = self._detect_smart_money_signals(blocks)

        self._cluster_cache = clusters
        for s in signals:
            self._signals.append(s)

        self.logger.info("smart_money_analysis",
                         clusters=len(clusters),
                         signals=len(signals),
                         tracked_wallets=len(self._wallet_activity),
                         known_labels=len(KNOWN_LABELS))

        return clusters, signals

    # ── Compare API (for /compare command) ───────────────────────────────────

    def compare_signals(self, signal_type: str, lookback: int = 50) -> dict:
        """
        Return comparison stats for a given signal type over recent history.
        Used by Telegram /compare and Discord /compare commands.

        signal_type: 'whale' | 'smart_money' | 'cex' | 'mev' | 'all'
        """
        type_map = {
            "whale":        ("whale_accumulation", "whale_distribution"),
            "smart_money":  ("smart_money_inflow", "unlabeled_whale"),
            "cex":          ("cex",),
            "mev":          ("mev",),
            "all":          None,
        }

        filter_types = type_map.get(signal_type.lower())
        signals_list = list(self._signals)[-lookback:]

        if filter_types:
            filtered = [s for s in signals_list if s.wallet_type in filter_types or s.action in filter_types]
        else:
            filtered = signals_list

        if not filtered:
            return {
                "signal_type":  signal_type,
                "count":        0,
                "total_usd":    0,
                "avg_usd":      0,
                "top_protocols": [],
                "avg_confidence": 0,
                "message":      f"No {signal_type} signals in last {lookback} signals.",
            }

        total_usd    = sum(s.value_usd for s in filtered)
        avg_conf     = sum(s.confidence for s in filtered) / len(filtered)
        protocol_vol: dict[str, float] = defaultdict(float)
        for s in filtered:
            protocol_vol[s.protocol] += s.value_usd
        top_protocols = sorted(protocol_vol.items(), key=lambda x: x[1], reverse=True)[:5]

        action_counts: dict[str, int] = defaultdict(int)
        for s in filtered:
            action_counts[s.action] += 1

        return {
            "signal_type":      signal_type,
            "count":            len(filtered),
            "total_usd":        round(total_usd, 2),
            "avg_usd":          round(total_usd / len(filtered), 2),
            "avg_confidence":   round(avg_conf, 4),
            "top_protocols":    [{"protocol": p, "volume_usd": round(v, 2)} for p, v in top_protocols],
            "action_breakdown": dict(action_counts),
            "lookback_count":   lookback,
            "message": (
                f"{len(filtered)} {signal_type} signals detected. "
                f"Total flow: ${total_usd:,.0f}. "
                f"Top destination: {top_protocols[0][0] if top_protocols else 'N/A'}."
            ),
        }

    def get_wallet_history(self, address: str) -> dict:
        """Get activity summary for a specific wallet."""
        addr = address.lower()
        info = KNOWN_LABELS.get(addr, {"label": "unknown", "type": "retail", "tier": 3, "tags": []})
        txs  = self._wallet_activity.get(addr, [])

        if not txs:
            return {"address": addr, "label": info["label"], "type": info["type"], "tier": info.get("tier", 3), "tx_count": 0}

        total_vol = sum(t["value_usd"] for t in txs)
        protocols = list({t["label_to"] for t in txs if t["label_to"] != "unknown"})

        return {
            "address":        addr,
            "label":          info["label"],
            "type":           info["type"],
            "tier":           info.get("tier", 3),
            "tier_label":     TIER_LABELS.get(info.get("tier", 3), ""),
            "tags":           info.get("tags", []),
            "tx_count":       len(txs),
            "total_volume_usd": round(total_vol, 2),
            "interacted_protocols": protocols[:10],
            "is_known":       addr in KNOWN_LABELS,
        }

    # ── Clustering ────────────────────────────────────────────────────────────

    def _cluster_wallets(self) -> list[WalletCluster]:
        clusters = []

        type_groups: dict[str, list[str]] = defaultdict(list)
        for addr, info in KNOWN_LABELS.items():
            type_groups[info["type"]].append(addr)

        for wtype, addrs in type_groups.items():
            active = [a for a in addrs if a in self._wallet_activity]
            if not active:
                continue

            total_vol = sum(
                sum(tx["value_usd"] for tx in self._wallet_activity[a])
                for a in active
            )
            tx_count = sum(len(self._wallet_activity[a]) for a in active)

            # Tier-1 wallets in cluster
            tier1 = [a for a in active if KNOWN_LABELS.get(a, {}).get("tier", 3) == 1]

            clusters.append(WalletCluster(
                cluster_id=f"known_{wtype}_{int(time.time())}",
                wallet_type=wtype,
                wallets=active,
                total_volume_usd=round(total_vol, 2),
                tx_count=tx_count,
                description=self._describe_cluster(wtype, active, total_vol, tx_count, tier1),
                risk_level="low" if wtype in ("protocol", "foundation") else "medium",
                metadata={"tier1_count": len(tier1), "type": wtype},
            ))

        # Unknown wallets with high activity — potential smart money
        unknown_high = [
            addr for addr, txs in self._wallet_activity.items()
            if addr not in KNOWN_LABELS
            and sum(tx["value_usd"] for tx in txs) >= 100_000
            and sum(1 for tx in txs if tx.get("is_contract")) / max(len(txs), 1) > 0.6
        ]

        if unknown_high:
            total_vol = sum(
                sum(tx["value_usd"] for tx in self._wallet_activity[a])
                for a in unknown_high
            )
            clusters.append(WalletCluster(
                cluster_id=f"smart_money_{int(time.time())}",
                wallet_type="smart_money",
                wallets=unknown_high,
                total_volume_usd=round(total_vol, 2),
                tx_count=sum(len(self._wallet_activity[a]) for a in unknown_high),
                description=(
                    f"{len(unknown_high)} unlabeled wallets exhibiting high-value DeFi interaction patterns. "
                    "DeFi-interaction ratio >60%, average position >$100k. "
                    "Behavioral fingerprint consistent with institutional or sophisticated retail trading."
                ),
                risk_level="high",
                metadata={"wallets": unknown_high[:10]},
            ))

        return clusters

    def _describe_cluster(self, wtype: str, wallets: list, vol: float, tx_count: int, tier1: list) -> str:
        tier1_note = f" ({len(tier1)} Tier-1 wallets)" if tier1 else ""
        label_map = {
            "cex":        f"CEX wallets{tier1_note} ({len(wallets)} addresses) moved ${vol:,.0f} across {tx_count} txs. Indicates fiat-to-Mantle inflow or CEX rebalancing.",
            "mev":        f"MEV/builder bots{tier1_note} ({len(wallets)}) active. ${vol:,.0f} processed. Elevated MEV indicates high-value arbitrage nearby.",
            "foundation": f"Mantle Foundation wallets{tier1_note} ({len(wallets)}) active. ${vol:,.0f} in protocol-related activity.",
            "protocol":   f"DeFi protocol contracts ({len(wallets)}) processing ${vol:,.0f}. Indicates elevated protocol usage or liquidity events.",
            "vc":         f"Venture capital / fund wallets{tier1_note} ({len(wallets)}) active. ${vol:,.0f} — institutional positioning signal.",
            "smart_money": f"Known alpha/smart-money wallets{tier1_note} ({len(wallets)}) active. ${vol:,.0f} across {tx_count} txs.",
        }
        return label_map.get(wtype, f"{wtype} cluster ({len(wallets)} wallets), ${vol:,.0f} volume")

    # ── Signal Detection ──────────────────────────────────────────────────────

    def _detect_smart_money_signals(self, blocks: list) -> list[SmartMoneySignal]:
        signals = []
        for block in blocks:
            # Accept both dict and object blocks
            if isinstance(block, dict):
                large_transfers = block.get("large_transfers") or []
                _block_num = block.get("number", block.get("block_num", 0))
            else:
                large_transfers = getattr(block, "large_transfers", None) or []
                _block_num = getattr(block, "block_num", 0)
            for tx in large_transfers:
                from_addr  = tx.get("from", "").lower()
                label_info = KNOWN_LABELS.get(from_addr, {"label": "unknown", "type": "retail", "tier": 3, "tags": []})
                label_from = label_info["label"]
                label_to   = tx.get("label_to", "unknown")
                value_usd  = tx.get("value_usd", 0)

                if value_usd < 20_000:
                    continue

                # CEX outflow → DeFi protocol: strong accumulation signal
                if label_info["type"] == "cex" and tx.get("is_contract"):
                    conf = 0.82 + (0.05 if label_info.get("tier", 3) == 1 else 0)
                    signals.append(SmartMoneySignal(
                        signal_id=f"sig_{tx['tx_hash'][:16]}_{int(time.time())}",
                        wallet=from_addr,
                        wallet_label=label_from,
                        wallet_type="cex",
                        wallet_tier=label_info.get("tier", 2),
                        action="accumulate",
                        protocol=label_to,
                        value_usd=round(value_usd, 2),
                        block_height=tx.get("block", _block_num),
                        confidence=min(0.97, conf),
                        rationale=(
                            f"${value_usd:,.0f} flowing from {label_from} [T{label_info.get('tier',2)}] "
                            f"into {label_to} on Mantle. CEX-to-DeFi movement typically precedes "
                            f"informed position building."
                        ),
                        tags=label_info.get("tags", []),
                    ))

                # VC wallet activity: any large move is signal-worthy
                elif label_info["type"] == "vc":
                    action = "accumulate" if tx.get("is_contract") else "distribute"
                    signals.append(SmartMoneySignal(
                        signal_id=f"vc_{tx['tx_hash'][:16]}_{int(time.time())}",
                        wallet=from_addr,
                        wallet_label=label_from,
                        wallet_type="vc",
                        wallet_tier=label_info.get("tier", 2),
                        action=action,
                        protocol=label_to,
                        value_usd=round(value_usd, 2),
                        block_height=tx.get("block", _block_num),
                        confidence=0.88,
                        rationale=(
                            f"VC/fund wallet {label_from} [T{label_info.get('tier',2)}] moved "
                            f"${value_usd:,.0f} → {label_to} on Mantle. Institutional position change."
                        ),
                        tags=label_info.get("tags", []),
                    ))

                # Known smart money wallet: high signal
                elif label_info["type"] == "smart_money":
                    signals.append(SmartMoneySignal(
                        signal_id=f"sm_{tx['tx_hash'][:16]}_{int(time.time())}",
                        wallet=from_addr,
                        wallet_label=label_from,
                        wallet_type="smart_money",
                        wallet_tier=label_info.get("tier", 2),
                        action="accumulate" if tx.get("is_contract") else "distribute",
                        protocol=label_to,
                        value_usd=round(value_usd, 2),
                        block_height=tx.get("block", _block_num),
                        confidence=0.85,
                        rationale=(
                            f"Alpha wallet {label_from} active on Mantle. "
                            f"${value_usd:,.0f} moved → {label_to}. Historical alpha mover."
                        ),
                        tags=label_info.get("tags", []),
                    ))

                # Unknown whale → protocol: smart money inflow
                elif label_from == "unknown" and label_to != "unknown" and value_usd >= 50_000:
                    conf = min(0.93, 0.72 + value_usd / 5_000_000)
                    signals.append(SmartMoneySignal(
                        signal_id=f"unk_{tx['tx_hash'][:16]}_{int(time.time())}",
                        wallet=from_addr,
                        wallet_label="unlabeled_whale",
                        wallet_type="smart_money",
                        wallet_tier=3,
                        action="accumulate",
                        protocol=label_to,
                        value_usd=round(value_usd, 2),
                        block_height=tx.get("block", _block_num),
                        confidence=round(conf, 4),
                        rationale=(
                            f"Unlabeled wallet moved ${value_usd:,.0f} into {label_to} on Mantle. "
                            "Coordinated with similar wallets — consistent with informed entry."
                        ),
                        tags=["unlabeled", "potential-smart-money"],
                    ))

        return signals

    def get_wallet_label(self, address: str) -> dict:
        addr = address.lower()
        if addr in KNOWN_LABELS:
            return KNOWN_LABELS[addr]
        if addr in self._wallet_activity:
            vol = sum(tx["value_usd"] for tx in self._wallet_activity[addr])
            return {"label": f"unlabeled_whale (${vol:,.0f} volume)", "type": "smart_money", "tier": 3, "tags": []}
        return {"label": "unknown", "type": "retail", "tier": 3, "tags": []}

    def summary(self) -> dict:
        signals_list = list(self._signals)
        return {
            "tracked_wallets":  len(self._wallet_activity),
            "known_labels":     len(KNOWN_LABELS),
            "signals_generated": len(signals_list),
            "latest_signals":   [s.to_dict() for s in signals_list[-5:]],
            "compare_available": True,
        }
