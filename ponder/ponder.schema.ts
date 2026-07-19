// ── P3-28 + P3-33: Ponder Indexer Schema ────────────────────────────────────────
// Defines the database schema for indexed events.
// Ponder auto-generates TypeScript types from this schema.

export const Finding = ponder
  .createTable("Finding", {
    id: ponder.string().primaryKey(),
    findingHash: ponder.string().notNull(),   // bytes32 hex
    anomalyType: ponder.string().notNull(),
    confidenceScore: ponder.int().notNull(),   // 0-100
    blockHeight: ponder.bigint().notNull(),
    recorder: ponder.string().notNull(),       // address hex
    timestamp: ponder.bigint().notNull(),
    blockNumber: ponder.bigint().notNull(),
    transactionHash: ponder.string().notNull(),
  })
  .index("anomalyType")
  .index("recorder")
  .index("timestamp")
  .index("confidenceScore");

export const Subscription = ponder
  .createTable("Subscription", {
    id: ponder.string().primaryKey(),           // subscriber address
    subscriber: ponder.string().notNull(),
    subscriptionType: ponder.string().notNull(),
    active: ponder.boolean().notNull().default(true),
    timestamp: ponder.bigint().notNull(),
    blockNumber: ponder.bigint().notNull(),
    transactionHash: ponder.string().notNull(),
  })
  .index("subscriber")
  .index("active");

export const SubscriptionEvent = ponder
  .createTable("SubscriptionEvent", {
    id: ponder.string().primaryKey(),           // txHash + logIndex
    subscriber: ponder.string().notNull(),
    eventType: ponder.string().notNull(),       // "subscribed" | "unsubscribed"
    subscriptionType: ponder.string(),
    timestamp: ponder.bigint().notNull(),
    blockNumber: ponder.bigint().notNull(),
    transactionHash: ponder.string().notNull(),
  })
  .index("subscriber")
  .index("eventType");

export const Agent = ponder
  .createTable("Agent", {
    id: ponder.string().primaryKey(),           // agent address
    agentName: ponder.string().notNull(),
    registeredAt: ponder.bigint().notNull(),
    findingsCount: ponder.int().notNull().default(0),
    blockNumber: ponder.bigint().notNull(),
  });

export const IntelFeedDelivery = ponder
  .createTable("IntelFeedDelivery", {
    id: ponder.string().primaryKey(),           // findingId + subscriber
    findingId: ponder.bigint().notNull(),
    subscriber: ponder.string().notNull(),
    timestamp: ponder.bigint().notNull(),
    blockNumber: ponder.bigint().notNull(),
    transactionHash: ponder.string().notNull(),
  })
  .index("subscriber")
  .index("findingId");

export const DailyStats = ponder
  .createTable("DailyStats", {
    id: ponder.string().primaryKey(),           // "YYYY-MM-DD"
    findingsCount: ponder.int().notNull().default(0),
    avgConfidence: ponder.real().notNull().default(0),
    newSubscriptions: ponder.int().notNull().default(0),
    topAnomalyType: ponder.string().notNull().default(""),
    timestamp: ponder.bigint().notNull(),
  });
