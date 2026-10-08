#!/usr/bin/env python3
"""Verify every Commons pronunciation file and attach license/credit metadata."""
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / 'dist/cards.json'
rows = json.loads(CARDS.read_text(encoding='utf-8'))
names = sorted({r['audioFile'] for r in rows if not r.get('audioVerified')})
chunks = [names[i:i+25] for i in range(0, len(names), 25)]

def plain(s):
    return html.unescape(re.sub(r'<[^>]*>', '', s or '')).strip()

def fetch(batch):
    query = urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','titles':'|'.join('File:'+n for n in batch)})
    url = 'https://commons.wikimedia.org/w/api.php?' + query
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'EnglishGaragePersonalPWA/1.0 (vocabulary audio verification)'})
            with urllib.request.urlopen(req, timeout=40) as response:
                data = json.load(response)
            found = {}
            for page in data.get('query',{}).get('pages',{}).values():
                info = (page.get('imageinfo') or [{}])[0]
                meta = info.get('extmetadata') or {}
                name = page.get('title','').removeprefix('File:')
                if not info.get('url'):
                    continue
                val = lambda key: meta.get(key,{}).get('value','')
                found[name] = {
                    'audio': info['url'].split('?')[0],
                    'audioAttribution': info.get('descriptionurl', ''),
                    'audioCredit': plain(val('Artist')),
                    'audioLicense': plain(val('LicenseShortName')),
                    'audioLicenseUrl': val('LicenseUrl'),
                    'audioVerified': True,
                }
            return found
        except Exception:
            if attempt == 4: raise
            time.sleep(5*(attempt+1))

if __name__ == '__main__':
    found = {}
    for i, batch in enumerate(chunks, 1):
        found.update(fetch(batch))
        print(f'Checked batch {i}/{len(chunks)}', flush=True)
        time.sleep(1.5)
    missing = sorted(set(names)-set(found))
    for r in rows:
        if r['audioFile'] in found:
            r.update(found[r['audioFile']])
    CARDS.write_text(json.dumps(rows, ensure_ascii=False, separators=(',',':')), encoding='utf-8')
    licenses = {}
    for r in rows:
        k = r.get('audioLicense','MISSING'); licenses[k] = licenses.get(k,0)+1
    print('Newly verified',len(found),'/',len(names),'files; missing:',len(missing))
    print('Licenses:',licenses)
    if missing: print('Missing examples:',missing[:30])
