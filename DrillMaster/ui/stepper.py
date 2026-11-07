"""
DrillMaster — Visual Stepper Widget
====================================
Sober horizontal stepper with 4 steps:
1. Projet | 2. Données | 3. Géométrie 3D | 4. Coupes
Minimalist design: thin line, numbered circles, label below.
v2.9.100 — stepper plus compact (cercles 26 px, hauteur 46).
"""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout
from qgis.PyQt.QtGui import QColor, QFont, QPainter, QPen, QBrush


class StepIndicator(QWidget):
    """A single numbered circle for the stepper."""

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self._index = index
        self._state = "idle"
        self.setFixedSize(26, 26)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        if self._state == "current":
            fill, text_c, ring = QColor("#1C2833"), QColor("#FFFFFF"), QColor("#2A3C4D")
        elif self._state == "done":
            fill, text_c, ring = QColor("#27AE60"), QColor("#FFFFFF"), QColor("#1E8449")
        else:
            fill, text_c, ring = QColor("#EBEDEF"), QColor("#85929E"), QColor("#D5DBDB")

        rect = self.rect().adjusted(3, 3, -3, -3)
        p.setBrush(QBrush(fill))
        p.setPen(QPen(ring, 1.5))
        p.drawEllipse(rect)

        p.setPen(QPen(text_c))
        f = QFont("Segoe UI", 8)
        f.setBold(True)
        p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, str(self._index + 1))


class StepperWidget(QWidget):
    """Row of 4 step indicators with connecting lines and labels."""

    # v2.9.228 — Lot 1b : labels traduisibles (contexte StepperWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self._indicators: list[StepIndicator] = []
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(0)

        from qgis.PyQt.QtWidgets import QVBoxLayout, QLabel

        for i in range(4):
            col = QVBoxLayout()
            col.setSpacing(2)
            col.setAlignment(Qt.AlignCenter)

            ind = StepIndicator(i)
            self._indicators.append(ind)
            col.addWidget(ind, 0, Qt.AlignCenter)

            lbl = QLabel([
                self.tr("Projet"), self.tr("Données"),
                self.tr("Géométrie 3D"), self.tr("Coupes"),
            ][i])
            lbl.setStyleSheet("font-size: 7.5pt; color: #566573; background: transparent;")
            lbl.setAlignment(Qt.AlignCenter)
            # v2.9.18 — bulle courte par étape (1–4)
            # v2.9.228 — Lot 1b : bulles traduisibles
            tips = (
                self.tr("1 · Nom, dossier, SCR, unités"),
                self.tr("2 · Données : import CSV, vérification & QC"),
                self.tr("3 · Géométrie 3D (calcul trajectoires & "
                        "contrôles)"),
                self.tr("4 · Tracer / générer coupes"),
            )
            lbl.setToolTip(tips[i])
            ind.setToolTip(tips[i])
            col.addWidget(lbl, 0, Qt.AlignCenter)

            layout.addLayout(col)

            if i < 3:
                from qgis.PyQt.QtWidgets import QFrame
                line = QFrame()
                line.setFixedHeight(2)
                line.setMinimumWidth(20)
                line.setStyleSheet("background-color: #D5DBDB; margin-top: 10px;")
                layout.addWidget(line, 1)

        self.set_step(0)

    def set_step(self, step: int):
        for i, ind in enumerate(self._indicators):
            if i < step:
                ind.set_state("done")
            elif i == step:
                ind.set_state("current")
            else:
                ind.set_state("idle")
