'use client';

import { useState, useEffect, useRef } from 'react';
import {
  PLAY_MS,
  clock,
  pct,
  progressToMinute,
  BOT_BEATS,
  MANUAL_BEATS,
  HOUR_TICKS,
  type Beat,
  type HourTick,
} from '@/lib/speed/timeline';

export function SpeedSection() {
  const [progress, setProgress] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [hasAutoplayed, setHasAutoplayed] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);
  const rafRef = useRef<number>(0);
  const startTsRef = useRef<number | null>(null);

  // Auto-play once on scroll into view
  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const reducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting && !hasAutoplayed) {
          if (!reducedMotion) setPlaying(true);
          setHasAutoplayed(true);
        }
      });
    }, { threshold: 0.35 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [hasAutoplayed]);

  // Animation loop — progress intentionally omitted from deps (used only to seed startTsRef on first call)
  useEffect(() => {
    if (!playing) return;
    const step = (ts: number) => {
      if (startTsRef.current == null) startTsRef.current = ts - progress * PLAY_MS;
      const elapsed = ts - startTsRef.current;
      const p = Math.min(1, elapsed / PLAY_MS);
      setProgress(p);
      if (p < 1) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        setPlaying(false);
        startTsRef.current = null;
      }
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(rafRef.current);
      startTsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing]);

  const minute = progressToMinute(progress);
  const playheadPct = pct(minute);

  const replay = () => {
    setProgress(0);
    startTsRef.current = null;
    setPlaying(true);
  };

  return (
    <section id="speed" ref={sectionRef} style={{
      background: 'var(--bg)', paddingTop: 96, paddingBottom: 96,
      borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)',
      position: 'relative', overflow: 'hidden',
    }}>
      <div className="halo" style={{ width: 480, height: 480, background: '#FBBF24', top: -180, left: '50%', transform: 'translateX(-50%)', opacity: 0.18 }} aria-hidden="true"/>

      <div className="mx-auto max-w-container px-6" style={{ position: 'relative', zIndex: 2 }}>
        <div style={{ maxWidth: 760, marginBottom: 48 }}>
          <div className="eyebrow"><span className="eyebrow-dot" aria-hidden="true"/>Скорость</div>
          <h2 className="text-h2 text-text-heading" style={{ margin: '16px 0 18px' }}>
            Проверяет HH каждые 15 минут.<br/>Письмо готово к отправке <span className="grad-text">моментально</span>.
          </h2>
          <p style={{ fontSize: 18, color: 'var(--text-sub)', margin: 0, lineHeight: 1.55, maxWidth: 620 }}>
            Бот мониторит свежие вакансии 24/7. Окно 9:00–21:00 по МСК настраивается, чтобы HR не получал отклик ночью. Готовое письмо приходит в Telegram, без захода на HH.
          </p>
        </div>

        {/* Race board */}
        <div className="race-board" style={{
          background: '#FFFFFF', border: '1px solid var(--line)', borderRadius: 28,
          padding: '28px 32px 26px',
          boxShadow: '0 1px 2px rgba(120,53,15,0.04), 0 16px 40px rgba(120,53,15,0.06)',
        }}>
          {/* Top bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 14, marginBottom: 24, flexWrap: 'wrap' }}>
            <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 18, fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '0.02em', fontVariantNumeric: 'tabular-nums' }}>
              {clock(minute)}
            </div>
            <button onClick={replay} style={{
              padding: '8px 14px', borderRadius: 999, background: 'var(--bg-pastel)',
              color: 'var(--text-heading)', border: '1px solid var(--line-strong)',
              fontSize: 13, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 8,
              cursor: 'pointer',
            }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
              </svg>
              Заново
            </button>
          </div>

          <RaceTrack minute={minute} playheadPct={playheadPct} />
        </div>

        {/* Stat strip */}
        <div className="speed-stats" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginTop: 20 }}>
          <StatTile value="~10 мин" label="от публикации до вашего отклика"/>
          <StatTile value="24 / 7" label="мониторинг ленты HH без перерыва"/>
          <FiltersTile/>
        </div>
      </div>

      <style>{`
        @media (max-width: 860px) { .speed-stats { grid-template-columns: 1fr !important; } }
        @media (max-width: 720px) { .race-board { padding: 22px 18px 20px !important; border-radius: 22px !important; } }
      `}</style>
    </section>
  );
}

function RaceTrack({ minute, playheadPct }: { minute: number; playheadPct: number }) {
  return (
    <div style={{ position: 'relative' }}>
      <Lane kind="bot" title="Откликер" subtitle="видит вакансию и пишет письмо" minute={minute} beats={BOT_BEATS}/>
      <TimeAxis minute={minute} playheadPct={playheadPct}/>
      <Lane kind="manual" title="Вручную" subtitle="откроете HH утром, ваш отклик в конце ленты" minute={minute} beats={MANUAL_BEATS}/>
      <Playhead playheadPct={playheadPct}/>
    </div>
  );
}

function Lane({ kind, title, subtitle, minute, beats }: { kind: string; title: string; subtitle: string; minute: number; beats: Beat[] }) {
  const isBot = kind === 'bot';
  const triggered = beats.filter(b => minute >= b.t);
  const fillToPct = triggered.length === 0 ? 0 : pct(triggered[triggered.length - 1].t);
  const sleepEnd = pct(720);

  return (
    <div className="race-lane" style={{ position: 'relative', display: 'grid', gridTemplateColumns: '200px 1fr', gap: 20, alignItems: 'stretch' }}>
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '18px 0', gap: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: isBot ? 'var(--brand-gradient)' : 'rgba(168,162,158,0.25)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            color: isBot ? '#fff' : '#78716C',
            boxShadow: isBot ? '0 6px 14px rgba(219,39,119,0.25)' : 'none',
          }}>
            {isBot ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            )}
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, letterSpacing: '-0.01em', color: 'var(--text-heading)' }}>{title}</div>
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--text-sub)', lineHeight: 1.4, paddingLeft: 38 }}>{subtitle}</div>
      </div>

      <div style={{ position: 'relative', height: 132, padding: '16px 0' }}>
        <div style={{
          position: 'absolute', left: 0, right: 0, top: 24, bottom: 24,
          background: isBot ? 'linear-gradient(90deg, rgba(251,191,36,0.06), rgba(219,39,119,0.04))' : 'rgba(168,162,158,0.06)',
          borderRadius: 16, border: '1px solid var(--line)',
        }}/>

        {!isBot && (
          <div style={{
            position: 'absolute', left: 0, top: 24, bottom: 24,
            width: `${sleepEnd}%`,
            background: 'repeating-linear-gradient(135deg, rgba(168,162,158,0.10) 0 8px, rgba(168,162,158,0.04) 8px 16px)',
            borderRadius: '16px 0 0 16px',
            display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none',
          }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(120,113,108,0.7)', letterSpacing: '0.18em', textTransform: 'uppercase', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
              ночь
            </div>
          </div>
        )}

        <div style={{
          position: 'absolute', left: 0, top: 24, bottom: 24,
          width: `${fillToPct}%`,
          background: isBot ? 'linear-gradient(90deg, rgba(251,191,36,0.32), rgba(249,115,22,0.32) 50%, rgba(219,39,119,0.32))' : 'rgba(120,113,108,0.18)',
          borderRadius: 16,
          transition: 'width 0.4s cubic-bezier(0.4,0,0.2,1)',
          boxShadow: isBot ? 'inset 0 0 0 1px rgba(249,115,22,0.25)' : 'none',
        }}/>

        {beats.map((b, i) => (
          <BeatMarker key={i} beat={b} triggered={minute >= b.t} isBot={isBot}/>
        ))}
      </div>
    </div>
  );
}

function BeatMarker({ beat, triggered, isBot }: { beat: Beat; triggered: boolean; isBot: boolean }) {
  const left = pct(beat.t);
  const cardAlign = left > 78 ? 'right' : left < 12 ? 'left' : 'center';
  const transformX = cardAlign === 'right' ? 'translateX(-100%)' : cardAlign === 'left' ? 'translateX(0)' : 'translateX(-50%)';
  const winColor = beat.emphasis === 'win' ? '#15803D' : beat.emphasis === 'lose' ? '#B91C1C' : null;

  return (
    <div style={{ position: 'absolute', left: `${left}%`, top: 0, bottom: 0, width: 0, pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute', left: 0,
        top: isBot ? 'auto' : 24, bottom: isBot ? 24 : 'auto',
        width: 1, height: 18,
        background: triggered ? (isBot ? 'rgba(249,115,22,0.5)' : 'rgba(120,113,108,0.4)') : 'rgba(168,162,158,0.25)',
        transform: 'translateX(-0.5px)', transition: 'background 0.4s',
      }}/>
      <div style={{
        position: 'absolute', left: 0, top: '50%',
        transform: 'translate(-50%, -50%)',
        width: triggered ? 18 : 12, height: triggered ? 18 : 12,
        borderRadius: 999,
        background: triggered ? (winColor || (isBot ? '#F97316' : '#78716C')) : '#fff',
        border: triggered ? '3px solid #fff' : `2px dashed ${isBot ? 'rgba(249,115,22,0.4)' : 'rgba(120,113,108,0.4)'}`,
        boxShadow: triggered ? (winColor === '#15803D' ? '0 0 0 4px rgba(22,163,74,0.18), 0 6px 14px rgba(22,163,74,0.25)' : winColor === '#B91C1C' ? '0 0 0 4px rgba(239,68,68,0.18), 0 6px 14px rgba(239,68,68,0.25)' : isBot ? '0 0 0 4px rgba(249,115,22,0.18), 0 6px 14px rgba(249,115,22,0.30)' : '0 0 0 4px rgba(120,113,108,0.15)') : 'none',
        transition: 'all 0.35s', zIndex: 3,
      }}/>
      <div style={{
        position: 'absolute', left: 0,
        top: isBot ? 'auto' : 'calc(50% + 22px)',
        bottom: isBot ? 'calc(50% + 22px)' : 'auto',
        transform: transformX,
        minWidth: 130,
        maxWidth: cardAlign === 'right' ? 170 : 220,
        padding: '8px 12px', borderRadius: 12,
        background: triggered ? '#fff' : 'transparent',
        border: triggered ? `1px solid ${winColor ? winColor + '40' : 'var(--line)'}` : '1px dashed rgba(168,162,158,0.35)',
        boxShadow: triggered ? '0 2px 6px rgba(120,53,15,0.06), 0 8px 18px rgba(120,53,15,0.05)' : 'none',
        opacity: triggered ? 1 : 0.5,
        transition: 'all 0.4s',
        textAlign: cardAlign === 'right' ? 'right' : 'left',
        pointerEvents: 'auto',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 800,
          color: winColor || (triggered ? (isBot ? '#C2410C' : '#57534E') : 'var(--text-muted)'),
          letterSpacing: '0.04em', fontVariantNumeric: 'tabular-nums', marginBottom: 2,
          justifyContent: cardAlign === 'right' ? 'flex-end' : 'flex-start',
        }}>
          {beat.emphasis === 'win' && triggered && (
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
          )}
          {beat.emphasis === 'lose' && triggered && (
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          )}
          {clock(beat.t)}
        </div>
        <div style={{ fontSize: 13, fontWeight: 700, color: triggered ? 'var(--text-heading)' : 'var(--text-muted)', lineHeight: 1.25, letterSpacing: '-0.005em', marginBottom: 2 }}>{beat.title}</div>
        <div style={{ fontSize: 11.5, color: triggered ? 'var(--text-sub)' : 'var(--text-muted)', lineHeight: 1.35, opacity: 0.9 }}>{beat.sub}</div>
      </div>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function TimeAxis({ minute, playheadPct: _playheadPct }: { minute: number; playheadPct: number }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 20, margin: '4px 0' }}>
      <div/>
      <div style={{ position: 'relative', height: 28 }}>
        <div style={{ position: 'absolute', left: 0, right: 0, top: '50%', height: 1, background: 'var(--line-strong)', transform: 'translateY(-50%)' }}/>
        {(HOUR_TICKS as HourTick[]).map((tick, i) => {
          const passed = minute >= tick.t;
          const isMidnight = tick.weight === 'midnight';
          const isStrong = tick.weight === 'strong';
          return (
            <div key={i} style={{
              position: 'absolute', left: `${pct(tick.t)}%`, top: '50%',
              transform: 'translate(-50%, -50%)',
              display: 'flex', alignItems: 'center', gap: 6, padding: '2px 8px',
              borderRadius: 999, background: '#fff',
              border: `1px solid ${isStrong ? 'var(--line-strong)' : 'var(--line)'}`,
              fontSize: 10.5, fontWeight: 700,
              color: passed ? 'var(--text-heading)' : 'var(--text-muted)',
              letterSpacing: '0.04em', fontVariantNumeric: 'tabular-nums', transition: 'color 0.3s',
            }}>
              {isMidnight && <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>}
              {tick.label}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Playhead({ playheadPct }: { playheadPct: number }) {
  return (
    <div style={{ position: 'absolute', left: 'calc(200px + 20px)', right: 0, top: 0, bottom: 0, pointerEvents: 'none' }} aria-hidden="true">
      <div style={{ position: 'absolute', left: `${playheadPct}%`, top: 0, bottom: 0, width: 0, transform: 'translateX(-50%)' }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0, width: 2,
          background: 'linear-gradient(to bottom, rgba(249,115,22,0) 0%, rgba(249,115,22,0.5) 10%, rgba(219,39,119,0.5) 90%, rgba(219,39,119,0) 100%)',
          transform: 'translateX(-1px)',
        }}/>
      </div>
    </div>
  );
}

function StatTile({ value, label }: { value: string; label: string }) {
  return (
    <div style={{ background: 'var(--bg-pastel)', border: '1px solid var(--line)', borderRadius: 20, padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ fontSize: 38, fontWeight: 900, color: 'var(--text-heading)', letterSpacing: '-0.02em', lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>{value}</div>
      <div style={{ fontSize: 14, color: 'var(--text-sub)', lineHeight: 1.4 }}>{label}</div>
    </div>
  );
}

function FiltersTile() {
  const chips = [
    { label: 'от 150 000 ₽',  kind: 'money' },
    { label: 'Удалённо',       kind: 'format' },
    { label: 'Москва',         kind: 'geo' },
    { label: 'Опыт 1–3',      kind: 'exp' },
    { label: '9:00–21:00',  kind: 'time' },
    { label: 'Стоп-слова',    kind: 'filter' },
    { label: 'Стиль письма',  kind: 'filter' },
    { label: 'Режим откликов', kind: 'filter' },
  ];

  type ChipStyle = { bg: string; color: string; border: string };
  const chipColor = (kind: string): ChipStyle => {
    switch (kind) {
      case 'money': return { bg: 'rgba(22,163,74,0.10)',  color: '#15803D', border: 'rgba(22,163,74,0.25)' };
      case 'neg':   return { bg: 'rgba(239,68,68,0.08)',  color: '#B91C1C', border: 'rgba(239,68,68,0.22)' };
      case 'time':  return { bg: 'rgba(249,115,22,0.10)', color: '#C2410C', border: 'rgba(249,115,22,0.25)' };
      default:      return { bg: '#fff', color: 'var(--text-heading)', border: 'var(--line-strong)' };
    }
  };

  return (
    <div style={{ background: 'var(--bg-pastel)', border: '1px solid var(--line)', borderRadius: 20, padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 12, position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--text-heading)', letterSpacing: '-0.01em', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
          Фильтры бота
        </div>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-sub)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>настраивается</div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 2 }}>
        {chips.map((c, i) => {
          const s = chipColor(c.kind);
          return (
            <span key={i} style={{
              display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 9px',
              borderRadius: 999, background: s.bg, color: s.color,
              border: `1px solid ${s.border}`, fontSize: 11.5, fontWeight: 600,
              fontVariantNumeric: 'tabular-nums', lineHeight: 1.2, whiteSpace: 'nowrap',
            }}>
              {c.kind === 'neg' && (
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              )}
              {c.label}
            </span>
          );
        })}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-sub)', lineHeight: 1.4, paddingTop: 4 }}>
        Бот откликается только на вакансии, которые подходят по вашим правилам
      </div>
    </div>
  );
}
