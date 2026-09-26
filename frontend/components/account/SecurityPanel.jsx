"use client";

import { useState } from "react";
import { changePassword, setCustomerToken } from "@/lib/api";

/**
 * Password and session security.
 *
 * The backend rotates the token on a successful change, so the new one is stored
 * here immediately - without that the customer would be signed out by their own
 * password change. Every other session is invalidated server-side at the same
 * moment, which is the point of the operation.
 */
export default function SecurityPanel({ user }) {
  const [form, setForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function set(name, value) {
    setForm((c) => ({ ...c, [name]: value }));
    setError("");
    setNotice("");
  }

  async function save(event) {
    event.preventDefault();

    if (form.new_password !== form.confirm_password) {
      setError("The two new passwords do not match.");
      return;
    }

    setBusy(true);
    setError("");
    try {
      const data = await changePassword({
        current_password: form.current_password,
        new_password: form.new_password,
      });
      if (data && data.token) setCustomerToken(data.token);
      setForm({ current_password: "", new_password: "", confirm_password: "" });
      setNotice(
        "Password updated. You've been signed out on every other device for safety."
      );
    } catch (err) {
      setError(readError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="dash-panel">
      <div className="dash-panel-head">
        <h2 className="serif">Security</h2>
      </div>

      {error && <p className="alert error">{error}</p>}
      {notice && <p className="alert admin-ok">{notice}</p>}

      <form className="addr-form" onSubmit={save}>
        <h3 className="serif">Change your password</h3>
        <div className="addr-fields">
          <label>
            Current password
            <input
              required
              type="password"
              autoComplete="current-password"
              value={form.current_password}
              onChange={(e) => set("current_password", e.target.value)}
            />
          </label>
          <label>
            New password
            <input
              required
              type="password"
              autoComplete="new-password"
              value={form.new_password}
              onChange={(e) => set("new_password", e.target.value)}
            />
            <span className="muted field-hint">
              At least 8 characters, and not your email or username.
            </span>
          </label>
          <label>
            Confirm new password
            <input
              required
              type="password"
              autoComplete="new-password"
              value={form.confirm_password}
              onChange={(e) => set("confirm_password", e.target.value)}
            />
          </label>
        </div>
        <div className="addr-actions">
          <button className="btn btn-dark" disabled={busy} type="submit">
            {busy ? "Updating…" : "Update password"}
          </button>
        </div>
      </form>

      <div className="note">
        <h4>Signed in as</h4>
        <p className="muted">
          {user.email}
        </p>
        <p className="muted">
          Forgotten it? Use the reset link on the sign-in page and we will email a
          secure link to set a new one.
        </p>
      </div>
    </section>
  );
}

function readError(err) {
  try {
    const body = JSON.parse(err.message);
    if (typeof body === "string") return body;
    if (body.detail) return body.detail;
    return Object.values(body).flat().join(" ");
  } catch {
    return "Something went wrong. Please try again.";
  }
}
