#!/usr/bin/env python3
"""Replace posters, portrait crops, and missing Potter images with landscape stills."""
import io
import argparse
import json
import random
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

from assign_potter_stills import score

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "dist/assets/potter-cards"
BAD_CAPTION = ("poster", "photoshoot", "behind the scenes", "directs", "directing", "on set",
               "chris columbus", "david yates", "alfonso cuar", "mike newell")


def dhash(image):
    pixels = list(image.convert("L").resize((9, 8), Image.Resampling.BILINEAR).getdata())
    return sum((pixels[y * 9 + x] > pixels[y * 9 + x + 1]) << (y * 8 + x)
               for y in range(8) for x in range(8))


def needs_replacement(word, source):
    if any(term in source["caption"].lower() for term in BAD_CAPTION):
        return True
    path = ASSETS / f"{word}.jpg"
    if not path.exists():
        return True
    with Image.open(path) as image:
        return image.width / image.height < 1.1 or image.width < 600


def fetch_image(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    with Image.open(io.BytesIO(data)) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        if image.width < 600 or image.height < 350 or image.width / image.height < 1.1:
            return None
        if image.width > 960:
            image.thumbnail((960, 960), Image.Resampling.LANCZOS)
        return image.copy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="append", default=[], metavar="WORD")
    args = parser.parse_args()
    source_path = ROOT / "data/potter-image-sources.json"
    sources = json.loads(source_path.read_text())
    catalog = json.loads((ROOT / "data/potter-image-catalog.json").read_text())
    bad = [word for word, source in sources.items() if needs_replacement(word, source) or word in args.replace]
    if not bad:
        print("No images need replacement")
        return
    print(f"Replacing {len(bad)} unsuitable images", flush=True)
    used_urls = {source["imageUrl"] for source in sources.values()}
    rejected_urls = set()
    hashes = []
    for word in sources:
        if word in bad:
            continue
        with Image.open(ASSETS / f"{word}.jpg") as image:
            hashes.append(dhash(image))
    random.Random(916).shuffle(catalog)
    errors = []
    for number, word in enumerate(bad, 1):
        previous = sources[word]
        candidates = [item for item in catalog if item["imageUrl"] not in used_urls and item["imageUrl"] not in rejected_urls and
                      not any(term in item["caption"].lower() for term in BAD_CAPTION)]
        candidates.sort(key=lambda item: (score(word, item["caption"]), item["film"] == previous["film"]), reverse=True)
        chosen = None
        for item in candidates[:100]:
            try:
                image = fetch_image(item["imageUrl"])
            except Exception:
                rejected_urls.add(item["imageUrl"])
                continue
            if image is None:
                rejected_urls.add(item["imageUrl"])
                continue
            visual_hash = dhash(image)
            if any((visual_hash ^ old).bit_count() <= 4 for old in hashes):
                rejected_urls.add(item["imageUrl"])
                continue
            chosen = (item, image, visual_hash)
            break
        if chosen is None:
            errors.append(word)
            continue
        item, image, visual_hash = chosen
        image.save(ASSETS / f"{word}.jpg", format="JPEG", quality=85, optimize=True)
        sources[word] = {**item, "captionMatchScore": score(word, item["caption"])}
        used_urls.add(item["imageUrl"])
        hashes.append(visual_hash)
        if number % 10 == 0 or number == len(bad):
            print(f"Replaced {number}/{len(bad)}; unresolved: {len(errors)}", flush=True)
    source_path.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(f"Could not replace: {', '.join(errors)}")
    print("All selected images are landscape film stills")


if __name__ == "__main__":
    main()
