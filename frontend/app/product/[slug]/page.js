import Link from "next/link";
import { notFound } from "next/navigation";
import ProductGallery from "@/components/ProductGallery";
import AddToCart from "@/components/AddToCart";
import ProductCard from "@/components/ProductCard";
import { FALLBACK_PRODUCTS, getProduct, getRelated, naira, results } from "@/lib/api";

const FALLBACK_DETAIL = {
  "shea-hibiscus-body-butter": {
    id: 1,
    name: "Shea & Hibiscus Body Butter",
    slug: "shea-hibiscus-body-butter",
    short_benefit: "Deep moisture with a petal-soft finish.",
    price: "8500.00",
    compare_at: "9800.00",
    size: "250 ml",
    rating: "4.90",
    review_count: 128,
    is_supplement: false,
    category_slug: "skin-body",
    category_name: "Skin & Body",
    benefits: ["Locks in moisture for 24 hours", "Calms tightness after bathing", "Subtle hibiscus-vanilla scent"],
    ingredients: "Butyrospermum Parkii (Shea) Butter, Cocos Nucifera Oil, Hibiscus Sabdariffa Extract, Tocopherol, Cera Alba, Vanilla Planifolia.",
    directions: "Warm a pearl-size amount between palms. Sweep over damp skin after bathing.",
    who_it_is_for: "Dry, mature and sensitive skin seeking richer moisture.",
    warnings: "For external use only. Patch test on inner arm. Discontinue if irritation occurs.",
    disclaimer: "Cosmetic only — not intended to diagnose, treat, cure or prevent any disease.",
    image: "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=900&q=80",
    gallery: ["https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=900&q=80", "https://images.unsplash.com/photo-1570172616994-4597c4d6433d?w=900&q=80", "https://images.unsplash.com/photo-1617897903246-719242758050?w=900&q=80"],
    faqs: [],
    reviews: [],
  },
};

function ratingStars(r) {
  const n = Math.round(Number(r) || 0);
  return "★".repeat(n) + "☆".repeat(Math.max(0, 5 - n));
}

export async function generateMetadata({ params }) {
  let p = null;
  try {
    p = await getProduct(params.slug);
  } catch {
    p = FALLBACK_DETAIL[params.slug] || null;
  }
  return {
    title: p ? p.name : "Product",
    description: p ? p.short_benefit : undefined,
    alternates: { canonical: `https://jakeala.com/product/${params.slug}` },
    openGraph: p
      ? { title: p.name, description: p.short_benefit, images: [p.image] }
      : undefined,
  };
}

export default async function ProductPage({ params }) {
  const slug = params.slug;
  let p = null;
  let related = [];
  try {
    p = await getProduct(slug);
    related = results(await getRelated(slug)) || [];
  } catch {
    p = FALLBACK_DETAIL[slug] || null;
  }
  if (!p) notFound();
  if (!related.length) {
    related = FALLBACK_PRODUCTS.filter((x) => x.slug !== slug).slice(0, 3);
  }

  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: p.name,
    image: p.gallery && p.gallery.length ? p.gallery : [p.image],
    description: p.short_benefit || p.description,
    sku: p.sku,
    brand: { "@type": "Brand", name: "Jakeala Naturals" },
    aggregateRating: { "@type": "AggregateRating", ratingValue: p.rating, reviewCount: p.review_count },
    offers: {
      "@type": "Offer",
      priceCurrency: "NGN",
      price: p.price,
      itemCondition: "https://schema.org/NewCondition",
      availability: p.in_stock === false ? "https://schema.org/OutOfStock" : "https://schema.org/InStock",
    },
  };

  /* eslint-disable @next/next/no-img-element */
  return (
    <>
      <div className="wrap">
        <nav className="breadcrumb" aria-label="Breadcrumb">
          <Link href="/">Home</Link>
          <span>/</span>
          <Link href={`/category/${p.category_slug || p.category?.slug}`}>
            {p.category_name || p.category?.name}
          </Link>
          <span>/</span>
          <span>{p.name}</span>
        </nav>

        <div className="pdp">
          <ProductGallery images={p.gallery || [p.image]} name={p.name} />

          <aside className="buybox">
            <p className="kicker">{p.category_name || p.category?.name || "Jakeala"}</p>
            <h1>{p.name}</h1>
            <div className="rating-row">
              <span className="stars">{ratingStars(p.rating)}</span>
              <span className="muted">{p.rating} · {p.review_count} reviews</span>
            </div>
            {p.size && <p className="muted">Size: <strong>{p.size}</strong></p>}
            <div className="price price-big">
              <span>{naira(p.price)}</span>
              {p.compare_at && <s>{naira(p.compare_at)}</s>}
            </div>
            <p>{p.short_benefit}</p>

            {Array.isArray(p.benefits) && p.benefits.length > 0 && (
              <ul className="bullets">
                {p.benefits.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            )}

            <AddToCart product={p} />

            {p.is_supplement && (
              <div className="supplement-note">
                <strong>Supplement notice.</strong> This product is a dietary supplement. The statements on this page
                have not been evaluated by the FDA or NAFDAC and are not intended to diagnose, treat, cure or prevent any disease.
              </div>
            )}

            <div className="accordion">
              {p.ingredients && (
                <details>
                  <summary>Ingredients</summary>
                  <p className="muted" style={{ marginTop: 8 }}>{p.ingredients}</p>
                </details>
              )}
              {p.directions && (
                <details>
                  <summary>Directions & dosage</summary>
                  <p className="muted" style={{ marginTop: 8 }}>{p.directions}</p>
                </details>
              )}
              {p.who_it_is_for && (
                <details>
                  <summary>Who it is for</summary>
                  <p className="muted" style={{ marginTop: 8 }}>{p.who_it_is_for}</p>
                </details>
              )}
              {p.warnings && (
                <details>
                  <summary>Warnings & safety</summary>
                  <p className="muted" style={{ marginTop: 8 }}>{p.warnings}</p>
                </details>
              )}
              {p.disclaimer && (
                <details>
                  <summary>Compliance & disclaimer</summary>
                  <p className="muted" style={{ marginTop: 8 }}>{p.disclaimer}</p>
                </details>
              )}
              {Array.isArray(p.faqs) &&
                p.faqs.map((f, i) => (
                  <details key={i}>
                    <summary>{f.q}</summary>
                    <p className="muted" style={{ marginTop: 8 }}>{f.a}</p>
                  </details>
                ))}
            </div>
          </aside>
        </div>
      </div>
<section className="section" style={{ paddingTop: 24 }}>
        <div className="wrap">
          <div className="section-head">
            <p className="kicker">Verified reviews</p>
            <h2>What customers say</h2>
          </div>
          <div className="reviews">
            {(p.reviews || []).map((r) => (
              <div className="review" key={r.id}>
                <div className="rating-row">
                  <span className="stars">{ratingStars(r.rating)}</span>
                  <strong>{r.title}</strong>
                </div>
                <p className="muted">{r.body}</p>
                <p className="muted" style={{ marginTop: 8 }}>
                  — {r.author} · {r.verified ? "Verified buyer" : "Guest"}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 24 }}>
        <div className="wrap">
          <div className="section-head">
            <p className="kicker">Pairs well with</p>
            <h2>Complementary rituals</h2>
          </div>
          <div className="grid-3">
            {related.slice(0, 3).map((r) => (
              <ProductCard key={r.slug || r.id} product={r} />
            ))}
          </div>
        </div>
      </section>

      {/* Sticky mobile add-to-cart */}
      <div className="sticky-cart">
        <div>
          <strong>{p.name}</strong>
          <span className="muted" style={{ display: "block" }}>{naira(p.price)}</span>
        </div>
        <AddToCart product={p} compact />
      </div>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
    </>
  );
}