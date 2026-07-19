# Mantle Intel Agent — Investment Thesis
## For Mirana Ventures & Alpha/Data Track Judges

> **TL;DR:** On-chain alpha delivery for Mantle Network — the first autonomous, real-time intelligence layer purpose-built for Mantle's DeFi ecosystem. Backtest: F1=0.963, Precision=100%, Recall=92.9%. Live API, 5 on-chain audit logs, ERC-8004 NFT identity, Telegram/Discord alerts. Built to win the Alpha & Data Track.

---

## 1. Problem: The Information Gap Is Costing Mantle DeFi Participants Money

Mantle's DeFi ecosystem — $500M+ TVL across Merchant Moe, Lendle, Agni Finance, mETH, and 15+ protocols — generates thousands of on-chain signals per hour. Today:

- **Professional traders** cannot distinguish informed whale flows from noise without expensive Nansen subscriptions ($1,200/mo) that barely cover Mantle-native data
- **Retail DeFi users** have zero visibility into smart money positioning before it impacts their LP positions
- **Protocol teams** have no real-time anomaly alerts for their own TVL — they discover exploits and liquidation cascades after the fact
- **Mirana itself** — as a Mantle-aligned fund — currently has no purpose-built tool for monitoring Mantle-specific on-chain signals

**The gap:** Nansen is generic. Dune is manual. On-chain analytics designed for Ethereum don't model Mantle's unique architecture (mETH LSD, Merchant Moe AMM, Lendle's collateral structure).

---

## 2. Solution: Mantle-Native Autonomous Intelligence

Mantle Intel Agent is a **5-agent AI pipeline** that continuously:

1. **Collects** — Polls Mantle RPC + Pyth oracle + mETH contract + Merchant Moe reserves every 6 seconds
2. **Detects** — Runs Isolation Forest (contamination=0.03) + Z-Score (3.0σ) + 8 pattern detectors on multi-dimensional block data
3. **Classifies** — 60+ Nansen-style wallet labels (CEX, VC, DeFi protocols, MEV bots) — no API key needed
4. **Narrates** — Investment-grade signal reports with signal tier (WATCH / ALERT / IMMEDIATE ACTION) and lead-time estimates
5. **Audits** — Every finding SHA256-hashed and permanently written to `MantleIntelAudit.sol` (immutable, on-chain)

**What makes it Mantle-specific:**
- mETH depeg detection: fires when mETH/ETH deviates >50bps from expected staking rate (Pyth + contract dual-source)
- Merchant Moe reserve imbalance: LP ratio shift >30% triggers liquidity alert
- Lendle TVL tracking: monitors total supply as borrowing demand proxy
- Cross-protocol correlation: detects simultaneous multi-protocol activity (highest-conviction signal)

---

## 3. Market Opportunity

### Total Addressable Market (TAM)
- On-chain analytics market: **$2.1B (2025) → $8.4B (2030)** — 32% CAGR (Verified Market Research)
- Mantle TVL: **$500M+** — generating $5-50M in daily on-chain volume to analyze
- Mantle ecosystem users: **~85,000 active wallets** (Q2 2026 on-chain data)

### Serviceable Addressable Market (SAM)
- Mantle-focused traders, funds, and protocols: ~500 potential professional subscribers
- At $99-999/mo → **$600k–$6M ARR from Mantle alone** at 10% penetration

### Serviceable Obtainable Market (SOM — 12-month target)
- 150 paying subscribers by Q1 2027 → **~$55,000 MRR ($660K ARR)**
- 3 protocol partnerships (data sharing deals) → **$10,000-30,000/mo additional**

---

## 4. Product-Market Fit Evidence

### Current Signal Quality (Backtest, June 2026)
| Metric | Result |
|--------|--------|
| Precision | **100%** (0 false positives) |
| Recall | **92.9%** (13/14 true events caught) |
| F1 Score | **0.963** |
| Methodology | 395 live mainnet blocks, 14 ground truth events, no simulation |

Wilson 95% CI: Precision [0.782, 1.000], Recall [0.697, 0.985]

### Live System Validation
- **Live API:** `https://mantle-intel-agent.vercel.app/api/live-feed` — `demo_mode: false`, real Mantle mainnet blocks
- **On-chain log:** 5 findings hashed + submitted to `MantleIntelAudit.sol` (0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b, Mantle Sepolia)
- **Sourcify verified:** Contract source publicly verifiable
- **NFT identity:** ERC-8004 agent identity minted (0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C)

### Why Users Would Pay
- A fund managing $10M on Mantle: 1 avoided liquidation cascade = $50,000+ saved → $999/mo fee is **0.024% of protected capital**
- A yield farmer in Merchant Moe LP: 1 LP imbalance alert = avoiding $5,000 impermanent loss → $99/mo is ROI-positive in <1 trade
- A protocol team (Lendle, Agni): Real-time whale tracking = faster governance response to TVL risk

---

## 5. Competitive Analysis

| Dimension | **Mantle Intel** | Nansen | Dune | Chainalysis |
|-----------|-----------------|--------|------|-------------|
| Mantle-native data | ✅ Deep | ❌ Generic | ❌ Manual | ❌ None |
| mETH/LSD tracking | ✅ Native | ❌ | ❌ | ❌ |
| Real-time alerts (<2s) | ✅ | ❌ 5-30min | ❌ Manual | ✅ (compliance) |
| Investment signal tier | ✅ (WATCH/ALERT/ACTION) | ❌ Labels | ❌ Raw data | ❌ |
| On-chain audit trail | ✅ Immutable | ❌ | ❌ | ❌ |
| Price (professional) | **$99-999/mo** | $1,200+/mo | $400/mo | $50k+/yr |
| Autonomous pipeline | ✅ | ❌ | ❌ | ❌ |

**Moat:** Mantle-specific protocol integrations (mETH rate, Merchant Moe reserves, Lendle TVL) cannot be replicated by generic analytics without significant protocol-specific engineering.

---

## 6. Revenue Model

### Subscription Tiers (Post-Hackathon)
```
Free          →  5-min delay, 10 findings/response, public dashboard
Professional  →  $99/mo  — real-time WebSocket, 500 findings/day, 30-day history
Professional →  $999/mo — real-time + predictive, unlimited, custom protocols, SLA
Enterprise    →  Custom  — white-label, on-premise, dedicated support
```

### Additional Revenue Streams
1. **Protocol partnerships** — Lendle, Agni, Merchant Moe pay for their own TVL monitoring data (B2B)
2. **API licensing** — CEXs pay for Mantle smart money flow data (listing/trading decisions)
3. **Signal marketplace** — Analyst-submitted signals with on-chain verification (protocol fee)
4. **Partnership funding** — Mantle Foundation ecosystem grants for infrastructure projects

### Unit Economics (Professional Tier)
- CAC: ~$500 (conference, DM outreach, hackathon visibility)
- LTV: $999 × 18 months avg retention = **$17,982 LTV**
- LTV/CAC: **35.9x** — extremely capital-efficient SaaS model

---

## 7. Why Mantle? Why Now?

### Mantle-Specific Tailwinds
1. **mETH Protocol** — $400M+ TVL in liquid staking creates structural demand for LSD monitoring
2. **Mantle Ecosystem Fund** — $200M+ in ecosystem grants = more protocols to track
3. **DeFi Summer 2.0 on Mantle** — TVL 3x'd in 2025, creating more alpha opportunities
4. **ERC-8004 adoption** — Agent NFT standard creates composable identity for autonomous agents

### First-Mover Advantage
- No purpose-built analytics tool exists for Mantle ecosystem today
- Protocol teams actively seeking TVL monitoring solutions (validated via Discord)
- Mantle Foundation actively incentivizing developer tooling

---

## 8. Team & Execution

**Jimoh Tech (sodiq-code)** — Full-stack developer, blockchain engineer
- Built end-to-end in <30 days: 5 Python agents, Solidity contract, React dashboard, Telegram/Discord bots
- Demonstrated ability to ship production-quality on-chain infrastructure fast
- GitHub: [sodiq-code/mantle-intel-agent](https://github.com/sodiq-code/mantle-intel-agent)

**Execution proof:**
- Working live system (not a prototype) — demo_mode=false, real mainnet blocks
- Deployed contract with 5 on-chain findings submitted
- Vercel deployment with Edge functions for sub-50ms API responses
- Deterministic backtest with reproducible results (seed=42)

---

## 9. Ask

**For Mirana Ventures (Turing Test Hackathon):**
- **$100K prize** → Mainnet deployment, dedicated RPC node, subgraph indexer, first 10 beta users
- **Strategic partnership** → Mirana as first professional subscriber + signal validation partner
- **Portfolio integration** → Mantle Intel alerts integrated into Mirana's Mantle portfolio monitoring

**Post-hackathon investment:**
- Pre-seed: $300K for 12 months of runway
  - 1 full-time engineer ($120K)
  - Infrastructure ($24K/yr)
  - Business development ($50K)
  - Remainder: operations + legal
- Target: 150 paying subscribers by month 12, self-sustaining at month 18

---

## 10. Risk Factors & Mitigations

| Risk | Mitigation |
|------|-----------|
| RPC rate limits at scale | Dedicated node (Alchemy/QuickNode) — $200/mo at 10M req/day |
| ML model false positives at higher load | Confidence threshold tunable; multi-confirm logic reduces noise |
| Competitive response from Nansen | Mantle-specific moat; move faster on protocol integrations |
| Mantle ecosystem bear market | Revenue diversification across protocols and chains (Phase 2) |
| Smart contract exploit on audit contract | Audit contract is write-only; no funds held; minimal attack surface |

---

*Mantle Intel Agent | Turing Test Hackathon 2026 | Alpha & Data Track (Mirana Ventures)*  
*Live: https://mantle-intel-agent.vercel.app | GitHub: sodiq-code/mantle-intel-agent*  
*Contract: 0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b (Mantle Sepolia)*
