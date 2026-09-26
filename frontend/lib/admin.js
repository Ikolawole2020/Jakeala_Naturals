const ADMIN = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const TOKEN_KEY = "jn_admin_token";

export class AdminUnauthorized extends Error {
  constructor() {
    super("Not authenticated");
    this.name = "AdminUnauthorized";
  }
}

export function adminToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAdminToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAdminToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function unwrap(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return Array.isArray(data.results) ? data.results : [];
}

export function adminApiBase() {
  return `${ADMIN}/admin`;
}

// True when this page is served from a real domain but the API URL is still the
// localhost default - i.e. NEXT_PUBLIC_API_URL was not set at build time.
// Vercel bakes NEXT_PUBLIC_* values in during `next build`, so a missing var
// silently ships a site that calls the visitor's own machine.
export function apiUrlMissingForHost() {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  const pageIsLocal = host === "localhost" || host === "127.0.0.1" || host === "";
  const apiIsLocal = /localhost|127\.0\.0\.1/.test(ADMIN);
  return !pageIsLocal && apiIsLocal;
}

export class AdminMisconfigured extends Error {
  constructor() {
    super(
      "This deployment is not configured with a backend URL, so it is still " +
        "calling localhost (your own computer).\n\n" +
        "Fix it in Vercel:  Project -> Settings -> Environment Variables, add\n" +
        "  NEXT_PUBLIC_API_URL = https://jakealanaturals.pythonanywhere.com/api\n" +
        "then redeploy - NEXT_PUBLIC_* values are baked in at build time, so " +
        "adding the variable alone is not enough."
    );
    this.name = "AdminMisconfigured";
  }
}

export class AdminOffline extends Error {
  constructor(url) {
    super(
      `Can't reach the backend at ${url}. Is the Django server running?\n` +
        `Start it with:  cd backend && python manage.py runserver 8000`
    );
    this.name = "AdminOffline";
    this.url = url;
  }
}

export async function adminApi(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  const t = adminToken();
  if (t) headers.Authorization = `Token ${t}`;
  const url = `${ADMIN}/admin${path}`;
  let res;
  try {
    res = await fetch(url, {
      ...options,
      headers: { ...headers, ...(options.headers || {}) },
    });
  } catch {
    // fetch only rejects on a network/CORS failure, never on a bad password.
    // Distinguish "this build has no API URL" from "the API is unreachable".
    if (apiUrlMissingForHost()) throw new AdminMisconfigured();
    throw new AdminOffline(ADMIN);
  }
  if (res.status === 401 || res.status === 403) throw new AdminUnauthorized();
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      detail = JSON.parse(text).detail || detail;
    } catch {
      /* keep text */
    }
    throw new Error(detail || text || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Auth
export const adminLogin = (body) => adminApi("/login/", { method: "POST", body: JSON.stringify(body) });
export const adminLogout = () => adminApi("/logout/", { method: "POST" });
export const adminMe = () => adminApi("/me/");
export const adminStats = () => adminApi("/stats/");

// Products
export const adminProducts = (qs = "?page_size=200") => adminApi(`/products/${qs}`);
export const adminCreateProduct = (d) => adminApi("/products/", { method: "POST", body: JSON.stringify(d) });
export const adminUpdateProduct = (id, d) => adminApi(`/products/${id}/`, { method: "PATCH", body: JSON.stringify(d) });
export const adminDeleteProduct = (id) => adminApi(`/products/${id}/`, { method: "DELETE" });

// Categories
export const adminCategories = (qs = "?page_size=200") => adminApi(`/categories/${qs}`);
export const adminCreateCategory = (d) => adminApi("/categories/", { method: "POST", body: JSON.stringify(d) });
export const adminUpdateCategory = (id, d) => adminApi(`/categories/${id}/`, { method: "PATCH", body: JSON.stringify(d) });
export const adminDeleteCategory = (id) => adminApi(`/categories/${id}/`, { method: "DELETE" });

// Orders
export const adminOrders = (qs = "?page_size=200") => adminApi(`/orders/${qs}`);
export const adminUpdateOrder = (id, d) => adminApi(`/orders/${id}/`, { method: "PATCH", body: JSON.stringify(d) });

// Reviews
export const adminReviews = (qs = "?page_size=200") => adminApi(`/reviews/${qs}`);
export const adminDeleteReview = (id) => adminApi(`/reviews/${id}/`, { method: "DELETE" });

// Articles
export const adminArticles = (qs = "?page_size=200") => adminApi(`/articles/${qs}`);
export const adminCreateArticle = (d) => adminApi("/articles/", { method: "POST", body: JSON.stringify(d) });
export const adminUpdateArticle = (id, d) => adminApi(`/articles/${id}/`, { method: "PATCH", body: JSON.stringify(d) });
export const adminDeleteArticle = (id) => adminApi(`/articles/${id}/`, { method: "DELETE" });

// Subscribers
export const adminSubscribers = () => adminApi("/subscribers/");
export const adminDeleteSubscriber = (id) => adminApi(`/subscribers/${id}/`, { method: "DELETE" });

// Messages
export const adminMessages = () => adminApi("/messages/");
export const adminDeleteMessage = (id) => adminApi(`/messages/${id}/`, { method: "DELETE" });

// Customers (accounts registered through /account)
export const adminCustomers = (qs = "?page_size=200") => adminApi(`/customers/${qs}`);
export const adminUpdateCustomer = (id, d) =>
  adminApi(`/customers/${id}/`, { method: "PATCH", body: JSON.stringify(d) });
export const adminDeleteCustomer = (id) => adminApi(`/customers/${id}/`, { method: "DELETE" });