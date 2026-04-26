import type { HowItWorksStep } from '@/lib/types';

export const HOW_IT_WORKS_STEPS: HowItWorksStep[] = [
  {
    number: '01',
    title: 'Резюме за 7–10 минут',
    description: 'Бот задаёт вопросы голосом или текстом. Загружаете старое резюме — он парсит файл и подсказывает, что усилить.',
    screen: 'resume-menu',
  },
  {
    number: '02',
    title: 'Подключение HH',
    description: 'Email или телефон — HH присылает одноразовый код. Вводите код в боте. Пароль не запрашиваем и не храним.',
    screen: 'hh-auth',
  },
  {
    number: '03',
    title: 'Фильтры и режим',
    description: 'Зарплата, опыт, гео, график, стоп-слова. Два режима: «С подтверждением» и «Автопилот» с порогом 75%.',
    screen: 'filters',
  },
  {
    number: '04',
    title: 'Отклики и переписка с HR',
    description: 'Бот отправляет отклики и предлагает ответы на сообщения от HR. Вся переписка — в Telegram, без захода на HH.',
    screen: 'vacancy',
  },
];
