"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AdminOffline, adminApiBase, adminLogin, setAdminToken } from "@/lib/admin";

export default function AdminLogin() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await adminLogin({ username, password });
      setAdminToken(res.token);
      router.push("/admin");
    } catch (err) {
      setError(
        err instanceof AdminOffline
          ? `Cannot connect to the backend.\n\n${err.message}`
          : err.message || "Login failed."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="wrap page-hero admin-login" style={{ maxWidth: 420 }}>
      <p className="kicker">Staff only</p>
      <h1 className="serif" style={{ fontSize: 40, margin: "8px 0 14px" }}>Admin sign in</h1>
      <p className="muted" style={{ marginBottom: 18 }}>
        Sign in with a staff account (e.g. the seeded <strong>admin</strong> user).
      </p>
      <form className="form" onSubmit={onSubmit}>
        <input
          autoComplete="username"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          autoComplete="current-password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="btn btn-dark" type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      {error && (
        <p
          className="alert"
          style={{
            marginTop: 14,
            background: "#fdecec",
            color: "#8a1f1f",
            whiteSpace: "pre-line",
            lineHeight: 1.5,
          }}
        >
          {error}
        </p>
      )}
      <p className="muted" style={{ marginTop: 18, fontSize: 13 }}>
        API endpoint: <code>{adminApiBase()}</code>
        <br />
        Backend down? Run <code>python manage.py runserver 8000</code> in the
        <code> backend</code> folder.
      </p>
    </div>
  );
}