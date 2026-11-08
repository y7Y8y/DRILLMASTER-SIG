"""Chantier 7 — les quatre écrans neufs confrontés au code.

Une maquette n'est pas une promesse tenue tant qu'on ne l'a pas confrontée
au code réel. Ce module fait la confrontation, écran par écran, et rend un
**écart** là où la maquette montre un comportement que rien ne tient.

    from drillmaster_v3.core.ecrans import ECRANS, ecarts
    for e in ecarts(chiffres=fiche_source(cas).as_dict()):
        print(e)        # ce que la maquette montre, ce que le code fait

Trois états, jamais deux :

- ``tenu``      — le comportement existe et un cas réel le prouve ;
- ``bloque``    — le comportement est **explicitement** refusé, avec sa raison ;
- ``sans_code`` — la maquette promet, le code ne sait pas encore : c'est un
  travail à faire, numéroté, jamais un mensonge.

R-17 : aucun mot du code ne sort d'ici. Les écarts parlent de « fichiers
lus », de « colonnes », de « forage » — jamais de séparateur interne.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class FicheSource:
    """Ce que l'écran 18 affiche après avoir lu un fichier — des chiffres."""
    nom: str = ""
    forages: int = 0
    lignes: int = 0
    colonnes: int = 0
    colonnes_reconnues: int = 0
    lignes_illisibles: int = 0
    doublons: tuple = ()
    bloquant: bool = False
    # ce que le fichier ne peut pas fournir : c'est dit, jamais vide.
    # Liste lue dans les données de référence, pas écrite ici.
    types_absents: tuple = ()

    def as_dict(self):
        return {
            "nom": self.nom, "forages": self.forages, "lignes": self.lignes,
            "colonnes": self.colonnes,
            "colonnes_reconnues": self.colonnes_reconnues,
            "lignes_illisibles": self.lignes_illisibles,
            "doublons": list(self.doublons), "bloquant": self.bloquant,
            "types_absents": list(self.types_absents),
        }


@dataclass
class Ecran:
    numero: int
    nom: str
    maquette: str                       # la planche qui le montre
    promesses: list = field(default_factory=list)

    def tenues(self):
        return [p for p in self.promesses if p.etat == "tenu"]

    def ecarts(self, contexte=None):
        return [p for p in self.promesses
                if p.etat != "tenu" and (contexte is None or p.verifie(contexte))]


@dataclass
class Promesse:
    phrase: str                         # ce que l'écran montre, en français
    etat: str                           # tenu | bloque | sans_code
    preuve: str = ""                    # fichier:rôle, ou le cas de test
    raison: str = ""                    # pour « bloque » uniquement
    _verifie: Callable = None

    def verifie(self, contexte) -> bool:
        if self._verifie is None:
            return True
        return bool(self._verifie(contexte))


# ── ce qui tient : vérifié par les tests du noyau ────────────────────
SOURCES = {
    "lecture": "drillmaster_v3/core/donnees/lecture.py",
    "projet": "drillmaster_v3/projet.py",
    "messages": "drillmaster_v3/core/messages.py",
    "pistes": "drillmaster_v3/core/tracks.py",
    "gestes": "drillmaster_v3/core/gestes.py",
}


def _doublon_bloque(ctx):
    """Un identifiant en double arrête la suite : c'est un blocage, pas un avis."""
    return ctx.get("doublons") and ctx.get("bloquant")


def _rien_ecrit(ctx):
    """Le fichier d'origine n'est jamais ouvert en écriture (empreinte comparée)."""
    return ctx.get("empreinte_intacte", True)


ECRANS = [
    Ecran(18, "Import", "maquettes/18_import.png", [
        Promesse("déposer un fichier, voir ce qu'il contient, décider",
                 "tenu", "lecture.lit_collets"),
        Promesse("les chiffres affichés viennent de la lecture, pas d'une estimation",
                 "tenu", "lecture.Lecture.resume"),
        Promesse("une ligne illisible est comptée et ignorée, jamais corrigée",
                 "tenu", "lecture.lit_collets · avertissement ligne N"),
        Promesse("le fichier d'origine n'est jamais modifié",
                 "tenu", "test_fonctionnel.Cas15", _verifie=_rien_ecrit),
        Promesse("un type de données absent est affiché absent, jamais vide et silencieux",
                 "tenu", "projet_issia.par_piste → état « non fourni »"),
        Promesse("les types de données sont nommés, chacun avec son état "
                 "« fourni / non fourni »",
                 "tenu", "specs/data/projet_issia.json · lu par les écrans"),
        Promesse("12 types de données lus à l'import",
                 "sans_code",
                 "seuls les colliers ont un lecteur : les 11 autres types "
                 "demandent chacun leur lecture"),
        Promesse("un fichier tableur (CSV, TXT, point-virgule ou virgule) "
                 "est lu, décimale et accents compris",
                 "tenu", "lecture._decode · lecture._nombre · lecture._detecte_separateur"),
        Promesse("Excel, LAS et Shapefile sont lus",
                 "sans_code",
                 "aucun lecteur pour ces trois formats : la lecture ne lit que "
                 "du texte séparé"),
    ]),
    Ecran(19, "Blocage", "maquettes/19_blocage.png", [
        Promesse("un identifiant en double arrête l'étape suivante",
                 "tenu", "lecture.lit_collets · blocage", _verifie=_doublon_bloque),
        Promesse("un blocage propose trois sorties, jamais une seule",
                 "tenu", "messages.blocage (R-22 : au moins deux)"),
        Promesse("les deux lignes fautives sont prises une par une, avec "
                 "leurs valeurs, avant toute décision",
                 "tenu", "lecture.Lecture.colonnes + message nommant les lignes"),
        Promesse("les colonnes du fichier sont montrées une par une, "
                 "avec un exemple et leur sens probable",
                 "tenu", "lecture.Lecture.colonnes · Colonne(nom, exemple, rôle)"),
        Promesse("un motif est obligatoire pour enregistrer la décision",
                 "tenu", "projet.exclut · ValueError si motif vide"),
        Promesse("la décision est réversible et le motif est conservé",
                 "tenu", "projet.reintegre"),
        Promesse("« Qui décide » est affiché et enregistré à côté de la décision",
                 "tenu", "projet.exclut(par=…) · projet.decisions"),
        Promesse("« DrillMaster a déjà vérifié » : 5 contrôles avant de vous "
                 "demander de décider",
                 "tenu", "lecture.verifie · identifiants, coordonnées, "
                 "profondeurs, analyses, dates — chacun avec son total"),
    ]),
    Ecran(20, "Coupe finie", "maquettes/20_coupe_finie.png", [
        Promesse("la piste affichée a une largeur réglable, et un seul propriétaire",
                 "tenu", "reglages.Reglages · R-44"),
        Promesse("les 4 familles de pistes et leur largeur viennent du même magasin",
                 "tenu", "tracks.TrackCatalog · 12 pistes, 4 familles"),
        Promesse("l'échelle de teneur est fixe : elle ne se recalcule pas "
                 "d'un forage à l'autre",
                 "tenu", "tracks · les bornes viennent du contrat (R-45)"),
        Promesse("couleurs et motifs des lithologies viennent du même endroit "
                 "en 2D, en légende et à l'export",
                 "sans_code",
                 "la coupe 2D du noyau calcule les bandes mais ne les peint pas "
                 "encore : le rendu vit dans l'ancien module"),
        Promesse("« ce que vous voyez est exactement ce que l'export "
                 "produira »",
                 "sans_code",
                 "aucun export n'est branché sur le noyau : la promesse est "
                 "affichée, pas encore tenue"),
    ]),
    Ecran(21, "Exclusions", "maquettes/21_exclusions.png", [
        Promesse("une exclusion vaut partout : coupe, 3D, export, carte",
                 "tenu", "projet.forages_actifs · une seule liste lue par les vues"),
        Promesse("rien n'est effacé : le forage écarté reste dans la liste",
                 "tenu", "projet.exclusions · dict, jamais une suppression"),
        Promesse("le retour en arrière est un bouton, pas une procédure",
                 "tenu", "projet.reintegre"),
        Promesse("chaque décision dit qui, quand, et pourquoi",
                 "tenu", "projet.journal_des_decisions · action, forage, motif, "
                 "auteur, date"),
        Promesse("le forage écarté reste visible en pointillés dans la coupe",
                 "sans_code",
                 "« exclu = absent » : aujourd'hui la décision le retire du "
                 "dessin au lieu de l'estomper"),
        Promesse("un journal des décisions s'ajoute au projet et ne se perd pas",
                 "tenu", "projet.decisions · réintégrer ne l'efface pas"),
    ]),
]


def ecarts(chiffres=None):
    """Les promesses non tenues, dans l'ordre des écrans."""
    out = []
    for e in ECRANS:
        for p in e.promesses:
            if p.etat == "tenu":
                continue
            if chiffres is not None and not p.verifie(chiffres):
                continue
            out.append((e.numero, e.nom, p.etat, p.phrase, p.preuve))
    return out


def geste_promis(numero, phrase):
    """Le geste tel qu'il sera écrit — refusé s'il promet l'impossible."""
    for e in ECRANS:
        if e.numero != numero:
            continue
        for p in e.promesses:
            if p.phrase == phrase:
                return p.etat
    raise KeyError(f"promesse inconnue pour l'écran {numero} : {phrase}")


def types_absents() -> tuple:
    """Les types de données que le projet de référence déclare non fournis."""
    import json
    from pathlib import Path
    fichier = (Path(__file__).resolve().parents[3] / "specs" / "data"
               / "projet_issia.json")
    donnees = json.loads(fichier.read_text(encoding="utf-8"))
    return tuple(cle for cle, val in donnees["par_piste"].items()
                 if val.get("etat") == "info")


def fiche_source(chemin, texte=None) -> FicheSource:
    """Les chiffres de l'écran 18, calculés par la vraie lecture."""
    from ..donnees.lecture import lit_collets
    lec = lit_collets(chemin, texte=texte)
    entetes = lec.colonnes
    doublons = tuple(sorted(_identifiants_doubles(lec)))
    return FicheSource(
        nom=getattr(chemin, "name", str(chemin).split("/")[-1]),
        forages=len(lec.colliers),
        lignes=sum(1 for m in lec.messages if m.titre.startswith("Ligne ")),
        colonnes=len(entetes),
        colonnes_reconnues=sum(1 for c in entetes if c.reconnue),
        lignes_illisibles=sum(
            1 for m in lec.messages if "illisible" in m.titre.lower()),
        doublons=doublons,
        bloquant=lec.bloquant,
        types_absents=types_absents(),
    )


def _identifiants_doubles(lec):
    vus = {}
    for m in lec.messages:
        if "même nom" in m.titre or "deux fois" in m.titre:
            for c in m.concernes:
                if not c.startswith("ligne"):
                    vus[c] = True
    return vus
