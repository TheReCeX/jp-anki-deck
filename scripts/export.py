#!/usr/bin/env python3
"""Export a finished .apkg into the repository layout.

    python scripts/export.py path/to/deck.apkg

Writes (and overwrites):
    data/notes.jsonl      one line per note (words, tags, deck and order of its cards)
    data/decks.json       deck tree and deck presets
    data/long/            very long fields (e.g. the guide card), referenced from notes.jsonl
    templates/<Type>/     card templates and notetype.json per note type
    templates/style.css   styling (or <Type>/style.css if the types differ)
    media/                media files (without the generated _kvw.js and _kvrn4.js)

Requires: pip install anki
"""
import argparse, json, re, shutil, sys, tempfile
from pathlib import Path

from anki.collection import Collection
from anki.import_export_pb2 import ImportAnkiPackageOptions
from anki.collection import ImportAnkiPackageRequest

LONG = 3000                 # fields longer than this go to data/long/
GENERATED_MEDIA = {"_kvw.js", "_kvrn4.js"}   # built by the add-on code, see scripts/build.py


def slug(s):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_") or "x"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("apkg")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    repo = Path(args.repo)

    tmp = tempfile.mkdtemp()
    col = Collection(str(Path(tmp) / "c.anki2"))
    col.import_anki_package(ImportAnkiPackageRequest(
        package_path=str(Path(args.apkg).resolve()),
        options=ImportAnkiPackageOptions(with_scheduling=True, with_deck_configs=True)))

    # ---------- note types ----------
    used = {m for (m,) in col.db.all("select distinct mid from notes")}
    types = [m for m in col.models.all() if m["id"] in used]
    names = {m["id"]: m["name"] for m in types}
    css_all = {m["css"] for m in types}
    shared_css = len(css_all) == 1
    tdir = repo / "templates"
    for old in tdir.glob("*/"):          # mirror: drop old exports of note types
        if old.is_dir():
            shutil.rmtree(old)
    for m in types:
        d = tdir / slug(m["name"])
        tm = []
        for t in m["tmpls"]:
            base = slug(t["name"])
            write(d / f"{base}.front.html", t["qfmt"])
            write(d / f"{base}.back.html", t["afmt"])
            extra = {k: v for k, v in t.items() if k not in ("name", "ord", "qfmt", "afmt") and v not in ("", None, 0)}
            tm.append({"name": t["name"], "file": base, **extra})
        fields = [{k: v for k, v in f.items() if k not in ("ord", "tag", "media") and not (k == "id" and v is None)} for f in m["flds"]]
        meta = {"id": m["id"], "name": m["name"], "sortf": m["sortf"], "type": m["type"],
                "css": "../style.css" if shared_css else "style.css",
                "fields": fields, "templates": tm,
                "latexPre": m.get("latexPre", ""), "latexPost": m.get("latexPost", ""),
                "originalStockKind": m.get("originalStockKind", 0)}
        write(d / "notetype.json", json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        write(d / "fields.txt", "\n".join(f["name"] for f in fields) + "\n")
        if not shared_css:
            write(d / "style.css", m["css"])
    if shared_css:
        write(tdir / "style.css", types[0]["css"])

    # ---------- decks ----------
    confs = {c["id"]: c for c in col.decks.all_config()}
    dname = {}
    decks = []
    for dk in sorted(col.decks.all(), key=lambda d: d["name"]):
        dname[dk["id"]] = dk["name"]
        if dk["id"] == 1 or dk.get("dyn"):
            continue
        e = {"name": dk["name"], "preset": confs[dk["conf"]]["name"]}
        if dk.get("desc"):
            e["desc"] = dk["desc"]
        if dk.get("collapsed"):
            e["collapsed"] = True
        decks.append(e)
    presets = [confs[k] for k in sorted(confs) if k != 1]
    for p in presets:
        p.pop("mod", None); p.pop("usn", None)
    write(repo / "data" / "decks.json", json.dumps({"decks": decks, "presets": presets}, ensure_ascii=False, indent=2) + "\n")

    # ---------- notes ----------
    cards = {}
    for nid, ord_, did, due, queue in col.db.all("select nid, ord, did, due, queue from cards order by nid, ord"):
        c = {"ord": ord_, "deck": dname[did], "due": due}
        if queue != 0:
            c["queue"] = queue
        cards.setdefault(nid, []).append(c)
    ldir = repo / "data" / "long"
    if ldir.exists():
        shutil.rmtree(ldir)
    public, private = [], []
    for nid, guid, mid, flds, tags in col.db.all("select id, guid, mid, flds, tags from notes order by id"):
        m = next(x for x in types if x["id"] == mid)
        vals = flds.split("\x1f")
        fields = {}
        for f, v in zip(m["flds"], vals):
            if len(v) > LONG:
                rel = f"long/{nid}_{slug(f['name'])}.html"
                write(repo / "data" / rel, v)
                v = "@file:" + rel
            fields[f["name"]] = v
        obj = {"id": nid, "guid": guid, "notetype": names[mid], "fields": fields,
               "tags": tags.split(), "cards": cards.get(nid, [])}
        line = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        (public if names[mid] == "Japanisch Anleitung" or "Beispiel" in tags.split() else private).append(line)
    # public: guide card and example note (tag Beispiel) only. private (git-ignored): vocabulary, see data/README.md
    write(repo / "data" / "notes.jsonl", "".join(l + "\n" for l in public))
    write(repo / "data" / "notes.private.jsonl", "".join(l + "\n" for l in private))

    # ---------- media ----------
    mdir = repo / "media"
    if mdir.exists():
        shutil.rmtree(mdir)
    mdir.mkdir(parents=True)
    n = 0
    for f in Path(col.media.dir()).iterdir():
        if f.is_file() and f.name not in GENERATED_MEDIA:
            shutil.copy2(f, mdir / f.name); n += 1
    col.close()
    print(f"{len(public) + len(private)} notes, {len(decks)} decks, {len(types)} note types, {n} media files exported to {repo}")


if __name__ == "__main__":
    sys.exit(main())
