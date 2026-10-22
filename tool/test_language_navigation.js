// Browser-language auto-selection, tested against the generated pages: run `python tool/build.py` first.
//   node --test tool/test_language_navigation.js
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const DIST = path.resolve(__dirname, '..', 'dist');
const ORIGIN = 'https://player0.dev';
const KEY = 'player0-language';

function read(rel) {
  return fs.readFileSync(path.join(DIST, rel), 'utf8');
}

function selectionScript(html) {
  const found = html.match(/<script data-language-select>([\s\S]*?)<\/script>/);
  assert.ok(found, 'page has the language selection script');
  return found[1];
}

function menuLinks(html) {
  const menu = html.match(/<details class="lang-menu">([\s\S]*?)<\/details>/);
  assert.ok(menu, 'page has the language menu');
  return [...menu[1].matchAll(/<a href="([^"]*)" hreflang="([^"]*)"/g)].map(m => ({ href: m[1], hreflang: m[2] }));
}

function fileFor(url) {
  const rel = url.replace(/^\//, '');
  return rel === '' || rel.endsWith('/') ? rel + 'index.html' : rel;
}

// Runs one page's generated script with a stubbed browser. `storage`: 'ok' | 'throws' (methods throw) | 'denied' (access throws).
function visit(rel, { url, languages = [], language, stored, storage = 'ok', referrer = '' } = {}) {
  const html = read(rel);
  const page = new URL(url || '/' + rel.replace(/index\.html$/, ''), ORIGIN);
  const replaced = [];
  const listeners = {};
  const store = new Map(stored === undefined ? [] : [[KEY, stored]]);
  const fail = () => { throw new Error('SecurityError'); };
  const local = storage === 'ok'
    ? { getItem: k => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k) }
    : { getItem: fail, setItem: fail, removeItem: fail };
  const context = {
    URL, URLSearchParams,
    location: { href: page.href, origin: page.origin, pathname: page.pathname, search: page.search, hash: page.hash, replace: to => replaced.push(to) },
    navigator: { languages, language },
    document: { referrer, documentElement: { dataset: {} }, addEventListener: (type, fn) => (listeners[type] = listeners[type] || []).push(fn) },
  };
  Object.defineProperty(context, 'localStorage', { get: () => (storage === 'denied' ? fail() : local) });
  vm.createContext(context);
  vm.runInContext(selectionScript(html), context);

  // Activates a real link from this page's language menu; returns the href the browser would follow.
  function choose(code, modifiers = {}) {
    const link = menuLinks(html).find(item => item.hreflang === code);
    assert.ok(link, `menu links ${code}`);
    const anchor = {
      href: new URL(link.href, page).href,
      getAttribute: name => (name === 'hreflang' ? link.hreflang : null),
      closest: selector => (selector === '.lang-menu a[hreflang]' ? anchor : null),
    };
    const event = { button: 0, defaultPrevented: false, metaKey: false, ctrlKey: false, shiftKey: false, altKey: false, target: anchor, ...modifiers };
    (listeners.click || []).forEach(fn => fn(event));
    return anchor.href;
  }

  return { replaced, store, choose, html };
}

const browser = (...languages) => ({ languages, language: languages[0] });

// Opens a followed link's target page fresh, as a new tab would: no referrer, the link's own query.
function land(href, options = {}) {
  const next = new URL(href);
  return visit(fileFor(next.pathname), { ...options, url: next.pathname + next.search + next.hash, referrer: '' });
}

test('dist is built', () => {
  assert.ok(fs.existsSync(path.join(DIST, 'index.html')), 'run python tool/build.py first');
});

test('supported locale variants match case-insensitively by language subtag', () => {
  const cases = [
    ['ko-KR', '/ko/'], ['KO', '/ko/'], ['ko_kr', '/ko/'], ['ja-JP', '/ja/'], ['ja', '/ja/'],
    ['zh-TW', '/zh-TW/'], ['zh-tw', '/zh-TW/'], ['zh-Hant', '/zh-TW/'], ['zh-Hant-TW', '/zh-TW/'],
    ['zh-HK', '/zh-TW/'], ['zh-MO', '/zh-TW/'], ['zh', '/zh-TW/'],
  ];
  for (const [tag, target] of cases) {
    assert.deepEqual(visit('index.html', browser(tag)).replaced, [target], tag);
  }
  for (const tag of ['en', 'en-GB', 'en-US', 'EN-gb']) {
    assert.deepEqual(visit('index.html', browser(tag)).replaced, [], tag);
  }
});

test('Simplified Chinese is not sent to the Traditional translation', () => {
  for (const tag of ['zh-CN', 'zh-Hans', 'zh-SG', 'zh-Hans-CN']) {
    assert.deepEqual(visit('index.html', browser(tag)).replaced, [], tag);
  }
  assert.deepEqual(visit('index.html', browser('zh-CN', 'ja')).replaced, ['/ja/']);
});

test('browser preferences are followed in order, past unsupported languages', () => {
  assert.deepEqual(visit('index.html', browser('ja', 'ko')).replaced, ['/ja/']);
  assert.deepEqual(visit('index.html', browser('fr-FR', 'de', 'ko-KR')).replaced, ['/ko/']);
  assert.deepEqual(visit('index.html', browser('en-US', 'ko')).replaced, [], 'English first keeps English');
  assert.deepEqual(visit('index.html', browser('fr', 'de')).replaced, [], 'nothing supported keeps English');
  assert.deepEqual(visit('index.html', { languages: [], language: 'ja-JP' }).replaced, ['/ja/'], 'navigator.language fallback');
  assert.deepEqual(visit('index.html', { languages: undefined, language: undefined }).replaced, []);
});

test('the same document is opened, with query and hash preserved exactly', () => {
  const run = visit('products/keycerto/index.html', { url: '/products/keycerto/?utm_source=x&a=%20b#how-to', ...browser('ko-KR') });
  assert.deepEqual(run.replaced, ['/ko/products/keycerto/?utm_source=x&a=%20b#how-to']);
  assert.deepEqual(visit('about/index.html', browser('zh-HK')).replaced, ['/zh-TW/about/']);
});

test('a remembered manual choice beats the browser language', () => {
  assert.deepEqual(visit('index.html', { ...browser('ko'), stored: 'ja' }).replaced, ['/ja/']);
  assert.deepEqual(visit('index.html', { ...browser('ko'), stored: 'en' }).replaced, [], 'saved English stays English');
});

test('malformed or unsupported saved values are ignored and never used as URLs', () => {
  for (const stored of ['fr', 'KO', '//evil.example', 'https://evil.example/', '__proto__', 'constructor', '', '{"ko":1}']) {
    const run = visit('index.html', { ...browser('ja'), stored });
    assert.deepEqual(run.replaced, ['/ja/'], JSON.stringify(stored));
  }
  assert.deepEqual(visit('index.html', { ...browser('en'), stored: 'evil' }).replaced, []);
});

test('blocked or throwing storage falls back to the browser language', () => {
  assert.deepEqual(visit('index.html', { ...browser('ko'), storage: 'throws' }).replaced, ['/ko/']);
  assert.deepEqual(visit('index.html', { ...browser('ko'), storage: 'denied' }).replaced, ['/ko/']);
});

test('explicitly localized URLs keep their language', () => {
  for (const rel of ['ko/index.html', 'ko/products/keycerto/index.html', 'ja/about/index.html', 'zh-TW/products/index.html', 'ko/legal/meloom/privacy/index.html']) {
    assert.deepEqual(visit(rel, browser('ja')).replaced, [], rel);
    assert.deepEqual(visit(rel, { ...browser('en'), stored: 'zh-TW' }).replaced, [], rel);
    assert.deepEqual(visit(rel, { ...browser('en'), stored: 'en' }).replaced, [], rel);
  }
});

test('missing translations and 404 pages never get an invented URL', () => {
  // The Meloom policy exists in English and Korean only.
  assert.deepEqual(visit('legal/meloom/privacy/index.html', browser('ja')).replaced, []);
  assert.deepEqual(visit('legal/meloom/privacy/index.html', browser('zh-TW', 'ko')).replaced, ['/ko/legal/meloom/privacy/']);
  assert.deepEqual(visit('legal/meloom/privacy/index.html', { ...browser('ko'), stored: 'ja' }).replaced, [], 'saved choice without that page stays');
  assert.deepEqual(visit('legal/meloom/privacy/index.html', browser('ko')).replaced, ['/ko/legal/meloom/privacy/']);
  for (const rel of ['404.html', 'ko/404.html']) {
    assert.deepEqual(visit(rel, { url: '/missing/page/?q=1', ...browser('ko') }).replaced, [], rel);
    assert.deepEqual(visit(rel, { url: '/missing/page/', ...browser('en'), stored: 'ja' }).replaced, [], rel);
  }
});

test('internal navigation is never redirected', () => {
  const referrer = ORIGIN + '/ja/products/meloom/';
  assert.deepEqual(visit('legal/meloom/privacy/index.html', { ...browser('ko'), referrer }).replaced, []);
  assert.deepEqual(visit('index.html', { ...browser('ko'), stored: 'ja', referrer }).replaced, []);
  assert.deepEqual(visit('index.html', { ...browser('ko'), referrer: 'https://www.example.com/' }).replaced, ['/ko/']);
  assert.deepEqual(visit('index.html', { ...browser('ko'), referrer: 'not a url' }).replaced, ['/ko/']);
});

test('choosing a language in the menu is remembered, English included', () => {
  const korean = visit('index.html', browser('en'));
  assert.equal(korean.choose('ko'), ORIGIN + '/ko/');
  assert.equal(korean.store.get(KEY), 'ko');

  const english = visit('ko/products/keycerto/index.html', browser('ko'));
  const href = english.choose('en');
  assert.equal(href, ORIGIN + '/products/keycerto/?lang=en', 'the English link is explicit');
  assert.equal(english.store.get(KEY), 'en');
  assert.deepEqual(land(href, { ...browser('ko'), stored: english.store.get(KEY) }).replaced, []);
  assert.deepEqual(visit('products/keycerto/index.html', { ...browser('ko'), stored: english.store.get(KEY) }).replaced, []);
});

test('menu links keep same-page alternates and legal fallbacks', () => {
  const links = Object.fromEntries(menuLinks(read('legal/meloom/privacy/index.html')).map(l => [l.hreflang, l.href]));
  assert.deepEqual(links, { ko: '/ko/legal/meloom/privacy/', ja: '/ja/legal/', 'zh-TW': '/zh-TW/legal/' });
  const run = visit('legal/meloom/privacy/index.html', browser('en'));
  assert.equal(run.choose('ja'), ORIGIN + '/ja/legal/');
  assert.equal(run.store.get(KEY), 'ja');

  const korean = Object.fromEntries(menuLinks(read('ko/legal/meloom/privacy/index.html')).map(l => [l.hreflang, l.href]));
  assert.deepEqual(korean, { en: '/legal/meloom/privacy/?lang=en', ja: '/ja/legal/', 'zh-TW': '/zh-TW/legal/' });
  const about = Object.fromEntries(menuLinks(read('ja/about/index.html')).map(l => [l.hreflang, l.href]));
  assert.deepEqual(about, { en: '/about/?lang=en', ko: '/ko/about/', 'zh-TW': '/zh-TW/about/' });
});

test('only the menu link opts out: canonical and hreflang URLs stay clean', () => {
  const html = read('ko/products/keycerto/index.html');
  assert.match(html, /<link rel="alternate" hreflang="en" href="https:\/\/player0\.dev\/products\/keycerto\/">/);
  assert.match(html, /<link rel="canonical" href="https:\/\/player0\.dev\/ko\/products\/keycerto\/">/);
  for (const tag of html.match(/<link [^>]*>/g)) assert.ok(!tag.includes('?lang='), tag);
  assert.ok(!read('sitemap.xml').includes('?lang='), 'sitemap has no opt-out URLs');
});

test('modified clicks open normally and are not saved as a choice', () => {
  const run = visit('ko/index.html', browser('ko'));
  for (const modifiers of [{ ctrlKey: true }, { metaKey: true }, { shiftKey: true }, { button: 1 }, { defaultPrevented: true }]) {
    assert.equal(run.choose('en', modifiers), ORIGIN + '/?lang=en', JSON.stringify(modifiers));
  }
  assert.equal(run.store.has(KEY), false);
});

test('English opened in a new tab stays English without any saved choice', () => {
  // Middle click, modified click or the context menu: no click handler saves anything and the referrer may be stripped.
  const href = new URL(menuLinks(read('ko/products/keycerto/index.html')).find(l => l.hreflang === 'en').href, ORIGIN).href;
  for (const storage of ['ok', 'throws', 'denied']) {
    assert.deepEqual(land(href, { ...browser('ko'), storage }).replaced, [], storage);
  }
  assert.deepEqual(land(href, { ...browser('ko'), stored: 'ja' }).replaced, [], 'beats a conflicting saved choice');
  assert.deepEqual(land(href, { ...browser('en'), stored: 'zh-TW' }).replaced, []);
});

test('manual English with storage blocked does not bounce back', () => {
  for (const storage of ['throws', 'denied']) {
    const run = visit('ko/about/index.html', { ...browser('ko'), storage, url: '/ko/about/?x=1#team' });
    const href = run.choose('en');
    const next = new URL(href);
    assert.equal(next.pathname, '/about/');
    assert.equal(next.searchParams.get('lang'), 'en');
    // Even without the referrer (stripped by policy), the opt-out keeps English.
    assert.deepEqual(land(href, { ...browser('ko'), storage }).replaced, []);
    // With the usual same-origin referrer it also stays English.
    assert.deepEqual(visit('about/index.html', { ...browser('ko'), storage, referrer: ORIGIN + '/ko/about/' }).replaced, []);
    // Other languages are plain links; a localized URL needs no opt-out.
    assert.equal(run.choose('ja'), ORIGIN + '/ja/about/');
  }
  // Automatic selection keeps every query string; only ?lang=<default> opts out.
  assert.deepEqual(visit('index.html', { url: '/?lang=ko', ...browser('ja') }).replaced, ['/ja/?lang=ko'], 'only the default language opts out');
});

test('every redirect lands on a generated page that does not redirect again', () => {
  const pages = [];
  (function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith('.html') && fs.readFileSync(full, 'utf8').includes('<!-- Generated from content/ by tool/build.py. -->')) {
        pages.push(path.relative(DIST, full).split(path.sep).join('/'));
      }
    }
  })(DIST);
  assert.ok(pages.length > 20);
  for (const rel of pages) {
    for (const tag of ['ko-KR', 'ja', 'zh-Hant', 'zh-CN', 'en-GB']) {
      for (const stored of [undefined, 'ko', 'ja', 'zh-TW', 'en']) {
        const { replaced } = visit(rel, { ...browser(tag), stored, url: rel.endsWith('404.html') ? '/missing/' : undefined });
        assert.ok(replaced.length <= 1);
        if (!replaced.length) continue;
        const target = replaced[0];
        assert.ok(target.startsWith('/') && !target.startsWith('//'), target);
        assert.ok(!rel.endsWith('404.html'), `${rel} must not redirect`);
        assert.ok(fs.existsSync(path.join(DIST, fileFor(target))), `${rel} -> ${target} exists`);
        assert.notEqual(target, '/' + rel.replace(/index\.html$/, ''));
        assert.deepEqual(visit(fileFor(target), { ...browser(tag), stored }).replaced, [], `${target} settles`);
      }
    }
  }
});

test('theme script, canonical and hreflang metadata are unchanged in shape', () => {
  const html = read('products/keycerto/index.html');
  assert.match(html, /localStorage\.getItem\('player0-theme'\)/);
  assert.match(html, /<link rel="canonical" href="https:\/\/player0\.dev\/products\/keycerto\/">/);
  for (const code of ['en', 'ko', 'ja', 'zh-TW']) assert.match(html, new RegExp(`<link rel="alternate" hreflang="${code}"`));
  assert.ok(html.indexOf('data-language-select') < html.indexOf('rel="stylesheet"'), 'decides before the stylesheet');
});
