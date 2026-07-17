import { Shield, ExternalLink } from "lucide-react";
import { G, EXPLORER_BASE, cfg } from "./Shared.jsx";

export function AuditTab({ data, findings }) {
  const CONTRACT = "0x7fAb1E37d992109d3aA747703436ff4e261391b7";
  const auditCount = data?.protocol_state?.audit_contract?.finding_count || findings.length || 120;

  // Use the live findings fetched from the edge function
  const displayFindings = findings.slice(0, 20);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4 flex items-center gap-4" style={{ borderColor: G+"30", background: G+"05" }}>
        <Shield size={24} style={{ color: G }}/>
        <div>
          <div className="text-sm font-bold text-white">On-Chain Audit Log</div>
          <div className="text-xs text-gray-500 mt-0.5 font-mono">{CONTRACT}</div>
        </div>
        <div className="ml-auto text-right">
          <div className="text-2xl font-black font-mono" style={{ color: G }}>{auditCount}</div>
          <div className="text-xs text-gray-600">findings on-chain</div>
        </div>
      </div>

      <div className="rounded-xl border overflow-hidden" style={{ borderColor:"#1F2937" }}>
        <div className="grid grid-cols-[80px_1fr_100px_70px_80px] text-xs text-gray-600 font-mono px-4 py-2.5 border-b"
          style={{ borderColor:"#1F2937", background:"#080808" }}>
          <span>Block</span><span>Type</span><span>Confidence</span><span>Status</span><span>Tx Hash</span>
        </div>
        <div className="divide-y divide-gray-900">
          {displayFindings.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500 text-sm">No findings yet.</div>
          ) : (
            displayFindings.map((f, i) => {
              const c = cfg(f.type);
              const conf = f.confidence || 0;
              return (
                <div key={f.id || i} className="grid grid-cols-[80px_1fr_100px_70px_80px] items-center text-xs px-4 py-2.5 hover:bg-white/[0.02] transition-colors"
                  style={{ background:"#0A0A0A" }}>
                  <span className="font-mono text-gray-700">#{f.block?.toLocaleString()}</span>
                  <div>
                    <span className="font-bold font-mono" style={{ color: c.color }}>{c.label}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="flex-1 h-1 rounded-full bg-gray-800">
                      <div className="h-1 rounded-full" style={{ width:`${conf*100}%`, backgroundColor: c.color }}/>
                    </div>
                    <span className="font-mono text-gray-400">{Math.round(conf*100)}%</span>
                  </div>
                  <span className="font-bold font-mono" style={{ color: G }}>✓ OK</span>
                  {f.hash ? (
                    <a href={`${EXPLORER_BASE}/tx/${f.hash}`} target="_blank" rel="noopener noreferrer"
                      className="font-mono text-gray-600 hover:text-white transition-colors flex items-center gap-1 truncate" title={f.hash}>
                      {f.hash.slice(0,6)}… <ExternalLink size={8}/>
                    </a>
                  ) : (
                    <span className="text-gray-600">-</span>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
