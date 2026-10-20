"""Presentation templates for the registry-driven Player Zero website."""
from __future__ import annotations

import html
from urllib.parse import quote


YOUTUBE_NAME = 'Player Zero Dev'
YOUTUBE_HANDLE = '@player0dev'


def e(value):
    return html.escape(str(value), quote=True)


def text(lang, english, korean):
    return korean if lang == 'ko' else english


def strings(site, lang, *keys):
    """A non-string chrome value (a list of paragraphs, say), with language fallback."""
    for candidate in (lang, site.default_lang):
        node = site.strings.get(candidate, {})
        for key in keys:
            node = node.get(key) if isinstance(node, dict) else None
        if node:
            return node
    return None


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


def how_label(lang, product):
    if product.get('kind') == 'game':
        return text(lang, 'How to play', '플레이 방법')
    return text(lang, 'How to use', '사용 방법')


def gallery(site, product, lang, name):
    galleries = product.get('galleries', {})
    shots = galleries.get(lang) or galleries.get(site.default_lang) or next(iter(galleries.values()), [])
    if not shots:
        shots = [{'src': src, 'alt': name} for src in product.get('images', {}).get('screenshots', [])]
    return shots


def policy_docs(site, product, lang):
    """(label, href) for each legal document, in the closest language it exists in."""
    out = []
    for entry in product.get('legal', []):
        langs = entry.get('languages', [site.default_lang])
        doc_lang = lang if lang in langs else (site.default_lang if site.default_lang in langs else langs[0])
        label = site.t(lang, 'doc.' + entry['doc'])
        if doc_lang != lang:
            label += f' ({site.language_name(doc_lang)})'
        out.append((label, site.url(doc_lang, 'legal', entry['path'])))
    return out


def shell(site, *, lang, path, title, description, body, alternates=None, main_class='page'):
    cfg = site.config
    domain = cfg['domain'].rstrip('/')
    canonical = domain + path
    nav_items = [('products', text(lang, 'Products', '제품')), ('about', text(lang, 'About', '회사 소개')), ('support', text(lang, 'Contact', '문의'))]
    if site.playables:
        nav_items.insert(1, ('play', site.t(lang, 'nav.play')))
    nav = []
    for slug, label in nav_items:
        href = site.url(lang, slug)
        current = ' aria-current="page"' if path.startswith(href) else ''
        nav.append(f'<a href="{href}"{current}>{e(label)}</a>')
    alternates = alternates or {}
    switches = []
    for code, href in alternates.items():
        label = 'EN' if code == 'en' else site.language_name(code)
        if code == lang:
            switches.append(f'<span aria-current="true">{e(label)}</span>')
        else:
            switches.append(f'<a href="{e(href)}" hreflang="{e(code)}" lang="{e(code)}">{e(label)}</a>')
    switch_html = f'<div class="lang-switch" role="group" aria-label="{text(lang, "Language", "언어")}">{"".join(switches)}</div>' if switches else ''
    alternates_html = '\n'.join(f'<link rel="alternate" hreflang="{e(code)}" href="{e(domain + href)}">' for code, href in alternates.items())
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
  <meta name="theme-color" content="#f6f5f1" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#121216" media="(prefers-color-scheme: dark)">
  <script>(()=>{{let t='system';try{{const s=localStorage.getItem('player0-theme');if(s==='light'||s==='dark')t=s;}}catch{{}}document.documentElement.dataset.theme=t;}})();</script>
  <link rel="canonical" href="{e(canonical)}">
  {alternates_html}
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{e(canonical)}">
  <meta property="og:image" content="{e(domain + image)}">
  <meta property="og:site_name" content="Player Zero">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="/styles.css">
  <link rel="icon" href="{e(cfg['logo'])}">
</head>
<body>
  <a class="skip-link" href="#main">{text(lang, 'Skip to content', '본문으로 이동')}</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{site.url(lang)}" aria-label="{text(lang, 'Player Zero home', 'Player Zero 홈')}"><img src="{e(cfg['logo'])}" alt="" width="40" height="40"><span class="brand-name">Player Zero</span></a>
      <nav class="site-nav" aria-label="{text(lang, 'Main navigation', '주요 메뉴')}">{''.join(nav)}</nav>
      <div class="site-settings">
        <select id="appearance" aria-label="{text(lang, 'Appearance', '화면 테마')}"><option value="system">{text(lang, 'System', '시스템')}</option><option value="light">{text(lang, 'Light', '밝게')}</option><option value="dark">{text(lang, 'Dark', '어둡게')}</option></select>
        {switch_html}
      </div>
    </div>
  </header>
  <main id="main" class="{e(main_class)}">{body}</main>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-id"><p class="footer-brand">Player Zero</p><p>{text(lang, 'Games and apps', '게임과 앱')}</p></div>
      <nav class="footer-links" aria-label="{text(lang, 'Footer', '하단 메뉴')}"><a href="{site.url(lang, 'products')}">{text(lang, 'Products', '제품')}</a><a href="{site.url(lang, 'about')}">{text(lang, 'About', '회사 소개')}</a><a href="{site.url(lang, 'support')}">{text(lang, 'Contact', '문의')}</a><a href="{e(cfg['youtube'])}">YouTube</a><a href="{site.url(lang, 'legal')}">{e(site.t(lang, 'legal.title'))}</a></nav>
      <div class="footer-bottom"><p>© 2026 Player Zero</p><a href="mailto:{e(cfg['contact'])}">{e(cfg['contact'])}</a></div>
    </div>
  </footer>
  <script>(()=>{{const s=document.getElementById('appearance');const r=document.documentElement;s.value=r.dataset.theme||'system';s.addEventListener('change',()=>{{r.dataset.theme=s.value;try{{if(s.value==='system')localStorage.removeItem('player0-theme');else localStorage.setItem('player0-theme',s.value);}}catch{{}}}});}})();</script>
</body>
</html>
'''


def button(href, label, secondary=False):
    cls = 'button button-secondary' if secondary else 'button'
    return f'<a class="{cls}" href="{e(href)}">{e(label)}</a>'


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
        rows.append((text(lang, 'Release', '출시'), text(lang, 'Date to be announced', '출시일 미정')))
    return '<dl class="facts">' + ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows if v) + '</dl>'


def channels(site, lang):
    cfg = site.config
    return f'''<ul class="channels">
        <li><span class="channel-label">{text(lang, 'Email', '이메일')}</span><a href="mailto:{e(cfg['contact'])}">{e(cfg['contact'])}</a><span class="channel-note">{text(lang, 'Product support, press and business enquiries', '제품 문의, 취재, 협업 제안')}</span></li>
        <li><span class="channel-label">YouTube</span><a href="{e(cfg['youtube'])}">{YOUTUBE_NAME}<span class="handle">{YOUTUBE_HANDLE}</span></a><span class="channel-note">{text(lang, 'Development updates', '개발 소식')}</span></li>
      </ul>'''


def contact_block(site, lang):
    return f'''<section class="contact-block">
      <div><h2>{text(lang, 'Get in touch', '연락하기')}</h2><p>{text(lang, 'Questions, feedback and enquiries all go to the same inbox.', '질문, 의견, 각종 문의는 모두 같은 메일로 받습니다.')}</p></div>
      {channels(site, lang)}
    </section>'''


# ------------------------------------------------------------------ home


def index_row(site, product, lang, copy):
    slug, name = product['slug'], copy.get('name', product['slug'])
    images = product.get('images', {})
    thumb = images.get('cover') or images.get('hero')
    art = (f'<img src="{e(thumb)}" alt="" width="160" height="90">' if thumb
           else f'<span class="index-initial" aria-hidden="true">{e(name[:1])}</span>')
    where = ' · '.join(part for part in (platforms(site, lang, product), status(site, lang, product)) if part)
    return f'''<li class="index-item index-{e(slug)}"><a href="{site.url(lang, 'products', slug)}">
          <span class="index-art">{art}</span>
          <span class="index-text"><span class="index-name">{e(name)}</span><span class="index-summary">{e(summary(copy))}</span><span class="index-meta">{e(where)}</span></span>
        </a></li>'''


def spotlight(site, product, lang, copy):
    """One product, presented with its own imagery and how it is played or used."""
    slug, name = product['slug'], copy.get('name', product['slug'])
    detail = site.url(lang, 'products', slug)
    images = product.get('images', {})
    game = product.get('kind') == 'game'
    shots = gallery(site, product, lang, name)
    hero = images.get('hero') or images.get('cover')
    upright = not game and bool(shots)
    if upright:
        media = '<div class="phones">' + ''.join(
            f'<figure class="phone"><img src="{e(shot["src"])}" alt="{e(shot.get("alt", name))}" width="540" height="960" loading="lazy">'
            + (f'<figcaption>{e(shot["caption"])}</figcaption>' if shot.get('caption') else '') + '</figure>'
            for shot in shots[:3]) + '</div>'
    elif hero:
        media = f'<img class="spotlight-shot" src="{e(hero)}" alt="{e(images.get("heroAlt", name))}" width="1600" height="900" loading="lazy">'
    else:
        media = f'<span class="placeholder">{e(name)}</span>'

    modes, steps = copy.get('modes') or [], copy.get('howTo') or []
    points_html = ''
    if modes or steps:
        points = modes or steps
        pictured = game and modes and len(shots) >= len(modes)
        heading = text(lang, 'Ways to play', '연주 방식') if modes else how_label(lang, product)
        items = []
        for i, point in enumerate(points):
            pic = (f'<img src="{e(shots[i]["src"])}" alt="{e(shots[i].get("alt", point["title"]))}" width="1280" height="720" loading="lazy">' if pictured else '')
            items.append(f'<li class="point">{pic}<h4>{e(point["title"])}</h4><p>{e(point["body"])}</p></li>')
        cls = 'points points-pictured' if pictured else 'points points-numbered'
        points_html = f'<div class="spotlight-points"><h3>{e(heading)}</h3><ol class="{cls}">{"".join(items)}</ol></div>'

    actions = []
    if steps:
        actions.append(button(detail + '#how-to', how_label(lang, product)))
    else:
        actions.append(button(detail, text(lang, 'View ' + name, name + ' 보기')))
    if product.get('video'):
        actions.append(button(detail + '#gameplay', text(lang, 'Watch gameplay', '플레이 영상 보기'), True))
    if steps:
        actions.append(f'<a class="text-link" href="{detail}">{e(text(lang, "More about " + name, name + " 자세히 보기"))}</a>')
    lead = (copy.get('description') or [''])[0]
    kind = 'spotlight-app' if upright else 'spotlight-game'
    return f'''<section class="spotlight {kind} tone tone-{e(slug)}" id="{e(slug)}" aria-labelledby="{e(slug)}-name">
      <div class="wrap">
        <div class="spotlight-main">
          <div class="spotlight-title">{meta_line(site, lang, product)}<h2 id="{e(slug)}-name"><a href="{detail}">{e(name)}</a></h2><p class="spotlight-tagline">{e(copy.get('tagline', ''))}</p></div>
          <div class="spotlight-media">{media}</div>
          <div class="spotlight-body"><p>{e(lead)}</p><div class="actions">{''.join(actions)}</div></div>
        </div>
        {points_html}
      </div>
    </section>'''


def home(site, lang, shell, content):
    products = ordered(site.products)
    rows, spotlights = [], []
    for product in products:
        copy, _ = content(site, product, lang)
        rows.append(index_row(site, product, lang, copy))
        spotlights.append(spotlight(site, product, lang, copy))
    listing = (f'<ul class="index-list">{"".join(rows)}</ul>' if rows
               else f'<p class="muted">{e(site.t(lang, "products.empty"))}</p>')
    lead = site.t(lang, 'home.lead')
    body = f'''<section class="home-intro wrap">
      <div class="home-intro-copy"><h1>Player Zero</h1><p class="lead">{e(lead)}</p></div>
      <div class="home-index"><h2>{e(site.t(lang, 'home.current'))}</h2>{listing}</div>
    </section>
    {''.join(spotlights)}
    <section class="studio wrap">
      <div class="studio-about"><h2>{e(site.t(lang, 'home.aboutTitle'))}</h2><p>{e(site.t(lang, 'home.about'))}</p><a class="text-link" href="{site.url(lang, 'about')}">{e(site.t(lang, 'home.aboutLink'))}</a></div>
      <div class="studio-contact"><h2>{text(lang, 'Get in touch', '연락하기')}</h2>{channels(site, lang)}</div>
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
    media = (f'<img src="{e(image)}" alt="{e(alt)}" width="1232" height="706" loading="lazy">' if image
             else f'<span class="placeholder">{e(name)}</span>')
    links = []
    if copy.get('howTo'):
        links.append((how_label(lang, product), detail + '#how-to'))
    if product.get('video'):
        links.append((text(lang, 'Gameplay video', '플레이 영상'), detail + '#gameplay'))
    if copy.get('faq'):
        links.append((text(lang, 'FAQ', '자주 묻는 질문'), detail + '#faq'))
    links += policy_docs(site, product, lang)
    links += [(link.get('label', link.get('platform', 'Link')), link['url']) for link in product.get('links', [])]
    link_html = ''.join(f'<a class="text-link" href="{e(href)}">{e(label)}</a>' for label, href in links)
    return f'''<article class="catalog-item catalog-{e(slug)}">
      <a class="catalog-art" href="{detail}" tabindex="-1">{media}</a>
      <div class="catalog-copy">
        <p class="catalog-summary">{e(summary(copy))}</p>
        <h2><a href="{detail}">{e(name)}</a></h2>
        <p class="catalog-tagline">{e(copy.get('tagline', ''))}</p>
        {paragraphs(copy.get('description', [])[:2])}
        {facts(site, lang, product)}
        <div class="actions">{button(detail, text(lang, 'View ' + name, name + ' 보기'))}{link_html}</div>
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
    how = how_label(lang, product)
    docs = legal_docs(site, product, lang)
    images = product.get('images', {})
    shots = gallery(site, product, lang, name)
    modes, steps = copy.get('modes') or [], copy.get('howTo') or []
    pictured = bool(game and modes and len(shots) == len(modes))

    actions = []
    if steps:
        actions.append(button('#how-to', how))
    if product.get('video'):
        actions.append(button('#gameplay', text(lang, 'Watch gameplay', '플레이 영상 보기'), bool(actions)))
    actions += [button(href, label, True) for label, href in docs[:1]]
    actions += [button(link['url'], link.get('label', link.get('platform', 'Link')), True) for link in product.get('links', [])]
    notice = f'<p class="notice">{e(site.t(lang, "detail.fallbackNotice", language=site.language_name(fallback)))}</p>' if fallback else ''

    media = ''
    hero = images.get('hero')
    if product.get('video'):
        video = e(product['video'])
        poster = f' poster="{e(hero)}"' if hero else ''
        media = f'''<figure class="hero-media" id="gameplay"><video controls playsinline preload="none"{poster} aria-label="{e(name + text(lang, ' gameplay video', ' 플레이 영상'))}"><source src="{video}" type="video/mp4"><a href="{video}">{text(lang, 'Open the gameplay video', '플레이 영상 열기')}</a></video><figcaption>{text(lang, 'Actual gameplay from the version in development', '개발 중인 버전의 실제 플레이 화면')}</figcaption></figure>'''
    elif hero:
        media = f'<figure class="hero-media hero-art"><img src="{e(hero)}" alt="{e(images.get("heroAlt", name))}" width="1024" height="500" fetchpriority="high"></figure>'

    blocks = [f'<section class="block block-split"><h2>{e(text(lang, "About " + name, name + " 소개"))}</h2>{paragraphs(copy.get("description", []))}</section>']

    if shots and not pictured:
        heading = text(lang, 'Screenshots', '게임 화면') if game else text(lang, 'In the app', '앱 화면')
        cls = 'gallery' if game else 'gallery gallery-portrait'
        figures = ''.join(
            f'<figure><a href="{e(shot["src"])}"><img src="{e(shot["src"])}" alt="{e(shot.get("alt", name))}" loading="lazy" width="{1280 if game else 540}" height="{720 if game else 960}"></a>'
            + (f'<figcaption>{e(shot["caption"])}</figcaption>' if shot.get('caption') else '') + '</figure>'
            for shot in shots)
        blocks.append(f'<section class="block"><h2>{heading}</h2><div class="{cls}">{figures}</div></section>')

    if modes:
        items = []
        for i, mode in enumerate(modes):
            pic = (f'<img src="{e(shots[i]["src"])}" alt="{e(shots[i].get("alt", mode["title"]))}" width="1280" height="720" loading="lazy">' if pictured else '')
            items.append(f'<li class="mode">{pic}<h3>{e(mode["title"])}</h3><p>{e(mode["body"])}</p></li>')
        cls = 'mode-list mode-list-pictured' if pictured else 'mode-list'
        blocks.append(f'<section class="block" id="modes"><h2>{text(lang, "Ways to play", "연주 방식")}</h2><ol class="{cls}">{"".join(items)}</ol></section>')

    if steps:
        blocks.append(f'<section class="block" id="how-to"><h2>{e(how)}</h2>{steps_list(steps)}</section>')

    if copy.get('features'):
        blocks.append(f'<section class="block"><h2>{text(lang, "Features", "주요 기능")}</h2>{feature_list(copy["features"])}</section>')

    if copy.get('faq'):
        faq = ''.join(f'<details><summary>{e(q["question"])}</summary><p>{e(q["answer"])}</p></details>' for q in copy['faq'])
        blocks.append(f'<section class="block block-split" id="faq"><h2>{text(lang, "Frequently asked questions", "자주 묻는 질문")}</h2><div class="faq-list">{faq}</div></section>')

    if docs:
        policy = ''.join(f'<a class="text-link" href="{e(href)}">{e(label)}</a>' for label, href in docs)
        blocks.append(f'<section class="block block-split"><h2>{e(site.t(lang, "detail.legal"))}</h2><div class="link-row">{policy}</div></section>')

    contact = site.config['contact']
    subject = quote(name)
    support_url = site.url(lang, 'support') + '#' + slug
    blocks.append(f'''<section class="block product-contact"><div><h2>{e(text(lang, 'Questions about ' + name + '?', name + '에 대해 궁금한 점이 있나요?'))}</h2><p>{text(lang, 'Write to us. Feedback is welcome too.', '메일로 보내주세요. 의견도 언제든 환영합니다.')}</p></div>
        <div class="actions"><a class="button button-secondary" href="mailto:{e(contact)}?subject={e(subject)}">{e(contact)}</a><a class="text-link" href="{support_url}">{text(lang, 'Contact & support', '문의 및 지원')}</a></div></section>''')

    body = f'''<article class="product-page product-page-{e(slug)}">
      <header class="product-hero tone tone-{e(slug)}">
        <div class="wrap">
          <p class="crumb"><a href="{site.url(lang, 'products')}">{text(lang, 'Products', '제품')}</a><span aria-hidden="true">/</span><span>{e(name)}</span></p>
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


# ------------------------------------------------------- about & support


def about(site, lang, shell):
    lead = site.t(lang, 'about.lead')
    cfg = site.config
    rows = [
        (text(lang, 'Company', '회사'), 'Player Zero'),
        (text(lang, 'What we make', '만드는 것'), text(lang, 'Games and apps', '게임과 앱')),
        (text(lang, 'Website', '웹사이트'), cfg['domain'].split('//')[-1].rstrip('/')),
    ]
    fact_rows = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows)
    fact_rows += f'<div><dt>{text(lang, "Email", "이메일")}</dt><dd><a href="mailto:{e(cfg["contact"])}">{e(cfg["contact"])}</a></dd></div>'
    fact_rows += f'<div><dt>YouTube</dt><dd><a href="{e(cfg["youtube"])}">{YOUTUBE_NAME}</a> <span class="handle">{YOUTUBE_HANDLE}</span></dd></div>'
    cards = []
    for product in ordered(site.products):
        copy = copy_for(site, product, lang)
        slug, name = product['slug'], copy.get('name', product['slug'])
        detail = site.url(lang, 'products', slug)
        images = product.get('images', {})
        thumb = images.get('cover') or images.get('hero')
        art = f'<a class="about-art" href="{detail}" tabindex="-1"><img src="{e(thumb)}" alt="" width="1232" height="706" loading="lazy"></a>' if thumb else ''
        cards.append(f'''<li class="about-product catalog-{e(slug)}">{art}<div><h3><a href="{detail}">{e(name)}</a></h3><p>{e(summary(copy))}</p><p class="muted">{e(platforms(site, lang, product))} · {e(status(site, lang, product))}</p></div></li>''')
    body = f'''<header class="page-intro"><h1>{e(site.t(lang, 'about.title'))}</h1><p class="lead">{e(lead)}</p></header>
      <section class="about-body">{paragraphs(strings(site, lang, 'about', 'paragraphs') or [])}<dl class="about-facts">{fact_rows}</dl></section>
      <section class="about-products"><h2>{e(site.t(lang, 'about.making'))}</h2><ul>{''.join(cards)}</ul></section>
      {contact_block(site, lang)}'''
    return shell(site, lang=lang, path=site.url(lang, 'about'), title=site.t(lang, 'about.title') + ' | Player Zero', description=site.t(lang, 'about.description'), body=body, alternates={l: site.url(l, 'about') for l in site.languages})


def support(site, lang, shell):
    cfg = site.config
    lead = text(lang, 'Write to us about a product, a problem you ran into, press or business. Everything goes to one inbox.', '제품 문의, 사용 중 문제, 취재와 협업 제안까지 모두 한 메일로 받습니다.')
    blocks = []
    for p in ordered(site.products):
        slug = p['slug']
        copy = copy_for(site, p, lang)
        name = copy.get('name', slug)
        subject = quote(name + ' support')
        detail = site.url(lang, 'products', slug)
        links = [f'<a class="text-link" href="mailto:{e(cfg["contact"])}?subject={e(subject)}">{e(text(lang, "Email about " + name, name + " 문의 메일 쓰기"))}</a>']
        if copy.get('faq'):
            links.append(f'<a class="text-link" href="{detail}#faq">{e(text(lang, name + " FAQ", name + " 자주 묻는 질문"))}</a>')
        else:
            links.append(f'<a class="text-link" href="{detail}">{e(text(lang, "About " + name, name + " 소개"))}</a>')
        links += [f'<a class="text-link" href="{e(href)}">{e(label)}</a>' for label, href in policy_docs(site, p, lang)]
        blocks.append(f'''<article class="support-product" id="{e(slug)}"><h2>{e(name)}</h2><p>{e(summary(copy))} · {e(platforms(site, lang, p))}</p><div class="link-stack">{''.join(links)}</div></article>''')
    checklist = [text(lang, 'Which product, and which platform or operating system', '어떤 제품인지, 어떤 기기와 운영체제인지'),
                 text(lang, 'What you were doing when it happened', '문제가 생겼을 때 무엇을 하고 있었는지'),
                 text(lang, 'What you expected, and what happened instead', '원래 기대한 동작과 실제로 일어난 일'),
                 text(lang, 'A screenshot, if you can take one', '가능하다면 화면 캡처')]
    body = f'''<header class="page-intro"><h1>{text(lang, 'Contact & support', '문의 및 지원')}</h1><p class="lead">{e(lead)}</p></header>
      <section class="support-main">
        <div class="support-mail"><p class="muted">{text(lang, 'Email', '이메일')}</p><a href="mailto:{e(cfg['contact'])}">{e(cfg['contact'])}</a><p>{text(lang, 'For development updates, follow', '개발 소식은 YouTube')} <a href="{e(cfg['youtube'])}">{YOUTUBE_NAME}</a> {text(lang, 'on YouTube (' + YOUTUBE_HANDLE + ').', '(' + YOUTUBE_HANDLE + ')에서 볼 수 있습니다.')}</p></div>
        <div class="support-grid">{''.join(blocks)}</div>
      </section>
      <section class="support-notes">
        <div><h2>{text(lang, 'Reporting a problem', '문제를 알려주실 때')}</h2><p>{text(lang, 'These details help us understand what happened:', '다음 내용을 함께 적어주시면 상황을 이해하는 데 도움이 됩니다.')}</p><ul class="checklist">{''.join(f'<li>{e(item)}</li>' for item in checklist)}</ul></div>
        <div><h2>{text(lang, 'Press & business', '취재 및 협업')}</h2><p>{text(lang, 'For press, collaboration or anything else, use the same address.', '취재, 협업 제안, 그 밖의 문의도 같은 주소로 보내주세요.')}</p><a class="text-link" href="mailto:{e(cfg['contact'])}">{e(cfg['contact'])}</a></div>
      </section>'''
    return shell(site, lang=lang, path=site.url(lang, 'support'), title=text(lang, 'Contact & support', '문의 및 지원') + ' | Player Zero', description=lead, body=body, alternates={l: site.url(l, 'support') for l in site.languages})
