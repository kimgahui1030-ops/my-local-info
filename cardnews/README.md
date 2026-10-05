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

## 아직 없는 것 (2단계 이후)
Pixabay·Pexels 자동 검색, AI 이미지 생성, 해외 이슈형 템플릿 B, 자동 발행·예약, 성과 수집. 수집기(`collect.py`)는 PC의 `Desktop\claude\cardnews\` 에 있습니다.

## 참고한 공개 소스 (모두 MIT, 코드 복사 없이 방식만 참고)
- jeevanbavandla/instagram-carousel-skill — 고정 크기 HTML 슬라이드 + Playwright 캡처 방식
- ecomcirclesocial-ecom/carousel-generator — Jinja 템플릿 + `**강조**` 하이라이트, 장마다 역할(role) 구분
- Hainrixz/open-carrusel — 대화로 슬라이드를 만들고 PNG로 내보내는 흐름
