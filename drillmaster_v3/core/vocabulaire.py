"""Chantier 10 — un mot par chose, et le mot est dans le code qui affiche.

Le défaut mesuré : le lexique du dépôt n'était lu par **aucun** fichier du
plugin, et le même objet s'écrivait de trois façons à l'écran
(`forage` / `trou` / `hole`, `teneur` / `analyse` / `assay`, `piste` /
`voie`). Une règle qu'on récite ne tient pas ; un mot qu'un test vérifie, si.

    from drillmaster_v3.core.vocabulaire import mot, remplace, verifie

    mot("teneur")            # « Teneurs »
    mot("teneur", "unite")   # « analyses »
    remplace("Afficher azimut / dip")   # « Afficher azimut / pendage »
    verifie("Ouvrir le projet en EPSG:32629")   # lève MotInterdit

Ce module ne réécrit pas `specs/data/lexique.json` : il le **lit**, et il
ajoute la seule chose qui manquait — la forme que le plugin emploie pour
parler de ses objets, avec ses variantes à corriger.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
FICHIER = RACINE / "specs" / "data" / "lexique.json"


class MotInterdit(ValueError):
    """Le mot est banni de l'interface (R-17) : il ne s'affiche pas."""


# ── un mot par chose ────────────────────────────────────────────────
# clé interne → le mot que l'utilisateur lit. Le choix est documenté :
# on garde le mot que le géologue emploie quand il parle à un confrère.
MOTS = {
    "forage": {"label": "Forage", "pluriel": "Forages"},
    "teneur": {"label": "Teneur", "pluriel": "Teneurs", "unite": "analyses"},
    "coupe": {"label": "Coupe", "pluriel": "Coupes"},
    "collet": {"label": "Collet", "pluriel": "Collets"},
    "pendage": {"label": "Pendage", "pluriel": "Pendages",
                "azimut": "Azimut"},
    "piste": {"label": "Piste", "pluriel": "Pistes"},
    "profil": {"label": "Profil d'ouvrage", "pluriel": "Profils d'ouvrage"},
    "intervalle": {"label": "Intervalle", "pluriel": "Intervalles"},
    "echelle": {"label": "Échelle", "pluriel": "Échelles"},
    "legende": {"label": "Légende", "pluriel": "Légendes"},
    "export": {"label": "Export", "pluriel": "Exports"},
}

# variante interdite → mot retenu. Ce sont les mots anglais et les
# doublons qui se glissent dans les textes affichés.
VARIANTES = {
    "hole": "forage",
    "holes": "forages",
    "assay": "teneur",
    "assays": "teneurs",
    "grade": "teneur",
    "grades": "teneurs",
    "collar": "collet",
    "collars": "collets",
    "dip": "pendage",
    "dip direction": "azimut du pendage",
    "dip_direction": "azimut du pendage",
    "track": "piste",
    "tracks": "pistes",
    "voie": "piste",
    "voies": "pistes",
    "section": "coupe",
}

# Mots qui ont un AUTRE sens : on ne les remplace pas. « profil » dans
# « profil d'affichage », « analyse » pour les valeurs, « trou » dans
# « trou de forage », « section » comme nom de classe passé à l'affichage.
NE_PAS_TOUCHER = ("profil d'affichage", "profil topographique", "analyse",
                  "trou", "sectionwidget")


def _donnees():
    return json.loads(FICHIER.read_text(encoding="utf-8"))


def mot(cle, forme="label"):
    """Le mot à afficher, dans la forme demandée."""
    if cle not in MOTS:
        raise KeyError(f"« {cle} » n'est pas un objet nommé de l'interface")
    table = MOTS[cle]
    if forme not in table:
        raise KeyError(f"« {cle} » n'a pas de forme « {forme} »")
    return table[forme]


def objets():
    """La liste des objets nommés — la même que vérifie le test."""
    return tuple(MOTS)


def remplace(texte):
    """Corrige les variantes d'un texte affiché, sans toucher aux autres sens.

    « Afficher azimut / dip » → « Afficher azimut / pendage »
    « Profils d'affichage… »  → inchangé (autre sens)
    """
    if not texte:
        return texte
    bas = texte.lower()
    if any(mot_protege in bas for mot_protege in NE_PAS_TOUCHER):
        return texte
    sortie = texte
    for variante, retenu in sorted(VARIANTES.items(),
                                   key=lambda kv: -len(kv[0])):
        if variante == "section":
            continue          # trop ambigu : traité au cas par cas
        sortie = re.sub(rf"\b{re.escape(variante)}\b", retenu, sortie,
                        flags=re.IGNORECASE)
    return sortie


def variantes_trouvees(texte):
    """Les variantes à corriger dans un texte. Vide = le mot est juste."""
    bas = (texte or "").lower()
    if any(p in bas for p in NE_PAS_TOUCHER):
        return []
    return [v for v in VARIANTES if v != "section"
            and re.search(rf"\b{re.escape(v)}\b", bas)]


def verifie(texte):
    """Refuse un mot banni (R-17), avec la raison en clair."""
    bas = str(texte).lower()
    for banni in _donnees()["interdits"]:
        if re.search(rf"\b{re.escape(banni)}\b", bas):
            raise MotInterdit(
                f"« {texte} » contient « {banni} », banni de l'interface : "
                "dites la même chose avec un mot que tout le monde connaît")
    return texte


def lisent_le_lexique():
    """Le défaut mesuré : combien de fichiers du plugin lisent ce lexique."""
    import ast
    racine = RACINE / "DrillMaster"
    n = 0
    for f in racine.rglob("*.py"):
        texte = f.read_text(encoding="utf-8", errors="ignore")
        try:
            arbre = ast.parse(texte)
        except SyntaxError:
            continue
        for n_noeud in ast.walk(arbre):
            if isinstance(n_noeud, (ast.Import, ast.ImportFrom)):
                nom = ast.unparse(n_noeud)
                if "lexique" in nom.lower() or "vocabulaire" in nom.lower():
                    n += 1
                    break
    return n
