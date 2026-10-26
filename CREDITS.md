<a id="readme-top"></a>

<div align="center">
  <h1>Credits and Attribution</h1>
  <p>
    This deck stands on the shoulders of free data and software.
    <br />
    License overview: <a href="LICENSE"><strong>LICENSE</strong></a> · Full texts: <a href="LICENSES/"><strong>LICENSES/</strong></a>
  </p>
</div>

## Data in the deck

| Source | Used for | License | Notes |
|---|---|---|---|
| [**KanjiVG**](https://kanjivg.tagaini.net) · Ulrich Apel | Stroke data, radical shape and position | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | converted to JS files |
| [**KANJIDIC2**](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) · EDRDG | Kanji information, readings | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), see [EDRDG licence](https://www.edrdg.org/edrdg/licence.html) | meanings translated into German |
| **diglabo-kanji-data** · based on 文部科学省「音訓の小・中・高等学校段階別割り振り表」(2017) | School grades of kanji | CC BY-SA 4.0 | machine-readable version by diglabo-kanji-data |
| [**JLPT lists**](https://www.tanos.co.uk/jlpt/) · Jonathan Waller | Unofficial JLPT levels | [CC BY](https://creativecommons.org/licenses/by/4.0/) | obtained via [davidluzgouveia/kanji-data](https://github.com/davidluzgouveia/kanji-data) (MIT) |
| [**BabelStone IDS**](https://www.babelstone.co.uk/CJK/IDS.TXT) · Andrew West (version 2025-06-27, Unicode 16.0) | Kanji structure where KanjiVG has no data | free to use | per the file header: facts not protected by copyright, no attribution required, given here anyway |
| [**Wadoku**](https://www.wadoku.de) · Ulrich Apel, co-authors, Wadoku e.V. | Some German word meanings of the planned Genki/Tobira vocabulary (not part of the current release) | [Wadoku.de data license 1.0](LICENSES/Wadoku-Datenlizenz-1.0.txt) | partly taken over, manually translated and edited. **Free and non-commercial distribution only, the license must accompany it** |

The planned vocabulary (not yet included, see README) follows the textbooks *Genki* (The Japan Times) and *Tobira* (Kurosio Publishers). The rights to these works belong to their holders. This deck is not affiliated with them.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Font

[**Sawarabi Mincho**](https://github.com/googlefonts/sawarabi-mincho/) · © 2024 The Sawarabi Mincho Project Authors · [SIL Open Font License 1.1](LICENSES/OFL-1.1-SawarabiMincho.txt). The font is included in the deck.

## Changes made to third-party data

* KANJIDIC2 meanings translated into German (CC BY-SA 4.0 also applies to the translations)
* KanjiVG stroke data converted to compact JS files
* Selection limited to the kanji that appear in the deck
* Wadoku entries shortened or edited for the cards (planned vocabulary)

## Add-on "Kanji-Wortindex"

Own code under CC BY-SA 4.0 (see [`LICENSE`](LICENSE)). The add-on ships no third-party data: it generates `_kvw.js` from the notes of the collection and reads the `_kvi_*.js` files included in the deck. The generated `_kvw.js` contains vocabulary with meanings and therefore also the Wadoku excerpts (see `LICENSE`, exception 2).

AnkiWeb: <https://ankiweb.net/shared/info/1607352118> · Code `1607352118`

<p align="right">(<a href="#readme-top">back to top</a>)</p>
