# Kanji-Wortindex (Anki add-on)

Optional desktop add-on for the deck. It rebuilds the word list shown in the kanji popup ("Words with this kanji") from the notes in your collection, so your own cards appear there too.

Everything works without it. The deck ships a static list, and the add-on only keeps it current. Anki syncs the generated `_kvw.js` as a media file, so phones are up to date as well and need no add-on.

## Install

**From AnkiWeb:** *Tools → Add-ons → Get Add-ons*, code `1607352118`, then restart Anki.
Page: <https://ankiweb.net/shared/info/1607352118>

**From source:**
```bash
cd addon/kanji_word_index
zip -r ../Kanji-Wortindex.ankiaddon . -x "__pycache__/*" "*.pyc"
```
Double-click the resulting `.ankiaddon` file to install it. The files must sit at the top level of the archive, not inside a folder.

## What it does

- Reads all notes with the fields `Expression`, `Reading`, `Bedeutung`, `Meaning`
- Writes `_kvw.js` into the media folder when the collection changes, on profile open and before a sync
- Menu entry *Tools → Update kanji word index now* (language follows Anki: German or English)
- Sets the current card aside when the guide card sends the message `jpGuideDone` ("Got it · put away")

## Files

| File | Purpose |
|---|---|
| `kanji_word_index/__init__.py` | Hooks, menu entry, messages |
| `kanji_word_index/kvw.py` | Builds the word index |
| `kanji_word_index/manifest.json` | Add-on metadata |

The add-on ships no third-party data. It reads the `_kvi_*.js` files that come with the deck.

## License

CC BY-SA 4.0, see [`../LICENSE`](../LICENSE).
