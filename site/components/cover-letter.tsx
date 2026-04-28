'use client';

import { useState, useEffect, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';

interface CoverLetterSample {
  jobTitle: string;
  company: string;
  abbr: string;
  letter: string;
}

const COVER_LETTERS: CoverLetterSample[] = [
  {
    jobTitle: 'Senior Product Designer',
    company: 'Yandex Eats',
    abbr: 'YE',
    letter:
      'Здравствуйте! Увидел вакансию Senior Product Designer в Yandex Eats. У вас в требованиях работа с дизайн-системой и B2C-флоу — это ровно то, чем я занимаюсь последние 4 года.\n\nПоследний кейс: переработал чекаут в food-delivery, конверсия выросла на 11%, среднее время оформления упало с 38 до 22 секунд. До этого 2 года вёл подсистему профилей в финтех-приложении на 1,2 млн MAU.\n\nЗаметил у вас в требованиях «работа со стрессом и дедлайнами» — у меня релизный цикл 2 недели последние 3 года, привык. Готов созвониться на 20 минут на этой неделе и показать кейсы под ваши задачи.',
  },
  {
    jobTitle: 'Шеф-повар горячего цеха',
    company: 'Ресторан «Белуга»',
    abbr: 'Б',
    letter:
      'Добрый день. По вакансии шеф-повара горячего цеха: 5 лет на горячке в авторских ресторанах СПб, последние 2 года — су-шеф в проекте на 120 посадок, средний чек 4 500 ₽.\n\nХАССП поднимал с нуля, прошёл 2 проверки Роспотребнадзора без замечаний. Бригада 6 человек, текучка за год — 1 человек. Вывел два сезонных меню, food cost удержал в 28%.\n\nВижу у вас в требованиях «опыт открытия» — участвовал в запуске 2 проектов, готов рассказать на стажировке. Удобно подъехать в любой будний день после 11:00.',
  },
  {
    jobTitle: 'Менеджер по продажам',
    company: 'СтройДвор',
    abbr: 'СД',
    letter:
      'Здравствуйте! По вакансии менеджера B2B в СтройДвор: 2 года в активных продажах стройматериалов, средний чек 380 000 ₽, план по новым клиентам делал 11 месяцев из 12, лучший месяц — 142% от плана.\n\nРаботаю в amoCRM, веду холодную базу по своим скриптам, конверсия из лида в сделку 18% (по отрасли средняя 8-10%). За последний год привёл 14 новых клиентов на повторные закупки.\n\nЗаметил, что вы ищете под расширение в регионы — у меня выстроена сеть из 6 субподрядчиков в ЦФО, могу принести их вам на старте. Готов выйти на собеседование на этой неделе.',
  },
];

const ROTATE_MS = 5500;

export function CoverLetter() {
  const [idx, setIdx] = useState(0);
  const [fade, setFade] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    timerRef.current = setInterval(() => {
      setFade(true);
      setTimeout(() => {
        setIdx((i) => (i + 1) % COVER_LETTERS.length);
        setFade(false);
      }, 280);
    }, ROTATE_MS);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const sample = COVER_LETTERS[idx];

  return (
    <section
      id="cover-letter"
      aria-labelledby="cover-letter-title"
      style={{
        background: 'var(--bg)',
        paddingTop: 96,
        paddingBottom: 96,
        borderTop: '1px solid var(--line)',
        borderBottom: '1px solid var(--line)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        className="halo"
        style={{ width: 480, height: 480, background: '#F97316', top: -160, right: -120, opacity: 0.18 }}
        aria-hidden="true"
      />
      <div
        className="halo"
        style={{ width: 380, height: 380, background: '#FBBF24', bottom: -160, left: -100, opacity: 0.18 }}
        aria-hidden="true"
      />

      <div className="mx-auto max-w-container px-6" style={{ position: 'relative', zIndex: 2 }}>
        <div
          className="cover-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 56,
            alignItems: 'center',
          }}
        >
          {/* Left column: text */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div>
              <div className="eyebrow">
                <span className="eyebrow-dot" aria-hidden="true" />
                Сопроводительное
              </div>
              <h2 id="cover-letter-title" className="text-h2 text-text-heading" style={{ margin: '16px 0 18px' }}>
                Письмо под вакансию, <span className="grad-text">не шаблон</span>
              </h2>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  'Собирается из текста вакансии и вашего резюме',
                  'Превью перед отправкой',
                  'Правки голосом или текстом',
                ].map((item) => (
                  <li key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 16, color: 'var(--text-sub)', lineHeight: 1.5 }}>
                    <span style={{ color: '#DB2777', fontWeight: 700, flexShrink: 0 }}>-</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <TrapsBlock />
          </div>

          {/* Right column: phone mockup */}
          <div style={{ display: 'flex', justifyContent: 'center', minWidth: 0 }}>
            <PhonePreview sample={sample} fade={fade} />
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 960px) { .cover-grid { grid-template-columns: 1fr !important; gap: 48px !important; } }
        @media (max-width: 720px) { .cover-grid { gap: 36px !important; } }
      `}</style>
    </section>
  );
}

function PhonePreview({ sample, fade }: { sample: CoverLetterSample; fade: boolean }) {
  return (
    <div
      style={{
        width: '100%',
        maxWidth: 360,
        aspectRatio: '360 / 620',
        borderRadius: 42,
        background: '#111',
        padding: 10,
        boxShadow: 'var(--shadow-phone)',
        position: 'relative',
      }}
    >
      <div
        style={{
          width: '100%',
          height: '100%',
          borderRadius: 34,
          overflow: 'hidden',
          background: '#17212B',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        {/* Status bar */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 34,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 26px',
            color: '#fff',
            fontWeight: 600,
            fontSize: 13,
            zIndex: 10,
          }}
        >
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>9:41</span>
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: 8,
              transform: 'translateX(-50%)',
              width: 110,
              height: 26,
              background: '#000',
              borderRadius: 20,
            }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="16" height="10" viewBox="0 0 16 10" fill="#fff" aria-hidden="true">
              <rect x="0" y="7" width="3" height="3" rx="0.5" />
              <rect x="4" y="5" width="3" height="5" rx="0.5" />
              <rect x="8" y="2" width="3" height="8" rx="0.5" />
              <rect x="12" y="0" width="3" height="10" rx="0.5" />
            </svg>
            <svg width="26" height="12" viewBox="0 0 26 12" fill="none" aria-hidden="true">
              <rect x="0.5" y="0.5" width="22" height="11" rx="2.5" stroke="#fff" opacity="0.5" />
              <rect x="2" y="2" width="19" height="8" rx="1.2" fill="#fff" />
              <rect x="23" y="3.5" width="1.5" height="5" rx="0.5" fill="#fff" opacity="0.5" />
            </svg>
          </div>
        </div>

        {/* Header */}
        <div
          style={{
            marginTop: 34,
            background: '#212D3B',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            borderBottom: '1px solid rgba(255,255,255,0.04)',
            flexShrink: 0,
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#6C7883"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 999,
              background: 'linear-gradient(135deg,#FBBF24,#F97316 33%,#EF4444 66%,#DB2777)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M14 4.1 12 6" />
              <path d="m5.1 8-2.9-.8" />
              <path d="m6 12-1.9 2" />
              <path d="M7.2 2.2 8 5.1" />
              <path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z" />
            </svg>
          </div>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
            <span style={{ fontWeight: 600, fontSize: 15, color: '#fff' }}>откликер</span>
            <span style={{ fontSize: 12, color: '#3390EC', fontWeight: 500 }}>бот · онлайн</span>
          </div>
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#6C7883"
            strokeWidth="2"
            aria-hidden="true"
          >
            <circle cx="5" cy="12" r="1.5" />
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="19" cy="12" r="1.5" />
          </svg>
        </div>

        {/* Chat area */}
        <div
          style={{
            flex: 1,
            padding: '12px 10px 8px',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <div
            style={{
              background: '#182533',
              color: '#fff',
              padding: '8px 11px',
              borderRadius: 14,
              borderBottomLeftRadius: 4,
              fontSize: 12.5,
              lineHeight: 1.4,
              alignSelf: 'flex-start',
              maxWidth: '92%',
            }}
            key={`intro-${sample.company}`}
          >
            Готов отклик на вакансию <b>{sample.jobTitle}</b>. Покажу письмо?
          </div>

          {/* Letter card */}
          <div
            key={`letter-${sample.company}`}
            style={{
              background: '#182533',
              color: '#fff',
              padding: '12px 13px',
              borderRadius: 14,
              borderBottomLeftRadius: 4,
              fontSize: 12,
              lineHeight: 1.5,
              alignSelf: 'flex-start',
              width: '94%',
              opacity: fade ? 0 : 1,
              transform: fade ? 'translateY(6px)' : 'none',
              transition: 'opacity .28s ease, transform .28s ease',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginBottom: 8,
                paddingBottom: 8,
                borderBottom: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 8,
                  background: '#fff',
                  color: '#92400E',
                  fontWeight: 800,
                  fontSize: 11,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {sample.abbr}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color: '#fff',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {sample.jobTitle}
                </div>
                <div style={{ fontSize: 11, color: '#6C7883' }}>{sample.company}</div>
              </div>
            </div>
            <div style={{ color: '#E6E9EC', fontSize: 11.5, lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
              {sample.letter}
            </div>
            <div
              style={{
                marginTop: 10,
                fontSize: 10,
                color: '#6C7883',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span>{sample.letter.length} знаков · в правилах HH</span>
              <span style={{ fontVariantNumeric: 'tabular-nums' }}>9:41</span>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div
          style={{
            padding: '6px 6px 10px',
            background: '#0E1621',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', gap: 4 }}>
            <button
              type="button"
              style={{
                flex: 1,
                padding: '11px 8px',
                borderRadius: 8,
                fontWeight: 700,
                fontSize: 12.5,
                background: 'rgba(22,160,67,0.18)',
                color: '#52D47C',
                border: '1px solid rgba(22,160,67,0.4)',
                cursor: 'default',
              }}
            >
              ✅ Отправить
            </button>
            <button
              type="button"
              style={{
                flex: 1,
                padding: '11px 8px',
                borderRadius: 8,
                fontWeight: 700,
                fontSize: 12.5,
                background: 'rgba(249,115,22,0.18)',
                color: '#FBBF24',
                border: '1px solid rgba(249,115,22,0.4)',
                cursor: 'default',
              }}
            >
              ✏️ Исправить
            </button>
            <button
              type="button"
              style={{
                flex: 1,
                padding: '11px 8px',
                borderRadius: 8,
                fontWeight: 700,
                fontSize: 12.5,
                background: 'rgba(239,68,68,0.14)',
                color: '#F87171',
                border: '1px solid rgba(239,68,68,0.35)',
                cursor: 'default',
              }}
            >
              ❌ Отмена
            </button>
          </div>
        </div>

        <div
          style={{
            position: 'absolute',
            bottom: 6,
            left: '50%',
            transform: 'translateX(-50%)',
            width: 120,
            height: 4,
            borderRadius: 2,
            background: 'rgba(255,255,255,0.3)',
          }}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}

function TrapsBlock() {
  return (
    <div
      style={{
        background: '#FEF3C7',
        border: '1px solid rgba(249,115,22,0.28)',
        borderRadius: 16,
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 10,
          background: 'rgba(249,115,22,0.18)',
          color: '#C2410C',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
        aria-hidden="true"
      >
        <AlertTriangle size={18} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 15,
            fontWeight: 800,
            color: '#92400E',
            letterSpacing: '-0.01em',
            marginBottom: 4,
          }}
        >
          Замечает ловушки работодателя
        </div>
        <div style={{ fontSize: 13.5, color: '#78350F', lineHeight: 1.45 }}>
          Скрытые требования в тексте вакансии бот вытаскивает в карточку, чтобы вы не пропустили, и учитывает при составлении сопроводительного.
        </div>
      </div>
    </div>
  );
}
