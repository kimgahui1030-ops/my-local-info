# 인스타그램 카드뉴스 발행: 기존 업로더를 바탕으로 한 기획·설계 (2026-10-05)

근거는 Google Drive 백업에 있는 두 업로더와 메모리 노트, 그리고 외부 자료입니다.
- **사용자 업로더**(자동업로더 V2.4.2 / QualiTube Uploader): `mlx.py`, `config.py`, `mlxproxy.py`, 사용 설명서, `uploader-prod-migration.md`, `capcut-export-upload.md`, `one-window-at-a-time.md`
- **카이안 딸깍업로더**: `upload.py`, `platforms/__init__.py`, `platforms/instagram.py`, `instagram_business.py`, `core/instagram_login.py`

업로더 본체의 `uploader.py`·`oauth.py`·`autopilot.py` 소스는 Drive에 없어 설명서와 노트로 재구성했습니다.

---

## 1. 결론 먼저

1. **멀티로그인 모바일 기능으로 카드뉴스를 올리는 것은 기술적으로 가능합니다.** 2026년의 Multilogin X "클라우드 폰"은 클라우드에 있는 실제 안드로이드 기기입니다. 인스타그램 앱을 설치하고, 이미지를 폰에 업로드해 앱에서 캐러셀을 올릴 수 있습니다. 앱 안의 조작을 자동화하려면 ADB나 Appium이 필요합니다. Multilogin API는 폰 생성·시작·파일 관리까지만 하고 앱 안의 동작은 제어하지 않습니다.
2. **다만 "기존에 등록한 계정을 모바일로 여는" 방식은 아닙니다.** 지금 Multilogin에 있는 48개는 유튜브용 **브라우저 프로필**(구글 계정)입니다. 클라우드 폰은 별도의 기기라서 인스타 계정을 새로 로그인해야 합니다. 브라우저 프로필을 폰으로 바꾸는 기능은 문서에서 찾지 못했습니다(추정). Multilogin에 인스타 계정이 등록된 기록도 없습니다.
3. **발행 방식을 정하는 가장 큰 변수는 "음악"입니다.** 딸깍업로더 코드에는 "사진/캐러셀 보너스는 음악이 포함된 게시물만 대상(2026-08-28, 메타 고객센터 확인)"이라는 기록이 있습니다. 그런데 공개 자료에서는 음악이 필수라는 근거를 찾지 못했습니다(음악을 넣으면 릴스 탭 노출이 늘어난다는 설명만 있음). 인스타 웹·비즈니스 스위트 예약·공식 API는 사진 게시물에 음악을 붙일 수 없고, **앱만 가능합니다.** 그래서 음악이 필수로 확인되면 앱 경로(폰 또는 클라우드 폰)가 사실상 유일한 길이 됩니다. 필수가 아니면 예약이 되는 공식 경로로 갈 수 있습니다. **이것부터 확인해야 합니다.**
4. 권장하는 구조는 이렇습니다. 제작은 `cardnews/`가 맡습니다. 발행은 기존 업로더의 **사이드카 규약과 어댑터 규약**을 그대로 따르는 "발행 큐"로 넘기고, 발행 경로는 계정마다 어댑터를 골라 끼웁니다. 처음 3계정은 사람이 마지막 [공유]를 누르는 방식으로 검증합니다.

---

## 2. 기존 업로더에서 가져올 것

| 항목 | 기존 업로더의 방식 | 인스타 발행에 적용 |
|---|---|---|
| 큐 규약 | 영상 옆 같은 이름 `.json` 사이드카. `channel` 이 폴더 채널과 다르거나 JSON이 깨지면 올리지 않음. 끝나면 `완료` 폴더로 이동 | 게시물 폴더 + `post.json` 사이드카, 같은 검증 규칙 |
| 어댑터 규약(카이안) | `upload(path, meta, cfg) -> {status, url, note}`. status 는 ok / manual / deferred / fail / blocked. 예외는 밖으로 던지지 않음 | 인스타 어댑터 5종을 같은 규약으로 |
| 계정 = 프로필 | 채널 1개 = Multilogin 프로필 1개(`profile_id`, `folder_id`), Selenium WebDriver 포트로 구동 | 웹 경로를 쓸 때 계정별 프로필. Playwright 코드는 Selenium으로 옮기거나 CDP 지원 여부를 먼저 시험 |
| 예약 | 유튜브는 `private + publishAt` 서버 예약이라 PC를 꺼도 됨. 업로드 순간에만 PC 필요 | 인스타 웹은 예약이 없어 발행 시각에 PC가 켜져 있어야 함. 서버 예약은 비즈니스 스위트나 API만 가능 |
| 슬롯 배정 | 하루 편수·시각, 기존 예약 조회, 시각 흔들기, 5분 미만 중복 차단 | 계정별 하루 슬롯(예: 5개), 같은 규칙 |
| 속도 조절 | 프로필 전환 30~90초, 같은 프로필 내 15~45초, 사이클당 1개, 창은 한 번에 하나 | 그대로 |
| 안전장치 | `state/STOP`, 실행 잠금, 내용 해시 중복 방지, `ledger.jsonl`, 업로드 후 차단 점검 | 그대로 |
| 알림 | 텔레그램 봇 | 발행 결과·수동 대기 건 알림 |

---

## 3. 발행 경로 5가지 비교

| 경로 | 예약 | 음악 | PC 꺼도 됨 | 약관 위험 | 준비 | 현재 상태 |
|---|---|---|---|---|---|---|
| **A. 수동(내 폰)** | 앱 예약 가능 | ✅ | ✅ | 없음 | 없음 | 바로 가능 |
| **B. 클라우드 폰(Multilogin)** | 앱 예약 가능 | ✅ | ✅(사람 조작 시) | 사람이 누르면 낮음 / Appium 자동화는 자동화 금지 조항에 걸릴 소지 | 계정별 폰 + 분 단위 요금 | 미착수 |
| **C. 인스타 웹 자동(`instagram.py post()`)** | ❌ | ❌ | ❌ | 자동화 금지 조항 소지 | 프로필 로그인 | 코드 있음, [공유하기] 실제 클릭 미검증 |
| **D. 메타 비즈니스 스위트** | ✅(최대 75일) | ❌(예약 시 음악 저장 불가 보고) | ✅ | 공식 도구라 낮음 | 프로페셔널 + 페이지 연결 | `instagram_business.py`는 릴스 전용, 캐러셀 확장 필요 |
| **E. 공식 API(Graph)** | ✅ | ❌ | ✅ | 없음(공식) | 메타 앱 + 토큰 + 이미지 공개 URL | 미착수 |

공식 API 수치(외부 자료, 착수 시 재확인): 계정당 24시간 100건, 캐러셀은 1건으로 계산, 캐러셀 최대 10장. 남은 한도는 `content_publishing_limit` 으로 확인합니다.

클라우드 폰 비용(외부 자료): 분당 약 $0.011, 플랜에 60~450분 포함. 한 건에 4분이 걸린다고 가정하면 48계정 × 하루 5건 × 4분 = 하루 960분으로 **월 약 $300** 수준입니다(추정). 3계정이면 월 약 $20입니다.

---

## 4. 권장 설계

### 4-1. 흐름
```
cardnews/out/<날짜>/<id>/   →  export_publish.py  →  발행대기/<계정>/<슬롯시각>_<id>/
 (검수 통과 ready 만)                                   cover.jpg … + post.json
                                                              │
                                     publish.py (작업 스케줄러 10분마다, 1회 실행 후 종료)
                                                              │
                         계정별 어댑터: manual | cloudphone | web | mbs | api
                                                              │
                                     완료/ 이동 · ledger.jsonl · meta.json published 기록 · 텔레그램
```

### 4-2. `post.json` 사이드카
```json
{
  "channel": "계정 표시 이름",
  "images": ["cover.jpg", "slide-02.jpg"],
  "caption": "…",
  "publish_at": "2026-10-06T08:40:00+09:00",
  "music_query": "선택 — 앱 경로에서만 사용",
  "source_id": "cardnews id",
  "content_hash": "이미지+캡션 해시(중복 방지)"
}
```
업로더와 같은 규칙을 씁니다. `channel` 이 폴더 계정과 다르면 건너뜁니다. 키 오타나 깨진 JSON이 있으면 그 건만 멈춥니다. 끝나면 `완료` 폴더로 옮깁니다.

### 4-3. 계정 설정 (`cardnews/brands.json` 확장)
```json
"sample": {
  "handle": "@…", "label": "…", "accent": "#…",
  "publish": {"adapter": "manual", "daily_slots": ["08:40", "12:10", "18:30", "21:00", "22:30"],
              "jitter_min": 15, "mlx_profile_id": null, "cloudphone_id": null, "auto_post": false}
}
```

### 4-4. 어댑터별 동작
- **manual**: 게시물 폴더를 Drive 동기화 폴더로 복사하고, 캡션 txt를 남기고, 텔레그램으로 "지금 올릴 것"을 알립니다. 상태는 `manual`이고, 사용자가 발행 링크를 알려주면 `ok`가 됩니다.
- **cloudphone**: Multilogin API로 그 계정의 폰을 시작하고, 이미지를 폰 Library에 올립니다. 이후 앱에서 사람이 캐러셀 선택 → 음악 → 캡션 붙여넣기 → [공유]를 합니다. 캡션은 클립보드나 메모로 전달합니다. 이 설계는 **마지막 [공유]를 사람이 누르는 것**을 기본으로 둡니다. 카이안 업로더가 다음 루프에 적용한 원칙과 같습니다.
- **web**: 기존 `instagram.post()` 를 재사용하고, 시작값은 `auto_post=false` 입니다. 쓰기 전에 한 계정으로 [공유하기]까지 실측하는 검증 1회가 선행 조건입니다. Multilogin 프로필에서 돌리려면 Selenium 포팅이 필요합니다.
- **mbs**: `instagram_business.py`에 이미지 캐러셀 경로를 추가합니다. 서버 예약이라 PC를 꺼도 되지만, 음악은 붙지 않습니다.
- **api**: 이미지를 Cloudflare Pages/R2에 올려 공개 URL을 만들고 → 컨테이너 생성 → 캐러셀 컨테이너 → publish 순서로 진행합니다. 발행 직후 공개 URL은 내립니다.

### 4-5. 지켜야 할 운영 규칙 (기존 업로더 규칙 그대로)
- 창·폰은 한 번에 하나만 엽니다. 시작 전에 같은 프로필은 stop합니다.
- 사이클당 1건만 처리하고, 계정 전환 사이 30~90초 쉽니다.
- 계정당 하루 슬롯 상한을 두고, 시각을 흔들고, 5분 미만 중복을 차단합니다.
- `STOP` 파일이 있으면 즉시 멈추고, 같은 내용 해시는 다시 올리지 않습니다.
- 발행 후 10분 뒤 게시물이 보이는지, 차단·제한 알림이 없는지 점검합니다.

---

## 5. 단계별 진행

| 단계 | 할 일 | 끝나는 조건 |
|---|---|---|
| **0. 확인** | 계정 1개를 프로페셔널로 전환해 대시보드에서 보너스 조건(음악 필요 여부, 조회수 기준, 팔로워 조건)을 직접 확인 | 음악 필수 여부 확정 → 경로 결정 |
| **1. 3계정 시범** | `export_publish.py` + `publish.py` + manual/cloudphone 어댑터, 사람이 [공유] | 2주간 하루 5건 무사고, 도달·보너스 초대 여부 기록 |
| **2. 예약 경로** | 음악이 필수가 아니면 mbs 또는 api 어댑터로 무인 예약 | PC를 꺼도 하루치 발행 |
| **3. 확장** | 결과가 좋으면 12계정 → 48계정, 계정별 주제 분리 | 계정 제한·연쇄 정지 0건 유지 |

---

## 6. 위험과 판단이 필요한 것
- **약관**: 인스타그램은 허가 없는 자동화 접근을 금지합니다. 웹·앱 화면을 자동으로 조작하는 경로(C, B의 Appium 자동화)는 이 조항에 걸릴 소지가 있습니다. 공식 경로(D, E)와 사람이 누르는 경로(A, B 수동)는 이 위험이 낮습니다.
- **다계정 연결**: 기기 지문과 IP를 분리해도 메타는 콘텐츠 유사성, 정산 정보, 행동 패턴 같은 다른 신호로 계정을 연결할 수 있습니다. 이 설계에는 탐지를 피하기 위한 설정을 넣지 않았습니다. 3계정 단계에서 실제로 문제가 없는지 확인한 뒤 늘립니다.
- **보너스 조건 불확실**: 한국 조회수 기준, 음악 필수 여부, 한 사람이 여러 계정으로 보너스를 받을 수 있는지는 공식 확인이 안 됐습니다. 해외 사용자 사례로 "3개월 사진 게시물 조회수 500만" 조건을 안내받았다는 글도 있어, 기준은 지역·계정마다 다를 수 있습니다.
- **기존 코드 불일치**: `instagram.py` 의 `auto_post` 기본값이 코드(true)와 설정 예시(false)에서 다릅니다. `false` 로 통일해야 합니다.

## 참고
- Multilogin 클라우드 폰·자동화: [Cloud phones API](https://multiloginx.helpjuice.com/en_US/postman/cloud-phones-api), [Appium cloud phone automation](https://multiloginx.helpjuice.com/en_US/custom-api-scripts-with-python/appium-cloud-phone-automation), [ADB in cloud phones](https://multiloginx.helpjuice.com/en_US/cloud-phones/adb-in-cloud-phones), [Android profiles](https://multilogin.com/help/en_US/profile-behavior-identity/android-profiles), [Multilogin repositions as a cloud phone platform](https://www.globenewswire.com/news-release/2026/07/31/3336738/0/en/multilogin-repositions-as-a-cloud-phone-platform-for-managing-multiple-social-media-accounts-cuts-entry-price-to-7-08-month.html), [Phone farm cost vs cloud phone pricing](https://multilogin.com/blog/phone-farm-cost-vs-cloud-phone-pricing/)
- 인스타 게시 API: [Publish Content using the Instagram Platform](https://developers.facebook.com/docs/instagram-platform/content-publishing/), [Instagram Posting API 2026 (Blotato)](https://www.blotato.com/blog/instagram-posting-api)
- 비즈니스 스위트 캐러셀 예약과 음악: [How to Schedule Carousel Posts (AdaptlyPost)](https://adaptlypost.com/blog/how-to-schedule-carousel-posts-on-instagram-and-facebook)
- 보너스와 음악: [Instagram Bonuses for Photos and Carousels (Miraflow)](https://miraflow.ai/blog/instagram-photo-carousel-bonus-program-explained-2026), [Threads 사용자 사례](https://www.threads.com/@bookedallnight_withnakita/post/DW6sx4ckbjl/instagram-said-i-can-start-getting-bonuses-if-i-can-meet-all-the-qualifications)
