"""
Standalone Telegram bot runner for Mantle Intel Agent.
Runs without the full pipeline — responds to /start, /status, /latest, /verify
and shows live demo data from findings.jsonl if available.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Load .env manually
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CONTRACT = os.environ.get("AUDIT_CONTRACT_ADDRESS", "0x03C88A1060626581854DB94e955a6be291782abb")
EXPLORER = "https://sepolia.mantlescan.xyz"
FINDINGS_FILE = Path(__file__).parent.parent / "data" / "findings.jsonl"
START_TIME = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

WELCOME = """🔍 <b>Mantle Intel Agent</b>

Autonomous on-chain intelligence for Mantle Network.
Detects whale moves, smart money inflows, and anomalous patterns — every finding verified on-chain.

<b>Commands:</b>
/start    — This message
/status   — Pipeline status + stats
/latest   — Last 5 findings
/verify &lt;hash&gt; — Verify a finding hash on-chain

<i>Built for the Find Evil! 2026 Hackathon — Alpha &amp; Data Track</i>
"""

def load_findings():
    findings = []
    if FINDINGS_FILE.exists():
        for line in FINDINGS_FILE.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    findings.append(json.loads(line))
                except Exception:
                    pass
    return findings

def fmt_finding(f: dict) -> str:
    icons = {
        "whale_accumulation": "🐋",
        "whale_distribution": "⚠️",
        "smart_money_inflow": "🧠",
        "tx_spike":           "📈",
        "value_spike":        "💰",
        "multivariate_anomaly": "🔍",
    }
    labels = {
        "whale_accumulation":   "Whale Accumulation",
        "whale_distribution":   "Whale Distribution",
        "smart_money_inflow":   "Smart Money Inflow",
        "tx_spike":             "TX Volume Spike",
        "value_spike":          "Value Spike",
        "multivariate_anomaly": "Multivariate Anomaly",
    }
    atype   = f.get("type", "anomaly")
    block   = f.get("block", 0)
    conf    = f.get("confidence_pct", f.get("confidence", 0))
    fhash   = f.get("hash", "")
    insight = f.get("insight", f.get("summary", "No insight available."))
    if len(insight) > 600:
        insight = insight[:600] + "..."
    audit   = f.get("audit", {})
    tx      = audit.get("tx_hash", "")
    status  = audit.get("status", "")

    if tx and status in ("recorded", "demo"):
        audit_line = f'🔗 <a href="{EXPLORER}/tx/{tx}">View on Mantle Explorer</a>'
    elif status == "demo":
        audit_line = "📝 On-chain hash recorded (demo mode)"
    else:
        audit_line = "⏳ Audit pending"

    return (
        f"{icons.get(atype, '⚡')} <b>{labels.get(atype, atype.replace('_',' ').title())}</b>\n"
        f"Block <code>{block:,}</code> · Confidence <b>{conf}%</b>\n\n"
        f"{insight}\n\n"
        f"🔐 Hash: <code>{fhash[:20]}{'...' if fhash else ''}</code>\n"
        f"{audit_line}"
    ).strip()

# ── Handlers ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(WELCOME)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    findings = load_findings()
    blocks = set(f.get("block", 0) for f in findings)
    msg = (
        f"📊 <b>Pipeline Status</b>\n\n"
        f"🔗 Network: <code>Mantle Sepolia (testnet)</code>\n"
        f"📦 Contract: <code>{CONTRACT}</code>\n"
        f"🚨 Findings total: <b>{len(findings)}</b>\n"
        f"📦 Unique blocks: <b>{len(blocks)}</b>\n"
        f"⏱ Bot started: <code>{START_TIME}</code>\n\n"
        f"Mode: 🟡 Demo Mode\n"
        f'🔗 <a href="{EXPLORER}/address/{CONTRACT}">View Contract on Explorer</a>'
    )
    await update.message.reply_html(msg)

async def cmd_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    findings = load_findings()
    if not findings:
        await update.message.reply_text("No findings yet. Run the pipeline first.")
        return
    for f in findings[-5:]:
        await update.message.reply_html(fmt_finding(f))
        await asyncio.sleep(0.4)

async def cmd_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /verify <finding_hash>")
        return
    query = context.args[0].lstrip("0x").lower()
    findings = load_findings()
    match = next((f for f in findings if f.get("hash", "").lower().lstrip("0x").startswith(query[:16])), None)
    if match:
        audit  = match.get("audit", {})
        tx     = audit.get("tx_hash", "")
        status = audit.get("status", "unknown")
        msg = (
            f"✅ <b>Finding Found</b>\n\n"
            f"Type: <b>{match.get('type','?')}</b>\n"
            f"Block: <code>{match.get('block',0):,}</code>\n"
            f"Confidence: <b>{match.get('confidence_pct', match.get('confidence', 0))}%</b>\n"
            f"Hash: <code>{match.get('hash','')[:32]}...</code>\n"
            f"Audit status: <code>{status}</code>\n"
        )
        if tx:
            msg += f'\n🔗 <a href="{EXPLORER}/tx/{tx}">View TX on Mantle Explorer</a>'
        else:
            msg += f'\n🔗 <a href="{EXPLORER}/address/{CONTRACT}">View Contract</a>'
    else:
        msg = (
            f"❌ <b>Finding Not Found</b>\n\n"
            f"Hash <code>{query[:20]}...</code> is not in the local findings store.\n"
            f"It may be a demo-mode finding or an invalid hash."
        )
    await update.message.reply_html(msg)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    print(f"Starting Mantle Intel Agent bot...")
    print(f"Contract: {CONTRACT}")
    print(f"Findings file: {FINDINGS_FILE}")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("latest", cmd_latest))
    app.add_handler(CommandHandler("verify", cmd_verify))
    print("Bot is polling. Send /start in Telegram to test.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
