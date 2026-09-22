import ProductCard from "@/components/ProductCard";
import { FALLBACK_PRODUCTS, getProducts, results } from "@/lib/api";

export const metadata = { title: "Shop" };

export default async function ShopPage({ searchParams }) {
  const q = searchParams?.q ? `?search=${encodeURIComponent(searchParams.q)}` : "";
  let products = FALLBACK_PRODUCTS;
  try {
    products = results(await getProducts(q));
    if (!products.length && !q) products = FALLBACK_PRODUCTS;
  } catch {
    products = FALLBACK_PRODUCTS.filter((p) =>
      !searchParams?.q || p.name.toLowerCase().includes(String(searchParams.q).toLowerCase())
    );
  }

  return (
    <div className="wrap page-hero">
      <p className="kicker">Catalog</p>
      <h1 className="serif" style={{ fontSize: 42, margin: "8px 0 24px" }}>Shop Jakeala Naturals</h1>
      <div className="grid-3">
        {products.map((p) => (
          <ProductCard key={p.slug} product={p} />
        ))}
      </div>
    </div>
  );
}
