import { useState } from "react";
import { DollarSign, Shield } from "lucide-react";
import { G } from "./Shared.jsx";

export function ROITab() {
  const [portfolio, setPortfolio] = useState(50000);
  const [tier, setTier] = useState("pro");
  const [avoidedEvents, setAvoidedEvents] = useState(2);

  const TIERS = {
    free:  { label:"Free", price:0,   signals:3,  alertDelay:"60min", whaleAccess:false },
    pro:   { label:"Pro $99/mo", price:99, signals:50, alertDelay:"Real-time", whaleAccess:true },
    inst:  { label:"Institutional $999/mo", price:999, signals:999, alertDelay:"Real-time + SMS", whaleAccess:true },
  };

  const SCENARIOS = [
    { name:"Lendle Liquidation Cascade", avgLoss:18000, prob:0.15, leadTime:"40min", freq:"~1/quarter" },
    { name:"Whale Exit (no warning)",    avgLoss:8500,  prob:0.35, leadTime:"4hrs",  freq:"~1/month" },
    { name:"mETH Depeg (caught early)",  avgLoss:12000, prob:0.08, leadTime:"30min", freq:"~1/6mo" },
    { name:"MEV Sandwich (avoided)",     avgLoss:2200,  prob:0.65, leadTime:"1block",freq:"~weekly" },
  ];

  const annualSubCost = TIERS[tier].price * 12;
  const expectedAnnualSavings = SCENARIOS.reduce((sum, s) => sum + s.avgLoss * s.prob * avoidedEvents, 0);
  const roi = annualSubCost > 0 ? ((expectedAnnualSavings - annualSubCost) / annualSubCost * 100).toFixed(0) : "∞";
  const payback = annualSubCost > 0 ? (annualSubCost / (expectedAnnualSavings / 12)).toFixed(1) : 0;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4" style={{ borderColor: G+"30", background: G+"05" }}>
        <div className="text-xs font-bold mb-1" style={{ color: G }}>INVESTMENT SIGNAL ROI CALCULATOR</div>
        <div className="text-xs text-gray-600">Model the value of early warning signals on your Mantle DeFi portfolio</div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <div className="text-xs text-gray-500 mb-2">Portfolio Size</div>
          <div className="flex items-center gap-2">
            <DollarSign size={12} style={{ color: G }}/>
            <input type="range" min="10000" max="1000000" step="5000" value={portfolio}
              onChange={e => setPortfolio(Number(e.target.value))}
              className="flex-1 accent-emerald-400"/>
          </div>
          <div className="text-lg font-black font-mono mt-1" style={{ color: G }}>
            ${portfolio.toLocaleString()}
          </div>
        </div>

        <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <div className="text-xs text-gray-500 mb-2">Subscription Tier</div>
          <div className="flex flex-col gap-1.5">
            {Object.entries(TIERS).map(([k, v]) => (
              <button key={k} onClick={() => setTier(k)}
                className="text-xs px-3 py-1.5 rounded-lg font-bold text-left transition-all"
                style={{
                  background: tier===k ? G+"20" : "transparent",
                  color: tier===k ? G : "#6B7280",
                  border: `1px solid ${tier===k ? G+"50" : "#1F2937"}`,
                }}>
                {v.label}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border p-4" style={{ borderColor:"#1F2937", background:"#0D0D0D" }}>
          <div className="text-xs text-gray-500 mb-2">Events Avoided/Year</div>
          <div className="flex items-center gap-2">
            <Shield size={12} style={{ color: G }}/>
            <input type="range" min="1" max="10" step="1" value={avoidedEvents}
              onChange={e => setAvoidedEvents(Number(e.target.value))}
              className="flex-1 accent-emerald-400"/>
          </div>
          <div className="text-lg font-black font-mono mt-1 text-white">{avoidedEvents} events/yr</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label:"Annual Subscription", value:`${annualSubCost.toLocaleString()}`, col:"#6B7280", sub:"cost" },
          { label:"Expected Savings", value:`${Math.round(expectedAnnualSavings).toLocaleString()}`, col: G, sub:"per year" },
          { label:"ROI", value:`${roi}%`, col:"#A855F7", sub: annualSubCost > 0 ? `${payback}mo payback` : "free tier" },
        ].map(({ label, value, col, sub }) => (
          <div key={label} className="rounded-xl border p-4 text-center"
            style={{ borderColor: col+"30", background: col+"08" }}>
            <div className="text-xl font-black font-mono" style={{ color: col }}>{value}</div>
            <div className="text-xs text-gray-400 mt-1 font-bold">{label}</div>
            <div className="text-xs text-gray-600 mt-0.5">{sub}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border overflow-hidden" style={{ borderColor:"#1F2937" }}>
        <div className="px-4 py-2.5 border-b text-xs font-bold text-gray-400"
          style={{ borderColor:"#1F2937", background:"#080808" }}>
          SIGNAL SCENARIO BREAKDOWN — avg loss avoided per event
        </div>
        {SCENARIOS.map(({ name, avgLoss, prob, leadTime, freq }) => (
          <div key={name} className="flex items-center gap-4 px-4 py-3 border-b border-gray-900/80 last:border-0"
            style={{ background:"#0A0A0A" }}>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-white">{name}</div>
              <div className="text-xs text-gray-600 font-mono mt-0.5">{freq} · {leadTime} warning</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-black font-mono" style={{ color: G }}>
                ${Math.round(avgLoss * prob * avoidedEvents).toLocaleString()}
              </div>
              <div className="text-xs text-gray-600">{Math.round(prob*100)}% prob · ${avgLoss.toLocaleString()} avg</div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-700 font-mono text-center">
        Based on Mantle DeFi historical patterns · Not financial advice · For illustration only
      </div>
    </div>
  );
}
