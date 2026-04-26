'use client';

import { Check, Send } from 'lucide-react';
import { PRICING_PLANS } from '@/lib/data/pricing';
import type { PricingPlan } from '@/lib/types';

interface PricingProps {
  plans?: PricingPlan[];
}

export function Pricing({ plans = PRICING_PLANS }: PricingProps) {
  return (
    <section id="pricing" style={{ background: 'var(--bg)', position: 'relative', overflow: 'hidden', padding: '96px 0' }}>
      <div className="mx-auto max-w-container px-6">
        <div style={{ textAlign: 'center', maxWidth: 720, margin: '0 auto' }}>
          <div className="eyebrow"><span className="eyebrow-dot" aria-hidden="true"/>Тарифы</div>
          <h2 className="text-h2 text-text-heading" style={{ margin: '16px 0 14px' }}>
            Один пакет<br/>на <span className="grad-text">активный поиск</span>
          </h2>
          <p style={{ fontSize: 17, color: 'var(--text-sub)', lineHeight: 1.55, margin: 0 }}>
            без автопродления. Нашли оффер — закрыли задачу.
          </p>
        </div>

        <div className="price-grid" style={{
          display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)',
          maxWidth: 880, margin: '48px auto 0', gap: 20, alignItems: 'stretch',
        }}>
          {plans.map(p => <PriceCard key={p.id} plan={p}/>)}
        </div>

        <div style={{ marginTop: 28, textAlign: 'center', color: 'var(--text-sub)', fontSize: 13, maxWidth: 560, margin: '28px auto 0', lineHeight: 1.6 }}>
          Оплата через ЮKassa, чеки 54-ФЗ. Возврат 14 дней по закону, если бот не прислал ни одной вакансии за 48 часов после оплаты.
        </div>
      </div>

      <style>{`@media (max-width: 960px) { .price-grid { grid-template-columns: 1fr !important; } }`}</style>
    </section>
  );
}

export interface PriceCardProps {
  plan: PricingPlan;
}

export function PriceCard({ plan }: PriceCardProps) {
  const isDark = plan.tone === 'dark';
  const isBrand = plan.tone === 'brand';

  return (
    <div style={{
      borderRadius: 24, padding: 32, position: 'relative',
      display: 'flex', flexDirection: 'column',
      background: isBrand ? 'var(--brand-gradient-text)' : isDark ? '#1C1917' : '#FFFFFF',
      border: isBrand || isDark ? '1px solid transparent' : '1px solid var(--line)',
      color: isDark ? '#FEF3C7' : isBrand ? '#fff' : 'var(--text-heading)',
      boxShadow: isBrand ? '0 24px 60px rgba(219,39,119,0.24), 0 8px 22px rgba(249,115,22,0.2)' : '0 1px 2px rgba(120,53,15,0.04)',
      transform: isBrand ? 'scale(1.03)' : 'none',
      zIndex: isBrand ? 2 : 1,
    }}>
      {plan.badge && (
        <div style={{
          position: 'absolute', top: -12, right: 24,
          padding: '5px 12px', borderRadius: 999, background: '#1C1917', color: '#FEF3C7',
          fontSize: 11, fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase',
        }}>
          {plan.badge}
        </div>
      )}

      <div style={{ fontSize: 13, fontWeight: 600, opacity: 0.8, letterSpacing: '0.04em', textTransform: 'uppercase' }}>{plan.name}</div>
      <div style={{ fontSize: 14, marginTop: 4, opacity: 0.85 }}>{plan.sub}</div>

      <div style={{ margin: '22px 0 8px', display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span style={{ fontSize: 56, fontWeight: 900, lineHeight: 1, letterSpacing: '-0.03em' }}>{plan.price}</span>
        <span style={{ fontSize: 22, fontWeight: 700, opacity: 0.9 }}>{plan.unit}</span>
      </div>
      <div style={{ fontSize: 14, opacity: 0.8, marginBottom: 24 }}>{plan.period}</div>

      <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 28px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {plan.features.map((f, i) => (
          <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 14, lineHeight: 1.45 }}>
            <Check size={16} color={isBrand ? '#fff' : isDark ? '#FBBF24' : '#DB2777'} />
            <span style={{ opacity: 0.95 }}>{f}</span>
          </li>
        ))}
      </ul>

      <a
        href={plan.href}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          marginTop: 'auto', padding: '14px 20px', borderRadius: 999, textAlign: 'center',
          fontSize: 15, fontWeight: 700,
          background: isBrand ? '#FFFFFF' : isDark ? 'var(--brand-gradient)' : '#1C1917',
          color: isBrand ? '#DB2777' : '#FFFFFF',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          transition: 'transform 0.15s',
        }}
        onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-1px)')}
        onMouseLeave={e => (e.currentTarget.style.transform = '')}
      >
        <Send size={16} /> {plan.cta}
      </a>
    </div>
  );
}
