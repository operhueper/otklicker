'use client';

import { useState } from 'react';
import { HOW_IT_WORKS_STEPS } from '@/lib/data/how-it-works';
import { BOT_SCREENS } from '@/lib/screens/bot-screens';
import { RealBotScreen } from './real-bot-screen';
import type { HowItWorksStep } from '@/lib/types';

interface HowItWorksProps {
  steps?: HowItWorksStep[];
}

export function HowItWorks({ steps = HOW_IT_WORKS_STEPS }: HowItWorksProps) {
  const [active, setActive] = useState(0);

  return (
    <section id="how" style={{ background: 'var(--bg-pastel)', position: 'relative', overflow: 'hidden', padding: '96px 0' }}>
      <div className="mx-auto max-w-container px-6" style={{ position: 'relative', zIndex: 2 }}>
        <div className="section-head" style={{ textAlign: 'center', maxWidth: 720, margin: '0 auto 56px' }}>
          <div className="eyebrow"><span className="eyebrow-dot" aria-hidden="true"/>Как это работает</div>
          <h2 className="text-h2 text-text-heading" style={{ margin: '16px 0 14px' }}>Четыре шага<br/>до первого <span className="grad-text">отклика</span></h2>
          <p style={{ fontSize: 17, color: 'var(--text-sub)', lineHeight: 1.55, margin: 0 }}>Всё внутри Telegram. Без браузера, без приложения, без копипастов.</p>
        </div>

        <div className="how-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: 60, alignItems: 'center' }}>
          {/* Left: step list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {steps.map((s, i) => {
              const isActive = active === i;
              return (
                <button
                  key={i}
                  onClick={() => setActive(i)}
                  aria-pressed={isActive}
                  style={{
                    textAlign: 'left',
                    background: isActive ? '#FFFFFF' : 'transparent',
                    border: isActive ? '1px solid var(--line-strong)' : '1px solid transparent',
                    borderRadius: 18, padding: '18px 22px',
                    display: 'flex', alignItems: 'flex-start', gap: 16,
                    transition: 'all 0.2s',
                    boxShadow: isActive ? '0 10px 30px rgba(120,53,15,0.08)' : 'none',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{
                    width: 42, height: 42, borderRadius: 12, flexShrink: 0,
                    background: isActive ? 'var(--brand-gradient-text)' : 'rgba(146, 64, 14, 0.08)',
                    color: isActive ? '#fff' : 'var(--text-heading)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 800, fontSize: 14, transition: 'all 0.2s',
                  }}>{s.number}</div>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.01em' }}>{s.title}</div>
                    <div style={{ fontSize: 14, lineHeight: 1.55, color: 'var(--text)', marginTop: 4 }}>{s.description}</div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: bot screen */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div key={active} className="animate-slide-in-from-right">
              <RealBotScreen {...BOT_SCREENS[steps[active].screen]} width={340} height={620} />
            </div>
          </div>
        </div>
      </div>

      <style>{`@media (max-width: 960px) { .how-grid { grid-template-columns: 1fr !important; gap: 48px !important; } }`}</style>
    </section>
  );
}
