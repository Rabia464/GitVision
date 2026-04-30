import { BrowserRouter as Router, Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import { Activity, LayoutDashboard, LogIn, LogOut, GitMerge, Bell, User } from "lucide-react";
import { AuthProvider, useAuth } from "./context/AuthContext";

import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import DynamicFeature from "./pages/DynamicFeature";
import Login from "./pages/Login";
import Register from "./pages/Register";

function FloatingHeader() {
  const { isLoggedIn, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header style={{
      position: 'fixed', top: '1rem', left: '50%', transform: 'translateX(-50%)',
      zIndex: 100, background: 'rgba(10, 10, 11, 0.75)', backdropFilter: 'blur(18px)',
      border: '1px solid var(--border-color)', borderRadius: '50px',
      padding: '0.75rem 2rem', display: 'flex', gap: '2rem', alignItems: 'center',
      boxShadow: '0 4px 30px rgba(0, 0, 0, 0.5)', whiteSpace: 'nowrap'
    }}>
      <Link to="/" className="flex-row gap-2" style={{ fontWeight: 700, fontSize: '1.2rem', textDecoration: 'none' }}>
        <GitMerge size={24} color="var(--accent-1)" />
        <span>GitVision</span>
      </Link>

      <nav className="flex-row gap-4" style={{ fontSize: '0.95rem' }}>
        <Link to="/dashboard" className="flex-row gap-2" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>
          <LayoutDashboard size={18} /> Dashboard
        </Link>
        <Link to="/app/profile" className="flex-row gap-2" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>
          <Activity size={18} /> Explorer
        </Link>
        {isLoggedIn && (
          <Link to="/app/notifications" className="flex-row gap-2" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>
            <Bell size={18} /> Notifications
          </Link>
        )}
      </nav>

      <div className="flex-row gap-2">
        {isLoggedIn ? (
          <button
            onClick={handleLogout}
            className="flex-row gap-2"
            style={{
              background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '20px', padding: '0.4rem 0.9rem', cursor: 'pointer',
              color: 'var(--accent-1)', fontSize: '0.9rem', fontWeight: 500,
              transition: 'all 0.2s'
            }}
          >
            <LogOut size={16} /> Logout
          </button>
        ) : (
          <Link
            to="/login"
            className="flex-row gap-2"
            style={{
              background: 'var(--accent-gradient)', borderRadius: '20px',
              padding: '0.4rem 1rem', color: '#fff', fontSize: '0.9rem',
              fontWeight: 600, textDecoration: 'none', transition: 'all 0.2s'
            }}
          >
            <LogIn size={16} /> Login
          </Link>
        )}
      </div>
    </header>
  );
}

function AppShell({ children, showHeader }) {
  return (
    <div>
      {showHeader && <FloatingHeader />}
      <div className={showHeader ? "page-wrap" : ""}>{children}</div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<AppShell showHeader={false}><Landing /></AppShell>} />
          <Route path="/dashboard" element={<AppShell showHeader={true}><Dashboard /></AppShell>} />
          <Route path="/app/:category" element={<AppShell showHeader={true}><DynamicFeature /></AppShell>} />
          <Route path="/app/:category/:username" element={<AppShell showHeader={true}><DynamicFeature /></AppShell>} />
          <Route path="/login" element={<AppShell showHeader={true}><Login /></AppShell>} />
          <Route path="/register" element={<AppShell showHeader={true}><Register /></AppShell>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
