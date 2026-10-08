#!/usr/bin/env python3
"""Download public The Gentlemen gallery backdrops for local card art review."""
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://mooveedb.com"
DEST = ROOT / "data/gentlemen-stills"
DEST.mkdir(parents=True, exist_ok=True)


def get(url):
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json,image/*"}), timeout=35) as response:
        return response.read()


def main():
    entries = []
    for offset in range(0, 63, 8):
        query = urlencode({"media_type": "tv", "media_id": 10, "group": "backdrops", "title": "The Gentlemen", "offset": offset, "limit": 8})
        payload = json.loads(get(BASE + "/api/media-images?" + query))
        for relative in re.findall(r'data-full-url="([^"]+)"', payload["html"]):
            url = urljoin(BASE, relative)
            if any(x["url"] == url for x in entries):
                continue
            index = len(entries) + 1
            path = DEST / f"still-{index:03d}.jpg"
            path.write_bytes(get(url))
            entries.append({"index": index, "path": str(path.relative_to(ROOT)), "url": url, "gallery": "https://mooveedb.com/tv/2024/the-gentlemen-236235"})
            print(index, path.name, flush=True)
    (DEST / "sources.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Downloaded {len(entries)} stills")


if __name__ == "__main__":
    main()
