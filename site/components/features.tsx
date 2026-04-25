'use client';

import { useState } from 'react';
import { Check } from 'lucide-react';
import { FEATURES } from '@/lib/data/features';
import { BOT_SCREENS } from '@/lib/screens/bot-screens';
import { RealBotScreen } from './real-bot-screen';
import type { Feature } from '@/lib/types';

interface FeaturesProps {
  features?: Feature[];
}

export function Features({ features = FEATURES }: FeaturesProps) {
  const [active, setActive] = useState(0);
  const cur = features[active];

  return (
    <section id="features" style={{ background: 'var(--bg-dark)', color: 'var(--text-on-dark)', position: 'relative', overflow: 'hidden', padding: '96px 0' }}>
      <div className="noise" aria-hidden="true"/>
      <div className="halo" style={{ width: 600, height: 600, background: '#DB2777', top: -200, right: -200, opacity: 0.2 }} aria-hidden="true"/>
      <div className="halo" style={{ width: 520, height: 520, background: '#F97316', bottom: -160, left: -140, opacity: 0.18 }} aria-hidden="true"/>

      <div className="mx-auto max-w-container px-6" style={{ position: 'relative', zIndex: 2 }}>
        <div style={{ textAlign: 'left', maxWidth: 720 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 14px', borderRadius: 999, background: 'rgba(254,243,199,0.08)', color: 'var(--text-on-dark-sub)', fontSize: 12, fontWeight: 600, letterSpacing: '0.02em', textTransform: 'uppercase', border: '1px solid var(--line-dark)' }}>
            <span className="eyebrow-dot" aria-hidden="true"/>
            Что внутри
          </div>
          <h2 className="text-h2" style={{ color: 'var(--text-on-dark)', marginTop: 14 }}>
            Что делает бот<br/>внутри <span className="grad-text">Telegram</span>
          </h2>
          <p style={{ color: 'var(--text-on-dark-sub)', maxWidth: 560, fontSize: 17, lineHeight: 1.55, marginTop: 14 }}>
            Резюме, отклики и переписка с HR — в одном чате. Без браузерных вкладок и копипастов.
          </p>
        </div>

        <div
          role="tablist"
          aria-label="Функции бота"
          style={{ display: 'flex', gap: 8, marginTop: 32, flexWrap: 'wrap' }}
        >
          {features.map((f, i) => (
            <button
              key={f.id}
              role="tab"
              aria-selected={active === i}
              aria-controls={`feat-panel-${f.id}`}
              id={`feat-tab-${f.id}`}
              onClick={() => setActive(i)}
              style={{
                padding: '12px 18px', borderRadius: 999, fontSize: 14, fontWeight: 600,
                border: active === i ? '1px solid transparent' : '1px solid var(--line-dark)',
                background: active === i ? 'var(--brand-gradient-text)' : 'transparent',
                color: active === i ? '#fff' : 'var(--text-on-dark-sub)',
                boxShadow: active === i ? '0 10px 24px rgba(219,39,119,0.25)' : 'none',
                transition: 'all 0.2s',
                cursor: 'pointer',
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div
          role="tabpanel"
          id={`feat-panel-${cur.id}`}
          aria-labelledby={`feat-tab-${cur.id}`}
          className="feat-grid"
          style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 64, alignItems: 'center', marginTop: 48 }}
        >
          <div>
            <h3 className="text-h3" style={{ color: 'var(--text-on-dark)', margin: '0 0 18px' }}>
              {cur.headline}
            </h3>
            <p style={{ fontSize: 17, lineHeight: 1.6, color: 'var(--text-on-dark-sub)', margin: '0 0 24px', maxWidth: 520 }}>
              {cur.lead}
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
              {cur.bullets.map((b, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{
                    width: 24, height: 24, borderRadius: 999, background: 'var(--brand-gradient)',
                    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0, marginTop: 2,
                  }}>
                    <Check size={14} />
                  </div>
                  <span style={{ fontSize: 15, lineHeight: 1.5, color: 'var(--text-on-dark)' }}>{b}</span>
                </li>
              ))}
            </ul>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div key={cur.id} className="animate-slide-in-features">
              <RealBotScreen {...BOT_SCREENS[cur.screen]} width={320} height={580} />
            </div>
          </div>
        </div>
      </div>

      <style>{`@media (max-width: 960px) { .feat-grid { grid-template-columns: 1fr !important; gap: 40px !important; } }`}</style>
    </section>
  );
}
