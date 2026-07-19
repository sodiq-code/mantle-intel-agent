import { TrendingUp } from "lucide-react";
import { G, cfg, ConfRing } from "./Shared.jsx";

export function SignalsTab({ findings }) {
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
