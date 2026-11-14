"""v2.9.260 — étape 2 : rendu des mesures de structure sur la coupe 2D.

Functions live here (not inline in ``section_dock.py``) so the cross-section
monolith stays under its BUD-160 line budget while the Structures track keeps
its drawing, tooltip, panel page and legend in one dedicated component.
"""

import math

from qgis.PyQt.QtCore import QCoreApplication, QPointF, Qt
from qgis.PyQt.QtGui import (
    QBrush, QColor, QFont, QPainter, QPen, QPixmap, QPolygonF)
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsPolygonItem, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget)

from .styles_qt import (
    BUTTON_SECONDARY, COLORS, INPUT_STYLE, make_collapsible_help)
from ..core.diagnostics import log_swallowed
from ..core.structure_classify import structure_family
from ..core.track_bands import LANE_WIDTH_PX


# v2.9.260 — SYNCHRO 2D ↔ 3D des mesures `structure`.  Le clic 2D sur une
# mesure et le contour de sélection 3D → 2D vivent ICI (pas dans
# section_dock.py) pour respecter le budget de lignes BUD-160.
_SELECTION_HIGHLIGHT_COLOR = "#00E5FF"


def structure_click_target(items_at_pos):
    """Identifie une mesure `structure` sous le clic 2D.

    Retourne ``(hole_id, depth, code, tooltip)`` ou ``None``.  Les items
    des mesures portent ``data(0) = ("structure", hole_id, depth, code,
    cx, cy, radius)`` posé par ``draw_structures``.
    """
    for item in (items_at_pos or []):
        if hasattr(item, "acceptedMouseButtons") \
                and item.acceptedMouseButtons() == Qt.NoButton:
            continue
        data = item.data(0) if hasattr(item, "data") else None
        if isinstance(data, tuple) and len(data) >= 4 \
                and data[0] == "structure":
            return (str(data[1]), float(data[2]), str(data[3]),
                    item.toolTip() or "")
    return None


def apply_structure_click(ws, target):
    """Sélectionne la mesure 2D dans l'espace de travail partagé.

    ``target`` vient de ``structure_click_target``.  Gère le toggle-off de
    la même manière que les intervalles.  Retourne ``True`` (le clic est
    consommé, l'appelant ne doit pas le traiter comme un intervalle).
    """
    if not target or ws is None:
        return True
    hole_id, depth, _code, tip = target
    curr_sel = ws.get_selected_interval()
    curr_hole = getattr(curr_sel, "hole_id", None) if curr_sel else None
    curr_from = getattr(curr_sel, "from_m", 0.0) if curr_sel else 0.0
    curr_to = getattr(curr_sel, "to_m", 0.0) if curr_sel else 0.0
    if (curr_sel and curr_hole == hole_id
            and abs(curr_from - depth) < 1e-3
            and abs(curr_to - depth) < 1e-3):
        ws.clear_selection()
        return True
    ws.select_interval(
        hole_id=hole_id,
        from_m=depth,
        to_m=depth,
        domain="structure",
        source="section_2d",
        attributes={"tooltip": tip.strip()},
    )
    return True


def highlight_structure_point(canvas, hole_id, depth) -> bool:
    """Contour de sélection 3D → 2D d'une mesure `structure`.

    Retourne ``True`` si au moins un marqueur correspond (la bande litho
    ne doit pas être dessinée par-dessus pour une sélection ponctuelle).
    """
    items = list(getattr(canvas, "_hole_items", {}).get(hole_id, []))
    found = False
    for it in items:
        try:
            data = it.data(0) if hasattr(it, "data") else None
        except Exception as _exc:
            log_swallowed(
                "section_structure : lecture identité item "
                "(contour sélection)", _exc)
            data = None
        if not (isinstance(data, tuple) and len(data) >= 7
                and data[0] == "structure"):
            continue
        if abs(float(data[2]) - float(depth)) > 1e-3:
            continue
        try:
            cx, cy, radius = (
                float(data[4]), float(data[5]), float(data[6]))
            item = canvas._draw_selection_outline(
                "ellipse", (cx, cy, radius),
                color=_SELECTION_HIGHLIGHT_COLOR)
            if item is not None:
                canvas._interval_selection_items.append(item)
                found = True
        except Exception as _exc:
            log_swallowed(
                "section_structure : contour de sélection "
                "(mesure structure)", _exc)
    return found


def _legend_label(text: str) -> "QLabel":
    """v2.9.22 — libellé de légende en petites capitales (même rendu)."""
    label = QLabel(QCoreApplication.translate(
        "SectionWidget", str(text or "")))
    label.setWordWrap(True)
    font = label.font()
    try:
        font.setCapitalization(QFont.SmallCaps)
    except Exception as _exc:
        log_swallowed("section_structure : _legend_label", _exc)
        pass
    font.setPointSize(max(8, font.pointSize()))
    label.setFont(font)
    label.setStyleSheet(
        (label.styleSheet() or "") +
        "border:none; background:transparent; padding:0;")
    return label


def draw_structures(canvas, sr):
    """v2.9.260 — pastilles point par mesure de structure.

    One marker per measurement at its measured depth along the drawn trace,
    coloured by the ``structure`` domain style, inside the ``structures``
    lane. No orientation is drawn here (dip/alpha stay tooltip + 3D step).
    """
    from ..core.track_layout import rightward_normal
    lane = canvas._track_plan.by_key.get("structures") \
        if getattr(canvas, "_track_plan", None) else None
    if lane is None:
        return
    radius = max(float(getattr(canvas, "_structure_marker_size", 5.0)) / 2.0,
                 1.5)
    step = radius * 2.0 + 2.0
    min_gap = max(float(getattr(canvas, "_structure_min_spacing", 9.0)),
                  radius * 2.0 + 2.0)
    centre = (float(lane.inner_edge) + float(lane.outer_edge)) / 2.0
    sign = 1.0 if lane.side == "right" else -1.0
    alpha = round(255 * float(getattr(canvas, "_structure_opacity", 90))
                  / 100.0)
    for ph in sr.holes:
        records = sorted(
            getattr(ph, "structure", None) or [],
            key=lambda record: float(record.depth))
        occupied: list[tuple[float, float]] = []
        items = canvas._hole_items.setdefault(ph.hole_id, [])
        for record in records:
            code = str(getattr(record, "structure_type", "")
                       or getattr(record, "type", "") or "").strip()
            if not code:
                continue
            style = canvas._style_for("structure", code)
            if style.get("visible", True) is False:
                continue
            frame = canvas._depth_tick_anchor(ph, float(record.depth))
            if frame is None:
                continue
            sp, tdx, tdy = frame
            nx, ny = rightward_normal(float(tdx), float(tdy))
            offset = centre
            cx = float(sp.x()) + nx * offset
            cy = float(sp.y()) + ny * offset
            # Density rule (explicit): shift outward until no overlap.
            for _ in range(6):
                free = all(
                    math.hypot(cx - ox, cy - oy) >= min_gap
                    for ox, oy in occupied)
                if free:
                    break
                offset += sign * step
                cx = float(sp.x()) + nx * offset
                cy = float(sp.y()) + ny * offset
            occupied.append((cx, cy))
            colour = QColor(str(style.get("color") or "#808080"))
            if alpha < 255:
                colour.setAlpha(alpha)
            item_start = len(items)
            family = structure_family(code)
            has_dip = (
                getattr(record, "dip", None) is not None
                and getattr(record, "dip_direction", None) is not None)
            symbol_len = max(float(getattr(
                canvas, "_structure_marker_size", 5.0)) * 2.4, 12.0)
            tooltip = structure_tooltip(canvas, ph, record, code)
            if family == "linear" and has_dip:
                _draw_linear_arrow(
                    canvas, cx, cy, float(record.dip),
                    float(record.dip_direction), colour, symbol_len,
                    tooltip, items)
            elif family in ("planar", "unknown") and has_dip:
                # Planar (and unknown-but-oriented) structures: tadpole tick.
                _draw_planar_tadpole(
                    canvas, cx, cy, float(record.dip),
                    float(record.dip_direction), colour, symbol_len,
                    tooltip, items)
                _draw_marker(
                    canvas, cx, cy, radius, colour, tooltip, items)
            else:
                # Composite / non-orientable / missing orientation: point.
                _draw_marker(
                    canvas, cx, cy, radius, colour, tooltip, items)
            # v2.9.260 — SYNC 2D↔3D : chaque item de la mesure porte une
            # identité (hole_id, profondeur, code, centre, rayon) pour que
            # le clic 2D sélectionne la MÊME mesure dans la Vue 3D et que
            # la 3D→2D sache dessiner le contour de sélection sur elle.
            for it in items[item_start:]:
                try:
                    it.setData(0, (
                        "structure", ph.hole_id, float(record.depth),
                        code, float(cx), float(cy), float(radius)))
                except Exception as _exc:
                    log_swallowed(
                        "section_structure : identification item "
                        "(synchronisation 2D↔3D)", _exc)
            canvas._legend_register_geom(
                "structure", code, "ellipse", (cx, cy, float(radius)))


def _section_bearing(canvas):
    """Azimut de la ligne de coupe en degrés (0=N, 90=E)."""
    line = getattr(canvas, "_line", None)
    if line is None:
        sr = getattr(canvas, "_result", None)
        line = getattr(sr, "line", None) if sr is not None else None
    if line is None or getattr(line, "length", 0.0) < 1e-9:
        return 0.0
    bearing = math.degrees(math.atan2(float(line.dx), float(line.dy)))
    return bearing % 360.0


def _scene_dip_vector(canvas, dip: float, dip_direction: float):
    """Unit scene vector of the down-dip direction under the current scales.

    The apparent dip in the section plane comes from projecting the true
    down-dip unit vector ``(cos(dip)*cos(delta), -sin(dip))`` (data space)
    into scene space (X = along section, Y = down = negative elevation).
    """
    delta = math.radians((float(dip_direction) - _section_bearing(canvas))
                         % 360.0)
    dip_rad = math.radians(float(dip))
    ux = math.cos(dip_rad) * math.cos(delta)
    uz = math.sin(dip_rad)
    sx = max(float(getattr(canvas, "_sx", 1.0) or 1.0), 1e-9)
    sy = max(float(getattr(canvas, "_sy", 1.0) or 1.0), 1e-9)
    vx = sx * ux
    vy = sy * uz
    norm = math.hypot(vx, vy) or 1.0
    return vx / norm, vy / norm


def _draw_marker(canvas, cx, cy, radius, colour, tooltip, items):
    marker = QGraphicsEllipseItem(
        cx - radius, cy - radius, radius * 2.0, radius * 2.0)
    marker.setBrush(QBrush(colour))
    marker.setPen(QPen(QColor("#202020"), 0.5))
    marker.setZValue(5.5)
    marker.setToolTip(tooltip)
    canvas.scene.addItem(marker)
    items.append(marker)
    return marker


def _draw_planar_tadpole(canvas, cx, cy, dip, dip_direction,
                         colour, length, tooltip, items):
    """Tadpole planaire : point + queue UNIQUE côté direction du pendage.

    La queue part du point vers le bas-pendage projeté dans la coupe ; il
    n'y a jamais de trait symétrique traversant (le sens du pendage doit
    rester lisible sur la page).
    """
    vx, vy = _scene_dip_vector(canvas, dip, dip_direction)
    tail = float(length)
    pen = QPen(colour, max(1.0, 0.8))
    line = canvas.scene.addLine(cx, cy, cx + vx * tail, cy + vy * tail, pen)
    line.setZValue(5.4)
    line.setToolTip(tooltip)
    items.append(line)
    return line


def _draw_linear_arrow(canvas, cx, cy, dip, dip_direction,
                       colour, length, tooltip, items):
    """Flèche orientée selon la plongée apparente (linéation/axe)."""
    vx, vy = _scene_dip_vector(canvas, dip, dip_direction)
    ex = cx + vx * float(length)
    ey = cy + vy * float(length)
    line = canvas.scene.addLine(cx, cy, ex, ey, QPen(colour, 1.2))
    line.setZValue(5.4)
    line.setToolTip(tooltip)
    items.append(line)
    back = 6.0
    side = 2.8
    bx = ex - vx * back
    by = ey - vy * back
    arrow = QPolygonF([
        QPointF(ex, ey),
        QPointF(bx - vy * side, by + vx * side),
        QPointF(bx + vy * side, by - vx * side),
    ])
    poly = QGraphicsPolygonItem(arrow)
    poly.setBrush(QBrush(colour))
    poly.setPen(QPen(colour, 1))
    poly.setZValue(5.6)
    poly.setToolTip(tooltip)
    canvas.scene.addItem(poly)
    items.append(poly)
    return poly


def structure_tooltip(canvas, ph, record, code):
    """Infobulle compacte d'un point de structure (données non inventées)."""
    label = (canvas._style_for("structure", code).get("label") or code)
    lines = [
        f"{ph.hole_id} · {float(record.depth):g} m",
        f"{code} · {label}" if str(label).strip() else code,
    ]
    if record.dip is not None and record.dip_direction is not None:
        lines.append(canvas.tr(
            "Pendage {dip}° / direction {dd}°").format(
                dip=float(record.dip), dd=float(record.dip_direction)))
    elif record.alpha is not None and record.beta is not None:
        lines.append(canvas.tr("Alpha {a}° / bêta {b}°").format(
            a=float(record.alpha), b=float(record.beta)))
    if record.confidence:
        lines.append(canvas.tr("Confiance : {value}").format(
            value=record.confidence))
    if record.comment:
        lines.append(str(record.comment))
    return "\n".join(lines)


def build_structure_group(widget):
    """v2.9.260 — page « Structures » du groupe Pistes."""
    frame = widget._group_frame()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(6, 6, 6, 8)
    layout.setSpacing(6)

    widget.chk_structures = QCheckBox(widget.tr("Afficher les structures"))
    widget.chk_structures.setToolTip(widget.tr(
        "Référentiel + taille/espacement · grisée sans fichier"))
    widget.chk_structures.setChecked(True)
    widget.chk_structures.stateChanged.connect(widget._on_section_style_change)
    layout.addWidget(widget.chk_structures)

    form = QFormLayout()
    widget.structure_side = QComboBox()
    widget.structure_side.addItem(widget.tr("Gauche"), "left")
    widget.structure_side.addItem(widget.tr("Droite"), "right")
    widget.structure_side.setCurrentIndex(1)
    widget.structure_side.setStyleSheet(INPUT_STYLE)
    widget.structure_side.setToolTip(widget.tr(
        "Côté de la piste des structures"))
    widget.structure_side.currentIndexChanged.connect(
        widget._on_section_style_change)
    form.addRow(widget.tr("Côté"), widget.structure_side)

    widget.structure_width = QDoubleSpinBox()
    widget.structure_width.setRange(2, 40)
    widget.structure_width.setValue(LANE_WIDTH_PX)
    widget.structure_width.setSuffix(" px")
    widget.structure_width.setStyleSheet(INPUT_STYLE)
    widget.structure_width.valueChanged.connect(
        widget._on_section_style_change)
    form.addRow(widget.tr("Largeur de voie"), widget.structure_width)

    widget.structure_marker_size = QDoubleSpinBox()
    widget.structure_marker_size.setRange(2, 20)
    widget.structure_marker_size.setValue(5.0)
    widget.structure_marker_size.setSingleStep(0.5)
    widget.structure_marker_size.setSuffix(" px")
    widget.structure_marker_size.setStyleSheet(INPUT_STYLE)
    widget.structure_marker_size.valueChanged.connect(
        widget._on_section_style_change)
    form.addRow(widget.tr("Taille des points"), widget.structure_marker_size)

    widget.structure_min_spacing = QDoubleSpinBox()
    widget.structure_min_spacing.setRange(4, 40)
    widget.structure_min_spacing.setValue(9.0)
    widget.structure_min_spacing.setSingleStep(1.0)
    widget.structure_min_spacing.setSuffix(" px")
    widget.structure_min_spacing.setStyleSheet(INPUT_STYLE)
    widget.structure_min_spacing.setToolTip(widget.tr(
        "Espacement minimal entre deux pastilles ; au-delà, la mesure "
        "suivante est décalée vers l'extérieur de la voie"))
    widget.structure_min_spacing.valueChanged.connect(
        widget._on_section_style_change)
    form.addRow(widget.tr("Espacement minimal"), widget.structure_min_spacing)

    widget.structure_opacity = QSpinBox()
    widget.structure_opacity.setRange(0, 100)
    widget.structure_opacity.setValue(90)
    widget.structure_opacity.setSuffix(" %")
    widget.structure_opacity.setStyleSheet(INPUT_STYLE)
    widget.structure_opacity.valueChanged.connect(
        widget._on_section_style_change)
    form.addRow(widget.tr("Opacité"), widget.structure_opacity)
    layout.addLayout(form)

    layout.addWidget(make_collapsible_help(widget.tr(
        "Un point par mesure à sa profondeur exacte, coloré par type dans "
        "le Référentiel. Les orientations et la confiance restent dans "
        "l'infobulle.")))
    edit_symbols = QPushButton(widget.tr("Libellés et symboles…"))
    edit_symbols.setStyleSheet(BUTTON_SECONDARY)
    edit_symbols.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    edit_symbols.setToolTip(widget.tr("Référentiel · Type de structure"))
    edit_symbols.clicked.connect(
        lambda _checked=False: widget._open_domain_reference("structure"))
    layout.addWidget(edit_symbols)

    # v2.9.261 — Incrément B : ouverture du dialogue rose/stéréonet.
    analyse_btn = QPushButton(widget.tr("Analyser les structures…"))
    analyse_btn.setStyleSheet(BUTTON_SECONDARY)
    analyse_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    analyse_btn.setToolTip(widget.tr(
        "Rose des directions et stéréonet des mesures de structure"))
    analyse_btn.clicked.connect(
        lambda _checked=False: open_structure_analysis(widget))
    layout.addWidget(analyse_btn)
    layout.addStretch(1)
    return frame


def _legend_structure_pixmap(family, radius, colour):
    """Pastille légende fidèle au rendu coupe : mini-tadpole / mini-flèche /
    point simple.

    Planaire (et inconnu orienté)  = point + queue sans pointe (tadpole) ;
    linéaire                       = flèche SANS point de base (comme la
                                     coupe : trait + pointe) ;
    composite / non-orientable     = point simple.
    La pastille est plus grande que l'ancienne (28×16) et la queue plus
    longue pour qu'un tadpole ne se confonde plus avec une flèche.
    """
    w, h = 28, 16
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    centre = QPointF(6.0, 8.0)
    end = QPointF(22.0, 12.0)
    if family == "linear":
        painter.setPen(QPen(colour, 1.2))
        painter.drawLine(centre, end)
        vx = end.x() - centre.x()
        vy = end.y() - centre.y()
        norm = math.hypot(vx, vy) or 1.0
        ux, uy = vx / norm, vy / norm
        bx = end.x() - ux * 5.5
        by = end.y() - uy * 5.5
        arrow = QPolygonF([
            end,
            QPointF(bx - uy * 2.6, by + ux * 2.6),
            QPointF(bx + uy * 2.6, by - ux * 2.6),
        ])
        painter.setBrush(QBrush(colour))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawPolygon(arrow)
    elif family in ("planar", "unknown"):
        painter.setPen(QPen(colour, 1.0))
        painter.drawLine(centre, end)
    if family != "linear":
        # Point de base du tadpole (planaire/inconnu) et point simple
        # (composite / non-orientable) ; la mini-flèche reste sans pastille.
        painter.setBrush(QBrush(colour))
        painter.setPen(QPen(QColor("#202020"), 0.5))
        painter.drawEllipse(centre, radius, radius)
    painter.end()
    return pixmap


def fill_structure_legend(widget, grid):
    """v2.9.260 — pastille de point + libellé par type dans la légende."""
    widget._clear_layout(grid)
    from .section_holes import legend_source_holes  # v313 légende = coupe
    codes = {
        str(getattr(st, "structure_type", None)
            or getattr(st, "type", None) or "").strip()
        for dh in legend_source_holes(widget)
        for st in (getattr(dh, "structure", None) or [])
        if str(getattr(st, "structure_type", None)
               or getattr(st, "type", None) or "").strip()
    }
    codes = sorted(
        codes,
        key=lambda code: (
            (widget.canvas._style_for("structure", code).get("label")
             or code).casefold(),
            code.casefold()))
    codes = [
        code for code in codes
        if widget.canvas._style_for("structure", code).get(
            "visible", True) is not False]
    if not codes:
        return
    for index, code in enumerate(codes):
        style = widget.canvas._style_for("structure", code)
        entry = QWidget()
        row_layout = QHBoxLayout(entry)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        swatch = QLabel()
        swatch.setFixedSize(28, 16)
        radius = max(
            float(getattr(widget.canvas, "_structure_marker_size", 5.0))
            / 2.0, 2.0)
        colour = QColor(str(style.get("color") or "#808080"))
        swatch.setPixmap(_legend_structure_pixmap(
            structure_family(code), radius, colour))
        swatch.setToolTip(code)
        label = _legend_label(style.get("label") or code)
        label.setToolTip(str(code))
        row_layout.addWidget(swatch)
        row_layout.addWidget(label, 1)
        widget._wire_legend_highlight_entry(entry, "structure", code)
        grid.addWidget(entry, index // 2, index % 2)


def has_data(dhs):
    """True if at least one source drillhole carries a structure measurement."""
    return any(getattr(dh, "structure", None) for dh in (dhs or []))


def track_spec(widget, sr):
    """v2.9.260 — spec du plan de pistes pour la voie Structures."""
    return {
        "side": widget._structure_side,
        "width": float(widget._structure_width),
        "active": (bool(widget._show_structures)
                   and any(getattr(ph, "structure", None)
                           for ph in sr.holes)),
    }


def update_legend_visibility(widget, has_structure):
    """Affiche/masque le bloc légende Structures (piste cochée + données)."""
    show = bool(
        getattr(widget.canvas, "_show_structures", False) and has_structure)
    for attr in ("structure_legend_title", "structure_legend_widget"):
        obj = getattr(widget, attr, None)
        if obj is not None:
            obj.setVisible(show)
    return show


def open_structure_analysis(widget):
    """v2.9.261 — ouvre l'analyse rose/stéréonet depuis la page Structures.

    La collecte passe par ``core.structure_analysis`` ; le dialogue reste
    léger et ne voit jamais le moteur QGIS de la coupe.  Il reçoit les deux
    jeux (projet + section courante) et l'``WorkspaceState`` partagé pour
    la synchronisation 2D↔3D (Incrément C).
    """
    from ..core.structure_analysis import collect_samples_from_holes
    from .structure_analysis_dialog import StructureAnalysisDialog

    holes = getattr(widget, "_drillholes", None) or []
    project_samples = collect_samples_from_holes(holes)
    canvas = getattr(widget, "canvas", None)
    section_holes = []
    sr = getattr(canvas, "_result", None) if canvas is not None else None
    if sr is not None:
        section_holes = list(getattr(sr, "holes", None) or [])
    section_samples = collect_samples_from_holes(section_holes)

    def code_color(code):
        if canvas is None or not hasattr(canvas, "_style_for"):
            return "#808080"
        return canvas._style_for("structure", code).get("color", "#808080")

    main_dock = getattr(widget, "main_dock", None)
    workspace_state = None
    if main_dock is not None:
        workspace_state = getattr(main_dock, "workspace_state", None)

    # v2.9.261 — dialogue NON modal : l'utilisateur peut laisser l'analyse
    # ouverte et vérifier la surbrillance 2D/3D derrière, sans fermer la rose.
    existing = getattr(widget, "_structure_analysis_dialog", None)
    if existing is not None and existing.isVisible():
        existing.raise_()
        existing.activateWindow()
        return

    dialog = StructureAnalysisDialog(
        samples=project_samples,
        section_samples=section_samples,
        parent=widget,
        code_color=code_color,
        workspace_state=workspace_state,
    )
    dialog.setWindowModality(Qt.NonModal)
    dialog.setAttribute(Qt.WA_DeleteOnClose, True)
    widget._structure_analysis_dialog = dialog

    def _forget_dialog():
        if getattr(widget, "_structure_analysis_dialog", None) is dialog:
            widget._structure_analysis_dialog = None

    dialog.finished.connect(_forget_dialog)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()


def create_legend_widgets(widget, layout):
    """v2.9.260 — construit le bloc légende Structures (une fois)."""
    title = QLabel(widget.tr("Structures — catégories"))
    title.setStyleSheet(
        f"font-weight:bold; color:{COLORS['primary']}; margin-top:6px;")
    widget.structure_legend_title = title
    layout.addWidget(title)
    holder = QWidget()
    grid = QGridLayout(holder)
    grid.setContentsMargins(0, 2, 0, 0)
    grid.setHorizontalSpacing(8)
    grid.setVerticalSpacing(5)
    widget.structure_legend_widget = holder
    widget.structure_legend_layout = grid
    layout.addWidget(holder)
    return holder


def read_structure_style(widget):
    """Lit les 6 clés de la piste Structures depuis les widgets du panneau."""
    return {
        "show_structures": getattr(widget, "chk_structures", None) is not None
        and widget.chk_structures.isChecked(),
        "structure_width": getattr(widget, "structure_width", None).value()
        if getattr(widget, "structure_width", None) else LANE_WIDTH_PX,
        "structure_opacity": getattr(widget, "structure_opacity", None).value()
        if getattr(widget, "structure_opacity", None) else 90,
        "structure_side": (
            (widget.structure_side.currentData() or "right")
            if getattr(widget, "structure_side", None) else "right"),
        "structure_marker_size": (
            widget.structure_marker_size.value()
            if getattr(widget, "structure_marker_size", None) else 5.0),
        "structure_min_spacing": (
            widget.structure_min_spacing.value()
            if getattr(widget, "structure_min_spacing", None) else 9.0),
    }


def apply_structure_style_to_widget(widget, style):
    """Applique les 6 clés Structures aux widgets du panneau (rétrocompat)."""
    if getattr(widget, "chk_structures", None) is None:
        return
    widget.chk_structures.setChecked(style.get("show_structures", True))
    widget._set_combo_data(widget.structure_side,
                           style.get("structure_side", "right"))
    widget.structure_width.setValue(
        float(style.get("structure_width", LANE_WIDTH_PX)))
    widget.structure_marker_size.setValue(
        float(style.get("structure_marker_size", 5.0)))
    widget.structure_min_spacing.setValue(
        float(style.get("structure_min_spacing", 9.0)))
    widget.structure_opacity.setValue(
        int(style.get("structure_opacity", 90)))
