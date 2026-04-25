// Identifiers for the five ready-made scenarios from real-bot.jsx
export type BotScreenId =
  | 'onboarding'
  | 'main-menu'
  | 'hh-auth'
  | 'hh-panel'
  | 'vacancy';

// Reply-keyboard button
export interface KeyboardButton {
  emoji?: string;
  label: string;
  primary?: boolean;
  accent?: 'green' | 'red';
  /** twoCol/pairLabel from source — not used in data, reserved for future */
}

// Keyboard row: single button or horizontal pair
export type KeyboardRow = KeyboardButton | KeyboardButton[];

// Chat header (optional override of default "Откликер · бот")
export interface ChatHeader {
  name: string;
  subtitle: string;
}

// One bot screen — what RealBotScreen accepts
export interface BotScreen {
  /**
   * HTML markup of the bubble content. Allowed because:
   *   1) data is static, lives in our repo;
   *   2) Telegram-style markup (colored links, <b>) is simpler as HTML than a component.
   * If dangerouslySetInnerHTML needs to be removed in Phase 2 — migrate to segment array.
   */
  content: string;
  buttons: KeyboardRow[];
  /** Time in bubble header "06:32" */
  time?: string;
  header?: Partial<ChatHeader>;
}

// Map of all five screens
export type BotScreenMap = Record<BotScreenId, BotScreen>;

// (Reserve for future — if HeroChat moves to a shared engine.)
// BotMessage is used only in HeroChat, where messages are constructed from JobCard.
// In Phase 1 HeroChat keeps its own local shape.
export interface BotMessage {
  role: 'bot' | 'user' | 'system';
  type: 'text' | 'options' | 'vacancy' | 'vacancy-rich' | 'typing' | 'stats' | 'file' | 'toast';
  content?: string;           // HTML or plain
  buttons?: KeyboardButton[];
  /** For type='vacancy-rich' — structured job card */
  job?: import('./job').JobCard;
  /** For type='toast' (response-bubble in HeroChat) */
  tone?: 'apply' | 'skip';
}
