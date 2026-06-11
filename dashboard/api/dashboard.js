/**
 * Mantle Intel Agent — Dashboard API (Vercel Edge Function)
 * Proxies /api/dashboard → live data from Mantle RPC.
 * This replaces the static dashboard.json approach.
 */
export { default, config } from "./live-feed.js";
