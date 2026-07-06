import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LinkShield",
  description: "A trustworthy link shortener",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,600;0,14..32,700;1,14..32,300;1,14..32,400;1,14..32,600;1,14..32,700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className="min-h-screen"
        style={{
          background: "var(--sgds-bg-default)",
          color: "var(--sgds-color-default)",
          fontFamily: "var(--sgds-font-family-brand)",
        }}
      >
        {children}
      </body>
    </html>
  );
}
