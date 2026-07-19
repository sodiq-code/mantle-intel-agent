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

# P2-19: Rate limiting
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    _SLOWAPI_AVAILABLE = True
except ImportError:
    _SLOWAPI_AVAILABLE = False

import structlog
structlog.configure(processors=[structlog.dev.ConsoleRenderer(colors=True)])

from agents.pipeline import MantleIntelPipeline

app = FastAPI(title="Mantle Intel Agent API", version="1.0.0")

# P2-19: Rate limiting setup
if _SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address, enabled=True)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
else:
    # No-op limiter for when slowapi is not installed
    class _NoOpLimiter:
        def limit(self, *args, **kwargs):
            return lambda f: f
    limiter = _NoOpLimiter()

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
# P2-19: Health endpoint is exempt from rate limiting
async def health():
    """P2-17: Real health check — verifies RPC, contract, and pipeline status."""
    checks = {
        "service": "mantle-intel-agent",
        "rpc": False,
        "contract": False,
        "pipeline_running": False,
        "last_cycle": None,
    }

    pipeline = get_pipeline()
    checks["pipeline_running"] = pipeline._running
    checks["last_cycle"] = pipeline._stats.get("last_cycle_success")

    # 1. RPC connectivity check
    try:
        if pipeline.audit._w3 and pipeline.audit._w3.is_connected():
            checks["rpc"] = True
    except Exception as exc:
        structlog.get_logger("health").warning("rpc_check_failed", error=str(exc))

    # 2. Contract reachability check
    try:
        if pipeline.audit._contract:
            pipeline.audit._contract.functions.findingCount().call()
            checks["contract"] = True
    except Exception as exc:
        structlog.get_logger("health").warning("contract_check_failed", error=str(exc))

    # Determine overall status
    if checks["rpc"] and checks["contract"]:
        status = "healthy"
    elif checks["rpc"] or checks["contract"]:
        status = "degraded"
    else:
        status = "unhealthy"

    return {
        "status": status,
        **checks,
    }


@app.get("/api/dashboard")
@limiter.limit("30/minute")
async def dashboard(request: Request):
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
@limiter.limit("30/minute")
async def findings(request: Request, limit: int = 20):
    """Get latest findings from JSONL store."""
    if not FINDINGS_PATH.exists():
        return JSONResponse(content={"findings": [], "total": 0})

    with open(FINDINGS_PATH) as f:
        lines = [l.strip() for l in f if l.strip()]

    parsed = []
    for line in lines[-limit:]:
        try:
            parsed.append(json.loads(line))
        except (json.JSONDecodeError, ValueError) as exc:
            structlog.get_logger("server").warning(
                "findings_jsonl_parse_error", error=str(exc))

    return JSONResponse(content={"findings": list(reversed(parsed)), "total": len(lines)})


@app.get("/api/verify/{finding_hash}")
@limiter.limit("30/minute")
async def verify(request: Request, finding_hash: str):
    """Verify a finding hash against on-chain contract."""
    pipeline = get_pipeline()
    result = await pipeline.audit.verify_finding(finding_hash)
    return JSONResponse(content=result)


@app.get("/api/stats")
@limiter.limit("30/minute")
async def stats(request: Request):
    """Pipeline stats."""
    pipeline = get_pipeline()
    return JSONResponse(content=pipeline.get_stats())


@app.post("/api/run-cycle")
@limiter.limit("5/minute")  # P2-19: Stricter for mutation endpoint
async def run_cycle(request: Request, background_tasks: BackgroundTasks):
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
        # P2-24: Path-traversal protection — explicit catch, no bare except
        try:
            f = (STATIC_DIR / path).resolve()
        except (ValueError, OSError) as exc:
            # Log malformed or OS-level path errors (e.g. null bytes, too long)
            structlog.get_logger("server").warning(
                "path_resolve_error", path=path, error=str(exc))
            return FileResponse(str(STATIC_DIR / "index.html"))

        static_dir_resolved = STATIC_DIR.resolve()

        # Reject any path that escapes STATIC_DIR (path-traversal defence)
        if not f.is_relative_to(static_dir_resolved):
            structlog.get_logger("server").warning(
                "path_traversal_blocked", path=path, resolved=str(f))
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden: path outside static directory"})

        if f.exists() and f.is_file():
            return FileResponse(str(f))

        # SPA fallback — only for safe, non-traversal paths
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Mantle Intel Agent API. Dashboard not built yet — run: cd dashboard && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
