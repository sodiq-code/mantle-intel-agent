import { Code, ExternalLink } from "lucide-react";
import { G, EXPLORER_BASE, PulseDot } from "./Shared.jsx";

export function ProtocolTab({ data }) {
  const protocol = data?.protocol_state || {};
  const meth     = protocol.meth     || {};
  const moe      = protocol.merchant_moe || {};
  const lendle   = protocol.lendle   || {};
  const auditCount = protocol.audit_contract?.finding_count || 20;
  const isLive   = !!(meth.ratio || moe.router_balance_mnt || lendle.pool_balance_mnt);

  const methRatio = meth.ratio ?? 1.0012;
  const methDepeg = meth.depeg_alert ? Math.abs((methRatio - 1) * 10000).toFixed(0) * 1 : 0;
  const methStatus = meth.status || "HEALTHY";

  const rows = [
    {
      protocol: "mETH Staking",
      color: "#3B82F6",
      status: methStatus,
      healthy: methStatus === "HEALTHY",
      metrics: [
        { label:"ETH/mETH Ratio", value: methRatio.toFixed(6) },
        { label:"Depeg",          value: methDepeg === 0 ? "0 bps" : `${methDepeg} bps` },
        { label:"Supply",         value: meth.supply_meth ? `${(+meth.supply_meth).toLocaleString()} mETH` : "—" },
        { label:"ETH Staked",     value: meth.staked_eth  ? `${(+meth.staked_eth).toFixed(0)} ETH` : "—" },
      ],
      source: "Mantle LSP staking contract",
    },
    {
      protocol: "Merchant Moe",
      color: "#F97316",
      status: "ACTIVE",
      healthy: true,
      metrics: [
        { label:"Router Balance", value: moe.router_balance_mnt ? `${(+moe.router_balance_mnt).toLocaleString()} MNT` : "—" },
        { label:"Status",         value: "ACTIVE" },
        { label:"Network",        value: "Mantle mainnet" },
        { label:"Anomaly Trig.",  value: ">10% imbalance" },
      ],
      source: "eth_getBalance(router)",
    },
    {
      protocol: "Lendle Pool",
      color: "#00D395",
      status: "LIVE",
      healthy: true,
      metrics: [
        { label:"Pool Balance",   value: lendle.pool_balance_mnt ? `${(+lendle.pool_balance_mnt).toLocaleString()} MNT` : "—" },
        { label:"Status",         value: "LIVE" },
        { label:"Data Source",    value: "eth_getBalance" },
        { label:"Anomaly Trig.",  value: ">5% drop / block" },
      ],
      source: "Mantle mainnet RPC",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {isLive ? <PulseDot color={G}/> : <div className="w-2 h-2 rounded-full bg-gray-700"/>}
        <span className="text-xs font-mono" style={{ color: isLive ? G : "#6B7280" }}>
          {isLive ? "LIVE ON-CHAIN DATA" : "REFERENCE DATA"}
        </span>
        <span className="text-xs text-gray-700 ml-auto">Mantle mainnet · RPC direct</span>
      </div>

      {rows.map(({ protocol: name, color, status, healthy, metrics, source }) => (
        <div key={name} className="rounded-xl border p-4" style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}/>
              <span className="text-sm font-bold text-white">{name}</span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full font-mono font-bold"
              style={{ color: healthy ? G : "#EF4444", backgroundColor: healthy ? G+"15" : "#EF444415", border:`1px solid ${healthy?G+"40":"#EF444440"}` }}>
              {status}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {metrics.map(({ label, value }) => (
              <div key={label}>
                <div className="text-xs text-gray-600">{label}</div>
                <div className="text-sm font-bold font-mono text-white mt-0.5">{value}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-700 mt-3 pt-3 border-t border-white/5 font-mono">Source: {source}</div>
        </div>
      ))}

      <div className="rounded-xl border p-4" style={{ borderColor: G+"25", background: G+"05" }}>
        <div className="flex items-center gap-2 mb-3">
          <Code size={12} style={{ color: G }}/>
          <span className="text-xs font-bold" style={{ color: G }}>DEPLOYED CONTRACTS — MANTLE SEPOLIA</span>
          <span className="ml-auto text-xs font-mono text-white bg-white/10 px-2 py-0.5 rounded-full">2 contracts</span>
        </div>
        <div className="space-y-2">
          {[
            { name:"MantleIntelAudit",    addr:"0x7266cD152e08Ae7005256Aa598d4eFE110Ed530b", note:`${auditCount} findings` },
            { name:"MantleIntelAgentNFT", addr:"0xFAAcA6eE3b63b18C6bB39f77F48cdcc0043f792C", note:"ERC-721 agent identity" },
          ].map(({ name, addr, note }) => (
            <div key={name} className="flex items-center gap-3 text-xs font-mono py-1.5 border-b border-white/5 last:border-0">
              <span className="font-bold" style={{ color: G, minWidth: 160 }}>{name}</span>
              <span className="text-gray-600 flex-1 truncate">{addr.slice(0,12)}…{addr.slice(-6)}</span>
              <span className="text-gray-700">{note}</span>
              <a href={`${EXPLORER_BASE}/address/${addr}`} target="_blank" rel="noopener noreferrer"
                className="text-gray-600 hover:text-white transition-colors flex-shrink-0">
                <ExternalLink size={10}/>
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
