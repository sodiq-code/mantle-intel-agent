// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SignalRegistry
 * @notice On-chain registry for Mantle Intel Agent investment signals.
 *         Stores alpha signals derived from anomaly detection pipeline.
 * @dev Deployed on Mantle Sepolia — part of Mantle Intel Agent suite.
 */
contract SignalRegistry {

    struct Signal {
        bytes32 signalHash;
        string  signalType;    // "BUY" | "SELL" | "WATCH" | "EXIT"
        string  protocol;      // e.g. "mETH", "Merchant Moe", "Lendle"
        uint8   strength;      // 0–100
        uint256 blockHeight;
        uint256 timestamp;
        address recorder;
        bool    resolved;
        bool    correct;       // filled in after resolution
    }

    Signal[]   public signals;
    uint256    public signalCount;
    address    public owner;

    mapping(address => bool) public authorizedAgents;

    event SignalRecorded(uint256 indexed signalId, string signalType, string protocol, uint8 strength, uint256 blockHeight);
    event SignalResolved(uint256 indexed signalId, bool correct);
    event AgentAuthorized(address agent, bool status);

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
        emit AgentAuthorized(agent, status);
    }

    function recordSignal(
        bytes32 signalHash,
        string calldata signalType,
        string calldata protocol,
        uint8  strength,
        uint256 blockHeight
    ) external onlyOwnerOrAgent returns (uint256 signalId) {
        signalId = signalCount++;
        signals.push(Signal({
            signalHash:  signalHash,
            signalType:  signalType,
            protocol:    protocol,
            strength:    strength,
            blockHeight: blockHeight,
            timestamp:   block.timestamp,
            recorder:    msg.sender,
            resolved:    false,
            correct:     false
        }));
        emit SignalRecorded(signalId, signalType, protocol, strength, blockHeight);
    }

    function resolveSignal(uint256 signalId, bool correct) external onlyOwnerOrAgent {
        require(signalId < signalCount, "Invalid signalId");
        signals[signalId].resolved = true;
        signals[signalId].correct  = correct;
        emit SignalResolved(signalId, correct);
    }

    function getSignals(uint256 offset, uint256 limit) external view returns (Signal[] memory) {
        uint256 end = offset + limit > signalCount ? signalCount : offset + limit;
        Signal[] memory result = new Signal[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = signals[i];
        }
        return result;
    }

    function getAccuracy() external view returns (uint256 resolved, uint256 correct, uint256 accuracyPct) {
        for (uint256 i = 0; i < signalCount; i++) {
            if (signals[i].resolved) {
                resolved++;
                if (signals[i].correct) correct++;
            }
        }
        accuracyPct = resolved > 0 ? (correct * 100) / resolved : 0;
    }
}
