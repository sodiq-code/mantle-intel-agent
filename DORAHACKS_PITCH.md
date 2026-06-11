# DoraHacks BUIDL Submission — Mantle Intel Agent

## Project Name
Mantle Intel Agent

## Tagline
Autonomous AI ops agent for Mantle — on-chain anomaly detection, smart-money threat analysis, and immutable audit logs powered by Qwen.

## Track
Alpha & Data (Mirana Ventures) — The Turing Test Hackathon 2026

---

## What It Does

Mantle Intel Agent is a production-grade autonomous AI system that monitors the Mantle network for anomalous wallet behavior, smart-money movements, and potential threats — writing every finding permanently on-chain.

**Three-layer intelligence stack:**
- **Qwen-Max** — deep anomaly reasoning, full threat report generation
- **Qwen-Turbo** — 50ms fast triage to filter noise from signal  
- **Qwen-Embedding** — semantic RAG search over 500+ indexed runbooks to match patterns against known threat playbooks

**What it detects:**
- Unusual transfer velocity / large value movements
- Smart-money wallet clustering
- Contract interaction anomalies
- Cross-chain bridge abuse patterns

---

## How It Works

1. **Ingest** — Agent polls Mantle RPC + Splunk MCP for real-time transaction data
2. **Triage** — Qwen-Turbo scores each wallet/transaction (< 50ms)
3. **Analyze** — High-priority targets get deep Qwen-Max analysis + RAG runbook lookup
4. **Record** — Finding (severity, confidence, MITRE tactic, IPFS report hash) is written to `MantleIntelAudit` contract via `recordFinding()`
5. **Surface** — Live dashboard at `mantle-intel-agent.vercel.app` shows all findings

---

## On-Chain Contracts (Mantle Sepolia)

| Contract | Address | Sourcify |
|---|---|---|
| MantleIntelAudit | `0x03C88A1060626581854DB94e955a6be291782abb` | [Verified ✓](https://repo.sourcify.dev/contracts/full_match/5003/0x03C88A1060626581854DB94e955a6be291782abb/) |
| MantleIntelAgentNFT (ERC-8004) | `0xa1A134f27b72140eAf61Da2c52632735a328742f` | [Verified ✓](https://repo.sourcify.dev/contracts/full_match/5003/0xa1A134f27b72140eAf61Da2c52632735a328742f/) |

**ERC-8004 Agent NFT:** Token ID 1 minted to deployer — encodes `agentType: anomaly_detector`, `capabilities: 7 (detect|report|audit)`, linked to audit contract. Enables trustless agent-to-agent composition on Mantle.

---

## Tech Stack

| Layer | Tech |
|---|---|
| AI Models | Qwen-Max, Qwen-Turbo, Qwen-Embedding (Alibaba Cloud) |
| Chain | Mantle Network (Sepolia testnet) |
| Smart Contracts | Solidity 0.8.20, Hardhat, Sourcify |
| Agent Runtime | Python, LangChain-style pipeline |
| Observability | Splunk MCP integration |
| Frontend | Next.js, Vercel |
| NFT Standard | ERC-8004 (Agent Identity extension of ERC-721) |

---

## Links

- **GitHub:** https://github.com/sodiq-code/mantle-intel-agent
- **Live Dashboard:** https://mantle-intel-agent.vercel.app
- **Audit Contract (Sourcify):** https://repo.sourcify.dev/contracts/full_match/5003/0x03C88A1060626581854DB94e955a6be291782abb/
- **NFT Contract (Sourcify):** https://repo.sourcify.dev/contracts/full_match/5003/0xa1A134f27b72140eAf61Da2c52632735a328742f/
- **Mantle Explorer:** https://sepolia.explorer.mantle.xyz/address/0x03C88A1060626581854DB94e955a6be291782abb

---

## Why Mantle

Mantle's low-fee, high-throughput L2 makes on-chain audit logs economically viable — every `recordFinding()` call costs < $0.001. That's the only way an agent can write thousands of findings per day without burning the treasury. The ERC-8004 NFT also demonstrates Mantle as a credible substrate for agentic identity primitives.

---

## What's Next

- Mainnet deployment (wallet being funded)
- Telegram bot alert channel (@MantleIntelBot)
- Multi-chain support (Base, Arbitrum feeding into same audit contract pattern)
- Agent marketplace using ERC-8004 identity NFTs

---

## Team

**Kudirat Oyindamola** — Platform Engineer  
Specializing in autonomous agent systems, on-chain observability, and AI-powered DevSecOps.

GitHub: https://github.com/sodiq-code

---

*Submitted to The Turing Test Hackathon 2026 — Alpha & Data track (Mirana Ventures)*
