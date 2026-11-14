"""
DrillMaster ORIG — cycle de vie du plugin (coquille fine).

Un fichier = un département. Ici : uniquement l'inscription QGIS
(dock, menu, actions). Toute logique vit dans core/ ou les vues.
"""

from __future__ import annotations


class DrillMasterOrigPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.dock = None
        self.action = None

    def initGui(self):
        from qgis.PyQt.QtWidgets import QAction
        from qgis.PyQt.QtGui import QIcon
        from qgis.PyQt.QtCore import Qt
        import os

        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
        self.action = QAction(
            QIcon(icon_path), "DrillMaster ORIG", self.iface.mainWindow())
        self.action.triggered.connect(self._toggle_dock)
        self.iface.addPluginToMenu("DrillMaster ORIG", self.action)
        self._ensure_dock()

    def _ensure_dock(self):
        if self.dock is not None:
            return
        from .dock import OrigDock
        self.dock = OrigDock(self.iface, self.iface.mainWindow())
        self.iface.addDockWidget(2, self.dock)

    def _toggle_dock(self):
        self._ensure_dock()
        self.dock.setVisible(not self.dock.isVisible())

    def unload(self):
        if self.dock is not None:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
        if self.action is not None:
            self.iface.removePluginMenu("DrillMaster ORIG", self.action)
            self.action.deleteLater()
            self.action = None
