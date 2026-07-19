import { useState, useEffect, useRef, useCallback } from "react";
import {
  AlertTriangle, Activity, Shield, ExternalLink,
  RefreshCw, TrendingUp, BarChart2,
  Wifi, WifiOff, Server, DollarSign, Cpu, Globe, GitBranch,
  AlertCircle, Zap
} from "lucide-react";

import { G, PulseDot, StatTile, FindingRow, IncidentCard, EXPLORER_BASE } from "./components/Shared.jsx";
import { SignalsTab } from "./components/SignalsTab.jsx";
import { ReasoningTab } from "./components/ReasoningTab.jsx";
import { ProtocolTab } from "./components/ProtocolTab.jsx";
import { AnalyticsTab } from "./components/AnalyticsTab.jsx";
import { AuditTab } from "./components/AuditTab.jsx";
import { ROITab } from "./components/ROITab.jsx";
import { APITab } from "./components/APITab.jsx";

const LIVE_FEED_URL = "/api/live-feed";
const SSE_FEED_URL  = "/api/live-feed?stream=1";
const FALLBACK_URL   = "/dashboard.json";
const REFRESH_MS    = 12_000;
const CONTRACT_ADDR = "0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b";
const GITHUB_URL    = "https://github.com/sodiq-code/mantle-intel-agent";

export default function App() {
  const [data,        setData]        = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [connected,   setConnected]   = useState(false);
  const [demoMode,    setDemoMode]    = useState(false);
  const [error,       setError]       = useState(null);
  const [activeTab,   setActiveTab]   = useState("findings");
  const [activeFilter,setFilter]      = useState("all");
  const [newIds,      setNewIds]      = useState(new Set());
  const [lastRefresh, setLastRefresh] = useState(null);
  const prevIds = useRef(new Set());

  const applyData = useCallback((d, isDemo = false) => {
    setData(d);
    setDemoMode(isDemo);
    setError(null);
    setLastRefresh(new Date());
    setLoading(false);
    const incoming = new Set((d.active_incidents || []).map(i => i.id));
    const fresh    = new Set([...incoming].filter(id => !prevIds.current.has(id)));
    if (fresh.size > 0) { setNewIds(fresh); setTimeout(() => setNewIds(new Set()), 4000); }
    prevIds.current = incoming;
  }, []);

  const API_KEY = import.meta.env.VITE_API_KEY || "";

  const fetchSnap = useCallback(async () => {
    try {
      const r = await fetch(LIVE_FEED_URL, { headers: { "X-API-KEY": API_KEY } });
      if (!r.ok) throw new Error(`API ${r.status}`);
      const json = await r.json();
      if (json.error) throw new Error(json.error);
      applyData(json, false);
      return true;
    } catch (e) {
      // Fallback to static dashboard.json so the dashboard is always usable
      try {
        const fb = await fetch(FALLBACK_URL);
        if (fb.ok) {
          const json = await fb.json();
          applyData(json, true);
          setError(`Live API unavailable — showing cached snapshot. (${e.message})`);
        } else {
          throw new Error("No data sources available");
        }
      } catch (e2) {
        setError(`Connection failed: ${e2.message}. Retrying...`);
        setLoading(false);
      }
      return false;
    }
  }, [applyData, API_KEY]);

  useEffect(() => {
    let active = true;
    const connectStream = async () => {
      try {
        const res = await fetch(SSE_FEED_URL, { headers: { "X-API-KEY": API_KEY } });
        if (!res.ok) throw new Error("Failed to connect");
        setConnected(true);
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        while (active) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try { applyData(JSON.parse(line.substring(6)), false); } catch {}
            }
          }
        }
      } catch {
        if (active) setConnected(false);
      }
    };
    connectStream();
    fetchSnap();
    const t = setInterval(fetchSnap, REFRESH_MS);
    return () => { active = false; clearInterval(t); };
  }, [applyData, fetchSnap, API_KEY]);

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex flex-col pt-14">
      <div className="max-w-6xl mx-auto w-full px-4 py-6 space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl glass-card animate-pulse relative overflow-hidden">
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/5 to-transparent" />
            </div>
          ))}
        </div>
        <div className="h-12 w-full rounded-xl glass-card animate-pulse" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 w-full rounded-xl glass-card animate-pulse" style={{ opacity: 1 - i * 0.15 }} />
          ))}
        </div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-50">
        <div className="text-center space-y-4 bg-slate-950/80 p-8 rounded-3xl backdrop-blur-md border border-white/10 shadow-2xl">
          <div className="w-12 h-12 rounded-full border-2 border-t-transparent animate-slow-spin mx-auto glow-text"
            style={{ borderColor: G, borderTopColor:"transparent" }}/>
          <p className="font-mono text-sm tracking-widest glow-text" style={{ color: G }}>INITIALIZING SECURE LINK…</p>
          <p className="text-xs text-slate-500 font-mono">ESTABLISHING ON-CHAIN CONNECTION</p>
        </div>
      </div>
    </div>
  );

  const stats    = data?.stats   || {};
  const allFnds  = data?.latest_findings || [];
  const activeInc= data?.active_incidents || [];
  const sm       = data?.smart_money_summary || {};
  const chain    = data?.chain   || {};
  const backtest = data?.backtest;
  const contract = data?.contract_address || CONTRACT_ADDR;
  const auditCount = data?.protocol_state?.audit_contract?.finding_count ?? allFnds.length ?? 0;

  const filtered = activeFilter === "all" ? activeInc : activeInc.filter(i => i.type === activeFilter);
  const sorted   = [...filtered].sort((a,b) => b.latest_block - a.latest_block);

  const TABS = [
    { key:"findings",  label:"Incidents",        icon:AlertTriangle, badge:activeInc.length },
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
    <div className="min-h-screen text-white bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">

      <div className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl shadow-sm">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">

          <div className="flex items-center gap-2.5 flex-shrink-0 group cursor-pointer">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center font-black text-black text-sm shadow-[0_0_15px_rgba(0,211,149,0.5)] transition-transform group-hover:scale-105"
              style={{ background: `linear-gradient(135deg,${G},#00a876)` }}>⬡</div>
            <div>
              <div className="text-sm font-black text-white tracking-tight font-['Outfit']">MANTLE INTEL</div>
              <div className="text-[10px] font-mono tracking-widest" style={{ color: G, marginTop:"-2px" }}>AGENT v6.0</div>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-4 flex-1 px-6 text-xs font-mono text-slate-500">
            {chain.mainnet?.latest_block > 0 && (
              <span className="flex items-center gap-1.5">
                <PulseDot color={G} size={6}/>
                <span style={{ color: G }}>BLK</span>
                <span className="text-white">#{chain.mainnet.latest_block.toLocaleString()}</span>
              </span>
            )}
            <span>|</span>
            <span className="flex items-center gap-1">
              <span>INCIDENTS</span>
              <span className="text-white font-bold">{activeInc.length}</span>
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

          <div className="flex items-center gap-2 ml-auto flex-shrink-0">
            <div className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full border"
              style={{ borderColor: connected ? G+"40":"#374151", color: connected ? G: demoMode ? "#EAB308" : "#6B7280", background: connected ? G+"10" : demoMode ? "#EAB30810" : "transparent" }}>
              {connected ? <Wifi size={10}/> : demoMode ? <AlertCircle size={10}/> : <WifiOff size={10}/>}
              {connected ? "LIVE" : demoMode ? "CACHED" : "POLLING"}
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

        {error && (
          <div className="border-t border-amber-500/20 bg-amber-500/5 px-4 py-2 flex items-center gap-2 text-xs font-mono">
            <AlertCircle size={11} className="text-amber-400 flex-shrink-0"/>
            <span className="text-amber-300 truncate flex-1">{error}</span>
            <button onClick={fetchSnap} className="text-amber-400 hover:text-amber-200 flex items-center gap-1 flex-shrink-0">
              <Zap size={10}/> retry
            </button>
          </div>
        )}

        {demoMode && !error && (
          <div className="border-t border-amber-500/20 bg-amber-500/5 px-4 py-1.5 flex items-center gap-2 text-xs font-mono">
            <AlertCircle size={10} className="text-amber-400 flex-shrink-0"/>
            <span className="text-amber-300">Cached snapshot mode — live API unreachable in this preview environment.</span>
          </div>
        )}
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-5">

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
            value={sm.tracked_wallets || 0}
            sub={`${sm.tier1_alerts||0} tier-1 alerts`} accent="#A855F7"/>
        </div>

        <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-hide">
          {TABS.map(({ key, label, icon: Icon, badge }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all whitespace-nowrap flex-shrink-0 relative overflow-hidden group"
              style={{
                background: activeTab===key ? G+"15" : "transparent",
                color: activeTab===key ? G : "#94A3B8",
              }}>
              {activeTab === key && <div className="absolute inset-0 border border-[rgba(0,211,149,0.3)] rounded-xl pointer-events-none" />}
              <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
              <Icon size={14} className="transition-transform group-hover:scale-110" />
              {label}
              {(badge === "NEW" || badge > 0) && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-mono ml-1 shadow-sm"
                  style={{ 
                    background: badge==="NEW" ? "#A855F725" : (activeTab===key ? G+"30":"#334155"),
                    color: badge==="NEW" ? "#D8B4FE" : (activeTab===key ? "#A7F3D0":"#CBD5E1"),
                    border: `1px solid ${badge==="NEW" ? "#A855F750" : (activeTab===key ? G+"50":"transparent")}`
                  }}>
                  {badge}
                </span>
              )}
            </button>
          ))}
        </div>

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

        {activeTab === "findings" && (
          <div className="space-y-4">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-hide">
              {FILTERS.map(f => (
                <button key={f.key} onClick={() => setFilter(f.key)}
                  className="text-xs px-3.5 py-1.5 rounded-lg whitespace-nowrap transition-all font-bold flex-shrink-0 hover:bg-slate-800"
                  style={{
                    background: activeFilter===f.key ? G+"20":"rgba(15,23,42,0.6)",
                    color: activeFilter===f.key ? G : "#94A3B8",
                    border: `1px solid ${activeFilter===f.key ? G+"50":"rgba(255,255,255,0.05)"}`,
                  }}>
                  {f.label}
                </button>
              ))}
            </div>

            {sorted.length === 0 ? (
              <div className="text-center py-20 text-gray-800">
                <Activity size={32} className="mx-auto mb-3 animate-pulse"/>
                <p className="text-sm text-gray-600">No active incidents in current window</p>
                <p className="text-xs mt-2 text-gray-700 font-mono">Scanning latest 100 blocks · refreshes every 12s</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sorted.map((inc, i) => (
                  <IncidentCard key={inc.id||i} incident={inc} isNew={newIds.has(inc.id)}/>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "signals"   && <SignalsTab   findings={allFnds}/>}
        {activeTab === "reasoning" && <ReasoningTab findings={allFnds}/>}
        {activeTab === "roi"       && <ROITab/>}
        {activeTab === "protocol"  && <ProtocolTab  data={data}/>}
        {activeTab === "analytics" && <AnalyticsTab data={data} backtest={backtest}/>}
        {activeTab === "audit"     && <AuditTab     data={data} findings={allFnds}/>}
        {activeTab === "api"       && <APITab       data={data} contract={contract}/>}

        <div className="border-t pt-6 flex items-center justify-between text-xs font-mono text-slate-500"
          style={{ borderColor:"rgba(255,255,255,0.05)" }}>
          <span>Mantle Intel Agent v6.0 · On-Chain Intelligence · Mantle Ecosystem</span>
          <div className="flex items-center gap-5 hidden sm:flex">
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-white transition-colors">
              <GitBranch size={10}/> GitHub
            </a>
            <a href={`${EXPLORER_BASE}/address/${CONTRACT_ADDR}`} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-white transition-colors">
              <Shield size={10}/> Contract
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
