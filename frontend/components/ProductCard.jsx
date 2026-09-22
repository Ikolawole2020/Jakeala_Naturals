import Link from "next/link";
import { naira } from "@/lib/api";

export default function ProductCard({ product }) {
  return (
    <article className="product-card">
      <Link href={`/product/${product.slug}`}>
        <div className="thumb">
          <img src={product.image} alt={product.name} />
        </div>
        <div className="body">
          <p className="kicker" style={{ fontSize: 11 }}>
            {product.category_name || product.category_slug || "Jakeala"}
          </p>
          <h3>{product.name}</h3>
          <p className="muted">{product.short_benefit}</p>
          <div className="price">
            <span>{naira(product.price)}</span>
            {product.compare_at && <s>{naira(product.compare_at)}</s>}
          </div>
          <span className="muted">★ {product.rating} · {product.review_count} reviews</span>
        </div>
      </Link>
    </article>
  );
}
