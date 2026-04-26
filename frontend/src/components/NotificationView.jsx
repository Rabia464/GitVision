import { useEffect, useState } from "react";
import { Bell, CheckCheck, AlertTriangle, RefreshCw, Inbox } from "lucide-react";
import client from "../api/client";

export default function NotificationView() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [marking, setMarking] = useState(false);

  const token = localStorage.getItem("gv_token");

  const fetchNotifications = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await client.get("/api/notifications");
      setNotifications(res.data || []);
    } catch (err) {
      setError(err?.response?.data?.error || "Could not load notifications. Are you logged in?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchNotifications();
  }, [token]);

  const markAllRead = async () => {
    setMarking(true);
    try {
      // Mark each unread notification as read
      const unread = notifications.filter((n) => !n.is_read);
      await Promise.all(unread.map((n) => client.patch(`/api/notifications/${n.notification_id}`, { is_read: true })));
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // silently handle
    } finally {
      setMarking(false);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <section className="animate-fade-in" style={{ animationDelay: "0.1s" }}>
      <div className="flex-row gap-4 mb-6" style={{ justifyContent: "space-between" }}>
        <div className="flex-row gap-2">
          <Bell size={24} color="var(--accent-1)" />
          <h1 style={{ marginBottom: 0 }}>Notification Center</h1>
          {unreadCount > 0 && (
            <span style={{
              background: "var(--accent-gradient)", color: "#fff",
              borderRadius: "20px", padding: "0.1rem 0.6rem",
              fontSize: "0.8rem", fontWeight: 700
            }}>{unreadCount}</span>
          )}
        </div>
        <div className="flex-row gap-2">
          <button className="btn-secondary flex-row gap-2" onClick={fetchNotifications} disabled={loading} style={{ fontSize: "0.9rem", padding: "0.5rem 1rem" }}>
            <RefreshCw size={16} /> Refresh
          </button>
          {unreadCount > 0 && (
            <button className="btn-primary flex-row gap-2" onClick={markAllRead} disabled={marking} style={{ fontSize: "0.9rem", padding: "0.5rem 1rem" }}>
              <CheckCheck size={16} /> Mark All Read
            </button>
          )}
        </div>
      </div>

      {!token && (
        <div className="glass-panel" style={{ textAlign: "center", padding: "3rem" }}>
          <Bell size={48} className="muted" style={{ margin: "0 auto 1rem", display: "block" }} />
          <h2>Login Required</h2>
          <p className="muted">You must be logged in to view your notifications.</p>
        </div>
      )}

      {token && loading && <div className="spinner mb-4" />}

      {token && error && (
        <div className="flex-row gap-2 error" style={{ background: "rgba(239,68,68,0.1)", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
          <AlertTriangle size={20} /> {error}
        </div>
      )}

      {token && !loading && notifications.length === 0 && !error && (
        <div className="glass-panel" style={{ textAlign: "center", padding: "3rem" }}>
          <Inbox size={48} className="muted" style={{ margin: "0 auto 1rem", display: "block" }} />
          <h2 className="muted">All Caught Up</h2>
          <p className="muted">No notifications yet. Start following developers to see activity here.</p>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {notifications.map((n) => (
          <div
            key={n.notification_id}
            className="glass-panel"
            style={{
              display: "flex", alignItems: "center", gap: "1rem",
              padding: "1rem 1.25rem",
              borderLeft: n.is_read ? "3px solid transparent" : "3px solid var(--accent-1)",
              opacity: n.is_read ? 0.6 : 1,
              transition: "all 0.2s ease"
            }}
          >
            <Bell size={18} color={n.is_read ? "var(--text-muted)" : "var(--accent-1)"} style={{ flexShrink: 0 }} />
            <div style={{ flexGrow: 1 }}>
              <p style={{ margin: 0, fontSize: "0.95rem" }}>{n.message}</p>
              <p className="muted" style={{ margin: "0.2rem 0 0", fontSize: "0.8rem" }}>
                {new Date(n.created_at).toLocaleString()}
              </p>
            </div>
            {!n.is_read && (
              <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--accent-1)", flexShrink: 0 }} />
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
