"""v2.9.258 — Traduction des messages de validation détaillés.

Le panneau groupé de l'étape 2 n'affiche déjà que des libellés courts
traduits (contexte ``ValidationMessages``).  L'éditeur CSV, lui, affichait
encore les messages bruts produits par ``core.validation`` — français,
avec les suggestions françaises — même en interface anglaise.

Ce module rationalise cette traduction à l'affichage : en français le
message source complet est conservé tel quel ; en anglais la ligne et
l'infobulle utilisent le libellé court du code (déjà couvert par
``i18n/drillmaster_en.ts``) puis la position réelle de la cellule.

Règles :
- aucune chaîne dépendante du nom de fichier ;
- rien n'est tronqué silencieusement : la position (ligne CSV) est
  toujours annoncée en anglais ;
- les suggestions françaises ne sont jamais mélangées à une interface
  anglaise.
"""
from __future__ import annotations

from typing import Optional

from ..core.i18n import load_language_setting
from ..core.validation_groups import GROUP_LABELS

_SEVERITY_LABELS = {
    "error": "Erreur",
    "warning": "Avertissement",
    "info": "Information",
}


def validation_english_mode() -> bool:
    """Vrai si l'interface anglaise est active (QSettings)."""
    return load_language_setting() == "en"


def validation_translate(text: str) -> str:
    """Traduit un libellé via le contexte ``ValidationMessages``."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("ValidationMessages", text)


def validation_label(code: Optional[str], severity: str = "") -> str:
    """Libellé court stable d'un code de validation.

    ``GROUP_LABELS`` porte le texte source français ; la traduction se
    fait ici.  Les messages sans code (hérités) retombent sur le libellé
    de sévérité, jamais sur le message source français en anglais.
    """
    label = GROUP_LABELS.get(code or "", "")
    if not label:
        label = _SEVERITY_LABELS.get(severity, code or "Validation")
    if validation_english_mode():
        return validation_translate(label) or label
    return label


def validation_issue_text(payload: dict) -> str:
    """Texte d'une ligne de problème pour la liste de l'éditeur CSV.

    ``payload`` est le dict renvoyé par ``ValidationIssue.to_dict()``
    (code, message, suggestion, row, column, locations…).
    """
    severity = payload.get("severity", "info")
    label = validation_label(payload.get("code"), severity)
    row = _first_row(payload)
    if row is None:
        return label
    if validation_english_mode():
        line_label = validation_translate("Ligne CSV {}") or "CSV line {}"
        return f"{label} — {line_label.format(row + 2)}"
    # Français : le message source est riche (ligne/forage/valeur) ; on
    # le conserve, en ajoutant la ligne uniquement si le message n'en
    # parle déjà pas clairement.
    return f"{payload.get('message', label)}"


def validation_issue_tooltip(payload: dict) -> str:
    """Infobulle de cellule : anglais court, français détaillé.

    La suggestion française n'est jamais ajoutée en anglais (elle
    rejoindrait les messages souches non traduits).
    """
    label = validation_label(payload.get("code"), payload.get("severity"))
    row = _first_row(payload)
    suffix = ""
    if row is not None and validation_english_mode():
        line_label = validation_translate("Ligne CSV {}") or "CSV line {}"
        suffix = f"\n{line_label.format(row + 2)}"
    if validation_english_mode():
        return f"{label}{suffix}"
    message = payload.get("message", label) or label
    suggestion = payload.get("suggestion", "") or ""
    if suggestion:
        prefix = validation_translate("Suggestion : {}")
        message = (f"{message}\n{prefix.format(suggestion)}"
                   if prefix != "Suggestion : {}"
                   else f"{message}\nSuggestion : {suggestion}")
    return message


def _first_row(payload: dict) -> Optional[int]:
    locations = payload.get("locations") or []
    if locations:
        first = locations[0]
        row = first.get("row") if isinstance(first, dict) else None
        if row is not None:
            return row
    row = payload.get("row")
    return row if isinstance(row, int) else None
