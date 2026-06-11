const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying MantleIntelAudit with account:", deployer.address);
  console.log("Network:", hre.network.name);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "MNT");

  const MantleIntelAudit = await hre.ethers.getContractFactory("MantleIntelAudit");
  const contract = await MantleIntelAudit.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("\n✅ MantleIntelAudit deployed to:", address);
  console.log("Network:", hre.network.name);
  console.log("Block:", await hre.ethers.provider.getBlockNumber());

  // Save deployment info
  const fs = require("fs");
  const deployInfo = {
    network: hre.network.name,
    address: address,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    abi_path: "artifacts/contracts/MantleIntelAudit.sol/MantleIntelAudit.json",
  };
  fs.writeFileSync("deployment.json", JSON.stringify(deployInfo, null, 2));
  console.log("\nDeployment info saved to deployment.json");
  console.log("\nNext step — verify contract:");
  console.log(`npx hardhat verify --network ${hre.network.name} ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
