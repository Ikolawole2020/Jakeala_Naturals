import Link from "next/link";

export default function NotFound() {
  return (
    <div className="wrap page-hero" style={{ textAlign: "center", maxWidth: 560 }}>
      <p className="kicker">404</p>
      <h1 className="serif" style={{ fontSize: 44, margin: "8px 0 12px" }}>This leaf blew away</h1>
      <p className="muted">The page you are looking for does not exist or has moved.</p>
      <Link href="/" className="btn btn-primary" style={{ marginTop: 24 }}>
        Back to the garden
      </Link>
    </div>
  );
}