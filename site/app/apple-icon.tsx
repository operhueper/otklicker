import { ImageResponse } from 'next/og';

export const size = { width: 180, height: 180 };
export const contentType = 'image/png';

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background:
            'linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%)',
        }}
      >
        <div
          style={{
            display: 'flex',
            fontSize: 130,
            fontWeight: 900,
            color: '#FFFBF0',
            lineHeight: 1,
            letterSpacing: '-0.05em',
            marginTop: '-8px',
          }}
        >
          о
        </div>
      </div>
    ),
    { ...size },
  );
}
