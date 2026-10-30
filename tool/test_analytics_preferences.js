const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync(require('node:path').join(__dirname, '../assets/analytics_preferences.js'), 'utf8');
function browser(initial = '', blocked = false, protocol = 'https:') {
  let cookie = initial;
  const writes = [];
  const nodes = Object.fromEntries(['analytics-status', 'analytics-exclude', 'analytics-include'].map(id => [id, {
    textContent: '', disabled: false, hidden: false, addEventListener(type, fn) { this.click = fn; }
  }]));
  const document = {getElementById: id => nodes[id]};
  Object.defineProperty(document, 'cookie', {
    get() { return cookie; },
    set(value) {
      writes.push(value);
      if (blocked) return;
      const flag = value.split(';')[0];
      cookie = value.includes('Max-Age=0') ? '' : flag;
    }
  });
  const events = {};
  const window = {addEventListener(type, fn) { events[type] = fn; }};
  vm.runInNewContext(code, {document, location: {protocol}, window});
  return {nodes, writes, events, cookie: () => cookie, setCookie: value => { cookie = value; }};
}
test('opening preferences never creates a cookie', () => {
  const b = browser();
  assert.equal(b.writes.length, 0);
  assert.match(b.nodes['analytics-status'].textContent, /집계 제외 미적용/);
});
test('explicit exclusion persists a host-only secure boolean with a one-year lifetime', () => {
  const b = browser(); b.nodes['analytics-exclude'].click();
  assert.equal(b.cookie(), '__Host-player0_analytics_opt_out=1');
  assert.match(b.writes[0], /Max-Age=31536000; Path=\/; Secure; SameSite=Lax$/);
  assert.ok(!b.writes[0].includes('Domain='));
  assert.match(b.nodes['analytics-status'].textContent, /집계 제외 적용 중/);
  assert.equal(b.nodes['analytics-exclude'].disabled, true);
  assert.equal(b.nodes['analytics-exclude'].hidden, true);
  assert.equal(b.nodes['analytics-include'].hidden, false);
  assert.equal(b.nodes['analytics-include'].disabled, false);
});
test('saved cookie is recognized after reopening, independently of other cookies', () => {
  const b = browser('theme=dark; __Host-player0_analytics_opt_out=1; locale=ko');
  assert.match(b.nodes['analytics-status'].textContent, /집계 제외 적용 중/);
  assert.equal(b.writes.length, 0);
});
test('returning to an open page re-reads changes made in another tab', () => {
  for (const event of ['focus', 'pageshow']) {
    const b = browser();
    assert.equal(b.nodes['analytics-exclude'].hidden, false);
    assert.equal(b.nodes['analytics-include'].hidden, true);
    b.setCookie('__Host-player0_analytics_opt_out=1'); b.events[event]();
    assert.match(b.nodes['analytics-status'].textContent, /다시 설정할 필요가 없습니다/);
    assert.equal(b.nodes['analytics-exclude'].hidden, true);
    assert.equal(b.nodes['analytics-include'].hidden, false);
    b.setCookie(''); b.events[event]();
    assert.match(b.nodes['analytics-status'].textContent, /집계 제외 미적용/);
    assert.equal(b.nodes['analytics-exclude'].hidden, false);
    assert.equal(b.nodes['analytics-include'].hidden, true);
    assert.equal(b.writes.length, 0);
  }
});
test('similar names and values do not count as exclusion', () => {
  for (const value of ['other__Host-player0_analytics_opt_out=1', '__Host-player0_analytics_opt_out=10']) {
    assert.match(browser(value).nodes['analytics-status'].textContent, /집계 제외 미적용/);
  }
});
test('explicit removal expires only the same host-only cookie', () => {
  const b = browser('__Host-player0_analytics_opt_out=1'); b.nodes['analytics-include'].click();
  assert.equal(b.cookie(), ''); assert.match(b.writes[0], /Max-Age=0/);
  assert.match(b.nodes['analytics-status'].textContent, /집계 제외 미적용/);
});
test('blocked cookies report failure instead of claiming success', () => {
  const b = browser('', true); b.nodes['analytics-exclude'].click();
  assert.match(b.nodes['analytics-status'].textContent, /저장하지 못했습니다/);
});
test('insecure connections cannot claim the secure preference was set', () => {
  const b = browser('', false, 'http:'); b.nodes['analytics-exclude'].click();
  assert.equal(b.writes.length, 0);
  assert.match(b.nodes['analytics-status'].textContent, /저장하지 못했습니다/);
});
