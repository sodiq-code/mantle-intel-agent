import { useState } from "react";
import { G } from "./Shared.jsx";

export function APITab({ data, contract }) {
  const [copied, setCopied] = useState("");
  const copy = (text, key) => {
    navigator.clipboard.writeText(text).then(() => { setCopied(key); setTimeout(()=>setCopied(""),1500); });
  };

  const snippets = [
    {
      title: "Fetch Live Findings",
      lang: "js",
      code: `const res = await fetch("https://mantle-intel-agent.vercel.app/api/live-feed?format=json");
const { latest_findings, stats } = await res.json();
console.log(\`\${latest_findings.length} anomalies · \${stats.avg_confidence * 100}% avg conf\`);`,
    },
    {
      title: "On-Chain findingCount()",
      lang: "js",
      code: `import { ethers } from "ethers";
const provider = new ethers.JsonRpcProvider("https://rpc.sepolia.mantle.xyz");
const audit = new ethers.Contract(
  "0x7fAb1E37d992109d3aA747703436ff4e261391b7",
  ["function findingCount() view returns(uint256)"],
  provider
);
const count = await audit.findingCount(); // → 120 (live findings)`,
    },
  ];

  const endpoints = [
    { method:"GET",  path:"/api/live-feed?format=json", desc:"JSON snapshot of live findings, stats, protocol state" },
    { method:"GET",  path:"/api/live-feed?stream=1",    desc:"Server-Sent Events stream (12s intervals)" },
    { method:"VIEW", path:"findingCount()",              desc:"On-chain finding count — 120 confirmed on-chain" },
    { method:"VIEW", path:"getPublicFindings(0,120)",     desc:"Paginated findings from audit contract" },
  ];

  return (
    <div className="space-y-4">
      {endpoints.map(({ method, path, desc }) => (
        <div key={path} className="flex items-center gap-3 p-3 rounded-xl border text-xs"
          style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <span className="font-bold font-mono px-2 py-0.5 rounded text-xs"
            style={{ backgroundColor: method==="GET" ? G+"20" : "#3B82F620", color: method==="GET" ? G : "#3B82F6" }}>
            {method}
          </span>
          <span className="font-mono text-white flex-1">{path}</span>
          <span className="text-gray-600 hidden sm:block">{desc}</span>
        </div>
      ))}

      {snippets.map(({ title, lang, code }) => (
        <div key={title} className="rounded-xl border overflow-hidden" style={{ borderColor:"#1F2937" }}>
          <div className="flex items-center justify-between px-4 py-2.5 border-b"
            style={{ borderColor:"#1F2937", background:"#080808" }}>
            <span className="text-xs font-bold text-gray-400">{title}</span>
            <button onClick={() => copy(code, title)}
              className="text-xs px-2 py-0.5 rounded font-mono transition-colors"
              style={{ color: copied===title ? G : "#6B7280", border:`1px solid ${copied===title ? G+"40":"#374151"}` }}>
              {copied===title ? "copied!" : "copy"}
            </button>
          </div>
          <pre className="p-4 text-xs font-mono text-gray-300 overflow-x-auto leading-relaxed"
            style={{ background:"#050505" }}>
            <code>{code}</code>
          </pre>
        </div>
      ))}
    </div>
  );
}
