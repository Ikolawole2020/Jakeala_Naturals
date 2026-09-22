// Single source of truth for absolute URLs (canonicals, sitemap, robots, JSON-LD).
//
// Point NEXT_PUBLIC_SITE_URL at whatever domain is serving this front end, e.g.
//   local dev  -> http://localhost:3000
//   production -> https://jakeala.com   (or https://jakeala-naturals.vercel.app)
// Falls back to the brand domain so nothing breaks if the var is missing.
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL || "https://jakeala.com"
).replace(/\/+$/, "");

export const SITE_EMAIL = process.env.NEXT_PUBLIC_SITE_EMAIL || "info@jakeala.com";

export const SITE_NAME = "Jakeala Naturals";

/** Build an absolute URL for a site-relative path. `siteUrl("/shop")` */
export function siteUrl(path = "") {
  if (!path) return SITE_URL;
  return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}
