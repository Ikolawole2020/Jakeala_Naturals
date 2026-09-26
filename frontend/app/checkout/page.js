"use client";

import { useEffect, useState } from "react";
import { checkout, getCart, naira, sessionKey } from "@/lib/api";

export default function CheckoutPage() {
  const [cart, setCart] = useState({ items: [], subtotal: 0 });
  const [done, setDone] = useState(null);
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    phone: "",
    address: "",
    city: "Lagos",
    state: "Lagos",
    country: "Nigeria",
    notes: "",
  });

  useEffect(() => {
    getCart(sessionKey()).then(setCart).catch(() => {});
  }, []);

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit(e) {
    e.preventDefault();
    try {
      const order = await checkout({ ...form, session_key: sessionKey() });
      window.dispatchEvent(new Event("cart:update"));
      setDone(order);
    } catch {
      setDone({ id: "DEMO", total: cart.subtotal, email: form.email });
    }
  }

  if (done) {
    return (
      <div className="wrap page-hero" style={{ maxWidth: 640 }}>
        <p className="kicker">Thank you</p>
        <h1 className="serif" style={{ fontSize: 40 }}>Order received</h1>
        <p className="muted">Reference #{done.id}. A confirmation will go to {done.email}.</p>
        <p style={{ marginTop: 12 }}>Total {naira(done.total)}</p>
      </div>
    );
  }

  return (
    <div className="wrap page-hero grid-2">
      <div>
        <p className="kicker">Checkout</p>
        <h1 className="serif" style={{ fontSize: 40, marginBottom: 16 }}>Secure checkout</h1>
        <form className="form form-2" onSubmit={submit}>
          <label className="acct-field">
            <span>Email</span>
            <input required type="email" autoComplete="email" placeholder="you@example.com" value={form.email} onChange={(e) => set("email", e.target.value)} />
          </label>
          <label className="acct-field">
            <span>Full name</span>
            <input required autoComplete="name" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
          </label>
          <label className="acct-field">
            <span>Phone</span>
            <input type="tel" autoComplete="tel" placeholder="For delivery updates" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          </label>
          <label className="acct-field">
            <span>State</span>
            <input required autoComplete="address-level1" value={form.state} onChange={(e) => set("state", e.target.value)} />
          </label>
          <label className="acct-field full">
            <span>Delivery address</span>
            <input required autoComplete="street-address" placeholder="Street and number" value={form.address} onChange={(e) => set("address", e.target.value)} />
          </label>
          <label className="acct-field">
            <span>City</span>
            <input required autoComplete="address-level2" value={form.city} onChange={(e) => set("city", e.target.value)} />
          </label>
          <label className="acct-field full">
            <span>Notes for us</span>
            <textarea rows={3} placeholder="Landmark, delivery window, anything else we should know" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
          </label>
          <div className="full">
            <button className="btn btn-primary" type="submit">Place order · Pay on fulfilment demo</button>
          </div>
        </form>
      </div>
      <aside className="buybox">
        <h3 className="serif">Basket</h3>
        {(cart.items || []).map((i) => (
          <p key={i.id} style={{ margin: "10px 0" }}>
            {i.product.name} × {i.quantity}
          </p>
        ))}
        <div className="price">Subtotal {naira(cart.subtotal)}</div>
        <p className="muted">Shipping ₦0 over ₦15,000, otherwise ₦2,500.</p>
      </aside>
    </div>
  );
}
