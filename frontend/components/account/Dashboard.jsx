"use client";

import { useEffect, useState } from "react";
import { myAddresses, myOrders } from "@/lib/api";
import ProfilePanel from "./ProfilePanel";
import SecurityPanel from "./SecurityPanel";
import OrdersPanel from "./OrdersPanel";
import AddressesPanel from "./AddressesPanel";

/**
 * The signed-in customer dashboard.
 *
 * Modelled on the familiar marketplace pattern: a summary of recent activity up
 * top, a tabbed set of panels below. Overview is the default rather than a bare
 * greeting, because a customer who opens their account almost always wants to
 * know where their last order is.
 */
export default function Dashboard({ user, onUserChange, onSignOut }) {
  const [tab, setTab] = useState("overview");
  const [orders, setOrders] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAll() {
    setLoading(true);
    try {
      // Both calls are independent, so they are issued together rather than in
      // sequence - the Overview counts need a number from each.
      const [o, a] = await Promise.all([myOrders(), myAddresses()]);
      setOrders(o || []);
      setAddresses(a || []);
      setError("");
    } catch {
      setError("We could not load your account just now. Please refresh.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  const name = [user.first_name, user.last_name].filter(Boolean).join(" ");
  const initials = (
    (user.first_name || user.email || "?")[0] + (user.last_name || "")[0] || ""
  ).toUpperCase();

  const tabs = [
    ["overview", "Overview"],
    ["orders", `Orders${orders.length ? ` (${orders.length})` : ""}`],
    ["addresses", "Addresses"],
    ["profile", "Profile"],
    ["security", "Security"],
  ];

  const spend = orders
    .filter((o) => o.status === "paid" || o.status === "fulfilled")
    .reduce((sum, o) => sum + Number(o.total || 0), 0);
  const active = orders.filter(
    (o) => o.status === "pending" || o.status === "paid"
  );

  return (
    <div className="wrap page-hero" style={{ paddingBottom: 72 }}>
      <header className="dash-head">
        <div className="dash-avatar" aria-hidden="true">{initials}</div>
        <div>
          <p className="kicker">Your account</p>
          <h1 className="serif" style={{ margin: "2px 0 4px" }}>
            {name ? `Hello, ${name}.` : "Your account"}
          </h1>
          <p className="muted">{user.email}</p>
        </div>
        <div className="dash-head-right">
          {user.email_verified ? (
            <span className="pill pill-ok">Email verified</span>
          ) : (
            <span className="pill pill-warn">Email unverified</span>
          )}
          <button className="btn btn-ghost" onClick={onSignOut}>Sign out</button>
        </div>
      </header>

      {!user.email_verified && (
        <p className="alert admin-ok" style={{ marginTop: 18 }}>
          Your email address is not verified yet. Check your inbox for the
          activation link &mdash; some features need it before they work.
        </p>
      )}

      <div className="dash-stats">
        <div className="stat">
          <span className="stat-n">{orders.length}</span>
          <span className="stat-l">Orders placed</span>
        </div>
        <div className="stat">
          <span className="stat-n">{active.length}</span>
          <span className="stat-l">In progress</span>
        </div>
        <div className="stat">
          <span className="stat-n">₦{spend.toLocaleString("en-NG")}</span>
          <span className="stat-l">Lifetime spend</span>
        </div>
        <div className="stat">
          <span className="stat-n">{addresses.length}</span>
          <span className="stat-l">Saved addresses</span>
        </div>
      </div>

      <nav className="dash-tabs" aria-label="Account sections">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            className={tab === key ? "on" : ""}
            aria-current={tab === key ? "page" : undefined}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </nav>

      {error && <p className="alert error">{error}</p>}
      {loading && <p className="muted">Loading your account…</p>}

      {!loading && tab === "overview" && (
        <Overview
          orders={orders}
          addresses={addresses}
          onOpenOrders={() => setTab("orders")}
          onShop={() => (window.location.href = "/shop")}
        />
      )}
      {!loading && tab === "orders" && <OrdersPanel orders={orders} onChanged={loadAll} />}
      {!loading && tab === "addresses" && (
        <AddressesPanel addresses={addresses} onChanged={loadAll} />
      )}
      {!loading && tab === "profile" && (
        <ProfilePanel user={user} onSaved={onUserChange} />
      )}
      {!loading && tab === "security" && <SecurityPanel user={user} />}
    </div>
  );
}

function Overview({ orders, addresses, onOpenOrders, onShop }) {
  const recent = orders.slice(0, 3);
  const defaultAddress = addresses.find((a) => a.is_default) || addresses[0];

  if (orders.length === 0) {
    return (
      <section className="dash-panel">
        <div className="empty">
          <h2 className="serif">No orders yet</h2>
          <p className="muted">
            When you place an order it will appear here, with its status and a
            link to track delivery.
          </p>
          <button className="btn btn-dark" onClick={onShop}>Browse the shop</button>
        </div>
      </section>
    );
  }

  return (
    <section className="dash-panel">
      <div className="dash-panel-head">
        <h2 className="serif">Recent orders</h2>
        <button className="linkish" onClick={onOpenOrders}>View all orders →</button>
      </div>

      <ul className="order-list">
        {recent.map((o) => (
          <li key={o.id} className="order-row">
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
                {o.city ? ` · ${o.city}` : ""}
              </p>
            </div>
            <div className="order-row-end">
              <StatusPill status={o.status} label={o.status_display} />
              <span className="order-total">
                ₦{Number(o.total).toLocaleString("en-NG")}
              </span>
            </div>
          </li>
        ))}
      </ul>

      {defaultAddress && (
        <p className="muted" style={{ marginTop: 18 }}>
          Delivering to <strong>{defaultAddress.label_display}</strong> &mdash;{" "}
          {defaultAddress.city}, {defaultAddress.state}.
        </p>
      )}
    </section>
  );
}

export function StatusPill({ status, label }) {
  // Tone follows meaning, not the raw value: paid and on-the-way are both
  // positive but should not look identical, and a cancelled order must not be
  // mistaken for a finished one.
  const tone =
    status === "cancelled"
      ? "pill-bad"
      : status === "fulfilled"
      ? "pill-ok"
      : status === "paid"
      ? "pill-info"
      : "pill-warn";
  return <span className={`pill ${tone}`}>{label || status}</span>;
}
