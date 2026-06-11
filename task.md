# Mantle Intel Agent — Deployment Tracker
Last updated: 2026-06-11

## STATUS

### ✅ DONE
- [x] All agents written + working (demo mode)
- [x] backtest/results.md populated (Recall 100%, Precision 40%, F1 0.57)
- [x] dashboard/index.html fixed (removed CDN Tailwind script)
- [x] dashboard built → dist/ ✅
- [x] contracts/package.json created
- [x] contracts compiled (MantleIntelAudit.sol) ✅
- [x] contracts/.env written with DEPLOYER_PRIVATE_KEY
- [x] Git initialized, committed, pushed → https://github.com/sodiq-code/mantle-intel-agent ✅

### ⏳ BLOCKED
- [ ] Contract deploy (wallet address: 0x07c05a8dd22B097Da462e1010ed4Bcb299CC40f0, needs testnet MNT)
  → All automated faucets require wallet connect/social auth
  → User must fund manually: https://faucet.quicknode.com/mantle/sepolia OR https://faucet.mantle.xyz
  → After funding, run: `cd contracts && npx hardhat run scripts/deploy.js --network mantle_testnet`

### ⏳ TODO (after deploy)
- [ ] Update README.md contract address table (replace TBD)
- [ ] Deploy dashboard to Vercel (connect GitHub, set root dir = dashboard/, build = npm run build, output = dist)
- [ ] Submit DoraHacks BUIDL: https://dorahacks.io/hackathon/mantle-network-hackathon/buidl
- [ ] Record 2min demo video

## DEPLOYER WALLET
- Address: 0x07c05a8dd22B097Da462e1010ed4Bcb299CC40f0
- Private key stored in: contracts/.env (DEPLOYER_PRIVATE_KEY)

## GITHUB
- Repo: https://github.com/sodiq-code/mantle-intel-agent
- Branch: main
- Status: pushed ✅

## DASHBOARD
- Built: dashboard/dist/ ✅  
- Deploy target: Vercel
  - Root dir: dashboard
  - Build cmd: npm run build
  - Output dir: dist
  - Framework: Vite

## CONTRACT
- File: contracts/src/MantleIntelAudit.sol
- Compiled: ✅
- Deployed testnet: ❌ (needs MNT)
- Deployed mainnet: ❌
