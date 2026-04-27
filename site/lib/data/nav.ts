export const NAV_LINKS = [
  { href: '#features', label: 'Возможности' },
  { href: '#pricing',  label: 'Тарифы' },
  { href: '#faq',      label: 'FAQ' },
] as const;

export const FOOTER_LINKS = {
  product: [
    { href: '#how',      label: 'Как работает' },
    { href: '#features', label: 'Фичи' },
    { href: '#pricing',  label: 'Тарифы' },
  ],
  support: [
    { href: '#faq',                      label: 'FAQ' },
    { href: 'mailto:info@otklicker.ru',  label: 'info@otklicker.ru' },
    { href: 'https://t.me/otklicker_support', label: 'Telegram-поддержка' },
  ],
  company: [
    { href: '/privacy',     label: 'Политика конфиденциальности' },
    { href: '/cookies',     label: 'Cookies' },
    { href: '/offer',       label: 'Оферта' },
    { href: '/bot-privacy', label: 'Политика данных бота' },
  ],
} as const;
