import { useEffect, useState } from "react";
import { ShieldAlert, Activity, HardDrive, Monitor, RefreshCw, AlertTriangle, Clock, Lock } from "lucide-react";
import client from "../api/client";

function LogTable({ columns, rows, emptyMsg }) {
  if (!rows.length) return <p className="muted" style={{ padding: "1.5rem", textAlign: "center" }}>{emptyMsg}</p>;
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={{ textAlign: "left", padding: "0.5rem 0.75rem", color: "var(--text-muted)", borderBottom: "1px solid var(--border-color)", whiteSpace: "nowrap" }}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
              onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              {columns.map((c) => (
                <td key={c.key} style={{ padding: "0.5rem 0.75rem", color: c.accent ? "var(--accent-2)" : "var(--text-main)", maxWidth: "280px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {c.render ? c.render(row[c.key], row) : String(row[c.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminView() {
  const [tab, setTab] = useState("activity");
  const [activityLogs, setActivityLogs] = useState([]);
  const [backupLogs, setBackupLogs] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const token = localStorage.getItem("gv_token");

  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [actRes, backRes, sessRes] = await Promise.all([
        client.get("/api/activity-logs?limit=50"),
        client.get("/api/backup-logs?limit=50"),
        client.get("/api/sessions?limit=50"),
      ]);
      setActivityLogs(actRes.data || []);
      setBackupLogs(backRes.data || []);
      setSessions(sessRes.data || []);
    } catch (err) {
      setError(err?.response?.data?.error || "Could not load admin data. Ensure you are logged in.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchData();
  }, [token]);

  const tabs = [
    { id: "activity", label: "Activity Log", icon: Activity, count: activityLogs.length },
    { id: "backup", label: "Backup Log", icon: HardDrive, count: backupLogs.length },
    { id: "sessions", label: "Sessions", icon: Monitor, count: sessions.length },
  ];

  const activityCols = [
    { key: "log_id", label: "ID", accent: true },
    { key: "action", label: "Action", render: (v) => (
      <span style={{ color: v === "INSERT" ? "#10b981" : v === "DELETE" ? "#ef4444" : "#f59e0b" }}>{v}</span>
    )},
    { key: "table_name", label: "Table" },
    { key: "details", label: "Details", render: (v) => v ? JSON.stringify(v) : "—" },
    { key: "timestamp", label: "Timestamp", render: (v) => new Date(v).toLocaleString() },
  ];

  const backupCols = [
    { key: "backup_id", label: "ID", accent: true },
    { key: "backup_type", label: "Type" },
    { key: "status", label: "Status", render: (v) => (
      <span style={{ color: v === "success" ? "#10b981" : "#ef4444" }}>{v}</span>
    )},
    { key: "backup_date", label: "Date", render: (v) => new Date(v).toLocaleString() },
  ];

  const sessionCols = [
    { key: "session_id", label: "ID", accent: true },
    { key: "login_time", label: "Logged In", render: (v) => new Date(v).toLocaleString() },
    { key: "logout_time", label: "Logged Out", render: (v) => v ? new Date(v).toLocaleString() : <span style={{ color: "#10b981" }}>Active</span> },
    { key: "ip_address", label: "IP Address" },
  ];

  const currentRows = tab === "activity" ? activityLogs : tab === "backup" ? backupLogs : sessions;
  const currentCols = tab === "activity" ? activityCols : tab === "backup" ? backupCols : sessionCols;

  return (
    <section className="animate-fade-in" style={{ animationDelay: "0.1s" }}>
      <div className="flex-row gap-4 mb-6" style={{ justifyContent: "space-between" }}>
        <div className="flex-row gap-2">
          <ShieldAlert size={24} color="var(--accent-1)" />
          <h1 style={{ marginBottom: 0 }}>Admin Console</h1>
        </div>
        <button className="btn-secondary flex-row gap-2" onClick={fetchData} disabled={loading} style={{ fontSize: "0.9rem", padding: "0.5rem 1rem" }}>
          <RefreshCw size={16} /> Refresh All
        </button>
      </div>

      {!token && (
        <div className="glass-panel" style={{ textAlign: "center", padding: "3rem" }}>
          <Lock size={48} className="muted" style={{ margin: "0 auto 1rem", display: "block" }} />
          <h2>Access Restricted</h2>
          <p className="muted">You must be logged in to access the Admin Console.</p>
        </div>
      )}

      {token && error && (
        <div className="flex-row gap-2 error" style={{ background: "rgba(239,68,68,0.1)", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
          <AlertTriangle size={20} /> {error}
        </div>
      )}

      {token && (
        <>
          {/* Tab Bar */}
          <div className="flex-row gap-2 mb-4" style={{ flexWrap: "wrap" }}>
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className="flex-row gap-2"
                style={{
                  background: tab === t.id ? "rgba(239,68,68,0.12)" : "rgba(255,255,255,0.04)",
                  border: tab === t.id ? "1px solid rgba(239,68,68,0.4)" : "1px solid var(--border-color)",
                  borderRadius: "8px", padding: "0.6rem 1rem",
                  color: tab === t.id ? "var(--accent-1)" : "var(--text-muted)",
                  cursor: "pointer", fontWeight: tab === t.id ? 600 : 400,
                  transition: "all 0.2s"
                }}
              >
                <t.icon size={16} /> {t.label}
                <span style={{ background: "rgba(255,255,255,0.08)", borderRadius: "10px", padding: "0 0.5rem", fontSize: "0.8rem" }}>
                  {t.count}
                </span>
              </button>
            ))}
          </div>

          {/* Table Panel */}
          <div className="glass-panel" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ padding: "1rem 1.25rem", borderBottom: "1px solid var(--border-color)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Clock size={16} className="muted" />
              <span className="muted" style={{ fontSize: "0.85rem" }}>Showing latest {currentRows.length} records</span>
            </div>
            {loading ? (
              <div style={{ padding: "2rem", textAlign: "center" }}>
                <div className="spinner" style={{ margin: "0 auto" }} />
              </div>
            ) : (
              <LogTable
                columns={currentCols}
                rows={currentRows}
                emptyMsg="No records found."
              />
            )}
          </div>
        </>
      )}
    </section>
  );
}
