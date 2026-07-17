export const config = { runtime: "edge" };

import { buildSnapshot, enforceAuthAndCors } from "./shared.js";

export default async function handler(req) {
  const auth = enforceAuthAndCors(req);
  if (!auth.ok) return auth.response;
  if (auth.preflight) return new Response(null, { status: 204, headers: auth.headers });

  const headers = { ...auth.headers, "Cache-Control": "no-store" };

  try {
    // Dashboard doesn't need protocol state? Let's check original. It did not have protocol state, but the return object was the same.
    // Original dashboard.js didn't fetch protocol_state. It passed false essentially.
    const snapshot = await buildSnapshot(false);
    return new Response(JSON.stringify(snapshot), {
      headers: { ...headers, "Content-Type": "application/json" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...headers, "Content-Type": "application/json" }
    });
  }
}
