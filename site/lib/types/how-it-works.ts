import type { BotScreenId } from './bot-screen';

export interface HowItWorksStep {
  number: string;
  title: string;
  description: string;
  screen: BotScreenId;
}
