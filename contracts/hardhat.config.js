require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  paths: {
    sources: "./src",
    artifacts: "./artifacts",
    cache: "./cache",
  },
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      evmVersion: "cancun"
    },
  },
  networks: {
    mantle_testnet: {
      url: process.env.MANTLE_TESTNET_RPC || "https://rpc.sepolia.mantle.xyz",
      chainId: 5003,
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
    },
    mantle_mainnet: {
      url: process.env.MANTLE_MAINNET_RPC || "https://rpc.mantle.xyz",
      chainId: 5000,
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
    },
  },
  sourcify: {
    enabled: true,
  },
  etherscan: {
    apiKey: {
      mantle_testnet: process.env.MANTLESCAN_API_KEY || "placeholder",
      mantle_mainnet: process.env.MANTLESCAN_API_KEY || "placeholder",
    },
    customChains: [
      {
        network: "mantle_testnet",
        chainId: 5003,
        urls: {
          apiURL: "https://api-sepolia.mantlescan.xyz/api",
          browserURL: "https://sepolia.mantlescan.xyz",
        },
      },
      {
        network: "mantle_mainnet",
        chainId: 5000,
        urls: {
          apiURL: "https://api.mantlescan.xyz/api",
          browserURL: "https://mantlescan.xyz",
        },
      },
    ],
  },
};
