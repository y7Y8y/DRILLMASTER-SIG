"""
DrillMaster — Étape 3 : calcul des trajectoires
"""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
)
from qgis.core import QgsTask, QgsApplication

from ..core.data_model import DrillHole
from ..core.geometry import compute_trajectory, validate_trajectory
from ..core.validation import ImportBundle, auto_survey_for_vertical
from .styles_qt import COLORS, BUTTON_PRIMARY, PROGRESS_STYLE, TABLE_STYLE


class GeometrisationTask(QgsTask):
    def __init__(self, bundle, step):
        from qgis.PyQt.QtCore import QCoreApplication as _QCore
        super().__init__(_QCore.translate(
            "Step3Geometry", "DrillMaster — calcul des trajectoires"),
            QgsTask.CanCancel)
        self.bundle = bundle
        self.sampling_step = step
        self.drillholes = []
        self.errors = []
        self.warnings = []

    def run(self):
        ids = sorted(self.bundle.collars.keys())
        if not ids:
            self.errors.append(self.tr("Aucun collet importé."))
            return False
        for i, hid in enumerate(ids):
            if self.isCanceled():
                return False
            self.setProgress(int((i / len(ids)) * 100))
            c = self.bundle.collars[hid]
            sv = self.bundle.surveys.get(hid, [])
            if not sv:
                sv = auto_survey_for_vertical(c)
            traj = compute_trajectory(c, sv, subdivide=True, max_segment=self.sampling_step)
            errs = validate_trajectory(traj)
            if errs:
                for e in errs:
                    self.errors.append(f"{hid}: {e}")
                continue
            self.drillholes.append(DrillHole(
                hole_id=hid, collar=c, survey=sv,
                litho=self.bundle.litho.get(hid, []),
                assays=self.bundle.assays.get(hid, []),
                alterations=self.bundle.alterations.get(hid, []),
                mineralizations=self.bundle.mineralizations.get(hid, []),
                structure=self.bundle.structure.get(hid, []),
                imagery=self.bundle.imagery.get(hid, []),
                geotech=self.bundle.geotech.get(hid, []),
                trajectory=traj,
            ))
        self.setProgress(100)
        return len(self.errors) == 0


class Step3Geometry(QWidget):
    validity_changed = pyqtSignal(bool)

    def __init__(self, main_dock, parent=None):
        super().__init__(parent)
        self.main_dock = main_dock
        self.drillholes = []
        self._task = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel(self.tr("Calcul des trajectoires 3D"))
        title.setObjectName("label_title")
        layout.addWidget(title)

        desc = QLabel(self.tr(
            "Calcul des trajectoires à partir des mesures de "
            "déviation et création des couches QGIS."))
        desc.setObjectName("label_subtitle")
        # v2.7.12.10 — revue écran : sans wrap, cette phrase (≈ 743 px de
        # largeur mini) forçait l'étape 3 à 775 px de large — le dock
        # (340–480 px) ne la contenait pas et le contenu débordait.
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.run_btn = QPushButton(
            self.tr("Générer les trajectoires 3D"))
        self.run_btn.setStyleSheet(BUTTON_PRIMARY)
        self.run_btn.setMinimumHeight(28)
        self.run_btn.setToolTip(self.tr("Calculer trajectoires 3D"))
        self.run_btn.clicked.connect(self._run)
        layout.addWidget(self.run_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet(PROGRESS_STYLE)
        layout.addWidget(self.progress)

        rg = QGroupBox(self.tr("Forages traités"))
        # v2.7.12.10 — REVUE ÉCRAN : le QGroupBox a une politique verticale
        # Expanding par défaut — avec un addStretch en bas, le GROUPE
        # (pas le stretch) absorbait l'espace libre : 3 forages = ~350 px
        # de blanc sous le tableau dans le cadre. Politique Maximum : le
        # groupe épouse son contenu, le vide va dans le stretch.
        rg.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        rl = QVBoxLayout(rg)
        rl.setContentsMargins(5, 5, 5, 5)
        self.results_table = QTableWidget(0, 6)
        compact_headers = ["ID", "X", "Y", "Z",
                           self.tr("Prof."), self.tr("Long. 3D")]
        full_headers = [
            self.tr("ID forage"), self.tr("X collet"), self.tr("Y collet"),
            self.tr("Z collet"), self.tr("Profondeur"),
            self.tr("Longueur 3D"),
        ]
        self.results_table.setHorizontalHeaderLabels(compact_headers)
        for column, tooltip in enumerate(full_headers):
            self.results_table.horizontalHeaderItem(column).setToolTip(tooltip)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_table.setStyleSheet(TABLE_STYLE)
        # v2.7.12.10 — revue écran (« certains éléments prennent trop
        # d'espaces ») : avant, la table avait 140 px de HAUTEUR MINIMUM
        # et le groupe « Forages traités » prenait TOUT l'espace restant
        # (stretch 1) — 3 forages = ~400 px de blanc sous le tableau.
        # La table épouse ses lignes (plafond 240 px, défilement interne
        # au-delà), le groupe colle à son contenu, le vide repasse en bas
        # de l'étape.
        self.results_table.setMinimumHeight(0)
        # Largeurs par ResizeToContents (inchangé — c'est ce qui montrait
        # les 6 colonnes à la fois dans le dock) ; le défilement
        # horizontal interne (AsNeeded) reste en filet de sécurité :
        # jamais de nom d'en-tête rogné sans moyen de le lire.
        rl.addWidget(self.results_table)
        layout.addWidget(rg)

        self.log_label = QLabel(self.tr(
            "Cliquez sur le bouton pour calculer les trajectoires."))
        self.log_label.setWordWrap(True)
        self.log_label.setObjectName("label_hint")
        layout.addWidget(self.log_label)
        layout.addStretch()

    def _run(self, *_args):
        bundle = self.main_dock.get_import_bundle()
        if not bundle or not bundle.collars:
            self.log_label.setText(self.tr(
                "Aucune donnée importée. Retournez à l'étape 2."))
            self.log_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 9pt;")
            return

        self.run_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        step = 20.0
        if self.main_dock.project:
            step = self.main_dock.project.config.get("default_sampling_step", 20.0)
        self._task = GeometrisationTask(bundle, step)
        self._task.progressChanged.connect(lambda: self.progress.setValue(int(self._task.progress())))
        self._task.taskCompleted.connect(self._done)
        self._task.taskTerminated.connect(self._done)
        QgsApplication.taskManager().addTask(self._task)
        self.log_label.setText(self.tr("Calcul en cours..."))
        self.log_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 9pt;")

    @staticmethod
    def _interval_counts(drillholes):
        """Display-ordered (label, count) per interval domain — adding a
        future domain (structures, tables libres) is a one-line change."""
        from qgis.PyQt.QtCore import QCoreApplication as _QCore
        _t = lambda s: _QCore.translate("Step3Geometry", s)
        return [
            (_t("Lithologie"), sum(len(dh.litho) for dh in drillholes)),
            (_t("Teneurs"), sum(len(dh.assays) for dh in drillholes)),
            (_t("Altérations"),
             sum(len(dh.alterations) for dh in drillholes)),
            (_t("Minéralisations"),
             sum(len(dh.mineralizations) for dh in drillholes)),
        ]

    @staticmethod
    def _component_note(drillholes):
        additional = sum(
            max(len(interval.components) - 1, 0)
            for drillhole in drillholes for interval in drillhole.litho)
        if not additional:
            return ""
        from qgis.PyQt.QtCore import QCoreApplication as _QCore
        return _QCore.translate(
            "Step3Geometry",
            "Lithologie : {} composant(s) complémentaire(s) — rendu en "
            "coupe : principal pleine bande, veines fines superposées, "
            "secondaires en barre latérale.").format(additional)

    def show_drillholes(self, dhs, msg):
        """Display already-computed drillholes (project restore path)."""
        from ..core.step3_summary import build_step3_summary
        self.drillholes = dhs
        self.main_dock.set_drillholes(dhs)
        self._fill_results()
        self.run_btn.setText(
                self.tr("Régénérer les trajectoires 3D"))
        text = build_step3_summary(
            len(dhs),
            interval_counts=self._interval_counts(dhs),
            verb=self.tr("restaurés depuis le GeoPackage"),
            extra_note=self._component_note(dhs))
        self.log_label.setText(text)
        self.log_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 9pt; font-weight: bold;")
        self.validity_changed.emit(bool(dhs))

    @staticmethod
    def _display_layer_names(names):
        from qgis.PyQt.QtCore import QCoreApplication as _QCore
        _t = lambda s: _QCore.translate("Step3Geometry", s)
        translations = {
            "Survey": _t("Trajectoires"),
            "Survey_Stations": _t("Stations de déviation"),
            "Assays": _t("Teneurs"),
            "Lithologie": _t("Lithologie"),
            "Collets": _t("Collets"),
            "Alterations": _t("Altérations"),
            "Mineralizations": _t("Minéralisations"),
            "Structures": _t("Structures"),
        }
        return [translations.get(name, name) for name in (names or [])]

    def _done(self, *_args):
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)
        task = self._task
        self._task = None
        if not task:
            return
        if task.errors:
            self.log_label.setText(self.tr("Erreurs :\n{}").format(
                "\n".join(task.errors)))
            self.log_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 9pt;")
            self.validity_changed.emit(False)
            return

        self.drillholes = task.drillholes
        self.main_dock.set_drillholes(self.drillholes)
        # v2.9.322 — trajectoires persistées (JSON, indépendant de
        # QGIS) : la réouverture du projet les restaure sans jamais
        # redemander « Générer les trajectoires ».
        try:
            from ..core.geometry_cache import save_geometry_cache
            save_geometry_cache(self.main_dock.project, self.drillholes)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Étape 3 : écriture du cache de trajectoires",
                          _exc)
        self._fill_results()

        try:
            self.main_dock.create_qgis_layers()
        except Exception as e:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Étape 3 : création des couches QGIS", e)
            self.log_label.setText(self.tr(
                "Erreur de création des couches : {}").format(e))
            self.log_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 9pt;")
            self.validity_changed.emit(False)
            return

        self.main_dock.setup_selection_sync()
        n = len(self.drillholes)

        # Explicit GeoPackage save confirmation
        from ..core.step3_summary import build_step3_summary
        rep = self.main_dock.last_gpkg_report or {}
        if rep.get("errors"):
            gpkg_msg = self.tr(
                "GeoPackage: erreurs d’écriture — {}").format(
                "; ".join(rep["errors"]))
            gpkg_color = COLORS['danger']
            self.log_label.setText(
                self.tr("{} forages traités.\n{}").format(n, gpkg_msg))
            self.log_label.setStyleSheet(
                f"color: {gpkg_color}; font-size: 9pt; font-weight: bold;")
            self.run_btn.setText(
                self.tr("Régénérer les trajectoires 3D"))
            self.main_dock.status_label.setText(gpkg_msg)
            self.validity_changed.emit(True)
            return
        elif rep.get("geometry") or rep.get("data"):
            suffix = self.tr(" — GeoPackage sauvegardé ({}, {})").format(
                rep.get('geometry_file', 'geometry.gpkg'),
                rep.get('data_file', 'data.gpkg'))
            gpkg_msg = suffix.lstrip(" —")
            gpkg_color = COLORS['success']
        else:
            suffix = self.tr(" — GeoPackage: aucune couche à sauvegarder.")
            gpkg_msg = self.tr("GeoPackage: aucune couche à sauvegarder.")
            gpkg_color = COLORS['text_medium']

        text = build_step3_summary(
            n,
            geometry_layers=self._display_layer_names(
                rep.get("geometry", [])),
            data_layers=self._display_layer_names(rep.get("data", [])),
            interval_counts=self._interval_counts(self.drillholes),
            suffix=suffix,
            extra_note=self._component_note(self.drillholes))
        self.log_label.setText(text)
        self.log_label.setStyleSheet(
            f"color: {gpkg_color}; font-size: 9pt; font-weight: bold;")
        self.run_btn.setText(
                self.tr("Régénérer les trajectoires 3D"))
        self.main_dock.status_label.setText(gpkg_msg)
        self.validity_changed.emit(True)

    def _fill_results(self):
        self.results_table.setRowCount(len(self.drillholes))
        # v2.7.12.10 — hauteur qui épouse les lignes (en-tête + 21 px par
        # ligne, plafond 240 px → défilement interne au-delà) ; le groupe
        # « Forages traités » ne fait plus de grand vide sous 3 lignes.
        rows = max(1, len(self.drillholes))
        self.results_table.setMaximumHeight(min(240, 34 + 21 * rows))
        for r, dh in enumerate(self.drillholes):
            self.results_table.setItem(r, 0, QTableWidgetItem(dh.hole_id))
            self.results_table.setItem(r, 1, QTableWidgetItem(f"{dh.collar.x:.1f}"))
            self.results_table.setItem(r, 2, QTableWidgetItem(f"{dh.collar.y:.1f}"))
            self.results_table.setItem(r, 3, QTableWidgetItem(f"{dh.collar.z:.1f}"))
            self.results_table.setItem(r, 4, QTableWidgetItem(f"{dh.total_depth:.2f}"))
            self.results_table.setItem(r, 5, QTableWidgetItem(f"{dh.trajectory_length:.2f}"))

    def reset(self):
        self.drillholes = []
        self.results_table.setRowCount(0)
        self.results_table.setMaximumHeight(55)  # v2.7.12.10 — en-tête seul
        self.run_btn.setText(
                self.tr("Générer les trajectoires 3D"))
        self.log_label.setText(self.tr(
            "Cliquez sur le bouton pour calculer les trajectoires."))
        self.log_label.setObjectName("label_hint")
        self.validity_changed.emit(False)
