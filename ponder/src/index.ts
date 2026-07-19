// ── P3-28 + P3-33: Ponder Event Indexing Functions ──────────────────────────────
// Handles FindingRecorded, AgentRegistered, IntelFeedSubscription, IntelFeedDelivery
//
// Start: cd ponder && bun install && bun run dev
// GraphQL API: http://localhost:42069/graphql
//
// Example queries:
//   { findings(orderBy: "timestamp", orderDirection: "desc", limit: 10) { items { anomalyType confidenceScore blockHeight } } }
//   { subscriptions(where: { active: true }) { items { subscriber subscriptionType } } }
//   { dailyStats(orderBy: "timestamp", orderDirection: "desc", limit: 30) { items { id findingsCount avgConfidence } } }

import { ponder } from "@/generated";
import {
  Finding,
  Subscription,
  SubscriptionEvent,
  Agent,
  IntelFeedDelivery,
  DailyStats,
} from "../ponder.schema";

// ── FindingRecorded ─────────────────────────────────────────────────────────────

ponder.on("MantleIntelAudit:FindingRecorded", async ({ event, context }) => {
  const { findingId, findingHash, anomalyType, confidenceScore, blockHeight, recorder, timestamp } = event.args;

  await context.db.insert(Finding).values({
    id: findingId.toString(),
    findingHash: findingHash,
    anomalyType: anomalyType,
    confidenceScore: Number(confidenceScore),
    blockHeight: blockHeight,
    recorder: recorder,
    timestamp: timestamp,
    blockNumber: event.block.number,
    transactionHash: event.transaction.hash,
  });

  // Update agent's finding count
  const agentRecord = await context.db.find(Agent, { id: recorder });
  if (agentRecord) {
    await context.db.update(Agent, { id: recorder }).set({
      findingsCount: agentRecord.findingsCount + 1,
    });
  }

  // Update daily stats
  const dayTimestamp = Number(timestamp) / 86400;
  const dayId = new Date(dayTimestamp * 86400 * 1000).toISOString().split("T")[0];
  const existing = await context.db.find(DailyStats, { id: dayId });
  if (existing) {
    const newCount = existing.findingsCount + 1;
    const newAvg = existing.avgConfidence + (Number(confidenceScore) - existing.avgConfidence) / newCount;
    await context.db.update(DailyStats, { id: dayId }).set({
      findingsCount: newCount,
      avgConfidence: newAvg,
    });
  } else {
    await context.db.insert(DailyStats).values({
      id: dayId,
      findingsCount: 1,
      avgConfidence: Number(confidenceScore),
      newSubscriptions: 0,
      topAnomalyType: anomalyType,
      timestamp: timestamp,
    });
  }
});

// ── AgentRegistered ─────────────────────────────────────────────────────────────

ponder.on("MantleIntelAudit:AgentRegistered", async ({ event, context }) => {
  const { agent, agentName } = event.args;

  await context.db.insert(Agent).values({
    id: agent,
    agentName: agentName,
    registeredAt: event.block.timestamp,
    findingsCount: 0,
    blockNumber: event.block.number,
  });
});

// ── IntelFeedSubscription ────────────────────────────────────────────────────────

ponder.on("MantleIntelAudit:IntelFeedSubscription", async ({ event, context }) => {
  const { subscriber, subscriptionType, timestamp } = event.args;

  // Update subscription entity
  await context.db.insert(Subscription).values({
    id: subscriber,
    subscriber: subscriber,
    subscriptionType: subscriptionType,
    active: true,
    timestamp: timestamp,
    blockNumber: event.block.number,
    transactionHash: event.transaction.hash,
  });

  // Create subscription event
  const eventId = `${event.transaction.hash}-${event.logIndex}`;
  await context.db.insert(SubscriptionEvent).values({
    id: eventId,
    subscriber: subscriber,
    eventType: "subscribed",
    subscriptionType: subscriptionType,
    timestamp: timestamp,
    blockNumber: event.block.number,
    transactionHash: event.transaction.hash,
  });

  // Update daily stats
  const dayTimestamp = Number(timestamp) / 86400;
  const dayId = new Date(dayTimestamp * 86400 * 1000).toISOString().split("T")[0];
  const existing = await context.db.find(DailyStats, { id: dayId });
  if (existing) {
    await context.db.update(DailyStats, { id: dayId }).set({
      newSubscriptions: existing.newSubscriptions + 1,
    });
  } else {
    await context.db.insert(DailyStats).values({
      id: dayId,
      findingsCount: 0,
      avgConfidence: 0,
      newSubscriptions: 1,
      topAnomalyType: "",
      timestamp: timestamp,
    });
  }
});

// ── IntelFeedDelivery ────────────────────────────────────────────────────────────

ponder.on("MantleIntelAudit:IntelFeedDelivery", async ({ event, context }) => {
  const { findingId, subscriber, timestamp } = event.args;

  await context.db.insert(IntelFeedDelivery).values({
    id: `${findingId}-${subscriber}`,
    findingId: findingId,
    subscriber: subscriber,
    timestamp: timestamp,
    blockNumber: event.block.number,
    transactionHash: event.transaction.hash,
  });
});
