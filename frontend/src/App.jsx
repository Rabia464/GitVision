import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import DynamicFeature from "./pages/DynamicFeature";
import Login from "./pages/Login";
import Register from "./pages/Register";

// A minimal floating header for all pages except Landing
import { Link } from "react-router-dom";
import { Activity, LayoutDashboard, LogIn, GitMerge } from "lucide-react";

function FloatingHeader() {
  return (
    <header style={{
      position: 'fixed',
      top: '1rem',
      left: '50%',
      transform: 'translateX(-50%)',
      zIndex: 100,
      background: 'rgba(10, 10, 11, 0.7)',
      backdropFilter: 'blur(16px)',
      border: '1px solid var(--border-color)',
      borderRadius: '50px',
      padding: '0.75rem 2rem',
      display: 'flex',
      gap: '2rem',
      alignItems: 'center',
      boxShadow: '0 4px 30px rgba(0, 0, 0, 0.5)'
    }}>
      <Link to="/" className="flex-row gap-2" style={{ fontWeight: 700, fontSize: '1.2rem' }}>
        <GitMerge size={24} color="var(--accent-1)" />
        <span>GitVision</span>
      </Link>
      <nav className="flex-row gap-4" style={{ fontSize: '0.95rem' }}>
        <Link to="/dashboard" className="flex-row gap-2" style={{ color: 'var(--text-muted)' }}>
          <LayoutDashboard size={18} /> Dashboard
        </Link>
        <Link to="/app/profile" className="flex-row gap-2" style={{ color: 'var(--text-muted)' }}>
          <Activity size={18} /> Explorer
        </Link>
      </nav>
      <Link to="/login" className="flex-row gap-2 muted">
        <LogIn size={18} />
      </Link>
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
      <Routes>
        <Route path="/" element={<AppShell showHeader={false}><Landing /></AppShell>} />
        <Route path="/dashboard" element={<AppShell showHeader={true}><Dashboard /></AppShell>} />
        <Route path="/app/:category" element={<AppShell showHeader={true}><DynamicFeature /></AppShell>} />
        <Route path="/app/:category/:username" element={<AppShell showHeader={true}><DynamicFeature /></AppShell>} />
        <Route path="/login" element={<AppShell showHeader={true}><Login /></AppShell>} />
        <Route path="/register" element={<AppShell showHeader={true}><Register /></AppShell>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}
