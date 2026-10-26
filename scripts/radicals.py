# -*- coding: utf-8 -*-
"""Generates media/_kvrn4.js (radical table: names, variants, strokes, deck kanji per radical).

Kanji of the deck = kanji in the Expression field. A kanji belongs to the radical of its glyph in
_kvl_*.js (data/radicals.json: radical_of_glyph); exceptions are listed under "overrides".
Within a radical the kanji are sorted by frequency rank (KANJIDIC, _kvi_*.js).
"""
import glob, json, os, re

KJ = re.compile('[㐀-䶿一-鿿豈-﫿]')
HEAD = '/* Radikalnamen (部首名), Varianten, Striche, Deck-Kanji je Radikal (automatisch erzeugt) */\n'


def _load(media_dir, prefix):
    out = {}
    for fn in glob.glob(os.path.join(media_dir, prefix + '_*.js')):
        t = open(fn, encoding='utf-8').read()
        m = re.search(r'\}\)\((\{.*\})\);?\s*$', t, re.S)
        if m:
            out.update(json.loads(m.group(1)))
    return out


def build(expressions, media_dir, data_file):
    spec = json.load(open(data_file, encoding='utf-8'))
    kvl, kvi = _load(media_dir, '_kvl'), _load(media_dir, '_kvi')
    kanji = []
    for e in expressions:
        for c in KJ.findall(re.sub(r'<[^>]*>', '', e)):
            if c not in kanji:
                kanji.append(c)
    per = {n: [] for n in spec['radicals']}
    for k in kanji:
        if k not in kvl:
            continue
        n = spec['overrides'].get(k) or spec['radical_of_glyph'].get(kvl[k][1])
        if n:
            per[n].append(k)

    def rank(k):
        v = kvi.get(k)
        return v[2] if v and v[2] else 10 ** 9
    body = {n: spec['radicals'][n] + [''.join(sorted(per[n], key=lambda k: (rank(k), k)))] for n in spec['radicals']}
    return HEAD + 'window.KVRN=' + json.dumps(body, ensure_ascii=False, separators=(',', ':')) + ';\n'


def write_to_media(col, data_file):
    rows = col.db.list("select flds from notes")        # Expression is the first field
    exprs = [r.split('\x1f')[0] for r in rows]
    d = col.media.dir()
    txt = build(exprs, d, data_file)
    with open(os.path.join(d, '_kvrn4.js'), 'w', encoding='utf-8') as fh:
        fh.write(txt)
