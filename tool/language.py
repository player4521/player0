"""Browser-language auto-selection: one small inline script per page, generated from the site languages.

The script runs in <head>, before the stylesheet, so a redirected visitor never renders the wrong page.
It only ever navigates a default-language page to that same page's generated alternate; localized URLs,
pages without the alternate and 404 pages are left alone. Stored and browser values are only compared
against the site languages and never used as URLs.

The menu's default-language link always carries ?lang=<default> (see `menu_href`), so English opened
any way (new tab, context menu, blocked storage, stripped referrer) stays English. Canonical and
hreflang URLs stay clean. Arriving from another page of this site never redirects either, so browsing
and English-only legal fallbacks do not switch language mid-visit.
"""
from __future__ import annotations

import json


STORAGE_KEY = 'player0-language'  # the visitor's manual menu choice
OPT_OUT = 'lang'  # ?lang=<default> keeps the default language; only the menu link uses it

_SCRIPT = r'''(()=>{const C=__CONFIG__,S=C.languages,D=C.base,A=C.alternates;
const valid=v=>typeof v==='string'&&S.indexOf(v)>=0;
const has=v=>valid(v)&&Object.prototype.hasOwnProperty.call(A,v)&&typeof A[v]==='string';
const read=()=>{try{const v=localStorage.getItem(C.key);return valid(v)?v:null;}catch(e){return null;}};
const save=v=>{try{localStorage.setItem(C.key,v);return localStorage.getItem(C.key)===v;}catch(e){return false;}};
const parts=t=>String(t).trim().toLowerCase().replace(/_/g,'-').split('-').filter(Boolean);
const script=p=>{for(const s of p.slice(1)){if(s==='hant'||s==='tw'||s==='hk'||s==='mo')return'hant';if(s==='hans'||s==='cn'||s==='sg'||s==='my')return'hans';}return'';};
const match=t=>{const p=parts(t);if(!p.length||!/^[a-z]{2,8}$/.test(p[0]))return null;
const exact=S.find(s=>s.toLowerCase()===p.join('-'));if(exact)return exact;
const same=S.filter(s=>parts(s)[0]===p[0]);if(p[0]!=='zh')return same[0]||null;
const w=script(p);return same.find(s=>w?script(parts(s))===w:script(parts(s))!=='hans')||null;};
const prefs=()=>{const l=[];try{const n=navigator;if(n.languages&&n.languages.length)l.push(...n.languages);if(n.language)l.push(n.language);}catch(e){}return l;};
const internal=r=>{try{return!!r&&new URL(r).origin===location.origin;}catch(e){return false;}};
const choose=()=>{try{if(new URLSearchParams(location.search).get(C.optOut)===D)return null;}catch(e){}
if(internal(document.referrer))return null;const saved=read();if(saved)return saved;
for(const t of prefs()){const m=match(t);if(m&&(m===D||has(m)))return m;}return null;};
if(C.lang===D){const t=choose();if(t&&t!==D&&has(t)){const u=A[t];
if(u.charAt(0)==='/'&&u.charAt(1)!=='/'&&u!==location.pathname){location.replace(u+location.search+location.hash);return;}}}
document.addEventListener('click',ev=>{if(ev.defaultPrevented||ev.button!==0||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return;
const a=ev.target&&ev.target.closest?ev.target.closest('.lang-menu a[hreflang]'):null;if(!a)return;
const v=a.getAttribute('hreflang');if(valid(v))save(v);});})();'''


def menu_href(site, code, href):
    """A language-menu target. The default language's link opts out of automatic selection explicitly."""
    if code != site.default_lang:
        return href
    return href + ('&' if '?' in href else '?') + OPT_OUT + '=' + site.default_lang


def selection_script(site, lang, alternates):
    """The inline <head> script for one page. `alternates` is the page's own {language: path} map."""
    if len(site.languages) < 2:
        return ''
    config = {
        'lang': lang,
        'base': site.default_lang,
        'languages': list(site.languages),
        'alternates': {code: href for code, href in (alternates or {}).items() if code in site.languages},
        'key': STORAGE_KEY,
        'optOut': OPT_OUT,
    }
    data = json.dumps(config, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    return '<script data-language-select>' + _SCRIPT.replace('__CONFIG__', data) + '</script>'
