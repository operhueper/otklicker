import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Политика данных бота @otklicker_bot',
};

export default function BotPrivacyPage() {
  return (
    <main style={{ maxWidth: 760, margin: '96px auto', padding: '0 24px' }}>
      <h1 style={{ fontSize: 32, fontWeight: 800 }}>Политика данных бота @otklicker_bot</h1>
      <p style={{ marginTop: 16 }}>Документ готовится. Будет опубликован в ближайшее время.</p>
      <a href="/" style={{ display: 'inline-block', marginTop: 24, color: 'var(--text-heading)' }}>← На главную</a>
    </main>
  );
}
