# player0.dev

Player Zero product hub. Static files only - no framework, no server, no database,
no analytics, no external fonts or CDNs. Python standard library builds it.

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

Three language axes are deliberately independent:

- **Site chrome** - `content/site.json` `languages`, strings in `content/i18n/`.
- **Product content** - per product, under `content.<lang>`. A product missing a
  language falls back to the default and says so on the page.
- **Legal documents** - per document, `legal[].languages`. Only the languages that
  actually exist get a URL.

The default language lives at the root (`/products/`), others under a prefix
(`/ko/products/`). Adding `ja` means adding `content/i18n/ja.json` and listing it
in `site.json`.

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
- No Functions, no Workers, no Web Analytics.

The Pages project is connected to `player4521/player0`. Production deploys
automatically from `main`; the working branch gets preview deployments. The
build command is `python tool/build.py` and the output directory is `dist`.


## Product presentation

`tool/presentation.py` renders the company, product, about and support pages.
`tool/build.py` remains the entry point. Product facts and translated copy live
in the registry; generated `dist/` files are never edited by hand.

Product content may additionally include `features` and `howTo` arrays of
`{title, body}`, `modes` with the same shape, and `faq` as
`{question, answer}` objects. An optional `summary` is used in the compact
home catalog and featured introduction, falling back to `tagline`.
`video` is an optional local video URL.
`galleries.<language>` is an array of `{src, alt, caption}` items.
The existing privacy documents and both legacy privacy redirects are retained.

Run `python tool/check_site.py` after the build to check internal links, anchor
targets, media files, document language, canonical URLs and deployment size.

Website artwork and gameplay are web derivatives of existing product media.
The source repositories and original approved files remain unchanged.
