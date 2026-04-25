// site/tailwind.config.ts
import type { Config } from 'tailwindcss';
import typography from '@tailwindcss/typography';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    // Override default screens (dropping sm:640 / md:768 / lg:1024 — not used in design)
    screens: {
      sm: '720px',  // mobile dense padding
      md: '960px',  // two-column grids -> single column
      lg: '1240px', // container
    },
    extend: {
      colors: {
        // Brand accents
        amber:  '#FBBF24',
        orange: '#F97316',
        red:    '#EF4444',
        pink:   '#DB2777',
        // Surfaces
        bg:           '#FAFAF9',
        'bg-pastel':  '#FEF3C7',
        'bg-pastel-2':'#FDE68A',
        'bg-cream':   '#FFFBF0',
        'bg-dark':    '#1C1917',
        'bg-dark-2':  '#292524',
        card:         '#FFFFFF',
        'card-dark':  '#292524',
        // Text
        text:                 '#78350F',
        'text-heading':       '#92400E',
        'text-sub':           '#B45309',
        'text-muted':         '#A8A29E',
        'text-on-dark':       '#FEF3C7',
        'text-on-dark-sub':   '#FBBF24',
        // Lines (accessible as border-line)
        line:                 'rgba(146, 64, 14, 0.12)',
        'line-strong':        'rgba(146, 64, 14, 0.22)',
        'line-dark':          'rgba(254, 243, 199, 0.12)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      fontSize: {
        // Custom sizes with line-height and letter-spacing — matches styles.css
        h1:    ['clamp(44px, 6vw, 80px)', { lineHeight: '1.02', letterSpacing: '-0.03em', fontWeight: '900' }],
        h2:    ['clamp(32px, 4vw, 52px)', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '800' }],
        h3:    ['clamp(30px, 3.4vw, 44px)', { lineHeight: '1.10', letterSpacing: '-0.02em', fontWeight: '800' }],
        lead:  ['19px', { lineHeight: '1.55', fontWeight: '500' }],
        body:  ['16px', { lineHeight: '1.55', fontWeight: '500' }],
        small: ['13px', { lineHeight: '1.5',  fontWeight: '500' }],
        eyebrow: ['12px', { lineHeight: '1', letterSpacing: '0.02em', fontWeight: '600' }],
      },
      borderRadius: {
        xs:   '8px',
        sm:   '12px',
        md:   '18px',
        lg:   '24px',
        xl:   '32px',
        // pill: use built-in 'full' (= 9999px)
      },
      boxShadow: {
        sm:           '0 1px 2px rgba(120,53,15,0.06), 0 2px 6px rgba(120,53,15,0.04)',
        md:           '0 4px 14px rgba(120,53,15,0.08), 0 12px 32px rgba(120,53,15,0.06)',
        lg:           '0 12px 40px rgba(120,53,15,0.12), 0 30px 80px rgba(120,53,15,0.08)',
        brand:        '0 20px 50px rgba(219,39,119,0.22), 0 6px 18px rgba(249,115,22,0.24)',
        'brand-hover':'0 24px 60px rgba(219,39,119,0.30), 0 8px 22px rgba(249,115,22,0.30)',
        // For phone mockup (real-bot.jsx:23)
        phone:        '0 30px 80px rgba(28,25,23,0.25), 0 10px 24px rgba(28,25,23,0.12), inset 0 0 0 1px rgba(255,255,255,0.06)',
      },
      backgroundImage: {
        // Only normal — subtle/intense presets were in tweaks-panel, not in prod
        'brand-gradient': 'linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%)',
      },
      keyframes: {
        'slide-in-from-right': {
          '0%':   { transform: 'translateX(120%) rotate(8deg)', opacity: '0' },
          '60%':  { opacity: '1' },
          '100%': { transform: 'translateX(0) rotate(0deg)', opacity: '1' },
        },
        'swipe-right': {
          '0%':   { transform: 'translate(0, 0) rotate(0deg)',          opacity: '1' },
          '100%': { transform: 'translate(120%, -30px) rotate(18deg)',  opacity: '0' },
        },
        'swipe-left': {
          '0%':   { transform: 'translate(0, 0) rotate(0deg)',           opacity: '1' },
          '100%': { transform: 'translate(-120%, -30px) rotate(-18deg)', opacity: '0' },
        },
        'pulse-ring': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(219, 39, 119, 0.5)' },
          '50%':      { boxShadow: '0 0 0 14px rgba(219, 39, 119, 0)' },
        },
        'typing-dots': {
          '0%, 60%, 100%': { transform: 'translateY(0)',     opacity: '0.3' },
          '30%':           { transform: 'translateY(-4px)',  opacity: '1' },
        },
        'float-y': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
      },
      animation: {
        'slide-in-from-right': 'slide-in-from-right 0.5s cubic-bezier(.2,.8,.2,1)',
        'slide-in-features':   'slide-in-from-right 0.6s cubic-bezier(.2,.8,.2,1)',
        'swipe-right':         'swipe-right 0.45s cubic-bezier(.2,.8,.2,1) forwards',
        'swipe-left':          'swipe-left 0.45s cubic-bezier(.2,.8,.2,1) forwards',
        'pulse-ring':          'pulse-ring 2.5s infinite',
        'typing-dots':         'typing-dots 1.2s infinite',
        'float-y':             'float-y 4s ease-in-out infinite',
      },
      maxWidth: {
        container: '1240px',
        prose:     '760px',  // legal pages and FAQ content width
        narrow:    '720px',  // section-head
        cards:     '880px',  // pricing-grid
      },
      spacing: {
        // Additions to default scale
        18: '4.5rem',  // 72px — Nav height
        22: '5.5rem',  // 88px
        26: '6.5rem',  // 104px
        30: '7.5rem',  // 120px — section padding desktop
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(.2,.8,.2,1)',
      },
    },
  },
  plugins: [
    typography, // markdown rendering for /privacy, /cookies, /offer
  ],
};

export default config;
