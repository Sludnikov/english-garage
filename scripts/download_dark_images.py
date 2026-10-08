"""Download the verified IMDb Dark (2017) photo gallery for local curation."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import re
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/dark-image-catalog.json"
OUT = Path("/private/tmp/dark-candidates")
OUT.mkdir(exist_ok=True)


def download(item):
    index = item["i"]
    target = OUT / f"{index:04d}.jpg"
    if target.exists() and target.stat().st_size > 5000:
        return index, "cached"
    url = re.sub(r"\._V1_.*\.jpg$", "._V1_QL75_UX1050_.jpg", item["url"])
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()
        if len(body) < 5000:
            return index, "too-small"
        target.write_bytes(body)
        return index, "ok"
    except Exception as exc:
        return index, str(exc)


def main():
    items = json.loads(CATALOG.read_text(encoding="utf-8"))
    counts = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for n, future in enumerate(as_completed(pool.submit(download, item) for item in items), 1):
            index, status = future.result()
            counts[status] = counts.get(status, 0) + 1
            if n % 100 == 0 or n == len(items):
                print(f"{n}/{len(items)}: {counts}", flush=True)


if __name__ == "__main__":
    main()
