'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { HERO_CHAT_JOBS } from '@/lib/data/hero-jobs';
import type { JobCard } from '@/lib/types';

interface HeroChatProps {
  jobs?: JobCard[];
  cycleMs?: number;
}

function letterPreview(job: JobCard): string {
  const t = job.title.toLowerCase();
  const exp = job.experience ? job.experience.toLowerCase() : 'релевантного';
  switch (job.title) {
    case 'Руководитель отдела продаж':
      return `«Здравствуйте! По вакансии руководителя отдела продаж: 4 года управления командой 8 человек, рост выручки на 34%...»`;
    case 'Senior Product Designer':
      return `«Здравствуйте! По вакансии Senior Product Designer: 5 лет в B2C, 3 кейса с ростом метрик на 20%+...»`;
    case 'Шеф-повар горячего цеха':
      return `«Здравствуйте! По вакансии шеф-повара: 6 лет на горячем цеху, команда 5 поваров, авторское меню из 24 блюд...»`;
    case 'Менеджер по продажам B2B':
      return `«Здравствуйте! По вакансии менеджера B2B: 3 года активных продаж, средний чек 480 тыс ₽, желаемая ЗП от 110 тыс...»`;
    case 'Lead UX Designer':
      return `«Финтех 2026. По вакансии Lead UX Designer: 6 лет в продукте, тимлид 4 дизайнеров, 2 года в финтехе...»`;
    case 'Медсестра процедурного кабинета':
      return `«Здравствуйте! По вакансии медсестры: 4 года в клинике, действующий сертификат до 2028, санкнижка в порядке...»`;
    case 'Бариста':
      return `«Здравствуйте! По вакансии бариста: кофе пью 8 лет, прошёл курс латте-арт, готов учиться на месте...»`;
    case 'Товаровед':
      return `«Здравствуйте! По вакансии товароведа: 3 года в сети, 1С Торговля 11, приёмка и инвентаризация ежедневно...»`;
    case 'РОП в онлайн-школе':
      return `«Здравствуйте! По вакансии РОП в EdTech: 3 года в онлайн-школе, рост конверсии в оплату с 8% до 17%...»`;
    case 'Водитель категории E':
      return `«Здравствуйте! По вакансии водителя E: стаж 7 лет, опыт вахт 15/15 по 2 года, тахограф и карта в порядке...»`;
    default:
      return `«По вакансии ${t}: ${exp} опыта, готов обсудить детали...»`;
  }
}

export function HeroChat({
  jobs = HERO_CHAT_JOBS,
  cycleMs = 3000,
}: HeroChatProps) {
  const [idx, setIdx] = useState(0);
  const [response, setResponse] = useState<{ kind: string; text: string } | null>(null);
  const [anim, setAnim] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const job = jobs[idx % jobs.length];

  const clearAllTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  }, []);

  useEffect(() => {
    if (paused || anim) return;
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const t1 = setTimeout(() => {
      const r = Math.random();
      const auto: 'apply' | 'skip' | 'voice-edit' =
        r < 0.6 ? 'apply' : r < 0.85 ? 'voice-edit' : 'skip';

      if (auto === 'voice-edit') {
        // Этап 1: показать "Слушаю правки…" на 1500ms (карточка не уезжает)
        setResponse({ kind: 'voice-listening', text: '' });
        const tv1 = setTimeout(() => {
          // Этап 2: показать toast о переформулировке на 450ms
          setResponse({ kind: 'voice-done', text: '✓ Переформулировал в формальный тон' });
          setAnim('out-right');
          const tv2 = setTimeout(() => {
            setIdx(i => (i + 1) % jobs.length);
            setAnim(null);
            const tv3 = setTimeout(() => setResponse(null), 900);
            timersRef.current.push(tv3);
          }, 450);
          timersRef.current.push(tv2);
        }, 1500);
        timersRef.current.push(tv1);
        return;
      }

      setAnim(auto === 'apply' ? 'out-right' : 'out-left');
      setResponse({
        kind: auto,
        text: auto === 'apply'
          ? `✅ Отклик отправлен на <b>${job.company}</b>`
          : `⏭ Пропущено. Ищу следующую…`,
      });
      const t2 = setTimeout(() => {
        setIdx(i => (i + 1) % jobs.length);
        setAnim(null);
        const t3 = setTimeout(() => setResponse(null), 900);
        timersRef.current.push(t3);
      }, 450);
      timersRef.current.push(t2);
    }, cycleMs);
    timersRef.current.push(t1);

    // Cleanup только внешнего t1: при смене anim/paused React дёргает cleanup,
    // и если бы тут был clearAllTimers — он бы убил t2/t3 от текущего цикла
    // и таймеры из act() (клик), что приводит к dead-lock'у anim="out-right".
    return () => clearTimeout(t1);
  }, [idx, anim, paused, job.company, cycleMs, jobs.length]);

  // Безопасная очистка всех таймеров на размонтирование.
  useEffect(() => () => clearAllTimers(), [clearAllTimers]);

  const act = useCallback((kind: string) => {
    if (anim) return;
    clearAllTimers();
    setPaused(true);
    setAnim(kind === 'apply' ? 'out-right' : 'out-left');
    setResponse({
      kind,
      text: kind === 'apply'
        ? `✅ Отклик отправлен на <b>${job.company}</b>`
        : `⏭ Пропущено. Ищу следующую…`,
    });
    const t1 = setTimeout(() => {
      setIdx(i => (i + 1) % jobs.length);
      setAnim(null);
      const t2 = setTimeout(() => {
        setResponse(null);
        setPaused(false);
      }, 1200);
      timersRef.current.push(t2);
    }, 450);
    timersRef.current.push(t1);
  }, [anim, job.company, jobs.length, clearAllTimers]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
      <div style={{
        width: '100%', maxWidth: 360, aspectRatio: '360 / 620', borderRadius: 42, background: '#111', padding: 10,
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
              {job.trap && (
                <div style={{
                  marginTop: 8, padding: '8px 10px', borderRadius: 10,
                  background: 'rgba(251,191,36,0.18)',
                  border: '1px solid rgba(251,191,36,0.35)',
                  display: 'flex', flexDirection: 'column', gap: 3,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, fontWeight: 700, color: '#FBBF24' }}>
                    <span aria-hidden="true">🚨</span>
                    <span>Ловушка для невнимательных</span>
                  </div>
                  <div style={{ fontSize: 11, lineHeight: 1.4, color: '#E0DFDC', fontStyle: 'italic' }}>
                    {job.trap}
                  </div>
                </div>
              )}
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

            {/* Letter ready message — показываем когда нет toast о решении */}
            {(!response || response.kind === 'voice-listening') && (
              <div style={{
                background: '#182533', color: '#fff', padding: '10px 12px',
                borderRadius: 14, borderBottomLeftRadius: 4, fontSize: 11.5,
                alignSelf: 'flex-start', maxWidth: '94%',
                opacity: anim ? 0.5 : 1, transition: 'opacity .2s',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5, fontSize: 11, fontWeight: 700, color: '#FBBF24' }}>
                  <span aria-hidden="true">✍</span>
                  <span>Письмо готово, учёл ловушку</span>
                </div>
                <div style={{ fontSize: 10.5, lineHeight: 1.45, color: '#A8B3BD', marginBottom: 6, fontStyle: 'italic' }}>
                  {letterPreview(job)}
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <span style={{
                    flex: 1, padding: '6px 8px', borderRadius: 8, textAlign: 'center',
                    background: 'rgba(22,160,67,0.18)', color: '#52D47C',
                    border: '1px solid rgba(22,160,67,0.4)', fontSize: 11, fontWeight: 700,
                  }}>📨 Отправить</span>
                  <span style={{
                    flex: 1, padding: '6px 8px', borderRadius: 8, textAlign: 'center',
                    background: 'rgba(251,191,36,0.18)', color: '#FBBF24',
                    border: '1px solid rgba(251,191,36,0.4)', fontSize: 11, fontWeight: 700,
                  }}>🎤 Поправить</span>
                  <span style={{
                    flex: 1, padding: '6px 8px', borderRadius: 8, textAlign: 'center',
                    background: 'rgba(168,179,189,0.12)', color: '#A8B3BD',
                    border: '1px solid rgba(168,179,189,0.3)', fontSize: 11, fontWeight: 700,
                  }}>✕ Отмена</span>
                </div>
              </div>
            )}

            {/* Voice listening pulse */}
            {response?.kind === 'voice-listening' && (
              <div style={{
                background: 'rgba(251,191,36,0.14)',
                border: '1px solid rgba(251,191,36,0.4)',
                color: '#FBBF24', padding: '8px 11px', borderRadius: 12, fontSize: 12,
                alignSelf: 'flex-start', maxWidth: '92%',
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                <div style={{ display: 'flex', gap: 3, alignItems: 'center' }}>
                  {[0,1,2,3,4].map(i => (
                    <div key={i} style={{
                      width: 3, height: 6 + (i % 3) * 5, borderRadius: 2,
                      background: '#FBBF24',
                      animation: `voice-pulse 0.8s ease-in-out ${i * 0.1}s infinite`,
                    }}/>
                  ))}
                </div>
                <span style={{ fontWeight: 700 }}>Слушаю правки…</span>
              </div>
            )}

            {/* Bot response toast (apply / skip / voice-done) */}
            {response && response.kind !== 'voice-listening' && (
              <div style={{
                background: response.kind === 'apply' || response.kind === 'voice-done'
                  ? 'rgba(22,163,74,0.18)'
                  : 'rgba(239,68,68,0.14)',
                border: `1px solid ${response.kind === 'apply' || response.kind === 'voice-done'
                  ? 'rgba(22,163,74,0.4)'
                  : 'rgba(239,68,68,0.35)'}`,
                color: '#fff', padding: '8px 11px', borderRadius: 12, fontSize: 12.5,
                alignSelf: 'flex-start', maxWidth: '92%',
              }} dangerouslySetInnerHTML={{ __html: response.text }}/>
            )}
          </div>
          <style>{`@keyframes voice-pulse { 0%, 100% { transform: scaleY(0.6); } 50% { transform: scaleY(1.4); } }`}</style>

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
