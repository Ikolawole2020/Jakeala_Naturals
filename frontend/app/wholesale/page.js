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
      <form className="form form-2" onSubmit={onSubmit}>
        <label className="acct-field full">
          <span>Business name</span>
          <input name="name" required autoComplete="organization" placeholder="Studio, apothecary or store" />
        </label>
        <label className="acct-field">
          <span>Work email</span>
          <input name="email" type="email" required autoComplete="email" placeholder="you@yourstore.com" />
        </label>
        <label className="acct-field">
          <span>Phone <em className="acct-hint">(optional)</em></span>
          <input name="phone" type="tel" autoComplete="tel" />
        </label>
        <label className="acct-field full">
          <span>Tell us about your business</span>
          <textarea
            name="message"
            required
            rows={5}
            placeholder="Cities you deliver to, estimated monthly volume, and which lines you're interested in."
          />
        </label>
        <div className="full">
          <button className="btn btn-primary">Request a line sheet</button>
        </div>
      </form>
      {msg && <p className="alert" style={{ marginTop: 16 }}>{msg}</p>}
    </div>
  );
}
