"""Track layout model for the 2D section (v2.7.7).

Single source of truth for track positions, lanes, gaps and auto-collapse.
The section canvas consumes the plan ; the future 3D view and any native
QGIS print layout will reuse the same proportions, so the rules are never
re-implemented per view.

Conventions (decided 19/08/2026 — AUDIT_V2.7.7.md) :

- The lithology column is centred on the hole trace (main axis).
- Coded tracks stack from the inside out. Canonical inner → outer order on
  a side : assays, alterations, mineralizations, structures (the structures
  lane is a reserved slot, drawn when v2.9 delivers STR-01).
- Depth ticks/labels are the backbone of the log : they always occupy the
  innermost lane of their side, next to the trace.
- Auto-collapse : a hidden or empty track leaves no hole — the next lane
  shifts inward automatically.
- Gaps are uniform (default 2 px ≈ 0,5 mm at 96 dpi).

v2.7.10.12 — band geometry follows the DRAWN trace: from/to band edges are
perpendicular to the scene-space polyline (same normal as the depth tick
rungs), and style codes shrink (font size) to fit the band width before
any elision is considered.

Everything is expressed in scene pixels from the trace centre (negative =
left), exactly like the rest of the canvas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

SIDE_LEFT = "left"
SIDE_RIGHT = "right"
KNOWN_SIDES = (SIDE_LEFT, SIDE_RIGHT)

# Canonical stacking order within one side, from the trace outward.
# v2.9.122 — intercepts (barre de seuil) juste à l'extérieur des teneurs.
# v2.9.262 — retour écran « bandes Imagerie flottantes » : la piste
# Imagerie est placée IMMÉDIATEMENT contre la colonne litho (avant les
# autres voies), sur son côté, pour que la photo reste collée à la
# trajectoire au lieu de se retrouver loin de la trace après plusieurs
# voies (ex. structures/assays).
CANONICAL_ORDER = (
    "imagery", "assays", "intercepts", "alterations", "mineralizations",
    "structures", "rqd", "recovery", "density")

DEFAULT_GAP = 1.5          # px — v2.9.20 un peu plus serré (teneurs↔prof)


def _sign(side: str) -> float:
    return 1.0 if side == SIDE_RIGHT else -1.0


def depth_lane_width(overhang: float, label_width: float) -> float:
    """Width of the depth lane. The tick itself is CENTRED on the trace
    (v2.7.8 convention) so the lane only reserves what sticks out beyond
    the litho band : tick overhang + gap + the measured label width.

    v2.9.20 — gap 2→1 px : rapproche un peu teneurs et profondeurs.
    """
    return max(float(overhang), 0.0) + 1.0 + max(float(label_width), 0.0)


def estimated_depth_label_width(font_size: float, digits: int = 5) -> float:
    """Fallback label width ≈ 0,55 em per digit (no font metrics available).
    Real measurements should be preferred whenever Qt is present."""
    return 0.55 * float(font_size) * max(int(digits), 1)


def scene_normal(dx: float, dy: float) -> tuple[float, float]:
    """Unit normal to a SCENE-space direction.

    v2.7.8.1 — the tick perpendicularity is computed directly on the
    DRAWN segment (scene coordinates, y down). No data-space tangent, no
    scale pair, no sign assumption : the rung is perpendicular to the
    polyline by construction, whatever the exaggeration or the y-flip of
    the scene mapping.
    """
    length = math.hypot(dx, dy) or 1.0
    return -dy / length, dx / length


def pattern_rotation_degrees(dx: float, dy: float) -> float:
    """Rotation (degrees, Qt convention) to align a brush pattern with a
    band whose SCENE direction is (dx, dy).

    The patterns are defined for a vertical band (hole axis pointing
    down, direction (0, +1) in scene coordinates). The rotation keeps
    every hatch (« horizontal », « diagonale »…) perpendicular/relative to
    the LOCAL band direction, so the motif follows the dip of the hole.
    Returns 0 for a vertical band.
    """
    angle = math.degrees(math.atan2(float(dy), float(dx)))
    return angle - 90.0


def depth_label_base(tick_end_x: float, tick_end_y: float,
                     normal_x: float, normal_y: float,
                     gap: float = 2.0) -> tuple[float, float]:
    """Anchor point of a depth label : just OUTSIDE the tick end, along the
    outward normal — the label never covers the tick line."""
    return (float(tick_end_x) + float(normal_x) * gap,
            float(tick_end_y) + float(normal_y) * gap)


def depth_tick_segment(trace_x: float, trace_y: float,
                       tangent_dx: float, tangent_dy: float,
                       half_length: float, side: str) -> dict:
    """Depth tick as a ladder rung (v2.7.8 convention).

    A fixed-length segment CENTRED on the hole trace point, perpendicular
    to the DRAWN segment direction — ``tangent_dx/dy`` are scene-space
    deltas of the bracketing polyline points (v2.7.8.1). ``side`` orients
    the normal so the reported ``side_end`` is the end on the chosen
    side — the label anchors there.
    """
    nx, ny = scene_normal(tangent_dx, tangent_dy)
    if nx * _sign(side) < 0:
        nx, ny = -nx, -ny
    half = max(float(half_length), 0.1)
    x1 = float(trace_x) - nx * half
    y1 = float(trace_y) - ny * half
    x2 = float(trace_x) + nx * half
    y2 = float(trace_y) + ny * half
    return {
        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        "nx": nx, "ny": ny,
        "side_end": (x2, y2),
    }


@dataclass
class TrackLane:
    """One drawn lane. ``x0``/``x1`` bound the lane (x0 <= x1) ;
    ``inner_edge`` is the edge closest to the trace."""
    key: str
    side: str
    x0: float
    x1: float

    @property
    def inner_edge(self) -> float:
        return self.x0 if self.side == SIDE_RIGHT else self.x1

    @property
    def outer_edge(self) -> float:
        return self.x1 if self.side == SIDE_RIGHT else self.x0

    @property
    def width(self) -> float:
        return self.x1 - self.x0


@dataclass
class TrackPlan:
    """Result of :func:`plan_tracks`. ``by_key`` holds the drawn lanes ;
    ``depth`` is the depth backbone lane (or None) ; the extents are the
    outermost edges reached on each side (useful for margins)."""
    lanes: list[TrackLane] = field(default_factory=list)
    by_key: dict[str, TrackLane] = field(default_factory=dict)
    depth: TrackLane | None = None
    left_extent: float = 0.0
    right_extent: float = 0.0


def plan_tracks(*, litho_visible: bool, litho_width: float,
                depth_visible: bool, depth_side: str, depth_lane_w: float,
                tracks: dict, gap: float = DEFAULT_GAP,
                left_reserve: float = 0.0) -> TrackPlan:
    """Compute the lane stack of one hole.

    ``tracks`` maps a track key to ``{"side": "left"|"right",
    "width": float, "active": bool}`` — ``active`` already encodes
    visibility AND data presence (that is what makes auto-collapse work).

    ``left_reserve`` (v2.7.11.1 — CM-03) : espace réservé À GAUCHE de la
    bande litho pour le rail des barrettes secondaires (D-01) — auparavant
    le rail marchait sur les voies voisines dès le troisième secondaire.
    Avec la valeur par défaut ``0.0`` le plan historique est inchangé.

    Unknown keys are ignored ; a lane declared on an unknown side is
    skipped rather than drawn anywhere. Never raises.
    """
    litho_half = (float(litho_width) / 2.0) if litho_visible else 0.0
    gap = max(float(gap), 0.0)
    left_reserve = max(float(left_reserve or 0.0), 0.0)
    depth_side = depth_side if depth_side in KNOWN_SIDES else SIDE_LEFT

    plan = TrackPlan()
    for side in KNOWN_SIDES:
        sign = _sign(side)
        # v2.7.8 — the depth ticks are centred ON the trace (ladder-rung
        # convention), so the depth lane starts exactly at the litho band
        # edge and only reserves the label gutter beyond it. Every other
        # lane keeps the uniform gap.
        reserve = left_reserve if side == SIDE_LEFT else 0.0
        cursor = sign * (litho_half + reserve + DEFAULT_GAP)
        if depth_visible and depth_side == side:
            inner = sign * (litho_half + reserve)
            outer = inner + sign * depth_lane_w
            lane = TrackLane("depth", side, inner, outer)
            # x0/x1 normalisation : a left lane has x1 (inner) > x0 (outer).
            lane.x0, lane.x1 = sorted((lane.x0, lane.x1))
            plan.depth = lane
            # v2.9.20 — gap réduit juste après la profondeur (teneurs collées)
            cursor = outer + sign * max(gap * 0.75, 1.0)
        for key in CANONICAL_ORDER:
            spec = tracks.get(key) or {}
            if not spec.get("active"):
                continue
            lane_side = spec.get("side")
            if lane_side != side:
                continue
            width = max(float(spec.get("width") or 0.0), 0.0)
            if width <= 0.0:
                continue
            if side == SIDE_RIGHT:
                lane = TrackLane(key, side, cursor, cursor + width)
            else:
                lane = TrackLane(key, side, cursor - width, cursor)
            plan.lanes.append(lane)
            plan.by_key[key] = lane
            cursor = sign * (abs(cursor) + width + gap)
    plan.left_extent = min(
        [0.0] + [lane.x0 for lane in plan.lanes]
        + ([plan.depth.x0] if plan.depth else []))
    plan.right_extent = max(
        [0.0] + [lane.x1 for lane in plan.lanes]
        + ([plan.depth.x1] if plan.depth else []))
    return plan


def band_polygon(lane: TrackLane, trace_x: float, length: float,
                 y_top: float, y_bottom: float, *,
                 bars: bool = False,
                 thickness: float = 3.5) -> list[tuple[float, float]]:
    """Corners of one interval band inside ``lane``, anchored on the trace.

    ``trace_x`` is the ABSOLUTE scene x of the trace centre ; the band
    grows outward from the lane inner edge by ``length`` px. With
    ``bars=True`` the band becomes a thin centred bar (histogram stick).

    v2.7.7.2 — extracted and tested after the assays lane was drawn at
    absolute coordinates (off-scene → invisible). Lane offsets are always
    relative to the trace, never absolute scene coordinates.
    """
    sign = 1.0 if lane.side == SIDE_RIGHT else -1.0
    inner = lane.inner_edge
    length = max(float(length), 0.0)
    if bars:
        mid_y = (float(y_top) + float(y_bottom)) / 2.0
        half = max(float(thickness), 0.1) / 2.0
        return [
            (trace_x + inner, mid_y - half),
            (trace_x + inner + sign * length, mid_y - half),
            (trace_x + inner + sign * length, mid_y + half),
            (trace_x + inner, mid_y + half),
        ]
    return [
        (trace_x + inner, float(y_top)),
        (trace_x + inner + sign * length, float(y_top)),
        (trace_x + inner + sign * length, float(y_bottom)),
        (trace_x + inner, float(y_bottom)),
    ]


# ---------------------------------------------------------------------------
# v2.7.10.12 — bandes perpendiculaires à la trace (cohérence graduations)
# ---------------------------------------------------------------------------
def rightward_normal(tangent_dx: float, tangent_dy: float) -> tuple[float, float]:
    """Unit SCENE-space normal pointing to the SCREEN-RIGHT of the trace.

    Pendant de :func:`scene_normal` (qui pointe à gauche de la direction) :
    ici le vecteur résultat a toujours une composante x positive pour un
    forage qui descend — donc un décalage POSITIF le long de cette normale
    revient exactement à l'ancien décalage horizontal ``+x`` lorsque le
    trou est vertical (aucune régression), tout en restant PERPENDICULAIRE
    à la trace réellement dessinée quand le trou est incliné ou que
    l'exagération verticale change la pente à l'écran.
    """
    length = math.hypot(float(tangent_dx), float(tangent_dy)) or 1.0
    return float(tangent_dy) / length, -float(tangent_dx) / length


def band_trapezoid(top_xy, top_tangent, bottom_xy, bottom_tangent,
                   inner: float, outer: float) -> list[tuple[float, float]]:
    """Corners of one interval band whose from/to edges are PERPENDICULAR
    to the drawn trace — the exact same scene-space normal the depth tick
    rungs use (v2.7.8.1), so a band boundary is by construction parallel
    to the graduation at the same depth.

    ``top_xy``/``bottom_xy`` are scene points ON the trace at the from/to
    depths ; ``top_tangent``/``bottom_tangent`` are the scene-space deltas
    of the drawn polyline at those depths ; ``inner``/``outer`` are
    trace-relative pixel offsets in the screen-right-positive convention
    (negative = left side).  Returns ``[top_inner, top_outer,
    bottom_outer, bottom_inner]`` — same winding as the historical
    axis-aligned rectangles, so fills, borders and pattern rotation keep
    working unchanged for a vertical hole.
    """
    m_tx, m_ty = rightward_normal(*top_tangent)
    m_bx, m_by = rightward_normal(*bottom_tangent)
    tx, ty = float(top_xy[0]), float(top_xy[1])
    bx, by = float(bottom_xy[0]), float(bottom_xy[1])
    inner, outer = float(inner), float(outer)
    return [
        (tx + m_tx * inner, ty + m_ty * inner),
        (tx + m_tx * outer, ty + m_ty * outer),
        (bx + m_bx * outer, by + m_by * outer),
        (bx + m_bx * inner, by + m_by * inner),
    ]


def diagonal_filet_polygon(top_xy, top_tangent, bottom_xy, bottom_tangent,
                           width_px: float, slant_px: float,
                           direction: int = 1) -> list[tuple[float, float]]:
    """Vein/accessory filet drawn as a DIAGONAL stripe across the host band.

    v2.7.11.3 — retour écran : le filet chevauchait la trace (z sous la
    polyligne du forage) → invisible.  La bandelette garde sa largeur mais
    est décalée d'un côté au ``from`` et de l'autre côté au ``to``
    (``direction`` = ±1 choisit le sens de la diagonale) : elle traverse la
    bande hôte en oblique comme sur un log papier et reste lisible quel que
    soit le pendage.  Mêmes ancres et mêmes normales que les bandes
    d'intervalle (alignées sur les graduations) ; aucune donnée inventée —
    c'est un rendu, jamais une interprétation d'angle.

    Même enroulement que :func:`band_trapezoid` (fills/bordures/motifs
    inchangés).  ``width_px`` est la largeur mesurée le long de la normale
    locale ; ``slant_px`` le décalage latéral aux deux bornes.
    """
    m_tx, m_ty = rightward_normal(*top_tangent)
    m_bx, m_by = rightward_normal(*bottom_tangent)
    tx, ty = float(top_xy[0]), float(top_xy[1])
    bx, by = float(bottom_xy[0]), float(bottom_xy[1])
    w2 = max(float(width_px), 0.1) / 2.0
    s = max(float(slant_px), 0.0) * (1 if direction >= 0 else -1)
    o_t = s     # au from : filet décalé d'un côté de la trace
    o_b = -s    # au to : de l'autre → diagonale à travers la bande
    return [
        (tx + m_tx * (o_t - w2), ty + m_ty * (o_t - w2)),
        (tx + m_tx * (o_t + w2), ty + m_ty * (o_t + w2)),
        (bx + m_bx * (o_b + w2), by + m_by * (o_b + w2)),
        (bx + m_bx * (o_b - w2), by + m_by * (o_b - w2)),
    ]


def stick_polygon(mid_xy, tangent, inner: float, outer: float,
                  thickness: float = 3.5) -> list[tuple[float, float]]:
    """Thin histogram stick (assays « bars » mode) centred at ``mid_xy``.

    The stick LENGTH follows the trace normal (the value direction) and
    its constant pixel thickness follows the trace tangent, both measured
    on the drawn polyline — the stick stays welded to the trace whatever
    the dip, instead of floating as an axis-aligned rectangle.
    """
    mx, my = rightward_normal(*tangent)
    length = math.hypot(float(tangent[0]), float(tangent[1])) or 1.0
    tx, ty = float(tangent[0]) / length, float(tangent[1]) / length
    half = max(float(thickness), 0.1) / 2.0
    cx, cy = float(mid_xy[0]), float(mid_xy[1])
    inner, outer = float(inner), float(outer)
    return [
        (cx + mx * inner - tx * half, cy + my * inner - ty * half),
        (cx + mx * outer - tx * half, cy + my * outer - ty * half),
        (cx + mx * outer + tx * half, cy + my * outer + ty * half),
        (cx + mx * inner + tx * half, cy + my * inner + ty * half),
    ]


def band_edge_x(top_xy, bottom_xy, y: float) -> float:
    """X of a band edge at screen ``y`` (clamped to the edge segment).

    A normal-offset edge is slanted when the hole deviates: measuring the
    edge AT the label height gives the exact horizontal room available —
    better than the perpendicular width for placing a standing text.
    """
    dy = float(bottom_xy[1]) - float(top_xy[1])
    if abs(dy) < 1e-9:
        return float(top_xy[0])
    t = min(max((float(y) - float(top_xy[1])) / dy, 0.0), 1.0)
    return float(top_xy[0]) + t * (float(bottom_xy[0]) - float(top_xy[0]))


def band_horizontal_room(inner_top, inner_bottom, outer_top, outer_bottom,
                         y: float) -> float:
    """Horizontal room (px) between the inner and outer edges at ``y``."""
    return abs(band_edge_x(outer_top, outer_bottom, y)
               - band_edge_x(inner_top, inner_bottom, y))



def angled_depot_candidates(
        gx: float, gy: float,
        npx: float, npy: float,
        utx: float, uty: float,
        side_sign: float,
        base: float,
        radii=None,
        angles_deg=None):
    """v2.9.14/2.9.15 — candidats de déport à ANGLE (pas seulement horizontal).

    Sur une séquence réelle MA/DF/MA/DF (ex. TPDD006 52–60 m : 1 m + 1 m
    + 1 m + 5 m), un placement purement horizontal aligne tous les codes
    sur la même ligne → longs rappels et chevauchements.  Ici chaque
    candidat est à ``(radius, angle)`` dans le plan (normale, tangente) :

        x = gx + side_sign * n * cos(θ) * r  +  t * sin(θ) * r
        y = gy + side_sign * n * cos(θ) * r  +  t * sin(θ) * r

    avec θ = 0 → pure normale (rappel le plus court), θ ≠ 0 → le code
    monte/descend le long du trou tout en restant hors bande.

    v2.9.15 — score = RAYON D'ABORD, angle ensuite.  Avant, |θ|×0.5
    pesait plus que (r−base)×0.15 : une pure normale à 50 px battait un
    angle ±15° à 8 px → rangée horizontale de longs rappels (retour
    écran post-2.9.14).  Désormais un voisin proche à ±30° gagne toujours
    sur un déport lointain à θ=0.

    Retourne ``[(score, x, y, radius, angle_deg), ...]``.
    """
    import math as _m
    if radii is None:
        # pas fins d'abord — coller au trou tant que l'OBB le permet
        # v2.9.25 — rayons plus serrés d'abord (rappels courts visibles)
        radii = (4.0, 7.0, 10.0, 14.0, 18.0, 24.0, 32.0, 42.0, 56.0)
    if angles_deg is None:
        # éventail plus dense près de 0 pour placement dynamique
        angles_deg = (0.0, -10.0, 10.0, -20.0, 20.0, -32.0, 32.0,
                      -45.0, 45.0, -60.0, 60.0, -75.0, 75.0)
    out = []
    sn = float(side_sign)
    for r_extra in radii:
        r = float(r_extra) + float(base)
        for ang in angles_deg:
            rad = _m.radians(float(ang))
            # composante normale / tangente
            cn, ct = _m.cos(rad), _m.sin(rad)
            x = (float(gx)
                 + sn * float(npx) * cn * r
                 + float(utx) * ct * r)
            y = (float(gy)
                 + sn * float(npy) * cn * r
                 + float(uty) * ct * r)
            # v2.9.15 — rayon court >> angle faible
            score = (float(r_extra) * 1.0 + abs(float(ang)) * 0.08)
            out.append((score, x, y, r, float(ang)))
    out.sort(key=lambda c: c[0])
    return out


def label_rotation_degrees(tangent_dx: float, tangent_dy: float) -> float:
    """v2.7.10.13 — rotation (degrés, convention Qt horaire, y-down) d'un
    code posé LE LONG de sa bande, comme sur un log papier.

    Le texte suit la tangente du segment réellement dessiné (pendage et
    exagération inclus) et n'est jamais à l'envers : l'angle est ramené
    dans (-90, 90] — un trou qui plonge à gauche lit son code de bas en
    haut au lieu de l'afficher cul retourné.  Trou vertical -> 90 (le
    code se lit du collet vers le fond, sens des profondeurs).
    """
    angle = math.degrees(math.atan2(float(tangent_dy), float(tangent_dx)))
    if angle > 90.0:
        angle -= 180.0
    elif angle <= -90.0:
        angle += 180.0
    return angle


def first_free_slot(center_x: float, center_y: float, width: float,
                    height: float, occupied, shifts,
                    padding: float = 1.0):
    """v2.7.10.15 — premier décalage libre pour un code DÉPORTÉ.

    Un micro-intervalle ne peut physiquement pas loger son code : le code
    cherche alors une place juste au-dessus / au-dessous, dans la MÊME
    piste (le trait de rappel vers l'intervalle est dessiné par la vue).
    ``occupied`` reçoit les rectangles déjà pris ``(x0, y0, x1, y1)`` ;
    ``shifts`` ordonne les décalages candidats (px) — le premier slot
    sans chevauchement (marge ``padding``) gagne, sinon None : la vue
    retombe alors sur le repli historique.  Pur, sans Qt.
    """
    x0 = float(center_x) - float(width) / 2.0 - float(padding)
    x1 = float(center_x) + float(width) / 2.0 + float(padding)
    for shift in shifts:
        y0 = float(center_y) + float(shift) - float(height) / 2.0 - padding
        y1 = float(center_y) + float(shift) + float(height) / 2.0 + padding
        if not any(x0 < ox1 and x1 > ox0 and y0 < oy1 and y1 > oy0
                   for ox0, oy0, ox1, oy1 in occupied):
            return float(shift)
    return None


def first_free_position(candidates, width: float, height: float,
                        occupied, padding: float = 1.0):
    """v2.7.10.16 — généralisation 2D de :func:`first_free_slot`.

    ``candidates`` ordonne les centres ``(x, y)`` essayés dans l'ordre —
    la vue y mélange le départ perpendiculaire à la trace et le repli le
    long de la piste.  Premier centre dont le rectangle (marge
    ``padding``) ne chevauche aucun rectangle ``occupied``
    ``(x0, y0, x1, y1)`` — ou None si tout est pris : la vue retombe sur
    le repli historique.
    """
    for cx, cy in candidates:
        x0 = float(cx) - float(width) / 2.0 - float(padding)
        x1 = float(cx) + float(width) / 2.0 + float(padding)
        y0 = float(cy) - float(height) / 2.0 - float(padding)
        y1 = float(cy) + float(height) / 2.0 + float(padding)
        if not any(x0 < ox1 and x1 > ox0 and y0 < oy1 and y1 > oy0
                   for ox0, oy0, ox1, oy1 in occupied):
            return (float(cx), float(cy))
    return None


def rotated_aabb(width: float, height: float,
                 rotation_deg: float) -> tuple[float, float]:
    """v2.7.10.18 — enveloppe axis-alignée EXACTE d'un rectangle pivoté de
    ``rotation_deg`` autour de son centre.

    Servait d'empreinte anti-collision une permutation naïve
    ``(height, width)``, exacte seulement à 90° : à 55–65° (trous
    inclinés) elle sous-estimait la hauteur réelle du code pivoté et deux
    libellés voisins se touchaient sur les bords (petit chevauchement
    constaté à l'écran).  L'AABB exacte bloque ça par construction.
    """
    rad = math.radians(float(rotation_deg) % 360.0)
    co, si = abs(math.cos(rad)), abs(math.sin(rad))
    return (float(width) * co + float(height) * si,
            float(width) * si + float(height) * co)


# ---------------------------------------------------------------------------
# v2.7.10.9 — placement des codes de style (jamais de chevauchement)
# ---------------------------------------------------------------------------
def code_fits(span_px: float, text_height_px: float,
              margin_px: float = 2.0) -> bool:
    """Le code n'est posé que si l'étendue écran du run l'accueille.

    Règle « assez de place » : le texte (debout, centré) doit tenir dans
    le trapèze from→to avec une marge. Sinon, la bande reste seule —
    l'infobulle et la légende décodent. Les codes ne peuvent plus se
    chevaucher, par construction.
    """
    return float(span_px) >= float(text_height_px) + float(margin_px)


def elide_code(code: str, max_width: float, measure) -> str:
    """Rogne le code à la largeur disponible (jamais de débordement).

    ``measure`` est la fonction de largeur (ex. ``QFontMetrics.
    horizontalAdvance``) ; le résultat se termine par « … » si rogné,
    et est vide si même un caractère ne tient pas.
    """
    text = str(code or "")
    if not text or float(max_width) <= 0:
        return ""
    if measure(text) <= max_width:
        return text
    if measure("…") > max_width or len(text) <= 1:
        return ""
    while len(text) > 1 and measure(text + "…") > max_width:
        text = text[:-1]
    return text + "…" if text else ""


def fit_font_size(span_px: float, measure_height, min_pt: float = 4.0,
                  max_pt: float = 6.0, step: float = 0.25,
                  margin_px: float = 2.0) -> float | None:
    """Plus grande taille de police (pt) dont le texte tient dans
    l'étendue écran ``span_px`` — ou None si même la taille minimale ne
    tient pas.

    v2.7.10.10 — taille ADAPTATIVE : le code rétrécit pour tenir dans les
    intervalles fins (jusqu'à ``min_pt``), au lieu de disparaître.
    ``measure_height(pt)`` renvoie la hauteur de texte en pixels pour une
    taille donnée. Sous ``min_pt`` le texte est illisible : on renvoie
    None (bande seule, l'infobulle décode).
    """
    span = float(span_px)
    size = float(max_pt)
    while size >= float(min_pt) - 1e-9:
        if measure_height(size) + float(margin_px) <= span:
            return round(size, 2)
        size -= float(step)
    return None


def fit_code_to_band(sizes, code: str, span_px: float, width_px: float,
                     measure_height, measure_width,
                     margin_px: float = 2.0) -> float | None:
    """v2.7.10.12 — plus grande taille où le code COMPLET tient dans le
    trapèze, AVANT tout rognage.

    Le code doit respecter DEUX contraintes à la taille choisie :

    - sa hauteur de texte entre dans l'étendue du run le long du forage
      (``span_px``) ;
    - sa LARGEUR mesurée entre dans la place horizontale de la bande à la
      hauteur du libellé (``width_px``, issu de
      :func:`band_horizontal_room`).

    On réduit donc la TAILLE du texte pour l'adapter à la largeur du
    polygone, au lieu d'abréger le nom du code (:func:`elide_code` ne
    reste qu'un dernier recours côté interface, quand même la plus petite
    taille proposée ne suffit pas).  Retourne None si aucune taille ne
    convient.
    """
    span = float(span_px)
    width = float(width_px)
    text = str(code or "")
    if not text:
        return None
    for size in sorted((float(s) for s in sizes), reverse=True):
        if (measure_height(size) + float(margin_px) <= span
                and measure_width(text, size) + float(margin_px) <= width):
            return round(size, 2)
    return None

def obb_intersects(a, b, pad: float = 0.0) -> bool:
    """v2.8.2 — intersection EXACTE de deux rectangles PIVOTÉS (OBB),
    théorème de l'axe séparateur.

    ``a`` et ``b`` = ``(cx, cy, largeur, hauteur, rotation_deg)`` — la
    boîte SERRÉE du texte pivotée autour de son centre (mêmes
    conventions que :func:`rotated_aabb`).  Retourne True si les deux
    boîtes se touchent ou se chevauchent ; ``pad`` est la distance
    miniérale considérée comme « séparé » (0 = se toucher compte
    comme intersection).

    Remplace l'enveloppe axis-aligned (AABB + marge 2 px) pour le test
    EN PLACE des codes : dans des voies de 10 px, l'AABB d'un code
    pivoté à 55–65° gonfle l'étendue horizontale d'environ 4 px de
    chaque côté — un code de la voie 2 dont le rectangle réel ne
    touche PAS le code de la voie 1 était rejeté par l'AABB et envoyé
    en rappel alors que sa bande le recevait (retour écran 22/08 :
    « on voit bien qu'il peut mettre le code à une taille adaptée mais
    il met le trait de rappel quand même »).
    """
    def corners(cx, cy, w, h, rot):
        rad = math.radians(float(rot))
        co, si = math.cos(rad), math.sin(rad)
        hw, hh = float(w) / 2.0, float(h) / 2.0
        return [(cx + x * co - y * si, cy + x * si + y * co)
                for x, y in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]

    ca = corners(*a)
    cb = corners(*b)

    def local_axes(pts):
        axes = []
        for i in (0, 1):
            dx = pts[i + 1][0] - pts[i][0]
            dy = pts[i + 1][1] - pts[i][1]
            length = math.hypot(dx, dy) or 1.0
            axes.append((dx / length, dy / length))
        return axes

    for ux, uy in local_axes(ca) + local_axes(cb):
        pa = [x * ux + y * uy for x, y in ca]
        pb = [x * ux + y * uy for x, y in cb]
        if max(pa) + pad <= min(pb) or max(pb) + pad <= min(pa):
            return False
    return True


def label_rect_free(placed, lx, ly, w, h, pad=1.0):
    """v2.9.305 — True si le rectangle ne chevauche aucun déjà posé.

    Puits serrés : les étiquettes de profondeur qui entreraient en
    collision avec une étiquette déjà placée (trou voisin) sont sautées ;
    le barreau, lui, reste dessiné.  ``placed`` accumule les rectangles
    retenus (lx, ly, w, h).
    """
    r = (lx - pad, ly - pad, w + 2.0 * pad, h + 2.0 * pad)
    for (px, py, pw, ph_) in placed:
        if (r[0] < px + pw and px < r[0] + r[2]
                and r[1] < py + ph_ and py < r[1] + r[3]):
            return False
    placed.append((lx, ly, w, h))
    return True


def zone_inset_frame(viewport_w, viewport_h, w=170.0, h=120.0, margin=10.0):
    """v2.9.310 : emplacement de l'encart zone (coin haut-droit, px).

    Renvoie (x, y, w, h) ou None si le viewport est trop petit.
    """
    if viewport_w < (w + 2 * margin) or viewport_h < (h + 2 * margin):
        return None
    return (viewport_w - w - margin, margin, w, h)


def mini_section_points(line, hole):
    """v2.9.310/313 — points (along, profondeur) d'un trou : l'encart
    « zone » est une MINI-COUPE lisible (pas un plan aplati)."""
    dx, dy = line.x2 - line.x1, line.y2 - line.y1
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / length, dy / length
    return [( (p.x - line.x1) * ux + (p.y - line.y1) * uy, p.depth)
            for p in (hole.trajectory or [])]


def zone_inset_project(pts_by_hole, frame, view_along=None, pad=8.0):
    """v2.9.310/312 — projette le plan (along, écart) dans l'encart.

    pts_by_hole : [[(along, ecart), ...], ...] ; view_along : fenêtre
    affichée (a_min, a_max) ou None. Échelles indépendantes (vue
    d'ensemble). Renvoie (polylignes, fenêtre) : polylignes = liste de
    ([(px, py), ...], dans_la_vue) ; fenêtre = bande verticale (x, y,
    w, h) px ou None.
    """
    x0, y0, fw, fh = frame
    xs = [p[0] for pts in pts_by_hole for p in pts]
    ys = [p[1] for pts in pts_by_hole for p in pts]
    if not xs:
        return [], None
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_max - x_min < 1e-9:
        x_max = x_min + 1.0
    if y_max - y_min < 1e-9:
        y_max = y_min + 1.0
    ix0, iy0 = x0 + pad, y0 + pad
    iw, ih = fw - 2 * pad, fh - 2 * pad

    def _px(a, e):
        return (ix0 + (a - x_min) / (x_max - x_min) * iw,
                iy0 + (e - y_min) / (y_max - y_min) * ih)

    polys = []
    for pts in pts_by_hole:
        poly = [_px(a, e) for a, e in pts]
        sel = bool(view_along) and any(
            view_along[0] - 1e-9 <= a <= view_along[1] + 1e-9
            for a, _ in pts)
        polys.append((poly, sel))
    win = None
    if view_along and view_along[1] > view_along[0]:
        wx1, _wy = _px(max(view_along[0], x_min), y_min)
        wx2, _wy2 = _px(min(view_along[1], x_max), y_min)
        if wx2 > wx1:
            win = (wx1, iy0, wx2 - wx1, ih)
    return polys, win
