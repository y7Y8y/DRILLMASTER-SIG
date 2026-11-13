"""
DrillMaster — Cross-Section Generation (V2)
============================================
Projects drillhole trajectories onto a vertical plane defined by a
2-point section line on the QGIS map.

V2 changes:
  - SectionLine computes azimuth, direction label
  - Offset calculated PER trajectory point (not just collar)
  - Real elevation kept separate from exaggerated elevation
  - SectionResult stores section metadata for display
"""

from __future__ import annotations

import colorsys
import hashlib
import math
from dataclasses import dataclass, field
from typing import Optional

from .display_profiles import make_display_transform

from .data_model import (
    CoreImageRecord, DrillHole, GeotechRecord, IntervalRecord,
    TrajectoryPoint)


# Compass directions for 8-sector labeling
_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


@dataclass
class SectionLine:
    """A section line defined by two points on the map (2D)."""
    x1: float
    y1: float
    x2: float
    y2: float
    name: str = ""        # e.g. "Section 001"
    section_id: int = 0   # auto-incremented

    @property
    def dx(self) -> float:
        return self.x2 - self.x1

    @property
    def dy(self) -> float:
        return self.y2 - self.y1

    @property
    def length(self) -> float:
        return math.hypot(self.dx, self.dy)

    @property
    def unit_x(self) -> float:
        l = self.length
        return self.dx / l if l > 0 else 0.0

    @property
    def unit_y(self) -> float:
        l = self.length
        return self.dy / l if l > 0 else 0.0

    @property
    def normal_x(self) -> float:
        """Unit normal x-component (perpendicular, pointing left of direction)."""
        return -self.unit_y

    @property
    def normal_y(self) -> float:
        """Unit normal y-component (perpendicular, pointing left of direction)."""
        return self.unit_x

    @property
    def azimuth(self) -> float:
        """
        Azimuth of the section line direction (degrees from North).
        0=N, 90=E, 180=S, 270=W.
        Uses map convention: X=East, Y=North.
        """
        if self.length < 1e-9:
            return 0.0
        # atan2(dx, dy) because az=0 is North (Y axis), az=90 is East (X axis)
        az = math.degrees(math.atan2(self.dx, self.dy))
        return az % 360

    def flip(self) -> None:
        """338 — inverse P1/P2 sur place (azimut +180°, même ligne).
        Comme les grands logiciels : « retourner la coupe » sans
        retracer.  azimuth/length/direction_label sont des propriétés
        dérivées : tout suit automatiquement."""
        self.x1, self.x2 = self.x2, self.x1
        self.y1, self.y2 = self.y2, self.y1

    @property
    def direction_label(self) -> str:
        """Ends of the section as read from P1 to P2, e.g. 'NE -> SW'.

        v2.7.6.3 (ORI-03) — correction d'une inversion : l'azimut est la
        direction **de P1 vers P2**. L'extrémité de départ est donc du côté
        opposé (azimut + 180). Une coupe d'azimut 234° se lit « NE -> SW » :
        elle part de son extrémité nord-est et se dirige vers le sud-ouest.
        L'ancienne formule affichait « SW -> NE », en contradiction avec
        l'azimut inscrit juste à côté et avec les repères P1/P2.
        """
        return (f"{compass16(self.azimuth + 180)} -> "
                f"{compass16(self.azimuth)}")

    @property
    def summary(self) -> str:
        """One-line summary for display."""
        return (f"Direction: {self.direction_label}  |  Azimut: {self.azimuth:.0f} deg  |  "
                f"Longueur: {self.length:.0f} m")


_COMPASS16 = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")


def compass16(az: float) -> str:
    """333/337 — rose 16 secteurs : 290° -> « WNW ».  Partagée par la
    bannière 2D, l'historique et tout affichage de direction (337 :
    UNE seule méthode de lecture, défendable et cohérente)."""
    return _COMPASS16[int((az % 360 + 11.25) / 22.5) % 16]


def _azimuth_to_compass(az: float) -> str:
    """Convert an azimuth angle to an 8-sector compass label."""
    az = az % 360
    sector = int((az + 22.5) / 45) % 8
    return _COMPASS[sector]


@dataclass
class ProjectedPoint:
    """A trajectory point projected onto the section plane."""
    along: float          # distance along the section line
    elevation: float      # REAL elevation (not exaggerated)
    offset: float         # REAL signed perpendicular distance at this point
    depth: float          # down-hole depth
    x_map: float          # original map X
    y_map: float          # original map Y


@dataclass
class ProjectedInterval:
    """An interval (litho/assay) projected onto the section."""
    along_top: float
    along_bottom: float
    elev_top: float       # REAL elevation
    elev_bottom: float    # REAL elevation
    offset: float         # signed lateral offset
    attributes: dict
    hole_id: str
    # v2.7.2 — components (multi-code lithologies, split alterations/
    # mineralizations) and source depths for inspection (V-05).
    components: list = field(default_factory=list)
    from_depth: float = 0.0
    to_depth: float = 0.0


@dataclass
class ProjectedStructure:
    """One point-wise structure measurement projected onto the section.

    v2.9.260 — step 2 of the ``structure`` rendering: the measurement is
    a point at its measured depth (same interpolation contract as the
    QGIS layer and the 3D view); the orientation values stay available
    for the drawing/3D steps without being interpreted here.
    """
    along: float
    elevation: float
    offset: float
    depth: float
    structure_type: str = ""
    dip: Optional[float] = None
    dip_direction: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    confidence: Optional[str] = None
    comment: str = ""


@dataclass
class ProjectedHole:
    """A complete drillhole projected onto the section plane."""
    hole_id: str
    offset: float
    points: list[ProjectedPoint] = field(default_factory=list)
    litho: list[ProjectedInterval] = field(default_factory=list)
    assays: list[ProjectedInterval] = field(default_factory=list)
    alterations: list[ProjectedInterval] = field(default_factory=list)
    mineralizations: list[ProjectedInterval] = field(default_factory=list)
    # v2.9.260 — point-wise structure measurements (step 2 rendering).
    structure: list[ProjectedStructure] = field(default_factory=list)
    # v2.9.262 — imagerie de trou : les enregistrements source sont
    # transportés tels quels sur le trou projeté. La piste 2D les dessine
    # à la profondeur source via _band_poly (from/to), et le rendu résout
    # les chemins au moment du dessin (cache ≈ 512 px).
    imagery: list[CoreImageRecord] = field(default_factory=list)
    # v2.9.264 — géotechnique groupée : enregistrements source transportés
    # tels quels (intervalles RQD/CR, points ou intervalles densité).
    geotech: list[GeotechRecord] = field(default_factory=list)
    collar_along: float = 0.0
    collar_elev: float = 0.0
    total_depth: float = 0.0


@dataclass
class SectionResult:
    """Complete result of a section generation."""
    line: SectionLine
    holes: list[ProjectedHole] = field(default_factory=list)
    buffer: float = 50.0
    buffer_mode: str = "collar"  # collar | trajectory
    vertical_exaggeration: float = 1.0
    # Bounding box in REAL section coordinates
    min_along: float = 0.0
    max_along: float = 0.0
    min_elev: float = 0.0       # visual bound (includes small padding)
    max_elev: float = 0.0
    data_min_elev: float = 0.0  # exact trajectory extrema for grid ticks
    data_max_elev: float = 0.0
    # v2.9.0 — topographie : profil de sol (along, elev) le long de la
    # ligne de coupe, ancré aux collets, et sa source ("dem", "csv" ou
    # "collars") — la source pilote le style du trait (plein vs pointillé).
    surface: list = field(default_factory=list)
    surface_source: str = ""
    # v2.9.179 — forages EXCLUS de la coupe par l'utilisateur
    # (proposition validée : buffer sélectionne, l'exclusion retire ;
    # exclu = absent — échelles et ligne de sol recalculées sans lui).
    excluded_hole_ids: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core projection
# ---------------------------------------------------------------------------
def compute_isotropic_scales(available_width: float, horizontal_range: float,
                             vertical_exaggeration: float = 1.0) -> tuple[float, float]:
    """Return truthful pixels/unit scales: sy/sx equals vertical exaggeration."""
    sx = max(float(available_width), 1.0) / max(float(horizontal_range), 1e-9)
    return sx, sx * max(float(vertical_exaggeration), 0.01)


def grid_tick_values(minimum: float, maximum: float, step: float) -> list[float]:
    """Return rounded ticks strictly inside the real axis extent."""
    if step <= 0 or maximum < minimum:
        return []
    first = math.ceil(minimum / step) * step
    count = max(int(math.floor((maximum - first) / step + 1e-9)) + 1, 0)
    return [round(first + index * step, 10) for index in range(count)]


def _nice_step(raw: float) -> float:
    """Round a raw step to the nearest 1/2/5×10ⁿ."""
    if raw <= 0:
        return 1.0
    exponent = math.floor(math.log10(raw))
    base = 10 ** exponent
    fraction = raw / base
    if fraction < 1.5:
        return base
    if fraction < 3:
        return 2 * base
    if fraction < 7:
        return 5 * base
    return 10 * base


def depth_tick_steps(total_depth: float, step: float = 0.0,
                     label_every: int = 2) -> tuple[float, float]:
    """Depth backbone steps (v2.7.7).

    Returns ``(major_step, label_step)`` : graduation step and label step.
    ``step <= 0`` selects an automatic 1/2/5×10ⁿ step aiming at ~10-12
    graduations whatever the hole depth ; ``label_every`` is the number of
    graduations between two labels (>= 1).
    """
    every = max(1, int(label_every or 2))
    if not total_depth or total_depth <= 0:
        return (float(step) if step > 0 else 0.0), 0.0
    if step <= 0:
        step = _nice_step(total_depth / 12.0)
    else:
        step = float(step)
    if step <= 0:
        return 0.0, 0.0
    return step, step * every


def project_point_onto_section(
    x: float, y: float, line: SectionLine
) -> tuple[float, float]:
    """
    Project a map point onto the section line.
    Returns (along, offset) where:
      - along = distance along the line from P1
      - offset = signed perpendicular distance (positive = left of direction)
    """
    px = x - line.x1
    py = y - line.y1
    along = px * line.unit_x + py * line.unit_y
    offset = px * line.normal_x + py * line.normal_y
    return along, offset


def point_to_section_segment_distance(along: float, offset: float,
                                      line_length: float) -> float:
    """Euclidean plan distance to the finite P1-P2 segment."""
    if along < 0:
        return math.hypot(along, offset)
    if along > line_length:
        return math.hypot(along - line_length, offset)
    return abs(offset)


def drillhole_buffer_status(
    drillhole: DrillHole,
    line: SectionLine,
    buffer: float,
    buffer_mode: str = "collar",
) -> dict:
    """Return the auditable corridor distance/inclusion for one drillhole."""
    collar_along, collar_offset = project_point_onto_section(
        drillhole.collar.x, drillhole.collar.y, line)
    mode = buffer_mode if buffer_mode in ("collar", "trajectory") else "collar"
    collar_dist = point_to_section_segment_distance(
        collar_along, collar_offset, line.length)
    if mode == "trajectory":
        # v2.9.135 — trou trop loin pour atteindre le corridor : on ne
        # projette pas chaque station. Collet déjà dedans : inclus.
        reach = float(getattr(drillhole, "total_depth", 0.0) or 0.0)
        if math.isfinite(collar_dist) and collar_dist > (buffer + reach):
            return {
                "hole_id": drillhole.hole_id,
                "distance": collar_dist,
                "along": collar_along,
                "included": False,
                "mode": mode,
            }
        if math.isfinite(collar_dist) and collar_dist <= buffer:
            return {
                "hole_id": drillhole.hole_id,
                "distance": collar_dist,
                "along": collar_along,
                "included": True,
                "mode": mode,
            }
        candidates = []
        for point in drillhole.trajectory:
            along, offset = project_point_onto_section(point.x, point.y, line)
            distance = point_to_section_segment_distance(
                along, offset, line.length)
            candidates.append((distance, along))
        if candidates:
            distance, nearest_along = min(candidates, key=lambda value: value[0])
            included = distance <= buffer
        else:
            distance, nearest_along, included = float("inf"), collar_along, False
    else:
        distance = point_to_section_segment_distance(
            collar_along, collar_offset, line.length)
        nearest_along = collar_along
        included = distance <= buffer
    return {
        "hole_id": drillhole.hole_id,
        "distance": distance,
        "along": nearest_along,
        "included": included,
        "mode": mode,
    }


def group_shared_collars(
    drillholes: list[DrillHole], tolerance: float = 0.1
) -> list[list[DrillHole]]:
    """Group true XYZ collar coincidences, independent of section projection."""
    tolerance = max(float(tolerance), 0.0)
    groups: list[list[DrillHole]] = []
    for drillhole in sorted(drillholes, key=lambda value: value.hole_id):
        target = None
        for group in groups:
            reference = group[0].collar
            collar = drillhole.collar
            if (math.hypot(collar.x - reference.x,
                           collar.y - reference.y) <= tolerance
                    and abs(collar.z - reference.z) <= tolerance):
                target = group
                break
        if target is None:
            target = []
            groups.append(target)
        target.append(drillhole)
    return groups


def compute_buffer_diagnostics(
    drillholes: list[DrillHole], line: SectionLine, buffer: float,
    buffer_mode: str = "collar",
) -> list[dict]:
    """Return sorted inclusion diagnostics for display and testing."""
    statuses = [
        drillhole_buffer_status(dh, line, buffer, buffer_mode)
        for dh in drillholes if dh.trajectory
    ]
    return sorted(statuses, key=lambda status: (
        not status["included"], status["distance"], status["hole_id"]))


def generate_section(
    drillholes: list[DrillHole],
    line: SectionLine,
    buffer: float = 50.0,
    vertical_exaggeration: float = 1.0,
    buffer_mode: str = "collar",
    surface=None,
    surface_source: str = "",
    excluded_hole_ids=None,
    display_config=None,
) -> SectionResult:
    """Project drillholes onto a vertical section plane.

    ``buffer_mode='collar'`` is the predictable geological corridor rule: a
    hole is selected from the Euclidean map distance of its collar to the
    finite section segment (standard rounded buffer around P1/P2). ``trajectory`` is available for
    deviated holes whose trace
    enters the corridor even when their collar starts outside it.

    ``surface`` (v2.9.0) — optional ground-surface profile
    ``(along, elev)`` ALREADY sampled and anchored to the collars by the
    caller (core.topography): stored on the result and extending the
    vertical VISUAL extent so the ground line is never clipped.  The grid
    ticks keep the trajectory extrema — the surface is context, not data.
    ``surface_source`` is "dem" | "csv" | "collars" and drives the line
    style (solid for measured sources, dashed for the collar-only
    interpolation — lower visual confidence, same shape information).
    """
    buffer_mode = buffer_mode if buffer_mode in ("collar", "trajectory") else "collar"
    # v2.9.179 — exclusions utilisateur (proposition validée) : un
    # forage exclu est ABSENT du résultat — les échelles (Jenks) et la
    # ligne de sol se recalculent donc sans lui (l'appelant filtre
    # aussi ses collets pour le MNT).
    excluded = {str(h) for h in (excluded_hole_ids or []) if h}
    result = SectionResult(
        line=line,
        buffer=buffer,
        buffer_mode=buffer_mode,
        excluded_hole_ids=sorted(excluded),
        vertical_exaggeration=vertical_exaggeration,
    )
    if surface:
        result.surface = list(surface)
        result.surface_source = (
            surface_source if surface_source in ("dem", "csv", "collars") else "")

    if line.length < 1e-9:
        return result

    all_along = []
    all_elev = []

    for dh in drillholes:
        if not dh.trajectory:
            continue
        if dh.hole_id in excluded:
            continue
        # v2.9.289 — profil d'affichage par type d'ouvrage (RC/DD = None).
        T = make_display_transform(dh, display_config)

        collar_along, collar_offset = project_point_onto_section(
            dh.collar.x, dh.collar.y, line
        )
        status = drillhole_buffer_status(dh, line, buffer, buffer_mode)
        if not status["included"]:
            continue

        ph = ProjectedHole(
            hole_id=dh.hole_id,
            offset=collar_offset,
            collar_along=collar_along,
            collar_elev=dh.collar.z,
            total_depth=dh.total_depth,
        )

        # Project all trajectory points — each with its OWN offset
        for tp in dh.trajectory:
            along, offset = project_point_onto_section(tp.x, tp.y, line)
            # Store REAL elevation (no exaggeration here) — v2.9.289 :
            # l'AXE vertical d'affichage peut être transformé par profil.
            elev = T(tp.z) if T else tp.z
            ph.points.append(ProjectedPoint(
                along=along,
                elevation=elev,
                offset=offset,
                depth=tp.depth,
                x_map=tp.x,
                y_map=tp.y,
            ))
            all_along.append(along)
            all_elev.append(elev)

        # v2.9.316 — EOH ACTIF : si total_depth dépasse la trajectoire,
        # la trace est prolongée dans la dernière direction jusqu'à
        # l'EOH — le barreau EOH, les graduations et la piste profondeur
        # suivent la profondeur modifiée (« c'est la profondeur aussi »).
        td_eoh = float(getattr(dh, "total_depth", 0.0) or 0.0)
        if td_eoh > 0 and ph.points and \
                td_eoh > ph.points[-1].depth + 1e-9:
            lp = ph.points[-1]
            if len(ph.points) >= 2:
                pp = ph.points[-2]
                dd = lp.depth - pp.depth
                if dd > 1e-9:
                    ka = (lp.along - pp.along) / dd
                    ke = (lp.elevation - pp.elevation) / dd
                    ko = (lp.offset - pp.offset) / dd
                else:
                    ka = ke = ko = 0.0
            else:
                ka, ke, ko = 0.0, -1.0, 0.0
            ext = td_eoh - lp.depth
            ph.points.append(ProjectedPoint(
                along=lp.along + ka * ext,
                elevation=lp.elevation + ke * ext,
                offset=lp.offset + ko * ext,
                depth=td_eoh,
                x_map=lp.x_map, y_map=lp.y_map))
            all_along.append(ph.points[-1].along)
            all_elev.append(ph.points[-1].elevation)

        # Project litho
        if dh.litho:
            ph.litho = _project_intervals(dh, dh.litho, line)

        # Project assays
        if dh.assays:
            ph.assays = _project_intervals(dh, dh.assays, line)

        # v2.7.2 — project alterations and mineralizations as their own tracks
        if getattr(dh, "alterations", None):
            ph.alterations = _project_intervals(dh, dh.alterations, line)
        if getattr(dh, "mineralizations", None):
            ph.mineralizations = _project_intervals(
                dh, dh.mineralizations, line)

        # v2.9.260 — project point-wise structure measurements (step 2).
        if getattr(dh, "structure", None):
            ph.structure = _project_structures(dh, dh.structure, line)

        # v2.9.262 — imagerie : on transporte les enregistrements source.
        # Aucune découpe ni interpolation n'est nécessaire ici : le rendu
        # 2D place chaque bande à son from/to via _depth_tick_anchor.
        if getattr(dh, "imagery", None):
            ph.imagery = sorted(
                list(dh.imagery),
                key=lambda record: (float(record.from_m), float(record.to_m)))

        # v2.9.264 — géotechnique groupée : mêmes enregistrements source.
        if getattr(dh, "geotech", None):
            ph.geotech = list(dh.geotech)

        # v2.9.289 — intervalles/structures sur l'AXE transformé (jamais
        # par intervalle : from/to réels conservés, positions cohérentes).
        if T:
            for lst in (ph.litho, ph.assays, ph.alterations,
                        ph.mineralizations):
                for iv in lst:
                    iv.elev_top = T(iv.elev_top)
                    iv.elev_bottom = T(iv.elev_bottom)
            for st in ph.structure:
                st.elevation = T(st.elevation)

        result.holes.append(ph)

    # Bounding box in REAL coordinates
    if all_along:
        # The distance axis is defined from P1=0 to P2=line.length, not from
        # the first/last visible hole. Truly overhanging trajectories remain
        # visible beyond those endpoints.
        result.min_along = min(0.0, min(all_along))
        result.max_along = max(line.length, max(all_along))
        result.data_min_elev = min(all_elev)
        result.data_max_elev = max(all_elev)
        # Respiration verticale : ≥ 2 m (v2.9.68) / 2 % si plus grand
        # (v2.9.0 — ground line never clipped) ; ticks = data extrema.
        from .topography import merge_surface_into_range
        result.min_elev, result.max_elev = merge_surface_into_range(
            result.data_min_elev, result.data_max_elev, result.surface)
    else:
        result.min_along = 0.0
        result.max_along = line.length
        result.min_elev = 0.0
        result.max_elev = 100.0
        result.data_min_elev = 0.0
        result.data_max_elev = 100.0

    return result


def _project_structures(
    dh: DrillHole,
    records: list,
    line: SectionLine,
) -> list[ProjectedStructure]:
    """Project point-wise structure measurements at their measured depth.

    v2.9.260 (step 2).  Uses the same trajectory interpolation as the
    QGIS ``Structures`` layer (``geometry.depth_to_xyz``) so the section
    always agrees with the map layer.  A measurement outside the
    trajectory is skipped, never invented.
    """
    from .geometry import depth_to_xyz

    result = []
    for record in records:
        xyz = depth_to_xyz(dh.trajectory, float(record.depth))
        if xyz is None:
            continue
        along, offset = project_point_onto_section(xyz[0], xyz[1], line)
        result.append(ProjectedStructure(
            along=along,
            elevation=float(xyz[2]),
            offset=offset,
            depth=float(record.depth),
            structure_type=str(record.type or ""),
            dip=record.dip,
            dip_direction=record.dip_direction,
            alpha=record.alpha,
            beta=record.beta,
            confidence=record.confidence,
            comment=str(record.comment or ""),
        ))
    return result


def _project_intervals(
    dh: DrillHole,
    intervals: list[IntervalRecord],
    line: SectionLine,
) -> list[ProjectedInterval]:
    """Project intervals with per-point offset."""
    from .geometry import depth_to_xyz

    result = []
    for iv in intervals:
        top_xyz = depth_to_xyz(dh.trajectory, iv.from_depth)
        bot_xyz = depth_to_xyz(dh.trajectory, iv.to_depth)
        if top_xyz is None or bot_xyz is None:
            continue

        top_along, top_off = project_point_onto_section(top_xyz[0], top_xyz[1], line)
        bot_along, bot_off = project_point_onto_section(bot_xyz[0], bot_xyz[1], line)

        result.append(ProjectedInterval(
            along_top=top_along,
            along_bottom=bot_along,
            elev_top=top_xyz[2],       # REAL elevation
            elev_bottom=bot_xyz[2],    # REAL elevation
            offset=(top_off + bot_off) / 2,  # average offset
            attributes=iv.attributes,
            hole_id=dh.hole_id,
            components=list(iv.components or []),
            from_depth=iv.from_depth,
            to_depth=iv.to_depth,
        ))
    return result



# ---------------------------------------------------------------------------
# Assay value classification (used for assay bar colours on sections)
# ---------------------------------------------------------------------------
CLASSIFICATION_METHODS: dict[str, str] = {
    "linear":   "Continu — linéaire (min-max)",
    "log":      "Continu — logarithmique",
    "equal":    "Classes — intervalles égaux",
    "quantile": "Classes — quantiles",
    "jenks":    "Classes — Jenks (ruptures naturelles)",
    "manual":   "Classes — seuils manuels",
}

# 372 — retour écran (« vert sombre puis clair, c'est bizarre ») :
# TOUTES les palettes montent du CLAIR vers le SOMBRE quand la teneur
# augmente (règle séquentielle, luminance décroissante de bout en bout).
ASSAY_RAMPS: dict[str, str] = {
    "grade": "Vert - jaune - rouge (faible -> fort)",
    "viridis": "Viridis inversé (jaune -> vert -> violet, clair -> foncé)",
    "blue_red": "Bleus (clair -> foncé)",
}


def _finite_numbers(values):
    return [
        float(v) for v in values
        if isinstance(v, (int, float)) and math.isfinite(float(v))
    ]


def jenks_breaks(values: list[float], n_classes: int = 7) -> list[float]:
    """Compute Fisher-Jenks natural breaks with bounded input size."""
    data = sorted(_finite_numbers(values))
    if not data:
        return []
    unique_count = len(set(data))
    classes = max(1, min(int(n_classes), unique_count))
    if classes == 1:
        return [data[0], data[-1]]
    # O(n²k) dynamic programming: deterministic quantile sampling prevents
    # large assay files from freezing the QGIS UI.
    if len(data) > 500:
        source = data
        data = [
            source[round(i * (len(source) - 1) / 499)]
            for i in range(500)
        ]
    n = len(data)
    lower = [[0] * (classes + 1) for _ in range(n + 1)]
    variance = [[float("inf")] * (classes + 1) for _ in range(n + 1)]
    for column in range(1, classes + 1):
        lower[0][column] = 1
        variance[0][column] = 0.0

    for length in range(1, n + 1):
        s1 = s2 = weight = 0.0
        current_variance = 0.0
        for offset in range(1, length + 1):
            lower_index = length - offset + 1
            value = data[lower_index - 1]
            weight += 1.0
            s1 += value
            s2 += value * value
            current_variance = s2 - (s1 * s1) / weight
            previous = lower_index - 1
            if previous:
                for column in range(2, classes + 1):
                    candidate = current_variance + variance[previous][column - 1]
                    if variance[length][column] >= candidate:
                        lower[length][column] = lower_index
                        variance[length][column] = candidate
        lower[length][1] = 1
        variance[length][1] = current_variance

    breaks = [data[0]] + [data[-1]] * classes
    position = n
    for column in range(classes, 1, -1):
        index = max(int(lower[position][column]) - 2, 0)
        breaks[column - 1] = data[index]
        position = max(int(lower[position][column]) - 1, 0)
    return breaks


def adaptive_break_step(vmin: float, vmax: float) -> float:
    """358 — pas d'arrondi 1/2/5×10ⁿ adapté à l'ÉTENDUE réelle des
    données (pas à leur magnitude) : « comprend vraiment les
    données ».  ~12 classes visées → bornes rondes ET nombreuses
    (Rb 6–1636 → pas 200 ; Li 100–12200 → pas 1000)."""
    span = max(float(vmax) - float(vmin), 1e-9)
    target = span / 12.0
    exp = 10.0 ** math.floor(math.log10(target))
    for m in (1.0, 2.0, 5.0, 10.0):
        if m * exp >= target:
            return float(m * exp)
    return 10.0 * exp


def round_jenks_breaks(boundaries: list[float]) -> tuple[list[float], float]:
    """367 — bornes = GRILLE complète de multiples du pas qui couvre
    les données (retour « les ruptures sont pas grandes ?? » : bornes
    206,3 / 2 100 et dernière classe 12 100–12 200 minuscule).  Plus
    aucune borne hors grille, plus aucune classe microscopique :
    first = floor(min/pas), last = ceil(max/pas).  Si trop de classes,
    le pas double (reste 1/2/5×10ⁿ)."""
    if len(boundaries) < 3:
        return list(boundaries), 0.0
    lo = float(boundaries[0])
    hi = float(boundaries[-1])
    step = adaptive_break_step(lo, hi)
    while math.ceil(hi / step) - math.floor(lo / step) > 10:
        step *= 2.0
    first = math.floor(lo / step) * step
    last = math.ceil(hi / step) * step
    count = int(round((last - first) / step))
    rounded = [round(first + i * step, 10) for i in range(count + 1)]
    return rounded, step


def compute_assay_scale(values: list[float], method: str = "linear",
                        n_classes: int = 5,
                        manual_breaks: list[float] = None,
                        round_breaks: bool = True) -> dict:
    """Build a reusable assay scale for both the map and section views."""
    vals = _finite_numbers(values)
    selected_method = method if method in CLASSIFICATION_METHODS else "linear"
    clean_breaks = sorted(set(_finite_numbers(manual_breaks or [])))
    if selected_method == "manual" and not clean_breaks:
        selected_method = "linear"

    scale = {
        "method": selected_method,
        "n_classes": (len(clean_breaks) + 1 if selected_method == "manual"
                      else max(2, int(n_classes))),
        "vmin": min(vals) if vals else 0.0,
        "vmax": max(vals) if vals else 1.0,
        "boundaries": [],
        "raw_boundaries": [],
        "manual_breaks": clean_breaks,
        "round_breaks": bool(round_breaks),
        "rounding_step": 0.0,
    }
    if not vals:
        return scale

    vmin, vmax = scale["vmin"], scale["vmax"]
    n = scale["n_classes"]

    if selected_method == "equal":
        step = (vmax - vmin) / n if vmax > vmin else 1.0
        scale["boundaries"] = [vmin + i * step for i in range(n + 1)]
    elif selected_method == "quantile":
        svals = sorted(vals)
        bounds = []
        for i in range(n + 1):
            idx = (len(svals) - 1) * i / n
            lo = int(math.floor(idx))
            hi = min(lo + 1, len(svals) - 1)
            t = idx - lo
            bounds.append(svals[lo] * (1 - t) + svals[hi] * t)
        scale["boundaries"] = bounds
    elif selected_method == "jenks":
        raw = jenks_breaks(vals, n)
        scale["raw_boundaries"] = list(raw)
        if round_breaks:
            bounds, rounding_step = round_jenks_breaks(raw)
            scale["rounding_step"] = rounding_step
        else:
            bounds = raw
        scale["boundaries"] = bounds
        scale["n_classes"] = max(len(bounds) - 1, 1)
    elif selected_method == "log":
        pos = [v for v in vals if v > 0]
        scale["vmin_log"] = min(pos) if pos else 1e-9
    elif selected_method == "manual":
        # Keep all user thresholds for stable project-wide classes, even when
        # a threshold falls outside the values visible in one section.
        scale["boundaries"] = [vmin] + clean_breaks + [vmax]
    return scale


def classify_assay(value, scale: dict) -> tuple[int, float]:
    """Return ``(class_index, colour_ratio)`` for an assay value."""
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return 0, 0.0
    method = scale.get("method", "linear")
    vmin, vmax = scale.get("vmin", 0.0), scale.get("vmax", 1.0)
    n = max(2, scale.get("n_classes", 5))

    if method == "manual":
        idx = sum(value >= b for b in scale.get("manual_breaks", []))
        idx = min(idx, n - 1)
        return idx, idx / max(n - 1, 1)

    if method in ("equal", "quantile", "jenks"):
        bounds = scale.get("boundaries", [])
        idx = 0
        for i in range(1, len(bounds) - 1):
            if value >= bounds[i]:
                idx = i
        idx = min(idx, n - 1)
        return idx, idx / max(n - 1, 1)

    if method == "log":
        lo = scale.get("vmin_log", 1e-9)
        hi = vmax if vmax > lo else lo * 10
        if value <= lo:
            return 0, 0.0
        try:
            r = (math.log10(value) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
        except (ValueError, ZeroDivisionError):
            r = 0.0
        return min(max(int(r * n), 0), n - 1), min(max(r, 0.0), 1.0)

    rng = vmax - vmin if vmax > vmin else 1.0
    r = (value - vmin) / rng
    return min(max(int(r * n), 0), n - 1), min(max(r, 0.0), 1.0)


def assay_scale_classes(scale: dict) -> list[tuple[float, float, float]]:
    """Return ``(lower, upper, colour_ratio)`` classes for legends/QGIS."""
    vmin = float(scale.get("vmin", 0.0))
    vmax = float(scale.get("vmax", 1.0))
    if vmax <= vmin:
        return [(vmin, vmax, 0.5)]
    method = scale.get("method", "linear")
    n = max(2, int(scale.get("n_classes", 5)))

    if method in ("equal", "quantile", "jenks"):
        bounds = list(scale.get("boundaries", []))
    elif method == "manual":
        breaks = [b for b in scale.get("manual_breaks", []) if vmin < b < vmax]
        bounds = [vmin] + breaks + [vmax]
        n = max(1, len(bounds) - 1)
    elif method == "log":
        lo = max(float(scale.get("vmin_log", 1e-9)), 1e-12)
        hi = max(vmax, lo * 10)
        bounds = [lo * ((hi / lo) ** (i / n)) for i in range(n + 1)]
        if vmin < lo:
            bounds[0] = vmin
    else:
        step = (vmax - vmin) / n
        bounds = [vmin + i * step for i in range(n + 1)]

    # Repeated quantile bounds create zero-width QGIS ranges; collapse them.
    compact = []
    for bound in bounds:
        if not compact or bound > compact[-1]:
            compact.append(bound)
    bounds = compact
    if len(bounds) < 2:
        return [(vmin, vmax, 0.5)]
    count = len(bounds) - 1
    return [
        (bounds[i], bounds[i + 1], i / max(count - 1, 1))
        for i in range(count)
    ]


def _interpolate_rgb(c1, c2, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


def assay_ramp_rgb(r: float, palette: str = "grade") -> str:
    """Return an unambiguous ``#RRGGBB`` colour for an assay ratio."""
    r = min(max(float(r), 0.0), 1.0)
    ramps = {
        # 380 — « je dis de revenir à CETTE palette » (légende en
        # capture) : la ramp D'ORIGINE vert vif → jaune → rouge vif,
        # celle des anciennes versions — abandon des pastels/turbo.
        "grade": ((0, 200, 0), (255, 220, 0), (255, 0, 0)),
        "viridis": ((253, 231, 37), (33, 145, 140), (68, 1, 84)),
        "blue_red": ((222, 235, 247), (66, 146, 198), (8, 48, 107)),
    }
    stops = ramps.get(palette, ramps["grade"])
    n = len(stops) - 1
    x = r * n
    i = min(int(x), n - 1)
    c = _interpolate_rgb(stops[i], stops[i + 1], x - i)
    return f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}"


def generated_litho_color(code: str) -> str:
    """Generate a stable, distinct fallback colour for an unknown code.

    Hash déterministe — dernier recours quand la bibliothèque ne
    reconnaît pas le code. Aucune table de codes projet.
    """
    digest = hashlib.sha1((code or "LITHO").encode("utf-8")).digest()
    # étaler les teintes (évite clusters voisins)
    hue = (int.from_bytes(digest[:2], "big") * 0.6180339887) % 1.0
    # v2.9.290 — aplats VIFS et distincts (retour écran « référentiel
    # pauvre en couleurs ») : saturation/valence relevées, litho ET
    # altérations (même générateur de repli).
    saturation = 0.75 + (digest[2] / 255.0) * 0.20  # 0.75–0.95
    value = 0.80 + (digest[3] / 255.0) * 0.18       # 0.80–0.98
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    return "#{:02X}{:02X}{:02X}".format(*(round(v * 255) for v in rgb))


def suggested_litho_color(code: str) -> str:
    """Couleur d'aide pour un code litho — flux universel.

    1) famille bibliothèque si reconnue ;
    2) sinon hash stable (generated_litho_color).

    Le Référentiel projet reste toujours prioritaire côté appelant.
    Pas de table de codes spécifiques à un site.
    """
    try:
        from .lithology_taxonomy import suggest_lithology_family
        family = suggest_lithology_family(code)
    except ImportError:  # pragma: no cover
        family = None
    if family and family.get("color"):
        col = family["color"]
        # v2.9.304 — « couleurs vives, certaines manquent » : une couleur
        # de famille TERNE (peu saturée ou sombre) est remplacée par la
        # couleur générée vive ; les familles déjà vives restent telles
        # quelles (palettes verbatim préservées).
        try:
            import colorsys
            r = int(col[1:3], 16) / 255.0
            g = int(col[3:5], 16) / 255.0
            b = int(col[5:7], 16) / 255.0
            _h, sat, val = colorsys.rgb_to_hsv(r, g, b)
            if sat >= 0.45 and val >= 0.55:
                return col
        except (ValueError, IndexError):
            return col
        return generated_litho_color(code)
    return generated_litho_color(code)


def get_litho_style(code: str, custom_styles: dict = None) -> dict:
    # v2.9.79 — flux simple et universel (= altération) :
    #   1) Référentiel projet (custom_styles) — choix user, toujours roi ;
    #   2) bibliothèque famille (suggestion) ;
    #   3) hash stable.
    fallback = suggested_litho_color(code)
    style = custom_styles.get(code, {}) if custom_styles else {}
    if not isinstance(style, dict):
        style = {"color": style}
    # v2.9.320 — « visible » du Référentiel TRANSMIS : les légendes
    # filtrent avec .get("visible", True) ; sans cette clé, un code
    # désactivé au Référentiel restait listé en légende (retour écran :
    # « quand tu désactives dans référentiel il ne prend pas en compte
    # dans la légende »).
    return {
        "color": style.get("color") or fallback,
        "pattern": style.get("pattern", ""),
        "label": style.get("label") or code,
        "visible": style.get("visible", True),
    }


def get_litho_color(code: str, custom_styles: dict = None) -> str:
    return get_litho_style(code, custom_styles)["color"]


def get_all_litho_codes(drillholes: list[DrillHole]) -> list[str]:
    """Every drawable lithology code, including multi-code components.

    v2.7.3 : component raw codes count too — a vein appearing only inside
    composite intervals must still show up in legends and QGIS categories
    (the legend must decode everything the views can draw).
    """
    codes = set()
    for dh in drillholes:
        for iv in dh.litho:
            component_codes = [c.raw_code for c in (iv.components or [])
                               if c.raw_code]
            if component_codes:
                codes.update(component_codes)
                continue
            code = iv.attributes.get("lithology", "")
            if code:
                codes.add(code)
    return sorted(codes)
