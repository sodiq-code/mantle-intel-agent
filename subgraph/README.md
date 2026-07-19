# ── P3-28: Subgraph README ─────────────────────────────────────────────────────
# Mantle Intel Agent — Subgraph & Ponder Indexer

Two options for indexing `MantleIntelAudit.sol` events for fast historical queries:

## Option A: Ponder Indexer (Recommended for Mantle)

Ponder works on **any EVM chain** including Mantle — no The Graph deployment needed.

```bash
cd ponder
bun install
bun run dev
```

GraphQL API: `http://localhost:42069/graphql`

### Example Queries

```graphql
# Get latest 10 findings
{
  findings(orderBy: "timestamp", orderDirection: "desc", limit: 10) {
    items { anomalyType confidenceScore blockHeight recorder timestamp }
  }
}

# Filter by anomaly type
{
  findings(where: { anomalyType: "whale_accumulation" }) {
    items { confidenceScore blockHeight findingHash }
  }
}

# Get active subscriptions
{
  subscriptions(where: { active: true }) {
    items { subscriber subscriptionType timestamp }
  }
}

# Daily stats for last 30 days
{
  dailyStats(orderBy: "timestamp", orderDirection: "desc", limit: 30) {
    items { id findingsCount avgConfidence newSubscriptions }
  }
}
```

## Option B: The Graph Subgraph

For chains supported by The Graph (Ethereum, Arbitrum, Optimism, etc.):

```bash
cd subgraph
npm install -g @graphprotocol/graph-cli
graph auth https://api.thegraph.com/deploy/ <YOUR_ACCESS_TOKEN>
graph codegen && graph build
graph deploy sodiq-code/mantle-intel-audit
```

**Note:** The Graph does not currently support Mantle natively. Use Ponder for Mantle.

## Architecture

```
┌──────────────────────┐
│  MantleIntelAudit.sol│
│  (0x7266cD...)       │
└──────────┬───────────┘
           │ Events
           ▼
┌──────────────────────┐
│  Ponder Indexer      │  ← Reads events directly from Mantle RPC
│  (TypeScript)        │     Stores in SQLite + serves GraphQL
│                      │     Latency: <50ms vs RPC 2-5s
└──────────┬───────────┘
           │ GraphQL API (:42069)
           ▼
┌──────────────────────┐
│  Dashboard / API     │  ← Fast historical queries
│  (React + Vercel)    │     Paginated, filtered, sorted
└──────────────────────┘
```

## Indexed Events

| Event | Entity | Key Fields |
|-------|--------|-----------|
| `FindingRecorded` | Finding | findingHash, anomalyType, confidenceScore, blockHeight |
| `IntelFeedSubscription` | Subscription + SubscriptionEvent | subscriber, subscriptionType, active |
| `IntelFeedDelivery` | IntelFeedDelivery | findingId, subscriber |
| `AgentRegistered` | Agent | agentName, findingsCount |
| _(Daily rollups)_ | DailyStats | findingsCount, avgConfidence, newSubscriptions |
