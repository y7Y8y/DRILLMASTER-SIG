"""Lecture des fichiers sources — le comportement, pas la promesse.

Traite réellement : encodage, séparateur, décimale à virgule, colonnes
renommées, doublons d'identifiant, fichier vide. Chaque anomalie produit un
`Message` du niveau qui convient (R-20). Aucun fichier n'est jamais modifié.
"""
from __future__ import annotations

import csv
import hashlib
import io
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..messages import (Niveau, Message, avertissement, blocage, information)

# alias de colonnes acceptés, en minuscules, sans accents
ALIAS = {
    "id": ("id", "holeid", "hole_id", "forage", "identifiant", "code",
           "bhid", "drillhole"),
    "x": ("x", "east", "est", "easting", "coord_x", "xcoord"),
    "y": ("y", "north", "nord", "northing", "coord_y", "ycoord"),
    "z": ("z", "elev", "elevation", "altitude", "rl", "zcoord"),
    "profondeur": ("profondeur", "depth", "prof", "profondeur_m", "eoh",
                   "final_depth", "to"),
}


def _sans_accent(texte):
    table = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
    return texte.strip().lower().translate(table)


@dataclass
class Forage:
    id: str
    x: float
    y: float
    z: float
    profondeur: float = 0.0
    ligne_source: int = 0


@dataclass
class Lecture:
    """Résultat d'une lecture : des données ET des messages. Jamais l'un sans l'autre."""
    colliers: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    journal: dict = field(default_factory=dict)

    @property
    def bloquant(self):
        return any(m.niveau is Niveau.BLOCAGE for m in self.messages)

    def resume(self):
        return {
            "forages": len(self.colliers),
            "messages": len(self.messages),
            "bloquant": self.bloquant,
            "journal": self.journal,
        }


def _decode(octets, nom):
    """R-17 : on ne parle pas d'encodage à l'utilisateur, on dit ce qui a été réparé."""
    messages = []
    for codec, reparation in (("utf-8-sig", None), ("cp1252", "accents réparés")):
        try:
            texte = octets.decode(codec)
        except UnicodeDecodeError:
            continue
        if reparation:
            messages.append(avertissement(
                "Le fichier n'était pas en UTF-8",
                "les accents ont été rétablis à la lecture ; le fichier "
                "d'origine n'a pas été modifié",
                (nom,), ("réenregistrer le fichier en UTF-8",),
                f"{nom}"))
        return texte, codec, messages
    raise ValueError("fichier illisible")


def _detecte_separateur(entete):
    compte = {sep: entete.count(sep) for sep in (";", "\t", ",")}
    return max(compte, key=compte.get) if max(compte.values()) else ","


def _nombre(brut, decimal_virgule=False):
    """Décimale à virgule OU à point : on regarde la valeur, pas le fichier.

    « 512.340,2 » → 512340.2 · « 512340.2 » → 512340.2 · « 512,340.2 » → 512340.2
    Une valeur illisible renvoie None : elle n'est jamais devinée.
    """
    t = (brut or "").strip().replace("\u202f", "").replace(" ", "")
    if not t or t.lower() in ("nd", "na", "n/a", "-", "nan", ""):
        return None
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):      # virgule décimale, points = milliers
            t = t.replace(".", "").replace(",", ".")
        else:                                # point décimal, virgules = milliers
            t = t.replace(",", "")
    elif "," in t:
        partie = t.split(",")
        if len(partie) == 2 and len(partie[1]) != 3:
            t = t.replace(",", ".")          # 512,25 → décimale
        elif len(partie) == 2 and len(partie[1]) == 3:
            t = t.replace(",", "")           # 512,340 → milliers
        else:
            t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def lit_collets(chemin, texte=None) -> Lecture:
    chemin = Path(chemin)
    octets = texte.encode("utf-8") if texte is not None else chemin.read_bytes()
    nom = chemin.name
    lec = Lecture()
    lec.journal["empreinte_source"] = hashlib.sha256(octets).hexdigest()[:16]

    if not octets.strip():
        lec.messages.append(blocage(
            "Le fichier est vide",
            "aucune ligne à lire : le projet ne peut pas démarrer avec ce fichier",
            (nom,), ("choisir un autre fichier", "vérifier l'export de la base"),
            nom))
        return lec

    texte, codec, messages = _decode(octets, nom)
    lec.messages.extend(messages)
    lec.journal["encodage"] = codec

    lignes = [l for l in texte.splitlines() if l.strip()]
    entete = lignes[0]
    sep = _detecte_separateur(entete)
    lec.journal["separateur"] = sep
    if sep != ";":
        lec.messages.append(information(
            "Séparateur reconnu",
            f"les colonnes sont séparées par « {sep} » ; la lecture en tient compte",
            nom))

    lecteur = csv.reader(io.StringIO("\n".join(lignes)), delimiter=sep)
    entetes = next(lecteur)
    index = {}
    for no, brut in enumerate(entetes):
        cle = _sans_accent(brut)
        for cible, alias in ALIAS.items():
            if cle in alias and cible not in index:
                index[cible] = no

    manquantes = [c for c in ("id", "x", "y") if c not in index]
    if manquantes:
        lec.messages.append(blocage(
            "Colonnes indispensables absentes",
            "sans identifiant ni coordonnées, un forage ne peut pas être placé "
            "sur la coupe", manquantes,
            ("renommer les colonnes dans le fichier", "choisir la correspondance à la main"),
            nom))
        return lec

    decimal_virgule = sep != ","
    vus = defaultdict(list)
    for no, ligne in enumerate(lecteur, start=2):
        if len(ligne) <= max(index.values()):
            continue
        try:
            f = Forage(
                id=ligne[index["id"]].strip(),
                x=_nombre(ligne[index["x"]], decimal_virgule),
                y=_nombre(ligne[index["y"]], decimal_virgule),
                z=_nombre(ligne[index.get("z", index["y"])], decimal_virgule),
                profondeur=_nombre(ligne[index["profondeur"]], decimal_virgule)
                if "profondeur" in index else 0.0,
                ligne_source=no,
            )
        except (ValueError, TypeError):
            lec.messages.append(avertissement(
                f"Ligne {no} illisible",
                "une valeur numérique est mal écrite : la ligne est ignorée, "
                "elle n'est pas corrigée",
                (f"ligne {no}",), ("corriger la valeur dans le fichier",), nom))
            continue
        if f.x is None or f.y is None:
            lec.messages.append(avertissement(
                f"Coordonnées absentes ligne {no}",
                "le forage ne peut pas être placé sur la coupe",
                (f.id or f"ligne {no}",), ("compléter les coordonnées",), nom))
            continue
        vus[f.id].append(f)
        lec.colliers.append(f)

    # doublons : même identifiant (le cas réel du projet Issia)
    for ident, liste in vus.items():
        if len(liste) > 1:
            memes = all((f.x, f.y) == (liste[0].x, liste[0].y) for f in liste)
            lignes_ = tuple(f"ligne {f.ligne_source}" for f in liste)
            lec.messages.append(blocage(
                "Deux forages portent le même nom" if memes
                else "Un identifiant est utilisé deux fois",
                "la trajectoire de ce forage deviendrait ambiguë : la coupe "
                "afficherait un forage fusionné, faux en profondeur",
                (ident,) + lignes_,
                ("corriger l'identifiant dans le fichier",
                 "fusionner les deux lignes" if memes else "exclure un des forages",
                 "exclure un des deux forages"),
                f"{nom} · {', '.join(lignes_)}"))

    if not lec.colliers:
        lec.messages.append(blocage(
            "Aucun forage lisible",
            "toutes les lignes ont été écartées : rien ne peut être dessiné",
            (nom,), ("vérifier le format du fichier",), nom))

    lec.messages.append(information(
        f"{len(lec.colliers)} forages lus",
        f"lecture terminée en {codec}, séparateur « {sep} », "
        f"aucun fichier modifié", nom))
    return lec
