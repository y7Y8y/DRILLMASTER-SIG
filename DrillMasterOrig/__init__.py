"""
DrillMaster ORIG — plugin QGIS (refonte).

Point d'entrée : classFactory(iface), appelé par QGIS au chargement.
"""

from __future__ import annotations


def classFactory(iface):
    from .qgis.plugin import DrillMasterOrigPlugin
    return DrillMasterOrigPlugin(iface)
