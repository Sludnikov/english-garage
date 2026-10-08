"""Check card identity, local images and the files required by the PWA."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REQUIRED = (
    "index.html",
    "app.js",
    "styles.css",
    "cards.json",
    "sw.js",
    "progress-worker.js",
    "manifest.webmanifest",
    "vendor/ts-fsrs.umd.js",
)


def main():
    missing = [name for name in REQUIRED if not (DIST / name).is_file()]
    cards = json.loads((DIST / "cards.json").read_text(encoding="utf-8"))
    ids = [card["id"] for card in cards]
    duplicates = [name for name, count in Counter(ids).items() if count > 1]
    missing_images = [card["id"] for card in cards if not (DIST / card["image"]).is_file()]
    counts = dict(Counter(card["deck"] for card in cards))
    print(f"Cards: {len(cards)}; decks: {counts}")
    print(f"Missing core files: {len(missing)}; duplicate IDs: {len(duplicates)}; missing images: {len(missing_images)}")
    if missing:
        print("Missing core files:", missing[:20])
    if duplicates:
        print("Duplicate IDs:", duplicates[:20])
    if missing_images:
        print("Missing images:", missing_images[:20])
    if missing or duplicates or missing_images:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
