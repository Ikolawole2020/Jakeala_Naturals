import Link from "next/link";
import { notFound } from "next/navigation";
import ProductGallery from "@/components/ProductGallery";
import AddToCart from "@/components/AddToCart";
import ProductCard from "@/components/ProductCard";
import { FALLBACK_PRODUCTS, getProduct, getRelated, imageUrl, naira, results } from "@/lib/api";
import { siteUrl } from "@/lib/site";

const FALLBACK_DETAIL = {
  "breast-massage-butter": {
    id: 1,
    name: "Breast Massage Butter",
    slug: "breast-massage-butter",
    short_benefit: "Warm, nourishing butter for breast massage rituals.",
    price: "9500.00",
    compare_at: null,
    size: "100 g",
    rating: "4.90",
    review_count: 12,
    is_supplement: false,
    category_slug: "feminine-care",
    category_name: "Feminine Care",
    benefits: ["Melts on contact for smooth massage glide", "Nourishing butters that absorb without heaviness", "Supports a calm, regular self-massage ritual"],
    ingredients: "Shea Butter, Cocoa Butter, Coconut Oil, Sweet Almond Oil, Vitamin E.",
    directions: "Warm a small amount between palms and massage gently in slow circular motions. Use as part of your regular self-care routine.",
    who_it_is_for: "Women seeking a gentle, intentional breast-care ritual.",
    warnings: "For external use only. Discontinue if irritation occurs.",
    disclaimer: "Cosmetic only — not intended to diagnose, treat, cure or prevent any disease.",
    image: "/media/products/breast-massage-butter.jpg",
    gallery: ["/media/products/breast-massage-butter.jpg", "/media/products/breast-massage-butter-2.jpg", "/media/products/breast-massage-butter-3.jpg", "/media/products/breast-massage-butter-4.jpg"],
    faqs: [],
    reviews: [],
  },
  "cycle-reset-tea": {
    id: 2,
    name: "Cycle Reset Tea",
    slug: "cycle-reset-tea",
    short_benefit: "A botanical tea for a more intentional monthly ritual.",
    price: "8500.00",
    compare_at: null,
    size: "1 tea bag · makes 12 fl oz",
    rating: "4.90",
    review_count: 132,
    is_supplement: false,
    category_slug: "womens-wellness",
    category_name: "Women's Wellness",
    benefits: ["Traditional botanicals for monthly comfort", "Caffeine-free and gentle on the stomach", "A grounding ritual, morning or evening"],
    ingredients: "Organic Cinnamon Bark, Organic Slippery Elm, Organic Lady's Mantle, Chaste Tree Berry Extract.",
    directions: "Steep 1 tea bag in 12 fl oz of freshly boiled water for 5-7 minutes. Enjoy warm, before and during your cycle.",
    who_it_is_for: "Women who want a warm, traditional herbal ritual around their monthly cycle.",
    warnings: "Not intended during pregnancy or breastfeeding without advice from your healthcare provider.",
    disclaimer: "This is a herbal tea, not a medicine. It is not intended to diagnose, treat, cure or prevent any disease.",
    image: "/media/products/cycle-reset-tea.jpg",
    gallery: ["/media/products/cycle-reset-tea.jpg"],
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
    alternates: { canonical: siteUrl(`/product/${params.slug}`) },
    openGraph: p
      ? { title: p.name, description: p.short_benefit, images: [imageUrl(p.image)] }
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
    image: (p.gallery && p.gallery.length ? p.gallery : [p.image]).map((src) => imageUrl(src)),

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