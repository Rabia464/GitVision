import { useEffect, useState } from "react";
import { User, Users, Star, BookOpen, AlertTriangle, TrendingUp, BarChart, Code2, Zap } from "lucide-react";
import client from "../api/client";

export default function ProfileView({ username }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!username) return;
    const run = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await client.get(`/api/github/profile/${encodeURIComponent(username)}`);
        setProfile(res.data);
      } catch (err) {
        setError(err?.response?.data?.error || "Could not load profile.");
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [username]);

  if (!username) {
    return (
      <section className="glass-panel text-center">
        <h2 style={{ marginBottom: '1rem' }}>No Target Selected</h2>
        <p className="muted">Please select a username from the Dashboard to analyze their profile.</p>
      </section>
    );
  }

  // Calculate Developer Score
  const devScore = profile ? (profile.followers * 2) + (profile.total_stars * 3) + (profile.repo_count * 1) : 0;

  return (
    <section className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="flex-row gap-2 mb-4">
        <User size={24} color="var(--accent-1)" />
        <h1 style={{ marginBottom: 0 }}>Profile Analysis: {username}</h1>
      </div>

      {loading && <div className="spinner mb-4" aria-label="loading" />}
      {error && (
        <div className="flex-row gap-2 error" style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontWeight: 500 }}>
           <AlertTriangle size={20} /> {error}
        </div>
      )}

      {profile && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Top Section: Metrics and Score */}
          <div className="dashboard-grid">
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.8rem', margin: 0 }}>Core Metrics</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '10px' }}>
                  <div className="flex-row gap-2 muted mb-2"><Users size={18}/> Followers</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-main)' }}>{profile.followers}</div>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '10px' }}>
                  <div className="flex-row gap-2 muted mb-2"><Users size={18}/> Following</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-main)' }}>{profile.following}</div>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '10px' }}>
                  <div className="flex-row gap-2 muted mb-2"><BookOpen size={18}/> Repos</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-2)' }}>{profile.repo_count}</div>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '10px' }}>
                  <div className="flex-row gap-2 muted mb-2"><Star size={18}/> Total Stars</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-1)' }}>{profile.total_stars}</div>
                </div>
              </div>
            </div>

            {/* Developer Score Card */}
            <div className="glass-panel" style={{ 
              display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', 
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(245, 158, 11, 0.15) 100%)',
              border: '2px solid rgba(245, 158, 11, 0.4)',
              textAlign: 'center', position: 'relative', overflow: 'hidden'
            }}>
              <div style={{ position: 'absolute', top: '-20px', left: '-20px', opacity: 0.1 }}>
                <Zap size={140} color="var(--accent-2)" />
              </div>
              <h3 style={{ margin: 0, color: 'var(--accent-2)', textTransform: 'uppercase', letterSpacing: '2px', fontSize: '0.95rem' }}>
                Developer Power Score
              </h3>
              <div style={{ 
                fontSize: '4.5rem', fontWeight: 800, fontFamily: "'Outfit', sans-serif", 
                background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                marginBottom: '1rem', lineHeight: 1
              }}>
                {devScore}
              </div>
              <p className="muted" style={{ fontSize: '0.85rem', margin: 0, zIndex: 1 }}>
                (Followers × 2) + (Stars × 3) + (Repos × 1)
              </p>
            </div>
          </div>

          {/* Analytics Placeholders Section */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1rem' }}>
            <h3 style={{ margin: 0, paddingBottom: '0.8rem', borderBottom: '1px solid var(--border-color)' }}>
              Analytics & Growth Patterns
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
              
              <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px dashed var(--border-color)', borderRadius: '12px', padding: '1.5rem', minHeight: '180px', display: 'flex', flexDirection: 'column' }}>
                <div className="flex-row gap-2 muted mb-4"><TrendingUp size={18} /> Follower Growth</div>
                <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <p className="muted" style={{ fontSize: '0.85rem' }}>Chart Placeholder:<br/>Snapshot Line Graph</p>
                </div>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px dashed var(--border-color)', borderRadius: '12px', padding: '1.5rem', minHeight: '180px', display: 'flex', flexDirection: 'column' }}>
                <div className="flex-row gap-2 muted mb-4"><BarChart size={18} /> Repository Growth</div>
                <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <p className="muted" style={{ fontSize: '0.85rem' }}>Chart Placeholder:<br/>Repo Creation Timeline</p>
                </div>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px dashed var(--border-color)', borderRadius: '12px', padding: '1.5rem', minHeight: '180px', display: 'flex', flexDirection: 'column' }}>
                <div className="flex-row gap-2 muted mb-4"><Code2 size={18} /> Most Used Language</div>
                <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <p className="muted" style={{ fontSize: '0.85rem' }}>Chart Placeholder:<br/>Language Pie Chart</p>
                </div>
              </div>

            </div>
          </div>

        </div>
      )}
    </section>
  );
}
