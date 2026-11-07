"""
DrillMaster — QGIS Plugin for drillhole modelling and visualisation.

Entry point: classFactory(iface) is called by QGIS on plugin load.
"""

from __future__ import annotations


def classFactory(iface):
    """QGIS plugin entry point.

    Args:
        iface: QgsPluginManagerInterface / QgisInterface instance.

    Returns:
        DrillMasterPlugin instance.
    """
    from .drillmaster import DrillMasterPlugin
    return DrillMasterPlugin(iface)
