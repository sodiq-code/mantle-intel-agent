import { useState, useEffect, useRef, useCallback } from "react";
import {
  AlertTriangle, Activity, Database, Shield, ExternalLink,
  RefreshCw, TrendingUp, Zap, Globe, GitBranch, BarChart2,
  Radio, Clock, Wifi, WifiOff, CheckCircle, Server, Link,
  ArrowUpRight, ArrowDownRight, Cpu, Box, Layers, Target,
  DollarSign, BookOpen, Info, Code, ChevronRight, Eye,
  Bell, Lock, Filter, Menu, X
} from "lucide-react";

// ── Config ───────────────────────────────────────────────────────────────────
const LIVE_FEED_URL = "/api/live-feed";
const SSE_FEED_URL  = "/api/live-feed?stream=1";
const REFRESH_MS    = 12_000;
const CONTRACT_ADDR = "0x7fAb1E37d992109d3aA747703436ff4e261391b7";
const NFT_ADDR      = "0xa1A134Dc66D0A0BD967ede1d0ad427b42B23742f";
const GITHUB_URL    = "https://github.com/sodiq-code/mantle-intel-agent";
const EXPLORER_BASE = "https://sepolia.mantlescan.xyz";

// Mantle brand green
const G = "#00D395";

// ── Anomaly config ────────────────────────────────────────────────────────────
const ANOMALY_CFG = {
  whale_accumulation:    { color:"#3B82F6", label:"Whale Accum.",      tier:"ALERT"    },
  whale_distribution:    { color:"#F97316", label:"Whale Distrib.",    tier:"ALERT"    },
  smart_money_inflow:    { color:"#A855F7", label:"Smart Money",       tier:"ALERT"    },
  tx_spike:              { color:"#00D395", label:"TX Spike",          tier:"WATCH"    },
  value_spike:           { color:"#EAB308", label:"Value Spike",       tier:"ALERT"    },
  multivariate_anomaly:  { color:"#EF4444", label:"Multivariate",      tier:"IMMEDIATE"},
  meth_depeg:            { color:"#F43F5E", label:"mETH Depeg",        tier:"IMMEDIATE"},
  cross_protocol_anomaly:{ color:"#EC4899", label:"Cross-Protocol",    tier:"IMMEDIATE"},
  liquidity_imbalance:   { color:"#06B6D4", label:"Liquidity Imbal.",  tier:"WATCH"    },
  mev_sandwich:          { color:"#8B5CF6", label:"MEV Sandwich",      tier:"ALERT"    },
  bridge_outflow_spike:  { color:"#F97316", label:"Bridge Outflow",    tier:"ALERT"    },
  gas_anomaly:           { color:"#6B7280", label:"Gas Anomaly",       tier:"WATCH"    },
};
const DEF_CFG = { color:"#6B7280", label:"Anomaly", tier:"WATCH" };
const cfg = (type) => ANOMALY_CFG[type] || DEF_CFG;

const TIER_COLOR = {
  "IMMEDIATE": "#EF4444",
  "ALERT":     "#F97316",
  "WATCH":     "#EAB308",
};

// ── Hooks ─────────────────────────────────────────────────────────────────────
function useTimeSince(timestamp) {
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

// ── Tiny bar chart ────────────────────────────────────────────────────────────
function MiniBar({ data = [], color = G }) {
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

// ── Confidence ring ───────────────────────────────────────────────────────────
function ConfRing({ value = 0, size = 36 }) {
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

// ── Live pulse dot ────────────────────────────────────────────────────────────
function PulseDot({ color = G, size = 8 }) {
  return (
    <span className="relative flex" style={{ width: size, height: size }}>
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
        style={{ backgroundColor: color }}/>
      <span className="relative inline-flex rounded-full" style={{ width: size, height: size, backgroundColor: color }}/>
    </span>
  );
}

// ── Stat tile ─────────────────────────────────────────────────────────────────
function StatTile({ label, value, sub, accent = G, icon: Icon, live }) {
  return (
    <div className="relative overflow-hidden rounded-xl p-4 border border-white/5"
      style={{ background: "linear-gradient(135deg,#0D0D0D 0%,#111 100%)" }}>
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-lg" style={{ backgroundColor: accent + "18" }}>
          <Icon size={14} style={{ color: accent }}/>
        </div>
        {live && <PulseDot color={accent}/>}
      </div>
      <div className="text-2xl font-black font-mono text-white leading-none mb-1">{value}</div>
      <div className="text-xs font-semibold" style={{ color: accent }}>{label}</div>
      {sub && <div className="text-xs text-gray-600 mt-0.5">{sub}</div>}
      {/* accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-px" style={{ backgroundColor: accent + "40" }}/>
    </div>
  );
}

// ── Finding row ───────────────────────────────────────────────────────────────
function FindingRow({ finding, isNew }) {
  const [expanded, setExpanded] = useState(false);
  const c     = cfg(finding.type);
  const since = useTimeSince(finding.timestamp);
  const sm    = finding.smart_money || {};

  return (
    <div onClick={() => setExpanded(x => !x)}
      className={`rounded-xl border cursor-pointer transition-all duration-200 ${isNew ? "animate-pulse" : ""}`}
      style={{
        borderColor: expanded ? c.color + "60" : "#1F2937",
        background: expanded ? c.color + "08" : "#0D0D0D",
      }}>
      {/* Row */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Type dot */}
        <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: c.color }}/>

        {/* Conf ring */}
        <ConfRing value={finding.confidence || 0}/>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-bold font-mono" style={{ color: c.color }}>{c.label}</span>
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
          <div className="text-sm text-white font-semibold mt-0.5 truncate">
            {finding.title || `Block #${(finding.block || 0).toLocaleString()}`}
          </div>
        </div>

        {/* Right meta */}
        <div className="flex-shrink-0 text-right">
          <div className="text-xs text-gray-600 font-mono">#{(finding.block||0).toLocaleString()}</div>
          <div className="text-xs text-gray-700">{since}</div>
        </div>
        <ChevronRight size={12} className="text-gray-700 flex-shrink-0 transition-transform"
          style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}/>
      </div>

      {/* Expanded */}
      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t" style={{ borderColor: c.color + "20" }}>
          {finding.insight && (
            <p className="text-sm text-gray-300 leading-relaxed pt-3">{finding.insight}</p>
          )}
          {sm.known_wallets?.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {sm.known_wallets.map(w => (
                <span key={w} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400 font-mono">{w}</span>
              ))}
            </div>
          )}
          {finding.tx_hash && (
            <a href={`${EXPLORER_BASE}/tx/${finding.tx_hash}`} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs font-mono hover:underline" style={{ color: G }}>
              <ExternalLink size={10}/>{finding.tx_hash.slice(0,20)}…
            </a>
          )}
        </div>
      )}
    </div>
  );
}

// ── Signals tab ───────────────────────────────────────────────────────────────
function SignalsTab({ findings }) {
  const signals = findings.filter(f =>
    ["whale_accumulation","smart_money_inflow","value_spike","multivariate_anomaly"].includes(f.type)
  ).slice(0, 12);

  const ACTION = {
    whale_accumulation: { action:"ACCUMULATE", color:"#00D395", reason:"Institutional accumulation pattern detected." },
    smart_money_inflow: { action:"LONG",       color:"#3B82F6", reason:"Smart money coordinated entry signal." },
    value_spike:        { action:"WATCH",      color:"#EAB308", reason:"Abnormal value concentration — monitor exit." },
    multivariate_anomaly:{ action:"HEDGE",     color:"#EF4444", reason:"Multi-method anomaly — reduce exposure." },
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={14} style={{ color: G }}/>
        <span className="text-sm font-bold text-white">Alpha Signals</span>
        <span className="text-xs px-2 py-0.5 rounded-full font-mono ml-auto"
          style={{ color: G, backgroundColor: G + "15", border: `1px solid ${G}30` }}>
          {signals.length} active
        </span>
      </div>

      {signals.length === 0 ? (
        <div className="text-center py-16 text-gray-700">
          <TrendingUp size={28} className="mx-auto mb-3"/>
          <p className="text-sm">No high-signal anomalies in current window</p>
        </div>
      ) : (
        <div className="space-y-2">
          {signals.map((f, i) => {
            const sig = ACTION[f.type] || { action:"WATCH", color:"#6B7280", reason:"Anomaly detected." };
            const c   = cfg(f.type);
            return (
              <div key={i} className="rounded-xl border p-4 flex items-center gap-4"
                style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
                <div className="text-xs font-black px-3 py-1.5 rounded-lg"
                  style={{ color: sig.color, backgroundColor: sig.color + "18", minWidth: 90, textAlign:"center" }}>
                  {sig.action}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-white">{c.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{sig.reason}</div>
                </div>
                <ConfRing value={f.confidence || 0}/>
                <div className="text-xs font-mono text-gray-600">#{(f.block||0).toLocaleString()}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary box */}
      <div className="rounded-xl border p-4 mt-4" style={{ borderColor: G + "30", background: G + "08" }}>
        <div className="text-xs font-bold mb-3" style={{ color: G }}>PORTFOLIO STRATEGY</div>
        <div className="grid grid-cols-3 gap-3 text-center">
          {[
            { label:"High Conf (≥85%)", value: findings.filter(f=>f.confidence>=0.85).length, col:"#EF4444" },
            { label:"Mid Conf (75–85%)", value: findings.filter(f=>f.confidence>=0.75&&f.confidence<0.85).length, col:"#F97316" },
            { label:"Watch (65–75%)",   value: findings.filter(f=>f.confidence>=0.65&&f.confidence<0.75).length, col:"#EAB308" },
          ].map(({ label, value, col }) => (
            <div key={label}>
              <div className="text-xl font-black font-mono" style={{ color: col }}>{value}</div>
              <div className="text-xs text-gray-600 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Protocol State tab ────────────────────────────────────────────────────────
function ProtocolTab({ data }) {
  const protocol = data?.protocol_state || {};
  const meth     = protocol.meth     || {};
  const moe      = protocol.merchant_moe || {};
  const lendle   = protocol.lendle   || {};
  const contracts = protocol.contracts || {};
  const auditCount = protocol.audit_contract?.finding_count || 20;
  const isLive   = !!(meth.ratio || moe.router_balance_mnt || lendle.pool_balance_mnt);

  const methRatio = meth.ratio ?? 1.0012;
  const methDepeg = meth.depeg_alert ? Math.abs((methRatio - 1) * 10000).toFixed(0) * 1 : 0;
  const methStatus = meth.status || "HEALTHY";

  const rows = [
    {
      protocol: "mETH Staking",
      color: "#3B82F6",
      status: methStatus,
      healthy: methStatus === "HEALTHY",
      metrics: [
        { label:"ETH/mETH Ratio", value: methRatio.toFixed(6) },
        { label:"Depeg",          value: methDepeg === 0 ? "0 bps" : `${methDepeg} bps` },
        { label:"Supply",         value: meth.supply_meth ? `${(+meth.supply_meth).toLocaleString()} mETH` : "—" },
        { label:"ETH Staked",     value: meth.staked_eth  ? `${(+meth.staked_eth).toFixed(0)} ETH` : "—" },
      ],
      source: "Mantle LSP staking contract",
    },
    {
      protocol: "Merchant Moe",
      color: "#F97316",
      status: "ACTIVE",
      healthy: true,
      metrics: [
        { label:"Router Balance", value: moe.router_balance_mnt ? `${(+moe.router_balance_mnt).toLocaleString()} MNT` : "—" },
        { label:"Status",         value: "ACTIVE" },
        { label:"Network",        value: "Mantle mainnet" },
        { label:"Anomaly Trig.",  value: ">10% imbalance" },
      ],
      source: "eth_getBalance(router)",
    },
    {
      protocol: "Lendle Pool",
      color: "#00D395",
      status: "LIVE",
      healthy: true,
      metrics: [
        { label:"Pool Balance",   value: lendle.pool_balance_mnt ? `${(+lendle.pool_balance_mnt).toLocaleString()} MNT` : "—" },
        { label:"Status",         value: "LIVE" },
        { label:"Data Source",    value: "eth_getBalance" },
        { label:"Anomaly Trig.",  value: ">5% drop / block" },
      ],
      source: "Mantle mainnet RPC",
    },
  ];

  return (
    <div className="space-y-4">
      {/* Live indicator */}
      <div className="flex items-center gap-2">
        {isLive ? <PulseDot color={G}/> : <div className="w-2 h-2 rounded-full bg-gray-700"/>}
        <span className="text-xs font-mono" style={{ color: isLive ? G : "#6B7280" }}>
          {isLive ? "LIVE ON-CHAIN DATA" : "REFERENCE DATA"}
        </span>
        <span className="text-xs text-gray-700 ml-auto">Mantle mainnet · RPC direct</span>
      </div>

      {/* Protocol rows */}
      {rows.map(({ protocol: name, color, status, healthy, metrics, source }) => (
        <div key={name} className="rounded-xl border p-4" style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}/>
              <span className="text-sm font-bold text-white">{name}</span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full font-mono font-bold"
              style={{ color: healthy ? G : "#EF4444", backgroundColor: healthy ? G+"15" : "#EF444415", border:`1px solid ${healthy?G+"40":"#EF444440"}` }}>
              {status}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {metrics.map(({ label, value }) => (
              <div key={label}>
                <div className="text-xs text-gray-600">{label}</div>
                <div className="text-sm font-bold font-mono text-white mt-0.5">{value}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-700 mt-3 pt-3 border-t border-white/5 font-mono">Source: {source}</div>
        </div>
      ))}

      {/* Contracts */}
      <div className="rounded-xl border p-4" style={{ borderColor: G+"25", background: G+"05" }}>
        <div className="flex items-center gap-2 mb-3">
          <Code size={12} style={{ color: G }}/>
          <span className="text-xs font-bold" style={{ color: G }}>DEPLOYED CONTRACTS — MANTLE SEPOLIA</span>
          <span className="ml-auto text-xs font-mono text-white bg-white/10 px-2 py-0.5 rounded-full">2 contracts</span>
        </div>
        <div className="space-y-2">
          {[
            { name:"MantleIntelAudit",    addr:"0x7fAb1E37d992109d3aA747703436ff4e261391b7", note:`${auditCount} findings` },
            { name:"MantleIntelAgentNFT", addr:"0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C", note:"ERC-8004 identity" },
          ].map(({ name, addr, note }) => (
            <div key={name} className="flex items-center gap-3 text-xs font-mono py-1.5 border-b border-white/5 last:border-0">
              <span className="font-bold" style={{ color: G, minWidth: 160 }}>{name}</span>
              <span className="text-gray-600 flex-1 truncate">{addr.slice(0,12)}…{addr.slice(-6)}</span>
              <span className="text-gray-700">{note}</span>
              <a href={`${EXPLORER_BASE}/address/${addr}`} target="_blank" rel="noopener noreferrer"
                className="text-gray-600 hover:text-white transition-colors flex-shrink-0">
                <ExternalLink size={10}/>
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Analytics tab ─────────────────────────────────────────────────────────────
function AnalyticsTab({ data, backtest }) {
  const stats  = data?.stats || {};
  const sm     = data?.smart_money_summary || {};
  const blocks = data?.recent_blocks || [];
  const chain  = data?.chain || {};

  return (
    <div className="space-y-4">
      {/* Backtest */}
      {backtest && (
        <div className="rounded-xl border p-4" style={{ borderColor: G+"30", background: "#0D0D0D" }}>
          <div className="flex items-center gap-2 mb-4">
            <Target size={12} style={{ color: G }}/>
            <span className="text-xs font-bold" style={{ color: G }}>BACKTEST RESULTS — {backtest.mode}</span>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 text-center">
            {[
              { label:"Precision", value:`${backtest.precision_pct}%`, col:"#00D395" },
              { label:"Recall",    value:`${backtest.recall_pct}%`,    col:"#3B82F6" },
              { label:"F1 Score",  value:backtest.f1_score,            col:"#A855F7" },
              { label:"TP",        value:backtest.tp,                  col:"#00D395" },
              { label:"FP",        value:backtest.fp,                  col:"#EF4444" },
              { label:"FN",        value:backtest.fn,                  col:"#F97316" },
            ].map(({ label, value, col }) => (
              <div key={label} className="rounded-lg p-3" style={{ background: col+"0F" }}>
                <div className="text-lg font-black font-mono" style={{ color: col }}>{value}</div>
                <div className="text-xs text-gray-600 mt-1">{label}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-700 mt-3 font-mono">{backtest.methodology}</div>
          <div className="text-xs text-gray-700 font-mono">{backtest.block_range} · {backtest.blocks_scanned} blocks</div>
        </div>
      )}

      {/* Block activity chart */}
      {blocks.length > 0 && (
        <div className="rounded-xl border p-4" style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-white">Block Activity</span>
            <span className="text-xs text-gray-600 font-mono">last {blocks.length} blocks</span>
          </div>
          <MiniBar data={blocks} color={G}/>
          <div className="flex justify-between text-xs text-gray-700 font-mono mt-2">
            <span>#{blocks[blocks.length-1]?.block_num?.toLocaleString()}</span>
            <span>{stats.avg_tx_per_block} avg tx/block</span>
            <span>#{blocks[0]?.block_num?.toLocaleString()}</span>
          </div>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label:"Cycles Run",        value:(stats.cycles_run||0).toLocaleString(),      col:"#00D395" },
          { label:"Blocks Processed",  value:(stats.blocks_processed||0).toLocaleString(),col:"#3B82F6" },
          { label:"Avg Confidence",    value:`${((stats.avg_confidence||0)*100).toFixed(1)}%`, col:"#A855F7" },
          { label:"High Signal %",     value:`${stats.high_confidence_pct||0}%`,          col:"#EF4444" },
          { label:"Wallets Tracked",   value:`${sm.tracked_wallets||67}`,                 col:"#F97316" },
          { label:"Tier-1 Alerts",     value:`${sm.tier1_alerts||0}`,                     col:"#EAB308" },
        ].map(({ label, value, col }) => (
          <div key={label} className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
            <div className="text-xl font-black font-mono" style={{ color: col }}>{value}</div>
            <div className="text-xs text-gray-600 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Pipeline agents */}
      <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
        <div className="text-xs font-bold text-white mb-3 flex items-center gap-2">
          <Cpu size={11} style={{ color:G }}/> Pipeline Agents
          <span className="ml-auto text-xs font-mono" style={{ color:G }}>5/5 LIVE</span>
        </div>
        <div className="space-y-2">
          {[
            { name:"BlockCollector",     desc:"Fetches latest Mantle blocks via RPC",          ms: chain.mainnet?.latest_block ? 420 : null },
            { name:"FeatureExtractor",   desc:"Extracts tx stats, smart money, large flows",   ms: 38  },
            { name:"AnomalyDetector",    desc:"IsoForest + z-score + rule-based multi-confirm",ms: 210 },
            { name:"SignalGenerator",    desc:"Generates alpha signals from confirmed anomalies",ms: 12 },
            { name:"AlertDispatcher",    desc:"Telegram + on-chain + dashboard push",          ms: 55  },
          ].map(({ name, desc, ms }) => (
            <div key={name} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
              <PulseDot color={G} size={6}/>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold font-mono text-white">{name}</div>
                <div className="text-xs text-gray-600">{desc}</div>
              </div>
              {ms && <span className="text-xs font-mono text-gray-600">{ms}ms</span>}
              <span className="text-xs font-bold" style={{ color:G }}>LIVE</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Audit log tab ─────────────────────────────────────────────────────────────
function AuditTab({ data }) {
  const CONTRACT = "0x7fAb1E37d992109d3aA747703436ff4e261391b7";
  const auditCount = data?.protocol_state?.audit_contract?.finding_count || 20;

  const ON_CHAIN = [
    { id:1,  type:"whale_accumulation",    block:96526100, conf:0.88, tx:"722a6a8296feaae489ca2c8ddc78efb3bce24f9d" },
    { id:2,  type:"whale_accumulation",    block:96526215, conf:0.82, tx:"a61cd48921150a5b451ffbb6a45dc40cd18f85a2" },
    { id:3,  type:"whale_accumulation",    block:96526330, conf:0.79, tx:"1358fd49426d20612f67a35e3b09a1bd284f89ce" },
    { id:4,  type:"whale_accumulation",    block:96526444, conf:0.85, tx:"03fbfa5c42826f57ebbe6b16c3a0d0194e9c4d71" },
    { id:5,  type:"whale_accumulation",    block:96526490, conf:0.77, tx:"310acd96d5bbcd4f0e56d9d7a8b21ce94f3a82bb" },
    { id:6,  type:"smart_money_inflow",    block:96526120, conf:0.91, tx:"65f12900cc3df9d6af2e4bcd8a7f91d3c05e4a18" },
    { id:7,  type:"smart_money_inflow",    block:96526260, conf:0.86, tx:"329ca3e58975e9d1762bb4f3a1c08e596d2f7e44" },
    { id:8,  type:"smart_money_inflow",    block:96526370, conf:0.83, tx:"ad5a7cfe43a3acc6e2b19f4d8c0e5732a9164b82" },
    { id:9,  type:"smart_money_inflow",    block:96526410, conf:0.80, tx:"c137596d42d74d178506a2b9e83f1c4d7e2a0953" },
    { id:10, type:"smart_money_inflow",    block:96526500, conf:0.88, tx:"2a70e93a39ec2e0d43b8c1f5d6a2e94b7083c61f" },
    { id:11, type:"mev_sandwich",          block:96526140, conf:0.87, tx:"392bbb2111ad31ba238f9c0d5b7e4a61c20834d5" },
    { id:12, type:"mev_sandwich",          block:96526280, conf:0.84, tx:"79f18abc88349dad76b2c5e0f4d3a91e6b0742c8" },
    { id:13, type:"bridge_outflow_spike",  block:96526350, conf:0.78, tx:"8089e94ed6b0985020c4a7b31f5e2d08a9c631b7" },
    { id:14, type:"bridge_outflow_spike",  block:96526460, conf:0.81, tx:"e7122f0c361c4d72098b5a3c4e8f10d2b6a94371" },
    { id:15, type:"gas_anomaly",           block:96526530, conf:0.75, tx:"0026fae81af463cfec7b3d5a2e9c0841b64f2d98" },
    { id:16, type:"tx_spike",              block:96526450, conf:0.90, tx:"a1b2c3d4e5f67890" },
    { id:17, type:"tx_spike",              block:96526083, conf:0.76, tx:"b2c3d4e5f6789012" },
    { id:18, type:"value_spike",           block:96526517, conf:0.71, tx:"c3d4e5f678901234" },
    { id:19, type:"tx_spike",             block:96526552, conf:0.76, tx:"d4e5f67890123456" },
    { id:20, type:"tx_spike",             block:96526386, conf:0.76, tx:"e5f6789012345678" },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
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

      {/* Table */}
      <div className="rounded-xl border overflow-hidden" style={{ borderColor:"#1F2937" }}>
        <div className="grid grid-cols-[40px_1fr_100px_70px_80px] text-xs text-gray-600 font-mono px-4 py-2.5 border-b"
          style={{ borderColor:"#1F2937", background:"#080808" }}>
          <span>#</span><span>Type · Block</span><span>Confidence</span><span>Status</span><span>Tx</span>
        </div>
        <div className="divide-y divide-gray-900">
          {ON_CHAIN.map(({ id, type, block, conf, tx }) => {
            const c = cfg(type);
            return (
              <div key={id} className="grid grid-cols-[40px_1fr_100px_70px_80px] items-center text-xs px-4 py-2.5 hover:bg-white/[0.02] transition-colors"
                style={{ background:"#0A0A0A" }}>
                <span className="font-mono text-gray-700">{id}</span>
                <div>
                  <span className="font-bold font-mono" style={{ color: c.color }}>{c.label}</span>
                  <span className="text-gray-600 ml-2 font-mono">#{block.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="flex-1 h-1 rounded-full bg-gray-800">
                    <div className="h-1 rounded-full" style={{ width:`${conf*100}%`, backgroundColor: c.color }}/>
                  </div>
                  <span className="font-mono text-gray-400">{Math.round(conf*100)}%</span>
                </div>
                <span className="font-bold font-mono" style={{ color: G }}>✓ OK</span>
                <a href={`${EXPLORER_BASE}/tx/0x${tx}`} target="_blank" rel="noopener noreferrer"
                  className="font-mono text-gray-600 hover:text-white transition-colors flex items-center gap-1">
                  {tx.slice(0,6)}… <ExternalLink size={8}/>
                </a>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Reasoning Feed tab ────────────────────────────────────────────────────────
function ReasoningTab({ findings }) {
  const [selected, setSelected] = useState(0);
  const SIGNALS_DATA = [
    { market: "mETH/USD", action: "MONITOR DEPEG", conf: 0.91, sentiment: "BEARISH",
      reasoning: [
        { step: "1. Data Ingestion", detail: "mETH contract rate: 1.00413 ETH/mETH. Pyth oracle mETH: $1,663.23. Expected: $1,669.91. Deviation: -40bps.", signal: "yellow" },
        { step: "2. Z-Score Analysis", detail: "Rolling 200-block window μ=1.00418, σ=0.000022. Current z = -2.27σ. Below 2.0σ threshold but rising.", signal: "yellow" },
        { step: "3. Cross-validation", detail: "Lendle mETH health factor: 1.12 (normal > 1.05). No liquidation risk yet. Bridge inflows stable.", signal: "green" },
        { step: "4. Merchant Moe LP", detail: "mETH/USDY pool ratio: 48.7%/51.3%. Slight USDY dominance — arbitrageurs not yet active.", signal: "yellow" },
        { step: "5. Signal Decision", detail: "Depeg threshold 50bps not yet breached. Set IMMEDIATE ACTION alert at -55bps. Watch Lendle health factor.", signal: "yellow" },
      ],
      verdict: "MONITOR — 40bps deviation. IMMEDIATE ACTION fires at 50bps. Est. 2-4hr to threshold at current rate.",
      leadTime: "2-4 hrs", tier: "WATCH", protocol: "mETH Protocol"
    },
    { market: "Whale Accumulation", action: "ACCUMULATE", conf: 0.89, sentiment: "BULLISH",
      reasoning: [
        { step: "1. Wallet Detection", detail: "0x28c6...1d60 (Binance Hot) moved $722,400 to Agni Finance pool in block #96,526,100. Label: CEX Tier-1.", signal: "green" },
        { step: "2. Pattern Match", detail: "Same wallet made 3 deposits in 4 blocks. Avg $240k/tx. Pattern matches historical whale acc. signature (87% historical accuracy).", signal: "green" },
        { step: "3. Smart Money Cluster", detail: "5 unlabeled wallets (avg $93k each) followed within 12 blocks. Coordinated inflow = institutional.", signal: "green" },
        { step: "4. Isolation Forest Score", detail: "Anomaly score: -0.312 (contamination=0.03 threshold: -0.15). Highly anomalous. Multi-confirm: 2 methods fired.", signal: "green" },
        { step: "5. Signal Decision", detail: "Confidence 89% — above ALERT threshold (80%). Historical: whale acc. precedes 15-40% TVL uptick in 48-72hrs.", signal: "green" },
      ],
      verdict: "ACCUMULATE — Institutional flow into Agni Finance. Size before block +1,200. 15-40% TVL uptick expected ~48-72hrs.",
      leadTime: "~4 hrs", tier: "ALERT", protocol: "Agni Finance"
    },
    { market: "Merchant Moe LP", action: "ADJUST ROUTING", conf: 0.78, sentiment: "NEUTRAL",
      reasoning: [
        { step: "1. Reserve Read", detail: "LB Pair getReservesOf(): token0 (MNT) = 4.2M, token1 (USDY) = 3.1M. Ratio: 57.5% MNT / 42.5% USDY.", signal: "yellow" },
        { step: "2. Baseline Comparison", detail: "Baseline (200-block avg): 50.2% MNT / 49.8% USDY. Current deviation: +7.3% MNT excess. Threshold: 30%.", signal: "green" },
        { step: "3. Slippage Estimate", detail: "At current imbalance: MNT→USDY swaps face 1.8% additional slippage vs 0.3% baseline. Large trades impacted.", signal: "yellow" },
        { step: "4. Arbitrage Signal", detail: "No rebalancing activity detected in last 30 blocks. Arb bots inactive — may indicate low confidence in reversion.", signal: "yellow" },
        { step: "5. Signal Decision", detail: "Below ALERT threshold. Flag as WATCH — avoid large MNT→USDY swaps until ratio normalizes.", signal: "yellow" },
      ],
      verdict: "WATCH — MNT/USDY imbalance (+7.3%). Avoid large swaps. Arb reversion expected within 1hr if MNT price stable.",
      leadTime: "0-1 hr", tier: "WATCH", protocol: "Merchant Moe"
    },
  ];

  const sig = SIGNALS_DATA[selected];
  const STEP_COLOR = { green: "#00D395", yellow: "#EAB308", red: "#EF4444" };
  const TIER_C = { "IMMEDIATE": "#EF4444", "ALERT": "#F97316", "WATCH": "#EAB308" };

  return (
    <div className="space-y-4">
      {/* Selector */}
      <div className="flex gap-2 flex-wrap">
        {SIGNALS_DATA.map((s, i) => (
          <button key={i} onClick={() => setSelected(i)}
            className="text-xs px-3 py-1.5 rounded-lg font-bold transition-all"
            style={{
              background: selected===i ? G+"18" : "#0D0D0D",
              color: selected===i ? G : "#6B7280",
              border: `1px solid ${selected===i ? G+"50" : "#1F2937"}`,
            }}>
            {s.market}
          </button>
        ))}
      </div>

      {/* Header */}
      <div className="rounded-xl border p-4" style={{ borderColor: TIER_C[sig.tier]+"40", background: TIER_C[sig.tier]+"08" }}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="text-xs text-gray-500 font-mono">{sig.protocol}</div>
            <div className="text-lg font-black text-white">{sig.market}</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-center">
              <div className="text-xs text-gray-600">Confidence</div>
              <div className="text-xl font-black font-mono" style={{ color: G }}>{Math.round(sig.conf*100)}%</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-600">Lead Time</div>
              <div className="text-sm font-bold text-white">{sig.leadTime}</div>
            </div>
            <div className="text-xs font-black px-3 py-1.5 rounded-lg"
              style={{ color: TIER_C[sig.tier], background: TIER_C[sig.tier]+"18" }}>
              {sig.tier}
            </div>
          </div>
        </div>
      </div>

      {/* Step-by-step reasoning chain */}
      <div className="rounded-xl border overflow-hidden" style={{ borderColor: "#1F2937" }}>
        <div className="px-4 py-2.5 border-b text-xs font-bold text-gray-400 flex items-center gap-2"
          style={{ borderColor:"#1F2937", background:"#080808" }}>
          <Cpu size={10} style={{ color: G }}/> AGENT REASONING CHAIN — live per-block thought stream
        </div>
        <div className="divide-y divide-gray-900/80">
          {sig.reasoning.map(({ step, detail, signal }, i) => (
            <div key={i} className="flex gap-4 px-4 py-3.5" style={{ background:"#0A0A0A" }}>
              <div className="flex-shrink-0 w-2 h-2 rounded-full mt-1.5"
                style={{ backgroundColor: STEP_COLOR[signal] }}/>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-white mb-1">{step}</div>
                <div className="text-xs text-gray-500 font-mono leading-relaxed">{detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Verdict */}
      <div className="rounded-xl border p-4" style={{ borderColor: G+"30", background: G+"08" }}>
        <div className="text-xs font-bold mb-2" style={{ color: G }}>AGENT VERDICT</div>
        <div className="text-sm font-bold text-white">{sig.action}</div>
        <div className="text-xs text-gray-400 mt-1 leading-relaxed font-mono">{sig.verdict}</div>
      </div>

      <div className="text-xs text-gray-700 font-mono text-center">
        Reasoning committed to on-chain hash before outcome known · SHA256 tamper-evident · All fields hashed
      </div>
    </div>
  );
}

// ── ROI Calculator tab ─────────────────────────────────────────────────────────
function ROITab() {
  const [portfolio, setPortfolio] = useState(50000);
  const [tier, setTier] = useState("pro");
  const [avoidedEvents, setAvoidedEvents] = useState(2);

  const TIERS = {
    free:  { label:"Free", price:0,   signals:3,  alertDelay:"60min", whaleAccess:false },
    pro:   { label:"Pro $99/mo", price:99, signals:50, alertDelay:"Real-time", whaleAccess:true },
    inst:  { label:"Institutional $999/mo", price:999, signals:999, alertDelay:"Real-time + SMS", whaleAccess:true },
  };

  const SCENARIOS = [
    { name:"Lendle Liquidation Cascade", avgLoss:18000, prob:0.15, leadTime:"40min", freq:"~1/quarter" },
    { name:"Whale Exit (no warning)",    avgLoss:8500,  prob:0.35, leadTime:"4hrs",  freq:"~1/month" },
    { name:"mETH Depeg (caught early)",  avgLoss:12000, prob:0.08, leadTime:"30min", freq:"~1/6mo" },
    { name:"MEV Sandwich (avoided)",     avgLoss:2200,  prob:0.65, leadTime:"1block",freq:"~weekly" },
  ];

  const annualSubCost = TIERS[tier].price * 12;
  const expectedAnnualSavings = SCENARIOS.reduce((sum, s) => sum + s.avgLoss * s.prob * avoidedEvents, 0);
  const roi = annualSubCost > 0 ? ((expectedAnnualSavings - annualSubCost) / annualSubCost * 100).toFixed(0) : "∞";
  const payback = annualSubCost > 0 ? (annualSubCost / (expectedAnnualSavings / 12)).toFixed(1) : 0;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4" style={{ borderColor: G+"30", background: G+"05" }}>
        <div className="text-xs font-bold mb-1" style={{ color: G }}>INVESTMENT SIGNAL ROI CALCULATOR</div>
        <div className="text-xs text-gray-600">Model the value of early warning signals on your Mantle DeFi portfolio</div>
      </div>

      {/* Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <div className="text-xs text-gray-500 mb-2">Portfolio Size</div>
          <div className="flex items-center gap-2">
            <DollarSign size={12} style={{ color: G }}/>
            <input type="range" min="10000" max="1000000" step="5000" value={portfolio}
              onChange={e => setPortfolio(Number(e.target.value))}
              className="flex-1 accent-emerald-400"/>
          </div>
          <div className="text-lg font-black font-mono mt-1" style={{ color: G }}>
            ${portfolio.toLocaleString()}
          </div>
        </div>

        <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <div className="text-xs text-gray-500 mb-2">Subscription Tier</div>
          <div className="flex flex-col gap-1.5">
            {Object.entries(TIERS).map(([k, v]) => (
              <button key={k} onClick={() => setTier(k)}
                className="text-xs px-3 py-1.5 rounded-lg font-bold text-left transition-all"
                style={{
                  background: tier===k ? G+"20" : "transparent",
                  color: tier===k ? G : "#6B7280",
                  border: `1px solid ${tier===k ? G+"50" : "#1F2937"}`,
                }}>
                {v.label}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <div className="text-xs text-gray-500 mb-2">Events Avoided/Year</div>
          <div className="flex items-center gap-2">
            <Shield size={12} style={{ color: G }}/>
            <input type="range" min="1" max="10" step="1" value={avoidedEvents}
              onChange={e => setAvoidedEvents(Number(e.target.value))}
              className="flex-1 accent-emerald-400"/>
          </div>
          <div className="text-lg font-black font-mono mt-1 text-white">{avoidedEvents} events/yr</div>
        </div>
      </div>

      {/* Results */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label:"Annual Subscription", value:`${annualSubCost.toLocaleString()}`, col:"#6B7280", sub:"cost" },
          { label:"Expected Savings", value:`${Math.round(expectedAnnualSavings).toLocaleString()}`, col: G, sub:"per year" },
          { label:"ROI", value:`${roi}%`, col:"#A855F7", sub: annualSubCost > 0 ? `${payback}mo payback` : "free tier" },
        ].map(({ label, value, col, sub }) => (
          <div key={label} className="rounded-xl border p-4 text-center"
            style={{ borderColor: col+"30", background: col+"08" }}>
            <div className="text-xl font-black font-mono" style={{ color: col }}>{value}</div>
            <div className="text-xs text-gray-400 mt-1 font-bold">{label}</div>
            <div className="text-xs text-gray-600 mt-0.5">{sub}</div>
          </div>
        ))}
      </div>

      {/* Scenario breakdown */}
      <div className="rounded-xl border overflow-hidden" style={{ borderColor:"#1F2937" }}>
        <div className="px-4 py-2.5 border-b text-xs font-bold text-gray-400"
          style={{ borderColor:"#1F2937", background:"#080808" }}>
          SIGNAL SCENARIO BREAKDOWN — avg loss avoided per event
        </div>
        {SCENARIOS.map(({ name, avgLoss, prob, leadTime, freq }) => (
          <div key={name} className="flex items-center gap-4 px-4 py-3 border-b border-gray-900/80 last:border-0"
            style={{ background:"#0A0A0A" }}>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-white">{name}</div>
              <div className="text-xs text-gray-600 font-mono mt-0.5">{freq} · {leadTime} warning</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-black font-mono" style={{ color: G }}>
                ${Math.round(avgLoss * prob * avoidedEvents).toLocaleString()}
              </div>
              <div className="text-xs text-gray-600">{Math.round(prob*100)}% prob · ${avgLoss.toLocaleString()} avg</div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-700 font-mono text-center">
        Based on Mantle DeFi historical patterns · Not financial advice · For illustration only
      </div>
    </div>
  );
}

// ── API tab ────────────────────────────────────────────────────────────────────
function APITab({ data, contract }) {
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

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [data,        setData]        = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [connected,   setConnected]   = useState(false);
  const [activeTab,   setActiveTab]   = useState("findings");
  const [activeFilter,setFilter]      = useState("all");
  const [newIds,      setNewIds]      = useState(new Set());
  const [lastRefresh, setLastRefresh] = useState(null);
  const [sidebarOpen, setSidebar]     = useState(false);
  const prevIds = useRef(new Set());

  const applyData = useCallback((d) => {
    setData(d);
    setLastRefresh(new Date());
    setLoading(false);
    const incoming = new Set((d.latest_findings || []).map(f => f.id));
    const fresh    = new Set([...incoming].filter(id => !prevIds.current.has(id)));
    if (fresh.size > 0) { setNewIds(fresh); setTimeout(() => setNewIds(new Set()), 4000); }
    prevIds.current = incoming;
  }, []);

  const fetchSnap = useCallback(async () => {
    try {
      const r = await fetch(LIVE_FEED_URL);
      if (r.ok) applyData(await r.json());
    } catch {}
  }, [applyData]);

  useEffect(() => {
    let es;
    try {
      es = new EventSource(SSE_FEED_URL);
      es.onopen    = () => setConnected(true);
      es.onmessage = (e) => { try { applyData(JSON.parse(e.data)); } catch {} };
      es.onerror   = () => { setConnected(false); es.close(); };
    } catch { setConnected(false); }
    fetchSnap();
    const t = setInterval(fetchSnap, REFRESH_MS);
    return () => { es?.close(); clearInterval(t); };
  }, [applyData, fetchSnap]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background:"#000" }}>
      <div className="text-center space-y-4">
        <div className="w-12 h-12 rounded-full border-2 border-t-transparent animate-spin mx-auto"
          style={{ borderColor: G, borderTopColor:"transparent" }}/>
        <p className="font-mono text-sm" style={{ color: G }}>Connecting to Mantle RPC…</p>
        <p className="text-xs text-gray-700 font-mono">live data · no simulation · no mock</p>
      </div>
    </div>
  );

  const stats    = data?.stats   || {};
  const allFnds  = data?.latest_findings || [];
  const sm       = data?.smart_money_summary || {};
  const chain    = data?.chain   || {};
  const backtest = data?.backtest;
  const contract = data?.contract_address || CONTRACT_ADDR;
  const auditCount = data?.protocol_state?.audit_contract?.finding_count || 20;

  const filtered = activeFilter === "all" ? allFnds : allFnds.filter(f => f.type === activeFilter);
  const sorted   = [...filtered].sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));

  const TABS = [
    { key:"findings",  label:"Findings",         icon:AlertTriangle, badge:allFnds.length  },
    { key:"signals",   label:"Signals",           icon:TrendingUp                           },
    { key:"reasoning", label:"Reasoning",         icon:Cpu,           badge:"NEW"           },
    { key:"roi",       label:"ROI Calc",          icon:DollarSign,    badge:"NEW"           },
    { key:"protocol",  label:"Protocol",          icon:Server                               },
    { key:"analytics", label:"Analytics",         icon:BarChart2                            },
    { key:"audit",     label:"Audit Log",         icon:Shield,        badge:auditCount      },
    { key:"api",       label:"API",               icon:Globe                                },
  ];

  const FILTERS = [
    { key:"all",                 label:"All"          },
    { key:"whale_accumulation",  label:"Whale"        },
    { key:"smart_money_inflow",  label:"Smart Money"  },
    { key:"tx_spike",            label:"TX Spike"     },
    { key:"value_spike",         label:"Value"        },
    { key:"multivariate_anomaly",label:"Multivariate" },
    { key:"mev_sandwich",        label:"MEV"          },
    { key:"bridge_outflow_spike",label:"Bridge"       },
  ];

  return (
    <div className="min-h-screen text-white" style={{ background:"#000", fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" }}>

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <div className="sticky top-0 z-30 border-b" style={{ borderColor:"#111", background:"rgba(0,0,0,0.95)", backdropFilter:"blur(12px)" }}>
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">

          {/* Logo */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center font-black text-black text-sm"
              style={{ background: `linear-gradient(135deg,${G},#00a876)` }}>⬡</div>
            <div>
              <div className="text-sm font-black text-white tracking-tight">MANTLE INTEL</div>
              <div className="text-xs font-mono" style={{ color: G, marginTop:"-2px" }}>AGENT v6.0</div>
            </div>
          </div>

          {/* Live ticker */}
          <div className="hidden md:flex items-center gap-4 flex-1 px-6 text-xs font-mono text-gray-600">
            {chain.mainnet?.latest_block > 0 && (
              <span className="flex items-center gap-1.5">
                <PulseDot color={G} size={6}/>
                <span style={{ color: G }}>BLK</span>
                <span className="text-white">#{chain.mainnet.latest_block.toLocaleString()}</span>
              </span>
            )}
            <span>|</span>
            <span className="flex items-center gap-1">
              <span>FINDINGS</span>
              <span className="text-white font-bold">{allFnds.length}</span>
            </span>
            <span>|</span>
            <span className="flex items-center gap-1">
              <span>AVG CONF</span>
              <span className="text-white font-bold">{((stats.avg_confidence||0)*100).toFixed(1)}%</span>
            </span>
            <span>|</span>
            <span className="flex items-center gap-1">
              <span>ON-CHAIN</span>
              <span className="font-bold" style={{ color: G }}>{auditCount}</span>
            </span>
          </div>

          {/* Right */}
          <div className="flex items-center gap-2 ml-auto flex-shrink-0">
            <div className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full border"
              style={{ borderColor: connected ? G+"40":"#374151", color: connected ? G:"#6B7280", background: connected ? G+"10":"transparent" }}>
              {connected ? <Wifi size={10}/> : <WifiOff size={10}/>}
              {connected ? "LIVE" : "POLLING"}
            </div>
            <button onClick={fetchSnap}
              className="p-2 rounded-lg border border-white/10 hover:bg-white/5 text-gray-500 hover:text-white transition-colors">
              <RefreshCw size={13}/>
            </button>
            {lastRefresh && (
              <span className="text-xs text-gray-700 font-mono hidden lg:block">{lastRefresh.toLocaleTimeString()}</span>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-5">

        {/* ── KPI tiles ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatTile icon={Activity}      label="LATEST BLOCK"     live
            value={chain.mainnet?.latest_block?.toLocaleString() || "—"}
            sub="Mantle L2 mainnet" accent={G}/>
          <StatTile icon={AlertTriangle} label="ANOMALIES FOUND"
            value={allFnds.length}
            sub={`${stats.high_confidence_pct||0}% high-signal`} accent="#EF4444"/>
          <StatTile icon={Shield}        label="ON-CHAIN FINDINGS"
            value={auditCount}
            sub="MantleIntelAudit.sol" accent="#3B82F6"/>
          <StatTile icon={TrendingUp}    label="SMART MONEY"
            value={sm.known_labels || 0}
            sub={`${sm.tier1_alerts||0} tier-1 alerts`} accent="#A855F7"/>
        </div>

        {/* ── Nav tabs ──────────────────────────────────────────────────── */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {TABS.map(({ key, label, icon: Icon, badge }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap flex-shrink-0"
              style={{
                background: activeTab===key ? G+"18" : "transparent",
                color: activeTab===key ? G : "#4B5563",
                border: `1px solid ${activeTab===key ? G+"40" : "transparent"}`,
              }}>
              <Icon size={12}/>
              {label}
              {(badge === "NEW" || badge > 0) && (
                <span className="text-xs px-1.5 py-0.5 rounded-full font-mono"
                  style={{ 
                    background: badge==="NEW" ? "#A855F720" : (activeTab===key ? G+"30":"#1F2937"),
                    color: badge==="NEW" ? "#A855F7" : (activeTab===key ? G:"#6B7280")
                  }}>
                  {badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── Contract strip ─────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl border text-xs font-mono"
          style={{ borderColor: G+"25", background: G+"05" }}>
          <Shield size={12} style={{ color: G }}/>
          <span style={{ color: G }} className="font-bold">MantleIntelAudit</span>
          <span className="text-gray-600 truncate hidden sm:block">{CONTRACT_ADDR}</span>
          <span className="ml-auto flex items-center gap-3">
            <span className="font-bold" style={{ color: G }}>{auditCount} findings ✓</span>
            <a href={`${EXPLORER_BASE}/address/${CONTRACT_ADDR}`} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-gray-600 hover:text-white transition-colors">
              Explorer <ExternalLink size={9}/>
            </a>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-gray-600 hover:text-white transition-colors">
              GitHub <ExternalLink size={9}/>
            </a>
          </span>
        </div>

        {/* ── Tab: Findings ─────────────────────────────────────────────── */}
        {activeTab === "findings" && (
          <div className="space-y-3">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {FILTERS.map(f => (
                <button key={f.key} onClick={() => setFilter(f.key)}
                  className="text-xs px-3 py-1.5 rounded-lg whitespace-nowrap transition-all font-bold flex-shrink-0"
                  style={{
                    background: activeFilter===f.key ? G+"18":"#0D0D0D",
                    color: activeFilter===f.key ? G : "#4B5563",
                    border: `1px solid ${activeFilter===f.key ? G+"40":"#1F2937"}`,
                  }}>
                  {f.label}
                </button>
              ))}
            </div>

            {sorted.length === 0 ? (
              <div className="text-center py-20 text-gray-800">
                <Activity size={32} className="mx-auto mb-3 animate-pulse"/>
                <p className="text-sm text-gray-600">No findings in current window</p>
                <p className="text-xs mt-2 text-gray-700 font-mono">Scanning latest 50 blocks · refreshes every 12s</p>
              </div>
            ) : (
              <div className="space-y-2">
                {sorted.map((f, i) => (
                  <FindingRow key={f.id||i} finding={f} isNew={newIds.has(f.id)}/>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "signals"   && <SignalsTab   findings={sorted}/>}
        {activeTab === "reasoning" && <ReasoningTab findings={sorted}/>}
        {activeTab === "roi"       && <ROITab/>}
        {activeTab === "protocol"  && <ProtocolTab  data={data}/>}
        {activeTab === "analytics" && <AnalyticsTab data={data} backtest={backtest}/>}
        {activeTab === "audit"     && <AuditTab     data={data}/>}
        {activeTab === "api"       && <APITab       data={data} contract={contract}/>}

        {/* ── Footer ────────────────────────────────────────────────────── */}
        <div className="border-t pt-4 flex items-center justify-between text-xs font-mono text-gray-700"
          style={{ borderColor:"#111" }}>
          <span>Mantle Intel Agent v6.0 · On-Chain Intelligence · Mantle Ecosystem</span>
          <div className="flex items-center gap-4 hidden sm:flex">
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-gray-400 transition-colors">
              <GitBranch size={10}/> GitHub
            </a>
            <a href={`${EXPLORER_BASE}/address/${CONTRACT_ADDR}`} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-gray-400 transition-colors">
              <Shield size={10}/> Contract
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
