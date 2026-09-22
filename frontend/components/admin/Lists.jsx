"use client";

import { useEffect, useState } from "react";
import {
  adminArticles, adminDeleteArticle, adminCreateArticle, adminUpdateArticle,
  adminDeleteMessage, adminDeleteReview, adminDeleteSubscriber,
  adminMessages, adminReviews, adminSubscribers, unwrap,
} from "@/lib/admin";

function Manager({ title, subtitle, loader, remove, confirmMsg, render }) {
  const [list, setList] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setList(unwrap(await loader()));
    } catch (e) {
      setError(e.message || `Failed to load ${String(title).toLowerCase()}.`);
    }
  }
  useEffect(() => { load(); }, []);

  async function del(item) {
    if (!confirm(confirmMsg(item))) return;
    try {
      await remove(item);
      load();
    } catch (e) {
      setError(e.message || "Delete failed.");
    }
  }

  return (
    <div className="admin-panel">
      <div className="admin-panel-head">
        <div>
          <h3>{title} ({list.length})</h3>
          <p className="muted">{subtitle}</p>
        </div>
      </div>
      {error && <p className="alert admin-error">{error}</p>}
      <table className="admin-table">
        <thead>
          <tr><th>Detail</th><th className="a-right">Actions</th></tr>
        </thead>
        <tbody>
          {list.map((item) => (
            <tr key={item.id}>
              <td>{render(item)}</td>
              <td className="a-right">
                <button className="admin-link danger" onClick={() => del(item)}>Delete</button>
              </td>
            </tr>
          ))}
          {list.length === 0 && <tr><td colSpan={2} className="muted">Nothing yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export function Reviews() {
  return (
    <Manager
      title="Reviews"
      subtitle="Moderate or remove customer reviews."
      loader={adminReviews}
      remove={(r) => adminDeleteReview(r.id)}
      confirmMsg={(r) => `Delete review by ${r.author}?`}
      render={(r) => (
        <>
          <strong>{r.title || "Untitled"}</strong> <span className="muted">★ {r.rating} / 5</span>
          <div className="muted">{r.body}</div>
          <div className="muted">— {r.author} on {r.product_name} · verified: {r.verified ? "yes" : "no"}</div>
        </>
      )}
    />
  );
}
export function Articles() {
  const [list, setList] = useState([]);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [error, setError] = useState("");

  async function load() {
    try {
      setList(unwrap(await adminArticles()));
    } catch (e) {
      setError(e.message || "Failed to load articles.");
    }
  }
  useEffect(() => { load(); }, []);

  function set(k, v) { setForm((s) => ({ ...s, [k]: v })); }

  async function save(e) {
    e.preventDefault();
    setError("");
    const payload = {
      title: form.title,
      slug: form.slug,
      excerpt: form.excerpt || "",
      body: form.body || "",
      category_label: form.category_label || "Wellness",
      cover: form.cover || "",
      published: form.published !== false,
    };
    try {
      if (editing && editing.id) await adminUpdateArticle(editing.id, payload);
      else await adminCreateArticle(payload);
      setEditing(null);
      setForm({});
      load();
    } catch (err) {
      setError(err.message || "Save failed.");
    }
  }

  async function remove(a) {
    if (!confirm(`Delete “${a.title}”?`)) return;
    try {
      await adminDeleteArticle(a.id);
      load();
    } catch (err) {
      setError(err.message || "Delete failed.");
    }
  }

  return (
    <div className="admin-panel">
      <div className="admin-panel-head">
        <div>
          <h3>Articles ({list.length})</h3>
          <p className="muted">Wellness journal posts.</p>
        </div>
        <button className="btn btn-dark" onClick={() => { setEditing({}); setForm({}); }}>+ Add article</button>
      </div>
      {error && <p className="alert admin-error">{error}</p>}
      {editing && (
        <div className="admin-card">
          <form className="admin-form" onSubmit={save}>
            <label>Title *<input required value={form.title || ""} onChange={(e) => set("title", e.target.value)} /></label>
            <label>Slug *<input required value={form.slug || ""} onChange={(e) => set("slug", e.target.value)} /></label>
            <label>Category label<input value={form.category_label || ""} onChange={(e) => set("category_label", e.target.value)} /></label>
            <label>Cover URL<input value={form.cover || ""} onChange={(e) => set("cover", e.target.value)} /></label>
            <label>Excerpt<textarea rows={2} value={form.excerpt || ""} onChange={(e) => set("excerpt", e.target.value)} /></label>
            <label>Body<textarea rows={5} value={form.body || ""} onChange={(e) => set("body", e.target.value)} /></label>
            <label className="admin-check"><input type="checkbox" checked={form.published !== false} onChange={(e) => set("published", e.target.checked)} /> Published</label>
            <button className="btn btn-dark" type="submit">{editing.id ? "Save changes" : "Create article"}</button>
          </form>
        </div>
      )}
      <table className="admin-table">
        <thead>
          <tr><th>Title</th><th>Label</th><th className="a-right">Actions</th></tr>
        </thead>
        <tbody>
          {list.map((a) => (
            <tr key={a.id}>
              <td><strong>{a.title}</strong><div className="muted">{a.excerpt}</div></td>
              <td className="muted">{a.category_label}{a.published ? "" : " · draft"}</td>
              <td className="a-right">
                <button className="admin-link" onClick={() => { setEditing(a); setForm(a); }}>Edit</button>
                <button className="admin-link danger" onClick={() => remove(a)}>Delete</button>
              </td>
            </tr>
          ))}
          {list.length === 0 && <tr><td colSpan={3} className="muted">No articles yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export function Subscribers() {
  return (
    <Manager
      title="Newsletter subscribers"
      subtitle="Everyone opted-in to the community list."
      loader={adminSubscribers}
      remove={(s) => adminDeleteSubscriber(s.id)}
      confirmMsg={(s) => `Remove ${s.email} from the list?`}
      render={(s) => (
        <>
          <strong>{s.email}</strong>
          <div className="muted">Signed up {String(s.created_at || "").slice(0, 16).replace("T", " ")}</div>
        </>
      )}
    />
  );
}

export function Messages() {
  return (
    <Manager
      title="Contact & wholesale messages"
      subtitle="Inquiries sent through the contact/wholesale forms."
      loader={adminMessages}
      remove={(m) => adminDeleteMessage(m.id)}
      confirmMsg={(m) => `Delete message from ${m.name}?`}
      render={(m) => (
        <>
          <strong>{m.subject || m.kind}</strong> <span className="muted">({m.kind})</span>
          <div className="muted">{m.message}</div>
          <div className="muted">— {m.name} · {m.email} {m.phone ? `· ${m.phone}` : ""}</div>
        </>
      )}
    />
  );
}
