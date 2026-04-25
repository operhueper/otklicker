import type { Metadata } from 'next';
import { Nav } from '@/components/nav';
import { Footer } from '@/components/footer';

export const metadata: Metadata = {
  title: 'Оферта',
  description: 'Оферта на использование сервиса откликер. Документ готовится.',
  alternates: { canonical: '/offer' },
  robots: { index: false, follow: false },
};

export default function OfferPage() {
  return (
    <>
      <Nav />
      <main style={{ maxWidth: 760, margin: '0 auto', padding: '120px 24px 64px' }}>
        <h1 style={{ fontSize: 32, fontWeight: 800 }}>Оферта</h1>
        <p style={{ marginTop: 16 }}>Документ готовится. Будет опубликован в ближайшее время.</p>
        <a href="/" style={{ display: 'inline-block', marginTop: 24, color: 'var(--text-heading)' }}>← На главную</a>
      </main>
      <Footer />
    </>
  );
}
