import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus, Mail, Lock, User, AlertTriangle, GitMerge, CheckCircle } from "lucide-react";
import client from "../api/client";

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await client.post("/api/auth/register", { username, email, password });
      navigate("/login");
    } catch (err) {
      setError(err?.response?.data?.error || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", position: "relative" }}>
      {/* BG glow */}
      <div style={{ position: "fixed", bottom: "20%", right: "30%", width: "40vw", height: "40vw", background: "radial-gradient(circle, rgba(245,158,11,0.06), transparent 70%)", borderRadius: "50%", pointerEvents: "none", zIndex: 0 }} />

      <div className="glass-panel animate-fade-in" style={{ width: "100%", maxWidth: "420px", padding: "2.5rem", zIndex: 1 }}>
        {/* Logo */}
        <div className="flex-row gap-2 mb-8" style={{ justifyContent: "center" }}>
          <GitMerge size={28} color="var(--accent-1)" />
          <span style={{ fontSize: "1.4rem", fontWeight: 700 }}>GitVision</span>
        </div>

        <h1 style={{ textAlign: "center", fontSize: "1.8rem", marginBottom: "0.4rem" }}>Create Account</h1>
        <p className="muted" style={{ textAlign: "center", marginBottom: "2rem", fontSize: "0.95rem" }}>Join the GitVision developer platform</p>

        <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ position: "relative" }}>
            <User size={18} style={{ position: "absolute", top: "50%", left: "1rem", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              id="register-username"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ paddingLeft: "3rem" }}
              required
            />
          </div>
          <div style={{ position: "relative" }}>
            <Mail size={18} style={{ position: "absolute", top: "50%", left: "1rem", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              id="register-email"
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ paddingLeft: "3rem" }}
              required
            />
          </div>
          <div style={{ position: "relative" }}>
            <Lock size={18} style={{ position: "absolute", top: "50%", left: "1rem", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              id="register-password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ paddingLeft: "3rem" }}
              required
            />
          </div>

          {error && (
            <div className="flex-row gap-2 error" style={{ background: "rgba(239,68,68,0.1)", padding: "0.75rem 1rem", borderRadius: "8px", fontSize: "0.9rem" }}>
              <AlertTriangle size={16} /> {error}
            </div>
          )}

          <button id="register-submit" className="btn-primary" type="submit" disabled={loading} style={{ marginTop: "0.5rem", height: "3rem" }}>
            {loading ? <div className="spinner" /> : <><UserPlus size={18} /> Create Account</>}
          </button>
        </form>

        <p className="muted" style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.9rem" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "var(--accent-2)", fontWeight: 600 }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
