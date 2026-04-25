import type { BotScreenId } from './bot-screen';

export type FeatureId = 'auto' | 'cards' | 'menu';

export interface Feature {
  id: FeatureId;
  /** Tab pill text ("01 · Автоотклики") */
  label: string;
  /** H3 headline in right column */
  headline: string;
  /** Lead paragraph */
  lead: string;
  /** Bullets with round checkboxes */
  bullets: string[];
  /** Which bot screen is shown on the right */
  screen: BotScreenId;
}
