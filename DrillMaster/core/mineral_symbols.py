"""Mineralization symbol library (v2.7.9 — « piste par piste », phase 1).

Pure Python, no Qt : every symbol and texture is a list of normalised
primitives in a unit box [-1, 1] (glyphs) or a unit tile [0, 1]×[0, 1]
(textures). The UI maps those primitives onto the drawn band, so the
library is testable standalone and reusable by the 3D view later.

Decisions recorded in AUDIT_V2.7.9.md :
- symbols are **suggestions** : they live in the project Référentiel
  (``symbol_id``), never in the source data, never applied silently to
  reclassify a value as alteration vs mineralization ;
- everything is drawn in the neutral mineralization ink (monochrome) :
  no colour competition with lithology / alteration / assays ;
- glyphs stay upright (readable) ; style textures follow the band axis
  by construction (they are mapped into the band parallelogram).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
# ("poly", [(x, y), ...], filled, alpha)
# ("ellipse", cx, cy, rx, ry, filled, alpha)
# ("line", x1, y1, x2, y2)


def P(*points, f=True, a=1.0):
    return ("poly", [(round(x, 3), round(y, 3)) for x, y in points], f, a)


def E(cx, cy, rx, ry, f=True, a=1.0):
    return ("ellipse", cx, cy, rx, ry, f, a)


def L(x1, y1, x2, y2):
    return ("line", round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3))


def star_points(n, outer=1.0, inner=0.45):
    import math
    pts = []
    for index in range(n * 2):
        radius = outer if index % 2 == 0 else inner
        angle = -math.pi / 2 + index * math.pi / n
        pts.append((radius * math.cos(angle), radius * math.sin(angle)))
    return pts


# ---------------------------------------------------------------------------
# Base glyph parts (unit box)
# ---------------------------------------------------------------------------
_DIAMOND_O = P((0, -1), (0.72, 0), (0, 1), (-0.72, 0), f=False)
_DIAMOND_F = P((0, -1), (0.72, 0), (0, 1), (-0.72, 0), f=True)
_DIAMOND_S = P((0, -0.66), (0.48, 0), (0, 0.66), (-0.48, 0), f=False)
_DIAMOND_L = P((0, -1), (0.88, 0), (0, 1), (-0.88, 0), f=True)
_RHOMB_O = P((-0.5, -1), (0.5, -1), (0.55, 1), (-0.55, 1), f=False)
_RHOMB_F = P((-0.5, -1), (0.5, -1), (0.55, 1), (-0.55, 1), f=True)
_RHOMB_S = P((-0.38, -0.7), (0.38, -0.7), (0.42, 0.7), (-0.42, 0.7), f=False)
_TRI_O = P((0, -1), (0.95, 0.65), (-0.95, 0.65), f=False)
_TRI_F = P((0, -1), (0.95, 0.65), (-0.95, 0.65), f=True)
_TRI_S = P((0, -0.7), (0.62, 0.45), (-0.62, 0.45), f=False)
_TRI_ELONG = P((0, -1), (0.55, 0.85), (-0.55, 0.85), f=True)
_SQUARE_O = P((-0.75, -0.75), (0.75, -0.75), (0.75, 0.75), (-0.75, 0.75), f=False)
_SQUARE_F = P((-0.75, -0.75), (0.75, -0.75), (0.75, 0.75), (-0.75, 0.75), f=True)
_SQUARE_S = P((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5), f=False)
_HEX_O = P((0, -1), (0.87, -0.5), (0.87, 0.5), (0, 1), (-0.87, 0.5),
            (-0.87, -0.5), f=False)
_HEX_F = P((0, -1), (0.87, -0.5), (0.87, 0.5), (0, 1), (-0.87, 0.5),
           (-0.87, -0.5), f=True)
_HEX_S = P((0, -0.7), (0.6, -0.35), (0.6, 0.35), (0, 0.7), (-0.6, 0.35),
           (-0.6, -0.35), f=False)
_CROSS = (L(-0.8, 0, 0.8, 0), L(0, -0.8, 0, 0.8))
_XCROSS = (L(-0.75, -0.75, 0.75, 0.75), L(-0.75, 0.75, 0.75, -0.75))
_STAR4 = P(*star_points(4), f=True)
_STAR4_O = P(*star_points(4), f=False)
_DOT = E(0, 0, 0.18, 0.18, f=True)
_DOT_BIG = E(0, 0, 0.3, 0.3, f=True)
_RAY = (L(0.75, 0.75, 1, 1), L(-0.75, 0.75, -1, 1),
        L(0.75, -0.75, 1, -1), L(-0.75, -0.75, -1, -1))
_WAVE = (L(-0.8, -0.3, -0.4, 0.3), L(-0.4, 0.3, 0, -0.3),
         L(0, -0.3, 0.4, 0.3), L(0.4, 0.3, 0.8, -0.3))
_FIBRE = (L(-0.7, -0.6, -0.3, -0.3), L(-0.4, -0.1, 0.0, 0.2),
          L(-0.1, 0.4, 0.3, 0.7))
_MICA = (L(-0.7, -0.5, -0.15, -0.5), L(-0.7, 0.0, -0.15, 0.0),
         L(-0.7, 0.5, -0.15, 0.5))
_LAYERED = (L(-0.8, -0.5, 0.8, -0.5), L(-0.8, 0, 0.8, 0),
            L(-0.8, 0.5, 0.8, 0.5))
_GEM = P((-0.55, -1), (0.55, -1), (0.9, -0.35), (0.9, 0.35), (0.55, 1),
         (-0.55, 1), (-0.9, 0.35), (-0.9, -0.35), f=False) + (L(0, -0.9, 0, 0.9),)
_HOURGLASS = P((0, -1), (0.7, 0), (0, 0.35), (-0.7, 0), f=True)

# ---------------------------------------------------------------------------
# Shape specs (deduped names from the user catalog)
# ---------------------------------------------------------------------------
SHAPES: dict[str, tuple] = {
    "diamond": (_DIAMOND_O,),
    "open_diamond": (_DIAMOND_O,),
    "filled_diamond": (_DIAMOND_F,),
    "diamond_small": (_DIAMOND_S,),
    "diamond_large": (_DIAMOND_L,),
    "diamond_dot": (_DIAMOND_O, _DOT),
    "spark_diamond": (_DIAMOND_F,) + _RAY,
    "rhombus": (_RHOMB_O,),
    "open_rhombus": (_RHOMB_O,),
    "filled_rhombus": (_RHOMB_F,),
    "rhombus_small": (_RHOMB_S,),
    "rhombus_dot": (_RHOMB_O, _DOT),
    "double_rhombus": (_RHOMB_O, _RHOMB_S),
    "triangle": (_TRI_O,),
    "triangle_open": (_TRI_O,),
    "filled_triangle": (_TRI_F,),
    "triangle_double": (_TRI_O, _TRI_S),
    "elongated_triangle": (_TRI_ELONG,),
    "square": (_SQUARE_O,),
    "open_square": (_SQUARE_O,),
    "filled_square": (_SQUARE_F,),
    "small_square": (_SQUARE_S,),
    "square_dot": (_SQUARE_O, _DOT),
    "square_cross": (_SQUARE_O,) + _CROSS,
    "cross_square": (_SQUARE_O,) + _CROSS,
    "cross": _CROSS,
    "diagonal_cross": _XCROSS,
    "four_point": _CROSS + (E(-0.85, 0, 0.12, 0.12), E(0.85, 0, 0.12, 0.12),
                            E(0, -0.85, 0.12, 0.12), E(0, 0.85, 0.12, 0.12)),
    "cross_dot": _CROSS + (_DOT,),
    "spark": _CROSS + (E(-0.85, 0, 0.1, 0.1, f=True), E(0.85, 0, 0.1, 0.1, f=True),
                       E(0, -0.85, 0.1, 0.1, f=True), E(0, 0.85, 0.1, 0.1, f=True)),
    "spark_long": _CROSS + _RAY,
    "spark_triangle": (_TRI_O,) + _RAY,
    "cross_circle": (E(0, 0, 0.8, 0.8, f=False),) + _CROSS,
    "circle_cross": (E(0, 0, 0.8, 0.8, f=False),) + _CROSS,
    "cross_circle_small": (E(0, 0, 0.55, 0.55, f=False),) + _CROSS,
    "circle": (E(0, 0, 0.8, 0.8, f=False),),
    "open_circle": (E(0, 0, 0.8, 0.8, f=False),),
    "filled_circle": (E(0, 0, 0.8, 0.8, f=True),),
    "solid_dot": (E(0, 0, 0.45, 0.45, f=True),),
    "filled_dot": (E(0, 0, 0.45, 0.45, f=True),),
    "circle_dot": (E(0, 0, 0.8, 0.8, f=False), _DOT),
    "circle_dot_large": (E(0, 0, 0.8, 0.8, f=False), _DOT_BIG),
    "double_circle": (E(0, 0, 0.8, 0.8, f=False), E(0, 0, 0.55, 0.55, f=False)),
    "bullseye": (E(0, 0, 0.8, 0.8, f=False), _DOT_BIG),
    "open_circle_dot": (E(0, 0, 0.6, 0.6, f=False), _DOT),
    "opaque_dot": (_DOT_BIG, E(0, 0, 0.45, 0.45, f=False)),
    "star_4": (_STAR4,),
    "star": P(*star_points(5), f=True),
    "star_double": (_STAR4, _STAR4_O),
    "platinum_star": (_STAR4,) + (_DOT,),
    "hexagon": (_HEX_O,),
    "hexagon_open": (_HEX_O,),
    "hexagon_filled": (_HEX_F,),
    "hexagon_small": (_HEX_S,),
    "double_hexagon": (_HEX_O, _HEX_S),
    "phosphate_hexagon": (_HEX_F,) + (_DOT,),
    "flower": (E(0, 0, 0.5, 0.5, f=False), E(-0.6, 0.6, 0.22, 0.22, f=False),
              E(0.6, 0.6, 0.22, 0.22, f=False), E(0.6, -0.6, 0.22, 0.22, f=False),
              E(-0.6, -0.6, 0.22, 0.22, f=False)),
    "flower_dot": (E(0, 0, 0.55, 0.55, f=False),) + (_DOT,),
    "wave": _WAVE,
    "serpentine": (_WAVE,) + (L(-0.8, -0.55, -0.4, -0.05),
                             L(-0.4, -0.05, 0, -0.55), L(0, -0.55, 0.4, -0.05),
                             L(0.4, -0.05, 0.8, -0.55),),
    "chlorite": (_WAVE,) + (L(-0.8, 0.55, -0.4, 0.15), L(-0.4, 0.15, 0, 0.55),
                            L(0, 0.55, 0.4, 0.15), L(0.4, 0.15, 0.8, 0.55)),
    "fibrous": _FIBRE,
    "fibrous_curve": (_FIBRE,) + (L(-0.6, -0.8, -0.2, -0.5), L(-0.2, 0.8, 0.2, 0.5)),
    "fibrous_parallel": (L(-0.7, -0.6, -0.3, -0.6), L(-0.4, -0.2, 0, -0.2),
                         L(-0.1, 0.2, 0.3, 0.2), L(0.2, 0.6, 0.6, 0.6)),
    "fibrous_amphibole": (_FIBRE,) + (_DOT,),
    "fibrous_pyroxene": (_FIBRE,) + (L(-0.6, 0.7, -0.2, 0.7),),
    "mica": _MICA,
    "mica_green": _MICA,
    "clay_mica": _MICA + (L(-0.7, -0.75, -0.15, -0.75),),
    "white_mica": (_MICA,) + (L(-0.7, -0.8, -0.15, -0.8),),
    "layered": _LAYERED,
    "clay_dash": (L(-0.7, 0, -0.2, 0), L(0.2, 0, 0.7, 0)),
    "clay_layer": _LAYERED,
    "clay_layers": _LAYERED,
    "light_fill": (P((-0.8, -0.8), (0.8, -0.8), (0.8, 0.8), (-0.8, 0.8),
                    f=True, a=0.35),),
    "gem": _GEM,
    "garnet": (E(0, 0, 0.4, 0.4, f=True), E(-0.55, -0.55, 0.14, 0.14, f=True),
               E(0.55, -0.55, 0.14, 0.14, f=True), E(0.55, 0.55, 0.14, 0.14, f=True),
               E(-0.55, 0.55, 0.14, 0.14, f=True)),
    "garnet_dot": (E(0, 0, 0.45, 0.45, f=True),) + (_DOT,),
    "garnet_bands": (E(0, 0, 0.5, 0.5, f=True),) + (L(-0.7, -0.4, 0.7, -0.4),
                                                 L(-0.7, 0.4, 0.7, 0.4)),
    "mn_garnet": (E(0, 0, 0.45, 0.45, f=True), _DOT),
    "garnet_vein_edge": (E(0, 0, 0.5, 0.5, f=True),) + (L(-0.8, 0.8, 0.8, -0.8),),
    "epidote": (L(-0.3, -0.8, -0.3, -0.4), L(-0.3, -0.1, -0.3, 0.3),
                L(-0.3, 0.6, -0.3, 0.9), L(0.3, -0.8, 0.3, -0.4),
                L(0.3, -0.1, 0.3, 0.3), L(0.3, 0.6, 0.3, 0.9)),
    "epidote_chlorite": (L(-0.3, -0.8, -0.3, 0.9),) + _WAVE,
    "pyroxene": P((-0.35, -1), (0.35, -1), (0.8, -0.4), (0.8, 0.4), (0.35, 1),
                  (-0.35, 1), (-0.8, 0.4), (-0.8, -0.4), f=False),
    "pyroxene_long": P((0, -1), (0.45, -0.5), (0.45, 0.5), (0, 1), (-0.45, 0.5),
                       (-0.45, -0.5), f=False),
    "pyroxene_symbol": ("pyroxene",),
    "pyroxene_diamond": (_DIAMOND_O, _DOT_BIG),
    "orthopyroxene": ("pyroxene",),
    "olivine": (_DIAMOND_O,) + (L(-0.5, 0.5, 0.5, -0.5),),
    "olivine_diamond": (_DIAMOND_O,) + (L(-0.5, 0.5, 0.5, -0.5),),
    "feldspar": (_SQUARE_O,) + (L(-0.75, 0, 0.75, 0),),
    "feldspar_square": (_SQUARE_O,) + (L(-0.75, 0, 0.75, 0),),
    "feldspar_cross": (_SQUARE_O,) + _CROSS,
    "feldspathoid": (_SQUARE_O, _DOT),
    "plagioclase": (_SQUARE_O,) + (L(0, -0.75, 0, 0.75),),
    "iron_oxide": (_SQUARE_F,) + (L(-0.6, -0.35, 0.6, -0.35), L(-0.6, 0.35, 0.6, 0.35)),
    "hematite": (_SQUARE_F,) + (L(-0.6, -0.35, 0.6, -0.35), L(-0.6, 0.35, 0.6, 0.35)),
    "hematite_lines": (L(-0.7, -0.5, 0.7, -0.5), L(-0.7, 0, 0.7, 0),
                       L(-0.7, 0.5, 0.7, 0.5)),
    "magnetite": (_DIAMOND_F,),
    "magnetite_dot": (_DIAMOND_F, _DOT),
    "magnetite_bands": (_DIAMOND_F,) + (L(-0.55, -0.35, 0.55, -0.35),
                                        L(-0.55, 0.35, 0.55, 0.35)),
    "magnetite_outline": (_DIAMOND_O,),
    "magnetite_carbonate": (_DIAMOND_F, E(0, 0, 0.3, 0.3, f=False)),
    "pyrite": (_SQUARE_O,) + _XCROSS,
    "quartz": (_HEX_O,) + (L(-0.6, 0, 0.6, 0),),
    "quartz_variant": (_HEX_O,) + (L(-0.6, 0, 0.6, 0), _DOT),
    "quartz_crystal": (_HEX_O,) + (L(-0.6, 0, 0.6, 0),) + (L(0, -0.9, 0, -0.5),),
    "quartz_vein": (L(-0.75, 0.75, 0.75, -0.75), L(-0.55, 0.95, 0.95, -0.55)),
    "quartz_carbonate": (_HEX_O,) + (E(0, 0, 0.28, 0.28, f=False),),
    "quartz_epidote": (_HEX_O,) + (L(-0.3, -0.9, -0.3, 0.9),),
    "quartz_sericite": (_HEX_O,) + (L(-0.5, -0.55, 0.5, -0.55), L(-0.5, 0.55, 0.5, 0.55)),
    "quartz_tourmaline": (_HEX_O, _TRI_S),
    "quartz_pyrite_calcite": (_HEX_O, _SQUARE_S, E(0, 0, 0.22, 0.22, f=False)),
    "rutilated_quartz": (_HEX_O,) + (L(-0.6, 0.7, 0.6, -0.7), L(-0.6, -0.7, 0.6, 0.7)),
    "agate": (E(0, 0, 0.8, 0.8, f=False), E(0, 0, 0.55, 0.55, f=False)),
    "jasper": (E(0, 0, 0.75, 0.75, f=True), _DOT),
    "chalcedony": (E(0, 0, 0.7, 0.7, f=False),) + _WAVE,
    "tourmaline": (_TRI_ELONG,),
    "carbonate": (E(0, 0, 0.6, 0.6, f=False),) + (L(-0.5, 0, 0.5, 0),),
    "carbonate_dot": (E(0, 0, 0.6, 0.6, f=False), _DOT),
    "carbonate_rhombus": (_RHOMB_O,) + (L(-0.5, 0, 0.5, 0),),
    "carbonate_lace": (_WAVE,) + (L(-0.8, 0.7, -0.4, 0.2), L(-0.4, 0.2, 0, 0.7),
                                L(0, 0.7, 0.4, 0.2), L(0.4, 0.2, 0.8, 0.7)),
    "talc": (L(-0.7, -0.5, -0.2, -0.2), L(-0.5, 0, 0, 0.3), L(-0.3, 0.5, 0.2, 0.8)),
    "talc_carbonate": (L(-0.7, -0.5, -0.2, -0.2), L(-0.3, 0.5, 0.2, 0.8),
                       E(0.55, -0.55, 0.25, 0.25, f=False)),
    "sulfide_group": (E(0, 0, 0.7, 0.7, f=True),),
    "sulfide_dots": (E(0, 0, 0.55, 0.55, f=True), E(-0.6, -0.6, 0.12, 0.12, f=True),
                     E(0.6, -0.6, 0.12, 0.12, f=True), E(0.6, 0.6, 0.12, 0.12, f=True)),
    "sulfide_circle": (E(0, 0, 0.7, 0.7, f=False), _DOT),
    "sulfide_rhombus": (_RHOMB_F,),
    "sulfate_group": _CROSS + (_DOT,),
    "sulfate_cross": _CROSS + (_DOT,),
    "oxide": (_SQUARE_S, _DOT),
    "oxide_dot": (_SQUARE_S, _DOT),
    "oxide_dots": (_SQUARE_S, _DOT, E(0.45, -0.45, 0.1, 0.1, f=True)),
    "oxide_circle": (E(0, 0, 0.6, 0.6, f=False), _DOT),
    "oxide_diamond": (_DIAMOND_O, _DOT),
    "oxide_grain": (_SQUARE_S,),
    "manganese": (E(0, 0, 0.6, 0.6, f=True), E(-0.5, 0.55, 0.1, 0.1, f=True),
                  E(0.5, 0.55, 0.1, 0.1, f=True), E(0, -0.6, 0.1, 0.1, f=True)),
    "manganese_oxide": (_SQUARE_F,) + (_DOT,),
    "manganese_oxide_dot": (_SQUARE_F,) + (_DOT, E(0.5, -0.5, 0.1, 0.1, f=True)),
    "mn_oxide": (_SQUARE_F,),
    "mn_oxide_dots": (_SQUARE_F, _DOT, E(0.5, -0.5, 0.1, 0.1, f=True)),
    "mn_carbonate": (_DIAMOND_F, E(0.35, -0.35, 0.2, 0.2, f=False)),
    "mn_silicate": (_DIAMOND_O,) + (L(-0.6, 0, 0.6, 0),),
    "moly_oxide": _CROSS + (_DOT,),
    "molybdate": _CROSS + (_DOT,),
    "limonite": (E(0, 0, 0.5, 0.5, f=True), E(-0.55, -0.55, 0.1, 0.1, f=True),
                 E(0.55, -0.55, 0.1, 0.1, f=True), E(0, 0.6, 0.1, 0.1, f=True)),
    "wad": (E(0, 0, 0.75, 0.55, f=True),),
    "kyanite": P((0, -1), (0.28, 0), (0, 1), (-0.28, 0), f=False),
    "sillimanite": (L(-0.5, -0.9, -0.5, 0.9), L(0, -0.9, 0, 0.9),
                    L(0.5, -0.9, 0.5, 0.9)),
    "sillimanite_fibrous": (_FIBRE,),
    "chiastolite": (_SQUARE_O,) + _XCROSS,
    "staurolite": _CROSS + (L(-0.8, -0.15, -0.8, 0.15), L(0.8, -0.15, 0.8, 0.15)),
    "hornblende": (_HEX_F,),
    "amphibole_blue": (_HEX_F,),
    "tremolite": P((0, -1), (0.3, 0), (0, 1), (-0.3, 0), f=False),
    "spinel": (_DIAMOND_F,) + (L(-0.5, 0, 0.5, 0),),
    "spinels": (_DIAMOND_F,) + (L(-0.5, 0, 0.5, 0),),
    "graphite": (_HEX_F,),
    "glass": (E(0, 0, 0.5, 0.5, f=False),),
    "glauconite": (E(0, 0, 0.7, 0.7, f=False), _DOT),
    "gypsum": _CROSS,
    "lawsonite": (_RHOMB_S,),
    "hemimorphite": (_TRI_ELONG,),
    "zeolite": (P((-0.8, -0.8), (-0.1, -0.8), (-0.1, -0.1), (-0.8, -0.1), f=False),
                P((0.1, -0.8), (0.8, -0.8), (0.8, -0.1), (0.1, -0.1), f=False),
                P((-0.8, 0.1), (-0.1, 0.1), (-0.1, 0.8), (-0.8, 0.8), f=False),
                P((0.1, 0.1), (0.8, 0.1), (0.8, 0.8), (0.1, 0.8), f=False)),
    "zeolite_cross": _CROSS + (_SQUARE_S,),
    "prehnite": (E(0, 0, 0.65, 0.65, f=False), _DOT_BIG),
    "pollucite": (_SQUARE_O, E(0, 0, 0.3, 0.3, f=False)),
    "travertine": (L(-0.8, -0.45, -0.45, -0.1), L(-0.45, -0.1, -0.1, -0.45),
                   L(-0.1, -0.45, 0.25, -0.1), L(0.25, -0.1, 0.6, -0.45),
                   L(-0.8, 0.45, -0.45, 0.1), L(-0.45, 0.1, -0.1, 0.45),
                   L(-0.1, 0.45, 0.25, 0.1), L(0.25, 0.1, 0.6, 0.45)),
    "tridymite": (_HEX_S,) + (_DOT,),
    "topaz": (_DIAMOND_L,),
    "turquoise": (E(0, 0, 0.65, 0.65, f=True), E(0, 0, 0.35, 0.35, f=False)),
    "tantalite": (_SQUARE_F,),
    "torbernite": (_SQUARE_O, _DOT),
    "telluride": _CROSS + (E(0, 0, 0.25, 0.25, f=False),),
    "tetrahedrite": (_TRI_F,),
    "tennantite": (_TRI_O, _DOT),
    "tenorite": (E(0, 0, 0.5, 0.5, f=True),),
    "uraninite": (E(0, 0, 0.55, 0.55, f=True), E(-0.6, -0.6, 0.1, 0.1, f=True),
                  E(0.6, -0.6, 0.1, 0.1, f=True), E(0.6, 0.6, 0.1, 0.1, f=True),
                  E(-0.6, 0.6, 0.1, 0.1, f=True)),
    "uranium_group": (E(0, 0, 0.55, 0.55, f=True), _STAR4_O),
    "vanadinite": (_HEX_F,),
    "vesuvianite": (_SQUARE_O, _DIAMOND_S),
    "vermiculite": _MICA,
    "wolframite": P((-0.35, -0.95), (0.35, -0.95), (0.35, 0.95), (-0.35, 0.95), f=False),
    "willemite": (_HEX_O,),
    "wulfenite": (_SQUARE_O, E(0, 0, 0.4, 0.4, f=False)),
    "wollastonite": (_DIAMOND_S,),
    "zincite": (E(0, 0, 0.5, 0.5, f=True),),
    "zircon": (_HOURGLASS,),
    "zoisite": (_RHOMB_O, _DOT),
    "pisolite": (E(0, 0, 0.8, 0.8, f=False), E(0, 0, 0.5, 0.5, f=False), _DOT),
    "zinnwaldite": _MICA + (L(-0.7, -0.8, -0.15, -0.8),),
    "unknown": (E(0, 0, 0.6, 0.6, f=False), _DOT),
    "secondary_minerals": (E(0, 0, 0.55, 0.55, f=False), E(0, 0.6, 0.14, 0.14, f=True)),
    "oxidized_sulfide": (E(0, 0, 0.55, 0.55, f=True), E(0, 0, 0.8, 0.8, f=False)),
    "mafic": (_SQUARE_S,),
    "chloritized_mafic": (_SQUARE_S,) + (_WAVE,),
    "chloritized_olivine": (_DIAMOND_O,) + (_WAVE,),
    "calc_silicate": (E(0, 0, 0.5, 0.5, f=False),) + (L(-0.7, 0, 0.7, 0),),
    "opal_wave": (_WAVE,) + (_DOT,),
    "orpiment": (_TRI_S,),
    "realgar": (_DIAMOND_F, _DOT),
    "rhodochrosite": (_RHOMB_F,),
    "rhodonite": (_RHOMB_O,),
    "scheelite": (E(0, 0, 0.7, 0.7, f=False), _SQUARE_S),
    "sphene": (_DIAMOND_O,) + (L(0, -0.9, 0, 0.9),),
    "sphalerite": (E(0, 0, 0.7, 0.7, f=False),) + (L(-0.5, 0.3, 0.5, -0.3),),
    "sericite": _MICA,
    "silica_alteration": _LAYERED,
    "smectite": (L(-0.7, -0.6, -0.2, -0.6), L(-0.3, -0.2, 0.2, -0.2),
                 L(0.1, 0.2, 0.6, 0.2)),
    "smectite_layers": _LAYERED,
    "smithsonite": (E(0, 0, 0.65, 0.65, f=False), _DOT),
    "stibnite": P((0, -1), (0.5, 0), (0, 1), (-0.5, 0), f=False),
    "scapolite": (_SQUARE_O,) + (L(0, -0.75, 0, 0.75),),
    "siderite": (_RHOMB_O,) + (L(-0.5, 0, 0.5, 0),),
    "malachite": (E(0, 0, 0.7, 0.7, f=False),) + (L(-0.6, 0.5, 0.6, -0.5),),
    "molybdenite": _LAYERED,
    "monazite": (_HEX_S,),
    "nepheline": (_HEX_O, _DOT),
    "nickel_diamond": (_DIAMOND_O, E(0, 0, 0.25, 0.25, f=False)),
    "nickel_sulfide": (E(0, 0, 0.6, 0.6, f=True), _DOT),
    "muscovite": _MICA,
    "phlogopite": _MICA,
    "pyrophyllite": _MICA,
    "rutile": (_DIAMOND_L,),
    "scheelite_dot": (E(0, 0, 0.7, 0.7, f=False), _DOT),
}

# ---------------------------------------------------------------------------
# Mineral code catalog (user's AA…ZN table → shape name)
# ---------------------------------------------------------------------------
MINERAL_SYMBOL_CATALOG: dict[str, str] = {
    "AA": "diamond", "AB": "rhombus", "AC": "triangle", "AD": "rhombus_small",
    "AE": "filled_triangle", "AF": "square", "AG": "star_4", "AH": "cross_square",
    "AI": "circle_cross", "AK": "open_rhombus", "AL": "cross", "AM": "filled_diamond",
    "AN": "open_square", "AO": "fibrous", "AP": "elongated_triangle",
    "AQ": "serpentine", "AR": "circle", "AS": "spark_diamond", "AT": "hexagon",
    "AU": "star", "AX": "triangle_double", "AZ": "bullseye", "BA": "cross_circle",
    "BC": "flower", "BE": "hexagon_open", "BH": "double_hexagon", "BI": "mica",
    "BL": "light_fill", "BM": "spark", "BO": "diamond_small", "CA": "open_circle",
    "CB": "double_circle", "CC": "filled_circle", "CD": "rhombus_small",
    "CE": "circle_dot", "CF": "cross_dot", "CG": "spark_long", "CH": "chlorite",
    "CI": "filled_square", "CJ": "four_point", "CK": "wave", "CL": "layered",
    "CM": "diamond_large", "CN": "filled_dot", "CO": "hexagon_filled",
    "CP": "diamond_dot", "CQ": "cross_circle_small", "CR": "solid_dot",
    "CS": "fibrous_curve", "CT": "square_dot", "CU": "circle_dot_large",
    "CV": "open_diamond", "CW": "fibrous_parallel", "CX": "triangle_open",
    "CY": "clay_dash", "CZ": "rhombus_dot", "DC": "clay_layer", "DD": "gem",
    "DG": "garnet_dot", "DI": "triangle_double", "DM": "magnetite_dot",
    "DO": "double_rhombus", "DS": "sulfide_dots", "DT": "carbonate_lace",
    "DX": "oxide_dots", "EC": "epidote_chlorite", "EN": "spark_triangle",
    "EP": "epidote", "ER": "flower_dot", "ES": "pyroxene_long",
    "FA": "olivine_diamond", "FD": "feldspar", "FE": "iron_oxide",
    "FL": "four_point", "FM": "moly_oxide", "FO": "olivine", "FP": "feldspathoid",
    "FU": "mica_green", "FX": "fibrous_amphibole", "FY": "fibrous_pyroxene",
    "GA": "garnet", "GB": "garnet_bands", "GC": "amphibole_blue", "GH": "spinels",
    "GI": "rhombus_small", "GL": "square_cross", "GN": "glauconite",
    "GO": "oxide_circle", "GR": "graphite", "GS": "glass", "GY": "gypsum",
    "HA": "square_cross", "HB": "hornblende", "HD": "filled_triangle",
    "HE": "hematite", "HL": "hematite", "HM": "hemimorphite",
    "HS": "hematite_lines", "HY": "pyroxene", "HZ": "carbonate_dot",
    "IA": "chiastolite", "IL": "clay_mica", "IM": "oxide_diamond", "JA": "sulfate_cross",
    "JD": "pyroxene_diamond", "KA": "clay_layers", "KF": "feldspar_square",
    "KM": "feldspar_cross", "KY": "kyanite", "LC": "calc_silicate",
    "LE": "oxide_grain", "LI": "limonite", "LM": "zeolite_cross",
    "LU": "open_circle_dot", "LW": "lawsonite", "MA": "magnetite",
    "MB": "magnetite_bands", "MC": "chloritized_mafic", "ME": "manganese_oxide",
    "MF": "mafic", "MG": "carbonate_rhombus", "MH": "oxide_dot", "MI": "mica",
    "ML": "malachite", "MM": "smectite_layers", "MN": "manganese",
    "MO": "molybdenite", "MP": "magnetite_outline", "MR": "sulfide_rhombus",
    "MS": "mn_silicate", "MT": "magnetite_carbonate", "MU": "muscovite",
    "MX": "mn_oxide_dots", "MY": "mn_carbonate", "MZ": "monazite", "NF": "nepheline",
    "NI": "nickel_diamond", "OC": "chloritized_olivine", "OL": "olivine",
    "OM": "orpiment", "OP": "opal_wave", "OQ": "opaque_dot", "OR": "orthopyroxene",
    "OS": "star_double", "OX": "oxide", "PE": "prehnite", "PF": "plagioclase",
    "PH": "phlogopite", "PL": "manganese_oxide_dot", "PM": "phosphate_hexagon",
    "PN": "nickel_sulfide", "PO": "sulfide_circle", "PP": "clay_mica",
    "PR": "pyroxene_symbol", "PS": "mn_oxide", "PT": "platinum_star",
    "PU": "pollucite", "PW": "molybdate", "PX": "pyroxene", "PY": "pyrite",
    "QA": "quartz_variant", "QC": "quartz_carbonate", "QE": "quartz_epidote",
    "QG": "agate", "QJ": "jasper", "QP": "quartz_pyrite_calcite",
    "QR": "rutilated_quartz", "QS": "quartz_sericite", "QT": "quartz_tourmaline",
    "QV": "quartz_vein", "QX": "quartz_crystal", "QY": "chalcedony",
    "QZ": "quartz", "RC": "rhodochrosite", "RE": "realgar", "RN": "rhodonite",
    "RU": "rutile", "SU": "sulfide_group", "SA": "sulfate_group", "SB": "stibnite",
    "SC": "scapolite", "SD": "siderite", "SE": "serpentine", "SF": "sillimanite_fibrous",
    "SG": "mn_garnet", "SH": "scheelite", "SI": "sillimanite", "SK": "smectite",
    "SL": "spinel", "SM": "smithsonite", "SN": "sphene", "SP": "sphalerite",
    "SR": "sericite", "SS": "silica_alteration", "ST": "staurolite",
    "SX": "oxidized_sulfide", "SY": "secondary_minerals", "TA": "talc",
    "TB": "torbernite", "TC": "talc_carbonate", "TE": "tenorite", "TH": "tetrahedrite",
    "TL": "telluride", "TN": "tennantite", "TO": "tourmaline", "TR": "tremolite",
    "TT": "tantalite", "TU": "turquoise", "TV": "travertine", "TY": "tridymite",
    "TZ": "topaz", "UN": "unknown", "UR": "uraninite", "UX": "uranium_group",
    "VA": "vanadinite", "VE": "vesuvianite", "VG": "garnet_vein_edge",
    "VM": "vermiculite", "WA": "wad", "WF": "wolframite", "WL": "willemite",
    "WM": "white_mica", "WN": "wulfenite", "WO": "wollastonite", "ZC": "zincite",
    "ZE": "zeolite", "ZI": "zircon", "ZO": "zoisite", "PI": "pisolite",
    "ZN": "zinnwaldite",
}

# Common mineral NAMES → shape (the catalog above uses 2-letter codes ; user
# data carries full words like MAGNETITE_CHALCOPYRITE).
MINERAL_NAME_ALIASES: dict[str, str] = {
    "PYRITE": "pyrite", "CHALCOPYRITE": "diamond_dot", "MAGNETITE": "magnetite",
    "HEMATITE": "hematite", "GOETHITE": "limonite", "LIMOINTE": "limonite",
    "LIMOINITE": "limonite", "QUARTZ": "quartz", "CALCITE": "carbonate",
    "DOLOMITE": "carbonate_rhombus", "ANKERITE": "carbonate_dot",
    "SIDERITE": "siderite", "CHLORITE": "chlorite", "EPIDOTE": "epidote",
    "SERICITE": "sericite", "MUSCOVITE": "muscovite", "BIOTITE": "mica",
    "PHLOGOPITE": "phlogopite", "TOURMALINE": "tourmaline", "GARNET": "garnet",
    "SPESSARTINE": "mn_garnet", "PYROXENE": "pyroxene", "AMPHIBOLE": "hornblende",
    "HORNBLENDE": "hornblende", "ACTINOLITE": "triangle", "TREMOLITE": "tremolite",
    "OLIVINE": "olivine", "FELDSPAR": "feldspar", "FELDSPATH": "feldspar",
    "PLAGIOCLASE": "plagioclase", "ORTHOCLASE": "feldspar", "MICROCLINE": "feldspar_cross",
    "ALBITE": "feldspar", "KAOLINITE": "clay_layers", "SMECTITE": "smectite",
    "MONTMORILLONITE": "smectite_layers", "ILLITE": "clay_mica", "ZELITE": "zeolite",
    "ZEOLITE": "zeolite", "TALC": "talc", "SERPENTINE": "serpentine",
    "GRAPHITE": "graphite", "SULFIDE": "sulfide_group", "SULPHIDE": "sulfide_group",
    "SULFURES": "sulfide_group", "SULPHURES": "sulfide_group", "GALENE": "square_cross",
    "GALENA": "square_cross", "SPHALERITE": "sphalerite", "BLENDE": "sphalerite",
    "ARSENOPYRITE": "spark_diamond", "MOLYBDENITE": "molybdenite",
    "BORNITE": "diamond_small", "COVELLITE": "open_diamond",
    "CHALCOCITE": "filled_circle", "CASSITERITE": "square_dot",
    "WOLFRAMITE": "wolframite", "SCHEELITE": "scheelite", "RUTILE": "rutile",
    "ILMENITE": "oxide_diamond", "ZIRCON": "zircon", "MONAZITE": "monazite",
    "APATITE": "hexagon", "FLUORITE": "four_point", "FLUORINE": "four_point",
    "BARITE": "cross_circle", "BARYTINE": "cross_circle", "GYPSUM": "gypsum",
    "ANHYDRITE": "cross_square", "CARBONATE": "carbonate", "CARBONATES": "carbonate",
    "SILICE": "silica_alteration", "SILICA": "silica_alteration",
    "SILICIFICATION": "silica_alteration", "OXYDE": "oxide", "OXIDE": "oxide",
    "OXYDES": "oxide", "OXIDES": "oxide", "MANGANESE": "manganese",
    "SPHENE": "sphene", "TITANITE": "sphene", "KYANITE": "kyanite",
    "SILLIMANITE": "sillimanite", "ANDALOUSITE": "diamond", "STAUROTIDE": "staurolite",
    "STAUROLITE": "staurolite", "CORDIERITE": "hexagon_filled",
    "GLAUCONITE": "glauconite", "VERMICULITE": "vermiculite", "PREHNITE": "prehnite",
    "ZOISITE": "zoisite", "EPIDOTE_CHLORITE": "epidote_chlorite",
    "STERILE": "unknown", "BARREN": "unknown", "NONE": "unknown",
}


def _normalise_spec(spec):
    """Normalise a SHAPES value into a tuple of primitives (v2.7.9.1).

    A spec may be : a single primitive (``P(...)`` directly — the bug
    source of the QGIS crash « 'bool' object is not subscriptable »), a
    tuple of primitives, or a tuple containing a shape-name reference.
    Anything malformed is dropped, never raised.
    """
    if spec is None:
        return SHAPES.get("unknown", ())
    if not isinstance(spec, tuple) or not spec:
        return ()
    if isinstance(spec[0], str) and spec[0] in ("poly", "ellipse", "line"):
        # Une primitive seule : ("poly"/"ellipse"/"line", ...) → l'emballer.
        return (spec,)
    return spec


def symbol_primitives(shape_name: str) -> tuple:
    """Normalised primitives for a glyph shape (unit box [-1, 1]).

    v2.7.9.1 — les formes définies directement comme primitive unique
    (« star », « pyroxene », « kyanite », « gem »…) étaient éclatées
    élément par élément, injectant des booléens/listes dans le dessin :
    c'est le crash remonté à l'étape 3. Chaque spec est désormais
    normalisée ; un élément invalide est ignoré, jamais propagé.
    """
    return _symbol_primitives(str(shape_name or "").strip(), 0)


def _symbol_primitives(name: str, depth: int) -> tuple:
    if depth > 6:  # garde anti-récursion (catalogue statique, purement défensif)
        return _normalise_spec(SHAPES.get("unknown"))
    spec = SHAPES.get(name)
    if spec is None:
        spec = SHAPES.get("unknown")
    resolved = []
    for entry in _normalise_spec(spec):
        if isinstance(entry, str):
            # Référence par nom (« pyroxene_symbol » → « pyroxene »).
            resolved.extend(_symbol_primitives(entry, depth + 1))
        elif (isinstance(entry, tuple) and len(entry) == 1
              and isinstance(entry[0], str)):
            resolved.extend(_symbol_primitives(entry[0], depth + 1))
        elif (isinstance(entry, tuple) and entry
              and isinstance(entry[0], str)
              and entry[0] in ("poly", "ellipse", "line")):
            resolved.append(entry)
        # Tout le reste (bool, liste, None…) est ignoré.
    if not resolved:
        return _normalise_spec(SHAPES.get("unknown"))
    return tuple(resolved)


# ---------------------------------------------------------------------------
# v2.7.9.2 — libellés français des formes (demande écran : « met tout en FR »)
# ---------------------------------------------------------------------------
_FR_TOKENS = {
    "diamond": "losange", "rhombus": "losange oblique", "triangle": "triangle",
    "square": "carré", "hexagon": "hexagone", "circle": "cercle",
    "dot": "point", "filled": "plein", "open": "ouvert", "small": "petit",
    "large": "grand", "cross": "croix", "star": "étoile",
    "double": "double", "elongated": "allongé", "spark": "à rayons",
    "wave": "ondulé", "serpentine": "serpentin", "chlorite": "chlorite",
    "fibrous": "fibreux", "curve": "courbe", "parallel": "parallèles",
    "mica": "mica", "green": "vert", "layered": "lité", "layers": "couches",
    "layer": "couche", "clay": "argile", "dash": "tiret", "light": "léger",
    "fill": "remplissage", "gem": "gemme", "garnet": "grenat",
    "bands": "bandes", "vein": "veine", "edge": "bordure",
    "epidote": "épidote", "pyroxene": "pyroxène", "long": "long",
    "feldspar": "feldspath", "feldspathoid": "feldspathoïde",
    "plagioclase": "plagioclase", "iron": "fer", "oxide": "oxyde",
    "oxides": "oxydes", "hematite": "hématite", "lines": "lignes",
    "magnetite": "magnétite", "outline": "contour", "carbonate": "carbonate",
    "lace": "dentelle", "talc": "talc", "sulfide": "sulfure",
    "sulfides": "sulfures", "sulfate": "sulfate", "group": "groupe",
    "manganese": "manganèse", "silicate": "silicate", "moly": "molybdène",
    "molybdate": "molybdate", "limonite": "limonite", "wad": "wad",
    "kyanite": "disthène", "sillimanite": "sillimanite",
    "chiastolite": "chiastolite", "staurolite": "staurotide",
    "hornblende": "hornblende", "amphibole": "amphibole", "blue": "bleu",
    "tremolite": "trémolite", "spinel": "spinelle", "spinels": "spinelles",
    "graphite": "graphite", "glass": "verre", "glauconite": "glauconite",
    "gypsum": "gypse", "lawsonite": "lawsonite", "hemimorphite": "hémimorphite",
    "zeolite": "zéolite", "zeolites": "zéolites", "prehnite": "prehnite",
    "pollucite": "pollucite", "travertine": "travertin", "tridymite": "tridymite",
    "topaz": "topaze", "turquoise": "turquoise", "tantalite": "tantalite",
    "torbernite": "torbernite", "telluride": "tellurure",
    "tetrahedrite": "tétraédrite", "tennantite": "tennantite",
    "tenorite": "ténorite", "uraninite": "uraninite", "uranium": "uranium",
    "vanadinite": "vanadinite", "vesuvianite": "vésuvianite",
    "vermiculite": "vermiculite", "wolframite": "wolframite",
    "willemite": "willémite", "wulfenite": "wulfénite",
    "wollastonite": "wollastonite", "zincite": "zincite", "zircon": "zircon",
    "zoisite": "zoïsite", "pisolite": "pisolite", "zinnwaldite": "zinnwaldite",
    "unknown": "inconnu", "secondary": "secondaires", "minerals": "minéraux",
    "oxidized": "oxydé", "mafic": "mafique", "chloritized": "chloritisé",
    "olivine": "olivine", "calc": "calco", "opal": "opale",
    "orpiment": "orpiment", "realgar": "réalgar",
    "rhodochrosite": "rhodochrosite", "rhodonite": "rhodonite",
    "scheelite": "schéelite", "sphene": "sphène", "sphalerite": "sphalérite",
    "sericite": "séricite", "silica": "silice", "alteration": "altération",
    "smectite": "smectite", "smithsonite": "smithsonite",
    "stibnite": "stibine", "scapolite": "scapolite", "siderite": "sidérite",
    "malachite": "malachite", "molybdenite": "molybdénite",
    "monazite": "monazite", "nepheline": "néphéline", "nickel": "nickel",
    "muscovite": "muscovite", "phlogopite": "phlogopite",
    "pyrophyllite": "pyrophyllite", "rutile": "rutile",
    "jasper": "jaspe", "chalcedony": "calcédoine", "agate": "agate",
    "quartz": "quartz", "tourmaline": "tourmaline", "crystal": "cristal",
    "variant": "variante", "rutilated": "rutilé", "bullseye": "cible",
    "flower": "fleur", "four_point": "quatre pointes", "hourglass": "sablier",
    "platinum": "platine", "phosphate": "phosphate", "opaque": "opaque",
    "talc_carbonate": "talc-carbonate", "solid": "plein",
}

# Les qualificatifs qui se placent APRÈS le nom en français :
# filled_diamond → « losange plein », open_square → « carré ouvert »…
_FR_POSTFIX = {"filled": "plein", "open": "ouvert", "small": "petit",
               "large": "grand", "double": "double", "elongated": "allongé",
               "long": "long"}

_FR_OVERRIDES = {
    "quartz_pyrite_calcite": "quartz-pyrite-calcite",
    "quartz_carbonate": "quartz-carbonate",
    "quartz_epidote": "quartz-épidote",
    "quartz_sericite": "quartz-séricite",
    "quartz_tourmaline": "quartz-tourmaline",
    "quartz_vein": "veine de quartz",
    "quartz_crystal": "cristal de quartz",
    "quartz_variant": "quartz (variante)",
    "rutilated_quartz": "quartz rutilé",
    "epidote_chlorite": "épidote-chlorite",
    "magnetite_carbonate": "magnétite-carbonate",
    "chloritized_mafic": "mafique chloritisé",
    "chloritized_olivine": "olivine chloritisée",
    "calc_silicate": "silicate calcique",
    "opal_wave": "opale ondulée",
    "garnet_vein_edge": "grenat en bord de veine",
    "garnet_bands": "grenat en bandes",
    "magnetite_bands": "magnétite en bandes",
    "sulfide_group": "sulfures (groupe)",
    "sulfate_group": "sulfates (groupe)",
    "uranium_group": "minéraux uranifères",
    "oxidized_sulfide": "sulfures oxydés",
    "secondary_minerals": "minéraux secondaires",
    "silica_alteration": "altération siliceuse",
    "hematite_lines": "hématite en lignes",
    "fibrous_amphibole": "amphibole fibreuse",
    "fibrous_pyroxene": "pyroxène fibreux",
    "pyroxene_diamond": "losange de pyroxène",
    "pyroxene_long": "pyroxène allongé",
    "pyroxene_symbol": "pyroxène",
    "olivine_diamond": "losange d'olivine",
    "feldspar_square": "carré de feldspath",
    "feldspar_cross": "feldspath croisé",
    "mica_green": "mica vert",
    "clay_mica": "argile-mica",
    "clay_layer": "couche d'argile",
    "clay_layers": "couches d'argile",
    "clay_dash": "tirets d'argile",
    "white_mica": "mica blanc",
    "smectite_layers": "couches de smectite",
    "carbonate_rhombus": "losange de carbonate",
    "carbonate_dot": "carbonate à point",
    "carbonate_lace": "dentelle carbonatée",
    "mn_garnet": "grenat manganifère",
    "mn_carbonate": "carbonate de Mn",
    "mn_oxide": "oxyde de Mn",
    "mn_oxide_dots": "oxydes de Mn pointés",
    "mn_silicate": "silicate de Mn",
    "manganese_oxide": "oxyde de manganèse",
    "manganese_oxide_dot": "oxyde de Mn à point",
    "moly_oxide": "oxyde de molybdène",
    "iron_oxide": "oxydes de fer",
    "oxide_circle": "cercle d'oxyde",
    "oxide_diamond": "losange d'oxyde",
    "oxide_dot": "oxyde à point",
    "oxide_dots": "oxydes pointés",
    "oxide_grain": "grains d'oxyde",
    "spark_diamond": "losange à rayons",
    "spark_long": "rayons longs",
    "spark_triangle": "triangle à rayons",
    "star_4": "étoile à 4 branches",
    "star_double": "étoile double",
    "platinum_star": "étoile de platinoïdes",
    "nickel_diamond": "losange de nickel",
    "nickel_sulfide": "sulfure de nickel",
    "phosphate_hexagon": "hexagone de phosphate",
    "diamond_dot": "losange à point",
    "diamond_large": "grand losange",
    "diamond_small": "petit losange",
    "rhombus_dot": "losange oblique à point",
    "rhombus_small": "petit losange oblique",
    "double_rhombus": "double losange oblique",
    "double_hexagon": "double hexagone",
    "double_circle": "double cercle",
    "hexagon_filled": "hexagone plein",
    "hexagon_open": "hexagone ouvert",
    "triangle_double": "double triangle",
    "triangle_open": "triangle ouvert",
    "elongated_triangle": "triangle allongé",
    "square_cross": "carré croisé",
    "square_dot": "carré à point",
    "cross_circle": "cercle à croix",
    "cross_circle_small": "petit cercle à croix",
    "cross_dot": "croix à point",
    "cross_square": "croix dans un carré",
    "diagonal_cross": "croix en X",
    "circle_cross": "cercle à croix",
    "circle_dot": "cercle à point",
    "circle_dot_large": "grand cercle à point",
    "open_circle_dot": "cercle ouvert à point",
    "opaque_dot": "point opaque",
    "sulfide_circle": "cercle de sulfure",
    "sulfide_dots": "sulfures pointés",
    "sulfide_rhombus": "losange de sulfure",
    "sulfate_cross": "sulfate croisé",
    "zeolite_cross": "zéolite croisée",
    "tourmaline": "tourmaline",
    "solid_dot": "point",
    "diamond": "losange",
    "circle": "cercle",
    "square": "carré",
    "triangle": "triangle",
    "cross": "croix",
    "star": "étoile",
    "hexagon": "hexagone",
}


def shape_label_fr(shape_name: str) -> str:
    """Libellé français d'une forme de symbole (v2.7.9.2).

    Composés connus d'abord, puis traduction par composants ; en dernier
    recours, le nom brut (jamais d'étiquette vide).
    """
    name = str(shape_name or "").strip()
    if not name:
        return name
    if name in _FR_OVERRIDES:
        return _FR_OVERRIDES[name]
    tokens = name.split("_")
    if len(tokens) == 2 and tokens[0] in _FR_POSTFIX:
        noun = _FR_TOKENS.get(tokens[1], tokens[1])
        qualifier = _FR_POSTFIX[tokens[0]]
        if qualifier in ("petit", "grand", "double"):
            return f"{qualifier} {noun}"
        return f"{noun} {qualifier}"
    translated = [_FR_TOKENS.get(token, token) for token in tokens]
    if len(translated) == 2:
        return f"{translated[0]} à {translated[1]}"
    return " ".join(translated)



def suggest_mineral_symbol(raw_code: str) -> str | None:
    """Shape name suggested for a mineral code/word — or None.

    Tries, in order : the 2-letter catalog, the full-word aliases, then
    each token of a composite value (``MAGNETITE_CHALCOPYRITE`` → the
    first recognisable mineral). Never raises, never invents a symbol.

    v2.7.9.7 — « retour au simple » : le résultat est TOUJOURS ramené à
    l'un des 8 symboles cœur (comme les motifs, pas de catalogue infini).
    """
    value = str(raw_code or "").strip()
    if not value:
        return None
    upper = value.upper()
    shape = None
    if upper in MINERAL_SYMBOL_CATALOG:
        shape = MINERAL_SYMBOL_CATALOG[upper]
    elif upper in MINERAL_NAME_ALIASES:
        shape = MINERAL_NAME_ALIASES[upper]
    else:
        import re as _re
        for token in _re.split(r"[^A-Za-z0-9]+", value):
            if not token:
                continue
            token_upper = token.upper()
            if token_upper in MINERAL_SYMBOL_CATALOG:
                shape = MINERAL_SYMBOL_CATALOG[token_upper]
                break
            if token_upper in MINERAL_NAME_ALIASES:
                shape = MINERAL_NAME_ALIASES[token_upper]
                break
    if shape is None:
        return None
    return to_core_symbol(shape)


# ---------------------------------------------------------------------------
# v2.7.9.7 — « retour au simple » : 8 symboles cœur, comme des motifs
# ---------------------------------------------------------------------------
CORE_SYMBOLS: tuple[str, ...] = (
    "diamond",      # losange
    "square",       # carré
    "triangle",     # triangle
    "circle",       # cercle
    "cross",        # croix
    "star",         # étoile
    "hexagon",      # hexagone
    "solid_dot",    # point
)

_CORE_FALLBACK = "solid_dot"


def to_core_symbol(shape_name: str) -> str:
    """Ramène n'importe quelle forme du catalogue aux 8 symboles cœur.

    Règle par famille (déterministe, jamais aléatoire) : tout ce qui est
    un losange/grenat/magnétite → losange ; carré/feldspath → carré ;
    cercle/point/sulfure → cercle ; croix → croix ; étoile → étoile ;
    hexagone → hexagone ; triangle → triangle ; le reste → point.

    v2.7.10.2 — « none » est PRÉSERVÉ : c'est la valeur « vide »
    explicite. Le ramener à « point » (fallback) la faisait revenir à un
    symbole par défaut dès qu'on appliquait (bug écran).
    """
    name = str(shape_name or "").strip().casefold()
    if name in ("none", ""):
        return name
    if name in CORE_SYMBOLS:
        return name
    # Correspondances explicites des minéraux les plus courants.
    if name in ("pyrite", "square_cross", "square_dot", "filled_square",
                "open_square", "feldspar", "feldspar_square",
                "feldspar_cross", "plagioclase"):
        return "square"
    if (name.startswith("quartz") or name in ("chalcedony", "agate",
                                              "jasper", "nepheline",
                                              "zeolite")):
        return "hexagon"
    if "star" in name:
        return "star"
    if "hexagon" in name:
        return "hexagon"
    if "triangle" in name:
        return "triangle"
    if "square" in name or "feldspar" in name:
        return "square"
    if "cross" in name:
        return "cross"
    if ("diamond" in name or "rhombus" in name or "garnet" in name
            or "magnetite" in name or "spinel" in name or "kyanite" in name):
        return "diamond"
    if "circle" in name or "dot" in name or "sulfide" in name \
            or "bullseye" in name or "flower" in name:
        return "circle"
    return _CORE_FALLBACK


# ---------------------------------------------------------------------------
# Mineralization STYLES (the 10 style textures)
# ---------------------------------------------------------------------------
# ("rect", x, y, w, h, alpha) / ("line", ...) / ("ellipse", ...)
MINERALIZATION_STYLES: tuple[dict, ...] = (
    {"key": "VN", "label": "Veinée", "kind": "veined"},
    {"key": "SV", "label": "Selvedge (bordure)", "kind": "selvedge"},
    {"key": "PE", "label": "Pervasive (diffuse)", "kind": "pervasive"},
    {"key": "DI", "label": "Disséminée", "kind": "disseminated"},
    {"key": "MO", "label": "Marbrée / tachetée", "kind": "mottled"},
    {"key": "FO", "label": "Contrôlée par foliation", "kind": "foliation"},
    {"key": "BD", "label": "En bandes / litage", "kind": "bands"},
    {"key": "PA", "label": "Amas / poches", "kind": "pods"},
    {"key": "ST", "label": "Stockwerk", "kind": "stockworks"},
    {"key": "MA", "label": "Massive", "kind": "massive"},
    {"key": "BR", "label": "Bréchique", "kind": "breccia"},
    {"key": "FL", "label": "Filonienne", "kind": "veined"},
)

STYLE_KEYS: tuple[str, ...] = tuple(style["key"] for style in MINERALIZATION_STYLES)



_STYLE_WORD_HINTS = {
    "MASSIVE": "MA", "MASSIF": "MA", "PERVASIVE": "PE", "DIFFUS": "PE",
    "BRECHIQUE": "BR", "BRECHE": "BR", "BRECCIA": "BR", "BR": "BR",
    "FILONIENE": "FL", "FILONIENNE": "FL", "FILON": "FL", "FL": "FL",
    "DISSEMINEE": "DI", "DISSÉMINÉE": "DI",
    "VEINED": "VN", "VEIN": "VN", "VEINULE": "VN", "VEINLET": "VN",
    "STOCKWORK": "ST", "STOCKWERK": "ST", "STOCKWERKS": "ST",
    "DISSEMINATED": "DI", "DISSEMINE": "DI",
    "MOTTLED": "MO", "PATCHY": "MO", "FOLIATION": "FO", "BANDED": "BD",
    "BANDES": "BD", "BEDDING": "BD", "LITAGE": "BD", "PODS": "PA",
    "PATCHES": "PA", "AMAS": "PA", "SELVEDGE": "SV", "BORDURE": "SV",
}


def suggest_style_key(raw_code: str) -> str | None:
    """Clé de style 2 lettres (VN, MA, DI…) reconnue dans la valeur — ou
    None. Valeurs inconnues (STERILE…) : None, rien n'est inventé."""
    value = str(raw_code or "").strip()
    if not value:
        return None
    folded = value.casefold()
    if folded in STYLE_KEYS:
        return folded
    if folded in _STYLE_WORD_HINTS:
        return _STYLE_WORD_HINTS[folded]
    for hint, key in _STYLE_WORD_HINTS.items():
        if hint.casefold() in folded:
            return key
    return None


# v2.7.10.5 — conversion des ANCIENS symboles (2.7.10.2/3) vers les codes
# 2 lettres. Les projets enregistrés avec « square », « cross »…
# affichaient « SQUARE »/« CROSS » au lieu de MA/VN. Correspondance
# inverse de l'ancienne corrélation ; les cas ambigus (cercle, triangle)
# retombent sur le style primaire (DI, FO) — documenté, modifiable.
CORE_TO_STYLE: dict[str, str] = {
    "square": "MA", "solid_dot": "PE", "cross": "VN", "star": "ST",
    "circle": "DI", "hexagon": "MO", "triangle": "FO", "diamond": "BD",
}


def legacy_symbol_to_style(symbol_id: str) -> str | None:
    """Ancien symbole cœur (2.7.10.2/3) → code 2 lettres, ou None si la
    valeur n'est pas un ancien symbole (c'est déjà un code libre)."""
    name = str(symbol_id or "").strip().casefold()
    if not name:
        return None
    return CORE_TO_STYLE.get(name)


def style_display_code(raw_code: str, stored: str = "",
                       pattern: str = "") -> str:
    """Texte affiché dans la piste de style (convention de log : le code
    2 lettres s'écrit dans la bande, comme sur un log papier).

    v2.9.69 — défaut : les **2 premières lettres** du code brut
    (BRECHIQUE→BR, FILONIENE→FI, MASSIVE→MA si reconnu sinon MA…).

    - ``stored == "none"`` → "" (rien n'est dessiné) ;
    - ``stored`` = ancien symbole cœur (square, cross…) → MA/VN… ;
    - ``stored`` autre (code libre déjà 2 lettres) → majuscules ;
    - sinon style reconnu (MASSIVE…) → son code 2 lettres ;
    - sinon motif legacy → code style ;
    - sinon **2 premières lettres alphanumériques** du code brut.
    """
    sid = str(stored or "").strip()
    if sid == "none":
        return ""
    if sid:
        mapped = legacy_symbol_to_style(sid)
        if mapped:
            return mapped
        # code libre déjà court → tel quel ; long → 2 lettres
        up = sid.upper()
        letters = "".join(c for c in up if c.isalnum())
        if len(letters) <= 3:
            return up[:4]
        return letters[:2]
    key = suggest_style_key(raw_code)
    if key is None and str(pattern or "").strip():
        key = legacy_pattern_to_style(pattern)
    if key:
        return key
    # v2.9.69 — défaut user : 2 premières lettres du code brut
    raw = str(raw_code or "").strip().upper()
    letters = "".join(c for c in raw if c.isalnum())
    if len(letters) >= 2:
        return letters[:2]
    return letters or ""


def legacy_pattern_to_style(pattern: str) -> str | None:
    """Map a pre-v2.7.9 stored pattern to a style texture (migration).

    ``""`` (solid) → MA, diagonals → VN, cross-hatches → ST, horizontals
    → BD, verticals → FO, dots → DI, ``"none"`` → None (transparent).
    """
    key = str(pattern or "").strip()
    if key in ("", "solid"):
        return "MA"
    if key == "none":
        return None
    if key in ("diagonal", "backward_diagonal"):
        return "VN"
    if key in ("cross", "diagonal_cross"):
        return "ST"
    if key == "horizontal":
        return "BD"
    if key == "vertical":
        return "FO"
    if key in ("dots", "dots_moyen", "dots_fin", "dots_dense"):
        return "DI"
    return "MA"
