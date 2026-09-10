import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/context/Providers";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { MobileBottomNav } from "@/components/layout/MobileBottomNav";
import { CartDrawer } from "@/components/layout/CartDrawer";
import { LocationModal } from "@/components/layout/LocationModal";

export const metadata: Metadata = {
  title: {
    default: "Cartify | Fresh Groceries & Daily Essentials in 15 Minutes",
    template: "%s | Cartify",
  },
  description:
    "Order farm-fresh organic produce, dairy, bakery breads, cold-pressed juices, and household essentials delivered in 15 minutes with Cartify.",
  keywords: [
    "online grocery",
    "fresh organic produce",
    "15 minute delivery",
    "supermarket online",
    "Cartify",
  ],
  authors: [{ name: "Cartify Inc." }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://cartify.com",
    title: "Cartify - Fresh Groceries in Minutes",
    description:
      "Farm-fresh produce and artisanal pantry goods delivered right to your doorstep.",
    siteName: "Cartify",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col font-sans">
        <Providers>
          <Header />
          <CartDrawer />
          <LocationModal />
          <main className="flex-1 pb-16 md:pb-0">{children}</main>
          <Footer />
          <MobileBottomNav />
        </Providers>
      </body>
    </html>
  );
}
