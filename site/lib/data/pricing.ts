import type { PricingPlan } from '@/lib/types';

export const PRICING_PLANS: PricingPlan[] = [
  {
    id: 'free',
    name: 'Бесплатный',
    price: '0',
    unit: '₽',
    period: 'постоянно',
    sub: 'Чтобы попробовать',
    features: [
      'Резюме через бота',
      'Мониторинг вакансий',
      'Карточки вакансий в Telegram',
    ],
    cta: 'Открыть @otklicker_bot',
    href: 'https://t.me/otklicker_bot',
    tone: 'light',
  },
  {
    id: 'active',
    name: 'Активный',
    price: '790',
    unit: '₽',
    period: 'за 3 недели',
    sub: 'Для активного поиска',
    features: [
      'Всё из бесплатного',
      'Автоотклики до 15 в день',
      'Письма под каждую вакансию',
      'HR-переписка в Telegram',
    ],
    cta: 'Открыть @otklicker_bot',
    href: 'https://t.me/otklicker_bot',
    tone: 'brand',
  },
];
