# Build tooling

Two scripts turn the deck into plain, diff-friendly files and back again.

```
pip install anki zstandard
python scripts/export.py  Japanisch_Genki_Tobira.apkg   # .apkg  -> data/, templates/, media/
python scripts/build.py                                  # data/, templates/, media/ -> dist/Japanisch_Genki_Tobira.apkg
```

| Path | Content |
|------|---------|
| `data/notes.jsonl` | Public notes (guide card, example note): id, guid, note type, fields, tags, decks/due of the cards |
| `data/notes.private.jsonl` | The vocabulary – git-ignored, see `data/README.md`; without it `build.py` makes the empty template deck |
| `data/radicals.json` | Static radical table used by `scripts/radicals.py` |
| `data/long/` | Very long fields (e.g. the guide card) as separate HTML files |
| `data/decks.json` | Deck tree and deck option presets |
| `templates/<Type>/` | `notetype.json`, card templates (`*.front.html`, `*.back.html`), `fields.txt` |
| `templates/style.css` | Shared card CSS |
| `media/` | Images, fonts and scripts used by the cards |

## Workflow

1. Edit words in `data/notes.jsonl`, templates in `templates/`, or add media.
2. `python scripts/build.py` creates `dist/Japanisch_Genki_Tobira.apkg`.
3. Import it into Anki. Note ids, note type ids, field/template ids, deck option ids and guids are preserved, so Anki **updates** existing notes and your review history stays intact.

`export.py` is the reverse direction: after changing the deck inside Anki, export it as `.apkg` ("Include scheduling" off) and run the script to refresh the files.

## Notes and limitations

- `build.py` regenerates the Kanji word index (`_kvw.js`) with `addon/kanji_word_index/kvw.py`, so keep that file in place.
- `_kvw.js` (word index) and `_kvrn4.js` (radical table, `scripts/radicals.py`) are regenerated on every build. Kanji without a frequency rank may sit in a different order than in the original deck.
- `export → build → export` is a fixed point: running it again gives identical files.
- Tested with `anki` 26.09 (Python package). The output `.apkg` is the modern format (Anki 2.1.50+).
