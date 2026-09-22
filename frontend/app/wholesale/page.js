"use client";

import { useState } from "react";
import { sendContact } from "@/lib/api";

export default function WholesalePage() {
  const [msg, setMsg] = useState("");
  async function onSubmit(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await sendContact({
        kind: "wholesale",
        name: fd.get("name"),
        email: fd.get("email"),
        phone: fd.get("phone"),
        subject: "Wholesale inquiry",
        message: fd.get("message"),
      });
      setMsg("Inquiry received. A wholesale lead will follow up.");
    } catch {
      setMsg("Inquiry noted. Start the API to persist it.");
    }
  }
  return (
    <div className="wrap page-hero" style={{ maxWidth: 640 }}>
      <p className="kicker">Partners</p>
      <h1 className="serif" style={{ fontSize: 42 }}>Wholesale & retail</h1>
      <p className="muted" style={{ margin: "8px 0 20px" }}>Studios, apothecaries and wellness shelves — write to us with volumes and location.</p>
      <form className="form" onSubmit={onSubmit}>
        <input name="name" required placeholder="Business name / buyer" />
        <input name="email" type="email" required placeholder="Work email" />
        <input name="phone" placeholder="Phone" />
        <textarea name="message" required rows={5} placeholder="Store profile, cities, estimated monthly volume" />
        <button className="btn btn-primary">Request a line sheet</button>
      </form>
      {msg && <p className="alert" style={{ marginTop: 16 }}>{msg}</p>}
    </div>
  );
}
