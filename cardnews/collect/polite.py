"""예의 바른 요청 계층 — 모든 외부 요청은 이 모듈을 거친다.

이전 수집기들(polite.py·채널수집기·트렌드 뷰어)에서 검증한 규칙을 옮겼다.
- 호스트별 최소 간격 + 무작위 지터
- 호스트별 1회 실행 상한
- 429·봇 확인·로그인 요구가 나오면 그 호스트는 이번 실행에서 멈춘다(서킷 브레이커, 안내는 1번)
- 그 밖의 실패는 연속 3번이면 멈춘다. 한 건의 사정(404 등)은 연속 실패로 세지 않는다
- 프록시·다계정·캡차 풀기는 쓰지 않는다
"""
from __future__ import annotations

import random
import time
import urllib.error
import urllib.request
from collections import defaultdict
from urllib.parse import urlparse

UA = "Mozilla/5.0 (cardnews-collector; +https://github.com)"
DEFAULT = {"gap": (2.0, 5.0), "cap": 60}
HOSTS = {
    "news.google.com": {"gap": (3.0, 7.0), "cap": 20},
    "www.reddit.com": {"gap": (5.0, 10.0), "cap": 5},
    "graph.facebook.com": {"gap": (1.0, 2.5), "cap": 150},  # 시간당 200회 한도 안쪽
}
URL_STOP = ("accounts/login", "/challenge", "/login", "consent.")
BODY_STOP = ("captcha", "not a bot", "not a robot", "unusual traffic")


class Stopped(Exception):
    """이 호스트는 이번 실행에서 더 부르지 않는다."""


_last: dict[str, float] = {}
_count: dict[str, int] = defaultdict(int)
_fails: dict[str, int] = defaultdict(int)
_stopped: dict[str, str] = {}


def _rule(host: str) -> dict:
    return {**DEFAULT, **HOSTS.get(host, {})}


def stopped() -> dict[str, str]:
    return dict(_stopped)


def _stop(host: str, why: str) -> None:
    if host not in _stopped:
        _stopped[host] = why
        print(f"  ⛔ {host}: {why} — 이번 실행에서 이 호스트는 멈춥니다")
    raise Stopped(f"{host}: {why}")


def get(url: str, headers: dict | None = None, timeout: int = 25) -> bytes:
    host = urlparse(url).netloc
    if host in _stopped:
        raise Stopped(f"{host}: {_stopped[host]}")
    rule = _rule(host)
    if _count[host] >= rule["cap"]:
        _stop(host, f"1회 실행 상한 {rule['cap']}건")
    wait = random.uniform(*rule["gap"]) - (time.monotonic() - _last.get(host, 0))
    if wait > 0 and host in _last:
        time.sleep(wait)
    _last[host] = time.monotonic()
    _count[host] += 1
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            final = r.geturl()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            _stop(host, "429 요청 과다")
        if e.code in (401, 403):
            _stop(host, f"{e.code} 접근 거부")
        if e.code >= 500:
            _fail(host)
        raise  # 404 같은 한 건의 사정은 연속 실패로 세지 않는다
    except (urllib.error.URLError, TimeoutError, OSError):
        _fail(host)
        raise
    head = body[:4000].decode("utf-8", "ignore").lower()
    is_data = head.lstrip().startswith(("<?xml", "<rss", "<feed", "{", "["))  # 정상 피드·JSON 은 본문 검사 생략
    if any(w in final.lower() for w in URL_STOP) or (not is_data and any(w in head for w in BODY_STOP)):
        _stop(host, "봇 확인·로그인 요구")
    _fails[host] = 0
    return body


def _fail(host: str) -> None:
    _fails[host] += 1
    if _fails[host] >= 3:
        _stop(host, "연속 3회 실패")
