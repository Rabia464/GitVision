import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import client from "../api/client";

export default function Repository() {
  const { username } = useParams();
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
      <section className="card">
        <h1>Repositories</h1>
        <p className="muted">Choose a username from Dashboard import results.</p>
      </section>
    );
  }

  return (
    <main>
      <section className="card">
        <h1>{username} Repositories</h1>
        {loading && <div className="spinner" aria-label="loading" />}
        {error && <p className="error">{error}</p>}
        <div className="repo-grid">
          {repos.map((repo) => (
            <article className="repo-card" key={repo.repo_id}>
              <h3>{repo.repo_name}</h3>
              <p className="muted">{repo.description || "No description provided."}</p>
              <p><strong>Stars:</strong> {repo.stars}</p>
              <p><strong>Language:</strong> {repo.language_name || "Unknown"}</p>
              {repo.github_url && (
                <p>
                  <a href={repo.github_url} target="_blank" rel="noreferrer">
                    Open on GitHub
                  </a>
                </p>
              )}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
