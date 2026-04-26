import { Inter } from 'next/font/google';
import type { Metadata } from 'next';
import './globals.css';

const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800', '900'],
  display: 'swap',
  variable: '--font-inter',
});

const siteUrl = 'https://otklicker.ru';
const siteDescription =
  'Telegram-бот @otklicker_bot для автооткликов на HH.ru. Резюме за 7-10 минут, отклики в первые минуты после публикации, переписка с HR в одном Telegram.';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'откликер: Telegram-бот автооткликов на HH.ru',
    template: '%s | откликер',
  },
  description: siteDescription,
  applicationName: 'откликер',
  keywords: [
    'HH.ru',
    'автоотклики',
    'Telegram-бот',
    'поиск работы',
    'AI-резюме',
    'отклики на вакансии',
    'откликер',
  ],
  authors: [{ name: 'откликер' }],
  creator: 'откликер',
  publisher: 'откликер',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'ru_RU',
    url: siteUrl,
    siteName: 'откликер',
    title: 'откликер: Telegram-бот автооткликов на HH.ru',
    description: siteDescription,
  },
  twitter: {
    card: 'summary_large_image',
    title: 'откликер: Telegram-бот автооткликов на HH.ru',
    description: siteDescription,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/manifest.json',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
