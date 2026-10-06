// 네이버 광고 전환 추적(프리미엄 로그분석, 신 스크립트 trans) — 모든 공개 페이지 방문과 전화·카톡 클릭을 네이버 광고 보고서로 보낸다
(function () {
  // 네이버 공통키(광고주센터 → 도구 → 프리미엄 로그분석) — 사이트에 공개되는 값이다
  var NAVER_WA = 's_5a33c8edf869';
  // 전환 유형 — call·inquiry는 광고 보고서에 안 나와서 보고서에 나오는 사용자정의 1·2번을 쓴다
  var CNV = { call: 'custom001', kakao: 'custom002' };

  var ready = false;
  var s = document.createElement('script');
  s.src = 'https://wcs.naver.net/wcslog.js';
  s.async = true;
  s.onload = function () {
    if (!window.wcs) return;
    try {
      window.wcs_add = window.wcs_add || {};
      window.wcs_add['wa'] = NAVER_WA;
      window.wcs.inflow('guponoodle.lol');
      window.wcs_do();
      ready = true;
    } catch (e) { /* 추적 실패가 화면을 막지 않게 한다 */ }
  };
  document.head.appendChild(s);

  function trans(type) {
    if (!ready || !window.wcs) return;
    try { window.wcs.trans({ type: type }); } catch (e) { /* 무시 */ }
  }

  // 전화·카카오톡 링크 클릭을 한 곳에서 잡는다 (개인정보는 보내지 않는다)
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('tel:') === 0) trans(CNV.call);
    else if (/(pf|open)\.kakao\.com/.test(href)) trans(CNV.kakao);
  }, true);
})();
