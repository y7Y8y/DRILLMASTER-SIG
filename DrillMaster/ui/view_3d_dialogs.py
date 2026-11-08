"""DrillMaster — Dialogues de la Vue 3D (volet 1, tranche 4, v2.9.149).

Fenêtres modales de la vue 3D, extraites de ``ui/view_3d.py`` (SPEC) :
le choix des éléments de teneurs (1 à 3, avec miroir « Comme la coupe
2D »).  Widgets volontairement basiques (QDialog + QListWidget) — le
combo à cases de la v2.9.143 ne se cochait pas de façon fiable dans
QGIS.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QLabel, QListWidget,
    QListWidgetItem, QVBoxLayout,
)


class _AssayElementDialog(QDialog):
    """v2.9.146 — choix des éléments teneurs affichés en 3D (1 à 3).

    Remplace le combo à cases de la v2.9.143 : dans QGIS, les cases
    d'un popup de combo éditable ne se cochent PAS de façon fiable
    (style de l'application, fermeture du popup, texte de la ligne
    écrasé par Qt au retour).  Retour écran : « on ne peut pas cocher,
    choisir des éléments, et ça enlève l'option comme la coupe 2D ».

    Ce dialogue n'utilise que des widgets robustes partout :
    - une case « Comme la coupe 2D » en tête (cochée = miroir du style
      2D, la liste est grisée) ;
    - une QListWidget à cases (1 à 3 éléments simultanés, même plafond
      que la coupe 2D — le 4ᵉ clic est refusé avec message) ;
    - OK / Annuler.
    """

    def __init__(self, elements, mirror_label, checked, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Éléments affichés en 3D"))
        self.setMinimumWidth(340)
        self._max_checked = 3
        self._updating = False
        self._limit_message = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.chk_mirror = QCheckBox(
            str(mirror_label or self.tr("Comme la coupe 2D")))
        self.chk_mirror.setChecked(not checked)
        layout.addWidget(self.chk_mirror)

        self.listw = QListWidget()
        self.listw.setMaximumHeight(260)
        checked_set = set(checked or [])
        for el in (elements or []):
            item = QListWidgetItem(str(el))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if (checked and str(el) in checked_set)
                else Qt.CheckState.Unchecked)
            self.listw.addItem(item)
        layout.addWidget(self.listw)

        hint = QLabel(
            self.tr("Jusqu'à {} éléments simultanés (même limite que "
                    "la coupe 2D).").format(self._max_checked))
        hint.setStyleSheet("color:#7F8C8D; font-size:8pt;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.chk_mirror.toggled.connect(self._mirror_toggled)
        self.listw.itemChanged.connect(self._item_changed)
        self._mirror_toggled(self.chk_mirror.isChecked())

    def _mirror_toggled(self, mirror_on: bool):
        """Miroir cochée → la liste est grisée (elle ne s'applique pas)."""
        self.listw.setEnabled(not mirror_on)

    def _item_changed(self, item):
        if self._updating or item is None:
            return
        if item.checkState() == Qt.CheckState.Checked:
            if self._checked_count() > self._max_checked:
                # Plafond atteint : la case est refusée, message gardé
                # pour la barre de statut du dock.
                self._updating = True
                item.setCheckState(Qt.CheckState.Unchecked)
                self._updating = False
                self._limit_message = self.tr(
                    "{} éléments maximum en 3D (même limite que la coupe 2D)"
                ).format(self._max_checked)

    def _checked_count(self) -> int:
        n = 0
        for i in range(self.listw.count()):
            if self.listw.item(i).checkState() == Qt.CheckState.Checked:
                n += 1
        return n

    def selected_elements(self) -> list:
        """Éléments choisis ; liste VIDE = miroir de la coupe 2D."""
        if self.chk_mirror.isChecked():
            return []
        out = []
        for i in range(self.listw.count()):
            item = self.listw.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                out.append(str(item.text()))
        return out

