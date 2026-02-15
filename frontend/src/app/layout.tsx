import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
});

export const metadata: Metadata = {
  title: 'Pensieve - Reflective Journaling',
  description: 'A privacy-first journaling system with an AI companion that learns your patterns and helps you reflect.',
  keywords: ['journal', 'reflection', 'psychology', 'privacy', 'mental health', 'AI companion'],
  authors: [{ name: 'Pensieve' }],
  creator: 'Pensieve',
  openGraph: {
    type: 'website',
    title: 'Pensieve - Reflective Journaling',
    description: 'Your private space for reflection with an AI companion that grows with you.',
    siteName: 'Pensieve',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#FAFBFC" media="(prefers-color-scheme: light)" />
        <meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)" />
      </head>
      <body className="font-sans antialiased">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
