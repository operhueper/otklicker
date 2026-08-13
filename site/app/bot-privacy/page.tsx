import fs from 'node:fs';
import path from 'node:path';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Metadata } from 'next';
import { Nav } from '@/components/nav';
import { Footer } from '@/components/footer';

export const metadata: Metadata = {
  title: 'Политика конфиденциальности бота — откликер',
  description:
    'Как мы обрабатываем персональные данные пользователей бота @otklicker_bot',
  alternates: { canonical: '/bot-privacy' },
  robots: { index: true, follow: true },
};

export default function BotPrivacyPage() {
  let md: string | null = null;
  try {
    md = fs.readFileSync(
      path.join(process.cwd(), '..', 'legal', 'BOT_PRIVACY_POLICY.md'),
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
              <h1>Политика конфиденциальности бота @otklicker_bot</h1>
              <p>
                Документ временно недоступен. Если нужна копия политики, напишите нам на{' '}
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
