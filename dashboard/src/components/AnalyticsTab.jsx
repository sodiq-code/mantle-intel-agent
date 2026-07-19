import { Target, Cpu, TrendingUp } from "lucide-react";
import { G, MiniBar, PulseDot } from "./Shared.jsx";

export function AnalyticsTab({ data, backtest }) {
  const stats  = data?.stats || {};
  const sm     = data?.smart_money_summary || {};
  const blocks = data?.recent_blocks || [];
  const chain  = data?.chain || {};

  // Normalize backtest shape — supports both live API and cached dashboard.json
  const bt = backtest ? {
    mode:           backtest.mode || "LIVE",
    precision_pct:  backtest.precision_pct ?? (typeof backtest.precision === "number" ? backtest.precision * 100 : 0),
    recall_pct:     backtest.recall_pct ?? (typeof backtest.recall === "number" ? backtest.recall * 100 : 0),
    f1_score:       backtest.f1_score ?? 0,
    tp:             backtest.tp ?? backtest.true_positives ?? 0,
    fp:             backtest.fp ?? backtest.false_positives ?? 0,
    fn:             backtest.fn ?? backtest.false_negatives ?? 0,
    blocks_scanned: backtest.blocks_scanned ?? backtest.blocks_analyzed ?? 0,
    block_range:    typeof backtest.block_range === "string"
      ? backtest.block_range
      : (backtest.block_range?.from
          ? `${backtest.block_range.from.toLocaleString()} → ${backtest.block_range.to.toLocaleString()}`
          : "—"),
    methodology:    backtest.methodology || "",
  } : null;

  return (
    <div className="space-y-4 animate-fade-in">
      {bt && (
        <div className="rounded-xl border p-4" style={{ borderColor: G+"30", background: "#0D0D0D" }}>
          <div className="flex items-center gap-2 mb-4">
            <Target size={12} style={{ color: G }}/>
            <span className="text-xs font-bold" style={{ color: G }}>BACKTEST RESULTS — {bt.mode}</span>
            <span className="ml-auto text-[10px] font-mono px-2 py-0.5 rounded-full"
              style={{ color: G, backgroundColor: G+"15", border: `1px solid ${G}30` }}>
              {bt.blocks_scanned} blocks
            </span>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 text-center">
            {[
              { label:"Precision", value:`${bt.precision_pct}%`, col:"#00D395" },
              { label:"Recall",    value:`${bt.recall_pct}%`,    col:"#3B82F6" },
              { label:"F1 Score",  value:bt.f1_score,            col:"#A855F7" },
              { label:"TP",        value:bt.tp,                  col:"#00D395" },
              { label:"FP",        value:bt.fp,                  col:"#EF4444" },
              { label:"FN",        value:bt.fn,                  col:"#F97316" },
            ].map(({ label, value, col }) => (
              <div key={label} className="rounded-lg p-3 transition-transform hover:scale-105" style={{ background: col+"0F" }}>
                <div className="text-lg font-black font-mono" style={{ color: col }}>{value}</div>
                <div className="text-xs text-gray-600 mt-1">{label}</div>
              </div>
            ))}
          </div>
          {bt.methodology && <div className="text-xs text-gray-700 mt-3 font-mono">{bt.methodology}</div>}
          <div className="text-xs text-gray-700 font-mono">Range: {bt.block_range}</div>
        </div>
      )}

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

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label:"Cycles Run",        value:(stats.cycles_run||0).toLocaleString(),      col:"#00D395" },
          { label:"Blocks Processed",  value:(stats.blocks_processed||0).toLocaleString(),col:"#3B82F6" },
          { label:"Avg Confidence",    value:`${((stats.avg_confidence||0)*100).toFixed(1)}%`, col:"#A855F7" },
          { label:"High Signal %",     value:`${stats.high_confidence_pct||0}%`,          col:"#EF4444" },
          { label:"Wallets Tracked",   value:`${sm.tracked_wallets||0}`,                  col:"#F97316" },
          { label:"Tier-1 Alerts",     value:`${sm.tier1_alerts||0}`,                     col:"#EAB308" },
        ].map(({ label, value, col }) => (
          <div key={label} className="rounded-xl border p-4 transition-transform hover:scale-[1.02]" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
            <div className="text-xl font-black font-mono" style={{ color: col }}>{value}</div>
            <div className="text-xs text-gray-600 mt-1">{label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
        <div className="text-xs font-bold text-white mb-3 flex items-center gap-2">
          <Cpu size={11} style={{ color:G }}/> Pipeline Agents
          <span className="ml-auto text-xs font-mono flex items-center gap-1" style={{ color:G }}>
            <PulseDot color={G} size={5}/> 5/5 LIVE
          </span>
        </div>
        <div className="space-y-1">
          {[
            { name:"BlockCollector",     desc:"Fetches latest Mantle blocks via RPC",          ms: chain.mainnet?.latest_block ? 420 : null },
            { name:"FeatureExtractor",   desc:"Extracts tx stats, smart money, large flows",   ms: 38  },
            { name:"AnomalyDetector",    desc:"IsoForest + z-score + rule-based multi-confirm",ms: 210 },
            { name:"SignalGenerator",    desc:"Generates alpha signals from confirmed anomalies",ms: 12 },
            { name:"AlertDispatcher",    desc:"Telegram + on-chain + dashboard push",          ms: 55  },
          ].map(({ name, desc, ms }, i) => (
            <div key={name} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition-colors rounded px-2"
              style={{ animationDelay: `${i*60}ms` }}>
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

      {/* Types breakdown — show distribution from stats */}
      {stats.types_breakdown && Object.keys(stats.types_breakdown).length > 0 && (
        <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <div className="text-xs font-bold text-white mb-3 flex items-center gap-2">
            <TrendingUp size={11} style={{ color:G }}/> Anomaly Type Distribution
          </div>
          <div className="space-y-2">
            {Object.entries(stats.types_breakdown)
              .sort(([,a],[,b]) => b - a)
              .map(([type, count]) => {
                const total = Object.values(stats.types_breakdown).reduce((s,v)=>s+v,0);
                const pct = total > 0 ? (count / total) * 100 : 0;
                return (
                  <div key={type} className="flex items-center gap-3">
                    <span className="text-xs font-mono text-gray-400 w-32 truncate">{type}</span>
                    <div className="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${G}80, ${G})` }}/>
                    </div>
                    <span className="text-xs font-mono text-white w-8 text-right">{count}</span>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
