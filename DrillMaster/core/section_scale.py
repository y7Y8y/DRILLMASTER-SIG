"""
Échelle COMMUNE des coupes (« échelle de projet »).

Problème corrigé : chaque coupe était mise à l'échelle pour REMPLIR la largeur
de la fenêtre (sx = largeur / longueur de la coupe) et son pas de graduation
horizontal dépendait de sa longueur (10, 20 ou 50 m selon la coupe). Deux
coupes n'étaient donc ni comparables ni corrélables, contrairement à la 3D qui
est toujours à l'échelle réelle.

Règle retenue : UNE échelle 1:N pour tout le projet ; le pas de graduation ne
dépend QUE de N (espacement ≥ 15 mm sur papier), jamais de la coupe.

Fonctions pures (aucun Qt) : testables seules.
"""
from __future__ import annotations

import math

SCENE_PX_MM = 25.4 / 96.0      # 1 px scène = 1/96 pouce = 0,2646 mm
COMMON_RATIOS = (500, 1000, 2000, 2500, 5000)
MIN_TICK_MM = 15.0             # espacement mini entre graduations (papier)
UNIT_FACTOR = {"m": 1.0, "km": 1000.0, "ft": 0.3048, "feet": 0.3048,
               "pi": 0.3048, "pieds": 0.3048}


def unit_factor(unit) -> float:
    return UNIT_FACTOR.get(str(unit or "m").strip().lower(), 1.0)


def sx_for_ratio(n: float, factor: float = 1.0) -> float:
    """px scène par unité de distance pour que 1 mm papier = n/1000 m."""
    return (1000.0 * factor / float(n)) / SCENE_PX_MM


def ratio_from_sx(sx: float, factor: float = 1.0) -> float:
    """N équivalent d'une échelle en px scène / unité (inverse de sx_for_ratio)."""
    return 1000.0 * factor / (float(sx) * SCENE_PX_MM)


def nice_step(raw: float) -> float:
    """Arrondi au 1 / 2 / 5 × 10ⁿ le plus proche (même règle que la coupe)."""
    if raw <= 0:
        return 1.0
    base = 10 ** math.floor(math.log10(raw))
    f = raw / base
    if f < 1.5:
        return base
    if f < 3:
        return 2 * base
    if f < 7:
        return 5 * base
    return 10 * base


def grid_step_for_ratio(n: float, factor: float = 1.0, exag: float = 1.0,
                        mm: float = MIN_TICK_MM) -> float:
    """Pas de graduation (en unités de distance) pour l'échelle 1:n.

    Horizontal : exag = 1 ; vertical : passer l'exagération verticale.
    Ne dépend NI de la longueur NI de la hauteur de la coupe.
    """
    units_per_mm = (float(n) / 1000.0) / max(float(factor), 1e-9)
    raw = mm * units_per_mm / max(float(exag), 1e-6)
    return nice_step(raw)


def common_elev_window(zmin: float, zmax: float, step: float):
    """Fenêtre d'élévation COMMUNE (min, max) arrondie au pas de graduation.

    Mêmes marges que la coupe automatique : ≥ 8 m ou 5 % de l'amplitude sous
    le trou le plus profond (« eoh » + axe), 2 % de l'amplitude au-dessus du
    collet le plus haut ; bornes arrondies VERS L'EXTÉRIEUR à un multiple du
    pas, pour que les graduations tombent aux mêmes altitudes partout.
    """
    span = max(float(zmax) - float(zmin), 1.0)
    step = max(float(step), 1e-6)
    lo = math.floor((float(zmin) - max(8.0, 0.05 * span)) / step) * step
    hi = math.ceil((float(zmax) + 0.02 * span) / step) * step
    return lo, hi


# --------------------------------------------------- échelle de projet AUTO
AUTO_RATIOS = (250, 500, 1000, 1500, 2000, 2500, 5000, 10000, 20000)
REF_WIDTH_PX = 1250.0   # largeur de référence (px écran), indépendante de la fenêtre


def auto_project_ratio(max_length: float, factor: float = 1.0) -> int:
    """Échelle 1:N commune choisie AUTOMATIQUEMENT pour tout le projet : la plus
    grande échelle standard pour laquelle la coupe la PLUS LONGUE tient dans la
    largeur de référence. Dépend du projet, jamais de la fenêtre ni de la coupe
    affichée : toutes les coupes reçoivent donc la même échelle (repère
    orthonormé comme en 3D : 1 m horizontal = 1 m vertical, partout)."""
    L = max(float(max_length), 1e-9)
    for n in AUTO_RATIOS:
        if L * sx_for_ratio(n, factor) <= REF_WIDTH_PX:
            return n
    return AUTO_RATIOS[-1]
