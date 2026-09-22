import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CookieBanner from "@/components/CookieBanner";

export const metadata = {
  title: {
    default: "Jakeala Naturals | Natural Wellness, Thoughtfully Made",
    template: "%s · Jakeala Naturals",
  },
  description:
    "Jakeala Naturals brings handcrafted herbal care together with modern natural wellness — skin and body, women's wellness, essential oils and eye-health supplements.",
  metadataBase: new URL("https://jakeala.com"),
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,480;9..144,600&family=Outfit:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link rel="icon" href="/logo.png" />
      </head>
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
        <CookieBanner />
      </body>
    </html>
  );
}
