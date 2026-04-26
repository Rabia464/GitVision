import { Link } from "react-router-dom";
import { GitMerge, Database, Layers, ArrowRight, Activity, Zap } from "lucide-react";

export default function Landing() {
  return (
    <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden' }}>
      {/* Background glow effects */}
      <div style={{
        position: 'absolute', top: '-10%', left: '-10%', width: '50vw', height: '50vw',
        background: 'radial-gradient(circle, rgba(239,68,68,0.08) 0%, rgba(0,0,0,0) 70%)',
        borderRadius: '50%', zIndex: -1, pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute', bottom: '-20%', right: '-10%', width: '60vw', height: '60vw',
        background: 'radial-gradient(circle, rgba(245,158,11,0.06) 0%, rgba(0,0,0,0) 70%)',
        borderRadius: '50%', zIndex: -1, pointerEvents: 'none'
      }} />

      {/* Nav */}
      <nav className="container flex-row" style={{ justifyContent: 'space-between', padding: '2rem 1.5rem', position: 'relative', zIndex: 10 }}>
        <div className="flex-row gap-2" style={{ fontWeight: 700, fontSize: '1.5rem' }}>
          <GitMerge size={32} color="var(--accent-1)" />
          <span>GitVision</span>
        </div>
        <div className="flex-row gap-4">
          <Link to="/login" style={{ color: 'var(--text-muted)', fontWeight: 500 }}>Login</Link>
          <Link to="/register" className="btn-secondary" style={{ padding: '0.5rem 1rem' }}>Sign Up</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="container" style={{ textAlign: 'center', paddingTop: '6rem', position: 'relative', zIndex: 10 }}>
        <div className="animate-fade-in" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '30px', color: 'var(--accent-1)', fontSize: '0.85rem', fontWeight: 600, marginBottom: '2rem' }}>
          <Zap size={16} /> v2.0 Next-Gen Analytics
        </div>
        
        <h1 className="title-large animate-fade-in delay-100">
          Unleash the power of <br/>
          <span className="text-gradient">Developer Intelligence</span>
        </h1>
        
        <p className="subtitle animate-fade-in delay-200" style={{ maxWidth: '600px', margin: '0 auto 3rem auto', lineHeight: 1.6 }}>
          GitVision seamlessly extracts, persists, and analyzes GitHub profiles and repositories into a structured PostgreSQL database for unrivaled insights.
        </p>

        <div className="flex-row gap-4 animate-fade-in delay-300" style={{ justifyContent: 'center', marginBottom: '6rem' }}>
          <Link to="/dashboard" className="btn-primary" style={{ padding: '1rem 2rem', fontSize: '1.1rem' }}>
            Launch Dashboard <ArrowRight size={20} />
          </Link>
          <Link to="/app/profile" className="btn-secondary" style={{ padding: '1rem 2rem', fontSize: '1.1rem' }}>
            Explore Data
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="repo-grid animate-fade-in delay-300" style={{ textAlign: 'left', paddingBottom: '4rem' }}>
          <div className="glass-panel float-anim" style={{ animationDelay: '0s' }}>
            <Database size={32} color="var(--accent-2)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>PostgreSQL Backed</h3>
            <p className="muted">Persist all GitHub data permanently. No more rate limits, just pure instant querying.</p>
          </div>
          
          <div className="glass-panel float-anim" style={{ animationDelay: '2s' }}>
            <Activity size={32} color="var(--accent-1)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>Deep Analytics</h3>
            <p className="muted">Track repository metrics, language dispersion, and follower networks instantly.</p>
          </div>
          
          <div className="glass-panel float-anim" style={{ animationDelay: '4s' }}>
            <Layers size={32} color="#10b981" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>Dynamic Engine</h3>
            <p className="muted">Built with a sleek, modular frontend that adapts to whatever insights you need to view.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
