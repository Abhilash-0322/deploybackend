import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Aptos Shield | AI-Powered Smart Contract Security",
  description: "Real-time compliance and security monitoring for Aptos blockchain dApps. Scan, validate, and monitor smart contracts with AI-powered vulnerability detection.",
  keywords: ["Aptos", "blockchain", "smart contracts", "security", "AI", "compliance"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body
        className={`${inter.variable} ${spaceGrotesk.variable} antialiased`}
        style={{ 
          fontFamily: 'var(--font-body)',
          background: 'var(--bg-dark)',
          color: 'var(--text-primary)'
        }}
      >
        {children}
      </body>
    </html>
  );
}
