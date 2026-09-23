"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCart, sessionKey } from "@/lib/api";
import CartDrawer from "./CartDrawer";

const NAV = [
  ["/shop", "Shop"],
  ["/category/womens-wellness", "Women"],
  ["/category/feminine-care", "Feminine Care"],
  ["/wellness", "Wellness"],
  ["/about", "Our Story"],
];

function AccountIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4 3.6-6 8-6s8 2 8 6" />
    </svg>
  );
}

function CartIcon({ count }) {
  return (
    <span style={{ position: "relative", display: "grid", placeItems: "center" }}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path d="M6 7h12l1 13H5L6 7z" />
        <path d="M9 7a3 3 0 0 1 6 0" />
      </svg>
      {count > 0 && <span className="cart-count">{count}</span>}
    </span>
  );
}

export default function Header() {
  const [open, setOpen] = useState(false);
  const [menu, setMenu] = useState(false);
  const [count, setCount] = useState(0);
  const [q, setQ] = useState("");
  const router = useRouter();

  useEffect(() => {
    getCart(sessionKey())
      .then((c) => setCount((c.items || []).reduce((s, i) => s + i.quantity, 0)))
      .catch(() => {});
    const onUp = () =>
      getCart(sessionKey())
        .then((c) => setCount((c.items || []).reduce((s, i) => s + i.quantity, 0)))
        .catch(() => {});
    window.addEventListener("cart:update", onUp);
    return () => window.removeEventListener("cart:update", onUp);
  }, []);

  return (
    <>
      <div className="announcement">Free shipping on orders over ₦15,000 · Thoughtful formulations, made with care</div>
      <header className="site-header">
        <div className="wrap nav">
          <Link href="/" className="brand" onClick={() => setMenu(false)}>
            <img src="/logo.png" alt="Jakeala Naturals" />
            <span className="brand-text">
              <strong>Jakeala</strong>
              <span>Naturals</span>
            </span>
          </Link>
          <nav className={`nav-links${menu ? " open" : ""}`} aria-label="Primary">
            {NAV.map(([href, label]) => (
              <Link key={href} href={href} onClick={() => setMenu(false)}>
                {label}
              </Link>
            ))}
          </nav>
          <div className="nav-actions">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                router.push(`/shop?q=${encodeURIComponent(q)}`);
                setMenu(false);
              }}
            >
              <input
                className="search"
                placeholder="Search botanicals…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                aria-label="Search"
              />
            </form>
            <Link href="/account" className="icon-btn" aria-label="Account" title="Account" onClick={() => setMenu(false)}>
              <AccountIcon />
            </Link>
            <button className="icon-btn" onClick={() => setOpen(true)} aria-label="Open cart" title="Cart">
              <CartIcon count={count} />
            </button>
            <button
              className="menu-btn"
              aria-label="Toggle menu"
              aria-expanded={menu}
              onClick={() => setMenu((m) => !m)}
            >
              {menu ? "✕" : "☰"}
            </button>
          </div>
        </div>
        {menu && (
          <nav className="mobile-nav" aria-label="Mobile">
            {NAV.map(([href, label]) => (
              <Link
                key={href}
                href={href}
                className="mobile-nav-link"
                onClick={() => setMenu(false)}
              >
                {label}
              </Link>
            ))}
            <Link href="/shop" className="btn btn-ghost mobile-cta" onClick={() => setMenu(false)}>Shop all</Link>
          </nav>
        )}
      </header>
      {open && <CartDrawer onClose={() => setOpen(false)} />}
    </>
  );
}
