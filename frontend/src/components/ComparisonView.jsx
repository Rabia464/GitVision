import { useState } from "react";
import { Scale, AlertTriangle, ArrowRight, User, Trophy, Users, BookOpen } from "lucide-react";
import client from "../api/client";

export default function ComparisonView() {
  const [user1, setUser1] = useState("");
  const [user2, setUser2] = useState("");
  const [data1, setData1] = useState(null);
  const [data2, setData2] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCompare = async (e) => {
    e.preventDefault();
    const u1 = user1.trim();
    const u2 = user2.trim();
    
    if (!u1 || !u2) {
      setError("Please enter two GitHub usernames to compare.");
      return;
    }
    
    setLoading(true);
    setError("");
    setData1(null);
    setData2(null);
    
    try {
      // Promise.all allows us to fetch both in parallel
      const [res1, res2] = await Promise.all([
        client.get(`/api/github/profile/${encodeURIComponent(u1)}`),
        client.get(`/api/github/profile/${encodeURIComponent(u2)}`)
      ]);
      
      setData1(res1.data);
      setData2(res2.data);
      
    } catch (err) {
      const apiMsg = err?.response?.data?.error;
      setError(apiMsg || "Comparison failed. One or both users might not exist in the database.");
    } finally {
      setLoading(false);
    }
  };

  const calculateScore = (profile) => {
    if (!profile) return 0;
    return (profile.followers * 2) + (profile.total_stars * 3) + (profile.repo_count * 1);
  };

  const score1 = calculateScore(data1);
  const score2 = calculateScore(data2);
  
  const isWinner1 = score1 > score2;
  const isWinner2 = score2 > score1;
  const isTie = score1 === score2 && data1 && data2;

  const renderCard = (profile, score, isWinner) => {
    if (!profile) return null;
    
    return (
      <div className="glass-panel" style={{ 
        position: 'relative', 
        overflow: 'hidden',
        border: isWinner ? '2px solid var(--accent-2)' : '1px solid var(--border-color)',
        boxShadow: isWinner ? '0 0 20px rgba(245, 158, 11, 0.2)' : 'none'
      }}>
        {isWinner && (
          <div style={{ position: 'absolute', top: 0, right: 0, background: 'var(--accent-2)', color: '#000', padding: '0.25rem 1rem', borderBottomLeftRadius: '10px', fontWeight: 'bold', fontSize: '0.85rem' }}>
            <Trophy size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} /> WINNER
          </div>
        )}
        
        <div className="flex-row gap-2 mb-4">
          <User size={24} color={isWinner ? "var(--accent-2)" : "var(--text-muted)"} />
          <h2 style={{ margin: 0 }}>{profile.username}</h2>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', display: 'flex', justifyContent: 'space-between' }}>
            <span className="muted flex-row gap-2"><Users size={16}/> Followers</span>
            <span style={{ fontWeight: 600 }}>{profile.followers}</span>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', display: 'flex', justifyContent: 'space-between' }}>
            <span className="muted flex-row gap-2"><BookOpen size={16}/> Repos</span>
            <span style={{ fontWeight: 600 }}>{profile.repo_count}</span>
          </div>
          
          <div style={{ 
            background: isWinner ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255,255,255,0.05)', 
            padding: '1.25rem', 
            borderRadius: '8px', 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '0.5rem'
          }}>
            <span style={{ color: isWinner ? 'var(--accent-2)' : 'var(--text-main)', fontWeight: 600 }}>Dev Score</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 800, color: isWinner ? 'var(--accent-2)' : 'var(--text-main)' }}>{score}</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <section className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
      <div className="flex-row gap-2 mb-6">
        <Scale size={24} color="var(--accent-1)" />
        <h1 style={{ marginBottom: 0 }}>Head-to-Head Comparison</h1>
      </div>

      <div className="glass-panel mb-8">
        <form onSubmit={handleCompare} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: '1 1 200px' }}>
            <label className="muted" style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Competitor 1</label>
            <input 
              type="text" 
              placeholder="GitHub Username" 
              value={user1} 
              onChange={(e) => setUser1(e.target.value)} 
            />
          </div>
          <div style={{ paddingBottom: '0.6rem', color: 'var(--text-muted)', fontWeight: 'bold' }}>
            VS
          </div>
          <div style={{ flex: '1 1 200px' }}>
            <label className="muted" style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Competitor 2</label>
            <input 
              type="text" 
              placeholder="GitHub Username" 
              value={user2} 
              onChange={(e) => setUser2(e.target.value)} 
            />
          </div>
          
          <button className="btn-primary" type="submit" disabled={loading} style={{ height: '3.1rem', flex: '0 0 auto' }}>
            {loading ? <div className="spinner" /> : <>Compare <ArrowRight size={18} /></>}
          </button>
        </form>
      </div>

      {error && (
        <div className="flex-row gap-2 error" style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontWeight: 500 }}>
           <AlertTriangle size={20} /> {error}
        </div>
      )}

      {(data1 || data2) && (
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          {isTie && <h2 style={{ color: 'var(--success)' }}>It's a Tie!</h2>}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '1.5rem' }}>
        {data1 && renderCard(data1, score1, isWinner1)}
        {data2 && renderCard(data2, score2, isWinner2)}
      </div>
      
    </section>
  );
}
