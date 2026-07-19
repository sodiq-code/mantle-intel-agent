import { useState, useEffect, useCallback } from "react";
import { Bell, X, AlertTriangle, TrendingUp } from "lucide-react";
import { G, cfg } from "./Shared.jsx";

export function NotificationCenter({ incidents = [], findings = [] }) {
  const [notifications, setNotifications] = useState([]);
  const [showPanel, setShowPanel] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Track new findings as notifications
  useEffect(() => {
    if (findings.length > 0) {
      setUnreadCount(prev => Math.min(prev + 1, 99));
    }
  }, [findings.length]);
  
  const dismiss = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);
  
  const clearAll = useCallback(() => {
    setUnreadCount(0);
  }, []);
  
  const recentIncidents = incidents.slice(0, 8);
  const recentFindings = findings.slice(0, 8);
  
  return (
    <>
      {/* Notification Bell */}
      <div className="relative">
        <button 
          onClick={() => { setShowPanel(!showPanel); if (showPanel) clearAll(); }}
          className="relative p-2 rounded-lg border border-white/10 hover:bg-white/5 text-gray-500 hover:text-white transition-colors"
        >
          <Bell size={14}/>
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-[9px] font-bold text-white flex items-center justify-center animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>
        
        {/* Notification Panel */}
        {showPanel && (
          <div className="absolute right-0 top-10 w-80 max-h-96 overflow-y-auto rounded-xl border shadow-2xl z-50"
            style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
            <div className="sticky top-0 px-4 py-3 border-b flex items-center justify-between z-10"
              style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
              <span className="text-xs font-bold text-white">Live Alerts</span>
              <button onClick={() => setShowPanel(false)} className="text-gray-500 hover:text-white">
                <X size={12}/>
              </button>
            </div>
            
            {recentFindings.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-600 text-xs">
                No recent alerts. Monitoring active...
              </div>
            ) : (
              <div className="divide-y divide-gray-900/50">
                {recentFindings.map((f, i) => {
                  const c = cfg(f.type);
                  return (
                    <div key={f.id || i} className="px-4 py-3 hover:bg-white/[0.02] transition-colors">
                      <div className="flex items-start gap-2.5">
                        <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: c.color }}/>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold font-mono" style={{ color: c.color }}>{c.label}</span>
                            <span className="text-[10px] font-mono text-gray-600">#{f.block?.toLocaleString()}</span>
                          </div>
                          <div className="text-xs text-gray-500 mt-0.5 truncate">{f.title || f.insight?.slice(0, 80)}</div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                              style={{ color: c.color, backgroundColor: c.color + "15" }}>
                              {Math.round((f.confidence || 0) * 100)}% conf
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
