import { siteUrl } from "@/lib/site";

export default function robots() {
  return {
    rules: [
      { userAgent: "*", allow: "/", disallow: ["/admin", "/admin/", "/checkout"] },
    ],
    sitemap: siteUrl("/sitemap.xml"),
  };
}