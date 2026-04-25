export interface JobCard {
  title: string;
  company: string;
  salary: string;
  location: string;
  match: number;
  schedule?: string;
  experience?: string;
  posted?: string;
  duties?: string[];
  requirements?: string[];
  tags?: string[];
  color?: string;
  abbr?: string;
  trap?: string;
}
