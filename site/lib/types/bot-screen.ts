export type BotScreenId =
  | 'onboarding'
  | 'main-menu'
  | 'hh-auth'
  | 'hh-panel'
  | 'vacancy'
  | 'resume-menu'
  | 'filters';

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
  content: string;
  buttons: KeyboardRow[];
  time?: string;
  header?: Partial<ChatHeader>;
}

export type BotScreenMap = Record<BotScreenId, BotScreen>;
