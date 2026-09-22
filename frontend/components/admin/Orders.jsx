"use client";

import { useEffect, useState } from "react";
import { adminOrders, adminUpdateOrder, unwrap } from "@/lib/admin";
import { naira } from "@/lib/api";

const STATUS = ["pending", "paid", "fulfilled", "cancelled"];

export default function Orders() {
  const [list, setList] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      let qs = "?ordering=-id";
      if (filter) qs += `&status=${filter}`;
      setList(unwrap(await adminOrders(qs)));
    } catch (e) {
      setError(e.message || "Failed to load orders.");
    }
  }
  useEffect(() => { load(); }, [filter]);

  async function setStatus(id, status) {
    await adminUpdateOrder(id, { status });
    load();
  }

  return (
    <div className="admin-panel">
      <div className="admin-panel-head">
        <div>
          <h3>Orders ({list.length})</h3>
          <p className="muted">Review, filter and update order status.</p>
        </div>
        <select className="admin-select" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All statuses</option>
          {STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {error && <p className="alert admin-error">{error}</p>}

      <table className="admin-table">
        <thead>
          <tr>
            <th>#</th><th>Customer</th><th>Total</th><th>Status</th><th>Date</th><th className="a-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {list.map((o) => (
            <tr key={o.id} onClick={() => setExpanded(expanded === o.id ? null : o.id)}>
              <td>{o.id}</td>
              <td><strong>{o.full_name}</strong><div className="muted">{o.email}</div></td>
              <td>{naira(o.total)}</td>
              <td>
                <select className="admin-select" defaultValue={o.status} onClick={(e) => e.stopPropagation()} onChange={(e) => setStatus(o.id, e.target.value)}>
                  {STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
              <td className="muted">{String(o.created_at || "").slice(0, 16).replace("T", " ")}</td>
              <td className="a-right"><button className="admin-link" onClick={() => setExpanded(expanded === o.id ? null : o.id)}>{expanded === o.id ? "Hide" : "View"}</button></td>
            </tr>
          ))}
          {list.length === 0 && <tr><td colSpan={6} className="muted">No orders match.</td></tr>}
        </tbody>
      </table>

      {expanded && list.find((o) => o.id === expanded) !== undefined && (
        <div className="admin-card">
          <h4>Order #{expanded} detail</h4>
          {(() => {
            const o = list.find((x) => x.id === expanded);
            return (
              <>
                <p className="muted">
                  {o.full_name} · {o.email} · {o.phone} · {o.address}, {o.city}, {o.state} {o.country}
                </p>
                <p className="muted">Status: <strong>{o.status}</strong> · Subtotal {naira(o.subtotal)} · Shipping {naira(o.shipping)} · <strong>Total {naira(o.total)}</strong></p>
                <ul className="admin-order-items">
                  {(o.items || []).map((i) => (
                    <li key={i.id}>{i.product_name} × {i.quantity} @ {naira(i.unit_price)}{i.subscribe ? " (sub)" : ""}</li>
                  ))}
                </ul>
                <p className="muted">{o.notes || "No notes."}</p>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
}