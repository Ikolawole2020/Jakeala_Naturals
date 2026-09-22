"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { adminMe, adminLogout, adminToken, clearAdminToken } from "@/lib/admin";
import Overview from "@/components/admin/Overview";
import Products from "@/components/admin/Products";
import Categories from "@/components/admin/Categories";
import Orders from "@/components/admin/Orders";
import { Reviews, Articles, Subscribers, Messages } from "@/components/admin/Lists";

const TABS = [
  ["overview", "Overview", Overview],
  ["products", "Products", Products],
  ["categories", "Categories", Categories],
  ["orders", "Orders", Orders],
  ["reviews", "Reviews", Reviews],
  ["articles", "Articles", Articles],
  ["subscribers", "Subscribers", Subscribers],
  ["messages", "Messages", Messages],
];

export default function AdminPage() {
  const router = useRouter();
  const [tab, setTab] = useState("overview");
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!adminToken()) {
      router.replace("/admin/login");
      return;
    }
    adminMe()
      .then(setUser)
      .catch(() => {
        clearAdminToken();
        router.replace("/admin/login");
      })
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return <p className="wrap page-hero" style={{ paddingTop: 24 }}>Checking access…</p>;
  }

  async function logout() {
    try {
      await adminLogout();
    } catch {
      /* ignore */
    }
    clearAdminToken();
    router.replace("/admin/login");
  }

  const Current = TABS.find(([k]) => k === tab)[2];

  return (
    <div className="wrap page-hero" style={{ paddingBottom: 72 }}>
      <div className="admin-bar">
        <div>
          <p className="kicker">Staff dashboard</p>
          <h1 className="serif" style={{ fontSize: 34 }}>Store Admin</h1>
        </div>
        <div className="admin-bar-right">
          {user && <span className="muted">Signed in as {user.username}</span>}
          <Link href="/" className="btn btn-ghost" style={{ padding: "9px 16px" }}>View site</Link>
          <button className="btn btn-primary" style={{ padding: "9px 16px" }} onClick={logout}>Sign out</button>
        </div>
      </div>

      <nav className="admin-tabs" aria-label="Admin">
        {TABS.map(([k, label]) => (
          <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>
            {label}
          </button>
        ))}
      </nav>

      <Current />
    </div>
  );
}