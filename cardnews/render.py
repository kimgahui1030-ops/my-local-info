#!/usr/bin/env python3
"""카드뉴스 렌더러: 스펙 JSON → 검수 → 1080×1350 JPEG + 캡션 묶음.

사용:
  python3 cardnews/render.py cardnews/specs/예시.json [다른 스펙 ...]
  python3 cardnews/render.py 스펙.json --check     # 검수만
  python3 cardnews/render.py 스펙.json --force     # 검수 error 가 있어도 렌더(미리보기용)

결과: cardnews/out/<날짜>/<id>/
  cover.jpg, slide-02.jpg …   발행할 이미지(순서대로)
  caption.txt                 그대로 붙여넣을 캡션
  credit.txt                  이미지 출처
  meta.json                   스펙 + 검수 결과 + 발행 상태
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

import lint

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
W, H = lint.W, lint.H

env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))


def mark(text: str) -> Markup:
    """[[강조]] → 노란 글자. 나머지는 이스케이프."""
    return Markup(lint.HL.sub(r'<em class="hl">\1</em>', html.escape(text)))


def load_brand(name: str) -> dict:
    brands = json.loads((ROOT / "brands.json").read_text("utf-8"))
    if name not in brands:
        raise SystemExit(f"brands.json 에 '{name}' 계정이 없습니다. 있는 계정: {', '.join(brands)}")
    b = dict(brands[name])
    b.setdefault("label", b["handle"])
    return b


def image_ctx(img: dict | None, spec_dir: Path) -> dict:
    if not img:
        return {"photo": None, "focus": "center", "ai_label": False}
    fp = Path(img["path"])
    if not fp.is_absolute():
        fp = (spec_dir / fp).resolve()
    return {"photo": fp.as_uri(), "focus": img.get("focus", "center"), "ai_label": img.get("source") == "ai"}


def build_slides(spec: dict, brand: dict, spec_dir: Path) -> list[tuple[str, dict]]:
    slides = spec.get("slides", [])
    total = 1 + len(slides)
    base = {"brand": brand, "fonts": (ROOT / "fonts").as_uri(), "total": total}
    out = [("magazine.html", {
        **base, **image_ctx(spec.get("image"), spec_dir),
        "title_lines": [mark(l) for l in spec["title"].split("\n") if l.strip()],
        "swipe": total > 1,
    })]
    no = 0
    for page, s in enumerate(slides, start=2):
        ctx = {**base, "page": page, "heading": s["heading"], "text": s.get("body", "")}
        if s.get("role", "body") == "cta":
            out.append(("info_cta.html", ctx))
        else:
            no += 1
            out.append(("info_body.html", {**ctx, **image_ctx(s.get("image"), spec_dir),
                                           "no": no, "emphasis": s.get("emphasis", "")}))
    return out


def jpeg_size(path: Path) -> tuple[int, int]:
    """JPEG 헤더에서 (가로, 세로)를 읽는다(외부 라이브러리 없이)."""
    data = path.read_bytes()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    raise ValueError(f"JPEG 크기를 읽지 못했습니다: {path}")


def credit_lines(spec: dict) -> list[str]:
    lines = []
    for where, img in lint._images(spec):
        src = img.get("source")
        if src == "ai":
            lines.append(f"{where}: AI 생성 이미지 ({img.get('tool', '도구 미기재')}) — 이미지에 표기함")
        elif src == "own":
            lines.append(f"{where}: 직접 촬영·보유 사진")
        else:
            lines.append(f"{where}: {img.get('credit', '')} {img.get('url', '')}".rstrip())
    return lines


def caption_text(spec: dict) -> str:
    tags = " ".join(t if t.startswith("#") else f"#{t}" for t in spec.get("hashtags", []))
    return spec["caption"].rstrip() + (f"\n\n{tags}" if tags else "") + "\n"


def render(spec_path: Path, out_root: Path, page, force: bool) -> bool:
    spec = json.loads(spec_path.read_text("utf-8"))
    spec_dir = spec_path.parent
    print(f"\n■ {spec_path.name}  ({spec.get('id')})")
    problems = lint.check_spec(spec, spec_dir, out_root)
    for p in problems:
        print("  ", p)
    if any(p.level == "error" for p in problems) and not force:
        print("  → 검수 error 가 있어 렌더하지 않았습니다. 고친 뒤 다시 실행하세요.")
        return False

    brand = load_brand(spec.get("brand", "sample"))
    day = spec.get("date") or date.today().isoformat()
    out = out_root / day / spec["id"]
    (out / "_html").mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()

    files, layout = [], []
    for i, (tpl, ctx) in enumerate(build_slides(spec, brand, spec_dir), start=1):
        html_path = out / "_html" / f"slide-{i:02d}.html"
        html_path.write_text(env.get_template(tpl).render(**ctx), "utf-8")
        page.goto(html_path.as_uri())
        page.evaluate("document.fonts.ready")
        boxes = page.evaluate("window.__fit()")
        layout += lint.check_layout(boxes, i)
        name = "cover.jpg" if i == 1 else f"slide-{i:02d}.jpg"
        page.screenshot(path=str(out / name), type="jpeg", quality=92)
        if jpeg_size(out / name) != (W, H):
            layout.append(lint.Problem("error", name, f"크기가 {jpeg_size(out / name)} 입니다"))
        files.append(name)
    for p in layout:
        print("  ", p)
    problems += layout

    (out / "caption.txt").write_text(caption_text(spec), "utf-8")
    (out / "credit.txt").write_text("\n".join(credit_lines(spec)) + "\n", "utf-8")
    errors = [str(p) for p in problems if p.level == "error"]
    meta = {
        **spec,
        "files": files,
        "rendered_at": datetime.now().isoformat(timespec="seconds"),
        "review": {"errors": errors, "warnings": [str(p) for p in problems if p.level == "warn"]},
        "status": "needs_fix" if errors else "ready",
        "published": spec.get("published"),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
    state = "수정 필요" if errors else "발행 준비 완료"
    print(f"  → {state}: {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out}  ({len(files)}장)")
    return not errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="카드뉴스 스펙을 검수하고 1080×1350 JPEG로 렌더합니다.")
    ap.add_argument("specs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true", help="검수만 하고 렌더하지 않음")
    ap.add_argument("--force", action="store_true", help="검수 error 가 있어도 렌더")
    a = ap.parse_args(argv)

    if a.check:
        bad = 0
        for sp in a.specs:
            spec = json.loads(sp.read_text("utf-8"))
            problems = lint.check_spec(spec, sp.parent, a.out)
            print(f"\n■ {sp.name}")
            for p in problems:
                print("  ", p)
            bad += any(p.level == "error" for p in problems)
        return 1 if bad else 0

    from playwright.sync_api import sync_playwright
    ok = True
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for sp in a.specs:
            ok &= render(sp.resolve(), a.out, page, a.force)
        browser.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
