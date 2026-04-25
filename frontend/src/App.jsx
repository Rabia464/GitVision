import { BrowserRouter as Router, Link, Navigate, Route, Routes } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import Repository from "./pages/Repository";

function AppShell({ children }) {
  return (
    <div>
      <header className="top-nav">
        <div className="container nav-content">
          <h2 className="brand">GitVision</h2>
          <nav className="nav-links">
            <Link to="/">Dashboard</Link>
            <Link to="/profile">Profile</Link>
            <Link to="/repositories">Repositories</Link>
            <Link to="/login">Login</Link>
          </nav>
        </div>
      </header>
      <div className="container page-wrap">{children}</div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/profile/:username" element={<Profile />} />
          <Route path="/repositories" element={<Repository />} />
          <Route path="/repositories/:username" element={<Repository />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AppShell>
    </Router>
  );
}
