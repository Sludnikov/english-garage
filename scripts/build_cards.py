#!/usr/bin/env python3
"""Build a reproducible, disjoint A2–B2 vocabulary set from open data."""
import csv
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
LEX = ROOT / "data/LexiCore_5000.csv"
RU = Path("/private/tmp/vocab-bloom-ru.jsonl")
WIKT = Path("/private/tmp/compact-wiktionary-en.jsonl")

DECKS = ["gentlemen", "dark", "potter"]
THEMES = {
    "gentlemen": set("estate mansion duke lord lady family brother sister father mother inheritance property lawyer business deal money cash bank account budget profit price cost rich wealthy debt loan pay buy sell shop market client customer manager company office meeting contract agreement promise trust secret threat danger fight police crime prison security guard suit jacket shirt shoes watch car driver garage road street house home garden farm horse dinner breakfast lunch drink food restaurant kitchen door room key letter phone message call visit invite guest party wedding friend enemy plan choice chance risk rule power owner service work job salary boss team partner support protect escape travel city country village neighbour respect polite rude confident clever honest careful decide explain offer accept refuse negotiate argue discover avoid improve repair build design decorate collect invest spend save earn succeed fail win lose return arrive leave stay move walk run drive ride carry bring take give find lose need want like love hate believe hope fear know learn remember forget ask answer speak tell listen hear see look watch show think understand choose change open close start finish wait help try use keep hold break fix clean cook read write sign search share hide reveal prove notice follow allow refuse deserve reward value item purchase upgrade style fashion elegant classic expensive luxury modern private public loyal kind generous patient calm quiet proud brave smart safe ready early late soon today tomorrow yesterday".split()),
    "dark": set("time past future present year month week day night morning evening hour minute second clock watch date season cycle repeat again before after during until since already still yet never always often sometimes memory dream remember forget know secret mystery question answer truth lie cause effect reason result change return disappear appear find search discover investigate explore cave forest tree path road tunnel door key light dark shadow sun moon star sky cloud rain storm thunder lightning wind air water river lake sea earth world universe space place town village city home house school family parent child son daughter mother father brother sister grandfather grandmother ancestor generation birth life death die alive dead young old age grow adult stranger friend neighbour meet follow chase escape hide reveal believe doubt trust suspect fear hope love hate choose decide prevent save protect help hurt kill survive danger safe lost alone together near far here there somewhere nowhere begin end finish start stop continue wait late early yesterday today tomorrow future past present parallel same different strange familiar possible impossible real unreal true false wrong right certain uncertain clear confused silent sound voice hear listen speak whisper shout ask answer call message letter diary book page write read photograph picture mirror reflection face name identity destiny fate chance choice consequence".split()),
    "potter": set("magic wizard witch spell wand castle school student teacher lesson class exam homework book library page story tale myth legend secret mystery adventure journey train station platform ticket luggage suitcase broom fly flight owl bird feather creature animal dragon snake spider cat dog horse forest tree lake river mountain cave garden stone rock fire flame water air earth light dark shadow star moon sun sky cloud rain snow storm thunder lightning door key lock room hall tower stairs corridor window wall portrait painting picture mirror cloak robe coat hat scarf gloves shoes boots bag pocket coin gold silver treasure gift prize award cup trophy game team player match sport win lose champion brave courage loyal friend friendship enemy villain hero protect defend fight attack escape hide find seek discover explore search rescue save heal hurt danger safe potion bottle cup glass food feast dinner breakfast lunch sweet candy chocolate bakery shop market bank vault money letter mail envelope newspaper photograph map path road village town city home family mother father brother sister cousin aunt uncle parent child baby guest party holiday Christmas celebration wedding birthday love trust promise truth lie choice decision hope dream fear smile laugh cry angry happy sad proud kind clever wise curious patient powerful weak strong young old new ancient famous rare common ordinary special strange wonderful".split()),
}

def records(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def main():
    ranks = {}
    with LEX.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            w = row["word"].lower().strip()
            if row["cefr_level"] in {"A2", "B1", "B2"} and re.fullmatch(r"[a-z]{3,18}", w):
                ranks.setdefault(w, (int(row["rank_global"]), row["cefr_level"], row["pos"]))

    translations = {}
    for row in records(RU):
        w = row.get("word", "").lower().strip()
        variants = row.get("variants_of_words") or []
        if w in ranks and variants and isinstance(variants[0], str):
            value = variants[0].strip()
            if re.search(r"[а-яё]", value, re.I) and len(value) <= 80:
                translations.setdefault(w, {})[row.get("part_of_speech", "")] = value

    audio = {}
    for row in records(WIKT):
        w = row.get("", "").lower().strip()
        path = row.get("a", "")
        if w in ranks and isinstance(path, str) and "en-us" in path.lower() and path.lower().endswith((".ogg", ".oga", ".mp3")):
            audio.setdefault(w, path)

    candidates = sorted((w for w in set(ranks) & set(translations) & set(audio) if ranks[w][2] in translations[w]), key=lambda w: ranks[w][0])
    # Prefer concrete, everyday content words over grammatical items and inflected duplicates.
    blocked = {"used", "using", "does", "did", "done", "been", "being", "having", "rather", "whether", "whilst", "among", "throughout", "upon", "unless", "although", "besides", "namely", "whose", "whom", "yourself", "himself", "herself", "ourselves", "themselves", "center", "centre", "emotion", "senior", "column", "impress", "aisle", "principle", "oak", "associate", "facility", "dive", "definition", "gas", "admit"}
    candidates = [w for w in candidates if w not in blocked and ranks[w][2] not in {"other", "determiner", "preposition", "conjunction", "pronoun", "article"}]
    if len(candidates) < 1500:
        raise SystemExit(f"Only {len(candidates)} usable words")

    selected = {d: [] for d in DECKS}
    used = set()
    for d in DECKS:
        for w in candidates:
            if w in THEMES[d] and w not in used and len(selected[d]) < 500:
                selected[d].append(w); used.add(w)
    for w in candidates:
        if w in used:
            continue
        target = min(DECKS, key=lambda d: len(selected[d]))
        if len(selected[target]) >= 500:
            break
        selected[target].append(w); used.add(w)
    if any(len(v) != 500 for v in selected.values()):
        raise SystemExit({d: len(v) for d, v in selected.items()})

    output = []
    for d in DECKS:
        for w in selected[d]:
            rank, level, pos = ranks[w]
            path = audio[w]
            # Wikimedia's encoded file path is provided by Wiktionary data.
            url = "https://upload.wikimedia.org/wikipedia/commons/" + "/".join(quote(part) for part in path.split("/"))
            output.append({
                "id": f"{d}-{w}", "deck": d, "word": w, "level": level,
                "pos": pos, "ru": translations[w][pos], "rank": rank,
                "audio": url, "audioSource": "Wikimedia Commons / Wiktionary",
                "audioFile": path.split("/")[-1],
                "audioAttribution": "https://commons.wikimedia.org/wiki/File:" + quote(path.split("/")[-1]),
                "image": f"assets/{d}.png",
                "imageType": "generated-theme-background",
                "imageSource": "Original generated thematic illustration for English Garage",
                "imageVerifiedForWord": False,
            })
    dest = ROOT / "dist/cards.json"
    if dest.exists():
        previous_cards = json.loads(dest.read_text(encoding='utf-8'))
        previous = {r['audioFile']: r for r in previous_cards if r.get('audioVerified')}
        previous_images = {r['id']: r for r in previous_cards if r.get('deck') in {'gentlemen', 'dark', 'potter'}}
        for r in output:
            old = previous.get(r['audioFile'])
            if old:
                for field in ('audio', 'audioAttribution', 'audioCredit', 'audioLicense', 'audioLicenseUrl', 'audioVerified'):
                    if field in old: r[field] = old[field]
            old_image = previous_images.get(r['id'])
            if old_image and old_image.get('image', '').startswith(('assets/gentlemen-cards/', 'assets/dark-cards/', 'assets/potter-cards/')) and (ROOT / 'dist' / old_image['image']).is_file():
                for field in ('image', 'imageType', 'imageSource', 'imageTimeSeconds', 'imageCaption', 'imageFilm', 'imageVerifiedForWord'):
                    if field in old_image: r[field] = old_image[field]
    dest.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(output)} cards to {dest}, {len(set(x['word'] for x in output))} distinct words")
    print({d: {level: sum(x['deck'] == d and x['level'] == level for x in output) for level in ('A2','B1','B2')} for d in DECKS})

if __name__ == "__main__":
    main()
