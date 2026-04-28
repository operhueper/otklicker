import { Inter } from 'next/font/google';
import type { Metadata } from 'next';
import Script from 'next/script';
import './globals.css';

const metricaId = process.env.NEXT_PUBLIC_YANDEX_METRICA_ID;

const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800', '900'],
  display: 'swap',
  variable: '--font-inter',
});

const siteUrl = 'https://otklicker.ru';
const siteDescription =
  'Telegram-бот @otklicker_bot для автооткликов на HH.ru. Резюме за 7-10 минут, отклики в первые минуты после публикации, переписка с HR в одном Telegram. Бесплатный тариф навсегда.';

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
  verification: {
    yandex: 'f0e9c0572fd1a856',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={inter.variable}>
      <body>
        {children}
        {metricaId ? (
          <>
            <Script id="yandex-metrica" strategy="afterInteractive">
              {`(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");ym(${metricaId},"init",{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true});`}
            </Script>
            <noscript>
              <div>
                <img
                  src={`https://mc.yandex.ru/watch/${metricaId}`}
                  style={{ position: 'absolute', left: '-9999px' }}
                  alt=""
                />
              </div>
            </noscript>
          </>
        ) : null}
      </body>
    </html>
  );
}
