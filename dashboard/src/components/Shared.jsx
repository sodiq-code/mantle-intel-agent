import { useState, useEffect } from "react";
import { ExternalLink, ChevronRight } from "lucide-react";

export const G = "#00D395";
export const EXPLORER_BASE = "https://sepolia.mantlescan.xyz";

export const ANOMALY_CFG = {
  whale_accumulation:    { color:"#3B82F6", label:"Whale Accum.",      tier:"ALERT"    },
  whale_distribution:    { color:"#F97316", label:"Whale Distrib.",    tier:"ALERT"    },
  smart_money_inflow:    { color:"#A855F7", label:"Smart Money",       tier:"ALERT"    },
  tx_spike:              { color:"#00D395", label:"TX Spike",          tier:"WATCH"    },
  value_spike:           { color:"#EAB308", label:"Value Spike",       tier:"ALERT"    },
  multivariate_anomaly:  { color:"#EF4444", label:"Multivariate",      tier:"IMMEDIATE"},
  meth_depeg:            { color:"#F43F5E", label:"mETH Depeg",        tier:"IMMEDIATE"},
  cross_protocol_anomaly:{ color:"#EC4899", label:"Cross-Protocol",    tier:"IMMEDIATE"},
  liquidity_imbalance:   { color:"#06B6D4", label:"Liquidity Imbal.",  tier:"WATCH"    },
  lp_imbalance:          { color:"#14B8A6", label:"LP Imbalance",      tier:"ALERT"    },
};
export const DEF_CFG = { color:"#6B7280", label:"Anomaly", tier:"WATCH" };
export const cfg = (type) => ANOMALY_CFG[type] || DEF_CFG;

export const TIER_COLOR = {
  "IMMEDIATE": "#EF4444",
  "ALERT":     "#F97316",
  "WATCH":     "#EAB308",
};

export function useTimeSince(timestamp) {
  const [ago, setAgo] = useState("");
  useEffect(() => {
    const update = () => {
      if (!timestamp) return setAgo("—");
      const secs = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
      if (secs < 60)  return setAgo(`${secs}s ago`);
      const mins = Math.floor(secs / 60);
      if (mins < 60)  return setAgo(`${mins}m ago`);
      return setAgo(`${Math.floor(mins / 60)}h ago`);
    };
    update();
    const t = setInterval(update, 5000);
    return () => clearInterval(t);
  }, [timestamp]);
  return ago;
}

export function MiniBar({ data = [], color = G }) {
  if (!data || data.length < 2) return null;
  const vals = data.map(b => b.tx_count || 0);
  const max  = Math.max(...vals, 1);
  return (
    <div className="flex items-end gap-px h-8 w-full">
      {vals.slice(-24).map((v, i) => (
        <div key={i} className="flex-1 rounded-sm transition-all"
          style={{ height: `${Math.max(8, (v / max) * 100)}%`, backgroundColor: color, opacity: 0.7 + (i / vals.length) * 0.3 }}/>
      ))}
    </div>
  );
}

export function ConfRing({ value = 0, size = 36 }) {
  const r = (size - 4) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(value, 1);
  const color = pct >= 0.85 ? "#EF4444" : pct >= 0.75 ? "#F97316" : G;
  return (
    <svg width={size} height={size} className="flex-shrink-0">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1F2937" strokeWidth="3"/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="3"
        strokeDasharray={circ} strokeDashoffset={circ * (1 - pct)}
        strokeLinecap="round" transform={`rotate(-90 ${size/2} ${size/2})`}/>
      <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle"
        fill={color} fontSize="9" fontWeight="700" fontFamily="monospace">
        {Math.round(pct * 100)}
      </text>
    </svg>
  );
}

export function PulseDot({ color = G, size = 8 }) {
  return (
    <span className="relative flex" style={{ width: size, height: size }}>
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
        style={{ backgroundColor: color }}/>
      <span className="relative inline-flex rounded-full" style={{ width: size, height: size, backgroundColor: color }}/>
    </span>
  );
}

export function StatTile({ label, value, sub, accent = G, icon: Icon, live }) {
  return (
    <div className="relative overflow-hidden rounded-xl p-4 glass-card group">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900/80 to-slate-950/90 pointer-events-none" />
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3">
          <div className="p-2 rounded-lg transition-transform group-hover:scale-110" style={{ backgroundColor: accent + "18" }}>
            <Icon size={14} style={{ color: accent }}/>
          </div>
          {live && <PulseDot color={accent}/>}
        </div>
        <div className="text-2xl font-black font-mono text-white leading-none mb-1 group-hover:glow-text transition-all duration-300">{value}</div>
        <div className="text-xs font-semibold" style={{ color: accent }}>{label}</div>
        {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-px transition-all duration-300 group-hover:h-0.5" style={{ backgroundColor: accent + "60" }}/>
    </div>
  );
}

export function FindingRow({ finding, isNew }) {
  const [expanded, setExpanded] = useState(false);
  const c     = cfg(finding.type);
  const since = useTimeSince(finding.timestamp);
  const sm    = finding.smart_money || {};

  return (
    <div onClick={() => setExpanded(x => !x)}
      className={`rounded-xl cursor-pointer transition-all duration-300 relative overflow-hidden group ${isNew ? "animate-pulse" : ""} ${expanded ? "glass-panel" : "glass-card"}`}
      style={{
        borderColor: expanded ? c.color + "60" : "rgba(255,255,255,0.05)",
      }}>
      <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-300 pointer-events-none" style={{ backgroundColor: c.color }} />
      <div className="flex items-center gap-3 px-4 py-3 relative z-10">
        <div className="w-2 h-2 rounded-full flex-shrink-0 group-hover:animate-ping" style={{ backgroundColor: c.color }}/>
        <ConfRing value={finding.confidence || 0}/>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-bold font-mono group-hover:glow-text transition-all" style={{ color: c.color }}>{c.label}</span>
            <span className="text-xs px-1.5 py-0.5 rounded font-mono border"
              style={{ color: TIER_COLOR[c.tier], borderColor: TIER_COLOR[c.tier] + "40", backgroundColor: TIER_COLOR[c.tier] + "10" }}>
              {c.tier}
            </span>
            {sm.tier1_involved && (
              <span className="text-xs px-1.5 py-0.5 rounded font-bold"
                style={{ color: G, backgroundColor: G + "15", border: `1px solid ${G}40` }}>
                TIER-1
              </span>
            )}
          </div>
          <div className="text-sm text-white font-semibold mt-0.5 truncate group-hover:text-slate-200">
            {finding.title || `Block #${(finding.block || 0).toLocaleString()}`}
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <div className="text-xs text-slate-500 font-mono group-hover:text-slate-400">#{(finding.block||0).toLocaleString()}</div>
          <div className="text-xs text-slate-400">{since}</div>
        </div>
        <ChevronRight size={14} className="text-slate-500 flex-shrink-0 transition-transform duration-300 group-hover:text-white"
          style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}/>
      </div>
      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t relative z-10" style={{ borderColor: c.color + "20", backgroundColor: "rgba(0,0,0,0.2)" }}>
          {finding.insight && (
            <p className="text-sm text-slate-300 leading-relaxed pt-3">{finding.insight}</p>
          )}
          {sm.known_wallets?.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {sm.known_wallets.map(w => (
                <span key={w} className="text-xs px-2 py-0.5 rounded-full bg-slate-800/50 text-slate-300 border border-slate-700/50 font-mono">{w}</span>
              ))}
            </div>
          )}
          {finding.tx_hash && (
            <a href={`${EXPLORER_BASE}/tx/${finding.tx_hash}`} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs font-mono hover:underline mt-2" style={{ color: G }}>
              <ExternalLink size={10}/>{finding.tx_hash.slice(0,20)}…
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export function IncidentCard({ incident, isNew }) {
  const [expanded, setExpanded] = useState(false);
  const c = cfg(incident.type);
  const since = useTimeSince(incident.latest_time ? incident.latest_time * 1000 : null);
  
  const isResolved = incident.state?.includes("Resolved");
  const isCritical = incident.state?.includes("Critical");
  const stateColor = isResolved ? "#22C55E" : (isCritical ? "#EF4444" : "#F59E0B");
  const dur = (incident.latest_block - incident.start_block) + 1;

  return (
    <div className={`rounded-xl transition-all duration-300 relative overflow-hidden group ${isNew ? "animate-pulse" : ""} glass-panel`}
      style={{ borderColor: c.color + "40" }}>
      <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundColor: c.color }} />
      
      <div onClick={() => setExpanded(x => !x)} className="flex items-start gap-4 px-5 py-4 relative z-10 cursor-pointer">
        <ConfRing value={incident.peak_confidence || 0} size={44}/>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-sm font-bold font-mono" style={{ color: c.color }}>{c.label} INCIDENT</span>
            <span className="text-xs px-2 py-0.5 rounded font-bold"
              style={{ color: stateColor, backgroundColor: stateColor + "15", border: `1px solid ${stateColor}40` }}>
              {incident.state.toUpperCase()}
            </span>
          </div>
          
          <div className="text-white font-medium mb-2 text-sm leading-snug">
            {incident.occurrences} signal{incident.occurrences !== 1 ? 's' : ''} detected over {dur} block{dur !== 1 ? 's' : ''}.
          </div>
          
          <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
            <span>START: {incident.start_block.toLocaleString()}</span>
            <span>LAST: {incident.latest_block.toLocaleString()}</span>
            {incident.peak_zscore > 0 && <span style={{color: c.color}}>PEAK Z: {incident.peak_zscore.toFixed(1)}σ</span>}
          </div>
        </div>

        <div className="flex-shrink-0 text-right flex flex-col items-end gap-2">
          <div className="text-xs text-slate-400 font-mono">{since}</div>
          <ChevronRight size={16} className="text-slate-500 transition-transform duration-300 group-hover:text-white"
            style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}/>
        </div>
      </div>
      
      {expanded && (
        <div className="px-5 pb-5 pt-2 border-t relative z-10 space-y-2" style={{ borderColor: c.color + "20", backgroundColor: "rgba(0,0,0,0.3)" }}>
          <div className="text-xs font-bold text-slate-400 mb-2 font-mono uppercase tracking-wider">Raw Anomalous Blocks</div>
          {incident.findings.map(f => (
            <FindingRow key={f.id} finding={f} />
          ))}
        </div>
      )}
    </div>
  );
}
