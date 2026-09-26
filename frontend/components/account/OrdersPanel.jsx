"use client";

import { useState } from "react";
import { myOrder } from "@/lib/api";
import { StatusPill } from "./Dashboard";

/**
 * Full order history for the signed-in customer.
 *
 * The list is already scoped to the caller by the API; this only opens a detail
 * view. Each order expands in place rather than navigating away, so a customer
 * checking three orders does not lose their place.
 */
export default function OrdersPanel({ orders }) {
  const [openId, setOpenId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function toggle(order) {
    setError("");
    if (openId === order.id) {
      setOpenId(null);
      setDetail(null);
      return;
    }
    setOpenId(order.id);
    setDetail(null);
    setLoading(true);
    try {
      setDetail(await myOrder(order.id));
    } catch {
      setError("We could not load that order. Please try again.");
      setOpenId(null);
    } finally {
      setLoading(false);
    }
  }

  if (orders.length === 0) {
    return (
      <section className="dash-panel">
        <div className="empty">
          <h2 className="serif">No orders yet</h2>
          <p className="muted">
            Anything you order will be listed here with its status, what was in
            it, and where it is going.
          </p>
          <a className="btn btn-dark" href="/shop">Browse the shop</a>
        </div>
      </section>
    );
  }

  return (
    <section className="dash-panel">
      <div className="dash-panel-head">
        <h2 className="serif">Your orders</h2>
        <span className="muted">{orders.length} total</span>
      </div>

      {error && <p className="alert error">{error}</p>}

      <ul className="order-list">
        {orders.map((o) => (
          <li key={o.id} className="order-block">
            <button
              className="order-row order-row-btn"
              onClick={() => toggle(o)}
              aria-expanded={openId === o.id}
            >
              {o.thumbnail ? <img className="order-thumb" src={o.thumbnail} alt="" /> : null}
              <div className="order-row-main">
                <p className="order-ref">
                  Order #{o.id}
                  {o.reference && <span className="muted"> · {o.reference}</span>}
                </p>
                <p className="muted">
                  {new Date(o.created_at).toLocaleDateString("en-NG", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}
                  {" · "}
                  {o.item_count} item{o.item_count === 1 ? "" : "s"}
                </p>
              </div>
              <div className="order-row-end">
                <StatusPill status={o.status} label={o.status_display} />
                <span className="order-total">
                  ₦{Number(o.total).toLocaleString("en-NG")}
                </span>
                <span className="order-caret">{openId === o.id ? "−" : "+"}</span>
              </div>
            </button>

            {openId === o.id && (
              <div className="order-detail">
                {loading && <p className="muted">Loading order…</p>}
                {detail && <OrderDetail order={detail} />}
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function OrderDetail({ order }) {
  return (
    <>
      <div className="order-detail-grid">
        <div>
          <h4>Delivering to</h4>
          <p>
            {order.full_name}
            <br />
            {order.address}
            <br />
            {order.city}, {order.state}
            <br />
            {order.country}
          </p>
          <p className="muted">{order.phone}</p>
        </div>
        <div>
          <h4>Order details</h4>
          <p className="muted">
            Reference<br />
            <strong>{order.reference || "—"}</strong>
          </p>
          <p className="muted" style={{ marginTop: 8 }}>
            Placed<br />
            <strong>{new Date(order.created_at).toLocaleString("en-NG")}</strong>
          </p>
          {order.paid_at && (
            <p className="muted" style={{ marginTop: 8 }}>
              Paid<br />
              <strong>{new Date(order.paid_at).toLocaleString("en-NG")}</strong>
            </p>
          )}
        </div>
      </div>

      <h4>Items</h4>
      <ul className="line-items">
        {order.items.map((item, i) => (
          <li key={`${item.sku}-${i}`}>
            <span>
              {item.product_name}
              {item.subscribe && <em className="muted"> · subscription</em>}
            </span>
            <span className="muted">
              {item.quantity} × ₦{Number(item.unit_price).toLocaleString("en-NG")}
            </span>
          </li>
        ))}
      </ul>

      {order.notes && (
        <p className="muted" style={{ marginTop: 12 }}>
          <strong>Note:</strong> {order.notes}
        </p>
      )}

      <p className="order-grand">
        <span>Total</span>
        <strong>₦{Number(order.total).toLocaleString("en-NG")}</strong>
      </p>

      <p className="muted" style={{ marginTop: 12 }}>
        Need help with this order? Email info@jakeala.com and quote order #
        {order.id}.
      </p>
    </>
  );
}
