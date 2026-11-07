"""Dialogue d'organisation pour les pistes codées (altérations,
minéralisations) — v2.7.11.6, retour écran.

Pendant « Options avancées… » du dialogue lithologie : ces domaines n'ont
ni rôle ni proportion (AM-05), donc la boîte propose trois organisations
SIMPLES et lues ensuite par core.validation à l'identique :

- standard — une seule colonne de codes ;
- wide_components — plusieurs colonnes de codes par intervalle
  (Alteration_1, Alteration_2… ou Style1, Style2…), aucune autre donnée
  n'est demandée (l'intensité est lue par appairage de suffixe si des
  colonnes Int_k existent) ;
- delimited_components — une cellule porte plusieurs codes séparés par
  un caractère déclaré (« / » par défaut).

Aucune cellule du CSV n'est modifiée, jamais.
"""
from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QWidget,
)
from qgis.PyQt.QtCore import Qt

from ..core.component_caps import cap_for
from ..core.data_registry import ComponentColumn, ImportStructureProfile
from .styles_qt import (
    apply_combo_popup_style, INPUT_STYLE, TOOLTIP_STYLE, make_collapsible_help)


class DomainStructureDialog(QDialog):
    """Décrit l'organisation d'un fichier codé ; jamais de réécriture."""

    def __init__(self, file_type, headers, profile=None, parent=None):
        super().__init__(parent)
        # v2.7.12.8 — infobulles lisibles dans le dialogue (cascade racine).
        self.setStyleSheet(TOOLTIP_STYLE)
        from ..core.import_detect import FILE_TYPE_LABELS
        self.file_type = file_type
        self.headers = list(headers or [])
        self.initial = ImportStructureProfile.from_dict(profile)
        self.domain_label = self.tr(FILE_TYPE_LABELS.get(file_type, file_type))
        self._build()
        self._load(self.initial)

    # ------------------------------------------------------------------
    def _build(self):
        self.setWindowTitle(self.tr("Organisation — {}").format(self.domain_label))
        self.resize(560, 420)
        layout = QVBoxLayout(self)
        layout.addWidget(make_collapsible_help(
            self.tr("Aucune cellule du fichier source ne sera modifiée. "
                    "Ce choix dit seulement COMMENT les codes sont rangés "
                    "dans les colonnes.")))

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(
            self.tr("Une seule colonne de codes (standard)"), "standard")
        self.mode_combo.addItem(
            self.tr("Plusieurs colonnes de codes par intervalle (ex. "
                    "Alteration_1, Alteration_2)"), "wide_components")
        self.mode_combo.addItem(
            self.tr("Plusieurs codes dans UNE cellule, séparés par un "
                    "caractère (ex. CH/EP/SI)"), "delimited_components")
        self.mode_combo.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.mode_combo)
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        row = QFormLayout()
        row.addRow(self.tr("Organisation"), self.mode_combo)
        layout.addLayout(row)

        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)

        # — standard —
        p0 = QWidget()
        form0 = QFormLayout(p0)
        self.standard_code = QComboBox()
        self.standard_code.addItem(self.tr("— Automatique —"), "")
        for header in self.headers:
            self.standard_code.addItem(header, header)
        self.standard_code.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.standard_code)
        form0.addRow(self.tr("Colonne des codes"), self.standard_code)
        form0.addRow(make_collapsible_help(
            self.tr("Une ligne = un intervalle, un code. C'est le cas "
                    "simple et historique.")))
        self.pages.addWidget(p0)

        # — plusieurs colonnes —
        p1 = QWidget()
        lay1 = QVBoxLayout(p1)
        wide_help = self.tr(
            "Cochez les colonnes qui portent un code. L'ordre de la liste "
            "= ordre des colonnes du fichier. Une cellule vide est "
            "ignorée, jamais comblée.")
        cap = cap_for(self.file_type)
        if cap:
            wide_help += self.tr(
                " Maximum {} colonnes de codes par intervalle.").format(cap)
        lay1.addWidget(make_collapsible_help(wide_help))
        self.wide_list = QListWidget()
        for header in self.headers:
            item = QListWidgetItem(header)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.wide_list.addItem(item)
        lay1.addWidget(self.wide_list)
        self.pages.addWidget(p1)

        # — cellule séparée —
        p2 = QWidget()
        form2 = QFormLayout(p2)
        self.delimited_code = QComboBox()
        self.delimited_code.addItem(self.tr("— Aucune —"), "")
        for header in self.headers:
            self.delimited_code.addItem(header, header)
        self.delimited_code.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.delimited_code)
        self.delimiter = QLineEdit("/")
        self.delimiter.setMaxLength(4)
        self.delimiter.setStyleSheet(INPUT_STYLE)
        form2.addRow(self.tr("Colonne des codes"), self.delimited_code)
        form2.addRow(self.tr("Séparateur"), self.delimiter)
        form2.addRow(make_collapsible_help(
            self.tr("Chaque morceau entre deux séparateurs devient un code "
                    "du même intervalle. La cellule source reste intacte.")))
        self.pages.addWidget(p2)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(self.tr("Enregistrer l'organisation"))
        buttons.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.error_label = QLabel(self.tr(""))
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color:#C0392B;")
        layout.addWidget(self.error_label)

    def _mode_changed(self, index):
        self.pages.setCurrentIndex(max(index, 0))

    # ------------------------------------------------------------------
    def _load(self, profile):
        mode = profile.mode if profile.mode in (
            "standard", "wide_components", "delimited_components"
        ) else "standard"
        index = self.mode_combo.findData(mode)
        self.mode_combo.setCurrentIndex(max(index, 0))
        self._mode_changed(max(index, 0))
        if mode == "standard" and profile.code_column:
            idx = self.standard_code.findData(profile.code_column)
            if idx >= 0:
                self.standard_code.setCurrentIndex(idx)
        if mode == "wide_components":
            chosen = {str(c.code_column)
                      for c in profile.component_columns or []}
            for row in range(self.wide_list.count()):
                item = self.wide_list.item(row)
                item.setCheckState(
                    Qt.Checked if item.text() in chosen else Qt.Unchecked)
        if mode == "delimited_components":
            idx = self.delimited_code.findData(profile.code_column)
            if idx >= 0:
                self.delimited_code.setCurrentIndex(idx)
            if profile.delimiter:
                self.delimiter.setText(profile.delimiter)

    # ------------------------------------------------------------------
    def _accept(self):
        mode = self.mode_combo.currentData()
        if mode == "wide_components":
            chosen = [
                self.wide_list.item(row).text()
                for row in range(self.wide_list.count())
                if self.wide_list.item(row).checkState() == Qt.Checked]
            if not chosen:
                self.error_label.setText(
                    self.tr("Cochez au moins une colonne de codes."))
                return
            cap = cap_for(self.file_type)
            extra = len(chosen) - cap if cap else 0
            if extra > 0:
                self.error_label.setText(self.tr(
                    "{} colonnes cochées — maximum {} (arbitrage CM-03). "
                    "Décochez : {}.").format(
                    len(chosen), cap, ', '.join(chosen[cap:])))
                return
            self._profile = ImportStructureProfile(
                mode="wide_components",
                component_columns=[
                    ComponentColumn(code_column=name) for name in chosen],
                confirmed=True, confidence=1.0)
        elif mode == "delimited_components":
            column = self.delimited_code.currentData()
            if not column:
                self.error_label.setText(
                    self.tr("Choisissez la colonne qui contient les codes séparés."))
                return
            separator = self.delimiter.text()
            if not separator:
                self.error_label.setText(self.tr("Le séparateur ne peut pas être vide."))
                return
            self._profile = ImportStructureProfile(
                mode="delimited_components",
                code_column=str(column), delimiter=separator,
                confirmed=True, confidence=1.0)
        else:
            self._profile = ImportStructureProfile(
                mode="standard",
                code_column=str(self.standard_code.currentData() or ""),
                confirmed=True, confidence=1.0)
        self.accept()

    def profile(self):
        return getattr(self, "_profile", self.initial)
