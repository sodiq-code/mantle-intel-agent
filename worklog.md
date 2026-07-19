# Mantle Intel Agent — P2 + P3 Implementation Worklog

## Project Current State
- Mantle Intel Agent: Python-based blockchain audit pipeline with Solidity contracts
- All 12 P2 items verified, tested, and pushed to main repo (commit bbe7206)
- All 9 P3 items verified, tested, and pushed to main repo (commit 54d75f9)
- 78 Python tests pass, 13 Solidity tests pass
- Pushed to https://github.com/sodiq-code/mantle-intel-agent (main branch)
- All Python files pass syntax check
- 78 Python tests pass (4 skipped — require RPC config)
- 13 Solidity tests pass (10 required + 3 bonus)
- Pushed to https://github.com/sodiq-code/mantle-intel-agent (commit bbe7206)

## Verification Results (2026-07-19)
All P2 items passed comprehensive verification:
- P2-16: ✅ OpenTelemetry tracing with spans in pipeline + audit agent
- P2-17: ✅ Real health check (RPC, contract, pipeline status)
- P2-18: ✅ asyncio.to_thread() for sync web3.py calls
- P2-19: ✅ slowapi rate limiting (30/min GET, 5/min POST)
- P2-20: ✅ Dockerfile + .dockerignore
- P2-21: ✅ All 25 deps pinned with == in requirements.txt
- P2-22: ✅ 13 Solidity test cases passing
- P2-23: ✅ Confidence threshold >= 75 in Solidity contract
- P2-24: ✅ Path-traversal protection + no bare excepts
- P2-25: ✅ LLM prompt sanitisation (injection patterns, hex stripping, truncation)
- P2-26: ✅ Circuit breaker (5 failures → 5x backoff, resets on success)
- P2-27: ✅ Daily file rotation with gzip + 30-day cleanup

## P3 Verification Results (2026-07-19)
All P3 items passed comprehensive verification:
- P3-28: ✅ The Graph subgraph + Ponder indexer for findings + subscriptions
- P3-29: ✅ JUDGES.md with 5-minute verification walkthrough (fixes broken link in RISK.md)
- P3-30: ✅ Anonymous usage analytics (SHA256 IP hashing, DAU/MAU, privacy-first)
- P3-31: ✅ LOI templates for Lendle, Merchant Moe, Agni Finance
- P3-32: ✅ Multi-sig documentation (Gnosis Safe 2-of-3, Gelato Relay)
- P3-33: ✅ Subscription event indexing (folded into P3-28 subgraph + Ponder)
- P3-34: ✅ pyproject.toml with PEP 621, optional deps, ruff, pytest config
- P3-35: ✅ SLSA Level 2 target in SECURITY.md with implementation plan
- P3-36: ✅ MODEL_CARD.md with full LLM disclosure, training data, limitations

## Completed P2 Modifications

### Tier 1: Security & Correctness ✅

**P2-24: Path-traversal protection**
- File: `server.py` (lines 249-274)
- Replaced bare `except Exception: pass` with explicit `(ValueError, OSError)` catch
- Added structlog logging for path resolution errors
- Added explicit 403 response for paths that resolve outside STATIC_DIR
- SPA fallback only triggers for safe, non-traversal paths

**P2-25: LLM prompt sanitisation**
- File: `agents/insight/insight_agent.py` (lines 187-317)
- Added `_INJECTION_PATTERNS` class variable with 12 common injection patterns
- Added `_sanitise_for_prompt()` static method: truncates to max_len, strips injection patterns
- Added `_sanitise_metrics()` static method: strips input_data/input/inputData fields, truncates strings, limits lists to 5 items
- Added `_sanitise_transfers()` static method: strips hex input fields from transfers, limits to 3 transfers
- Updated `_build_prompt()` to sanitise all user-influenced data before embedding in prompt

**P2-26: Circuit breaker**
- File: `agents/pipeline.py` (lines 61-62, 185-190, 221-266)
- Added `_consecutive_failures` counter and `_circuit_open` flag
- On exception: increment counter, log with structlog
- At 5 consecutive failures: set circuit_open, log CRITICAL, notify incident channels, back off for 5x poll_interval
- On successful cycle: reset counter and flag, log if previously failed
- `get_stats()` now includes `circuit_open` and `consecutive_failures`

**P2-23: Confidence threshold reconciliation**
- File: `contracts/src/MantleIntelAudit.sol` (line 129)
- Changed `require(confidenceScore >= 50)` → `require(confidenceScore >= 75)`
- Added detailed comment explaining why threshold matches pipeline's 0.75 filter
- Updated struct comment to reference P2-23
- Verified with test: confidence=74 now reverts, confidence=75 succeeds

### Tier 2: Operational Reliability ✅

**P2-17: Real /api/health check**
- File: `server.py` (lines 112-155)
- Replaced stub `{"status": "ok"}` with real checks
- Checks RPC connectivity via `web3.is_connected()`
- Checks contract reachability via `findingCount().call()`
- Reports pipeline running status and last successful cycle timestamp
- Returns structured: `{status: healthy|degraded|unhealthy, rpc, contract, pipeline_running, last_cycle}`
- Added `last_cycle_success` to pipeline stats

**P2-27: File rotation for findings.jsonl**
- Files: `agents/pipeline.py` (lines 276-358), `agents/audit/audit_agent.py` (lines 342-396)
- Added `_rotate_if_needed()` static method to pipeline
- Added `_rotate_audit_log()` static method to audit agent
- If file's mtime is from a previous day: gzip with date suffix, truncate original
- Cleans up gzipped files older than 30 days
- Rotation applied before each append to findings.jsonl and audit_log.jsonl

**P2-16: OpenTelemetry tracing**
- New file: `agents/tracing.py`
- Created tracer provider with OTLP exporter (configurable via OTEL_EXPORTER_OTLP_ENDPOINT)
- Falls back to ConsoleSpanExporter when no endpoint configured
- Added spans to `pipeline.run_cycle()` with attributes: cycle_number, new_findings, elapsed_s
- Added spans to `audit.record_finding()` with attributes: finding_id, anomaly_type, confidence, block_height, audit_status, tx_hash
- Graceful import — if OTel not installed, spans are no-ops

### Tier 3: Infrastructure ✅

**P2-18: Async collect_blocks**
- File: `agents/collector/collector_agent.py` (lines 229-269)
- Extracted sync logic to `_collect_blocks_sync()` method
- `collect_blocks()` now delegates via `asyncio.to_thread()` to prevent blocking event loop
- Pipeline call unchanged (collect_blocks still async, but internally non-blocking)

**P2-19: Rate limiting**
- File: `server.py` (lines 24-52, 158-217)
- Added slowapi integration with graceful fallback (NoOpLimiter when not installed)
- Applied `@limiter.limit("30/minute")` to GET endpoints (dashboard, findings, verify, stats)
- Applied `@limiter.limit("5/minute")` to POST endpoint (run-cycle) — stricter for mutations
- Health endpoint exempt from rate limiting
- Added slowapi to requirements.in and requirements.txt

**P2-20: Dockerfile**
- New files: `Dockerfile`, `.dockerignore`
- Multi-stage build from python:3.12-slim
- Includes OTel and slowapi pip installs
- HEALTHCHECK using /api/health endpoint
- .dockerignore excludes node_modules, __pycache__, .git, data/, .env, etc.

**P2-21: Pin dependencies**
- New file: `requirements.in` (source of truth for pip-compile)
- Updated `requirements.txt` with pinned versions including new P2-16 and P2-19 deps

### Tier 4: Testing ✅

**P2-22: Solidity test suite**
- New file: `contracts/test/MantleIntelAudit.js`
- 13 tests covering all contract functionality:
  1. ✅ recordFinding() succeeds with confidence=75
  2. ✅ recordFinding() reverts with confidence < 75 (P2-23)
  3. ✅ recordFinding() reverts on duplicate hash
  4. ✅ recordFinding() reverts on empty anomaly type
  5. ✅ verifyFinding() returns correct data after recording
  6. ✅ verifyFinding() returns false for unknown hash
  7. ✅ getPublicFindings() pagination works
  8. ✅ getFindingsByType() filtering works
  9. ✅ subscribe() / isSubscribed() works
  10. ✅ Unauthorized address cannot call recordFinding()
  11. ✅ Owner can authorize and revoke agents
  12. ✅ getStats() returns correct data
  13. ✅ Non-owner cannot authorize agents

## Verification Results
- All Python files pass `py_compile` syntax check
- Solidity contract compiles: 22 files, 0 errors
- All 13 Solidity tests pass (767ms execution time)
- No regressions in existing code structure

## Unresolved Issues / Risks
- OpenTelemetry packages are optional — if not installed, tracing is silently disabled
- slowapi is optional — if not installed, rate limiting is silently disabled
- The health check creates a pipeline instance on first call (get_pipeline() lazy init)
- Circuit breaker uses fixed 5x backoff — could be improved to exponential backoff in future
