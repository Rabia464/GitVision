import { useState } from "react";
import { Link } from "react-router-dom";

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
        `Imported ${res.data.imported_username}: ${res.data.repos_upserted} repositories processed into PostgreSQL.`
      );
    } catch (err) {
      const apiMsg = err?.response?.data?.error;
      setError(apiMsg || "Import failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <section className="card">
        <h1>Dashboard</h1>
        <p className="muted">Import a GitHub profile and persist it into GitVision PostgreSQL.</p>
        <form className="import-row" onSubmit={handleImport}>
          <input
            type="text"
            placeholder="Enter GitHub username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Importing..." : "Import Profile"}
          </button>
        </form>
        {loading && <div className="spinner" aria-label="loading" />}
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}
      </section>

      {lastImported && (
        <section className="card">
          <h3>Imported User</h3>
          <div className="link-row">
            <Link to={`/profile/${lastImported}`}>Open Profile</Link>
            <Link to={`/repositories/${lastImported}`}>Open Repositories</Link>
          </div>
        </section>
      )}
    </main>
  );
}
