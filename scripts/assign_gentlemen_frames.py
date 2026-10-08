#!/usr/bin/env python3
"""Fill remaining Gentlemen card images with diverse frames from official clips."""
import json
import random
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "dist/assets/gentlemen-cards"
VIDEOS = {
    "trailer": (Path("/private/tmp/gentlemen-trailer-frames"), "https://www.netflix.com/tudum/videos/the-gentlemen-season-2-trailer"),
    "teaser": (Path("/private/tmp/gentlemen-teaser-frames"), "https://www.netflix.com/title/81437051"),
    "deleted": (Path("/private/tmp/gentlemen-deleted-frames"), "https://www.netflix.com/tudum/videos/the-gentlemen-season-2-deleted-scenes"),
}


def signature(path):
    with Image.open(path) as source:
        image = source.convert("RGB")
        # The top-right watermark and letterbox bars should not drive selection.
        w, h = image.size
        image = image.crop((int(w * .06), int(h * .15), int(w * .94), int(h * .85)))
        tiny = image.resize((8, 5), Image.Resampling.BILINEAR)
        pixels = list(tiny.getdata())
        mean = sum(sum(p) for p in pixels) / (len(pixels) * 3)
        dark = sum(max(p) < 22 for p in pixels) / len(pixels)
        pale = sum(min(p) > 235 for p in pixels) / len(pixels)
        # Reject black frames, fades, and flat graphic intertitles.
        if mean < 31 or dark > .63 or pale > .72:
            return None
        spread = sum(sum((v - mean) ** 2 for v in p) for p in pixels) / (len(pixels) * 3)
        if spread < 270:
            return None
        return tuple(v for p in pixels for v in p)


def distance(a, b):
    return sum((x-y) * (x-y) for x, y in zip(a, b)) / len(a)


def dhash(path):
    with Image.open(path) as source:
        image = source.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
        pixels = list(image.getdata())
    return sum((pixels[y * 9 + x] > pixels[y * 9 + x + 1]) << (y * 8 + x)
               for y in range(8) for x in range(8))


def main():
    cards = json.loads((ROOT / "dist/cards.json").read_text())
    source_file = ROOT / "data/gentlemen-frame-sources.json"
    if source_file.exists():
        generated = set(json.loads((ROOT / "data/gentlemen-generated-words.json").read_text(encoding="utf-8")))
        missing = [word for word in json.loads(source_file.read_text(encoding="utf-8")) if word not in generated]
    else:
        missing = [c["word"] for c in cards if c["deck"] == "gentlemen" and not (ASSETS / f'{c["word"]}.jpg').exists()]
    candidates = []
    for kind, (directory, url) in VIDEOS.items():
        for path in sorted(directory.glob("*.jpg")):
            sig = signature(path)
            if sig is not None:
                number = int(path.stem.split("-")[-1])
                if kind == "trailer" and (17 <= number <= 24 or 88 <= number <= 95 or 179 <= number <= 187 or number >= 245):
                    continue
                if kind == "teaser" and (70 <= number <= 75 or number >= 139):
                    continue
                candidates.append({"path": path, "kind": kind, "url": url, "index": number, "sig": sig, "hash": dhash(path)})
    print(f"{len(missing)} missing cards, {len(candidates)} usable frames")
    if len(candidates) < len(missing):
        raise SystemExit("Not enough usable frames")

    # Farthest-point sampling favors varied scenes, lighting, and compositions.
    random.Random(1973).shuffle(candidates)
    selected = []
    available = list(candidates)
    minimum = [float("inf")] * len(available)
    deleted_count = 0
    while len(selected) < len(missing):
        if deleted_count >= 120:
            for i in range(len(available) - 1, -1, -1):
                if available[i]["kind"] == "deleted":
                    available.pop(i)
                    minimum.pop(i)
        if not available:
            raise SystemExit("Ran out of diverse frames")
        if not selected:
            choice = max(range(len(available)), key=lambda i: sum(available[i]["sig"]) / len(available[i]["sig"]))
        else:
            choice = max(range(len(available)), key=lambda i: minimum[i])
        item = available.pop(choice)
        minimum.pop(choice)
        selected.append(item)
        deleted_count += item["kind"] == "deleted"
        for i, other in enumerate(available):
            d = distance(item["sig"], other["sig"])
            if (item["hash"] ^ other["hash"]).bit_count() <= 5:
                d *= .01
            if item["kind"] == other["kind"] and abs(item["index"] - other["index"]) <= 3:
                d *= .05
            if d < minimum[i]:
                minimum[i] = d
        if len(selected) % 50 == 0:
            print(f"selected {len(selected)}", flush=True)

    # Shuffle assignment so adjacent cards do not repeat a single scene sequence.
    random.Random(2026).shuffle(selected)
    provenance = {}
    for word, item in zip(missing, selected):
        with Image.open(item["path"]) as image:
            image.convert("RGB").save(ASSETS / f"{word}.jpg", quality=88, optimize=True)
        provenance[word] = {
            "source": item["url"],
            "clip": item["kind"],
            "timeSeconds": round((item["index"] - 1) / 2, 1),
        }
    (ROOT / "data/gentlemen-frame-sources.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Assigned {len(provenance)} real series frames")


if __name__ == "__main__":
    main()
