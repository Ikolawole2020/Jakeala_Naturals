import Link from "next/link";
import { notFound } from "next/navigation";
import ProductCard from "@/components/ProductCard";
import { FALLBACK_CATEGORIES, FALLBACK_PRODUCTS, getCategories, getProducts, results } from "@/lib/api";
import { siteUrl } from "@/lib/site";

export async function generateMetadata({ params }) {
  const c = FALLBACK_CATEGORIES.find((x) => x.slug === params.slug);
  if (!c) {
    try {
      const cats = results(await getCategories());
      const found = cats.find((x) => x.slug === params.slug);
      if (found) return { title: found.name, description: found.tagline };
    } catch { /* fallback below */ }
    return { title: "Collection" };
  }
  return {
    title: c.name,
    description: c.tagline,
    alternates: { canonical: siteUrl(`/category/${params.slug}`) },
  };
}

export default async function CategoryPage({ params }) {
  const slug = params.slug;
  let category = FALLBACK_CATEGORIES.find((c) => c.slug === slug) || null;
  let products = FALLBACK_PRODUCTS.filter((p) => p.category_slug === slug);

  try {
    const cats = results(await getCategories());
    if (cats.length) category = cats.find((c) => c.slug === slug) || null;
    if (category) {
      const fresh = results(await getProducts(`?category__slug=${slug}`));
      if (fresh.length) products = fresh;
    }
  } catch { /* rely on fallback */ }

  if (!category) notFound();

  return (
    <div className="wrap page-hero">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/">Home</Link>
        <span>/</span>
        <Link href="/shop">Shop</Link>
        <span>/</span>
        <span>{category.name}</span>
      </nav>
      <p className="kicker">{category.tagline}</p>
      <h1 className="serif" style={{ fontSize: 42, margin: "8px 0 12px" }}>{category.name}</h1>
      {category.description && <p className="muted" style={{ maxWidth: 620 }}>{category.description}</p>}
      <p className="muted" style={{ margin: "12px 0 28px" }}>
        {products.length} {products.length === 1 ? "formula" : "formulas"}
      </p>
      <div className="grid-3">
        {products.map((p) => (
          <ProductCard key={p.slug || p.id} product={p} />
        ))}
      </div>
    </div>
  );
}