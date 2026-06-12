# 92/100 Target — Upgrade Plan

## Score Gap Analysis
Current: 82/100
Target:  92/100
Gap:     +10pts needed

## Where the 10pts come from:

### Part A Gaps (currently 40/50 → target 46/50 = +6pts)
- A1 Technical Innovation: 7→9 (+2) — add pnpm demo-style zero-key quickstart, add anti-gaming section to docs
- A2 Code Quality: 8→9 (+1) — add coverage badge to README, add integrity CI step for hash audit
- A5 Narrative/Pitch: 8→9 (+1) — rewrite DoraHacks hook with "loss story" opener
- A3 Demo: 8→9 (+1) — add interactive arena-like element to dashboard (signal simulator)
- A4 Docs: 9→10 (+1) — add ONCHAIN.md with every TX, every contract, every cast command

### Part B Gaps (currently 42/50 → target 46/50 = +4pts)  
- B1 Insight Value: 12→14 (+2) — add real-time reasoning feed showing WHAT the agent is thinking per block
- B2 Data Sources: 13→14 (+1) — add Limitless/prediction market signal or social signal to data mix
- B3 Investment Utility: 10→11 (+1) — add P&L impact calculator tab to dashboard

## Execution Tasks (in order):
1. [ ] Rewrite DoraHacks submission hook (narrative-first, "loss story")
2. [ ] Create docs/ONCHAIN.md — every tx, cast verify commands
3. [ ] Add "Agent Reasoning Feed" tab to dashboard — live per-block thought stream
4. [ ] Add "Signal Simulator" / ROI Calculator to dashboard
5. [ ] Add Limitless/social signal source to CollectorAgent (mock-with-fallback ok)
6. [ ] Add coverage badge + ONCHAIN badge to README
7. [ ] Rebuild dashboard dist
8. [ ] Commit + push + deploy Vercel
