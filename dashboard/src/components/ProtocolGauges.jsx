import { G, PulseDot } from "./Shared.jsx";

function GaugeCircle({ value, max, label, color = G, unit = "", size = 80 }) {
  const pct = max > 0 ? Math.min(value / max, 1) : 0;
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Background track */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1F2937" strokeWidth="5"/>
          {/* Value arc */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="5"
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}/>
          {/* Glow effect */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="5"
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            opacity={0.3}
            filter="url(#glow)"
            style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}/>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-sm font-black font-mono" style={{ color }}>{value !== null && value !== undefined ? value.toFixed(2) : '—'}</span>
        </div>
      </div>
      <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">{label}</span>
    </div>
  );
}

export function ProtocolGauges({ protocolState = {} }) {
  const meth = protocolState.meth || {};
  const moe = protocolState.merchant_moe || {};
  const lendle = protocolState.lendle || {};
  
  const methRatio = meth.ratio ?? 1.0012;
  const isDepeg = meth.depeg_alert;
  
  return (
    <div className="rounded-xl border p-5" style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
      <div className="flex items-center gap-2 mb-5">
        <PulseDot color={G} size={6}/>
        <span className="text-xs font-bold text-white">Protocol Health Monitor</span>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full ml-auto"
          style={{ 
            color: isDepeg ? '#EF4444' : G, 
            backgroundColor: isDepeg ? '#EF444415' : G + '15',
            border: `1px solid ${isDepeg ? '#EF444440' : G + '40'}`
          }}>
          {isDepeg ? 'DEPEG ALERT' : 'ALL HEALTHY'}
        </span>
      </div>
      
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <GaugeCircle
          value={methRatio}
          max={1.05}
          label="mETH Ratio"
          color={isDepeg ? '#EF4444' : '#3B82F6'}
        />
        <GaugeCircle
          value={meth.supply_meth || 0}
          max={100000}
          label="mETH Supply"
          color="#8B5CF6"
        />
        <GaugeCircle
          value={moe.router_balance_mnt || 0}
          max={500000}
          label="Moe Liquidity"
          color="#F97316"
        />
        <GaugeCircle
          value={lendle.pool_balance_mnt || 0}
          max={500000}
          label="Lendle TVL"
          color="#06B6D4"
        />
      </div>
      
      <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-xs font-bold font-mono" style={{ color: isDepeg ? '#EF4444' : '#3B82F6' }}>
            {meth.staked_eth ? `${Math.round(meth.staked_eth)} ETH` : '—'}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">Staked ETH</div>
        </div>
        <div>
          <div className="text-xs font-bold font-mono text-orange-400">
            {moe.router_balance_mnt ? `${Math.round(moe.router_balance_mnt).toLocaleString()} MNT` : '—'}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">Moe Router</div>
        </div>
        <div>
          <div className="text-xs font-bold font-mono text-cyan-400">
            {lendle.pool_balance_mnt ? `${Math.round(lendle.pool_balance_mnt).toLocaleString()} MNT` : '—'}
          </div>
          <div className="text-[10px] text-gray-600 font-mono">Lendle Pool</div>
        </div>
      </div>
    </div>
  );
}
