import { useParams, Link } from "react-router-dom";
import { User, Database, GitCompare, Bell, ShieldAlert, Activity, ChevronRight } from "lucide-react";
import ProfileView from "../components/ProfileView";
import RepositoryView from "../components/RepositoryView";
import ComparisonView from "../components/ComparisonView";
import NotificationView from "../components/NotificationView";
import AdminView from "../components/AdminView";

export default function DynamicFeature() {
  const { category, username } = useParams();

  const renderCategory = () => {
    switch (category) {
      case "profile":
        return <ProfileView username={username} />;
      case "repositories":
        return <RepositoryView username={username} />;
      case "compare":
        return <ComparisonView />;
      case "notifications":
        return <NotificationView />;
      case "admin":
        return <AdminView />;
      default:
        return (
          <div className="glass-panel" style={{ padding: "4rem 2rem", textAlign: "center" }}>
            <Activity size={48} className="muted" style={{ margin: "0 auto 1rem", display: "block" }} />
            <h2 className="muted">Unknown Module: {category}</h2>
            <p className="muted">Select an active module from the sidebar.</p>
          </div>
        );
    }
  };

  const menuItems = [
    { title: "Profile Analysis", icon: User, path: "profile" },
    { title: "Repository Data", icon: Database, path: "repositories" },
    { title: "Head-to-Head Compare", icon: GitCompare, path: "compare" },
    { title: "Notifications", icon: Bell, path: "notifications" },
    { title: "Admin Console", icon: ShieldAlert, path: "admin" },
  ];

  return (
    <div className="container animate-fade-in" style={{
      display: "grid",
      gridTemplateColumns: "240px 1fr",
      gap: "2rem",
      minHeight: "80vh"
    }}>
      {/* Sidebar */}
      <aside>
        <div className="glass-panel" style={{ position: "sticky", top: "6rem", padding: "1rem" }}>
          <h3 style={{
            marginBottom: "1rem", padding: "0 0.5rem 0.75rem",
            borderBottom: "1px solid var(--border-color)",
            fontSize: "0.8rem", textTransform: "uppercase",
            letterSpacing: "1.5px", color: "var(--text-muted)"
          }}>
            Modules
          </h3>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
            {menuItems.map((item) => {
              const active = category === item.path;
              const linkPath = username ? `/app/${item.path}/${username}` : `/app/${item.path}`;
              return (
                <Link
                  key={item.path}
                  to={linkPath}
                  style={{
                    display: "flex", alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.7rem 0.75rem",
                    borderRadius: "8px",
                    background: active ? "rgba(239, 68, 68, 0.1)" : "transparent",
                    borderLeft: active ? "3px solid var(--accent-1)" : "3px solid transparent",
                    color: active ? "var(--accent-1)" : "var(--text-muted)",
                    fontWeight: active ? 600 : 400,
                    fontSize: "0.92rem",
                    transition: "all 0.2s ease",
                    textDecoration: "none"
                  }}
                  onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
                  onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = "transparent"; }}
                >
                  <div className="flex-row gap-2">
                    <item.icon size={17} /> {item.title}
                  </div>
                  {active && <ChevronRight size={15} />}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Main Panel */}
      <main style={{ minWidth: 0 }}>
        {renderCategory()}
      </main>
    </div>
  );
}
