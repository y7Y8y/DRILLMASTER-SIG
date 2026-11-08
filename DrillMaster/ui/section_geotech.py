"""v2.9.264 — Chantier 3 : pistes 2D géotechniques (RQD, récup, densité).

Chaque domaine propriétaire reste dans un module dédié (même principe que
``section_structure.py`` / ``section_imagery.py``) : la piste, la page de
réglages, l'infobulle et la légende quantitative vivent ici.

Règles implémentées :
- RQD / CR : bande continue de ``from``/``to`` colorée par la valeur 0–100 %.
- Densité : point à ``depth`` (mode ponctuel) ou bande si ``from``/``to``.
- Unité toujours affichée ; jamais convertie.
- Échelle (bornes + unité) calculée UNE fois dans
  ``core.geotech.geotech_legend_scale`` : le dessin et la légende disent
  exactement la même chose.
- Piste grisée (bande hachurée) pour un forage sans mesure du domaine,
  jamais bloquante.
- Pas de rendu 3D dans ce chantier.
"""

from __future__ import annotations

import math

from qgis.PyQt.QtCore import QLineF, QPointF, Qt
from qgis.PyQt.QtGui import (
    QBrush, QColor, QPen, QPixmap, QPolygonF)
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem,
    QGridLayout, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget)

from .styles_qt import (
    BUTTON_SECONDARY, COLORS, INPUT_STYLE, make_collapsible_help)
from ..core.geotech import (
    geotech_anchor, geotech_colour, geotech_default_unit,
    geotech_depth_text, geotech_kind, geotech_label, geotech_legend_scale,
    geotech_link_pairs, geotech_unit_for, geotech_value_text)
from ..core.track_bands import LANE_WIDTH_PX
from ..core.track_layout import rightward_normal
from ..core.diagnostics import log_swallowed

GEOTECH_KIND_ORDER = ("rqd", "recovery", "density")

# Gris de la piste « sans mesure » — constant partagé par le dessin ET la
# légende, pour que la pastille de légende ne dérive jamais du rendu.
# v2.9.267 — gris « aucune mesure » : la constante vit dans core/geotech
# (partagée par la légende 3D), ré-exportée ici pour les appelants 2D.
from ..core.geotech import GEOTECH_MISSING_COLOUR  # noqa: E402
GEOTECH_MISSING_EDGE = "#BDBDBD"


def _attr(kind: str, suffix: str) -> str:
    return f"{geotech_kind(kind)}_{suffix}"


def has_data(dhs, kind: str) -> bool:
    kind = geotech_kind(kind)
    if not kind:
        return False
    for dh in dhs or []:
        for record in getattr(dh, "geotech", None) or []:
            if geotech_kind(getattr(record, "kind", "")) == kind:
                return True
    return False


def geotech_track_spec(widget, sr, kind: str) -> dict:
    """Spec de piste pour le plan de pistes (auto-collapse sans donnée)."""
    kind = geotech_kind(kind)
    show_attr = f"_{kind}"
    width_attr = f"_{kind}_width"
    side_attr = f"_{kind}_side"
    return {
        "side": getattr(widget, side_attr, "right"),
        "width": float(getattr(widget, width_attr, 10.0)),
        "active": (bool(getattr(widget, show_attr, True))
                   and any(
                       any(geotech_kind(getattr(r, "kind", "")) == kind
                           for r in (getattr(ph, "geotech", None) or []))
                       for ph in sr.holes)),
    }


# ---------------------------------------------------------------------------
# Infobulle
# ---------------------------------------------------------------------------
def geotech_tooltip(canvas, ph, record, kind: str) -> str:
    kind = geotech_kind(kind)
    value = float(getattr(record, "value", 0.0))
    unit = geotech_unit_for(kind, record)
    lines = [f"{ph.hole_id} · {geotech_depth_text(record)}"]
    lines.append(canvas.tr("{label} : {value}").format(
        label=canvas.tr(geotech_label(kind)),
        value=geotech_value_text(value, kind, unit)))
    if geotech_kind(kind) == "density" and not unit:
        lines.append(canvas.tr("Unité par défaut : g/cm³"))
    if getattr(record, "comment", ""):
        lines.append(str(record.comment))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------
def draw_geotech(canvas, sr, kind: str):
    """Dessine la piste d'un domaine géotechnique sur la coupe courante."""
    kind = geotech_kind(kind)
    if not kind:
        return
    plan = getattr(canvas, "_track_plan", None)
    lane = plan.by_key.get(kind) if plan is not None else None
    if lane is None:
        return
    opacity = max(
        0, min(100, int(getattr(canvas, f"_{kind}_opacity", 90))))
    alpha = round(255 * opacity / 100.0)
    # Échelle UNIQUE (même fonction pour le dessin ET la légende) : les
    # bornes écrites sous la rampe sont celles qui ont servi à colorer.
    records = [
        record
        for ph in sr.holes
        for record in (getattr(ph, "geotech", None) or [])
        if geotech_kind(getattr(record, "kind", "")) == kind
    ]
    lo, hi, unit = geotech_legend_scale(kind, records)
    canvas._geotech_legend_ranges[kind] = (lo, hi, unit)

    inner = float(lane.inner_edge)
    outer = float(lane.outer_edge)
    centre = (inner + outer) / 2.0
    step = max(4.0, float(getattr(canvas, f"_{kind}_marker_size", 5.0)))
    radius = max(step / 2.0, 1.5)
    link_on = kind == "density" and bool(
        getattr(canvas, "_density_link", True))

    for ph in sr.holes:
        records = [
            record for record in (getattr(ph, "geotech", None) or [])
            if geotech_kind(getattr(record, "kind", "")) == kind
        ]
        items = canvas._hole_items.setdefault(ph.hole_id, [])
        if not records:
            _draw_missing_band(
                canvas, ph, inner, outer, alpha, kind, items)
            continue
        if link_on:
            _draw_density_line(
                canvas, ph, records, inner, outer, lo, hi, alpha, items)
        for record in records:
            colour = QColor(geotech_colour(float(record.value), kind, lo, hi))
            if alpha < 255:
                colour.setAlpha(alpha)
            tooltip = geotech_tooltip(canvas, ph, record, kind)
            if getattr(record, "is_interval", False):
                _draw_interval_band(
                    canvas, ph, record, inner, outer, colour,
                    tooltip, kind, items)
            else:
                _draw_point_marker(
                    canvas, ph, record, inner, outer, colour, radius,
                    tooltip, kind, items)


def _anchor_points(canvas, ph, records, centre: float) -> dict:
    """Position scène de chaque mesure, indexée par son ancrage."""
    points = {}
    for record in records:
        anchor = geotech_anchor(record)
        if anchor is None or anchor in points:
            continue
        frame = canvas._depth_tick_anchor(ph, float(anchor))
        if frame is None:
            continue
        sp, tdx, tdy = frame
        nx, ny = rightward_normal(float(tdx), float(tdy))
        points[anchor] = (
            float(sp.x()) + nx * centre, float(sp.y()) + ny * centre)
    return points


def _draw_density_line(canvas, ph, records, inner, outer, lo, hi, alpha,
                       items):
    """Courbe de tendance de la densité (mesures voisines seulement).

    Les paires viennent de ``core.geotech.geotech_link_pairs`` : un vide
    réel rompt la courbe au lieu d'être comblé — on ne trace jamais une
    tendance qui n'a pas été mesurée.  Chaque segment prend la couleur de
    la rampe à la valeur moyenne de ses deux extrémités.
    """
    centre = (float(inner) + float(outer)) / 2.0
    points = _anchor_points(canvas, ph, records, centre)
    for first, second in geotech_link_pairs(records):
        start = points.get(geotech_anchor(first))
        end = points.get(geotech_anchor(second))
        if start is None or end is None:
            continue
        middle = (float(first.value) + float(second.value)) / 2.0
        colour = QColor(geotech_colour(middle, "density", lo, hi))
        if alpha < 255:
            colour.setAlpha(alpha)
        line = QGraphicsLineItem(
            QLineF(start[0], start[1], end[0], end[1]))
        line.setPen(QPen(colour, 1.5))
        line.setZValue(5.1)          # sous les points (5.5), sur le vide
        canvas.scene.addItem(line)
        items.append(line)


def _draw_interval_band(canvas, ph, record, inner, outer, colour,
                        tooltip, kind, items):
    from_m = float(record.from_m)
    to_m = float(record.to_m)
    f, t = min(from_m, to_m), max(from_m, to_m)
    if t - f < 1e-9:
        return
    poly = canvas._band_poly(ph, f, t, inner, outer)
    if poly is None:
        return
    item = QGraphicsPolygonItem(poly)
    item.setBrush(QBrush(colour))
    item.setPen(QPen(QColor("#202020"), 0.5))
    item.setZValue(5.2)
    item.setToolTip(tooltip)
    canvas.scene.addItem(item)
    items.append(item)
    try:
        item.setData(0, (
            "geotech", kind, ph.hole_id, float(record.value), t,
            float(item.pen().color().red()), str(record.comment or "")))
    except Exception as _exc:
        # identification optionnelle — ne bloque jamais une bande déjà dessinée
        log_swallowed("section_geotech : identification bande", _exc)


def _draw_point_marker(canvas, ph, record, inner, outer, colour,
                       radius, tooltip, kind, items):
    depth = float(record.depth)
    frame = canvas._depth_tick_anchor(ph, depth)
    if frame is None:
        return
    sp, tdx, tdy = frame
    nx, ny = rightward_normal(float(tdx), float(tdy))
    centre = (float(inner) + float(outer)) / 2.0
    cx = float(sp.x()) + nx * centre
    cy = float(sp.y()) + ny * centre
    marker = QGraphicsEllipseItem(
        cx - radius, cy - radius, radius * 2.0, radius * 2.0)
    marker.setBrush(QBrush(colour))
    marker.setPen(QPen(QColor("#202020"), 0.5))
    marker.setZValue(5.5)
    marker.setToolTip(tooltip)
    canvas.scene.addItem(marker)
    items.append(marker)
    try:
        marker.setData(0, (
            "geotech", kind, ph.hole_id, float(record.value), depth,
            int(marker.brush().color().red()), str(record.comment or "")))
    except Exception as _exc:
        # identification optionnelle — ne bloque jamais un point déjà dessiné
        log_swallowed("section_geotech : identification point", _exc)


def _draw_missing_band(canvas, ph, inner, outer, alpha, kind, items):
    """Bande grisée + hachures pour un forage sans mesure du domaine."""
    total = float(getattr(ph, "total_depth", 0.0) or 0.0)
    if total <= 0:
        return
    poly = canvas._band_poly(ph, 0.0, total, inner, outer)
    if poly is None:
        return
    grey = QColor(GEOTECH_MISSING_COLOUR)
    if alpha < 255:
        grey.setAlpha(alpha)
    item = QGraphicsPolygonItem(poly)
    item.setBrush(QBrush(grey))
    pen = QPen(QColor(GEOTECH_MISSING_EDGE), 1.0, Qt.PenStyle.DashLine)
    if alpha < 255:
        pen.setColor(QColor(GEOTECH_MISSING_EDGE))
    item.setPen(pen)
    item.setZValue(5.0)
    item.setToolTip(canvas.tr(
        "Aucune mesure {domain} pour ce forage.").format(
            domain=canvas.tr(geotech_label(kind))))
    canvas.scene.addItem(item)
    items.append(item)


# ---------------------------------------------------------------------------
# Page de réglages
# ---------------------------------------------------------------------------
def build_geotech_group(widget, kind: str):
    """Page « domaine géotechnique » du groupe Pistes (une par kind)."""
    kind = geotech_kind(kind)
    frame = widget._group_frame()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(6, 6, 6, 8)
    layout.setSpacing(6)

    title = widget.tr(geotech_label(kind))
    chk = QCheckBox(widget.tr("Afficher {domain}").format(domain=title))
    chk.setToolTip(widget.tr(
        "Valeurs numériques colorées par rampe · grisée sans fichier"))
    chk.setChecked(True)
    chk.stateChanged.connect(widget._on_section_style_change)
    layout.addWidget(chk)
    setattr(widget, f"chk_{kind}", chk)

    form = QFormLayout()
    side = QComboBox()
    side.addItem(widget.tr("Gauche"), "left")
    side.addItem(widget.tr("Droite"), "right")
    side.setCurrentIndex(1)
    side.setStyleSheet(INPUT_STYLE)
    side.setToolTip(widget.tr("Côté de la piste {domain}").format(
        domain=title))
    side.currentIndexChanged.connect(widget._on_section_style_change)
    form.addRow(widget.tr("Côté"), side)
    setattr(widget, f"{kind}_side", side)

    width = QDoubleSpinBox()
    width.setRange(2, 40)
    width.setValue(13.0)
    width.setSuffix(" px")
    width.setStyleSheet(INPUT_STYLE)
    width.valueChanged.connect(widget._on_section_style_change)
    form.addRow(widget.tr("Largeur de voie"), width)
    setattr(widget, f"{kind}_width", width)

    opacity = QSpinBox()
    opacity.setRange(0, 100)
    opacity.setValue(90)
    opacity.setSuffix(" %")
    opacity.setStyleSheet(INPUT_STYLE)
    opacity.valueChanged.connect(widget._on_section_style_change)
    form.addRow(widget.tr("Opacité"), opacity)
    setattr(widget, f"{kind}_opacity", opacity)

    if kind == "density":
        marker = QDoubleSpinBox()
        marker.setRange(2, 20)
        marker.setValue(6.0)
        marker.setSingleStep(0.5)
        marker.setSuffix(" px")
        marker.setStyleSheet(INPUT_STYLE)
        marker.setToolTip(widget.tr(
            "Taille des points de densité (mode ponctuel)"))
        marker.valueChanged.connect(widget._on_section_style_change)
        form.addRow(widget.tr("Taille des points"), marker)
        setattr(widget, "density_marker_size", marker)
    layout.addLayout(form)

    if kind == "density":
        link = QCheckBox(widget.tr("Relier les points (courbe de tendance)"))
        link.setToolTip(widget.tr(
            "Segment tracé uniquement entre mesures voisines : un vide "
            "réel rompt la courbe, il n'est jamais comblé."))
        link.setChecked(True)
        link.stateChanged.connect(widget._on_section_style_change)
        layout.addWidget(link)
        setattr(widget, "density_link", link)

    layout.addWidget(make_collapsible_help(widget.tr(
        "Bande colorée selon la valeur (rampe continue) ; la valeur et "
        "l'unité restent dans l'infobulle. Densité ponctuelle par "
        "défaut, segments acceptés si from/to sont présents.")))
    layout.addStretch(1)
    return frame


# ---------------------------------------------------------------------------
# Style read / apply
# ---------------------------------------------------------------------------
def read_geotech_style(widget, kind: str) -> dict:
    kind = geotech_kind(kind)
    chk = getattr(widget, f"chk_{kind}", None)
    side = getattr(widget, f"{kind}_side", None)
    width = getattr(widget, f"{kind}_width", None)
    opacity = getattr(widget, f"{kind}_opacity", None)
    data = {
        f"show_{kind}": chk is not None and chk.isChecked(),
        f"{kind}_width": width.value() if width is not None else 13.0,
        f"{kind}_side": (side.currentData() or "right")
        if side is not None else "right",
        f"{kind}_opacity": opacity.value() if opacity is not None else 90,
    }
    if kind == "density":
        marker = getattr(widget, "density_marker_size", None)
        data["density_marker_size"] = (
            marker.value() if marker is not None else 6.0)
        link = getattr(widget, "density_link", None)
        data["density_link"] = (
            link.isChecked() if link is not None else True)
    return data


def apply_geotech_style_to_widget(widget, style, kind: str):
    kind = geotech_kind(kind)
    chk = getattr(widget, f"chk_{kind}", None)
    if chk is None:
        return
    chk.setChecked(style.get(f"show_{kind}", True))
    side = getattr(widget, f"{kind}_side", None)
    if side is not None:
        widget._set_combo_data(side, style.get(f"{kind}_side", "right"))
    width = getattr(widget, f"{kind}_width", None)
    if width is not None:
        width.setValue(float(style.get(f"{kind}_width", 13.0)))
    opacity = getattr(widget, f"{kind}_opacity", None)
    if opacity is not None:
        opacity.setValue(int(style.get(f"{kind}_opacity", 90)))
    if kind == "density":
        marker = getattr(widget, "density_marker_size", None)
        if marker is not None:
            marker.setValue(float(style.get("density_marker_size", 6.0)))
        link = getattr(widget, "density_link", None)
        if link is not None:
            link.setChecked(bool(style.get("density_link", True)))


# ---------------------------------------------------------------------------
# Légende
# ---------------------------------------------------------------------------
def _legend_swatch(colour: str) -> str:
    """Pastille de couleur HTML (rampe et gris « sans mesure »)."""
    return f'<span style="background:{colour};">&nbsp;&nbsp;&nbsp;</span>'


def create_legend_widgets(widget, layout, kind: str):
    """Construit le bloc légende (titre + rampe) d'un domaine géotechnique."""
    kind = geotech_kind(kind)
    title = QLabel(widget.tr("{domain} — échelle quantitative").format(
        domain=widget.tr(geotech_label(kind))))
    title.setStyleSheet(
        f"font-weight:bold; color:{COLORS['primary']}; margin-top:6px;")
    setattr(widget, f"{kind}_legend_title", title)
    layout.addWidget(title)

    label = QLabel(widget.tr("Aucune mesure {domain} disponible.").format(
        domain=widget.tr(geotech_label(kind))))
    label.setObjectName("label_hint")
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    setattr(widget, f"{kind}_legend_label", label)
    layout.addWidget(label)

    ramp = QLabel()
    ramp.setTextFormat(Qt.TextFormat.RichText)
    ramp.setWordWrap(True)
    setattr(widget, f"{kind}_legend_ramp", ramp)
    layout.addWidget(ramp)
    return label


def refresh_geotech_legend(widget, kind: str, has: bool) -> bool:
    """Affiche/masque et remplit la légende d'un domaine géotechnique."""
    kind = geotech_kind(kind)
    # La légende n'est visible que si la piste a réellement été dessinée :
    # draw_geotech remplit `_geotech_legend_ranges[kind]`.  Sans données
    # dessinées, on ne montre ni le bloc ni une échelle 0–100 fantôme.
    drawn = kind in (getattr(widget.canvas, "_geotech_legend_ranges", None)
                     or {})
    show = bool(getattr(widget.canvas, f"_{kind}", False)
                and has and drawn)
    title = getattr(widget, f"{kind}_legend_title", None)
    label = getattr(widget, f"{kind}_legend_label", None)
    ramp = getattr(widget, f"{kind}_legend_ramp", None)
    if title is not None:
        title.setVisible(show)
    if label is not None:
        label.setVisible(show)
    if ramp is not None:
        ramp.setVisible(show)
    if not show or ramp is None:
        return show
    ranges = getattr(widget.canvas, "_geotech_legend_ranges", None) or {}
    # Mêmes bornes que le dessin (remplies par draw_geotech) : la légende
    # ne recalcule jamais son échelle dans son coin.
    lo, hi, unit = ranges.get(kind, geotech_legend_scale(kind))
    from ..core.geotech import geotech_ramp_rgb
    colours = "".join(
        _legend_swatch(colour) for colour in geotech_ramp_rgb(kind, lo, hi))
    unit_text = str(unit or "").strip() or geotech_default_unit(kind)
    if label is not None:
        label.setText(
            f"{lo:g} {unit_text} &nbsp;{colours}&nbsp; {hi:g} {unit_text}"
            f"<br/>{_legend_swatch(GEOTECH_MISSING_COLOUR)} "
            f"{widget.tr('Gris : aucune mesure pour ce forage.')}")
    return show


# ---------------------------------------------------------------------------
# Câblage compact (gardes BUD-160 de section_dock.py)
# ---------------------------------------------------------------------------
def init_geotech_defaults(widget):
    """Initialise les attributs par défaut des trois pistes (une passe)."""
    for kind, marker in (("rqd", 5.0), ("recovery", 5.0), ("density", 6.0)):
        # Attribut de visibilité : `_rqd` / `_recovery` / `_density` (le
        # même que geotech_display_attrs / draw_geotech / track_spec).
        setattr(widget, f"_{kind}", True)
        setattr(widget, f"_{kind}_width", 13.0)
        setattr(widget, f"_{kind}_side", "right")
        setattr(widget, f"_{kind}_opacity", 90)
        setattr(widget, f"_{kind}_marker_size", marker)
    widget._density_link = True
    widget._geotech_legend_ranges = {}


def geotech_display_attrs() -> dict:
    """Clés de style → attributs du Canvas pour les trois pistes."""
    attrs = {}
    for kind in GEOTECH_KIND_ORDER:
        attrs[f"show_{kind}"] = f"_{kind}"
        attrs[f"{kind}_width"] = f"_{kind}_width"
        attrs[f"{kind}_side"] = f"_{kind}_side"
        attrs[f"{kind}_opacity"] = f"_{kind}_opacity"
        attrs[f"{kind}_marker_size"] = f"_{kind}_marker_size"
    attrs["density_link"] = "_density_link"
    return attrs


def geotech_track_pages(widget) -> list:
    """Pages Pistes des trois domaines (ordre stable, i18n au point)."""
    return [
        (widget.tr("RQD"), build_geotech_group(widget, "rqd"), "rqd", True),
        (widget.tr("Récupération"),
         build_geotech_group(widget, "recovery"), "recovery", True),
        (widget.tr("Densité"),
         build_geotech_group(widget, "density"), "density", True),
    ]


def geotech_track_tips(widget) -> dict:
    """Infobulles Pistes des trois domaines (i18n au point)."""
    return {
        "rqd": widget.tr(
            "Bande colorée 0–100 % · grisée sans fichier"),
        "recovery": widget.tr(
            "Bande colorée 0–100 % · grisée sans fichier"),
        "density": widget.tr(
            "Points/segments colorés · grisée sans fichier"),
    }


def add_geotech_legends(widget, layout):
    """Ajoute les trois blocs légende (une passe, BUD-160)."""
    for kind in GEOTECH_KIND_ORDER:
        create_legend_widgets(widget, layout, kind)


def refresh_all_geotech_legends(widget):
    """Rafraîchit visibilité + contenu des trois légendes géotechniques."""
    for kind in GEOTECH_KIND_ORDER:
        refresh_geotech_legend(
            widget, kind, widget._project_has_domain_data(kind))
