import { useState, useMemo } from "react";
import { TrendingUp, ChevronLeft, ChevronRight, ArrowUpDown, ChevronUp, ChevronDown } from "lucide-react";
import { G, cfg, ConfRing } from "./Shared.jsx";

const PAGE_SIZE = 6;

const ACTION = {
  whale_accumulation:   { action:"ACCUMULATE", color:"#00D395", reason:"Institutional accumulation pattern detected." },
  smart_money_inflow:   { action:"LONG",       color:"#3B82F6", reason:"Smart money coordinated entry signal." },
  value_spike:          { action:"WATCH",      color:"#EAB308", reason:"Abnormal value concentration — monitor exit." },
  multivariate_anomaly: { action:"HEDGE",      color:"#EF4444", reason:"Multi-method anomaly — reduce exposure." },
};

export function SignalsTab({ findings }) {
  const [sortBy, setSortBy] = useState("confidence");
  const [sortDir, setSortDir] = useState("desc");
  const [page, setPage] = useState(0);

  const signals = useMemo(() =>
    findings.filter(f =>
      ["whale_accumulation","smart_money_inflow","value_spike","multivariate_anomaly"].includes(f.type)
    ),
  [findings]);

  const sorted = useMemo(() => {
    const out = [...signals];
    out.sort((a, b) => {
      let va, vb;
      switch (sortBy) {
        case "confidence": va = a.confidence || 0; vb = b.confidence || 0; break;
        case "block":      va = a.block || 0;      vb = b.block || 0;      break;
        case "type":       va = a.type || "";      vb = b.type || "";      break;
        case "action":     va = ACTION[a.type]?.action || ""; vb = ACTION[b.type]?.action || ""; break;
        default:           va = a.confidence || 0; vb = b.confidence || 0;
      }
      if (typeof va === "string") return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      return sortDir === "asc" ? va - vb : vb - va;
    });
    return out;
  }, [signals, sortBy, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const paged = sorted.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  const toggleSort = (col) => {
    if (sortBy === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortBy(col); setSortDir("desc"); }
    setPage(0);
  };

  const headers = [
    { key: "action",     label: "Action" },
    { key: "type",       label: "Signal" },
    { key: "block",      label: "Block" },
    { key: "confidence", label: "Conf" },
  ];

  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={14} style={{ color: G }}/>
        <span className="text-sm font-bold text-white">Alpha Signals</span>
        <span className="text-xs px-2 py-0.5 rounded-full font-mono ml-auto"
          style={{ color: G, backgroundColor: G + "15", border: `1px solid ${G}30` }}>
          {signals.length} active
        </span>
      </div>

      {/* Sort controls */}
      <div className="flex items-center gap-2 text-xs font-mono">
        <span className="text-gray-700">Sort:</span>
        {headers.map(h => (
          <button key={h.key} onClick={() => toggleSort(h.key)}
            className="flex items-center gap-1 px-2 py-1 rounded transition-colors hover:bg-white/5"
            style={{ color: sortBy === h.key ? G : "#6B7280" }}>
            {h.label}
            {sortBy === h.key && (sortDir === "asc"
              ? <ChevronUp size={10}/>
              : <ChevronDown size={10}/>)}
            {sortBy !== h.key && <ArrowUpDown size={9} className="opacity-40"/>}
          </button>
        ))}
      </div>

      {paged.length === 0 ? (
        <div className="text-center py-16 text-gray-700 rounded-xl border border-white/5">
          <TrendingUp size={28} className="mx-auto mb-3"/>
          <p className="text-sm">No high-signal anomalies in current window</p>
          <p className="text-xs text-gray-700 font-mono mt-1">Monitoring 4 signal types · refreshes every 12s</p>
        </div>
      ) : (
        <div className="space-y-2">
          {paged.map((f, i) => {
            const sig = ACTION[f.type] || { action:"WATCH", color:"#6B7280", reason:"Anomaly detected." };
            const c   = cfg(f.type);
            return (
              <div key={i} className="rounded-xl border p-4 flex items-center gap-4 hover:border-white/20 transition-all group animate-slide-up"
                style={{ borderColor: "#1F2937", background: "linear-gradient(135deg, #0D0D0D, #0A0A0A)" }}>
                <div className="text-xs font-black px-3 py-1.5 rounded-lg transition-transform group-hover:scale-105"
                  style={{ color: sig.color, backgroundColor: sig.color + "18", minWidth: 100, textAlign:"center", boxShadow: `inset 0 0 12px ${sig.color}15` }}>
                  {sig.action}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-white group-hover:text-white">{c.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5 truncate">{sig.reason}</div>
                </div>
                <ConfRing value={f.confidence || 0}/>
                <div className="text-xs font-mono text-gray-600 hidden sm:block">#{(f.block||0).toLocaleString()}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {sorted.length > PAGE_SIZE && (
        <div className="flex items-center justify-between text-xs font-mono px-1">
          <span className="text-gray-600">
            {safePage * PAGE_SIZE + 1}–{Math.min((safePage+1)*PAGE_SIZE, sorted.length)} of {sorted.length}
          </span>
          <div className="flex items-center gap-1">
            <button onClick={() => setPage(p => Math.max(0, p-1))} disabled={safePage === 0}
              className="p-1 rounded hover:bg-white/5 disabled:opacity-30 text-gray-500 hover:text-white transition-colors">
              <ChevronLeft size={12}/>
            </button>
            {Array.from({ length: totalPages }).map((_, idx) => (
              <button key={idx} onClick={() => setPage(idx)}
                className="w-6 h-6 rounded text-xs font-bold transition-colors"
                style={{ background: idx === safePage ? G+"20" : "transparent", color: idx === safePage ? G : "#6B7280" }}>
                {idx + 1}
              </button>
            ))}
            <button onClick={() => setPage(p => Math.min(totalPages-1, p+1))} disabled={safePage >= totalPages-1}
              className="p-1 rounded hover:bg-white/5 disabled:opacity-30 text-gray-500 hover:text-white transition-colors">
              <ChevronRight size={12}/>
            </button>
          </div>
        </div>
      )}

      <div className="rounded-xl border p-4 mt-4" style={{ borderColor: G + "30", background: G + "08" }}>
        <div className="text-xs font-bold mb-3 flex items-center gap-2" style={{ color: G }}>
          <TrendingUp size={11}/> PORTFOLIO STRATEGY
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          {[
            { label:"High Conf (≥85%)", value: findings.filter(f=>f.confidence>=0.85).length, col:"#EF4444" },
            { label:"Mid Conf (75–85%)", value: findings.filter(f=>f.confidence>=0.75&&f.confidence<0.85).length, col:"#F97316" },
            { label:"Watch (65–75%)",   value: findings.filter(f=>f.confidence>=0.65&&f.confidence<0.75).length, col:"#EAB308" },
          ].map(({ label, value, col }) => (
            <div key={label} className="rounded-lg p-2" style={{ background: col + "0F" }}>
              <div className="text-xl font-black font-mono" style={{ color: col }}>{value}</div>
              <div className="text-[10px] text-gray-600 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
