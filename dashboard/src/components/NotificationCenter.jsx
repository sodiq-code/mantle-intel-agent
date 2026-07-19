import { useState, useEffect, useCallback, useRef } from "react";
import { Bell, X, CheckCheck, AlertTriangle } from "lucide-react";
import { G, cfg, useTimeSince } from "./Shared.jsx";

export function NotificationCenter({ incidents = [], findings = [] }) {
  const [showPanel, setShowPanel] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [dismissed, setDismissed] = useState(new Set());
  const prevFindingIds = useRef(new Set());
  const prevIncidentCount = useRef(0);

  // Track genuinely NEW findings by comparing IDs to previous set
  useEffect(() => {
    const currentIds = new Set(findings.map(f => f.id || f.hash || f.block));
    let newCount = 0;
    for (const id of currentIds) {
      if (!prevFindingIds.current.has(id)) newCount++;
    }
    // Only increment if we have a baseline (skip first load)
    if (prevFindingIds.current.size > 0 && newCount > 0) {
      setUnreadCount(prev => Math.min(prev + newCount, 99));
    }
    prevFindingIds.current = currentIds;
  }, [findings]);

  // Also track new incidents
  useEffect(() => {
    if (incidents.length > prevIncidentCount.current && prevIncidentCount.current !== 0) {
      setUnreadCount(prev => Math.min(prev + (incidents.length - prevIncidentCount.current), 99));
    }
    prevIncidentCount.current = incidents.length;
  }, [incidents.length]);

  const markAllRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  const togglePanel = useCallback(() => {
    setShowPanel(prev => {
      const next = !prev;
      if (next) setUnreadCount(0); // clear on open
      return next;
    });
  }, []);

  const dismissItem = useCallback((id) => {
    setDismissed(prev => new Set([...prev, id]));
  }, []);

  // Merge findings + incidents into a single feed, newest first
  const feed = [
    ...findings.slice(0, 12).map(f => ({
      id: `f-${f.id || f.hash || f.block}`,
      type: f.type,
      block: f.block,
      confidence: f.confidence,
      title: f.title,
      insight: f.insight,
      time: f.timestamp,
      kind: "finding",
    })),
    ...incidents.slice(0, 6).map(i => ({
      id: `i-${i.id}`,
      type: i.type,
      block: i.latest_block,
      confidence: i.peak_confidence,
      title: `${cfg(i.type).label} incident`,
      insight: `${i.occurrences} occurrences over ${i.latest_block - i.start_block + 1} blocks`,
      time: i.latest_time ? i.latest_time * 1000 : null,
      kind: "incident",
    })),
  ].filter(item => !dismissed.has(item.id));

  return (
    <>
      {/* Notification Bell */}
      <div className="relative">
        <button
          onClick={togglePanel}
          aria-label={`Notifications (${unreadCount} unread)`}
          className="relative p-2 rounded-lg border border-white/10 hover:bg-white/5 text-gray-500 hover:text-white transition-colors"
        >
          <Bell size={14}/>
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full bg-red-500 text-[9px] font-bold text-white flex items-center justify-center animate-pulse"
              style={{ boxShadow: "0 0 8px rgba(239,68,68,0.6)" }}>
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* Notification Panel */}
        {showPanel && (
          <>
            {/* Click-outside overlay */}
            <div className="fixed inset-0 z-40" onClick={() => setShowPanel(false)}/>
            <div className="absolute right-0 top-10 w-80 max-h-96 rounded-xl border shadow-2xl z-50 flex flex-col animate-fade-in"
              style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
              <div className="sticky top-0 px-4 py-3 border-b flex items-center justify-between z-10 flex-shrink-0"
                style={{ borderColor: "#1F2937", background: "#0D0D0D" }}>
                <div className="flex items-center gap-2">
                  <Bell size={11} style={{ color: G }}/>
                  <span className="text-xs font-bold text-white">Live Alerts</span>
                  {unreadCount > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400 font-mono">{unreadCount} new</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {feed.length > 0 && (
                    <button onClick={markAllRead} title="Mark all read"
                      className="text-gray-500 hover:text-white transition-colors">
                      <CheckCheck size={12}/>
                    </button>
                  )}
                  <button onClick={() => setShowPanel(false)} className="text-gray-500 hover:text-white">
                    <X size={12}/>
                  </button>
                </div>
              </div>

              <div className="overflow-y-auto flex-1">
                {feed.length === 0 ? (
                  <div className="px-4 py-10 text-center">
                    <AlertTriangle size={20} className="mx-auto mb-2 text-gray-700"/>
                    <p className="text-gray-600 text-xs">No alerts yet.</p>
                    <p className="text-gray-700 text-[10px] font-mono mt-1">Monitoring active…</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-900/50">
                    {feed.map((item) => {
                      const c = cfg(item.type);
                      return <NotificationItem key={item.id} item={item} color={c.color} label={c.label} onDismiss={() => dismissItem(item.id)}/>;
                    })}
                  </div>
                )}
              </div>

              <div className="px-4 py-2 border-t text-[10px] font-mono text-gray-700 flex items-center justify-between flex-shrink-0"
                style={{ borderColor: "#1F2937" }}>
                <span>{feed.length} total</span>
                <span>Auto-refresh 12s</span>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function NotificationItem({ item, color, label, onDismiss }) {
  const since = useTimeSince(item.time);
  const isIncident = item.kind === "incident";
  return (
    <div className="px-4 py-3 hover:bg-white/[0.02] transition-colors group relative">
      <button onClick={onDismiss}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-700 hover:text-white transition-all p-0.5"
        title="Dismiss">
        <X size={10}/>
      </button>
      <div className="flex items-start gap-2.5">
        <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 animate-pulse" style={{ backgroundColor: color }}/>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold font-mono" style={{ color }}>{label}</span>
            {isIncident && (
              <span className="text-[9px] px-1 py-0.5 rounded font-mono font-bold"
                style={{ color: "#EF4444", backgroundColor: "#EF444415" }}>
                INCIDENT
              </span>
            )}
            <span className="text-[10px] font-mono text-gray-600 ml-auto">#{item.block?.toLocaleString()}</span>
          </div>
          <div className="text-xs text-gray-500 mt-0.5 truncate">{item.title || (item.insight && item.insight.slice(0, 80))}</div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded"
              style={{ color, backgroundColor: color + "15" }}>
              {Math.round((item.confidence || 0) * 100)}% conf
            </span>
            <span className="text-[10px] font-mono text-gray-700">{since}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
