"""
Mantle Intel Agent — FastAPI Server
Serves dashboard data and exposes API for the React frontend.
Run: uvicorn server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

import structlog
structlog.configure(processors=[structlog.dev.ConsoleRenderer(colors=True)])

from agents.pipeline import MantleIntelPipeline

app = FastAPI(title="Mantle Intel Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
_pipeline: MantleIntelPipeline | None = None
_pipeline_task = None

DATA_DIR      = Path("data")
FINDINGS_PATH = DATA_DIR / "findings.jsonl"
DASHBOARD_PATH = DATA_DIR / "dashboard.json"

DATA_DIR.mkdir(exist_ok=True)


def get_pipeline() -> MantleIntelPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = MantleIntelPipeline(poll_interval=30, blocks_per_cycle=100)
    return _pipeline


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "mantle-intel-agent"}


@app.get("/api/dashboard")
async def dashboard():
    """Main dashboard data endpoint."""
    if DASHBOARD_PATH.exists():
        with open(DASHBOARD_PATH) as f:
            return JSONResponse(content=json.load(f))

    # Return empty state if pipeline hasn't run yet
    return JSONResponse(content={
        "last_updated": None,
        "stats": {"cycles_run": 0, "blocks_processed": 0, "findings_total": 0},
        "latest_findings": [],
        "smart_money_summary": {},
        "demo_mode": True,
        "contract_address": os.getenv("AUDIT_CONTRACT_ADDRESS", "not_deployed"),
        "network": "testnet",
    })


@app.get("/api/findings")
async def findings(limit: int = 20):
    """Get latest findings from JSONL store."""
    if not FINDINGS_PATH.exists():
        return JSONResponse(content={"findings": [], "total": 0})

    with open(FINDINGS_PATH) as f:
        lines = [l.strip() for l in f if l.strip()]

    parsed = []
    for line in lines[-limit:]:
        try:
            parsed.append(json.loads(line))
        except Exception:
            pass

    return JSONResponse(content={"findings": list(reversed(parsed)), "total": len(lines)})


@app.get("/api/verify/{finding_hash}")
async def verify(finding_hash: str):
    """Verify a finding hash against on-chain contract."""
    pipeline = get_pipeline()
    result = await pipeline.audit.verify_finding(finding_hash)
    return JSONResponse(content=result)


@app.get("/api/stats")
async def stats():
    """Pipeline stats."""
    pipeline = get_pipeline()
    return JSONResponse(content=pipeline.get_stats())


@app.post("/api/run-cycle")
async def run_cycle(background_tasks: BackgroundTasks):
    """Trigger a pipeline cycle manually."""
    pipeline = get_pipeline()
    background_tasks.add_task(pipeline.run_cycle)
    return {"message": "Cycle started"}


@app.on_event("startup")
async def startup():
    """Start pipeline loop on server start."""
    global _pipeline_task
    pipeline = get_pipeline()

    async def run():
        try:
            await pipeline.run_continuous()
        except Exception as e:
            print(f"Pipeline error: {e}")

    _pipeline_task = asyncio.create_task(run())


# ── Static files (built dashboard) ───────────────────────────────────────────

STATIC_DIR = Path("dashboard/dist")
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/")
    async def index():
        return FileResponse(str(STATIC_DIR / "index.html"))

    @app.get("/{path:path}")
    async def spa(path: str):
        f = STATIC_DIR / path
        if f.exists() and f.is_file():
            return FileResponse(str(f))
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Mantle Intel Agent API. Dashboard not built yet — run: cd dashboard && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
