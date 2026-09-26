"use client";

import { useEffect, useState } from "react";
import { api, getOrders, login, naira, register, verifyEmail } from "@/lib/api";

const TOKEN_KEY = "jn_customer_token";

export default function AccountPage() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [user, setUser] = useState(null);
  const [busy, setBusy] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [lookupEmail, setLookupEmail] = useState("");
  const [orders, setOrders] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      api("/auth/me/", { headers: { Authorization: `Token ${token}` } })
        .then(setUser)
        .catch(() => localStorage.removeItem(TOKEN_KEY));
    }

    const params = new URLSearchParams(window.location.search);
    const email = params.get("email");
    const code = params.get("code");
    const purpose = params.get("purpose");
    if (email && code && purpose === "verify") {
      setVerifying(true);
      setMode("login");
      verifyEmail({ email, code })
        .then((data) => {
          saveSession(data);
          setMessage("Email verified. You are now signed in.");
          window.history.replaceState({}, "", "/account");
        })
        .catch((err) => setError(readError(err)))
        .finally(() => setVerifying(false));
    }
  }, []);

  function update(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setError(""); setMessage("");
  }

  function saveSession(data) {
    localStorage.setItem(TOKEN_KEY, data.token);
    setUser(data.user);
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true); setError(""); setMessage("");
    try {
      if (mode === "register") {
        const result = await register(form);
        setMessage(result.email_sent
          ? "Account created. Check your email and click the verification link."
          : "Account created. Email delivery is temporarily unavailable. Please contact support before signing in.");
        setMode("login");
      } else {
        saveSession(await login({ identifier: form.email, password: form.password }));
        setMessage("Welcome back.");
      }
    } catch (err) { setError(readError(err)); }
    finally { setBusy(false); }
  }

  async function track(event) {
    event.preventDefault(); setMessage(""); setOrders(null);
    try {
      const res = await getOrders(lookupEmail);
      const list = Array.isArray(res) ? res : res.results || [];
      setOrders(list);
      setMessage(list.length ? `${list.length} order${list.length === 1 ? "" : "s"} found.` : "No orders found for that email yet.");
    } catch { setError("Could not load orders. Please try again."); }
  }

  if (user) return <div className="wrap page-hero" style={{ maxWidth: 560 }}>
    <p className="kicker">Your account</p><h1 className="serif">Hello, {user.first_name || "there"}.</h1>
    <p className="muted">Signed in as {user.email}</p>
    <p className="alert">{user.email_verified ? "Your email is verified." : "Your email still needs verification."}</p>
    <button className="btn btn-ghost" onClick={() => { localStorage.removeItem(TOKEN_KEY); setUser(null); }}>Sign out</button>
  </div>;

  if (verifying) return <div className="wrap page-hero" style={{ maxWidth: 480 }}>
    <p className="kicker">Portal</p><h1 className="serif">Verifying your email…</h1>
    <p className="muted">Please wait while we confirm your account.</p>
  </div>;

  const title = mode === "login" ? "Welcome back" : "Create account";
  return <div className="wrap page-hero" style={{ maxWidth: 480 }}>
    <p className="kicker">Portal</p><h1 className="serif">{title}</h1>
    <form className="form" onSubmit={submit}>
      {mode === "register" && <input placeholder="Full name" autoComplete="name" required value={form.full_name} onChange={(e) => update("full_name", e.target.value)} />}
      <input type="email" placeholder="Email" autoComplete="email" required value={form.email} onChange={(e) => update("email", e.target.value)} />
      <input type="password" placeholder="Password" autoComplete={mode === "login" ? "current-password" : "new-password"} required value={form.password} onChange={(e) => update("password", e.target.value)} />
      <button className="btn btn-dark" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
    </form>
    {error && <p className="alert error" role="alert">{error}</p>}
    {message && <p className="alert" role="status">{message}</p>}
    <button className="btn btn-ghost" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); setMessage(""); }}>{mode === "login" ? "Need an account?" : "Already have an account?"}</button>
    <div style={{ borderTop: "1px solid var(--line)", marginTop: 28, paddingTop: 18 }}>
      <p className="kicker">Track orders</p><h2 className="serif" style={{ fontSize: 24 }}>Look up your past orders</h2>
      <form className="form" onSubmit={track}><input type="email" required placeholder="Order email" value={lookupEmail} onChange={(e) => setLookupEmail(e.target.value)} /><button className="btn btn-primary">Find orders</button></form>
      {orders && orders.map((o) => <div className="review" key={o.id}><p className="muted">Order #{o.id} · {o.status} · {o.created_at?.slice(0, 10)}</p><p style={{ fontWeight: 650 }}>Total {naira(o.total)}</p><p className="muted">{(o.items || []).map((i) => `${i.product_name} × ${i.quantity}`).join(", ")}</p></div>)}
    </div>
  </div>;
}

function readError(err) {
  try { const body = JSON.parse(err.message); return typeof body === "string" ? body : Object.values(body).flat().join(" "); }
  catch { return "Something went wrong. Please try again."; }
}
