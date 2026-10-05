# cardnews — 인스타그램 카드뉴스 제작 도구 (1단계 MVP)

말로 요청하면 Claude가 카피를 쓰고, 이 도구가 검수한 뒤 1080×1350 JPEG와 캡션을 한 폴더로 묶어 줍니다. 설계 배경은 `docs/instagram-cardnews-plan.md`, Claude 작업 절차는 `.claude/skills/cardnews/SKILL.md` 를 보세요.

## 설치
```bash
pip install -r cardnews/requirements.txt
python3 -m playwright install chromium
```

## 사용
```bash
python3 cardnews/render.py cardnews/specs/sample-gg-birth.json   # 표지 1장(매거진형)
python3 cardnews/render.py cardnews/specs/sample-sn-rent.json    # 정보형 캐러셀 5장
python3 cardnews/render.py cardnews/specs/*.json --check         # 검수만
python3 cardnews/selftest.py                                     # 도구 자체 점검
```

결과는 `cardnews/out/<날짜>/<id>/` 에 생깁니다(저장소에는 올라가지 않음).

| 파일 | 내용 |
|---|---|
| `cover.jpg`, `slide-02.jpg` … | 올릴 이미지, 이름 순서대로 |
| `caption.txt` | 그대로 붙여넣을 캡션 |
| `credit.txt` | 이미지 출처 |
| `meta.json` | 스펙, 검수 결과(`status: ready / needs_fix`), 발행 기록 |

## 구성
| 파일 | 역할 |
|---|---|
| `render.py` | 스펙 → 검수 → HTML 템플릿 → Playwright 캡처(JPEG 92%) |
| `lint.py` | 검수 게이트: 제목 길이·강조, 캡션 길이·해시태그 상한, 사실(facts) 대조, 과장어, 이미지 출처·원본 사진 금지, 7일 중복, 글자 넘침, 표지 크롭 안전선 |
| `templates/` | `magazine.html`(표지 A), `info_body.html`·`info_cta.html`(정보형 캐러셀) |
| `brands.json` | 계정별 핸들·라벨·대표색 — 계정을 늘리면 여기에 추가 |
| `prompts/copy_ko.md` | 카피 규칙과 스펙 형식 |
| `fonts/` | Pretendard (SIL OFL 1.1, `OFL-Pretendard.txt`) |

## 매일 자동으로 돌리기
```
05:30 KST  GitHub Actions cardnews-collect  →  RSS·지역 데이터 수집 → cardnews/sources/<날짜>.json (main 에 커밋)
07:00 KST  Claude 루틴(ROUTINE.md)          →  소재 선택·카피·검수 → cardnews/specs/daily/<날짜>/ (cardnews-daily 브랜치에 푸시)
  푸시 직후 GitHub Actions cardnews-render   →  Pexels 사진 → 렌더 → 구글 드라이브 "카드뉴스/<날짜>/" → 텔레그램 알림
사용자                                       →  폰 드라이브 앱에서 저장 → 인스타 앱에서 음악·캡션 넣고 공유
```
- 수집 소스: `collect/feeds.json` (계정 방향 `life`/`issue` 와 맞춤). 계정별 하루 개수: `brands.json` 의 `daily_count`.
- 인스타 벤치마킹(`collect/ig_benchmark.py`, 공식 API): 계정마다 최근 28일 중앙값 대비 좋아요·댓글 2배 이상을 "터진 글"로, 14일 무게시는 휴면으로 기록하고 팔로워 증가를 하루 단위로 환산합니다. 새 후보는 `collect/ig_inbox.txt` 에 아이디를 적으면 확정·관찰·탈락으로 판정합니다.
- 모든 외부 요청은 `collect/polite.py` 를 거칩니다: 호스트별 간격·지터·상한, 429·봇 확인·로그인 요구 시 그 호스트 중단, 연속 3회 실패 시 중단. 프록시·다계정·캡차 풀기는 쓰지 않습니다.
- 알림(`collect/notify.py`): 3일 안에 평소의 5배 이상 나온 글은 바로, 지난 7일 정리는 월요일에 텔레그램으로 보냅니다. 평소보다 크게 줄어든 피드도 알립니다.
- 저장소 Secrets: `RCLONE_CONFIG`(구글 드라이브), `DRIVE_DIR`, `PEXELS_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — 없는 것은 그 단계만 건너뜁니다.
- 예약 수집(`schedule`)은 워크플로 파일이 기본 브랜치(main)에 있어야 동작합니다.

## 아직 없는 것 (2단계 이후)
AI 이미지 생성, 해외 이슈형 템플릿 B, 인스타 자동 발행·예약, 성과 수집. 수집기(`collect.py`)는 PC의 `Desktop\claude\cardnews\` 에 있습니다.

## 참고한 공개 소스 (모두 MIT, 코드 복사 없이 방식만 참고)
- jeevanbavandla/instagram-carousel-skill — 고정 크기 HTML 슬라이드 + Playwright 캡처 방식
- ecomcirclesocial-ecom/carousel-generator — Jinja 템플릿 + `**강조**` 하이라이트, 장마다 역할(role) 구분
- Hainrixz/open-carrusel — 대화로 슬라이드를 만들고 PNG로 내보내는 흐름
