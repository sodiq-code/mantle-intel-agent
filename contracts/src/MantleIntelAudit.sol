// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MantleIntelAudit v2.0
 * @notice On-chain audit log for Mantle Intel Agent findings.
 *         Every agent decision is hashed (SHA256 off-chain) and recorded here,
 *         enabling fully independent verifiability of all AI-generated insights.
 *
 * @dev Deployed on Mantle Network (chainId 5000 mainnet / 5003 testnet).
 *      AI agent calls recordFinding() after each anomaly detection cycle.
 *      Anyone can call verifyFinding() to check a specific finding hash.
 *
 * v2.0 changes:
 *   - getPublicFindings() — public paginated feed for external agents
 *   - IntelFeedSubscription event — enables pub/sub for downstream integrations
 *   - getFindingsByType() — filter by anomaly type
 *   - getStats() — public stats endpoint
 *   - Any address can subscribe to intel feed (permissionless read)
 */
import "@openzeppelin/contracts/access/Ownable.sol";

contract MantleIntelAudit is Ownable {

    // ── Events ──────────────────────────────────────────────────────────────

    event FindingRecorded(
        uint256 indexed findingId,
        bytes32 indexed findingHash,
        string  anomalyType,
        uint8   confidenceScore,   // 0-100
        uint256 blockHeight,
        address indexed recorder,
        uint256 timestamp
    );

    event AgentRegistered(address indexed agent, string agentName);

    /// @notice Emitted when an external address subscribes to the intel feed.
    ///         Downstream agents listen to this event for automated integration.
    event IntelFeedSubscription(
        address indexed subscriber,
        string  subscriptionType,   // "all" | "whale_only" | "smart_money_only"
        uint256 timestamp
    );

    /// @notice Emitted when intel feed delivers a finding to a subscriber.
    event IntelFeedDelivery(
        uint256 indexed findingId,
        address indexed subscriber,
        uint256 timestamp
    );

    // ── Storage ─────────────────────────────────────────────────────────────

    struct Finding {
        bytes32 findingHash;       // SHA256 of canonical 4-field JSON (off-chain)
        string  anomalyType;       // e.g. "whale_accumulation", "smart_money_inflow"
        uint8   confidenceScore;   // 0-100, threshold >= 80 required to record (P2-25: matches pipeline 0.80)
        uint256 blockHeight;       // Mantle block when anomaly was detected
        address recorder;          // agent wallet that submitted
        uint256 timestamp;
        bool    exists;
    }

    struct Subscription {
        string  subscriptionType;
        bool    active;
        uint256 subscribedAt;
    }

    mapping(uint256 => Finding)  public findings;
    mapping(bytes32 => uint256)  public hashToFindingId;   // reverse lookup
    mapping(address => bool)     public authorizedAgents;
    mapping(address => Subscription) public subscriptions; // intel feed subscribers
    mapping(string => uint256[]) private _findingsByType;  // type → finding IDs

    uint256 public findingCount;
    uint256[] private _allFindingIds;  // ordered array for pagination

    // ── Constructor ──────────────────────────────────────────────────────────

    constructor() Ownable(msg.sender) {
        authorizedAgents[msg.sender] = true;
    }

    // ── Modifiers ────────────────────────────────────────────────────────────



    modifier onlyAuthorized() {
        require(authorizedAgents[msg.sender], "Not authorized agent");
        _;
    }

    // ── Agent Management ─────────────────────────────────────────────────────

    function authorizeAgent(address agent, string calldata agentName) external onlyOwner {
        authorizedAgents[agent] = true;
        emit AgentRegistered(agent, agentName);
    }

    function revokeAgent(address agent) external onlyOwner {
        authorizedAgents[agent] = false;
    }

    // ── Core AI-Callable Function ─────────────────────────────────────────────

    /**
     * @notice Record a new agent finding on-chain.
     *         Called by the Audit Agent after anomaly detection.
     * @param findingHash    SHA256 of canonical 4-field JSON (block, confidence, tx_count, type)
     * @param anomalyType    Human-readable anomaly category
     * @param confidenceScore 0-100 confidence from ML model
     * @param blockHeight    Mantle block number of anomaly
     *
     * P2-25 FIX: Confidence threshold is 80, matching the off-chain pipeline's
     *        CONFIDENCE_THRESHOLD = 0.80. This ensures the contract enforces the
     *        same standard as the pipeline — a direct recordFinding() call with
     *        confidence below 80 (which the pipeline would reject) is also
     *        rejected on-chain. Thresholds must stay in sync.
     */
    function recordFinding(
        bytes32 findingHash,
        string  calldata anomalyType,
        uint8   confidenceScore,
        uint256 blockHeight
    ) external onlyAuthorized returns (uint256 findingId) {
        require(confidenceScore >= 80, "Confidence too low");
        require(hashToFindingId[findingHash] == 0, "Finding already recorded");
        require(bytes(anomalyType).length > 0, "Empty anomaly type");

        findingCount++;
        findingId = findingCount;

        findings[findingId] = Finding({
            findingHash:     findingHash,
            anomalyType:     anomalyType,
            confidenceScore: confidenceScore,
            blockHeight:     blockHeight,
            recorder:        msg.sender,
            timestamp:       block.timestamp,
            exists:          true
        });

        hashToFindingId[findingHash] = findingId;
        _allFindingIds.push(findingId);
        _findingsByType[anomalyType].push(findingId);

        emit FindingRecorded(
            findingId,
            findingHash,
            anomalyType,
            confidenceScore,
            blockHeight,
            msg.sender,
            block.timestamp
        );
    }

    // ── Verification ──────────────────────────────────────────────────────────

    /**
     * @notice Verify a finding by its hash.
     * @return verified  true if the hash exists in the audit log
     * @return findingId internal finding ID (0 if not found)
     * @return timestamp unix timestamp of recording
     * @return confidence confidence score 0-100
     */
    function verifyFinding(bytes32 findingHash)
        external
        view
        returns (bool verified, uint256 findingId, uint256 timestamp, uint8 confidence)
    {
        findingId = hashToFindingId[findingHash];
        if (findingId == 0) {
            return (false, 0, 0, 0);
        }
        Finding storage f = findings[findingId];
        return (f.exists, findingId, f.timestamp, f.confidenceScore);
    }

    /**
     * @notice Get all details of a finding by ID.
     */
    function getFinding(uint256 findingId)
        external
        view
        returns (
            bytes32 findingHash,
            string memory anomalyType,
            uint8 confidenceScore,
            uint256 blockHeight,
            address recorder,
            uint256 timestamp
        )
    {
        require(findings[findingId].exists, "Finding not found");
        Finding storage f = findings[findingId];
        return (f.findingHash, f.anomalyType, f.confidenceScore, f.blockHeight, f.recorder, f.timestamp);
    }

    // ── Public Intel Feed API (v2.0) ──────────────────────────────────────────

    /**
     * @notice Get paginated public findings feed.
     *         Permissionless — any address can query.
     *         Used by external agents, dashboards, and Intel Feed subscribers.
     *
     * @param offset   Start index (0 = oldest)
     * @param limit    Max results to return (max 50)
     * @return ids     Array of finding IDs
     * @return total   Total number of findings in contract
     */
    function getPublicFindings(uint256 offset, uint256 limit)
        external
        view
        returns (uint256[] memory ids, uint256 total)
    {
        total = _allFindingIds.length;
        if (limit > 50) limit = 50;
        if (offset >= total) {
            return (new uint256[](0), total);
        }

        uint256 end = offset + limit;
        if (end > total) end = total;
        uint256 length = end - offset;

        ids = new uint256[](length);
        for (uint256 i = 0; i < length; i++) {
            ids[i] = _allFindingIds[offset + i];
        }
    }

    /**
     * @notice Get finding IDs filtered by anomaly type.
     *         Useful for downstream agents that only care about specific signals.
     *
     * @param anomalyType  e.g. "whale_accumulation", "smart_money_inflow"
     * @param limit        Max results (max 50)
     */
    function getFindingsByType(string calldata anomalyType, uint256 limit)
        external
        view
        returns (uint256[] memory ids)
    {
        uint256[] storage typeIds = _findingsByType[anomalyType];
        uint256 count = typeIds.length;
        if (limit > 50) limit = 50;
        if (count == 0) return new uint256[](0);

        uint256 returnCount = count < limit ? count : limit;
        ids = new uint256[](returnCount);
        // Return most recent first
        for (uint256 i = 0; i < returnCount; i++) {
            ids[i] = typeIds[count - 1 - i];
        }
    }

    /**
     * @notice Get recent finding IDs (latest N, newest first).
     */
    function getRecentFindings(uint256 count)
        external
        view
        returns (uint256[] memory ids)
    {
        if (count > findingCount) count = findingCount;
        ids = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            ids[i] = findingCount - i;
        }
    }

    /**
     * @notice Public stats — total findings, latest block, confidence distribution.
     *         Useful for dashboard and external integrations.
     */
    function getStats()
        external
        view
        returns (
            uint256 totalFindings,
            uint256 latestBlockHeight,
            uint256 latestTimestamp,
            uint8   latestConfidence
        )
    {
        totalFindings = findingCount;
        if (findingCount == 0) {
            return (0, 0, 0, 0);
        }
        Finding storage latest = findings[findingCount];
        return (findingCount, latest.blockHeight, latest.timestamp, latest.confidenceScore);
    }

    // ── Intel Feed Subscription (v2.0) ────────────────────────────────────────

    /**
     * @notice Subscribe to the Mantle Intel Agent public feed.
     *         Permissionless. Emits IntelFeedSubscription for off-chain listeners.
     *         External agents call this to signal they want to receive future findings.
     *
     * @param subscriptionType  "all" | "whale_only" | "smart_money_only" | "high_confidence"
     */
    function subscribe(string calldata subscriptionType) external {
        subscriptions[msg.sender] = Subscription({
            subscriptionType: subscriptionType,
            active:           true,
            subscribedAt:     block.timestamp
        });

        emit IntelFeedSubscription(
            msg.sender,
            subscriptionType,
            block.timestamp
        );
    }

    /**
     * @notice Unsubscribe from intel feed.
     */
    function unsubscribe() external {
        subscriptions[msg.sender].active = false;
    }

    /**
     * @notice Check if an address is subscribed.
     */
    function isSubscribed(address subscriber) external view returns (bool) {
        return subscriptions[subscriber].active;
    }
}
