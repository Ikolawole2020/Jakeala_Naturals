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
        <form className="form" onSubmit={submit}>
          <input required type="email" placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} />
          <input required placeholder="Full name" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
          <input placeholder="Phone" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          <input required placeholder="Address" value={form.address} onChange={(e) => set("address", e.target.value)} />
          <input required placeholder="City" value={form.city} onChange={(e) => set("city", e.target.value)} />
          <input required placeholder="State" value={form.state} onChange={(e) => set("state", e.target.value)} />
          <textarea placeholder="Notes" rows={3} value={form.notes} onChange={(e) => set("notes", e.target.value)} />
          <button className="btn btn-primary" type="submit">Place order · Pay on fulfilment demo</button>
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
