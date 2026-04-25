export interface JobCard {
  // Common (present in both HERO_CHAT_JOBS and SAMPLE_JOBS)
  title: string;
  company: string;
  salary: string;
  location: string;
  match: number; // 0..100

  // HERO_CHAT_JOBS only (chat variant)
  schedule?: string;
  experience?: string;
  posted?: string;
  duties?: string[];
  requirements?: string[];

  // SAMPLE_JOBS only (swipe variant)
  tags?: string[];
  /** CSS background-image for card header — e.g. 'linear-gradient(135deg, #FBBF24, #F97316)' */
  color?: string;
  /** Abbreviation for logo tile */
  abbr?: string;
}
