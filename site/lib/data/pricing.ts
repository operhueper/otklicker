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
      'Резюме голосом через бота',
      'Бот сам следит за свежими вакансиями',
      'Карточки вакансий в Telegram',
      '5 откликов с письмом под каждую, чтобы попробовать',
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
      'До 15 откликов в день, бот делает сам',
      'Письмо под каждую вакансию',
      'Переписка с работодателем в Telegram',
    ],
    cta: 'Открыть @otklicker_bot',
    href: 'https://t.me/otklicker_bot',
    tone: 'brand',
  },
];
