"""Presentation templates for the registry-driven Player Zero website."""
from __future__ import annotations

import html
import hashlib
from pathlib import Path
from urllib.parse import quote

from language import menu_href, selection_script


LOGO_SIZE = (969, 627)
SOCIAL_MENU_MIN = 2  # fewer accounts than this are linked directly; more go behind one footer menu


def e(value):
    return html.escape(str(value), quote=True)


def text(lang, english, korean):
    """Legacy two-language pick, kept for old callers. Chrome wording lives in content/i18n: see `ui`."""
    return korean if lang == 'ko' else english


def ui(site, lang, key, **fmt):
    """A chrome string from the i18n `ui` table, {placeholders} filled, with language fallback."""
    return site.t(lang, 'ui.' + key, **fmt)


def strings(site, lang, *keys):
    """A non-string chrome value (a list of paragraphs, say), with language fallback."""
    for candidate in (lang, site.default_lang):
        node = site.strings.get(candidate, {})
        for key in keys:
            node = node.get(key) if isinstance(node, dict) else None
        if node:
            return node
    return None


def language_label(site, lang, code):
    """`code` named in `lang` (英語 on a Japanese page), else in its own name."""
    return strings(site, lang, 'languageNames', code) or site.language_name(code)


def ordered(products):
    return sorted(products, key=lambda p: (p.get('order', 1000), p['slug']))


def copy_for(site, product, lang):
    blocks = product.get('content', {})
    return blocks.get(lang) or blocks.get(site.default_lang) or next(iter(blocks.values()), {})


def platforms(site, lang, product):
    return ' · '.join(site.t(lang, 'platform.' + value) for value in product.get('platforms', []))


def status(site, lang, product):
    return site.t(lang, 'status.' + product.get('status', 'in-development'))


def summary(copy):
    return copy.get('summary') or copy.get('tagline', '')


def how_label(lang, product, site=None):
    game = product.get('kind') == 'game'
    if site is None:
        return text(lang, 'How to play', '플레이 방법') if game else text(lang, 'How to use', '사용 방법')
    return ui(site, lang, 'howToPlay' if game else 'howToUse')


def modes_label(site, lang, product):
    return ui(site, lang, 'waysToPlay' if product.get('kind') == 'game' else 'modes')


def video_for(product, lang):
    """The visitor's localized video, then its English base, then the legacy video."""
    videos = product.get('videos') or {}
    return videos.get(lang) or videos.get('en') or product.get('video')


def video_text(site, lang, product, key, **fmt):
    """A game's video shows gameplay; any other product's is a product video."""
    kind = 'game' if product.get('kind') == 'game' else 'app'
    return ui(site, lang, f'video.{kind}.{key}', **fmt)


def gallery(site, product, lang, name):
    galleries = product.get('galleries', {})
    shots = galleries.get(lang) or galleries.get(site.default_lang) or next(iter(galleries.values()), [])
    if not shots:
        shots = [{'src': src, 'alt': name} for src in product.get('images', {}).get('screenshots', [])]
    return shots


def doc_language(site, entry, lang):
    """The language a legal document opens in: the visitor's if it exists, else the default, else its first."""
    langs = entry.get('languages', [site.default_lang])
    return lang if lang in langs else (site.default_lang if site.default_lang in langs else langs[0])


def policy_docs(site, product, lang):
    """(label, href) for each legal document, in the closest language it exists in.
    A document in another language says which, so nobody opens a policy expecting a translation."""
    out = []
    for entry in product.get('legal', []):
        doc_lang = doc_language(site, entry, lang)
        label = site.t(lang, 'doc.' + entry['doc'])
        if doc_lang != lang:
            label = ui(site, lang, 'docInLanguage', doc=label, language=language_label(site, lang, doc_lang))
        out.append((label, site.url(doc_lang, 'legal', entry['path'])))
    return out


def featured(products):
    """The product the home page leads with: the first featured one in registry order, else the first one."""
    items = ordered(products)
    return next((p for p in items if p.get('featured')), items[0] if items else None)


def brand_mark(cfg):
    """The approved mark for each theme, unaltered. Without a separate dark original, one image serves both."""
    light = cfg.get('logoLight') or cfg['logo']
    dark = cfg.get('logoDark')
    size = f'width="{LOGO_SIZE[0]}" height="{LOGO_SIZE[1]}"'
    if not dark or dark == light:
        return f'<img src="{e(light)}" alt="" {size}>'
    return (f'<img class="brand-light" src="{e(light)}" alt="" {size}>'
            f'<img class="brand-dark" src="{e(dark)}" alt="" {size}>')


def social_links(cfg):
    """(name, url) for each official social account. `socials` is optional; a config with only `youtube` still works."""
    entries = cfg.get('socials')
    if entries is None:
        entries = [{'name': 'YouTube', 'url': cfg['youtube']}] if cfg.get('youtube') else []
    return [(item['name'], item['url']) for item in entries if item.get('name') and item.get('url')]


def social_label(lang, site=None):
    return e(ui(site, lang, 'social')) if site is not None else text(lang, 'Social', 'SNS')


def social_list(cfg):
    """Platform names only: the account names and handles live on the platforms themselves."""
    links = social_links(cfg)
    if not links:
        return ''
    return '<ul class="social-links">' + ''.join(f'<li><a href="{e(url)}">{e(name)}</a></li>' for name, url in links) + '</ul>'


def footer_social(site, lang):
    links = social_links(site.config)
    if len(links) < SOCIAL_MENU_MIN:
        return ''.join(f'<a href="{e(url)}">{e(name)}</a>' for name, url in links)
    items = ''.join(f'<li><a href="{e(url)}">{e(name)}</a></li>' for name, url in links)
    return f'<details class="social-menu"><summary>{social_label(lang, site)}</summary><ul>{items}</ul></details>'


def language_menu(site, lang, path, alternates):
    """Every site language, each in its own name, behind one compact menu. Links keep the visitor on the
    same page where that language has it; otherwise they go to the nearest page it does have.
    The default-language link is explicit (?lang=en) so no browser-language redirect overrides it."""
    if len(site.languages) < 2:
        return ''
    section = 'legal' if path.startswith(site.url(lang, 'legal')) else ''
    items = []
    for code in site.languages:
        name = e(site.language_name(code))
        if code == lang:
            items.append(f'<li><span aria-current="true" lang="{e(code)}">{name}</span></li>')
        else:
            href = menu_href(site, code, alternates.get(code) or site.url(code, section))
            items.append(f'<li><a href="{e(href)}" hreflang="{e(code)}" lang="{e(code)}">{name}</a></li>')
    return (f'<details class="lang-menu"><summary><span class="visually-hidden">{e(ui(site, lang, "language"))} </span>'
            f'{e(site.language_name(lang))}</summary><ul>{"".join(items)}</ul></details>')


def stylesheet_name():
    """A content-addressed filename prevents old browser/CDN CSS from styling new HTML."""
    source = Path(__file__).resolve().parents[1] / 'styles.css'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    return f'styles.{digest}.css'


def shell(site, *, lang, path, title, description, body, alternates=None, main_class='page'):
    cfg = site.config
    domain = cfg['domain'].rstrip('/')
    canonical = domain + path
    nav_items = [('products', site.t(lang, 'nav.products')), ('about', site.t(lang, 'nav.about')), ('support', site.t(lang, 'nav.contact'))]
    if site.playables:
        nav_items.insert(1, ('play', site.t(lang, 'nav.play')))
    nav = []
    for slug, label in nav_items:
        href = site.url(lang, slug)
        current = ' aria-current="page"' if path.startswith(href) else ''
        nav.append(f'<a href="{href}"{current}>{e(label)}</a>')
    alternates = alternates or {}
    switch_html = language_menu(site, lang, path, alternates)
    alternates_html = '\n'.join(f'<link rel="alternate" hreflang="{e(code)}" href="{e(domain + href)}">' for code, href in alternates.items())
    appearance = e(ui(site, lang, 'appearance'))
    image = cfg['logo']
    for product in site.products:
        if '/products/' + product['slug'] + '/' in path:
            image = product.get('images', {}).get('hero', image)
    return f'''<!doctype html>
<!-- Generated from content/ by tool/build.py. -->
<html lang="{e(lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="robots" content="index,follow">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#f4f2ed" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#12100e" media="(prefers-color-scheme: dark)">
  <script>(()=>{{let t='system';try{{const s=localStorage.getItem('player0-theme');if(s==='light'||s==='dark')t=s;}}catch{{}}document.documentElement.dataset.theme=t;}})();</script>
  {selection_script(site, lang, alternates)}
  <link rel="canonical" href="{e(canonical)}">
  {alternates_html}
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{e(canonical)}">
  <meta property="og:image" content="{e(domain + image)}">
  <meta property="og:site_name" content="Player Zero">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="/{stylesheet_name()}">
  <link rel="icon" href="{e(cfg['logo'])}">
</head>
<body>
  <a class="skip-link" href="#main">{e(ui(site, lang, 'skipToContent'))}</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{site.url(lang)}" aria-label="{e(ui(site, lang, 'homeLabel'))}">{brand_mark(cfg)}</a>
      <nav class="site-nav" aria-label="{e(ui(site, lang, 'mainNav'))}">{''.join(nav)}</nav>
      <div class="site-settings">
        <label class="setting-label" for="appearance">{appearance}</label>
        <select id="appearance" aria-label="{appearance}"><option value="system">{e(ui(site, lang, 'themeSystem'))}</option><option value="light">{e(ui(site, lang, 'themeLight'))}</option><option value="dark">{e(ui(site, lang, 'themeDark'))}</option></select>
        {switch_html}
      </div>
    </div>
  </header>
  <main id="main" class="{e(main_class)}">{body}</main>
  <footer class="site-footer">
    <div class="footer-inner">
      <p class="footer-copy">© 2026 Player Zero</p>
      <nav class="footer-links" aria-label="{e(ui(site, lang, 'footerNav'))}"><a href="{site.url(lang, 'products')}">{e(site.t(lang, 'nav.products'))}</a><a href="{site.url(lang, 'about')}">{e(site.t(lang, 'nav.about'))}</a><a href="{site.url(lang, 'support')}">{e(site.t(lang, 'nav.contact'))}</a><a href="{site.url(lang, 'legal')}">{e(site.t(lang, 'legal.title'))}</a><a href="{site.url(lang, 'website-privacy')}">{e(site.t(lang, 'footer.websitePrivacy'))}</a>{footer_social(site, lang)}</nav>
    </div>
  </footer>
  <script>(()=>{{const s=document.getElementById('appearance');const r=document.documentElement;s.value=r.dataset.theme||'system';s.addEventListener('change',()=>{{r.dataset.theme=s.value;try{{if(s.value==='system')localStorage.removeItem('player0-theme');else localStorage.setItem('player0-theme',s.value);}}catch{{}}}});document.querySelectorAll('.social-menu,.lang-menu').forEach(m=>{{m.addEventListener('keydown',ev=>{{if(ev.key==='Escape'&&m.open){{m.open=false;m.querySelector('summary').focus();}}}});document.addEventListener('click',ev=>{{if(m.open&&!m.contains(ev.target))m.open=false;}});}});}})();</script>
</body>
</html>
'''


def button(href, label, secondary=False):
    cls = 'button button-secondary' if secondary else 'button'
    return f'<a class="{cls}" href="{e(href)}">{e(label)}</a>'


def product_link_label(site, lang, link):
    """A product link's localized label, then the default language or legacy label."""
    labels = link.get('labels') or {}
    return (labels.get(lang) or labels.get(site.default_lang) or link.get('label')
            or link.get('platform') or ui(site, lang, 'link'))


def primary_product_link(product):
    """Only an explicitly registered primary link becomes the store action."""
    return next((link for link in product.get('links', [])
                 if link.get('primary') and link.get('url')), None)


def eyebrow(label, number=None):
    prefix = f'<span class="section-number">{e(number)}</span>' if number else ''
    return f'<p class="eyebrow">{prefix}{e(label)}</p>'


def paragraphs(values, cls='body-copy'):
    return '<div class="' + cls + '">' + ''.join(f'<p>{e(v)}</p>' for v in values) + '</div>'


def meta_line(site, lang, product):
    parts = [site.t(lang, 'kind.' + product.get('kind', 'app')), platforms(site, lang, product)]
    items = ''.join(f'<span>{e(part)}</span>' for part in parts if part)
    return f'<p class="meta">{items}<span class="status">{e(status(site, lang, product))}</span></p>'


def facts(site, lang, product):
    rows = [(site.t(lang, 'detail.platforms'), platforms(site, lang, product)),
            (site.t(lang, 'detail.status'), status(site, lang, product))]
    if product.get('status') != 'released':
        rows.append(release_fact(lang, site, product))
    return '<dl class="facts">' + ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows if v) + '</dl>'


def release_fact(lang, site=None, product=None):
    if site is None:
        return text(lang, 'Release', '출시일'), text(lang, 'Date to be announced', '미정')
    release = copy_for(site, product, lang).get('releaseWindow') if product else None
    return ui(site, lang, 'release'), release or ui(site, lang, 'releaseTbd')


def channels(site, lang):
    cfg = site.config
    social = social_list(cfg)
    social_row = f'\n        <li class="channel-social"><span class="channel-label">{social_label(lang, site)}</span>{social}</li>' if social else ''
    return f'''<ul class="channels">
        <li><span class="channel-label">{e(ui(site, lang, 'email'))}</span><a href="mailto:{e(cfg['contact'])}">{e(cfg['contact'])}</a><span class="channel-note">{e(ui(site, lang, 'emailNote'))}</span></li>{social_row}
      </ul>'''


def contact_block(site, lang):
    return f'''<section class="contact-block">
      <h2>{e(site.t(lang, 'nav.contact'))}</h2>
      {channels(site, lang)}
    </section>'''


# ------------------------------------------------------------------ home


def feature_stage(site, product, lang, copy):
    """The featured product: its key art on a stage in the product's own tone, with the facts that matter first."""
    slug, name = product['slug'], copy.get('name', product['slug'])
    detail = site.url(lang, 'products', slug)
    images = product.get('images', {})
    art, alt, size = images.get('cover'), images.get('coverAlt'), (1232, 706)
    if not art:
        art, alt, size = images.get('hero'), images.get('heroAlt'), (1600, 900)
    kicker = ' · '.join(part for part in (site.t(lang, 'kind.' + product.get('kind', 'app')), status(site, lang, product)) if part)
    rows = []
    modes = copy.get('modes') or []
    if modes:
        rows.append((modes_label(site, lang, product), ' · '.join(mode['title'] for mode in modes if mode.get('title'))))
    rows.append((site.t(lang, 'detail.platforms'), platforms(site, lang, product)))
    if product.get('status') != 'released':
        rows.append(release_fact(lang, site, product))
    fact_rows = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows if v)
    lede, tagline = summary(copy), copy.get('tagline', '')
    lines = (f'<p class="feature-summary">{e(lede)}</p>' if lede else '') + (f'<p class="feature-tagline">{e(tagline)}</p>' if tagline and tagline != lede else '')
    figure = (f'<figure class="feature-art"><img src="{e(art)}" alt="{e(alt or name)}" width="{size[0]}" height="{size[1]}" fetchpriority="high"></figure>' if art else '')
    primary = primary_product_link(product)
    actions = button(detail, ui(site, lang, 'viewFeatured', name=name), bool(primary))
    if primary:
        actions = f'<div class="actions">{button(primary["url"], product_link_label(site, lang, primary))}{actions}</div>'
    return f'''<section class="feature tone tone-{e(slug)}{'' if art else ' feature-plain'}" aria-labelledby="feature-{e(slug)}">
      <div class="feature-copy">
        <p class="feature-kicker">{e(kicker)}</p>
        <h2 class="feature-name" id="feature-{e(slug)}">{e(name)}</h2>
        {lines}
        {f'<dl class="feature-facts">{fact_rows}</dl>' if fact_rows else ''}
        {actions}
      </div>
      {figure}
    </section>'''


def lineup_item(site, product, lang, copy, avoid=None):
    """One compact catalog row. `avoid` is the image already shown on the stage, so the row uses another one."""
    slug, name = product['slug'], copy.get('name', product['slug'])
    images = product.get('images', {})
    choices = [src for src in (images.get('cover'), images.get('hero')) if src]
    thumb = next((src for src in choices if src != avoid), choices[0] if choices else None)
    art = (f'<img src="{e(thumb)}" alt="" width="320" height="180">' if thumb
           else f'<span class="lineup-initial" aria-hidden="true">{e(name[:1])}</span>')
    country_sets = product.get('countryGalleries') or {}
    views = country_sets.get(lang) or country_sets.get(site.default_lang) or next(iter(country_sets.values()), [])
    if views:
        preview = [views[i] for i in (1, 2, 4) if i < len(views)] or views[:3]
        art = '<span class="lineup-country-art" aria-hidden="true">' + ''.join(f'<img src="{e(shot["src"])}" alt="" width="1080" height="1920" loading="lazy">' for shot in preview) + '</span>'
    where = platforms(site, lang, product)
    state = product.get('status', 'in-development')
    return f'''<li class="lineup-item lineup-{e(slug)}"><a href="{site.url(lang, 'products', slug)}">
          <span class="lineup-art">{art}</span>
          <div class="lineup-text">
            <p class="lineup-kind">{e(site.t(lang, 'kind.' + product.get('kind', 'app')))}</p>
            <h3 class="lineup-name">{e(name)}</h3>
            <p class="lineup-summary">{e(summary(copy))}</p>
            <p class="lineup-meta">{f'<span>{e(where)}</span>' if where else ''}<span class="lineup-status status-{e(state)}">{e(status(site, lang, product))}</span></p>
          </div>
        </a></li>'''


def country_gallery(site, product, lang, *, home=False):
    galleries = product.get('countryGalleries') or {}
    shots = galleries.get(lang) or galleries.get(site.default_lang) or next(iter(galleries.values()), [])
    if not shots:
        return ''
    copy = copy_for(site, product, lang)
    wording = copy.get('countryGallery') or {}
    name = copy.get('name', product['slug'])
    title = wording.get('title') or name
    ident = ('home-countries-' + product['slug']) if home else 'countries'
    loading = 'lazy' if home else 'eager'
    cards = ''.join(f'<li><figure><a href="{e(shot["src"])}"><img src="{e(shot["src"])}" alt="{e(shot.get("alt", name))}" width="1080" height="1920" loading="{loading}"></a><figcaption><strong>{e(shot.get("country", shot.get("code", "")))}</strong><span>{e(shot.get("city", ""))}</span></figcaption></figure></li>' for shot in shots)
    links = ''
    if home:
        detail_url = site.url(lang, 'products', product['slug'])
        links = button(detail_url, ui(site, lang, 'viewProduct', name=name))
        if product.get('overviewVideo'):
            links += f'<a class="text-link" href="{detail_url}#overview-video">{e(copy.get("overviewVideo", {}).get("link") or video_text(site, lang, product, "watch"))}</a>'
    kind = 'home-country-showcase wrap' if home else 'hero-country-showcase'
    return f'<section class="country-showcase {kind}" id="{ident}" aria-labelledby="{ident}-title"><header><div><p class="country-kicker">{e(name)}</p><h2 id="{ident}-title">{e(title)}</h2><p class="country-lead">{e(wording.get("lead", ""))}</p></div>{f"<div class=actions>{links}</div>" if links else ""}</header><ol class="country-grid">{cards}</ol><p class="country-note">{e(wording.get("note", ""))}</p></section>'


def overview_video(site, product, lang):
    media = product.get('overviewVideo')
    if not media or not media.get('src'):
        return ''
    copy = copy_for(site, product, lang)
    wording = copy.get('overviewVideo') or {}
    name = copy.get('name', product['slug'])
    tracks = ''.join(f'<track kind="subtitles" src="{e(track["src"])}" srclang="{e(track["lang"])}" label="{e(track["label"])}"' + (' default' if track['lang'] == lang else '') + '>' for track in media.get('tracks', []))
    caption = f'<figcaption>{e(wording["caption"])}</figcaption>' if wording.get("caption") else ''
    return f'<section class="block overview-video" id="overview-video"><div><h2>{e(wording.get("title") or video_text(site, lang, product, "link"))}</h2><p>{e(wording.get("lead", ""))}</p></div><figure><video controls playsinline muted preload="none" poster="{e(media.get("poster", ""))}" width="1080" height="1920" aria-label="{e(video_text(site, lang, product, "label", name=name))}"><source src="{e(media["src"])}" type="video/mp4">{tracks}<a href="{e(media["src"])}">{e(video_text(site, lang, product, "open"))}</a></video>{caption}</figure></section>'


def home(site, lang, shell, content):
    lead = featured(site.products)
    stage, avoid = '', None
    if lead:
        copy, _ = content(site, lead, lang)
        stage = feature_stage(site, lead, lang, copy)
        avoid = lead.get('images', {}).get('cover') or lead.get('images', {}).get('hero')
    rows = []
    for product in ordered(site.products):
        copy, _ = content(site, product, lang)
        rows.append(lineup_item(site, product, lang, copy, avoid if product is lead else None))
    listing = (f'<ul class="lineup-list">{"".join(rows)}</ul>' if rows
               else f'<p class="muted lineup-empty">{e(site.t(lang, "products.empty"))}</p>')
    country_sections = ''.join(country_gallery(site, product, lang, home=True) for product in ordered(site.products))
    body = f'''<h1 class="visually-hidden">{e(site.t(lang, 'home.title'))}</h1>
    {stage}
    <section class="lineup wrap" aria-labelledby="lineup-title">
      <div class="lineup-head"><h2 id="lineup-title">{e(site.t(lang, 'home.catalog'))}</h2><a class="text-link" href="{site.url(lang, 'products')}">{e(site.t(lang, 'home.catalogLink'))}</a></div>
      {listing}
    </section>
    {country_sections}
    <section class="company" aria-labelledby="company-title">
      <div class="wrap company-inner">
        <div class="company-about"><h2 id="company-title">{e(site.t(lang, 'home.aboutTitle'))}</h2><p>{e(site.t(lang, 'home.about'))}</p><a class="text-link" href="{site.url(lang, 'about')}">{e(site.t(lang, 'home.aboutLink'))}</a></div>
        <div class="company-contact"><h2>{e(site.t(lang, 'home.contactTitle'))}</h2>{channels(site, lang)}</div>
      </div>
    </section>'''
    return shell(site, lang=lang, path=site.url(lang), title=site.t(lang, 'home.title'), description=site.t(lang, 'home.description'), body=body, alternates={l: site.url(l) for l in site.languages}, main_class='page-wide page-home')


# -------------------------------------------------------------- products


def project_row(site, product, lang, content):
    slug = product['slug']
    copy, _ = content(site, product, lang)
    name = copy.get('name', slug)
    images = product.get('images', {})
    image = images.get('cover') or images.get('hero')
    alt = images.get('coverAlt') or images.get('heroAlt') or name
    detail = site.url(lang, 'products', slug)
    video = video_for(product, lang)
    media = (f'<img src="{e(image)}" alt="{e(alt)}" width="1232" height="706" loading="lazy">' if image
             else f'<span class="placeholder">{e(name)}</span>')
    links = []
    if copy.get('howTo'):
        links.append((how_label(lang, product, site), detail + '#how-to'))
    if video:
        links.append((video_text(site, lang, product, 'link'), detail + '#gameplay'))
    if product.get('overviewVideo'):
        links.append((copy.get('overviewVideo', {}).get('link') or video_text(site, lang, product, 'watch'), detail + '#overview-video'))
    if copy.get('faq'):
        links.append((ui(site, lang, 'faqShort'), detail + '#faq'))
    links += policy_docs(site, product, lang)
    primary = primary_product_link(product)
    links += [(product_link_label(site, lang, link), link['url'])
              for link in product.get('links', []) if link is not primary]
    primary_action = button(primary['url'], product_link_label(site, lang, primary)) if primary else ''
    link_html = ''.join(f'<a class="text-link" href="{e(href)}">{e(label)}</a>' for label, href in links)
    return f'''<article class="catalog-item catalog-{e(slug)}">
      <a class="catalog-art" href="{detail}" tabindex="-1">{media}</a>
      <div class="catalog-copy">
        <p class="catalog-summary">{e(summary(copy))}</p>
        <h2><a href="{detail}">{e(name)}</a></h2>
        <p class="catalog-tagline">{e(copy.get('tagline', ''))}</p>
        {paragraphs(copy.get('description', [])[:2])}
        {facts(site, lang, product)}
        <div class="actions">{primary_action}{button(detail, ui(site, lang, 'viewProduct', name=name), bool(primary))}{link_html}</div>
      </div>
    </article>'''


def products(site, lang, shell, content):
    rows = ''.join(project_row(site, p, lang, content) for p in ordered(site.products))
    if not rows:
        rows = f'<p class="muted">{e(site.t(lang, "products.empty"))}</p>'
    body = f'''<header class="page-intro"><h1>{e(site.t(lang, 'products.title'))}</h1><p class="lead">{e(site.t(lang, 'products.lead'))}</p></header>
      <section class="catalog">{rows}</section>
      {contact_block(site, lang)}'''
    return shell(site, lang=lang, path=site.url(lang, 'products'), title=site.t(lang, 'products.title') + ' | Player Zero', description=site.t(lang, 'products.description'), body=body, alternates={l: site.url(l, 'products') for l in site.languages})


# ---------------------------------------------------------------- detail


def feature_list(items):
    return '<ul class="feature-list">' + ''.join(f'<li><h3>{e(item["title"])}</h3><p>{e(item["body"])}</p></li>' for item in items) + '</ul>'


def steps_list(items):
    return '<ol class="steps">' + ''.join(f'<li><h3>{e(item["title"])}</h3><p>{e(item["body"])}</p></li>' for item in items) + '</ol>'


def detail(site, product, lang, shell, content, legal_docs):
    copy, fallback = content(site, product, lang)
    slug = product['slug']
    name = copy.get('name', slug)
    game = product.get('kind') == 'game'
    how = how_label(lang, product, site)
    docs = legal_docs(site, product, lang)
    images = product.get('images', {})
    shots = gallery(site, product, lang, name)
    modes, steps = copy.get('modes') or [], copy.get('howTo') or []
    pictured = bool(game and modes and len(shots) == len(modes))
    video = video_for(product, lang)

    primary = primary_product_link(product)
    actions = [button(primary['url'], product_link_label(site, lang, primary))] if primary else []
    if steps:
        actions.append(button('#how-to', how, bool(actions)))
    if video:
        actions.append(button('#gameplay', video_text(site, lang, product, 'watch'), bool(actions)))
    if product.get('overviewVideo'):
        actions.append(button('#overview-video', copy.get('overviewVideo', {}).get('link') or video_text(site, lang, product, 'watch'), True))
    actions += [button(href, label, True) for label, href in docs[:1]]
    actions += [button(link['url'], product_link_label(site, lang, link), True)
                for link in product.get('links', []) if link is not primary]
    notice = f'<p class="notice">{e(site.t(lang, "detail.fallbackNotice", language=language_label(site, lang, fallback)))}</p>' if fallback else ''

    media = ''
    hero = images.get('hero')
    if video:
        video = e(video)
        posters = product.get('videoPosters') or {}
        poster_url = posters.get(lang) or posters.get('en') or hero
        poster = f' poster="{e(poster_url)}"' if poster_url else ''
        caption = f'<figcaption>{e(video_text(site, lang, product, "caption"))}</figcaption>' if game else ''
        media = f'''<figure class="hero-media" id="gameplay"><video controls playsinline preload="none"{poster} aria-label="{e(video_text(site, lang, product, 'label', name=name))}"><source src="{video}" type="video/mp4"><a href="{video}">{e(video_text(site, lang, product, 'open'))}</a></video>{caption}</figure>'''
    elif hero:
        media = f'<figure class="hero-media hero-art"><img src="{e(hero)}" alt="{e(images.get("heroAlt", name))}" width="1024" height="500" fetchpriority="high"></figure>'

    blocks = [f'<section class="block block-split"><h2>{e(ui(site, lang, "aboutProduct", name=name))}</h2>{paragraphs(copy.get("description", []))}</section>']

    if product.get('countryGalleries'):
        media = country_gallery(site, product, lang)
    if product.get('overviewVideo'):
        blocks.append(overview_video(site, product, lang))

    if shots and not pictured:
        heading = ui(site, lang, 'screenshotsGame' if game else 'screenshotsApp')
        cls = 'gallery' if game else 'gallery gallery-portrait'
        figures = ''.join(
            f'<figure><a href="{e(shot["src"])}"><img src="{e(shot["src"])}" alt="{e(shot.get("alt", name))}" loading="lazy" width="{1280 if game else 540}" height="{720 if game else 960}"></a>'
            + (f'<figcaption>{e(shot["caption"])}</figcaption>' if shot.get('caption') else '') + '</figure>'
            for shot in shots)
        blocks.append(f'<section class="block"><h2>{e(heading)}</h2><div class="{cls}">{figures}</div></section>')

    if modes:
        items = []
        for i, mode in enumerate(modes):
            pic = (f'<img src="{e(shots[i]["src"])}" alt="{e(shots[i].get("alt", mode["title"]))}" width="1280" height="720" loading="lazy">' if pictured else '')
            items.append(f'<li class="mode">{pic}<h3>{e(mode["title"])}</h3><p>{e(mode["body"])}</p></li>')
        cls = 'mode-list mode-list-pictured' if pictured else 'mode-list'
        blocks.append(f'<section class="block" id="modes"><h2>{e(modes_label(site, lang, product))}</h2><ol class="{cls}">{"".join(items)}</ol></section>')

    if steps:
        blocks.append(f'<section class="block" id="how-to"><h2>{e(how)}</h2>{steps_list(steps)}</section>')

    if copy.get('features'):
        blocks.append(f'<section class="block"><h2>{e(ui(site, lang, "features"))}</h2>{feature_list(copy["features"])}</section>')

    if copy.get('faq'):
        faq = ''.join(f'<details><summary>{e(q["question"])}</summary><p>{e(q["answer"])}</p></details>' for q in copy['faq'])
        blocks.append(f'<section class="block block-split" id="faq"><h2>{e(ui(site, lang, "faq"))}</h2><div class="faq-list">{faq}</div></section>')

    if docs:
        policy = ''.join(f'<a class="text-link" href="{e(href)}">{e(label)}</a>' for label, href in docs)
        blocks.append(f'<section class="block block-split"><h2>{e(site.t(lang, "detail.legal"))}</h2><div class="link-row">{policy}</div></section>')

    contact = site.config['contact']
    subject = quote(name)
    support_url = site.url(lang, 'support') + '#' + slug
    blocks.append(f'''<section class="block product-contact"><h2>{e(ui(site, lang, 'productQuestions', name=name))}</h2>
        <div class="actions"><a class="button button-secondary" href="mailto:{e(contact)}?subject={e(subject)}">{e(contact)}</a><a class="text-link" href="{support_url}">{e(ui(site, lang, 'contactSupport'))}</a></div></section>''')

    body = f'''<article class="product-page product-page-{e(slug)}">
      <header class="product-hero tone tone-{e(slug)}">
        <div class="wrap">
          <p class="crumb"><a href="{site.url(lang, 'products')}">{e(site.t(lang, 'nav.products'))}</a><span aria-hidden="true">/</span><span>{e(name)}</span></p>
          <div class="product-hero-top">
            <div><p class="product-summary">{e(summary(copy))}</p><h1>{e(name)}</h1><p class="product-lead">{e(copy.get('tagline', ''))}</p></div>
            <div class="product-hero-side">{facts(site, lang, product)}<div class="actions">{''.join(actions)}</div></div>
          </div>
          {notice}
          {media}
        </div>
      </header>
      <div class="wrap">{''.join(blocks)}</div>
    </article>'''
    return shell(site, lang=lang, path=site.url(lang, 'products', slug), title=f'{name} | Player Zero', description=copy.get('tagline', name), body=body, alternates={l: site.url(l, 'products', slug) for l in site.languages}, main_class='page-wide page-product')


def website_privacy(site, lang, shell):
    """Company website notice, separate from every product's app policy."""
    localized = site.website_privacy['content']
    copy = localized.get(lang) or localized[site.default_lang]
    sections = ''.join(f'<section><h2>{e(item["title"])}</h2>{paragraphs(item["paragraphs"])}</section>'
                       for item in copy['sections'])
    references = ''.join(f'<li><a href="{e(item["url"])}">{e(item["label"])}</a></li>'
                         for item in site.website_privacy.get('references', []))
    email = site.config['contact']
    body = f'''<header class="page-intro"><h1>{e(site.t(lang, 'websitePrivacy.title'))}</h1><p class="lead">{e(site.t(lang, 'websitePrivacy.lead'))}</p></header>
      <div class="prose">{sections}<section><h2>{e(site.t(lang, 'websitePrivacy.references'))}</h2><ul>{references}</ul></section>
      <section><h2>{e(site.t(lang, 'websitePrivacy.contact'))}</h2><p><a href="mailto:{e(email)}">{e(email)}</a></p></section></div>'''
    return shell(site, lang=lang, path=site.url(lang, 'website-privacy'),
                 title=site.t(lang, 'websitePrivacy.title') + ' | Player Zero',
                 description=site.t(lang, 'websitePrivacy.description'), body=body,
                 alternates={code: site.url(code, 'website-privacy') for code in site.languages})


# ------------------------------------------------------- about & support


def about(site, lang, shell):
    lead = site.t(lang, 'about.lead')
    cfg = site.config
    rows = [
        (ui(site, lang, 'company'), 'Player Zero'),
        (ui(site, lang, 'whatWeMake'), ui(site, lang, 'gamesAndApps')),
        (ui(site, lang, 'website'), cfg['domain'].split('//')[-1].rstrip('/')),
    ]
    fact_rows = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows)
    fact_rows += f'<div><dt>{e(ui(site, lang, "email"))}</dt><dd><a href="mailto:{e(cfg["contact"])}">{e(cfg["contact"])}</a></dd></div>'
    social = social_list(cfg)
    if social:
        fact_rows += f'<div><dt>{social_label(lang, site)}</dt><dd>{social}</dd></div>'
    # The company page says who we are; the products page is the catalog, so this only points to it.
    onward = f'<p class="about-onward"><a class="text-link" href="{site.url(lang, "products")}">{e(site.t(lang, "about.productsLink"))}</a></p>'
    body = f'''<header class="page-intro"><h1>{e(site.t(lang, 'about.title'))}</h1><p class="lead">{e(lead)}</p></header>
      <section class="about-body"><div class="about-text">{paragraphs(strings(site, lang, 'about', 'paragraphs') or [])}{onward}</div><dl class="about-facts">{fact_rows}</dl></section>'''
    return shell(site, lang=lang, path=site.url(lang, 'about'), title=site.t(lang, 'about.title') + ' | Player Zero', description=site.t(lang, 'about.description'), body=body, alternates={l: site.url(l, 'about') for l in site.languages})


def support(site, lang, shell):
    cfg = site.config
    social = social_list(cfg)
    lead = ui(site, lang, 'supportLead')
    title = ui(site, lang, 'contactSupport')
    blocks = []
    for p in ordered(site.products):
        slug = p['slug']
        copy = copy_for(site, p, lang)
        name = copy.get('name', slug)
        # The subject stays English in every language: it sorts mail in the shared inbox.
        subject = quote(name + ' support')
        detail = site.url(lang, 'products', slug)
        links = [f'<a class="text-link" href="mailto:{e(cfg["contact"])}?subject={e(subject)}">{e(ui(site, lang, "emailAbout", name=name))}</a>']
        if copy.get('faq'):
            links.append(f'<a class="text-link" href="{detail}#faq">{e(ui(site, lang, "productFaq", name=name))}</a>')
        else:
            links.append(f'<a class="text-link" href="{detail}">{e(ui(site, lang, "aboutProduct", name=name))}</a>')
        links += [f'<a class="text-link" href="{e(href)}">{e(label)}</a>' for label, href in policy_docs(site, p, lang)]
        line = ' · '.join(part for part in (summary(copy), platforms(site, lang, p)) if part)
        blocks.append(f'''<article class="support-product" id="{e(slug)}"><h2>{e(name)}</h2><p>{e(line)}</p><div class="link-stack">{''.join(links)}</div></article>''')
    if not blocks:
        blocks.append(f'<p class="muted">{e(site.t(lang, "products.empty"))}</p>')
    checklist = strings(site, lang, 'ui', 'checklist') or []
    body = f'''<header class="page-intro"><h1>{e(title)}</h1><p class="lead">{e(lead)}</p></header>
      <section class="support-main">
        <div class="support-mail"><p class="muted">{e(ui(site, lang, 'email'))}</p><a href="mailto:{e(cfg['contact'])}">{e(cfg['contact'])}</a>{f'<div class="support-social"><p class="muted">{social_label(lang, site)}</p>{social}</div>' if social else ''}</div>
        <div class="support-grid">{''.join(blocks)}</div>
      </section>
      <section class="support-notes">
        <h2>{e(ui(site, lang, 'reportTitle'))}</h2>
        <div><p>{e(ui(site, lang, 'reportIntro'))}</p><ul class="checklist">{''.join(f'<li>{e(item)}</li>' for item in checklist)}</ul></div>
      </section>'''
    return shell(site, lang=lang, path=site.url(lang, 'support'), title=title + ' | Player Zero', description=lead, body=body, alternates={l: site.url(l, 'support') for l in site.languages})
