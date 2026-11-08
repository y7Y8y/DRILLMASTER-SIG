"""DrillMaster — les contours de sélection de la coupe 2D (chantier 6, tranche 2).

Extrait de ``ui/section_dock.py``. Ces trois fonctions dessinent le **trait
qui entoure une bande sélectionnée** — celui qu'on voit quand on clique une
entrée de légende : un contour extérieur qui ne mange ni le voisin du dessus
ni celui du dessous.

Pourquoi elles sortent en premier
---------------------------------
Ce sont les seules de la classe ``SectionCanvas`` qui ne lisent **rien** de
l'instance : ni couleur, ni échelle, ni état. Trois fonctions, 122 lignes,
une géométrie pure — Qt ne leur donne qu'un polygone et rend un chemin. Le
déplacement ne peut donc pas changer un pixel, et c'est ce qui rend la
tranche sûre : on ne déplace pas du code qu'on espère équivalent, on déplace
du code qui n'a aucun accès à l'état.

Ce que ce module possède
------------------------
- ``_inset_band_depth_ends`` : rentre les deux bouts en profondeur d'un
  trapèze (anti-débordement sur les intervalles voisins) ;
- ``_exterior_outline_path`` : élargit un chemin vers l'extérieur (le trait
  du pinceau reste hors de la bande) ;
- ``_exterior_outline_path_from_poly`` : l'enchaînement des deux, à partir
  d'un polygone ;
- ``_add_tooltip_hit_pad`` : la zone de survol élargie (le seul lien avec la
  vue était ``self.scene``, désormais passé en argument) ;
- ``_draw_axis_aligned_pattern_lines`` : les traits de motif calés sur l'axe
  du forage — 130 lignes de trigonométrie, même contrat.

``section_dock`` ré-exporte les trois : aucun appelant n'a eu à changer.
"""
from __future__ import annotations

import math

import math

from qgis.PyQt.QtCore import QPointF, Qt
from qgis.PyQt.QtGui import (
    QBrush, QColor, QPainterPath, QPainterPathStroker, QPen, QPolygonF,
)

from .coupe_socle import _ClippedStrokeItem


def _inset_band_depth_ends(poly, inset: float = 1.0):
    """Rentre les bords From/To d'une bande trapèze (anti-débord voisins).

    Winding historique band_trapezoid :
    [top_inner, top_outer, bottom_outer, bottom_inner].
    Les côtés latéraux (inner/outer) restent ; seuls les bouts
    profondeur sont décalés vers l'intérieur avant l'expand extérieur.
    """
    if poly is None or inset <= 0:
        return poly
    try:
        n = int(poly.size()) if hasattr(poly, "size") else len(poly)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
        return poly
    if n < 4:
        return poly
    try:
        pts = [poly.at(i) for i in range(n)]
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
        try:
            pts = list(poly)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
            return poly
    ti, to, bo, bi = pts[0], pts[1], pts[2], pts[3]
    mid_tx = 0.5 * (float(ti.x()) + float(to.x()))
    mid_ty = 0.5 * (float(ti.y()) + float(to.y()))
    mid_bx = 0.5 * (float(bi.x()) + float(bo.x()))
    mid_by = 0.5 * (float(bi.y()) + float(bo.y()))
    dx = mid_bx - mid_tx
    dy = mid_by - mid_ty
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return poly
    # bande trop courte : inset proportionnel (ne pas inverser)
    max_in = max(0.0, 0.35 * length)
    ins = min(float(inset), max_in)
    if ins <= 1e-9:
        return poly
    ux, uy = dx / length, dy / length

    def _mv(p, s):
        return QPointF(float(p.x()) + ux * s, float(p.y()) + uy * s)

    new_pts = [_mv(ti, ins), _mv(to, ins), _mv(bo, -ins), _mv(bi, -ins)]
    for extra in pts[4:]:
        new_pts.append(extra)
    try:
        return QPolygonF(new_pts)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Piste lithologie : _inset_band_depth_ends", _exc)
        return poly


def _exterior_outline_path_from_poly(poly, *, gap: float = 0.35,
                                    pen_w: float = 1.5,
                                    depth_inset: float = 1.0):
    """Contour extérieur autour d'un QPolygonF (bandes litho / teneurs).

    v2.9.107 — inset From/To puis expand latéral : le trait ne mange
    plus les intervalles voisins en profondeur.
    """
    if poly is None:
        return None
    try:
        poly2 = _inset_band_depth_ends(poly, inset=float(depth_inset))
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("section_dock : _exterior_outline_path_from_poly", _exc)
        # inset optionnel
        poly2 = poly
    path = QPainterPath()
    try:
        path.addPolygon(poly2 if poly2 is not None else poly)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("section_dock : _exterior_outline_path_from_poly", _exc)
        # poly invalide
        return None
    return _exterior_outline_path(path, gap=gap, pen_w=pen_w)


def _exterior_outline_path(path, *, gap: float = 0.35,
                           pen_w: float = 1.5):
    """Élargit un QPainterPath vers l'extérieur (gap + demi-trait).

    Le chemin retourné est la région élargie : le stroke du pen est
    centré sur son contour extérieur → le trait reste hors de la
    bande (gap libre latéral). Fill = none à l'appelant.
    """
    if path is None:
        return None
    try:
        src = QPainterPath(path)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("section_dock : _exterior_outline_path", _exc)
        # copie path impossible
        return None
    if src.isEmpty():
        return None
    # expand jusqu'au centre du trait = gap + pen_w/2
    expand = max(float(gap) + float(pen_w) * 0.5, 0.35)
    try:
        stroker = QPainterPathStroker()
        stroker.setWidth(expand * 2.0)
        stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
        rim = stroker.createStroke(src)
        outer = src.united(rim)
        if outer is None or outer.isEmpty():
            return src
        return outer
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("section_dock : _exterior_outline_path", _exc)
        # stroker indisponible — pas d'offset
        return src


def _add_tooltip_hit_pad(scene, items, poly, tooltip, z_value=4.2):
    """v2.9.12 — zone de survol élargie pour infobulle.

    Les micro-intervalles (1 m) et les voies d'une double altération font
    des polygones trop fins pour la souris. Un pad invisible (~8 px de
    demi-largeur) reprend le même tooltip, au-dessus du remplissage mais
    sous les codes (z 15).

    Chantier 6, tranche 3 — la scène est passée en argument au lieu d'être
    lue sur ``self`` : c'est le seul lien que la fonction avait avec la vue.
    """
    if not tooltip or poly is None:
        return
    try:
        path = QPainterPath()
        path.addPolygon(poly)
        stroker = QPainterPathStroker()
        stroker.setWidth(8.0)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        fat = stroker.createStroke(path)
        # united with original so the interior still hits
        fat = fat.united(path)
        # brush quasi-invisible mais « solide » pour le hit-test
        brush = QBrush(QColor(0, 0, 0, 1))
        hit = scene.addPath(fat, QPen(Qt.PenStyle.NoPen), brush)
        hit.setZValue(float(z_value))
        hit.setToolTip(tooltip)
        # ne pas voler les clics de sélection de forage
        hit.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        items.append(hit)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("section_dock : _add_tooltip_hit_pad", _exc)
        # stroker/path indisponible : pas de pad, tooltip polygone seul
        pass


def _draw_axis_aligned_pattern_lines(scene, items, poly, brush_style, ink_colour,
                                 z_value, axis_dx, axis_dy):
    """v2.9.31 — ≥2 traits H/V/diag RELATIFS À L'AXE du forage.

    Repère local :
      û = axe (from→to le long du trou) ;
      n̂ = normale droite (vers l'extérieur de bande).
    « vertical »   = // û  (suit la trajectoire) ;
    « horizontal » = // n̂  (⊥ trajectoire) ;
    FDiag / BDiag  = ±45° dans ce repère.

    Chantier 6, tranche 3 — même contrat : la scène arrive en argument.
    """
    al = math.hypot(float(axis_dx), float(axis_dy))
    if al < 0.5:
        # trou quasi-point : repli écran
        axis_dx, axis_dy, al = 0.0, 1.0, 1.0
    ux, uy = float(axis_dx) / al, float(axis_dy) / al
    # normale droite (scène y-down)
    nx, ny = -uy, ux
    # centre + demi-axes via bbox corners projected
    br = poly.boundingRect()
    cx = br.center().x()
    cy = br.center().y()
    # étendues le long de û et n̂ (max projection des 4 coins)
    corners = [
        (float(poly[i].x()), float(poly[i].y()))
        for i in range(min(4, len(poly)))]
    if len(corners) < 2:
        return
    projs_u = [(x - cx) * ux + (y - cy) * uy for x, y in corners]
    projs_n = [(x - cx) * nx + (y - cy) * ny for x, y in corners]
    u_min, u_max = min(projs_u), max(projs_u)
    n_min, n_max = min(projs_n), max(projs_n)
    len_u = max(u_max - u_min, 1.0)
    len_n = max(n_max - n_min, 1.0)

    def _n_lines(length):
        return max(2, min(5, int(float(length) / 3.5)))

    strokes = QPainterPath()

    def _seg(u0, n0, u1, n1):
        x0 = cx + u0 * ux + n0 * nx
        y0 = cy + u0 * uy + n0 * ny
        x1 = cx + u1 * ux + n1 * nx
        y1 = cy + u1 * uy + n1 * ny
        strokes.moveTo(x0, y0)
        strokes.lineTo(x1, y1)

    kinds = []
    if brush_style in (Qt.BrushStyle.HorPattern, Qt.BrushStyle.CrossPattern):
        kinds.append("H")  # // normale = « horizontal » log
    if brush_style in (Qt.BrushStyle.VerPattern, Qt.BrushStyle.CrossPattern):
        kinds.append("V")  # // axe = « vertical » log
    if brush_style in (Qt.BrushStyle.FDiagPattern, Qt.BrushStyle.DiagCrossPattern):
        kinds.append("FD")
    if brush_style in (Qt.BrushStyle.BDiagPattern, Qt.BrushStyle.DiagCrossPattern):
        kinds.append("BD")

    for kind in kinds:
        if kind == "V":
            # traits // axe : espacés le long de la normale
            n = _n_lines(len_n)
            for i in range(1, n + 1):
                nn = n_min + (n_max - n_min) * i / (n + 1.0)
                _seg(u_min, nn, u_max, nn)
        elif kind == "H":
            # traits ⊥ axe : espacés le long de l'axe
            n = _n_lines(len_u)
            for i in range(1, n + 1):
                uu = u_min + (u_max - u_min) * i / (n + 1.0)
                _seg(uu, n_min, uu, n_max)
        elif kind == "FD":
            # diagonale u+n = const
            span = len_u + len_n
            count = max(2, min(6, int(span / 4.0)))
            for i in range(1, count + 1):
                c = (u_min + n_min) + span * i / (count + 1.0)
                # u+n=c intersect rectangle [u_min,u_max]×[n_min,n_max]
                pts = []
                for u in (u_min, u_max):
                    nn = c - u
                    if n_min - 1e-6 <= nn <= n_max + 1e-6:
                        pts.append((u, nn))
                for nn in (n_min, n_max):
                    u = c - nn
                    if u_min - 1e-6 <= u <= u_max + 1e-6:
                        pts.append((u, nn))
                uniq = []
                for pt in pts:
                    if all(abs(pt[0]-q[0]) > 1e-4 or abs(pt[1]-q[1]) > 1e-4
                           for q in uniq):
                        uniq.append(pt)
                if len(uniq) >= 2:
                    _seg(uniq[0][0], uniq[0][1], uniq[1][0], uniq[1][1])
        elif kind == "BD":
            # diagonale u-n = const
            span = len_u + len_n
            count = max(2, min(6, int(span / 4.0)))
            c_min = u_min - n_max
            c_max = u_max - n_min
            for i in range(1, count + 1):
                c = c_min + (c_max - c_min) * i / (count + 1.0)
                pts = []
                for u in (u_min, u_max):
                    nn = u - c
                    if n_min - 1e-6 <= nn <= n_max + 1e-6:
                        pts.append((u, nn))
                for nn in (n_min, n_max):
                    u = c + nn
                    if u_min - 1e-6 <= u <= u_max + 1e-6:
                        pts.append((u, nn))
                uniq = []
                for pt in pts:
                    if all(abs(pt[0]-q[0]) > 1e-4 or abs(pt[1]-q[1]) > 1e-4
                           for q in uniq):
                        uniq.append(pt)
                if len(uniq) >= 2:
                    _seg(uniq[0][0], uniq[0][1], uniq[1][0], uniq[1][1])

    if strokes.isEmpty():
        return
    pen = QPen(ink_colour, 1.0)
    pen.setCosmetic(True)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    clip_item = _ClippedStrokeItem(poly, strokes, pen)
    clip_item.setZValue(float(z_value) + 0.01)
    scene.addItem(clip_item)
    items.append(clip_item)
