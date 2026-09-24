const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Origin that serves media. Strips the trailing "/api" so the same value works
// for API calls and for image paths.
const API_ORIGIN = API.replace(/\/api\/?$/, "");

/**
 * Resolve a product or category image to a full URL.
 *
 * Catalogue images may be stored either as an absolute URL (an Unsplash link, a
 * CDN) or as a site-relative path such as `/media/products/cycle-reset-tea.jpg`.
 * Relative paths are served by the Django backend, so they are prefixed with the
 * API origin here. Storing relative paths keeps one catalogue row working on
 * localhost and in production without hardcoding a domain.
 */
export function imageUrl(src) {
  if (!src) return "";
  if (/^(https?:)?\/\//i.test(src) || src.startsWith("data:")) return src;
  return `${API_ORIGIN}${src.startsWith("/") ? src : `/${src}`}`;
}

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
export const register = (body) => api("/auth/register/", { method: "POST", body: JSON.stringify(body) });
export const login = (body) => api("/auth/login/", { method: "POST", body: JSON.stringify(body) });
export const verifyEmail = (body) => api("/auth/verify-email/", { method: "POST", body: JSON.stringify(body) });
export const requestPasswordReset = (body) => api("/auth/password/reset/", { method: "POST", body: JSON.stringify(body) });
export const confirmPasswordReset = (body) => api("/auth/password/reset/confirm/", { method: "POST", body: JSON.stringify(body) });
export const subscribe = (email) => api("/newsletter/", { method: "POST", body: JSON.stringify({ email }) });
export const sendContact = (body) => api("/contact/", { method: "POST", body: JSON.stringify(body) });

export const FALLBACK_CATEGORIES = [
  { slug: "womens-wellness", name: "Women's Wellness", tagline: "Everyday rituals for feminine balance", image: "/media/products/cycle-reset-tea.jpg" },
  { slug: "feminine-care", name: "Feminine Care", tagline: "Gentle care, made with intention", image: "/media/products/yoni-cleansing-oil.jpg" },
];

export const FALLBACK_PRODUCTS = [
  { slug: "breast-massage-butter", name: "Breast Massage Butter", short_benefit: "Warm, nourishing butter for breast massage rituals.", price: "9500.00", image: "/media/products/breast-massage-butter.jpg", rating: "4.90", review_count: 12, category_slug: "feminine-care", is_featured: true },
  { slug: "cycle-reset-tea", name: "Cycle Reset Tea", short_benefit: "A botanical tea for a more intentional monthly ritual.", price: "8500.00", image: "/media/products/cycle-reset-tea.jpg", rating: "4.90", review_count: 132, category_slug: "womens-wellness", is_featured: true },
  { slug: "lenu-harmony-herbal-tea", name: "Lenu Harmony Herbal Tea", short_benefit: "Gentle harmony for bloating, mood and pampering.", price: "9000.00", image: "/media/products/lenu-harmony-herbal-tea.jpg", rating: "4.85", review_count: 64, category_slug: "womens-wellness", is_featured: true },
  { slug: "teen-comfort-flow", name: "Teen Comfort Flow", short_benefit: "Cool, calm and in control during your cycle.", price: "7500.00", image: "/media/products/teen-comfort-flow.jpg", rating: "4.80", review_count: 45, category_slug: "womens-wellness", is_featured: true },
  { slug: "ease-flow-menorrhagia-tea", name: "Ease Flow Menorrhagia Tea", short_benefit: "A supportive blend for heavy menstrual flow.", price: "9000.00", image: "/media/products/ease-flow.jpg", rating: "4.82", review_count: 38, category_slug: "womens-wellness", is_featured: true },
  { slug: "yoni-cleansing-oil", name: "Yoni Cleansing Oil", short_benefit: "A gentle botanical oil for daily feminine freshness.", price: "7800.00", image: "/media/products/yoni-cleansing-oil.jpg", rating: "4.85", review_count: 18, category_slug: "feminine-care", is_featured: true },
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
