"""Chantier 8 — la navigation : une action n'existe que si on la trouve.

Deux règles, et un outil qui les tient.

**R-56 · Une action a exactement un chemin.** Pas deux boutons pour la même
chose, pas un troisième caché dans un menu contextuel. Le chemin se lit dans
le code : `Chemin(ecran, zone, geste)`.

**R-58 · Un raccourci n'existe que s'il est écrit sur le bouton.** Une touche
qui n'est affichée nulle part est un pouvoir invisible : celui qui la connaît
va deux fois plus vite, l'autre ne saura jamais qu'elle existe. Tant qu'un
geste n'a pas sa touche imprimée à côté de son libellé, il n'a pas de
raccourci.

**R-57 · Ce qui n'est pas atteignable n'est pas écrit.** Un écran qu'aucun
geste n'ouvre est du code mort ; un geste qu'aucun écran ne déclare est une
trappe. Les deux sont mesurés, jamais supposés.

Le registre est la source : les écrans déclarent leurs gestes, et
`tools/audit_navigation.py` vérifie que le plugin réel ne fait pas autre
chose. Quand les deux diffèrent, c'est le registre qu'on corrige — ou le
code.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Les zones d'un écran. Cinq, pas six : au-delà, on ne sait plus où regarder.
ZONES = ("barre haute", "panneau", "zone de travail", "barre basse",
         "menu contextuel")

# Les genres de geste. Un geste se dit par ce qu'on fait, pas par l'objet Qt.
GESTES = ("bouton", "case", "curseur", "ligne de liste", "clic droit",
          "double-clic", "raccourci", "dépôt")


@dataclass(frozen=True)
class Chemin:
    """Un chemin d'accès, lisible : où c'est, comment on y arrive."""
    ecran: str
    zone: str
    geste: str
    quoi: str                       # ce que ça fait, en français simple
    cle: str = ""                   # raccourci, s'il existe (jamais seul)

    def __post_init__(self):
        if self.zone not in ZONES:
            raise ValueError(f"zone inconnue : {self.zone}")
        if self.geste not in GESTES:
            raise ValueError(f"geste inconnu : {self.geste}")
        # R-58 — un raccourci est toujours écrit quelque part à l'écran
        if self.cle:
            raise ValueError(
                "un raccourci sans touche affichée est un pouvoir invisible "
                "(R-58) : donnez-lui sa touche écrite, ou pas de raccourci")

    def phrase(self):
        return f"{self.ecran} › {self.zone} › {self.geste} : {self.quoi}"


@dataclass
class Ecran:
    nom: str
    chemins: list = field(default_factory=list)

    def ajoute(self, zone, geste, quoi, cle=""):
        c = Chemin(self.nom, zone, geste, quoi, cle)
        if any(x.quoi == quoi and x.zone == zone for x in self.chemins):
            raise ValueError(f"« {quoi} » est déjà dans {self.nom} › {zone} "
                             "(R-56 : un seul chemin)")
        self.chemins.append(c)
        return c

    def par_zone(self, zone):
        return [c for c in self.chemins if c.zone == zone]

    def raccourcis(self):
        return [c for c in self.chemins if c.cle]


class Navigation:
    """Le registre des écrans et de leurs chemins."""

    def __init__(self):
        self.ecrans = {}

    def ecran(self, nom):
        if nom not in self.ecrans:
            self.ecrans[nom] = Ecran(nom)
        return self.ecrans[nom]

    # ── contrôles de la R-56 ─────────────────────────────────────────
    def doublons(self):
        """La même chose atteignable deux fois dans la même zone."""
        vus, doubles = {}, []
        for e in self.ecrans.values():
            for c in e.chemins:
                cle = (e.nom, c.zone, c.quoi)
                if cle in vus:
                    doubles.append(c)
                vus[cle] = c
        return doubles

    def sans_raccourci_isole(self):
        """Un raccourci qui n'a pas d'autre chemin est une trappe (R-57)."""
        trappes = []
        for e in self.ecrans.values():
            for c in e.raccourcis():
                autres = [x for x in e.chemins
                          if x.quoi == c.quoi and x.geste != "raccourci"]
                if not autres:
                    trappes.append(c)
        return trappes

    def par_geste(self, geste):
        return [c for e in self.ecrans.values() for c in e.chemins
                if c.geste == geste]

    def resume(self):
        return {
            "ecrans": len(self.ecrans),
            "chemins": sum(len(e.chemins) for e in self.ecrans.values()),
            "raccourcis": len(self.par_geste("raccourci")),
            "zones_vides": sorted(
                {z for e in self.ecrans.values() for z in ZONES}
                - {c.zone for e in self.ecrans.values() for c in e.chemins}),
        }


def navigation_du_plugin() -> Navigation:
    """Le registre tel qu'il devrait être : quatre écrans, chemins uniques."""
    n = Navigation()
    e = n.ecran("Données")
    e.ajoute("zone de travail", "dépôt", "importer un fichier de colliers")
    e.ajoute("zone de travail", "bouton", "voir ce que le fichier contient")
    e.ajoute("panneau", "bouton", "enregistrer la décision sur un doublon")
    e.ajoute("barre basse", "bouton", "revenir en arrière sur un import")
    e = n.ecran("Coupe 2D")
    e.ajoute("panneau", "case", "afficher ou masquer une piste")
    e.ajoute("panneau", "curseur", "régler la largeur d'une piste")
    e.ajoute("panneau", "bouton", "réintégrer un forage écarté")
    e.ajoute("zone de travail", "clic droit", "exclure un forage de la coupe")
    e.ajoute("zone de travail", "double-clic", "ouvrir la fiche d'un forage")
    e.ajoute("barre haute", "bouton", "exporter la coupe à l'échelle")
    e = n.ecran("Vue 3D")
    e.ajoute("panneau", "bouton", "basculer en mode Guidé ou Expert")
    e.ajoute("zone de travail", "clic droit", "voir une photo de carotte")
    e.ajoute("barre basse", "bouton", "revenir à la coupe")
    e = n.ecran("Référentiel")
    e.ajoute("panneau", "ligne de liste", "choisir une famille")
    e.ajoute("panneau", "bouton", "changer la couleur d'une famille")
    e.ajoute("barre haute", "bouton", "annuler un changement de couleur")
    return n
