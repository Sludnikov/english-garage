# Sources and licenses

- `LexiCore_5000.csv`: [X-Trivle/LexiCore](https://github.com/X-Trivle/LexiCore), CC BY 4.0. Used for rough global rank and CEFR filtering.
- Russian draft translations: [Vocab Bloom Hub](https://vocab-bloom-hub.com/en/docs/data-license), CC BY 4.0. Source JSONL files were used to build `dist/cards.json`; they are not bundled because they contain a much larger corpus.
- US pronunciation path index: [compact Wiktionary dictionary](https://github.com/tdulcet/compact-dictionaries), built from Wiktionary. The cards include direct Wikimedia Commons file pages, file authors and file licenses as fetched by `scripts/verify_audio.py`.
- Card illustrations and garage/avatar art: generated specifically for English Garage. They are not screenshots from any film or series.

The card data is a derived educational set. It still needs human linguistic review and a separate meaning-specific image for each card before it satisfies the full specification.
