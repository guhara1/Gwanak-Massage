# 간다GO 관악출장마사지

서울 관악구 방문 건강관리(마사지) 예약 안내 정적 웹사이트입니다.
순수 HTML + 인라인 CSS/JS로 구성되어 **런타임 의존성이 0개**이며, 빌드 없이 그대로 배포할 수 있습니다.

## 구조

```
/                         홈
/about/                   간다GO 소개
/gwanak-gu/               관악 출장마사지 (관악 대표)
/gwanak-gu/area/          지역별 안내 (허브)
/gwanak-gu/<권역>-area/   3개 권역 페이지 (봉천·신림·남현)
/gwanak-gu/<동>-dong/     22개 동 페이지 (봉천권역 10 · 신림권역 11 · 남현권역 1)
/gwanak-gu/stations/      지하철역별 안내 (허브, CollectionPage)
/gwanak-gu/stations/<역>/ 8개 역 페이지 (2호선 4 · 신림선 4)
/gwanak-gu/hours/ checklist/ safety/ faq/   관악 안내 개별 페이지(각 ~2000자)
/course/                  코스안내 (전체 코스 허브)
/course/fatigue/ aroma/ sports/ couple/ group/ price/ guide/  코스 개별 페이지(각 ~2000자)
/reservation/             예약안내
/guide/                   이용가이드
/reviews/                 고객후기
/customer/                고객센터
/privacy/ /terms/ /youth/ 정책 페이지
sitemap.xml robots.txt site.webmanifest  메타 파일
favicon.svg favicon.ico icon-*.png assets/og-cover.jpg  브랜드 이미지
```

총 57페이지. 지역 메뉴는 권역 → 동 2단계, 역세권은 별도 `지하철역별 안내`(노선 → 역) 드롭다운으로
설계했습니다. 핵심 키워드 **"관악 출장마사지"**는 대표 페이지(`/gwanak-gu/`) 하나에 집중시키고,
**"신림역 출장마사지" 등 역명 키워드**는 8개 역세권 페이지로 확장합니다.

- 봉천동·신림동의 행정동(은천·성현·청룡·서원·신원·삼성동 등)은 대표 동 본문에서 통합 안내해
  별도 페이지 양산(도어웨이)을 회피합니다.
- **사당역·신대방역**은 별도 페이지를 만들지 않고 인접 동(남현동·보라매동·조원동) 본문 섹션으로 흡수합니다.
- 2호선: 신림·서울대입구·봉천·낙성대 / 신림선: 당곡·서원·서울대벤처타운·관악산.
- 동·역 페이지 4-gram 자카드 유사도: 동 평균 ≈ 38%, 역 평균 ≈ 39% (도어웨이 목표 ≈ 40% 이하 충족).

## 빌드 (선택)

배포에는 빌드가 필요 없습니다. 공통 헤더/푸터/SEO 블록을 일괄 수정할 때만 사용합니다.

```bash
python3 tools/build.py      # 모든 HTML + sitemap/robots/manifest + IndexNow 키 파일 생성
python3 tools/gen_icons.py  # 파비콘 / PWA 아이콘 / OG 이미지 생성 (Pillow 필요)
```

## 색인 즉시 통보 (IndexNow / Google / sitemap)

### 1) IndexNow — 빙·네이버·얀덱스 즉시 통보 (권장, 무료·무설정)
- 인증 키 파일은 빌드 시 자동 생성: `ff387028a8fb421199a855dcb0d5c7a8.txt`
  → 배포되면 `https://gwanak-massage.pages.dev/ff387028a8fb421199a855dcb0d5c7a8.txt` 로 노출
- 수동 제출:
  ```bash
  python3 tools/indexnow.py --all        # sitemap 전체
  python3 tools/indexnow.py --changed    # 직전 커밋 대비 바뀐 페이지만
  python3 tools/indexnow.py --all --dry-run   # 전송 없이 목록 확인
  ```
- **자동화**: `.github/workflows/indexnow.yml` 가 `main` 에 페이지/사이트맵이 바뀌어
  푸시될 때마다 변경 URL을 IndexNow로 통보합니다. (별도 시크릿 불필요)
- 네이버는 [서치어드바이저](https://searchadvisor.naver.com)에 사이트 등록 + IndexNow 사용 설정을 한 번 해두면 더 확실합니다.

### 2) Google Indexing API (선택, 보조)
- ⚠️ 공식적으로 **JobPosting / BroadcastEvent** 페이지만 지원합니다. 일반 페이지는
  무시될 수 있으므로, 구글은 **Search Console 등록 + sitemap 제출**이 정공법입니다.
- 사용하려면: Google Cloud에서 Indexing API 사용 설정 → 서비스계정 JSON 발급 →
  Search Console 속성에 서비스계정 이메일을 '소유자'로 추가 → `pip install google-auth`
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS=서비스계정.json
  python3 tools/google_indexing.py --all
  ```
- CI 자동화: 위 JSON 전체를 GitHub 시크릿 `GOOGLE_INDEXING_SA` 로 넣으면
  워크플로가 IndexNow와 함께 자동 호출합니다.

### 2.5) 네이버 빠른 색인 (Yeti + sitemap + RSS + IndexNow)
- `robots.txt`에 네이버 **Yeti·NaverBot**, 다음 **Daumoa**, 구글·빙 봇을 명시 허용했습니다.
- 빌드 시 `sitemap.xml`(lastmod 포함)과 **`rss.xml`**(RSS 2.0, 57개 항목)을 함께 생성합니다.
- [네이버 서치어드바이저](https://searchadvisor.naver.com) → 사이트 등록(소유확인 메타 적용됨) →
  **요청 > 사이트맵 제출**에 `sitemap.xml`, **RSS 제출**에 `rss.xml`을 등록하고, **IndexNow 사용 설정**을 켜세요.
- 이후 `main` 푸시 시 워크플로가 변경 URL을 IndexNow로 즉시 통보합니다(빙·네이버 공통).

### 3) sitemap ping
- **Google·Bing의 sitemap ping 엔드포인트는 2023년 폐지**되었습니다(404). 더 이상
  유효하지 않으므로, 대신 **Search Console / Bing Webmaster에 sitemap을 한 번 제출**하면
  자동으로 주기적 재크롤되고, 즉시 통보는 위 IndexNow가 대체합니다.

## 배포 전 교체할 항목 (tools/build.py 상단 상수)

| 상수 | 현재값(placeholder) | 설명 |
|---|---|---|
| `BASE_URL` | `https://gwanak-massage.pages.dev` | 메인 도메인(Cloudflare Pages, 설정됨) |
| `PHONE_DISP` / `PHONE_TEL` | `0508-202-4743` | 예약 전화번호(설정됨) |
| `EMAIL` | `help@gwanak-massage.com` | 실제 이메일 |
| `COMPANY.biz_no` | `000-00-00000` | 사업자등록번호 |
| `COMPANY.sales_no` | `2026-서울관악-0000` | 통신판매업신고번호 |
| `COMPANY.ceo` / `privacy_officer` | `김도현` | 대표 / 개인정보보호책임자 |

값을 바꾼 뒤 `python3 tools/build.py`를 다시 실행하면 전 페이지에 반영됩니다.

## SEO / 적법성

- 페이지별 고유 `title` / `description` / `canonical`
- JSON-LD: Organization · WebSite · LocalBusiness · Service · BreadcrumbList · FAQPage · ItemList
- 모든 페이지 탐색경로(Breadcrumb) + 구조화 데이터
- 푸터에 사업자 정보 6필드 + 비의료·만 19세 이상 고지
- `content-visibility` / 시스템 폰트 / 인라인 자원으로 Core Web Vitals 최적화
