"""Vocabulaire — les mots affichés viennent d'un seul endroit (chantier 10).

Le plugin ne lisait le lexique du dépôt **dans aucun fichier** : chaque
message écrivait son propre vocabulaire, et le même objet s'appelait
« tige », « piste » ou « track » selon le fichier.

Ce module ne réécrit rien : il lit `specs/data/lexique.json`, embarqué dans
le paquet pour que le plugin l'ait sous la main une fois installé dans QGIS.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

FICHIER = Path(__file__).resolve().parent / "lexique.json"


class MotInterdit(ValueError):
    """Un mot banni de l'interface (R-17)."""


_DONNEES = None


def _donnees():
    global _DONNEES
    if _DONNEES is None:
        _DONNEES = json.loads(FICHIER.read_text(encoding="utf-8"))
    return _DONNEES


def charger():
    """Charge le lexique une fois et le garde. Explicite, pour les écrans."""
    return _donnees()


def mot(cle, champ="label"):
    """Le mot à afficher pour un objet nommé du lexique."""
    return _donnees()["types_donnees"][cle][champ]


def module(cle):
    return _donnees()["modules"][cle]


def verifie(texte):
    """Refuse un mot du code à l'écran, sur des mots entiers (R-17)."""
    bas = str(texte).lower()
    for banni in _donnees()["interdits"]:
        if re.search(rf"\b{re.escape(banni)}\b", bas):
            raise MotInterdit(
                f"« {texte} » contient « {banni} » : dites la même chose "
                "avec un mot que tout le monde connaît")
    return texte
