#!/usr/bin/env python3
"""Attach downloaded Harry Potter film stills to the 500 Potter cards."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "dist/cards.json"
ASSETS = ROOT / "dist/assets/potter-cards"


def main():
    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    sources = json.loads((ROOT / "data/potter-image-sources.json").read_text(encoding="utf-8"))
    potter = [card for card in cards if card["deck"] == "potter"]
    if len(potter) != 500 or len(sources) != 500:
        raise SystemExit(f"Expected 500 Potter cards and sources, found {len(potter)} and {len(sources)}")
    missing = [card["word"] for card in potter if not (ASSETS / f'{card["word"]}.jpg').is_file()]
    if missing:
        raise SystemExit(f"Missing {len(missing)} Potter images: {', '.join(missing[:30])}")
    for card in potter:
        word = card["word"]
        source = sources[word]
        card["image"] = f"assets/potter-cards/{word}.jpg"
        card["imageType"] = "film-still"
        card["imageSource"] = source["pageUrl"]
        card["imageCaption"] = source["caption"]
        card["imageFilm"] = source["film"]
        card["imageVerifiedForWord"] = False
    CARDS.write_text(json.dumps(cards, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Attached {len(potter)} film stills to Potter cards")


if __name__ == "__main__":
    main()
