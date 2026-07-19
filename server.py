"""
Mantle Intel Agent — FastAPI Server
Serves dashboard data and exposes API for the React frontend.
Run: uvicorn server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
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
    # P3-30: Record anonymous analytics for API requests
    if request.url.path.startswith("/api/"):
        _analytics.record_request(
            endpoint=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

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
ANALYTICS_PATH = DATA_DIR / "analytics.jsonl"

DATA_DIR.mkdir(exist_ok=True)


# ── P3-30: Anonymous Usage Analytics ───────────────────────────────────────────
# Privacy-first: NO cookies, NO fingerprinting, NO wallet addresses, NO PII.
# Only tracks: endpoint hit counts, daily unique session hashes (SHA256 of IP),
# pipeline cycle counts, and finding type distributions.

class _Analytics:
    """In-memory analytics with daily JSONL persistence.

    All data is aggregated and anonymous. Individual requests are never
    stored — only daily rollup counts.
    """

    def __init__(self):
        self._day = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        self._endpoint_counts: dict[str, int] = defaultdict(int)
        self._daily_sessions: set[str] = set()    # SHA256 hashes of IPs
        self._finding_types: dict[str, int] = defaultdict(int)
        self._pipeline_cycles = 0
        self._total_api_calls = 0
        self._total_findings_served = 0
        self._start_time = time.time()

    def record_request(self, endpoint: str, client_ip: str | None = None) -> None:
        """Record an API request. client_ip is hashed immediately, never stored."""
        self._maybe_rotate()
        self._endpoint_counts[endpoint] += 1
        self._total_api_calls += 1
        if client_ip:
            # Hash the IP so we can count unique sessions without storing PII
            session_hash = hashlib.sha256(
                (client_ip + self._day).encode()
            ).hexdigest()[:16]
            self._daily_sessions.add(session_hash)

    def record_finding_served(self, count: int = 1) -> None:
        self._total_findings_served += count

    def record_finding_type(self, anomaly_type: str) -> None:
        self._finding_types[anomaly_type] += 1

    def record_pipeline_cycle(self) -> None:
        self._pipeline_cycles += 1

    def _maybe_rotate(self) -> None:
        """Rotate daily analytics to JSONL if the day has changed."""
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        if today != self._day:
            self._flush_to_disk()
            self._day = today
            self._endpoint_counts.clear()
            self._daily_sessions.clear()
            self._finding_types.clear()
            self._pipeline_cycles = 0
            self._total_api_calls = 0
            self._total_findings_served = 0

    def _flush_to_disk(self) -> None:
        """Append daily rollup to analytics JSONL."""
        rollup = {
            "date": self._day,
            "unique_sessions": len(self._daily_sessions),
            "total_api_calls": self._total_api_calls,
            "endpoint_counts": dict(self._endpoint_counts),
            "finding_types_served": dict(self._finding_types),
            "findings_served": self._total_findings_served,
            "pipeline_cycles": self._pipeline_cycles,
        }
        try:
            with open(ANALYTICS_PATH, "a") as f:
                f.write(json.dumps(rollup, default=str) + "\n")
        except (OSError, ValueError) as exc:
            structlog.get_logger("analytics").warning(
                "analytics_flush_failed", error=str(exc))

    def get_summary(self, days: int = 30) -> dict:
        """Get aggregated analytics for the last N days.

        Returns only aggregated, non-identifiable counts.
        No IP hashes, no individual request records.
        """
        # Load historical data from JSONL
        historical = {"total_api_calls": 0, "unique_sessions": 0,
                      "findings_served": 0, "pipeline_cycles": 0,
                      "finding_types": defaultdict(int),
                      "endpoint_counts": defaultdict(int),
                      "days_active": 0}

        if ANALYTICS_PATH.exists():
            try:
                with open(ANALYTICS_PATH) as f:
                    lines = [l.strip() for l in f if l.strip()]
                # Only last N days
                for line in lines[-days:]:
                    try:
                        day_data = json.loads(line)
                        historical["total_api_calls"] += day_data.get("total_api_calls", 0)
                        historical["unique_sessions"] += day_data.get("unique_sessions", 0)
                        historical["findings_served"] += day_data.get("findings_served", 0)
                        historical["pipeline_cycles"] += day_data.get("pipeline_cycles", 0)
                        historical["days_active"] += 1
                        for k, v in day_data.get("finding_types_served", {}).items():
                            historical["finding_types"][k] += v
                        for k, v in day_data.get("endpoint_counts", {}).items():
                            historical["endpoint_counts"][k] += v
                    except (json.JSONDecodeError, ValueError):
                        pass
            except (OSError, ValueError):
                pass

        # Add current (in-memory) day
        current_day = {
            "total_api_calls": self._total_api_calls,
            "unique_sessions": len(self._daily_sessions),
            "findings_served": self._total_findings_served,
            "pipeline_cycles": self._pipeline_cycles,
        }

        total_api = historical["total_api_calls"] + current_day["total_api_calls"]
        total_sessions = historical["unique_sessions"] + current_day["unique_sessions"]
        total_findings = historical["findings_served"] + current_day["findings_served"]
        total_cycles = historical["pipeline_cycles"] + current_day["pipeline_cycles"]

        # Merge finding types
        all_finding_types = dict(historical["finding_types"])
        for k, v in self._finding_types.items():
            all_finding_types[k] = all_finding_types.get(k, 0) + v

        all_endpoint_counts = dict(historical["endpoint_counts"])
        for k, v in self._endpoint_counts.items():
            all_endpoint_counts[k] = all_endpoint_counts.get(k, 0) + v

        uptime_seconds = time.time() - self._start_time
        days_active = historical["days_active"] + 1  # +1 for today

        return {
            "period_days": days,
            "days_active": days_active,
            "uptime_seconds": round(uptime_seconds, 1),
            "total_api_calls": total_api,
            "total_unique_sessions": total_sessions,
            "avg_daily_sessions": round(total_sessions / max(days_active, 1), 1),
            "total_findings_served": total_findings,
            "total_pipeline_cycles": total_cycles,
            "finding_type_distribution": all_finding_types,
            "endpoint_distribution": all_endpoint_counts,
            "current_day": current_day,
            "privacy_notice": (
                "Anonymous only. No cookies, no fingerprinting, "
                "no wallet addresses, no PII. IPs are SHA256-hashed "
                "and discarded after daily rollup."
            ),
        }


_analytics = _Analytics()


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

    # P3-30: Track finding types served (anonymous analytics)
    for f in parsed:
        _analytics.record_finding_type(f.get("type", "unknown"))
    _analytics.record_finding_served(len(parsed))

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


# P3-30: Anonymous usage analytics endpoint
@app.get("/api/analytics/summary")
@limiter.limit("30/minute")
async def analytics_summary(request: Request, days: int = 30):
    """P3-30: Anonymous usage analytics — aggregated, non-identifiable stats.

    Privacy notice: No cookies, no fingerprinting, no wallet addresses,
    no PII. Client IPs are SHA256-hashed immediately and discarded after
    daily rollup. Only aggregated counts are stored and served.

    Returns DAU/MAU proxies (unique session hashes per day/month).
    """
    if days < 1:
        days = 1
    if days > 365:
        days = 365
    return JSONResponse(content=_analytics.get_summary(days=days))


@app.post("/api/run-cycle")
@limiter.limit("5/minute")  # P2-19: Stricter for mutation endpoint
async def run_cycle(request: Request, background_tasks: BackgroundTasks):
    """Trigger a pipeline cycle manually."""
    pipeline = get_pipeline()
    _analytics.record_pipeline_cycle()  # P3-30: Track cycle triggers
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


def main():
    """Entry point for `mantle-intel` CLI script (pyproject.toml [project.scripts])."""
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
