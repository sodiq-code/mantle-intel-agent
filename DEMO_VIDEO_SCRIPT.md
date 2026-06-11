# Mantle Intel Agent — Demo Video Script
**Target length:** 2 minutes  
**Format:** Screen recording + voiceover  
**Audience:** Hackathon judges (Find Evil! 2026 — Alpha & Data track)

---

## Scene 1 — Hook (0:00–0:15)
**Screen:** Live dashboard at `https://mantle-intel-agent.vercel.app`  
**Voiceover:**
> "On-chain data is noisy. Wallets move millions in seconds — and most anomaly tools miss it. Mantle Intel Agent is an autonomous AI ops system that watches the Mantle network in real time, detects smart-money threats, and writes every finding directly on-chain."

---

## Scene 2 — Architecture Overview (0:15–0:35)
**Screen:** Show `README.md` architecture diagram or draw.io screenshot  
**Voiceover:**
> "The system runs a 3-layer intelligence stack: Qwen-Max for deep anomaly reasoning, Qwen-Turbo for fast triage, and Qwen-Embedding for semantic search across 500+ indexed runbooks. It connects to Mantle RPC, Splunk MCP, and a Hardhat-deployed audit contract — all on Mantle Sepolia."

**Show:** `agent/agent.py` open in editor — highlight the three model calls

---

## Scene 3 — Live Agent Run (0:35–1:10)
**Screen:** Terminal — run the agent against a known suspicious wallet  
```bash
cd /home/user/mantle-intel-agent
python agent/agent.py --wallet 0xSUSPICIOUS --chain mantle_testnet
```
**Voiceover:**
> "Watch the agent work. First, Qwen-Turbo does a 50ms triage — is this wallet worth investigating? Yes. Qwen-Max then deep-dives: cross-referencing transfer patterns, contract interactions, and historical velocity. It generates a structured threat report — severity, confidence score, MITRE-style tactic label."

**Show:** JSON output with `severity: HIGH`, `confidence: 0.91`, `tactic: "TA0010 Exfiltration"`

---

## Scene 4 — On-Chain Audit Log (1:10–1:35)
**Screen:** Mantle Sepolia explorer — open contract `0x03C88A1060626581854DB94e955a6be291782abb`  
**URL:** `https://sepolia.explorer.mantle.xyz/address/0x03C88A1060626581854DB94e955a6be291782abb`

**Voiceover:**
> "Every finding is immutable. The agent calls `recordFinding()` — writing the wallet address, severity, IPFS hash of the full report, and timestamp directly to the MantleIntelAudit contract. No backend. No trust required."

**Show:** A `FindingRecorded` event in the explorer — click into it, show the decoded parameters.

**Then switch to:** Sourcify verification page  
`https://repo.sourcify.dev/contracts/full_match/5003/0x03C88A1060626581854DB94e955a6be291782abb/`

> "And it's fully verified — open source, auditable."

---

## Scene 5 — ERC-8004 Agent NFT (1:35–1:50)
**Screen:** Sourcify page for NFT contract  
`https://repo.sourcify.dev/contracts/full_match/5003/0xa1A134f27b72140eAf61Da2c52632735a328742f/`

**Voiceover:**
> "The agent also has an on-chain identity — an ERC-8004 Agent NFT. Token ID 1 encodes the agent's type, capabilities bitmask, and a pointer to its audit contract. This is the foundation for trustless agent-to-agent composition on Mantle."

**Show:** `agentIdentities[1]` call result in explorer showing `agentType: anomaly_detector`, `capabilities: 7`

---

## Scene 6 — Dashboard (1:50–2:00)
**Screen:** Live dashboard `https://mantle-intel-agent.vercel.app`  
**Voiceover:**
> "All findings surface in the live dashboard — searchable, filterable, real-time. Built on Mantle. Autonomous. Open source."

**End card:**
- GitHub: `github.com/sodiq-code/mantle-intel-agent`
- Contract: `0x03C88A1060626581854DB94e955a6be291782abb`
- NFT: `0xa1A134f27b72140eAf61Da2c52632735a328742f`
- Dashboard: `mantle-intel-agent.vercel.app`

---

## Recording Tips
- Use OBS or Loom for screen + mic capture
- Record at 1920×1080
- Keep terminal font size large (18pt+) so judges can read
- Pause 1–2s on each contract address so it's readable
- No background music needed — clean narration is more professional
- Export as MP4, upload to YouTube (unlisted) or Loom link for DoraHacks submission
