// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

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

interface IERC721 {
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    function balanceOf(address owner) external view returns (uint256);
    function ownerOf(uint256 tokenId) external view returns (address);
    function transferFrom(address from, address to, uint256 tokenId) external;
    function approve(address to, uint256 tokenId) external;
    function getApproved(uint256 tokenId) external view returns (address);
    function setApprovalForAll(address operator, bool approved) external;
    function isApprovedForAll(address owner, address operator) external view returns (bool);
}

contract MantleIntelAgentNFT {

    // ── ERC-721 State ────────────────────────────────────────────────────────
    string public name     = "Mantle Intel Agent Identity";
    string public symbol   = "MIAI";
    uint256 public totalSupply;

    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => address) private _tokenApprovals;
    mapping(address => mapping(address => bool)) private _operatorApprovals;

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
    mapping(uint256 => string)        private _tokenURIs;

    address public owner;

    // Capability bitmask constants
    uint256 public constant CAP_ANOMALY_DETECTION  = 1;
    uint256 public constant CAP_SMART_MONEY        = 2;
    uint256 public constant CAP_LLM_INSIGHT        = 4;
    uint256 public constant CAP_ONCHAIN_AUDIT      = 8;
    uint256 public constant CAP_FULL_PIPELINE      = 15; // all four

    // ── Events ───────────────────────────────────────────────────────────────
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    event AgentMinted(uint256 indexed tokenId, string agentName, address auditContract);
    event AgentDeactivated(uint256 indexed tokenId);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

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
        uint256 tokenId = ++totalSupply;

        _owners[tokenId]   = to;
        _balances[to]     += 1;

        agentIdentities[tokenId] = AgentIdentity({
            agentName:       agentName,
            agentType:       agentType,
            version:         version,
            auditContract:   auditContract,
            capabilities:    capabilities,
            mintedAt:        block.timestamp,
            active:          true
        });

        _tokenURIs[tokenId] = tokenURI_;

        emit Transfer(address(0), to, tokenId);
        emit AgentMinted(tokenId, agentName, auditContract);

        return tokenId;
    }

    /**
     * @notice Query whether an agent has a specific capability.
     */
    function hasCapability(uint256 tokenId, uint256 capability) external view returns (bool) {
        return (agentIdentities[tokenId].capabilities & capability) != 0;
    }

    /**
     * @notice Get full agent identity.
     */
    function getAgentIdentity(uint256 tokenId) external view returns (AgentIdentity memory) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        return agentIdentities[tokenId];
    }

    function deactivateAgent(uint256 tokenId) external onlyOwner {
        agentIdentities[tokenId].active = false;
        emit AgentDeactivated(tokenId);
    }

    // ── ERC-721 Standard ────────────────────────────────────────────────────

    function balanceOf(address _owner) external view returns (uint256) {
        return _balances[_owner];
    }

    function ownerOf(uint256 tokenId) external view returns (address) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        return _owners[tokenId];
    }

    function tokenURI(uint256 tokenId) external view returns (string memory) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        return _tokenURIs[tokenId];
    }

    function approve(address to, uint256 tokenId) external {
        require(_owners[tokenId] == msg.sender, "Not owner");
        _tokenApprovals[tokenId] = to;
        emit Approval(msg.sender, to, tokenId);
    }

    function getApproved(uint256 tokenId) external view returns (address) {
        return _tokenApprovals[tokenId];
    }

    function setApprovalForAll(address operator, bool approved) external {
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    function isApprovedForAll(address _owner, address operator) external view returns (bool) {
        return _operatorApprovals[_owner][operator];
    }

    function transferFrom(address from, address to, uint256 tokenId) external {
        require(_owners[tokenId] == from, "Not owner");
        require(
            msg.sender == from ||
            _tokenApprovals[tokenId] == msg.sender ||
            _operatorApprovals[from][msg.sender],
            "Not authorized"
        );
        _balances[from] -= 1;
        _balances[to]   += 1;
        _owners[tokenId] = to;
        delete _tokenApprovals[tokenId];
        emit Transfer(from, to, tokenId);
    }
}
