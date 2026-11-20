#!/usr/bin/env python3
"""Create local AAC pronunciations with Piper's public-domain Kristin voice."""

import json
import os
import subprocess
import tempfile
import wave
from pathlib import Path

from piper import PiperVoice


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "dist" / "cards.json"
OUTPUT = ROOT / "dist" / "assets" / "audio"
MODEL = Path("/private/tmp/en_US-kristin-medium.onnx")


def main() -> None:
    cards = json.loads(CARDS.read_text())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    voice = PiperVoice.load(MODEL)
    with tempfile.TemporaryDirectory(prefix="english-garage-audio-") as temp:
        wav_path = Path(temp) / "word.wav"
        m4a_path = Path(temp) / "word.m4a"
        for index, card in enumerate(cards, 1):
            target = OUTPUT / f"{card['id']}.m4a"
            if target.exists() and target.stat().st_size > 5000:
                continue
            with wave.open(str(wav_path), "wb") as wav_file:
                voice.synthesize_wav(card["word"], wav_file)
            if wav_path.stat().st_size <= 44:
                raise RuntimeError(f"Empty speech file for {card['id']}")
            subprocess.run(
                ["afconvert", str(wav_path), str(m4a_path), "-f", "m4af", "-d", "aac", "-b", "48000"],
                check=True,
            )
            if m4a_path.stat().st_size <= 5000:
                raise RuntimeError(f"Empty AAC file for {card['id']}")
            os.replace(m4a_path, target)
            if index % 100 == 0:
                print(f"Created {index}/{len(cards)}", flush=True)
    print(f"Ready: {len(cards)} audio files in {OUTPUT}")


if __name__ == "__main__":
    main()
