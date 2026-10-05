#!/usr/bin/env python3
"""인스타 벤치마킹 계정 수집 — 메타 공식 API(Business Discovery)로 "터진 글"을 찾는다.

로그인 쿠키·화면 조작 없이 내 프로페셔널 계정의 토큰으로 다른 비즈니스·크리에이터
계정의 공개 게시물 수치(좋아요·댓글·조회수·캡션)를 읽는다. GitHub Actions 에서 매일 돈다.

  IG_USER_ID=... IG_ACCESS_TOKEN=... python3 cardnews/collect/ig_benchmark.py
  python3 cardnews/collect/ig_benchmark.py --fixture-dir 응답JSON폴더   # 네트워크 없이 시험

결과: cardnews/sources/benchmark/<날짜>.json (계정별 중앙값·터진 글).
collect_sources.py 가 오늘 파일의 터진 글을 소재로 합친다.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "sources" / "benchmark"
KST = timezone(timedelta(hours=9))
FIELDS = ("followers_count,media_count,media.limit({n}){{id,caption,like_count,comments_count,"
          "view_count,media_type,media_product_type,permalink,timestamp}}")


def fetch(username: str, n: int, user_id: str, token: str, version: str) -> dict:
    fields = f"business_discovery.username({username}){{{FIELDS.format(n=n)}}}"
    url = (f"https://graph.facebook.com/{version}/{user_id}?"
           + urllib.parse.urlencode({"fields": fields, "access_token": token}))
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)["business_discovery"]
    except urllib.error.HTTPError as e:  # 메타 오류 메시지를 그대로 남긴다(토큰은 남기지 않음)
        msg = json.loads(e.read() or b"{}").get("error", {}).get("message", str(e))
        raise RuntimeError(msg) from None


def analyze(acc: dict, data: dict, multiple: float) -> dict:
    """사진·캐러셀만으로 좋아요 중앙값을 내고, 그 배수 이상을 터진 글로 고른다."""
    feed = [m for m in data.get("media", {}).get("data", [])
            if m.get("media_type") in ("IMAGE", "CAROUSEL_ALBUM") and m.get("media_product_type", "FEED") == "FEED"]
    likes = [m["like_count"] for m in feed if isinstance(m.get("like_count"), int)]
    median = statistics.median(likes) if likes else None
    hot = []
    for m in feed:
        lk = m.get("like_count")
        if median and isinstance(lk, int) and lk >= multiple * median:
            hot.append({**m, "x_median": round(lk / median, 1)})
    hot.sort(key=lambda m: m["x_median"], reverse=True)
    return {
        "username": acc["username"], "direction": acc["direction"],
        "followers": data.get("followers_count"), "media_count": data.get("media_count"),
        "feed_posts": len(feed), "likes_hidden": len(feed) - len(likes),
        "median_likes": median, "hot": hot,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--fixture-dir", type=Path, help="<username>.json 응답을 담은 폴더(시험용)")
    a = ap.parse_args(argv)

    cfg = json.loads((HERE / "ig_accounts.json").read_text("utf-8"))
    user_id, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN")
    version = os.environ.get("IG_GRAPH_VERSION", "v23.0")
    if not a.fixture_dir and not (user_id and token):
        print("IG_USER_ID / IG_ACCESS_TOKEN 이 없어 벤치마킹 수집을 건너뜁니다.")
        return 0

    day = a.date or datetime.now(KST).date().isoformat()
    accounts, errors = [], []
    for acc in cfg["accounts"]:
        try:
            if a.fixture_dir:
                data = json.loads((a.fixture_dir / f"{acc['username']}.json").read_text("utf-8"))
            else:
                data = fetch(acc["username"], cfg.get("media_limit", 50), user_id, token, version)
            r = analyze(acc, data, cfg.get("hot_multiple", 2.0))
            accounts.append(r)
            print(f"✓ @{acc['username']}: 사진·캐러셀 {r['feed_posts']}개, 중앙값 {r['median_likes']}, 터진 글 {len(r['hot'])}개")
        except Exception as e:
            errors.append({"username": acc["username"], "error": str(e)[:300]})
            print(f"✖ @{acc['username']}: {e}")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{day}.json"
    out.write_text(json.dumps({"date": day, "accounts": accounts, "errors": errors},
                              ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"→ {out.name}: 계정 {len(accounts)}개, 터진 글 {sum(len(x['hot']) for x in accounts)}개, 실패 {len(errors)}개")
    return 0 if accounts or not errors else 1


if __name__ == "__main__":
    sys.exit(main())
