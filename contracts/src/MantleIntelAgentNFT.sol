// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MantleIntelAgentNFT
 * @notice ERC-8004 Agent Identity NFT for Mantle Intel Agent.
 *         Represents a registered autonomous AI agent on-chain.
 *         Each NFT encodes the agent's capabilities, audit contract,
 *         and verifiable identity — enabling trustless agent-to-agent composition.
 *
 * @dev ERC-8004 extends ERC-721 with agent-specific metadata:
 *      - agentType: classifier (e.g. "anomaly_detector", "smart_money_tracker")
 *      - capabilities: bitmask of agent abilities
 *      - auditContract: address of the agent's on-chain audit log
 *      - version: semantic version string
 */
contract MantleIntelAgentNFT is ERC721URIStorage, Ownable {

    uint256 public totalSupply;

    // ── ERC-8004 Agent Metadata ──────────────────────────────────────────────
    struct AgentIdentity {
        string  agentName;          // "Mantle Intel Agent v1.0"
        string  agentType;          // "multi_agent_pipeline"
        string  version;            // "1.0.0"
        address auditContract;      // MantleIntelAudit.sol address
        uint256 capabilities;       // bitmask: 1=anomaly, 2=smartmoney, 4=insight, 8=audit
        uint256 mintedAt;
        bool    active;
    }

    mapping(uint256 => AgentIdentity) public agentIdentities;

    // Capability bitmask constants
    uint256 public constant CAP_ANOMALY_DETECTION  = 1;
    uint256 public constant CAP_SMART_MONEY        = 2;
    uint256 public constant CAP_LLM_INSIGHT        = 4;
    uint256 public constant CAP_ONCHAIN_AUDIT      = 8;
    uint256 public constant CAP_FULL_PIPELINE      = 15; // all four

    // ── Events ───────────────────────────────────────────────────────────────
    event AgentMinted(uint256 indexed tokenId, string agentName, address auditContract);
    event AgentDeactivated(uint256 indexed tokenId);

    constructor() ERC721("Mantle Intel Agent Identity", "MIAI") Ownable(msg.sender) {}

    // ── ERC-8004 Core ────────────────────────────────────────────────────────

    /**
     * @notice Mint an agent identity NFT.
     * @param to            Recipient (agent operator wallet)
     * @param agentName     Human-readable agent name
     * @param agentType     Agent classifier string
     * @param version       Semantic version
     * @param auditContract Address of MantleIntelAudit contract
     * @param capabilities  Bitmask of agent capabilities
     * @param tokenURI_     Metadata URI (IPFS or data URI)
     */
    function mintAgentIdentity(
        address to,
        string calldata agentName,
        string calldata agentType,
        string calldata version,
        address auditContract,
        uint256 capabilities,
        string calldata tokenURI_
    ) external onlyOwner returns (uint256) {
        totalSupply++;
        uint256 tokenId = totalSupply;

        agentIdentities[tokenId] = AgentIdentity({
            agentName:       agentName,
            agentType:       agentType,
            version:         version,
            auditContract:   auditContract,
            capabilities:    capabilities,
            mintedAt:        block.timestamp,
            active:          true
        });

        _mint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);

        emit AgentMinted(tokenId, agentName, auditContract);

        return tokenId;
    }

    /**
     * @notice Query whether an agent has a specific capability.
     */
    function hasCapability(uint256 tokenId, uint256 capability) external view returns (bool) {
        _requireOwned(tokenId);
        return (agentIdentities[tokenId].capabilities & capability) != 0;
    }

    /**
     * @notice Get full agent identity.
     */
    function getAgentIdentity(uint256 tokenId) external view returns (AgentIdentity memory) {
        _requireOwned(tokenId);
        return agentIdentities[tokenId];
    }

    function deactivateAgent(uint256 tokenId) external onlyOwner {
        _requireOwned(tokenId);
        agentIdentities[tokenId].active = false;
        emit AgentDeactivated(tokenId);
    }
}
