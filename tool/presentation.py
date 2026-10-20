"""Presentation templates for the registry-driven Player Zero website."""
from __future__ import annotations

import html
from urllib.parse import quote


def e(value):
    return html.escape(str(value), quote=True)


def text(lang, english, korean):
    return korean if lang == 'ko' else english


def shell(site, *, lang, path, title, description, body, alternates=None, main_class='page'):
    cfg = site.config
    domain = cfg['domain'].rstrip('/')
    canonical = domain + path
    nav = []
    nav_items = [('products', text(lang, 'Projects', '제품')), ('about', text(lang, 'About', '회사 소개')), ('support', text(lang, 'Contact', '문의'))]
    if site.playables:
        nav_items.insert(1, ('play', site.t(lang, 'nav.play')))
    for slug, label in nav_items:
        href = site.url(lang, slug)
        current = ' aria-current="page"' if path.startswith(href) else ''
        nav.append(f'<a href="{href}"{current}>{label}</a>')
    alternates = alternates or {}
    switches = []
    for code, href in alternates.items():
        label = 'EN' if code == 'en' else site.language_name(code)
        switches.append(f'<span class="current" aria-current="true">{e(label)}</span>' if code == lang else f'<a href="{e(href)}" hreflang="{e(code)}">{e(label)}</a>')
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
  <meta name="theme-color" content="#f5f4ef">
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
  <a class="skip-link" href="#main">{text(lang,'Skip to content','본문으로 이동')}</a>
  <header class="site-header">
    <a class="brand" href="{site.url(lang)}" aria-label="{text(lang,'Player Zero home','Player Zero 홈')}">
      <img src="{e(cfg['logo'])}" alt="" width="50" height="50">
      <span class="brand-name">PLAYER ZERO</span>
    </a>
    <nav class="site-nav" aria-label="{text(lang,'Main navigation','주요 메뉴')}">{''.join(nav)}<span class="lang-switch">{''.join(switches)}</span></nav>
  </header>
  <main id="main" class="{e(main_class)}">{body}</main>
  <footer class="site-footer">
    <div><p class="footer-brand">Player Zero</p><p class="footer-tagline">{text(lang,'Games, everyday apps, and a little curiosity.','게임과 일상의 앱, 그리고 작은 호기심.')}</p></div>
    <div class="footer-links"><a href="{site.url(lang,'products')}">{text(lang,'Projects','제품')}</a><a href="{site.url(lang,'support')}">{text(lang,'Contact','문의')}</a><a href="{e(cfg['youtube'])}">YouTube ↗</a><a href="{site.url(lang,'legal')}">{site.t(lang,'legal.title')}</a></div>
    <div class="footer-bottom"><p>© 2026 Player Zero</p><a href="mailto:{e(cfg['contact'])}">{e(cfg['contact'])}</a><p>PLAYER0.DEV</p></div>
  </footer>
</body>
</html>
'''


def button(href, label, secondary=False):
    cls = 'button button-secondary' if secondary else 'button'
    return f'<a class="{cls}" href="{e(href)}">{e(label)}<span aria-hidden="true">↗</span></a>'


def eyebrow(label, number=None):
    prefix = f'<span class="section-number">{e(number)}</span>' if number else ''
    return f'<p class="eyebrow">{prefix}{e(label)}</p>'


def paragraphs(values, cls='body-copy'):
    return '<div class="' + cls + '">' + ''.join(f'<p>{e(v)}</p>' for v in values) + '</div>'


def project_row(site, product, lang, content):
    slug = product['slug']
    copy, _ = content(site, product, lang)
    name = copy.get('name', slug)
    image = product.get('images', {}).get('cover', product.get('images', {}).get('hero'))
    alt = product.get('images', {}).get('coverAlt', product.get('images', {}).get('heroAlt', name))
    media = (f'<img src="{e(image)}" alt="{e(alt)}" width="1280" height="720" loading="lazy">'
             if image else f'<span class="project-placeholder">{e(name)}</span>')
    detail = site.url(lang, 'products', slug)
    kind = site.t(lang, f'kind.{product.get("kind", "app")}')
    return f'''<article class="project-row project-{e(slug)}">
      <a class="project-art" href="{detail}" aria-label="{e(name)}">
        {media}
        <span class="art-arrow" aria-hidden="true">↗</span>
      </a>
      <div class="project-copy">
      <div class="project-meta"><span>{e(kind)}</span><span class="status-dot">{e(site.t(lang, 'status.' + product.get('status', 'in-development')))}</span></div>
        <h2><a href="{detail}">{e(name)}</a></h2>
        <p class="project-tagline">{e(copy['tagline'])}</p>
        <p class="project-summary">{e(copy['description'][0])}</p>
        {button(detail, text(lang, 'Explore ' + name, name + ' 살펴보기'), True)}
      </div>
    </article>'''


def contact_block(site, lang):
    return f'''<section class="contact-band">
      <div>{eyebrow(text(lang, 'KEEP IN TOUCH', '개발 소식'))}<h2>{text(lang, 'There’s more in the making.', '다음 소식도 함께해요.')}</h2>
      <p>{text(lang, 'Follow our work, or tell us what’s on your mind.', '개발 소식이 궁금하거나 전하고 싶은 이야기가 있다면.')}</p></div>
      <div class="contact-actions">{button(site.config['youtube'], 'YouTube @player0lab')}
      <a class="text-link" href="mailto:{e(site.config['contact'])}">{e(site.config['contact'])} <span aria-hidden="true">↗</span></a></div>
    </section>'''


def home(site, lang, shell, content):
    products = sorted(site.products, key=lambda p: (p.get('order', 1000), p['slug']))
    featured = next((p for p in products if p['slug'] == 'keycerto'), products[0] if products else None)
    preview = ''
    if featured:
        fc, _ = content(site, featured, lang)
        images = featured.get('images', {})
        image = images.get('hero') or images.get('cover')
        preview_media = (f'<img src="{e(image)}" alt="{e(images.get("heroAlt", fc["name"]))}" width="1280" height="720" fetchpriority="high">'
                         if image else f'<span class="project-placeholder">{e(fc["name"])}</span>')
        preview = f'''<a class="hero-preview" href="{site.url(lang, 'products', featured['slug'])}">
        <div class="preview-label"><span class="live-dot" aria-hidden="true"></span>{text(lang, 'ON OUR WORKBENCH', '지금 만들고 있어요')}<span>01 / {e(featured.get('kind', 'app').upper())}</span></div>
        {preview_media}
        <div class="preview-caption"><div><strong>{e(fc['name'])}</strong><span>{e(fc['tagline'])}</span></div><span class="preview-arrow" aria-hidden="true">↗</span></div>
      </a>'''
    headline = text(lang, 'Curiosity,<br><span>made playable.</span>', '호기심을,<br><span>플레이로.</span>')
    lead = text(lang, 'An independent developer making games to get lost in, and apps to share your day with.', '음악에 빠져드는 게임부터 하루를 함께하는 앱까지. 작은 호기심을 직접 만지고 즐길 수 있는 경험으로 만듭니다.')
    rows = ''.join(project_row(site, p, lang, content) for p in products)
    body = f'''<section class="home-hero">
      <div class="hero-copy">{eyebrow(text(lang, 'INDEPENDENT GAMES & EVERYDAY APPS', '게임과 일상의 앱을 만드는 독립 개발사'))}
      <h1>{headline}</h1><p class="hero-lead">{e(lead)}</p>
      <div class="hero-actions">{button('#projects', text(lang, 'Explore the projects', '만들고 있는 것들'))}
      <a class="text-link" href="{site.url(lang, 'about')}">{text(lang, 'About Player Zero', '회사 소개')} <span aria-hidden="true">↗</span></a></div></div>
      {preview}
    </section>
    <section id="projects" class="projects-section">
      <div class="section-heading">{eyebrow(text(lang, 'CURRENT PROJECTS', '만들고 있는 것들'), '01')}
      <p>{text(lang, 'Different ideas. The same curiosity.', '서로 다른 아이디어, 같은 호기심.')}<br><span class="muted">{text(lang, 'Both projects are in development.', '두 제품 모두 개발 중입니다.')}</span></p></div>
      {rows}
    </section>
    <section class="lab-note">
      <div>{eyebrow(text(lang, 'THE WAY WE WORK', '우리가 만드는 경험'), '02')}<h2>{text(lang, 'A good idea deserves<br>to be played with.', '좋은 아이디어는<br>직접 즐겨봐야 하니까.')}</h2></div>
      <div><p>{text(lang, 'What if a keyboard could write a story to music? What if your day had a room of its own? We start with questions like these, then build, play and refine.', '키보드로 음악에 맞춰 이야기를 쓴다면? 오늘의 날씨와 시간을 하나의 방에 담는다면? Player Zero은 이런 질문에서 출발해, 만들고 즐기고 다듬습니다.')}</p>
      <a class="text-link" href="{site.url(lang, 'about')}">{text(lang, 'Meet Player Zero', 'Player Zero 알아보기')} <span aria-hidden="true">↗</span></a></div>
    </section>{contact_block(site, lang)}'''
    return shell(site, lang=lang, path=site.url(lang), title='Player Zero — ' + text(lang, 'Games & everyday apps', '게임과 일상의 앱'), description=lead, body=body, alternates={l: site.url(l) for l in site.languages}, main_class='page page-home')


def products(site, lang, shell, content):
    rows = ''.join(project_row(site, p, lang, content) for p in sorted(site.products, key=lambda p: p.get('order', 1000)))
    body = f'''<header class="page-intro">{eyebrow(text(lang, 'OUR PROJECTS', '우리가 만드는 것들'))}<h1>{text(lang, 'Games. Apps.<br>Little discoveries.', '게임, 앱,<br>그리고 작은 발견.')}</h1>
      <p class="hero-lead">{text(lang, 'Meet the projects taking shape at Player Zero.', 'Player Zero에서 조금씩 모습을 갖춰가는 제품들을 만나보세요.')}</p></header>
      <section class="projects-section">{rows}</section>{contact_block(site, lang)}'''
    return shell(site, lang=lang, path=site.url(lang, 'products'), title=text(lang, 'Projects', '제품') + ' | Player Zero', description=site.t(lang, 'products.description'), body=body, alternates={l: site.url(l, 'products') for l in site.languages})


def feature_list(items):
    return '<div class="feature-grid">' + ''.join(f'<article class="feature"><span class="feature-index">{i:02d}</span><div><h3>{e(item["title"])}</h3><p>{e(item["body"])}</p></div></article>' for i, item in enumerate(items, 1)) + '</div>'


def steps_list(items):
    return '<ol class="steps">' + ''.join(f'<li><span class="step-number">{i:02d}</span><h3>{e(item["title"])}</h3><p>{e(item["body"])}</p></li>' for i, item in enumerate(items, 1)) + '</ol>'


def detail(site, product, lang, shell, content, legal_docs):
    copy, fallback = content(site, product, lang)
    slug, name = product['slug'], copy['name']
    game = product.get('kind') == 'game'
    title_how = text(lang, 'How to play', '플레이 방법') if game else text(lang, 'A moment in your room', '작은 방에서 보내는 하루')
    kind = site.t(lang, 'kind.' + product['kind'])
    platform_text = ' · '.join(site.t(lang, 'platform.' + p) for p in product.get('platforms', []))
    docs = legal_docs(site, product, lang)
    actions = button('#how-to', title_how) if copy.get('howTo') else ''
    if product.get('video'):
        actions += button('#gameplay', text(lang, 'Watch gameplay', '플레이 영상 보기'), True)
    if docs:
        actions += button(docs[0][1], docs[0][0], True)
    actions += ''.join(button(link['url'], link.get('label', link.get('platform', 'Link')), True) for link in product.get('links', []))
    images = product.get('images', {})
    alt = images.get('heroAlt', name)
    media = ''
    if product.get('video'):
        video = e(product['video'])
        media = f'''<figure class="product-media" id="gameplay"><video controls playsinline preload="none" poster="{e(images.get('hero',''))}" aria-label="{e(name + text(lang, ' gameplay trailer', ' 실제 플레이 영상'))}"><source src="{video}" type="video/mp4"><a href="{video}">{text(lang, 'Open the gameplay video', '플레이 영상 열기')}</a></video><figcaption>{text(lang, 'Actual gameplay · Development build', '개발 중인 게임의 실제 플레이 화면')}</figcaption></figure>'''
    elif images.get('hero'):
        media = f'<figure class="product-media meloom-media"><img src="{e(images["hero"])}" alt="{e(alt)}" width="1024" height="500" fetchpriority="high"><figcaption>{e(name)} · {text(lang, "In development", "개발 중")}</figcaption></figure>'
    modes = ''
    if copy.get('modes'):
        modes = f'''<section class="detail-section" id="modes">{eyebrow(text(lang, 'THREE WAYS TO FIND YOUR RHYTHM', '나에게 맞는 연주 방식'))}
        <h2>{text(lang, 'Same music. Your way to play.', '같은 음악, 나에게 맞는 방식.')}</h2>
        <div class="mode-grid">''' + ''.join(f'<article class="mode"><span class="mode-symbol" aria-hidden="true">{["●", "● ●", "Aa"][i]}</span><h3>{e(m["title"])}</h3><p>{e(m["body"])}</p></article>' for i, m in enumerate(copy['modes'])) + '</div></section>'
    galleries = product.get('galleries', {})
    gallery = galleries.get(lang, galleries.get(site.default_lang, []))
    if not gallery:
        gallery = [{'src': src, 'alt': name, 'caption': name} for src in images.get('screenshots', [])]
    gallery_block = ''
    if gallery:
        gallery_block = f'<section class="detail-section">{eyebrow(text(lang, "A CLOSER LOOK", "조금 더 가까이"))}<h2>{text(lang, "On the screen", "화면으로 만나보세요.")}</h2><div class="screenshot-grid {"phone-gallery" if not game else ""}">'
        for shot in gallery:
            gallery_block += f'<figure><a href="{e(shot["src"])}" target="_blank" rel="noopener" aria-label="{e(text(lang, "Open image: ", "이미지 크게 보기: ") + shot["caption"])}"><img src="{e(shot["src"])}" alt="{e(shot["alt"])}" loading="lazy" width="{1280 if game else 540}" height="{720 if game else 960}"></a><figcaption>{e(shot["caption"])}</figcaption></figure>'
        gallery_block += '</div></section>'
    faq = ''.join(f'<details><summary>{e(q["question"])}</summary><p>{e(q["answer"])}</p></details>' for q in copy.get('faq', []))
    policy_links = ''.join(f'<a class="text-link" href="{e(href)}">{e(label)} ↗</a>' for label, href in docs)
    legal_block = f'<section class="detail-section product-legal"><h2>{e(site.t(lang,"detail.legal"))}</h2>{policy_links}</section>' if docs else ''
    notice = f'<p class="notice">{e(site.t(lang,"detail.fallbackNotice",language=site.language_name(fallback)))}</p>' if fallback else ''
    how_block = (f'<section class="detail-section" id="how-to">{eyebrow(text(lang,"GETTING STARTED","처음 만나는 순간"))}<h2>{e(title_how)}</h2>{steps_list(copy["howTo"])}</section>' if copy.get('howTo') else '')
    features_block = (f'<section class="detail-section">{eyebrow(text(lang,"WHAT MAKES IT YOURS","이 제품에서 만나는 것들"))}<h2>{text(lang,"More to discover.","즐길수록 발견하는 것들.")}</h2>{feature_list(copy["features"])}</section>' if copy.get('features') else '')
    faq_block = (f'<section class="detail-section faq-section" id="faq"><div>{eyebrow(text(lang,"GOOD TO KNOW","궁금한 이야기"))}<h2>{text(lang,"A few answers.","미리 알아두세요.")}</h2></div><div class="faq-list">{faq}</div></section>' if faq else '')
    support_slug = slug if slug in {'keycerto', 'meloom'} else ''
    support_url = site.url(lang, 'support') + ('#' + support_slug if support_slug else '')
    body = f'''<article class="product-page product-page-{slug}">
      <header class="product-intro"><p class="crumb"><a href="{site.url(lang, 'products')}">{text(lang, 'Projects', '제품')}</a><span aria-hidden="true">/</span>{e(name)}</p>
      <div class="product-title-row"><div>{eyebrow(kind)}<h1>{e(name)}</h1><p class="product-lead">{e(copy['tagline'])}</p></div>
      <aside class="product-facts"><span class="status-dot">{e(site.t(lang, 'status.' + product.get('status', 'in-development')))}</span><span>{e(platform_text)}</span><span>{text(lang, 'Release date to be announced', '출시일 미정') if product.get('status') != 'released' else ''}</span></aside></div>
      <div class="product-actions">{actions}</div>{notice}</header>
      {media}
      <section class="product-story"><h2>{text(lang, 'Meet ' + name, name + ' 소개')}</h2>{paragraphs(copy['description'])}</section>
      {modes}
      {how_block}
      {features_block}
      {gallery_block}
      {faq_block}
      {legal_block}
      <section class="product-contact"><h2>{text(lang, 'A question about ' + name + '?', name + '에 대해 궁금한가요?')}</h2><p>{text(lang, 'We’d love to hear from you.', '문의와 피드백을 기다리고 있어요.')}</p>{button(support_url, text(lang, 'Contact & support', '문의 및 지원'), True)}</section>
    </article>'''
    return shell(site, lang=lang, path=site.url(lang, 'products', slug), title=f'{name} | Player Zero', description=copy['tagline'], body=body, alternates={l: site.url(l, 'products', slug) for l in site.languages})


def about(site, lang, shell):
    intro = text(lang, 'Player Zero is an independent software developer making games and everyday apps. We follow ideas that invite a little curiosity, and turn them into things you can spend time with.', 'Player Zero은 게임과 일상의 앱을 만드는 독립 개발사입니다. 호기심을 부르는 아이디어를 따라, 직접 시간을 보내며 즐길 수 있는 경험을 만듭니다.')
    points = [
        {'title':text(lang,'A question becomes a game.','질문 하나가 게임이 됩니다.'),'body':text(lang,'KEYCERTO began with a simple connection: the rhythm of music and the motion of typing. A page of words gives every performance something to leave behind.','KEYCERTO는 음악의 박자와 타자를 치는 움직임을 연결합니다. 한 곡의 연주가 끝나면, 종이 위에 편지와 이야기 한 장이 남습니다.')},
        {'title':text(lang,'An everyday moment becomes a place.','일상의 한순간이 공간이 됩니다.'),'body':text(lang,'Meloom brings weather, time and a companion into a room. It is a different way to spend a quiet moment with your day.','Meloom은 날씨와 시간, 작은 동반자를 하나의 방에 담습니다. 하루의 정보를 확인하는 일에 잠시 머무를 수 있는 공간을 더합니다.')},
        {'title':text(lang,'The next idea stays open.','다음 아이디어는 열어둡니다.'),'body':text(lang,'Games and apps can start from very different places. We make room for both, with each project given room to find its own character.','게임과 앱은 서로 다른 곳에서 출발할 수 있습니다. Player Zero는 각 제품의 개성을 살려 다양한 게임과 앱을 만들어갑니다.')},
    ]
    body = f'''<header class="page-intro about-intro">{eyebrow('PLAYER ZERO')}<h1>{text(lang, 'Games and apps,<br>made with care.', '게임과 앱을<br>만듭니다.')}</h1><p class="hero-lead">{e(intro)}</p></header>
      <section class="about-principles">{feature_list(points)}</section>
      <section class="about-project-links"><h2>{text(lang, 'See what’s taking shape.', '지금 만들고 있는 것들.')}</h2>{button(site.url(lang,'products'),text(lang,'Meet our projects','제품 둘러보기'))}</section>{contact_block(site,lang)}'''
    return shell(site,lang=lang,path=site.url(lang,'about'),title=text(lang,'About','회사 소개')+' | Player Zero',description=intro,body=body,alternates={l:site.url(l,'about') for l in site.languages})


def support(site, lang, shell):
    lead = text(lang,'Questions, feedback or a story to share? Start here.','제품에 대한 질문, 피드백, 함께 나누고 싶은 이야기를 들려주세요.')
    blocks = []
    for p in sorted(site.products,key=lambda p:p.get('order',1000)):
        slug = p['slug']
        blocks_by_language = p['content']
        copy = blocks_by_language.get(lang) or blocks_by_language.get(site.default_lang) or next(iter(blocks_by_language.values()))
        name = copy['name']
        subject = quote(name + ' support')
        has_faq = bool(copy.get('faq'))
        product_url = site.url(lang, 'products', slug) + ('#faq' if has_faq else '')
        product_label = text(lang,'Read the product FAQ','제품의 자주 묻는 질문') if has_faq else text(lang,'Explore the project','제품 살펴보기')
        blocks.append(f'''<article class="support-product" id="{e(slug)}"><h2>{e(name)}</h2><p>{text(lang,'Questions about the project or help with a problem.','제품이 궁금하거나 사용 중 문제가 생겼다면 연락해 주세요.')}</p>
        <a class="text-link" href="mailto:{e(site.config['contact'])}?subject={e(subject)}">{e(site.config['contact'])} ↗</a>
        <a class="text-link" href="{e(product_url)}">{e(product_label)} ↗</a></article>''')
    body = f'''<header class="page-intro">{eyebrow(text(lang,'LET’S TALK','문의 및 지원'))}<h1>{text(lang,'A direct line<br>to Player Zero.','Player Zero에<br>이야기를 건네세요.')}</h1><p class="hero-lead">{e(lead)}</p></header>
      <section class="support-grid">{''.join(blocks)}</section>
      <section class="support-note"><h2>{text(lang,'Help us understand what happened.','이렇게 알려주시면 도움이 돼요.')}</h2><p>{text(lang,'For a technical problem, include the product name, your platform, what you were doing and what happened. A screenshot can help show the issue.','문제가 생겼다면 제품 이름, 사용 기기와 운영체제, 문제가 발생한 상황과 증상을 적어주세요. 화면 캡처가 있으면 상황을 이해하는 데 도움이 됩니다.')}</p></section>
      <section class="support-note"><h2>{text(lang,'Press & other enquiries','취재 및 그 밖의 문의')}</h2><p>{text(lang,'For press, collaboration or a general hello, use the same email.','취재와 협업 제안, 일반 문의도 같은 이메일로 보내주세요.')}</p><a class="text-link" href="mailto:{site.config['contact']}">{site.config['contact']} ↗</a></section>
      {contact_block(site,lang)}'''
    return shell(site,lang=lang,path=site.url(lang,'support'),title=text(lang,'Support & contact','문의 및 지원')+' | Player Zero',description=lead,body=body,alternates={l:site.url(l,'support') for l in site.languages})
