# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-10-26

First public release. **Genki and Tobira vocabulary is not included yet.** The release ships the templates and 14 example words (deck `Japanisch::Beispiel`).

### Added
- Note types with cards in both directions (recognition and recall), 14 example words in four chapters
- German and English meanings with a language switch
- Kanji popup with animated stroke order, readings, radical, components, school grade and JLPT level
- Four writing modes: Watch, Blind, Snap, Guided
- Radical cards listing all kanji of the deck, word list per kanji
- Settings panel inside the card: rōmaji or furigana, accent color, sizes, width, font
- Guide card (German and English) with licenses and sources, including the Wadoku license text
- Optional add-on Kanji-Wortindex (also on [AnkiWeb](https://ankiweb.net/shared/info/1607352118))
- Card templates, add-on source, license texts and credits in this repository
- Build tooling in `scripts/`: export a deck to plain files (`data/`, `templates/`, `media/`) and build it again, keeping ids so re-imports update existing cards

## Planned

### Added
- Vocabulary from Genki 1, Genki 2 and Tobira (about 3,700 words), as soon as the license of the Wadoku-derived meanings is clarified
- Updated README and guide card for the full deck

[1.0.0]: https://github.com/TheReCeX/jp-anki-deck/releases/tag/v1.0
