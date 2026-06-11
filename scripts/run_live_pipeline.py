#!/usr/bin/env python3
"""
Mantle Intel Agent — Autonomous Live Pipeline
Runs all 5 agents in a continuous loop with uptime logging.

Usage:
    python3 scripts/run_live_pipeline.py [--interval 60] [--cycles N]

Environment:
    MANTLE_RPC_URL   — override default mainnet RPC
    PRIVATE_KEY      — deployer key for on-chain audit writes
    TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID — bot alert channel
"""

import os
import sys
import time
import json
import logging
import argparse
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent
DATA_DIR  = ROOT / "data"
LOG_DIR   = ROOT / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

UPTIME_FILE   = DATA_DIR / "uptime.json"
FINDINGS_FILE = DATA_DIR / "findings_live.json"

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "pipeline.log"),
    ],
)
log = logging.getLogger("pipeline")

# ── agent imports ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(ROOT))
try:
    from agents.collector.collector_agent    import CollectorAgent
    from agents.anomaly.anomaly_agent        import AnomalyAgent
    from agents.smartmoney.smartmoney_agent  import SmartMoneyAgent
    from agents.audit.audit_agent            import AuditAgent
    from agents.telegram.telegram_bot        import TelegramBot
    AGENTS_OK = True
except ImportError as e:
    log.warning(f"Agent import issue: {e} — running in lightweight mode")
    AGENTS_OK = False


# ── uptime tracker ────────────────────────────────────────────────────────────
def load_uptime() -> dict:
    if UPTIME_FILE.exists():
        try:
            return json.loads(UPTIME_FILE.read_text())
        except Exception:
            pass
    return {
        "start_time": datetime.now(timezone.utc).isoformat(),
        "total_cycles": 0,
        "successful_cycles": 0,
        "failed_cycles": 0,
        "findings_emitted": 0,
        "on_chain_writes": 0,
        "last_heartbeat": None,
        "last_block": None,
        "agent_versions": {
            "collector": "1.0",
            "anomaly": "1.0",
            "smartmoney": "1.0",
            "audit": "1.0",
            "telegram": "1.0",
        },
        "sessions": [],
    }


def save_uptime(state: dict):
    state["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    UPTIME_FILE.write_text(json.dumps(state, indent=2))


# ── lightweight fallback cycle (no full agent import) ─────────────────────────
def lightweight_cycle(state: dict, rpc_url: str) -> dict:
    """Direct RPC fetch + anomaly check without full agent stack."""
    import urllib.request, struct, random

    payload = json.dumps({
        "jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1
    }).encode()
    req = urllib.request.Request(
        rpc_url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        block_hex = json.loads(r.read())["result"]
        block_num = int(block_hex, 16)

    # fetch last 10 blocks for context
    findings = []
    for _ in range(3):
        blk_payload = json.dumps({
            "jsonrpc": "2.0", "method": "eth_getBlockByNumber",
            "params": [hex(block_num), True], "id": 2
        }).encode()
        req2 = urllib.request.Request(
            rpc_url, data=blk_payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req2, timeout=10) as r2:
            blk = json.loads(r2.read()).get("result", {})
        txs = blk.get("transactions", [])
        tx_count = len(txs)
        if tx_count >= 6:
            findings.append({
                "block": block_num,
                "type": "tx_spike",
                "tx_count": tx_count,
                "confidence": min(0.5 + tx_count * 0.05, 0.95),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            log.info(f"Anomaly detected block {block_num}: tx_spike (count={tx_count})")
        block_num -= 1

    state["last_block"] = block_num
    return findings


# ── full agent cycle ──────────────────────────────────────────────────────────
def full_agent_cycle(state: dict) -> dict:
    """Run all 5 agents in sequence."""
    collector   = CollectorAgent()
    anomaly     = AnomalyAgent()
    smartmoney  = SmartMoneyAgent()
    audit       = AuditAgent()

    # 1. collect
    blocks = collector.collect(blocks=20)
    # 2. detect
    findings = anomaly.detect(blocks)
    # 3. enrich
    for f in findings:
        f["smart_money"] = smartmoney.enrich(f)
    # 4. audit write (if private key available)
    if os.environ.get("PRIVATE_KEY"):
        for f in findings:
            try:
                tx = audit.submit_finding(f)
                if tx:
                    f["tx_hash"] = tx
                    state["on_chain_writes"] = state.get("on_chain_writes", 0) + 1
                    log.info(f"On-chain finding written: {tx}")
            except Exception as e:
                log.warning(f"Audit write failed: {e}")

    return findings


# ── persist findings ──────────────────────────────────────────────────────────
def persist_findings(findings: list):
    existing = []
    if FINDINGS_FILE.exists():
        try:
            existing = json.loads(FINDINGS_FILE.read_text())
        except Exception:
            pass
    combined = existing + findings
    # keep last 1000
    FINDINGS_FILE.write_text(json.dumps(combined[-1000:], indent=2))


# ── telegram alert ────────────────────────────────────────────────────────────
def send_telegram(findings: list):
    token   = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    import urllib.request
    for f in findings:
        text = (
            f"🔍 *Mantle Intel Alert*\n"
            f"Block: `{f.get('block','?')}`\n"
            f"Type: `{f.get('type','?')}`\n"
            f"Confidence: `{f.get('confidence',0):.1%}`\n"
            f"TXs: `{f.get('tx_count','?')}`"
        )
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }).encode()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            log.warning(f"Telegram send failed: {e}")


# ── main loop ─────────────────────────────────────────────────────────────────
def run(interval: int = 60, max_cycles: int = 0):
    rpc_url = os.environ.get("MANTLE_RPC_URL", "https://rpc.mantle.xyz")
    state   = load_uptime()

    # record session start
    session = {
        "start": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "mode": "full" if AGENTS_OK else "lightweight",
        "interval_s": interval,
    }
    state.setdefault("sessions", []).append(session)
    save_uptime(state)

    log.info(f"Mantle Intel Agent pipeline started (mode={'full' if AGENTS_OK else 'lightweight'}, interval={interval}s)")
    log.info(f"RPC: {rpc_url}")
    log.info(f"Uptime file: {UPTIME_FILE}")

    cycle = 0
    try:
        while True:
            cycle += 1
            log.info(f"── Cycle {cycle} ──────────────────────────────")
            state["total_cycles"] += 1

            try:
                if AGENTS_OK:
                    findings = full_agent_cycle(state)
                else:
                    findings = lightweight_cycle(state, rpc_url)

                state["successful_cycles"] += 1
                state["findings_emitted"] = state.get("findings_emitted", 0) + len(findings)

                if findings:
                    persist_findings(findings)
                    send_telegram(findings)
                    log.info(f"Cycle {cycle}: {len(findings)} findings emitted")
                else:
                    log.info(f"Cycle {cycle}: no anomalies detected")

            except Exception as e:
                state["failed_cycles"] += 1
                log.error(f"Cycle {cycle} failed: {e}")
                log.debug(traceback.format_exc())

            save_uptime(state)

            if max_cycles and cycle >= max_cycles:
                log.info(f"Reached max_cycles={max_cycles}, stopping.")
                break

            log.info(f"Sleeping {interval}s...")
            time.sleep(interval)

    except KeyboardInterrupt:
        log.info("Pipeline stopped by user.")

    session["end"]    = datetime.now(timezone.utc).isoformat()
    session["cycles"] = cycle
    save_uptime(state)
    log.info(f"Pipeline exited. Total cycles: {cycle}, findings: {state['findings_emitted']}")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mantle Intel Agent autonomous pipeline")
    parser.add_argument("--interval", type=int, default=60,  help="Seconds between cycles (default: 60)")
    parser.add_argument("--cycles",   type=int, default=0,   help="Max cycles to run (0=infinite)")
    args = parser.parse_args()
    run(interval=args.interval, max_cycles=args.cycles)
