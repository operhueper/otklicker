import type { Metadata } from 'next';
import { Nav } from '@/components/nav';
import { Hero } from '@/components/hero';
import { CoverLetter } from '@/components/cover-letter';
import { HHvsOtklicker } from '@/components/hh-vs-otklicker';
import { Features } from '@/components/features';
import { Pricing } from '@/components/pricing';
import { FAQ } from '@/components/faq';
import { FinalCTA } from '@/components/final-cta';
import { Footer } from '@/components/footer';
import { CookieBanner } from '@/components/cookie-banner';
import { FAQ_ITEMS } from '@/lib/data/faq';

const homeDescription =
  'Telegram-бот @otklicker_bot для поиска работы на HH.ru. Резюме за 7-10 минут, свежие вакансии карточками, письмо под каждую и переписка с HR в одном Telegram. Бесплатный тариф навсегда.';

export const metadata: Metadata = {
  title: 'откликер: Telegram-бот для поиска работы на HH.ru',
  description: homeDescription,
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    locale: 'ru_RU',
    url: 'https://otklicker.ru/',
    siteName: 'откликер',
    title: 'откликер: Telegram-бот для поиска работы на HH.ru',
    description: homeDescription,
  },
  twitter: {
    card: 'summary_large_image',
    title: 'откликер: Telegram-бот для поиска работы на HH.ru',
    description: homeDescription,
  },
};

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'откликер',
  description:
    'Telegram-бот для поиска работы на HH.ru. Резюме за 7-10 минут, свежие вакансии карточками, письмо под каждую и переписка с HR в Telegram.',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Telegram',
  url: 'https://otklicker.ru',
  inLanguage: 'ru',
  offers: [
    {
      '@type': 'Offer',
      name: 'Бесплатный',
      price: '0',
      priceCurrency: 'RUB',
      availability: 'https://schema.org/InStock',
    },
    {
      '@type': 'Offer',
      name: 'Активный',
      price: '790',
      priceCurrency: 'RUB',
      description: '3 недели',
      availability: 'https://schema.org/InStock',
    },
  ],
  publisher: {
    '@type': 'Organization',
    name: 'ИП Энбом К.И.',
    alternateName: 'откликер',
    url: 'https://otklicker.ru',
    email: 'info@otklicker.ru',
    identifier: {
      '@type': 'PropertyValue',
      propertyID: 'ОГРНИП',
      value: '324632700187012',
    },
    sameAs: ['https://t.me/otklicker_bot', 'https://t.me/otklicker'],
  },
};

const faqJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: FAQ_ITEMS.map((item) => ({
    '@type': 'Question',
    name: item.q,
    acceptedAnswer: {
      '@type': 'Answer',
      text: item.a,
    },
  })),
};

export default function HomePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <Nav />
      <main>
        <Hero variant="chat" />
        <CoverLetter />
        <HHvsOtklicker />
        <Features />
        <Pricing />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
      <CookieBanner />
    </>
  );
}
