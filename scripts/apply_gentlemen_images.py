#!/usr/bin/env python3
"""Attach each Gentlemen card to its own local image and record provenance."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "dist/cards.json"
ASSETS = ROOT / "dist/assets/gentlemen-cards"
SOURCES = ROOT / "data/gentlemen-stills"


def main():
    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    mapped = json.loads((ROOT / "data/gentlemen-image-sources.json").read_text(encoding="utf-8"))
    gallery_sources = json.loads((ROOT / "data/gentlemen-gallery-sources.json").read_text(encoding="utf-8"))
    frame_sources = json.loads((ROOT / "data/gentlemen-frame-sources.json").read_text(encoding="utf-8"))
    generated_words = set(json.loads((ROOT / "data/gentlemen-generated-words.json").read_text(encoding="utf-8")))
    source_urls = {}
    for name in ("sources.json", "tudum-sources.json", "ending-sources.json", "cast-sources.json"):
        for item in json.loads((SOURCES / name).read_text(encoding="utf-8")):
            source_urls[Path(item["path"]).name] = item["url"]

    # Restore original series photos in case an earlier generated asset reused a word filename.
    for word, info in mapped.items():
        shutil.copyfile(SOURCES / info["file"], ASSETS / f"{word}.jpg")

    gentlemen = [card for card in cards if card["deck"] == "gentlemen"]
    missing = [card["word"] for card in gentlemen if not (ASSETS / (card["word"] + ".jpg")).is_file()]
    if missing:
        raise SystemExit(f"Missing {len(missing)} Gentlemen images: {', '.join(missing[:30])}")
    if len(gentlemen) != 500:
        raise SystemExit(f"Expected 500 Gentlemen cards, found {len(gentlemen)}")

    for card in gentlemen:
        word = card["word"]
        card["image"] = f"assets/gentlemen-cards/{word}.jpg"
        if word in mapped:
            card["imageType"] = "series-photo"
            card["imageSource"] = source_urls[mapped[word]["file"]]
            card.pop("imageTimeSeconds", None)
        elif word in gallery_sources:
            card["imageType"] = "series-photo"
            card["imageSource"] = gallery_sources[word]["imageUrl"]
            card.pop("imageTimeSeconds", None)
        elif word in frame_sources and word not in generated_words:
            card["imageType"] = "series-frame"
            card["imageSource"] = frame_sources[word]["source"]
            card["imageTimeSeconds"] = frame_sources[word]["timeSeconds"]
        else:
            card["imageType"] = "generated-word-photo"
            card["imageSource"] = "Original generated photo inspired by the series' visual style"
            card.pop("imageTimeSeconds", None)
        card["imageVerifiedForWord"] = False

    CARDS.write_text(json.dumps(cards, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    counts = {image_type: sum(card["imageType"] == image_type for card in gentlemen)
              for image_type in ("series-photo", "series-frame", "generated-word-photo")}
    print(f"Attached {len(gentlemen)} unique images ({counts['series-photo']} series photos, "
          f"{counts['series-frame']} series frames, {counts['generated-word-photo']} generated)")


if __name__ == "__main__":
    main()
