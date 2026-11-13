"""DrillMaster — Vue 3D : widget d'assemblage (volet 1, tranche 4, v2.9.149).

Ce module ASSEMBLE la vue 3D (SPEC de restructuration) ; les couches
vivent dans leurs modules dédiés :

    core/camera3d.py          caméra orbitale pure
    core/style_resolver.py    source unique couleur/libellé 2D+3D
    core/mesh_builder.py      géométrie pure
    ui/view_3d_canvas.py      canvas (délègue dessin/interaction)
    ui/view_3d_renderer.py    dessin QPainter de la scène
    ui/view_3d_interaction.py souris/molette/survol/sélection
    ui/view_3d_overlays.py    légende/gizmo/badge/infobulle
    ui/overlay_layout.py      layout unique des overlays (pur)
    ui/view_3d_panel.py       panneau latéral
    ui/view_3d_surface.py     grille MNT (cascade partagée 2D)
    ui/view_3d_dialogs.py     dialogues (choix d'éléments)
"""

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QLabel, QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from ..core.multi_assay import format_grade_value  # noqa: F401 — réexport historique
from ..core.spatial_model import SpatialModel
from ..core.workspace import WorkspaceState
from .styles_qt import COLORS, suppress_button_focus_rects
from .view_3d_canvas import View3DCanvas
from .view_3d_dialogs import _AssayElementDialog  # noqa: F401 — utilisé par les handlers



class View3DWidget(QWidget):
    """Complete 3D View workspace tab integrated into VisualizationDock."""

    def __init__(self, workspace_state: WorkspaceState, main_dock=None, parent=None):
        super().__init__(parent)
        self.workspace_state = workspace_state
        self.main_dock = main_dock
        self.spatial_model = SpatialModel()
        self.canvas = View3DCanvas(self.workspace_state)
        # v2.9.142 — projet courant (source CSV topographie) + statut du MNT
        # affiché dans la barre de statut (diagnostic « MNT plat »).
        self._project = None
        self._mnt_status = ""
        self._build()
        suppress_button_focus_rects(self)
        # v2.9.171 — cases multi-domaines cachées par défaut (scope=all)
        self._update_multi_domain_visibility()

    def _build(self):
        # v2.9.150 — synchro « parfaite » : une édition du Référentiel
        # rafraîchit la 3D EN DIRECT (le résolveur lit le projet à chaque
        # résolution ; il suffit de repeindre).
        self.workspace_state.subscribe(
            "referential_changed", self._on_referential_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ------------------------------------------------------------------
        # Center Splitter: Canvas 3D (stretch 1) + Side Panel (240 px)
        # ------------------------------------------------------------------
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(True)

        # Container for Canvas (seamless full height, no redundant top bar)
        canvas_container = QWidget()
        cc_layout = QVBoxLayout(canvas_container)
        cc_layout.setContentsMargins(0, 0, 0, 0)
        cc_layout.setSpacing(0)

        # Forward aliases for compatibility with external references / tests
        self.combo_cam = self.canvas.combo_cam
        self.btn_zoom_all = self.canvas.btn_zoom_all
        self.btn_center_sel = self.canvas.btn_center_sel

        self.canvas.hover_changed.connect(self._on_hover_changed)
        cc_layout.addWidget(self.canvas, 1)

        splitter.addWidget(canvas_container)

        # Right Side Control Panel
        side_panel = self._build_side_panel()
        splitter.addWidget(side_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([650, 230])

        layout.addWidget(splitter, 1)

        # Bottom Diagnostic Bar
        self.status_bar = QLabel(self.tr("3D prête. Orbite : clic gauche · Pan : clic droit · Zoom : molette · Clic : sélectionner"))
        self.status_bar.setStyleSheet(f"color:{COLORS['text_medium']}; font-size:8pt; padding:2px 8px; background:#FFFFFF; border-top:1px solid {COLORS['border']};")
        layout.addWidget(self.status_bar)

    def _build_side_panel(self) -> QWidget:
        """Panneau latéral — délégué au module panneau (v2.9.149)."""
        from .view_3d_panel import build_side_panel
        return build_side_panel(self)
    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_camera_preset_changed(self, idx: int):
        data = self.combo_cam.itemData(idx)
        if data and isinstance(data, (tuple, list)) and len(data) == 2:
            self.canvas.set_view_preset(data[0], data[1])

    def _on_exag_changed(self, val: float):
        self.canvas._exag_user_touched = True  # v317 : son choix prime
        self.canvas.v_exag = val
        if hasattr(self, "spin_exag_side") and abs(self.spin_exag_side.value() - val) > 0.01:
            self.spin_exag_side.blockSignals(True)
            self.spin_exag_side.setValue(val)
            self.spin_exag_side.blockSignals(False)
        self.canvas.update()

    def _on_scope_changed(self, idx: int):
        scope = self.combo_scope.itemData(idx)
        self.canvas.scope_mode = scope
        # v2.9.171 — le multi-domaine n'est utile que sur PEU de forages
        # (sélection/coupe).  En « Projet complet » (potentiellement 300+
        # forages), les cases disparaissent : illisible, surchargé —
        # c'est ce que font les gros logiciels (Leapfrog, Micromine).
        self._update_multi_domain_visibility()
        self.canvas.update()

    def _update_multi_domain_visibility(self):
        """v2.9.171 — cases « Domaines simultanés » visibles seulement en
        scope « Coupe active »/« Sélection seule » ; en « Projet
        complet », retour au domaine seul (300 forages = surchargé)."""
        scope = self.canvas.scope_mode
        show = scope in ("section", "selection")
        primary = self.combo_geo_mode.currentData() or "litho"
        if hasattr(self, "domain_checks"):
            for k, chk in self.domain_checks.items():
                chk.setVisible(show)
                if not show and k != primary:
                    # retour au domaine seul
                    chk.blockSignals(True)
                    chk.setChecked(False)
                    chk.blockSignals(False)
            if not show:
                if primary in self.domain_checks:
                    self.domain_checks[primary].blockSignals(True)
                    self.domain_checks[primary].setChecked(True)
                    self.domain_checks[primary].blockSignals(False)
                if primary == "trajectory":
                    # v2.9.172 — le setter de LISTE filtrerait
                    # "trajectory" : passer par geo_domain.
                    self.canvas.geo_domain = primary
                else:
                    self.canvas.active_domains = [primary]
        # le sous-titre aussi ; l'ASTUCE inverse (v2.9.177) : en « Projet
        # complet » elle dit où débloquer les domaines simultanés.
        if getattr(self, "_sub_multi_lbl", None) is not None:
            self._sub_multi_lbl.setVisible(show)
        if getattr(self, "lbl_multi_hint", None) is not None:
            self.lbl_multi_hint.setVisible(not show)

    def _on_mnt_extent_changed(self, idx):
        # v2.9.141 — changement d'emprise MNT → recalcul immédiat de la surface.
        self._surface_sig = None
        self._compute_surface_grid()

    def _on_geo_domain_changed(self, idx: int):
        domain = self.combo_geo_mode.itemData(idx)
        # v2.9.166 — le combo définit le domaine PRINCIPAL ; les autres
        # cases cochées restent actives (elles deviennent secondaires).
        others = [d for d in self.canvas.active_domains if d != domain]
        # v2.9.173 — en « Projet complet » les cases simultanées sont
        # CACHÉES : le combo y remplace TOUT (avant, l'ancien principal
        # restait en secondaire → « ça s'affiche en double »).
        if self.canvas.scope_mode not in ("section", "selection"):
            others = []
        if domain == "trajectory":
            # v2.9.172 — « Trajectoires seules » : VRAIMENT seul (avant,
            # les cases restaient cochées → tubes fantômes).
            self.canvas.geo_domain = "trajectory"
            if hasattr(self, "domain_checks"):
                for chk in self.domain_checks.values():
                    chk.blockSignals(True)
                    chk.setChecked(False)
                    chk.blockSignals(False)
        else:
            self.canvas.active_domains = [domain] + others
            # synchronise les cases (le domaine principal est coché)
            if hasattr(self, "domain_checks"):
                for k, chk in self.domain_checks.items():
                    chk.blockSignals(True)
                    chk.setChecked(k in self.canvas.active_domains)
                    chk.blockSignals(False)
        self._sync_primary_ui(domain)
        self.canvas.update()

    def _sync_primary_ui(self, primary: str):
        """v2.9.172 — combo + widgets teneurs alignés sur le principal
        (source unique : ``active_domains`` ; le combo = le 1er)."""
        if not primary:
            return
        for i in range(self.combo_geo_mode.count()):
            if self.combo_geo_mode.itemData(i) == primary:
                if self.combo_geo_mode.currentIndex() != i:
                    self.combo_geo_mode.blockSignals(True)
                    self.combo_geo_mode.setCurrentIndex(i)
                    self.combo_geo_mode.blockSignals(False)
                break
        is_assays = (primary == "assays")
        self.lbl_assay_elem.setVisible(is_assays)
        self.lbl_assay_summary.setVisible(is_assays)
        self.btn_assay_choose.setVisible(is_assays)
        if is_assays:
            self.canvas.recompute_assay_scale()

    def _update_geo_mode_availability(self):
        """v2.9.141 — un fichier non importé ne doit pas proposer son domaine.

        Désactive (grisé) les entrées du combo « Domaine affiché » dont AUCUN
        forage ne porte de donnée — même règle que la coupe 2D (pistes grisées
        sans fichier).  Bascule sur le 1er domaine disponible si nécessaire.
        """
        dhs = self.canvas._drillholes or []
        has = {
            "litho": any(getattr(d, "litho", None) for d in dhs),
            "assays": any(getattr(d, "assays", None) for d in dhs),
            "alterations": any(getattr(d, "alterations", None) for d in dhs),
            "mineralizations": any(getattr(d, "mineralizations", None) for d in dhs),
            "structure": any(getattr(d, "structure", None) for d in dhs), "imagery": any(getattr(d, "imagery", None) for d in dhs), **{k: any(any(getattr(r, "kind", "") == k for r in (getattr(d, "geotech", None) or [])) for d in dhs) for k in ("rqd", "recovery", "density")},  # v2.9.260/263 ; v2.9.267 géotech (même ligne : cliquet T4-149)
            "intercepts": bool(self.canvas._threshold_rules),
            "trajectory": any(getattr(d, "trajectory", None) for d in dhs),
        }
        model = self.combo_geo_mode.model()
        for i in range(self.combo_geo_mode.count()):
            key = self.combo_geo_mode.itemData(i)
            enabled = bool(has.get(key, False))
            item = model.item(i)
            if item is not None:
                item.setEnabled(enabled)
        # v2.9.166 — les cases « Domaines simultanés » suivent la même règle
        if hasattr(self, "domain_checks"):
            for k, chk in self.domain_checks.items():
                chk.setEnabled(bool(has.get(k, False)))
        # Si la sélection courante est devenue indisponible, bascule.
        cur = self.combo_geo_mode.currentData()
        if not has.get(cur, False):
            for i in range(self.combo_geo_mode.count()):
                key = self.combo_geo_mode.itemData(i)
                if has.get(key, False):
                    self.combo_geo_mode.blockSignals(True)
                    self.combo_geo_mode.setCurrentIndex(i)
                    self.combo_geo_mode.blockSignals(False)
                    # v2.9.172 — les cases suivent (avant, elles
                    # restaient cochées sur un domaine disparu).
                    if hasattr(self, "domain_checks"):
                        for k2, chk in self.domain_checks.items():
                            chk.blockSignals(True)
                            chk.setChecked(k2 == key)
                            chk.blockSignals(False)
                    self.canvas.geo_domain = key
                    break
        self.canvas.update()

    def reset_after_project_close(self):
        """v2.9.152 — fermeture du projet : la 3D se vide comme la 2D.

        Forages, surface MNT, sélection, éléments, seuils, statut :
        plus de « vue 3D qui garde l'ancien projet » (retour écran).
        """
        self._project = None
        self.canvas.set_drillholes([], style_resolver=None, project=None)
        self.canvas.set_active_section(None)
        self.canvas.assay_display_elements = []
        self.canvas._assay_elements = []
        self.canvas._assay_scales = {}
        self.canvas._assay_scale = None
        self.canvas._threshold_rules = []
        self.canvas.set_surface_grid(None, "")
        self._mnt_status = ""
        self._surface_sig = None
        self._auto_plane_sec_key = None
        self._sync_project_id = None
        self._refresh_assay_summary()
        self._update_geo_mode_availability()
        self._on_hover_changed("")

    def _on_domain_toggled(self, key: str, state: int):
        """v2.9.166 — case « Domaines simultanés » cochée/décochée.

        v2.9.172 — SYNC COMBO ↔ CASES (retour écran : « intercept +
        litho = des mélanges ») : le principal est CONSERVÉ tant que sa
        case reste cochée ; INTERCEPTS fait partie des cases ; combo
        resynchronisé.
        """
        checked = []
        # Ordre canonique : litho > altérations > minéralisations >
        # teneurs > structures > intercepts
        for k in ("litho", "alterations", "mineralizations", "assays",
                  "structure", "imagery", "intercepts", "rqd", "recovery", "density"):
            chk = self.domain_checks.get(k)
            if chk is not None and chk.isChecked():
                checked.append(k)
        if not checked:
            # garde ≥ 1 domaine (setChecked re-déclenche le handler)
            if key in self.domain_checks:
                self.domain_checks[key].setChecked(True)
            return
        # v2.9.172 — le principal courant reste principal s'il est
        # toujours coché (avant : checked[0] → combo sautait sans raison).
        primary = self.canvas.geo_domain
        if primary not in checked:
            primary = checked[0]
        self.canvas.active_domains = (
            [primary] + [k for k in checked if k != primary])
        self._sync_primary_ui(primary)
        self.canvas.update()

    def _on_referential_changed(self, _domain_key=""):
        """Édition du Référentiel → repeint (v2.9.189 : invalide le cache)."""
        self.canvas._scene_rev = getattr(self.canvas, "_scene_rev", 0) + 1
        self.canvas.update()
        self.status_bar.setText(self.tr(
            "Référentiel mis à jour — vue 3D rafraîchie."))

    def _apply_assay_elements_display(self, elements):
        """v2.9.146 — éléments choisis ([] = miroir coupe 2D) + résumé."""
        from ..core.multi_assay import clamp_display_elements
        self.canvas.assay_display_elements = clamp_display_elements(elements)
        if len(self.canvas.assay_display_elements) == 1:
            self.canvas.active_assay_element = self.canvas.assay_display_elements[0]
        self._refresh_assay_summary()
        self.canvas.recompute_assay_scale()
        self.canvas.update()
        self._on_hover_changed("")

    def _refresh_assay_summary(self):
        """Le libellé résume toujours l'état réel (miroir ou éléments)."""
        from ..core.multi_assay import assay_selection_summary
        self.lbl_assay_summary.setText(
            assay_selection_summary(
                self.canvas.assay_display_elements,
                self._assay_mirror_label))

    def _open_assay_element_dialog(self):
        """v2.9.146 — dialogue robuste de choix des éléments (1 à 3)."""
        elems = self.canvas.get_available_assay_elements()
        if not elems:
            self.status_bar.setText(
                self.tr("Aucun élément analytique disponible dans les données."))
            return
        dialog = _AssayElementDialog(
            elems, self._assay_mirror_label,
            list(self.canvas.assay_display_elements or []), self)
        if dialog.exec_():
            self._apply_assay_elements_display(dialog.selected_elements())
            if dialog._limit_message:
                self.status_bar.setText(dialog._limit_message)

    def _on_hover_changed(self, text: str):
        if text:
            first_line = text.split("\n")[0]
            self.status_bar.setText(self.tr("Survol : {}").format(first_line))
        else:
            n = self.canvas.displayed_holes_count
            yaw = self.canvas.yaw_deg
            pitch = self.canvas.pitch_deg
            dom_label = self.combo_geo_mode.currentText()
            # v2.9.142 — la SOURCE du MNT est visible (diagnostic « MNT
            # plat » : DEM réel, CSV topographie, ou repli collets).
            mnt = f" | {self._mnt_status}" if self._mnt_status else ""
            img = self.canvas.imagery_status_snippet(self.tr)
            status = self.tr("3D : {} forages | {}{} | Azimut : {}° | Pendage : {}°").format(n, dom_label, mnt, f"{yaw:.0f}", f"{pitch:.0f}")
            self.status_bar.setText(status + (f" | {img}" if img else ""))
    def _section_mnt_choice(self):
        """Choix « Source MNT » de la coupe 2D — délégué (v2.9.149)."""
        from .view_3d_surface import section_mnt_choice
        return section_mnt_choice(self)
    def _compute_surface_grid(self):
        """Grille MNT (cascade 2D partagée) — déléguée (v2.9.149)."""
        from .view_3d_surface import compute_surface_grid
        compute_surface_grid(self)
    def sync_with_project(self, project, active_section_line=None):
        """Synchronize 3D scene with the active MainDock project and 2D section."""
        if not project:
            return
        # v2.9.142 — projet conservé (lecture du CSV topographie pour le MNT).
        self._project = project

        drillholes = []
        if self.main_dock and hasattr(self.main_dock, "drillholes"):
            drillholes = self.main_dock.drillholes or []

        self.spatial_model.set_drillholes(drillholes)
        resolver = getattr(project, "resolve_category_style", None)

        self.canvas.set_drillholes(drillholes, style_resolver=resolver, project=project)

        # v2.9.141 — grise les domaines sans fichier importé.
        self._update_geo_mode_availability()

        # v2.9.172 — éléments teneurs (miroir 2D + choix conservé) :
        # délégué au canvas qui possède cet état (widget reste mince).
        self._assay_mirror_label = self.canvas.sync_assay_elements(project)
        self._refresh_assay_summary()

        section_holes = []
        buf_val = 20.0
        sec_line = active_section_line
        if self.main_dock and hasattr(self.main_dock, "section_widget"):
            sw = self.main_dock.section_widget
            if not sec_line and hasattr(sw, "_line") and sw._line:
                sec_line = sw._line
            elif not sec_line and hasattr(sw, "canvas") and hasattr(sw.canvas, "_line") and sw.canvas._line:
                sec_line = sw.canvas._line
            if hasattr(sw, "buffer_spin"):
                buf_val = sw.buffer_spin.value()
            if hasattr(sw, "canvas") and hasattr(sw.canvas, "_result") and sw.canvas._result:
                section_holes = [h.hole_id for h in sw.canvas._result.holes]
            # v2.9.317 — exagération 2D partagée vers la 3D.
            _cnv2 = getattr(sw, "canvas", None)
            if _cnv2 is not None:
                self.canvas.sync_exag_from_2d(_cnv2, self)

        # Enable or disable Section plane checkbox based on whether a section is active
        has_section = bool(sec_line)
        self.chk_plane.setEnabled(has_section)
        # v2.9.149 — plan de coupe fantôme : une coupe RESTAURÉE ne coche
        # plus le plan ; seule une coupe changée EN SESSION le coche.
        sec_key = id(sec_line) if has_section else None
        if sec_key != getattr(self, "_auto_plane_sec_key", None):
            first_seen = not hasattr(self, "_auto_plane_sec_key")
            project_changed = (id(project) != getattr(self, "_sync_project_id", None))
            if has_section and not first_seen and not project_changed:
                self.chk_plane.setChecked(True)
                self.canvas.show_section_plane = True
            self._auto_plane_sec_key = sec_key
        self._sync_project_id = id(project)
        self.chk_corridor.setEnabled(has_section)
        if has_section:
            self.chk_plane.setToolTip(self.tr("Plan vertical de la coupe : {}").format(getattr(sec_line, 'name', self.tr('Coupe active'))))
            self.canvas.set_active_section(sec_line, buffer_val=buf_val, section_holes=section_holes)
        else:
            self.chk_plane.setToolTip(self.tr("Aucun plan de coupe actif — tracez une coupe sur la carte à l’étape 4"))
            self.canvas.set_active_section(None)

        # v2.9.141 (P1) — recalcule la surface réelle APRÈS set_active_section
        # (qui met à jour les forages de coupe), quand les forages OU le jeu
        # de rasters MNT OU les forages de la coupe changent — pas à chaque
        # passage sur l'onglet (un DEM chargé après coup est pris en compte).
        # v2.9.142 — la signature suit AUSSI le combo « Source MNT » de la
        # coupe 2D et le CSV topographie du projet (changement de source ⇒
        # recalcul, y compris repli raster → CSV).
        try:
            from .raster_surface import qgis_raster_layers
            _raster_ids = tuple(sorted(lid for lid, _l in qgis_raster_layers()))
        except ImportError:
            # QGIS absent (tests hors QGIS) — l'absence de rasters n'est
            # pas un échec, c'est l'état attendu hors environment.
            _raster_ids = ()
        _csv_sig = ""
        try:
            _topo_path = project.get_imported_file_path("topography")
            if _topo_path:
                import os as _os
                _csv_sig = f"{_topo_path}|{_os.path.getmtime(_topo_path)}"
        except Exception as exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : signature du CSV topographie "
                          "(recalcul différé au prochain passage)", exc)
            _csv_sig = ""
        _sec_ids = tuple(sorted(self.canvas._section_hole_ids))
        sig = (tuple(sorted(d.hole_id for d in drillholes)), _raster_ids,
               _sec_ids, self._section_mnt_choice() or "auto", _csv_sig)
        if sig != getattr(self, "_surface_sig", None):
            self._surface_sig = sig
            self._compute_surface_grid()

        self._on_hover_changed("")
