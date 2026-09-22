"use client";

import { useEffect, useState } from "react";
import { adminCategories, adminCreateCategory, adminDeleteCategory, adminUpdateCategory, unwrap } from "@/lib/admin";

export default function Categories() {
  const [list, setList] = useState([]);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({});

  async function load() {
    try {
      setList(unwrap(await adminCategories()));
    } catch (e) {
      setError(e.message || "Failed to load categories.");
    }
  }
  useEffect(() => { load(); }, []);

  function set(k, v) {
    setForm((s) => ({ ...s, [k]: v }));
  }

  async function save(e) {
    e.preventDefault();
    setError("");
    const payload = {
      name: form.name,
      slug: form.slug,
      tagline: form.tagline || "",
      description: form.description || "",
      image: form.image || "",
      sort_order: Number(form.sort_order || 0),
    };
    try {
      if (editing && editing.id) await adminUpdateCategory(editing.id, payload);
      else await adminCreateCategory(payload);
      setEditing(null);
      setForm({});
      load();
    } catch (err) {
      setError(err.message || "Save failed.");
    }
  }

  async function remove(c) {
    if (!confirm(`Delete category “${c.name}”?`)) return;
    try {
      await adminDeleteCategory(c.id);
      load();
    } catch (err) {
      setError(err.message || "Delete failed (products may reference it).");
    }
  }

  return (
    <div className="admin-panel">
      <div className="admin-panel-head">
        <div>
          <h3>Categories ({list.length})</h3>
          <p className="muted">Navigate the catalog sections.</p>
        </div>
        <button className="btn btn-dark" onClick={() => { setEditing({}); setForm({}); }}>+ Add category</button>
      </div>

      {error && <p className="alert admin-error">{error}</p>}

      {editing && (
        <div className="admin-card">
          <form className="admin-form" onSubmit={save}>
            <label>Name *<input required value={form.name || ""} onChange={(e) => set("name", e.target.value)} /></label>
            <label>Slug *<input required value={form.slug || ""} onChange={(e) => set("slug", e.target.value)} /></label>
            <label>Tagline<input value={form.tagline || ""} onChange={(e) => set("tagline", e.target.value)} /></label>
            <label>Sort order<input value={form.sort_order || 0} onChange={(e) => set("sort_order", e.target.value)} /></label>
            <label>Image URL<input value={form.image || ""} onChange={(e) => set("image", e.target.value)} /></label>
            <label>Description<textarea rows={2} value={form.description || ""} onChange={(e) => set("description", e.target.value)} /></label>
            <button className="btn btn-dark" type="submit">{editing.id ? "Save changes" : "Create category"}</button>
          </form>
        </div>
      )}

      <table className="admin-table">
        <thead>
          <tr><th>Name</th><th>Slug</th><th>Order</th><th>Products</th><th className="a-right">Actions</th></tr>
        </thead>
        <tbody>
          {list.map((c) => (
            <tr key={c.id}>
              <td><strong>{c.name}</strong></td>
              <td className="muted">{c.slug}</td>
              <td>{c.sort_order}</td>
              <td>{c.product_count || 0}</td>
              <td className="a-right">
                <button className="admin-link" onClick={() => { setEditing(c); setForm(c); }}>Edit</button>
                <button className="admin-link danger" onClick={() => remove(c)}>Delete</button>
              </td>
            </tr>
          ))}
          {list.length === 0 && <tr><td colSpan={5} className="muted">No categories yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}