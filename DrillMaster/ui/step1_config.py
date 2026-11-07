"""
DrillMaster — Step 1: Project Configuration
"""
from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QDoubleSpinBox, QLabel, QGroupBox, QPushButton, QFileDialog, QMessageBox,
)
from qgis.gui import QgsProjectionSelectionWidget
from qgis.core import QgsCoordinateReferenceSystem

from .styles_qt import COLORS, INPUT_STYLE, BUTTON_SECONDARY, make_collapsible_help
from ..core.project import DEFAULT_BASE_DIR


class Step1Config(QWidget):
    validity_changed = pyqtSignal(bool)

    def __init__(self, main_dock, parent=None):
        super().__init__(parent)
        self.main_dock = main_dock
        self._build()
        self._connect()
        self._validate()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel(self.tr("Configuration du projet"))
        title.setObjectName("label_title")
        layout.addWidget(title)

        form_group = QGroupBox(self.tr("Paramètres"))
        form = QFormLayout(form_group)
        form.setSpacing(5)
        form.setContentsMargins(8, 6, 8, 6)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.tr("ex: Projet_Tintio"))
        self.name_edit.setStyleSheet(INPUT_STYLE)
        form.addRow(self.tr("Nom du projet *"), self.name_edit)

        folder_row = QWidget()
        folder_layout = QHBoxLayout(folder_row)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(5)
        self.project_dir_edit = QLineEdit(os.path.abspath(DEFAULT_BASE_DIR))
        self.project_dir_edit.setPlaceholderText(self.tr("Dossier parent des projets"))
        self.project_dir_edit.setStyleSheet(INPUT_STYLE)
        self.project_dir_edit.setToolTip(
            self.tr("Dossier parent · sous-dossier = nom projet"))
        # v2.7.12.7 — revue écran : le chemin long était tronqué à
        # l'écran (« ers\LENOVO\QGIS\… ») sans moyen de le lire en
        # entier ; l'infobulle porte désormais le chemin complet.
        self.project_dir_edit.textChanged.connect(self._dir_tooltip)
        folder_layout.addWidget(self.project_dir_edit, 1)
        self.project_dir_btn = QPushButton(self.tr("Parcourir"))
        self.project_dir_btn.setStyleSheet(BUTTON_SECONDARY)
        self.project_dir_btn.clicked.connect(self._browse_project_dir)
        folder_layout.addWidget(self.project_dir_btn)
        form.addRow(self.tr("Dossier du projet *"), folder_row)

        self.crs_widget = QgsProjectionSelectionWidget()
        self.crs_widget.setCrs(QgsCoordinateReferenceSystem("EPSG:32630"))
        self.crs_widget.setStyleSheet(INPUT_STYLE)
        form.addRow(self.tr("SCR (projeté) *"), self.crs_widget)

        self.crs_info = QLabel(self.tr(""))
        self.crs_info.setWordWrap(True)
        self.crs_info.setObjectName("label_hint")
        form.addRow("", self.crs_info)

        self.units_combo = QComboBox()
        self.units_combo.addItems([self.tr("Mètres (m)"), self.tr("Pieds (ft)")])
        self.units_combo.setStyleSheet(INPUT_STYLE)
        form.addRow(self.tr("Unités"), self.units_combo)
        # v2.9.296 — type de forage dès la création (« RC/DD, Auger,
        # Puits ») : écrit dans display_profiles.global à la création.
        self.hole_type_combo = QComboBox()
        for lab, val in ((self.tr("RC / DD"), "RC"),
                         (self.tr("Auger"), "AUGER"),
                         (self.tr("Puits"), "PUITS")):
            self.hole_type_combo.addItem(lab, val)
        form.addRow(self.tr("Type de forage"), self.hole_type_combo)

        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(0.1, 9999.0)
        self.step_spin.setValue(20.0)
        self.step_spin.setSuffix(" m")
        self.step_spin.setDecimals(1)
        self.step_spin.setStyleSheet(INPUT_STYLE)
        # v2.7.10.36 — le suffixe est synchronisé sur la combo Unités.
        # v2.7.12.7 — revue écran : pas de tag de version ni de jargon
        # (« suffixe ») dans le texte vu par l'utilisateur.
        self.step_spin.setToolTip(self.tr("Pas trajectoire 3D (m)"))
        form.addRow(self.tr("Pas d’échantillonnage"), self.step_spin)

        layout.addWidget(form_group)

        layout.addWidget(make_collapsible_help(self.tr(
            "Pas d'échantillonnage = découpage des trajectoires 3D en "
            "segments de cette longueur maximum (lissage entre stations "
            "de déviation).")))

        # v2.9.222 — PRÉPARATION AU DÉMARRAGE : réouvrir le dernier
        # projet pendant le démarreur (CSV + GeoPackage prêts à
        # l'arrivée).  Mémorisé dans QSettings — préférence session.
        self.reopen_check = QCheckBox(self.tr(
            "Réouvrir le dernier projet au démarrage"))
        try:
            from qgis.PyQt.QtCore import QSettings
            self.reopen_check.setChecked(QSettings().value(
                "DrillMaster/reopen_last_project", True, type=bool))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Étape 1 : lecture du réglage de réouverture "
                          "(défaut coché)", _exc)
            self.reopen_check.setChecked(True)
        self.reopen_check.setToolTip(
            self.tr("Le démarreur recharge le dernier projet "
                    "(données, géométrie) pour un atelier prêt à l'ouverture"))
        self.reopen_check.toggled.connect(self._save_reopen_setting)
        layout.addWidget(self.reopen_check)

        # v2.9.227 — Lot 1a : RÉGLAGE LANGUE (plan langue : étape 1,
        # mémorisé QSettings, jamais de question au démarrage).
        # Bascule À CHAUD : le traducteur est remplacé et les textes
        # câblés se ré-appliquent immédiatement (titres des docks,
        # onglets, démarreur) ; les autres suivent aux lots 2-5.
        lang_row = QHBoxLayout()
        lang_row.setSpacing(6)
        lang_lbl = QLabel(self.tr("Langue"))
        lang_lbl.setStyleSheet(
            "color: #566573; font-size: 8pt; background: transparent;")
        self.lang_combo = QComboBox()
        from ..core.i18n import LANGUAGE_LABELS, LANGUAGES
        for _code in LANGUAGES:
            self.lang_combo.addItem(LANGUAGE_LABELS[_code], _code)
        from ..core.i18n import load_language_setting
        _cur = load_language_setting()
        _idx = self.lang_combo.findData(_cur)
        self.lang_combo.setCurrentIndex(_idx if _idx >= 0 else 0)
        self.lang_combo.setToolTip(self.tr(
            "Langue de l'interface · mémorisée, jamais demandée au "
            "démarrage"))
        self.lang_combo.currentIndexChanged.connect(self._on_language)
        lang_row.addWidget(lang_lbl)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch(1)
        layout.addLayout(lang_row)

        open_btn = QPushButton(self.tr("Ouvrir un projet existant"))
        open_btn.setStyleSheet(BUTTON_SECONDARY)
        open_btn.clicked.connect(self._open_existing)
        # v2.7.12.7 — revue écran : ce bouton occupait la pleine largeur
        # (il ressemblait à l'action principale) ; c'est une action
        # secondaire → largeur au contenu, alignée à gauche. La note des
        # champs obligatoires était orpheline tout en bas (après le
        # stretch) — elle reste collée au formulaire.
        layout.addWidget(open_btn, 0, Qt.AlignLeft)

        note = QLabel(self.tr(
            "* Champs obligatoires. Le SCR doit être projeté (pas EPSG:4326)."))
        note.setObjectName("label_hint")
        layout.addWidget(note)

        layout.addStretch()

    def _connect(self):
        self.name_edit.textChanged.connect(self._validate)
        self.project_dir_edit.textChanged.connect(self._validate)
        self.crs_widget.crsChanged.connect(self._validate)
        # v2.7.10.36 — le suffixe du pas suit les unités (m ↔ pi).
        self.units_combo.currentIndexChanged.connect(
            lambda *_args: self._sync_step_suffix())

    def _on_language(self, index):
        """v2.9.227 — bascule de langue À CHAUD : mémorise, remplace
        le traducteur, ré-applique les textes câblés."""
        from ..core.i18n import save_language_setting
        code = self.lang_combo.itemData(index) or "fr"
        save_language_setting(code)
        cb = getattr(self, "on_language_changed", None)
        if cb:
            try:
                cb(code)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Étape 1 : changement de langue "
                              "(appliqué au prochain démarrage)", _exc)

    def _save_reopen_setting(self, checked):
        """v2.9.222 — le réglage vit dans QSettings (session)."""
        try:
            from qgis.PyQt.QtCore import QSettings
            QSettings().setValue("DrillMaster/reopen_last_project",
                                 bool(checked))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Étape 1 : enregistrement du réglage de "
                          "réouverture (non conservé)", _exc)

    def _sync_step_suffix(self):
        self.step_spin.setSuffix(
            " m" if self.units_combo.currentIndex() == 0 else " pi")

    def _project_name_collision(self, name, base_dir):
        """Un dossier projet portant ce nom existe déjà (avec config.json).

        Jamais pour le projet ACTUELLEMENT ouvert : retourner à l'étape 1
        d'un projet ouvert est de la navigation, pas une création —
        l'exempter évite de bloquer le bouton « Suivant » (B-02 comme
        école : on ne bloque jamais par erreur)."""
        from ..core.project import DrillMasterProject
        safe_name = DrillMasterProject._sanitise_name(name)
        candidate = os.path.join(base_dir, safe_name)
        if not os.path.isfile(os.path.join(candidate, "config.json")):
            return False
        current = self.main_dock.project
        current_dir = (
            os.path.abspath(current.paths.project_dir)
            if current and getattr(current, "paths", None) else "")
        return os.path.abspath(candidate) != current_dir

    def _validate(self):
        name = self.name_edit.text().strip()
        base_dir = self.project_dir_edit.text().strip()
        crs = self.crs_widget.crs()
        errors = []

        if not name:
            errors.append(self.tr("Nom du projet requis"))
        if not base_dir:
            errors.append(self.tr("Dossier du projet requis"))
        elif os.path.exists(base_dir) and not os.path.isdir(base_dir):
            errors.append(self.tr("Le chemin du projet pointe vers un fichier"))
        if not crs.isValid():
            errors.append(self.tr("SCR invalide"))
        elif crs.isGeographic():
            errors.append(self.tr(
                "'{}' est géographique; choisissez un SCR projeté"
            ).format(crs.authid()))
        # v2.7.10.36 — collision de nom vue EN DIRECT (le garde à la
        # création existe dans main_dock._create_project ; ici l'utilisateur
        # le sait avant « Suivant », pas après).
        if name and base_dir and self._project_name_collision(name, base_dir):
            errors.append(self.tr(
                "Un projet de ce nom existe déjà dans ce dossier — "
                "ouvrez-le ou changez le nom"))

        valid = not errors
        self.crs_info.setText(
            self.tr("SCR projeté: {}").format(crs.authid()) if valid
            else self.tr("Erreur: {}").format(" | ".join(errors)))
        self.crs_info.setStyleSheet(
            f"color: {COLORS['success']}; font-size: 9pt;" if valid
            else f"color: {COLORS['danger']}; font-size: 9pt;")
        self.validity_changed.emit(valid)

    def get_project_name(self):
        return self.name_edit.text().strip()

    def get_crs(self):
        return self.crs_widget.crs()

    def get_units(self):
        return "meters" if self.units_combo.currentIndex() == 0 else "feet"

    def get_hole_data_type(self):
        """v2.9.296 — choix du type de forage (« RC », « AUGER »…)."""
        return str(self.hole_type_combo.currentData() or "")

    def get_sampling_step(self):
        return self.step_spin.value()

    def get_project_base_dir(self):
        return os.path.abspath(os.path.expanduser(
            self.project_dir_edit.text().strip() or DEFAULT_BASE_DIR))

    def _dir_tooltip(self, text=""):
        """v2.7.12.7 — chemin complet dans l'infobulle (le champ le
        tronque à l'écran) + le rappel du sous-dossier projet."""
        if text:
            self.project_dir_edit.setToolTip(
                self.tr("{}\nSous-dossier = nom projet").format(text))
        else:
            self.project_dir_edit.setToolTip(
                self.tr("Dossier parent · sous-dossier = nom projet"))

    def _browse_project_dir(self, *_args):
        start = self.get_project_base_dir()
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Choisir le dossier parent des projets"), start)
        if path:
            self.project_dir_edit.setText(os.path.abspath(path))

    def _open_existing(self, *_args):
        start = self.get_project_base_dir()
        project_dir = QFileDialog.getExistingDirectory(
            self, self.tr("Choisir un dossier de projet DrillMaster"),
            start)
        if not project_dir:
            return
        if not os.path.isfile(os.path.join(project_dir, "config.json")):
            QMessageBox.warning(
                self, self.tr("Projet DrillMaster invalide"),
                self.tr("Le dossier sélectionné ne contient pas de fichier config.json."))
            return
        self.main_dock.load_existing_project(project_dir)
