export const config = { runtime: "edge" };

import { buildSnapshot, enforceAuthAndCors } from "./shared.js";

export default async function handler(req) {
  const url    = new URL(req.url);
  const stream = url.searchParams.get("stream") === "1";

  const auth = enforceAuthAndCors(req);
  if (!auth.ok) return auth.response;
  if (auth.preflight) return new Response(null, { status: 204, headers: auth.headers });

  const headers = { ...auth.headers, "Cache-Control": "no-store" };

  if (stream) {
    const encoder = new TextEncoder();
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();

    (async () => {
      try {
        for (let i = 0; i < 5; i++) {
          const snapshot = await buildSnapshot(true);
          const data = `data: ${JSON.stringify(snapshot)}\n\n`;
          await writer.write(encoder.encode(data));
          if (i < 4) await new Promise(r => setTimeout(r, 12000));
        }
      } catch(e) {
        const errData = `data: ${JSON.stringify({error: e.message})}\n\n`;
        await writer.write(encoder.encode(errData));
      } finally {
        await writer.close();
      }
    })();

    return new Response(readable, {
      headers: {
        ...headers,
        "Content-Type": "text/event-stream",
        "X-Accel-Buffering": "no",
      }
    });
  }

  try {
    const snapshot = await buildSnapshot(true);
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
