const hre = require("hardhat");
const fs  = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployer:", deployer.address);
  const bal = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(bal), "MNT");

  const NFT = await hre.ethers.getContractFactory("MantleIntelAgentNFT");
  console.log("Deploying MantleIntelAgentNFT...");
  const nft = await NFT.deploy();
  await nft.waitForDeployment();
  const addr = await nft.getAddress();
  console.log("MantleIntelAgentNFT deployed to:", addr);

  // Mint Agent NFT #1
  const auditContract = process.env.AUDIT_CONTRACT_ADDRESS || "0x7fAb1E37d992109d3aA747703436ff4e261391b7";
  console.log("Minting Agent NFT #1 to", deployer.address, "...");
  const tx = await nft.mintAgentIdentity(
    deployer.address,
    "Mantle Intel Agent",
    "INTEL_AGENT",
    "1.0.0",
    auditContract,
    7,
    "ipfs://mantle-intel-agent-metadata"
  );
  await tx.wait();
  console.log("Minted! TX:", tx.hash);

  // Save deployment
  const depFile = path.join(__dirname, "../deployment.json");
  let dep = {};
  if (fs.existsSync(depFile)) dep = JSON.parse(fs.readFileSync(depFile, "utf8"));
  dep.nft_testnet = {
    address: addr,
    network: "mantle_sepolia",
    chainId: 5003,
    deployer: deployer.address,
    mintTx: tx.hash,
    deployedAt: new Date().toISOString()
  };
  fs.writeFileSync(depFile, JSON.stringify(dep, null, 2));
  console.log("Saved to deployment.json");
  console.log("\nNFT Contract:", addr);
  console.log("Explorer:", `https://sepolia.mantlescan.xyz/address/${addr}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
