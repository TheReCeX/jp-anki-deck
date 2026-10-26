#!/usr/bin/env python3
"""Build the Anki deck (.apkg) from the files in this repository.

    python scripts/build.py [-o dist/Japanisch_Genki_Tobira.apkg]

Inputs:
    data/notes.jsonl    all notes (words) with tags, deck and order of their cards
    data/decks.json     deck tree and presets
    data/long/          long fields referenced as "@file:long/..." in notes.jsonl
    templates/          note types (notetype.json, card templates, style.css)
    media/              media files (fonts, stroke data, kanji info, ...)

The word index _kvw.js is generated here with addon/kanji_word_index/kvw.py,
the same code the add-on uses.

Requires: pip install anki
"""
import argparse, hashlib, importlib.util, json, shutil, sys, tempfile, zipfile
from pathlib import Path

import zstandard

from anki.collection import Collection, ExportAnkiPackageOptions


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def load_kvw(repo):
    spec = importlib.util.spec_from_file_location("kvw", repo / "addon" / "kanji_word_index" / "kvw.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def add_notetype(col, tdir):
    meta = json.loads(read(tdir / "notetype.json"))
    mm = col.models
    m = mm.new(meta["name"])
    m["flds"], m["tmpls"] = [], []
    for f in meta["fields"]:
        nf = mm.new_field(f["name"])
        nf.update({k: v for k, v in f.items() if k != "name"})
        mm.add_field(m, nf)
    for t in meta["templates"]:
        nt = mm.new_template(t["name"])
        nt["qfmt"] = read(tdir / f"{t['file']}.front.html")
        nt["afmt"] = read(tdir / f"{t['file']}.back.html")
        nt.update({k: v for k, v in t.items() if k not in ("name", "file")})
        mm.add_template(m, nt)
    m["css"] = read((tdir / meta["css"]).resolve())
    m["sortf"] = meta.get("sortf", 0)
    m["latexPre"] = meta.get("latexPre", m.get("latexPre", ""))
    m["latexPost"] = meta.get("latexPost", m.get("latexPost", ""))
    if meta.get("originalStockKind"):
        m["originalStockKind"] = meta["originalStockKind"]
    mm.add_dict(m)
    m = mm.by_name(meta["name"])
    return m, meta["id"]


def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _field(num, wire, payload):
    return _varint(num << 3 | wire) + payload


def add_all_media(pkg, mdir):
    """Anki's exporter only packs media that note fields reference. The templates also load fonts,
    stroke data and kanji info from the media folder, so rewrite the media part of the package."""
    comp = zstandard.ZstdCompressor(level=10)
    entries, files = b"", {}
    for i, f in enumerate(sorted(p for p in Path(mdir).iterdir() if p.is_file())):
        data = f.read_bytes()
        e = (_field(1, 2, _varint(len(f.name.encode())) + f.name.encode())
             + _field(2, 0, _varint(len(data)))
             + _field(3, 2, _varint(20) + hashlib.sha1(data).digest()))
        entries += _field(1, 2, _varint(len(e)) + e)
        files[str(i)] = comp.compress(data)
    tmp = Path(str(pkg) + ".tmp")
    with zipfile.ZipFile(pkg) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as zout:
        for name in zin.namelist():
            if name == "media" or name.isdigit():
                continue
            zout.writestr(name, zin.read(name))
        zout.writestr("media", comp.compress(entries))
        for name, data in files.items():
            zout.writestr(name, data)
    tmp.replace(pkg)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    repo = Path(args.repo)
    out = Path(args.out) if args.out else repo / "dist" / "Japanisch_Genki_Tobira.apkg"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    tmp = Path(tempfile.mkdtemp())
    path = str(tmp / "c.anki2")
    col = Collection(path)

    # note types
    types, ids = {}, []
    for d in sorted((repo / "templates").iterdir()):
        if (d / "notetype.json").exists():
            m, orig = add_notetype(col, d)
            types[m["name"]] = m
            ids.append((m["id"], orig))

    # presets and decks
    dd = json.loads(read(repo / "data" / "decks.json"))
    pid = {}
    for p in dd["presets"]:
        cid = col.decks.add_config_returning_id(p["name"])
        conf = col.decks.get_config(cid)
        conf.update({k: v for k, v in p.items() if k not in ("id", "name")})
        col.decks.update_config(conf)
        if p.get("id") and p["id"] != cid:     # keep the original id, so a re-import updates the preset
            col.db.execute("update deck_config set id=? where id=?", p["id"], cid)
            cid = p["id"]
        pid[p["name"]] = cid
    for e in dd["decks"]:
        did = col.decks.id(e["name"])
        dk = col.decks.get(did)
        dk["conf"] = pid[e["preset"]]
        dk["desc"] = e.get("desc", "")
        dk["collapsed"] = e.get("collapsed", False)
        col.decks.save(dk)

    # notes
    fixes = []
    note_lines = []
    for fn in ("notes.jsonl", "notes.private.jsonl"):      # the private file is optional (not in the repo)
        f = repo / "data" / fn
        if f.exists():
            note_lines += f.read_text(encoding="utf-8").splitlines()
    if True:
        for line in note_lines:
            if not line.strip():
                continue
            n = json.loads(line)
            m = types[n["notetype"]]
            note = col.new_note(m)
            for k, v in n["fields"].items():
                if v.startswith("@file:"):
                    v = read(repo / "data" / v[6:])
                note[k] = v
            note.tags = n["tags"]
            first_deck = n["cards"][0]["deck"] if n["cards"] else "Default"
            col.add_note(note, col.decks.id(first_deck))
            fixes.append((note.id, n))
    # guid, deck and position of each card exactly as in notes.jsonl
    for nid, n in fixes:
        col.db.execute("update notes set guid=? where id=?", n["guid"], nid)
        keep = {c["ord"] for c in n["cards"]}
        gone = [cid for cid, o in col.db.all("select id, ord from cards where nid=?", nid) if o not in keep]
        if gone:
            col.remove_cards_and_orphaned_notes(gone)     # cards that were deleted on purpose
        for c in n["cards"]:
            col.db.execute("update cards set did=?, due=?, queue=? where nid=? and ord=?",
                           col.decks.id(c["deck"]), c["due"], c.get("queue", 0), nid, c["ord"])
    # keep the note ids from notes.jsonl (stable ids = reproducible export, clean diffs)
    for nid, n in fixes:
        if n["id"] != nid:
            col.db.execute("update cards set nid=? where nid=?", n["id"], nid)
            col.db.execute("update notes set id=? where id=?", n["id"], nid)
    # restore the original note type ids, so that importing the deck into an existing
    # collection updates the existing note types and notes instead of duplicating them
    for new, old in ids:
        for sql in ("update notetypes set id=? where id=?", "update fields set ntid=? where ntid=?",
                    "update templates set ntid=? where ntid=?", "update notes set mid=? where mid=?"):
            col.db.execute(sql, old, new)
    col.close()

    # media, then the generated word index
    col = Collection(path)
    mdir = Path(col.media.dir())
    for f in (repo / "media").iterdir():
        if f.is_file():
            shutil.copy2(f, mdir / f.name)
    load_kvw(repo).write_to_media(col)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import radicals
    radicals.write_to_media(col, repo / "data" / "radicals.json")

    col.export_anki_package(out_path=str(out), limit=None, options=ExportAnkiPackageOptions(
        with_scheduling=True, with_deck_configs=True, with_media=True, legacy=False))
    n, c = col.note_count(), col.card_count()
    col.close()
    add_all_media(out, mdir)
    print(f"{n} notes, {c} cards, {len(list(mdir.iterdir()))} media files -> {out}")


if __name__ == "__main__":
    sys.exit(main())
