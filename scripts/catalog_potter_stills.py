#!/usr/bin/env python3
"""Build a source catalog from Harry Potter Fan Zone's eight film still galleries."""
import json
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = []
    seen = set()
    for film in range(1, 9):
        page_url = f"https://www.harrypotterfanzone.com/harry-potter-movie-stills/movie-{film}/"
        cached = Path(f"/private/tmp/hpfz-movie{film}.html")
        if cached.exists():
            html = cached.read_text(encoding="utf-8")
        else:
            request = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                html = response.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.select('a[href*="/pictures/"]'):
            image = link.find("img")
            if not image:
                continue
            url = image.get("src", "")
            if not url.startswith("https://media.harrypotterfanzone.com/") or url in seen:
                continue
            seen.add(url)
            catalog.append({
                "film": film,
                "caption": image.get("alt", "").strip(),
                "imageUrl": url,
                "pageUrl": link.get("href", page_url),
                "galleryUrl": page_url,
            })
    out = ROOT / "data/potter-image-catalog.json"
    out.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Cataloged {len(catalog)} unique film stills")


if __name__ == "__main__":
    main()
