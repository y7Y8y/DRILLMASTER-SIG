"""
DrillMaster ORIG — trajectoires 3D (pur, testé standalone).

Deux méthodes :
  - ``minimum_curvature`` (défaut) : référence industrielle, lisse les
    déviations réelles des sondes ;
  - ``average_angle`` (compat v2) : angle moyen linéaire.

Convention dip : POSITIF VERS LE BAS (core/units.py — source unique).
"""

from __future__ import annotations

import math

from .model import Collar, DrillHole, SurveyStation, TrajectoryPoint
from .units import DEG, direction_vector, normalize_azimuth

_MIN_DOGLEG = 1e-10


def _dogleg(u1, u2) -> float:
    """Angle (rad) entre deux vecteurs unitaires consécutifs."""
    dot = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1] + u1[2] * u2[2]))
    return math.acos(dot)


def _segment_delta(u1, u2, dl: float) -> tuple[float, float, float]:
    """Déplacement 3D d'un segment dl entre directions u1 et u2.

    Courbure minimale : facteur de rapport RF = (2/beta)·tan(beta/2) ;
    dégénère en angle moyen (droite) quand beta -> 0.
    """
    beta = _dogleg(u1, u2)
    if beta < _MIN_DOGLEG:
        factor = 0.5
    else:
        factor = math.tan(beta / 2.0) / beta
    return tuple(
        dl * (u1[i] + u2[i]) * factor for i in range(3))


def compute_trajectory(
    collar: Collar,
    surveys: list[SurveyStation],
    method: str = "minimum_curvature",
) -> list[TrajectoryPoint]:
    """Trajectoire complète d'un trou, collet inclus comme station 0.

    ``method`` : ``minimum_curvature`` (défaut) ou ``average_angle``.
    """
    stations = sorted(surveys, key=lambda s: s.depth)
    points: list[TrajectoryPoint] = [
        TrajectoryPoint(0.0, collar.x, collar.y, collar.elevation,
                        stations[0].azimuth if stations else 0.0,
                        stations[0].dip if stations else 0.0)
    ]
    if not stations:
        return points

    prev_depth = 0.0
    prev_az = stations[0].azimuth
    prev_dip = stations[0].dip
    x, y, z = collar.x, collar.y, collar.elevation

    for st in stations:
        dl = st.depth - prev_depth
        if dl <= 0.0:
            prev_az, prev_dip = st.azimuth, st.dip
            continue
        if method == "average_angle":
            az = _mean_az(prev_az, st.azimuth)
            dip = (prev_dip + st.dip) / 2.0
            u = direction_vector(az, dip)
            dx, dy, dz = (dl * u[0], dl * u[1], dl * u[2])
        else:
            u1 = direction_vector(prev_az, prev_dip)
            u2 = direction_vector(st.azimuth, st.dip)
            dx, dy, dz = _segment_delta(u1, u2, dl)
        x, y, z = x + dx, y + dy, z + dz
        points.append(TrajectoryPoint(
            st.depth, x, y, z,
            normalize_azimuth(st.azimuth), st.dip))
        prev_depth, prev_az, prev_dip = st.depth, st.azimuth, st.dip

    return points


def _mean_az(az1: float, az2: float) -> float:
    from .units import circular_mean_azimuth
    return circular_mean_azimuth(az1, az2)


def point_at_depth(
    trajectory: list[TrajectoryPoint], depth: float
) -> Optional[TrajectoryPoint]:
    """Interpolation linéaire entre points de trajectoire (hors bornes = None)."""
    if not trajectory or depth < trajectory[0].depth:
        return None
    if depth > trajectory[-1].depth:
        return None
    for i in range(1, len(trajectory)):
        a, b = trajectory[i - 1], trajectory[i]
        if depth <= b.depth:
            if b.depth == a.depth:
                return a
            t = (depth - a.depth) / (b.depth - a.depth)
            return TrajectoryPoint(
                depth,
                a.x + t * (b.x - a.x),
                a.y + t * (b.y - a.y),
                a.z + t * (b.z - a.z),
                a.azimuth + t * (b.azimuth - a.azimuth),
                a.dip + t * (b.dip - a.dip),
            )
    return trajectory[-1]


def validate_surveys(surveys: list[SurveyStation]) -> list[str]:
    """Erreurs bloquantes QC (message en français, prêt pour l'UI)."""
    errors: list[str] = []
    for s in surveys:
        if s.depth < 0:
            errors.append(f"{s.hole_id} · profondeur négative ({s.depth})")
        if not 0.0 <= s.azimuth <= 360.0:
            errors.append(f"{s.hole_id} · azimut hors [0, 360] ({s.azimuth})")
        if not -180.0 <= s.dip <= 180.0:
            errors.append(f"{s.hole_id} · dip hors [-180, 180] ({s.dip})")
    depths = [s.depth for s in surveys]
    if len(set(depths)) != len(depths):
        errors.append("profondeurs de stations dupliquées")
    return errors


def build_hole(collar: Collar, surveys: list[SurveyStation],
               method: str = "minimum_curvature") -> DrillHole:
    """Construit un DrillHole avec sa trajectoire calculée."""
    hole = DrillHole(collar=collar, surveys=sorted(
        surveys, key=lambda s: s.depth))
    hole.trajectory = compute_trajectory(collar, hole.surveys, method)
    return hole
