#!/usr/bin/env python3
"""수집 결과 텔레그램 알림 — "떡상은 즉시, 나머지는 주 1회".

- 매일: 최근 3일 안에 올라온 글 중 계정 평소의 alert_multiple 배(기본 5배) 이상이 나오면 바로 알린다.
  수집 실패·평소보다 크게 줄어든 피드도 함께 알린다.
- 월요일: 지난 7일 터진 글 상위 10개, 후보 판정, 휴면 계정을 한 번에 정리해 보낸다.

  TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 cardnews/collect/notify.py [--date YYYY-MM-DD] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "sources"
KST = timezone(timedelta(hours=9))


def load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8")) if path.exists() else {}


def strength(h: dict) -> float:
    return max(h.get("x_median") or 0, h.get("x_comments") or 0, h.get("x_views") or 0)


def line(acc: str, h: dict) -> str:
    first = (h.get("caption") or "").strip().split("\n", 1)[0][:40]
    return f"· @{acc} ×{strength(h)} ({h.get('like_count')}❤ {h.get('comments_count')}💬) {first}\n  {h.get('permalink')}"


def daily(day: date, cfg: dict) -> str:
    bench, src = load(SRC / "benchmark" / f"{day}.json"), load(SRC / f"{day}.json")
    alert = cfg.get("alert_multiple", 5.0)
    hits = [(a["username"], h) for a in bench.get("accounts", []) for h in a.get("hot", [])
            if strength(h) >= alert and h.get("age_days", 99) <= 3]
    parts = []
    if hits:
        parts.append(f"🔥 떡상 {len(hits)}건 (평소의 {alert:g}배 이상, 3일 이내)")
        parts += [line(u, h) for u, h in sorted(hits, key=lambda x: -strength(x[1]))[:8]]
    problems = [f"· 피드 {e['feed']}: {e['error'][:80]}" for e in src.get("errors", [])]
    problems += [f"· 피드 {h['feed']}: 오늘 {h['today']}건 (7일 평균 {h['avg7']})" for h in src.get("health", [])]
    problems += [f"· @{e['username']}: {e['error'][:80]}" for e in bench.get("errors", [])]
    if bench.get("partial"):
        problems.append("· 인스타 벤치마킹이 호출 한도로 중간에 멈췄습니다")
    if problems:
        parts.append("⚠️ 수집 점검\n" + "\n".join(problems[:10]))
    return "\n".join(parts)


def weekly(day: date) -> str:
    hot, cands, dormant = {}, {}, set()
    for i in range(7):
        b = load(SRC / "benchmark" / f"{day - timedelta(days=i)}.json")
        for a in b.get("accounts", []):
            if a.get("status") == "휴면" and i == 0:
                dormant.add(a["username"])
            for h in a.get("hot", []):
                hot.setdefault(h["permalink"], (a["username"], h))
        for c in b.get("candidates", []):
            cands.setdefault(c["username"], c)
    top = sorted(hot.values(), key=lambda x: -strength(x[1]))[:10]
    parts = [f"📊 주간 벤치마킹 ({day - timedelta(days=6)} ~ {day})", f"터진 글 {len(hot)}건 — 상위 {len(top)}개"]
    parts += [line(u, h) for u, h in top]
    if cands:
        parts.append("후보 판정: " + ", ".join(
            f"@{u} {c['verdict']}{'(꿀통)' if c.get('honey') else ''}" for u, c in cands.items()))
    if dormant:
        parts.append("휴면(14일 이상 게시 없음): " + ", ".join(f"@{u}" for u in sorted(dormant)))
    return "\n".join(parts)


def send(text: str) -> None:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("텔레그램 설정이 없어 보내지 않았습니다.")
        return
    data = urllib.parse.urlencode({"chat_id": chat, "text": text[:4000], "disable_web_page_preview": "true"}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=20).read()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    day = date.fromisoformat(a.date) if a.date else datetime.now(KST).date()
    cfg = load(HERE / "ig_accounts.json")
    msgs = [m for m in (daily(day, cfg), weekly(day) if day.weekday() == 0 else "") if m]
    for m in msgs:
        print(m, "\n---")
        if not a.dry_run:
            send(m)
    if not msgs:
        print("알릴 것 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
