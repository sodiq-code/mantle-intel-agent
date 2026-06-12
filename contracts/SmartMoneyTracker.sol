// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SmartMoneyTracker
 * @notice On-chain ledger of tracked smart money wallets and their activity.
 *         Mantle Intel Agent registers wallets and logs flow events here.
 */
contract SmartMoneyTracker {

    enum WalletTier { UNKNOWN, TIER3, TIER2, TIER1 }
    enum WalletType { UNKNOWN, CEX, MEV, WHALE, FOUNDATION, PROTOCOL, BRIDGE }

    struct TrackedWallet {
        address wallet;
        string  label;
        WalletTier tier;
        WalletType walletType;
        uint256 registeredAt;
        uint256 lastSeenBlock;
        uint256 alertCount;
        bool    active;
    }

    struct FlowEvent {
        address wallet;
        uint256 blockHeight;
        uint256 valueMnt;      // in wei (18 decimals)
        string  direction;     // "IN" | "OUT"
        string  anomalyType;
        uint8   confidence;
        uint256 timestamp;
    }

    mapping(address => TrackedWallet) public wallets;
    address[]  public walletList;
    FlowEvent[] public flowEvents;

    uint256 public walletCount;
    uint256 public flowEventCount;
    address public owner;

    mapping(address => bool) public authorizedAgents;

    event WalletRegistered(address indexed wallet, string label, WalletTier tier);
    event FlowEventLogged(address indexed wallet, uint256 blockHeight, string direction, uint256 valueMnt);

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

    function registerWallet(
        address wallet,
        string calldata label,
        WalletTier tier,
        WalletType walletType
    ) external onlyOwnerOrAgent {
        if (!wallets[wallet].active) {
            walletList.push(wallet);
            walletCount++;
        }
        wallets[wallet] = TrackedWallet({
            wallet:          wallet,
            label:           label,
            tier:            tier,
            walletType:      walletType,
            registeredAt:    block.timestamp,
            lastSeenBlock:   block.number,
            alertCount:      wallets[wallet].alertCount,
            active:          true
        });
        emit WalletRegistered(wallet, label, tier);
    }

    function logFlowEvent(
        address wallet,
        uint256 blockHeight,
        uint256 valueMnt,
        string calldata direction,
        string calldata anomalyType,
        uint8  confidence
    ) external onlyOwnerOrAgent {
        flowEvents.push(FlowEvent({
            wallet:      wallet,
            blockHeight: blockHeight,
            valueMnt:    valueMnt,
            direction:   direction,
            anomalyType: anomalyType,
            confidence:  confidence,
            timestamp:   block.timestamp
        }));
        flowEventCount++;
        wallets[wallet].lastSeenBlock = blockHeight;
        wallets[wallet].alertCount++;
        emit FlowEventLogged(wallet, blockHeight, direction, valueMnt);
    }

    function getFlowEvents(uint256 offset, uint256 limit) external view returns (FlowEvent[] memory) {
        uint256 end = offset + limit > flowEventCount ? flowEventCount : offset + limit;
        FlowEvent[] memory result = new FlowEvent[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = flowEvents[i];
        }
        return result;
    }

    function getTopTier1Wallets() external view returns (address[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < walletList.length; i++) {
            if (wallets[walletList[i]].tier == WalletTier.TIER1) count++;
        }
        address[] memory result = new address[](count);
        uint256 idx = 0;
        for (uint256 i = 0; i < walletList.length; i++) {
            if (wallets[walletList[i]].tier == WalletTier.TIER1) {
                result[idx++] = walletList[i];
            }
        }
        return result;
    }
}
