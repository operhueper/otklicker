'use client';

import { useState } from 'react';
import { Plus, Minus } from 'lucide-react';
import { FAQ_ITEMS } from '@/lib/data/faq';
import type { FAQItem } from '@/lib/types';

interface FAQProps {
  items?: FAQItem[];
  defaultOpen?: number | null;
}

export function FAQ({ items = FAQ_ITEMS, defaultOpen = 0 }: FAQProps) {
  const [open, setOpen] = useState<number>(defaultOpen ?? -1);

  return (
    <section id="faq" style={{ background: 'var(--bg-pastel)', padding: '96px 0' }}>
      <div className="mx-auto max-w-container px-6">
        <div style={{ textAlign: 'center', maxWidth: 720, margin: '0 auto 48px' }}>
          <div className="eyebrow"><span className="eyebrow-dot" aria-hidden="true"/>FAQ</div>
          <h2 className="text-h2 text-text-heading" style={{ margin: '16px 0 0' }}>
            Короткие ответы<br/>на частые вопросы
          </h2>
        </div>

        <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {items.map((it, i) => {
            const isOpen = open === i;
            return (
              <div key={it.id} style={{
                background: '#fff', borderRadius: 18, border: '1px solid var(--line)',
                overflow: 'hidden', transition: 'all 0.2s',
              }}>
                <button
                  onClick={() => setOpen(isOpen ? -1 : i)}
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${it.id}`}
                  id={`faq-btn-${it.id}`}
                  style={{ width: '100%', padding: '22px 26px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, textAlign: 'left', cursor: 'pointer' }}
                >
                  <span style={{ fontSize: 17, fontWeight: 700, color: 'var(--text-heading)' }}>{it.q}</span>
                  <div style={{
                    width: 32, height: 32, borderRadius: 999,
                    background: isOpen ? 'var(--brand-gradient)' : 'var(--bg-pastel)',
                    color: isOpen ? '#fff' : 'var(--text-heading)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0, transition: 'all 0.2s',
                  }}>
                    {isOpen ? <Minus size={16}/> : <Plus size={16}/>}
                  </div>
                </button>
                {isOpen && (
                  <div
                    id={`faq-answer-${it.id}`}
                    role="region"
                    aria-labelledby={`faq-btn-${it.id}`}
                    style={{ padding: '0 26px 24px', fontSize: 15, lineHeight: 1.6, color: 'var(--text)', maxWidth: 620 }}
                  >
                    {it.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
