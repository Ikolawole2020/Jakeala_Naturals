import { getArticles, getProducts, results } from "@/lib/api";
import { SITE_URL } from "@/lib/site";

// Regenerate at most hourly so new products/articles appear without a rebuild.
export const revalidate = 3600;

const STATIC_ROUTES = [
  "",
  "/shop",
  "/wellness",
  "/about",
  "/contact",
  "/wholesale",
  "/account",
  "/category/womens-wellness",
  "/category/essential-oils",
  "/category/eye-health",
  "/category/skin-body",
  "/legal/privacy",
  "/legal/terms",
  "/legal/shipping",
  "/legal/accessibility",
];

export default async function sitemap() {
  const now = new Date();
  const entries = STATIC_ROUTES.map((r) => ({
    url: `${SITE_URL}${r}`,
    lastModified: now,
    changeFrequency: r ? "monthly" : "daily",
    priority: r ? 0.7 : 1.0,
  }));

  // Live product pages. If the API is unreachable we still ship the static map.
  try {
    for (const p of results(await getProducts("?page_size=200"))) {
      if (!p?.slug) continue;
      entries.push({
        url: `${SITE_URL}/product/${p.slug}`,
        lastModified: now,
        changeFrequency: "weekly",
        priority: 0.8,
      });
    }
  } catch {
    /* API offline - fall back to the static routes above */
  }

  // Live wellness articles.
  try {
    for (const a of results(await getArticles())) {
      if (!a?.slug) continue;
      entries.push({
        url: `${SITE_URL}/wellness/${a.slug}`,
        lastModified: a.published_at ? new Date(a.published_at) : now,
        changeFrequency: "monthly",
        priority: 0.6,
      });
    }
  } catch {
    /* API offline - fall back to the static routes above */
  }

  const seen = new Set();
  return entries.filter((e) => {
    if (seen.has(e.url)) return false;
    seen.add(e.url);
    return true;
  });
}
