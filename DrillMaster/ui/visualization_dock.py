"""
DrillMaster — Visualization Dock (v2.9.136)
===========================================
Large workspace dock dedicated to spatial exploration and analysis:
  - Tab 1: Coupe 2D (SectionWidget — fully operational)
  - Tab 2: Vue 3D (View3DWidget)

Features a reactive top context bar powered by WorkspaceState:
[ Projet : {nom} ] • [ Coupe active : {coupe} ] • [ Forages : {n} ] • [ Mode : {mode} ]
"""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDockWidget, QFrame, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)
from qgis.gui import QgsDockWidget

from .section_dock import SectionWidget
from .styles_qt import (
    BASE_STYLE, COLORS, TAB_STYLE, suppress_button_focus_rects,
)
from .view_3d_v2 import View3DV2


def _view3d_enabled() -> bool:
    """383 — nouvelle vue 3D (moteur core/scene3d) ACTIVE par défaut.
    DRILLMASTER_3D=0 la coupe (diagnostic) ; sinon elle est toujours là."""
    import os
    flag = (os.environ.get("DRILLMASTER_3D") or "").strip().lower()
    return flag not in ("0", "false", "non", "no")


class VisualizationDock(QgsDockWidget):
    """Large visualization workspace kept separate from the compact controller."""

    SECTION_TAB = 0
    VIEW_3D_TAB = 1

    def __init__(self, iface, main_dock, workspace_state, parent=None):
        # v2.9.210 — RETRAIT de l'onglet Interprétation (demande
        # explicite de l'utilisateur) : le dock garde Coupe 2D + Vue
        # 3D.  Si la fonctionnalité revient un jour, elle s'appellera
        # « Corrélations proposées » (nom retenu par l'utilisateur).
        # v2.9.227 — Lot 1a : titre traduisible (tr(), contexte =
        # VisualizationDock — voir i18n/drillmaster_en.ts).
        from qgis.PyQt.QtCore import QCoreApplication as _QCA
        super().__init__(_QCA.translate(
            "VisualizationDock", "DrillMaster — Visualisation"), parent)
        self.setObjectName("DrillMasterVisualizationDock")
        self.iface = iface
        self.main_dock = main_dock
        self.workspace_state = workspace_state
        self.setAllowedAreas(
            Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
            | Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable)
        self._build()
        self.visibilityChanged.connect(self._on_visibility_changed)

        # React to workspace state events
        self.workspace_state.subscribe("project_name", self._on_project_changed)
        self.workspace_state.subscribe("current_section_id", self._on_section_id_changed)

    def _build(self):
        central = QWidget()
        central.setStyleSheet(BASE_STYLE)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ------------------------------------------------------------------
        # 1. Top Common Context Bar (Projet · Coupe active · Forages · Mode)
        # ------------------------------------------------------------------
        self.context_bar = QFrame()
        self.context_bar.setObjectName("DrillMasterContextBar")
        self.context_bar.setStyleSheet(f"""
            QFrame#DrillMasterContextBar {{
                background-color: #FFFFFF;
                border-bottom: 1px solid {COLORS['border']};
                border-top: none;
                border-left: none;
                border-right: none;
                padding: 4px 12px;
            }}
            #DrillMasterContextBar QLabel {{
                background: transparent;
                border: none;
                text-decoration: none;
            }}
        """)
        c_layout = QHBoxLayout(self.context_bar)
        c_layout.setContentsMargins(8, 4, 8, 4)
        c_layout.setSpacing(16)

        self.lbl_ctx_project = QLabel(self.tr("Projet : Aucun projet"))
        self.lbl_ctx_project.setStyleSheet(
            f"font-weight:bold; color:{COLORS['primary']}; font-size:8.5pt;")
        c_layout.addWidget(self.lbl_ctx_project)

        dot1 = QLabel(self.tr("•"))
        dot1.setStyleSheet(f"color:{COLORS['text_medium']};")
        c_layout.addWidget(dot1)

        self.lbl_ctx_section = QLabel(self.tr("Coupe : Aucune coupe"))
        self.lbl_ctx_section.setStyleSheet(
            f"color:{COLORS['text_dark']}; font-size:8.5pt;")
        c_layout.addWidget(self.lbl_ctx_section)

        dot2 = QLabel(self.tr("•"))
        dot2.setStyleSheet(f"color:{COLORS['text_medium']};")
        c_layout.addWidget(dot2)

        self.lbl_ctx_holes = QLabel(self.tr("Forages : -"))
        self.lbl_ctx_holes.setStyleSheet(
            f"color:{COLORS['text_dark']}; font-size:8.5pt;")
        c_layout.addWidget(self.lbl_ctx_holes)

        c_layout.addStretch(1)

        dot3 = QLabel(self.tr("•"))
        dot3.setStyleSheet(f"color:{COLORS['text_medium']};")
        c_layout.addWidget(dot3)

        self.lbl_ctx_mode = QLabel(self.tr("Mode : Coupe 2D"))
        self.lbl_ctx_mode.setStyleSheet(
            f"font-weight:bold; color:{COLORS['accent']}; font-size:8.5pt;")
        c_layout.addWidget(self.lbl_ctx_mode)

        layout.addWidget(self.context_bar)

        # ------------------------------------------------------------------
        # 2. Tabs: Coupe 2D | Vue 3D
        # ------------------------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.setObjectName("DrillMasterVisualizationTabs")
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Tab 1: Coupe 2D (SectionWidget)
        self.section_widget = SectionWidget(main_dock=self.main_dock)
        self.tabs.addTab(self.section_widget, self.tr("Coupe 2D"))
        # v2.9.178 — onglets expliqués, COURTS (convention TT-17).
        self.tabs.setTabToolTip(
            self.SECTION_TAB,
            self.tr("Coupe 2D · pistes litho/teneurs/altérations · "
                    "synchro carte + 3D"))

        # Tab 2: Vue 3D — 337 : OPT-IN (désactivée par défaut,
        # leçon perf des 333/336) ; activable en un clic, mémorisé.
        _v3d_ok = False
        _v3d_err = ""
        if _view3d_enabled():
            try:
                self._build_view3d()
                self.tabs.addTab(self.view_3d_widget, self.tr("Vue 3D"))
                _v3d_ok = True
            except Exception as _exc:  # la coupe 2D ne doit JAMAIS en pâtir
                from ..core.diagnostics import log_swallowed
                log_swallowed("visualization : construction vue 3D v2", _exc)
                _v3d_err = str(_exc)
        if not _v3d_ok:
            ph = QWidget()
            vlay = QVBoxLayout(ph)
            msg = QLabel(
                self.tr("Vue 3D indisponible : {}").format(_v3d_err)
                if _v3d_err else
                self.tr("Vue 3D désactivée (DRILLMASTER_3D=0)."))
            self._v3d_msg = msg
            msg.setWordWrap(True)
            btn = QPushButton(self.tr("Activer la vue 3D"))
            btn.setToolTip(self.tr(
                "Construit la scène 3D sur ce poste et mémorise le "
                "choix.  DRILLMASTER_3D=1 (ou =0) force l'activation "
                "(ou la désactivation) sans passer par ce bouton."))
            btn.clicked.connect(self._enable_view3d)
            vlay.addStretch(1)
            vlay.addWidget(msg, 0, Qt.AlignHCenter)
            vlay.addWidget(btn, 0, Qt.AlignHCenter)
            vlay.addStretch(1)
            self.tabs.addTab(ph, self.tr("Vue 3D"))
        # v2.9.178 — l'ancienne bulle d'attente de la 3D datait d'avant
        # remplacée (court, mais VRAI).
        self.tabs.setTabToolTip(
            self.VIEW_3D_TAB,
            self.tr("Vue 3D · orbite/pan/zoom · domaines simultanés en "
                    "Coupe/Sélection · ❓ = aide"))

        # Global Undo / Redo bar at top right
        # v2.9.205 — PÉRIMÈTRE HONNÊTE (retour écran : « export et
        # annuler/rétablir, c'est pour un seul onglet ou je comprends
        # pas ? »).  Cette barre n'agit QUE sur la COUPE 2D (réglages
        # pour Annuler/Rétablir, image PNG pour Exporter) — posée sur
        # la rangée d'onglets elle PARAISSAIT générale.  Elle vivait
        # déjà avec l'onglet Coupe 2D (ses raccourcis s'éteignent
        # quand l'onglet est caché) : désormais elle ne s'AFFICHE que
        # sur cet onglet.
        undo_bar = self.section_widget.build_global_undo_bar(self.tabs)
        self._undo_bar = undo_bar
        self.tabs.setCornerWidget(undo_bar, Qt.TopRightCorner)

        layout.addWidget(self.tabs, 1)
        self.setWidget(central)
        suppress_button_focus_rects(self)
        self.setMinimumHeight(260)


    # ------------------------------------------------------------------
    # Context Bar Updates
    # ------------------------------------------------------------------
    def update_context_bar(self, project_name=None, section_name=None,
                           holes_count=None, mode=None):
        """Update context labels reactively from WorkspaceState."""
        if project_name is not None:
            text = (self.tr("Projet : {}").format(project_name)
                    if project_name
                    else self.tr("Projet : Aucun projet"))
            self.lbl_ctx_project.setText(text)
        if section_name is not None:
            text = (self.tr("Coupe : {}").format(section_name)
                    if section_name
                    else self.tr("Coupe : Aucune coupe"))
            self.lbl_ctx_section.setText(text)
        if holes_count is not None:
            if holes_count == "-" or holes_count is None:
                text = self.tr("Forages : -")
            else:
                s_suffix = "s" if str(holes_count) not in ("0", "1") else ""
                text = self.tr("{} forage{}").format(holes_count, s_suffix)
            self.lbl_ctx_holes.setText(text)
        if mode is not None:
            self.lbl_ctx_mode.setText(self.tr("Mode : {}").format(mode))

    def _on_project_changed(self, project_name):
        self.update_context_bar(project_name=project_name)

    def _on_section_id_changed(self, section_id):
        self.sync_context()

    def sync_context(self):
        """Full refresh of context bar from MainDock and SectionWidget state."""
        proj_name = None
        if self.main_dock and getattr(self.main_dock, "project", None):
            proj = self.main_dock.project
            proj_name = (
                getattr(proj, "name", None)
                or (proj.config.get("project_name") if getattr(proj, "config", None) else None)
                or (proj.paths.project_name if getattr(proj, "paths", None) else None)
            )
        if not proj_name and self.workspace_state:
            proj_name = self.workspace_state.get("project_name")

        sec_name = None
        holes_count = "-"
        sec_details = ""
        if self.section_widget and getattr(self.section_widget, "_line", None):
            line = self.section_widget._line
            sec_name = getattr(line, "name", None) or self.tr("Coupe")

            # Métadonnées géométriques compactes
            az = getattr(line, "azimuth", None)
            length = getattr(line, "length", None)
            buf = getattr(self.section_widget, "buffer_spin", None)
            buf_val = buf.value() if buf else getattr(line, "buffer", None)
            buf_unit = getattr(self.section_widget, "_buffer_unit", "m")

            parts = []
            if az is not None:
                parts.append(self.tr("Az {}°").format(f"{az:.0f}"))
            if length is not None:
                parts.append(self.tr("L {} m").format(f"{length:.0f}"))
            if buf_val is not None:
                parts.append(f"Buffer ±{buf_val:.0f} {buf_unit}")
            if parts:
                sec_details = f" ({', '.join(parts)})"

            if getattr(self.section_widget, "canvas", None) and getattr(self.section_widget.canvas, "_result", None):
                holes_count = str(len(self.section_widget.canvas._result.holes))
            elif getattr(self.section_widget, "_drillholes", None):
                holes_count = str(len(self.section_widget._drillholes))
        elif self.main_dock and getattr(self.main_dock, "drillholes", None):
            holes_count = str(len(self.main_dock.drillholes))

        idx = self.tabs.currentIndex()
        if idx == self.VIEW_3D_TAB and hasattr(self, "view_3d_widget"):
            count_3d = len(self.view_3d_widget.canvas._get_visible_drillholes())
            sec_label = (self.tr("Plan repère : {}").format(sec_name)
                         if sec_name else self.tr("Aucun plan repère"))
            self.update_context_bar(proj_name, sec_label, count_3d, "Vue 3D")
            return

        mode_names = {
            self.SECTION_TAB: self.tr("Coupe 2D"),
            self.VIEW_3D_TAB: self.tr("Vue 3D"),
        }
        mode = mode_names.get(idx, self.tr("Coupe 2D"))
        full_sec = f"{sec_name}{sec_details}" if sec_name else None
        self.update_context_bar(proj_name, full_sec, holes_count, mode)

    # ------------------------------------------------------------------
    # View and Tab Management
    # ------------------------------------------------------------------
    def show_section_view(self):
        self.tabs.setCurrentIndex(self.SECTION_TAB)
        self.show()
        self.raise_()
        self.workspace_state.set("active_view", "section_2d")
        self.sync_context()

    def retranslate(self):
        """v2.9.227 — Lot 1a : ré-applique les textes traduits (appelé
        au changement de langue À CHAUD)."""
        from qgis.PyQt.QtCore import QCoreApplication as _QCA
        self.setWindowTitle(_QCA.translate(
            "VisualizationDock", "DrillMaster — Visualisation"))
        self.tabs.setTabText(self.SECTION_TAB, self.tr("Coupe 2D"))
        self.tabs.setTabText(self.VIEW_3D_TAB, self.tr("Vue 3D"))

    def _build_view3d(self):
        """337 — construit le widget 3D (appelé si opt-in actif)."""
        self.view_3d_widget = View3DV2(
            workspace_state=self.workspace_state,
            main_dock=self.main_dock)

    def _enable_view3d(self):
        """383 — clic « Activer la vue 3D » (si elle avait échoué/coupée)."""
        from qgis.PyQt.QtCore import QSettings
        QSettings().setValue("DrillMaster/view3d_enabled", True)
        idx = self.VIEW_3D_TAB
        self.tabs.removeTab(idx)
        self._build_view3d()
        self.tabs.insertTab(idx, self.view_3d_widget, self.tr("Vue 3D"))
        self.tabs.setCurrentIndex(idx)
        try:
            self.view_3d_widget.sync_with_project(
                self.main_dock.project if self.main_dock else None)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("visualization : activation 3D", _exc)

    def _on_tab_changed(self, index):
        names = {
            self.SECTION_TAB: "section_2d",
            self.VIEW_3D_TAB: "view_3d",
        }
        mode_labels = {
            self.SECTION_TAB: self.tr("Coupe 2D"),
            self.VIEW_3D_TAB: self.tr("Vue 3D"),
        }
        self.workspace_state.set("active_view", names.get(index, "map"))
        # v2.9.205 — la barre Annuler/Rétablir/Exporter n'agit QUE
        # sur la coupe 2D : elle disparaît des autres onglets (fini
        # le bouton « Exporter » qui exporte la coupe pendant que tu
        # regardes la 3D).
        if hasattr(self, "_undo_bar") and self._undo_bar is not None:
            self._undo_bar.setVisible(index == self.SECTION_TAB)
        self.sync_context()

        # Synchronize 3D scene when tab opens
        if index == self.VIEW_3D_TAB and hasattr(self, "view_3d_widget"):
            project = getattr(self.main_dock, "project", None) if self.main_dock else None
            active_line = getattr(self.section_widget, "_line", None) if self.section_widget else None
            self.view_3d_widget.sync_with_project(project, active_line)

    def _on_visibility_changed(self, visible):
        if visible:
            self._on_tab_changed(self.tabs.currentIndex())
            self.sync_context()
        elif self.workspace_state.get("active_view") == "section_2d":
            self.workspace_state.set("active_view", "map")
