import Link from "next/link";
import { imageUrl } from "@/lib/api";

import Newsletter from "@/components/Newsletter";
import ProductCard from "@/components/ProductCard";
import { FALLBACK_CATEGORIES, FALLBACK_PRODUCTS, getCategories, getFeatured, getArticles, results } from "@/lib/api";

async function safe(fn, fallback) {
  try {
    return await fn();
  } catch {
    return fallback;
  }
}

export default async function HomePage() {
  const categories = results(await safe(getCategories, FALLBACK_CATEGORIES)) || FALLBACK_CATEGORIES;
  const featured = results(await safe(getFeatured, FALLBACK_PRODUCTS)) || FALLBACK_PRODUCTS;
  const articles = results(await safe(getArticles, []));

  return (
    <>
      <section className="hero">
        <div className="leaf-orb" />
        <div className="hero-inner">
          <p className="kicker" style={{ color: "#f3c56a" }}>Where every skin is our priority</p>
          <h1>Natural Wellness. Thoughtfully Made.</h1>
          <p>
            Handcrafted herbal care with a modern, inclusive and science-aware spirit — rituals you can actually keep.
          </p>
          <div className="hero-actions">
            <Link href="/shop" className="btn btn-primary">Shop Now</Link>
            <Link href="/wellness" className="btn btn-ghost" style={{ color: "#fff", borderColor: "rgba(255,255,255,.45)" }}>
              Explore Wellness
            </Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head">
            <p className="kicker">Collections</p>
            <h2>Choose the ritual that meets you today</h2>
          </div>
          <div className="grid-4">
            {(categories.length ? categories : FALLBACK_CATEGORIES).map((c) => (
              <Link key={c.slug} href={`/category/${c.slug}`} className="cat-card">
                <img src={imageUrl(c.image)} alt="" />
                <div className="shade">
                  <h3>{c.name}</h3>
                  <span>{c.tagline}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="wrap">
          <div className="promise">
            <div><strong>Clean ingredients</strong><span>Transparent botanical inputs</span></div>
            <div><strong>Thoughtful formulations</strong><span>Purpose before trend</span></div>
            <div><strong>Botanical inspiration</strong><span>Nature, not costume</span></div>
            <div><strong>Made with care</strong><span>Inclusive, everyday rituals</span></div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head">
            <p className="kicker">Featured</p>
            <h2>Formulas with a clear purpose</h2>
          </div>
          <div className="grid-3">
            {(featured.length ? featured : FALLBACK_PRODUCTS).slice(0, 6).map((p) => (
              <ProductCard key={p.slug} product={p} />
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="wrap">
          <div className="section-head">
            <p className="kicker">Learn</p>
            <h2>Wellness, without the noise</h2>
          </div>
          <div className="grid-3">
            {(articles.length ? articles : [
              { slug: "reading-inci-lists", title: "How to read a botanical INCI list", excerpt: "Ingredient order, extracts, and what fragrance can hide.", category_label: "Guides" },
              { slug: "five-minute-evening-ritual", title: "Building a 5-minute evening ritual", excerpt: "Oil, breath, and a warm cloth.", category_label: "Self-Care" },
              { slug: "screen-hours-nutrition", title: "Screen hours and nutritional support", excerpt: "What lutein can and cannot claim.", category_label: "Eye Health" },
            ]).slice(0, 3).map((a) => (
              <Link key={a.slug} href={`/wellness/${a.slug}`} className="product-card" style={{ padding: 22 }}>
                <p className="kicker">{a.category_label}</p>
                <h3 style={{ marginTop: 8 }}>{a.title}</h3>
                <p className="muted">{a.excerpt}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="wrap">
          <div className="trust">
            <div className="trust-item"><b>4.8</b><span className="muted">Average product rating</span></div>
            <div className="trust-item"><b>Secure</b><span className="muted">Encrypted checkout</span></div>
            <div className="trust-item"><b>NG</b><span className="muted">Ships across Nigeria</span></div>
            <div className="trust-item"><b>Clear</b><span className="muted">Full ingredients on every PDP</span></div>
          </div>
        </div>
      </section>

      <Newsletter />
    </>
  );
}
