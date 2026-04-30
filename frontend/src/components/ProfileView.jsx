import { useEffect, useState } from "react";
import { User, Users, Star, BookOpen, AlertTriangle, Zap } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { useRequireAuth } from "../context/AuthContext";
import client from "../api/client";

export default function ProfileView({ username }) {
  const [profile, setProfile] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [repos, setRepos] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const requireAuth = useRequireAuth();

  // Colors for the Pie Chart
  const COLORS = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899'];

  useEffect(() => {
    if (!username) return;
    const run = async () => {
      setLoading(true);
      setError("");
      try {
        // 1. Fetch Profile
        const res = await client.get(`/api/github/profile/${encodeURIComponent(username)}`);
        const userData = res.data;
        setProfile(userData);

        try {
           // 2. Fetch Snapshots (Historical Data)
           if (userData && userData.user_id) {
             const snapRes = await client.get(`/api/snapshots?user_id=${userData.user_id}`);
             // Reverse so chronological order (API returns DESC)
             const chartData = (snapRes.data || []).reverse().map(s => ({
               name: s.date.substring(5), // mm-dd
               followers: s.followers,
               repos: s.repo_count
             }));
             setSnapshots(chartData);
             
             // 3. Fetch Follow status if logged in
             // We'd check GET /api/users/<uid>/followers or similar. For now, assuming false.
           }
        } catch(e) {
           console.warn("Could not fetch snapshots", e);
        }

        try {
           // 4. Fetch Repos for Language Pie Chart
           const repoRes = await client.get(`/api/github/repositories/${encodeURIComponent(username)}`);
           setRepos(repoRes.data || []);
        } catch(e) {
           console.warn("Could not fetch repos for language chart", e);
        }

      } catch (err) {
        setError(err?.response?.data?.error || "Could not load profile.");
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [username]);

  const handleFollow = () => {
    requireAuth(async () => {
      if (!profile || !profile.user_id) return;
      setActionLoading(true);
      try {
        if (isFollowing) {
          await client.delete(`/api/users/${profile.user_id}/follow`);
          setIsFollowing(false);
        } else {
          await client.post(`/api/users/${profile.user_id}/follow`);
          setIsFollowing(true);
        }
      } catch (err) {
        setError("Follow action failed.");
      } finally {
        setActionLoading(false);
      }
    });
  };

  if (!username) {
    return (
      <section className="glass-panel text-center">
        <h2 style={{ marginBottom: '1rem' }}>No Target Selected</h2>
        <p className="muted">Please select a username from the Dashboard to analyze their profile.</p>
      </section>
    );
  }

  const devScore = profile ? (profile.followers * 2) + (profile.total_stars * 3) + (profile.repo_count * 1) : 0;

  // Process languages for Pie Chart
  const langCount = {};
  repos.forEach(r => {
    if (r.language_name) {
      langCount[r.language_name] = (langCount[r.language_name] || 0) + 1;
    }
  });
  const languageData = Object.keys(langCount).map(key => ({
    name: key,
    value: langCount[key]
  })).sort((a,b) => b.value - a.value).slice(0, 5); // Top 5 languages

  // Tooltip custom style
  const customTooltipStyle = {
    backgroundColor: 'rgba(10,10,11,0.9)', 
    border: '1px solid var(--border-color)', 
    borderRadius: '8px',
    color: '#fff'
  };

  return (
    <section className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="flex-row gap-4 mb-6" style={{ justifyContent: 'space-between' }}>
        <div className="flex-row gap-2">
          <User size={24} color="var(--accent-1)" />
          <h1 style={{ marginBottom: 0 }}>Profile Analysis: {username}</h1>
        </div>
        <div>
          {/* Phase 2: Action Button */}
          {profile && (
            <button 
              className="btn-primary" 
              onClick={handleFollow} 
              disabled={actionLoading}
              style={{ fontSize: '0.9rem', padding: '0.6rem 1rem' }}
            >
               {actionLoading ? <div className="spinner" /> : isFollowing ? "Unfollow" : "Follow User"}
            </button>
          )}
        </div>
      </div>

      {loading && <div className="spinner mb-4" aria-label="loading" />}
      {error && (
        <div className="flex-row gap-2 error" style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontWeight: 500 }}>
           <AlertTriangle size={20} /> {error}
        </div>
      )}

      {profile && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
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

          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '1rem' }}>
            <h3 style={{ margin: 0, paddingBottom: '0.8rem', borderBottom: '1px solid var(--border-color)' }}>
              Analytics & Growth Patterns
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
              
              <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px dashed var(--border-color)', borderRadius: '12px', padding: '1rem', height: '220px', display: 'flex', flexDirection: 'column' }}>
                <h4 className="muted mb-2 text-center" style={{ fontSize: '0.9rem' }}>Follower Growth</h4>
                {snapshots.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={snapshots} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={customTooltipStyle} itemStyle={{ color: 'var(--accent-1)' }} />
                      <Line type="monotone" dataKey="followers" stroke="var(--accent-1)" strokeWidth={3} dot={{ r: 4, fill: 'var(--accent-1)' }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <p className="muted" style={{ fontSize: '0.85rem' }}>Insufficient Snapshots</p>
                  </div>
                )}
              </div>

              <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px dashed var(--border-color)', borderRadius: '12px', padding: '1rem', height: '220px', display: 'flex', flexDirection: 'column' }}>
                <h4 className="muted mb-2 text-center" style={{ fontSize: '0.9rem' }}>Repository Growth</h4>
                {snapshots.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={snapshots} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={customTooltipStyle} itemStyle={{ color: 'var(--accent-2)' }} />
                      <Line type="monotone" dataKey="repos" stroke="var(--accent-2)" strokeWidth={3} dot={{ r: 4, fill: 'var(--accent-2)' }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <p className="muted" style={{ fontSize: '0.85rem' }}>Insufficient Snapshots</p>
                  </div>
                )}
              </div>

              <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px dashed var(--border-color)', borderRadius: '12px', padding: '1rem', height: '220px', display: 'flex', flexDirection: 'column' }}>
                <h4 className="muted mb-2 text-center" style={{ fontSize: '0.9rem' }}>Top Languages</h4>
                {languageData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%" style={{ position: 'relative', left: '-15px' }}>
                    <PieChart>
                      <Pie data={languageData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={60} paddingAngle={5}>
                        {languageData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={customTooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <p className="muted" style={{ fontSize: '0.85rem' }}>No Language Data</p>
                  </div>
                )}
              </div>

            </div>
          </div>

        </div>
      )}
    </section>
  );
}
