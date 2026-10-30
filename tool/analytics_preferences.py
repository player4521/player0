"""An explicit per-browser analytics opt-out; no visitor identifier or metrics."""

def render(site, shell):
    page = shell(site, lang='ko', path='/analytics-preferences/',
        title='방문 집계 설정 | Player Zero',
        description='이 브라우저의 Player Zero 웹사이트 방문 집계 제외 설정',
        body='''    <section class="page-head">
      <p class="eyebrow">PLAYER ZERO</p>
      <h1>이 브라우저의 방문 집계</h1>
      <p class="lead">사이트를 제작하거나 확인하는 접속을 방문 통계에서 제외할 수 있습니다.</p>
    </section>
    <section class="prose">
      <p id="analytics-status" role="status" aria-live="polite">설정을 확인하고 있습니다.</p>
      <div class="actions">
        <button type="button" class="button" id="analytics-exclude">이 브라우저 집계 제외</button>
        <button type="button" class="button button-secondary" id="analytics-include">집계 제외 해제</button>
      </div>
      <p>선택은 이 브라우저에만 저장됩니다. 다른 기기나 브라우저에서는 별도로 설정해 주세요. 쿠키를 삭제하거나 저장 기간이 만료되면 다시 설정해야 합니다.</p>
      <p>집계 제외 여부만 담은 쿠키를 최대 1년 동안 저장합니다. 개인별 식별번호를 만들거나 사이트 이용을 막지 않습니다. 이미 수집된 과거 통계에는 적용되지 않습니다.</p>
      <noscript><p>이 설정을 변경하려면 JavaScript가 필요합니다.</p></noscript>
      <p><a href="/ko/">홈페이지로 돌아가기</a></p>
    </section>
    <script src="/assets/analytics_preferences.js" defer></script>''')
    return page.replace('<meta name="description"', '<meta name="robots" content="noindex, nofollow">\n  <meta name="description"', 1)
