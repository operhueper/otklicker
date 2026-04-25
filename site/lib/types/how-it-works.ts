import type { BotScreenId } from './bot-screen';

export interface HowItWorksStep {
  /** Two-digit number: "01" .. "04" */
  number: string;
  title: string;
  description: string;
  screen: BotScreenId;
}
