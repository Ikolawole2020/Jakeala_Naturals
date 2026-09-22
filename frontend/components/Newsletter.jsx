"use client";

import { useState } from "react";
import { subscribe } from "@/lib/api";

export default function Newsletter() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    try {
      const res = await subscribe(email);
      setMsg(res.message || "Welcome to the community.");
      setEmail("");
    } catch {
      setMsg("You are on the list — or the API is offline. We’ll still keep a place for you.");
    }
  }

  return (
    <section className="section">
      <div className="wrap">
        <div className="newsletter">
          <div>
            <p className="kicker" style={{ color: "#f3c56a" }}>Community</p>
            <h2 style={{ color: "#fff", margin: "8px 0 10px" }}>Join the Jakeala Naturals community</h2>
            <p style={{ opacity: 0.9 }}>
              A first-order note and a downloadable wellness guide for new members. No noise — just useful ritual ideas.
            </p>
          </div>
          <form onSubmit={onSubmit}>
            <input type="email" required placeholder="you@email.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            <button className="btn btn-primary" type="submit">Join</button>
          </form>
          {msg && <p style={{ gridColumn: "1 / -1" }}>{msg}</p>}
        </div>
      </div>
    </section>
  );
}
