import { useEffect, useState, useCallback } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────
type Status = "pending" | "approved" | "editing" | "rejected" | "awaiting_capture" | "capture_ready" | "rendering";

interface QueueItem {
  id: string;
  day: string;
  topic: string;
  hook: string;
  script: string;
  tags: string;
  source_url: string;
  reference_url: string;
  status: Status;
  notes: string;
  capture_file: string;
  decided_at: string | null;
  created_at: string;
}

interface QueueStats {
  pending: number;
  approved: number;
  rejected: number;
  awaiting_capture: number;
  capture_ready: number;
  total: number;
}

// ── Status badge config ───────────────────────────────────────────────────────
const STATUS_META: Record<Status, { label: string; color: string; dot: string }> = {
  pending:          { label: "PENDING",         color: "#6B7280", dot: "#6B7280" },
  approved:         { label: "APPROVED",        color: "#10B981", dot: "#10B981" },
  editing:          { label: "EDITING",         color: "#F59E0B", dot: "#F59E0B" },
  rejected:         { label: "REJECTED",        color: "#EF4444", dot: "#EF4444" },
  awaiting_capture: { label: "AWAITING CAPTURE",color: "#8B5CF6", dot: "#8B5CF6" },
  capture_ready:    { label: "CAPTURE READY",   color: "#22D3EE", dot: "#22D3EE" },
  rendering:        { label: "RENDERING",       color: "#F97316", dot: "#F97316" },
};

// ── API helpers ───────────────────────────────────────────────────────────────
const api = {
  list: (status?: string) =>
    fetch(`/api/review${status ? `?status=${status}` : ""}`).then((r) => r.json()),
  sync: () => fetch("/api/review/sync", { method: "POST" }).then((r) => r.json()),
  approve: (id: string) =>
    fetch(`/api/review/${id}/approve`, { method: "POST" }).then((r) => r.json()),
  reject: (id: string, reason: string) =>
    fetch(`/api/review/${id}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    }).then((r) => r.json()),
  update: (id: string, patch: Partial<QueueItem>) =>
    fetch(`/api/review/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }).then((r) => r.json()),
  requestCapture: (id: string) =>
    fetch(`/api/review/${id}/request-capture`, { method: "POST" }).then((r) => r.json()),
  captureStatus: (id: string) =>
    fetch(`/api/review/${id}/capture-status`).then((r) => r.json()),
  stats: () => fetch("/api/review/stats").then((r) => r.json()),
};

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <div style={{
      background: "#0F1623", border: "1px solid #1E2D40", borderRadius: 10,
      padding: "18px 22px", minWidth: 140, flex: 1,
    }}>
      <div style={{ fontSize: 11, color: "#6B7280", fontWeight: 600, letterSpacing: 1, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 700, color: accent || "#F1F5F9", lineHeight: 1 }}>{value}</div>
    </div>
  );
}

// ── Status badge ──────────────────────────────────────────────────────────────
function Badge({ status }: { status: Status }) {
  const m = STATUS_META[status] || { label: status.toUpperCase(), color: "#6B7280", dot: "#6B7280" };
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "3px 10px", borderRadius: 20, border: `1px solid ${m.color}22`,
      background: `${m.color}18`, color: m.color,
      fontSize: 10, fontWeight: 700, letterSpacing: 1,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: m.dot, flexShrink: 0 }} />
      {m.label}
    </span>
  );
}

// ── Inline editor ─────────────────────────────────────────────────────────────
function InlineEditor({
  item, onSave, onCancel,
}: { item: QueueItem; onSave: (patch: Partial<QueueItem>) => void; onCancel: () => void }) {
  const [hook, setHook] = useState(item.hook);
  const [script, setScript] = useState(item.script);
  const [refUrl, setRefUrl] = useState(item.reference_url);
  const [notes, setNotes] = useState(item.notes);

  const ta: React.CSSProperties = {
    width: "100%", background: "#0A0E17", border: "1px solid #1E2D40",
    borderRadius: 6, color: "#CBD5E1", padding: "8px 10px", fontSize: 13,
    resize: "vertical", fontFamily: "inherit", boxSizing: "border-box",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
      <label style={{ fontSize: 11, color: "#22D3EE", fontWeight: 600 }}>HOOK</label>
      <textarea style={{ ...ta, minHeight: 56 }} value={hook} onChange={(e) => setHook(e.target.value)} />
      <label style={{ fontSize: 11, color: "#22D3EE", fontWeight: 600 }}>SCRIPT</label>
      <textarea style={{ ...ta, minHeight: 96 }} value={script} onChange={(e) => setScript(e.target.value)} />
      <label style={{ fontSize: 11, color: "#22D3EE", fontWeight: 600 }}>REFERENCE SHORTS URL (style clone)</label>
      <input
        style={{ ...ta, minHeight: "auto", height: 36 }}
        placeholder="https://youtube.com/shorts/..."
        value={refUrl}
        onChange={(e) => setRefUrl(e.target.value)}
      />
      <label style={{ fontSize: 11, color: "#22D3EE", fontWeight: 600 }}>NOTES</label>
      <textarea style={{ ...ta, minHeight: 48 }} value={notes} onChange={(e) => setNotes(e.target.value)} />
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button onClick={onCancel} style={btnStyle("#1E2D40", "#94A3B8")}>Cancel</button>
        <button onClick={() => onSave({ hook, script, reference_url: refUrl, notes })}
          style={btnStyle("#22D3EE", "#0A0E17")}>Save changes</button>
      </div>
    </div>
  );
}

function btnStyle(bg: string, color: string): React.CSSProperties {
  return {
    padding: "7px 16px", borderRadius: 6, border: "none", cursor: "pointer",
    background: bg, color, fontSize: 12, fontWeight: 600, letterSpacing: 0.5,
  };
}

// ── Queue card ────────────────────────────────────────────────────────────────
function QueueCard({
  item, onAction,
}: { item: QueueItem; onAction: (id: string, action: string, data?: unknown) => void }) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);

  return (
    <div style={{
      background: "#0F1623", border: "1px solid #1E2D40", borderRadius: 12,
      padding: "18px 20px", marginBottom: 10,
      borderLeft: `3px solid ${STATUS_META[item.status]?.dot || "#6B7280"}`,
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12, justifyContent: "space-between" }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4, flexWrap: "wrap" }}>
            <Badge status={item.status} />
            {item.day && (
              <span style={{ fontSize: 11, color: "#4B5563", fontWeight: 600 }}>DAY {item.day}</span>
            )}
            {item.reference_url && (
              <span style={{ fontSize: 10, color: "#22D3EE", background: "#22D3EE18",
                border: "1px solid #22D3EE22", borderRadius: 12, padding: "2px 8px" }}>
                REF STYLE
              </span>
            )}
          </div>
          <div style={{ fontSize: 15, fontWeight: 600, color: "#E2E8F0", marginBottom: 4,
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {item.topic}
          </div>
          {item.hook && (
            <div style={{ fontSize: 12, color: "#64748B", fontStyle: "italic",
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              "{item.hook}"
            </div>
          )}
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {(item.status === "pending" || item.status === "editing") && (
            <>
              <button onClick={() => onAction(item.id, "approve")}
                style={btnStyle("#10B981", "#fff")}>✓ Approve</button>
              <button onClick={() => setEditing(true)}
                style={btnStyle("#1E2D40", "#F59E0B")}>✎ Edit</button>
              <button onClick={() => setShowReject(!showReject)}
                style={btnStyle("#1E2D40", "#EF4444")}>✕ Reject</button>
            </>
          )}
          {item.status === "approved" && (
            <button onClick={() => onAction(item.id, "request-capture")}
              style={btnStyle("#8B5CF6", "#fff")}>⏺ Request Capture</button>
          )}
          {item.status === "awaiting_capture" && (
            <button onClick={() => onAction(item.id, "check-capture")}
              style={btnStyle("#22D3EE", "#0A0E17")}>↻ Check Capture</button>
          )}
          <button onClick={() => setExpanded(!expanded)}
            style={btnStyle("#0A0E17", "#6B7280")}>{expanded ? "▲" : "▼"}</button>
        </div>
      </div>
      {showReject && (
        <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center" }}>
          <input
            placeholder="Reason (optional)"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            style={{ flex: 1, background: "#0A0E17", border: "1px solid #1E2D40",
              borderRadius: 6, color: "#CBD5E1", padding: "6px 10px", fontSize: 12 }}
          />
          <button onClick={() => { onAction(item.id, "reject", rejectReason); setShowReject(false); }}
            style={btnStyle("#EF4444", "#fff")}>Confirm reject</button>
        </div>
      )}
      {expanded && !editing && (
        <div style={{ marginTop: 14, borderTop: "1px solid #1E2D40", paddingTop: 14,
          display: "flex", flexDirection: "column", gap: 8 }}>
          {item.script && (
            <div>
              <div style={{ fontSize: 10, color: "#22D3EE", fontWeight: 700, marginBottom: 4 }}>SCRIPT</div>
              <div style={{ fontSize: 12, color: "#94A3B8", whiteSpace: "pre-wrap" }}>{item.script}</div>
            </div>
          )}
          {item.tags && (
            <div>
              <div style={{ fontSize: 10, color: "#22D3EE", fontWeight: 700, marginBottom: 4 }}>TAGS</div>
              <div style={{ fontSize: 12, color: "#64748B" }}>{item.tags}</div>
            </div>
          )}
          {item.source_url && (
            <div>
              <div style={{ fontSize: 10, color: "#22D3EE", fontWeight: 700, marginBottom: 4 }}>SOURCE</div>
              <a href={item.source_url} target="_blank" rel="noreferrer"
                style={{ fontSize: 12, color: "#38BDF8" }}>{item.source_url}</a>
            </div>
          )}
          {item.reference_url && (
            <div>
              <div style={{ fontSize: 10, color: "#22D3EE", fontWeight: 700, marginBottom: 4 }}>STYLE REFERENCE</div>
              <a href={item.reference_url} target="_blank" rel="noreferrer"
                style={{ fontSize: 12, color: "#22D3EE" }}>{item.reference_url}</a>
            </div>
          )}
          {item.capture_file && (
            <div>
              <div style={{ fontSize: 10, color: "#8B5CF6", fontWeight: 700, marginBottom: 4 }}>CAPTURE FILE</div>
              <div style={{ fontSize: 12, color: "#A78BFA" }}>{item.capture_file}</div>
            </div>
          )}
          {item.notes && (
            <div>
              <div style={{ fontSize: 10, color: "#F59E0B", fontWeight: 700, marginBottom: 4 }}>NOTES</div>
              <div style={{ fontSize: 12, color: "#FCD34D" }}>{item.notes}</div>
            </div>
          )}
          {item.decided_at && (
            <div style={{ fontSize: 10, color: "#374151", marginTop: 4 }}>Decided: {item.decided_at}</div>
          )}
          <button onClick={() => setEditing(true)} style={{ ...btnStyle("#1E2D40", "#F59E0B"), alignSelf: "flex-start", marginTop: 4 }}>
            ✎ Edit this Short
          </button>
        </div>
      )}
      {editing && (
        <InlineEditor
          item={item}
          onSave={(patch) => { onAction(item.id, "update", patch); setEditing(false); setExpanded(false); }}
          onCancel={() => setEditing(false)}
        />
      )}
    </div>
  );
}

// ── Filter tab bar ────────────────────────────────────────────────────────────
function FilterBar({
  active, onChange, counts,
}: { active: string; onChange: (v: string) => void; counts: Partial<QueueStats> }) {
  const tabs = [
    { key: "", label: "All", count: counts.total },
    { key: "pending", label: "Pending", count: counts.pending },
    { key: "approved", label: "Approved", count: counts.approved },
    { key: "awaiting_capture", label: "Capture", count: counts.awaiting_capture },
    { key: "capture_ready", label: "Ready", count: counts.capture_ready },
    { key: "rejected", label: "Rejected", count: counts.rejected },
  ];
  return (
    <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 16 }}>
      {tabs.map((tab) => (
        <button key={tab.key} onClick={() => onChange(tab.key)} style={{
          padding: "6px 14px", borderRadius: 20, border: "1px solid",
          borderColor: active === tab.key ? "#22D3EE" : "#1E2D40",
          background: active === tab.key ? "#22D3EE18" : "transparent",
          color: active === tab.key ? "#22D3EE" : "#6B7280",
          fontSize: 12, fontWeight: 600, cursor: "pointer",
        }}>
          {tab.label}{tab.count !== undefined ? ` (${tab.count ?? 0})` : ""}
        </button>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ReviewQueue() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [stats, setStats] = useState<Partial<QueueStats>>({});
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [csvExists, setCsvExists] = useState(false);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [qRes, sRes] = await Promise.all([api.list(filter), api.stats()]);
      setItems(qRes.items || []);
      setCsvExists(qRes.csv_exists || false);
      setStats(sRes);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const id = setInterval(async () => {
      const awaiting = items.filter((i) => i.status === "awaiting_capture");
      for (const item of awaiting) {
        const res = await api.captureStatus(item.id);
        if (res.ready) { showToast(`Capture ready: ${item.topic}`); refresh(); }
      }
    }, 15000);
    return () => clearInterval(id);
  }, [items, refresh]);

  const handleSync = async () => {
    setSyncing(true);
    const res = await api.sync();
    setSyncing(false);
    showToast(`Synced — ${res.added} new shorts added (${res.total} total)`);
    refresh();
  };

  const handleAction = async (id: string, action: string, data?: unknown) => {
    let res: { ok?: boolean; brief_path?: string } = {};
    if (action === "approve")         res = await api.approve(id);
    else if (action === "reject")     res = await api.reject(id, String(data || ""));
    else if (action === "update")     res = await api.update(id, data as Partial<QueueItem>);
    else if (action === "request-capture") {
      res = await api.requestCapture(id);
      if (res.ok) showToast(`Capture brief written — check data/captures/${id}/capture_brief.md`);
    }
    else if (action === "check-capture") {
      const cap = await api.captureStatus(id);
      showToast(cap.ready ? `Capture ready: ${cap.file}` : "No MP4 found yet — drop your recording into the captures folder");
    }
    if (action !== "check-capture") refresh();
  };

  return (
    <div style={{ fontFamily: "'Inter', 'Segoe UI', sans-serif", color: "#E2E8F0", padding: "0 0 40px" }}>
      {toast && (
        <div style={{
          position: "fixed", top: 20, right: 20, zIndex: 9999,
          background: "#0F1623", border: "1px solid #22D3EE",
          borderRadius: 10, padding: "12px 20px", color: "#22D3EE",
          fontSize: 13, fontWeight: 600, maxWidth: 380,
          boxShadow: "0 4px 24px #00000088",
        }}>{toast}</div>
      )}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontSize: 11, color: "#22D3EE", fontWeight: 700, letterSpacing: 2, marginBottom: 4 }}>OPERATIONAL WORKSPACE</div>
            <h2 style={{ margin: 0, fontSize: 28, fontWeight: 700, color: "#F1F5F9" }}>Shorts Review Queue</h2>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {!csvExists && (
              <span style={{ fontSize: 11, color: "#EF4444", background: "#EF444418",
                border: "1px solid #EF444433", borderRadius: 8, padding: "4px 10px" }}>
                No shorts_plan.csv — run the pipeline first
              </span>
            )}
            <button onClick={handleSync} disabled={syncing} style={btnStyle("#22D3EE", "#0A0E17")}>
              {syncing ? "Syncing…" : "↻ Sync from CSV"}
            </button>
            <button onClick={refresh} style={btnStyle("#1E2D40", "#94A3B8")}>Refresh</button>
          </div>
        </div>
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 24 }}>
        <StatCard label="TOTAL SHORTS"     value={stats.total ?? 0} />
        <StatCard label="PENDING REVIEW"   value={stats.pending ?? 0} accent="#6B7280" />
        <StatCard label="APPROVED"         value={stats.approved ?? 0} accent="#10B981" />
        <StatCard label="AWAITING CAPTURE" value={stats.awaiting_capture ?? 0} accent="#8B5CF6" />
        <StatCard label="CAPTURE READY"    value={stats.capture_ready ?? 0} accent="#22D3EE" />
        <StatCard label="REJECTED"         value={stats.rejected ?? 0} accent="#EF4444" />
      </div>
      <div style={{
        background: "#0A0E17", border: "1px solid #1E2D40", borderRadius: 10,
        padding: "14px 18px", marginBottom: 20,
        display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap",
      }}>
        {["Sync CSV", "→", "Review each Short", "→", "Approve / Edit / Reject",
          "→", "Request Capture (OBS)", "→", "Drop MP4", "→", "Render"].map((step, i) => (
          <span key={i} style={{
            fontSize: 11, fontWeight: step === "→" ? 400 : 600,
            color: step === "→" ? "#374151" : i % 4 === 0 ? "#22D3EE" : "#94A3B8",
          }}>{step}</span>
        ))}
      </div>
      <FilterBar active={filter} onChange={setFilter} counts={stats} />
      {loading ? (
        <div style={{ color: "#4B5563", fontSize: 13, padding: "40px 0", textAlign: "center" }}>Loading queue…</div>
      ) : items.length === 0 ? (
        <div style={{
          background: "#0F1623", border: "1px dashed #1E2D40", borderRadius: 12,
          padding: "40px 24px", textAlign: "center", color: "#374151",
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📋</div>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>No shorts in this view</div>
          <div style={{ fontSize: 12 }}>
            {filter ? `No items with status "${filter}"` : "Click Sync from CSV to load your shorts plan"}
          </div>
        </div>
      ) : (
        items.map((item) => (
          <QueueCard key={item.id} item={item} onAction={handleAction} />
        ))
      )}
    </div>
  );
}
