import { notFound } from "next/navigation";

const DOCS = {
  privacy: {
    title: "Privacy Policy",
    intro: "Jakeala Naturals (jakeala.com) respects your privacy and handles your personal data with care and transparency.",
    sections: [
      ["Information we collect", ["Contact and order details you provide at checkout or sign-up (name, email, address, phone, order history).", "Cart and preference data stored in your browser to keep your basket while you shop.", "If enabled, anonymised analytics to understand how the site is used."]],
      ["How we use it", ["To fulfil and deliver orders, process returns and provide customer support.", "To send the newsletter and wellness guide you explicitly opt into.", "To improve the site through aggregate, non-identifying usage data."]],
      ["Sharing", ["We never sell your personal data. We share only what is needed with payment and delivery partners to complete your order."]],
      ["Storage & security", ["Data is stored on secured systems and transmitted over encrypted connections. We keep order records only as long as legally required."]],
      ["Your rights", ["You may request access to, correction of, or deletion of your personal data by emailing info@jakeala.com."]],
      ["Cookies", ["We use essential cookies for cart and checkout. See our cookie consent banner and the Accessibility statement for options."]],
    ],
  },
  terms: {
    title: "Terms of Service",
    intro: "By using jakeala.com you agree to these terms. Please read them before placing an order.",
    sections: [
      ["Orders & payment", ["All prices are in Nigerian Naira (NGN). We reserve the right to refuse or cancel an order in cases of error or suspected fraud.", "Payment is collected at fulfilment or via the checkout method shown at time of purchase."]],
      ["Shipping & delivery", ["Orders over ₦15,000 ship free within Nigeria; otherwise a flat rate applies. Delivery times depend on your location.", "See the Shipping & Returns page for full details."]],
      ["Returns & refunds", ["Unopened, unused products may be returned within 14 days. Supplements and intimate items are final sale for hygiene reasons."]],
      ["Content & claims", ["Product information is provided in good faith and is not medical advice. Supplements are not intended to diagnose, treat, cure or prevent any disease."]],
      ["Liability", ["We are not liable for misuse of products or for results that vary by individual. Always follow directions and warnings on the product page."]],
      ["Contact", ["Questions about these terms can be sent to info@jakeala.com."]],
    ],
  },
  shipping: {
    title: "Shipping & Returns",
    intro: "Clear, honest shipping and returns so you know exactly what to expect.",
    sections: [
      ["Shipping within Nigeria", ["Orders of ₦15,000 or more ship free. Below that, a flat ₦2,500 delivery fee applies.", "We dispatch within 1–2 business days and share tracking where available."]],
      ["Delivery times", ["Most orders arrive within 3–7 business days depending on your city.", "For wholesale or bulk orders we agree on a delivery schedule with you directly."]],
      ["Returns", ["Unopened, unused items may be returned within 14 days of delivery for a refund to your original payment method.", "Items must be in their original packaging. Return shipping is the customer's responsibility unless the item arrived damaged."]],
      ["Non-returnable items", ["For hygiene and safety, opened cosmetics and dietary supplements are final sale."]],
      ["Damaged or incorrect orders", ["Contact us at info@jakeala.com within 48 hours of delivery with photos and we will make it right."]],
    ],
  },
  accessibility: {
    title: "Accessibility Statement",
    intro: "Jakeala Naturals is committed to a warm, inclusive experience for every visitor, including people using assistive technology.",
    sections: [
      ["Our approach", ["We design mobile-first with high-contrast colours, clear hierarchy and a fast-loading grid."]],
      ["Standards", ["We aim to meet WCAG 2.1 AA: semantic HTML, keyboard-navigable menus, readable text sizes and descriptive labels and alt text."]],
      ["Feedback", ["If something is difficult to use, please tell us at info@jakeala.com — your feedback helps us improve for everyone."]],
      ["Ongoing work", ["Accessibility is a continuous process. We audit key journeys regularly and act on what we learn."]],
    ],
  },
};

export function generateStaticParams() {
  return Object.keys(DOCS).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }) {
  const doc = DOCS[params.slug];
  return {
    title: doc ? `${doc.title} · Jakeala Naturals` : "Legal",
    description: doc ? doc.intro : undefined,
    alternates: { canonical: `https://jakeala.com/legal/${params.slug}` },
  };
}

export default function LegalPage({ params }) {
  const doc = DOCS[params.slug];
  if (!doc) notFound();

  return (
    <div className="wrap page-hero policy" style={{ maxWidth: 760, paddingBottom: 72 }}>
      <p className="kicker">Legal</p>
      <h1 className="serif" style={{ fontSize: 42, margin: "8px 0 14px" }}>{doc.title}</h1>
      <p className="muted">{doc.intro}</p>
      <p className="muted" style={{ marginTop: 8 }}>Last updated: January 2026 · info@jakeala.com</p>
      {doc.sections.map(([heading, points]) => (
        <section key={heading}>
          <h2>{heading}</h2>
          <ul>
            {points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}