"use client";

import { useEffect, useState } from "react";
import { adminCategories, adminDeleteProduct, adminProducts, unwrap } from "@/lib/admin";
import { naira } from "@/lib/api";
import ProductForm from "./ProductForm";

function fmt(v) {
  return v === null || v === undefined || v === "" ? "—" : v;
}

export default function Products() {
  const [list, setList] = useState([]);
  const [cats, setCats] = useState([]);
  const [editing, setEditing] = useState(null); // null = closed, {} = new, obj = edit
  const [error, setError] = useState("");

  async function load() {
    try {
      setList(unwrap(await adminProducts("?ordering=-id")));
      setCats(unwrap(await adminCategories()));
    } catch (e) {
      setError(e.message || "Failed to load products.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(p) {
    if (!confirm(`Delete “${p.name}”?`)) return;
    await adminDeleteProduct(p.id);
    load();
  }

  return (
    <div className="admin-panel">
      <div className="admin-panel-head">
        <div>
          <h3>Products ({list.length})</h3>
          <p className="muted">Add, edit and remove catalog items.</p>
        </div>
        <button className="btn btn-dark" onClick={() => setEditing({})}>+ Add product</button>
      </div>

      {error && <p className="alert admin-error">{error}</p>}

      {editing && (
        <div className="admin-card">
          <h4>{editing.id ? `Edit: ${editing.name}` : "New product"}</h4>
          <ProductForm
            categories={cats}
            editing={editing.id ? editing : null}
            initial={editing.id ? editing : {}}
            onDone={() => { setEditing(null); load(); }}
          />
        </div>
      )}

      <table className="admin-table">
        <thead>
          <tr>
            <th>Name</th><th>Category</th><th>Price</th><th>SKU</th><th>Stock</th><th>Flags</th><th className="a-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {list.map((p) => (
            <tr key={p.id}>
              <td><strong>{p.name}</strong><div className="muted">{p.slug}</div></td>
              <td>{p.category_name || fmt(p.category)}</td>
              <td>{naira(p.price)}</td>
              <td>{p.sku}</td>
              <td>{p.in_stock ? "In stock" : "Out"}</td>
              <td className="muted">{p.is_featured ? "Featured " : ""}{p.is_supplement ? "· Suppl." : ""}</td>
              <td className="a-right">
                <button className="admin-link" onClick={() => setEditing(p)}>Edit</button>
                <button className="admin-link danger" onClick={() => remove(p)}>Delete</button>
              </td>
            </tr>
          ))}
          {list.length === 0 && (
            <tr><td colSpan={7} className="muted">No products yet.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}