#!/usr/bin/env python3
"""카드뉴스 소재 수집기 — GitHub Actions 에서 매일 돌린다.

feeds.json 의 RSS/Atom 과 저장소의 public/data/local-info.json 을 읽어
cardnews/sources/<날짜>.json 하나로 모은다. 최근 keep_days 일 안에 이미 모은
링크는 다시 넣지 않는다. 외부 라이브러리 없이 표준 라이브러리만 쓴다.

  python3 cardnews/collect/collect_sources.py            # 오늘(KST)
  python3 cardnews/collect/collect_sources.py --fixture f.xml   # 네트워크 없이 시험
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import polite  # noqa: E402

HERE = Path(__file__).resolve().parent
CARDNEWS = HERE.parent
REPO = CARDNEWS.parent
OUT = CARDNEWS / "sources"
KST = timezone(timedelta(hours=9))
ATOM = "{http://www.w3.org/2005/Atom}"


def clean(text: str | None, limit: int = 600) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def item_id(link: str) -> str:
    return hashlib.sha1(link.encode("utf-8")).hexdigest()[:12]


def to_iso(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return parsedate_to_datetime(raw).astimezone(KST).isoformat(timespec="minutes")
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(KST).isoformat(timespec="minutes")
    except ValueError:
        return raw


def parse_feed(xml_bytes: bytes, feed: dict, limit: int) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter("item"):  # RSS 2.0
        link = (it.findtext("link") or "").strip()
        items.append({"title": it.findtext("title"), "link": link,
                      "summary": it.findtext("description"), "published": it.findtext("pubDate"),
                      "origin": it.findtext("source")})
    for it in root.iter(f"{ATOM}entry"):  # Atom
        link_el = it.find(f"{ATOM}link")
        link = (link_el.get("href") if link_el is not None else "") or ""
        items.append({"title": it.findtext(f"{ATOM}title"), "link": link,
                      "summary": it.findtext(f"{ATOM}summary") or it.findtext(f"{ATOM}content"),
                      "published": it.findtext(f"{ATOM}published") or it.findtext(f"{ATOM}updated"),
                      "origin": None})
    out = []
    for it in items[:limit]:
        if not it["link"] or not it["title"]:
            continue
        out.append({
            "id": item_id(it["link"]),
            "title": clean(it["title"], 200),
            "summary": clean(it["summary"]),
            "link": it["link"],
            "published": to_iso(it["published"]),
            "source": clean(it["origin"], 80) or feed["name"],
            "feed": feed["name"],
            "direction": feed["direction"],
            "lang": feed.get("lang", "ko"),
        })
    return out


def fetch(url: str) -> bytes:
    return polite.get(url)


def local_info(today: date) -> list[dict]:
    """저장소의 지역 행사·혜택 데이터 중 아직 끝나지 않은 것."""
    path = REPO / "public" / "data" / "local-info.json"
    if not path.exists():
        return []
    out = []
    for x in json.loads(path.read_text("utf-8")):
        if x.get("endDate", "9999") < today.isoformat():
            continue
        link = x.get("link") if x.get("link") not in (None, "", "#") else f"local-info:{x['id']}"
        out.append({
            "id": item_id(link), "title": x["title"],
            "summary": clean(f"{x.get('summary', '')} 대상: {x.get('target', '')} 장소: {x.get('location', '')} "
                             f"기간: {x.get('startDate', '')}~{x.get('endDate', '')}"),
            "link": link, "published": "", "source": "local-info.json", "feed": "local-info",
            "direction": "life", "lang": "ko",
        })
    return out


def benchmark_items(today: date, recent_days: int = 21) -> list[dict]:
    """ig_benchmark.py 가 오늘 만든 결과에서 최근 터진 글만 소재로 가져온다(주제·구조 참고용)."""
    path = OUT / "benchmark" / f"{today.isoformat()}.json"
    if not path.exists():
        return []
    cutoff = datetime.combine(today - timedelta(days=recent_days), datetime.min.time(), KST)
    out = []
    for acc in json.loads(path.read_text("utf-8")).get("accounts", []):
        for m in acc.get("hot", []):
            try:
                ts = datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00"))
            except (KeyError, ValueError):
                continue
            if ts < cutoff:
                continue
            caption = m.get("caption") or ""
            out.append({
                "id": item_id(m["permalink"]),
                "title": clean(caption.split("\n", 1)[0], 200) or f"@{acc['username']} 게시물",
                "summary": clean(caption),
                "link": m["permalink"], "published": ts.astimezone(KST).isoformat(timespec="minutes"),
                "source": f"@{acc['username']}", "feed": "instagram-benchmark",
                "direction": acc["direction"], "lang": "en" if acc["username"] == "realkhalilu" else "ko",
                "metrics": {"likes": m.get("like_count"), "comments": m.get("comments_count"),
                            "x_median": m.get("x_median"), "x_comments": m.get("x_comments"),
                            "media_type": m.get("media_type")},
            })
    return out


def feed_health(today: date, counts: dict[str, int], days: int = 7) -> list[dict]:
    """조용한 실패 잡기: 평소엔 들어오던 피드가 0건이거나 평소의 1/3 아래면 표시한다."""
    hist: dict[str, list[int]] = {}
    for f in OUT.glob("*.json"):
        try:
            d = date.fromisoformat(f.stem)
        except ValueError:
            continue
        if d < today and today - d <= timedelta(days=days):
            for name, n in json.loads(f.read_text("utf-8")).get("feed_counts", {}).items():
                hist.setdefault(name, []).append(n)
    out = []
    for name, n in counts.items():
        past = hist.get(name)
        if not past:
            continue
        avg = sum(past) / len(past)
        if avg >= 3 and n < avg / 3:
            out.append({"feed": name, "today": n, "avg7": round(avg, 1), "note": "평소보다 크게 줄었습니다"})
    return out


def seen_links(today: date, keep_days: int) -> set[str]:
    seen = set()
    for f in OUT.glob("*.json"):
        try:
            d = date.fromisoformat(f.stem)
        except ValueError:
            continue
        if d < today and today - d <= timedelta(days=keep_days):
            seen |= {x["link"] for x in json.loads(f.read_text("utf-8")).get("items", [])}
    return seen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (기본: 오늘 KST)")
    ap.add_argument("--fixture", type=Path, help="네트워크 대신 이 XML 파일을 모든 피드로 사용(시험용)")
    a = ap.parse_args(argv)

    cfg = json.loads((HERE / "feeds.json").read_text("utf-8"))
    today = date.fromisoformat(a.date) if a.date else datetime.now(KST).date()
    seen = seen_links(today, cfg.get("keep_days", 14))

    items, errors, counts = [], [], {}
    for feed in cfg["feeds"]:
        try:
            raw = a.fixture.read_bytes() if a.fixture else fetch(feed["url"])
            got = parse_feed(raw, feed, cfg.get("per_feed_limit", 30))
            items += got
            counts[feed["name"]] = len(got)
            print(f"✓ {feed['name']}: {len(got)}건")
        except Exception as e:  # 피드 하나가 막혀도 나머지는 계속
            errors.append({"feed": feed["name"], "error": f"{type(e).__name__}: {e}"[:200]})
            print(f"✖ {feed['name']}: {type(e).__name__}: {e}")
    items += local_info(today)
    bench = benchmark_items(today)
    if bench:
        print(f"✓ 인스타 벤치마킹 터진 글: {len(bench)}건")
    items += bench

    uniq, dup = {}, 0
    for x in items:
        if x["link"] in seen or x["id"] in uniq:
            dup += 1
            continue
        uniq[x["id"]] = x

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{today.isoformat()}.json"
    data = {"date": today.isoformat(), "collected_at": datetime.now(KST).isoformat(timespec="seconds"),
            "count": len(uniq), "feed_counts": counts, "health": feed_health(today, counts),
            "items": list(uniq.values()), "errors": errors}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"→ {out.relative_to(REPO)}: 새 소재 {len(uniq)}건 (중복 제외 {dup}, 실패 피드 {len(errors)})")
    return 0 if uniq or not errors else 1


if __name__ == "__main__":
    sys.exit(main())
