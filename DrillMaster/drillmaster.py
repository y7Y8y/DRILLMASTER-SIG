"""
DrillMaster — Main Plugin Class
================================
Handles plugin lifecycle: loading, menu action, dock widget creation.
"""

from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtGui import QAction
from qgis.PyQt.QtWidgets import QMainWindow

from .core.workspace import WorkspaceState
from .ui.main_dock import MainDock
from .ui.visualization_dock import VisualizationDock


def _tr(text):
    """v2.9.230 — FIX CRASH (retour écran : « 'DrillMasterPlugin'
    object has no attribute 'tr' ») : la classe du plugin n'hérite
    PAS de QObject — pas de _tr().  Contexte explicite
    DrillMasterPlugin (celui du .ts)."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("DrillMasterPlugin", text)


def _read_plugin_version() -> str:
    """v2.9.323 — version du paquet chargé (jamais une constante)."""
    try:
        import os
        meta = os.path.join(os.path.dirname(__file__), "metadata.txt")
        with open(meta, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("version="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def _schedule_splash_close(splash, delay_ms):
    """Ferme le démarreur SANS geler le thread principal (v2.9.253).

    v2.9.221/223 utilisaient ``QThread.msleep()`` (thread GUI de
    QGIS) pour garantir une visibilité minimale.  Sous Windows/QGIS
    ce gel laissait le compositeur sur un rendu partiel : la barre
    de menus et les icônes de QGIS restaient ensuite en zone
    blanche, et tout revenait à la normale au déchargement du
    plugin.  ``QTimer.singleShot`` laisse la boucle d'événements de
    Qt peindre normalement avant de fermer, sans jamais bloquer.

    Retourne True si la fermeture a été planifiée ; False si elle a
    dû être immédiate (repli sûr, jamais de fuite).
    """
    if splash is None:
        return False
    try:
        from qgis.PyQt.QtCore import QTimer
        delay = max(0, int(delay_ms))
        # 356 — ceinture + bretelles : close, puis hide de secours,
        # puis deleteLater.  Un PC lent ne peut plus garder le logo.
        QTimer.singleShot(delay, splash.close)
        QTimer.singleShot(delay + 400, splash.hide)
        QTimer.singleShot(delay + 450, splash.deleteLater)
        return True
    except Exception as _exc:
        from .core.diagnostics import log_swallowed
        log_swallowed("Démarreur : fermeture planifiée indisponible "
                      "(fermeture immédiate)", _exc)
        try:
            splash.close()
        except Exception:
            pass
        return False


class DrillMasterPlugin:
    """DrillMaster QGIS plugin — entry point."""

    def __init__(self, iface):
        self.iface = iface
        self.dock: MainDock = None
        self.visualization_dock: VisualizationDock = None
        self.workspace_state: WorkspaceState = None
        self.action: QAction = None
        # v2.9.272 — entrée « À propos » (attribution : auteur, version,
        # licence, dépôt).  Initialisée ici pour qu'un unload prématuré
        # ne tombe jamais sur un attribut absent.
        self.about_action: QAction = None
        self._visualization_was_visible = False

    # ------------------------------------------------------------------
    # Plugin lifecycle
    # ------------------------------------------------------------------
    def initGui(self):
        """Called by QGIS when the plugin is loaded."""
        # v2.9.227 — Lot 1a : traducteur installé AU CHARGEMENT selon
        # la langue mémorisée (QSettings — jamais de question au
        # démarrage, règle du plan langue).  Le français est la
        # langue source : aucun traducteur à installer.
        from .core.i18n import load_language_setting, set_language
        set_language(load_language_setting())
        # Create the toggle action
        # v2.9.227 — l'emoji pioche est RETIRÉ du texte (retour écran :
        # QGIS affichait l'icône ET l'emoji côte à côte — double
        # logo).  Le texte reste « DrillMaster » pour les menus.
        self.action = QAction("DrillMaster", self.iface.mainWindow())
        # v2.9.218 — ICÔNE RÉELLE dans la barre QGIS (retour écran :
        # « l'icône de l'extension ne sort pas à l'interface QGIS ») :
        # l'action n'avait AUCUNE icône — le bouton barre n'affichait
        # que le texte.  icon.png est livré dans le plugin depuis
        # l'origine : on l'utilise (barre + menu, taille QGIS).
        import os as _os
        from qgis.PyQt.QtGui import QIcon
        _icon_path = _os.path.join(_os.path.dirname(__file__), "icon.png")
        if _os.path.isfile(_icon_path):
            self.action.setIcon(QIcon(_icon_path))
        self.action.setWhatsThis("Modélisation et visualisation de forages miniers/géotechniques")
        self.action.triggered.connect(self._toggle_dock)

        # Add to plugin menu and toolbar
        self.iface.addPluginToMenu("&DrillMaster", self.action)
        self.iface.addToolBarIcon(self.action)

        # v2.9.272 — ATTRIBUTION (audit PASS 9 : l'auteur, la version et
        # la licence n'étaient visibles NULLE PART — metadata.txt disait
        # « DrillMaster Team », aucun dialogue « À propos », aucun
        # LICENSE).  Entrée de menu SEULEMENT : la barre d'outils garde
        # un unique bouton, celui de l'atelier.
        from .ui.about_dialog import make_about_icon
        self.about_action = QAction(
            _tr("À propos de DrillMaster"), self.iface.mainWindow())
        self.about_action.setIcon(make_about_icon())
        self.about_action.setWhatsThis(
            _tr("Auteur, version, licence et dépôt du plugin"))
        self.about_action.triggered.connect(self._show_about)
        self.iface.addPluginToMenu("&DrillMaster", self.about_action)

        # v2.9.254 — PETITES MAJUSCULES SANS MUTATION GLOBALE : les
        # petites majuscules des survols sont portées par le QSS
        # TOOLTIP_STYLE (contexte du plugin) et par les QFont des
        # infobulles 3D — PLUS AUCUN appel à
        # QApplication.setFont(..., "QToolTip") : ce réglage global
        # déréglait les dialogues et boutons QGIS (texte absent,
        # éléments désalignés), et ne revenait qu'au déchargement.

    def unload(self):
        """Called by QGIS when the plugin is unloaded."""
        # v2.9.227 — retire le traducteur proprement.
        try:
            from .core.i18n import set_language
            set_language("fr")
        except Exception as _exc:
            from .core.diagnostics import log_swallowed
            log_swallowed("Déchargement : retrait du traducteur "
                          "(ignoré)", _exc)
        # Remove menu item and toolbar icon
        self.iface.removePluginMenu("&DrillMaster", self.action)
        self.iface.removeToolBarIcon(self.action)
        # v2.9.272 — l'entrée « À propos » part avec le plugin.
        if getattr(self, "about_action", None) is not None:
            self.iface.removePluginMenu("&DrillMaster", self.about_action)
            self.about_action = None

        # v2.9.254 — aucune restauration de police globale : le plugin
        # ne modifie plus QApplication.setFont() — plus rien à remettre
        # en état au déchargement.

        self._save_layout()
        if self.visualization_dock:
            self.iface.mainWindow().removeDockWidget(self.visualization_dock)
            self.visualization_dock.deleteLater()
            self.visualization_dock = None
        if self.dock:
            self.dock.clear_map_overlays()
            self.iface.mainWindow().removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
        self.workspace_state = None

    # ------------------------------------------------------------------
    # Dock management
    # ------------------------------------------------------------------
    def _toggle_dock(self, *_args):
        """Show/hide the controller; preserve optional workspace visibility."""
        if self.dock is None:
            self._create_dock()
            return

        if self.dock.isVisible():
            self._visualization_was_visible = bool(
                self.visualization_dock and self.visualization_dock.isVisible())
            if self.visualization_dock:
                self.visualization_dock.hide()
            self.dock.hide()
        else:
            # v2.9.221 — le DÉMARREUR REVIENT à chaque réouverture
            # (retour écran : « à 1er démarrage seulement, une fois
            # tout fermé il réapparaît plus »).  Pour l'utilisateur,
            # cliquer le bouton APRÈS avoir tout fermé = redémarrer
            # le plugin : le démarreur s'affiche, progression réelle
            # (monter/restaurer les docks), jamais de délai artificiel.
            from .ui.splash import make_splash
            # v2.9.323 — la version AFFICHÉE au démarrage est celle du
            # paquet chargé (metadata.txt) : plus de « c'est toujours
            # 320 » ambigu — ce qui s'affiche EST ce qui tourne.
            # v2.9.223 — DEUX marches pour DEUX étapes (la v2.9.222
            # laissait la barre à 2/8 = 25 %).
            _sp = make_splash(self.iface.mainWindow(),
                              version=_read_plugin_version(),
                              n_steps=2)
            try:
                if _sp is not None:
                    _sp.show()
                    _sp.step(_tr("Réouverture de l'atelier…"))
                self.dock.show()
                self.dock.raise_()
                if self.visualization_dock and self._visualization_was_visible:
                    self.visualization_dock.show()
                    self.visualization_dock.raise_()
                self.iface.mainWindow().raise_()
                if _sp is not None:
                    _sp.step(_tr("Prêt."))
                    _sp.finish()
                    # v2.9.253 — la visibilité est ensuite donnée par
                    # QTimer.singleShot, JAMAIS par QThread.msleep()
                    # sur le thread GUI de QGIS (gel → barre de menus
                    # et icônes QGIS corrompues sous Windows).
                    if _schedule_splash_close(_sp, 350):
                        _sp = None
            finally:
                if _sp is not None:
                    _sp.close()
                    _sp.deleteLater()

    def _show_about(self):
        """Ouvre le dialogue « À propos » (v2.9.272).

        Jamais d'exception remontée : une fiche d'identité illisible ne
        doit pas faire planter QGIS (même contrat que ``make_splash``).
        """
        try:
            from .ui.about_dialog import AboutDialog
            dialog = AboutDialog(self.iface.mainWindow())
            dialog.exec()
        except Exception as _exc:
            from .core.diagnostics import log_swallowed
            log_swallowed("À propos : ouverture du dialogue "
                          "(fenêtre ignorée)", _exc)

    def _create_dock(self):
        """Create compact controller + optional large visualization workspace.

        v2.9.220 — DÉMARREUR (retour écran : « un démarreur de plugin
        qui affiche l'icône, le nom et un chargement ») : écran de
        démarrage au premier clic, progression RÉELLE (chaque étape
        de la création des docks avance la barre), jamais de délai
        artificiel.  En cas d'échec du splash, le plugin démarre
        normalement (make_splash ne lève jamais)."""
        from .ui.splash import make_splash
        _version = ""
        try:
            _meta = os.path.join(os.path.dirname(__file__), "metadata.txt")
            for _line in open(_meta, encoding="utf-8"):
                if _line.strip().startswith("version="):
                    _version = _line.strip().split("=", 1)[1].strip()
                    break
        except Exception as _exc:
            from .core.diagnostics import log_swallowed
            log_swallowed("Démarreur : lecture de la version "
                          "(splash sans numéro)", _exc)
        # v2.9.223 — SIX marches pour SIX étapes : la barre finit
        # PLEINE (retour écran : « ne charge pas jusqu'à la fin »).
        _splash = make_splash(self.iface.mainWindow(), version=_version,
                              n_steps=6)
        _t0 = None
        try:
            if _splash is not None:
                _splash.show()
                try:
                    from qgis.PyQt.QtCore import QElapsedTimer
                    _t0 = QElapsedTimer()
                    _t0.start()
                except Exception as _exc:
                    from .core.diagnostics import log_swallowed
                    log_swallowed("Démarreur : chrono de visibilité "
                                  "(sans minimum)", _exc)
            self.workspace_state = WorkspaceState()
            parent = self.iface.mainWindow()
            if _splash is not None:
                _splash.step(_tr("Contrôle · Données & Coupes…"))
            self.dock = MainDock(
                self.iface, workspace_state=self.workspace_state, parent=parent)
            if _splash is not None:
                _splash.step(_tr("Visualisation · Coupe 2D & Vue 3D…"))
            self.visualization_dock = VisualizationDock(
                self.iface, self.dock, self.workspace_state, parent=parent)
            if _splash is not None:
                _splash.step(_tr("Connexion des vues…"))
            self.dock.attach_visualization_dock(self.visualization_dock)
            if _splash is not None:
                _splash.step(_tr("Ouverture de l'atelier…"))
            window = self.iface.mainWindow()
            window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
            # Wide visual workspace defaults above the map; users may redock
            # or float it, and QSettings preserves that choice afterwards.
            window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.visualization_dock)
            self._restore_layout()
            self.dock.show()
            self.dock.raise_()
            # v2.9.222 — PRÉPARATION (retour écran : « le démarrage doit
            # permettre au plugin de SE PRÉPARER et éviter d'être lent ») :
            # le démarreur ROUVRE LE DERNIER PROJET (CSV + GeoPackage,
            # le vrai travail lourd) — à l'arrivée, l'atelier est PRÊT.
            # Réglable à l'étape 1 ; jamais de blocage si le projet
            # manque (préparé sans projet, comme avant).
            if _splash is not None:
                # v2.9.234 — reconstruction de langue
                self.dock._rebuild_callback = self._rebuild_docks
                _splash.step(_tr("Dernier projet…"))
            try:
                self.dock.prepare_startup()
            except Exception as _exc:
                from .core.diagnostics import log_swallowed
                log_swallowed("Démarreur : préparation du dernier "
                              "projet (démarré sans projet)", _exc)
            if _splash is not None:
                _splash.step(_tr("Prêt."))
                _splash.finish()
                # v2.9.253 — visibilité minimale SANS bloqueur : la
                # fermeture est planifiée sur la boucle d'événements
                # (QTimer.singleShot).  QThread.msleep() sur le thread
                # GUI de QGIS gelait le compositeur sous Windows et
                # corrompait la barre de menus / les icônes de QGIS.
                _remain_ms = 0
                if _t0 is not None:
                    _remain_ms = 800 - _t0.elapsed()
                if _schedule_splash_close(_splash, _remain_ms):
                    _splash = None
            from qgis.PyQt.QtWidgets import QApplication
            QApplication.processEvents()
        finally:
            if _splash is not None:
                _splash.close()
                _splash.deleteLater()

    def _rebuild_docks(self):
        """v2.9.234 — changement de langue : détruit et reconstruit
        les docks.  Le démarreur repasse, TOUT arrive dans la
        nouvelle langue."""
        try:
            self._save_layout()
        except Exception as _exc:
            from .core.diagnostics import log_swallowed
            log_swallowed("Reconstruction : disposition (non "
                          "conservée)", _exc)
        try:
            if self.visualization_dock:
                self.iface.mainWindow().removeDockWidget(
                    self.visualization_dock)
                self.visualization_dock.deleteLater()
                self.visualization_dock = None
            if self.dock:
                self.iface.mainWindow().removeDockWidget(self.dock)
                self.dock.deleteLater()
                self.dock = None
            self._create_dock()
        except Exception as _exc:
            from .core.diagnostics import log_swallowed
            log_swallowed("Reconstruction : docks non reconstruits "
                          "(rechargez le plugin)", _exc)

    def _save_layout(self):
        settings = QSettings()
        if self.dock:
            settings.setValue(
                "DrillMaster/controlDockGeometry", self.dock.saveGeometry())
        if self.visualization_dock:
            settings.setValue(
                "DrillMaster/visualizationDockGeometry",
                self.visualization_dock.saveGeometry())
            settings.setValue(
                "DrillMaster/visualizationDockVisible",
                self.visualization_dock.isVisible())
            settings.setValue(
                "DrillMaster/visualizationDockHeight",
                max(self.visualization_dock.height(), 260))

    def _restore_layout(self):
        settings = QSettings()
        control_geometry = settings.value("DrillMaster/controlDockGeometry")
        visual_geometry = settings.value("DrillMaster/visualizationDockGeometry")
        if control_geometry:
            self.dock.restoreGeometry(control_geometry)
        if visual_geometry:
            self.visualization_dock.restoreGeometry(visual_geometry)
        if not self.visualization_dock.isFloating():
            saved_height = settings.value(
                "DrillMaster/visualizationDockHeight", 0, type=int)
            target_height = (
                saved_height if saved_height > 0
                else max(int(self.iface.mainWindow().height() * 0.42), 260))
            self.iface.mainWindow().resizeDocks(
                [self.visualization_dock], [target_height], Qt.Orientation.Vertical)
        visible = settings.value(
            "DrillMaster/visualizationDockVisible", False, type=bool)
        self._visualization_was_visible = visible
        if visible:
            self.visualization_dock.show()
        else:
            self.visualization_dock.hide()
