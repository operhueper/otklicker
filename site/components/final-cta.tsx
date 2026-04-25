import { Send } from 'lucide-react';

export function FinalCTA() {
  return (
    <section style={{ padding: '80px 0 40px', background: 'var(--bg)' }}>
      <div className="mx-auto max-w-container px-6">
        <div style={{
          borderRadius: 32, padding: '64px 48px',
          background: 'var(--brand-gradient-text)',
          color: '#fff', position: 'relative', overflow: 'hidden',
          display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 20,
          boxShadow: '0 30px 80px rgba(219,39,119,0.25)',
        }}>
          <div style={{ position: 'absolute', top: -80, right: -80, width: 300, height: 300, borderRadius: '50%', background: 'rgba(255,255,255,0.15)', filter: 'blur(40px)' }} aria-hidden="true"/>
          <div style={{ position: 'absolute', bottom: -60, left: -60, width: 220, height: 220, borderRadius: '50%', background: 'rgba(251, 191, 36, 0.3)', filter: 'blur(40px)' }} aria-hidden="true"/>

          <div style={{ position: 'relative', zIndex: 2, maxWidth: 720 }}>
            <h2 style={{ fontSize: 'clamp(36px, 4.4vw, 56px)', fontWeight: 900, letterSpacing: '-0.03em', lineHeight: 1.05, margin: '0 0 16px' }}>
              Свежая вакансия<br/>ждать не будет
            </h2>
            <p style={{ fontSize: 18, opacity: 0.9, margin: '0 0 28px', maxWidth: 520, marginLeft: 'auto', marginRight: 'auto' }}>
              Запустите @otklicker_bot — пока вы читаете эту страницу, бот уже мог бы отправить отклик.
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <a
                href="https://t.me/otklicker_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="btn"
                style={{ padding: '18px 32px', fontSize: 17, background: '#FFFFFF', color: '#DB2777', boxShadow: '0 16px 40px rgba(0,0,0,0.16)' }}
              >
                <Send size={20}/> Открыть @otklicker_bot
              </a>
              <a
                href="https://t.me/otklicker"
                target="_blank"
                rel="noopener noreferrer"
                className="btn"
                style={{ padding: '18px 28px', fontSize: 16, background: 'rgba(255,255,255,0.15)', color: '#fff', border: '1px solid rgba(255,255,255,0.3)' }}
              >
                Канал @otklicker
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
