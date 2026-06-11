import { useState, useEffect, useRef, useCallback } from "react";
import {
  AlertTriangle, Activity, Database, Shield, ExternalLink,
  RefreshCw, TrendingUp, Zap, Globe, GitBranch, BarChart2,
  ChevronDown, ChevronUp, Radio, Filter, Clock, Wifi, WifiOff,
  CheckCircle, Server, Link
} from "lucide-react";

// ── Config ───────────────────────────────────────────────────────────────────
const LIVE_FEED_URL  = "/api/live-feed";
const SSE_FEED_URL   = "/api/live-feed?stream=1";
const REFRESH_MS     = 15_000;   // fallback polling interval

const ANOMALY_COLORS = {
  whale_accumulation:   { bg: "bg-blue-900/40",   border: "border-blue-500",  badge: "bg-blue-600",   label: "🐋 Whale Accumulation" },
  whale_distribution:   { bg: "bg-orange-900/40", border: "border-orange-500",badge: "bg-orange-600", label: "⚠️ Whale Distribution" },
  smart_money_inflow:   { bg: "bg-purple-900/40", border: "border-purple-500",badge: "bg-purple-600", label: "🧠 Smart Money" },
  tx_spike:             { bg: "bg-green-900/40",  border: "border-green-500", badge: "bg-green-600",  label: "📈 TX Spike" },
  value_spike:          { bg: "bg-yellow-900/40", border: "border-yellow-500",badge: "bg-yellow-600", label: "💰 Value Spike" },
  multivariate_anomaly: { bg: "bg-red-900/40",    border: "border-red-500",   badge: "bg-red-600",    label: "🔍 Multivariate" },
};
const DEFAULT_COLORS = { bg: "bg-gray-800/40", border: "border-gray-600", badge: "bg-gray-600", label: "⚡ Anomaly" };

// ── Helpers ───────────────────────────────────────────────────────────────────

function useCounter(value) {
  const [display, setDisplay] = useState(value);
  const prev = useRef(value);
  useEffect(() => {
    if (value === prev.current) return;
    const start = prev.current;
    const end   = value;
    const diff  = end - start;
    if (Math.abs(diff) > 500) { setDisplay(end); prev.current = end; return; }
    const steps = 20;
    let step = 0;
    const t = setInterval(() => {
      step++;
      setDisplay(Math.round(start + (diff * step) / steps));
      if (step >= steps) { clearInterval(t); prev.current = end; }
    }, 30);
    return () => clearInterval(t);
  }, [value]);
  return display;
}

function TimeSince({ timestamp }) {
  const [ago, setAgo] = useState("");
  useEffect(() => {
    const update = () => {
      if (!timestamp) return setAgo("unknown");
      const diff = Date.now() - new Date(timestamp).getTime();
      const secs = Math.floor(diff / 1000);
      if (secs < 60) return setAgo(`${secs}s ago`);
      const mins = Math.floor(secs / 60);
      if (mins < 60) return setAgo(`${mins}m ago`);
      const hrs = Math.floor(mins / 60);
      return setAgo(`${hrs}h ago`);
    };
    update();
    const t = setInterval(update, 5000);
    return () => clearInterval(t);
  }, [timestamp]);
  return <span className="text-xs text-gray-500 font-mono">{ago}</span>;
}

function ConfidenceBar({ value }) {
  const pct   = Math.round(value * 100);
  const color = pct >= 90 ? "bg-red-500" : pct >= 80 ? "bg-orange-500" : pct >= 70 ? "bg-yellow-500" : "bg-blue-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-300 w-10 text-right">{pct}%</span>
    </div>
  );
}

function LiveBadge({ connected }) {
  return (
    <span className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full font-medium transition-colors
      ${connected ? "text-green-400 bg-green-900/30 border border-green-800/50" : "text-yellow-500 bg-yellow-900/30 border border-yellow-800/50"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-green-500 animate-pulse" : "bg-yellow-500"}`} />
      {connected ? "Live RPC" : "Polling"}
    </span>
  );
}

function FindingCard({ finding, isNew }) {
  const [expanded, setExpanded] = useState(false);
  const colors = ANOMALY_COLORS[finding.type] || DEFAULT_COLORS;
  const audit  = finding.audit || {};
  const isHighConf = finding.confidence >= 0.85;

  return (
    <div
      className={`${colors.bg} border ${colors.border} rounded-lg p-4 cursor-pointer 
        hover:brightness-110 transition-all duration-200
        ${isNew ? "ring-1 ring-white/30 shadow-lg shadow-blue-900/20" : ""}`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colors.badge} text-white whitespace-nowrap`}>
              {colors.label}
            </span>
            {isHighConf && (
              <span className="text-xs bg-red-900/80 text-red-300 border border-red-700 px-1.5 py-0.5 rounded-full">
                🔥 High Signal
              </span>
            )}
            <span className="text-xs text-gray-400 font-mono">Block {(finding.block || 0).toLocaleString()}</span>
            {audit.status === "recorded" && (
              <span className="text-xs bg-green-900/70 text-green-300 px-1.5 py-0.5 rounded-full flex items-center gap-1">
                <Shield size={9} /> On-Chain ✓
              </span>
            )}
            {audit.status === "testnet" && (
              <span className="text-xs bg-blue-900/50 text-blue-400 px-1.5 py-0.5 rounded-full flex items-center gap-1">
                <CheckCircle size={9} /> Testnet ✓
              </span>
            )}
          </div>
          <div className="text-xs text-gray-200 mb-2 font-medium leading-tight">
            {finding.title || finding.type}
          </div>
          <ConfidenceBar value={finding.confidence || 0} />
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <TimeSince timestamp={finding.timestamp} />
          {expanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3 border-t border-white/10 pt-3">
          <p className="text-sm text-gray-200 leading-relaxed">{finding.insight || finding.description}</p>

          {finding.large_transfers?.length > 0 && (
            <div className="bg-gray-900/60 rounded-lg p-3 space-y-1.5">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Large Transfers</div>
              {finding.large_transfers.slice(0, 5).map((t, i) => (
                <div key={i} className="flex items-center gap-1 text-xs font-mono">
                  <span className="text-blue-400 truncate max-w-[35%]">{t.label_from !== "unknown" ? t.label_from : t.from?.slice(0,10)+"..."}</span>
                  <span className="text-gray-600">→</span>
                  <span className="text-green-400 truncate max-w-[35%]">{t.label_to !== "unknown" ? t.label_to : t.to?.slice(0,10)+"..."}</span>
                  <span className="text-yellow-400 ml-auto whitespace-nowrap">${(t.value_usd||0).toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}

          {finding.raw_metrics && (
            <div className="bg-gray-900/60 rounded-lg p-3">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Raw Metrics</div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1 text-xs font-mono text-gray-400">
                {Object.entries(finding.raw_metrics).slice(0, 9).map(([k, v]) => (
                  <div key={k} className="flex gap-1">
                    <span className="text-gray-600">{k.replace(/_/g,"_")}:</span>
                    <span>{typeof v === "number" ? (v > 1000 ? v.toLocaleString() : v) : JSON.stringify(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-3 text-xs text-gray-600 flex-wrap pt-1">
            <span className="font-mono">{(finding.hash || "").slice(0, 24)}...</span>
            {audit.explorer && (
              <a href={audit.explorer} target="_blank" rel="noopener noreferrer"
                 onClick={e => e.stopPropagation()}
                 className="flex items-center gap-1 text-blue-400 hover:text-blue-300">
                <ExternalLink size={10} /> Verify on Mantle Explorer
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, color = "text-white", pulse, raw }) {
  const animated = useCounter(typeof raw === "number" ? raw : 0);
  const display  = typeof raw === "number" ? animated.toLocaleString() : value;
  return (
    <div className="bg-gray-800/50 border border-gray-700/60 rounded-xl p-4 hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-2 mb-1.5">
        <Icon size={13} className="text-gray-500" />
        <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">{label}</span>
        {pulse && <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse ml-auto" />}
      </div>
      <div className={`text-2xl font-bold font-mono ${color}`}>{display}</div>
      {sub && <div className="text-xs text-gray-600 mt-1">{sub}</div>}
    </div>
  );
}

function LiveBlockFeed({ recentBlocks }) {
  if (!recentBlocks?.length) return null;
  return (
    <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Server size={14} className="text-green-400" />
        <h3 className="text-sm font-semibold text-white">Live Block Feed — Mantle Mainnet</h3>
        <span className="text-xs text-gray-600 ml-auto">~2s block time</span>
      </div>
      <div className="space-y-1 max-h-52 overflow-y-auto no-scrollbar">
        {recentBlocks.map((b, i) => (
          <div key={b.block_num}
            className={`flex items-center gap-3 text-xs font-mono py-1.5 px-2 rounded transition-colors
              ${b.is_anomaly ? "bg-red-900/30 border border-red-800/40 text-red-300" : "hover:bg-gray-800/50 text-gray-400"}`}>
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${i === 0 ? "bg-green-500 animate-pulse" : b.is_anomaly ? "bg-red-500" : "bg-gray-700"}`} />
            <span className="text-gray-300 w-20">{b.block_num?.toLocaleString()}</span>
            <span className="text-gray-600 w-10 text-right">{b.tx_count}tx</span>
            <span className={`w-20 text-right ${b.value_usd > 0 ? "text-yellow-500" : "text-gray-700"}`}>
              ${b.value_usd?.toLocaleString()}
            </span>
            {b.is_anomaly && <span className="text-red-400 ml-auto">⚠ anomaly</span>}
            <span className="text-gray-700 ml-auto"><TimeSince timestamp={b.timestamp} /></span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TypeBreakdown({ breakdown }) {
  if (!breakdown || Object.keys(breakdown).length === 0) return (
    <div className="text-xs text-gray-600 text-center py-4">No findings yet in this window</div>
  );
  const total = Object.values(breakdown).reduce((a, b) => a + b, 0);
  const colors = {
    whale_accumulation: "bg-blue-600",
    whale_distribution: "bg-orange-600",
    smart_money_inflow: "bg-purple-600",
    tx_spike:           "bg-green-600",
    value_spike:        "bg-yellow-600",
    multivariate_anomaly: "bg-red-600",
  };
  return (
    <div className="space-y-2">
      {Object.entries(breakdown).sort(([,a],[,b]) => b - a).map(([type, count]) => (
        <div key={type} className="flex items-center gap-2">
          <div className="w-28 text-xs text-gray-400 truncate">{type.replace(/_/g, " ")}</div>
          <div className="flex-1 bg-gray-700 rounded-full h-1.5">
            <div className={`${colors[type] || "bg-gray-500"} h-1.5 rounded-full transition-all duration-500`}
                 style={{ width: `${(count / total) * 100}%` }} />
          </div>
          <div className="text-xs font-mono text-gray-400 w-5 text-right">{count}</div>
        </div>
      ))}
    </div>
  );
}

function FilterBar({ activeFilter, setFilter }) {
  const filters = [
    { key: "all", label: "All" },
    { key: "whale_accumulation",   label: "🐋 Whale" },
    { key: "smart_money_inflow",   label: "🧠 Smart Money" },
    { key: "tx_spike",             label: "📈 TX Spike" },
    { key: "value_spike",          label: "💰 Value" },
    { key: "multivariate_anomaly", label: "🔍 Multi" },
  ];
  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
      <Filter size={12} className="text-gray-600 flex-shrink-0" />
      {filters.map(f => (
        <button key={f.key} onClick={() => setFilter(f.key)}
          className={`text-xs px-2.5 py-1 rounded-full whitespace-nowrap transition-colors flex-shrink-0
            ${activeFilter === f.key ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}>
          {f.label}
        </button>
      ))}
    </div>
  );
}

function BacktestPanel({ backtest }) {
  if (!backtest) return null;
  return (
    <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-1 flex items-center gap-2">
        <GitBranch size={14} className="text-green-400" /> Live Backtest Performance
        <span className="text-xs bg-green-900/40 text-green-500 border border-green-800/40 px-1.5 py-0.5 rounded-full ml-auto">
          Real Mantle Data ✓
        </span>
      </h3>
      <p className="text-xs text-gray-600 mb-3">{backtest.block_range} · {backtest.blocks_scanned?.toLocaleString()} blocks · {backtest.note}</p>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {[
          { metric: "Precision",  value: `${backtest.precision_pct}%`,  color: "text-green-400" },
          { metric: "Recall",     value: `${backtest.recall_pct}%`,     color: "text-blue-400"  },
          { metric: "F1 Score",   value: backtest.f1_score?.toFixed(4), color: "text-purple-400"},
          { metric: "TP",         value: backtest.tp,                   color: "text-green-400" },
          { metric: "FP",         value: backtest.fp,                   color: "text-red-400"   },
          { metric: "FN",         value: backtest.fn,                   color: "text-yellow-400"},
        ].map(({ metric, value, color }) => (
          <div key={metric} className="bg-gray-900/50 rounded-lg p-2.5 text-center">
            <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
            <div className="text-xs text-gray-500 mt-0.5">{metric}</div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-700 mt-2">{backtest.methodology}</p>
    </div>
  );
}

function IntelFeedPanel({ contract, intelFeed }) {
  const [copied, setCopied] = useState(false);
  const snippet = `// Mantle Intel Agent — Live Feed Integration
// REST endpoint (updates every ~15s from real Mantle RPC)
const res = await fetch("https://mantle-intel-agent.vercel.app/api/live-feed");
const data = await res.json();
console.log("Latest findings:", data.latest_findings);
console.log("Latest block:", data.chain.mainnet.latest_block);

// SSE stream (real-time push)
const es = new EventSource("https://mantle-intel-agent.vercel.app/api/live-feed?stream=1");
es.onmessage = (e) => {
  const { latest_findings, chain } = JSON.parse(e.data);
  console.log(\`Block \${chain.mainnet.latest_block}: \${latest_findings.length} anomalies\`);
};

// On-chain verification (Mantle Sepolia testnet)
const contract = new ethers.Contract("${contract}", ABI, provider);
const count = await contract.findingCount();  // live on-chain count
const page  = await contract.getPublicFindings(1, 20);  // paginated`;

  return (
    <div className="bg-gray-800/40 border border-gray-700/60 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Globe size={16} className="text-blue-400" />
        <h3 className="text-sm font-semibold text-white">Public Intel Feed API</h3>
        <span className="text-xs bg-green-900/40 text-green-400 border border-green-800/40 px-2 py-0.5 rounded-full ml-auto">
          Live Edge Function ✓
        </span>
      </div>
      <p className="text-xs text-gray-400 mb-4 leading-relaxed">
        Serverless edge function on Vercel — queries Mantle RPC directly. No API key. Permissionless.
        Refreshes from real chain data on every request.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">REST Endpoint</div>
          <code className="text-xs text-green-400">/api/live-feed</code>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">SSE Stream</div>
          <code className="text-xs text-blue-400">/api/live-feed?stream=1</code>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">On-Chain Query</div>
          <code className="text-xs text-purple-400">getPublicFindings(offset, limit)</code>
        </div>
      </div>
      <div className="bg-gray-950/80 rounded-lg p-3 relative">
        <button onClick={() => { navigator.clipboard.writeText(snippet); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
          className="absolute top-2 right-2 text-xs text-gray-500 hover:text-white px-2 py-1 bg-gray-800 rounded transition-colors">
          {copied ? "Copied!" : "Copy"}
        </button>
        <pre className="text-xs font-mono text-gray-300 overflow-x-auto whitespace-pre-wrap leading-relaxed pr-14">{snippet}</pre>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [data, setData]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [liveConnected, setConnected] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [activeTab, setActiveTab]     = useState("findings");
  const [newFindingIds, setNewIds]    = useState(new Set());
  const prevIds = useRef(new Set());
  const sseRef  = useRef(null);

  const applyData = useCallback((d) => {
    setData(d);
    setLastRefresh(new Date());
    setLoading(false);

    // Highlight new findings
    const incoming = new Set((d.latest_findings || []).map(f => f.id));
    const fresh    = new Set([...incoming].filter(id => !prevIds.current.has(id)));
    if (fresh.size > 0) setNewIds(fresh);
    prevIds.current = incoming;
    setTimeout(() => setNewIds(new Set()), 4000);
  }, []);

  const fetchSnap = useCallback(async () => {
    try {
      const r = await fetch(LIVE_FEED_URL);
      if (r.ok) applyData(await r.json());
    } catch {}
  }, [applyData]);

  // SSE connection
  useEffect(() => {
    let es;
    const connectSSE = () => {
      try {
        es = new EventSource(SSE_FEED_URL);
        es.onopen    = () => setConnected(true);
        es.onmessage = (e) => { try { applyData(JSON.parse(e.data)); } catch {} };
        es.onerror   = () => { setConnected(false); es.close(); };
        sseRef.current = es;
      } catch {
        setConnected(false);
      }
    };
    connectSSE();

    // Fallback polling
    fetchSnap();
    const poll = setInterval(fetchSnap, REFRESH_MS);

    return () => { es?.close(); clearInterval(poll); };
  }, [applyData, fetchSnap]);

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-400 text-sm">Connecting to Mantle RPC...</p>
        <p className="text-gray-700 text-xs mt-1">Fetching live block data</p>
      </div>
    </div>
  );

  const stats        = data?.stats || {};
  const allFindings  = data?.latest_findings || [];
  const sm           = data?.smart_money_summary || {};
  const contract     = data?.contract_address || "Not deployed";
  const recentBlocks = data?.recent_blocks || [];
  const backtest     = data?.backtest;
  const chain        = data?.chain || {};

  const findings = activeFilter === "all"
    ? allFindings
    : allFindings.filter(f => f.type === activeFilter);
  const sortedFindings = [...findings].sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));

  const tabs = [
    { key: "findings",   label: "Findings",    icon: AlertTriangle },
    { key: "blocks",     label: "Live Blocks",  icon: Activity      },
    { key: "analytics",  label: "Analytics",   icon: BarChart2     },
    { key: "api",        label: "Intel API",   icon: Globe         },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans">
      {/* Header */}
      <div className="border-b border-gray-800/80 bg-gray-950/95 sticky top-0 z-20 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <h1 className="text-base font-bold text-white flex items-center gap-2 flex-wrap">
                <span className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center text-xs font-black flex-shrink-0">⬡</span>
                <span>Mantle Intel Agent</span>
                <span className="text-xs bg-blue-900/50 text-blue-400 border border-blue-800/50 px-1.5 py-0.5 rounded font-mono">v3.0</span>
              </h1>
              <p className="text-xs text-gray-600">Autonomous On-Chain Intelligence · Alpha &amp; Data Track · Mantle Network</p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <LiveBadge connected={liveConnected} />
              {chain.mainnet?.latest_block > 0 && (
                <span className="text-xs font-mono text-gray-600 hidden sm:block">
                  #{chain.mainnet.latest_block?.toLocaleString()}
                </span>
              )}
              <button onClick={fetchSnap} className="text-gray-500 hover:text-white transition-colors p-1.5 hover:bg-gray-800 rounded">
                <RefreshCw size={13} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-5 space-y-5">
        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard icon={Activity}      label="Latest Block"
                    value={chain.mainnet?.latest_block?.toLocaleString() || "0"}
                    raw={chain.mainnet?.latest_block}
                    sub="Mantle L2 mainnet" pulse />
          <StatCard icon={Database}      label="Blocks Scanned"
                    value={(stats.blocks_processed || 0).toLocaleString()}
                    raw={stats.blocks_processed}
                    sub={`~${stats.avg_tx_per_block || 0} avg tx/block`} />
          <StatCard icon={AlertTriangle} label="Findings (Window)"
                    value={allFindings.length}
                    sub={`${stats.high_confidence_pct || 0}% high-signal`} color="text-orange-400" />
          <StatCard icon={TrendingUp}    label="Smart Money"
                    value={sm.known_labels || 0}
                    sub={`${sm.tier1_alerts || 0} tier-1 alerts`} color="text-purple-400" />
        </div>

        {/* Contract info */}
        <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4 flex items-start gap-3">
          <Shield size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <p className="text-sm font-semibold text-green-400">MantleIntelAudit.sol</p>
              <span className="text-xs bg-blue-900/40 text-blue-400 border border-blue-800/40 px-1.5 py-0.5 rounded-full">
                Deployed · Mantle Sepolia Testnet
              </span>
              <span className="text-xs bg-green-900/40 text-green-500 border border-green-800/40 px-1.5 py-0.5 rounded-full">
                getPublicFindings() ✓
              </span>
            </div>
            <p className="text-xs font-mono text-gray-400 break-all">{contract}</p>
            <div className="flex items-center gap-3 mt-1.5 flex-wrap text-xs text-gray-600">
              <span>Every finding SHA256-hashed &amp; recorded on-chain</span>
              <a href={`https://sepolia.mantlescan.xyz/address/${contract}`}
                 target="_blank" rel="noopener noreferrer"
                 className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1">
                <ExternalLink size={10} /> Explorer
              </a>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="text-xs text-gray-600">This window</div>
            <div className="text-lg font-bold font-mono text-green-400">{allFindings.length}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-gray-800 overflow-x-auto no-scrollbar">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap flex-shrink-0
                ${activeTab === key ? "border-blue-500 text-white" : "border-transparent text-gray-500 hover:text-gray-300"}`}>
              <Icon size={13} /> {label}
              {key === "findings" && allFindings.length > 0 && (
                <span className="text-xs bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded-full">{allFindings.length}</span>
              )}
            </button>
          ))}
          <div className="ml-auto text-xs text-gray-700 pb-2 flex-shrink-0">
            {lastRefresh ? `↻ ${lastRefresh.toLocaleTimeString()}` : ""}
          </div>
        </div>

        {/* Findings Tab */}
        {activeTab === "findings" && (
          <div className="space-y-3">
            <FilterBar activeFilter={activeFilter} setFilter={setActiveFilter} />
            {sortedFindings.length === 0 ? (
              <div className="text-center py-16 text-gray-700">
                <Activity size={36} className="mx-auto mb-3 animate-pulse" />
                <p className="text-sm">No {activeFilter === "all" ? "" : activeFilter.replace(/_/g," ")} findings in current window</p>
                <p className="text-xs mt-2 text-gray-800">Pipeline scans last 50 blocks · refreshes every 15s</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {sortedFindings.map((f, i) => (
                  <FindingCard key={f.id || i} finding={f} isNew={newFindingIds.has(f.id)} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Live Blocks Tab */}
        {activeTab === "blocks" && (
          <div className="space-y-4">
            <LiveBlockFeed recentBlocks={recentBlocks} />
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Mainnet Stats</h3>
                <div className="space-y-2 text-xs">
                  {[
                    ["Latest Block", chain.mainnet?.latest_block?.toLocaleString()],
                    ["Avg TX/Block",  stats.avg_tx_per_block],
                    ["RPC",          "rpc.mantle.xyz"],
                    ["Chain ID",     "5000"],
                    ["Block Time",   "~2s"],
                  ].map(([k,v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-500">{k}</span>
                      <span className="font-mono text-gray-300">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Testnet (Sepolia)</h3>
                <div className="space-y-2 text-xs">
                  {[
                    ["Latest Block",   chain.testnet?.latest_block?.toLocaleString()],
                    ["Audit Contract", contract?.slice(0,14)+"..."],
                    ["NFT Contract",   "0xa1A134...742f"],
                    ["RPC",           "rpc.sepolia.mantle.xyz"],
                    ["Chain ID",       "5003"],
                  ].map(([k,v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-500">{k}</span>
                      <span className="font-mono text-gray-300">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === "analytics" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <BarChart2 size={14} className="text-blue-400" /> Findings by Type
                </h3>
                <TypeBreakdown breakdown={stats.types_breakdown} />
              </div>
              <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <TrendingUp size={14} className="text-purple-400" /> Smart Money Intel
                </h3>
                <div className="space-y-3">
                  {[
                    { label: "Wallets Tracked",    value: `${sm.tracked_wallets || 67}` },
                    { label: "Known Labels",        value: `${sm.known_labels || 0} wallets` },
                    { label: "Tier-1 Alerts",       value: sm.tier1_alerts || 0 },
                    { label: "Total Flow (Window)", value: `$${((stats.total_value_usd || 0)).toLocaleString()}` },
                    { label: "Avg Confidence",      value: `${((stats.avg_confidence || 0) * 100).toFixed(1)}%` },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">{label}</span>
                      <span className="font-mono text-white font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <BacktestPanel backtest={backtest} />
          </div>
        )}

        {/* API Tab */}
        {activeTab === "api" && (
          <div className="space-y-4">
            <IntelFeedPanel contract={contract} intelFeed={data?.intel_feed} />
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <Radio size={14} className="text-green-400" /> Live Feed Snapshot
                <span className="text-xs text-gray-600 ml-auto">GET /api/live-feed</span>
              </h3>
              <div className="bg-gray-950/80 rounded-lg p-3 overflow-x-auto max-h-72 overflow-y-auto">
                <pre className="text-xs font-mono text-gray-300 leading-relaxed">
                  {JSON.stringify({
                    live: data?.live,
                    last_updated: data?.last_updated,
                    chain: data?.chain,
                    stats: { blocks_processed: stats.blocks_processed, findings_total: stats.findings_total, avg_tx_per_block: stats.avg_tx_per_block },
                    findings_preview: sortedFindings.slice(0,2).map(f => ({ id: f.id, type: f.type, block: f.block, confidence: f.confidence })),
                    backtest: backtest ? { precision_pct: backtest.precision_pct, recall_pct: backtest.recall_pct, f1_score: backtest.f1_score, mode: backtest.mode } : null,
                  }, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-gray-800 pt-4 border-t border-gray-900">
          Mantle Intel Agent v3.0 · Turing Test Hackathon 2026 · Alpha &amp; Data Track (Mirana Ventures)
          · <a href="https://github.com/sodiq-code/mantle-intel-agent" target="_blank" rel="noopener noreferrer" className="hover:text-gray-600">GitHub</a>
          · <a href="https://sepolia.mantlescan.xyz/address/0x03C88A1060626581854DB94e955a6be291782abb" target="_blank" rel="noopener noreferrer" className="hover:text-gray-600">Contract</a>
        </div>
      </div>
    </div>
  );
}
