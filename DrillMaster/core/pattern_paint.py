"""
DEPRECATED (audit 2.9.87) — non utilisé sur le chemin actif de rendu.
paint_style n'est branché que via _StyledFillItem (lui-même mort).
Coupe/légende/réf actifs = brush Qt + drawers locaux 2.9.33/87.
Ne pas supprimer encore.  Voir audit 2.9.87 A-03.

PatternRenderer unique — coupe, légende, référentiel (v2.9.86).

    paint_style(painter, clip_rect_or_path, style, *, axis_dx, axis_dy)

Même StyleDefinition → même géométrie de motif ; seul le clip change.
Pas de dessin spécifique « si légende ».  Vectoriel (traits / points),
pas de BrushStyle Qt comme source de vérité du SENS.

Dépend de Qt uniquement à l'appel (QPainter) — import lazy.
"""
from __future__ import annotations

import math
from typing import Sequence, Union

from .geo_style import (
    StyleDefinition,
    style_from_pattern,
    DEFAULT_DOT_RADIUS_RATIO,
    DEFAULT_UNDERLAY_ALPHA,
)


def _axis_frame(axis_dx: float, axis_dy: float):
    al = math.hypot(float(axis_dx), float(axis_dy))
    if al < 0.5:
        return 0.0, 1.0, -1.0, 0.0
    ux, uy = float(axis_dx) / al, float(axis_dy) / al
    return ux, uy, -uy, ux  # normale droite (y-down)


def _bounds_un(corners, cx, cy, ux, uy, nx, ny):
    pu = [(x - cx) * ux + (y - cy) * uy for x, y in corners]
    pn = [(x - cx) * nx + (y - cy) * ny for x, y in corners]
    u0, u1 = min(pu), max(pu)
    n0, n1 = min(pn), max(pn)
    return u0, u1, n0, n1, max(u1 - u0, 1.0), max(n1 - n0, 1.0)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _n_el(length, spacing):
    if length < 1.0 or spacing <= 0:
        return 0
    # plafond bas : grammaire lisible, pas texture dense
    return max(2, min(12, int(float(length) / float(spacing))))


def _corners_from_rect(x, y, w, h):
    return [
        (float(x), float(y)),
        (float(x) + float(w), float(y)),
        (float(x) + float(w), float(y) + float(h)),
        (float(x), float(y) + float(h)),
    ]


def _layout_geometry(style: StyleDefinition, corners, axis_dx, axis_dy):
    """Calcule segments / dots en coords scène (pur Python).

    v2.9.86 — spacing = identité de la clé (profil), pas un écrasement
    adaptatif qui rend diagonal ≈ backward ≈ horizontal.
    """
    kind = style.kind
    if kind not in ("lines", "dots") or len(corners) < 2:
        return kind, False, [], [], 0.0

    cx = sum(p[0] for p in corners) / len(corners)
    cy = sum(p[1] for p in corners) / len(corners)
    if style.follow_axis:
        ux, uy, nx, ny = _axis_frame(axis_dx, axis_dy)
    else:
        # légende : axe vertical fictif (convention log)
        ux, uy, nx, ny = 0.0, 1.0, -1.0, 0.0
    # rotation_deg du style (repère local)
    if abs(float(style.rotation_deg)) > 1e-6:
        rad = math.radians(float(style.rotation_deg))
        co, si = math.cos(rad), math.sin(rad)
        ux, uy = ux * co - uy * si, ux * si + uy * co
        nx, ny = -uy, ux

    u0, u1, n0, n1, len_u, len_n = _bounds_un(corners, cx, cy, ux, uy, nx, ny)
    size = min(len_u, len_n)
    if size < float(style.min_motif_px):
        return kind, False, [], [], 0.0

    # Identité clé : spacing du profil.  Ne compresser que si < 2 traits.
    spacing = float(style.spacing_for_key())
    if size < spacing * 1.1:
        spacing = _clamp(size / 2.0, 2.5, spacing)

    def xy(u, n):
        return (cx + u * ux + n * nx, cy + u * uy + n * ny)

    segs, dots = [], []
    key = style.key

    if kind == "lines":
        kinds = []
        if key in ("horizontal", "cross"):
            kinds.append("H")
        if key in ("vertical", "cross"):
            kinds.append("V")
        if key in ("diagonal", "diagonal_cross"):
            kinds.append("FD")
        if key in ("backward_diagonal", "diagonal_cross"):
            kinds.append("BD")

        def add_seg(uu0, nn0, uu1, nn1):
            x0, y0 = xy(uu0, nn0)
            x1, y1 = xy(uu1, nn1)
            segs.append((x0, y0, x1, y1))

        for knd in kinds:
            if knd == "V":
                # // axe : lignes le long de u, espacées en n
                n = _n_el(len_n, spacing)
                for i in range(1, n + 1):
                    nn = n0 + (n1 - n0) * i / (n + 1.0)
                    add_seg(u0, nn, u1, nn)
            elif knd == "H":
                # ⊥ axe
                n = _n_el(len_u, spacing)
                for i in range(1, n + 1):
                    uu = u0 + (u1 - u0) * i / (n + 1.0)
                    add_seg(uu, n0, uu, n1)
            elif knd == "FD":
                span = len_u + len_n
                count = max(2, min(10, int(span / spacing)))
                for i in range(1, count + 1):
                    c = (u0 + n0) + span * i / (count + 1.0)
                    hits = []
                    for u in (u0, u1):
                        nn = c - u
                        if n0 - 1e-6 <= nn <= n1 + 1e-6:
                            hits.append((u, nn))
                    for nn in (n0, n1):
                        u = c - nn
                        if u0 - 1e-6 <= u <= u1 + 1e-6:
                            hits.append((u, nn))
                    uniq = []
                    for pt in hits:
                        if all(abs(pt[0] - q[0]) > 1e-4 or abs(pt[1] - q[1]) > 1e-4
                               for q in uniq):
                            uniq.append(pt)
                    if len(uniq) >= 2:
                        add_seg(uniq[0][0], uniq[0][1], uniq[1][0], uniq[1][1])
            elif knd == "BD":
                count = max(2, min(10, int((len_u + len_n) / spacing)))
                c_min, c_max = u0 - n1, u1 - n0
                for i in range(1, count + 1):
                    c = c_min + (c_max - c_min) * i / (count + 1.0)
                    hits = []
                    for u in (u0, u1):
                        nn = u - c
                        if n0 - 1e-6 <= nn <= n1 + 1e-6:
                            hits.append((u, nn))
                    for nn in (n0, n1):
                        u = c + nn
                        if u0 - 1e-6 <= u <= u1 + 1e-6:
                            hits.append((u, nn))
                    uniq = []
                    for pt in hits:
                        if all(abs(pt[0] - q[0]) > 1e-4 or abs(pt[1] - q[1]) > 1e-4
                               for q in uniq):
                            uniq.append(pt)
                    if len(uniq) >= 2:
                        add_seg(uniq[0][0], uniq[0][1], uniq[1][0], uniq[1][1])
        return kind, len(segs) >= 1, segs, [], spacing

    # dots — rayon + stagger du profil (identité)
    dspace = spacing
    nu = _n_el(len_u, dspace)
    nn = _n_el(len_n, dspace)
    if nu < 1 or nn < 1:
        return kind, False, [], [], dspace
    r = float(getattr(style, "dot_radius_px", 0) or 0) or _clamp(
        dspace * DEFAULT_DOT_RADIUS_RATIO, 1.2, 2.4)
    r = _clamp(r, 1.1, 2.6)  # gros disques lisibles, pas grains de sable
    stagger = bool(getattr(style, "stagger", False))
    for i in range(1, nu + 1):
        uu = u0 + (u1 - u0) * i / (nu + 1.0)
        row_shift = (dspace * 0.5) if (stagger and (i % 2 == 0)) else 0.0
        for j in range(1, nn + 1):
            nnn = n0 + (n1 - n0) * j / (nn + 1.0) + row_shift
            if nnn < n0 - 1e-6 or nnn > n1 + 1e-6:
                continue
            x, y = xy(uu, nnn)
            dots.append((x, y, r))
    return kind, len(dots) >= 1, [], dots, dspace



def paint_style(
    painter,
    style: StyleDefinition,
    *,
    rect=None,
    polygon_points: Sequence[tuple[float, float]] | None = None,
    axis_dx: float = 0.0,
    axis_dy: float = 1.0,
    draw_underlay: bool = True,
    draw_border: bool = False,
    border_color: str = "#7F8C8D",
    background: str = "",
):
    """Dessine ``style`` dans le clip donné — API UNIQUE coupe/légende.

    Fournir ``rect`` (x, y, w, h) OU ``polygon_points`` [(x,y), …].
    """
    # Lazy Qt
    from qgis.PyQt.QtCore import Qt, QPointF, QRectF
    from qgis.PyQt.QtGui import (
        QColor, QPen, QBrush, QPainterPath,
    )

    if rect is not None:
        x, y, w, h = [float(v) for v in rect]
        corners = _corners_from_rect(x, y, w, h)
        clip = QPainterPath()
        clip.addRect(QRectF(x, y, w, h))
        bounds = QRectF(x, y, w, h)
    elif polygon_points and len(polygon_points) >= 2:
        corners = [(float(p[0]), float(p[1])) for p in polygon_points]
        clip = QPainterPath()
        clip.moveTo(corners[0][0], corners[0][1])
        for px, py in corners[1:]:
            clip.lineTo(px, py)
        clip.closeSubpath()
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        bounds = QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
    else:
        return

    painter.save()
    painter.setRenderHint(painter.Antialiasing, False)
    try:
        painter.setClipPath(clip)
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("pattern_paint : paint_style", _exc)
        # clip indisponible — dessin un peu hors bande, mieux que crash
        pass

    if background:
        painter.fillRect(bounds, QColor(background))

    fill = QColor(style.fill_color or "#CCCCCC")
    fill.setAlpha(int(round(255 * float(style.fill_alpha))))

    if style.kind == "none":
        painter.restore()
        return

    if style.kind == "solid" or not style.has_motif:
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(fill, Qt.SolidPattern))
        painter.drawPath(clip)
        if draw_border:
            painter.setPen(QPen(QColor(border_color), 1))
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawPath(clip)
        painter.restore()
        return

    # underlay
    if draw_underlay:
        under = QColor(fill)
        under.setAlpha(int(round(
            fill.alpha() * float(style.underlay_alpha or DEFAULT_UNDERLAY_ALPHA))))
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(under, Qt.SolidPattern))
        painter.drawPath(clip)

    kind, ok, segs, dots, _sp = _layout_geometry(
        style, corners, axis_dx, axis_dy)
    if not ok:
        # trop petit : aplat plein (honnête)
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(fill, Qt.SolidPattern))
        painter.drawPath(clip)
        if draw_border:
            painter.setPen(QPen(QColor(border_color), 1))
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawPath(clip)
        painter.restore()
        return

    ink = QColor(style.resolved_ink(lightness=fill.lightness()))
    ink.setAlpha(255)

    if kind == "lines" and segs:
        pen = QPen(ink, float(style.stroke_px or 1.0))
        pen.setCosmetic(True)
        pen.setCapStyle(Qt.FlatCap)
        dash = tuple(getattr(style, "dash", ()) or ())
        if dash:
            # tireté cosmétique — rythme propre à la clé (╱≠╲, +≠×)
            try:
                pen.setStyle(Qt.CustomDashLine)
                pen.setDashPattern([float(v) for v in dash])
            except Exception as _exc:
                from .diagnostics import log_swallowed
                log_swallowed("pattern_paint : paint_style", _exc)
                # setDashPattern indisponible — trait continu
                pass
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.NoBrush))
        for x0, y0, x1, y1 in segs:
            painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))
    elif kind == "dots" and dots:
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(ink))
        for x, y, r in dots:
            painter.drawEllipse(QPointF(x, y), r, r)

    if draw_border:
        painter.setPen(QPen(QColor(border_color), 1))
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawPath(clip)

    painter.restore()


def paint_style_swatch(
    style: StyleDefinition,
    width: float = 44,
    height: float = 22,
    *,
    pad: float = 2.0,
    background: str = "#FFFFFF",
    border_color: str = "#7F8C8D",
):
    """QPixmap pastille — même paint_style que la coupe (légende / référentiel)."""
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtGui import QPixmap, QPainter, QColor

    w, h = int(max(width, 4)), int(max(height, 4))
    pix = QPixmap(w, h)
    pix.fill(QColor(background))
    painter = QPainter(pix)
    # légende : pas follow_axis → axe fictif vertical dans paint
    leg_style = StyleDefinition(
        key=style.key,
        kind=style.kind,
        fill_color=style.fill_color,
        ink_color=style.ink_color,
        spacing_px=style.spacing_px,
        stroke_px=style.stroke_px,
        rotation_deg=style.rotation_deg,
        follow_axis=False,
        underlay_alpha=style.underlay_alpha,
        fill_alpha=style.fill_alpha,
        min_motif_px=min(float(style.min_motif_px), 4.0),
        dash=tuple(getattr(style, "dash", ()) or ()),
        dot_radius_px=float(getattr(style, "dot_radius_px", 1.1) or 1.1),
        stagger=bool(getattr(style, "stagger", False)),
    )
    paint_style(
        painter, leg_style,
        rect=(pad, pad, w - 2 * pad, h - 2 * pad),
        axis_dx=0.0, axis_dy=1.0,
        draw_underlay=True,
        draw_border=True,
        border_color=border_color,
        background="",
    )
    painter.end()
    return pix


def style_from_band(pattern_key: str, colour_hex: str, alpha: float = 1.0,
                    *, follow_axis: bool = True) -> StyleDefinition:
    """Raccourci coupe / légende depuis clé + couleur bande."""
    try:
        from .reference import PATTERN_UNDERLAY_ALPHA_RATIO
        ua = float(PATTERN_UNDERLAY_ALPHA_RATIO)
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("Piste lithologie : style_from_band", _exc)
        # référence indisponible hors plugin — défaut local
        ua = DEFAULT_UNDERLAY_ALPHA
    return style_from_pattern(
        pattern_key, colour_hex,
        fill_alpha=alpha,
        follow_axis=follow_axis,
        underlay_alpha=ua,
    )
