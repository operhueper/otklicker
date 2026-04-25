import { MousePointerClick } from 'lucide-react';

interface BrandMarkProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const SIZE_MAP: Record<string, [number, number]> = {
  sm: [36, 16],
  md: [48, 22],
  lg: [72, 34],
  xl: [96, 44],
};

export function BrandMark({ size = 'md' }: BrandMarkProps) {
  const [box, icon] = SIZE_MAP[size] ?? SIZE_MAP.md;
  return (
    <div
      style={{
        width: box,
        height: box,
        borderRadius: Math.round(box * 0.3),
        background: 'var(--brand-gradient)',
        boxShadow: '0 8px 22px rgba(219, 39, 119, 0.28)',
        color: '#fff',
        flexShrink: 0,
      }}
      className="inline-flex items-center justify-center"
    >
      <MousePointerClick size={icon} strokeWidth={2.2} />
    </div>
  );
}

interface BrandLockupProps {
  size?: 'sm' | 'md' | 'lg';
}

export function BrandLockup({ size = 'md' }: BrandLockupProps) {
  const titleSize = size === 'lg' ? 26 : size === 'sm' ? 16 : 20;
  return (
    <div className="inline-flex items-center gap-3">
      <BrandMark size={size} />
      <div className="flex flex-col leading-none">
        <div
          style={{ fontWeight: 800, fontSize: titleSize, letterSpacing: '-0.02em' }}
          className="text-text-heading"
        >
          откликер
        </div>
        {size !== 'sm' && (
          <div className="text-text-sub mt-1" style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.02em' }}>
            найди работу мечты
          </div>
        )}
      </div>
    </div>
  );
}
