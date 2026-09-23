"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCart, imageUrl, naira, sessionKey, updateCartItem } from "@/lib/api";

export default function CartDrawer({ onClose }) {
  const [cart, setCart] = useState({ items: [], subtotal: "0" });

  function load() {
    getCart(sessionKey())
      .then(setCart)
      .catch(() => setCart({ items: [], subtotal: "0" }));
  }

  useEffect(() => {
    load();
  }, []);

  async function changeQty(item, quantity) {
    await updateCartItem({ session: sessionKey(), item_id: item.id, quantity });
    window.dispatchEvent(new Event("cart:update"));
    load();
  }

  return (
    <>
      <div className="overlay" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label="Cart">
        <header style={{ display: "flex", justifyContent: "space-between" }}>
          <strong className="serif">Your basket</strong>
          <button onClick={onClose} style={{ border: 0, background: "none", cursor: "pointer" }}>
            Close
          </button>
        </header>
        <div className="items">
          {(cart.items || []).length === 0 && <p className="muted">Your basket is empty. Begin with a ritual you will actually keep.</p>}
          {(cart.items || []).map((item) => (
            <div className="line" key={item.id}>
              <img src={imageUrl(item.product.image)} alt="" />
              <div>
                <strong>{item.product.name}</strong>
                <p className="muted">{item.subscribe ? "Subscribe & save 10%" : "One-time"}</p>
                <div className="qty">
                  <button onClick={() => changeQty(item, item.quantity - 1)}>-</button>
                  <span>{item.quantity}</span>
                  <button onClick={() => changeQty(item, item.quantity + 1)}>+</button>
                </div>
              </div>
              <div>{naira(item.line_total || item.product.price * item.quantity)}</div>
            </div>
          ))}
        </div>
        <footer>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
            <span>Subtotal</span>
            <strong>{naira(cart.subtotal)}</strong>
          </div>
          <Link href="/checkout" className="btn btn-primary" style={{ width: "100%" }} onClick={onClose}>
            Checkout
          </Link>
        </footer>
      </aside>
    </>
  );
}
