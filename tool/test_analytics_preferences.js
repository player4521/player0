const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync(require('node:path').join(__dirname, '../assets/analytics_preferences.js'), 'utf8');
function browser(initial = '', blocked = false, protocol = 'https:') {
  let cookie = initial;
  const writes = [];
  const nodes = Object.fromEntries(['analytics-status', 'analytics-exclude', 'analytics-include'].map(id => [id, {
    textContent: '', disabled: false, addEventListener(type, fn) { this.click = fn; }
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
  vm.runInNewContext(code, {document, location: {protocol}});
  return {nodes, writes, cookie: () => cookie};
}
test('opening preferences never creates a cookie', () => {
  const b = browser();
  assert.equal(b.writes.length, 0);
  assert.match(b.nodes['analytics-status'].textContent, /제외 설정이 없습니다/);
});
test('explicit exclusion persists a host-only secure boolean with a one-year lifetime', () => {
  const b = browser(); b.nodes['analytics-exclude'].click();
  assert.equal(b.cookie(), '__Host-player0_analytics_opt_out=1');
  assert.match(b.writes[0], /Max-Age=31536000; Path=\/; Secure; SameSite=Lax$/);
  assert.ok(!b.writes[0].includes('Domain='));
  assert.match(b.nodes['analytics-status'].textContent, /제외됩니다/);
  assert.equal(b.nodes['analytics-exclude'].disabled, true);
});
test('saved cookie is recognized after reopening, independently of other cookies', () => {
  const b = browser('theme=dark; __Host-player0_analytics_opt_out=1; locale=ko');
  assert.match(b.nodes['analytics-status'].textContent, /제외됩니다/);
  assert.equal(b.writes.length, 0);
});
test('similar names and values do not count as exclusion', () => {
  for (const value of ['other__Host-player0_analytics_opt_out=1', '__Host-player0_analytics_opt_out=10']) {
    assert.match(browser(value).nodes['analytics-status'].textContent, /제외 설정이 없습니다/);
  }
});
test('explicit removal expires only the same host-only cookie', () => {
  const b = browser('__Host-player0_analytics_opt_out=1'); b.nodes['analytics-include'].click();
  assert.equal(b.cookie(), ''); assert.match(b.writes[0], /Max-Age=0/);
  assert.match(b.nodes['analytics-status'].textContent, /제외 설정이 없습니다/);
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
