"""Band layout for multi-phenomenon interval tracks (v2.7.2, refined v2.7.3).

Pure, QGIS-free geometry decisions implementing the product decisions
validated on 17/08/2026, refined after the visual review of 18/08/2026 :

- D-01 : without proportions, the primary lithology keeps the full band.
  v2.9.20 — secondaries are FINE strips INSIDE the host (inner edge),
  never a left-hand rail outside the track.
  v2.9.91 — up to MAX_DRAWN_SECONDARIES_NO_PROP (4) secondaries drawn as
  barrettes with a guaranteed min width; overflow is NOT silent (export
  has no tooltips) — a visible « +N » annotation carries the rest.
  Never an invented 50/50.  Veins and accessories stay fine overlays.
- D-01b (rendu) : a secondary whose code clearly names a vein
  (…VEIN…, VEINE, VEINULE, VN, FILON…) is drawn as a vein filet.  This is
  a pure rendering hint : stored roles are never rewritten.
- D-02 : with proportions, the band is subdivided side by side; veins and
  accessories remain superposed whatever their proportion.
- D-05 : unknown roles are preserved in the data but drawn as secondaries.
- AM-01 (v2.8.0, corrigé v2.8.1, décision écran) : a coded track
  (alterations, mineralizations) is laid out BY POSITION — lane 1 always
  carries the first column's code (``Alteration_1`` / ``Alteration``),
  lane k exists only because some interval carries k codes
  (``lane_slots``).  Lanes are glued; the thin bold line at a boundary
  is drawn ONLY on the intervals where two codes coexist there (no
  permanent grid).  Each lane is filled from its OWN intensity only.
  The shared group (CM-03) is retired.
- AM-02 : parallel lanes never overwrite each other (by construction).

Every value returned is a *fraction* of the track width so any view (2D
section, future 3D, exports) can scale it to pixels or world units without
re-implementing the rules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# --- Roles ------------------------------------------------------------------
ROLE_PRIMARY = "primary"
ROLE_SECONDARY = "secondary"
OVERLAY_ROLES = ("vein", "accessory")
KNOWN_ROLES = (ROLE_PRIMARY, ROLE_SECONDARY) + OVERLAY_ROLES

# --- Width fractions (decisions D-01/D-02) ----------------------------------
FULL = 1.0
VEIN_FRACTION = 0.24
ACCESSORY_FRACTION = 0.18
# Deliberately far from 0.5 so a reduced band can never be mistaken for an
# invented 50/50 proportion (D-01).  v2.9.20 — strip INSIDE the host.
REDUCED_FRACTION = 0.28
# Inset from the host edge for the internal secondary strip (D-01).
SIDE_BAND_GAP = 0.04
# v2.9.91 — up to 4 secondary barrettes (no silent drop; export has no bubbles).
MAX_DRAWN_SECONDARIES_NO_PROP = 4
# Minimum barrette width as a fraction of the litho track (readability).
MIN_SECONDARY_WIDTH_FRACTION = 0.12
# Total width budget inside the host for ALL secondary strips (host still shows).
SECONDARY_STRIP_BUDGET = 0.56
# Gap between adjacent secondary barrettes (fraction of track).
SECONDARY_STRIP_GAP = 0.02

# Band kinds (draw order follows the returned list order).
KIND_BASE = "base"        # full-width primary reference band
KIND_SPLIT = "split"      # proportional side-by-side subdivision (D-02)
KIND_REDUCED = "reduced"  # secondary side bar, left of the track (D-01)
KIND_OVERLAY = "overlay"  # vein/accessory fine superposed band


@dataclass
class BandSpec:
    """One drawable band, all geometry expressed as track-width fractions."""

    raw_code: str
    role: str        # canonical role used for drawing (unknown -> secondary)
    kind: str
    center: float    # relative to the track centre (|0.5| = track edges)
    width: float     # fraction of the total track width
    # v2.9.91 — set on the BASE band when secondaries cannot all be drawn
    # (cap 4 and/or min-width budget).  Render draws a visible « +N ».
    overflow_count: int = 0
    overflow_codes: tuple = ()


# --- Vein/accessory rendering hints (D-01b, render only) ---------------------

# v2.7.11.2 — CM-04 (arbitrage du 21/08/2026) : tokens EXACTS de la
# codification utilisateur ajoutés.  VQZ (veine de quartz) et STW
# (stockwerk = réseau de veinules) ont la couleur de famille « veine »
# depuis longtemps ; leur géométrie restait une barrette latérale —
# incohérence réparée : couleur et géométrie disent la même chose.
_VEIN_TOKENS = {"VEIN", "VEINE", "VEINULE", "VEINULES", "VN", "VNS",
                "FILON", "FILONS", "QZV", "VNE", "VQZ", "STW"}
_VEIN_SUBSTRINGS = ("VEIN", "VEINUL", "FILON")


def looks_like_vein(raw_code) -> bool:
    """True when a code clearly names a vein (rendering hint only).

    Deliberately conservative : whole tokens (``QTZ_VEIN``, ``VN``) or the
    unambiguous substrings VEIN/VEINUL/FILON.  Nothing here ever rewrites a
    stored value — it only steers the drawing geometry.
    """
    folded = str(raw_code or "").upper().strip()
    if not folded:
        return False
    tokens = {t for t in re.split(r"[^A-Z0-9]+", folded) if t}
    if tokens & _VEIN_TOKENS:
        return True
    return any(marker in folded for marker in _VEIN_SUBSTRINGS)


def draw_role(role: str, raw_code) -> str:
    """Role actually used for drawing.

    A declared (or unknown, D-05) secondary whose code names a vein renders
    as a vein filet; every other role is returned untouched.

    v2.9.21 — rôle vide + code veine (QTZ_VEIN…) → filet aussi (la bulle
    et le layout ne doivent plus diverger).
    """
    if role in OVERLAY_ROLES:
        return role
    if role in (ROLE_SECONDARY, "") and looks_like_vein(raw_code):
        return "vein"
    return role


def _role_and_proportion(component) -> tuple[str, float | None, str]:
    """Read (role, proportion, raw_code) from a dataclass or a mapping."""
    if isinstance(component, dict):
        role = str(component.get("role") or "")
        proportion = component.get("proportion")
        raw_code = str(component.get("raw_code") or "")
    else:
        role = str(getattr(component, "role", "") or "")
        proportion = getattr(component, "proportion", None)
        raw_code = str(getattr(component, "raw_code", "") or "")
    if role not in KNOWN_ROLES:
        role = ROLE_SECONDARY  # D-05 : unknown roles render as secondaries
    role = draw_role(role, raw_code)  # D-01b : vein-like secondary -> filet
    try:
        proportion = float(proportion) if proportion is not None else None
    except (TypeError, ValueError):
        proportion = None
    return role, proportion, raw_code


def component_band_layout(components) -> list[BandSpec]:
    """Lay out interval components as drawable bands.

    Draw order is the returned order: base/split bands first, overlays last.
    An empty input returns an empty list (caller keeps its legacy behaviour).
    """
    entries = [(idx,) + _role_and_proportion(c)
               for idx, c in enumerate(components or [])]
    if not entries:
        return []

    dividers = [e for e in entries if e[1] not in OVERLAY_ROLES]
    overlays = [e for e in entries if e[1] in OVERLAY_ROLES]
    if not dividers:
        # An interval made only of veins: the first one becomes the base so
        # the interval is never invisible.
        dividers, overlays = entries[:1], entries[1:]

    primary = next((e for e in dividers if e[1] == ROLE_PRIMARY), None)
    base = primary or dividers[0]

    bands: list[BandSpec] = []
    split_possible = bool(dividers) and all(
        e[2] is not None for e in dividers)
    total = (sum(e[2] for e in dividers) or 0.0) if split_possible else 0.0
    if split_possible and 0.0 < total <= 100.5:
        # D-02 : side-by-side subdivision, in source order.  Any undeclared
        # remainder extends the base band (the host), never a fake share ;
        # a noisy sum above 100 % is normalised back to the full width.
        cursor = -0.5
        if total > 100.001:
            widths = [max(e[2], 0.0) / total for e in dividers]
            remainder = 0.0
        else:
            widths = [max(e[2], 0.0) / 100.0 for e in dividers]
            remainder = max(0.0, FULL - sum(widths))
        for i, entry in enumerate(dividers):
            width = widths[i] + (remainder if entry == base else 0.0)
            if width <= 1e-9:
                continue
            bands.append(BandSpec(
                raw_code=entry[3], role=entry[1], kind=KIND_SPLIT,
                center=cursor + width / 2.0, width=width))
            cursor += width
    else:
        # D-01 / v2.9.20 / v2.9.91 : primary = full host ; secondaries =
        # thin strips INSIDE the host (inner/left edge).  Up to
        # MAX_DRAWN_SECONDARIES_NO_PROP barrettes with min width ; overflow
        # is reported on the BASE band (visible « +N », never silent —
        # export has no tooltips).  No external left rail.
        secondaries = [e for e in dividers if e is not base]
        n_want = len(secondaries)
        # How many barrettes fit at min width inside the strip budget.
        unit = MIN_SECONDARY_WIDTH_FRACTION + SECONDARY_STRIP_GAP
        max_by_width = max(
            0, int((SECONDARY_STRIP_BUDGET + SECONDARY_STRIP_GAP) // unit)
            if unit > 1e-12 else 0)
        if max_by_width < 1 and n_want > 0:
            # Always try at least one barrette if any secondary exists.
            max_by_width = 1
        n_draw = min(n_want, MAX_DRAWN_SECONDARIES_NO_PROP, max_by_width)
        overflow_entries = secondaries[n_draw:]
        overflow_count = len(overflow_entries)
        overflow_codes = tuple(e[3] for e in overflow_entries)

        bands.append(BandSpec(
            raw_code=base[3], role=base[1], kind=KIND_BASE,
            center=0.0, width=FULL,
            overflow_count=overflow_count,
            overflow_codes=overflow_codes))

        if n_draw > 0:
            # Equal share of budget, capped at REDUCED_FRACTION, floored at min.
            gaps = SECONDARY_STRIP_GAP * max(n_draw - 1, 0)
            usable = max(SECONDARY_STRIP_BUDGET - gaps, MIN_SECONDARY_WIDTH_FRACTION)
            width_each = usable / float(n_draw)
            width_each = min(width_each, REDUCED_FRACTION)
            width_each = max(width_each, MIN_SECONDARY_WIDTH_FRACTION)
            # Left edge of host, marching inward (negative centers).
            cursor = -(FULL / 2.0) + SIDE_BAND_GAP
            for entry in secondaries[:n_draw]:
                center = cursor + width_each / 2.0
                # Keep strip fully inside the host half-width.
                right = center + width_each / 2.0
                if right > FULL / 2.0 - 1e-9:
                    center = FULL / 2.0 - SIDE_BAND_GAP - width_each / 2.0
                bands.append(BandSpec(
                    raw_code=entry[3], role=entry[1], kind=KIND_REDUCED,
                    center=center, width=width_each))
                cursor += width_each + SECONDARY_STRIP_GAP

    # v2.9.20 — plus de rail externe : reduced_rail_fraction → 0.

    for _idx, role, _prop, raw_code in overlays:
        bands.append(BandSpec(
            raw_code=raw_code, role=role, kind=KIND_OVERLAY, center=0.0,
            width=VEIN_FRACTION if role == "vein" else ACCESSORY_FRACTION))
    return bands


# --- Rail des secondaires litho : espace réservé (CM-03, v2.7.11.1) -----------

def reduced_rail_fraction(secondary_count: int) -> float:
    """v2.9.20 — barrettes INTERNES : plus de réserve hors piste.

    Conservée pour compat API / plan_tracks(left_reserve=…) ; renvoie
    toujours 0.0 (les secondaires sans % tiennent dans la bande hôte).
    """
    return 0.0


# --- Grouped coded-track layout (AM-01, v2.7.3) -------------------------------

# --- Voies parallèles fixes (v2.8.0, corrigé v2.8.1, écran 22/08/2026) -------
# Le groupe partagé (CM-03) est retiré : les codes d'un intervalle se
# partent la piste par POSITION — la voie 1 porte TOUJOURS le code de la
# 1ʳ colonne (``Alteration_1`` / ``Alteration``), la voie 2 n'existe que
# parce qu'un intervalle porte 2 codes, la voie 3 si un en porte 3.
# Les voies sont COLLÉES (pas d'espace entre elles) : la frontière entre
# deux voies est un TRAIT FIN GRAS dessiné par le rendu, JAMAIS une
# grille permanente — le trait n'apparaît que sur les intervalles qui
# portent 2+ codes, entre les voies qui y coexistent.  Chaque voie
# calcule son remplissage à partir de SA PROPRE intensité uniquement.
#
# Largeur de voie = « minimale lisible » (décision écran) : le code de
# 2 lettres y tient, et le remplissage FAIBLE (0,45 × largeur) reste
# visible.  Ne jamais descendre sous 8 px tant que le code reste dans
# la voie.
LANE_WIDTH_PX = 12.0  # v2.9.69 défaut user


def lane_slots(lane_count, lane_width: float = LANE_WIDTH_PX) -> list[tuple]:
    """Voies collées — ``n`` voies égales de largeur ``lane_width``.

    ``n`` = le plus grand nombre de codes d'un même intervalle dans la
    section (calculé par le rendu, codes visibles seuls).  Retourne
    ``[(r_start, r_end)]`` où ``r`` est en pixels mesurés depuis le bord
    interne de la piste : la voie i occupe ``[i*w, (i+1)*w)`` et la
    largeur totale de la piste est ``n*w``.  ``lane_slots(0) == []``
    (rien d'inventé).
    """
    n = max(int(lane_count or 0), 0)
    width = max(float(lane_width), 1.0)
    return [(index * width, (index + 1) * width) for index in range(n)]


# --- Intensity by width (AM-03) ----------------------------------------------
_INTENSITY_WEAK = {
    "faible", "weak", "low", "legere", "légère", "leger", "léger",
    "trace", "1", "w", "f"}
_INTENSITY_MODERATE = {
    "moderee", "modérée", "modere", "moderate", "moyenne", "medium",
    "moyen", "2", "m", "mod"}
_INTENSITY_STRONG = {
    "fort", "forte", "strong", "high", "intense", "intensive", "3", "s"}

INTENSITY_WEAK_FRACTION = 0.45
INTENSITY_MODERATE_FRACTION = 0.7
INTENSITY_STRONG_FRACTION = 1.0


def intensity_factor(raw_intensity) -> float:
    """Map a raw intensity label to a band-width fraction.

    The raw value is never judged or transformed in the data; an unknown or
    missing intensity simply draws at the neutral moderate width (AM-03).
    """
    if raw_intensity is None:
        return INTENSITY_MODERATE_FRACTION
    folded = str(raw_intensity).strip().casefold()
    if not folded:
        return INTENSITY_MODERATE_FRACTION
    if folded in _INTENSITY_WEAK:
        return INTENSITY_WEAK_FRACTION
    if folded in _INTENSITY_STRONG:
        return INTENSITY_STRONG_FRACTION
    return INTENSITY_MODERATE_FRACTION


# --- Explicit delimited splitting (AM-06) --------------------------------------
# Domain content fields eligible for an explicit "several codes in one cell"
# convention outside lithology.  Minerals are the splittable field for
# mineralizations; styles stay single (AM-05 only forbids *automatic*
# separation, declared conventions remain allowed).
SPLIT_CONTENT_FIELDS = {
    "alterations": "alteration",
    "mineralizations": "minerals",
}


def split_delimited_codes(raw_value: str, delimiter: str) -> list[str]:
    """Split one cell on an explicitly declared delimiter.

    Pure helper shared by validation and views: strips parts and refuses an
    empty delimiter.  Never invoked without a confirmed user convention.
    """
    if not delimiter:
        return [raw_value.strip()] if raw_value.strip() else []
    return [part.strip() for part in str(raw_value).split(delimiter)
            if part.strip()]
