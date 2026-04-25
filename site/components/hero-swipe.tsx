'use client';

import { useState, useEffect } from 'react';
import { SAMPLE_JOBS } from '@/lib/data/sample-jobs';
import type { JobCard } from '@/lib/types';

interface HeroSwipeProps {
  jobs?: JobCard[];
  cycleMs?: number;
}

function SwipeJobCard({ job, style }: { job: JobCard; style: React.CSSProperties }) {
  return (
    <div style={{
      position: 'absolute', inset: 0, background: '#fff', borderRadius: 24,
      boxShadow: '0 20px 60px rgba(28,25,23,0.14), 0 6px 18px rgba(28,25,23,0.08)',
      overflow: 'hidden', display: 'flex', flexDirection: 'column',
      ...style,
    }}>
      <div style={{ height: 170, background: job.color, position: 'relative', display: 'flex', alignItems: 'flex-end', padding: 18 }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 70% 20%, rgba(255,255,255,0.3), transparent 60%)' }} aria-hidden="true"/>
        <div style={{
          position: 'absolute', top: 16, right: 16, padding: '6px 12px', borderRadius: 999,
          background: 'rgba(255,255,255,0.95)', color: '#92400E', fontWeight: 800, fontSize: 13,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          {job.match}% match
        </div>
        <div style={{
          width: 68, height: 68, borderRadius: 18, background: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 26, fontWeight: 800, color: '#92400E',
          boxShadow: '0 6px 14px rgba(0,0,0,0.12)',
        }}>{job.abbr}</div>
      </div>
      <div style={{ padding: '22px 22px 20px', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: '#B45309', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{job.company}</div>
          <h3 style={{ margin: '4px 0 0', fontSize: 22, fontWeight: 800, color: '#92400E', lineHeight: 1.15, letterSpacing: '-0.01em' }}>{job.title}</h3>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, color: '#78350F', fontSize: 14 }}>
          <div>{job.salary}</div>
          <div>{job.location}</div>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 'auto' }}>
          {job.tags?.map(t => (
            <span key={t} style={{ padding: '4px 10px', borderRadius: 999, background: '#FEF3C7', color: '#92400E', fontSize: 11, fontWeight: 600 }}>{t}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

export function HeroSwipe({ jobs = SAMPLE_JOBS, cycleMs = 2800 }: HeroSwipeProps) {
  const [stack, setStack] = useState(jobs);
  const [swipeDir, setSwipeDir] = useState<string | null>(null);
  const [counter, setCounter] = useState({ liked: 127, passed: 94 });

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    const id = setInterval(() => {
      handleSwipe(Math.random() > 0.35 ? 'right' : 'left');
    }, cycleMs);
    return () => clearInterval(id);
  }, [stack, cycleMs]);

  function handleSwipe(dir: string) {
    setSwipeDir(dir);
    const t = setTimeout(() => {
      setStack(s => {
        const next = s.slice(1);
        return next.length ? [...next, s[0]] : jobs;
      });
      setSwipeDir(null);
      setCounter(c => ({
        liked: c.liked + (dir === 'right' ? 1 : 0),
        passed: c.passed + (dir === 'left' ? 1 : 0),
      }));
    }, 380);
    return () => clearTimeout(t);
  }

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: 440, margin: '0 auto' }}>
      <div style={{ position: 'absolute', top: -40, left: 0, right: 0, display: 'flex', justifyContent: 'space-between', zIndex: 3 }}>
        <div style={{ padding: '8px 14px', borderRadius: 999, background: 'rgba(239,68,68,0.1)', color: '#B91C1C', fontWeight: 700, fontSize: 13, display: 'flex', alignItems: 'center', gap: 6, border: '1px solid rgba(239,68,68,0.2)' }}>
          {counter.passed} пропущено
        </div>
        <div style={{ padding: '8px 14px', borderRadius: 999, background: 'rgba(22, 163, 74, 0.1)', color: '#15803D', fontWeight: 700, fontSize: 13, display: 'flex', alignItems: 'center', gap: 6, border: '1px solid rgba(22, 163, 74, 0.2)' }}>
          {counter.liked} откликов
        </div>
      </div>
      <div style={{ position: 'relative', width: '100%', height: 460 }}>
        {stack.slice(0, 3).map((job, i) => {
          const isTop = i === 0;
          const offset = i * 12;
          const scale = 1 - i * 0.04;
          let transform = `translateY(${offset}px) scale(${scale})`;
          let opacity = 1;
          if (isTop && swipeDir) {
            transform = swipeDir === 'right' ? 'translate(120%, -30px) rotate(18deg)' : 'translate(-120%, -30px) rotate(-18deg)';
            opacity = 0;
          }
          return (
            <SwipeJobCard
              key={`${job.title}-${i}-${stack[0].title}`}
              job={job}
              style={{ transform, transition: 'transform 0.4s cubic-bezier(.2,.8,.2,1), opacity 0.3s', opacity, zIndex: 10 - i }}
            />
          );
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: 18, marginTop: 22, position: 'relative', zIndex: 5 }}>
        <button
          onClick={() => handleSwipe('left')}
          aria-label="Пропустить"
          style={{ width: 60, height: 60, borderRadius: 999, background: '#fff', boxShadow: '0 8px 24px rgba(239, 68, 68, 0.18), 0 0 0 1px rgba(239, 68, 68, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#EF4444' }}
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
        <button
          onClick={() => handleSwipe('right')}
          aria-label="Откликнуться"
          style={{ width: 60, height: 60, borderRadius: 999, background: 'var(--brand-gradient)', boxShadow: '0 10px 30px rgba(219,39,119,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        </button>
      </div>
    </div>
  );
}
