'use client';

import { useState, useEffect } from 'react';

const STORAGE_KEY = 'otklicker_cookie_consent';

interface CookieBannerProps {
  storageKey?: string;
  policyHref?: string;
}

export function CookieBanner({ storageKey = STORAGE_KEY, policyHref = '/cookies' }: CookieBannerProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const existing = localStorage.getItem(storageKey);
      if (!existing) setVisible(true);
    } catch {
      // localStorage unavailable (e.g. incognito with strict settings)
    }
  }, [storageKey]);

  const accept = (value: 'all' | 'essential') => {
    try {
      localStorage.setItem(storageKey, value);
    } catch {
      // ignore
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 200,
      background: 'var(--bg)', borderTop: '1px solid var(--line)',
      padding: '16px 24px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      gap: 16, flexWrap: 'wrap',
    }}>
      <p style={{ margin: 0, fontSize: 14, color: 'var(--text)', lineHeight: 1.5, flex: 1, minWidth: 240 }}>
        Сайт использует cookies для аналитики и улучшения работы. Продолжая просмотр, вы соглашаетесь с{' '}
        <a href={policyHref} style={{ color: 'var(--text-heading)', fontWeight: 600, textDecoration: 'underline' }}>
          Политикой использования cookies
        </a>.
      </p>
      <div style={{ display: 'flex', gap: 10, flexShrink: 0 }}>
        <button
          onClick={() => accept('essential')}
          style={{
            padding: '9px 18px', borderRadius: 999, fontSize: 13, fontWeight: 600, cursor: 'pointer',
            background: 'transparent', color: 'var(--text-heading)', border: '1px solid var(--line-strong)',
          }}
        >
          Только необходимые
        </button>
        <button
          onClick={() => accept('all')}
          style={{
            padding: '9px 18px', borderRadius: 999, fontSize: 13, fontWeight: 700, cursor: 'pointer',
            background: 'var(--brand-gradient)', color: '#fff', border: 'none',
          }}
        >
          Принять
        </button>
      </div>
    </div>
  );
}
