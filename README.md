# player0.dev

Player Zero product hub. Static files only - no framework, application server,
database or public metrics endpoint. Python standard library builds it.
Fonts and product media are local. Cloudflare injects its Web Analytics beacon
through the existing player0.dev zone setup; the static generator does not add a second beacon.

## Commands

```bash
python tool/build.py           # write dist/
python tool/build.py --check   # fail if dist/ is stale
python tool/serve.py           # preview dist/ at http://127.0.0.1:8791
python tool/sync_legal.py      # pull legal docs from the product repos (optional)
```

`dist/` is the deploy output. Nothing in `dist/` is edited by hand.

## Adding a product

Create one file in `content/products/<slug>.json`. Nothing else is touched - the
home cards, the products index, the detail page, the sitemap and the legal index
all read the registry.

```json
{
  "slug": "example",
  "kind": "app",                       // app | game
  "status": "in-development",          // released | testing | in-development | coming-soon
  "platforms": ["android", "steam"],
  "order": 30,
  "featured": true,                    // show on the home page
  "images": { "hero": "/assets/x.png", "screenshots": ["/assets/y.png"] },
  "links": [{ "platform": "steam", "label": "Steam", "url": "https://..." }],
  "legal": [{ "doc": "privacy", "path": "example/privacy", "languages": ["en"] }],
  "content": {
    "en": { "name": "Example", "tagline": "One line.", "description": ["Para."] }
  }
}
```

Any of `images`, `links`, `legal` and `screenshots` may be omitted - the matching
section disappears from the page.

## Adding a browser game

Create one file in `content/play/<slug>.json`. Same shape, plus an embed:

```json
{ "slug": "example", "order": 10,
  "embed": { "src": "/play/example/game/", "width": 16, "height": 9 },
  "content": { "en": { "name": "Example", "tagline": "One line.",
                       "description": ["Para."], "controls": ["Any key"] } } }
```

Put the game's own files under `dist/play/<slug>/game/` (or point `embed.src` at
an external host). The page supplies the frame, the ratio and the metadata.

## Languages

Author new product copy and promotional media in English first. English is the
canonical base for localized versions.

Three language axes are deliberately independent:

- **Site chrome** - `content/site.json` `languages`, strings in `content/i18n/`.
- **Product content** - per product, under `content.<lang>`. A product missing a
  language falls back to the default and says so on the page.
- **Legal documents** - per document, `legal[].languages`. Only the languages that
  actually exist get a URL.

The default language lives at the root (`/products/`), others under a prefix
(`/ko/products/`). Adding `ja` means adding `content/i18n/ja.json` and listing it
in `site.json`.

Browser-language selection is one small inline script per page
(`tool/language.py`), built from `site.json` `languages` and the page's own
hreflang alternates. No cookies, no server, no network.

- Only default-language (unprefixed) pages ever redirect, and only to the same
  page's generated alternate, with query and hash kept, via `location.replace`.
  Localized URLs such as `/ko/products/keycerto/` always stay as shared. Pages
  without that translation and 404 pages stay put.
- Order: `?lang=en` opt-out, then no redirect when arriving from another page
  of this site (same-origin referrer, so browsing and English-only legal
  fallbacks never switch language mid-visit), then a saved menu choice
  (`localStorage` `player0-language`), then `navigator.languages` in order
  (then `navigator.language`), else English.
- Matching ignores case and region (`ko-KR` -> `ko`, `en-GB` -> English).
  `zh-TW`, `zh-Hant`, `zh-HK`, `zh-MO` and plain `zh` open `zh-TW`; Simplified
  `zh-CN`/`zh-Hans`/`zh-SG` do not, and the next browser language is tried.
- The menu's English link always carries `?lang=en`, so English opened any way
  (new tab, middle or modified click, context menu, blocked storage, stripped
  referrer) stays English. Only that menu link has it: canonical, hreflang and
  sitemap URLs stay clean, and other language links are unchanged.
- An ordinary click on a menu link also saves that language, English included.
  Modified and middle clicks open normally and save nothing. Saved values are
  only accepted when they name a site language; they are never URLs.

Run `node --test tool/test_language_navigation.js` after the build: it executes
the generated script against stubbed browsers.

## Legal documents

Markdown in `content/legal/<product>/<doc>.<lang>.md`. Meloom's policy is authored
in the Meloom repository because the app ships the same text; `tool/sync_legal.py`
mirrors it here and `--check` fails if the copies drift. The site builds without
the product repositories present.

## URLs that must not break

`/privacy/` and `/privacy/ko/` are printed inside the Meloom app's own policy text
and are used for the Play Console listing. They 301 to the new paths via
`content/site.json` `redirects`, which becomes `dist/_redirects`. Do not remove
those rules.

## Deploy

Cloudflare Pages project `player0`, custom domain already attached.

- Framework preset: **None**
- Build command: **`python tool/build.py`**
- Build output directory: **`dist`**
- No Functions or Workers. Web Analytics uses the existing automatic setup on the
  `player0.dev` zone. Keep the separate Pages-project analytics setting disabled.

The Pages project is connected to `player4521/player0`. Production deploys
automatically from `main`; the working branch gets preview deployments. The
build command is `python tool/build.py` and the output directory is `dist`.


## Website privacy and private analytics

The company website notice is `content/website_privacy.json`, separate from the
Meloom app policies. It is built at `/website-privacy/` and each site language's
prefixed route, with a localized footer link.

Cloudflare Web Analytics uses the existing automatic injection for the
`player0.dev` zone, preserving its collected history. The separate Pages-project
collector is disabled; do not enable a second collector for the same site.
Do not add a manual beacon to templates or generated HTML:
multiple copies can double-count measurements. There are no public analytics
exports, metrics files, dashboard HTML or metrics APIs in this repository/site.
Aggregate statistics are viewed in the Cloudflare account dashboard after login;
counts are not a verified number of individual people.

When `content/site.json` has `analytics.dashboardUrl`, the builder accepts
only the official generic account-selector URL
`https://dash.cloudflare.com/?to=/:account/web-analytics` and generates `/stats`
and `/stats/` HTTP 302 redirects. The destination query is URL-encoded so Pages
does not interpret `:account` as a route placeholder. Other or missing URLs
generate neither shortcut.
Account-specific dashboard URLs, account IDs and siteTag values stay out of public
configuration; the signed-in owner selects the site inside Cloudflare.
The shortcut contains no analytics data and does not grant access: Cloudflare
login and account permissions protect the dashboard. It is not password hiding
or security through a secret URL. `/stats` is excluded from robots and the sitemap.
Do not put account credentials, private dashboard exports or access tokens in
site content. The analytics dashboard URL itself is a public redirect destination.

Run `python tool/test_website_privacy.py` after changing the notice or shortcut.
Keep the existing build, link and language-navigation checks as well.

## Product presentation

`tool/presentation.py` renders the company, product, about and support pages.
`tool/build.py` remains the entry point. Product facts and translated copy live
in the registry; generated `dist/` files are never edited by hand.

Product content may additionally include `features` and `howTo` arrays of
`{title, body}`, `modes` with the same shape, and `faq` as
`{question, answer}` objects. An optional `summary` is used in the compact
home catalog and featured introduction, falling back to `tagline`.
`video` is an optional local video URL and remains supported for existing products.
An optional `videos` map provides localized URLs, for example
`{"en": "/assets/example-en.mp4", "ko": "/assets/example-ko.mp4"}`. Pages choose
the requested language, then `en`, then the legacy `video` URL. An optional
`videoPosters` map uses the same language fallback before `images.hero`.
`galleries.<language>` is an array of `{src, alt, caption}` items.
The existing privacy documents and both legacy privacy redirects are retained.

Run `python tool/check_site.py` after the build to check internal links, anchor
targets, media files, document language, canonical URLs and deployment size.

Website artwork and gameplay are web derivatives of existing product media.
The source repositories and original approved files remain unchanged.

## Internal browser visits

`/analytics-preferences/` is a noindex, non-sitemap utility page with explicit
per-browser controls. It stores only `__Host-player0_analytics_opt_out=1` for up
to one year (Secure, host-only, Path=/, SameSite=Lax). It is an opt-out flag,
not a unique visitor ID. Nothing is stored merely by opening the page.

The production zone's Configuration Rule disables RUM only on this preferences
route or when the opt-out cookie is present, with the hostname restricted to
player0.dev. Keep normal unmarked visitors measured. This is an account-side
setting: deploying static files alone does not configure Cloudflare. No manual
beacon is added and the original automatic collector/history stay intact.
The flag affects subsequent page loads, not already-open pages or past data.
Activate it once in each working browser and reapply after clearing cookies,
using another browser profile, or expiry. This excludes Web Analytics, not
Cloudflare's operational edge-request counts.

Validate with `node --test tool/test_analytics_preferences.js`, the normal
build/link/language/privacy checks, then confirm that a marked browser gets no
injected beacon while an unmarked request still gets exactly one.
