"""v2.9.262 — Chantier 2 E2 : piste 2D « Imagerie » de la coupe.

The image lane is a dedicated visual track.  Each ``CoreImageRecord`` is
one interval along the hole (a cutting box can be one row 0–15 or fifteen
rows 0–1 … 14–15 — the renderer never splits or guesses).

Rules implemented here (all decided for Chantier 2):

- **Continuous / interval band** : the record's ``from_m``..``to_m`` is
  mapped to the same perpendicular trapezoid as every other lane.
- **≈ 1024 px cache** : ``QImageReader`` decodes then scales with
  ``SmoothTransformation`` and the result is cached (``QPixmap``) keyed by
  resolved path + mtime, so the section redraw never re-reads
  full-resolution photographs.
- **Lazy load** : only records actually drawn load an image ; files that
  are missing or unreadable never block the section.
- **Missing file** : hatched band + explicit warning in the tooltip.
- **Material label** : ``core`` / ``rc`` / ``auger`` / ``pit`` / ``other``
  is an informative label, never a filter, never an error.
- **link / copy** : both storage modes resolve through the same order
  (as-is, project dir, ``data_import/``, ``assets/``) — the copy mode just
  makes the resolved file live inside ``assets/``.
"""

import math
import os
from collections import OrderedDict

from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import (
    QBrush, QColor, QFont, QImage, QImageReader, QPainter, QPainterPath,
    QPen, QPixmap, QPolygonF, QTransform)
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGraphicsPixmapItem, QGraphicsPolygonItem, QGraphicsRectItem,
    QGraphicsSimpleTextItem, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget)

from .styles_qt import (
    BUTTON_SECONDARY, COLORS, INPUT_STYLE, make_collapsible_help)
from ..core.diagnostics import log_swallowed
from ..core.data_model import CORE_IMAGE_MATERIALS
from ..core.image_paths import (
    base_candidates as _base_candidates,
    resolve_image_path)

# v2.9.262 — taille max. du cache. Augmentée à 1024 px au retour écran
# « c'est pas net / trop pixelisé » : la piste peut être étirée sur une
# grande hauteur à l'export HD ; 512 px laissait des carrés visibles.
IMAGERY_CACHE_TARGET_PX = 1024
IMAGERY_CACHE_MAX_ENTRIES = 120

# Informative material colours (legend + missing-hatch context only).
IMAGERY_MATERIAL_COLORS = {
    "core": "#8B6F52",
    "rc": "#5DA8D6",
    "auger": "#43886B",
    "pit": "#566573",
    "other": "#95A5A6",
}

_IMAGERY_MATERIAL_FR = {
    "core": "Carotte",
    "rc": "RC",
    "auger": "Auger",
    "pit": "Puits droit",
    "other": "Autre",
}

_MISSING_HATCH = "#E67E22"
_MISSING_PEN = "#A04000"


# ---------------------------------------------------------------------------
# Lazy resized cache
# ---------------------------------------------------------------------------
class ImageryPixmapCache:
    """Resized ``QPixmap`` cache, one entry per resolved image file.

    The cache is intentionally small (240 entries) and keyed by
    ``path -> (mtime_ns, pixmap)``.  A missing file is cached with a
    ``None`` pixmap and a negative mtime: the next redraw sees the new
    mtime as soon as the file appears, without reloading on every pan.
    """

    def __init__(self, target_px: int = IMAGERY_CACHE_TARGET_PX,
                 max_entries: int = IMAGERY_CACHE_MAX_ENTRIES):
        self.target_px = max(int(target_px or 0), 64)
        self.max_entries = max(int(max_entries), 16)
        self._cache: "OrderedDict[str, tuple[int, object]]" = OrderedDict()

    def clear(self) -> None:
        self._cache.clear()

    def get(self, path: str):
        """Return a cached ``QPixmap`` or ``None`` (missing/unreadable)."""
        try:
            stat = os.stat(str(path))
            mtime = int(stat.st_mtime_ns)
        except OSError:
            mtime = -1
        key = str(path)
        entry = self._cache.get(key)
        if entry is not None and entry[0] == mtime:
            self._cache.move_to_end(key)
            return entry[1]
        pixmap = self._load_resized(path) if mtime >= 0 else None
        self._cache[key] = (mtime, pixmap)
        self._cache.move_to_end(key)
        while len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)
        return pixmap

    def _load_resized(self, path: str):
        """Decode a photograph then cache it at a sharp reduced size.

        Retour écran « c'est pas net / trop pixelisé » : la réduction faite
        par ``QImageReader.setScaledSize`` passe parfois par un échantillonnage
        rapide (carrés visibles). On lit désormais le décodage complet puis on
        redimensionne SOIT via ``QImage.scaled(..., SmoothTransformation)`` :
        le cache garde une image nette ~1024 px (limite côté cache) et le
        rendu n'aligne plus des blocs.

        On conserve les lectures de repli (QImageReader pleine, QImage
        directe) pour ne pas re-bloquer sur un décodeur capricieux.
        """
        path_str = str(path)
        target = max(int(self.target_px), 128)

        def _scaled_pixmap(image) -> "QPixmap | None":
            try:
                if image is None or image.isNull():
                    return None
                w = image.width()
                h = image.height()
                scaled = image
                if (w > target or h > target):
                    if w >= h:
                        scaled = image.scaled(
                            target, max(1, round(h * target / w)),
                            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    else:
                        scaled = image.scaled(
                            max(1, round(w * target / h)), target,
                            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                if scaled.isNull():
                    return None
                pixmap = QPixmap.fromImage(scaled)
                return pixmap if not pixmap.isNull() else None
            except Exception as _exc:
                log_swallowed("section_imagery : réduction QImage", _exc)
                return None

        # 1) lecture par QImageReader (décodage complet, redimensionnement
        #    doux ensuite) — c'est le chemin nominal.
        try:
            reader = QImageReader(path_str)
            reader.setAutoTransform(True)
            pixmap = _scaled_pixmap(reader.read())
            if pixmap is not None:
                return pixmap
        except Exception as _exc:
            log_swallowed("section_imagery : lecture QImageReader", _exc)

        # 2) chargement Qt direct (couvre certains chemins que
        #    QImageReader rejette silencieusement).
        try:
            pixmap = _scaled_pixmap(QImage(path_str))
            if pixmap is not None:
                return pixmap
        except Exception as _exc:
            log_swallowed("section_imagery : QImage direct", _exc)

        # Dernier recours d'information : format détecté + erreur Qt.
        format_hint = ""
        error_hint = ""
        try:
            probe = QImageReader(path_str)
            format_hint = str(probe.format().data().decode(
                "ascii", "replace")) if probe.format() else ""
            error_hint = probe.errorString()
        except Exception as _probe_exc:
            # Diagnostique optionnel : si le probe échoue, on garde les
            # placeholders « ? » — le rendu ne dépend pas de ce bloc.
            log_swallowed("section_imagery : sondage format", _probe_exc)
        log_swallowed(
            "section_imagery : image illisible",
            RuntimeError(
                f"{path_str} | format={format_hint or '?'} | {error_hint or '?'}"))
        return None


def _canvas_cache(canvas) -> ImageryPixmapCache:
    cache = getattr(canvas, "_imagery_cache", None)
    if cache is None:
        cache = ImageryPixmapCache()
        canvas._imagery_cache = cache
    return cache


# ---------------------------------------------------------------------------
# Path resolution (link/copy shared order)
# ---------------------------------------------------------------------------
# La résolution vit dans core/image_paths.py (sans Qt, testable).


# ---------------------------------------------------------------------------
# Track spec / data detection
# ---------------------------------------------------------------------------
def has_data(dhs) -> bool:
    return any(getattr(dh, "imagery", None) for dh in (dhs or []))


def imagery_source_dir(widget) -> str:
    """Dossier du CSV « imagery » courant (résolution liens relatifs)."""
    try:
        step2 = getattr(getattr(widget, "main_dock", None), "step2", None)
        tab = getattr(step2, "tabs", {}).get("imagery") if step2 else None
        parse_result = getattr(tab, "parse_result", None)
        if parse_result is not None:
            return os.path.dirname(str(parse_result.file_path or ""))
    except Exception as _exc:
        log_swallowed("section_imagery : imagery_source_dir", _exc)
    return ""


def imagery_project_and_source(canvas):
    """Resolve project + CSV source dir through the canvas providers."""
    provider = getattr(canvas, "imagery_project_provider", None)
    project = provider() if callable(provider) else None
    source_provider = getattr(canvas, "imagery_source_dir_provider", None)
    source = (source_provider() if callable(source_provider)
              else getattr(canvas, "_imagery_source_dir", ""))
    return project, str(source or "")


def imagery_track_spec(widget, sr) -> dict:
    """Spec of the Imagery lane (auto-collapse when hidden/no image)."""
    return {
        "side": getattr(widget, "_imagery_side", "right"),
        "width": float(getattr(widget, "_imagery_width", 10.0)),
        "active": (bool(getattr(widget, "_show_imagery", True))
                   and any(getattr(ph, "imagery", None) for ph in sr.holes)),
    }


# ---------------------------------------------------------------------------
# Tooltip
# ---------------------------------------------------------------------------
def _material_text(canvas, material_label: str) -> str:
    key = str(material_label or "").casefold()
    if key in CORE_IMAGE_MATERIALS or key == "":
        if key == "":
            return canvas.tr("—")
        return canvas.tr(_IMAGERY_MATERIAL_FR.get(key, key))
    return canvas.tr(_IMAGERY_MATERIAL_FR["other"])


def imagery_tooltip(canvas, ph, record, resolved, missing: bool = False,
                    unreadable: bool = False) -> str:
    lines = [f"{ph.hole_id} · {record.span_text} m"]
    line = canvas.tr("Matériau : {}").format(
        _material_text(canvas, record.material_label))
    if missing:
        line += canvas.tr("  ⚠ image introuvable")
    elif unreadable:
        line += canvas.tr("  ⚠ image illisible")
    lines.append(line)
    path = resolved or str(record.image_path or "")
    if path:
        lines.append(canvas.tr("Fichier : {}").format(path))
    if record.orientation:
        lines.append(canvas.tr("Orientation : {}").format(record.orientation))
    if record.comment:
        lines.append(str(record.comment))
    if missing:
        lines.append(canvas.tr(
            "Bande hachurée : le fichier n'existe pas dans le dossier projet "
            "ni dans assets/."))
    elif unreadable:
        lines.append(canvas.tr(
            "Bande hachurée : le fichier existe mais n'a pas pu être lu "
            "(format non reconnu par Qt ou fichier corrompu)."))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def _affine_for_pixmap(poly, pixmap):
    """Map a pixmap onto the lane trapezoid by its four corners.

    The affine maps an image rectangle to a parallelogram exactly.  Most
    imagery intervals are straight enough for this; the painter clip path
    in :func:`_composite_band_pixmap` still guards against slight
    trapezoid overflow on curved traces.
    """
    if len(poly) < 4 or pixmap is None or pixmap.width() <= 0:
        return None, None
    ax, ay = poly[0].x(), poly[0].y()      # top inner
    bx, by = poly[1].x(), poly[1].y()      # top outer
    dx, dy = poly[3].x(), poly[3].y()      # bottom inner
    pw = max(float(pixmap.width()), 1.0)
    ph = max(float(pixmap.height()), 1.0)
    # Qt convention: x' = m11*x + m21*y + dx, y' = m12*x + m22*y + dy.
    transform = QTransform(
        (bx - ax) / pw, (by - ay) / pw,      # m11, m12 (along pixmap width)
        (dx - ax) / ph, (dy - ay) / ph,      # m21, m22 (along pixmap height)
        ax, ay,                              # dx, dy
    )
    return transform, QRectF(0.0, 0.0, pw, ph)


def _composite_band_pixmap(poly, pixmap):
    """Rasterise ``pixmap`` clipped to ``poly`` into a new pixmap.

    PyQt/QGIS ne garantit pas ``QGraphicsItem.setClipPath`` sur
    ``QGraphicsPixmapItem`` (retour écran QGIS 3.44 : ``AttributeError:
    'QGraphicsPixmapItem' object has no attribute 'setClipPath'``).  On
    compose donc l'image dans une ``QPixmap`` au gabarit du polygone :
    le clip est fait par ``QPainter``, et le résultat se pose sans
    transform ni clip path sur la scène.

    Returns ``(composited_pixmap, scene_rect)`` or ``(None, None)``.
    """
    if poly is None or len(poly) < 3 or pixmap is None or pixmap.width() <= 0:
        return None, None
    scene_rect = poly.boundingRect()
    if scene_rect.width() <= 0 or scene_rect.height() <= 0:
        return None, None
    width = max(1, int(round(scene_rect.width())))
    height = max(1, int(round(scene_rect.height())))
    out = QPixmap(width, height)
    if out.isNull():
        return None, None
    out.fill(Qt.GlobalColor.transparent)
    try:
        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(-scene_rect.left(), -scene_rect.top())
        local = QPolygonF([
            QPointF(p.x() - scene_rect.left(), p.y() - scene_rect.top())
            for p in poly])
        transform, _image_rect = _affine_for_pixmap(local, pixmap)
        if transform is not None:
            painter.setTransform(transform)
            # Clip dans l'espace LOGIQUE de la pixmap : on reprend le
            # polygone local, inversé par la même transformation.
            inverse, invertible = transform.inverted()
            if invertible:
                clip = QPainterPath()
                inv_local = QPolygonF([
                    inverse.map(QPointF(
                        p.x(), p.y())) for p in local])
                clip.addPolygon(inv_local)
                clip.closeSubpath()
                painter.setClipPath(clip)
            # La transformation place le rectangle (0,0,pw,ph) sur la bande.
            painter.drawPixmap(0, 0, pixmap)
        painter.end()
    except Exception as _exc:
        log_swallowed("section_imagery : composition bande", _exc)
        return None, None
    return out, scene_rect


def _draw_hatched_missing(canvas, items, ph, record, res_path, poly,
                          unreadable: bool = False):
    colour = QColor(_MISSING_HATCH)
    alpha = max(40, min(140, int(float(getattr(
        canvas, "_imagery_opacity", 100)) * 1.1)))
    colour.setAlpha(alpha)
    polygon = QGraphicsPolygonItem(poly)
    polygon.setBrush(QBrush(colour, Qt.BrushStyle.BDiagPattern))
    polygon.setPen(QPen(QColor(_MISSING_PEN), 0.4))
    polygon.setZValue(4.0)
    polygon.setToolTip(imagery_tooltip(
        canvas, ph, record, res_path,
        missing=not bool(res_path), unreadable=unreadable))
    polygon.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
    canvas.scene.addItem(polygon)
    items.append(polygon)


# v2.9.262 — badge-lettre matériau : la photo porte déjà l'information
# visuelle, une bande colorée à côté grignoterait de l'espace pour une
# info redondante. Une lettre en badge discret dans le coin de la photo
# est plus lisible et ne coûte aucune largeur supplémentaire.
_BADGE_LETTERS = {
    "core": "C",
    "rc": "R",
    "auger": "A",
    "pit": "P",
    "other": "O",
}


def _material_badge_letter(material_label: str) -> str:
    return str(_BADGE_LETTERS.get(
        str(material_label or "").casefold(), ""))


def _draw_material_badge(canvas, items, ph, record, poly, tooltip: str = ""):
    letter = _material_badge_letter(record.material_label)
    if not letter or poly is None or len(poly) < 3:
        return
    try:
        rect = poly.boundingRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        size = min(10.0, max(6.0, min(rect.width(), rect.height()) * 0.22))
        margin = max(1.5, size * 0.18)
        # Coin haut de la bande : on prend le point le plus haut (le
        # moins "y") pour rester dans la photo quelle que soit l'oblique.
        top = min(poly, key=lambda p: (p.y(), p.x()))
        bx = top.x() - size * 0.5
        by = top.y() - size * 0.5
        if bx < rect.left():
            bx = rect.left() + margin
        if by < rect.top():
            by = rect.top() + margin
        if bx + size > rect.right() - margin:
            bx = max(rect.left() + margin, rect.right() - size - margin)
        if by + size > rect.bottom() - margin:
            by = max(rect.top() + margin, rect.bottom() - size - margin)
        badge_rect = QRectF(bx, by, size, size)
        background = QGraphicsRectItem(badge_rect)
        bg = QColor("#2C3E50")
        bg.setAlpha(215)
        background.setBrush(QBrush(bg))
        background.setPen(QPen(QColor("#FFFFFF"), 0.4))
        background.setZValue(5.0)
        background.setToolTip(tooltip)
        background.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        canvas.scene.addItem(background)
        items.append(background)

        text_item = QGraphicsSimpleTextItem(letter)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(max(6, int(size * 0.72)))
        text_item.setFont(font)
        text_item.setBrush(QBrush(QColor("#FFFFFF")))
        text_item.setZValue(5.1)
        text_rect = text_item.boundingRect()
        text_item.setPos(
            bx + (size - text_rect.width()) / 2.0,
            by + (size - text_rect.height()) / 2.0)
        text_item.setToolTip(tooltip)
        text_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        canvas.scene.addItem(text_item)
        items.append(text_item)
    except Exception as _exc:
        log_swallowed("section_imagery : badge matériau", _exc)


def _draw_image_item(canvas, items, ph, record, res_path, pixmap, poly):
    # v2.9.262 — le clip n'est PAS posé sur l'item (QGraphicsPixmapItem
    # n'a pas setClipPath sous QGIS 3.44). On conserve la transform affine
    # de l'item, qui est ce qui cale la photo sur la trajectoire : c'est
    # exactement le même mécanisme que les bandes litho. Le léger débord
    # sur une trace très courbe (trapèze non parfait) est accepté ; le
    # cadre fin redessine la limite exacte de la bande.
    transform, _rect = _affine_for_pixmap(poly, pixmap)
    if transform is None:
        return
    tooltip = imagery_tooltip(canvas, ph, record, res_path, False)
    item = QGraphicsPixmapItem(pixmap)
    item.setTransform(transform)
    # v2.9.262 — export HD : interpolation douce quand la scène agrandit
    # la bande (sinon blocs visibles).
    item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
    item.setZValue(4.0)
    item.setToolTip(tooltip)
    item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
    try:
        item.setData(0, (
            "imagery", ph.hole_id, float(record.from_m),
            float(record.to_m), res_path))
    except Exception as _exc:
        log_swallowed("section_imagery : identification item", _exc)
    canvas.scene.addItem(item)
    items.append(item)

    # v2.9.262 (retour écran) — matériau en badge-lettre incrusté dans la
    # photo (pas de bande colorée externe) : zéro largeur supplémentaire,
    # lisible à petite échelle, et directement attaché à la bonne bande.
    _draw_material_badge(canvas, items, ph, record, poly, tooltip)

    # Thin rim keeps the image interval readable against the section.
    rim = QGraphicsPolygonItem(poly)
    # v2.9.262 — retour écran QGIS 3.44 : setBrush attend un QBrush, pas
    # l'énumération brute Qt.NoBrush (TypeError 'BrushStyle').
    rim.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    pen = QPen(QColor("#34495E"), 0.35)
    pen.setCosmetic(True)
    rim.setPen(pen)
    rim.setZValue(4.1)
    rim.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
    canvas.scene.addItem(rim)
    items.append(rim)


def draw_imagery(canvas, sr, project=None, source_dir: str = ""):
    """Draw the Imagery lane for every hole in the section result."""
    lane = None
    plan = getattr(canvas, "_track_plan", None)
    if plan is not None:
        lane = plan.by_key.get("imagery")
    if lane is None:
        return
    cache = _canvas_cache(canvas)
    for ph in sr.holes:
        records = sorted(
            getattr(ph, "imagery", None) or [],
            key=lambda record: (float(record.from_m), float(record.to_m)))
        items = canvas._hole_items.setdefault(ph.hole_id, [])
        for record in records:
            f = min(float(record.from_m), float(record.to_m))
            t = max(float(record.from_m), float(record.to_m))
            if t - f < 1e-6:
                continue
            poly = canvas._band_poly(ph, f, t, lane.inner_edge, lane.outer_edge)
            if poly is None:
                continue
            res_path = resolve_image_path(project, record.image_path, source_dir)
            pixmap = cache.get(res_path) if res_path else None
            if pixmap is not None:
                _draw_image_item(
                    canvas, items, ph, record, res_path, pixmap, poly)
            else:
                # res_path vide = fichier absent ; res_path présent mais
                # pixmap None = fichier sur disque, illisible par Qt.
                _draw_hatched_missing(
                    canvas, items, ph, record, res_path, poly,
                    unreadable=bool(res_path))


# ---------------------------------------------------------------------------
# Panel page
# ---------------------------------------------------------------------------
def build_imagery_group(widget):
    """v2.9.262 — page « Imagerie » du groupe Pistes."""
    frame = widget._group_frame()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(6, 6, 6, 8)
    layout.setSpacing(6)

    widget.chk_imagery = QCheckBox(widget.tr("Afficher l'imagerie"))
    widget.chk_imagery.setToolTip(widget.tr(
        "Bandes photo/scan le long du forage · grisée sans fichier"))
    widget.chk_imagery.setChecked(True)
    widget.chk_imagery.stateChanged.connect(widget._on_section_style_change)
    layout.addWidget(widget.chk_imagery)

    form = QFormLayout()
    widget.imagery_side = QComboBox()
    widget.imagery_side.addItem(widget.tr("Gauche"), "left")
    widget.imagery_side.addItem(widget.tr("Droite"), "right")
    widget.imagery_side.setCurrentIndex(1)
    widget.imagery_side.setStyleSheet(INPUT_STYLE)
    widget.imagery_side.setToolTip(widget.tr("Côté de la piste Imagerie"))
    widget.imagery_side.currentIndexChanged.connect(
        widget._on_section_style_change)
    form.addRow(widget.tr("Côté"), widget.imagery_side)

    widget.imagery_width = QDoubleSpinBox()
    widget.imagery_width.setRange(6, 120)
    widget.imagery_width.setValue(10.0)
    widget.imagery_width.setSuffix(" px")
    widget.imagery_width.setStyleSheet(INPUT_STYLE)
    widget.imagery_width.setToolTip(widget.tr(
        "Largeur de la bande photo (piste fine, collée à la trajectoire ; "
        "les photos sont réduites à ≈ 1024 px au premier affichage puis "
        "mises en cache)"))
    widget.imagery_width.valueChanged.connect(widget._on_section_style_change)
    form.addRow(widget.tr("Largeur de voie"), widget.imagery_width)

    widget.imagery_opacity = QSpinBox()
    widget.imagery_opacity.setRange(0, 100)
    widget.imagery_opacity.setValue(100)
    widget.imagery_opacity.setSuffix(" %")
    widget.imagery_opacity.setStyleSheet(INPUT_STYLE)
    widget.imagery_opacity.setToolTip(widget.tr(
        "Opacité des bandes d'image (les hachures d'image absente restent "
        "visibles)"))
    widget.imagery_opacity.valueChanged.connect(widget._on_section_style_change)
    form.addRow(widget.tr("Opacité"), widget.imagery_opacity)
    layout.addLayout(form)

    layout.addWidget(make_collapsible_help(widget.tr(
        "Une bande par intervalle photo/scan, à sa profondeur exacte, "
        "côté gauche ou droit, dans une piste fine collée au forage. "
        "Les images sont réduites à ≈ 1024 px puis mises en cache : "
        "la coupe reste fluide et ne relit jamais une "
        "photo pleine résolution au déplacement. Si un fichier manque ou "
        "ne se lit pas, la bande passe en hachures avec l'avertissement "
        "dans l'infobulle — jamais d'erreur bloquante. Le matériau "
        "(carotte/RC/auger/puits/autre) est une étiquette, pas un filtre.")))
    open_btn = QPushButton(widget.tr("Ouvrir le dossier assets…"))
    open_btn.setStyleSheet(BUTTON_SECONDARY)
    open_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    open_btn.setToolTip(widget.tr(
        "Dossier projets/assets/ : images copiées en mode « copy »"))
    open_btn.clicked.connect(
        lambda _checked=False: open_imagery_assets(widget))
    layout.addWidget(open_btn)
    layout.addStretch(1)
    return frame


def open_imagery_assets(widget):
    """v2.9.262 — ouvre le dossier ``assets/`` du projet (mode copy)."""
    project = None
    try:
        project = widget._project() if hasattr(widget, "_project") else None
    except Exception as _exc:
        log_swallowed("section_imagery : open_imagery_assets", _exc)
    if project is None and getattr(widget, "main_dock", None):
        project = getattr(widget.main_dock, "project", None)
    paths = getattr(project, "paths", None) if project is not None else None
    assets = getattr(paths, "assets_dir", None) if paths is not None else None
    if not assets:
        return
    os.makedirs(assets, exist_ok=True)
    try:
        from qgis.PyQt.QtCore import QUrl
        from qgis.PyQt.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(assets))
    except Exception as _exc:
        log_swallowed("section_imagery : ouverture dossier assets", _exc)


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
def _legend_label(text: str) -> "QLabel":
    label = QLabel(text)
    label.setWordWrap(True)
    font = label.font()
    try:
        font.setCapitalization(QFont.Capitalization.SmallCaps)
    except Exception as _exc:
        log_swallowed("section_imagery : _legend_label", _exc)
    font.setPointSize(max(8, font.pointSize()))
    label.setFont(font)
    label.setStyleSheet(
        (label.styleSheet() or "") +
        "border:none; background:transparent; padding:0;")
    return label


def create_legend_widgets(widget, layout):
    """Build (once) the Imagery legend title and grid."""
    title = QLabel(widget.tr("Imagerie — matériaux"))
    title.setStyleSheet(
        f"font-weight:bold; color:{COLORS['primary']}; margin-top:6px;")
    widget.imagery_legend_title = title
    layout.addWidget(title)
    holder = QWidget()
    grid = QGridLayout(holder)
    grid.setContentsMargins(0, 2, 0, 0)
    grid.setHorizontalSpacing(8)
    grid.setVerticalSpacing(5)
    widget.imagery_legend_widget = holder
    widget.imagery_legend_layout = grid
    layout.addWidget(holder)
    return holder


def fill_imagery_legend(widget, grid):
    """Material legend entries actually present in the project."""
    widget._clear_layout(grid)
    materials = set()
    for dh in (getattr(widget, "_drillholes", None) or []):
        for record in (getattr(dh, "imagery", None) or []):
            materials.add(record.material_label)
    materials.discard("")
    if not materials:
        return
    order = [m for m in CORE_IMAGE_MATERIALS if m in materials]
    for index, material in enumerate(order):
        entry = QWidget()
        row_layout = QHBoxLayout(entry)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        swatch = QLabel()
        swatch.setFixedSize(16, 16)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor("#2C3E50")
        bg.setAlpha(215)
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(QColor("#FFFFFF"), 0.5))
        painter.drawRect(1, 1, 14, 14)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(9)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        letter = _material_badge_letter(material)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()
        swatch.setPixmap(pixmap)
        swatch.setToolTip(f"{material} ({letter})")
        label = _legend_label(widget.tr(
            _IMAGERY_MATERIAL_FR.get(material, material)))
        label.setToolTip(f"{material} ({letter})")
        row_layout.addWidget(swatch)
        row_layout.addWidget(label, 1)
        grid.addWidget(entry, index // 2, index % 2)


def refresh_imagery_legend(widget) -> bool:
    """Dock delegation: visibility + rows in one call (BUD-160)."""
    has_imagery = widget._project_has_domain_data("imagery")
    show = update_legend_visibility(widget, has_imagery)
    if show:
        fill_imagery_legend(widget, widget.imagery_legend_layout)
    return show


def update_legend_visibility(widget, has_imagery: bool) -> bool:
    show = bool(
        getattr(widget.canvas, "_show_imagery", False) and has_imagery)
    for attr in ("imagery_legend_title", "imagery_legend_widget"):
        obj = getattr(widget, attr, None)
        if obj is not None:
            obj.setVisible(show)
    return show


# ---------------------------------------------------------------------------
# Style read/apply
# ---------------------------------------------------------------------------
def read_imagery_style(widget) -> dict:
    return {
        "show_imagery": getattr(widget, "chk_imagery", None) is not None
        and widget.chk_imagery.isChecked(),
        "imagery_width": getattr(widget, "imagery_width", None).value()
        if getattr(widget, "imagery_width", None) else 10.0,
        "imagery_side": (
            (widget.imagery_side.currentData() or "right")
            if getattr(widget, "imagery_side", None) else "right"),
        "imagery_opacity": getattr(widget, "imagery_opacity", None).value()
        if getattr(widget, "imagery_opacity", None) else 100,
    }


def apply_imagery_style_to_widget(widget, style):
    if getattr(widget, "chk_imagery", None) is None:
        return
    widget.chk_imagery.setChecked(style.get("show_imagery", True))
    widget._set_combo_data(widget.imagery_side,
                           style.get("imagery_side", "right"))
    widget.imagery_width.setValue(float(style.get("imagery_width", 10.0)))
    widget.imagery_opacity.setValue(int(style.get("imagery_opacity", 100)))
