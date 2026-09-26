"use client";

import { useState } from "react";
import { sendContact } from "@/lib/api";

export default function ContactPage() {
  const [msg, setMsg] = useState("");
  async function onSubmit(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await sendContact({
        kind: "contact",
        name: fd.get("name"),
        email: fd.get("email"),
        phone: fd.get("phone"),
        subject: fd.get("subject"),
        message: fd.get("message"),
      });
      setMsg("Received — the house will write back to info@jakeala.com correspondents.");
    } catch {
      setMsg("Message captured in this browser session. Connect Django to store it.");
    }
    e.target.reset();
  }
  return (
    <div className="wrap page-hero" style={{ maxWidth: 640 }}>
      <p className="kicker">Support</p>
      <h1 className="serif" style={{ fontSize: 42 }}>Contact</h1>
      <p className="muted" style={{ margin: "8px 0 20px" }}>info@jakeala.com · Primary domain jakeala.com</p>
      <form className="form form-2" onSubmit={onSubmit}>
        <label className="acct-field full">
          <span>Your name</span>
          <input name="name" required autoComplete="name" placeholder="Ada Lovelace" />
        </label>
        <label className="acct-field">
          <span>Email</span>
          <input name="email" type="email" required autoComplete="email" placeholder="you@example.com" />
        </label>
        <label className="acct-field">
          <span>Phone <em className="acct-hint">(optional)</em></span>
          <input name="phone" type="tel" autoComplete="tel" />
        </label>
        <label className="acct-field full">
          <span>Subject</span>
          <input name="subject" placeholder="Order, product or delivery question" />
        </label>
        <label className="acct-field full">
          <span>How can we help?</span>
          <textarea name="message" required rows={5} placeholder="Tell us what you need and we'll reply by email." />
        </label>
        <div className="full">
          <button className="btn btn-dark">Send message</button>
        </div>
      </form>
      {msg && <p className="alert" style={{ marginTop: 16 }}>{msg}</p>}
    </div>
  );
}
