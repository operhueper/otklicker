import type { BotScreenId } from './bot-screen';

export type FeatureId = 'tinder' | 'cover' | 'hr';

export interface Feature {
  id: FeatureId;
  label: string;
  headline: string;
  lead: string;
  bullets: string[];
  screen: BotScreenId;
}
