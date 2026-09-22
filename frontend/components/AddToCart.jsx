"use client";

import { useState } from "react";
import { addToCart, naira, sessionKey } from "@/lib/api";

export default function AddToCart({ product, compact }) {
  const [qty, setQty] = useState(1);
  const [sub, setSub] = useState(false);
  const [status, setStatus] = useState("");

  const unit = Number(product.price) * (sub ? 0.9 : 1);
  const total = naira(unit * qty);

  async function add() {
    try {
      await addToCart({
        session: sessionKey(),
        product_id: product.id,
        quantity: qty,
        subscribe: sub,
      });
      if (typeof window !== "undefined") window.dispatchEvent(new Event("cart:update"));
      setStatus("Added to basket ✓");
    } catch {
      setStatus("Could not add right now.");
    }
  }

  return (
    <div className="addbox">
      {!compact && (
        <div className="qty" style={{ justifyContent: "flex-start" }}>
          <span style={{ fontWeight: 600 }}>Qty</span>
          <button type="button" onClick={() => setQty(Math.max(1, qty - 1))}>−</button>
          <span aria-live="polite">{qty}</span>
          <button type="button" onClick={() => setQty(qty + 1)}>+</button>
        </div>
      )}
      <div className="subscribe">
        <button type="button" className={`chip ${!sub ? "on" : ""}`} onClick={() => setSub(false)}>
          One-time
          <br />
          <strong>{naira(product.price)}</strong>
        </button>
        <button type="button" className={`chip ${sub ? "on" : ""}`} onClick={() => setSub(true)}>
          Subscribe & save 10%
          <br />
          <strong>{naira(unit)}</strong>
        </button>
      </div>
      <button className="btn btn-primary" style={{ width: "100%" }} onClick={add}>
        {status || (compact ? `Add · ${total}` : `Add to cart · ${total}`)}
      </button>
    </div>
  );
}