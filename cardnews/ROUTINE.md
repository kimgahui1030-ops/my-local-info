# 매일 카드뉴스 자동 제작 (Claude 루틴용 지시서)

매일 아침 새 Claude 세션이 이 문서를 그대로 따라 오늘 치 카드뉴스 스펙을 만들고 푸시합니다. 렌더·사진·드라이브 업로드·알림은 GitHub Actions(`cardnews-render`)가 이어서 합니다.

## 순서

1. **저장소 준비**
   ```bash
   git fetch origin main
   git fetch origin cardnews-daily || true
   if git rev-parse -q --verify origin/cardnews-daily >/dev/null; then
     git checkout -B cardnews-daily origin/cardnews-daily && git merge --no-edit origin/main   # 지난 스펙 유지 + 오늘 소재
   else
     git checkout -B cardnews-daily origin/main
   fi
   pip install -r cardnews/requirements.txt   # 렌더 확인용
   ```
2. **오늘 날짜(KST)와 소재 확인**: `DAY=$(TZ=Asia/Seoul date +%F)`. `cardnews/sources/$DAY.json` 이 없으면 만들지 말고 "오늘 소재 수집이 안 됐다"고 보고한 뒤 끝냅니다. `errors` 에 실패한 피드가 있으면 보고에 적습니다.
3. **계정별 개수 정하기**: `cardnews/brands.json` 에서 `daily_count > 0` 인 계정마다 그 개수만큼, `direction` 이 같은 소재에서 고릅니다.
4. **소재 고르기**
   - 이미 쓴 소재는 제외합니다. `cardnews/specs/daily/` 아래 최근 14일 스펙의 `source.url` 과 같은 링크입니다.
   - 반응이 클 소재를 고릅니다. 숫자가 있는 것, 대상이 분명한 혜택, 의외성 있는 사건, 저장·공유할 이유가 있는 것이 좋습니다.
   - **사실이 부족한 소재는 건너뜁니다.** 쓸 수 있는 사실은 소재의 `title` 과 `summary` 에 있는 것뿐입니다. 원문 링크를 열 수 없다고 가정하고, 요약에 없는 숫자·날짜·대상은 만들지 않습니다.
   - 영어 소재(issue)는 한국어로 쓰되, 고유명사·숫자는 원문 그대로 `facts` 에 넣습니다.
   - `feed: "instagram-benchmark"` 소재는 벤치마킹 계정에서 실제로 터진 글입니다. `metrics.x_median`(좋아요)·`metrics.x_comments`(댓글)는 계정 최근 28일 평소의 몇 배인지입니다. 댓글 배수가 높은 글을 가장 우선합니다(반응·논쟁이 큰 소재). 그다음 좋아요 배수 순입니다. 단, **주제와 구조만 가져오고 문장·사진은 가져오지 않습니다.** 사실은 그 캡션에 적힌 것만 쓰고, 캡션이 짧아 사실이 부족하면 건너뜁니다.
5. **스펙 쓰기**: `cardnews/prompts/copy_ko.md` 규칙을 그대로 따릅니다. 파일은 `cardnews/specs/daily/$DAY/<id>.json` 입니다.
   - `id`: `$DAY-<계정키>-<짧은영문슬러그>`
   - `date`: `$DAY`, `brand`: 계정 키
   - `source`: `{"url": 소재 link, "type": "news" 또는 "local-info", "feed": 소재 feed}`
   - 사진은 `"image": {"query": "영어 검색어 2~4단어"}` 로만 둡니다. 실제 사진은 Actions 가 Pexels 에서 붙입니다. 사람 얼굴이 특정되거나 특정 사건 현장을 재현해야 하는 소재면 이미지를 생략합니다.
   - 생활정보형 여러 단계 내용은 `template: "info"`(5~7장), 단일 사건은 `template: "magazine"`.
6. **검수·확인**
   ```bash
   python3 cardnews/render.py cardnews/specs/daily/$DAY/*.json
   ```
   - `✖` error 는 모두 고칩니다. 고칠 수 없으면 그 스펙을 지웁니다.
   - 사진은 아직 없으니 색 배경으로 나옵니다. 각 `cover.jpg` 를 Read 로 열어 제목 줄바꿈·잘림을 확인합니다.
7. **푸시** — 스펙만 올립니다(이미지는 올리지 않음).
   ```bash
   git add cardnews/specs/daily/$DAY
   git commit -m "feat(cardnews): $DAY 카드뉴스 N건 [CF-Pages-Skip]"
   git push -u origin cardnews-daily
   ```
8. **보고**: 만든 개수(계정별), 각 제목, 건너뛴 소재와 이유, 실패한 피드를 짧게 정리합니다.

## 지킬 것
- 원문에 없는 사실을 만들지 않습니다. 확신이 없으면 그 소재는 버립니다.
- 같은 날 같은 소재를 두 계정에 쓰지 않습니다.
- 정치·질병·사고 피해자처럼 민감한 소재는 자극적인 제목을 쓰지 않습니다.
- 쿠키·토큰·키를 파일에 적지 않습니다.
