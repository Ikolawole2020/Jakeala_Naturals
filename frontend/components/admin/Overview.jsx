"use client";

import { useEffect, useState } from "react";
import { adminStats } from "@/lib/admin";
import { naira } from "@/lib/api";

export default function Overview() {
  const [s, setS] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    adminStats()
      .then(setS)
      .catch((e) => setError(e.message || "Failed to load stats."));
  }, []);

  if (!s && !error) return <p className="muted">Loading overview…</p>;

  const cards = [
    ["Products", s?.products, "active"],
    ["Categories", s?.categories, ""],
    ["Orders", s?.orders, "active"],
    ["Pending orders", s?.pending_orders, s?.pending_orders ? "warn" : ""],
    ["Revenue", naira(s?.revenue), "active"],
    ["Subscribers", s?.subscribers, ""],
    ["Messages", s?.messages, ""],
    ["Articles", s?.articles, ""],
  ];

  return (
    <div className="admin-panel">
      <h3>Overview</h3>
      <p className="muted">At-a-glance store health.</p>
      {error && <p className="alert admin-error">{error}</p>}
      <div className="admin-stats">
        {cards.map(([label, value, tone]) => (
          <div key={label} className={`admin-stat ${tone}`}>
            <div className="admin-stat-value">{value === undefined ? "—" : value}</div>
            <div className="muted">{label}</div>
          </div>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 18 }}>
        Use the tabs above to manage products, categories, orders, reviews, articles, subscribers and messages.
      </p>
    </div>
  );
}