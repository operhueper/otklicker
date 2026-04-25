// Synced with docs/PRODUCT_FACTS.md §5.
// Currently two plans: Бесплатный and Активный (790 ₽ / 3 weeks).
// 'dark' tone is not used now but kept because more-sections.jsx:72 has an isDark branch.
export type PricingTone = 'light' | 'brand' | 'dark';

export interface PricingPlan {
  /** Unique slug — used in data attributes and analytics */
  id: 'free' | 'active' | string;
  /** Card title ("Бесплатный", "Активный") */
  name: string;
  /** Price as string — "0", "790" — displayed with split number/currency */
  price: string;
  /** Currency symbol ("₽") */
  unit: string;
  /** Billing period ("постоянно", "за 3 недели") */
  period: string;
  /** Subtitle below name ("Чтобы попробовать", "Для активного поиска") */
  sub: string;
  /** Optional badge in top-right corner ("37 ₽ в день") */
  badge?: string;
  /** Feature list — matches more-sections.jsx, synced with PRODUCT_FACTS §5 */
  features: string[];
  /** CTA button text ("Попробовать", "Оформить пакет") */
  cta: string;
  /** CTA destination — currently always t.me/otklicker_bot */
  href: string;
  /** Card tone */
  tone: PricingTone;
}
