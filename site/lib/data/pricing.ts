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
      'Резюме голосом, собранное так, чтобы пройти ATS работодателя',
      'Свежие вакансии карточками в Telegram',
      'Письмо под каждую вакансию',
      '5 откликов на проверку',
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
    pricePerDay: '≈ 38 ₽ в день',
    sub: 'Для активного поиска',
    features: [
      'Всё из бесплатного',
      'До 15 откликов в день',
      'Письмо под каждую вакансию',
      'Переписка с работодателем в Telegram',
    ],
    cta: 'Открыть @otklicker_bot',
    href: 'https://t.me/otklicker_bot',
    tone: 'brand',
  },
];
