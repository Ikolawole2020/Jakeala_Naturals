"use client";

import { useEffect, useState } from "react";
import {
  adminCustomers,
  adminDeleteCustomer,
  adminUpdateCustomer,
  unwrap,
} from "@/lib/admin";

const BLANK = { email: "", first_name: "", last_name: "", phone: "" };

function Badge({ on, children }) {
  return <span className={on ? "badge on" : "badge"}>{children}</span>;
}

export default function Customers() {
  const [list, setList] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(BLANK);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setList(unwrap(await adminCustomers()));
      setError("");
    } catch (e) {
      setError(e.message || "Failed to load customers.");
    }
  }
  useEffect(() => { load(); }, []);

  const shown = list.filter((c) => {
    if (!query.trim()) return true;
    const q = query.trim().toLowerCase();
    return [c.email, c.username, c.first_name, c.last_name]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });

  function startEdit(c) {
    setEditing(c.id);
    setForm({
      email: c.email || "",
      first_name: c.first_name || "",
      last_name: c.last_name || "",
      phone: c.phone || "",
    });
    setPassword("");
    setError("");
    setNotice("");
  }

  async function saveEdit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = { ...form };
      // An empty field is left untouched server-side; only send a password when
      // staff actually typed one, so saving a name never clears the password.
      if (password) payload.password = password;
      await adminUpdateCustomer(editing, payload);
      setEditing(null);
      setNotice("Customer updated.");
      await load();
    } catch (err) {
      setError(err.message || "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function patch(c, body, label) {
    try {
      await adminUpdateCustomer(c.id, body);
      setNotice(`${label} for ${c.email}.`);
      await load();
    } catch (err) {
      setError(err.message || "Update failed.");
    }
  }

  async function remove(c) {
    const extra = c.order_count
      ? `\n\nThis customer has ${c.order_count} order(s). The orders are kept for your records.`
      : "";
    if (!confirm(`Delete the account for ${c.email}? This cannot be undone.${extra}`)) return;
    try {
      await adminDeleteCustomer(c.id);
      setNotice(`Deleted ${c.email}.`);
      await load();
    } catch (err) {
      setError(err.message || "Delete failed.");
    }
  }

  return (
    <div className="admin-panel">
      <div className="admin-panel-head">
        <div>
          <h3>Customer accounts ({shown.length})</h3>
          <p className="muted">
            Everyone who registered at /account. Orders are kept when an account is deleted.
          </p>
        </div>
        <input
          className="input"
          placeholder="Search name or email"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ maxWidth: 260 }}
        />
      </div>

      {error && <p className="alert admin-error">{error}</p>}
      {notice && <p className="alert admin-ok">{notice}</p>}

      <table className="admin-table">
        <thead>
          <tr>
            <th>Customer</th>
            <th>Status</th>
            <th>Orders</th>
            <th>Joined</th>
            <th className="a-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((c) => (
            <tr key={c.id}>
              <td>
                <strong>{c.email || c.username}</strong>
                <div className="muted">
                  {[c.first_name, c.last_name].filter(Boolean).join(" ") || c.username}
                  {c.phone ? ` - ${c.phone}` : ""}
                </div>
                {c.orders && c.orders.length > 0 && (
                  <div className="muted">
                    {c.orders
                      .slice(0, 3)
                      .map((o) => `#${o.id} ${o.status} (${o.total})`)
                      .join("   ")}
                  </div>
                )}
              </td>
              <td>
                <Badge on={c.email_verified}>verified</Badge>{" "}
                <Badge on={c.is_active}>active</Badge>{" "}
                {c.is_staff && <Badge on>staff</Badge>}
              </td>
              <td>{c.order_count}</td>
              <td className="muted">
                {c.date_joined ? new Date(c.date_joined).toLocaleDateString() : "-"}
              </td>
              <td className="a-right">
                <button className="admin-link" onClick={() => startEdit(c)}>Edit</button>{" "}
                <button className="admin-link" onClick={() => patch(c, { is_active: !c.is_active }, c.is_active ? "Disabled" : "Enabled")}>
                  {c.is_active ? "Disable" : "Enable"}
                </button>{" "}
                <button className="admin-link" onClick={() => patch(c, { is_staff: !c.is_staff }, c.is_staff ? "Removed staff access" : "Granted staff access")}>
                  {c.is_staff ? "Unstaff" : "Make staff"}
                </button>{" "}
                <button className="admin-link danger" onClick={() => remove(c)}>Delete</button>
              </td>
            </tr>
          ))}
          {shown.length === 0 && (
            <tr><td colSpan={5} className="muted">No customer accounts yet.</td></tr>
          )}
        </tbody>
      </table>

      {editing && (
        <form className="admin-form" onSubmit={saveEdit}>
          <h4>Edit customer</h4>
          <div className="admin-form-grid">
            <label>
              Email
              <input
                className="input"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </label>
            <label>
              Phone
              <input
                className="input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </label>
            <label>
              First name
              <input
                className="input"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
            </label>
            <label>
              Last name
              <input
                className="input"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </label>
            <label>
              New password (leave blank to keep current)
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />
            </label>
          </div>
          <div className="admin-actions">
            <button className="btn btn-primary" disabled={busy} type="submit">
              {busy ? "Saving..." : "Save changes"}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

