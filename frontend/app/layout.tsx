import type { Metadata } from "next";
import "./globals.css";
import "./landing.css";
import "./dashboard.css";

import GlobalLayout from "./GlobalLayout";

export const metadata: Metadata = {
  title: "FETRI Predictivo",
  description: "Predicción de triatlón",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body>
        <GlobalLayout>
          {children}
        </GlobalLayout>
      </body>
    </html>
  );
}
