#!/usr/bin/env python3
"""Download and resize the selected film stills for local flashcards."""
import argparse
import io
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist/assets/potter-cards"


def download(item):
    word, source = item
    dest = OUT / f"{word}.jpg"
    last_error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(source["imageUrl"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                data = response.read()
            with Image.open(io.BytesIO(data)) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
                if image.width < 500 or image.height < 300:
                    raise ValueError(f"image too small: {image.size}")
                if image.width > 960:
                    image.thumbnail((960, 960), Image.Resampling.LANCZOS)
                image.save(dest, format="JPEG", quality=85, optimize=True)
            return word, None
        except Exception as error:
            last_error = f"{type(error).__name__}: {error}"
            time.sleep(1 + attempt)
    return word, last_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    sources = json.loads((ROOT / "data/potter-image-sources.json").read_text())
    items = list(sources.items())[: args.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    errors = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(download, item) for item in items]
        for number, future in enumerate(as_completed(futures), 1):
            word, error = future.result()
            if error:
                errors[word] = error
            if number % 50 == 0 or number == len(items):
                print(f"Processed {number}/{len(items)}; errors: {len(errors)}", flush=True)
    error_path = ROOT / "data/potter-download-errors.json"
    if errors:
        error_path.write_text(json.dumps(errors, indent=2) + "\n")
        raise SystemExit(f"Failed to download {len(errors)} images")
    error_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
