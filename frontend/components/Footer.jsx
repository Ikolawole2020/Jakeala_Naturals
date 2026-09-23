import Link from "next/link";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="wrap footer-grid">
        <div>
          <h4 className="serif">Jakeala Naturals</h4>
          <p className="muted" style={{ color: "#c5d6c8", marginTop: 8 }}>
            Where every skin is our priority. Handcrafted herbal care with a modern, science-aware approach to everyday wellness.
          </p>
        </div>
        <div>
          <h4>Shop</h4>
          <Link href="/category/womens-wellness">Women&apos;s Wellness</Link>
          <Link href="/category/feminine-care">Feminine Care</Link>
        </div>
        <div>
          <h4>House</h4>
          <Link href="/about">Brand story</Link>
          <Link href="/wellness">Wellness journal</Link>
          <Link href="/contact">Contact</Link>
          <Link href="/wholesale">Wholesale</Link>
          <Link href="/admin">Staff login</Link>
        </div>
        <div>
          <h4>Care</h4>
          <Link href="/legal/shipping">Shipping & returns</Link>
          <Link href="/legal/privacy">Privacy</Link>
          <Link href="/legal/terms">Terms</Link>
          <Link href="/legal/accessibility">Accessibility</Link>
        </div>
      </div>
      <div className="wrap legal">
        <span>© {new Date().getFullYear()} Jakeala Naturals · jakeala.com</span>
        <span>info@jakeala.com</span>
      </div>
    </footer>
  );
}
