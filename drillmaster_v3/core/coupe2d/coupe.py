"""Coupe 2D — projection réelle sur une ligne, inclusion, intercepts.

Ce module ne dessine rien : il **calcule**. Le dessin consomme son résultat,
donc la 2D, l'export et la carte QGIS ne peuvent pas divergér (R-09).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..geometrie.trajectoire import Point, fond
from ..messages import avertissement, information


@dataclass(frozen=True)
class Ligne:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def longueur(self):
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)

    @property
    def orientation(self):
        """Azimut de la coupe, 0 = Nord, sens horaire."""
        a = math.degrees(math.atan2(self.x2 - self.x1, self.y2 - self.y1))
        return round(a % 360, 1)

    @property
    def _dx(self):
        return (self.x2 - self.x1) / (self.longueur or 1)

    @property
    def _dy(self):
        return (self.y2 - self.y1) / (self.longueur or 1)

    def abscisse(self, x, y):
        """Distance le long de la ligne (peut sortir de [0, longueur])."""
        return (x - self.x1) * self._dx + (y - self.y1) * self._dy

    def ecart(self, x, y):
        """Distance perpendiculaire à la ligne."""
        return abs(-(x - self.x1) * self._dy + (y - self.y1) * self._dx)

    def dans(self, x, y, buffer):
        return self.ecart(x, y) <= buffer and -buffer <= self.abscisse(x, y) \
            <= self.longueur + buffer


@dataclass
class Inclusion:
    inclus: list = field(default_factory=list)
    exclus: list = field(default_factory=list)   # [(forage, raison)]
    messages: list = field(default_factory=list)

    def resume(self):
        return {"inclus": len(self.inclus), "exclus": len(self.exclus)}


def inclusion(colliers, ligne: Ligne, buffer):
    """R-14 : un forage hors coupe est **annoncé**, jamais silencieusement absent."""
    res = Inclusion()
    for f in colliers:
        if ligne.dans(f.x, f.y, buffer):
            res.inclus.append(f)
        else:
            raison = (f"à {ligne.ecart(f.x, f.y):.0f} m de l'axe "
                      f"(tolérance {buffer:.0f} m)")
            res.exclus.append((f, raison))
    if res.exclus:
        res.messages.append(information(
            f"{len(res.exclus)} forages hors coupe",
            "ils restent dans le projet et réapparaîtront si on élargit "
            "la tolérance", f"coupe {ligne.orientation:.0f}°"))
    return res


@dataclass(frozen=True)
class TraceCoupe:
    """Un forage projeté dans le plan de coupe."""
    id: str
    abscisse: float          # distance le long de l'axe, en mètres
    altitude_collet: float
    altitude_fond: float
    profondeur: float
    points: tuple = ()

    @property
    def hauteur(self):
        return self.altitude_collet - self.altitude_fond


def projette(colliers, ligne: Ligne, mesures=None, methode="courbure_minimale",
             profondeurs=None):
    """Projette chaque forage inclus : une seule géométrie, calculée une fois."""
    traces = []
    mesures = mesures or {}
    profondeurs = profondeurs or {}
    for f in colliers:
        prof = profondeurs.get(f.id, f.profondeur or 0.0)
        p_fond = fond(f.x, f.y, f.z, mesures.get(f.id, []), methode, prof)
        traces.append(TraceCoupe(
            id=f.id,
            abscisse=round(ligne.abscisse(f.x, f.y), 1),
            altitude_collet=round(f.z, 2),
            altitude_fond=round(p_fond.z, 2),
            profondeur=round(prof, 1)))
    traces.sort(key=lambda t: t.abscisse)
    return traces


# ── intercepts : plusieurs seuils, longueur minimale, coupure possible ──
def intercepts(analyses, seuils, longueur_min=1.0, sans_teneur_ok=False):
    """analyses : [(forage_id, de, à, teneur)]. Retourne les intervalles retenus.

    Un intervalle est retenu si la moyenne pondérée dépasse un seuil ET si sa
    longueur atteint `longueur_min`. Aucune valeur manquante n'est inventée.
    """
    par_forage = {}
    for fid, de, a, teneur in analyses:
        par_forage.setdefault(fid, []).append((float(de), float(a), teneur))
    resultat = []
    for fid, liste in par_forage.items():
        liste.sort()
        for seuil in seuils:
            courant = None
            for de, a, teneur in liste:
                if teneur is None or teneur < seuil:
                    if courant:
                        resultat.append(courant)
                        courant = None
                    continue
                if courant and abs(courant["a"] - de) < 1e-9:
                    courant["a"] = a
                else:
                    if courant:
                        resultat.append(courant)
                    courant = {"forage": fid, "seuil": seuil, "de": de, "a": a}
            if courant:
                resultat.append(courant)
    retenus = []
    for i in resultat:
        i["longueur"] = round(i["a"] - i["de"], 2)
        if i["longueur"] >= longueur_min:
            retenus.append(i)
    retenus.sort(key=lambda i: (i["forage"], i["de"]))
    return retenus


def rattachement(id_forage, ids_connus):
    """R-14 : un forage absent des analyses est signalé, jamais sous-entendu."""
    if id_forage in ids_connus:
        return None
    return avertissement(
        "Des analyses ne correspondent à aucun forage",
        "ces teneurs resteraient invisibles en coupe : l'identifiant du "
        "fichier d'analyses ne correspond à aucun collet",
        (id_forage,),
        ("vérifier l'identifiant dans le fichier d'analyses",
         "exclure ces analyses de la coupe"),
        "fichier d'analyses")


def controle_couverture(traces, largeur_coupe=None):
    """R-14 : ce qui est vide est signalé, ce qui est hors cadre aussi."""
    messages = []
    if not traces:
        messages.append(avertissement(
            "Aucun forage dans cette coupe",
            "la coupe serait vide : élargir la tolérance ou déplacer l'axe",
            ("coupe",), ("élargir la tolérance", "déplacer l'axe"),
            "coupe 2D"))
        return messages
    abscisses = [t.abscisse for t in traces]
    if largeur_coupe and (min(abscisses) < 0 or max(abscisses) > largeur_coupe):
        messages.append(avertissement(
            "Un forage sort du cadre de la coupe",
            "il serait tronqué à l'export : la longueur de coupe doit "
            "couvrir tous les forages inclus",
            ("cadre",), ("allonger la coupe", "réduire la tolérance"),
            "coupe 2D"))
    vides = [t.id for t in traces if t.profondeur <= 0]
    if vides:
        messages.append(avertissement(
            f"{len(vides)} forages sans profondeur",
            "leur piste serait vide : la profondeur finale manque dans le fichier",
            tuple(vides[:5]), ("compléter la profondeur dans le fichier",),
            "collets"))
    return messages
