export type BotScreenId =
  | 'onboarding'
  | 'main-menu'
  | 'hh-auth'
  | 'vacancy'
  | 'resume-menu'
  | 'filters'
  | 'hr-chat';

export interface BotMessage {
  side: 'in' | 'out';
  author?: string;
  content: string;
  time?: string;
  kind?: 'normal' | 'forwarded' | 'preview';
}

export interface KeyboardButton {
  emoji?: string;
  label: string;
  primary?: boolean;
  accent?: 'green' | 'red';
}

export type KeyboardRow = KeyboardButton | KeyboardButton[];

export interface ChatHeader {
  name: string;
  subtitle: string;
}

export interface BotScreen {
  content?: string;
  messages?: BotMessage[];
  buttons: KeyboardRow[];
  time?: string;
  header?: Partial<ChatHeader>;
}

export type BotScreenMap = Record<BotScreenId, BotScreen>;
