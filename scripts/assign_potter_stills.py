#!/usr/bin/env python3
"""Assign one captioned Harry Potter film still to every Potter card."""
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNONYMS = {
    "flight": "flying fly broom quidditch", "magic": "spell wand wizard witch magical",
    "attack": "battle duel fight attacks", "hero": "harry", "friendship": "friends trio harry ron hermione",
    "wise": "dumbledore mcgonagall", "adventure": "journey travels quest",
    "silver": "silver", "coin": "coins money gringotts", "powerful": "voldemort dumbledore spell",
    "treasure": "horcrux gold cup locket", "lock": "door locked key",
    "journey": "train travels travelling", "seek": "search searching looking",
    "ancient": "hogwarts dumbledore", "castle": "hogwarts castle",
    "creature": "dragon hippogriff basilisk thestral creature beast",
    "rescue": "rescues saves protects", "defend": "protects defends battle",
    "feast": "great hall dinner feast", "curious": "looks examines investigates",
    "courage": "brave battle fights", "spider": "aragog spiders",
    "heal": "hospital heals", "platform": "platform kings cross train",
    "myth": "legend tale story", "prize": "cup trophy tournament",
    "legend": "deathly hallows dumbledore", "corridor": "corridor hallway",
    "owl": "hedwig owl", "walking": "walks walking",
    "writing": "writes writing letter diary", "gate": "gate entrance",
    "joy": "celebrates happy smiling", "ring": "ring",
    "childhood": "young baby child", "romantic": "kiss kissing",
}
STOP = {"the", "and", "with", "from", "into", "that", "this", "harry", "potter", "ron", "hermione", "in", "at", "of", "a", "to"}


def terms(word):
    raw = [word] + SYNONYMS.get(word, "").split()
    out = set()
    for token in raw:
        token = token.lower()
        if token in STOP:
            continue
        out.add(token)
        if len(token) > 4:
            if token.endswith("ing"):
                out.add(token[:-3])
            if token.endswith("ed"):
                out.add(token[:-2])
            if token.endswith("s"):
                out.add(token[:-1])
    return out


def score(word, caption):
    tokens = set(re.findall(r"[a-z]+", caption.lower()))
    if not tokens:
        return 0
    exact = word in tokens
    matches = terms(word) & tokens
    if not matches:
        return 0
    value = (12 if exact else 6) + min(3, len(matches) - 1)
    if "portrait" in tokens and word != "portrait":
        value -= 2
    return value


def main():
    cards = [c for c in json.loads((ROOT / "dist/cards.json").read_text()) if c["deck"] == "potter"]
    catalog = json.loads((ROOT / "data/potter-image-catalog.json").read_text())
    catalog = [item for item in catalog if not any(term in item["caption"].lower() for term in
               ("poster", "photoshoot", "behind the scenes", "directs", "directing", "on set",
                "chris columbus", "david yates", "alfonso cuar", "mike newell"))]
    if len(cards) != 500 or len(catalog) < 1000:
        raise SystemExit("Unexpected card or source count")
    random.Random(2701).shuffle(catalog)
    edges = []
    for card in cards:
        for index, image in enumerate(catalog):
            relevance = score(card["word"], image["caption"])
            if relevance > 0:
                edges.append((relevance, card["word"], index))
    random.Random(443).shuffle(edges)
    edges.sort(key=lambda row: row[0], reverse=True)
    assigned = {}
    used = set()
    film_counts = Counter()
    for relevance, word, index in edges:
        if word in assigned or index in used:
            continue
        image = catalog[index]
        if film_counts[image["film"]] >= 75:
            continue
        assigned[word] = {**image, "captionMatchScore": relevance}
        used.add(index)
        film_counts[image["film"]] += 1

    # Fill the rest evenly across all eight films, avoiding excessive portraits.
    remaining = [i for i in range(len(catalog)) if i not in used]
    random.Random(917).shuffle(remaining)
    for card in cards:
        word = card["word"]
        if word in assigned:
            continue
        remaining.sort(key=lambda i: (film_counts[catalog[i]["film"]], "portrait" in catalog[i]["caption"].lower()))
        index = remaining.pop(0)
        image = catalog[index]
        assigned[word] = {**image, "captionMatchScore": 0}
        used.add(index)
        film_counts[image["film"]] += 1
    out = ROOT / "data/potter-image-sources.json"
    out.write_text(json.dumps(assigned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Assigned {len(assigned)} stills; caption matches: {sum(x['captionMatchScore'] > 0 for x in assigned.values())}")
    print("Film counts:", dict(sorted(film_counts.items())))


if __name__ == "__main__":
    main()
