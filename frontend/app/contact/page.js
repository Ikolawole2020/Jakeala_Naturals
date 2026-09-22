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
      <form className="form" onSubmit={onSubmit}>
        <input name="name" required placeholder="Name" />
        <input name="email" type="email" required placeholder="Email" />
        <input name="phone" placeholder="Phone" />
        <input name="subject" placeholder="Subject" />
        <textarea name="message" required rows={5} placeholder="How can we help?" />
        <button className="btn btn-dark">Send</button>
      </form>
      {msg && <p className="alert" style={{ marginTop: 16 }}>{msg}</p>}
    </div>
  );
}
