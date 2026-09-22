"use client";

import { useState } from "react";
import { adminCreateProduct, adminUpdateProduct } from "@/lib/admin";

function toList(v) {
  if (!v) return [];
  return String(v).split(",").map((s) => s.trim()).filter(Boolean);
}

const COLS = { required: "block", marginTop: 6, marginBottom: 2 };

export default function ProductForm({ categories, editing, initial, onDone }) {
  const [f, setF] = useState({
    category: editing ? initial.category : categories[0]?.id,
    name: initial.name || "",
    slug: initial.slug || "",
    short_benefit: initial.short_benefit || "",
    description: initial.description || "",
    price: initial.price || "",
    compare_at: initial.compare_at || "",
    size: initial.size || "",
    sku: initial.sku || "",
    image: initial.image || "",
    gallery: Array.isArray(initial.gallery) ? initial.gallery.join(", ") : initial.gallery || "",
    benefits: Array.isArray(initial.benefits) ? initial.benefits.join(", ") : initial.benefits || "",
    ingredients: initial.ingredients || "",
    directions: initial.directions || "",
    who_it_is_for: initial.who_it_is_for || "",
    warnings: initial.warnings || "",
    disclaimer: initial.disclaimer || "",
    is_featured: !!initial.is_featured,
    is_supplement: !!initial.is_supplement,
    in_stock: initial.in_stock !== false,
    rating: initial.rating || "4.80",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function set(k, v) {
    setF((s) => ({ ...s, [k]: v }));
  }

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const payload = {
      category: Number(f.category),
      name: f.name,
      slug: f.slug,
      short_benefit: f.short_benefit,
      description: f.description,
      price: f.price,
      compare_at: f.compare_at || null,
      size: f.size,
      sku: f.sku,
      image: f.image,
      gallery: toList(f.gallery),
      benefits: toList(f.benefits),
      ingredients: f.ingredients,
      directions: f.directions,
      who_it_is_for: f.who_it_is_for,
      warnings: f.warnings,
      disclaimer: f.disclaimer,
      is_featured: f.is_featured,
      is_supplement: f.is_supplement,
      in_stock: f.in_stock,
      rating: f.rating,
    };
    try {
      if (editing) {
        await adminUpdateProduct(editing.id, payload);
      } else {
        await adminCreateProduct(payload);
      }
      onDone();
    } catch (err) {
      setError(err.message || "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="admin-form" onSubmit={save}>
      <div className="admin-form-grid">
        <label>Name *<input required value={f.name} onChange={(e) => set("name", e.target.value)} /></label>
        <label>Slug *<input required value={f.slug} onChange={(e) => set("slug", e.target.value)} /></label>
        <label>Category *
          <select value={f.category} onChange={(e) => set("category", e.target.value)}>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>
        <label>SKU *<input required value={f.sku} onChange={(e) => set("sku", e.target.value)} /></label>
        <label>Price (NGN) *<input required value={f.price} onChange={(e) => set("price", e.target.value)} /></label>
        <label>Compare-at<input value={f.compare_at} onChange={(e) => set("compare_at", e.target.value)} /></label>
        <label>Size<input value={f.size} onChange={(e) => set("size", e.target.value)} /></label>
        <label>Rating<input value={f.rating} onChange={(e) => set("rating", e.target.value)} /></label>
      </div>
      <label>Short benefit *<input required value={f.short_benefit} onChange={(e) => set("short_benefit", e.target.value)} /></label>
      <label>Description<textarea rows={3} value={f.description} onChange={(e) => set("description", e.target.value)} /></label>
      <label>Image URL *<input required value={f.image} onChange={(e) => set("image", e.target.value)} /></label>
      <label>Gallery URLs (comma-separated)<input value={f.gallery} onChange={(e) => set("gallery", e.target.value)} /></label>
      <label>Benefits (comma-separated)<input value={f.benefits} onChange={(e) => set("benefits", e.target.value)} /></label>
      <label>Ingredients<textarea rows={2} value={f.ingredients} onChange={(e) => set("ingredients", e.target.value)} /></label>
      <label>Directions<textarea rows={2} value={f.directions} onChange={(e) => set("directions", e.target.value)} /></label>
      <label>Who it is for<input value={f.who_it_is_for} onChange={(e) => set("who_it_is_for", e.target.value)} /></label>
      <label>Warnings<textarea rows={2} value={f.warnings} onChange={(e) => set("warnings", e.target.value)} /></label>
      <label>Disclaimer<textarea rows={2} value={f.disclaimer} onChange={(e) => set("disclaimer", e.target.value)} /></label>
      <div className="admin-check-row">
        <label><input type="checkbox" checked={f.is_featured} onChange={(e) => set("is_featured", e.target.checked)} /> Featured</label>
        <label><input type="checkbox" checked={f.is_supplement} onChange={(e) => set("is_supplement", e.target.checked)} /> Supplement</label>
        <label><input type="checkbox" checked={f.in_stock} onChange={(e) => set("in_stock", e.target.checked)} /> In stock</label>
      </div>
      {error && <p className="alert admin-error">{error}</p>}
      <button className="btn btn-dark" type="submit" disabled={busy}>
        {busy ? "Saving…" : editing ? "Save changes" : "Create product"}
      </button>
    </form>
  );
}