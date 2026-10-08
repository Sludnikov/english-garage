"""Choose 500 distinct series stills from the downloaded Dark IMDb gallery."""

from pathlib import Path
from PIL import Image, ImageStat
import json
import random


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/private/tmp/dark-candidates")
CATALOG = json.loads((ROOT / "data/dark-image-catalog.json").read_text(encoding="utf-8"))


def dhash(image):
    gray = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    values = list(gray.get_flattened_data())
    result = 0
    for row in range(8):
        for col in range(8):
            result = (result << 1) | (values[row * 9 + col] > values[row * 9 + col + 1])
    return result


def features(index):
    with Image.open(SOURCE / f"{index:04d}.jpg") as image:
        if image.width / image.height < 1.3 or image.width / image.height > 2.5:
            return None
        gray = image.convert("L").resize((80, 40))
        pixels = list(gray.get_flattened_data())
        mean, stddev = ImageStat.Stat(gray).mean[0], ImageStat.Stat(gray).stddev[0]
        black = sum(pixel < 15 for pixel in pixels) / len(pixels)
        if mean < 25 or black > .72:
            return None
        return {"index": index, "hash": dhash(image), "mean": mean, "stddev": stddev}


def main():
    rng = random.Random(20260929)
    candidates = [item for index in range(1200) if not 35 <= index <= 50
                  if (item := features(index)) is not None]
    selected = []
    for block in range(4):
        group = [item for item in candidates if block * 300 <= item["index"] < (block + 1) * 300]
        for item in group:
            item["score"] = rng.random() * 25 + min(item["mean"], 100) / 5 + item["stddev"] / 3
        group.sort(key=lambda item: item["score"], reverse=True)
        accepted = []
        for threshold in (8, 6, 4, 2):
            for item in group:
                if item in accepted:
                    continue
                if any((item["hash"] ^ other["hash"]).bit_count() <= threshold for other in selected):
                    continue
                accepted.append(item)
                selected.append(item)
                if len(accepted) == 125:
                    break
            if len(accepted) == 125:
                break
        if len(accepted) != 125:
            raise SystemExit(f"Block {block}: only {len(accepted)} images")
        print(f"Block {block + 1}: {len(group)} candidates, {len(accepted)} selected")

    rng.shuffle(selected)
    # These gallery entries are title graphics. Use nearby episode stills instead.
    replacements = {199: 198, 661: 663}
    for item in selected:
        if item["index"] in replacements:
            item["index"] = replacements[item["index"]]
    cards = [card for card in json.loads((ROOT / "dist/cards.json").read_text(encoding="utf-8"))
             if card["deck"] == "dark"]
    assert len(cards) == len(selected) == 500
    result = {}
    for card, image in zip(cards, selected):
        item = CATALOG[image["index"]]
        result[card["word"]] = {
            "galleryIndex": image["index"],
            "imageUrl": item["url"].split("._V1_")[0] + "._V1_QL75_UX1050_.jpg",
            "pageUrl": item["href"].split("?", 1)[0],
            "provider": "IMDb",
        }
    target = ROOT / "data/dark-image-sources.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} selections to {target}")


if __name__ == "__main__":
    main()
