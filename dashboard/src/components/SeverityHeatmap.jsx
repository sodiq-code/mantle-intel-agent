import { AlertTriangle } from "lucide-react";
import { G, ANOMALY_CFG, cfg } from "./Shared.jsx";

export function SeverityHeatmap({ findings = [], blocks = [] }) {
  if (findings.length === 0) return null;

  // Group findings by type
  const typeCounts = {};
  const typeConfidences = {};
  for (const f of findings) {
    const t = f.type || 'unknown';
    typeCounts[t] = (typeCounts[t] || 0) + 1;
    if (!typeConfidences[t]) typeConfidences[t] = [];
    typeConfidences[t].push(f.confidence || 0);
  }

  // Get top types sorted by count
  const types = Object.entries(typeCounts)
    .sort(([,a],[,b]) => b - a)
    .slice(0, 6);

  if (types.length === 0) return null;

  return (
    <div className="rounded-xl border p-4" style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle size={12} style={{ color: G }}/>
          <span className="text-xs font-bold text-white">Anomaly Severity Heatmap</span>
        </div>
        <span className="text-xs font-mono text-gray-600">{findings.length} total detections</span>
      </div>

      <div className="space-y-2.5">
        {types.map(([type, count]) => {
          const c = cfg(type);
          const confs = typeConfidences[type] || [];
          const avgConf = confs.reduce((a,b) => a+b, 0) / confs.length;
          const maxConf = Math.max(...confs);
          const intensity = avgConf; // 0-1 scale

          return (
            <div key={type} className="flex items-center gap-3">
              <div className="w-28 flex-shrink-0">
                <div className="text-xs font-bold font-mono truncate" style={{ color: c.color }}>{c.label}</div>
              </div>

              <div className="flex-1 h-6 rounded-md overflow-hidden relative" style={{ background: "#1a1a2e" }}>
                <div className="h-full rounded-md transition-all duration-500 flex items-center px-2"
                  style={{
                    width: `${Math.max(8, intensity * 100)}%`,
                    background: `linear-gradient(90deg, ${c.color}40, ${c.color})`,
                    boxShadow: `0 0 12px ${c.color}30`
                  }}>
                  <span className="text-[10px] font-bold font-mono text-white">{count}×</span>
                </div>
              </div>

              <div className="w-16 text-right flex-shrink-0">
                <div className="text-xs font-bold font-mono" style={{ color: c.color }}>
                  {Math.round(avgConf * 100)}%
                </div>
                <div className="text-[10px] text-gray-600 font-mono">avg</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-3 gap-2">
        <div className="text-center">
          <div className="text-lg font-black font-mono text-red-400">
            {findings.filter(f => f.confidence >= 0.85).length}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">HIGH (≥85%)</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-black font-mono text-orange-400">
            {findings.filter(f => f.confidence >= 0.75 && f.confidence < 0.85).length}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">MEDIUM (75-85%)</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-black font-mono text-yellow-400">
            {findings.filter(f => f.confidence < 0.75).length}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">WATCH (&lt;75%)</div>
        </div>
      </div>
    </div>
  );
}
