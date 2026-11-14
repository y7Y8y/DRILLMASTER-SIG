"""v2.9.261 — Incrément B : dialogue d'analyse `structure`.

Le dialogue consomme STRICTEMENT ``core.structure_analysis.py`` :
aucune conversion d'angle, aucune projection et aucun bin n'est calculé
dans ``paintEvent``.  Le calcul est préparé une fois par ``set_model()`` /
``set_rose_mode()``, puis les widgets ne font que dessiner des coordonnées,
des chemins et des infobulles déjà préparés.

Séparation voulue :
- ``core/structure_analysis.py`` = moteur (oriente, projette, tranche) ;
- ``ui/structure_analysis_dialog.py`` = présentation (Qt, filtres,
  infobulles, feedback de sélection, hit-test) ;
- ``WorkspaceState`` ne reçoit que des ``select_interval`` / ``clear_selection``
  (le dialogue n'appelle JAMAIS directement la vue 2D/3D).

Incrément C : filtres dynamiques (périmètre/famille/type), purge des
``_hit_buckets`` aux points visibles seulement, feedback de sélection
(halo cyan) et toggle re-clic / clic dans le vide.
"""

from __future__ import annotations

import math

from qgis.PyQt.QtCore import QPointF, QRectF, Qt, pyqtSignal
from qgis.PyQt.QtGui import (
    QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap,
)
from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout,
    QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from .styles_qt import COLORS, INPUT_STYLE, TOOLTIP_STYLE
from ..core.structure_analysis import (
    StructureSample,
    analysis_counts,
    filter_structure_samples,
    pole_density_grid,
    project_schmidt,
    resolve_orientation,
    rose_bins,
    sample_codes,
)

_MODE_DIRECTION = "direction"
_MODE_ORIENTATION = "orientation"

_SELECTION_COLOR = "#00E5FF"

_HOVER_RADIUS_PX = 4.0
_MIN_HIT_RADIUS = 6.0
_POINT_RADIUS_PX = 3.0
_HOVER_POINT_RADIUS_PX = 4.8
_SELECTED_POINT_RADIUS_PX = 5.6
_GRID_TICKS = 4
_MARGIN_PX = 26.0
_EMPTY_HIT = -1

_DENSITY_GRID_SIZE = 96
_DENSITY_BLUR_PASSES = 4
_DENSITY_MIN_ALPHA = 16
_DENSITY_MAX_ALPHA = 158
_DENSITY_MIN_VALUE = 0.018
_DENSITY_CONTOUR_LEVELS = (0.34, 0.68)
_DENSITY_CONTOUR_COLOR = (91, 101, 113, 180)
_DENSITY_STOPS = (
    (0.00, (68, 114, 196)),
    (0.30, (52, 152, 219)),
    (0.50, (241, 196, 15)),
    (0.72, (230, 126, 34)),
    (1.00, (192, 57, 43)),
)


class _StructureRoseWidget(QWidget):
    """Widget "bête" de rose : dessine des ``RoseBin`` déjà calculés."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bins = []
        self._bin_size = 10.0
        self._radius = 80.0
        self._center = QPointF(0.0, 0.0)
        self._wedge_paths = []
        self.setMinimumSize(260, 260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def set_bins(self, bins, bin_size: float = 10.0):
        """Consomme les classes du moteur (aucun calcul d'angle ici)."""
        self._bins = list(bins or [])
        self._bin_size = float(bin_size or 10.0)
        self._rebuild_layout()

    def _wedge_colour(self, start: float) -> QColor:
        """Couleur de classe = périodicité azimutale (lisible sur papier)."""
        hue = int((float(start) % 360.0) * 359.0 / 360.0)
        color = QColor.fromHsv(hue % 360, 170, 210, 165)
        return color

    def _rebuild_layout(self):
        w = max(self.width(), self.minimumWidth())
        h = max(self.height(), self.minimumHeight())
        cx = w / 2.0
        cy = h / 2.0
        radius = max(min(w, h) / 2.0 - (_MARGIN_PX + 8.0), 20.0)
        self._center = QPointF(cx, cy)
        self._radius = radius
        self._wedge_paths = []
        if not self._bins:
            return
        max_count = max((bin_.count for bin_ in self._bins), default=1)
        max_count = max(max_count, 1)
        for bin_ in self._bins:
            if bin_.count <= 0:
                continue
            r = max(radius * float(bin_.count) / float(max_count), 2.0)
            rect = QRectF(
                cx - r, cy - r, r * 2.0, r * 2.0)
            # Qt: 0° = 3 h, sens anti-horaire positif.  On veut 0° = Nord
            # (haut) et des classes qui augmentent en SENS HORAIRE.
            # ``[start,end[`` est donc tracé depuis ``90 - start`` avec un
            # balayage NÉGATIF (sens horaire Qt).
            start_angle = 90.0 - float(bin_.start)
            span = -(float(bin_.end) - float(bin_.start))
            path = QPainterPath()
            path.moveTo(self._center)
            path.arcTo(rect, start_angle, span)
            path.closeSubpath()
            self._wedge_paths.append(
                (path, bin_.count, float(bin_.start)))
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._draw_grid(painter)
        if self._wedge_paths:
            pen = QPen(QColor(COLORS["border_dark"]), 1.0)
            painter.setPen(pen)
            for path, _count, start in self._wedge_paths:
                painter.setBrush(QBrush(self._wedge_colour(start)))
                painter.drawPath(path)
        painter.end()

    def resizeEvent(self, _event):
        self._rebuild_layout()
        super().resizeEvent(_event)

    def _draw_grid(self, painter):
        cx, cy = self._center.x(), self._center.y()
        r = self._radius
        painter.setPen(QPen(QColor(COLORS["border_dark"]), 1.0))
        painter.drawEllipse(self._center, r, r)
        painter.setPen(QPen(QColor(COLORS["border"]), 1.0, Qt.DashLine))
        painter.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        painter.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))

        font = QFont(self.font())
        font.setPointSize(max(7, self.font().pointSize() - 1))
        painter.setFont(font)
        painter.setPen(QColor(COLORS["text_medium"]))
        painter.drawText(QPointF(cx - r - 30.0, cy + 5.0), "0/360")
        painter.drawText(QPointF(cx + r + 6.0, cy + 5.0), "90")
        painter.drawText(QPointF(cx - 12.0, cy - r - 5.0), "N")
        painter.drawText(QPointF(cx - 4.0, cy + r + 13.0), "S")


class _StructureStereonetWidget(QWidget):
    """Widget "bête" de stéréonet : dessine les points déjà projetés.

    Le fond de grille est mis en cache dans un ``QPixmap`` : il n'est
    redessiné que lorsque la taille change, jamais à chaque repaint.
    """

    point_clicked = pyqtSignal(int)      # index dans le modèle visible
    empty_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit_points = []
        self._screen_points = []
        self._hit_zones = []
        self._hit_buckets = {}
        self._hover_index = None
        self._selected_index = None
        self._radius = 80.0
        self._center = QPointF(0.0, 0.0)
        self._grid_cache = QPixmap()
        self._grid_cache_size = (0, 0)
        self._zone_size = 16.0
        self._density_raster = []
        self._density_cache_size = (0, 0)
        self.setMinimumSize(260, 260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def set_model(self, unit_points):
        """Consomme les points projetés par ``core.structure_analysis``.

        ``unit_points`` = liste de ``(index, sample, orientation, ux, uy,
        tooltip)`` dans un repère unité (Est→droite, Nord→haut).

        IMPORTANT (Incrément C) : cette méthode PURGE puis reconstruit
        ``_hit_buckets`` uniquement avec les points présents dans
        ``unit_points`` — jamais de sélection fantôme après un filtre.
        """
        self._unit_points = list(unit_points or [])
        self._hover_index = None
        if self._selected_index is not None \
                and self._selected_index >= len(self._unit_points):
            self._selected_index = None
        self._density_raster = pole_density_grid(
            [(float(ux), float(uy))
             for (_index, _sample, _orientation, ux, uy, _tip)
             in self._unit_points],
            grid_size=_DENSITY_GRID_SIZE,
            blur_passes=_DENSITY_BLUR_PASSES,
        )
        self._density_cache_size = (0, 0)
        self._grid_cache_size = (0, 0)
        self._rebuild_screen()
        self.update()

    def _rebuild_screen(self):
        w = max(self.width(), self.minimumWidth())
        h = max(self.height(), self.minimumHeight())
        margin = _MARGIN_PX + 8.0
        size = max(min(w, h) - margin * 2.0, 60.0)
        self._radius = size / 2.0
        self._center = QPointF(w / 2.0, h / 2.0)
        self._zone_size = max(float(self._radius * 0.06), 14.0)

        self._screen_points = []
        self._hit_zones = []
        self._hit_buckets = {}
        for (index, sample, orientation, ux, uy, tooltip) in self._unit_points:
            sx = self._center.x() + float(ux) * self._radius
            sy = self._center.y() - float(uy) * self._radius
            colour = self._sample_colour(sample)
            self._screen_points.append(
                (index, sample, tooltip, float(sx), float(sy), colour))
            zone = self._zone_key(sx, sy)
            self._hit_buckets.setdefault(zone, []).append(
                (float(sx), float(sy), index))
            self._hit_zones.append(
                (float(sx), float(sy), _POINT_RADIUS_PX, index))
        self._rebuild_grid_cache()
        self.update()

    def set_selected_index(self, index):
        """Surbrillance du pôle sélectionné (Incrément C)."""
        selected = None if index is None or index < 0 \
            else int(index)
        if selected != self._selected_index:
            self._selected_index = selected
            self.update()

    def _sample_colour(self, sample: StructureSample):
        callback = getattr(self, "code_color", None)
        if callable(callback):
            colour = callback(str(sample.code or ""))
            return QColor(str(colour or "#808080"))
        # Repli sans référentiel : couleur stable par code (jamais l'énorme
        # palette du référentiel — ce repli n'est qu'un secours UI).
        index = max(0, hash(str(sample.code or "")) % 7)
        palette = ["#2471A3", "#1E8449", "#B7950B", "#873600",
                   "#6C3483", "#2C3E50", "#A93226"]
        return QColor(palette[index])

    @staticmethod
    def _zone_key(x, y):
        return (int(x // 16.0), int(y // 16.0))

    @staticmethod
    def _density_color(value: float) -> QColor:
        """Rampe bleu → cyan → jaune → orange → rouge pour la densité."""
        v = max(0.0, min(1.0, float(value)))
        red, green, blue = _DENSITY_STOPS[-1][1]
        for idx in range(len(_DENSITY_STOPS) - 1):
            p0, (r0, g0, b0) = _DENSITY_STOPS[idx]
            p1, (r1, g1, b1) = _DENSITY_STOPS[idx + 1]
            if v <= p1:
                span = (p1 - p0) or 1.0
                t = (v - p0) / span
                red = round(r0 + (r1 - r0) * t)
                green = round(g0 + (g1 - g0) * t)
                blue = round(b0 + (b1 - b0) * t)
                break
        alpha = _DENSITY_MIN_ALPHA + round(
            (_DENSITY_MAX_ALPHA - _DENSITY_MIN_ALPHA) * math.sqrt(v))
        return QColor(red, green, blue, alpha)

    def _build_density_image(self) -> QImage:
        """Convertit la grille 0..1 du moteur en QImage alpha (modèle)."""
        grid = self._density_raster
        if not grid:
            return QImage()
        size = len(grid)
        image = QImage(size, size, QImage.Format_RGBA8888)
        image.fill(QColor(0, 0, 0, 0))
        for iy, row in enumerate(grid):
            for ix, value in enumerate(row):
                if value < _DENSITY_MIN_VALUE:
                    continue
                image.setPixelColor(ix, iy, self._density_color(value))
        return image

    def _density_contour_segments(self, level):
        """Segments de contour (marching squares) sur la grille du moteur.

        Retourne des segments en coordonnées écran.  C'est du pré-calcul
        fait dans le cache de grille, jamais dans ``paintEvent``.
        """
        grid = self._density_raster
        if not grid:
            return []
        n = len(grid)
        cx, cy = self._center.x(), self._center.y()
        r = self._radius
        scale = 2.0 * r / float(n - 1)
        segments = []

        def edge_point(p0, p1, v0, v1):
            if abs(v1 - v0) < 1e-9:
                return (p0 + p1) * 0.5
            t = (level - v0) / (v1 - v0)
            return p0 + (p1 - p0) * t

        def to_screen(px, py):
            return (cx + (px / float(n - 1) - 0.5) * scale * float(n - 1),
                    cy + (py / float(n - 1) - 0.5) * scale * float(n - 1))

        for iy in range(n - 1):
            for ix in range(n - 1):
                v0 = grid[iy][ix]        # haut gauche
                v1 = grid[iy][ix + 1]    # haut droit
                v2 = grid[iy + 1][ix + 1]  # bas droit
                v3 = grid[iy + 1][ix]    # bas gauche
                a0 = v0 >= level
                a1 = v1 >= level
                a2 = v2 >= level
                a3 = v3 >= level
                if a0 == a1 == a2 == a3:
                    continue
                crossings = []
                if a0 != a1:
                    t = edge_point(float(ix), float(ix + 1), v0, v1)
                    crossings.append((float(t), float(iy)))
                if a1 != a2:
                    t = edge_point(float(iy), float(iy + 1), v1, v2)
                    crossings.append((float(ix + 1), float(t)))
                if a2 != a3:
                    t = edge_point(float(ix + 1), float(ix), v2, v3)
                    crossings.append((float(t), float(iy + 1)))
                if a3 != a0:
                    t = edge_point(float(iy + 1), float(iy), v3, v0)
                    crossings.append((float(ix), float(t)))
                if len(crossings) == 2:
                    (x0, y0), (x1, y1) = crossings
                    sx0, sy0 = to_screen(x0, y0)
                    sx1, sy1 = to_screen(x1, y1)
                    segments.append((sx0, sy0, sx1, sy1))
                elif len(crossings) == 4:
                    # Cas ambigus (selles) : choix stable selon la parité.
                    if a0 and a2:
                        pairs = ((0, 1), (2, 3))
                    else:
                        pairs = ((1, 2), (3, 0))
                    for first, second in pairs:
                        (x0, y0), (x1, y1) = crossings[first], crossings[second]
                        sx0, sy0 = to_screen(x0, y0)
                        sx1, sy1 = to_screen(x1, y1)
                        segments.append((sx0, sy0, sx1, sy1))
        return segments

    def _draw_density_contours(self, painter):
        """Isodensités discrètes : rendent la heatmap lisible/professionnelle."""
        if not self._density_raster:
            return
        painter.save()
        painter.setClipPath(self._circle_clip_path())
        pen = QPen(QColor(*_DENSITY_CONTOUR_COLOR), 0.8)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.NoBrush))
        for level in _DENSITY_CONTOUR_LEVELS:
            for x0, y0, x1, y1 in self._density_contour_segments(level):
                painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))
        painter.restore()

    def _circle_clip_path(self):
        rect = QRectF(
            self._center.x() - self._radius,
            self._center.y() - self._radius,
            self._radius * 2.0,
            self._radius * 2.0,
        )
        path = QPainterPath()
        path.addEllipse(rect)
        return path

    def _draw_density(self, painter):
        """Dessine la heatmap pré-calculée, masquée au disque."""
        cx, cy = self._center.x(), self._center.y()
        r = self._radius
        image = self._build_density_image()
        self._density_cache_size = (image.width(), image.height())
        if image.isNull():
            return
        rect = QRectF(cx - r, cy - r, r * 2.0, r * 2.0)
        clip = QPainterPath()
        clip.addEllipse(rect)
        painter.save()
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setClipPath(clip)
        painter.drawImage(rect, image)
        painter.restore()
        self._draw_density_contours(painter)

    def _rebuild_grid_cache(self):
        w = max(self.width(), self.minimumWidth())
        h = max(self.height(), self.minimumHeight())
        if (w, h) == self._grid_cache_size and not self._grid_cache.isNull():
            return
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        self._draw_density(painter)
        self._draw_grid(painter)
        painter.end()
        self._grid_cache = pixmap
        self._grid_cache_size = (w, h)

    def _draw_grid(self, painter):
        cx, cy = self._center.x(), self._center.y()
        r = self._radius
        painter.setPen(QPen(QColor(COLORS["border_dark"]), 1.2))
        painter.drawEllipse(self._center, r, r)
        painter.setPen(QPen(QColor(COLORS["border"]), 1.0, Qt.DashLine))
        painter.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        painter.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))
        for i in range(1, _GRID_TICKS):
            frac = float(i) / float(_GRID_TICKS)
            rr = r * frac
            painter.setPen(QPen(QColor(COLORS["border"]), 0.7, Qt.DotLine))
            painter.drawEllipse(self._center, rr, rr)
        # Quadrillage cardinal : N/E/S/O comme labels.
        font = QFont(self.font())
        font.setPointSize(max(7, self.font().pointSize() - 1))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(COLORS["text_medium"]))
        painter.drawText(QPointF(cx - 12.0, cy - r - 6.0), "N")
        painter.drawText(QPointF(cx + r + 4.0, cy + 5.0), "E")
        painter.drawText(QPointF(cx - 4.0, cy + r + 13.0), "S")
        painter.drawText(QPointF(cx - r - 18.0, cy + 5.0), "W")

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self._grid_cache.isNull():
            painter.drawPixmap(0, 0, self._grid_cache)
        for index, sample, tooltip, sx, sy, colour in self._screen_points:
            if index == self._selected_index:
                # Halo de sélection : contour cyan + point légèrement plus
                # grand que les autres (feedback visuel explicite).
                halo = QColor(_SELECTION_COLOR)
                halo.setAlpha(70)
                painter.setPen(QPen(halo, 5.0))
                painter.setBrush(QBrush(Qt.NoBrush))
                painter.drawEllipse(
                    QPointF(sx, sy), _SELECTED_POINT_RADIUS_PX + 3.0,
                    _SELECTED_POINT_RADIUS_PX + 3.0)
                painter.setPen(QPen(QColor(_SELECTION_COLOR), 1.6))
            elif index == self._hover_index:
                painter.setPen(QPen(QColor("#202020"), 0.8))
            else:
                painter.setPen(QPen(QColor("#202020"), 0.6))
            radius = _SELECTED_POINT_RADIUS_PX if index == self._selected_index \
                else (_HOVER_POINT_RADIUS_PX if index == self._hover_index
                      else _POINT_RADIUS_PX)
            painter.setBrush(QBrush(colour))
            painter.drawEllipse(QPointF(sx, sy), radius, radius)
        painter.end()

    def _hit_index_for_pos(self, x, y):
        """Anticipation du clic : résout x,y → index d'échantillon.

        Un simple dictionnaire de buckets (grille mémoire) rend le
        survol/click O(1) au lieu d'un balayage linéaire sur des milliers
        de points.  La méthode renvoie ``_EMPTY_HIT`` si aucun point n'est
        assez proche (le dialogue peut alors vider la sélection).
        """
        zone = self._zone_key(x, y)
        best = None
        best_dist = float("inf")
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for px, py, index in self._hit_buckets.get(
                        (zone[0] + dx, zone[1] + dy), ()):
                    dist_sq = (px - x) ** 2 + (py - y) ** 2
                    if dist_sq < best_dist:
                        best_dist = dist_sq
                        best = index
        if best is None:
            return _EMPTY_HIT
        if math.sqrt(best_dist) > max(_MIN_HIT_RADIUS, _HOVER_RADIUS_PX):
            return _EMPTY_HIT
        return best

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        index = self._hit_index_for_pos(float(pos.x()), float(pos.y()))
        if index == _EMPTY_HIT:
            index = None
        if index != self._hover_index:
            self._hover_index = index
            self.update()
        tooltip = ""
        if index is not None:
            for hit_index, sample, tip, _x, _y, _c in self._screen_points:
                if hit_index == index:
                    tooltip = str(tip or "")
                    break
        self.setToolTip(tooltip)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position() if hasattr(event, "position") else event.pos()
            index = self._hit_index_for_pos(float(pos.x()), float(pos.y()))
            if index == _EMPTY_HIT:
                self.empty_clicked.emit()
            else:
                self.point_clicked.emit(int(index))
            event.accept()
            return
        super().mousePressEvent(event)

    def leaveEvent(self, _event):
        self._hover_index = None
        self.setToolTip("")
        self.update()
        super().leaveEvent(_event)

    def resizeEvent(self, _event):
        self._rebuild_screen()
        super().resizeEvent(_event)


class StructureAnalysisDialog(QDialog):
    """Dialogue d'analyse des mesures structure (rose + stéréonet)."""

    def __init__(self, samples=None, section_samples=None, parent=None,
                 code_color=None, workspace_state=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Analyse des structures"))
        self.setStyleSheet(TOOLTIP_STYLE + BASE_DIALOG_STYLE)
        self.resize(940, 640)
        self.setMinimumSize(880, 560)

        self._project_samples = list(samples or [])
        self._section_samples = list(section_samples or [])
        self._visible_samples = list(self._project_samples)
        self._code_color = code_color
        self._workspace_state = workspace_state
        self._ws_unsubscribers = []
        self._visible_index_by_key = {}
        self._unit_points = []

        self._rose_widget = _StructureRoseWidget()
        self._rose_widget.code_color = code_color
        self._stereonet_widget = _StructureStereonetWidget()
        self._stereonet_widget.code_color = code_color
        self._stereonet_widget.point_clicked.connect(self._on_point_clicked)
        self._stereonet_widget.empty_clicked.connect(self._on_empty_clicked)

        self.scope_combo = QComboBox()
        self.scope_combo.setStyleSheet(INPUT_STYLE)
        self.scope_combo.addItem(self.tr("Section courante"), "section")
        self.scope_combo.addItem(self.tr("Projet"), "project")
        self.scope_combo.setCurrentIndex(1)
        self.scope_combo.currentIndexChanged.connect(self._on_filter_changed)

        self.family_combo = QComboBox()
        self.family_combo.setStyleSheet(INPUT_STYLE)
        self.family_combo.addItem(self.tr("Toutes les familles"), "")
        for label, value in (
                (self.tr("Planaire"), "planar"),
                (self.tr("Linéaire"), "linear"),
                (self.tr("Composite"), "composite"),
                (self.tr("Non-orientable"), "non_orientable"),
                (self.tr("Inconnue"), "unknown")):
            self.family_combo.addItem(label, value)
        self.family_combo.currentIndexChanged.connect(self._on_filter_changed)

        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(INPUT_STYLE)
        self.type_combo.addItem(self.tr("Tous les types"), "")
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)

        self.rose_mode = QComboBox()
        self.rose_mode.setStyleSheet(INPUT_STYLE)
        self.rose_mode.addItem(self.tr("Directions 0–360°"), _MODE_DIRECTION)
        self.rose_mode.addItem(self.tr("Orientations 0–180°"), _MODE_ORIENTATION)
        self.rose_mode.currentIndexChanged.connect(self._on_rose_mode_changed)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(
            f"color:{COLORS['text_medium']}; padding:4px 0;")

        self.selection_label = QLabel()
        self.selection_label.setWordWrap(True)
        self.selection_label.setStyleSheet(
            f"color:{COLORS['accent']}; font-weight:bold; padding:2px 0;")

        rose_title = QLabel(self.tr("Rose"))
        rose_title.setAlignment(Qt.AlignHCenter)
        stereonet_title = QLabel(self.tr("Stéréonet"))
        stereonet_title.setAlignment(Qt.AlignHCenter)

        left = QVBoxLayout()
        left.addWidget(rose_title)
        left.addWidget(self._rose_widget)

        right = QVBoxLayout()
        right.addWidget(stereonet_title)
        right.addWidget(self._stereonet_widget)

        charts = QHBoxLayout()
        charts.addLayout(left, 1)
        charts.addLayout(right, 1)

        # Filtres en 2 colonnes sous les deux graphiques : ils ne rognent
        # plus la rose, donc les deux cercles gardent la même hauteur utile.
        filters = QGridLayout()
        filters.setHorizontalSpacing(14)
        filters.setVerticalSpacing(6)
        filters.addWidget(QLabel(self.tr("Périmètre")), 0, 0)
        filters.addWidget(self.scope_combo, 0, 1)
        filters.addWidget(QLabel(self.tr("Famille")), 0, 2)
        filters.addWidget(self.family_combo, 0, 3)
        filters.addWidget(QLabel(self.tr("Type")), 1, 0)
        filters.addWidget(self.type_combo, 1, 1)
        filters.addWidget(QLabel(self.tr("Mode de la rose")), 1, 2)
        filters.addWidget(self.rose_mode, 1, 3)
        filters.setColumnStretch(1, 1)
        filters.setColumnStretch(3, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(self.tr("Fermer"))
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(charts, 1)
        layout.addLayout(filters)
        layout.addWidget(self.summary)
        layout.addWidget(self.selection_label)
        layout.addWidget(buttons)

        if self._workspace_state is not None:
            self._ws_unsubscribers.append(
                self._workspace_state.subscribe(
                    "selected_interval",
                    self._on_workspace_selected_interval))

        self._recompute_model()

    # ------------------------------------------------------------------
    # Filtres & modèle — le dialogue ne calcule jamais d'angle lui-même
    # ------------------------------------------------------------------
    def _base_samples(self):
        scope = str(self.scope_combo.currentData() or "project")
        if scope == "section" and self._section_samples:
            return list(self._section_samples)
        return list(self._project_samples)

    def _family_filter(self):
        value = str(self.family_combo.currentData() or "")
        return value if value else None

    def _type_filter(self):
        value = str(self.type_combo.currentData() or "")
        return value if value else None

    def _reload_type_combo(self, base_samples):
        """Repeuple Type autour des codes de la famille courante."""
        family = self._family_filter()
        if family:
            candidates = filter_structure_samples(
                base_samples, families={family})
        else:
            candidates = base_samples
        codes = sample_codes(candidates)
        current = self._type_filter()
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        self.type_combo.addItem(self.tr("Tous les types"), "")
        for code in codes:
            self.type_combo.addItem(code, code)
        index = self.type_combo.findData(current)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        self.type_combo.blockSignals(False)

    def _recompute_model(self):
        base_samples = self._base_samples()
        self._reload_type_combo(base_samples)
        families = {self._family_filter()} if self._family_filter() else None
        codes = {self._type_filter()} if self._type_filter() else None
        self._visible_samples = filter_structure_samples(
            base_samples, families=families, codes=codes)

        self._recompute_rose()
        unit_points = self._build_unit_points()
        self._stereonet_widget.set_model(unit_points)
        self._refresh_selected_highlight()
        self._refresh_summary()

    def _build_unit_points(self):
        unit_points = []
        self._visible_index_by_key = {}
        for visible_index, sample in enumerate(self._visible_samples):
            orientation = resolve_orientation(sample)
            if orientation is None:
                continue
            ux, uy = project_schmidt(
                orientation.trend, orientation.plunge, radius=1.0)
            tooltip = self._point_tooltip(sample, orientation)
            unit_points.append(
                (visible_index, sample, orientation, ux, uy, tooltip))
            key = (str(sample.hole_id or ""), round(float(sample.depth), 6))
            self._visible_index_by_key[key] = visible_index
        self._unit_points = unit_points
        return unit_points

    def _recompute_rose(self):
        mode = str(self.rose_mode.currentData() or _MODE_DIRECTION)
        bins = rose_bins(self._visible_samples, mode=mode, bin_size=10.0)
        self._rose_widget.set_bins(bins, bin_size=10.0)

    def _refresh_summary(self):
        counts = analysis_counts(self._visible_samples)
        self.summary.setText(self.tr(
            "Total : {total} · tracées : {oriented} · non tracées : "
            "{no_orientation} (dont alpha/bêta seuls : {alpha_beta} · "
            "non-orientables : {non})\n{planar} planaires · {linear} "
            "linéaires · {composite} composites · {non} non-orientables · "
            "{unknown} inconnues"
        ).format(
            total=counts["total"],
            oriented=counts["oriented"],
            no_orientation=counts["no_orientation"],
            alpha_beta=counts["alpha_beta_only"],
            non=counts["non_orientable"],
            planar=counts["planar"],
            linear=counts["linear"],
            composite=counts["composite"],
            unknown=counts["unknown"],
        ))

    # ------------------------------------------------------------------
    # Événements du dialogue
    # ------------------------------------------------------------------
    def _on_filter_changed(self, _index=0):
        self._recompute_model()

    def _on_rose_mode_changed(self, _index=0):
        self._recompute_rose()

    def _sample_for_visible_index(self, index):
        if index is None or index < 0 or index >= len(self._visible_samples):
            return None
        return self._visible_samples[index]

    def _selected_sample(self):
        sel = self._workspace_state.get_selected_interval() \
            if self._workspace_state is not None else None
        if sel is None:
            return None
        hole = getattr(sel, "hole_id", None)
        depth = getattr(sel, "from_m", None)
        if hole is None or depth is None:
            return None
        return (str(hole), round(float(depth), 6), str(getattr(sel, "domain", "") or ""))

    def _refresh_selected_highlight(self):
        selected = self._selected_sample()
        index = None
        if selected is not None:
            key = (selected[0], selected[1])
            if selected[2] in ("", "structure") and key in self._visible_index_by_key:
                index = self._visible_index_by_key[key]
        self._stereonet_widget.set_selected_index(index)
        self._refresh_selected_label(index)

    def _refresh_selected_label(self, index):
        """Affiche la mesure sélectionnée sous le résumé (consultable
        même quand la coupe/3D est masquée par le dialogue)."""
        sample = self._sample_for_visible_index(index)
        if sample is None:
            self.selection_label.clear()
            return
        self.selection_label.setText(self.tr(
            "Sélection : {hole} · {depth:g} m · {code}"
        ).format(
            hole=str(sample.hole_id or ""),
            depth=sample.depth,
            code=str(sample.code or ""),
        ))

    def _on_workspace_selected_interval(self, _value):
        self._refresh_selected_highlight()

    # ------------------------------------------------------------------
    # Clic : toggle point / vide = clear (Incrément C)
    # ------------------------------------------------------------------
    def _publish_selection(self, sample):
        if self._workspace_state is None:
            return
        selected = self._selected_sample()
        if selected is not None and selected[0] == str(sample.hole_id or "") \
                and abs(selected[1] - round(float(sample.depth), 6)) < 1e-6 \
                and selected[2] in ("", "structure"):
            self._workspace_state.clear_selection()
            return
        attributes = {"code": str(sample.code or ""),
                      "origin": "structure_analysis"}
        self._workspace_state.select_interval(
            hole_id=str(sample.hole_id or ""),
            from_m=float(sample.depth),
            to_m=float(sample.depth),
            domain="structure",
            source="structure_analysis",
            attributes=attributes,
        )

    def _on_point_clicked(self, index):
        sample = self._sample_for_visible_index(int(index))
        if sample is None:
            return
        self._publish_selection(sample)
        self._refresh_selected_highlight()

    def _on_empty_clicked(self):
        if self._workspace_state is None:
            return
        self._workspace_state.clear_selection()
        self._refresh_selected_highlight()

    # ------------------------------------------------------------------
    # Infobulle — consommée du modèle, jamais recalculée dans le widget
    # ------------------------------------------------------------------
    def _sample_colour(self, sample: StructureSample):
        callback = self._code_color
        if callable(callback):
            return QColor(str(callback(str(sample.code or "")) or "#808080"))
        return None

    def _point_tooltip(self, sample: StructureSample, orientation):
        lines = [
            self.tr("Forage : {hole} · {depth:g} m").format(
                hole=str(sample.hole_id or ""), depth=sample.depth),
            self.tr("Type : {type}").format(type=str(sample.code or "")),
        ]
        if sample.dip is not None and sample.dip_direction is not None:
            lines.append(self.tr(
                "Pendage (brut) : {dip}° / direction {dd}°").format(
                    dip=sample.dip, dd=sample.dip_direction))
        if sample.alpha is not None and sample.beta is not None:
            lines.append(self.tr(
                "Alpha (brut) : {a}° / bêta {b}°").format(
                    a=sample.alpha, b=sample.beta))
        if orientation is not None:
            lines.append(self.tr(
                "Pôle : {trend}° / {plunge}°").format(
                    trend=float(orientation.trend),
                    plunge=float(orientation.plunge)))
        if sample.confidence:
            lines.append(self.tr("Confiance : {value}").format(
                value=sample.confidence))
        if sample.comment:
            lines.append(str(sample.comment))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Fermeture — désabonnement du WorkspaceState (anti-dangling)
    # ------------------------------------------------------------------
    def reject(self):
        for unsubscribe in list(self._ws_unsubscribers):
            try:
                unsubscribe()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed(
                    "structure_analysis_dialog : désabonnement sélection", _exc)
        self._ws_unsubscribers.clear()
        super().reject()


BASE_DIALOG_STYLE = f"""
    QWidget {{
        background-color: {COLORS['bg_main']};
        font-family: 'Segoe UI', 'Sans Serif';
        font-size: 9pt;
        color: {COLORS['text_dark']};
    }}
    QLabel {{ border: none; background: transparent; }}
    QComboBox {{ background: {COLORS['bg_input']}; border: 1px solid {COLORS['border_dark']}; }}
"""
