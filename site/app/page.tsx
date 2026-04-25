import { Nav } from '@/components/nav';
import { Hero } from '@/components/hero';
import { TeaserStrip } from '@/components/teaser-strip';
import { HowItWorks } from '@/components/how-it-works';
import { Features } from '@/components/features';
import { SpeedSection } from '@/components/speed';
import { Pricing } from '@/components/pricing';
import { FAQ } from '@/components/faq';
import { FinalCTA } from '@/components/final-cta';
import { Footer } from '@/components/footer';
import { CookieBanner } from '@/components/cookie-banner';

export default function HomePage() {
  return (
    <>
      <Nav />
      <main>
        <Hero variant="chat" />
        <TeaserStrip />
        <HowItWorks />
        <Features />
        <SpeedSection />
        <Pricing />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
      <CookieBanner />
    </>
  );
}
