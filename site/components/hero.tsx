import { Send, ArrowRight } from 'lucide-react';
import { HeroChat } from './hero-chat';
import { HeroSwipe } from './hero-swipe';

export type HeroVariant = 'chat' | 'swipe';

interface HeroProps {
  variant?: HeroVariant;
}

export function Hero({ variant = 'chat' }: HeroProps) {
  return (
    <section id="top" style={{ paddingTop: 120, paddingBottom: 80, position: 'relative', overflow: 'hidden' }}>
      <div className="halo" style={{ width: 520, height: 520, background: '#FBBF24', top: -120, right: -120 }} aria-hidden="true"/>
      <div className="halo" style={{ width: 420, height: 420, background: '#DB2777', bottom: -140, left: -80, opacity: 0.22 }} aria-hidden="true"/>

      <div className="mx-auto max-w-container px-6" style={{ position: 'relative', zIndex: 2 }}>
        <div className="hero-grid" style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 80, alignItems: 'center' }}>
          {/* Left: copy */}
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" aria-hidden="true"/>
              Telegram-бот для поиска работы на HH.ru
            </div>
            <h1 className="text-h1 text-text-heading" style={{ margin: '22px 0 20px' }}>
              Откликается на<br/>
              <span className="grad-text">свежие вакансии</span><br/>
              за вас.
            </h1>
            <p style={{ fontSize: 19, lineHeight: 1.55, color: 'var(--text-sub)', maxWidth: 540, margin: '0 0 36px' }}>
              Бот следит за лентой HH и отправляет отклик в первые минуты после публикации. Вы — в начале стопки, а не в конце. Резюме, отклики и переписка с HR — в одном Telegram.
            </p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 36 }}>
              <a
                href="https://t.me/otklicker_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
                style={{ padding: '16px 26px', fontSize: 16 }}
              >
                <Send size={18} /> Открыть @otklicker_bot
              </a>
              <a
                href="https://t.me/otklicker"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-ghost"
                style={{ padding: '16px 22px', fontSize: 15 }}
              >
                Канал @otklicker <ArrowRight size={16} />
              </a>
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-sub)', lineHeight: 1.5, maxWidth: 460 }}>
              Авторизация на HH по одноразовому коду. Пароль не запрашиваем и не храним.
            </div>
          </div>

          {/* Right: visual */}
          <div style={{ position: 'relative', minHeight: 540 }}>
            {variant === 'chat' && <HeroChat />}
            {variant === 'swipe' && <HeroSwipe />}
          </div>
        </div>
      </div>

      <style>{`@media (max-width: 960px) { .hero-grid { grid-template-columns: 1fr !important; gap: 48px !important; } }`}</style>
    </section>
  );
}
