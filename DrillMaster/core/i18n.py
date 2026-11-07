"""DrillMaster — Infrastructure i18n (Lot 1a du plan langue, v2.9.227).

**Approche** : `self.tr()` standard (contexte = nom de la classe)
partout dans les sources — compatible Qt Linguist.  Les traductions
vivent dans des fichiers **.ts** (le format XML de Qt Linguist :
traduisibles dans Linguist, diffables dans Git) et sont lus
DIRECTEMENT au chargement par un QTranslator custom — **aucune
compilation lrelease nécessaire** dans la chaîne de l'utilisateur
(les .qm restent possibles plus tard sans toucher au code : les
appels tr() sont identiques).

Règles du plan (docs/PLAN_LANGUE.md) :
- langue mémorisée dans QSettings ("DrillMaster/language"),
  JAMAIS demandée au démarrage ;
- français = langue source (l'absence de traduction affiche le
  français) ;
- vocabulaire verrouillé : forage = drillhole, coupe = cross-section
  (titres) / section (libellés courts), barrette = tick,
  Référentiel = Reference (docs/DICO_TERMES_FR_EN.md).

Pur Python pour le PARSING (testable sans Qt) ; la classe
TsTranslator nécessite Qt (importée uniquement par l'UI).
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N_DIR = os.path.join(REPO, "i18n")

# langues supportées (l'ordre = l'ordre du combo)
LANGUAGES = ("fr", "en")
LANGUAGE_LABELS = {"fr": "Français", "en": "English"}
DEFAULT_LANGUAGE = "fr"


def ts_path(language: str) -> str:
    """Chemin du fichier .ts d'une langue."""
    return os.path.join(I18N_DIR, f"drillmaster_{language}.ts")


def parse_ts(path: str) -> dict:
    """Parse un fichier .ts Qt Linguist → {(contexte, source):
    traduction}.  Pur Python (aucun Qt) — testable seul.

    Une traduction vide, absente ou marquée « unfinished » est
    IGNORÉE (le français source s'affiche — jamais de texte vide).
    """
    if not path or not os.path.isfile(path):
        return {}
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return {}
    out = {}
    root = tree.getroot()
    for context in root.iter("context"):
        name = context.findtext("name") or ""
        for message in context.iter("message"):
            source = message.findtext("source")
            trans = message.find("translation")
            if source is None or trans is None:
                continue
            if trans.get("type") in ("unfinished", "obsolete"):
                continue
            # v2.9.248 — le texte est préservé TEL QUEL (les gabarits
            # peuvent Porter des espaces de tête : «  |  Buffer : ±{} »)
            # — seul le test de vacuité utilise strip().
            text = trans.text or ""
            if text.strip():
                out[(name, source)] = text
    return out


def available_languages() -> list:
    """Langues qui ont un fichier .ts présent."""
    return [lang for lang in LANGUAGES if os.path.isfile(ts_path(lang))]


def load_language_setting() -> str:
    """Langue mémorisée (QSettings), avec repli honnête :
    QSettings indisponible (tests) → français."""
    try:
        from qgis.PyQt.QtCore import QSettings
        value = str(QSettings().value("DrillMaster/language",
                                      DEFAULT_LANGUAGE) or "")
        return value if value in LANGUAGES else DEFAULT_LANGUAGE
    except Exception as _exc:
        # SILENCE JUSTIFIÉ (v2.9.227) : hors QGIS (tests), le
        # français est le défaut — journalisé pour l'audit.
        from .diagnostics import log_swallowed
        log_swallowed("i18n : lecture de la langue (français "
                      "conservé)", _exc)
        return DEFAULT_LANGUAGE


def save_language_setting(language: str) -> None:
    try:
        from qgis.PyQt.QtCore import QSettings
        QSettings().setValue("DrillMaster/language", str(language))
    except Exception as _exc:
        # SILENCE JUSTIFIÉ (v2.9.227) : hors QGIS (tests), rien à
        # mémoriser — journalisé pour l'audit.
        from .diagnostics import log_swallowed
        log_swallowed("i18n : mémorisation de la langue "
                      "(choix non conservé)", _exc)


def install_translator(language: str, parent=None):
    """Installe le traducteur de la langue sur l'application.

    Retourne (translator, ok) : translator=None si la langue est le
    français (source — aucun traducteur nécessaire) ou si Qt est
    absent.  NE LÈVE JAMAIS : sans traduction, l'UI reste en
    français.
    """
    if language not in LANGUAGES or language == DEFAULT_LANGUAGE:
        return None, False
    try:
        from qgis.PyQt.QtCore import QCoreApplication, QTranslator

        class TsTranslator(QTranslator):
            """QTranslator qui lit un .ts DIRECTEMENT (pas de .qm) :
            translate() retourne '' (source) quand il ne connaît
            pas — le comportement standard de Qt."""

            def __init__(self, mapping, parent=None):
                super().__init__(parent)
                self._map = dict(mapping or {})

            def translate(self, context, sourceText,
                          disambiguation=None, n=-1):
                # RESTREINT (pas except Exception large) : méthode
                # virtuelle Qt appelée à CHAQUE texte — aucune
                # journalisation possible ici.
                # v2.9.255 — repli `None` (PAS `""`): avec PyQt/QGIS,
                # un traducteur installé qui retourne "" est traité
                # comme une VRAIE traduction vide et BLANCHIT les
                # textes inconnus de toute l'application (menus,
                # boutons, dialogues de QGIS).  `None` (rien trouvé)
                # laisse Qt reprendre le texte source / les autres
                # traducteurs — l'interface n'est plus jamais vidée.
                return self._map.get((str(context), str(sourceText)),
                                     None)

        mapping = parse_ts(ts_path(language))
        if not mapping:
            return None, False
        translator = TsTranslator(mapping, parent)
        QCoreApplication.installTranslator(translator)
        return translator, True
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed(f"i18n : installation du traducteur "
                      f"{language!r} (interface en français)", _exc)
        return None, False


# traducteur courant (module) — un seul à la fois
_current_translator = None


def set_language(language: str, parent=None) -> bool:
    """v2.9.227 — bascule la langue de TOUTE l'application : retire
    l'éventuel traducteur courant, installe celui de la langue.
    Retourne True si un traducteur est actif (langue ≠ français).
    NE LÈVE JAMAIS."""
    global _current_translator
    try:
        if _current_translator is not None:
            remove_translator(_current_translator)
            _current_translator = None
        translator, _ok = install_translator(language, parent=parent)
        _current_translator = translator
        return translator is not None
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed(f"i18n : bascule vers {language!r} "
                      "(français conservé)", _exc)
        return False


def remove_translator(translator) -> None:
    """Retire proprement un traducteur installé."""
    if translator is None:
        return
    try:
        from qgis.PyQt.QtCore import QCoreApplication
        QCoreApplication.removeTranslator(translator)
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("i18n : retrait du traducteur (ignoré)", _exc)
