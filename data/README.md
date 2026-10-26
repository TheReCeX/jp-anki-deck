# Data

| File | Content | In Git |
|------|---------|--------|
| `notes.jsonl` | Guide card and one example note | yes |
| `notes.private.jsonl` | The vocabulary (Genki/Tobira, Wadoku-derived meanings) | **no** (git-ignored, pending permission) |
| `decks.json` | Deck tree and deck option presets | yes |
| `radicals.json` | Static radical table for `_kvrn4.js` | yes |
| `long/` | Long fields (guide card) | yes |

`scripts/build.py` reads both note files if present; without `notes.private.jsonl` it builds the empty template deck.
