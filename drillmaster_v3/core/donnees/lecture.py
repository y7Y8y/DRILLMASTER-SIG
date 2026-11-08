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
    "date": ("date", "date_fin", "fin", "end_date", "datefin"),
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


@dataclass(frozen=True)
class Colonne:
    """Une colonne du fichier, telle qu'elle sera montrée avant l'import."""
    nom: str
    exemple: str
    role: str = ""              # « identifiant », « longitude »… vide = à confirmer

    @property
    def reconnue(self):
        return bool(self.role)


@dataclass
class Lecture:
    """Résultat d'une lecture : des données ET des messages. Jamais l'un sans l'autre."""
    colliers: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    journal: dict = field(default_factory=dict)
    colonnes: list = field(default_factory=list)
    verifications: object = None

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
            # R-17 : on ne montre jamais le nom d'un encodage. L'utilisateur
            # n'a pas à savoir ce qu'est « utf-8-sig » ; il doit savoir que
            # ses accents étaient abîmés et qu'ils sont rétablis.
            messages.append(avertissement(
                "Les accents du fichier étaient abîmés",
                "ils ont été rétablis à la lecture ; le fichier d'origine "
                "n'a pas été modifié",
                (nom,), ("réenregistrer le fichier avec ses accents",),
                f"{nom}"))
        return texte, codec, messages
    raise ValueError("fichier illisible")


def _detecte_separateur(entete):
    compte = {sep: entete.count(sep) for sep in (";", "\t", ",")}
    return max(compte, key=compte.get) if max(compte.values()) else ","


def _colonne_nombre(valeur, decimal_virgule=None):
    """Cette colonne contient-elle des nombres ? On regarde 20 valeurs, pas 1."""
    essais = [v for v in valeur if (v or "").strip()][:20]
    if not essais:
        return False
    return all(_nombre(v, decimal_virgule) is not None for v in essais)


def _colonnes_hostiles(entetes):
    """Les noms de colonnes qui contiennent le séparateur : on le dit, on ne devine pas."""
    return [e for e in entetes if any(sep in (e or "") for sep in (";", "\t"))]


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

    # ce que l'écran d'import montre : chaque colonne, son exemple, son rôle.
    # Une colonne non reconnue n'est pas devinée : elle est dite « à confirmer ».
    SENS = {"id": "identifiant du forage", "x": "position est",
            "y": "position nord", "z": "altitude du collet",
            "profondeur": "profondeur finale", "date": "date de fin"}
    role_de = {no: SENS[c] for c, no in index.items()}
    premiere = next(lecteur, None) or []
    lec.colonnes = [
        Colonne(nom=(brut or "").strip(),
                exemple=(premiere[no].strip() if no < len(premiere) else ""),
                role=role_de.get(no, ""))
        for no, brut in enumerate(entetes)]

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
    debut = 2 if premiere else 3
    lignes_donnees = [premiere] + list(lecteur) if premiere else list(lecteur)
    for no, ligne in enumerate(lignes_donnees, start=2):
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

    # les cinq contrôles faits AVANT de demander une décision (écran 19)
    lec.verifications = verifie(
        entetes, lignes_donnees, index,
        {i for i, lst in vus.items() if len(lst) > 1})

    if not lec.colliers:
        lec.messages.append(blocage(
            "Aucun forage lisible",
            "toutes les lignes ont été écartées : rien ne peut être dessiné",
            (nom,), ("vérifier le format du fichier",), nom))

    lec.messages.append(information(
        f"{len(lec.colliers)} forages lus",
        f"lecture terminée, séparateur « {sep} », aucun fichier modifié", nom))
    return lec


# ── les contrôles faits AVANT de demander une décision (écran 19) ─────
# Une décision ne porte que sur ce qui reste. Ces cinq contrôles sont
# calculés, pas racontés : l'écran montre leur résultat, pas une promesse.
CONTROLES = (
    "identifiants", "coordonnees", "profondeurs", "analyses", "dates",
)


@dataclass(frozen=True)
class Controle:
    cle: str
    libelle: str
    reussi: int = 0
    total: int = 0

    @property
    def etat(self):
        if self.total == 0:
            return "info"          # rien à vérifier : on le dit
        if self.reussi == self.total:
            return "ok"
        return "blocage" if self.reussi == 0 else "avertissement"

    def phrase(self):
        return f"{self.reussi} sur {self.total}"


@dataclass
class Verifications:
    """Le résultat des cinq contrôles, avec le cas où l'on ne sait pas."""
    lignes: int = 0
    colonnes: tuple = ()
    colonnes_reconnues: int = 0
    controles: tuple = ()

    def avant_de_demander(self):
        """Ce qui bloque encore, en clair : le reste est vérifié, donc pas à décider."""
        return tuple(c.libelle for c in self.controles
                     if c.etat in ("blocage", "avertissement"))


def verifie(entetes, lignes, index, doublons, analyses=None) -> Verifications:
    """Les cinq contrôles de l'écran 19, calculés sur les lignes réellement lues.

    ``lignes``   : liste de listes (les valeurs brutes du fichier)
    ``index``    : rôle → numéro de colonne
    ``doublons`` : identifiants vus plusieurs fois
    ``analyses`` : liste de (identifiant de forage, valeur) ou None
    """
    def val(ligne, role):
        no = index.get(role)
        if no is None or no >= len(ligne):
            return ""
        return ligne[no]

    ids = [val(l, "id").strip() for l in lignes]
    connus = {i for i in ids if i}

    ctrl = []
    # 1 · identifiants uniques
    ctrl.append(Controle(
        "identifiants", "Identifiants uniques",
        len(connus), len(lignes)))

    # 2 · coordonnées lisibles et dans une emprise plausible
    lisibles = 0
    for l in lignes:
        x = _nombre(val(l, "x"))
        y = _nombre(val(l, "y"))
        if x is None or y is None:
            continue
        if abs(x) > 1e7 or abs(y) > 1e7:      # hors de toute emprise terrestre
            continue
        lisibles += 1
    ctrl.append(Controle("coordonnees", "Coordonnées dans une emprise plausible",
                         lisibles, len(lignes)))

    # 3 · profondeurs cohérentes avec les coordonnées
    if "profondeur" in index:
        ok = sum(1 for l in lignes
                 if (_nombre(val(l, "profondeur")) or 0) > 0
                 and _nombre(val(l, "x")) is not None)
        ctrl.append(Controle("profondeurs",
                             "Profondeurs renseignées pour chaque forage",
                             ok, len(lignes)))
    else:
        ctrl.append(Controle("profondeurs",
                             "Profondeurs renseignées pour chaque forage",
                             0, 0))

    # 4 · chaque analyse est rattachée à un forage connu
    if analyses:
        rattachees = sum(1 for ident, _ in analyses if ident in connus)
        ctrl.append(Controle("analyses",
                             "Analyses rattachées à un forage connu",
                             rattachees, len(analyses)))
    else:
        ctrl.append(Controle("analyses",
                             "Analyses rattachées à un forage connu", 0, 0))

    # 5 · dates plausibles (année entre 1900 et aujourd'hui + 1)
    no_date = index.get("date")
    if no_date is None:
        ctrl.append(Controle("dates", "Dates de fin plausibles", 0, 0))
    else:
        bonnes = 0
        for l in lignes:
            brut = val(l, "date").strip()
            annee = brut[:4]
            if len(annee) == 4 and annee.isdigit() and 1900 <= int(annee) <= 2100:
                bonnes += 1
        ctrl.append(Controle("dates", "Dates de fin plausibles", bonnes, len(lignes)))

    reconnues = sum(1 for role in index)
    return Verifications(lignes=len(lignes), colonnes=tuple(entetes),
                         colonnes_reconnues=reconnues,
                         controles=tuple(ctrl))
