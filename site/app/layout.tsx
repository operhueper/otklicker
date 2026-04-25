import { Inter } from 'next/font/google';
import type { Metadata } from 'next';
import './globals.css';

const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800', '900'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://otklicker.ru'),
  title: {
    default: 'откликер — Telegram-бот автооткликов на HH.ru',
    template: '%s | откликер',
  },
  description: 'Бот следит за лентой HH и отправляет отклик в первые минуты после публикации. Резюме, отклики и переписка с HR — в одном Telegram.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
