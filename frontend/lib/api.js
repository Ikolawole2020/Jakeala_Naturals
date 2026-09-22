const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function sessionKey() {
  if (typeof window === "undefined") return "guest";
  let key = localStorage.getItem("jn_session");
  if (!key) {
    key = "jn_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("jn_session", key);
  }
  return key;
}

export async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const getCategories = () => api("/categories/");
export const getProducts = (qs = "") => api(`/products/${qs}`);
export const getFeatured = () => api("/products/featured/");
export const getProduct = (slug) => api(`/products/${slug}/`);
export const getRelated = (slug) => api(`/products/${slug}/related/`);
export const getArticles = () => api("/articles/");
export const getArticle = (slug) => api("/articles/" + slug + "/");
export const getCart = (session) => api(`/cart/?session=${session}`);
export const addToCart = (body) => api("/cart/add/", { method: "POST", body: JSON.stringify(body) });
export const updateCartItem = (body) => api("/cart/update_item/", { method: "POST", body: JSON.stringify(body) });
export const checkout = (body) => api("/checkout/", { method: "POST", body: JSON.stringify(body) });
export const getOrders = (email) => api(`/orders/?email=${encodeURIComponent(email)}`);
export const subscribe = (email) => api("/newsletter/", { method: "POST", body: JSON.stringify({ email }) });
export const sendContact = (body) => api("/contact/", { method: "POST", body: JSON.stringify(body) });

export const FALLBACK_CATEGORIES = [
  { slug: "womens-wellness", name: "Women's Wellness", tagline: "Everyday rituals for feminine balance", image: "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=900&q=80" },
  { slug: "essential-oils", name: "Essential Oils", tagline: "Botanical aromas, purposeful blends", image: "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=900&q=80" },
  { slug: "eye-health", name: "Eye Health", tagline: "Nourish vision from the inside", image: "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=900&q=80" },
  { slug: "skin-body", name: "Skin & Body", tagline: "Clean textures the skin understands", image: "https://images.unsplash.com/photo-1570172616994-4597c4d6433d?w=900&q=80" },
];

export const FALLBACK_PRODUCTS = [
  { slug: "shea-hibiscus-body-butter", name: "Shea & Hibiscus Body Butter", short_benefit: "Deep moisture with a petal-soft finish.", price: "8500.00", compare_at: "9800.00", size: "250 ml", image: "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=900&q=80", rating: "4.90", review_count: 128, category_slug: "skin-body", is_featured: true },
  { slug: "turmeric-glow-cleansing-bar", name: "Turmeric Glow Cleansing Bar", short_benefit: "Gentle daily cleanse with golden botanicals.", price: "3200.00", image: "https://images.unsplash.com/photo-1617897903246-719242758050?w=900&q=80", rating: "4.70", review_count: 86, category_slug: "skin-body", is_featured: true },
  { slug: "rosehip-restore-face-serum", name: "Rosehip Restore Face Serum", short_benefit: "Lightweight oil serum for texture and glow.", price: "12500.00", image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=900&q=80", rating: "4.85", review_count: 64, category_slug: "skin-body", is_featured: true },
  { slug: "calm-grove-essential-blend", name: "Calm Grove Essential Blend", short_benefit: "Cedar, lavender and sweet orange for evening air.", price: "7800.00", image: "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=900&q=80", rating: "4.80", review_count: 51, category_slug: "essential-oils", is_featured: true },
  { slug: "moon-cycle-comfort-tea", name: "Moon Cycle Comfort Tea", short_benefit: "A warming cup for cramp-heavy days.", price: "6200.00", image: "https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?w=900&q=80", rating: "4.75", review_count: 90, category_slug: "womens-wellness", is_featured: true },
  { slug: "lutein-berry-vision-capsules", name: "Lutein + Berry Vision Capsules", short_benefit: "Daily lutein, zeaxanthin and bilberry.", price: "18900.00", image: "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=900&q=80", rating: "4.65", review_count: 41, category_slug: "eye-health", is_featured: true, is_supplement: true },
];

export function naira(value) {
  const n = Number(value || 0);
  return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(n);
}

export function results(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.results)) return payload.results;
  return [];
}
