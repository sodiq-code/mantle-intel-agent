import { useState, useEffect } from "react";
import { AlertTriangle, Activity, Database, Shield, ExternalLink, RefreshCw, TrendingUp } from "lucide-react";

const ANOMALY_COLORS = {
  whale_accumulation:   { bg: "bg-blue-900/40",   border: "border-blue-500",  badge: "bg-blue-600",   label: "🐋 Whale Accumulation" },
  whale_distribution:   { bg: "bg-orange-900/40", border: "border-orange-500",badge: "bg-orange-600", label: "⚠️ Whale Distribution" },
  smart_money_inflow:   { bg: "bg-purple-900/40", border: "border-purple-500",badge: "bg-purple-600", label: "🧠 Smart Money Inflow" },
  tx_spike:             { bg: "bg-green-900/40",  border: "border-green-500", badge: "bg-green-600",  label: "📈 TX Volume Spike" },
  value_spike:          { bg: "bg-yellow-900/40", border: "border-yellow-500",badge: "bg-yellow-600", label: "💰 Value Spike" },
  multivariate_anomaly: { bg: "bg-red-900/40",    border: "border-red-500",   badge: "bg-red-600",    label: "🔍 Multivariate Anomaly" },
};

const DEFAULT_COLORS = { bg: "bg-gray-800/40", border: "border-gray-600", badge: "bg-gray-600", label: "⚡ Anomaly" };

function ConfidenceBar({ value }) {
  const pct   = Math.round(value * 100);
  const color = pct >= 85 ? "bg-red-500" : pct >= 70 ? "bg-orange-500" : "bg-yellow-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-300 w-10 text-right">{pct}%</span>
    </div>
  );
}

function FindingCard({ finding }) {
  const [expanded, setExpanded] = useState(false);
  const colors = ANOMALY_COLORS[finding.type] || DEFAULT_COLORS;
  const audit  = finding.audit || {};

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-lg p-4 cursor-pointer hover:brightness-110 transition-all`}
         onClick={() => setExpanded(!expanded)}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded ${colors.badge} text-white`}>
              {colors.label}
            </span>
            <span className="text-xs text-gray-400 font-mono">Block {(finding.block || 0).toLocaleString()}</span>
            {audit.status === "recorded" && (
              <span className="text-xs bg-green-800 text-green-300 px-1.5 py-0.5 rounded flex items-center gap-1">
                <Shield size={10} /> On-Chain
              </span>
            )}
            {audit.status === "demo" && (
              <span className="text-xs bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded">Demo</span>
            )}
          </div>
          <ConfidenceBar value={finding.confidence || 0} />
        </div>
        <span className="text-gray-500 text-xs mt-1">{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div className="mt-3 space-y-3">
          <div className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
            {finding.insight || finding.description || "No insight available"}
          </div>

          {finding.raw_metrics && (
            <div className="bg-gray-900/60 rounded p-2 text-xs font-mono text-gray-400">
              {Object.entries(finding.raw_metrics).map(([k, v]) => (
                <div key={k}><span className="text-gray-500">{k}:</span> {JSON.stringify(v)}</div>
              ))}
            </div>
          )}

          <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
            <span className="font-mono">Hash: {(finding.hash || "").slice(0, 20)}...</span>
            {audit.explorer && audit.tx_hash && (
              <a href={audit.explorer} target="_blank" rel="noopener noreferrer"
                 className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
                 onClick={e => e.stopPropagation()}>
                <ExternalLink size={10} /> Verify on Mantle Explorer
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className="text-gray-400" />
        <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      </div>
      <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  const load = async () => {
    try {
      const r = await fetch("/api/dashboard");
      if (!r.ok) throw new Error("not ok");
      const d = await r.json();
      setData(d);
      setLastRefresh(new Date());
    } catch {
      // Use mock data for static demo
      setData(MOCK_DATA);
      setLastRefresh(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30_000);
    return () => clearInterval(t);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <Activity className="animate-spin mx-auto text-blue-400 mb-3" size={32} />
          <p className="text-gray-400">Loading Mantle Intel Agent...</p>
        </div>
      </div>
    );
  }

  const stats  = data?.stats || {};
  const findings = data?.latest_findings || [];
  const sm     = data?.smart_money_summary || {};
  const contract = data?.contract_address || "Not deployed";
  const network  = data?.network || "mainnet";
  const explorerBase = network === "mainnet" ? "https://mantlescan.xyz" : "https://sepolia.mantlescan.xyz";
  const demoMode = data?.demo_mode;

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/80 sticky top-0 z-10 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-blue-400">⬡</span> Mantle Intel Agent
            </h1>
            <p className="text-xs text-gray-500">Autonomous On-Chain Intelligence · Alpha &amp; Data Track</p>
          </div>
          <div className="flex items-center gap-3">
            {demoMode && (
              <span className="text-xs bg-yellow-900/50 text-yellow-400 border border-yellow-800 px-2 py-1 rounded">
                Demo Mode
              </span>
            )}
            <button onClick={load} className="text-gray-400 hover:text-white transition-colors p-1">
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard icon={Activity}   label="Cycles Run"     value={stats.cycles_run || 0} />
          <StatCard icon={Database}   label="Blocks Scanned" value={(stats.blocks_processed || 0).toLocaleString()} />
          <StatCard icon={AlertTriangle} label="Findings"    value={stats.findings_total || 0} color="text-orange-400" />
          <StatCard icon={TrendingUp} label="Smart Money Signals" value={sm.signals_generated || 0} color="text-purple-400" />
        </div>

        {/* Contract info */}
        <div className="bg-gray-800/40 border border-gray-700 rounded-lg p-4 flex items-start gap-3">
          <Shield size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-green-400 mb-1">Audit Contract — MantleIntelAudit.sol</p>
            <p className="text-xs font-mono text-gray-300 break-all">{contract}</p>
            <p className="text-xs text-gray-500 mt-1">
              Every finding is SHA256-hashed and recorded on Mantle Network.
              {contract !== "Not deployed" && contract !== "not_deployed" && (
                <a href={`${explorerBase}/address/${contract}`}
                   target="_blank" rel="noopener noreferrer"
                   className="ml-2 text-blue-400 hover:text-blue-300 inline-flex items-center gap-1">
                  <ExternalLink size={10} /> View on Explorer
                </a>
              )}
            </p>
          </div>
        </div>

        {/* Findings */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
              Latest Findings
            </h2>
            <span className="text-xs text-gray-600">
              {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString()}` : ""}
            </span>
          </div>

          {findings.length === 0 ? (
            <div className="text-center py-12 text-gray-600">
              <Activity size={32} className="mx-auto mb-3 animate-pulse" />
              <p>Pipeline running — waiting for anomalies...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {[...findings].reverse().map((f, i) => (
                <FindingCard key={f.id || i} finding={f} />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-700 pt-4 border-t border-gray-800">
          Mantle Intel Agent · The Turing Test Hackathon 2026 · Alpha &amp; Data Track (Mirana Ventures)
          · Built by Kudirat Oyindamola
        </div>
      </div>
    </div>
  );
}

// ── Mock data for static deploy (when API not available) ─────────────────────

const MOCK_DATA = {
  last_updated: new Date().toISOString(),
  demo_mode: true,
  audit_demo: true,
  contract_address: "0x0000000000000000000000000000000000000000",
  network: "testnet",
  stats: {
    cycles_run: 3,
    blocks_processed: 300,
    findings_total: 4,
    started_at: new Date(Date.now() - 3600000).toISOString(),
  },
  smart_money_summary: { signals_generated: 7, tracked_wallets: 24 },
  latest_findings: [
    {
      id: "whale_68000025_demo",
      type: "whale_accumulation",
      block: 68000025,
      confidence: 0.93,
      confidence_pct: 93,
      hash: "a3f2c91d4b88e0712a45b6c78d3e9f01234567890abcdef",
      insight: "🐋 WHALE ACCUMULATION — Mantle Block 68,000,025\n\n1 large transfer totaling $722,500 USD. Binance Hot Wallet → Agni Finance. CEX-to-DeFi movement typically precedes informed position building on Mantle.\n\n💡 Implication: Large DeFi inflows on Mantle have historically preceded 15–40% TVL increases within 48–72 hours.\n\n📊 Confidence: 93% | Method: Pattern Match",
      raw_metrics: { transfer_count: 1, total_usd: 722500, labeled_count: 1 },
      audit: { status: "demo", tx_hash: "0xdemo123", explorer: "" },
    },
    {
      id: "smartmoney_68000060_demo",
      type: "smart_money_inflow",
      block: 68000060,
      confidence: 0.87,
      confidence_pct: 87,
      hash: "b7e1d54c2a99f1823b56a7d89e4f02345678901bcdef01",
      insight: "🧠 SMART MONEY SIGNAL — Mantle Block 68,000,060\n\n5 unlabeled wallets collectively moved $420,000 into Merchant Moe on Mantle. Coordinated behavior across 1 block window — consistent with informed entry before a known protocol event.\n\n💡 Implication: This pattern has preceded major protocol TVL moves in 72% of historical cases.\n\n📊 Confidence: 87% | Method: Wallet Clustering | Wallets: 5",
      raw_metrics: { wallet_count: 5, total_usd: 420000, avg_per_wallet: 84000 },
      audit: { status: "demo", tx_hash: "0xdemo456", explorer: "" },
    },
    {
      id: "zscore_tx_68000025_demo",
      type: "tx_spike",
      block: 68000025,
      confidence: 0.79,
      confidence_pct: 79,
      hash: "c9f3e65d1b00a2934c67b8e90f5a13456789012cdef012",
      insight: "📈 TX VOLUME SPIKE — Mantle Block 68,000,025\n\nTransaction volume spike: 280 txs vs baseline 75 (z=3.11σ). Possible protocol event or coordinated activity on Mantle.\n\n📊 Confidence: 79% | Method: Z-Score | Z=3.11",
      raw_metrics: { tx_count: 280, mean_tx: 75, zscore: 3.11 },
      audit: { status: "demo", tx_hash: "0xdemo789", explorer: "" },
    },
  ],
};
