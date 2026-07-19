// ── P3-28 + P3-33: Ponder Indexer Config ────────────────────────────────────────
// Ponder indexes MantleIntelAudit events directly from Mantle RPC.
// No The Graph deployment needed — works on any EVM chain.
//
// Start: cd ponder && bun install && bun run dev
// GraphQL endpoint: http://localhost:42069/graphql

import { createConfig } from "@ponder/core";
import { http } from "viem";

import { MantleIntelAudit } from "../contracts/artifacts/contracts/src/MantleIntelAudit.sol/MantleIntelAudit.json";

export default createConfig({
  networks: {
    mantleSepolia: {
      chainId: 5003,
      transport: http(process.env.PONDER_RPC_URL_MANTLE_SEPOLIA || "https://rpc.sepolia.mantle.xyz"),
    },
    // Uncomment for mainnet:
    // mantleMainnet: {
    //   chainId: 5000,
    //   transport: http(process.env.PONDER_RPC_URL_MANTLE_MAINNET || "https://rpc.mantle.xyz"),
    // },
  },
  contracts: {
    MantleIntelAudit: {
      network: "mantleSepolia",
      abi: MantleIntelAudit.abi,
      address: "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b",
      startBlock: 39815592,
    },
  },
});
