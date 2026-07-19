import { G, PulseDot } from "./Shared.jsx";

// Shared SVG defs for glow filter — referenced by all gauge arcs
function GlowDefs() {
  return (
    <defs>
      <filter id="gauge-glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <linearGradient id="gauge-track" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#1F2937"/>
        <stop offset="100%" stopColor="#0F172A"/>
      </linearGradient>
    </defs>
  );
}

function GaugeCircle({ value, max, label, color = G, unit = "", size = 80, decimals = 2 }) {
  const pct = max > 0 ? Math.min(value / max, 1) : 0;
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  const displayVal = (value !== null && value !== undefined) ? value : null;

  return (
    <div className="flex flex-col items-center gap-1.5 group">
      <div className="relative transition-transform duration-300 group-hover:scale-105" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <GlowDefs/>
          {/* Background track */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="url(#gauge-track)" strokeWidth="5"/>
          {/* Value arc */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="5"
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}/>
          {/* Glow effect */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="5"
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            opacity={0.5}
            filter="url(#gauge-glow)"
            style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}/>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-sm font-black font-mono leading-none" style={{ color }}>
            {displayVal !== null ? displayVal.toFixed(decimals) : '—'}
          </span>
          {unit && <span className="text-[9px] font-mono text-gray-600 mt-0.5">{unit}</span>}
        </div>
      </div>
      <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider group-hover:text-gray-400 transition-colors">{label}</span>
    </div>
  );
}

export function ProtocolGauges({ protocolState = {} }) {
  const meth = protocolState.meth || {};
  const moe = protocolState.merchant_moe || {};
  const lendle = protocolState.lendle || {};

  const methRatio = meth.ratio ?? 1.0012;
  const isDepeg = meth.depeg_alert;
  const moeBal = moe.router_balance_mnt || 0;
  const lendleBal = lendle.pool_balance_mnt || 0;
  const supplyMeth = meth.supply_meth || 0;
  const stakedEth = meth.staked_eth || 0;

  // Aggregate health
  const healthyCount = [!isDepeg, moeBal > 0, lendleBal > 0, supplyMeth > 0].filter(Boolean).length;
  const healthPct = (healthyCount / 4) * 100;

  return (
    <div className="rounded-xl border p-5 relative overflow-hidden" style={{ borderColor: "#1F2937", background: "linear-gradient(135deg, #0D0D0D, #0A0A0A)" }}>
      {/* Subtle background glow */}
      <div className="absolute -top-20 -right-20 w-40 h-40 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ backgroundColor: isDepeg ? '#EF4444' : G }}/>

      <div className="flex items-center gap-2 mb-5 relative">
        <PulseDot color={G} size={6}/>
        <span className="text-xs font-bold text-white">Protocol Health Monitor</span>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full ml-auto"
          style={{
            color: isDepeg ? '#EF4444' : G,
            backgroundColor: isDepeg ? '#EF444415' : G + '15',
            border: `1px solid ${isDepeg ? '#EF444440' : G + '40'}`
          }}>
          {isDepeg ? 'DEPEG ALERT' : `${healthyCount}/4 HEALTHY`}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 relative">
        <GaugeCircle
          value={methRatio}
          max={1.05}
          decimals={4}
          label="mETH Ratio"
          color={isDepeg ? '#EF4444' : '#3B82F6'}
        />
        <GaugeCircle
          value={supplyMeth}
          max={100000}
          decimals={0}
          unit="mETH"
          label="mETH Supply"
          color="#8B5CF6"
        />
        <GaugeCircle
          value={moeBal}
          max={500000}
          decimals={0}
          unit="MNT"
          label="Moe Liquidity"
          color="#F97316"
        />
        <GaugeCircle
          value={lendleBal}
          max={500000}
          decimals={0}
          unit="MNT"
          label="Lendle TVL"
          color="#06B6D4"
        />
      </div>

      <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-3 gap-2 text-center relative">
        <div className="group cursor-default">
          <div className="text-xs font-bold font-mono transition-transform group-hover:scale-110" style={{ color: isDepeg ? '#EF4444' : '#3B82F6' }}>
            {stakedEth ? `${Math.round(stakedEth)} ETH` : '—'}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">Staked ETH</div>
        </div>
        <div className="group cursor-default">
          <div className="text-xs font-bold font-mono text-orange-400 transition-transform group-hover:scale-110">
            {moeBal ? `${Math.round(moeBal).toLocaleString()} MNT` : '—'}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">Moe Router</div>
        </div>
        <div className="group cursor-default">
          <div className="text-xs font-bold font-mono text-cyan-400 transition-transform group-hover:scale-110">
            {lendleBal ? `${Math.round(lendleBal).toLocaleString()} MNT` : '—'}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">Lendle Pool</div>
        </div>
      </div>

      {/* Health progress bar */}
      <div className="mt-3 h-1 rounded-full overflow-hidden" style={{ background: "#1F2937" }}>
        <div className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${healthPct}%`,
            background: `linear-gradient(90deg, ${isDepeg ? '#EF4444' : G}, ${isDepeg ? '#F87171' : '#34D399'})`,
            boxShadow: `0 0 8px ${isDepeg ? '#EF444460' : G + '60'}`
          }}/>
      </div>
    </div>
  );
}
