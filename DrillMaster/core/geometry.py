"""
DrillMaster — 3D Trajectory Geometry
=====================================
Computes 3D drillhole trajectories from collar and survey data
using the average-angle (linear interpolation) method.

Conventions (standard mining):
  - Dip     = angle signed (0° = horizontal, -90° = down, +90° = up)
  - Azimuth = direction from North  (0° = N, 90° = E, 180° = S, 270° = W)
  - Z       = elevation (positive = up); depth decreases elevation

Formula for a segment of length dL with average dip D and azimuth A:
  horizontal  = dL * cos(D)
  dx          = horizontal * sin(A)
  dy          = horizontal * cos(A)
  dz          = -dL * sin(D)   (negative: going down reduces elevation)

Pure Python + numpy — testable standalone.
"""

from __future__ import annotations

import math
from typing import Optional

from .data_model import (
    CollarRecord,
    SurveyRecord,
    TrajectoryPoint,
    DrillHole,
)


def _circular_mean_azimuth(az1: float, az2: float) -> float:
    """
    Compute the circular mean of two azimuth angles in degrees.
    Handles wraparound (e.g. mean of 359° and 1° = 0°, not 180°).
    """
    a1 = math.radians(az1 % 360)
    a2 = math.radians(az2 % 360)
    x = math.cos(a1) + math.cos(a2)
    y = math.sin(a1) + math.sin(a2)
    avg = math.degrees(math.atan2(y, x)) % 360
    # Normalise: if very close to 360, return 0 (handles floating-point edge cases)
    if avg > 359.99:
        avg = 0.0
    return avg


def collar_info_text(collar, survey) -> str:
    """v2.9.288 — ligne « Az X / Dip Y » du collet, jamais muette si donnée.

    Le collet prime ; à défaut, le 1er tir de déviation (cohérent avec la
    trajectoire prolongée v2.9.284) ; les deux champs indépendamment.
    Retourne "" si aucune des deux sources ne porte azimut/pendage.
    """
    az = getattr(collar, "azimuth", None)
    dip = getattr(collar, "dip", None)
    if (az is None or dip is None) and survey:
        first = survey[0]
        az = az if az is not None else getattr(first, "azimuth", None)
        dip = dip if dip is not None else getattr(first, "dip", None)
    parts = []
    if az is not None:
        parts.append(f"Az {az:.0f}")
    if dip is not None:
        parts.append(f"Dip {dip:.0f}")
    return " / ".join(parts)


def _compute_segment_displacement(
    dL: float,
    dip_deg: float,
    az_deg: float,
) -> tuple[float, float, float]:
    """
    Compute (dx, dy, dz) for a segment of length dL.
    Dip signed (negative = down, positive = up), azimuth from North.
    """
    az_rad = math.radians(az_deg)
    # v2.9.286 — convention SIGNÉE standard (Datamine/Leapfrog/Micromine/
    # Surpac) : dip NÉGATIF = vers le bas, POSITIF = vers le haut, 0 =
    # horizontal.  Les fichiers « positif = bas » sont convertis à
    # l'import (convention « Historique », étape 2) : plus d'abs() ici.
    dip_rad = math.radians(dip_deg)
    horizontal = dL * math.cos(dip_rad)
    dx = horizontal * math.sin(az_rad)
    dy = horizontal * math.cos(az_rad)
    dz = dL * math.sin(dip_rad)
    return dx, dy, dz


def compute_trajectory(
    collar: CollarRecord,
    survey: list[SurveyRecord],
    subdivide: bool = False,
    max_segment: float = 5.0,
) -> list[TrajectoryPoint]:
    """
    Compute the 3D trajectory of a drillhole.

    Uses the average-angle method between consecutive survey stations.
    If no survey station exists at depth 0, a synthetic one is created
    from the collar's azimuth/dip (or defaults: az=0, dip=-90 = vertical down).
    Empty survey list = straight hole (puits droit) to max_depth —
    same contract as auto_survey_for_vertical (étape 3) ; tests WELL-97.

    Args:
        collar: Collar record with x, y, z, max_depth, optional az/dip.
        survey: List of survey stations (sorted or unsorted).
        subdivide: If True, subdivide long segments for smoother trajectories.
        max_segment: Maximum segment length when subdividing.

    Returns:
        List of TrajectoryPoint (x, y, z, depth) from collar to EOH.
    """
    trajectory: list[TrajectoryPoint] = []

    # --- Build the station list, ensuring a station at depth 0 ---
    stations = sorted(survey, key=lambda s: s.depth)

    if not stations or stations[0].depth > 0.01:
        # v2.9.284 — coude artificiel au collet (RC) : le 1er tir est souvent
        # >0 m.  Avant, la station synthétique à 0 m prenait le défaut vertical
        # → coude en « S ».  On PROLONGE le 1er tir réel jusqu'à la surface
        # (pratique Geoscience) : collar az/dip si présents, sinon 1er tir ;
        # défaut vertical UNIQUEMENT si aucun survey (WELL-97 inchangé).
        if collar.azimuth is not None and collar.dip is not None:
            initial_az, initial_dip = collar.azimuth, collar.dip
        elif stations:
            initial_az, initial_dip = stations[0].azimuth, stations[0].dip
        else:
            initial_az, initial_dip = 0.0, -90.0
        stations.insert(0, SurveyRecord(
            hole_id=collar.hole_id,
            depth=0.0,
            azimuth=initial_az,
            dip=initial_dip,
        ))

    # --- Ensure final station reaches max_depth ---
    # (handled in the loop by extending past the last station)

    # --- Starting point: collar ---
    cx, cy, cz = collar.x, collar.y, collar.z
    current_depth = 0.0
    trajectory.append(TrajectoryPoint(cx, cy, cz, 0.0))

    for i in range(len(stations)):
        st = stations[i]
        # Determine the end of this segment
        if i < len(stations) - 1:
            next_st = stations[i + 1]
            end_depth = next_st.depth
            avg_az = _circular_mean_azimuth(st.azimuth, next_st.azimuth)
            avg_dip = (st.dip + next_st.dip) / 2.0
        else:
            # Last station: extend to max_depth
            end_depth = collar.max_depth
            avg_az = st.azimuth
            avg_dip = st.dip

        seg_len = end_depth - st.depth
        if seg_len <= 0:
            continue

        if subdivide and seg_len > max_segment:
            # Subdivide for smoother trajectory
            n_sub = int(math.ceil(seg_len / max_segment))
            sub_len = seg_len / n_sub
            for _ in range(n_sub):
                dx, dy, dz = _compute_segment_displacement(sub_len, avg_dip, avg_az)
                cx += dx
                cy += dy
                cz += dz
                current_depth += sub_len
                trajectory.append(TrajectoryPoint(cx, cy, cz, current_depth))
        else:
            dx, dy, dz = _compute_segment_displacement(seg_len, avg_dip, avg_az)
            cx += dx
            cy += dy
            cz += dz
            current_depth += seg_len
            trajectory.append(TrajectoryPoint(cx, cy, cz, current_depth))

    return trajectory


def validate_trajectory(trajectory: list[TrajectoryPoint]) -> list[str]:
    """
    Validate a computed trajectory. Returns a list of error messages
    (empty if valid).
    """
    errors = []
    if not trajectory:
        errors.append("Trajectoire vide.")
        return errors

    if len(trajectory) < 2:
        errors.append("Trajectoire trop courte (moins de 2 points).")
        return errors

    for i, pt in enumerate(trajectory):
        if any(v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))
               for v in (pt.x, pt.y, pt.z, pt.depth)):
            errors.append(f"Point {i}: valeur NaN ou infinie détectée.")
            return errors

    # Check total length > 0
    total_len = 0.0
    for i in range(1, len(trajectory)):
        p0 = trajectory[i - 1]
        p1 = trajectory[i]
        total_len += math.sqrt(
            (p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2 + (p1.z - p0.z) ** 2
        )
    if total_len < 1e-9:
        errors.append("Trajectoire de longueur nulle.")

    # Check depth is monotonic (increasing)
    for i in range(1, len(trajectory)):
        if trajectory[i].depth < trajectory[i - 1].depth - 1e-6:
            errors.append(
                f"Profondeur non-monotone au point {i}: "
                f"{trajectory[i].depth} < {trajectory[i-1].depth}"
            )
            break

    return errors


def depth_to_xyz(
    trajectory: list[TrajectoryPoint],
    target_depth: float,
) -> Optional[tuple[float, float, float]]:
    """
    Interpolate (x, y, z) at a given down-hole depth along the trajectory.
    Returns None if depth is outside the trajectory range.
    """
    if not trajectory:
        return None

    if target_depth <= trajectory[0].depth:
        pt = trajectory[0]
        return (pt.x, pt.y, pt.z)

    if target_depth >= trajectory[-1].depth:
        pt = trajectory[-1]
        return (pt.x, pt.y, pt.z)

    for i in range(1, len(trajectory)):
        p0 = trajectory[i - 1]
        p1 = trajectory[i]
        if p0.depth <= target_depth <= p1.depth:
            denom = p1.depth - p0.depth
            if denom < 1e-12:
                return (p0.x, p0.y, p0.z)
            t = (target_depth - p0.depth) / denom
            x = p0.x + t * (p1.x - p0.x)
            y = p0.y + t * (p1.y - p0.y)
            z = p0.z + t * (p1.z - p0.z)
            return (x, y, z)

    return None


def build_drillhole(
    collar: CollarRecord,
    survey: list[SurveyRecord],
    litho: list = None,
    assays: list = None,
    alterations: list = None,
    mineralizations: list = None,
    structure: list = None,
    subdivide: bool = True,
    max_segment: float = 5.0,
) -> DrillHole:
    """
    Build a complete DrillHole object with computed trajectory.
    """
    trajectory = compute_trajectory(collar, survey, subdivide, max_segment)
    return DrillHole(
        hole_id=collar.hole_id,
        collar=collar,
        survey=survey,
        litho=litho or [],
        assays=assays or [],
        alterations=alterations or [],
        mineralizations=mineralizations or [],
        structure=structure or [],
        trajectory=trajectory,
    )


# ---------------------------------------------------------------------------
# v2.7.6.9 — orientation helpers for the on-screen section rose
# ---------------------------------------------------------------------------
# Moved from core.export_layout when the export feature was removed
# (AUDIT_V2.7.6.9.md). These are pure plan-view geometry used by the
# section canvas "localisation rose" badge — nothing export-specific.

def section_azimuth_degrees(x1: float, y1: float, x2: float, y2: float) -> float:
    """Geographic azimuth (0-360°, clockwise from north) of a section line."""
    if x1 == x2 and y1 == y2:
        return 0.0
    azimuth = math.degrees(math.atan2(x2 - x1, y2 - y1))
    return (azimuth + 360.0) % 360.0


def azimuth_label(azimuth: float) -> str:
    """« N045° » style label (whole degrees, always 3 digits)."""
    return f"N{round(azimuth) % 360:03d}°"


def compass_needle(azimuth: float, cx: float, cy: float,
                   radius: float) -> dict:
    """Two-tone needle of a simple, legible compass rose.

    ``azimuth`` = direction of true north on screen (0 = up, clockwise).
    Returns the ``north`` (filled) and ``south`` (light) polygons plus the
    ``label`` position of the letter N. Single geometric source shared by
    every view that draws this rose.
    """
    angle = math.radians(azimuth % 360.0)
    ux, uy = math.sin(angle), -math.cos(angle)   # towards north
    px, py = -uy, ux                             # perpendicular
    tip = (cx + ux * radius, cy + uy * radius)
    tail = (cx - ux * radius, cy - uy * radius)
    half = radius * 0.34
    left = (cx - px * half, cy - py * half)
    right = (cx + px * half, cy + py * half)
    label_gap = radius * 1.32
    return {
        "north": [tip, left, right],
        "south": [tail, right, left],
        "center": (cx, cy),
        "tip": tip,
        "label": (cx + ux * label_gap, cy + uy * label_gap),
    }


def section_rose_model(azimuth: float, cx: float, cy: float,
                       radius: float) -> dict:
    """Localisation rose of a section: plan view, north always up.

    Screen review 18/08/2026: a vertical section has no "north on screen" —
    its horizontal axis is a ground direction, its vertical axis is
    elevation, so a rotating needle inside the section plane is ambiguous.
    A mini plan view is drawn instead: north stays up and the section trace
    is shown as an arrow at its real azimuth, from P1 to P2.
    """
    needle = compass_needle(0.0, cx, cy, radius)
    angle = math.radians(azimuth % 360.0)
    ux, uy = math.sin(angle), -math.cos(angle)
    reach = radius * 1.05
    tail = (cx - ux * reach, cy - uy * reach)     # P1 end
    head = (cx + ux * reach, cy + uy * reach)     # P2 end
    wing = radius * 0.28
    px, py = -uy, ux
    arrow = [
        head,
        (head[0] - ux * wing + px * wing * 0.55,
         head[1] - uy * wing + py * wing * 0.55),
        (head[0] - ux * wing - px * wing * 0.55,
         head[1] - uy * wing - py * wing * 0.55)]
    return {
        "needle": needle,
        "p1": tail,
        "p2": head,
        "arrow": arrow,
        "p1_label": (cx - ux * reach * 1.32, cy - uy * reach * 1.32),
        "p2_label": (cx + ux * reach * 1.32, cy + uy * reach * 1.32),
    }
