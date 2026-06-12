// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AlertLog
 * @notice Immutable on-chain log of all alerts dispatched by Mantle Intel Agent.
 *         Telegram alerts, webhook triggers, and dashboard pushes are hashed
 *         and committed here for auditability.
 */
contract AlertLog {

    enum AlertChannel { TELEGRAM, WEBHOOK, DASHBOARD, EMAIL }
    enum AlertSeverity { LOW, MEDIUM, HIGH, CRITICAL }

    struct Alert {
        bytes32      alertHash;      // sha256 of alert payload
        AlertChannel channel;
        AlertSeverity severity;
        string       anomalyType;
        uint256      blockHeight;
        uint8        confidence;
        uint256      timestamp;
        address      dispatcher;
        bool         acknowledged;
    }

    Alert[]  public alerts;
    uint256  public alertCount;
    uint256  public criticalCount;
    address  public owner;

    mapping(address => bool) public authorizedAgents;

    // Subscriber registry — who gets alerts
    mapping(address => bool) public subscribers;
    address[] public subscriberList;

    event AlertDispatched(uint256 indexed alertId, AlertChannel channel, AlertSeverity severity, string anomalyType);
    event AlertAcknowledged(uint256 indexed alertId);
    event Subscribed(address indexed subscriber);
    event Unsubscribed(address indexed subscriber);

    modifier onlyOwnerOrAgent() {
        require(msg.sender == owner || authorizedAgents[msg.sender], "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedAgents[msg.sender] = true;
    }

    function authorizeAgent(address agent, bool status) external {
        require(msg.sender == owner, "Only owner");
        authorizedAgents[agent] = status;
    }

    function subscribe() external {
        if (!subscribers[msg.sender]) {
            subscribers[msg.sender] = true;
            subscriberList.push(msg.sender);
            emit Subscribed(msg.sender);
        }
    }

    function unsubscribe() external {
        subscribers[msg.sender] = false;
        emit Unsubscribed(msg.sender);
    }

    function dispatchAlert(
        bytes32      alertHash,
        AlertChannel channel,
        AlertSeverity severity,
        string calldata anomalyType,
        uint256      blockHeight,
        uint8        confidence
    ) external onlyOwnerOrAgent returns (uint256 alertId) {
        alertId = alertCount++;
        if (severity == AlertSeverity.CRITICAL) criticalCount++;
        alerts.push(Alert({
            alertHash:    alertHash,
            channel:      channel,
            severity:     severity,
            anomalyType:  anomalyType,
            blockHeight:  blockHeight,
            confidence:   confidence,
            timestamp:    block.timestamp,
            dispatcher:   msg.sender,
            acknowledged: false
        }));
        emit AlertDispatched(alertId, channel, severity, anomalyType);
    }

    function acknowledgeAlert(uint256 alertId) external onlyOwnerOrAgent {
        require(alertId < alertCount, "Invalid alertId");
        alerts[alertId].acknowledged = true;
        emit AlertAcknowledged(alertId);
    }

    function getAlerts(uint256 offset, uint256 limit) external view returns (Alert[] memory) {
        uint256 end = offset + limit > alertCount ? alertCount : offset + limit;
        Alert[] memory result = new Alert[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = alerts[i];
        }
        return result;
    }

    function getSubscriberCount() external view returns (uint256) {
        return subscriberList.length;
    }

    function getCriticalAlertRate() external view returns (uint256) {
        return alertCount > 0 ? (criticalCount * 100) / alertCount : 0;
    }
}
