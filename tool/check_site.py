#!/usr/bin/env python3
"""Check generated pages for broken local links, media and metadata."""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.refs = []
        self.h1 = 0
        self.lang = ''
        self.canonical = ''
        self.image_alt_missing = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'html':
            self.lang = attrs.get('lang', '')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href', '')
        if tag == 'img' and 'alt' not in attrs:
            self.image_alt_missing += 1
        for name in ['src', 'href', 'poster']:
            if attrs.get(name):
                self.refs.append((tag, name, attrs[name]))


def main():
    config = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
    pages = {p: Page(p.read_text(encoding='utf-8')) for p in DIST.rglob('*.html')}
    redirects = {parts[0]: parts[1] for line in (DIST / '_redirects').read_text().splitlines() if len(parts := line.split()) >= 2}
    errors = []
    checked_refs = 0
    for file, page in pages.items():
        rel = file.relative_to(DIST).as_posix()
        url = '/' + (rel[:-10] if rel.endswith('index.html') else rel)
        if page.h1 != 1:
            errors.append(f'{rel}: expected one h1, got {page.h1}')
        if page.lang not in config['languages']:
            errors.append(f'{rel}: missing or invalid document language')
        if page.canonical != config['domain'].rstrip('/') + url:
            errors.append(f'{rel}: canonical URL mismatch')
        if page.image_alt_missing:
            errors.append(f'{rel}: image alt attribute missing')
        duplicates = [value for value, count in Counter(page.ids).items() if count > 1]
        if duplicates:
            errors.append(f'{rel}: duplicate IDs {duplicates}')
        for tag, name, ref in page.refs:
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc:
                continue
            target_url = urlsplit(urljoin('https://local.invalid' + url, ref))
            path = unquote(target_url.path)
            path = redirects.get(path, path)
            target = DIST / path.lstrip('/')
            if target.is_dir():
                target = target / 'index.html'
            checked_refs += 1
            if not target.is_file():
                errors.append(f'{rel}: broken {tag}[{name}] {ref}')
                continue
            if target_url.fragment and target in pages and unquote(target_url.fragment) not in pages[target].ids:
                errors.append(f'{rel}: missing anchor {ref}')
    for path in (DIST / 'assets').rglob('*'):
        if path.is_file() and path.stat().st_size > 25 * 1024 * 1024:
            errors.append(f'{path.relative_to(DIST)} exceeds the Pages file limit')
    expected = {'/privacy/': '/legal/meloom/privacy/', '/privacy/ko/': '/ko/legal/meloom/privacy/'}
    for old, target in expected.items():
        if redirects.get(old) != target:
            errors.append(f'Legacy privacy redirect changed: {old}')
    result = {'pages': len(pages), 'local_references_checked': checked_refs, 'errors': errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
