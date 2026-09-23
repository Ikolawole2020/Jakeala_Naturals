export const metadata = { title: "Our story" };

export default function AboutPage() {
  return (
    <div className="wrap page-hero" style={{ maxWidth: 760, paddingBottom: 72 }}>
      <p className="kicker">Brand story</p>
      <h1 className="serif" style={{ fontSize: 46, margin: "8px 0 18px" }}>The evolution of Jakeala</h1>
      <p>
        Jakeala Naturals brings together the spirit of handcrafted herbal care with a modern approach to natural wellness.
        The brand is rooted in the belief that personal care should feel thoughtful, inclusive and connected to nature.
      </p>
      <p style={{ marginTop: 16 }}>
        We create products designed to support everyday rituals — women&apos;s wellness teas and gentle feminine care, made
        with transparent botanical ingredients.
      </p>
      <p style={{ marginTop: 16 }}>
        Our goal is to make natural wellness easier to understand and easier to incorporate into everyday life. Every product
        should have a clear purpose, transparent ingredients and an experience that makes customers feel cared for.
      </p>
      <p className="muted" style={{ marginTop: 24 }}>
        Where every skin is our priority.
      </p>
    </div>
  );
}
