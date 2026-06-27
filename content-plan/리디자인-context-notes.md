# 리디자인 컨텍스트 노트 (2026-06-28)

목표: 사이트가 "AI가 만든 템플릿"으로 읽히지 않도록, 구포국수 고유 정체성으로 시각 레이어 재설계. 콘텐츠·SEO·구조화데이터(JSON-LD)·JS·접근성은 보존.

## 진단 — 기존이 AI 티 나는 이유
- AI 디폴트 룩 #1 그대로: 크림(#F9F8F5) + Noto Serif KR + 테라코타(#8B5E3C).
- 영어 eyebrow(OUR STORY/PROGRAM/REVIEWS), 01/02/03 번호, rounded-2xl + 큰 soft shadow + hover translateY-8.
- wave SVG divider, grain overlay — 전형적 AI 장식.

## 새 디자인 시스템 — "낙동강이 말린 80년"
시그니처: 널어 말린 소면 가닥(가는 세로선)이 hero에 매달려 흔들리는 모티프. 섹션 구분도 strand-divider(짧은 세로 틱)로.

팔레트(재료에서 도출, 테라코타 탈피):
- --ink #211A12 (간장빛 다크우드/밤)
- --paper #F4ECDB (소면/생밀 따뜻한 크림 — AI 크림보다 더 금빛)
- --card #FCF8EF
- --gold #C68A1E / --gold-deep #A06E12 (금빛노을브릿지 — 주 액센트/CTA, 흰글씨 대비 위해 deep 사용)
- --river #2C5A52 (낙동강 청자빛 — 두 번째 차가운 축, 모노톤 브라운 탈피)
- --seal #B23A2A (낙관 주홍 — 로고/푸터 도장 점에만, "악세서리 하나")
- --taupe #6E6151 (따뜻한 본문 보조)

타이포:
- Display: Song Myung (드라마틱 명조, Noto Serif KR 디폴트 탈피)
- Body/UI: Pretendard 유지

레이아웃 원칙:
- 카드 radius 4px + hairline border, 그림자 절제, hover는 translateY-3 + border 금색.
- eyebrow 영어 → 한글 마커(.mark: 금색 세로선 + 한글 라벨). strand 모티프와 연결.
- wave/grain 제거 → 평면 색면 + strand-divider.
- process는 진짜 순서라 번호 유지(명조 숫자 + hairline 연결선).
- hero: 어두운 ink 그라데이션 + 소면 strand 흔들림(로드 모션 1회 절제), 좌측 정렬 대형 명조 헤드라인 + 금색 솔리드 버튼.

## 보존
- <head> 전체(GA, meta, OG, canonical), 모든 JSON-LD(@graph/Event/FAQ/Breadcrumb), naver-site-verification.
- 모든 카피 텍스트, 링크(naver 예약/카카오/인스타/블로그), sr-only GEO 블록.
- 하단 JS(헤더 스크롤/모바일메뉴/IntersectionObserver reveal/FAQ 아코디언) — 클래스명 유지하여 무수정.
- 접근성(skip link, aria, prefers-reduced-motion → strand 흔들림도 정지).

## 빌드
- tailwind.css는 prebuilt 서브셋. 새 유틸 클래스 추가 시 재빌드 필요.
- `node_modules/.bin/tailwindcss -i tailwind.input.css -o tailwind.css --minify` 로 재빌드 완료(16.5KB).

## 완료 기록 (2026-06-28)
- 히어로 배경 교체: 기존 hero-bg.jpg(손글씨 간판, 밝은 크림 배경)는 다크 오버레이로 헤드라인이 묻혀 가독성 불량 → **gupo-noodle-drying.jpg(널어 말린 소면 가닥, 시그니처 모티프)** 로 변경. 좌측 90% 어둡게 깔아 헤드라인 가독성 확보. 손글씨 간판은 "이야기" 섹션 이미지로 이동(브랜드 자산으로 적합).
- 검증: 데스크톱 전 섹션 스크린샷 확인, FAQ 아코디언 동작 확인, 콘솔 에러 0. 모바일 리사이즈는 MCP 스크린샷에 반영 안 됨(렌더 1512 고정) — 반응형은 기존 md: 분기 + process/stat grid-cols-2 유지로 대응.
- 보존 확인: JSON-LD/GA/메타/naver 인증/JS/카피/링크/sr-only 전부 무수정. 구색상(#8B5E3C 등)·Noto Serif·영어 eyebrow 0건.
- 미커밋: 사용자 요청 시 커밋(현재 git main 브랜치).
