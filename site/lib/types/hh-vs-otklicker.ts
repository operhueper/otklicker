import type { LucideIcon } from 'lucide-react';

export interface HHvsOtklickerPair {
  /** Стабильный id для key и аналитики. */
  id: string;
  /** Левая колонка: что происходит на HH в браузере. */
  pain: {
    icon: LucideIcon;
    title: string;
    text: string;
  };
  /** Правая колонка: что делает бот в Telegram. */
  answer: {
    icon: LucideIcon;
    title: string;
    text: string;
  };
}
