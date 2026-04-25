'use client';

import { useState, useEffect } from 'react';
import { HERO_CHAT_JOBS } from '@/lib/data/hero-jobs';
import type { JobCard } from '@/lib/types';

interface HeroChatProps {
  jobs?: JobCard[];
  initialSent?: number;
  initialSkipped?: number;
  cycleMs?: number;
}

export function HeroChat({
  jobs = HERO_CHAT_JOBS,
  initialSent = 127,
  initialSkipped = 94,
  cycleMs = 3000,
}: HeroChatProps) {
  const [idx, setIdx] = useState(0);
  const [sent, setSent] = useState(0);
  const [skipped, setSkipped] = useState(0);
  const [response, setResponse] = useState<{ kind: string; text: string } | null>(null);
  const [anim, setAnim] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);

  const job = jobs[idx % jobs.length];

  useEffect(() => {
    if (paused || anim) return;
    const t = setTimeout(() => {
      const auto = Math.random() < 0.7 ? 'apply' : 'skip';
      setAnim(auto === 'apply' ? 'out-right' : 'out-left');
      setResponse({
        kind: auto,
        text: auto === 'apply'
          ? `✅ Отклик отправлен на <b>${job.company}</b>`
          : `⏭ Пропущено. Ищу следующую…`,
      });
      const t2 = setTimeout(() => {
        if (auto === 'apply') setSent(s => s + 1);
        else setSkipped(s => s + 1);
        setIdx(i => (i + 1) % jobs.length);
        setAnim(null);
        const t3 = setTimeout(() => setResponse(null), 900);
        return () => clearTimeout(t3);
      }, 450);
      return () => clearTimeout(t2);
    }, cycleMs);
    return () => clearTimeout(t);
  }, [idx, anim, paused, job.company, cycleMs, jobs.length]);

  const act = (kind: string) => {
    if (anim) return;
    setPaused(true);
    setAnim(kind === 'apply' ? 'out-right' : 'out-left');
    setResponse({
      kind,
      text: kind === 'apply'
        ? `✅ Отклик отправлен на <b>${job.company}</b>`
        : `⏭ Пропущено. Ищу следующую…`,
    });
    const t1 = setTimeout(() => {
      if (kind === 'apply') setSent(s => s + 1);
      else setSkipped(s => s + 1);
      setIdx(i => (i + 1) % jobs.length);
      setAnim(null);
      const t2 = setTimeout(() => {
        setResponse(null);
        setPaused(false);
      }, 1200);
      return () => clearTimeout(t2);
    }, 450);
    return () => clearTimeout(t1);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
      {/* Live counters */}
      <div style={{ display: 'flex', gap: 10, position: 'absolute', top: -6, zIndex: 3 }}>
        <div style={{
          padding: '7px 13px', borderRadius: 999, background: 'rgba(22,163,74,0.12)',
          color: '#15803D', fontWeight: 700, fontSize: 12, display: 'flex', alignItems: 'center', gap: 6,
          border: '1px solid rgba(22,163,74,0.25)',
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="#15803D" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          {initialSent + sent} откликов
        </div>
        <div style={{
          padding: '7px 13px', borderRadius: 999, background: 'rgba(239,68,68,0.1)',
          color: '#B91C1C', fontWeight: 700, fontSize: 12, display: 'flex', alignItems: 'center', gap: 6,
          border: '1px solid rgba(239,68,68,0.2)',
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          {initialSkipped + skipped} пропущено
        </div>
      </div>

      <div style={{
        width: 360, height: 620, borderRadius: 42, background: '#111', padding: 10,
        boxShadow: 'var(--shadow-phone)', position: 'relative',
      }}>
        <div style={{
          width: '100%', height: '100%', borderRadius: 34, overflow: 'hidden',
          background: '#17212B', display: 'flex', flexDirection: 'column', position: 'relative',
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
              background: 'linear-gradient(135deg,#FBBF24,#F97316 33%,#EF4444 66%,#DB2777)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M14 4.1 12 6"/><path d="m5.1 8-2.9-.8"/><path d="m6 12-1.9 2"/><path d="M7.2 2.2 8 5.1"/><path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>
              </svg>
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
              <span style={{ fontWeight: 600, fontSize: 15, color: '#fff' }}>Откликер</span>
              <span style={{ fontSize: 12, color: '#3390EC', fontWeight: 500 }}>бот · онлайн</span>
            </div>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6C7883" strokeWidth="2" aria-hidden="true"><circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/></svg>
          </div>

          {/* Chat area */}
          <div style={{ flex: 1, padding: '10px 10px 8px', display: 'flex', flexDirection: 'column', gap: 6, overflow: 'hidden', position: 'relative' }}>
            <div style={{
              background: '#182533', color: '#fff', padding: '8px 11px 6px',
              borderRadius: 14, borderBottomLeftRadius: 4, fontSize: 12.5, lineHeight: 1.35,
              alignSelf: 'flex-start', maxWidth: '92%',
            }}>
              Нашёл свежую вакансию под твоё резюме 👇
            </div>

            {/* Vacancy card */}
            <div key={idx} style={{
              background: '#182533', color: '#fff', padding: '10px 12px',
              borderRadius: 14, borderBottomLeftRadius: 4, fontSize: 11.5, lineHeight: 1.45,
              alignSelf: 'flex-start', width: '94%', maxHeight: 320, overflow: 'hidden',
              position: 'relative',
              transform: anim === 'out-right' ? 'translateX(130%) rotate(10deg)' :
                         anim === 'out-left'  ? 'translateX(-130%) rotate(-10deg)' : 'none',
              opacity: anim ? 0 : 1,
              transition: 'transform .45s cubic-bezier(.2,.8,.2,1), opacity .35s',
            }}>
              <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6, display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                <span style={{ color: '#FBBF24' }}>▍</span>
                <span>{job.title}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 1.5, marginBottom: 7 }}>
                <div>🏢 <b>{job.company}</b></div>
                <div>💵 {job.salary}</div>
                <div>📍 {job.location}</div>
                <div>💼 {job.schedule}</div>
                <div>🎓 Опыт: {job.experience}</div>
              </div>
              <div style={{ marginTop: 6 }}>
                <div style={{ fontWeight: 700, marginBottom: 2 }}>📋 Обязанности:</div>
                {job.duties?.map((d, i) => <div key={i} style={{ paddingLeft: 2 }}>• {d}</div>)}
              </div>
              <div style={{ marginTop: 6 }}>
                <div style={{ fontWeight: 700, marginBottom: 2 }}>✅ Требования:</div>
                {job.requirements?.map((r, i) => <div key={i} style={{ paddingLeft: 2 }}>• {r}</div>)}
              </div>
              <div style={{
                marginTop: 7, fontSize: 10.5, color: '#6C7883',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span>📅 Опубликовано: 🔥 {job.posted}</span>
                <span style={{ fontVariantNumeric: 'tabular-nums' }}>9:41</span>
              </div>
              <div style={{
                position: 'absolute', left: 0, right: 0, bottom: 0, height: 28,
                background: 'linear-gradient(to bottom, rgba(24,37,51,0), #182533)',
                pointerEvents: 'none',
              }} aria-hidden="true"/>
            </div>

            {/* Match badge */}
            <div style={{
              background: '#182533', color: '#fff', padding: '6px 10px',
              borderRadius: 12, borderBottomLeftRadius: 4, fontSize: 11.5, alignSelf: 'flex-start',
              opacity: anim ? 0.5 : 1, transition: 'opacity .2s',
            }}>
              <b style={{ color: '#FBBF24' }}>{job.match}% match</b> с твоим резюме 🔥
            </div>

            {/* Bot response toast */}
            {response && (
              <div style={{
                background: response.kind === 'apply' ? 'rgba(22,163,74,0.18)' : 'rgba(239,68,68,0.14)',
                border: `1px solid ${response.kind === 'apply' ? 'rgba(22,163,74,0.4)' : 'rgba(239,68,68,0.35)'}`,
                color: '#fff', padding: '8px 11px', borderRadius: 12, fontSize: 12.5,
                alignSelf: 'flex-start', maxWidth: '92%',
              }} dangerouslySetInnerHTML={{ __html: response.text }}/>
            )}
          </div>

          {/* Reply keyboard */}
          <div style={{ padding: '6px 6px 10px', background: '#0E1621', display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0 }}>
            <div style={{ display: 'flex', gap: 4 }}>
              <button
                onClick={() => act('apply')}
                disabled={!!anim}
                style={{
                  flex: 1, padding: '11px 10px', borderRadius: 8, fontWeight: 700, fontSize: 13.5,
                  background: 'rgba(22,160,67,0.18)', color: '#52D47C',
                  border: '1px solid rgba(22,160,67,0.4)', cursor: anim ? 'default' : 'pointer',
                  transition: 'transform .12s',
                }}
              >
                ✅ Откликнуться
              </button>
              <button
                onClick={() => act('skip')}
                disabled={!!anim}
                style={{
                  flex: 1, padding: '11px 10px', borderRadius: 8, fontWeight: 700, fontSize: 13.5,
                  background: 'rgba(239,68,68,0.14)', color: '#F87171',
                  border: '1px solid rgba(239,68,68,0.35)', cursor: anim ? 'default' : 'pointer',
                  transition: 'transform .12s',
                }}
              >
                ❌ Пропустить
              </button>
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              <div style={{ flex: 1, padding: '9px 10px', borderRadius: 8, background: '#223445', color: 'rgba(255,255,255,0.55)', fontSize: 12.5, fontWeight: 600, textAlign: 'center' }}>⚫ В чёрный список</div>
              <div style={{ flex: 1, padding: '9px 10px', borderRadius: 8, background: '#223445', color: 'rgba(255,255,255,0.55)', fontSize: 12.5, fontWeight: 600, textAlign: 'center' }}>🔗 Открыть на HH</div>
            </div>
          </div>

          <div style={{ position: 'absolute', bottom: 6, left: '50%', transform: 'translateX(-50%)', width: 120, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.3)' }} aria-hidden="true"/>
        </div>
      </div>
    </div>
  );
}
