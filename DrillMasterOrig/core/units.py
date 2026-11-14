"""
DrillMaster ORIG — cœur pur : conventions et conversions.

RÈGLE ABSOLUE n°1 (ARCHITECTURE.md) : les conventions sont déclarées
ICI et nulle part ailleurs.

  - X = Esting (m ou ft), Y = Northing, Z = élévation (positive vers le haut)
  - Profondeur : distance descendante depuis le collet, >= 0
  - Azimut : degrés depuis le Nord, [0, 360[
  - Dip : degrés signés depuis l'horizontale, POSITIF VERS LE BAS
    (0° = horizontal, +90° = vertical descendant, -90° = remontée)

Le v2 documentait deux conventions contradictoires ; ici une seule.
"""

from __future__ import annotations

import math

DEG = math.pi / 180.0


def direction_vector(azimuth_deg: float, dip_deg: float) -> tuple[float, float, float]:
    """Vecteur unitaire (dx, dy, dz) d'un azimut/dip (conventions ci-dessus).

    Descendant (dip > 0) => dz négatif ; remontant (dip < 0) => dz positif.
    """
    az = azimuth_deg % 360.0
    horiz = math.cos(dip_deg * DEG)
    return (
        horiz * math.sin(az * DEG),
        horiz * math.cos(az * DEG),
        -math.sin(dip_deg * DEG),
    )


def circular_mean_azimuth(az1: float, az2: float) -> float:
    """Moyenne circulaire de deux azimuts (359° et 1° => 0°, pas 180°)."""
    a1, a2 = az1 % 360.0, az2 % 360.0
    x = math.cos(a1 * DEG) + math.cos(a2 * DEG)
    y = math.sin(a1 * DEG) + math.sin(a2 * DEG)
    avg = math.degrees(math.atan2(y, x)) % 360.0
    return 0.0 if avg > 359.99 else avg


def normalize_azimuth(azimuth_deg: float) -> float:
    """Azimut ramené dans [0, 360[."""
    az = azimuth_deg % 360.0
    return 0.0 if az > 359.99 else az
