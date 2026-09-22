"use client";

import { useEffect, useState } from "react";

export default function CookieBanner() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    setShow(!localStorage.getItem("jn_cookie"));
  }, []);
  if (!show) return null;
  return (
    <div style={{ position: "fixed", left: 16, bottom: 16, right: 16, zIndex: 60, maxWidth: 420, background: "#142016", color: "#fff", padding: 16, borderRadius: 16 }}>
      <p style={{ fontSize: 14 }}>We use essential cookies for cart and optional analytics. See the privacy policy.</p>
      <button
        className="btn btn-primary"
        style={{ marginTop: 10 }}
        onClick={() => {
          localStorage.setItem("jn_cookie", "1");
          setShow(false);
        }}
      >
        Accept
      </button>
    </div>
  );
}
