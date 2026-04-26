import { useEffect, useState } from "react";
import { Database, Star, Code, ExternalLink, AlertTriangle } from "lucide-react";
import client from "../api/client";

export default function RepositoryView({ username }) {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!username) return;
    const run = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await client.get(`/api/github/repositories/${encodeURIComponent(username)}`);
        setRepos(res.data || []);
      } catch (err) {
        setError(err?.response?.data?.error || "Could not load repositories.");
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
        <p className="muted">Please select a username from the Dashboard to load repository data.</p>
      </section>
    );
  }

  return (
    <section className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
      <div className="flex-row gap-2 mb-6">
        <Database size={24} color="var(--accent-2)" />
        <h1 style={{ marginBottom: 0 }}>Repository Data: {username}</h1>
      </div>

      {loading && <div className="spinner mb-4" aria-label="loading" />}
      {error && (
        <div className="flex-row gap-2 error" style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontWeight: 500 }}>
           <AlertTriangle size={20} /> {error}
        </div>
      )}

      <div className="repo-grid">
        {repos.map((repo) => (
          <article className="glass-panel" key={repo.repo_id} style={{ display: 'flex', flexDirection: 'column', padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.8rem', color: 'var(--text-main)' }}>
              {repo.repo_name}
            </h3>
            
            <p className="muted" style={{ fontSize: '0.95rem', flexGrow: 1, marginBottom: '1.5rem', lineHeight: 1.5 }}>
              {repo.description || "No description provided."}
            </p>
            
            <div className="flex-row gap-4" style={{ fontSize: '0.9rem', marginBottom: '1.2rem' }}>
              <div className="flex-row gap-2" style={{ color: 'var(--accent-2)', fontWeight: 600 }}>
                <Star size={16} /> {repo.stars}
              </div>
              <div className="flex-row gap-2 muted">
                <Code size={16} /> {repo.language_name || "Unknown"}
              </div>
            </div>

            {repo.github_url && (
              <a 
                href={repo.github_url} 
                target="_blank" 
                rel="noreferrer"
                className="btn-secondary flex-row gap-2" 
                style={{ justifyContent: 'center', fontSize: '0.9rem', padding: '0.6rem' }}
              >
                Access Source <ExternalLink size={16} />
              </a>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
