import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import NavBar from "./components/NavBar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Narodne novine — NLP pretraživanje zakona",
  description:
    "Inteligentno pretraživanje hrvatskih zakona, uredbi i odluka uz automatski generirane sažetke i ključne informacije.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="hr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 dark:bg-zinc-950">
        <NavBar />
        <div className="flex-1">{children}</div>
        <footer className="border-t border-zinc-200 dark:border-zinc-800 py-6 text-center
                           text-xs text-zinc-400 dark:text-zinc-600">
          Narodne novine NLP — podaci iz{" "}
          <a
            href="https://narodne-novine.nn.hr"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-zinc-600 dark:hover:text-zinc-400"
          >
            narodne-novine.nn.hr
          </a>
        </footer>
      </body>
    </html>
  );
}
