#!/usr/bin/env python3
"""카드뉴스 도구 자체 점검: 검수 규칙과 렌더 결과(1080×1350 JPEG)를 확인한다.

  python3 cardnews/selftest.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import lint  # noqa: E402
import render  # noqa: E402

ok = True


def check(cond: bool, msg: str) -> None:
    global ok
    print(("  ✓ " if cond else "  ✖ ") + msg)
    ok &= cond


def levels(spec: dict, **kw) -> set[str]:
    return {f"{p.level}:{p.where}" for p in lint.check_spec(spec, **kw)}


def main() -> int:
    base = json.loads((ROOT / "specs" / "sample-gg-birth.json").read_text("utf-8"))

    print("검수 규칙")
    check(not any(l.startswith("error") for l in levels(base)), "예시 스펙은 error 없음")
    bad = {**base, "facts": ["300만 원"]}
    check("error:사실" in levels(bad), "캡션에 없는 사실은 error")
    bad = {**base, "caption": base["caption"] + " 충격"}
    check("warn:과장" in levels(bad), "과장어는 warn")
    bad = {**base, "image": {"path": "x.jpg", "source": "original_post"}}
    check("error:표지" in levels(bad), "원본 게시물 사진은 error")
    bad = {**base, "image": {"path": "x.jpg", "source": "pexels"}}
    check("error:표지" in levels(bad), "출처 없는 무료 사진은 error")
    bad = {**base, "caption": "가" * 2300}
    check("error:캡션" in levels(bad), "2,200자 초과 캡션은 error")
    bad = {**base, "template": "info", "slides": [{"heading": "x"}] * 20}
    check("error:구성" in levels(bad), "21장은 error")

    print("렌더")
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        tmp = Path(tmp)
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 900})
        # 테스트용 사진(1200×900)을 만든다
        page.set_content("<body style='margin:0;width:1200px;height:900px;"
                         "background:linear-gradient(45deg,#2a9d8f,#e9c46a,#e76f51)'></body>")
        photo = tmp / "photo.jpg"
        page.screenshot(path=str(photo), type="jpeg")
        page.set_viewport_size({"width": lint.W, "height": lint.H})

        spec = {**base, "id": "selftest-photo", "image": {"path": str(photo), "source": "ai", "tool": "test"}}
        sp = tmp / "spec.json"
        sp.write_text(json.dumps(spec, ensure_ascii=False), "utf-8")
        out = tmp / "out"
        check(render.render(sp, out, page, force=False), "사진 표지 렌더 통과")
        d = next(out.glob("*/selftest-photo"))
        check(render.jpeg_size(d / "cover.jpg") == (1080, 1350), "cover.jpg 1080×1350")
        meta = json.loads((d / "meta.json").read_text("utf-8"))
        check(meta["status"] == "ready", "meta.json status=ready")
        check("AI 생성 이미지" in (d / "credit.txt").read_text("utf-8"), "credit.txt 에 AI 표기")

        long = {**base, "id": "selftest-long", "title": "가나다라마바사아자차카타파하" * 3 + "\n짧은 줄"}
        sp.write_text(json.dumps(long, ensure_ascii=False), "utf-8")
        check(not render.render(sp, out, page, force=True), "너무 긴 제목은 넘침 error")

        info = json.loads((ROOT / "specs" / "sample-sn-rent.json").read_text("utf-8"))
        sp.write_text(json.dumps(info, ensure_ascii=False), "utf-8")
        check(render.render(sp, out, page, force=False), "정보형 캐러셀 렌더 통과")
        d = next(out.glob("*/sample-sn-rent"))
        files = sorted(p.name for p in d.glob("*.jpg"))
        check(files == ["cover.jpg", "slide-02.jpg", "slide-03.jpg", "slide-04.jpg", "slide-05.jpg"], f"5장 생성 {files}")
        check(all(render.jpeg_size(d / f) == (1080, 1350) for f in files), "모든 장 1080×1350")
        browser.close()

    print("\n결과:", "통과" if ok else "실패")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
