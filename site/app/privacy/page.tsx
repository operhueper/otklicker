import fs from 'node:fs';
import path from 'node:path';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Политика конфиденциальности',
  description:
    'Политика конфиденциальности сайта otklicker.ru. Что мы собираем у посетителей и как обрабатываем эти данные.',
};

export default function PrivacyPage() {
  const md = fs.readFileSync(
    path.join(process.cwd(), '..', 'legal', 'SITE_PRIVACY_POLICY.md'),
    'utf-8',
  );

  return (
    <main className="mx-auto max-w-[720px] px-5 py-16 md:py-24">
      <article className="prose prose-stone max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
      </article>
      <p className="mt-12">
        <a href="/" className="text-text-heading underline-offset-4 hover:underline">
          ← На главную
        </a>
      </p>
    </main>
  );
}
