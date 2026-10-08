"""Attach the curated Dark (2017) series stills to its 500 cards."""

from pathlib import Path
import json
import shutil


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SOURCE = Path("/private/tmp/dark-candidates")


def main():
    mapping = json.loads((ROOT / "data/dark-image-sources.json").read_text(encoding="utf-8"))
    cards_path = DIST / "cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    dark_cards = [card for card in cards if card["deck"] == "dark"]
    if len(dark_cards) != len(mapping) or set(mapping) != {card["word"] for card in dark_cards}:
        raise SystemExit("Dark source mapping does not match the 500 cards")

    destination = DIST / "assets/dark-cards"
    destination.mkdir(parents=True, exist_ok=True)
    for card in dark_cards:
        source = mapping[card["word"]]
        image_file = destination / f"{card['word']}.jpg"
        shutil.copyfile(SOURCE / f"{source['galleryIndex']:04d}.jpg", image_file)
        card["image"] = f"assets/dark-cards/{card['word']}.jpg"
        card["imageType"] = "series-photo"
        card["imageSource"] = source["imageUrl"]
        card["imageVerifiedForWord"] = False

    cards_path.write_text(json.dumps(cards, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Attached {len(dark_cards)} unique Dark series photos")


if __name__ == "__main__":
    main()
