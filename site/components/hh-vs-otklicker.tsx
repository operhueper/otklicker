import { HH_VS_OTKLICKER_PAIRS } from '@/lib/data/hh-vs-otklicker';
import type { HHvsOtklickerPair } from '@/lib/types';

interface HHvsOtklickerProps {
  pairs?: HHvsOtklickerPair[];
}

export function HHvsOtklicker({ pairs = HH_VS_OTKLICKER_PAIRS }: HHvsOtklickerProps) {
  return (
    <section
      id="hh-vs-otklicker"
      aria-labelledby="hh-vs-otklicker-title"
      style={{
        background: 'var(--bg-pastel)',
        padding: '96px 0',
        position: 'relative',
        overflow: 'hidden',
        borderTop: '1px solid var(--line-strong)',
      }}
    >
      <div
        className="halo"
        style={{ width: 520, height: 520, background: '#DB2777', top: -180, left: -120, opacity: 0.12 }}
        aria-hidden="true"
      />
      <div
        className="halo"
        style={{ width: 460, height: 460, background: '#FBBF24', bottom: -160, right: -120, opacity: 0.18 }}
        aria-hidden="true"
      />

      <div className="mx-auto max-w-container px-6" style={{ position: 'relative', zIndex: 2 }}>
        <div style={{ maxWidth: 760, marginBottom: 56 }}>
          <div className="eyebrow">
            <span className="eyebrow-dot" aria-hidden="true" />
            HH.ru в браузере vs откликер в Telegram
          </div>
          <h2
            id="hh-vs-otklicker-title"
            className="text-h2 text-text-heading"
            style={{ margin: '16px 0 18px' }}
          >
            Что вы делаете на HH.ru вручную <br />и что бот делает <span className="grad-text">за вас</span>
          </h2>
          <p style={{ fontSize: 18, color: 'var(--text-sub)', margin: 0, lineHeight: 1.55, maxWidth: 640 }}>
            Поиск, отклик, переписка с HR и аналитика только в Telegram. Без захода на HH.ru с любого устройства.
          </p>
        </div>

        {/* Header row (desktop only) */}
        <div
          className="hh-vs-header"
          aria-hidden="true"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 24,
            marginBottom: 16,
            paddingLeft: 8,
            paddingRight: 8,
          }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: 'var(--text-sub)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}
          >
            HH.ru в браузере
          </div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              background: 'var(--brand-gradient)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              color: 'transparent',
            }}
          >
            откликер в Telegram
          </div>
        </div>

        <ul
          style={{
            listStyle: 'none',
            padding: 0,
            margin: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {pairs.map((pair) => (
            <li
              key={pair.id}
              className="hh-vs-row"
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 24,
                alignItems: 'stretch',
              }}
            >
              <PainCard pair={pair} />
              <AnswerCard pair={pair} />
            </li>
          ))}
        </ul>
      </div>

      <style>{`
        @media (max-width: 960px) {
          .hh-vs-header { display: none !important; }
          .hh-vs-row {
            grid-template-columns: 1fr !important;
            gap: 0 !important;
          }
        }
      `}</style>
    </section>
  );
}

function PainCard({ pair }: { pair: HHvsOtklickerPair }) {
  const Icon = pair.pain.icon;
  return (
    <article
      className="hh-vs-pain"
      style={{
        background: '#F5F5F4',
        border: '1px solid rgba(120,53,15,0.08)',
        borderRadius: 18,
        padding: '22px 24px',
        display: 'flex',
        gap: 14,
        alignItems: 'flex-start',
        position: 'relative',
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 12,
          background: 'rgba(120,53,15,0.08)',
          color: '#78350F',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
        aria-hidden="true"
      >
        <Icon size={20} strokeWidth={2} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: '#A8A29E',
            marginBottom: 6,
          }}
          className="hh-vs-mobile-label"
        >
          HH.ru в браузере
        </div>
        <h3
          style={{
            fontSize: 17,
            fontWeight: 800,
            color: 'var(--text-heading)',
            letterSpacing: '-0.01em',
            margin: '0 0 6px',
            lineHeight: 1.3,
          }}
        >
          {pair.pain.title}
        </h3>
        <p style={{ fontSize: 14.5, color: 'var(--text)', lineHeight: 1.5, margin: 0 }}>{pair.pain.text}</p>
      </div>

      <style>{`
        .hh-vs-pain .hh-vs-mobile-label { display: none; }
        @media (max-width: 960px) {
          .hh-vs-pain { border-radius: 18px 18px 0 0 !important; border-bottom: none !important; }
          .hh-vs-pain .hh-vs-mobile-label { display: block; }
        }
      `}</style>
    </article>
  );
}

function AnswerCard({ pair }: { pair: HHvsOtklickerPair }) {
  const Icon = pair.answer.icon;
  return (
    <article
      className="hh-vs-answer"
      style={{
        background: '#FFFFFF',
        border: '1px solid rgba(249,115,22,0.28)',
        borderRadius: 18,
        padding: '22px 24px',
        display: 'flex',
        gap: 14,
        alignItems: 'flex-start',
        position: 'relative',
        boxShadow: '0 8px 24px rgba(219,39,119,0.08), 0 2px 6px rgba(249,115,22,0.06)',
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 12,
          background: 'var(--brand-gradient)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 6px 16px rgba(219,39,119,0.22)',
        }}
        aria-hidden="true"
      >
        <Icon size={20} strokeWidth={2.2} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            background: 'var(--brand-gradient)',
            WebkitBackgroundClip: 'text',
            backgroundClip: 'text',
            color: 'transparent',
            marginBottom: 6,
          }}
          className="hh-vs-mobile-label"
        >
          откликер в Telegram
        </div>
        <h3
          style={{
            fontSize: 17,
            fontWeight: 800,
            color: 'var(--text-heading)',
            letterSpacing: '-0.01em',
            margin: '0 0 6px',
            lineHeight: 1.3,
          }}
        >
          {pair.answer.title}
        </h3>
        <p style={{ fontSize: 14.5, color: 'var(--text)', lineHeight: 1.5, margin: 0 }}>{pair.answer.text}</p>
      </div>

      <style>{`
        .hh-vs-answer .hh-vs-mobile-label { display: none; }
        @media (max-width: 960px) {
          .hh-vs-answer { border-radius: 0 0 18px 18px !important; margin-bottom: 8px; }
          .hh-vs-answer .hh-vs-mobile-label { display: block; }
        }
      `}</style>
    </article>
  );
}
