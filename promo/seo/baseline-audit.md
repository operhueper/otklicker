# SEO baseline для otklicker.ru — 2026-04-25

## Реализовано в Phase 4

- [x] `<title>` и `<meta description>` на всех 5 страницах (главная, /privacy, /cookies, /offer, /bot-privacy)
- [x] Open Graph (type, locale, url, siteName, title, description) — глобально через layout, переопределение на главной
- [x] Twitter Card (summary_large_image)
- [x] OG-image 1200×630 — через `app/opengraph-image.tsx` + `next/og` (динамическая генерация на build-time)
- [x] `robots.txt` через `app/robots.ts` (Allow: /, Disallow: /offer и /bot-privacy)
- [x] `sitemap.xml` через `app/sitemap.ts` — 3 URL (/, /privacy, /cookies)
- [x] JSON-LD SoftwareApplication на главной (с двумя Offer: Бесплатный 0 ₽, Активный 790 ₽)
- [x] Canonical URLs на всех страницах через `alternates.canonical`
- [x] favicon — `app/icon.tsx` + `app/apple-icon.tsx` (Next.js auto-нарезка размеров)
- [x] manifest.json (PWA-light)
- [x] `<html lang="ru">` (унаследовано из Phase 1)
- [x] `noindex, nofollow` для placeholder-страниц `/offer` и `/bot-privacy`
- [x] `metadataBase` для абсолютных URL в OG/Twitter

## Технические решения

- **Pencil MCP недоступен в этой сессии** — экспорт нод брендбука (`cIcTM`, `xez6k`, `U2B8J`) не выполнен. Использован fallback: favicon и OG-image сгенерированы через `next/og` на основе бренд-цветов и буквы «о» (для иконки), полного wordmark «откликер» (для OG).
- **OG-image через next/og.** Static export поддерживает `app/opengraph-image.tsx` для статических (не динамических) маршрутов — генерится один раз на build-time. Issue Next.js #51147 касается только маршрутов с `generateStaticParams`.
- **manifest.json** положен в `public/`, не через `app/manifest.ts`, потому что не требует динамики.

## Отложено (требует настройки/решения)

- [ ] Yandex.Metrica counter ID — пользователь подключит в отдельной сессии
- [ ] Search Console / Yandex.Webmaster verification (после деплоя на otklicker.ru)
- [ ] Schema.org Organization (когда будут реквизиты ИП/ООО для JSON-LD)
- [ ] Backlinks / outreach — отдельная задача после деплоя
- [ ] Полноценный favicon-set из брендбука (`cIcTM`, `xez6k`) — когда Pencil MCP будет доступен или будет ручной экспорт

## Верификационный чеклист (после `npm run build`)

- [ ] `out/robots.txt` существует, содержит `User-agent: *`, `Sitemap: https://otklicker.ru/sitemap.xml`
- [ ] `out/sitemap.xml` валидный, 3 URL
- [ ] `out/index.html` содержит `<script type="application/ld+json">` с SoftwareApplication
- [ ] `out/index.html` содержит `<meta property="og:image">`
- [ ] `out/opengraph-image.png` (или `opengraph-image-*.png`) существует, размер 1200×630
- [ ] `out/icon.png` и `out/apple-icon.png` существуют
- [ ] `/offer/index.html` содержит `<meta name="robots" content="noindex, nofollow">`
- [ ] `/bot-privacy/index.html` содержит `<meta name="robots" content="noindex, nofollow">`
