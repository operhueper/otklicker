import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: '*', allow: '/', disallow: ['/offer', '/bot-privacy'] }],
    sitemap: 'https://otklicker.ru/sitemap.xml',
    host: 'https://otklicker.ru',
  };
}
