# Mantle Intel Agent — Demo Video Script
**Target length: 90–120 seconds**  
**Hackathon: Find Evil! 2026 — Alpha & Data Track**

---

## What to record (step by step)

### [0:00–0:12] Hook — Open on the dashboard
- Open **https://mantle-intel-agent.vercel.app** in browser
- Let the live feed show for 3 seconds
- Narrate: *"This is Mantle Intel Agent — an autonomous AI system that monitors the Mantle network for anomalous wallet behavior and verifies every finding permanently on-chain."*

---

### [0:12–0:30] Show the pipeline running
- Open terminal and run:
  ```bash
  cd /home/user/mantle-intel-agent
  python3 main.py --demo --cycles 1
  ```
- Let it print findings to the terminal
- Narrate: *"Three Qwen AI models working together — Turbo for fast triage, Max for deep threat reasoning, Embedding for RAG runbook matching — detecting whale accumulation, smart money inflows, and anomalous patterns."*

---

### [0:30–0:50] On-chain audit proof
- Open **https://sepolia.mantlescan.xyz/address/0x03C88A1060626581854DB94e955a6be291782abb**
- Show the contract page and recent transactions
- Narrate: *"Every finding is written on-chain to our audit contract — immutable, timestamped, verifiable by anyone."*
- Click one transaction to show the data

---

### [0:50–1:05] Telegram bot live
- Open Telegram → **@MantleIntelAgentBot**
- Type `/start` — show welcome message
- Type `/latest` — show last findings
- Type `/status` — show pipeline stats
- Narrate: *"Real-time alerts via Telegram — /latest pulls the last five findings, /verify lets anyone confirm a hash on-chain."*

---

### [1:05–1:18] ERC-8004 Agent NFT
- Open **https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C**
- Show the contract
- Narrate: *"The agent has an on-chain identity — an ERC-8004 NFT encoding its capabilities, version, and audit contract link. Machine-verifiable provenance."*

---

### [1:18–1:30] Close on GitHub + dashboard
- Show **https://github.com/sodiq-code/mantle-intel-agent**
- End back on the live dashboard
- Narrate: *"Fully open-source. Production-ready architecture. Built on Mantle for the Find Evil! 2026 hackathon."*

---

## Recording tips
- Use OBS or Loom (free, browser-based)
- Keep terminal font large (18pt+)
- Record at 1080p
- Mute system sounds, use mic narration
- Loom link works fine for submission — no need to upload to YouTube

---

## Key URLs to show on screen
| What | URL |
|---|---|
| Live Dashboard | https://mantle-intel-agent.vercel.app |
| Audit Contract | https://sepolia.mantlescan.xyz/address/0x03C88A1060626581854DB94e955a6be291782abb |
| NFT Contract | https://sepolia.mantlescan.xyz/address/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C |
| Sourcify (Audit) | https://repo.sourcify.dev/contracts/full_match/5003/0x03C88A1060626581854DB94e955a6be291782abb/ |
| Sourcify (NFT) | https://repo.sourcify.dev/contracts/full_match/5003/0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C/ |
| GitHub | https://github.com/sodiq-code/mantle-intel-agent |
| Telegram Bot | https://t.me/MantleIntelAgentBot |
