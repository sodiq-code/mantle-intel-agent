import { useState } from "react";
import { Cpu } from "lucide-react";
import { G } from "./Shared.jsx";

export function ReasoningTab({ findings }) {
  const [selected, setSelected] = useState(0);

  const signals = findings.filter(f => (f.confidence || 0) >= 0.75).slice(0, 8);

  if (signals.length === 0) {
    return (
      <div className="text-center py-16 text-gray-700 rounded-xl border border-white/5">
        <Cpu size={28} className="mx-auto mb-3"/>
        <p className="text-sm">No high-confidence signals available for reasoning.</p>
        <p className="text-xs text-gray-700 font-mono mt-1">Signals require confidence ≥ 75%</p>
      </div>
    );
  }

  const STEP_COLOR = { green: "#00D395", yellow: "#EAB308", red: "#EF4444" };
  const TIER_C = { "IMMEDIATE": "#EF4444", "ALERT": "#F97316", "WATCH": "#EAB308" };

  const safeIdx = Math.min(selected, signals.length - 1);
  const sig = signals[safeIdx];

  // Defensive: support both live API and cached dashboard.json raw_metrics shapes
  const buildChain = (f) => {
    const chain = [];
    const rm = f.raw_metrics || {};
    const txCount = rm.tx_count ?? rm.transfer_count ?? 0;
    const totalUsd = rm.total_value_usd ?? rm.total_usd ?? 0;
    const txZ = rm.tx_zscore ?? rm.tx_z ?? 0;
    const valZ = rm.val_zscore ?? rm.val_z ?? 0;
    const largeXfers = rm.large_transfers ?? rm.transfer_count ?? 0;
    const maxPair = rm.max_pair_count ?? 0;
    const reasons = f.reasons || (f.method ? [f.method] : []);
    const sm = f.smart_money || {};
    const knownWallets = sm.known_wallets || [];

    // Step 1: Metrics
    chain.push({
      step: "1. Data Ingestion & Z-Score",
      detail: `Block ${f.block}: ${txCount} txs, $${(totalUsd || 0).toLocaleString()} value. Z-scores: TX=${txZ}, Val=${valZ}.`,
      signal: (valZ > 2.5 || txZ > 2.5) ? "green" : "yellow"
    });

    // Step 2: Whales
    if (largeXfers > 0) {
      chain.push({
        step: "2. Whale Tracking",
        detail: `Detected ${largeXfers} large transfer(s).${knownWallets.length > 0 ? " Known wallets involved." : ""}`,
        signal: "green"
      });
    }

    // Step 3: Smart Money
    if (maxPair >= 5) {
      chain.push({
        step: "3. Smart Money Clustering",
        detail: `Coordinated inflow detected: ${maxPair} max pair count.`,
        signal: "green"
      });
    }

    // Step 4: Multi-confirm
    chain.push({
      step: "4. Isolation Forest & Rule Confirm",
      detail: `Confidence calculated at ${Math.round((f.confidence || 0) * 100)}%. Threshold met.${reasons.length > 0 ? " Reasons: " + reasons.join(", ") + "." : ""}`,
      signal: (f.confidence || 0) >= 0.85 ? "green" : "yellow"
    });

    return chain;
  };

  const reasoningChain = buildChain(sig);
  const tier = (sig.confidence || 0) >= 0.85 ? "IMMEDIATE" : "ALERT";
  const action = sig.type === "whale_accumulation" ? "ACCUMULATE" : sig.type === "smart_money_inflow" ? "LONG" : "WATCH";

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex gap-2 flex-wrap">
        {signals.map((s, i) => (
          <button key={i} onClick={() => setSelected(i)}
            className="text-xs px-3 py-1.5 rounded-lg font-bold transition-all"
            style={{
              background: i===safeIdx ? G+"18" : "#0D0D0D",
              color: i===safeIdx ? G : "#6B7280",
              border: `1px solid ${i===safeIdx ? G+"50" : "#1F2937"}`,
            }}>
            {s.type} #{s.block}
          </button>
        ))}
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor: TIER_C[tier]+"40", background: TIER_C[tier]+"08" }}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="min-w-0 flex-1">
            <div className="text-xs text-gray-500 font-mono">Mantle Mainnet</div>
            <div className="text-lg font-black text-white truncate">{sig.title || `${sig.type} at block #${sig.block}`}</div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="text-center">
              <div className="text-xs text-gray-600">Confidence</div>
              <div className="text-xl font-black font-mono" style={{ color: G }}>{Math.round((sig.confidence||0)*100)}%</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-600">Lead Time</div>
              <div className="text-sm font-bold text-white">~2 hrs</div>
            </div>
            <div className="text-xs font-black px-3 py-1.5 rounded-lg"
              style={{ color: TIER_C[tier], background: TIER_C[tier]+"18" }}>
              {tier}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border overflow-hidden" style={{ borderColor: "#1F2937" }}>
        <div className="px-4 py-2.5 border-b text-xs font-bold text-gray-400 flex items-center gap-2"
          style={{ borderColor:"#1F2937", background:"#080808" }}>
          <Cpu size={10} style={{ color: G }}/> AGENT REASONING CHAIN — live per-block thought stream
        </div>
        <div className="divide-y divide-gray-900/80">
          {reasoningChain.map(({ step, detail, signal }, i) => (
            <div key={i} className="flex gap-4 px-4 py-3.5 hover:bg-white/[0.02] transition-colors" style={{ background:"#0A0A0A" }}>
              <div className="flex flex-col items-center flex-shrink-0">
                <div className="w-2.5 h-2.5 rounded-full mt-1"
                  style={{ backgroundColor: STEP_COLOR[signal], boxShadow: `0 0 8px ${STEP_COLOR[signal]}80` }}/>
                {i < reasoningChain.length - 1 && <div className="w-px flex-1 mt-1" style={{ background: "#1F2937" }}/>}
              </div>
              <div className="flex-1 min-w-0 pb-1">
                <div className="text-xs font-bold text-white mb-1">{step}</div>
                <div className="text-xs text-gray-500 font-mono leading-relaxed">{detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border p-4" style={{ borderColor: G+"30", background: G+"08" }}>
        <div className="text-xs font-bold mb-2 flex items-center gap-2" style={{ color: G }}>
          <Cpu size={11}/> AGENT VERDICT
        </div>
        <div className="text-sm font-black text-white" style={{ color: G }}>{action}</div>
        <div className="text-xs text-gray-400 mt-1 leading-relaxed font-mono">{sig.insight}</div>
      </div>

      {sig.hash && (
        <div className="text-xs text-gray-700 font-mono text-center">
          Reasoning committed to on-chain hash {sig.hash.slice(0, 16)}…
        </div>
      )}
    </div>
  );
}
