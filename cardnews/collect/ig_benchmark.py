#!/usr/bin/env python3
"""인스타 벤치마킹 계정 수집 — 메타 공식 API(Business Discovery)로 "터진 글"과 계정 상태를 기록한다.

로그인 쿠키·화면 조작 없이 내 프로페셔널 계정의 토큰으로 다른 비즈니스·크리에이터 계정의
공개 게시물 수치를 읽는다. GitHub Actions 에서 매일 돈다.

판정 규칙(이전 발굴기·bench_watch·SNS성장학교 강의에서 가져옴)
- 터진 글: 계정 **최근 28일** 중앙값의 2배 이상. 좋아요뿐 아니라 **댓글** 배수도 본다
  ("소재 판단은 댓글 수"). 옛 대박이 기준을 부풀리지 않도록 최근 창만 쓴다.
- 계정 상태: 마지막 게시 14일 넘으면 휴면 → 그 계정 글은 소재에서 뺀다.
- 팔로워 증가: 지난 스냅샷과의 차이 ÷ 실제 경과일(하루 환산).
- 후보(ig_inbox.txt): 확정·관찰·탈락으로 판정만 하고, 확정이면 그날부터 터진 글도 함께 본다.

  IG_USER_ID=... IG_ACCESS_TOKEN=... python3 cardnews/collect/ig_benchmark.py
  python3 cardnews/collect/ig_benchmark.py --fixture-dir 응답JSON폴더 --date 2000-01-10   # 시험
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import polite  # noqa: E402

OUT = HERE.parent / "sources" / "benchmark"
KST = timezone(timedelta(hours=9))
FIELDS = ("followers_count,media_count,media.limit({n}){{id,caption,like_count,comments_count,"
          "media_type,media_product_type,permalink,timestamp}}")
RATE_CODES = {4, 17, 32, 613}  # 메타 호출 한도 오류 → 즉시 전체 중단


class RateLimited(Exception):
    pass


def fetch(username: str, n: int, user_id: str, token: str, version: str) -> dict:
    fields = f"business_discovery.username({username}){{{FIELDS.format(n=n)}}}"
    url = (f"https://graph.facebook.com/{version}/{user_id}?"
           + urllib.parse.urlencode({"fields": fields, "access_token": token}))
    try:
        return json.loads(polite.get(url, timeout=30))["business_discovery"]
    except urllib.error.HTTPError as e:  # 메타 오류 메시지만 남긴다(토큰은 남기지 않음)
        err = json.loads(e.read() or b"{}").get("error", {})
        if err.get("code") in RATE_CODES:
            raise RateLimited(err.get("message", "호출 한도")) from None
        raise RuntimeError(err.get("message", str(e))) from None


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("+0000", "+00:00"))


def median_or_none(xs: list[int]) -> float | None:
    return statistics.median(xs) if xs else None


def analyze(acc: dict, data: dict, cfg: dict, now: datetime) -> dict:
    window = timedelta(days=cfg.get("window_days", 28))
    mult = cfg.get("hot_multiple", 2.0)
    feed = [m for m in data.get("media", {}).get("data", [])
            if m.get("media_type") in ("IMAGE", "CAROUSEL_ALBUM") and m.get("media_product_type", "FEED") == "FEED"
            and m.get("timestamp")]
    for m in feed:
        m["_ts"] = parse_ts(m["timestamp"])
    recent = [m for m in feed if now - m["_ts"] <= window]
    base = recent if len(recent) >= 5 else feed  # 최근 글이 너무 적으면 전체로 대신
    likes = [m["like_count"] for m in base if isinstance(m.get("like_count"), int)]
    comments = [m["comments_count"] for m in base if isinstance(m.get("comments_count"), int)]
    med_l, med_c = median_or_none(likes), median_or_none(comments)

    last = max((m["_ts"] for m in feed), default=None)
    last_age = (now - last).days if last else None
    status = "휴면" if last_age is None or last_age > 14 else "활동"
    hot = []
    for m in recent:
        lk, cm = m.get("like_count"), m.get("comments_count")
        xl = round(lk / med_l, 1) if med_l and isinstance(lk, int) else None
        xc = round(cm / med_c, 1) if med_c and isinstance(cm, int) and cm >= 10 else None
        if (xl and xl >= mult) or (xc and xc >= mult):
            hot.append({k: v for k, v in m.items() if not k.startswith("_")}
                       | {"x_median": xl, "x_comments": xc, "age_days": (now - m["_ts"]).days})
    hot.sort(key=lambda h: max(h["x_median"] or 0, h["x_comments"] or 0), reverse=True)
    return {
        "username": acc["username"], "direction": acc.get("direction", "life"),
        "followers": data.get("followers_count"), "media_count": data.get("media_count"),
        "feed_posts": len(feed), "recent_posts": len(recent),
        "posts_per_day": round(len(recent) / window.days, 2),
        "likes_hidden": len(base) - len(likes), "median_likes": med_l, "median_comments": med_c,
        "median_basis": "최근" if base is recent else "전체", "last_post_days": last_age,
        "status": status, "hot": hot if status == "활동" else [],
    }


def verdict(r: dict, cfg: dict) -> str:
    """후보 판정(카드뉴스 매거진 기준으로 조정한 bench_watch 규칙)."""
    v = cfg.get("verdict", {})
    if r["status"] != "활동":
        return "탈락"
    med = r["median_likes"] or 0
    if med >= v.get("confirm_median_likes", 200) and r["posts_per_day"] >= v.get("confirm_posts_per_day", 0.5):
        return "확정"
    if med >= v.get("watch_median_likes", 50):
        return "관찰"
    return "탈락"


def followers_growth(username: str, followers: int | None, day: date) -> dict | None:
    """이전 스냅샷과 비교해 하루 환산 팔로워 증가를 낸다(건너뛴 날은 경과일로 나눔)."""
    if followers is None:
        return None
    for f in sorted(OUT.glob("*.json"), reverse=True):
        try:
            d = date.fromisoformat(f.stem)
        except ValueError:
            continue
        if d >= day:
            continue
        for acc in json.loads(f.read_text("utf-8")).get("accounts", []):
            if acc["username"] == username and acc.get("followers") is not None:
                days = (day - d).days
                return {"per_day": round((followers - acc["followers"]) / days, 1), "since": d.isoformat(), "days": days}
    return None


def load_inbox() -> list[dict]:
    path = HERE / "ig_inbox.txt"
    if not path.exists():
        return []
    out = []
    for line in path.read_text("utf-8").splitlines():
        parts = line.split("#", 1)[0].split()
        if parts:
            name = parts[0].rstrip("/").split("/")[-1].lstrip("@")
            out.append({"username": name, "direction": parts[1] if len(parts) > 1 else "life", "candidate": True})
    return out


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

    day = date.fromisoformat(a.date) if a.date else datetime.now(KST).date()
    now = datetime.combine(day, datetime.max.time(), KST) if a.date else datetime.now(KST)
    known = {x["username"] for x in cfg["accounts"]}
    targets = cfg["accounts"] + [c for c in load_inbox() if c["username"] not in known]

    accounts, candidates, errors, partial = [], [], [], False
    for acc in targets:
        try:
            if a.fixture_dir:
                data = json.loads((a.fixture_dir / f"{acc['username']}.json").read_text("utf-8"))
            else:
                data = fetch(acc["username"], cfg.get("media_limit", 50), user_id, token, version)
        except (RateLimited, polite.Stopped) as e:
            errors.append({"username": acc["username"], "error": f"한도·차단으로 중단: {e}"[:300]})
            print(f"⛔ 호출 한도 — 남은 계정은 다음 실행으로 넘깁니다: {e}")
            partial = True
            break
        except Exception as e:
            errors.append({"username": acc["username"], "error": str(e)[:300]})
            print(f"✖ @{acc['username']}: {e}")
            continue
        r = analyze(acc, data, cfg, now)
        r["followers_growth"] = followers_growth(acc["username"], r["followers"], day)
        if acc.get("candidate"):
            r["verdict"] = verdict(r, cfg)
            r["honey"] = r["verdict"] == "확정" and (r["followers"] or 0) <= 10_000  # 작지만 잘 되는 계정
            if r["verdict"] != "확정":
                r["hot"] = []
            candidates.append(r)
            print(f"? 후보 @{acc['username']}: {r['verdict']}{' (꿀통)' if r['honey'] else ''}")
        else:
            accounts.append(r)
            print(f"✓ @{acc['username']}: {r['status']}, 최근 {r['recent_posts']}개, 중앙 좋아요 {r['median_likes']}"
                  f"·댓글 {r['median_comments']}, 터진 글 {len(r['hot'])}개")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{day.isoformat()}.json"
    out.write_text(json.dumps({"date": day.isoformat(), "partial": partial, "accounts": accounts + [
        c for c in candidates if c["verdict"] == "확정"], "candidates": candidates, "errors": errors},
        ensure_ascii=False, indent=1) + "\n", "utf-8")
    hot = sum(len(x["hot"]) for x in accounts + candidates)
    print(f"→ {out.name}: 계정 {len(accounts)}개, 후보 {len(candidates)}개, 터진 글 {hot}개, 실패 {len(errors)}개"
          + (" (중간 중단)" if partial else ""))
    return 0 if accounts or candidates or not errors else 1


if __name__ == "__main__":
    sys.exit(main())
