"""
DrillMaster ORIG — dock principal (squelette v0.1).

Structure cible (ARCHITECTURE.md) : en-tête sobre, corps à étapes,
pied de statut. Toute option passe par les fabriques dés le premier
écran — jamais de style inline hors tokens.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget)

try:
    from qgis.gui import QgsDockWidget
    _BASE = QgsDockWidget
except Exception:
    from qgis.PyQt.QtWidgets import QDockWidget
    _BASE = QDockWidget

from .design_tokens import COLORS, TYPE, FONT_FAMILY


class OrigDock(_BASE):

    def __init__(self, iface, parent=None):
        super().__init__("DrillMaster ORIG", parent)
        self.iface = iface
        self.setObjectName("DrillMasterOrigDock")
        self.setStyleSheet(self._base_style())
        self._build()

    def _base_style(self) -> str:
        return (
            f"QWidget {{ background: {COLORS['bg_main']};"
            f" font-family: {FONT_FAMILY}; font-size: {TYPE['body']};"
            f" color: {COLORS['text_dark']}; }}"
            f"QToolTip {{ color: #FDFEFE;"
            f" background-color: {COLORS['surface_dark']};"
            f" border: 1px solid {COLORS['primary_lt']}; padding: 3px; }}")

    def _build(self):
        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(
            f"QFrame {{ background: {COLORS['bg_card']};"
            f" border-bottom: 1px solid {COLORS['border']}; }}")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(12, 8, 12, 8)
        title = QLabel(QCoreApplication.translate("OrigDock", "DrillMaster ORIG"))
        title.setStyleSheet(
            f"font-size: {TYPE['title']}; font-weight: bold;"
            f" color: {COLORS['primary']}; background: transparent;")
        subtitle = QLabel(QCoreApplication.translate(
            "OrigDock", "Cœur pur · courbure minimale · v0.1"))
        subtitle.setStyleSheet(
            f"font-size: {TYPE['small']}; color: {COLORS['text_light']};"
            f" background: transparent;")
        hlay.addWidget(title)
        hlay.addStretch(1)
        hlay.addWidget(subtitle)
        lay.addWidget(header)

        body = QLabel(QCoreApplication.translate(
            "OrigDock",
            "Fondations posées : modèle de données, conventions "
            "verrouillées, trajectoires en courbure minimale (8 tests). "
            "Les étapes d'import et de coupe arrivent par tranches."))
        body.setWordWrap(True)
        body.setContentsMargins(12, 12, 12, 12)
        body.setAlignment(Qt.AlignTop)
        lay.addWidget(body, 1)

        footer = QFrame()
        footer.setStyleSheet(
            f"QFrame {{ background: {COLORS['bg_card']};"
            f" border-top: 1px solid {COLORS['border']}; }}")
        flay = QHBoxLayout(footer)
        flay.setContentsMargins(12, 6, 12, 6)
        self.status_label = QLabel(QCoreApplication.translate(
            "OrigDock", "Prêt."))
        self.status_label.setStyleSheet(
            f"font-size: {TYPE['small']}; color: {COLORS['text_medium']};"
            f" background: transparent;")
        flay.addWidget(self.status_label)
        flay.addStretch(1)
        lay.addWidget(footer)

        self.setWidget(root)
