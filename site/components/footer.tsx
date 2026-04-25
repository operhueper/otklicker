import { BrandLockup } from './brand';
import { FOOTER_LINKS } from '@/lib/data/nav';

export function Footer() {
  return (
    <footer style={{ background: 'var(--bg)', borderTop: '1px solid var(--line)', padding: '48px 0 36px' }}>
      <div className="mx-auto max-w-container px-6" style={{ display: 'flex', justifyContent: 'space-between', gap: 32, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div style={{ maxWidth: 320 }}>
          <BrandLockup size="md"/>
          <p style={{ fontSize: 14, color: 'var(--text-sub)', marginTop: 16, lineHeight: 1.6 }}>
            Telegram-бот для поиска работы на HH.ru · @otklicker_bot
          </p>
        </div>

        <div style={{ display: 'flex', gap: 56, flexWrap: 'wrap', fontSize: 14 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginBottom: 4 }}>Продукт</div>
            {FOOTER_LINKS.product.map(l => (
              <a key={l.href} href={l.href} style={{ color: 'var(--text-sub)' }}>{l.label}</a>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginBottom: 4 }}>Поддержка</div>
            {FOOTER_LINKS.support.map(l => (
              <a key={l.href} href={l.href} style={{ color: 'var(--text-sub)' }}>{l.label}</a>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontWeight: 700, color: 'var(--text-heading)', marginBottom: 4 }}>Компания</div>
            {FOOTER_LINKS.company.map(l => (
              <a key={l.href} href={l.href} style={{ color: 'var(--text-sub)' }}>{l.label}</a>
            ))}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-container px-6" style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', fontSize: 12, color: 'var(--text-sub)' }}>
        <div>© 2026 Откликер. Не аффилирован с hh.ru.</div>
        <div>
          <a href="mailto:info@otklicker.ru" style={{ color: 'var(--text-sub)' }}>info@otklicker.ru</a>
        </div>
      </div>
    </footer>
  );
}
