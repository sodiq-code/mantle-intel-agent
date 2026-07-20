# Mantle Intel Agent — Fix Worklog

## Session: 2026-07-20

---
Task ID: 1
Agent: Main
Task: Fix all 7 STILL BROKEN issues (P1 #7, P1 #8, P1 #20, P2 #25, P2 #23, P1 #16, P1 #19)

Work Log:
- Analyzed all 7 issues by reading relevant source files
- P1 #7: Changed Python AnomalyFinding.sha256_hash() to use canonical 4-field JSON (block, confidence, tx_count, type) with sort_keys=True
- P1 #7: Changed JS api/shared.js to use canonicalFindingHash() with alphabetically-sorted keys matching Python
- P1 #7: Updated dashboard/api/live-feed.js to import canonicalFindingHash and BACKTEST_RESULTS
- P1 #8: Created api/backtest_data.js as single source of truth for backtest metrics (replaces hardcoded values)
- P1 #8: Updated both api/shared.js and dashboard/api/live-feed.js to import from backtest_data.js
- P1 #20: Verified submit_findings_testnet.py already uses matching canonical JSON format; updated docstring
- P2 #25: Updated Solidity contract MantleIntelAudit.sol threshold from >=75 to >=80 matching Python's 0.80
- P2 #25: Updated docs/MODEL_CARD.md to reference >=80 threshold
- P2 #23: Removed os.makedirs("data") module-level side effect from agents/pipeline.py
- P2 #23: Created _ensure_data_dir() lazy function, called in _append_finding() and _update_dashboard()
- P1 #16: Expanded requirements.txt from 26 to 67 pinned dependencies including all transitive deps
- P1 #19: Qualified all "100% precision" claims across 8 files with † dagger footnotes or * asterisk
- P1 #19: Added Wilson 95% CI inline to all precision tables in docs
- P1 #19: Added wilson_ci and _note to backtest/results_live.json
- Updated test files to match new canonical 4-field hash format
- Ran comprehensive verification: 83/83 tests pass, cross-language hash consistency confirmed

Stage Summary:
- All 7 fixes implemented and verified
- Cross-language hash: Python, JS, and submit_findings_testnet.py produce IDENTICAL hashes
- Threshold alignment: Python 0.80 == Solidity >=80 == docs say >=80
- No import-time side effects from pipeline.py
- requirements.txt has 67 fully pinned dependencies
- All "100% precision" claims qualified with Wilson CI context
