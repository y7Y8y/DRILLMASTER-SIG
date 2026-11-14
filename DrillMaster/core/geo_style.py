"""
DEPRECATED (audit 2.9.87) — non utilisé sur le chemin actif de rendu.
StyleDefinition / grammaire 2.9.86 hors coupe-légende-réf actifs.
Chemin courant = reference.PATTERN_KEYS + brush maps UI (2.9.33/87).
Ne pas supprimer encore.  Voir audit 2.9.87 A-03.

StyleDefinition — grammaire de motifs simple et lisible (v2.9.86).

Principe (feedback utilisateur) :
  • Couleur = identité principale
  • Motif = signal secondaire, PAS toute la géologie
  • Vocabulaire COURT, chaque primitive reconnaissable
    en pastille de légende (~40×20) ET en bande mince de coupe

Grammaire (PATTERN_KEYS) :
    SOLID (plein)     ─────  |||||  /////  \\\\\
    ·····  •••••      +++++  ×××××

Pas de densités micro (dots_fin/moyen) ni de textures complexes.
Un seul renderer : pattern_paint.paint_style.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Grammaire — 8 primitives + plein
# ---------------------------------------------------------------------------
LINE_KEYS = frozenset({
    "diagonal", "backward_diagonal", "cross", "diagonal_cross",
    "horizontal", "vertical",
})
DOT_KEYS = frozenset({
    "dots", "dots_dense", "dense",  # dense = alias historique → dots
})

# Géométrie lisible (px).  Espacements LARGES + traits nets = pas de
# « texture pixel ».  Conçu pour pastille ≥ 36×18 et bande ≥ ~8 px.
DEFAULT_SPACING = 6.0
DEFAULT_STROKE = 1.15
DEFAULT_DOT_RADIUS = 1.55
DEFAULT_UNDERLAY_ALPHA = 0.55
MIN_MOTIF_PX = 5.0
INK_ON_DARK = "#FFFFFF"
INK_ON_LIGHT = "#1A252F"
LIGHTNESS_SPLIT = 130

# Compat anciens imports / tests
DEFAULT_DOT_RADIUS_RATIO = 0.28
DOT_SPACING_FACTOR = {
    "dots": 1.0,
    "dense": 1.0,
    "dots_dense": 0.62,
    "dots_fin": 1.0,      # alias → dots
    "dots_moyen": 1.0,    # alias → dots
}

# key -> (spacing, stroke, dash, radius, stagger)
# dash toujours () : traits CONTINUS (lisibles) — pas de tireté micro.
MOTIF_PROFILES: dict[str, Tuple[float, float, Tuple[float, ...], float, bool]] = {
    # Lignes — 1 direction, rythme large
    "horizontal":        (5.5, 1.25, (), 0.0, False),   # ─────
    "vertical":          (5.0, 1.25, (), 0.0, False),   # |||||
    "diagonal":          (5.5, 1.20, (), 0.0, False),   # /////
    "backward_diagonal": (5.5, 1.20, (), 0.0, False),   # \\\\\
    # Croisillons — 2 directions, plus aéré pour rester lisible
    "cross":             (7.0, 1.10, (), 0.0, False),   # +++++
    "diagonal_cross":    (7.0, 1.10, (), 0.0, False),   # ×××××
    # Points — 2 densités SEULEMENT, gros disques, grille claire
    "dots":              (7.5, 1.0,  (), 1.70, False),  # ····· clairsemé
    "dense":             (7.5, 1.0,  (), 1.70, False),  # alias → dots
    "dots_dense":        (4.6, 1.0,  (), 1.90, False),  # ••••• serré mais net
    # Anciennes densités → mêmes profils que dots (normalise les mappe)
    "dots_fin":          (7.5, 1.0,  (), 1.70, False),
    "dots_moyen":        (7.5, 1.0,  (), 1.70, False),
}


def kind_for_key(pattern_key: str) -> str:
    """solid | lines | dots | none — SENS du motif."""
    try:
        from .reference import normalise_pattern
        key = normalise_pattern(pattern_key)
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("geo_style : kind_for_key", _exc)
        # hors QGIS / import circulaire : clé brute
        key = str(pattern_key or "").strip()
    if key in ("none",):
        return "none"
    if not key or key == "solid":
        return "solid"
    if key in LINE_KEYS:
        return "lines"
    if key in DOT_KEYS or key in ("dots_fin", "dots_moyen"):
        return "dots"
    return "solid"


def profile_for_key(key: str) -> Tuple[float, float, Tuple[float, ...], float, bool]:
    """(spacing, stroke, dash, radius, stagger)."""
    k = str(key or "").strip()
    if k in MOTIF_PROFILES:
        return MOTIF_PROFILES[k]
    kind = kind_for_key(k)
    if kind == "dots":
        return (7.5, 1.0, (), DEFAULT_DOT_RADIUS, False)
    if kind == "lines":
        return (DEFAULT_SPACING, DEFAULT_STROKE, (), 0.0, False)
    return (DEFAULT_SPACING, DEFAULT_STROKE, (), 0.0, False)


def ink_for_fill_hex(fill_hex: str, *, kind: str = "lines") -> str:
    if kind in ("solid", "none", ""):
        return ""
    h = str(fill_hex or "").lstrip("#")
    if len(h) < 6:
        return INK_ON_LIGHT
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return INK_ON_LIGHT
    L = 0.5 * (max(r, g, b) + min(r, g, b))
    return INK_ON_DARK if L < LIGHTNESS_SPLIT else INK_ON_LIGHT


def ink_for_lightness(lightness: float, *, kind: str = "lines") -> str:
    if kind in ("solid", "none", ""):
        return ""
    try:
        L = float(lightness)
    except (TypeError, ValueError):
        L = 200.0
    return INK_ON_DARK if L < LIGHTNESS_SPLIT else INK_ON_LIGHT


@dataclass(frozen=True)
class StyleDefinition:
    """Style de remplissage : couleur + une primitive de motif."""
    key: str = ""
    kind: str = "solid"          # solid | lines | dots | none
    fill_color: str = "#CCCCCC"
    ink_color: str = ""
    spacing_px: float = DEFAULT_SPACING
    stroke_px: float = DEFAULT_STROKE
    rotation_deg: float = 0.0
    follow_axis: bool = True
    underlay_alpha: float = DEFAULT_UNDERLAY_ALPHA
    fill_alpha: float = 1.0
    min_motif_px: float = MIN_MOTIF_PX
    dash: Tuple[float, ...] = ()
    dot_radius_px: float = DEFAULT_DOT_RADIUS
    stagger: bool = False

    @property
    def has_motif(self) -> bool:
        return self.kind in ("lines", "dots")

    def resolved_ink(self, *, lightness: Optional[float] = None) -> str:
        if self.ink_color:
            return self.ink_color
        if lightness is not None:
            return ink_for_lightness(lightness, kind=self.kind)
        return ink_for_fill_hex(self.fill_color, kind=self.kind)

    def spacing_for_key(self) -> float:
        return max(3.0, float(self.spacing_px))


def style_from_pattern(
    pattern_key: str,
    fill_color: str = "#CCCCCC",
    *,
    fill_alpha: float = 1.0,
    follow_axis: bool = True,
    underlay_alpha: float = DEFAULT_UNDERLAY_ALPHA,
    spacing_px: float | None = None,
    stroke_px: float | None = None,
    ink_color: str = "",
) -> StyleDefinition:
    """Construit un StyleDefinition depuis une clé de la grammaire."""
    try:
        from .reference import normalise_pattern
        key = normalise_pattern(pattern_key)
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("Motif : style_from_pattern", _exc)
        # hors QGIS / import circulaire : clé brute
        key = str(pattern_key or "").strip()
    kind = kind_for_key(key)
    if kind == "solid":
        key = key if key else ""
    sp, st, dash, radius, stagger = profile_for_key(key)
    if spacing_px is not None:
        sp = float(spacing_px)
    if stroke_px is not None:
        st = float(stroke_px)
    return StyleDefinition(
        key=key,
        kind=kind,
        fill_color=str(fill_color or "#CCCCCC"),
        ink_color=str(ink_color or ""),
        spacing_px=float(sp),
        stroke_px=float(st),
        follow_axis=bool(follow_axis),
        underlay_alpha=float(underlay_alpha),
        fill_alpha=max(0.0, min(1.0, float(fill_alpha))),
        dash=tuple(dash),
        dot_radius_px=float(radius),
        stagger=bool(stagger),
    )
