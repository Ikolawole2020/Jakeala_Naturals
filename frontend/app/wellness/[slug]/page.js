import Link from "next/link";
import { notFound } from "next/navigation";
import { getArticle } from "@/lib/api";

const FALLBACK_ARTICLES = {
  "reading-inci-lists": {
    title: "How to read a botanical INCI list",
    category_label: "Ingredient Guides",
    excerpt: "A calm walkthrough of ingredient order, extracts and what fragrance can hide.",
    body:
      "The first five ingredients usually make up most of the formula. Look for butters and oils you recognise. Extracts appear lower because they are used in smaller amounts. Jakeala lists every botanical input in plain language on every product page.",
  },
  "five-minute-evening-ritual": {
    title: "Building a 5-minute evening ritual",
    category_label: "Self-Care",
    excerpt: "Oil, breath, and a warm cloth — no 12-step performance required.",
    body:
      "Dim one light. Cleanse. Press a facial oil into damp skin. Sit for four slow breaths. That is enough on a difficult day. Consistency outruns complexity.",
  },
  "screen-hours-nutrition": {
    title: "Screen hours and nutritional support",
    category_label: "Eye Health",
    excerpt: "What lutein and zeaxanthin actually do — and what a supplement cannot claim.",
    body:
      "Macular pigments help filter high-energy visible light. A supplement can contribute to daily intake. It is not a treatment for eye disease. Rest your gaze every 20 minutes and keep check-ups with an optometrist.",
  },
};

export async function generateMetadata({ params }) {
  const fallback = FALLBACK_ARTICLES[params.slug];
  let title = fallback ? fallback.title : "Wellness";
  let desc = fallback ? fallback.excerpt : undefined;
  try {
    const a = await getArticle(params.slug);
    title = a.title;
    desc = a.excerpt;
  } catch { /* use fallback */ }
  return {
    title,
    description: desc,
    alternates: { canonical: `https://jakeala.com/wellness/${params.slug}` },
  };
}

export default async function ArticlePage({ params }) {
  const slug = params.slug;
  let a = FALLBACK_ARTICLES[slug] || null;
  try {
    a = await getArticle(slug);
  } catch { /* use fallback */ }
  if (!a) notFound();

  const schema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: a.title,
    description: a.excerpt,
    articleSection: a.category_label,
    author: { "@type": "Organization", name: "Jakeala Naturals" },
    publisher: { "@type": "Organization", name: "Jakeala Naturals", url: "https://jakeala.com" },
  };

  return (
    <div className="wrap page-hero" style={{ maxWidth: 760, paddingBottom: 72 }}>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/">Home</Link>
        <span>/</span>
        <Link href="/wellness">Wellness journal</Link>
        <span>/</span>
        <span>{a.title}</span>
      </nav>
      <p className="kicker">{a.category_label}</p>
      <h1 className="serif" style={{ fontSize: 42, margin: "8px 0 14px" }}>{a.title}</h1>
      <p className="muted" style={{ fontSize: 17 }}>{a.excerpt}</p>
      {a.cover && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={a.cover} alt="" style={{ borderRadius: 22, marginTop: 22, width: "100%", aspectRatio: "2 / 1", objectFit: "cover" }} />
      )}
      <div className="policy" style={{ marginTop: 28 }}>
        <p>{a.body}</p>
      </div>
      <Link href="/wellness" className="btn btn-ghost" style={{ marginTop: 28 }}>
        Back to the journal
      </Link>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
    </div>
  );
}