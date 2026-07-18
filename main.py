"""
Mantle Intel Agent — Entry Point
Usage:
    python main.py              # Run one cycle (demo)
    python main.py --loop       # Run continuously
    python main.py --bot        # Run with Telegram bot
    python main.py --backtest   # Run backtest analysis
    python main.py --cycles 3   # Run N cycles
"""
from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True),
    ]
)

from agents.pipeline import MantleIntelPipeline
from bot.telegram_bot import MantleIntelBot


def _send_telegram_direct(incident: dict):
    """Direct HTTP Telegram alert — no dependencies, always works."""
    import urllib.request, ssl
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    atype = incident.get("type", "anomaly")
    block = incident.get("latest_block", incident.get("block", "?"))
    conf = incident.get("peak_confidence", incident.get("confidence_pct", 0))
    state = incident.get("state", "NEW")
    text = (
        f"🔍 *Mantle Intel Alert*\n"
        f"Type: `{atype}`\n"
        f"Block: `{block}`\n"
        f"Confidence: `{conf}%`\n"
        f"State: `{state}`\n"
        f"Contract: `0x7266cD15...Ed530b`"
    )
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10, context=ctx)
    except Exception:
        pass  # Best-effort alert


def print_banner():
    print("\n" + "="*70)
    print("  MANTLE INTEL AGENT")
    print("  Autonomous On-Chain Intelligence for Mantle Network")
    print("  Mantle Intel Agent — On-Chain Intelligence for the Mantle Ecosystem")
    print("="*70 + "\n")


def print_finding(finding: dict):
    atype   = finding.get("type", "anomaly")
    block   = finding.get("block", 0)
    conf    = finding.get("confidence_pct", 0)
    insight = finding.get("insight", "")
    fhash   = finding.get("hash", "")
    audit   = finding.get("audit", {})

    icons = {
        "whale_accumulation": "🐋",
        "smart_money_inflow": "🧠",
        "tx_spike":           "📈",
        "value_spike":        "💰",
        "multivariate_anomaly": "🔍",
    }
    icon = icons.get(atype, "⚡")

    print(f"\n{'-'*60}")
    print(f"{icon}  [{atype.upper()}]  Block {block:,}  |  Confidence: {conf}%")
    print(f"{'-'*60}")
    print(insight[:600])
    print(f"\n📎 Finding Hash: {fhash[:32]}...")
    print(f"🔐 Audit Status: {audit.get('status', 'unknown')}")
    if audit.get("tx_hash"):
        print(f"🔗 On-Chain TX: {audit.get('tx_hash', '')[:40]}...")


async def run_demo(args):
    """Run pipeline demo mode."""
    print_banner()
    print(f"Mode: {'Continuous loop' if args.loop else f'{args.cycles} cycle(s)'}")
    print(f"Telegram bot: {'enabled' if args.bot else 'disabled'}")
    print()

    bot = None
    if args.bot:
        bot = MantleIntelBot()
        if not bot.is_configured():
            print("⚠️  Telegram bot: TELEGRAM_BOT_TOKEN not set — running without bot")
            bot = None

    async def on_incident(incident: dict):
        print_finding(incident)
        if bot:
            await bot.push_incident(incident)
        # Direct Telegram fallback (works without python-telegram-bot)
        _send_telegram_direct(incident)

    pipeline = MantleIntelPipeline(
        on_incident=on_incident,
        poll_interval=30,
        blocks_per_cycle=100,
    )

    if bot:
        bot.set_pipeline(pipeline)

    if args.loop:
        print("Starting continuous pipeline loop. Ctrl+C to stop.\n")
        if bot and bot.is_configured():
            bot_task = asyncio.create_task(bot.run_polling())
            pipeline_task = asyncio.create_task(pipeline.run_continuous())
            await asyncio.gather(bot_task, pipeline_task)
        else:
            await pipeline.run_continuous()
    else:
        total_findings = []
        for i in range(args.cycles):
            print(f"\n⟳ Running cycle {i+1}/{args.cycles}...")
            findings = await pipeline.run_cycle()
            total_findings.extend(findings)
            if i < args.cycles - 1:
                await asyncio.sleep(2)

        stats = pipeline.get_stats()
        print(f"\n{'='*60}")
        print(f"  PIPELINE COMPLETE")
        print(f"  Cycles: {stats['cycles_run']} | Blocks: {stats['blocks_processed']} | Findings: {stats['findings_total']}")
        print(f"  Data saved to: data/findings.jsonl")
        print(f"  Dashboard: data/dashboard.json")
        print(f"{'='*60}\n")

        return total_findings


async def run_backtest(args):
    """Run backtest analysis on simulated data."""
    print_banner()
    print("Running backtest analysis on Mantle blockchain data...\n")

    from backtest.backtest import run_backtest as do_backtest
    await do_backtest()


def main():
    parser = argparse.ArgumentParser(description="Mantle Intel Agent")
    parser.add_argument("--loop",     action="store_true", help="Run continuously")
    parser.add_argument("--bot",      action="store_true", help="Enable Telegram bot")
    parser.add_argument("--backtest", action="store_true", help="Run backtest")
    parser.add_argument("--cycles",   type=int, default=1, help="Number of cycles to run")
    args = parser.parse_args()

    try:
        if args.backtest:
            asyncio.run(run_backtest(args))
        else:
            asyncio.run(run_demo(args))
    except KeyboardInterrupt:
        print("\n\nStopped by user.")


if __name__ == "__main__":
    main()
