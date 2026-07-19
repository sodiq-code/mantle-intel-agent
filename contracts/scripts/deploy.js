/**
 * Mantle Intel Agent — Deploy Script v2.0
 * Deploys MantleIntelAudit to Mantle testnet OR mainnet.
 *
 * Usage:
 *   Testnet:  npx hardhat run scripts/deploy.js --network mantleTestnet
 *   Mainnet:  npx hardhat run scripts/deploy.js --network mantle
 *
 * Prerequisites (mainnet):
 *   1. Fund wallet 0x07c05a8dd22B097Da462e1010ed4Bcb299CC40f0 with ~0.01 MNT
 *      (get from https://faucet.mantle.xyz for testnet)
 *   2. Set DEPLOYER_PRIVATE_KEY in .env
 *   3. npx hardhat run scripts/deploy.js --network mantle
 *
 * Current Status:
 *   Testnet deployed: 0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b
 *   Mainnet: Ready to deploy — requires MNT for gas
 */

const hre = require("hardhat");
const fs  = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const networkName = hre.network.name;
  const isMainnet   = networkName === "mantle";

  console.log("════════════════════════════════════════════════════");
  console.log("  Mantle Intel Agent — Deploy MantleIntelAudit v2.0");
  console.log("════════════════════════════════════════════════════");
  console.log(`Network:   ${networkName} ${isMainnet ? "(MAINNET ⚠️)" : "(testnet)"}`);
  console.log(`Deployer:  ${deployer.address}`);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  const balEth  = hre.ethers.formatEther(balance);
  console.log(`Balance:   ${balEth} MNT`);

  if (parseFloat(balEth) < 0.001) {
    console.error("\n❌ INSUFFICIENT BALANCE");
    console.error("   Need at least 0.001 MNT for deployment.");
    if (isMainnet) {
      console.error("   Fund wallet: 0x07c05a8dd22B097Da462e1010ed4Bcb299CC40f0");
      console.error("   Bridge MNT: https://bridge.mantle.xyz");
    } else {
      console.error("   Testnet faucet: https://faucet.mantle.xyz");
    }
    process.exit(1);
  }

  if (isMainnet) {
    console.log("\n⚠️  MAINNET DEPLOYMENT — deploying in 5 seconds...");
    await new Promise(r => setTimeout(r, 5000));
  }

  console.log("\n📄 Deploying MantleIntelAudit v2.0...");
  const MantleIntelAudit = await hre.ethers.getContractFactory("MantleIntelAudit");
  const contract = await MantleIntelAudit.deploy();
  await contract.waitForDeployment();

  const address   = await contract.getAddress();
  const blockNum  = await hre.ethers.provider.getBlockNumber();
  const explorerBase = isMainnet
    ? "https://mantlescan.xyz"
    : "https://sepolia.mantlescan.xyz";

  console.log("\n✅ MantleIntelAudit v2.0 deployed!");
  console.log(`   Address: ${address}`);
  console.log(`   Block:   ${blockNum}`);
  console.log(`   Network: ${networkName}`);
  console.log(`   Explorer: ${explorerBase}/address/${address}`);

  // ── Save deployment info ──────────────────────────────────────────────────
  const deployInfo = {
    contractName:  "MantleIntelAudit",
    version:       "2.0",
    network:       networkName,
    chainId:       isMainnet ? 5000 : 5003,
    address:       address,
    deployer:      deployer.address,
    blockNumber:   blockNum,
    timestamp:     new Date().toISOString(),
    explorerUrl:   `${explorerBase}/address/${address}`,
    abi_path:      "artifacts/contracts/MantleIntelAudit.sol/MantleIntelAudit.json",
    features: [
      "recordFinding()",
      "verifyFinding()",
      "getPublicFindings() — public paginated feed",
      "getFindingsByType() — filter by anomaly type",
      "getStats() — public stats",
      "subscribe() — intel feed subscription",
    ],
  };

  const deployPath = path.join(__dirname, "..", "deployment.json");
  let allDeployments = {};
  if (fs.existsSync(deployPath)) {
    try {
      allDeployments = JSON.parse(fs.readFileSync(deployPath, "utf8"));
    } catch {}
  }
  allDeployments[networkName] = deployInfo;
  fs.writeFileSync(deployPath, JSON.stringify(allDeployments, null, 2));
  console.log(`\n📁 Deployment info saved to contracts/deployment.json`);

  // ── Update .env.example with new address ─────────────────────────────────
  const envKey = isMainnet ? "AUDIT_CONTRACT_MAINNET" : "AUDIT_CONTRACT_TESTNET";
  console.log(`\n🔧 Add to .env:`);
  console.log(`   ${envKey}=${address}`);

  // ── Verify instructions ───────────────────────────────────────────────────
  console.log(`\n📋 Next: Verify contract on explorer:`);
  console.log(`   npx hardhat verify --network ${networkName} ${address}`);
  console.log(`\n📋 Update agents/.env:`);
  console.log(`   ${envKey}=${address}`);
}

main().catch((error) => {
  console.error("\n❌ Deployment failed:", error.message);
  process.exitCode = 1;
});
