/**
 * P2-22: Solidity Test Suite for MantleIntelAudit.sol
 *
 * Tests cover:
 *   1. recordFinding() succeeds with valid params (confidence=75)
 *   2. recordFinding() reverts with confidence < 75 (P2-23 fix)
 *   3. recordFinding() reverts on duplicate hash
 *   4. recordFinding() reverts on empty anomaly type
 *   5. verifyFinding() returns correct data after recording
 *   6. verifyFinding() returns false for unknown hash
 *   7. getPublicFindings() pagination works
 *   8. getFindingsByType() filtering works
 *   9. subscribe() / isSubscribed() works
 *  10. Unauthorized address cannot call recordFinding()
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MantleIntelAudit", function () {
  let audit;
  let owner;
  let authorized;
  let unauthorized;

  // Helper: compute a bytes32 hash from a string
  function hashString(str) {
    return ethers.keccak256(ethers.toUtf8Bytes(str));
  }

  beforeEach(async function () {
    [owner, authorized, unauthorized] = await ethers.getSigners();

    const MantleIntelAudit = await ethers.getContractFactory("MantleIntelAudit");
    audit = await MantleIntelAudit.deploy();
    await audit.waitForDeployment();

    // Authorize the 'authorized' signer
    await audit.authorizeAgent(await authorized.getAddress(), "TestAgent");
  });

  // ── Test 1: recordFinding() succeeds with valid params ────────────────────

  it("should record a finding with valid params and confidence=75", async function () {
    const findingHash = hashString("test-finding-1");
    const anomalyType = "whale_accumulation";
    const confidence = 75;  // P2-23: minimum threshold
    const blockHeight = 1000;

    await expect(
      audit.connect(authorized).recordFinding(
        findingHash, anomalyType, confidence, blockHeight
      )
    ).to.emit(audit, "FindingRecorded").withArgs(
      1, findingHash, anomalyType, confidence, blockHeight,
      await authorized.getAddress(),
      (v) => v > 0  // timestamp
    );

    expect(await audit.findingCount()).to.equal(1);
  });

  // ── Test 2: recordFinding() reverts with confidence < 75 (P2-23) ──────────

  it("should revert when confidence is below 75 (P2-23 threshold)", async function () {
    const findingHash = hashString("test-finding-low-confidence");

    // Test confidence = 50 (old threshold, should now fail)
    await expect(
      audit.connect(authorized).recordFinding(
        findingHash, "whale_accumulation", 50, 1000
      )
    ).to.be.revertedWith("Confidence too low");

    // Test confidence = 74 (just below threshold)
    await expect(
      audit.connect(authorized).recordFinding(
        findingHash, "whale_accumulation", 74, 1000
      )
    ).to.be.revertedWith("Confidence too low");

    // Test confidence = 0
    await expect(
      audit.connect(authorized).recordFinding(
        findingHash, "whale_accumulation", 0, 1000
      )
    ).to.be.revertedWith("Confidence too low");
  });

  // ── Test 3: recordFinding() reverts on duplicate hash ─────────────────────

  it("should revert on duplicate finding hash", async function () {
    const findingHash = hashString("duplicate-finding");

    // First call succeeds
    await audit.connect(authorized).recordFinding(
      findingHash, "whale_accumulation", 80, 1000
    );

    // Second call with same hash reverts
    await expect(
      audit.connect(authorized).recordFinding(
        findingHash, "smart_money_inflow", 85, 2000
      )
    ).to.be.revertedWith("Finding already recorded");
  });

  // ── Test 4: recordFinding() reverts on empty anomaly type ─────────────────

  it("should revert on empty anomaly type", async function () {
    const findingHash = hashString("empty-type-finding");

    await expect(
      audit.connect(authorized).recordFinding(
        findingHash, "", 80, 1000
      )
    ).to.be.revertedWith("Empty anomaly type");
  });

  // ── Test 5: verifyFinding() returns correct data after recording ──────────

  it("should verify a recorded finding correctly", async function () {
    const findingHash = hashString("verify-test-finding");
    const anomalyType = "smart_money_inflow";
    const confidence = 90;
    const blockHeight = 5000;

    await audit.connect(authorized).recordFinding(
      findingHash, anomalyType, confidence, blockHeight
    );

    const result = await audit.verifyFinding(findingHash);
    expect(result.verified).to.be.true;
    expect(result.findingId).to.equal(1);
    expect(result.confidence).to.equal(confidence);
    expect(result.timestamp).to.be.gt(0);
  });

  // ── Test 6: verifyFinding() returns false for unknown hash ────────────────

  it("should return false for unknown finding hash", async function () {
    const unknownHash = hashString("nonexistent-finding");

    const result = await audit.verifyFinding(unknownHash);
    expect(result.verified).to.be.false;
    expect(result.findingId).to.equal(0);
    expect(result.timestamp).to.equal(0);
    expect(result.confidence).to.equal(0);
  });

  // ── Test 7: getPublicFindings() pagination works ──────────────────────────

  it("should paginate public findings correctly", async function () {
    // Record 5 findings
    for (let i = 1; i <= 5; i++) {
      await audit.connect(authorized).recordFinding(
        hashString(`paginated-finding-${i}`),
        `anomaly_type_${i}`,
        80,
        1000 + i
      );
    }

    // Get first 3
    const [ids1, total1] = await audit.getPublicFindings(0, 3);
    expect(ids1.length).to.equal(3);
    expect(total1).to.equal(5);

    // Get next 3 (only 2 remain)
    const [ids2, total2] = await audit.getPublicFindings(3, 3);
    expect(ids2.length).to.equal(2);
    expect(total2).to.equal(5);

    // Offset beyond total returns empty
    const [ids3, total3] = await audit.getPublicFindings(10, 3);
    expect(ids3.length).to.equal(0);
    expect(total3).to.equal(5);
  });

  // ── Test 8: getFindingsByType() filtering works ───────────────────────────

  it("should filter findings by anomaly type", async function () {
    // Record 3 of one type and 2 of another
    for (let i = 1; i <= 3; i++) {
      await audit.connect(authorized).recordFinding(
        hashString(`whale-finding-${i}`),
        "whale_accumulation",
        80,
        1000 + i
      );
    }
    for (let i = 1; i <= 2; i++) {
      await audit.connect(authorized).recordFinding(
        hashString(`smart-money-finding-${i}`),
        "smart_money_inflow",
        85,
        2000 + i
      );
    }

    // Filter by whale_accumulation
    const whaleIds = await audit.getFindingsByType("whale_accumulation", 10);
    expect(whaleIds.length).to.equal(3);

    // Filter by smart_money_inflow
    const smIds = await audit.getFindingsByType("smart_money_inflow", 10);
    expect(smIds.length).to.equal(2);

    // Filter by non-existent type
    const noneIds = await audit.getFindingsByType("nonexistent_type", 10);
    expect(noneIds.length).to.equal(0);

    // Limit results
    const limitedIds = await audit.getFindingsByType("whale_accumulation", 2);
    expect(limitedIds.length).to.equal(2);
  });

  // ── Test 9: subscribe() / isSubscribed() works ────────────────────────────

  it("should handle subscription lifecycle", async function () {
    const subscriber = unauthorized;

    // Initially not subscribed
    expect(await audit.isSubscribed(await subscriber.getAddress())).to.be.false;

    // Subscribe
    await expect(
      audit.connect(subscriber).subscribe("all")
    ).to.emit(audit, "IntelFeedSubscription");

    expect(await audit.isSubscribed(await subscriber.getAddress())).to.be.true;

    // Unsubscribe
    await audit.connect(subscriber).unsubscribe();
    expect(await audit.isSubscribed(await subscriber.getAddress())).to.be.false;
  });

  // ── Test 10: Unauthorized address cannot call recordFinding() ─────────────

  it("should reject recordFinding from unauthorized address", async function () {
    const findingHash = hashString("unauthorized-finding");

    await expect(
      audit.connect(unauthorized).recordFinding(
        findingHash, "whale_accumulation", 80, 1000
      )
    ).to.be.revertedWith("Not authorized agent");
  });

  // ── Bonus: Agent management ────────────────────────────────────────────────

  it("should allow owner to authorize and revoke agents", async function () {
    const newAgent = unauthorized;

    // Not authorized initially
    await expect(
      audit.connect(newAgent).recordFinding(
        hashString("new-agent-test"), "test_type", 80, 1000
      )
    ).to.be.revertedWith("Not authorized agent");

    // Owner authorizes
    await audit.authorizeAgent(await newAgent.getAddress(), "NewAgent");

    // Now authorized
    await expect(
      audit.connect(newAgent).recordFinding(
        hashString("new-agent-test"), "test_type", 80, 1000
      )
    ).to.emit(audit, "FindingRecorded");

    // Owner revokes
    await audit.revokeAgent(await newAgent.getAddress());

    // No longer authorized
    await expect(
      audit.connect(newAgent).recordFinding(
        hashString("new-agent-test-2"), "test_type", 85, 2000
      )
    ).to.be.revertedWith("Not authorized agent");
  });

  // ── Bonus: getStats() returns correct data ─────────────────────────────────

  it("should return correct stats", async function () {
    // No findings yet
    const stats0 = await audit.getStats();
    expect(stats0.totalFindings).to.equal(0);

    // Record a finding
    await audit.connect(authorized).recordFinding(
      hashString("stats-finding"), "value_spike", 95, 9999
    );

    const stats1 = await audit.getStats();
    expect(stats1.totalFindings).to.equal(1);
    expect(stats1.latestBlockHeight).to.equal(9999);
    expect(stats1.latestConfidence).to.equal(95);
  });

  // ── Bonus: Only owner can authorize agents ─────────────────────────────────

  it("should reject non-owner trying to authorize agents", async function () {
    await expect(
      audit.connect(unauthorized).authorizeAgent(
        await unauthorized.getAddress(), "SelfAuth"
      )
    ).to.be.reverted;  // Ownable: only owner
  });
});
