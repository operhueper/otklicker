'use client';

import { useState, useEffect } from 'react';
import { Send } from 'lucide-react';
import { BrandLockup } from './brand';
import { NAV_LINKS } from '@/lib/data/nav';

export function Nav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav
      role="navigation"
      aria-label="Основная навигация"
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        backdropFilter: scrolled ? 'saturate(140%) blur(14px)' : 'none',
        WebkitBackdropFilter: scrolled ? 'saturate(140%) blur(14px)' : 'none',
        background: scrolled ? 'rgba(250, 250, 249, 0.78)' : 'transparent',
        borderBottom: scrolled ? '1px solid var(--line)' : '1px solid transparent',
        transition: 'all 0.2s ease',
      }}
    >
      <div
        className="mx-auto max-w-container px-6"
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 72 }}
      >
        <a href="#top"><BrandLockup size="sm" /></a>
        <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
          <div
            className="nav-links"
            style={{ display: 'flex', gap: 24, fontSize: 14, fontWeight: 500, color: 'var(--text-heading)' }}
          >
            {NAV_LINKS.map(link => (
              <a key={link.href} href={link.href}>{link.label}</a>
            ))}
          </div>
          <a
            href="https://t.me/otklicker_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary nav-cta"
            style={{ padding: '10px 18px', fontSize: 14 }}
            aria-label="Открыть бота в Telegram"
          >
            <Send size={16} /> <span className="nav-cta-text">Открыть @otklicker_bot</span><span className="nav-cta-text-short">Открыть бота</span>
          </a>
        </div>
      </div>
      <style>{`
        .nav-cta-text-short { display: none; }
        @media (max-width: 860px) { .nav-links { display: none !important; } }
        @media (max-width: 480px) {
          .nav-cta-text { display: none; }
          .nav-cta-text-short { display: inline; }
        }
      `}</style>
    </nav>
  );
}
