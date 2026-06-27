# 전 영역 93점+ 작업 체크리스트 (2026-06-28)

## 신뢰성·SEO
- [ ] favicon: data URI → 실제 /favicon.svg 파일 + 링크
- [ ] robots.txt: Yeti 명시 + AI 검색봇 허용 + Host 제거
- [ ] sitemap.xml: lastmod 2026-06-28
- [ ] JSON-LD: 자가 aggregateRating + review 배열 제거(구글 self-serving 리스크)
- [ ] JSON-LD: WebPage 노드 + dateModified(신선도)
- [ ] og:image / twitter:image → gupo-noodle-drying.jpg(대표성·비율)

## 성능
- [ ] Font Awesome CDN(JS ~1MB+) 제거 → 인라인 SVG 스프라이트로 교체(아이콘 16종)
- [ ] 메뉴 토글 JS를 SVG(menu/close)로 갱신
- [ ] 접근성 focus-visible 전역 스타일

## 접근성(대비)
- [ ] --taupe 어둡게(#5C5042) — 본문 보조 4.5:1
- [ ] 소형 골드 텍스트(.mark/.link-gold) --gold-ink(#7A4F0A)로 대비 확보

## 콘텐츠(기관 방문자 93점)
- [ ] 단체·기관 안내 섹션 신설(id=group, 내비 링크)
  - 세금계산서·현금영수증 발행 / 영업배상책임보험 가입 / 1회차 50명+ 2교실 분반 / 공문·견적서 / 현장결제 / 실내·엘리베이터·인솔
  - 체험학습 절차 4단계 / 교과 연계(맷돌=전통문화, 제면=식생활)
- [ ] FAQ 2건 추가(세금계산서·보험 / 체험학습 공문) — 화면+FAQPage 스키마 동기화

## 마무리
- [ ] tailwind.css 재빌드
- [ ] 브라우저 검증(섹션·아코디언·아이콘·콘솔)
- [ ] 커밋 & 배포(main 푸시)
