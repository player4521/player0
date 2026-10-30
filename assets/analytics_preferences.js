(() => {
  'use strict';
  const name = '__Host-player0_analytics_opt_out';
  const status = document.getElementById('analytics-status');
  const exclude = document.getElementById('analytics-exclude');
  const include = document.getElementById('analytics-include');
  function excluded() {
    return document.cookie.split(';').some(part => part.trim() === name + '=1');
  }
  function show() {
    const off = excluded();
    status.textContent = off
      ? '집계 제외 적용 중 · 이 브라우저에서는 다시 설정할 필요가 없습니다.'
      : '집계 제외 미적용 · 이 브라우저를 제외하려면 아래 버튼을 눌러 주세요.';
    exclude.hidden = off;
    exclude.disabled = off;
    include.hidden = !off;
    include.disabled = !off;
    return off;
  }
  function fail() {
    status.textContent = '설정을 저장하지 못했습니다. HTTPS 연결과 사이트 쿠키 허용 여부를 확인해 주세요.';
  }
  function set(off) {
    try {
      if (location.protocol !== 'https:') { fail(); return; }
      document.cookie = name + (off ? '=1; Max-Age=31536000' : '=; Max-Age=0') + '; Path=/; Secure; SameSite=Lax';
      if (show() !== off) fail();
    } catch (_) { fail(); }
  }
  exclude.addEventListener('click', () => set(true));
  include.addEventListener('click', () => set(false));
  function refresh() {
    try { show(); } catch (_) {
      exclude.disabled = true; include.disabled = true; fail();
    }
  }
  window.addEventListener('pageshow', refresh);
  window.addEventListener('focus', refresh);
  refresh();
})();
