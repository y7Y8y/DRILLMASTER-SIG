"""Progressive editor for lithology file structure profiles."""
from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QStackedWidget, QTableWidget,
    QVBoxLayout, QWidget,
)

from ..core.data_registry import ComponentColumn, ImportStructureProfile
from .styles_qt import (
    apply_combo_popup_style, BUTTON_SECONDARY, INPUT_STYLE, TABLE_STYLE,
    TOOLTIP_STYLE, make_collapsible_help,
)


class LithologyStructureDialog(QDialog):
    """Describe structure explicitly; never rewrite a source value."""

    MODES = (
        ("Une lithologie par intervalle (standard)", "standard"),
        ("Plusieurs colonnes sur une ligne (organisation large)",
         "wide_components"),
        ("Plusieurs codes dans une cellule", "delimited_components"),
        # v2.7.11.0 — le mode « lignes répétées par intervalle » est
        # retiré (directive du jour : « une règle, un format large »).
    )
    MODE_EXPLANATIONS = {
        "standard": (
            "Une ligne = un intervalle principal. Exemple : "
            "0–5 | DIORITE."),
        "wide_components": (
            "Une ligne = un intervalle complet ; plusieurs colonnes portent "
            "les composants. Exemple : 0–5 | DIORITE | QTZ | SULF."),
        "delimited_components": (
            "Une cellule contient plusieurs codes. Exemple : "
            "DIORITE/QTZ_VEIN. La séparation n'est appliquée qu'après validation."),
    }
    ROLES = (
        ("Non défini", ""), ("Principal", "primary"),
        ("Secondaire", "secondary"), ("Veine", "vein"),
        ("Accessoire", "accessory"),
    )

    def __init__(self, headers, profile=None, rows=None, mappings=None,
                 parent=None):
        super().__init__(parent)
        # v2.7.12.8 — infobulles lisibles dans le dialogue (cascade racine).
        self.setStyleSheet(TOOLTIP_STYLE)
        self.headers = list(headers or [])
        self.rows = list(rows or [])
        self.forbidden_component_columns = {
            raw for raw, canonical in (mappings or {}).items()
            if canonical in {"hole_id", "from", "to"}
        }
        self.initial = ImportStructureProfile.from_dict(profile)
        self._build()
        self._load(self.initial)

    def _build(self):
        self.setWindowTitle(self.tr("Organisation des lithologies"))
        self.resize(720, 470)
        layout = QVBoxLayout(self)
        intro = QLabel(
            self.tr("Option avancée : utilisez-la seulement si "
                    "l’organisation détectée ne correspond pas à votre "
                    "fichier. Aucune cellule du CSV ne sera modifiée."))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel(self.tr("Comment les lithologies sont-elles enregistrées ?")))
        self.mode_combo = QComboBox()
        for label, key in self.MODES:
            self.mode_combo.addItem(self.tr(label), key)
        self.mode_combo.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.mode_combo)
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        mode_row.addWidget(self.mode_combo, 1)
        layout.addLayout(mode_row)

        self._mode_help = make_collapsible_help("")
        self.mode_explanation = self._mode_help._help_body
        layout.addWidget(self._mode_help)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._standard_page())
        self.pages.addWidget(self._wide_page())
        self.pages.addWidget(self._delimited_page())
        layout.addWidget(self.pages, 1)

        self.proportion_unit_widget = QWidget()
        unit_row = QHBoxLayout(self.proportion_unit_widget)
        unit_row.setContentsMargins(0, 0, 0, 0)
        unit_row.addWidget(QLabel(self.tr("Comment les proportions sont-elles écrites ?")))
        self.proportion_unit = QComboBox()
        self.proportion_unit.addItem(
            self.tr("Pourcentage de 0 à 100"), "percent")
        self.proportion_unit.addItem(self.tr("Fraction de 0 à 1"), "fraction")
        self.proportion_unit.addItem(self.tr("Aucune proportion ou unité inconnue"), "unknown")
        self.proportion_unit.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.proportion_unit)
        unit_row.addWidget(self.proportion_unit, 1)
        layout.addWidget(self.proportion_unit_widget)

        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setObjectName("label_hint")
        layout.addWidget(self.preview)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(self.tr("Valider l’organisation"))
        buttons.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _mode_changed(self, index):
        if hasattr(self, "pages"):
            self.pages.setCurrentIndex(max(index, 0))
        mode = self.mode_combo.currentData()
        self.mode_explanation.setText(
            self.tr(self.MODE_EXPLANATIONS.get(mode, "")))
        if hasattr(self, "proportion_unit_widget"):
            self.proportion_unit_widget.setVisible(
                mode == "wide_components")
        if hasattr(self, "preview"):
            self.preview.setVisible(mode == "delimited_components")
        if mode == "delimited_components":
            self._update_preview()

    def _header_combo(self, allow_empty=True):
        combo = QComboBox()
        if allow_empty:
            combo.addItem(self.tr("— Aucune —"), "")
        for header in self.headers:
            combo.addItem(header, header)
        combo.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(combo)
        return combo

    def _role_combo(self):
        combo = QComboBox()
        for label, key in self.ROLES:
            combo.addItem(self.tr(label), key)
        combo.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(combo)
        return combo

    def _standard_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.standard_code = self._header_combo()
        form.addRow(self.tr("Colonne lithologique"), self.standard_code)
        form.addRow(make_collapsible_help(
            self.tr("Chaque ligne représente un intervalle principal "
                    "complet. Les supports répétés restent des doublons.")))
        return page

    def _wide_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(make_collapsible_help(
            self.tr("Ajoutez autant de composants que nécessaire. Une ligne "
                    "reste un intervalle complet, même avec plusieurs "
                    "colonnes lithologiques.")))
        self.components_table = QTableWidget(0, 3)
        self.components_table.setHorizontalHeaderLabels([
            self.tr("Colonne du code"), self.tr("Rôle"),
            self.tr("Colonne de proportion")])
        self.components_table.setStyleSheet(TABLE_STYLE)
        self.components_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.components_table)
        actions = QHBoxLayout()
        add = QPushButton(self.tr("Ajouter un composant"))
        add.setStyleSheet(BUTTON_SECONDARY)
        add.clicked.connect(
            lambda _checked=False: self._add_component())
        actions.addWidget(add)
        remove = QPushButton(self.tr("Retirer le composant sélectionné"))
        remove.setStyleSheet(BUTTON_SECONDARY)
        remove.clicked.connect(self._remove_component)
        actions.addWidget(remove)
        actions.addStretch()
        layout.addLayout(actions)
        return page

    def _delimited_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.delimited_code = self._header_combo()
        self.delimiter = QLineEdit("/")
        self.delimiter.setMaxLength(4)
        self.delimiter.setStyleSheet(INPUT_STYLE)
        self.first_role = QComboBox()
        self.first_role.addItem(self.tr("Aucune hiérarchie supposée"), "")
        self.first_role.addItem(
            self.tr("Premier composant principal, suivants secondaires"), "primary")
        self.first_role.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.first_role)
        form.addRow(self.tr("Colonne lithologique"), self.delimited_code)
        form.addRow(self.tr("Séparateur"), self.delimiter)
        form.addRow(self.tr("Convention"), self.first_role)
        form.addRow(make_collapsible_help(
            self.tr("Un aperçu est affiché avant validation. Le caractère "
                    "« _ » est interdit comme séparateur automatique.")))
        self.delimiter.textChanged.connect(self._update_preview)
        self.delimited_code.currentIndexChanged.connect(self._update_preview)
        return page

    def _add_component(self, definition=None):
        # QPushButton.clicked transmet ``checked: bool`` au slot. Ce booléen
        # n'est pas une définition de composant et doit être ignoré.
        if isinstance(definition, bool):
            definition = None
        # v2.7.11.1 — CM-03 : plafond géologique/lisibilité (1 primaire +
        # 3 secondaires) — refus expliqué, jamais de troncation.
        from ..core.component_caps import MAX_LITHOLOGY_COMPONENTS
        if self.components_table.rowCount() >= MAX_LITHOLOGY_COMPONENTS:
            QMessageBox.information(
                self, self.tr("Organisation des lithologies"),
                self.tr("Maximum {} composants par intervalle "
                        "(1 principal + 3 secondaires — arbitrage CM-03 "
                        "du 21/08/2026). Au-delà, réunissez ces "
                        "composants dans le fichier source ; aucun "
                        "composant ne serait tronqué silencieusement.")
                .format(MAX_LITHOLOGY_COMPONENTS))
            return
        definition = ComponentColumn.from_dict(definition or {})
        row = self.components_table.rowCount()
        self.components_table.insertRow(row)
        code = self._header_combo()
        role = self._role_combo()
        proportion = self._header_combo()
        code_index = code.findData(definition.code_column)
        if code_index >= 0:
            code.setCurrentIndex(code_index)
        role_index = role.findData(definition.role)
        if role_index >= 0:
            role.setCurrentIndex(role_index)
        proportion_index = proportion.findData(definition.proportion_column)
        if proportion_index >= 0:
            proportion.setCurrentIndex(proportion_index)
        self.components_table.setCellWidget(row, 0, code)
        self.components_table.setCellWidget(row, 1, role)
        self.components_table.setCellWidget(row, 2, proportion)

    def _remove_component(self, *_args):
        row = self.components_table.currentRow()
        if row >= 0:
            self.components_table.removeRow(row)

    @staticmethod
    def _set_combo(combo, value):
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _load(self, profile):
        self._set_combo(self.mode_combo, profile.mode)
        self._set_combo(self.proportion_unit, profile.proportion_unit)
        self._set_combo(self.standard_code, profile.code_column)
        self._set_combo(self.delimited_code, profile.code_column)
        self.delimiter.setText(profile.delimiter or "/")
        self._set_combo(self.first_role, profile.first_component_role)
        self.components_table.setRowCount(0)
        for component in profile.component_columns:
            self._add_component(component)
        if not profile.component_columns:
            candidate = profile.code_column or next((
                header for header in self.headers
                if header not in self.forbidden_component_columns), "")
            self._add_component(ComponentColumn(candidate, "primary"))
        self._mode_changed(self.mode_combo.currentIndex())
        self._update_preview()

    def profile(self):
        mode = self.mode_combo.currentData()
        profile = ImportStructureProfile(
            mode=mode,
            proportion_unit=self.proportion_unit.currentData(),
            confirmed=True,
            confidence=1.0)
        if mode == "standard":
            profile.code_column = self.standard_code.currentData()
        elif mode == "wide_components":
            for row in range(self.components_table.rowCount()):
                profile.component_columns.append(ComponentColumn(
                    code_column=self.components_table.cellWidget(
                        row, 0).currentData(),
                    role=self.components_table.cellWidget(
                        row, 1).currentData(),
                    proportion_column=self.components_table.cellWidget(
                        row, 2).currentData()))
        else:
            profile.code_column = self.delimited_code.currentData()
            profile.delimiter = self.delimiter.text()
            profile.first_component_role = self.first_role.currentData()
        return profile

    def _update_preview(self, *_args):
        if not hasattr(self, "delimited_code"):
            return
        header = self.delimited_code.currentData()
        delimiter = self.delimiter.text()
        try:
            column = self.headers.index(header)
        except ValueError:
            self.preview.setText(self.tr(""))
            return
        examples = []
        for row in self.rows:
            if column >= len(row):
                continue
            raw = row[column]
            if delimiter and delimiter in raw:
                examples.append(
                    f"{raw} → {' | '.join(value.strip() for value in raw.split(delimiter))}")
            if len(examples) == 3:
                break
        self.preview.setText(
            self.tr("Aperçu : {}").format(" ; ".join(examples))
            if examples else
            self.tr("Aucune valeur à séparer dans l’aperçu actuel."))

    def _validate_and_accept(self, *_args):
        profile = self.profile()
        if profile.mode == "wide_components":
            codes = [component.code_column for component in profile.component_columns]
            if not codes or any(not code for code in codes):
                QMessageBox.warning(
                    self, self.tr("Organisation incomplète"),
                    self.tr("Chaque composant doit posséder une colonne de code."))
                return
            if len(codes) != len(set(codes)):
                QMessageBox.warning(
                    self, self.tr("Colonnes répétées"),
                    self.tr("Une colonne de code ne peut pas représenter deux composants."))
                return
        elif not profile.code_column:
            QMessageBox.warning(
                self, self.tr("Organisation incomplète"),
                self.tr("Choisissez la colonne contenant la lithologie."))
            return
        selected_codes = (
            [component.code_column for component in profile.component_columns]
            if profile.mode == "wide_components"
            else [profile.code_column])
        forbidden = self.forbidden_component_columns.intersection(selected_codes)
        if forbidden:
            QMessageBox.warning(
                self, self.tr("Colonne incompatible"),
                self.tr("Une colonne de forage ou de limite ne peut "
                        "pas servir de composant lithologique : {}.")
                .format(', '.join(sorted(forbidden))))
            return
        if profile.mode == "delimited_components":
            if not profile.delimiter or profile.delimiter == "_":
                QMessageBox.warning(
                    self, self.tr("Séparateur invalide"),
                    self.tr("Choisissez un séparateur explicite autre que « _ »."))
                return
            self._update_preview()
        self.accept()
