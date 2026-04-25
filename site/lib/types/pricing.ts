export type PricingTone = 'light' | 'brand' | 'dark';

export interface PricingPlan {
  id: 'free' | 'active' | string;
  name: string;
  price: string;
  unit: string;
  period: string;
  sub: string;
  badge?: string;
  features: string[];
  cta: string;
  href: string;
  tone: PricingTone;
}
