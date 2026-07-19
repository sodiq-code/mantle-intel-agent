import { G, cfg } from "./Shared.jsx";
import { Activity } from "lucide-react";

export function BlockTimeline({ blocks = [], findings = [] }) {
  // Find which blocks have anomalies
  const anomalyBlocks = new Set(findings.map(f => f.block));

  if (blocks.length === 0) return null;

  const maxTx = Math.max(...blocks.map(b => b.tx_count || 0), 1);
  const width = 100; // total width %
  const barWidth = width / blocks.length;

  return (
    <div className="rounded-xl border p-4" style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity size={12} style={{ color: G }}/>
          <span className="text-xs font-bold text-white">Block Activity Timeline</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: G }}/> Normal
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500"/> Anomaly
          </span>
        </div>
      </div>

      <div className="relative h-20 w-full">
        <svg viewBox={`0 0 ${blocks.length * 8} 80`} className="w-full h-full" preserveAspectRatio="none">
          {blocks.map((block, i) => {
            const isAnomaly = anomalyBlocks.has(block.block_num);
            const height = Math.max(4, ((block.tx_count || 0) / maxTx) * 70);
            const x = i * 8;
            const color = isAnomaly ? "#EF4444" : G;
            const opacity = isAnomaly ? 1 : 0.5 + ((block.tx_count || 0) / maxTx) * 0.5;

            return (
              <g key={i}>
                <rect
                  x={x}
                  y={75 - height}
                  width={6}
                  height={height}
                  rx={1.5}
                  fill={color}
                  opacity={opacity}
                  className="transition-all duration-200"
                />
                {isAnomaly && (
                  <circle
                    cx={x + 3}
                    cy={75 - height - 4}
                    r={2}
                    fill="#EF4444"
                    className="animate-pulse"
                  />
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="flex justify-between text-xs text-gray-700 font-mono mt-2">
        <span>#{blocks[blocks.length-1]?.block_num?.toLocaleString()}</span>
        <span className="text-gray-500">{findings.length} anomalies in window</span>
        <span>#{blocks[0]?.block_num?.toLocaleString()}</span>
      </div>
    </div>
  );
}
