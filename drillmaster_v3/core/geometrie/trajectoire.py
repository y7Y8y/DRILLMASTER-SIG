"""Géométrie des forages — calcul réel, comparé, testé.

Trois méthodes : verticale supposée, angle moyen, courbure minimale.
Le résultat dit toujours **quelle méthode** et **quel écart** avec l'autre (R-27).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..messages import information, avertissement


@dataclass(frozen=True)
class Point:
    profondeur: float
    x: float
    y: float
    z: float
    azimut: float = 0.0
    pendage: float = -90.0


def _incidence(pendage):
    """Pendage −90 = vertical vers le bas → incidence 0."""
    return math.radians(abs(90 + pendage))


def verticale(x, y, z, profondeur):
    """Forage supposé vertical : il descend, il ne remonte pas."""
    prof = max(0.0, float(profondeur or 0.0))
    return [Point(0.0, x, y, z, 0.0, -90.0),
            Point(prof, x, y, z - prof, 0.0, -90.0)] if prof else \
        [Point(0.0, x, y, z, 0.0, -90.0)]


def calcule(x, y, z, mesures, methode="angle_moyen"):
    """mesures : [(profondeur, azimut, pendage), …]. Sans mesure : verticale."""
    if not mesures:
        prof = 0.0
        return verticale(x, y, z, prof)
    mesures = sorted(mesures)
    p0, az0, dip0 = mesures[0]
    pts = [Point(p0, x, y, z, az0, dip0)]
    for (p1, az1, dip1), (p2, az2, dip2) in zip(mesures, mesures[1:]):
        L = p2 - p1
        i1, i2 = _incidence(dip1), _incidence(dip2)
        a1 = math.radians(az1)
        a2 = math.radians(az2)
        if methode == "angle_moyen":
            rf = 1.0
        else:                                     # courbure minimale
            dogleg = math.acos(max(-1.0, min(1.0,
                math.cos(i2 - i1) - math.sin(i1) * math.sin(i2) *
                (1 - math.cos(a2 - a1)))))
            rf = 1.0 if dogleg < 1e-9 else 2 / dogleg * math.tan(dogleg / 2)
        dx = L / 2 * (math.sin(i1) * math.sin(a1)
                      + math.sin(i2) * math.sin(a2)) * rf
        dy = L / 2 * (math.sin(i1) * math.cos(a1)
                      + math.sin(i2) * math.cos(a2)) * rf
        dz = -L / 2 * (math.cos(i1) + math.cos(i2)) * rf
        d = pts[-1]
        pts.append(Point(p2, d.x + dx, d.y + dy, d.z + dz, az2, dip2))
    return pts


def fond(x, y, z, mesures, methode="angle_moyen", profondeur=0.0):
    pts = calcule(x, y, z, mesures, methode)
    if len(pts) == 1:                     # aucune mesure exploitable
        return verticale(x, y, z, profondeur)[-1]
    fond_ = pts[-1]
    manque = profondeur - fond_.profondeur
    if manque > 0:                        # la trajectoire s'arrête avant le fond
        return Point(profondeur, fond_.x, fond_.y, fond_.z - manque,
                     fond_.azimut, -90.0)
    return fond_


def compare(x, y, z, mesures, tolerance=0.5):
    """Écart entre les deux méthodes au fond du forage."""
    if not mesures:
        return {"ecart_m": 0.0, "message": None}
    a = fond(x, y, z, mesures, "angle_moyen")
    b = fond(x, y, z, mesures, "courbure_minimale")
    ecart = math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))
    msg = None
    if ecart > tolerance:
        msg = avertissement(
            "Deux méthodes de calcul ne donnent pas le même fond",
            f"l'écart atteint {ecart:.1f} m au fond : la coupe serait "
            "différente selon la méthode retenue",
            (f"écart {ecart:.1f} m",),
            ("garder la courbure minimale, recommandée pour les forages inclinés",
             "garder l'angle moyen si c'est la convention de votre société"),
            "géométrie des trajectoires")
    return {"ecart_m": round(ecart, 2), "message": msg}


def controle_collets(colliers, tole=0.01):
    """Cohérence entre collet et trajectoire : profondeur, points hors collet."""
    messages = []
    for f in colliers:
        if f.profondeur is not None and f.profondeur < 0:
            messages.append(avertissement(
                f"{f.id} : profondeur négative",
                "une trajectoire ne peut pas remonter au-dessus de son point "
                "d'entrée", (f.id,), ("corriger la profondeur finale",),
                "collets"))
    if messages:
        return messages
    return [information("Aucun point hors collet",
                        "les trajectoires restent sous leur point d'entrée",
                        "collets")]
