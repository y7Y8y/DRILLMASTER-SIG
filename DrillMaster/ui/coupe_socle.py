"""DrillMaster — le socle de la coupe 2D : couleurs, style, motifs, items.

Extrait de ``ui/section_dock.py`` (chantier 6, tranche 1). Rien n'a changé
de comportement : les mêmes constantes, les mêmes fonctions, les mêmes
classes, déplacées ici pour que le monolithe cesse d'être le seul endroit
où l'on peut lire une couleur de sélection ou une encre de motif.

Ce que ce module possède :

- les **couleurs d'interaction** de la coupe (sélection, clic-légende) et
  leurs largeurs de trait — une seule source pour la scène et l'export ;
- les **motifs lithologiques** (le motif Qt par nom) et la règle d'encre
  qui garantit qu'une coupe et sa légende peignent la même chose ;
- les **petites capitales** de l'export et des légendes ;
- les **items graphiques** qui portent ces règles (motif sans
  anticrénelage, trait clipé au polygone, remplissage clipé).

``section_dock`` ré-exporte tout : aucun appelant n'a eu à changer.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import (
    QBrush, QColor, QFont, QPainter, QPen, QPolygonF,
)
from qgis.PyQt.QtWidgets import QGraphicsPolygonItem, QLabel

from qgis.PyQt.QtCore import QCoreApplication


SELECTION_HIGHLIGHT_COLOR = "#00E5FF"  # cyan vif = règle 1 (slot)
# v2.9.122 — clic-légende ≠ couleur de règle (cyan/magenta/ambre).
LEGEND_CLICK_COLOR = "#34495E"  # anthracite / ardoise (interaction UI)

# v2.9.114 — largeurs scène (pen non-cosmetic) : dock lisible, export HD fin
SELECTION_OUTLINE_PEN_DOCK = 1.85
SELECTION_OUTLINE_PEN_EXPORT = 0.9


def _selection_highlight_pen(width: float = 2.0,
                             color: str = None) -> "QPen":
    """Pinceau pointillé de sélection.

    v2.9.112 — **non-cosmetic** : largeur en unités scène.
    v2.9.116 — ``color`` optionnelle (multi-règles) ; défaut =
    SELECTION_HIGHLIGHT_COLOR (légende HL reste cyan unique).
    """
    hex_c = str(color or SELECTION_HIGHLIGHT_COLOR).strip() or SELECTION_HIGHLIGHT_COLOR
    if not hex_c.startswith("#"):
        hex_c = "#" + hex_c
    pen = QPen(QColor(hex_c), float(width), Qt.DashLine)
    pen.setCosmetic(False)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen

def _selection_chrome_stylesheet() -> str:
    """Style row légende sélectionnée — bordure = LEGEND_CLICK_COLOR."""
    base = QColor(LEGEND_CLICK_COLOR)
    # fond clair dérivé (mélange blanc) — pas une 2e couleur magique
    fill = QColor(
        (base.red() + 255 * 2) // 3,
        (base.green() + 255 * 2) // 3,
        (base.blue() + 255 * 2) // 3,
    )
    return (
        f"QWidget {{ background: {fill.name()}; "
        f"border: 1px dashed {LEGEND_CLICK_COLOR}; "
        f"border-radius: 3px; }}"
    )

# v2.7.5 — one unmistakable Qt style per offered key (see core/reference
# PATTERN_KEYS).  Existing key→style assignments are kept for saved
# projects; "dots" is now genuinely SPARSE points and legacy "dense"
# reads as the same sparse look (they were indiscernible by design).
_LITHO_BRUSH_PATTERNS = {
    "": Qt.SolidPattern,
    "diagonal": Qt.FDiagPattern,
    "backward_diagonal": Qt.BDiagPattern,
    "cross": Qt.CrossPattern,
    "diagonal_cross": Qt.DiagCrossPattern,
    "horizontal": Qt.HorPattern,
    "vertical": Qt.VerPattern,
    "dots": Qt.Dense1Pattern,
    "dense": Qt.Dense1Pattern,  # legacy alias, reads as sparse dots
# v2.7.8.2 — trois densités de pointillés discernables sur 8 px
    "dots_moyen": Qt.Dense3Pattern,
    "dots_fin": Qt.Dense5Pattern,
    "dots_dense": Qt.Dense7Pattern,
}


# v2.7.10.27/32 — les motifs à LIGNES seuls reçoivent une encre
# contrastée ; les motifs DENSES (Qt.Dense* = remplissage) gardent la
# couleur de base, sinon la bande entière vire au gris.
_LINE_BRUSH_STYLES = (Qt.FDiagPattern, Qt.BDiagPattern, Qt.CrossPattern,
                      Qt.DiagCrossPattern, Qt.HorPattern, Qt.VerPattern)


def _pattern_ink_colour(base_colour: QColor, brush_style=None) -> QColor:
    """v2.9.33/87 — ENCRE unique coupe=légende.

    Lignes : blanc sur foncé, ardoise sur clair.
    Dense* : couleur de base (remplissage Qt, pas encre grise).
    """
    if brush_style in _LINE_BRUSH_STYLES:
        return (QColor("#FFFFFF") if base_colour.lightness() < 130
                else QColor("#4A4A4A"))
    return QColor(base_colour)


def _export_smallcaps_font(point_size: int = 8, bold: bool = False) -> "QFont":
    """Police export en petites capitales (même intention que le panneau)."""
    f = QFont("Segoe UI", max(6, int(point_size)))
    f.setBold(bool(bold))
    try:
        f.setCapitalization(QFont.SmallCaps)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : _export_smallcaps_font", _exc)
        # SmallCaps indisponible — casse logicielle plus bas
        pass
    return f


def _export_sc_text(text) -> str:
    """Texte pour petite-capitale : Qt SmallCaps + filet upper poli."""
    s = str(text or "")
    # SmallCaps Qt affiche les minuscules en petites caps ; on garde
    # le libellé tel quel si possible, sinon upper léger en secours.
    return s


def _legend_label(text: str) -> "QLabel":
    """v2.9.22 — libellé de légende en petites capitales (lisibilité codes)."""
    label = QLabel(QCoreApplication.translate(
        "SectionWidget", str(text or "")))
    label.setWordWrap(True)
    font = label.font()
    try:
        font.setCapitalization(QFont.SmallCaps)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Légende : _legend_label", _exc)
        # SmallCaps indisponible sur certains backends Qt — CSS en secours.
        pass
    font.setPointSize(max(8, font.pointSize()))
    label.setFont(font)
    # filet CSS en secours (thèmes Qt qui ignorent SmallCaps)
    label.setStyleSheet(
        (label.styleSheet() or "")
        + "QLabel { font-variant: small-caps; letter-spacing: 0.3px; "
        "background: transparent; }")
    return label


class _PatternPolygonItem(QGraphicsPolygonItem):
    """v2.9.28 — polygone hachuré SANS antialiasing.

    Les motifs Qt (FDiag, Dense…) sont des bitmaps 1-bit : l'AA du
    QGraphicsView les floute en « gratté pixelisé ».  On coupe l'AA
    uniquement pour cet item ; le reste de la scène garde l'AA.
    """

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        super().paint(painter, option, widget)
        painter.restore()


class _ClippedStrokeItem(QGraphicsPolygonItem):
    """v2.9.29 — traits de motif clipés au polygone, AA off, ≥2 traits."""

    def __init__(self, poly, strokes_path, pen, parent=None):
        super().__init__(poly, parent)
        self._strokes = strokes_path
        self._pen = pen
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(Qt.NoBrush))

    def paint(self, painter, option, widget=None):
        # v2.9.30 — NE PAS passer un QPolygon à setClipRegion (TypeError
        # sous PyQt6 / QGIS 3.44 : attend un QRegion).  setClipPath avec
        # QPainterPath est le chemin portable et précis.
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        try:
            from qgis.PyQt.QtGui import QPainterPath, QRegion
            clip = QPainterPath()
            clip.addPolygon(self.polygon())
            painter.setClipPath(clip)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : paint", _exc)
            # repli : QRegion construit depuis le polygone (pas QPolygon nu)
            try:
                from qgis.PyQt.QtGui import QRegion
                painter.setClipRegion(QRegion(self.polygon().toPolygon()))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("section_dock : paint", _exc)
                # pas de clip — traits un peu hors bande, mieux que crash
                pass
        painter.setPen(self._pen)
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawPath(self._strokes)
        painter.restore()


class _ClippedFillItem(QGraphicsPolygonItem):
    """v2.9.80 — points / fills de motif clipés au polygone (pattern_engine)."""

    def __init__(self, poly, fill_path, ink_colour, parent=None):
        super().__init__(poly, parent)
        self._fill = fill_path
        self._ink = QColor(ink_colour)
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(Qt.NoBrush))

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        try:
            from qgis.PyQt.QtGui import QPainterPath
            clip = QPainterPath()
            clip.addPolygon(self.polygon())
            painter.setClipPath(clip)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : paint", _exc)
            # pas de clip — points un peu hors bande, mieux que crash
            pass
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(self._ink))
        painter.drawPath(self._fill)
        painter.restore()



class _StyledFillItem(QGraphicsPolygonItem):
    """DEPRECATED (audit 2.9.87) — non utilisé sur le chemin actif.

    Expérience v2.9.84 paint_style.  Rendu courant = _add_patterned_poly
    (brush Qt 2.9.33).  Ne pas réactiver sans décision produit.
    Conservé pour éviter de casser un import / test caché.
    """

    def __init__(self, poly, style_def, border_pen, axis_dx=0.0, axis_dy=1.0,
                 parent=None):
        super().__init__(poly, parent)
        self._style_def = style_def
        self._axis_dx = float(axis_dx)
        self._axis_dy = float(axis_dy)
        self.setPen(border_pen if border_pen is not None else QPen(Qt.NoPen))
        self.setBrush(QBrush(Qt.NoBrush))

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        try:
            from ..core.pattern_paint import paint_style
            poly = self.polygon()
            pts = [(float(poly.at(i).x()), float(poly.at(i).y()))
                   for i in range(poly.size())]
            paint_style(
                painter, self._style_def,
                polygon_points=pts,
                axis_dx=self._axis_dx,
                axis_dy=self._axis_dy,
                draw_underlay=True,
                draw_border=False,
            )
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("section_dock : paint", _exc)
            c = QColor(getattr(self._style_def, "fill_color", None) or "#CCC")
            painter.setPen(QPen(Qt.NoPen))
            painter.setBrush(QBrush(c))
            painter.drawPolygon(self.polygon())
        if self.pen().style() != Qt.NoPen:
            painter.setPen(self.pen())
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawPolygon(self.polygon())
        painter.restore()
