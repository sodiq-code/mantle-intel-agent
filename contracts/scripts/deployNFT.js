const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying MantleIntelAgentNFT with:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "MNT");

  // Deploy
  const NFT = await hre.ethers.getContractFactory("MantleIntelAgentNFT");
  const nft = await NFT.deploy();
  await nft.waitForDeployment();

  const address = await nft.getAddress();
  console.log("MantleIntelAgentNFT deployed to:", address);

  // Mint token ID 1 to deployer
  const auditContract = process.env.AUDIT_CONTRACT_ADDRESS || "0x03C88A1060626581854DB94e955a6be291782abb";
  const tx = await nft.mintAgentIdentity(
    deployer.address,         // to
    "Mantle Intel Agent",     // agentName
    "anomaly_detector",       // agentType
    "1.0.0",                  // version
    auditContract,            // auditContract address
    7,                        // capabilities bitmask: 0b111 = detect + report + audit
    "https://mantle-intel-agent.vercel.app/api/nft/1" // tokenURI
  );
  await tx.wait();
  console.log("Minted Agent NFT token ID 1 to:", deployer.address);
  console.log("Mint tx:", tx.hash);

  // Update deployment.json
  const deploymentPath = path.join(__dirname, "../deployment.json");
  let deployment = {};
  if (fs.existsSync(deploymentPath)) {
    deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  }

  const network = hre.network.name;
  deployment[network] = deployment[network] || {};
  deployment[network].MantleIntelAgentNFT = address;
  deployment[network].MantleIntelAgentNFT_mintTx = tx.hash;

  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2));
  console.log("deployment.json updated");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
