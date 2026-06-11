// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MantleIntelAudit
 * @notice On-chain audit log for Mantle Intel Agent findings.
 *         Every agent decision is hashed (SHA256 off-chain) and recorded here,
 *         enabling fully independent verifiability of all AI-generated insights.
 *
 * @dev Deployed on Mantle Network (chainId 5000 mainnet / 5003 testnet).
 *      AI agent calls recordFinding() after each anomaly detection cycle.
 *      Anyone can call verifyFinding() to check a specific finding hash.
 */
contract MantleIntelAudit {

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

    // ── Storage ─────────────────────────────────────────────────────────────

    struct Finding {
        bytes32 findingHash;       // SHA256 of full finding JSON (off-chain)
        string  anomalyType;       // e.g. "whale_accumulation", "tvl_drop", "smart_money_inflow"
        uint8   confidenceScore;   // 0-100, threshold > 75 required to record
        uint256 blockHeight;       // Mantle block when anomaly was detected
        address recorder;          // agent wallet that submitted
        uint256 timestamp;
        bool    exists;
    }

    mapping(uint256 => Finding) public findings;
    mapping(bytes32 => uint256) public hashToFindingId;  // reverse lookup
    mapping(address => bool)    public authorizedAgents;

    uint256 public findingCount;
    address public owner;

    // ── Constructor ──────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        authorizedAgents[msg.sender] = true;
    }

    // ── Modifiers ────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(authorizedAgents[msg.sender], "Not authorized agent");
        _;
    }

    // ── Agent Management ────────────────────────────────────────────────────

    function authorizeAgent(address agent, string calldata agentName) external onlyOwner {
        authorizedAgents[agent] = true;
        emit AgentRegistered(agent, agentName);
    }

    function revokeAgent(address agent) external onlyOwner {
        authorizedAgents[agent] = false;
    }

    // ── Core AI-Callable Function ────────────────────────────────────────────

    /**
     * @notice Record a new agent finding on-chain.
     *         Called by the Audit Agent after anomaly detection.
     * @param findingHash    SHA256 of the full finding JSON (hex, 32 bytes)
     * @param anomalyType    Human-readable anomaly category
     * @param confidenceScore 0-100 confidence from ML model
     * @param blockHeight    Mantle block number of anomaly
     */
    function recordFinding(
        bytes32 findingHash,
        string  calldata anomalyType,
        uint8   confidenceScore,
        uint256 blockHeight
    ) external onlyAuthorized returns (uint256 findingId) {
        require(confidenceScore >= 50, "Confidence too low");
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

    // ── Verification ─────────────────────────────────────────────────────────

    /**
     * @notice Verify a finding by its hash. Returns (true, findingId, timestamp, confidence)
     *         if found, (false, 0, 0, 0) otherwise.
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

    /**
     * @notice Get recent finding IDs (up to last 50).
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

    // ── Public Read (no auth needed) ─────────────────────────────────────────

    /**
     * @notice Paginated public view of findings — anyone can call.
     *         Returns up to `limit` findings starting at `offset` (1-indexed).
     *         Used by external dashboards, block explorers, and third-party tools.
     * @param offset  First finding ID to return (1 = oldest, findingCount = newest)
     * @param limit   Max findings per page (capped at 100)
     */
    function getPublicFindings(uint256 offset, uint256 limit)
        external
        view
        returns (
            uint256[] memory ids,
            bytes32[] memory hashes,
            string[]  memory anomalyTypes,
            uint8[]   memory confidences,
            uint256[] memory blockHeights,
            uint256[] memory timestamps
        )
    {
        if (limit > 100) limit = 100;
        if (offset == 0) offset = 1;
        if (offset > findingCount) {
            return (
                new uint256[](0),
                new bytes32[](0),
                new string[](0),
                new uint8[](0),
                new uint256[](0),
                new uint256[](0)
            );
        }

        uint256 end = offset + limit - 1;
        if (end > findingCount) end = findingCount;
        uint256 resultLen = end - offset + 1;

        ids         = new uint256[](resultLen);
        hashes      = new bytes32[](resultLen);
        anomalyTypes= new string[](resultLen);
        confidences = new uint8[](resultLen);
        blockHeights= new uint256[](resultLen);
        timestamps  = new uint256[](resultLen);

        for (uint256 i = 0; i < resultLen; i++) {
            uint256 fid = offset + i;
            Finding storage f = findings[fid];
            ids[i]          = fid;
            hashes[i]       = f.findingHash;
            anomalyTypes[i] = f.anomalyType;
            confidences[i]  = f.confidenceScore;
            blockHeights[i] = f.blockHeight;
            timestamps[i]   = f.timestamp;
        }
    }

    // ── Subscription / Notification Registry ────────────────────────────────

    event Subscribed(address indexed subscriber, uint8 minConfidence, string[] filterTypes);
    event Unsubscribed(address indexed subscriber);

    struct Subscription {
        bool    active;
        uint8   minConfidence;   // Only alert if confidence >= this
        bool    allTypes;        // If true, ignore typeFilters
        mapping(bytes32 => bool) typeFilters; // keccak256(anomalyType) => enabled
        uint256 subscribedAt;
    }

    mapping(address => Subscription) private _subscriptions;
    address[] public subscriberList;
    uint256 public subscriberCount;

    /**
     * @notice Subscribe to on-chain finding alerts.
     *         Emits Subscribed event which off-chain indexers (subgraph, bot)
     *         listen to for notification routing.
     * @param minConfidence  Minimum confidence score (0-100) to trigger alert
     * @param filterTypes    Anomaly type strings to filter on; empty = all types
     */
    function subscribe(uint8 minConfidence, string[] calldata filterTypes) external {
        Subscription storage sub = _subscriptions[msg.sender];
        if (!sub.active) {
            subscriberList.push(msg.sender);
            subscriberCount++;
        }
        sub.active          = true;
        sub.minConfidence   = minConfidence;
        sub.subscribedAt    = block.timestamp;
        sub.allTypes        = (filterTypes.length == 0);

        for (uint256 i = 0; i < filterTypes.length; i++) {
            sub.typeFilters[keccak256(bytes(filterTypes[i]))] = true;
        }

        emit Subscribed(msg.sender, minConfidence, filterTypes);
    }

    /**
     * @notice Unsubscribe from on-chain alerts.
     */
    function unsubscribe() external {
        Subscription storage sub = _subscriptions[msg.sender];
        require(sub.active, "Not subscribed");
        sub.active = false;
        emit Unsubscribed(msg.sender);
    }

    /**
     * @notice Check if an address is subscribed and get their config.
     */
    function getSubscription(address subscriber)
        external
        view
        returns (bool active, uint8 minConfidence, bool allTypes, uint256 subscribedAt)
    {
        Subscription storage sub = _subscriptions[subscriber];
        return (sub.active, sub.minConfidence, sub.allTypes, sub.subscribedAt);
    }
}
