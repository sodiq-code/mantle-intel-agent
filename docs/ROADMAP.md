# Mantle Intel Agent — Post-Hackathon Scalability Roadmap

> From hackathon prototype → production-grade on-chain intelligence infrastructure for Mantle Network

---

## Phase 0 — Hackathon (Current, June 2026)

**Status: Complete ✅**

| Component | Status |
|-----------|--------|
| 5-agent Python pipeline (Collector → Anomaly → SmartMoney → Insight → Audit) | ✅ Live |
| Isolation Forest + Z-Score + Pattern Match anomaly detection | ✅ Live |
| 60+ Nansen-style wallet labels | ✅ Live |
| mETH depeg detection via oracle | ✅ Live |
| Merchant Moe + Lendle RPC polling | ✅ Live |
| Pyth oracle price integration | ✅ Live |
| MantleIntelAudit.sol on-chain audit log (ERC-8004) | ✅ Testnet |
| Telegram bot + Discord webhook | ✅ Live |
| React dashboard + public REST API | ✅ Live (Vercel) |
| Backtest: F1=1.00, Precision=100% | ✅ Verified |

---

## Phase 1 — Mainnet Launch (Q3 2026)

**Target: Production-grade, zero-downtime operation**

### Infrastructure
- [ ] **Mainnet contract deployment** — `MantleIntelAudit.sol` on Mantle mainnet (address TBD)
- [ ] **Subgraph indexer** — The Graph subgraph on Mantle for fast historical query (<50ms vs RPC 2-5s)
- [ ] **Dedicated RPC** — Upgrade from public `rpc.mantle.xyz` to Alchemy/QuickNode dedicated node
- [ ] **Redis cache layer** — Block cache + finding deduplication at scale (10k+ blocks/day)
- [ ] **PostgreSQL persistence** — Replace in-memory deque with durable finding storage
- [ ] **Kubernetes deployment** — Auto-scaling pipeline pods (collector, anomaly, insight separate services)

### Agent Upgrades
- [ ] **Live Pyth oracle integration** — Real-time MNT/USD, mETH/ETH, USDY/USD price streams
- [ ] **Cross-chain bridge tracking** — Monitor Mantle Bridge L1→L2 inflows as leading indicator
- [ ] **Lendle liquidation predictor** — Track health factors, predict cascades 2-4hrs early
- [ ] **Governance event integration** — Mantle governance proposals correlated with on-chain flows
- [ ] **MEV extraction monitor** — Track sandwich attacks, arbitrage profits on Mantle DEXs

### Data Sources (Phase 1)
| Source | Type | Latency | Cost |
|--------|------|---------|------|
| Mantle RPC (dedicated) | Block data | ~500ms | ~$200/mo |
| Pyth Hermes API | Price oracle | <100ms | Free |
| The Graph (Mantle subgraph) | Historical queries | <50ms | ~$50/mo |
| Mantle Bridge contract | Bridge events | ~1s | Free (RPC) |

---

## Phase 2 — Multi-Protocol Intelligence (Q4 2026)

**Target: Broadest Mantle ecosystem coverage**

### Protocol Coverage Expansion
- [ ] **Aurelius Finance** — Isolated lending market monitoring
- [ ] **INIT Capital** — Position management + hook-based alerts
- [ ] **Pendle Finance (Mantle)** — Yield trading + PT/YT price anomalies
- [ ] **Velo Finance** — veVELO lock/unlock pattern detection
- [ ] **Cleopatra Exchange** — Liquidity mining flow tracking
- [ ] **FusionX V3** — Concentrated liquidity position changes

### Cross-Chain Intelligence
- [ ] **Ethereum → Mantle bridge flows** — Leading indicator for MNT price action
- [ ] **Arbitrum/Optimism comparison** — Multi-L2 smart money tracking (same wallets across chains)
- [ ] **LayerZero messaging** — Cross-chain DeFi strategy detection

### ML Model Upgrades
- [ ] **LSTM time-series model** — Replace z-score with learned temporal patterns
- [ ] **Graph neural network** — Wallet relationship graph for cluster detection
- [ ] **Ensemble anomaly scorer** — Combine Isolation Forest + LSTM + GNN outputs
- [ ] **Online learning** — Model updates without pipeline restart

---

## Phase 3 — Subscription API & Revenue (Q1 2027)

**Target: Self-sustaining, revenue-generating product**

### API Product
```
Tier 1 — Free (Open Access)
  - /api/live-feed: 5-min delayed, 10 findings/response
  - Public dashboard access

Tier 2 — Professional ($99/mo)
  - Real-time WebSocket feed (< 2s latency)
  - 500 findings/day
  - Historical query API (30-day lookback)
  - Telegram/Discord bot for personal wallet tracking
  - 5 custom wallet labels

Tier 3 — Institutional ($999/mo)
  - Real-time + predictive signals (lead-time estimates)
  - Unlimited findings + full history
  - Custom protocol coverage requests
  - Dedicated Slack/Telegram alerts
  - SLA: 99.9% uptime, < 500ms alert latency
  - API key management, team access

Tier 4 — Enterprise (Custom pricing)
  - White-label dashboard
  - Custom ML model training on proprietary data
  - On-premise deployment option
  - Dedicated support + 24hr SLA
```

### Revenue Model
| Tier | Target Users | Monthly Rev |
|------|-------------|-------------|
| Free | 500 wallets, 50 protocols | $0 (funnel) |
| Pro | 100 traders, 20 small funds | $9,900 |
| Institutional | 15 hedge funds, 5 VCs | $14,985 |
| Enterprise | 3 protocols, 2 CEXs | ~$30,000 |
| **Total MRR (Q1 2027 target)** | | **~$55,000** |

**Annual ARR target: $660,000 by end of 2027**

---

## Phase 4 — On-Chain Intelligence Protocol (2027+)

**Target: Decentralized intelligence marketplace on Mantle**

### Protocol Vision
- **Signal Marketplace** — Analysts stake MNT to publish signals; quality tracked on-chain
- **Truth-seeking mechanism** — Signals verified against realized outcomes (oracle-fed)
- **Reputation NFT (ERC-8004 extension)** — Analyst reputation as transferable, composable identity
- **DAO governance** — MNT holders vote on signal categories, protocol coverage, fee split
- **Subscriber NFT** — Access pass to signal feeds (tradeable, secondary market)

### Token Economics (Proposed)
- **MINTEL token** — Protocol governance + signal staking
- **Revenue share** — 70% to analysts, 20% to protocol treasury, 10% to MNT stakers
- **Burn mechanism** — 5% of subscription fees burned (deflationary)

---

## Competitive Moat

| Dimension | Mantle Intel Agent | Nansen | Dune Analytics | Chainalysis |
|-----------|-------------------|--------|----------------|-------------|
| Mantle-native | ✅ Deep | ❌ Generic | ❌ Generic | ❌ Generic |
| Real-time alerts | ✅ <2s | ❌ 5-30min | ❌ Manual | ✅ (compliance) |
| mETH/LSD tracking | ✅ Native | ❌ Limited | ❌ Manual | ❌ None |
| On-chain audit log | ✅ Immutable | ❌ None | ❌ None | ❌ None |
| Investment signals | ✅ VC-grade | ✅ Labels only | ❌ Raw data | ❌ Compliance |
| Cost | $99-999/mo | $1,200/mo | $400/mo | $50k+/yr |

---

## Scalability Architecture (Phase 1)

```
┌──────────────────────────────────────────────────────────────┐
│                    MANTLE INTEL AGENT v2                      │
├─────────────────┬──────────────────┬──────────────────────────┤
│   Data Layer    │   Agent Layer    │      Delivery Layer       │
│                 │                  │                           │
│ Mantle RPC ─────┤                  │                           │
│ (dedicated)     │  CollectorAgent  │  Telegram Bot             │
│                 │       ↓          │  Discord Webhook          │
│ Pyth Oracle ────┤  AnomalyAgent   │  REST API (Vercel Edge)   │
│ (real-time)     │       ↓          │  WebSocket (Phase 2)      │
│                 │  SmartMoney     │  Dashboard (React)        │
│ The Graph ──────┤  Agent           │                           │
│ (historical)    │       ↓          │  On-chain Audit           │
│                 │  InsightAgent   │  (MantleIntelAudit.sol)   │
│ Bridge Events ──┤       ↓          │                           │
│ (L1 → L2)       │  AuditAgent     │                           │
├─────────────────┴──────────────────┴──────────────────────────┤
│                  Redis Cache + PostgreSQL                      │
│              Kubernetes (auto-scale 1-10 pods)                │
└──────────────────────────────────────────────────────────────┘
```

---

## KPIs & Success Metrics

| Metric | Phase 0 (Now) | Phase 1 | Phase 2 | Phase 3 |
|--------|--------------|---------|---------|---------|
| Detection precision | 100% | ≥95% | ≥90% | ≥88% (more signals) |
| Alert latency | <30s | <5s | <2s | <500ms |
| Protocol coverage | 8 | 15 | 25+ | 30+ |
| Labeled wallets | 60+ | 500+ | 2,000+ | 5,000+ |
| Paying subscribers | 0 | 10 | 50 | 150+ |
| Monthly findings | ~500 | 5,000 | 20,000 | 100,000+ |

---

*Mantle Intel Agent — Built for The Turing Test Hackathon 2026 (Mantle Network / DoraHacks)*  
*GitHub: [sodiq-code/mantle-intel-agent](https://github.com/sodiq-code/mantle-intel-agent)*
