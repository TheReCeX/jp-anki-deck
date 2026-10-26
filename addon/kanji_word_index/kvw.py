# -*- coding: utf-8 -*-
"""Wortindex "Kanji -> Wörter im Deck" (_kvw.js). Wird sowohl beim Deck-Bau als auch vom Anki-Add-on benutzt."""
import re, json, glob, os, hashlib, html

KJ = '㐀-䶿一-鿿豈-﫿'
KRUN = re.compile('[' + KJ + '々]+$')
GRP = re.compile(r'([^\s\[\]]+)\[([^\]]+)\]')
HTML = re.compile(r'<[^>]*>|\[sound:[^\]]*\]')
FILE = '_kvw.js'

def kata2hira(s): return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)
def hira2kata(s): return ''.join(chr(ord(c) + 0x60) if 'ぁ' <= c <= 'ゖ' else c for c in s)

def load_kvi(media_dir):
    """kanji -> (on_hira[set], kun_stems[set]) aus den _kvi_xx.js-Dateien im Medienordner"""
    out = {}
    for fn in glob.glob(os.path.join(media_dir, '_kvi_*.js')):
        try:
            t = open(fn, encoding='utf-8').read()
            m = re.search(r'\}\)\((\{.*\})\);?\s*$', t, re.S)
            d = json.loads(m.group(1))
        except Exception:
            continue
        for k, v in d.items():
            on = set(kata2hira(x) for x in v[4])
            kun, forms = set(), set()
            for x in v[5]:
                p = x.replace('-', '').split('・'); st = p[0]; ok = ''.join(p[1:])
                if not st: continue
                kun.add(st)
                for n in range(len(ok) + 1): forms.add((st + ok[:n], st))     # Okurigana-Anfang gehört oft zur Lesung (受付 = うけ+つけ)
            for b in on: forms.add((b, b))
            out[k] = (on, kun, sorted(forms))
    return out

_VOICE = {'か': 'が', 'き': 'ぎ', 'く': 'ぐ', 'け': 'げ', 'こ': 'ご', 'さ': 'ざ', 'し': 'じ', 'す': 'ず', 'せ': 'ぜ', 'そ': 'ぞ', 'た': 'だ', 'ち': 'じ', 'つ': 'ず', 'て': 'で', 'と': 'ど',
          'は': 'ば', 'ひ': 'び', 'ふ': 'ぶ', 'へ': 'べ', 'ほ': 'ぼ'}
_PSEM = {'は': 'ぱ', 'ひ': 'ぴ', 'ふ': 'ぷ', 'へ': 'ぺ', 'ほ': 'ぽ'}

def variants(b):
    """Grundlesung -> mögliche Wortformen (Rendaku, Halb-Rendaku, Sokuon)"""
    v = {b}
    f = b[0]
    if f in _VOICE: v.add(_VOICE[f] + b[1:])
    if f in _PSEM: v.add(_PSEM[f] + b[1:])
    for x in list(v):
        if len(x) > 1 and x[-1] in 'くきつち': v.add(x[:-1] + 'っ')
    return v

def align(run, reading, kvi):
    """Kanji-Folge + Gruppenlesung -> [(kanji, Grundlesung|None)] oder None"""
    chars = []
    for c in run:
        chars.append(chars[-1] if (c == '々' and chars) else c)
    n = len(chars)
    if n == 1:
        c = chars[0]; on, kun, forms = kvi.get(c, (set(), set(), []))
        for f, b in sorted(forms, key=lambda x: (-len(x[0]), x[0], x[1])):
            if reading in variants(f): return [(run[0], b)]
        return [(run[0], None)]
    cand = []
    for c in chars:
        on, kun, forms = kvi.get(c, (set(), set(), []))
        L = []
        for f, b in forms:
            for w in sorted(variants(f)): L.append((w, b))
        cand.append(sorted(L, key=lambda x: (-len(x[0]), x[0], x[1])))
    memo = {}
    def go(i, j):
        if i == n: return [] if j == len(reading) else None
        if (i, j) in memo: return memo[(i, j)]
        res = None
        for w, b in cand[i]:
            if reading.startswith(w, j):
                r = go(i + 1, j + len(w))
                if r is not None: res = [b] + r; break
        memo[(i, j)] = res
        return res
    r = go(0, 0)
    if r is None: return None
    return [(run[k], r[k]) for k in range(n)]

def chap_key(tags):
    best = None
    for t in tags.split():
        m = re.fullmatch(r'Genki(\d)::Chapter(\d+)', t)
        if m: k = (0, int(m.group(1)), int(m.group(2)), 'G%s·%d' % (m.group(1), int(m.group(2))))
        else:
            m = re.fullmatch(r'Tobira::第(\d+)課', t)
            if m: k = (1, 0, int(m.group(1)), 'T·%d' % int(m.group(1)))
            else: continue
        if best is None or k[:3] < best[:3]: best = k
    return best

MUSTW = re.compile(r'Genki\d::Chapter\d+::Kanji|Tobira::第\d+課::漢字RW|Radikal漢字::\S+')   # Wörter, die man schreiben können soll

def must_write(tags):
    return any(MUSTW.fullmatch(t) for t in (tags or '').split())

def clip(s, n=2):
    s = html.unescape(HTML.sub('', s or '')).replace('\xa0', ' ').strip()
    p = [x.strip() for x in re.split(r'\s*[;；]\s*', s) if x.strip()]
    return '; '.join(p[:n])

def build(rows, kvi):
    """rows: [(Expression, Reading, Bedeutung, Meaning, tags)] -> js-Text"""
    W, widx, K, MW = [], {}, {}, set()
    rows = sorted(rows, key=lambda r: tuple(' '.join(sorted((x or '').split())) if i == 4 else (x or '') for i, x in enumerate(r)))   # unabhängig von der Notiz-Reihenfolge
    for expr, rd, de, en, tags in rows:
        expr = html.unescape(HTML.sub('', expr or '')).replace('\xa0', ' ').strip(); rd = html.unescape(HTML.sub('', rd or '')).replace('\xa0', ' ').strip()
        if not expr or not re.search('[' + KJ + ']', expr): continue
        ck = chap_key(tags)
        kana = GRP.sub(lambda m: m.group(2), rd).replace(' ', '') if rd else ''
        key = expr
        if key in widx: wi = widx[key]
        else:
            wi = len(W); widx[key] = wi; W.append([expr, kana, clip(de), clip(en), ck[3] if ck else '', ck[:3] if ck else (9, 0, 0)])
        if must_write(tags): MW.add(wi)
        for m in GRP.finditer(rd):
            km = KRUN.search(m.group(1))
            if not km: continue
            run = km.group(0); al = align(run, kata2hira(m.group(2)), kvi)
            if al is None: al = [(c, None) for c in run if c != '々']
            for c, b in al:
                if c == '々' or not re.match('[' + KJ + ']', c): continue
                if b is None: lab = ''
                else:
                    on = kvi.get(c, (set(), set(), []))[0]
                    lab = hira2kata(b) if b in on else b
                g = K.setdefault(c, {}).setdefault(lab, [])
                if wi not in g: g.append(wi)
    order = lambda i: W[i][5]
    ks = {}
    for c, gs in K.items():
        L = [[lab, sorted(ix, key=order)] for lab, ix in gs.items()]
        L.sort(key=lambda x: (x[0] == '', -len(x[1]), x[0]))
        ks[c] = L
    used = sorted({i for gs in ks.values() for _, ix in gs for i in ix})
    remap = {o: n for n, o in enumerate(used)}
    Wo = [W[i][:5] + ([1] if i in MW else []) for i in used]   # 6. Eintrag 1 = schreiben können
    ko = {c: [[lab, [remap[i] for i in ix]] for lab, ix in gs] for c, gs in ks.items()}
    body = json.dumps({'w': Wo, 'k': ko}, ensure_ascii=False, separators=(',', ':'))
    return '/* Wortindex: Kanji -> Wörter aus dem eigenen Deck (automatisch erzeugt) */\nwindow.KVW=' + body + ';\n'

def collect(col):
    """Alle Notizen mit Feldern Expression/Reading/Bedeutung/Meaning aus einer Anki-Sammlung"""
    rows = []
    for m in col.models.all():
        names = [f['name'] for f in m['flds']]
        if 'Expression' not in names or 'Reading' not in names: continue
        ix = {n: i for i, n in enumerate(names)}
        for flds, tags in col.db.all('select flds, tags from notes where mid = ?', m['id']):
            f = flds.split('\x1f')
            g = lambda n: f[ix[n]] if n in ix and ix[n] < len(f) else ''
            rows.append((g('Expression'), g('Reading'), g('Bedeutung'), g('Meaning'), tags))
    return rows

def write_to_media(col):
    d = col.media.dir(); txt = build(collect(col), load_kvi(d)); p = os.path.join(d, FILE)
    try:
        if os.path.exists(p) and open(p, encoding='utf-8').read() == txt: return False
    except Exception: pass
    with open(p, 'w', encoding='utf-8') as fh: fh.write(txt)
    return True
