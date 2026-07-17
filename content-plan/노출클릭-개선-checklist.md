<!-- 2026-07-17 노출량·CTR 개선 + 플레이스→홈페이지 트래픽 분산 작업 체크리스트 -->

# 노출·클릭 개선 작업 체크리스트 (2026-07-17)

> 근거 데이터. 서치어드바이저 최근 30일 — 노출 7.9천 / 클릭 42 / CTR 0.5%.
> 브랜드 검색(구포국수체험관) 노출 3,074에 클릭 5(0.2%) = 플레이스가 흡수.
> 목적형 검색(주차 1.2~1.9% · 예약 2.4% · 무료체험 3.3%)은 CTR 높음 → 전용 페이지로 공략.

## 1. CTR (클릭률)
- [x] 홈 title → "구포국수체험관 공식 홈페이지 | 예약·가격·주차 안내"
- [x] 홈 meta description → 공식·가격·보호자무료·주차지원·견적서 두괄식 리라이트
- [x] og:title / twitter:title 동기화 (WebPage 스키마 name·dateModified 포함)

## 2. 노출량 (색인 문서 1 → 8)
- [x] guide/guide.css 공용 스타일 (디자인 토큰 동일)
- [x] guide/booking-price.html — 예약·가격·소요시간 총정리
- [x] guide/parking.html — 주차 안내
- [x] guide/age.html — 몇 살부터 가능?
- [x] guide/experience-course.html — 체험 순서 (HowTo 스키마 포함)
- [x] guide/late-arrival.html — 지각·입장·엘리베이터 안내
- [x] guide/busan-with-kids.html — 부산여행 아이랑
- [x] guide/walking-course.html — 체험 후 낙동강 도보 코스
- [x] 각 페이지: 고유 title/desc/canonical/OG + Article·FAQPage·BreadcrumbList JSON-LD + 두괄식 첫 문단

## 3. 연결 (크롤 확장·분산)
- [x] vercel.json에 cleanUrls (guide/parking.html → /guide/parking)
- [x] sitemap.xml 8개 URL로 갱신 (lastmod 2026-07-17)
- [x] index.html FAQ 아래 '이용 가이드' 링크 섹션 추가 (표준 a href)
- [x] footer에 가이드 링크 추가

## 4. 부수 수정
- [x] FAQ 화면↔스키마 문구 불일치 3건 동기화

## 5. 검증·마무리
- [x] 전체 8페이지 JSON-LD 파싱·태그 짝·내부링크·사이트맵 검사 (ALL PASSED)
- [x] tailwind.css 재빌드 (md:col-span-2 등 새 클래스 포함 확인)
- [x] git 커밋
- [ ] (사용자 액션) 배포 확인 후 서치어드바이저 → 요청 > 웹페이지 수집요청으로 신규 7개 URL 제출
- [ ] (사용자 액션) 2~4주 후 서치어드바이저에서 키워드별 노출·CTR 재확인
