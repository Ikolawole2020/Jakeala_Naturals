"use client";

export default function Error({ reset }) {
  return (
    <div className="wrap page-hero" style={{ textAlign: "center", maxWidth: 560 }}>
      <h1 className="serif" style={{ fontSize: 40 }}>Something went wrong</h1>
      <p className="muted">We hit a snag. Your basket is safe — you can try again.</p>
      <button className="btn btn-primary" style={{ marginTop: 24 }} onClick={() => reset()}>
        Try again
      </button>
    </div>
  );
}