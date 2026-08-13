import fs from 'node:fs';
import path from 'node:path';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Metadata } from 'next';
import { Nav } from '@/components/nav';
import { Footer } from '@/components/footer';

export const metadata: Metadata = {
  title: 'Публичная оферта — откликер',
  description:
    'Условия использования Telegram-бота @otklicker_bot и тарифные планы',
  alternates: { canonical: '/offer' },
  robots: { index: true, follow: true },
};

export default function OfferPage() {
  let md: string | null = null;
  try {
    md = fs.readFileSync(
      path.join(process.cwd(), '..', 'legal', 'OFFER.md'),
      'utf-8',
    );
  } catch {
    md = null;
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-[720px] px-5 py-16 md:py-24" style={{ paddingTop: 120 }}>
        <article className="prose prose-stone max-w-none">
          {md ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
          ) : (
            <>
              <h1>Публичная оферта</h1>
              <p>
                Документ временно недоступен. Если нужна копия оферты, напишите нам на{' '}
                <a href="mailto:info@otklicker.ru">info@otklicker.ru</a>.
              </p>
            </>
          )}
        </article>
        <p className="mt-12">
          <a href="/" className="text-text-heading underline-offset-4 hover:underline">
            ← На главную
          </a>
        </p>
      </main>
      <Footer />
    </>
  );
}
