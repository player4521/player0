#!/usr/bin/env python3
"""player0.dev static site generator.

Registry driven: everything on the site comes from `content/`. Adding a product
means adding one JSON file under `content/products/`; adding a browser game means
adding one under `content/play/`. No page is written by hand.

Python standard library only - no build system, no dependencies, no runtime server.

    python tool/build.py            # write dist/
    python tool/build.py --check    # fail if dist/ is stale
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import presentation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DIST = ROOT / "dist"

STATUS_ORDER = ("released", "testing", "in-development", "coming-soon")


# --------------------------------------------------------------------- loading
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(folder: Path) -> list[dict]:
    if not folder.is_dir():
        return []
    items = [load_json(p) for p in sorted(folder.glob("*.json"))]
    items.sort(key=lambda it: (it.get("order", 1000), it.get("slug", "")))
    return items


class Site:
    def __init__(self) -> None:
        self.config = load_json(CONTENT / "site.json")
        self.default_lang: str = self.config["defaultLanguage"]
        self.languages: list[str] = self.config["languages"]
        self.strings = {
            lang: load_json(CONTENT / "i18n" / f"{lang}.json")
            for lang in self.languages
        }
        self.products = load_registry(CONTENT / "products")
        self.playables = load_registry(CONTENT / "play")

    def t(self, lang: str, dotted: str, **fmt) -> str:
        """Look up a chrome string, falling back to the default language."""
        for candidate in (lang, self.default_lang):
            node = self.strings.get(candidate)
            for part in dotted.split("."):
                if not isinstance(node, dict) or part not in node:
                    node = None
                    break
                node = node[part]
            if isinstance(node, str):
                return node.format(**fmt) if fmt else node
        return dotted

    def language_name(self, lang: str) -> str:
        return self.strings.get(lang, {}).get("languageName", lang)

    # URLs -----------------------------------------------------------------
    def prefix(self, lang: str) -> str:
        """The default language lives at the root; others get a folder."""
        return "" if lang == self.default_lang else f"/{lang}"

    def url(self, lang: str, *parts: str) -> str:
        tail = "/".join(p.strip("/") for p in parts if p)
        return f"{self.prefix(lang)}/{tail}/" if tail else f"{self.prefix(lang)}/"


# ------------------------------------------------------------------- markdown
_URL = re.compile(r"https?://[^\s<>()\[\]]+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_CODE = re.compile(r"`([^`]+)`")
_STRONG = re.compile(r"\*\*([^*]+)\*\*")


def render_inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = _CODE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = _STRONG.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = _URL.sub(lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', out)
    out = _EMAIL.sub(lambda m: f'<a href="mailto:{m.group(0)}">{m.group(0)}</a>', out)
    return out


def render_markdown(source: str) -> str:
    """The same markdown subset the Meloom app renders: headings, paragraphs,
    bullets, inline code and bold. No tables, images or code blocks."""
    blocks: list[str] = []
    paragraph: list[str] = []
    bullets: list[str] = []

    def flush() -> None:
        if paragraph:
            blocks.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()
        if bullets:
            items = "\n".join(f"    <li>{render_inline(i)}</li>" for i in bullets)
            blocks.append(f"<ul>\n{items}\n  </ul>")
            bullets.clear()

    for raw in source.replace("\r\n", "\n").split("\n"):
        stripped = raw.strip()
        if not stripped:
            flush()
            continue
        for marker, tag in (("### ", "h3"), ("## ", "h2"), ("# ", "h1")):
            if stripped.startswith(marker):
                flush()
                blocks.append(f"<{tag}>{render_inline(stripped[len(marker):])}</{tag}>")
                break
        else:
            if stripped.startswith("- "):
                if paragraph:
                    flush()
                bullets.append(stripped[2:])
            elif bullets:
                bullets[-1] = f"{bullets[-1]} {stripped}"
            else:
                paragraph.append(stripped)
    flush()
    return "\n  ".join(blocks)


# ---------------------------------------------------------------- page shell
def esc(value: str) -> str:
    return html.escape(value, quote=True)


def shell(site: Site, *, lang: str, path: str, title: str, description: str,
          body: str, alternates: dict[str, str] | None = None, main_class: str = "page") -> str:
    return presentation.shell(site, lang=lang, path=path, title=title,
                              description=description, body=body,
                              alternates=alternates, main_class=main_class)




# -------------------------------------------------------------- product logic
def product_content(site: Site, product: dict, lang: str) -> tuple[dict, str | None]:
    """Product copy in `lang`, or the default language plus the language it fell
    back to. Product languages are independent of the site's languages."""
    blocks = product.get("content", {})
    if lang in blocks:
        return blocks[lang], None
    fallback = site.default_lang if site.default_lang in blocks else next(iter(blocks))
    return blocks[fallback], fallback


def status_badge(site: Site, product: dict, lang: str) -> str:
    status = product.get("status", "in-development")
    return (f'<span class="badge badge-{esc(status)}">'
            f'{esc(site.t(lang, f"status.{status}"))}</span>')


def product_card(site: Site, product: dict, lang: str) -> str:
    copy, _ = product_content(site, product, lang)
    href = site.url(lang, "products", product["slug"])
    kind = esc(site.t(lang, f'kind.{product.get("kind", "app")}'))
    hero = product.get("images", {}).get("hero")
    thumb = (f'<img class="card-thumb" src="{hero}" alt="" loading="lazy" '
             f'width="640" height="360">') if hero else ""
    tagline = copy.get("tagline", "")
    return f"""      <li class="card product-card">
        <a class="card-link" href="{href}">
          {thumb}
          <span class="card-meta">{kind} {status_badge(site, product, lang)}</span>
          <h3>{esc(copy.get("name", product["slug"]))}</h3>
          <p>{esc(tagline)}</p>
        </a>
      </li>"""


def legal_docs_for(site: Site, product: dict, lang: str) -> list[tuple[str, str]]:
    """(label, href) for each legal document a product registers. Documents are
    never translated here: a language without its own copy links to an existing one."""
    return presentation.policy_docs(site, product, lang)


# ------------------------------------------------------------------- builders
def build_home(site: Site, lang: str) -> str:
    return presentation.home(site, lang, shell, product_content)




def build_products(site: Site, lang: str) -> str:
    return presentation.products(site, lang, shell, product_content)




def build_product_detail(site: Site, product: dict, lang: str) -> str:
    return presentation.detail(site, product, lang, shell, product_content, legal_docs_for)




def play_card(site: Site, game: dict, lang: str) -> str:
    copy, _ = product_content(site, game, lang)
    href = site.url(lang, "play", game["slug"])
    thumb = game.get("images", {}).get("hero")
    img = (f'<img class="card-thumb" src="{thumb}" alt="" loading="lazy" '
           f'width="640" height="360">') if thumb else ""
    return f"""      <li class="card product-card">
        <a class="card-link" href="{href}">
          {img}
          <span class="card-meta">{esc(site.t(lang, "kind.webgame"))}</span>
          <h3>{esc(copy.get("name", game["slug"]))}</h3>
          <p>{esc(copy.get("tagline", ""))}</p>
        </a>
      </li>"""


def build_play_index(site: Site, lang: str) -> str:
    if site.playables:
        cards = "\n".join(play_card(site, g, lang) for g in site.playables)
        listing = f'    <ul class="grid">\n{cards}\n    </ul>'
    else:
        listing = f'    <p class="muted">{esc(site.t(lang, "play.empty"))}</p>'

    body = (f'    <header class="page-head">\n'
            f'      <h1>{esc(site.t(lang, "play.title"))}</h1>\n'
            f'      <p class="lead">{esc(site.t(lang, "play.lead"))}</p>\n'
            f'    </header>\n\n{listing}\n')

    return shell(site, lang=lang, path=site.url(lang, "play"),
                 title=f'{site.t(lang, "play.title")} | {site.config["brand"]}',
                 description=site.t(lang, "play.description"),
                 body=body,
                 alternates={l: site.url(l, "play") for l in site.languages})


def build_play_detail(site: Site, game: dict, lang: str) -> str:
    copy, fallback = product_content(site, game, lang)
    name = copy.get("name", game["slug"])
    embed = game.get("embed", {})

    frame = ""
    if embed.get("src"):
        frame = (f'      <div class="game-stage" style="--game-ratio: '
                 f'{embed.get("width", 16)} / {embed.get("height", 9)}">\n'
                 f'        <iframe src="{esc(embed["src"])}" title="{esc(name)}"\n'
                 f'                allow="autoplay; fullscreen" loading="lazy"></iframe>\n'
                 f'      </div>\n')

    paragraphs = "\n".join(f"      <p>{esc(p)}</p>" for p in copy.get("description", []))

    controls = ""
    if copy.get("controls"):
        items = "\n".join(f"        <li>{esc(c)}</li>" for c in copy["controls"])
        controls = (f'    <section class="section">\n'
                    f'      <h2>{esc(site.t(lang, "play.controls"))}</h2>\n'
                    f'      <ul>\n{items}\n      </ul>\n    </section>\n')

    body = (f'    <article class="product">\n'
            f'      <p class="crumb"><a href="{site.url(lang, "play")}">'
            f'{esc(site.t(lang, "play.title"))}</a></p>\n'
            f'      <h1>{esc(name)}</h1>\n'
            f'      <p class="lead">{esc(copy.get("tagline", ""))}</p>\n'
            f'{frame}'
            f'      <div class="prose">\n{paragraphs}\n      </div>\n'
            f'    </article>\n\n{controls}')

    return shell(site, lang=lang, path=site.url(lang, "play", game["slug"]),
                 title=f'{name} | {site.config["brand"]}',
                 description=copy.get("tagline", name),
                 body=body,
                 alternates={l: site.url(l, "play", game["slug"]) for l in site.languages})


def build_legal_index(site: Site, lang: str) -> str:
    sections = []
    for product in site.products:
        docs = legal_docs_for(site, product, lang)
        if not docs:
            continue
        copy, _ = product_content(site, product, lang)
        items = "\n".join(f'        <li><a href="{href}">{esc(label)}</a></li>'
                          for label, href in docs)
        sections.append(f'    <section class="section">\n'
                        f'      <h2>{esc(copy.get("name", product["slug"]))}</h2>\n'
                        f'      <ul class="link-list">\n{items}\n      </ul>\n    </section>')
    if not sections:
        sections.append(f'    <p class="muted">{esc(site.t(lang, "legal.empty"))}</p>')

    untranslated = any(presentation.doc_language(site, entry, lang) != lang
                       for product in site.products for entry in product.get("legal", []))
    notice = (f'      <p class="notice">{esc(site.t(lang, "legal.fallbackNotice"))}</p>\n'
              if untranslated else "")

    body = (f'    <header class="page-head">\n'
            f'      <h1>{esc(site.t(lang, "legal.title"))}</h1>\n'
            f'      <p class="lead">{esc(site.t(lang, "legal.lead"))}</p>\n'
            f'{notice}'
            f'    </header>\n\n' + "\n\n".join(sections) + "\n")

    return shell(site, lang=lang, path=site.url(lang, "legal"),
                 title=f'{site.t(lang, "legal.title")} | {site.config["brand"]}',
                 description=site.t(lang, "legal.description"),
                 body=body,
                 alternates={l: site.url(l, "legal") for l in site.languages})


def build_legal_doc(site: Site, product: dict, entry: dict, doc_lang: str) -> str:
    source = CONTENT / "legal" / f'{entry["path"]}.{doc_lang}.md'
    copy, _ = product_content(site, product, doc_lang)
    name = copy.get("name", product["slug"])
    label = site.t(doc_lang, f'doc.{entry["doc"]}')

    back = site.url(doc_lang, "products", product["slug"])
    body = (f'    <p class="crumb"><a href="{back}">'
            f'{esc(site.t(doc_lang, "legal.backToProduct", product=name))}</a></p>\n'
            f'    <div class="prose">\n  {render_markdown(source.read_text(encoding="utf-8"))}\n    </div>\n')

    alternates = {l: site.url(l, "legal", entry["path"])
                  for l in entry.get("languages", [site.default_lang])}

    return shell(site, lang=doc_lang, path=site.url(doc_lang, "legal", entry["path"]),
                 title=f'{name} {label} | {site.config["brand"]}',
                 description=f'{label} for {name}, an app by {site.config["brand"]}.',
                 body=body, alternates=alternates, main_class="page")


def build_404(site: Site, lang: str | None = None) -> str:
    """Each language gets a 404.html in its own folder; Pages serves the nearest one."""
    lang = lang or site.default_lang
    body = (f'    <section class="hero">\n'
            f'      <h1>{esc(site.t(lang, "notFound.title"))}</h1>\n'
            f'      <p class="lead">{esc(site.t(lang, "notFound.lead"))}</p>\n'
            f'      <p class="more"><a href="{site.url(lang)}">{esc(site.t(lang, "notFound.back"))}</a></p>\n'
            f'    </section>\n')
    return shell(site, lang=lang, path=site.url(lang) + "404.html",
                 title=f'{site.t(lang, "notFound.title")} | {site.config["brand"]}',
                 description=site.t(lang, "notFound.description"), body=body)


# ----------------------------------------------------------------- collecting
def build_all(site: Site) -> dict[str, str]:
    """Every generated text file, keyed by its path inside dist/."""
    pages: dict[str, str] = {}

    def put(url: str, content: str) -> None:
        rel = url.strip("/")
        pages[f"{rel}/index.html" if rel else "index.html"] = content

    for lang in site.languages:
        put(site.url(lang), build_home(site, lang))
        put(site.url(lang, "products"), build_products(site, lang))
        put(site.url(lang, "about"), presentation.about(site, lang, shell))
        put(site.url(lang, "support"), presentation.support(site, lang, shell))
        put(site.url(lang, "play"), build_play_index(site, lang))
        put(site.url(lang, "legal"), build_legal_index(site, lang))
        for product in site.products:
            put(site.url(lang, "products", product["slug"]),
                build_product_detail(site, product, lang))
        for game in site.playables:
            put(site.url(lang, "play", game["slug"]),
                build_play_detail(site, game, lang))

    # Legal documents follow the document's own languages, not the site's.
    for product in site.products:
        for entry in product.get("legal", []):
            for doc_lang in entry.get("languages", [site.default_lang]):
                put(site.url(doc_lang, "legal", entry["path"]),
                    build_legal_doc(site, product, entry, doc_lang))

    for lang in site.languages:
        pages[site.url(lang).lstrip("/") + "404.html"] = build_404(site, lang)

    redirects = "\n".join(f"{src}  {dst}  {code}"
                          for src, dst, code in site.config.get("redirects", []))
    pages["_redirects"] = redirects + "\n" if redirects else ""

    urls = sorted({("/" + k[: -len("index.html")]).replace("//", "/")
                   for k in pages if k.endswith("index.html")})
    domain = site.config["domain"].rstrip("/")
    pages["sitemap.xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{domain}{u}</loc></url>\n" for u in urls)
        + "</urlset>\n")
    pages["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {domain}/sitemap.xml\n"
    return pages


def copy_static(check_only: bool) -> list[str]:
    """styles.css and assets/ are copied verbatim."""
    problems: list[str] = []
    pairs: list[tuple[Path, Path]] = [
        (ROOT / "styles.css", DIST / "styles.css"),
        (ROOT / "styles.css", DIST / presentation.stylesheet_name()),
    ]
    for src in sorted((ROOT / "assets").rglob("*")):
        if src.is_file():
            pairs.append((src, DIST / "assets" / src.relative_to(ROOT / "assets")))

    for src, dst in pairs:
        if check_only:
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                problems.append(f"{dst.relative_to(ROOT).as_posix()} is stale")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="do not write; fail if dist/ does not match content/")
    args = parser.parse_args()

    site = Site()
    pages = build_all(site)
    problems: list[str] = []

    for rel, content in pages.items():
        target = DIST / rel
        if args.check:
            if not target.exists():
                problems.append(f"dist/{rel} is missing")
            elif target.read_text(encoding="utf-8") != content:
                problems.append(f"dist/{rel} is stale")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")

    problems += copy_static(args.check)

    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        return 1

    if args.check:
        print("check ok")
    else:
        print(f"built {len(pages)} pages + static files into dist/")
        print(f"  languages : {', '.join(site.languages)}")
        print(f"  products  : {', '.join(p['slug'] for p in site.products) or '-'}")
        print(f"  playables : {', '.join(g['slug'] for g in site.playables) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
