import type { BotScreen, BotMessage, KeyboardRow, KeyboardButton } from '@/lib/types';

interface RealBotScreenProps extends BotScreen {
  width?: number;
  height?: number;
}

function KbdButton({ emoji, label, primary, accent, flex }: KeyboardButton & { flex?: boolean }) {
  const bg =
    accent === 'green' ? 'rgba(46, 160, 67, 0.1)' :
    accent === 'red'   ? 'rgba(239, 68, 68, 0.1)' :
    primary            ? 'rgba(219, 39, 119, 0.14)' :
    '#223445';
  const border =
    accent === 'green' ? '1px solid rgba(46,160,67,0.3)' :
    accent === 'red'   ? '1px solid rgba(239,68,68,0.3)' :
    primary            ? '1px solid rgba(219, 39, 119, 0.4)' :
    '1px solid transparent';
  return (
    <div style={{
      background: bg,
      color: '#fff',
      borderRadius: 8,
      padding: '11px 12px',
      fontSize: 14,
      fontWeight: 600,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 6,
      flex: flex ? 1 : undefined,
      border,
    }}>
      {emoji && <span style={{ fontSize: 15 }}>{emoji}</span>}
      <span>{label}</span>
    </div>
  );
}

function MessageBubble({ msg }: { msg: BotMessage }) {
  const isOut = msg.side === 'out';
  const isForwarded = msg.kind === 'forwarded';
  const isPreview = msg.kind === 'preview';

  const bg = isOut ? '#2B5278' : isPreview ? '#1F3247' : '#182533';
  const accent = isForwarded ? '#3390EC' : isPreview ? '#FBBF24' : null;

  return (
    <div style={{
      background: bg,
      color: '#fff',
      padding: '10px 12px 8px',
      borderRadius: 14,
      borderBottomLeftRadius: isOut ? 14 : 4,
      borderBottomRightRadius: isOut ? 4 : 14,
      borderLeft: accent ? `3px solid ${accent}` : 'none',
      fontSize: 13.5,
      lineHeight: 1.45,
      position: 'relative',
      alignSelf: isOut ? 'flex-end' : 'flex-start',
      maxWidth: '88%',
      paddingRight: 44,
    }}>
      {msg.author && (
        <div style={{ fontSize: 12, fontWeight: 600, color: accent ?? '#3390EC', marginBottom: 4 }}>
          {msg.author}
        </div>
      )}
      <div dangerouslySetInnerHTML={{ __html: msg.content }} />
      {msg.time && (
        <span style={{ position: 'absolute', right: 10, bottom: 5, fontSize: 11, color: '#6C7883', fontWeight: 500 }}>{msg.time}</span>
      )}
    </div>
  );
}

export function RealBotScreen({ content, messages, buttons = [], time = '06:32', width = 360, height = 620, header }: RealBotScreenProps) {
  const peerName = header?.name ?? 'Откликер';
  const peerSub = header?.subtitle ?? 'бот · онлайн';

  return (
    <div style={{
      width,
      height,
      borderRadius: 42,
      background: '#111',
      padding: 10,
      boxShadow: 'var(--shadow-phone)',
      position: 'relative',
      flexShrink: 0,
    }}>
      <div style={{
        width: '100%',
        height: '100%',
        borderRadius: 34,
        overflow: 'hidden',
        background: '#17212B',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}>
        {/* Status bar */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 34,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 26px', color: '#fff', fontWeight: 600, fontSize: 13, zIndex: 10,
        }}>
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>9:41</span>
          <div style={{ position: 'absolute', left: '50%', top: 8, transform: 'translateX(-50%)', width: 110, height: 26, background: '#000', borderRadius: 20 }}/>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="16" height="10" viewBox="0 0 16 10" fill="#fff" aria-hidden="true"><rect x="0" y="7" width="3" height="3" rx="0.5"/><rect x="4" y="5" width="3" height="5" rx="0.5"/><rect x="8" y="2" width="3" height="8" rx="0.5"/><rect x="12" y="0" width="3" height="10" rx="0.5"/></svg>
            <svg width="26" height="12" viewBox="0 0 26 12" fill="none" aria-hidden="true"><rect x="0.5" y="0.5" width="22" height="11" rx="2.5" stroke="#fff" opacity="0.5"/><rect x="2" y="2" width="19" height="8" rx="1.2" fill="#fff"/><rect x="23" y="3.5" width="1.5" height="5" rx="0.5" fill="#fff" opacity="0.5"/></svg>
          </div>
        </div>

        {/* Header */}
        <div style={{
          marginTop: 34, background: '#212D3B', padding: '10px 14px',
          display: 'flex', alignItems: 'center', gap: 10,
          borderBottom: '1px solid rgba(255,255,255,0.04)', flexShrink: 0,
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6C7883" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>
          <div style={{
            width: 36, height: 36, borderRadius: 999,
            background: 'linear-gradient(135deg, #FBBF24, #F97316 33%, #EF4444 66%, #DB2777)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M14 4.1 12 6"/><path d="m5.1 8-2.9-.8"/><path d="m6 12-1.9 2"/><path d="M7.2 2.2 8 5.1"/><path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>
            </svg>
          </div>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
            <span style={{ fontWeight: 600, fontSize: 15, color: '#fff' }}>{peerName}</span>
            <span style={{ fontSize: 12, color: '#3390EC', fontWeight: 500 }}>{peerSub}</span>
          </div>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6C7883" strokeWidth="2" aria-hidden="true"><circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/></svg>
        </div>

        {/* Scroll area */}
        <div style={{ flex: 1, padding: '14px 10px 10px', display: 'flex', flexDirection: 'column', gap: 8, overflow: 'hidden' }}>
          {messages && messages.length > 0 ? (
            messages.map((m, i) => <MessageBubble key={i} msg={m} />)
          ) : content ? (
            <div style={{
              background: '#182533',
              color: '#fff',
              padding: '12px 14px 10px',
              borderRadius: 14,
              borderBottomLeftRadius: 4,
              fontSize: 13.5,
              lineHeight: 1.45,
              position: 'relative',
              alignSelf: 'flex-start',
              maxWidth: '92%',
            }}>
              <div dangerouslySetInnerHTML={{ __html: content }}/>
              <span style={{ position: 'absolute', right: 10, bottom: 6, fontSize: 11, color: '#6C7883', fontWeight: 500 }}>{time}</span>
            </div>
          ) : null}
        </div>

        {/* Reply keyboard */}
        <div style={{
          background: '#0E1621',
          padding: '6px 6px 10px',
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
          borderTop: '1px solid rgba(255,255,255,0.04)',
        }}>
          {(buttons as KeyboardRow[]).map((row, i) => {
            if (Array.isArray(row)) {
              return (
                <div key={i} style={{ display: 'flex', gap: 4 }}>
                  {(row as KeyboardButton[]).map((b, j) => <KbdButton key={j} {...b} flex />)}
                </div>
              );
            }
            return <KbdButton key={i} {...(row as KeyboardButton)} />;
          })}
        </div>

        {/* Home bar */}
        <div style={{
          position: 'absolute', bottom: 6, left: '50%', transform: 'translateX(-50%)',
          width: 120, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.3)',
        }} aria-hidden="true" />
      </div>
    </div>
  );
}
