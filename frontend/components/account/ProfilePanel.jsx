"use client";

import { useState } from "react";
import { updateMe } from "@/lib/api";

/**
 * Editable profile details.
 *
 * The email address is shown but not editable on purpose: it is the account's
 * identity and the destination of every verification and order message, so
 * changing it needs a verification step of its own rather than a silent edit.
 */
export default function ProfilePanel({ user, onSaved }) {
  const [form, setForm] = useState({
    first_name: user.first_name || "",
    last_name: user.last_name || "",
    phone: user.phone || "",
    marketing_opt_in: Boolean(user.marketing_opt_in),
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
    setBusy(true);
    setError("");
    try {
      const updated = await updateMe(form);
      onSaved(updated);
      setNotice("Your details have been saved.");
    } catch (err) {
      setError(readError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="dash-panel">
      <div className="dash-panel-head">
        <h2 className="serif">Profile details</h2>
      </div>

      {error && <p className="alert error">{error}</p>}
      {notice && <p className="alert admin-ok">{notice}</p>}

      <form className="addr-form" onSubmit={save}>
        <div className="addr-fields">
          <label>
            First name
            <input
              autoComplete="given-name"
              value={form.first_name}
              onChange={(e) => set("first_name", e.target.value)}
            />
          </label>
          <label>
            Last name
            <input
              autoComplete="family-name"
              value={form.last_name}
              onChange={(e) => set("last_name", e.target.value)}
            />
          </label>
          <label>
            Phone
            <input
              type="tel"
              autoComplete="tel"
              placeholder="+234 ..."
              value={form.phone}
              onChange={(e) => set("phone", e.target.value)}
            />
          </label>
          <label>
            Email address
            <input type="email" value={user.email} readOnly disabled />
            <span className="muted field-hint">
              Your email is how we reach you about orders. Contact us if it needs
              to change.
            </span>
          </label>
        </div>

        <label className="check-row">
          <input
            type="checkbox"
            checked={form.marketing_opt_in}
            onChange={(e) => set("marketing_opt_in", e.target.checked)}
          />
          <span>
            Email me about new teas, rituals and occasional offers.
            <span className="muted"> Unsubscribe any time.</span>
          </span>
        </label>

        <div className="addr-actions">
          <button className="btn btn-dark" disabled={busy} type="submit">
            {busy ? "Saving…" : "Save details"}
          </button>
        </div>
      </form>

      <dl className="meta-list">
        <div>
          <dt>Member since</dt>
          <dd>
            {user.date_joined
              ? new Date(user.date_joined).toLocaleDateString("en-NG", {
                  month: "long",
                  year: "numeric",
                })
              : "—"}
          </dd>
        </div>
        <div>
          <dt>Reference</dt>
          <dd className="muted">{user.username}</dd>
        </div>
        <div>
          <dt>Email status</dt>
          <dd>
            {user.email_verified ? "Verified" : "Not yet verified"}
          </dd>
        </div>
      </dl>
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
