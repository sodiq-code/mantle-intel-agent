const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

const NFT_ADDRESS = "0xa1A134f27b72140eAf61Da2c52632735a328742f";

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Minting with:", deployer.address);

  const NFT = await hre.ethers.getContractFactory("MantleIntelAgentNFT");
  const nft = NFT.attach(NFT_ADDRESS);

  const auditContract = process.env.AUDIT_CONTRACT_ADDRESS || "0x03C88A1060626581854DB94e955a6be291782abb";

  const tx = await nft.mintAgentIdentity(
    deployer.address,
    "Mantle Intel Agent",
    "anomaly_detector",
    "1.0.0",
    auditContract,
    7,
    "https://mantle-intel-agent.vercel.app/api/nft/1"
  );

  console.log("Mint tx sent:", tx.hash);
  const receipt = await tx.wait();
  console.log("Minted! Block:", receipt.blockNumber);

  // Update deployment.json
  const deploymentPath = path.join(__dirname, "../deployment.json");
  let deployment = {};
  if (fs.existsSync(deploymentPath)) {
    deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  }
  deployment["mantle_testnet"] = deployment["mantle_testnet"] || {};
  deployment["mantle_testnet"].MantleIntelAgentNFT = NFT_ADDRESS;
  deployment["mantle_testnet"].MantleIntelAgentNFT_mintTx = tx.hash;
  deployment["mantle_testnet"].MantleIntelAgentNFT_block = receipt.blockNumber;

  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2));
  console.log("deployment.json updated:", deploymentPath);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
