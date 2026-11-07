"""
DrillMaster — Control Dock V2.7.1
=================================
Architecture: dock Contrôle compact; grandes vues dans VisualizationDock.
Le stepper reste dans l'Assistant et la Coupe 2D est une vue séparée.
"""

from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import Qt, QThread
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QTabWidget, QToolButton, QMenu,
)
from qgis.gui import QgsDockWidget

from .stepper import StepperWidget
from .step1_config import Step1Config
from .step2_import import Step2Import
from .step3_geometry import Step3Geometry
from .step4_section import Step4Section
from .reference_dialog import ReferenceDialog
from .styles_qt import COLORS, BASE_STYLE, BUTTON_PRIMARY, BUTTON_SECONDARY, TAB_STYLE
from .styles_qt import suppress_button_focus_rects
# focus rect helper imported below


from ..core.project import DrillMasterProject
from ..core.workspace import WorkspaceState
from ..core.validation import ImportBundle
from ..core.data_model import DrillHole


def compute_auto_trajectories(bundle, step: float,
                              on_progress=None) -> list:
    """v2.9.322/334/336 — génération tolérante, PURE (aucun état UI) :
    thread GUI ou worker.  Forage en erreur sauté + journalisé.
    336 : on_progress(i) toutes les 10 fiches — le worker y libère le
    GIL (msleep) pour que l'interface respire pendant le calcul."""
    from ..core.geometry import compute_trajectory, validate_trajectory
    from ..core.validation import auto_survey_for_vertical
    from ..core.data_model import DrillHole
    out = []
    for _i, hid in enumerate(sorted(bundle.collars or {})):
        if on_progress is not None and _i and _i % 10 == 0:
            try:
                on_progress(_i)
            except Exception as exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("trajectoires : on_progress", exc)
        try:
            c = bundle.collars[hid]
            sv = bundle.surveys.get(hid, []) or []
            if not sv:
                sv = auto_survey_for_vertical(c)
            traj = compute_trajectory(
                c, sv, subdivide=True, max_segment=step)
            _errs = validate_trajectory(traj)
            if _errs:
                raise ValueError("invalid trajectory: %r" % _errs)
            out.append(DrillHole(
                hole_id=hid, collar=c, survey=sv, trajectory=traj))
        except Exception as exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed(
                "Ouverture : génération auto du forage %s" % hid, exc)
    return out


class _TrajWorker334(QThread):
    """334 — gros projets (>150 forages) : trajectoires hors thread
    GUI ; application par signal terminé (_on_traj_done)."""

    def __init__(self, bundle, step, parent=None):
        super().__init__(parent)
        self.bundle = bundle
        self.step = step
        self.result = []

    def run(self):
        import time as _t
        _t0 = _t.perf_counter()
        # 336 — pause 1 ms toutes les 10 fiches : le thread GUI
        # récupère le GIL, l'interface ne fige plus pendant le calcul.
        self.result = compute_auto_trajectories(
            self.bundle, self.step,
            on_progress=lambda _i: self.msleep(1))
        from ..core.diagnostics import record_timing
        record_timing("open: trajectories (worker)",
                      _t.perf_counter() - _t0)


class MainDock(QgsDockWidget):
    def __init__(self, iface, workspace_state=None, parent=None):
        # v2.9.182 — titre aligné sur la convention des docks (docs/
        # CONVENTION_DOCKS.md) : le nom DIT la frontière produire/lire.
        # v2.9.227 — Lot 1a : titre traduisible (contexte = MainDock).
        from qgis.PyQt.QtCore import QCoreApplication as _QCA
        super().__init__(_QCA.translate(
            "MainDock", "DrillMaster — Contrôle · Données & Coupes"),
            parent)
        self.setObjectName("DrillMasterControlDock")
        self.iface = iface
        self.workspace_state = workspace_state or WorkspaceState()
        self.visualization_dock = None
        self.section_widget = None

        self.project: Optional[DrillMasterProject] = None
        self.import_bundle = ImportBundle()
        self.drillholes: list[DrillHole] = []
        self.layers: dict = {}
        self.last_gpkg_report: Optional[dict] = None
        self.selected_hole_id: Optional[str] = None
        # v2.9.167 — drapeau de réentrance sélection carte
        self._selection_from_map: bool = False
        self._buffer_band = None
        self._step_valid = [False, False, False, False]
        self._build()
        from qgis.core import QgsProject
        QgsProject.instance().layersWillBeRemoved.connect(
            self._on_project_layers_will_be_removed)
        # Keep the assistant compact. The coupe splitter may collapse its
        # property panel when the user narrows the QGIS dock.
        self.setMinimumWidth(340)
        self.setMaximumWidth(480)

    def _build(self):
        central = QWidget()
        central.setStyleSheet(BASE_STYLE)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Main tab widget (Assistant / Coupe) ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(TAB_STYLE)

        # ===== Assistant tab =====
        self.wizard_page = QWidget()
        wl = QVBoxLayout(self.wizard_page)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)

        # Header with title + stepper (INSIDE the Assistant tab)
        header = QFrame()
        header.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-bottom: 1px solid {COLORS['border']};")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(10, 5, 10, 4)
        hl.setSpacing(2)
        title_row = QHBoxLayout()
        title = QLabel(self.tr("DrillMaster"))
        title.setObjectName("label_title")
        title_row.addWidget(title)
        title_row.addStretch()
        # v2.9.272 — ⓘ À PROPOS : l'attribution (auteur, version, licence,
        # dépôt) devient accessible depuis l'atelier et pas seulement
        # depuis le menu QGIS.  Style repris du pattern « ⓘ Aide »
        # (styles_qt.make_collapsible_help) : bordure nulle, gris, curseur
        # main — rien de nouveau visuellement.  VOLONTAIREMENT hors du
        # menu « Projet ▾ » : ce menu est désactivé sans projet, or la
        # fiche d'identité doit rester lisible à tout moment.
        self.about_button = QToolButton()
        self.about_button.setText("ⓘ")
        self.about_button.setObjectName("about_button")
        self.about_button.setToolTip(self.tr("À propos de DrillMaster"))
        self.about_button.setCursor(Qt.PointingHandCursor)
        self.about_button.setStyleSheet(
            f"QToolButton {{ color:{COLORS['text_medium']}; border:none; "
            f"padding:0 4px; font-size:10pt; background:transparent; }}")
        self.about_button.clicked.connect(
            lambda _checked=False: self._open_about_dialog())
        title_row.addWidget(self.about_button)
        self.project_menu_button = QToolButton()
        self.project_menu_button.setText(self.tr("Projet ▾"))
        self.project_menu_button.setPopupMode(QToolButton.InstantPopup)
        self.project_menu_button.setStyleSheet(
            BUTTON_SECONDARY.replace("QPushButton", "QToolButton"))
        self.project_menu_button.setToolTip(self.tr("Outils du projet"))
        project_menu = QMenu(self.project_menu_button)
        self.reference_action = project_menu.addAction(
            self.tr("Référentiel du projet…"))
        self.reference_action.setToolTip(self.tr("Référentiel · libellés & symboles"))
        self.reference_action.triggered.connect(
            lambda _checked=False: self._open_reference_dialog())
        # v2.9.289 — profils d'affichage par type d'ouvrage.
        self.profiles_action = project_menu.addAction(
            self.tr("Profils d'affichage…"))
        self.profiles_action.setToolTip(self.tr(
            "Profils de visualisation par type d'ouvrage"))
        self.profiles_action.triggered.connect(
            lambda _checked=False: self._open_display_profiles_dialog())
        project_menu.addSeparator()
        self.close_project_action = project_menu.addAction(
            self.tr("Fermer le projet"))
        self.close_project_action.setToolTip(self.tr("Fermer le projet (fichiers gardés)"))
        self.close_project_action.triggered.connect(
            lambda _checked=False: self._close_project(
                message=self.tr(
                    "Projet fermé — les fichiers sont conservés.")))
        self.reset_project_action = project_menu.addAction(
            self.tr("Réinitialiser le projet…"))
        self.reset_project_action.setToolTip(
            self.tr("Réinitialiser · option suppression dossier"))
        self.reset_project_action.triggered.connect(
            lambda _checked=False: self._confirm_project_reset())
        self.project_menu_button.setMenu(project_menu)
        self.project_menu_button.setEnabled(False)
        title_row.addWidget(self.project_menu_button)
        hl.addLayout(title_row)
        self.project_name_label = QLabel(self.tr("Aucun projet ouvert"))
        self.project_name_label.setStyleSheet(
            f"color:{COLORS['text_light']}; font-size:8pt; background:transparent;")
        hl.addWidget(self.project_name_label)
        self.stepper = StepperWidget()
        hl.addWidget(self.stepper)
        wl.addWidget(header)

        # Stacked steps
        self.stack = QStackedWidget()
        self.step1 = Step1Config(self)
        # v2.9.227 — Lot 1a : bascule de langue à chaud (étape 1 →
        # traducteur + re-traduction des textes câblés).
        self.step1.on_language_changed = self._on_language_changed
        self.step2 = Step2Import(self)
        self.step3 = Step3Geometry(self)
        self.step4 = Step4Section(self)
        self.stack.addWidget(self.step1)
        self.stack.addWidget(self.step2)
        self.stack.addWidget(self.step3)
        self.stack.addWidget(self.step4)
        wl.addWidget(self.stack, 1)
        suppress_button_focus_rects(self)

        # Footer with nav buttons (inside assistant)
        footer = QFrame()
        footer.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_card']}; border-top: 1px solid {COLORS['border']}; }}")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(10, 4, 10, 4)
        fl.setSpacing(6)
        self.status_label = QLabel(self.tr("Prêt"))
        self.status_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 8pt; background: transparent;")
        # v2.7.12.10 — revue écran («GeoPackage sauvegardé
        # (drillmaster_geometry.gpk… » rogné au bord) : sans wrap, les
        # messages longs se tronquaient entre le label et les boutons.
        # Le détail complet est déjà dans l'étape (log vert) — le pied de
        # page passe sur deux lignes au lieu de couper le nom des fichiers.
        self.status_label.setWordWrap(True)
        fl.addWidget(self.status_label)
        fl.addStretch()
        self.btn_prev = QPushButton(self.tr("Précédent"))
        self.btn_prev.setStyleSheet(BUTTON_SECONDARY)
        self.btn_prev.setEnabled(False)
        self.btn_prev.clicked.connect(self._go_prev)
        fl.addWidget(self.btn_prev)
        self.btn_next = QPushButton(self.tr("Suivant"))
        self.btn_next.setStyleSheet(BUTTON_PRIMARY)
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._go_next)
        fl.addWidget(self.btn_next)
        wl.addWidget(footer)

        self.tab_widget.addTab(self.wizard_page, "Assistant")
        # The controller has a single workflow page. Large views live in the
        # optional VisualizationDock and never compete for this narrow space.
        self.tab_widget.tabBar().hide()

        layout.addWidget(self.tab_widget, 1)
        self.setWidget(central)

        # Signals
        self.step1.validity_changed.connect(lambda v: self._on_validity(0, v))
        self.step2.validity_changed.connect(lambda v: self._on_validity(1, v))
        self.step3.validity_changed.connect(lambda v: self._on_validity(2, v))
        self.step4.validity_changed.connect(lambda v: self._on_validity(3, v))
        self._current_step = 0

    def attach_visualization_dock(self, visualization_dock):
        """Wire the optional large workspace after both docks are created."""
        self.visualization_dock = visualization_dock
        self.section_widget = visualization_dock.section_widget
        self.section_widget.section_generated.connect(self._on_section_signal)
        self.step4.attach_history_widget(self.section_widget.history_group)
        self.workspace_state.subscribe(
            "selected_hole_id", self.section_widget.highlight_hole,
            emit_current=True)
        # v2.9.219 — FIX CRASH (retour écran : « TypeError:
        # subscribe() got multiple values for emit_current ») :
        # subscribe() prend UN événement par appel — la v2.9.218
        # avait empilé deux paires dans le même appel.  Sélection
        # MULTIPLE carte QGIS : la coupe met en évidence TOUS les
        # forages (la 3D suivait déjà).
        self.workspace_state.subscribe(
            "selected_hole_ids", self.section_widget.highlight_hole,
            emit_current=True)
        self.workspace_state.subscribe(
            "selected_interval", self.section_widget.on_workspace_interval,
            emit_current=True)
        self.workspace_state.subscribe(
            "highlight_code", self.section_widget.on_workspace_highlight_code,
            emit_current=True)
        # v2.9.165 — rétro-synchro 2D/3D → carte QGIS : quand un forage
        # est sélectionné dans la coupe ou la vue 3D, il est sélectionné
        # sur la couche collets (retour écran : « la synchro doit se
        # faire partout : carte, 2D, 3D »).
        self.workspace_state.subscribe(
            "selected_hole_id", self._on_hole_selected_sync_map)

    def _on_hole_selected_sync_map(self, hid):
        """v2.9.165 — rétro-synchro : un forage sélectionné en 2D/3D
        est sélectionné sur la couche collets de la carte QGIS.

        v2.9.167 — DRAPEAU : si la sélection vient DÉJÀ de la carte
        (``_selection_from_map``), on ne réécrit pas — sinon la
        multi-sélection carte est réduite à 1 forage.
        """
        if getattr(self, "_selection_from_map", False):
            return  # vient de la carte → pas de rétro-écriture
        if hid:
            self._select_on_map([hid])

    def _update_project_tools(self):
        enabled = bool(self.project and self.project.paths)
        self.project_menu_button.setEnabled(enabled)
        if enabled:
            name = self.project.config.get("project_name", "")
            self.project_name_label.setText(
                self.tr("Projet : {}").format(name) if name
                else self.tr("Projet ouvert"))
            self.project_menu_button.setToolTip(
                self.tr("Outils du projet : {}").format(name) if name
                else self.tr("Outils du projet"))
        else:
            self.project_name_label.setText(
                self.tr("Aucun projet ouvert"))

    def _open_about_dialog(self):
        """Dialogue « À propos » (v2.9.272) — attribution du plugin.

        Aucune condition de projet (contrairement au Référentiel) : la
        fiche d'identité doit rester lisible même l'atelier vide.  Jamais
        d'exception remontée vers QGIS.
        """
        try:
            from .about_dialog import AboutDialog
            AboutDialog(self).exec_()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("À propos : ouverture depuis l'atelier "
                          "(fenêtre ignorée)", _exc)

    def _open_display_profiles_dialog(self):
        from .display_profiles_dialog import DisplayProfilesDialog
        dlg = DisplayProfilesDialog(self.project, self)
        if dlg.exec():
            # v2.9.295 — régénération ROBUSTE : la chaîne historique
            # visualization_dock.section_widget.canvas pouvait casser
            # (section_widget réaffecté, canvas absent) → le choix du
            # type ne faisait RIEN à l'écran. On essaie tous les chemins.
            sw = getattr(self, "section_widget", None)
            cnv = getattr(sw, "canvas", None)
            for target in (cnv, sw):
                if target is not None and hasattr(target, "_regenerate"):
                    target._regenerate()
                    if hasattr(target, "update"):
                        target.update()
                    break

    def _open_reference_dialog(self, domain_key=None, raw_code=None):
        if not self.project:
            return
        dialog = ReferenceDialog(
            self.project, self, domain_key=domain_key, raw_code=raw_code)
        dialog.reference_saved.connect(self._on_reference_saved)
        dialog.exec_()

    def _on_reference_saved(self, domain_key=""):
        """CHEMIN UNIQUE de synchronisation (v2.7.10).

        Après TOUTE édition du Référentiel — symbole, couleur, motif,
        visibilité, « Appliquer » ou « OK » — les vues sont reconstruites
        depuis le dépôt du projet : un seul appel, sans condition par
        domaine, sans cache intermédiaire. Ce qui est sur le disque est
        ce qui est dessiné, partout.
        """
        if not self.project:
            return
        # v2.9.150 — l'événement voyage aussi sur le bus partagé
        # (WorkspaceState) : toute vue (3D) peut
        # s'abonner sans couplage direct au dock.
        try:
            self.workspace_state.set("referential_changed", domain_key or "")
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Projet (sauvegarde/chargement) : _on_reference_saved", _exc)
            pass  # bus optionnel — l'appel direct ci-dessous reste le chemin sûr
        if self.section_widget:
            self.section_widget.reload_reference_styles()
        if getattr(self, "visualization_dock", None) and hasattr(self.visualization_dock, "view_3d_widget"):
            self.visualization_dock.view_3d_widget.sync_with_project(self.project)
        self.update_litho_layer_style()
        self.update_domain_layer_style(
            "alterations", "alteration", "alteration",
            self._alteration_codes())
        self.update_domain_layer_style(
            "mineralizations", "mineralization_style",
            "mineralization_style", self._mineralization_style_codes())
        if domain_key == "structure" or not domain_key:
            self.update_structure_layer_style()
        self._apply_assay_field_aliases()
        if domain_key:
            domain_label = {
                "lithology": self.tr("Lithologie"),
                "alteration": self.tr("Altérations"),
                "mineralization_style": self.tr(
                    "Styles de minéralisation"),
                "minerals": self.tr("Minéraux"),
                "assay_elements": self.tr("Éléments mesurés"),
                "structure": self.tr("Type de structure"),
            }.get(domain_key, domain_key)
            self.status_label.setText(
                self.tr("✓ Référentiel appliqué : {}").format(domain_label))
        else:
            self.status_label.setText(self.tr("✓ Référentiel appliqué"))
        self.workspace_state.set(
            "reference_revision",
            self.project.config.get("last_modified", ""))

    def _go_next(self, *_args):
        # Returning to step 1 in an already-open project is navigation, not a
        # request to create the same project again.
        if (self._current_step == 0 and self.project is None
                and not self._create_project()):
            return
        if self._current_step < 3:
            self._current_step += 1
            self._update_step()

    def _go_prev(self, *_args):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step()

    def _update_step(self):
        self.stack.setCurrentIndex(self._current_step)
        self.stepper.set_step(self._current_step)
        self.btn_prev.setEnabled(self._current_step > 0)
        self.btn_next.setEnabled(self._step_valid[self._current_step] and self._current_step < 3)
        if self.project:
            self.project.set_step(self._current_step + 1)
        names = [self.tr("Projet"), self.tr("Données"),
                 self.tr("Géométrie 3D"), self.tr("Coupes")]
        self.status_label.setText(
            self.tr("Étape {}/4 — {}").format(
                self._current_step + 1, names[self._current_step]))

        # Geometry is deliberately manual: entering step 3 never starts a
        # background task. The single action button makes the operation and
        # GeoPackage write explicit to the user.

    def _on_validity(self, idx, valid):
        self._step_valid[idx] = valid
        self.btn_next.setEnabled(valid and self._current_step < 3)

    def _create_project(self):
        import os
        name = self.step1.get_project_name()
        crs = self.step1.get_crs()
        base_dir = self.step1.get_project_base_dir()
        safe_name = DrillMasterProject._sanitise_name(name)
        existing_config = os.path.join(base_dir, safe_name, "config.json")
        if os.path.isfile(existing_config):
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, self.tr("Projet déjà existant"),
                self.tr("Un projet de ce nom existe déjà dans ce "
                        "dossier. Utilisez 'Ouvrir un projet existant' "
                        "ou changez le nom."))
            self.status_label.setText(self.tr(
                "Projet '{}' déjà existant : création annulée."
            ).format(name))
            return False
        self.project = DrillMasterProject(base_dir=base_dir)
        try:
            self.project.create(
                name, crs.authid(), self.step1.get_units(),
                self.step1.get_sampling_step(), crs.description())
        except OSError as error:
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, self.tr("Création impossible"),
                self.tr("Le dossier du projet ne peut pas être créé :"
                        "\n{}").format(error))
            self.project = None
            return False
        self._reset_session_state()
        # v2.9.296 — type de forage choisi à l'Étape 1 : appliqué tout de
        # suite (sinon Auto = détection par préfixe).
        _hdt = self.step1.get_hole_data_type()
        if _hdt:
            self.project.config["display_profiles"] = {
                "enabled": True, "global": _hdt, "params": {}}
            self.project.save_config()
        self.workspace_state.set(
            "project_path", self.project.paths.project_dir)
        self.workspace_state.set("project_name", name)
        if self.section_widget:
            self.section_widget.load_project_settings()
            self.section_widget.set_style_resolver(
                self.project.resolve_category_style)
            # v2.9.306 — type Étape 1 : combo synchro + exag auto à la
            # création (sinon « s'applique pas partout »).
            if self.step1.get_hole_data_type() in ("AUGER", "PUITS"):
                self.section_widget._auto_vertical_exag()
        self._update_project_tools()
        if getattr(self, "visualization_dock", None):
            self.visualization_dock.sync_context()
        self.status_label.setText(
                self.tr("Projet « {} » créé.").format(name))
        return True

    # --- Generated layer lifecycle ---
    def _on_project_layers_will_be_removed(self, layer_ids):
        """Evict wrappers before QGIS destroys their underlying C++ objects."""
        removed = set(layer_ids or [])
        kept = {}
        for key, layer in self.layers.items():
            if not self._layer_alive(layer):
                continue
            try:
                if layer.id() not in removed:
                    kept[key] = layer
            except RuntimeError:
                continue
        self.layers = kept

    @staticmethod
    def _layer_alive(layer):
        """Return False for SIP wrappers whose C++ QgsVectorLayer was deleted."""
        if layer is None:
            return False
        try:
            from qgis.PyQt import sip
            if sip.isdeleted(layer):
                return False
        except ImportError:
            # Some QGIS/PyQt builds expose no qgis.PyQt.sip helper; probing
            # layer.id() below remains a reliable fallback.
            pass
        try:
            layer.id()  # forces SIP to validate the wrapped C++ object
            return True
        except (RuntimeError, AttributeError):
            return False

    def _remove_generated_layers(self):
        """Forget and safely remove both live and already-deleted wrappers."""
        from qgis.core import QgsProject
        qgs_project = QgsProject.instance()
        previous = list(self.layers.values())
        # Clear first so a failing wrapper can never remain cached.
        self.layers = {}
        for layer in previous:
            if not self._layer_alive(layer):
                continue
            try:
                layer_id = layer.id()
                if qgs_project.mapLayer(layer_id) is not None:
                    qgs_project.removeMapLayer(layer_id)
            except RuntimeError:
                # The project can delete a layer between the liveness check and
                # removal (project close/reload or another plugin callback).
                continue

    # --- Step 2 ---
    def _invalidate_generated_geometry(self):
        """Remove stale generated outputs while keeping saved section history."""
        self._remove_generated_layers()
        self.drillholes = []
        if self.section_widget:
            self.section_widget.set_drillholes([])
            self.section_widget.canvas._result = None
            self.section_widget.canvas.scene.clear()
        self.step3.reset()
        self.step4.reset()

    def _reset_session_state(self):
        """Purge every per-project UI state (new project or project switch).

        The import tabs used to keep the previous project's files, previews
        and validation results; they must start empty for another project.
        """
        self._invalidate_generated_geometry()
        self.step2.reset_all()
        self.import_bundle = ImportBundle()

    # --- v2.7.6.9 (RESET-01) — fermer / réinitialiser le projet -----------

    def _remove_project_group(self):
        """Supprime le groupe racine « FORAGES - {nom} » (couches de coupes
        comprises) du projet QGIS courant."""
        if not self.project or not self.project.config.get("project_name"):
            return
        from qgis.core import QgsProject
        from ..core.layers import GROUP_ROOT_TEMPLATE
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(
            GROUP_ROOT_TEMPLATE.format(
                name=self.project.config.get("project_name", "")))
        if group is not None:
            root.removeChildNode(group)

    def _close_project(self, message=None):
        """RESET-01 — retour à l'état « aucun projet ouvert », sans
        suppression de fichiers."""
        if message is None:
            message = self.tr("Projet fermé.")
        import time as _t336
        _t336_0 = _t336.perf_counter()
        # 336 — un worker trajectoires encore en cours est ABANDONNÉ :
        # son résultat ne sera pas appliqué au projet fermé.  La
        # référence QThread reste vivante jusqu'à sa fin réelle
        # (jamais de destruction pendant l'exécution).
        if getattr(self, "_traj_worker", None) is not None:
            self._traj_abandoned = True
        project_name = (self.project.config.get("project_name", "")
                        if self.project else "")
        self._remove_generated_layers()
        self._remove_project_group()
        self.clear_map_overlays()
        self._reset_session_state()
        self.workspace_state.set("project_path", None)
        self.workspace_state.set("selected_hole_id", None)
        self.workspace_state.set("current_section_id", None)
        self.project = None
        self.step1.name_edit.clear()
        self._current_step = 0
        self._step_valid = [False, False, False, False]
        self._update_step()
        if self.section_widget:
            self.section_widget.reset_after_project_close()
        # v2.9.152 — la vue 3D se vide AUSSI à la fermeture du projet
        # (retour écran : « la 3D reste encore là, pas synchro »).
        viz = getattr(self, "visualization_dock", None)
        if viz is not None and hasattr(viz, "view_3d_widget"):
            try:
                viz.view_3d_widget.reset_after_project_close()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Projet (sauvegarde/chargement) : _close_project", _exc)
                pass  # la fermeture ne doit jamais être bloquée par la 3D
        self._update_project_tools()
        if project_name:
            message = f"{message} — {project_name}"
        self.status_label.setText(message)
        from ..core.diagnostics import record_timing
        record_timing("close project (_close_project)",
                      _t336.perf_counter() - _t336_0)

    def _confirm_project_reset(self):
        """RESET-01 — dialogue : fermer en gardant les fichiers, ou tout
        supprimer définitivement (confirmation renforcée + garde-fous de
        ``DrillMasterProject.delete_project_folder``)."""
        if not self.project:
            return
        from qgis.PyQt.QtWidgets import (
            QDialog, QDialogButtonBox, QLabel, QMessageBox, QRadioButton,
            QVBoxLayout)
        project_dir = (self.project.paths.project_dir
                       if self.project.paths else "")
        name = self.project.config.get(
            "project_name", self.tr("ce projet"))
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Réinitialiser le projet"))
        layout = QVBoxLayout(dialog)
        intro = QLabel(
            self.tr("Projet ouvert : <b>{}</b><br>"
                    "Que voulez-vous faire ?").format(name))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        keep_files = QRadioButton(
            self.tr("Fermer le projet — les fichiers sont conservés, "
                    "il pourra être rouvert."))
        keep_files.setChecked(True)
        delete_files = QRadioButton(
            self.tr("Fermer ET supprimer définitivement le dossier du "
                    "projet (fichiers importés, GeoPackages, coupes)."))
        layout.addWidget(keep_files)
        layout.addWidget(delete_files)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText(self.tr("Continuer"))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() != QDialog.Accepted:
            return
        if keep_files.isChecked():
            self._close_project(
                message=self.tr(
                    "Projet fermé — les fichiers sont conservés."))
            return

        # --- Suppression définitive : confirmation renforcée ---------------
        confirm = QMessageBox(self)
        confirm.setIcon(QMessageBox.Warning)
        confirm.setWindowTitle(self.tr("Suppression définitive"))
        confirm.setText(self.tr(
            "Le dossier suivant sera supprimé définitivement "
            "(action irréversible) :"))
        confirm.setInformativeText(
            project_dir or self.tr("(dossier introuvable)"))
        confirm.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        confirm.button(QMessageBox.Ok).setText(self.tr("Supprimer"))
        confirm.setCheckBox(
            self.tr("Je comprends que les fichiers de ce projet seront "
                    "définitivement supprimés."))
        confirm.button(QMessageBox.Ok).setEnabled(False)

        def _toggle_ok(_state):
            confirm.button(QMessageBox.Ok).setEnabled(
                confirm.checkBox().isChecked())

        confirm.checkBox().stateChanged.connect(_toggle_ok)
        if confirm.exec_() != QMessageBox.Ok:
            return
        ok, message = self.project.delete_project_folder()
        if not ok:
            QMessageBox.critical(
                self, self.tr("Suppression refusée"),
                self.tr("Le dossier n'a pas été supprimé :"
                        "\n{}").format(message))
            return
        self._close_project(
            message=self.tr("Projet supprimé — vous pouvez démarrer "
                            "un nouveau projet."))

    def step2_on_file_imported(self, ft):
        self._invalidate_generated_geometry()
        self.step2.step2_validate_all()
    def step2_validate_all(self):
        self.step2.step2_validate_all()
    def step2_on_data_edited(self, ft):
        """Invalidate generated geometry and revalidate after CSV edits."""
        self._invalidate_generated_geometry()
        labels = {
            "collar": self.tr("Collets"), "survey": self.tr("Déviations"),
            "litho": self.tr("Lithologie"), "assays": self.tr("Teneurs"),
            "alterations": self.tr("Altérations"),
            "mineralizations": self.tr("Minéralisations"),
        }
        self.status_label.setText(self.tr(
            "{} : données modifiées — régénérez les trajectoires 3D."
        ).format(labels.get(ft, ft)))
        self.step2.step2_validate_all()
    def _auto_generate_trajectories(self, bundle):
        """322/334 — chemin synchrone (petits projets), mesuré."""
        import time as _t
        _t0 = _t.perf_counter()
        step = float(self.project.config.get(
            "default_sampling_step", 20.0) or 20.0)
        out = compute_auto_trajectories(bundle, step)
        from ..core.diagnostics import record_timing
        record_timing("open: trajectories (sync)",
                      _t.perf_counter() - _t0)
        return out

    def _start_traj_worker(self, bundle):
        """334 — lance le worker trajectoires (gros projets)."""
        if getattr(self, "_traj_worker", None) is not None:
            return
        step = float(self.project.config.get(
            "default_sampling_step", 20.0) or 20.0)
        self._traj_abandoned = False   # 336
        self._traj_worker = _TrajWorker334(bundle, step, self)
        self._traj_worker.finished.connect(self._on_traj_done)
        self._traj_worker.start()

    def _on_traj_done(self):
        """334/336 — retour worker : application côté GUI, SAUF si le
        projet a été fermé/réinitialisé entre-temps (le résultat est
        jeté — plus de figeage après fermeture)."""
        w = getattr(self, "_traj_worker", None)
        self._traj_worker = None
        if w is None:
            return
        if getattr(self, "_traj_abandoned", False) or self.project is None:
            from ..core.diagnostics import record_timing
            record_timing("open: worker discarded (closed)", 0.0)
            return
        dhs = w.result or []
        if dhs:
            self._apply_restored_drillholes(dhs, "auto", True)

    def _apply_restored_drillholes(self, dhs, dhs_source, restored):
        """334 — bloc d'application extrait de load_existing_project,
        partagé chemin synchrone / worker."""
        if restored:
            for drillhole in dhs:
                if dhs_source != "gpkg":
                    drillhole.litho = self.import_bundle.litho.get(
                        drillhole.hole_id, [])
                    drillhole.assays = self.import_bundle.assays.get(
                        drillhole.hole_id, [])
                drillhole.alterations = self.import_bundle.alterations.get(
                    drillhole.hole_id, [])
                drillhole.mineralizations = self.import_bundle.mineralizations.get(
                    drillhole.hole_id, [])
                drillhole.structure = self.import_bundle.structure.get(
                    drillhole.hole_id, [])
                drillhole.imagery = self.import_bundle.imagery.get(
                    drillhole.hole_id, [])
                drillhole.geotech = self.import_bundle.geotech.get(
                    drillhole.hole_id, [])
        self.set_drillholes(dhs)
        self.create_qgis_layers(persist=False)
        self.setup_selection_sync()
        self.step3.show_drillholes(
            dhs, self.tr("{} forages restaurés depuis le GeoPackage.")
            .format(len(dhs)))
        section_count = self.restore_saved_sections(dhs)
        saved_step = self.project.get_step() - 1
        target_step = min(max(saved_step, 2), 3)
        self._step_valid = [True, True, True, bool(section_count)]
        self._current_step = target_step
        self._update_step()
        return section_count   # 335 — utilisé par le message d'état

    def get_import_bundle(self):
        return self.step2.get_bundle()

    # --- Step 3 ---
    def set_drillholes(self, dhs):
        self.drillholes = dhs
        if self.section_widget:
            self.section_widget.set_drillholes(dhs)
    def get_drillholes(self):
        return self.drillholes

    def _assay_style_with_reference(self, style):
        enriched = dict(style or {})
        if not self.project:
            return enriched
        element = enriched.get("element")
        entry = self.project.get_reference_repository().get_entry(
            "assay_elements", element) if element else None
        if entry:
            enriched["precision"] = entry.precision
            enriched["unit"] = entry.source_unit
        return enriched

    def create_qgis_layers(self, persist=True):
        from ..core.layers import setup_all_layers
        if not self.project or not self.drillholes:
            return None
        # Replace the previous generated set without dereferencing stale SIP
        # wrappers left by a QGIS project close/reload.
        self._remove_generated_layers()
        crs = self.step1.get_crs()
        elem = self.step2.get_assay_element_columns()
        if not elem:
            elem = sorted({
                key for dh in self.drillholes for iv in dh.assays
                for key, value in iv.attributes.items()
                if isinstance(value, (int, float))
            })
        litho_c = self.project.get_litho_styles()
        assay_s = self._assay_style_with_reference(
            self.project.get_assay_style())
        result = setup_all_layers(
            self.project.config.get("project_name", "DrillMaster"),
            self.project.paths.geometry_gpkg,
            self.project.paths.data_gpkg,
            crs, self.drillholes, elem, litho_c, assay_s,
            save_gpkg=persist,
            domain_style_resolver=self.project.resolve_category_style)
        combined_ext = None
        if isinstance(result, tuple) and len(result) == 3:
            self.layers, combined_ext, self.last_gpkg_report = result
        elif isinstance(result, tuple) and len(result) == 2:
            self.layers, combined_ext = result
            self.last_gpkg_report = None
        else:
            self.layers = result
            self.last_gpkg_report = None
        self._apply_assay_field_aliases()
        if combined_ext is not None:
            self.iface.mapCanvas().setExtent(combined_ext)
            self.iface.mapCanvas().refresh()
        return self.last_gpkg_report

    def _apply_assay_field_aliases(self):
        """Expose reference labels/units in QGIS without renaming fields."""
        layer = self.layers.get("assays")
        if not self._layer_alive(layer) or not self.project:
            return
        repository = self.project.get_reference_repository()
        domain = repository.domains.get("assay_elements")
        if not domain:
            return
        for entry in domain.entries.values():
            index = layer.fields().indexOf(entry.raw_code)
            if index < 0:
                continue
            alias = entry.label or entry.raw_code
            if entry.symbol and entry.symbol.casefold() not in alias.casefold():
                alias = f"{alias} ({entry.symbol})"
            if entry.source_unit:
                alias = f"{alias} — {entry.source_unit}"
            layer.setFieldAlias(index, alias)

    def update_assay_layer_style(self, style):
        """Apply the section grade-map settings to the QGIS assay layer."""
        style = self._assay_style_with_reference(style)
        layer = self.layers.get("assays")
        if not self._layer_alive(layer):
            self.layers.pop("assays", None)
            return
        from ..core.styles import create_assay_style
        element = style.get("element")
        field_names = [f.name() for f in layer.fields()]
        if element not in field_names:
            return
        values = []
        for dh in self.drillholes:
            for iv in dh.assays:
                value = iv.attributes.get(element)
                if isinstance(value, (int, float)):
                    values.append(value)
        layer.setRenderer(create_assay_style(element, values, style))
        layer.triggerRepaint()
        if self.iface:
            self.iface.mapCanvas().refresh()

    def update_litho_layer_style(self):
        """Refresh map lithology colours after an edit in the side panel."""
        layer = self.layers.get("litho")
        if not self._layer_alive(layer) or not self.project:
            self.layers.pop("litho", None)
            return
        from ..core.styles import create_litho_style
        from ..core.section import get_all_litho_codes
        layer.setRenderer(create_litho_style(
            get_all_litho_codes(self.drillholes),
            self.project.get_litho_styles(),
        ))
        layer.triggerRepaint()
        if self.iface:
            self.iface.mapCanvas().refresh()

    # --- v2.7.4 — Altérations / Minéralisations : same instant repaint ---

    def _alteration_codes(self):
        codes = set()
        for dh in self.drillholes or []:
            for iv in getattr(dh, "alterations", []) or []:
                component_codes = [c.raw_code for c in (iv.components or [])
                                   if c.raw_code]
                if component_codes:
                    codes.update(component_codes)
                else:
                    value = str(iv.attributes.get("alteration", "") or "")
                    if value.strip():
                        codes.add(value)
        return sorted(codes, key=str.casefold)

    def _mineralization_style_codes(self):
        codes = {
            str(iv.attributes.get("mineralization_style", "") or "")
            for dh in self.drillholes or []
            for iv in getattr(dh, "mineralizations", []) or []}
        return sorted((c for c in codes if c.strip()), key=str.casefold)

    def _structure_type_codes(self):
        codes = {
            str(st.type or "").strip()
            for dh in self.drillholes or []
            for st in getattr(dh, "structure", []) or []}
        return sorted((c for c in codes if c.strip()), key=str.casefold)

    def update_structure_layer_style(self):
        """Refresh the ``Structures`` point layer from the Référentiel."""
        codes = self._structure_type_codes()
        if not codes:
            return
        layer = self.layers.get("structure")
        if not self._layer_alive(layer):
            self.layers.pop("structure", None)
            return
        from ..core.styles import create_structure_style
        styles = {}
        for code in codes:
            resolved = self.project.resolve_category_style("structure", code)
            styles[code] = {
                "color": ("" if getattr(resolved, "visible", True) is False
                          else (getattr(resolved, "color", "") or "")),
                "label": getattr(resolved, "label", "") or code,
                "visible": bool(getattr(resolved, "visible", True)),
                "pattern": getattr(resolved, "pattern", "") or "",
            }
        layer.setRenderer(create_structure_style(codes, styles))
        layer.triggerRepaint()
        if self.iface:
            self.iface.mapCanvas().refresh()

    def update_domain_layer_style(self, layer_key, domain_key, field_name,
                                  codes):
        """Rebuild the categorized renderer of a coded-track QGIS layer
        from the fresh Référentiel — same instant-repaint contract as the
        lithology layer (feedback 18/08/2026)."""
        if not codes or not self.project:
            return
        layer = self.layers.get(layer_key)
        if not self._layer_alive(layer):
            self.layers.pop(layer_key, None)
            return
        from ..core.styles import create_domain_style
        from ..core.reference import MINERALIZATION_INK
        # v2.7.9.6 — les domaines à symbole sont dessinés en encre neutre
        # sur la carte (pas de fausse couleur), « transparent » compris :
        # la carte ne contredit jamais la coupe.
        symbol_domain = domain_key in (
            "mineralization_style", "minerals")
        styles = {}
        for code in codes:
            resolved = self.project.resolve_category_style(domain_key, code)
            # v2.7.9.7 — entrée décochée du Référentiel : invisible sur la
            # carte aussi (jamais de contradiction coupe/carte).
            if getattr(resolved, "visible", True) is False:
                colour = "#00000000"
            elif symbol_domain:
                if getattr(resolved, "symbol_id", "") == "none":
                    colour = "#00000000"  # transparent
                else:
                    colour = MINERALIZATION_INK
            else:
                colour = resolved.color or ""
            styles[code] = {
                "color": colour,
                "label": resolved.label or code,
                "pattern": "" if symbol_domain else (resolved.pattern or ""),
            }
        layer.setRenderer(create_domain_style(field_name, codes, styles))
        layer.triggerRepaint()
        if self.iface:
            self.iface.mapCanvas().refresh()

    def setup_selection_sync(self):
        layer = self.layers.get("collars")
        if not self._layer_alive(layer):
            self.layers.pop("collars", None)
            return
        layer.selectionChanged.connect(self._on_selection)

    def _on_selection(self, *_args):
        # v2.9.167 — DRAPEAU DE RÉENTRANCE : la sélection vient de la
        # CARTE → on propage vers 2D/3D, mais on NE RÉÉCRIT PAS la
        # sélection sur la carte (sinon la multi-sélection est réduite
        # à un seul forage par la rétro-synchro — retour écran : le
        # collapse des deux fonctionnalités v2.9.165 qui se marchent dessus).
        self._selection_from_map = True
        try:
            self._on_selection_impl(*_args)
        finally:
            self._selection_from_map = False

    def _on_selection_impl(self, *_args):
        layer = self.layers.get("collars")
        if not self._layer_alive(layer):
            self.layers.pop("collars", None)
            return
        sels = list(layer.getSelectedFeatures())
        if not sels:
            self.selected_hole_id = None
            self.workspace_state.set("selected_hole_id", None)
            self.workspace_state.set("selected_hole_ids", [])
            return
        # v2.9.165 — sélection MULTIPLE : TOUS les forages sélectionnés
        # sur la carte sont propagés (avant : seul le premier).
        hids = [str(s["hole_id"]).strip()
                for s in sels if s["hole_id"]]
        if not hids:
            self.selected_hole_id = None
            self.workspace_state.set("selected_hole_id", None)
            self.workspace_state.set("selected_hole_ids", [])
            return
        self.selected_hole_id = hids[-1]
        self.workspace_state.set("selected_hole_id", hids[-1])
        self.workspace_state.set("selected_hole_ids", hids)

    def _select_on_map(self, hole_ids):
        """v2.9.165 — rétro-synchro 2D/3D → carte QGIS.

        Sélectionne les forages sur la couche collets quand ils sont
        sélectionnés dans la coupe 2D ou la vue 3D (retour écran :
        « la synchro doit se faire partout : carte, 2D, 3D »).
        Le signal ``selectionChanged`` est BLOQUÉ pendant l'opération
        pour éviter la boucle infinie (carte → workspace → carte).
        """
        layer = self.layers.get("collars")
        if not self._layer_alive(layer):
            return
        try:
            ids = list(hole_ids or [])
            # Cherche les feature IDs correspondant aux hole_ids
            expr = " OR ".join(
                f'"hole_id" = \'{hid}\'' for hid in ids) if ids else None
            if expr:
                from qgis.core import QgsFeatureRequest
                fids = [f.id() for f in layer.getFeatures(
                    QgsFeatureRequest().setFilterExpression(expr))]
                if fids:
                    # Bloque le signal pour éviter la boucle
                    layer.blockSignals(True)
                    layer.selectByIds(fids)
                    layer.blockSignals(False)
                else:
                    layer.blockSignals(True)
                    layer.removeSelection()
                    layer.blockSignals(False)
        except Exception as exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Carte QGIS : sélection rétro-synchrone "
                          "(2D/3D → carte)", exc)

    # --- Section signal handler ---
    def _on_section_signal(self, msg):
        if msg.startswith("DELETE:"):
            section_name = msg[7:]
            from qgis.core import QgsProject
            project = QgsProject.instance()
            for layer_id, layer in project.mapLayers().items():
                if layer.name() == section_name:
                    project.removeMapLayer(layer.id())
                    break

    # --- Step 4 ---
    def get_map_canvas(self):
        return self.iface.mapCanvas() if self.iface else None

    def get_map_unit_label(self):
        """Return the actual projected CRS distance unit abbreviation."""
        try:
            from qgis.core import QgsUnitTypes
            label = QgsUnitTypes.toAbbreviatedString(
                self.step1.get_crs().mapUnits())
            if label:
                return label
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("main_dock : get_map_unit_label", _exc)
            # Any unit lookup failure falls back to the configured unit.
            # Nothing to answer or surface here (best-effort label).
            pass
        return "ft" if (self.project and self.project.config.get("units") == "feet") else "m"

    def update_section_buffer_preview(self, line, distance, visible=True):
        """Draw the finite P1-P2 buffer corridor as a translucent map overlay."""
        canvas = self.get_map_canvas()
        if not canvas:
            return
        if self._buffer_band is None:
            from qgis.gui import QgsRubberBand
            from qgis.core import QgsWkbTypes
            from qgis.PyQt.QtGui import QColor
            self._buffer_band = QgsRubberBand(
                canvas, QgsWkbTypes.PolygonGeometry)
            try:
                self._buffer_band.setStrokeColor(QColor(28, 40, 51, 210))
                self._buffer_band.setFillColor(QColor(28, 40, 51, 45))
            except AttributeError:
                self._buffer_band.setColor(QColor(28, 40, 51, 80))
            self._buffer_band.setWidth(1)
        self._buffer_band.reset()
        if not visible or not line:
            canvas.refresh()
            return
        from qgis.core import QgsGeometry, QgsPointXY
        centreline = QgsGeometry.fromPolylineXY([
            QgsPointXY(line.x1, line.y1), QgsPointXY(line.x2, line.y2)])
        corridor = centreline.buffer(float(distance), 12)
        self._buffer_band.setToGeometry(corridor, None)
        canvas.refresh()

    def clear_map_overlays(self):
        if self._buffer_band is not None:
            self._buffer_band.reset()
            try:
                self._buffer_band.deleteLater()
            except AttributeError:
                canvas = self.get_map_canvas()
                if canvas:
                    canvas.scene().removeItem(self._buffer_band)
            self._buffer_band = None

    def get_section_widget(self):
        return self.section_widget
    def show_section_tab(self):
        if self.visualization_dock:
            self.visualization_dock.show_section_view()

    def create_section_line_layer(self, p1, p2, name=None):
        from ..core.layers import create_section_line_layer, GROUP_SECTIONS, get_or_create_root_group
        if not self.project:
            return
        crs = self.step1.get_crs()
        root = get_or_create_root_group(self.project.config.get("project_name", "DrillMaster"))
        sg = root.findGroup(GROUP_SECTIONS)
        if sg is None:
            sg = root.addGroup(GROUP_SECTIONS)
        create_section_line_layer(((p1[0], p1[1]), (p2[0], p2[1])), crs, sg, layer_name=name)

    def rename_section_layer(self, old_name, new_name):
        """Keep a renamed history row and its QGIS line layer in sync."""
        from qgis.core import QgsProject
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == old_name:
                layer.setName(new_name)
                break
        if self.step4._line and self.step4._line.name == old_name:
            self.step4._line.name = new_name
            self.step4.line_status.setText(
                f"{new_name}  |  {self.step4._line.summary}")

    def restore_saved_sections(self, dhs=None):
        """Restore step-4 history and its QGIS line layers from config."""
        if not self.project:
            return 0
        records = self.project.get_sections()
        if self.section_widget:
            self.section_widget.restore_sections(records, dhs or [])
        from qgis.core import QgsProject
        existing_names = {
            layer.name() for layer in QgsProject.instance().mapLayers().values()
        }
        for record in records:
            if record.get("name") in existing_names:
                continue
            try:
                self.create_section_line_layer(
                    (float(record["x1"]), float(record["y1"])),
                    (float(record["x2"]), float(record["y2"])),
                    name=record.get("name"),
                )
                existing_names.add(record.get("name"))
            except (KeyError, TypeError, ValueError):
                continue
        return len(records)

    # --- Load existing project with FULL restore (steps 2 + 3) ---
    def _on_language_changed(self, code):
        """v2.9.227/234 — bascule de langue demandée par l'étape 1.
        v2.9.234 — RECONSTRUCTION COMPLÈTE (choix lead) : les widgets
        déjà construits gardent leur texte (Qt ne ré-appelle pas
        tr()).  Détruire et reconstruire les docks est plus simple
        et plus honnête que 300 lignes de retranslate() manuel —
        le démarreur repasse, tout arrive dans la nouvelle langue."""
        from ..core.i18n import set_language, save_language_setting
        save_language_setting(code)
        set_language(code)
        cb = getattr(self, "_rebuild_callback", None)
        if cb is not None:
            try:
                cb()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Changement de langue : reconstruction "
                              "des docks (effet au prochain "
                              "démarrage)", _exc)
        else:
            self.retranslate()      # repli : au moins les titres

    def retranslate(self):
        """v2.9.227 — Lot 1a : ré-applique les textes traduits."""
        from qgis.PyQt.QtCore import QCoreApplication as _QCA
        self.setWindowTitle(_QCA.translate(
            "MainDock", "DrillMaster — Contrôle · Données & Coupes"))
        if getattr(self, "visualization_dock", None):
            self.visualization_dock.retranslate()

    def prepare_startup(self) -> bool:
        """v2.9.222 — PRÉPARATION AU DÉMARRAGE (retour écran : « le
        démarrage doit permettre au plugin de se préparer et éviter
        d'être lent »).  Rouvre le DERNIER projet (CSV + GeoPackage
        — le vrai travail lourd) si : (1) la case « Réouvrir le
        dernier projet » est cochée (défaut : oui, étape 1), (2) le
        dossier existe encore.  Retourne True si un projet est prêt.
        Jamais d'exception : un projet manquant = démarrage à vide,
        exactement comme avant."""
        import os
        try:
            from qgis.PyQt.QtCore import QSettings
            settings = QSettings()
            if not settings.value(
                    "DrillMaster/reopen_last_project", True, type=bool):
                return False
            last = str(settings.value("DrillMaster/last_project_dir",
                                      "") or "")
            if not last or not os.path.isdir(last):
                return False
            self.load_existing_project(last)
            return True
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Démarrage : préparation du dernier projet "
                          "(démarrage à vide)", _exc)
            return False

    def load_existing_project(self, project_ref):
        """Restore a project selected either by folder path or legacy name."""
        import os
        self.project = DrillMasterProject()
        if os.path.isdir(project_ref):
            opened = self.project.load(project_ref)
        else:
            opened = self.project.open_by_name(project_ref)
        if not opened:
            self._update_project_tools()
            self.status_label.setText(self.tr(
                "Projet '{}' introuvable ou configuration illisible."
            ).format(project_ref))
            return
        name = self.project.config.get("project_name", os.path.basename(project_ref))
        # v2.9.222 — MÉMORISATION du dernier projet (préparation au
        # démarrage) : QSettings, pas dans le projet — c'est un fait
        # de SESSION utilisateur, pas une propriété du gisement.
        try:
            from qgis.PyQt.QtCore import QSettings
            QSettings().setValue(
                "DrillMaster/last_project_dir",
                self.project.paths.project_dir)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Projet : mémorisation du dernier projet "
                          "(réouverture au démarrage désactivée)", _exc)
        self._update_project_tools()
        self.workspace_state.set("project_path", self.project.paths.project_dir)
        self.workspace_state.set("project_name", name)
        self._reset_session_state()
        if self.section_widget:
            self.section_widget.load_project_settings()
            self.section_widget.set_style_resolver(
                self.project.resolve_category_style)
            # v2.9.306 — ouverture : si type étiré et exag encore <= 1,
            # rendre l'effet visible (un réglage manuel est respecté).
            _g = ((self.project.config or {}).get("display_profiles")
                  or {}).get("global")
            if _g in ("AUGER", "PUITS") and float(
                    getattr(self.section_widget.canvas, "_v_exag", 1.0)
                    or 1.0) <= 1.0:
                self.section_widget._auto_vertical_exag()
        if getattr(self, "visualization_dock", None):
            self.visualization_dock.sync_context()

        # ---- Restore step 1 fields ----
        self.step1.name_edit.setText(name)
        self.step1.project_dir_edit.setText(self.project.base_dir)
        crs_id = self.project.config.get("crs", "")
        if crs_id:
            from qgis.core import QgsCoordinateReferenceSystem
            self.step1.crs_widget.setCrs(QgsCoordinateReferenceSystem(crs_id))
        self.step1.units_combo.setCurrentIndex(0 if self.project.config.get("units", "meters") == "meters" else 1)
        self.step1.step_spin.setValue(self.project.config.get("default_sampling_step", 20.0))

        # ---- Restore step 2: re-parse the saved CSV copies ----
        restored = False
        try:
            restored = self.step2.restore_from_project()
        except Exception as e:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Main dock : restauration des imports du projet", e)
            self.status_label.setText(
                self.tr("Restauration des imports : {}").format(e))

        if restored:
            self.import_bundle = self.step2.get_bundle()

        # Prefer the already-computed GeoPackage. Reopening a project must not
        # silently launch the geometry task or overwrite its saved outputs.
        from ..core.layers import load_drillholes_from_gpkg
        import os
        geo_gpkg = self.project.paths.geometry_gpkg
        data_gpkg = self.project.paths.data_gpkg
        dhs = []
        dhs_source = ""
        if os.path.isfile(geo_gpkg):
            try:
                from qgis.core import QgsCoordinateReferenceSystem
                crs = QgsCoordinateReferenceSystem(crs_id) if crs_id else None
                # v2.9.286 — anciens projets : « positif = bas » par défaut
                conv = str(self.project.config.get(
                    "dip_convention", "historique"))
                dhs = load_drillholes_from_gpkg(
                    geo_gpkg, data_gpkg, crs, dip_convention=conv)
                if dhs:
                    dhs_source = "gpkg"
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Projet (sauvegarde/chargement) : load_existing_project", _exc)
                dhs = []
        # v2.9.322 — GeoPackage absent ou illisible : le cache JSON
        # (écrit à la génération) restaure les trajectoires ; à défaut,
        # génération SILENCIEUSE en mémoire (collets+déviations
        # suffisent).  Plus jamais « cliquez sur Générer » à la
        # réouverture tant que les données sont là.
        if not dhs and restored and self.import_bundle and getattr(
                self.import_bundle, "collars", None):
            from ..core.geometry_cache import load_geometry_cache
            dhs = load_geometry_cache(
                self.project, self.import_bundle.collars,
                self.import_bundle.surveys) or []
            if dhs:
                dhs_source = "cache"
            else:
                n_col = len(self.import_bundle.collars or {})
                if n_col > 150:
                    # 334 — gros projet : worker, ouverture immédiate
                    self._start_traj_worker(self.import_bundle)
                    dhs = []
                else:
                    dhs = self._auto_generate_trajectories(
                        self.import_bundle)
                    if dhs:
                        dhs_source = "auto"
        if dhs:
            # 334 — bloc extrait dans _apply_restored_drillholes.
            # 335 — FIX régression 334 : section_count vivait dans le
            # bloc extrait → UnboundLocalError au message d'état.
            section_count = self._apply_restored_drillholes(
                dhs, dhs_source, restored)
            self.status_label.setText(self.tr(
                "Projet '{}' chargé : {} forages et {} coupe(s) "
                "restaurés.").format(name, len(dhs), section_count))
            return

        if restored:
            section_count = self.restore_saved_sections([])
            self._step_valid = [True, True, False, bool(section_count)]
            self._current_step = 2
            self._update_step()
            n = len(self.import_bundle.collars)
            self.status_label.setText(self.tr(
                "Projet '{}' chargé : {} forages importés et {} "
                "coupe(s) retrouvées. Cliquez sur 'Générer les "
                "trajectoires 3D'.").format(name, n, section_count))
            return

        # ---- Nothing to restore: keep any saved section history visible ----
        section_count = self.restore_saved_sections([])
        saved = self.project.config.get("current_step", 1) - 1
        if 0 <= saved <= 3:
            self._current_step = min(saved, 1)  # never skip past import
            self._update_step()
        self.status_label.setText(self.tr(
            "Projet '{}' chargé : aucune donnée importée, {} coupe(s) "
            "retrouvées.").format(name, section_count))
