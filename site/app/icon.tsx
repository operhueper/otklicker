import { ImageResponse } from 'next/og';

export const size = { width: 512, height: 512 };
export const contentType = 'image/png';

export default function Icon() {
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
          borderRadius: '20%',
        }}
      >
        <div
          style={{
            display: 'flex',
            fontSize: 360,
            fontWeight: 900,
            color: '#FFFBF0',
            lineHeight: 1,
            letterSpacing: '-0.05em',
            marginTop: '-20px',
          }}
        >
          о
        </div>
      </div>
    ),
    { ...size },
  );
}
