import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import client from "../api/client";

export default function Profile() {
  const { username } = useParams();
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
      <section className="card">
        <h1>Profile</h1>
        <p className="muted">Choose a username from Dashboard import results.</p>
      </section>
    );
  }

  return (
    <main>
      <section className="card">
        <h1>Profile</h1>
        {loading && <div className="spinner" aria-label="loading" />}
        {error && <p className="error">{error}</p>}
        {profile && (
          <div className="profile-grid">
            <p><strong>Username:</strong> {profile.username}</p>
            <p><strong>Followers:</strong> {profile.followers}</p>
            <p><strong>Following:</strong> {profile.following}</p>
            <p><strong>Repositories:</strong> {profile.repo_count}</p>
            <p><strong>Total Stars:</strong> {profile.total_stars}</p>
          </div>
        )}
        {profile && (
          <p>
            <Link to={`/repositories/${profile.username}`}>View repositories</Link>
          </p>
        )}
      </section>
    </main>
  );
}
