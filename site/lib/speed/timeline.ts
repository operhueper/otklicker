export const T_START = 0;    // 19:00
export const T_END = 870;    // 09:30 next day = 14h30m
export const PLAY_MS = 13000;

export function clock(m: number): string {
  const h = (Math.floor(m / 60) + 19) % 24;
  const mm = Math.floor(m % 60);
  return `${h.toString().padStart(2, '0')}:${mm.toString().padStart(2, '0')}`;
}

export interface Zone {
  tStart: number;
  tEnd: number;
  screen: number;
  playWeight: number;
}

export const ZONES: Zone[] = [
  { tStart: 0,   tEnd: 60,  screen: 0.40, playWeight: 0.36 },
  { tStart: 60,  tEnd: 720, screen: 0.22, playWeight: 0.18 },
  { tStart: 720, tEnd: 870, screen: 0.38, playWeight: 0.46 },
];

export const ZONE_SCREEN_STARTS: number[] = ZONES.reduce<number[]>((acc, _z, i) => {
  acc.push(i === 0 ? 0 : acc[i - 1] + ZONES[i - 1].screen);
  return acc;
}, []);

export const ZONE_PLAY_STARTS: number[] = ZONES.reduce<number[]>((acc, _z, i) => {
  acc.push(i === 0 ? 0 : acc[i - 1] + ZONES[i - 1].playWeight);
  return acc;
}, []);

export function pct(t: number): number {
  if (t <= ZONES[0].tStart) return 0;
  if (t >= ZONES[ZONES.length - 1].tEnd) return 100;
  for (let i = 0; i < ZONES.length; i++) {
    const z = ZONES[i];
    if (t >= z.tStart && t <= z.tEnd) {
      const local = (t - z.tStart) / (z.tEnd - z.tStart);
      return (ZONE_SCREEN_STARTS[i] + local * z.screen) * 100;
    }
  }
  return 100;
}

export function progressToMinute(p: number): number {
  if (p <= 0) return 0;
  if (p >= 1) return T_END;
  for (let i = 0; i < ZONES.length; i++) {
    const z = ZONES[i];
    const start = ZONE_PLAY_STARTS[i];
    const end = start + z.playWeight;
    if (p >= start && p <= end) {
      const local = (p - start) / z.playWeight;
      return z.tStart + local * (z.tEnd - z.tStart);
    }
  }
  return T_END;
}

export interface Beat {
  t: number;
  title: string;
  sub: string;
  emphasis: 'first' | 'mid' | 'win' | 'lose';
}

export const BOT_BEATS: Beat[] = [
  { t: 10,  title: 'Бот заметил и откликнулся',   sub: 'Через 10 минут после публикации', emphasis: 'first' },
  { t: 60,  title: 'В первой десятке откликов',   sub: 'Утром HR увидит вас сверху',       emphasis: 'mid' },
  { t: 855, title: 'HR читает топ-20 откликов',   sub: 'Вы в этой стопке',                emphasis: 'win' },
];

export const MANUAL_BEATS: Beat[] = [
  { t: 780, title: 'Открыли HH утром',     sub: 'На вакансии уже 87 откликов',         emphasis: 'first' },
  { t: 855, title: 'Ваш отклик — 88-й',   sub: 'HR уже архивирует хвост стопки',      emphasis: 'lose' },
];

export interface HourTick {
  t: number;
  label: string;
  weight: 'strong' | 'weak' | 'midnight';
}

export const HOUR_TICKS: HourTick[] = [
  { t: 0,   label: '19:00', weight: 'strong' },
  { t: 30,  label: '19:30', weight: 'weak' },
  { t: 60,  label: '20:00', weight: 'weak' },
  { t: 360, label: '01:00', weight: 'midnight' },
  { t: 720, label: '07:00', weight: 'weak' },
  { t: 870, label: '09:30', weight: 'strong' },
];
