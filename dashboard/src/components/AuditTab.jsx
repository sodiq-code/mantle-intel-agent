import { useState, useMemo } from "react";
import { Shield, ExternalLink, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Search, ArrowUpDown } from "lucide-react";
import { G, EXPLORER_BASE, cfg } from "./Shared.jsx";

const CONTRACT = "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b";
const PAGE_SIZE = 10;

export function AuditTab({ data, findings }) {
  const auditCount = data?.protocol_state?.audit_contract?.finding_count ?? findings.length ?? 0;

  const [sortBy, setSortBy] = useState("block");
  const [sortDir, setSortDir] = useState("desc");
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  // All available findings (not truncated to 20)
  const allFindings = findings;

  const types = useMemo(() => {
    const set = new Set(allFindings.map(f => f.type).filter(Boolean));
    return ["all", ...Array.from(set)];
  }, [allFindings]);

  const filtered = useMemo(() => {
    let out = allFindings;
    if (typeFilter !== "all") out = out.filter(f => f.type === typeFilter);
    if (query.trim()) {
      const q = query.toLowerCase();
      out = out.filter(f =>
        String(f.block || "").includes(q) ||
        String(f.type || "").toLowerCase().includes(q) ||
        String(f.title || "").toLowerCase().includes(q) ||
        String(f.hash || "").toLowerCase().includes(q)
      );
    }
    return out;
  }, [allFindings, query, typeFilter]);

  const sorted = useMemo(() => {
    const out = [...filtered];
    out.sort((a, b) => {
      let va, vb;
      switch (sortBy) {
        case "block":      va = a.block || 0;        vb = b.block || 0;        break;
        case "confidence": va = a.confidence || 0;   vb = b.confidence || 0;   break;
        case "type":       va = a.type || "";        vb = b.type || "";        break;
        case "txhash":     va = a.hash || "";        vb = b.hash || "";        break;
        default:           va = a.block || 0;        vb = b.block || 0;
      }
      if (typeof va === "string") {
        return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      return sortDir === "asc" ? va - vb : vb - va;
    });
    return out;
  }, [filtered, sortBy, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const paged = sorted.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  const toggleSort = (col) => {
    if (sortBy === col) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortBy(col);
      setSortDir("desc");
    }
    setPage(0);
  };

  const SortIcon = ({ col }) => {
    if (sortBy !== col) return <ArrowUpDown size={9} className="text-gray-700"/>;
    return sortDir === "asc"
      ? <ChevronUp size={11} style={{ color: G }}/>
      : <ChevronDown size={11} style={{ color: G }}/>;
  };

  const cols = [
    { key: "block",      label: "Block",      sortable: true,  width: "90px" },
    { key: "type",       label: "Type",       sortable: true,  width: "1fr" },
    { key: "confidence", label: "Confidence", sortable: true,  width: "120px" },
    { key: "status",     label: "Status",     sortable: false, width: "70px" },
    { key: "txhash",     label: "Tx Hash",    sortable: true,  width: "90px" },
  ];

  return (
    <div className="space-y-4 animate-fade-in">
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

      {/* Toolbar: search + type filter */}
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600"/>
          <input
            value={query}
            onChange={e => { setQuery(e.target.value); setPage(0); }}
            placeholder="Search block / type / title / hash…"
            className="w-full pl-9 pr-3 py-2 rounded-lg text-xs font-mono bg-slate-900/60 border border-white/5 text-white placeholder-gray-700 focus:outline-none focus:border-emerald-500/40 transition-colors"
          />
        </div>
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
          {types.map(t => (
            <button key={t} onClick={() => { setTypeFilter(t); setPage(0); }}
              className="text-xs px-3 py-1.5 rounded-lg whitespace-nowrap transition-all font-bold flex-shrink-0"
              style={{
                background: typeFilter===t ? G+"20":"rgba(15,23,42,0.6)",
                color: typeFilter===t ? G : "#94A3B8",
                border: `1px solid ${typeFilter===t ? G+"50":"rgba(255,255,255,0.05)"}`,
              }}>
              {t === "all" ? "All" : cfg(t).label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-xl border overflow-hidden" style={{ borderColor:"#1F2937" }}>
        {/* Header row */}
        <div className="grid text-xs text-gray-600 font-mono px-4 py-2.5 border-b"
          style={{ borderColor:"#1F2937", background:"#080808", gridTemplateColumns: `90px 1fr 120px 70px 90px` }}>
          {cols.map(col => (
            <button key={col.key}
              onClick={col.sortable ? () => toggleSort(col.key) : undefined}
              className={`flex items-center gap-1 ${col.sortable ? "cursor-pointer hover:text-gray-400" : "cursor-default"} ${col.key === "confidence" ? "justify-center" : ""}`}
              style={{ width: col.width }}>
              {col.label}
              {col.sortable && <SortIcon col={col.key}/>}
            </button>
          ))}
        </div>

        {/* Rows */}
        <div className="divide-y divide-gray-900">
          {paged.length === 0 ? (
            <div className="px-4 py-12 text-center text-gray-600 text-sm">
              <Shield size={20} className="mx-auto mb-2 text-gray-800"/>
              No findings match your filters.
            </div>
          ) : (
            paged.map((f, i) => {
              const c = cfg(f.type);
              const conf = f.confidence || 0;
              return (
                <div key={f.id || i} className="grid items-center text-xs px-4 py-2.5 hover:bg-white/[0.02] transition-colors animate-fade-in"
                  style={{ background:"#0A0A0A", gridTemplateColumns: `90px 1fr 120px 70px 90px` }}>
                  <span className="font-mono text-gray-500">#{f.block?.toLocaleString()}</span>
                  <div className="min-w-0">
                    <span className="font-bold font-mono" style={{ color: c.color }}>{c.label}</span>
                    {f.title && <div className="text-gray-600 truncate text-[10px] mt-0.5">{f.title}</div>}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="flex-1 h-1 rounded-full bg-gray-800 overflow-hidden">
                      <div className="h-1 rounded-full transition-all duration-500"
                        style={{ width:`${conf*100}%`, backgroundColor: c.color, boxShadow: `0 0 6px ${c.color}80` }}/>
                    </div>
                    <span className="font-mono text-gray-400 w-8 text-right">{Math.round(conf*100)}%</span>
                  </div>
                  <span className="font-bold font-mono" style={{ color: G }}>✓ OK</span>
                  {f.hash ? (
                    <a href={`${EXPLORER_BASE}/tx/${f.hash}`} target="_blank" rel="noopener noreferrer"
                      className="font-mono text-gray-600 hover:text-white transition-colors flex items-center gap-1 truncate" title={f.hash}>
                      {f.hash.slice(0,6)}… <ExternalLink size={8}/>
                    </a>
                  ) : (
                    <span className="text-gray-700">—</span>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Pagination footer */}
        {sorted.length > 0 && (
          <div className="flex items-center justify-between px-4 py-2.5 border-t text-xs font-mono"
            style={{ borderColor:"#1F2937", background:"#080808" }}>
            <span className="text-gray-600">
              {safePage * PAGE_SIZE + 1}–{Math.min((safePage+1)*PAGE_SIZE, sorted.length)} of {sorted.length}
            </span>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(p => Math.max(0, p-1))} disabled={safePage === 0}
                className="p-1 rounded hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed text-gray-500 hover:text-white transition-colors">
                <ChevronLeft size={12}/>
              </button>
              {Array.from({ length: totalPages }).slice(0, 7).map((_, idx) => (
                <button key={idx} onClick={() => setPage(idx)}
                  className="w-6 h-6 rounded text-xs font-bold transition-colors"
                  style={{
                    background: idx === safePage ? G+"20" : "transparent",
                    color: idx === safePage ? G : "#6B7280",
                  }}>
                  {idx + 1}
                </button>
              ))}
              {totalPages > 7 && <span className="text-gray-700 px-1">…</span>}
              <button onClick={() => setPage(p => Math.min(totalPages-1, p+1))} disabled={safePage >= totalPages-1}
                className="p-1 rounded hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed text-gray-500 hover:text-white transition-colors">
                <ChevronRight size={12}/>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
