import Link from "next/link";
import { getArticles, results } from "@/lib/api";

export const metadata = { title: "Wellness journal" };

export default async function WellnessPage() {
  let articles = [
    { slug: "reading-inci-lists", title: "How to read a botanical INCI list", excerpt: "A calm walkthrough of ingredient order.", category_label: "Guides" },
    { slug: "five-minute-evening-ritual", title: "Building a 5-minute evening ritual", excerpt: "Oil, breath, and a warm cloth.", category_label: "Self-Care" },
    { slug: "screen-hours-nutrition", title: "Screen hours and nutritional support", excerpt: "What lutein and zeaxanthin actually do.", category_label: "Eye Health" },
  ];
  try {
    const remote = results(await getArticles());
    if (remote.length) articles = remote;
  } catch {}

  return (
    <div className="wrap page-hero">
      <p className="kicker">Journal</p>
      <h1 className="serif" style={{ fontSize: 42, marginBottom: 24 }}>Education & self-care</h1>
      <div className="grid-3">
        {articles.map((a) => (
          <Link key={a.slug} href={`/wellness/${a.slug}`} className="product-card" style={{ padding: 22 }}>
            <p className="kicker">{a.category_label}</p>
            <h3 style={{ marginTop: 8 }}>{a.title}</h3>
            <p className="muted">{a.excerpt}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
