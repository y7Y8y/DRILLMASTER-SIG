"""
DrillMaster — Accordéon normalisé (Lot DA-1, v2.9.396)
=======================================================
Extrait de ``ui/section_dock.py`` (où il vivait depuis v2.7) : le
``CollapsibleGroup`` devient un composant partagé. Comportement
inchangé (compatibilité v2.7.12.13/14 : absorption d'espace,
updateGeometry au repli) ; seuls les fonds d'en-tête passent aux
tokens — les teintes bleutées #EAF0F4 / #F7F9F9 entraient en
concurrence avec les données (principe data-ink, docs/DESIGN.md).
"""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from ..design_tokens import COLORS, TYPE


class CollapsibleGroup(QWidget):
    """Accordion with visually distinct main (0) and nested (1) levels."""

    def __init__(self, title, content, expanded=False, parent=None, level=0):
        super().__init__(parent)
        self.level = level
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14 if level else 0, 2 if level else 0, 0, 2 if level else 0)
        layout.setSpacing(0)
        self.header = QToolButton()
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(expanded)
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        # v2.7.12.14 — REVUE ÉCRAN (onglet Coupe 2D) : la politique
        # horizontale de QToolButton est Fixed (taille sizeHint) — les
        # titres « flottent » à moitié dans le panneau. En Expanding, le
        # titre fait toute la largeur : un vrai accordéon.
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # v2.9.396 — DA-1 : fonds sur tokens (survol discret pour le
        # niveau principal, fond principal pour les niveaux imbriqués) ;
        # hiérarchie par la VALEUR, jamais par une teinte.
        if level == 0:
            self.header.setStyleSheet(f"""
                QToolButton {{
                    background: {COLORS['hover_subtle']}; color: {COLORS['primary']};
                    border: none; border-left: 3px solid {COLORS['accent']};
                    border-bottom: 1px solid {COLORS['border_dark']};
                    padding: 8px 7px; font-size: {TYPE['body']}; font-weight: bold;
                    text-align: left;
                }}
            """)
        else:
            self.header.setStyleSheet(f"""
                QToolButton {{
                    background: {COLORS['bg_main']}; color: {COLORS['text_medium']};
                    border: 1px solid {COLORS['border']};
                    padding: 5px 6px; font-size: {TYPE['small']}; font-weight: normal;
                    text-align: left;
                }}
            """)
        self.content = content
        self.content.setVisible(expanded)
        self.header.toggled.connect(self._toggle)
        layout.addWidget(self.header)
        # v2.7.12.13 — le contenu absorbe l'espace restant : à l'étape 4
        # (sans défilement) la table d'historique remplit l'étape ; dans
        # les panneaux (sous QScrollArea) aucun effet, la hauteur reste
        # la sizeHint.
        layout.addWidget(self.content, 1)

    def _toggle(self, expanded):
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.content.setVisible(expanded)
        # v2.7.12.14 — changer la visibilité change la sizeHint du
        # groupe — sans updateGeometry(), Qt ne re-propage PAS la
        # nouvelle taille : espaces fantômes entre titres repliés.
        self.updateGeometry()
