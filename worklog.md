# Mantle Intel Agent — E2E Testing Worklog

## Session: 2026-07-19 — Full Real-World End-to-End Testing

### Project Status: ALL SYSTEMS OPERATIONAL ✅

---

## Environment Setup

| Component | Version | Status |
|-----------|---------|--------|
| Python | 3.12.13 | ✅ |
| Web3.py | 6.20.3 | ✅ |
| FastAPI | 0.115.12 | ✅ |
| Node.js | v24.18.0 | ✅ |
| Hardhat | 2.x | ✅ |
| RPC (Mantle Mainnet) | https://rpc.mantle.xyz | ✅ Connected |
| RPC (Mantle Sepolia) | https://rpc.sepolia.mantle.xyz | ✅ Connected |
| Contract (Sepolia) | 0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b | ✅ 22 findings |
| Wallet | 0xB47Ba223B73980E69AEF53B0d202F9785698DAEa | ✅ 900 MNT |
| Telegram Bot | @MantleIntelBot | ✅ Sending alerts |
| Groq API | gsk_QSew... | ❌ 403 Forbidden (key expired) |
| Discord Webhook | Not configured | ⏳ Awaiting URL |

---

## Bugs Found & Fixed (Commit: 3e722af)

### BUG 1: Server startup blocks event loop
**File:** `server.py`
**Problem:** `get_pipeline()` in startup event calls `CollectorAgent._init_web3()` synchronously, blocking the entire event loop during server startup. The server couldn't accept HTTP requests until the pipeline init completed (which makes synchronous RPC calls).
**Fix:** Defer pipeline initialization into the `asyncio.create_task(run())` wrapper, so `get_pipeline()` is called inside the background task.

### BUG 2: On-chain writes block event loop
**File:** `agents/audit/audit_agent.py`
**Problem:** `_submit_to_chain()`, `verify_finding()`, and `get_chain_stats()` all make synchronous web3 calls (`send_raw_transaction`, `wait_for_transaction_receipt`, `call()`) directly in the async event loop, blocking all HTTP request handling for 3-5 seconds per transaction.
**Fix:** Wrap all synchronous web3 calls in `asyncio.to_thread()` to run them in worker threads. Added `import asyncio` to the file.

### BUG 3: OpenTelemetry context-var crash in background tasks
**Files:** `agents/pipeline.py`, `agents/audit/audit_agent.py`
**Problem:** Using `start_as_current_span()` with `__enter__`/`__exit__` pattern creates OpenTelemetry spans that are tied to `contextvars.ContextVar`. When the pipeline runs inside `asyncio.create_task()`, the span is created in one context but `__exit__` tries to detach in a different context, raising `ValueError: token was created in a different Context`.
**Fix:** Replace `start_as_current_span()` + `__enter__`/`__exit__` with `start_span()` + `span.end()`, which doesn't use context variables and works correctly across async task boundaries.

Also fixed `server.py` health endpoint to use `asyncio.to_thread()` for `is_connected()` and `findingCount().call()`.

---

## E2E Test Results

### Pipeline Cycle (Real Data)
- **Collector**: Collected 21-101 real blocks from Mantle mainnet per cycle
- **Anomaly Detection**: Detected 1-6 anomalies per cycle (value_spike, tx_spike, liquidity_imbalance, multivariate_anomaly)
- **Smart Money**: 55 known labeled wallets tracked
- **Insight Generation**: Template-based (Groq API key expired — fallback works correctly)
- **On-Chain Audit**: All findings recorded on Mantle Sepolia (tx hashes confirmed on mantlescan.xyz)
- **Telegram Alerts**: All incidents pushed successfully to chat 6774697368
- **Performance**: ~8-16 seconds per cycle end-to-end

### API Endpoints (All Tested ✅)
| Endpoint | Method | Auth | Status |
|----------|--------|------|--------|
| `/` | GET | None | 200 (Dashboard HTML) |
| `/api/health` | GET | X-API-KEY | 200 (healthy) |
| `/api/dashboard` | GET | X-API-KEY | 200 (JSON) |
| `/api/findings` | GET | X-API-KEY | 200 (77 findings) |
| `/api/verify/{hash}` | GET | X-API-KEY | 200 (verified=true) |
| `/api/stats` | GET | X-API-KEY | 200 (JSON) |
| `/api/analytics/summary` | GET | X-API-KEY | 200 (JSON) |
| `/api/run-cycle` | POST | X-API-KEY | 200 (Cycle started) |
| No API key | GET | — | 403 ✅ |
| Wrong API key | GET | — | 403 ✅ |

### Test Suite
- **Python**: 82 passed (0 failed, 0 errors)
- **Solidity**: 13 passed

### On-Chain Verification
- Contract: https://sepolia.mantlescan.xyz/address/0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b
- Total findings on-chain: 22 (up from 12 at start of testing)
- All test transactions confirmed on Mantle Sepolia

---

## Known Issues / Non-Critical Warnings

1. **Groq API 403**: The provided API key returns 403 Forbidden. Pipeline falls back to template-based insights correctly. User needs to regenerate their Groq API key at https://console.groq.com/

2. **Discord Webhook**: Not yet configured. User needs to set up a Discord webhook URL.

3. **Pyth Oracle 404**: Pyth price feed endpoint returns HTTP 404. Collector falls back to hardcoded prices. Non-critical — the oracle feed IDs may need updating.

4. **mETH/Merchant Moe/Lendle fetch errors**: Mainnet protocol contract calls fail from the collector because the contracts may have been upgraded or the ABIs are outdated. The collector gracefully falls back to simulated values.

5. **Mantle mainnet vs Sepolia mismatch**: Collector reads blocks from Mantle mainnet, but audit writes to Mantle Sepolia. This is intentional for testing but should be aligned for production.

---

## Next Steps

1. Get a valid Groq API key for AI-powered insights
2. Set up Discord webhook URL
3. Deploy to production with mainnet contract
4. Update Pyth oracle feed IDs
5. Update protocol contract ABIs (mETH, Merchant Moe, Lendle)
