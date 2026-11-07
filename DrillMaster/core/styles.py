"""
DrillMaster — QGIS Layer Styles
"""

from __future__ import annotations


def _gtype_point():
    from qgis.core import QgsWkbTypes
    return QgsWkbTypes.PointGeometry

def _gtype_line():
    from qgis.core import QgsWkbTypes
    return QgsWkbTypes.LineGeometry

def _circle():
    from qgis.core import QgsSimpleMarkerSymbolLayer
    try:
        return QgsSimpleMarkerSymbolLayer.Circle
    except AttributeError:
        from qgis.core import QgsSimpleMarkerSymbolLayerBase
        return QgsSimpleMarkerSymbolLayerBase.Circle


def create_collar_style():
    from qgis.core import (QgsSimpleMarkerSymbolLayer, QgsSymbol,
                           QgsSingleSymbolRenderer)
    from qgis.PyQt.QtGui import QColor
    sl = QgsSimpleMarkerSymbolLayer()
    sl.setShape(_circle())
    # v2.9.304 — taille réduite, sans chevauchement (retour écran).
    sl.setSize(1.8)
    sl.setColor(QColor("#C0392B"))
    sl.setStrokeColor(QColor("#000000"))
    sl.setStrokeWidth(0.4)
    sym = QgsSymbol.defaultSymbol(_gtype_point())
    sym.changeSymbolLayer(0, sl)
    return QgsSingleSymbolRenderer(sym)


def create_survey_style():
    from qgis.core import (QgsSimpleLineSymbolLayer, QgsSymbol,
                           QgsSingleSymbolRenderer)
    from qgis.PyQt.QtGui import QColor
    sl = QgsSimpleLineSymbolLayer()
    sl.setColor(QColor("#1C2833"))
    sl.setWidth(0.5)
    sym = QgsSymbol.defaultSymbol(_gtype_line())
    sym.changeSymbolLayer(0, sl)
    return QgsSingleSymbolRenderer(sym)


# v2.9.82 — ADAPTATEUR CARTE QGIS des clés pattern_engine / PATTERN_KEYS.
# La coupe dessine via core.pattern_engine ; la couche intervalle QGIS
# est une LIGNE : même clé → tiretés distincts (projection 1D).
_LINE_DASH_PATTERNS = {
    "diagonal": [4.0, 2.0],
    "backward_diagonal": [2.0, 2.0],
    "cross": [5.0, 1.5, 1.0, 1.5],
    "diagonal_cross": [3.0, 1.0, 1.0, 1.0],
    "horizontal": [6.0, 2.0],
    "vertical": [1.6, 1.4],
    "dots": [0.5, 3.5],
    "dense": [0.5, 3.5],
    "dots_fin": [0.4, 4.5],
    "dots_moyen": [0.5, 3.0],
    "dots_dense": [0.6, 2.0],
}


# v2.9.152 — rendu 3D des motifs : des MARQUES PERPENDICULAIRES au tube
# (tirets obliques, échelons, croix, points), JAMAIS de traits parallèles
# à l'axe — un trait parallèle se lit comme une barrette litho (retour
# écran : « certains motifs renvoient comme si c'étaient des barrettes,
# c'est confus »).  La légende 3D consomme la MÊME spéc.
TUBE_PATTERN_RENDER = {
    "diagonal":          {"kind": "tick", "tilt": 0.62, "period": 5.0},
    "backward_diagonal": {"kind": "tick", "tilt": -0.62, "period": 5.0},
    "horizontal":        {"kind": "tick", "tilt": 0.0, "period": 5.0},
    "vertical":          {"kind": "double_tick", "period": 6.5},
    "cross":             {"kind": "plus", "period": 6.5},
    "diagonal_cross":    {"kind": "cross_x", "period": 7.5},
    "dots":              {"kind": "dot", "period": 6.0, "radius": 0.9},
    "dots_moyen":        {"kind": "dot", "period": 4.4, "radius": 0.8},
    "dots_fin":          {"kind": "dot", "period": 3.2, "radius": 0.62},
    "dots_dense":        {"kind": "dot", "period": 2.3, "radius": 0.7},
}


def pattern_min_marks(kind):
    """Nombre MINIMUM de marques pour IDENTIFIER un motif (v2.9.155).

    Retour écran : « au moins 1 marque, centrée — on saura ?? avec une
    marque ?? ».  Justement non : un POINT isolé ne dit pas si c'est
    dots_fin ou dots_dense (c'est le RYTHME qui porte la densité), et
    un échelon isolé ne donne pas la cadence.  La 2D garde sa densité
    native (le motif se répète le long de la bande, même courte) — la
    3D fait pareil : l'espacement se comprime pour loger le minimum.

    - ``dot`` → 3 (rythme = lecture de la densité) ;
    - ``tick`` → 2 (cadence + inclinaison) ;
    - ``double_tick`` / ``plus`` / ``cross_x`` → 1 (glyphe déjà
      identifiable seul).
    """
    return {"dot": 3, "tick": 2}.get(str(kind or ""), 1)


def pattern_mark_geometry(length, tube_w, spec):
    """Géométrie BORNÉE des marques d'un motif sur un tube (v2.9.156).

    Retour écran : « sur certains intervalles moins larges les motifs
    sortent ou ne s'affichent pas — gère bien nos 10 motifs par
    défaut ».  Pure et testée sur une MATRICE complète
    (segment court/long × tube fin/épais × les 10 motifs) :

    - ``n_marks`` ≥ ``pattern_min_marks(kind)`` (rythme identifiable) ;
    - ``half`` (travers du tube) : dans le tube, avec un plancher de
      visibilité 2,2 px pour les tubes fins (léger dépassement admis) ;
    - ``axial`` (demi-emprise LE LONG de l'axe, pour les inclinaisons
      et les croix) : ne déborde JAMAIS du segment (≤ 35 % de sa
      longueur) — jamais l'effet « barrette » ;
    - ``mark_w`` / ``dot_r`` : planchers de visibilité, pointillés
      bornés par l'espacement (pas de fusion en bouillie).

    Retourne ``dict(n_marks, half, axial, mark_w, dot_r)``.
    """
    kind = str((spec or {}).get("kind") or "")
    length = max(1.0, float(length))
    tube_w = max(1.0, float(tube_w))
    spacing = float((spec or {}).get("period", 5.0)) * max(2.2, tube_w * 0.85)
    n_marks = max(pattern_min_marks(kind), int(length // spacing))
    # traverse du tube : dedans, plancher de visibilité
    half = max(tube_w * 0.42, 2.2)
    half = min(half, max(2.2, length * 0.6))
    # emprise axiale d'une marque (inclinaison des tick, bras des croix)
    if kind == "tick":
        axial = half * abs(float((spec or {}).get("tilt", 0.0)))
    elif kind in ("plus", "cross_x"):
        axial = half * 0.8
    else:
        axial = 0.0
    axial = min(axial, length * 0.35)
    # v2.9.158 — épaississement (retour écran : « croix, points… on voit
    # rien ») : les marques doivent se lire d'un coup d'œil sur le tube.
    mark_w = max(1.3, tube_w * 0.22)
    dot_r = max(0.8, float((spec or {}).get("radius", 0.8))
                * max(1.0, tube_w * 0.20))
    if kind == "dot":
        # pas de fusion : rayon borné par l'espacement réel des marques
        real_spacing = length / max(1, n_marks)
        dot_r = min(dot_r, max(0.8, real_spacing * 0.35))
    return {"n_marks": n_marks, "half": half, "axial": axial,
            "mark_w": mark_w, "dot_r": dot_r}


def tube_pattern_render(pattern_key):
    """Spéc de rendu 3D d'un motif du Référentiel (v2.9.152).

    Retourne un dict ``{"kind": …, "period": …, …}`` (copie) ou ``None``
    si le motif est vide/inconnu.  ``period`` est en unités de largeur
    de tube (espacement des marques le long de l'axe) ; ``kind`` :
    ``tick`` (échelon perpendiculaire, incliné par ``tilt``),
    ``double_tick``, ``plus``, ``cross_x``, ``dot``.
    Source unique — le rendu des TUBES 3D et la LÉGENDE 3D consomment
    la même spéc (plus de légende qui ne reflète pas les motifs).
    """
    key = str(pattern_key or "").strip().lower()
    spec = TUBE_PATTERN_RENDER.get(key)
    return dict(spec) if spec else None


def line_dash_pattern(pattern_name):
    """Motif de tirets PARTAGÉ (v2.9.150, SPEC B-2/D2).

    Source unique des motifs « ligne » : la carte QGIS l'utilise pour
    ses symboles (``_LINE_DASH_PATTERNS``) et la vue 3D pour les
    surcharges de motifs sur les tubes — mêmes motifs partout.
    Retourne la liste de tirets, ou ``None`` si le nom est inconnu/vide.
    """
    key = str(pattern_name or "").strip().lower()
    if not key:
        return None
    return _LINE_DASH_PATTERNS.get(key)


def create_litho_style(actual_codes=None, custom_colors=None):
    """
    Categorized style using ONLY codes present in the data.
    actual_codes: list of litho codes found in the data.
    """
    from qgis.core import (QgsSymbol, QgsSingleSymbolRenderer,
                           QgsCategorizedSymbolRenderer, QgsRendererCategory)
    from qgis.PyQt.QtGui import QColor
    from .section import get_litho_color

    codes = actual_codes or []
    custom = custom_colors or {}

    cats = []
    dash_patterns = _LINE_DASH_PATTERNS
    for code in codes:
        sym = QgsSymbol.defaultSymbol(_gtype_line())
        style = custom.get(code, {}) if isinstance(custom, dict) else {}
        # v2.7.9.7 — entrée décochée du Référentiel : transparente sur la
        # carte (jamais de contradiction coupe/carte).
        if style.get("visible") is False:
            sym.setColor(QColor(0, 0, 0, 0))
        else:
            hex_c = get_litho_color(code, custom)
            sym.setColor(QColor(hex_c))
        sym.setWidth(2.0)
        pattern = style.get("pattern", "") if isinstance(style, dict) else ""
        if pattern in dash_patterns:
            layer = sym.symbolLayer(0)
            if hasattr(layer, "setUseCustomDashPattern"):
                layer.setUseCustomDashPattern(True)
                layer.setCustomDashVector(dash_patterns[pattern])
        label = (style.get("label") if isinstance(style, dict) else "") or code
        cats.append(QgsRendererCategory(code, sym, label))

    if not cats:
        sym = QgsSymbol.defaultSymbol(_gtype_line())
        sym.setColor(QColor("#CCCCCC"))
        sym.setWidth(1.5)
        return QgsSingleSymbolRenderer(sym)

    return QgsCategorizedSymbolRenderer("lithology", cats)


def create_domain_style(field_name, codes, styles=None):
    """v2.7.3 — categorized line style for coded interval domains
    (alterations, mineralization styles).

    Colours/labels/patterns come from the project referential; a missing
    entry keeps a stable automatic colour, so every code is always drawn
    and always decodable (never color alone: the category label is kept).
    """
    from qgis.core import (QgsSymbol, QgsSingleSymbolRenderer,
                           QgsCategorizedSymbolRenderer, QgsRendererCategory)
    from qgis.PyQt.QtGui import QColor
    from .reference import automatic_code_color

    dash_patterns = _LINE_DASH_PATTERNS
    cats = []
    for code in (codes or []):
        info = (styles or {}).get(code, {})
        if not isinstance(info, dict):
            info = {}
        sym = QgsSymbol.defaultSymbol(_gtype_line())
        sym.setColor(QColor(
            info.get("color") or automatic_code_color(field_name, code)))
        sym.setWidth(2.0)
        pattern = info.get("pattern", "")
        if pattern in dash_patterns:
            layer = sym.symbolLayer(0)
            if hasattr(layer, "setUseCustomDashPattern"):
                layer.setUseCustomDashPattern(True)
                layer.setCustomDashVector(dash_patterns[pattern])
        cats.append(QgsRendererCategory(code, sym, info.get("label") or code))

    if not cats:
        sym = QgsSymbol.defaultSymbol(_gtype_line())
        sym.setColor(QColor("#CCCCCC"))
        sym.setWidth(1.5)
        return QgsSingleSymbolRenderer(sym)

    return QgsCategorizedSymbolRenderer(field_name, cats)


def create_structure_style(codes=None, styles=None,
                           field_name="type", marker_size=3.0):
    """v2.9.258-rendu — categorized POINT style for the ``structure`` layer.

    Colours/labels come from the project Référentiel (``structure``
    domain), never from a frozen palette.  The symbol is deliberately
    small so closely-spaced measurements stay readable at high density;
    QGIS point identification still exposes all fields natively.
    """
    from qgis.core import (QgsSymbol, QgsSingleSymbolRenderer,
                           QgsCategorizedSymbolRenderer, QgsRendererCategory,
                           QgsSimpleMarkerSymbolLayer)
    from qgis.PyQt.QtGui import QColor
    from .reference import automatic_code_color

    cats = []
    for code in (codes or []):
        info = (styles or {}).get(code, {})
        if not isinstance(info, dict):
            info = {}
        sym = QgsSymbol.defaultSymbol(_gtype_point())
        layer = sym.symbolLayer(0)
        if isinstance(layer, QgsSimpleMarkerSymbolLayer):
            layer.setShape(_circle())
            layer.setSize(float(marker_size))
            layer.setStrokeWidth(0.6)
            layer.setStrokeColor(QColor("#FFFFFF"))
        if info.get("visible") is False:
            sym.setColor(QColor(0, 0, 0, 0))
        else:
            sym.setColor(QColor(
                info.get("color")
                or automatic_code_color("structure", code)))
        cats.append(QgsRendererCategory(
            code, sym, info.get("label") or code))

    if not cats:
        sym = QgsSymbol.defaultSymbol(_gtype_point())
        sym.setColor(QColor("#CCCCCC"))
        layer = sym.symbolLayer(0)
        if isinstance(layer, QgsSimpleMarkerSymbolLayer):
            layer.setShape(_circle())
            layer.setSize(float(marker_size))
        return QgsSingleSymbolRenderer(sym)

    return QgsCategorizedSymbolRenderer(field_name, cats)


def create_assay_style(field_name=None, values=None, style=None):
    """Create the shared assay grade-map renderer used on the QGIS map."""
    from qgis.core import (
        QgsSymbol, QgsSingleSymbolRenderer,
        QgsGraduatedSymbolRenderer, QgsRendererRange,
    )
    from qgis.PyQt.QtGui import QColor
    from .section import (
        compute_assay_scale, assay_scale_classes, assay_ramp_rgb,
    )

    cfg = style or {}
    width = float(cfg.get("map_line_width", 1.8))
    opacity = min(max(float(cfg.get("opacity", 72)) / 100.0, 0.0), 1.0)
    vals = [v for v in (values or []) if isinstance(v, (int, float))]

    if not field_name or not vals:
        sym = QgsSymbol.defaultSymbol(_gtype_line())
        sym.setColor(QColor("#E67E22"))
        sym.setWidth(width)
        sym.setOpacity(opacity)
        return QgsSingleSymbolRenderer(sym)

    method = cfg.get("method", "linear")
    # QgsGraduatedSymbolRenderer is range-based. Approximate continuous
    # ramps with enough narrow ranges that map and section read as the same
    # project-wide gradient, while true classified modes keep the chosen count.
    renderer_classes = (24 if method in ("linear", "log")
                        else cfg.get("n_classes", 5))
    scale = compute_assay_scale(
        vals, method, renderer_classes, cfg.get("manual_breaks", []),
        cfg.get("round_breaks", True))
    palette = cfg.get("palette", "grade")
    ranges = []
    precision = cfg.get("precision")
    unit = cfg.get("unit", "")
    def _format(value):
        if precision is not None:
            try:
                return f"{value:.{max(0, min(int(precision), 12))}f}"
            except (TypeError, ValueError):
                # Precision unreadable: default formatting applies below.
                pass
        return f"{value:.4g}"
    for lower, upper, ratio in assay_scale_classes(scale):
        sym = QgsSymbol.defaultSymbol(_gtype_line())
        sym.setColor(QColor(assay_ramp_rgb(ratio, palette)))
        sym.setWidth(width)
        sym.setOpacity(opacity)
        label = f"{_format(lower)} - {_format(upper)}"
        if unit:
            label += f" {unit}"
        ranges.append(QgsRendererRange(lower, upper, sym, label))

    if not ranges:
        return create_assay_style(None, None, cfg)
    return QgsGraduatedSymbolRenderer(field_name, ranges)


def create_section_line_style():
    from qgis.core import (QgsSimpleLineSymbolLayer, QgsSymbol,
                           QgsSingleSymbolRenderer)
    from qgis.PyQt.QtGui import QColor
    sl = QgsSimpleLineSymbolLayer()
    sl.setColor(QColor("#C0392B"))
    sl.setWidth(1.0)
    sl.setCustomDashVector([5, 3])
    sl.setUseCustomDashPattern(True)
    sym = QgsSymbol.defaultSymbol(_gtype_line())
    sym.changeSymbolLayer(0, sl)
    return QgsSingleSymbolRenderer(sym)
