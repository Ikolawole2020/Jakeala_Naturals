"use client";

import { useState } from "react";
import { getOrders, naira } from "@/lib/api";

export default function AccountPage() {
  const [mode, setMode] = useState("login");
  const [lookupEmail, setLookupEmail] = useState("");
  const [orders, setOrders] = useState(null);
  const [message, setMessage] = useState("");

  async function track() {
    try {
      const res = await getOrders(lookupEmail);
      const list = Array.isArray(res) ? res : res.results || [];
      setOrders(list);
      setMessage(list.length ? `${list.length} order${list.length === 1 ? "" : "s"} found.` : "No orders found for that email yet.");
    } catch {
      setOrders([]);
      setMessage("Could not reach the API. Start the backend to look up orders.");
    }
  }

  return (
    <div className="wrap page-hero" style={{ maxWidth: 480 }}>
      <p className="kicker">Portal</p>
      <h1 className="serif" style={{ fontSize: 40 }}>{mode === "login" ? "Welcome back" : "Create account"}</h1>
      <form className="form" onSubmit={(e) => e.preventDefault()} style={{ marginTop: 16 }}>
        {mode === "register" && <input placeholder="Full name" required />}
        <input type="email" placeholder="Email" required />
        <input type="password" placeholder="Password" required />
        <button className="btn btn-dark">{mode === "login" ? "Sign in" : "Register"}</button>
      </form>
      <button className="btn btn-ghost" style={{ marginTop: 12 }} onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Need an account?" : "Already have an account?"}
      </button>

      <div style={{ borderTop: "1px solid var(--line)", marginTop: 28, paddingTop: 18 }}>
        <p className="kicker">Track orders</p>
        <h2 className="serif" style={{ fontSize: 24, margin: "8px 0 12px" }}>Look up your past orders</h2>
        <form className="form" onSubmit={(e) => { e.preventDefault(); track(); }}>
          <input type="email" required placeholder="Order email" value={lookupEmail} onChange={(e) => setLookupEmail(e.target.value)} />
          <button className="btn btn-primary" type="submit">Find orders</button>
        </form>
        {message && <p className="alert" style={{ marginTop: 12 }}>{message}</p>}
        {orders &&
          orders.map((o) => (
            <div key={o.id} className="review" style={{ marginTop: 12 }}>
              <p className="muted">Order #{o.id} · {o.status} · {o.created_at?.slice(0, 10)}</p>
              <p style={{ fontWeight: 650 }}>Total {naira(o.total)}</p>
              <p className="muted">
                {(o.items || []).map((i) => `${i.product_name} × ${i.quantity}`).join(", ")}
              </p>
            </div>
          ))}
      </div>
    </div>
  );
}
