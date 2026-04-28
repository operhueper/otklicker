import type { BotScreenId } from './bot-screen';

export type FeatureId = 'resume' | 'tinder' | 'cover' | 'hr';

export interface Feature {
  id: FeatureId;
  label: string;
  headline: string;
  lead: string;
  bullets: string[];
  screen: BotScreenId;
}
