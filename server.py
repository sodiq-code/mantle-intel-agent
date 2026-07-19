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

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

import structlog
structlog.configure(processors=[structlog.dev.ConsoleRenderer(colors=True)])

from agents.pipeline import MantleIntelPipeline

app = FastAPI(title="Mantle Intel Agent API", version="1.0.0")

# Strict CORS for institutional standard
frontend_url = os.getenv("FRONTEND_URL")
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", frontend_url if frontend_url else "http://localhost:5173,http://localhost:8000")
origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-KEY", "Content-Type", "Authorization"],
)

# Institutional Standard API Key Middleware
API_KEY = os.getenv("API_KEY")

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Allow static assets and root (React app) without API key
    if request.url.path.startswith("/api/"):
        if not API_KEY:
            env = os.getenv("ENV", "development")
            if env == "production":
                return JSONResponse(
                    status_code=503,
                    content={"error": "Service unavailable: API_KEY not configured in production"}
                )
            # In development mode, allow without key (with warning)
            import structlog as _sl
            _sl.get_logger().warning("api_key_not_set", msg="API_KEY not set — running in open mode (development only)")
        else:
            provided_key = request.headers.get("X-API-KEY")
            if provided_key != API_KEY:
                return JSONResponse(
                    status_code=403, 
                    content={"error": "Forbidden: Invalid or missing X-API-KEY"}
                )
    return await call_next(request)

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
        try:
            f = (STATIC_DIR / path).resolve()
            static_dir_resolved = STATIC_DIR.resolve()
            if f.is_relative_to(static_dir_resolved) and f.exists() and f.is_file():
                return FileResponse(str(f))
        except Exception:
            pass
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Mantle Intel Agent API. Dashboard not built yet — run: cd dashboard && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
