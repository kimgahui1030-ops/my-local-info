"""카드뉴스 검수 게이트.

스펙 단계(렌더 전)와 레이아웃 단계(렌더 후) 두 번 검사한다.
error 는 발행 전에 반드시 고쳐야 하는 것, warn 은 사람이 보고 판단할 것.
규칙의 근거는 docs/instagram-cardnews-plan.md 3-3·3-6 절.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

W, H = 1080, 1350
SAFE_Y = 135  # 1:1 크롭 안전선(위아래)
SAFE_X = 54   # 좌우 5% — 프로필 그리드 세로(3:4) 크롭에도 안전

HL = re.compile(r"\[\[(.+?)\]\]")
HASHTAG = re.compile(r"#[^\s#]+")

# 사실이 아닌데 붙이면 신뢰를 깎는 과장어. facts 에 들어 있으면 허용.
EXAGGERATION = ["참사", "대참사", "충격", "경악", "소름", "역대급", "발칵", "난리", "폭망", "미쳤다", "초토화"]

TEMPLATES = {"magazine", "info"}
IMAGE_SOURCES = {"pixabay", "pexels", "own", "ai", "licensed"}


@dataclass
class Problem:
    level: str  # "error" | "warn"
    where: str
    msg: str

    def __str__(self) -> str:
        mark = "✖" if self.level == "error" else "△"
        return f"{mark} [{self.where}] {self.msg}"


def plain(text: str) -> str:
    return HL.sub(r"\1", text)


def _images(spec: dict):
    if spec.get("image"):
        yield "표지", spec["image"]
    for i, s in enumerate(spec.get("slides", []), start=2):
        if s.get("image"):
            yield f"{i}장", s["image"]


def check_spec(spec: dict, spec_dir: Path | None = None, out_root: Path | None = None,
               today: date | None = None) -> list[Problem]:
    p: list[Problem] = []
    add = lambda level, where, msg: p.append(Problem(level, where, msg))

    sid = spec.get("id", "")
    if not re.fullmatch(r"[\w-]+", sid):
        add("error", "id", "id 는 글자·숫자·-·_ 만 쓸 수 있습니다")
    if spec.get("template") not in TEMPLATES:
        add("error", "template", f"template 은 {sorted(TEMPLATES)} 중 하나여야 합니다")

    # 제목: 2줄, 줄당 13~16자, 강조 [[ ]] 1곳
    title = spec.get("title", "")
    if not title.strip():
        add("error", "제목", "제목이 비어 있습니다")
    if title.count("[[") != title.count("]]"):
        add("error", "제목", "[[ ]] 괄호 짝이 맞지 않습니다")
    lines = [l for l in title.split("\n") if l.strip()]
    if len(lines) > 3:
        add("error", "제목", f"{len(lines)}줄 — 표지 제목은 최대 3줄입니다")
    elif len(lines) != 2:
        add("warn", "제목", f"{len(lines)}줄 — 2줄을 권장합니다")
    for i, line in enumerate(lines, 1):
        n = len(plain(line))
        if not 13 <= n <= 16:
            add("warn", "제목", f"{i}번째 줄 {n}자 — 줄당 13~16자를 권장합니다")
    hl = len(HL.findall(title))
    if hl != 1:
        add("warn", "제목", f"강조 [[ ]] {hl}곳 — 1곳을 권장합니다")

    # 캡션
    caption = spec.get("caption", "")
    tags = HASHTAG.findall(caption) + [t if t.startswith("#") else f"#{t}" for t in spec.get("hashtags", [])]
    full_len = len(caption) + sum(len(t) + 1 for t in spec.get("hashtags", []))
    if not caption.strip():
        add("error", "캡션", "캡션이 비어 있습니다")
    if full_len > 2200:
        add("error", "캡션", f"{full_len}자 — 인스타그램 캡션 상한 2,200자를 넘습니다")
    if len(tags) > 30:
        add("error", "캡션", f"해시태그 {len(tags)}개 — 상한 30개를 넘습니다")
    style = spec.get("caption_style", "K")
    if style == "K":
        if not 600 <= len(caption) <= 700:
            add("warn", "캡션", f"{len(caption)}자 — 국내 기사체(K)는 600~700자를 권장합니다")
        if not caption.lstrip().startswith("["):
            add("warn", "캡션", "K 캡션은 첫 줄을 [제목] 으로 시작합니다")
        if tags:
            add("warn", "캡션", "K 캡션은 해시태그 없이 쓰는 것이 벤치마크 형식입니다")
    elif style == "G":
        first = caption.strip().split("\n", 1)[0]
        if not first.rstrip().endswith("?"):
            add("warn", "캡션", "G 캡션은 첫 줄을 질문으로 시작합니다")

    # 사실 고정: 숫자·고유명사는 원문 그대로
    facts = spec.get("facts", [])
    body = plain(title) + "\n" + caption
    for f in facts:
        if f not in body:
            add("error", "사실", f"'{f}' 이(가) 제목·캡션에 없습니다 — 원문 숫자·고유명사를 바꾸지 마세요")
    for word in EXAGGERATION:
        if word in body and not any(word in f for f in facts):
            add("warn", "과장", f"'{word}' — 원문에 없는 과장어인지 확인하세요")

    # 장수
    slides = spec.get("slides", [])
    total = 1 + len(slides)
    if total > 20:
        add("error", "구성", f"{total}장 — 인스타그램 상한 20장을 넘습니다")
    elif total > 10:
        add("warn", "구성", f"{total}장 — 공식 API·예약 도구는 10장까지만 받습니다")
    if spec.get("template") == "magazine" and slides:
        add("warn", "구성", "magazine 은 표지 1장용입니다 — 여러 장이면 info 를 쓰세요")
    for i, s in enumerate(slides, start=2):
        if s.get("role", "body") not in {"body", "cta"}:
            add("error", f"{i}장", "role 은 body 또는 cta 입니다")
        if not (s.get("heading") or "").strip():
            add("error", f"{i}장", "heading 이 비어 있습니다")

    # 이미지: 출처 기록 필수, 원본 게시물 사진 금지
    for where, img in _images(spec):
        if img.get("query") and not img.get("path"):
            add("warn", where, f"사진은 렌더 단계에서 '{img['query']}' 로 검색해 붙입니다(키가 없으면 색 배경)")
            continue
        src = img.get("source")
        if src == "original_post":
            add("error", where, "원본 게시물 사진은 쓰지 않습니다(저작권·오리지널 정책)")
        elif src not in IMAGE_SOURCES:
            add("error", where, f"image.source 는 {sorted(IMAGE_SOURCES)} 중 하나여야 합니다")
        if src in {"pixabay", "pexels", "licensed"} and not img.get("credit"):
            add("error", where, "이미지 출처(credit)를 적어 주세요")
        path = img.get("path")
        if path:
            fp = Path(path)
            if not fp.is_absolute() and spec_dir:
                fp = spec_dir / fp
            if not fp.exists():
                add("error", where, f"이미지 파일이 없습니다: {path}")
        else:
            add("error", where, "image.path 가 없습니다")

    # 같은 소재 7일 안 중복
    url = (spec.get("source") or {}).get("url")
    if url and out_root and out_root.exists():
        today = today or date.today()
        for meta in out_root.glob("*/*/meta.json"):
            try:
                m = json.loads(meta.read_text("utf-8"))
                d = date.fromisoformat(meta.parent.parent.name)
            except (ValueError, OSError):
                continue
            if m.get("id") != sid and (m.get("source") or {}).get("url") == url \
                    and today - d <= timedelta(days=7):
                add("warn", "중복", f"7일 안에 같은 소재를 썼습니다: {m.get('id')} ({d})")
    return p


def check_layout(boxes: list[dict], slide_no: int) -> list[Problem]:
    """렌더 후 글자 상자 검사. 표지는 크롭 안전선까지 본다."""
    p: list[Problem] = []
    where = "표지" if slide_no == 1 else f"{slide_no}장"
    for b in boxes:
        if b["overflow"]:
            p.append(Problem("error", where, f"{b['name']} 글자가 칸을 넘칩니다 — 문구를 줄이세요"))
        if slide_no == 1 and b["name"] in {"title", "label"}:
            if b["top"] < SAFE_Y or b["bottom"] > H - SAFE_Y or b["left"] < SAFE_X or b["right"] > W - SAFE_X:
                p.append(Problem("error", where, f"{b['name']} 이(가) 크롭 안전선 밖으로 나갑니다"))
    return p
