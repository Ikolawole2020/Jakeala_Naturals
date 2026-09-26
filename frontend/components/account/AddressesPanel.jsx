"use client";

import { useState } from "react";
import { createAddress, deleteAddress, updateAddress } from "@/lib/api";

const BLANK = {
  label: "home",
  full_name: "",
  phone: "",
  line1: "",
  line2: "",
  city: "",
  state: "",
  country: "Nigeria",
};

// Offered as suggestions rather than a closed dropdown, so a customer outside
// this list (or outside Nigeria entirely) is never blocked from ordering.
const STATES = [
  "Lagos", "Abuja", "Kano", "Rivers", "Oyo", "Kaduna", "Enugu", "Anambra",
  "Ibadan", "Port Harcourt", "Benin", "Ilorin", "Maiduguri", "Jos",
  "Abeokuta", "Calabar", "Akure", "Uyo", "Asaba",
];

/**
 * The customer's address book.
 *
 * The same form adds and edits. Exactly one card can be the default - the API
 * enforces that too, but the UI is where a mistake would first be obvious, so it
 * never offers a second "default".
 */
export default function AddressesPanel({ addresses, onChanged }) {
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(BLANK);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function set(name, value) {
    setForm((c) => ({ ...c, [name]: value }));
  }

  function startAdd() {
    setEditing("new");
    setForm(BLANK);
    setError("");
    setNotice("");
  }

  function startEdit(a) {
    setEditing(a.id);
    setForm({
      label: a.label,
      full_name: a.full_name,
      phone: a.phone,
      line1: a.line1,
      line2: a.line2 || "",
      city: a.city,
      state: a.state,
      country: a.country || "Nigeria",
    });
    setError("");
    setNotice("");
  }

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (editing === "new") {
        await createAddress(form);
        setNotice("Address saved.");
      } else {
        await updateAddress(editing, form);
        setNotice("Address updated.");
      }
      setEditing(null);
      onChanged();
    } catch (err) {
      setError(readError(err));
    } finally {
      setBusy(false);
    }
  }

  async function makeDefault(a) {
    setError("");
    try {
      await updateAddress(a.id, { is_default: true });
      onChanged();
    } catch (err) {
      setError(readError(err));
    }
  }

  async function remove(a) {
    if (
      !confirm(
        `Delete the ${a.label_display} address for ${a.full_name}?\n\nPast orders keep their own copy of the address, so they are not affected.`
      )
    ) {
      return;
    }
    setError("");
    try {
      await deleteAddress(a.id);
      setNotice(`Deleted the ${a.label_display} address.`);
      onChanged();
    } catch (err) {
      setError(readError(err));
    }
  }

  return (
    <section className="dash-panel">
      <div className="dash-panel-head">
        <h2 className="serif">Saved addresses</h2>
        {!editing && (
          <button
            className="btn btn-dark"
            style={{ padding: "9px 16px" }}
            onClick={startAdd}
          >
            Add an address
          </button>
        )}
      </div>

      {error && <p className="alert error">{error}</p>}
      {notice && <p className="alert admin-ok">{notice}</p>}

      {addresses.length === 0 && !editing && (
        <div className="empty">
          <h3 className="serif">No saved addresses</h3>
          <p className="muted">
            Save one now and checkout becomes a few taps. You can keep several and
            pick a default.
          </p>
        </div>
      )}

      <div className="addr-grid">
        {addresses.map((a) => (
          <article
            key={a.id}
            className={`addr-card${a.is_default ? " is-default" : ""}`}
          >
            <div className="addr-card-head">
              <span className="addr-label">{a.label_display}</span>
              {a.is_default && <span className="pill pill-ok">Default</span>}
            </div>
            <p className="addr-name">{a.full_name}</p>
            <p className="muted">
              {a.line1}
              <br />
              {a.line2}
              {a.line2 && <br />}
              {a.city}, {a.state}
              <br />
              {a.country}
            </p>
            <p className="muted">{a.phone}</p>
            <div className="acct-actions">
              <button className="linkish" onClick={() => startEdit(a)}>Edit</button>
              {!a.is_default && (
                <button className="linkish" onClick={() => makeDefault(a)}>
                  Make default
                </button>
              )}
              <button className="linkish danger" onClick={() => remove(a)}>
                Delete
              </button>
            </div>
          </article>
        ))}
      </div>

      {editing && (
        <form className="acct-form" onSubmit={save}>
          <h3 className="serif">
            {editing === "new" ? "New address" : "Edit address"}
          </h3>
          <div className="acct-grid">
            <label className="acct-field">
              Label
              <select value={form.label} onChange={(e) => set("label", e.target.value)}>
                <option value="home">Home</option>
                <option value="work">Work</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="acct-field">
              Full name
              <input
                required
                value={form.full_name}
                onChange={(e) => set("full_name", e.target.value)}
              />
            </label>
            <label className="acct-field">
              Phone
              <input
                required
                type="tel"
                value={form.phone}
                onChange={(e) => set("phone", e.target.value)}
              />
            </label>
            <label className="acct-field full">
              Address line 1
              <input
                required
                value={form.line1}
                onChange={(e) => set("line1", e.target.value)}
              />
            </label>
            <label className="acct-field full">
              Address line 2 (optional)
              <input value={form.line2} onChange={(e) => set("line2", e.target.value)} />
            </label>
            <label className="acct-field">
              City
              <input required value={form.city} onChange={(e) => set("city", e.target.value)} />
            </label>
            <label className="acct-field">
              State
              <input
                required
                list="ng-states"
                value={form.state}
                onChange={(e) => set("state", e.target.value)}
              />
            </label>
          </div>
          <datalist id="ng-states">
            {STATES.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
          <div className="acct-actions">
            <button className="btn btn-dark" disabled={busy} type="submit">
              {busy ? "Saving…" : "Save address"}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
        </form>
      )}
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
