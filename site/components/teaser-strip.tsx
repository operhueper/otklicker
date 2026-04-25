export function TeaserStrip() {
  const items = [
    { v: '×3', l: 'больше приглашений' },
    { v: 'x7', l: 'быстрее первый оффер' },
    { v: '24/7', l: 'HR-автоответы' },
  ];

  return (
    <div style={{ background: 'var(--bg-pastel)', padding: '28px 0', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)' }}>
      <div className="mx-auto max-w-container px-6" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }} id="teaser-grid">
        {items.map((it, i) => (
          <div key={i} style={{
            display: 'flex', flexDirection: 'column', gap: 4,
            borderLeft: i > 0 ? '1px solid var(--line-strong)' : 'none',
            paddingLeft: i > 0 ? 24 : 0,
          }}>
            <div style={{ fontSize: 38, fontWeight: 900, color: 'var(--text-heading)', letterSpacing: '-0.02em', lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>
              {it.v}
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-sub)', fontWeight: 500 }}>{it.l}</div>
          </div>
        ))}
      </div>
      <style>{`@media (max-width: 720px) { #teaser-grid { grid-template-columns: repeat(2, 1fr) !important; } }`}</style>
    </div>
  );
}
