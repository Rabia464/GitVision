import { useState } from "react";
import { Link } from "react-router-dom";
import { CloudDownload, CheckCircle, AlertTriangle, ArrowRight, User, Settings, Database, Activity } from "lucide-react";
import client from "../api/client";

export default function Dashboard() {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [lastImported, setLastImported] = useState("");

  const handleImport = async (e) => {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed) {
      setError("Please enter a GitHub username.");
      return;
    }
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await client.get(`/api/github/import/${encodeURIComponent(trimmed)}`);
      setLastImported(res.data.imported_username);
      setMessage(
        `${res.data.repos_upserted} repositories imported successfully.`
      );
    } catch (err) {
      const apiMsg = err?.response?.data?.error;
      setError(apiMsg || "Import failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container animate-fade-in">
      <div className="flex-row gap-4 mb-8">
        <div style={{ background: 'var(--accent-gradient)', padding: '0.8rem', borderRadius: '12px' }}>
          <Settings size={28} color="#fff" />
        </div>
        <div>
          <h1 style={{ marginBottom: 0, fontSize: '2rem' }}>Control Center</h1>
          <p className="muted" style={{ marginTop: '0.2rem' }}>Import and manage data</p>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Main Import Panel */}
        <section className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div className="flex-row gap-2 mb-4">
            <CloudDownload size={24} color="var(--accent-1)" />
            <h2 style={{ marginBottom: 0, fontSize: '1.5rem' }}>Data Pipeline</h2>
          </div>
          <p className="muted mb-8" style={{ fontSize: '1.05rem', lineHeight: 1.5 }}>
            Trigger an automated extraction sequence. GitVision will pull the target's profile, repositories, and languages, then safely persist them into the PostgreSQL cluster.
          </p>
          
          <form onSubmit={handleImport}>
            <div style={{ position: 'relative', marginBottom: '1rem' }}>
              <User size={20} className="muted" style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', left: '1rem' }} />
              <input
                type="text"
                placeholder="Target GitHub Username..."
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{ paddingLeft: '3rem', height: '3.5rem', fontSize: '1.1rem' }}
              />
            </div>
            
            <button className="btn-primary w-full" type="submit" disabled={loading} style={{ height: '3.5rem' }}>
              {loading ? (
                <>
                  <div className="spinner" /> Executing Pipeline...
                </>
              ) : (
                <>
                  Initiate Extraction <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="flex-row gap-2 error" style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginTop: '1.5rem', fontWeight: 500 }}>
               <AlertTriangle size={20} /> {error}
            </div>
          )}
          {message && (
            <div className="flex-row gap-2 success" style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '1rem', borderRadius: '8px', marginTop: '1.5rem', fontWeight: 500 }}>
              <CheckCircle size={20} /> {message}
            </div>
          )}
        </section>

        {/* Side Panel */}
        <section className="glass-panel" style={{ background: 'rgba(26,26,30, 0.3)' }}>
          <div className="flex-row gap-2 mb-4">
            <Database size={24} className="muted" />
            <h3 style={{ marginBottom: 0, color: 'var(--text-muted)' }}>Latest Activity</h3>
          </div>
          
          {!lastImported ? (
            <div style={{ padding: '2rem 0', textAlign: 'center', opacity: 0.5 }}>
              <Activity size={48} className="muted mb-4" style={{ margin: '0 auto', display: 'block' }} />
              <p>No recent extractions.</p>
            </div>
          ) : (
            <div className="animate-fade-in" style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.5rem' }}>
              <div className="flex-row gap-2 mb-4" style={{ color: 'var(--accent-2)', fontWeight: 600 }}>
                <CheckCircle size={20} /> Target Acquired: {lastImported}
              </div>
              <p className="muted mb-4">Data is now available in the analytics engine.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                <Link to={`/app/profile/${lastImported}`} className="btn-secondary flex-row gap-2" style={{ justifyContent: 'center' }}>
                  <User size={18} /> View Profile Schema
                </Link>
                <Link to={`/app/repositories/${lastImported}`} className="btn-secondary flex-row gap-2" style={{ justifyContent: 'center' }}>
                  <Database size={18} /> View Repositories Schema
                </Link>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
