# -*- coding: utf-8 -*-
"""Kanji-Wortindex für das Deck „Japanisch (Genki + Tobira)“.

Erzeugt aus allen Notizen mit den Feldern Expression/Reading/Bedeutung/Meaning die Datei _kvw.js im Medienordner.
Die Karte liest diese Datei im Kanji-Popup („Wörter mit diesem Kanji“). Anki synchronisiert Medien automatisch,
dadurch ist die Liste auch auf Handy (AnkiDroid/iOS) aktuell, ohne dass dort ein Add-on laufen muss.

Außerdem: Der Knopf „Verstanden · aussortieren“ auf der Anleitungskarte schickt die Nachricht „jpGuideDone“;
das Add-on setzt dann die aktuelle Karte aus (wie Taste @).
"""
from aqt import mw, gui_hooks
from aqt.qt import QAction, QTimer
from aqt.utils import tooltip
from anki import lang as _lang

from . import kvw

_timer = None

_T = {
    "de": {"menu": "Kanji-Wortindex jetzt aktualisieren", "done": "Kanji-Wortindex aktualisiert.",
           "same": "Kanji-Wortindex ist bereits aktuell.", "err": "Kanji-Wortindex: Fehler – %s"},
    "en": {"menu": "Update kanji word index now", "done": "Kanji word index updated.",
           "same": "Kanji word index is already up to date.", "err": "Kanji word index: error – %s"},
}


def _t(key):
    lang = str(getattr(_lang, "current_lang", "en") or "en").lower()
    return _T["de" if lang.startswith("de") else "en"][key]


def rebuild(show=False):
    try:
        if not mw or not mw.col:
            return
        changed = kvw.write_to_media(mw.col)
        if show:
            tooltip(_t("done") if changed else _t("same"))
    except Exception as e:                      # nie Anki stören
        print("[Kanji-Wortindex]", e)
        if show:
            tooltip(_t("err") % e)


def _schedule(*_args):
    """Mehrere Änderungen kurz hintereinander (Import, Bearbeiten) zu einem Lauf bündeln."""
    global _timer
    if _timer is None:
        _timer = QTimer(mw)
        _timer.setSingleShot(True)
        _timer.timeout.connect(rebuild)
    _timer.start(3000)


def _on_op(changes, handler):
    if getattr(changes, "note_text", False) or getattr(changes, "tag", False) or getattr(changes, "notetype", False):
        _schedule()


def _menu():
    a = QAction(_t("menu"), mw)
    a.triggered.connect(lambda: rebuild(True))
    mw.form.menuTools.addAction(a)


def _on_js(handled, message, context):
    """Anleitungskarte: aktuelle Karte aussetzen (nur im Lernmodus, nur für diese Nachricht)."""
    if message != "jpGuideDone":
        return handled
    try:
        from aqt.reviewer import Reviewer
        if isinstance(context, Reviewer) and context.card:
            if hasattr(context, "suspend_current_card"):
                context.suspend_current_card()
            else:                                   # ältere Anki-Versionen
                context.onSuspendCard()
            return (True, "ok")
    except Exception as e:
        print("[Kanji-Wortindex]", e)
    return (True, "no")


gui_hooks.webview_did_receive_js_message.append(_on_js)
gui_hooks.profile_did_open.append(lambda *a: _schedule())
gui_hooks.sync_will_start.append(lambda *a: rebuild())
gui_hooks.add_cards_did_add_note.append(_schedule)
gui_hooks.operation_did_execute.append(_on_op)
_menu()
