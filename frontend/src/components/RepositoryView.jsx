import { useEffect, useState } from "react";
import { Database, Star, Code, ExternalLink, AlertTriangle, MessageSquare, Plus, X, Tag, Send, Loader } from "lucide-react";
import client from "../api/client";
import { useAuth, useRequireAuth } from "../context/AuthContext";

function CommentThread({ repoId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState("");
  const { isLoggedIn } = useAuth();
  const requireAuth = useRequireAuth();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await client.get(`/api/repos/${repoId}/comments`);
        setComments(res.data || []);
      } catch {
        setError("Could not load comments.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [repoId]);

  const handlePost = () => {
    requireAuth(async () => {
      if (!newComment.trim()) return;
      setPosting(true);
      try {
        await client.post(`/api/repos/${repoId}/comments`, { content: newComment.trim() });
        const res = await client.get(`/api/repos/${repoId}/comments`);
        setComments(res.data || []);
        setNewComment("");
      } catch {
        setError("Failed to post comment.");
      } finally {
        setPosting(false);
      }
    });
  };

  return (
    <div style={{ borderTop: "1px solid var(--border-color)", marginTop: "1rem", paddingTop: "1rem" }}>
      {loading && <div className="spinner mb-2" />}
      {error && <p className="error" style={{ fontSize: "0.85rem" }}>{error}</p>}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "0.75rem", maxHeight: "150px", overflowY: "auto" }}>
        {comments.length === 0 && !loading && (
          <p className="muted" style={{ fontSize: "0.8rem" }}>No comments yet. Be the first!</p>
        )}
        {comments.map((c) => (
          <div key={c.comment_id} style={{ background: "rgba(0,0,0,0.3)", borderRadius: "6px", padding: "0.5rem 0.75rem", fontSize: "0.85rem" }}>
            <span style={{ color: "var(--accent-2)", fontWeight: 600, marginRight: "0.5rem" }}>@{c.username || "user"}</span>
            <span className="muted">{c.content}</span>
          </div>
        ))}
      </div>
      {/* Always show comment input — requireAuth handles redirect if not logged in */}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <input
          placeholder={isLoggedIn ? "Write a comment..." : "Login to comment..."}
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handlePost()}
          style={{ flexGrow: 1, padding: "0.5rem 0.75rem", fontSize: "0.85rem", cursor: isLoggedIn ? "text" : "pointer" }}
          onClick={!isLoggedIn ? handlePost : undefined}
          readOnly={!isLoggedIn}
        />
        <button className="btn-primary" onClick={handlePost} style={{ padding: "0.5rem 0.75rem" }}>
          {posting ? <Loader size={14} /> : <Send size={14} />}
        </button>
      </div>
    </div>
  );
}

function TagSection({ repoId, initialTags }) {
  const [tags, setTags] = useState(initialTags || []);
  const [newTag, setNewTag] = useState("");
  const [adding, setAdding] = useState(false);
  const [showInput, setShowInput] = useState(false);
  const requireAuth = useRequireAuth();

  const handleAdd = () => {
    requireAuth(async () => {
      if (!newTag.trim()) return;
      setAdding(true);
      try {
        const res = await client.post("/api/tags", { tag_name: newTag.trim() });
        const tagId = res.data?.tag_id;
        if (tagId) {
          await client.post(`/api/repos/${repoId}/tags/${tagId}`);
          setTags((prev) => [...prev, { tag_id: tagId, tag_name: newTag.trim() }]);
        }
        setNewTag("");
        setShowInput(false);
      } catch {
        // silently fail
      } finally {
        setAdding(false);
      }
    });
  };

  return (
    <div className="flex-row gap-2" style={{ flexWrap: "wrap", marginTop: "0.75rem" }}>
      {tags.map((t) => (
        <span key={t.tag_id} style={{
          background: "rgba(245, 158, 11, 0.12)", border: "1px solid rgba(245, 158, 11, 0.3)",
          borderRadius: "20px", padding: "0.2rem 0.7rem", fontSize: "0.8rem", color: "var(--accent-2)"
        }}>
          #{t.tag_name}
        </span>
      ))}
      {!showInput && (
        <button
          onClick={() => { setShowInput(true); }}
          style={{ background: "rgba(255,255,255,0.06)", border: "1px solid var(--border-color)", borderRadius: "20px", padding: "0.2rem 0.6rem", fontSize: "0.8rem", cursor: "pointer", color: "var(--text-muted)" }}>
          <Plus size={12} style={{ display: "inline", marginRight: "2px" }} /> tag
        </button>
      )}
      {showInput && (
        <div className="flex-row gap-2">
          <input value={newTag} onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="tag name..." style={{ width: "100px", padding: "0.2rem 0.6rem", fontSize: "0.8rem" }}
            autoFocus
          />
          <button className="btn-primary" onClick={handleAdd} disabled={adding} style={{ padding: "0.2rem 0.6rem", fontSize: "0.8rem" }}>
            {adding ? <Loader size={12} /> : "Add"}
          </button>
          <button onClick={() => setShowInput(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}>
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

export default function RepositoryView({ username }) {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [starred, setStarred] = useState({});
  const [expandedComments, setExpandedComments] = useState({});
  const requireAuth = useRequireAuth();

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

  const handleStar = (repoId) => {
    requireAuth(async () => {
      try {
        if (starred[repoId]) {
          await client.delete(`/api/repos/${repoId}/star`);
          setStarred((prev) => ({ ...prev, [repoId]: false }));
        } else {
          await client.post(`/api/repos/${repoId}/star`);
          setStarred((prev) => ({ ...prev, [repoId]: true }));
        }
      } catch {
        // silently fail
      }
    });
  };

  const toggleComments = (repoId) => {
    setExpandedComments((prev) => ({ ...prev, [repoId]: !prev[repoId] }));
  };

  if (!username) {
    return (
      <section className="glass-panel text-center">
        <h2 style={{ marginBottom: "1rem" }}>No Target Selected</h2>
        <p className="muted">Please select a username from the Dashboard to load repository data.</p>
      </section>
    );
  }

  return (
    <section className="animate-fade-in" style={{ animationDelay: "0.2s" }}>
      <div className="flex-row gap-2 mb-6">
        <Database size={24} color="var(--accent-2)" />
        <h1 style={{ marginBottom: 0 }}>Repository Data: {username}</h1>
      </div>

      {loading && <div className="spinner mb-4" aria-label="loading" />}
      {error && (
        <div className="flex-row gap-2 error" style={{ background: "rgba(239, 68, 68, 0.1)", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem", fontWeight: 500 }}>
          <AlertTriangle size={20} /> {error}
        </div>
      )}

      <div className="repo-grid">
        {repos.map((repo) => (
          <article className="glass-panel" key={repo.repo_id} style={{ display: "flex", flexDirection: "column", padding: "1.25rem" }}>
            <div className="flex-row gap-2" style={{ justifyContent: "space-between", marginBottom: "0.75rem" }}>
              <h3 style={{ fontSize: "1.1rem", margin: 0, color: "var(--text-main)" }}>{repo.repo_name}</h3>
              {/* Star button — always visible, requireAuth handles redirect */}
              <button
                onClick={() => handleStar(repo.repo_id)}
                title="Star this repo"
                style={{
                  background: starred[repo.repo_id] ? "rgba(245, 158, 11, 0.15)" : "rgba(255,255,255,0.05)",
                  border: starred[repo.repo_id] ? "1px solid rgba(245,158,11,0.4)" : "1px solid var(--border-color)",
                  borderRadius: "8px", padding: "0.35rem 0.6rem",
                  cursor: "pointer", color: "var(--accent-2)", display: "flex", alignItems: "center", gap: "4px",
                  transition: "all 0.2s"
                }}
              >
                <Star size={14} fill={starred[repo.repo_id] ? "var(--accent-2)" : "none"} /> {repo.stars}
              </button>
            </div>

            <p className="muted" style={{ fontSize: "0.9rem", flexGrow: 1, marginBottom: "1rem", lineHeight: 1.5 }}>
              {repo.description || "No description provided."}
            </p>

            <div className="flex-row gap-2 muted mb-2" style={{ fontSize: "0.85rem" }}>
              <Code size={14} /> {repo.language_name || "Unknown"}
            </div>

            <TagSection repoId={repo.repo_id} initialTags={repo.tags || []} />

            <div className="flex-row gap-2" style={{ marginTop: "1rem" }}>
              {repo.github_url && (
                <a href={repo.github_url} target="_blank" rel="noreferrer"
                  className="btn-secondary flex-row gap-2"
                  style={{ justifyContent: "center", fontSize: "0.85rem", padding: "0.5rem 0.75rem", flex: 1, textDecoration: "none" }}>
                  Source <ExternalLink size={14} />
                </a>
              )}
              <button
                onClick={() => toggleComments(repo.repo_id)}
                className="btn-secondary flex-row gap-2"
                style={{ fontSize: "0.85rem", padding: "0.5rem 0.75rem", flex: 1 }}>
                <MessageSquare size={14} /> Comments
              </button>
            </div>

            {expandedComments[repo.repo_id] && <CommentThread repoId={repo.repo_id} />}
          </article>
        ))}
      </div>
    </section>
  );
}
