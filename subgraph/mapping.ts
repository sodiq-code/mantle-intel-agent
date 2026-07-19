// ── P3-28 + P3-33: Subgraph Event Handlers ─────────────────────────────────────
// Indexes FindingRecorded, AgentRegistered, IntelFeedSubscription, IntelFeedDelivery

import {
  FindingRecorded as FindingRecordedEvent,
  AgentRegistered as AgentRegisteredEvent,
  IntelFeedSubscription as IntelFeedSubscriptionEvent,
  IntelFeedDelivery as IntelFeedDeliveryEvent,
} from "../generated/MantleIntelAudit/MantleIntelAudit";

import {
  Finding,
  Subscription,
  SubscriptionEvent,
  Agent,
  IntelFeedDelivery as IntelFeedDeliveryEntity,
  DailyStats,
} from "../generated/schema";

// ── FindingRecorded Handler ─────────────────────────────────────────────────────

export function handleFindingRecorded(event: FindingRecordedEvent): void {
  let finding = new Finding(event.params.findingId.toString());
  finding.findingHash = event.params.findingHash;
  finding.anomalyType = event.params.anomalyType;
  finding.confidenceScore = event.params.confidenceScore;
  finding.blockHeight = event.params.blockHeight;
  finding.recorder = event.params.recorder;
  finding.timestamp = event.params.timestamp;
  finding.blockNumber = event.block.number;
  finding.transactionHash = event.transaction.hash;
  finding.save();

  // Update agent's finding count
  let agent = Agent.load(event.params.recorder.toHexString());
  if (agent != null) {
    agent.findingsCount = agent.findingsCount + 1;
    agent.save();
  }

  // Update daily stats
  let dayId = event.params.timestamp.toI32() / 86400;  // seconds per day
  let dayIdStr = dayId.toString();
  let dailyStats = DailyStats.load(dayIdStr);
  if (dailyStats == null) {
    dailyStats = new DailyStats(dayIdStr);
    dailyStats.findingsCount = 0;
    dailyStats.newSubscriptions = 0;
    dailyStats.avgConfidence = 0.0;
    dailyStats.uniqueAnomalyTypes = 0;
    dailyStats.topAnomalyType = "";
    dailyStats.timestamp = event.params.timestamp;
  }
  dailyStats.findingsCount = dailyStats.findingsCount + 1;
  // Running average: new_avg = old_avg + (new_value - old_avg) / count
  let count = dailyStats.findingsCount;
  dailyStats.avgConfidence =
    dailyStats.avgConfidence + (event.params.confidenceScore - dailyStats.avgConfidence) / count;
  dailyStats.save();
}

// ── AgentRegistered Handler ─────────────────────────────────────────────────────

export function handleAgentRegistered(event: AgentRegisteredEvent): void {
  let agent = new Agent(event.params.agent.toHexString());
  agent.agentName = event.params.agentName;
  agent.registeredAt = event.block.timestamp;
  agent.findingsCount = 0;
  agent.blockNumber = event.block.number;
  agent.save();
}

// ── IntelFeedSubscription Handler ────────────────────────────────────────────────

export function handleIntelFeedSubscription(event: IntelFeedSubscriptionEvent): void {
  // Create or update subscription entity
  let subId = event.params.subscriber.toHexString() + "-" + event.params.timestamp.toString();
  let subscription = new Subscription(subId);
  subscription.subscriber = event.params.subscriber;
  subscription.subscriptionType = event.params.subscriptionType;
  subscription.active = true;
  subscription.timestamp = event.params.timestamp;
  subscription.blockNumber = event.block.number;
  subscription.transactionHash = event.transaction.hash;
  subscription.save();

  // Create subscription event
  let eventId = event.transaction.hash.toHexString() + "-" + event.logIndex.toString();
  let subEvent = new SubscriptionEvent(eventId);
  subEvent.subscriber = event.params.subscriber;
  subEvent.eventType = "subscribed";
  subEvent.subscriptionType = event.params.subscriptionType;
  subEvent.timestamp = event.params.timestamp;
  subEvent.blockNumber = event.block.number;
  subEvent.transactionHash = event.transaction.hash;
  subEvent.save();

  // Update daily stats
  let dayId = event.params.timestamp.toI32() / 86400;
  let dayIdStr = dayId.toString();
  let dailyStats = DailyStats.load(dayIdStr);
  if (dailyStats == null) {
    dailyStats = new DailyStats(dayIdStr);
    dailyStats.findingsCount = 0;
    dailyStats.newSubscriptions = 0;
    dailyStats.avgConfidence = 0.0;
    dailyStats.uniqueAnomalyTypes = 0;
    dailyStats.topAnomalyType = "";
    dailyStats.timestamp = event.params.timestamp;
  }
  dailyStats.newSubscriptions = dailyStats.newSubscriptions + 1;
  dailyStats.save();
}

// ── IntelFeedDelivery Handler ────────────────────────────────────────────────────

export function handleIntelFeedDelivery(event: IntelFeedDeliveryEvent): void {
  let deliveryId = event.params.findingId.toString() + "-" + event.params.subscriber.toHexString();
  let delivery = new IntelFeedDeliveryEntity(deliveryId);
  delivery.findingId = event.params.findingId;
  delivery.subscriber = event.params.subscriber;
  delivery.timestamp = event.params.timestamp;
  delivery.blockNumber = event.block.number;
  delivery.transactionHash = event.transaction.hash;
  delivery.save();
}
