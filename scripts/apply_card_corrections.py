#!/usr/bin/env python3
"""Apply reviewed vocabulary and scene corrections without changing card IDs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "dist/cards.json"
CORRECTIONS = ROOT / "data/card-corrections.json"
IMAGE_FIELDS = ("image", "imageType", "imageSource", "imageCaption", "imageFilm", "imageTimeSeconds")


def main():
    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    corrections = json.loads(CORRECTIONS.read_text(encoding="utf-8"))
    by_id = {card["id"]: card for card in cards}
    unknown = set(corrections) - set(by_id)
    if unknown:
        raise SystemExit(f"Unknown cards: {sorted(unknown)}")
    for card_id, change in corrections.items():
        card = by_id[card_id]
        if "imageFrom" in change:
            source = by_id[change["imageFrom"]]
            if source["deck"] != card["deck"]:
                raise SystemExit(f"Cross-deck image: {card_id}")
            for field in IMAGE_FIELDS:
                if field in source:
                    card[field] = source[field]
                else:
                    card.pop(field, None)
            card["imageVerifiedForWord"] = False
        for field in ("pos", "ru", "imageContext"):
            if field in change:
                card[field] = change[field]
    CARDS.write_text(json.dumps(cards, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Applied {len(corrections)} corrections to {len(cards)} cards")


if __name__ == "__main__":
    main()
