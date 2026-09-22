export default function robots() {
  return {
    rules: [{ userAgent: "*", allow: "/" }],
    sitemap: "https://jakeala.com/sitemap.xml",
  };
}