export default function sitemap() {
  const base = "https://jakeala.com";
  const now = new Date();
  const staticRoutes = [
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
  return staticRoutes.map((r) => ({
    url: `${base}${r}`,
    lastModified: now,
    changeFrequency: r ? "monthly" : "daily",
    priority: r ? 0.7 : 1.0,
  }));
}