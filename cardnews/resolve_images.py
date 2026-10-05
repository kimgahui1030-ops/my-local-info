#!/usr/bin/env python3
"""스펙의 image.query(영어 검색어)로 Pexels 사진을 찾아 붙인다 — GitHub Actions 렌더 단계에서 실행.

  PEXELS_API_KEY=... python3 cardnews/resolve_images.py 스펙.json [...]

- path 가 이미 있는 이미지는 건드리지 않는다.
- 키가 없거나 결과가 없으면 image 를 지우고 브랜드 색 배경으로 렌더되게 둔다(meta 에 이유 기록).
- 스펙 파일을 제자리에서 고친다(러너 안에서만, 커밋하지 않음).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT / "out" / "_photos"
API = "https://api.pexels.com/v1/search"


def search(query: str, key: str) -> dict | None:
    url = f"{API}?{urllib.parse.urlencode({'query': query, 'orientation': 'portrait', 'per_page': 5})}"
    req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "cardnews"})
    with urllib.request.urlopen(req, timeout=20) as r:
        photos = json.load(r).get("photos", [])
    return photos[0] if photos else None


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "cardnews"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dest.write_bytes(r.read())


def resolve(img: dict, name: str, key: str | None) -> tuple[dict | None, str]:
    if img.get("path") or not img.get("query"):
        return img, ""
    if not key:
        return None, f"PEXELS_API_KEY 없음 — '{img['query']}' 사진 대신 색 배경"
    try:
        hit = search(img["query"], key)
        if not hit:
            return None, f"'{img['query']}' 검색 결과 없음 — 색 배경"
        dest = PHOTOS / f"{name}-{hit['id']}.jpg"
        download(hit["src"].get("portrait") or hit["src"]["large2x"], dest)
        return {**img, "path": str(dest), "source": "pexels",
                "credit": f"Pexels / {hit.get('photographer', '')}", "url": hit.get("url", "")}, ""
    except Exception as e:
        return None, f"사진 검색 실패({type(e).__name__}) — 색 배경"


def main(paths: list[str]) -> int:
    key = os.environ.get("PEXELS_API_KEY") or None
    for p in map(Path, paths):
        spec = json.loads(p.read_text("utf-8"))
        notes = []
        if spec.get("image"):
            spec["image"], note = resolve(spec["image"], spec["id"], key)
            notes.append(note)
            if spec["image"] is None:
                del spec["image"]
        for i, s in enumerate(spec.get("slides", []), start=2):
            if s.get("image"):
                s["image"], note = resolve(s["image"], f"{spec['id']}-{i}", key)
                notes.append(note)
                if s["image"] is None:
                    del s["image"]
        notes = [n for n in notes if n]
        if notes:
            spec["image_notes"] = notes
        p.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(f"{p.name}: " + ("; ".join(notes) if notes else "사진 준비 완료"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
