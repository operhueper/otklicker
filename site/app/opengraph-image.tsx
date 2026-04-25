import { ImageResponse } from 'next/og';

export const alt = 'откликер — Telegram-бот автооткликов на HH.ru';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          justifyContent: 'center',
          padding: '80px',
          background:
            'linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%)',
          color: '#FFFBF0',
          fontFamily: 'sans-serif',
        }}
      >
        <div
          style={{
            display: 'flex',
            fontSize: 36,
            fontWeight: 600,
            opacity: 0.9,
            marginBottom: 24,
            letterSpacing: '0.02em',
          }}
        >
          Telegram-бот
        </div>
        <div
          style={{
            display: 'flex',
            fontSize: 144,
            fontWeight: 900,
            letterSpacing: '-0.04em',
            lineHeight: 1,
          }}
        >
          откликер
        </div>
        <div
          style={{
            display: 'flex',
            fontSize: 44,
            fontWeight: 600,
            opacity: 0.95,
            marginTop: 32,
            maxWidth: 1000,
            lineHeight: 1.2,
          }}
        >
          Автоотклики на HH.ru за вас
        </div>
        <div
          style={{
            display: 'flex',
            fontSize: 28,
            fontWeight: 500,
            opacity: 0.8,
            marginTop: 24,
            maxWidth: 1000,
            lineHeight: 1.3,
          }}
        >
          @otklicker_bot · резюме за 7-10 минут · переписка с HR в Telegram
        </div>
      </div>
    ),
    { ...size },
  );
}
