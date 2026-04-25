import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://otklicker.ru';
  const lastModified = new Date('2026-04-25');
  return [
    { url: `${base}/`, lastModified, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${base}/privacy`, lastModified, changeFrequency: 'yearly', priority: 0.3 },
    { url: `${base}/cookies`, lastModified, changeFrequency: 'yearly', priority: 0.3 },
  ];
}
