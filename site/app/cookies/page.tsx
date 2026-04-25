import fs from 'node:fs';
import path from 'node:path';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Metadata } from 'next';
import { Nav } from '@/components/nav';
import { Footer } from '@/components/footer';

export const metadata: Metadata = {
  title: 'Политика использования cookies',
  description:
    'Какие cookies использует сайт otklicker.ru, как ими управлять и как отозвать согласие.',
  alternates: { canonical: '/cookies' },
  robots: { index: true, follow: true },
};

export default function CookiesPage() {
  const md = fs.readFileSync(
    path.join(process.cwd(), '..', 'legal', 'COOKIE_POLICY.md'),
    'utf-8'
  );
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-[720px] px-5 py-16 md:py-24" style={{ paddingTop: 120 }}>
        <article className="prose prose-stone max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
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
