"""Optional project-wide editor for meanings and shared category symbols.

v2.9.88 — sélecteur couleur domaine : litho = tons vifs only,
altération = tons pastel only (pas de spectre libre mélangeant les deux).
"""
from __future__ import annotations

from qgis.PyQt.QtCore import QCoreApplication, Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QBrush, QIcon, QPainter, QPen, QPixmap
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QColorDialog, QDialog,
    QDialogButtonBox, QGridLayout, QScrollArea,
    QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from ..core.reference import (
    PATTERN_KEYS, PATTERN_LABELS, ReferenceRepository, cycle_pattern_list, \
    normalise_pattern,
    SYMBOL_FREE_DOMAINS,
    clamp_domain_color, domain_color_palette, is_pastel_tone, is_vivid_tone,
)
from ..core.mineral_symbols import style_display_code
from .styles_qt import (
    apply_combo_popup_style, BUTTON_SECONDARY, COLORS, INPUT_STYLE,
    TABLE_STYLE, TOOLTIP_STYLE, make_collapsible_help,
)


_PATTERN_BRUSHES = {
    "": Qt.SolidPattern,
    "diagonal": Qt.FDiagPattern,
    "backward_diagonal": Qt.BDiagPattern,
    "cross": Qt.CrossPattern,
    "diagonal_cross": Qt.DiagCrossPattern,
    "horizontal": Qt.HorPattern,
    "vertical": Qt.VerPattern,
    "dots": Qt.Dense1Pattern,
    "dense": Qt.Dense1Pattern,  # legacy alias (v2.7.5)
    "dots_moyen": Qt.Dense3Pattern,
    "dots_fin": Qt.Dense5Pattern,
    "dots_dense": Qt.Dense7Pattern,
}


def _pattern_icon(pattern, colour="#85929E"):
    """v2.9.87 — preview motifs 2.9.33 (underlay + QBrush Qt)."""
    brush_style = _PATTERN_BRUSHES.get(
        normalise_pattern(pattern), Qt.SolidPattern)
    pixmap = QPixmap(58, 18)
    pixmap.fill(QColor("#FFFFFF"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, False)
    if brush_style != Qt.SolidPattern:
        underlay = QColor(colour)
        underlay.setAlpha(round(255 * 0.55))
        painter.fillRect(0, 0, 57, 17, QBrush(underlay, Qt.SolidPattern))
        # encre lignes contrastée comme la coupe
        ink = QColor(colour)
        if brush_style in (
                Qt.FDiagPattern, Qt.BDiagPattern, Qt.CrossPattern,
                Qt.DiagCrossPattern, Qt.HorPattern, Qt.VerPattern):
            ink = (QColor("#FFFFFF") if QColor(colour).lightness() < 130
                   else QColor("#4A4A4A"))
        painter.setPen(QPen(QColor("#7F8C8D"), 1))
        painter.setBrush(QBrush(ink, brush_style))
    else:
        painter.setPen(QPen(QColor("#7F8C8D"), 1))
        painter.setBrush(QBrush(QColor(colour), brush_style))
    painter.drawRect(0, 0, 57, 17)
    painter.end()
    return QIcon(pixmap)


# v2.7.10 — la version affichée dans le titre permet de vérifier d'un
# coup d'œil quel zip est réellement installé dans QGIS (diagnostic des
# « rien ne se passe » qui sont en fait un vieux zip).
REFERENCE_VERSION = "2.9.382"


class _DomainColorPicker(QDialog):
    """Sélecteur de couleur RÉDUIT à la gamme du domaine (v2.9.88).

    - lithologie → pastilles VIVES uniquement
    - altération → pastilles PASTEL uniquement
    Pas de spectre libre (évite mélange litho/altéro sur la coupe).
    """

    def __init__(self, parent, domain_key: str, initial: str, code_label: str = ""):
        super().__init__(parent)
        self._domain_key = domain_key
        self._chosen = QColor(initial or "#CCCCCC")
        kind = (self.tr("pastel") if domain_key == "alteration"
                else self.tr("vives"))
        title = self.tr("Couleur {}").format(kind)
        if code_label:
            title = self.tr("{} — {}").format(title, code_label)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        lay.addWidget(make_collapsible_help(
            self.tr("Altération : tons pastel uniquement (voile lisible "
                    "sur la litho).")
            if domain_key == "alteration" else
            self.tr("Lithologie : tons vifs uniquement (identité de roche).")))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(320)
        host = QWidget()
        grid = QGridLayout(host)
        grid.setSpacing(4)
        palette = domain_color_palette(domain_key)
        cur = clamp_domain_color(domain_key, initial or "#CCCCCC")
        if cur not in palette:
            palette = [cur] + list(palette)
        self._buttons = []
        cols = 9
        for i, hx in enumerate(palette):
            btn = QPushButton()
            btn.setFixedSize(34, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(hx)
            btn.setStyleSheet(
                f"QPushButton {{ background:{hx}; border:1px solid #7F8C8D; }}"
                f"QPushButton:checked {{ border:2px solid #1A252F; }}"
            )
            btn.setCheckable(True)
            btn.setChecked(hx.upper() == cur.upper())
            btn.clicked.connect(lambda _=False, h=hx, b=btn: self._pick(h, b))
            grid.addWidget(btn, i // cols, i % cols)
            self._buttons.append(btn)
        scroll.setWidget(host)
        lay.addWidget(scroll)

        self._preview = QLabel(cur)
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setMinimumHeight(36)
        self._set_preview(cur)
        lay.addWidget(self._preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _pick(self, hx: str, btn: QPushButton):
        for b in self._buttons:
            b.setChecked(b is btn)
        self._set_preview(hx)

    def _set_preview(self, hx: str):
        hx = clamp_domain_color(self._domain_key, hx)
        self._chosen = QColor(hx)
        fg = "#FFFFFF" if self._chosen.lightness() < 128 else "#000000"
        self._preview.setText(hx)
        self._preview.setStyleSheet(
            f"background:{hx}; color:{fg}; border:1px solid #5D6D7E; "
            f"font-weight:bold; padding:6px;")

    def selected_hex(self) -> str:
        return clamp_domain_color(self._domain_key, self._chosen.name().upper())




class ReferenceDialog(QDialog):
    """Edit project metadata without changing any source value."""

    reference_saved = pyqtSignal(str)

    CATEGORY_COLUMNS = (
        "Valeur d’origine", "Libellé affiché", "Couleur", "Motif",
        "Visible", "État", "Utilisations")
    ELEMENT_COLUMNS = (
        "Colonne d’origine", "Libellé affiché", "Symbole", "Unité",
        "Décimales", "Limite de détection", "État")

    # v2.7.3/v2.7.4 — each domain says WHAT it drives.  The referential is
    # the SINGLE source of symbols for every present and future view
    # (feedback « et le reste ? », 18/08/2026) : nothing here is limited
    # to the 2D section or to QGIS — 3D and interpretation will read the
    # same table, so a symbol is never set twice.
    # v2.7.6.9 — « exports » retiré de la phrase : la fonctionnalité
    # d'export a été supprimée (AUDIT_V2.7.6.9.md).
    _SHARED_NOTE = (
        "Ces symboles sont la source unique partagée par toutes les vues : "
        "coupe 2D, couches QGIS — et demain 3D et interprétation.")
    DOMAIN_USAGE = {
        "lithology": (
            "Sert à : la couleur et le motif des bandes de lithologie."),
        "alteration": (
            "Sert à : la couleur et le motif des bandes de la piste "
            "« Altérations »."),
        "alteration_intensity": (
            "Sert à : la LARGEUR des bandes d’altération (faible → "
            "étroite, forte → pleine largeur), JAMAIS leur couleur. "
            "Le rang sert à ordonner les valeurs — la couleur n’est donc "
            "pas proposée ici."),
        "mineralization_style": (
            "Sert à : la couleur et le motif des bandes de la piste "
            "« Minéralisations »."),
        "minerals": (
            "Sert à : les libellés lisibles dans les infobulles des "
            "minéralisations. Aucune bande automatique (AM-05) : la "
            "couleur n’est donc pas proposée ici."),
        "assay_elements": (
            "Sert à : les noms, unités et décimales des éléments de "
            "teneur."),
        "structure": (
            "Sert à : la couleur des points des mesures de structure "
            "observées (couche QGIS ; coupe 2D et vue 3D à venir)."),
    }

    def __init__(self, project, parent=None, domain_key=None, raw_code=None):
        super().__init__(parent)
        # v2.7.12.8 — infobulles lisibles dans le dialogue (cascade racine).
        self.setStyleSheet(TOOLTIP_STYLE)
        self.project = project
        original = project.get_reference_repository()
        self.repository = ReferenceRepository.from_dict(original.to_dict())
        self._baseline = self.repository.to_dict()
        self._loading = False
        self._detail_row = -1
        self._reset_entries = set()
        self._requested_domain = domain_key
        self._requested_code = raw_code
        self._symbol_free_reason = ""
        self._pattern_identity_domain = False
        self._symbol_domain = False
        self._build()
        self._load_domains()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        self.setWindowTitle(
            self.tr("Référentiel du projet — v{}").format(REFERENCE_VERSION))
        self.resize(1080, 650)
        self.setMinimumSize(760, 480)
        layout = QVBoxLayout(self)

        layout.addWidget(make_collapsible_help(
            self.tr("Codes, libellés et symboles partagés entre les "
                    "données et toutes les vues. Les valeurs d'origine "
                    "ne sont jamais modifiées.")))

        tools = QHBoxLayout()
        tools.addWidget(QLabel(self.tr("Domaine")))
        self.domain_combo = QComboBox()
        self.domain_combo.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.domain_combo)
        self.domain_combo.currentIndexChanged.connect(self._change_domain)
        tools.addWidget(self.domain_combo, 2)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.tr("Rechercher une valeur ou un libellé…"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setStyleSheet(INPUT_STYLE)
        self.search_edit.textChanged.connect(self._apply_filters)
        tools.addWidget(self.search_edit, 3)
        self.status_filter = QComboBox()
        self.status_filter.addItem(QCoreApplication.translate("ReferenceDialog", "Toutes les entrées"), "all")
        self.status_filter.addItem(QCoreApplication.translate("ReferenceDialog", "Personnalisées"), "custom")
        self.status_filter.addItem(QCoreApplication.translate("ReferenceDialog", "Automatiques"), "automatic")
        self.status_filter.addItem(QCoreApplication.translate("ReferenceDialog", "Nouvelles"), "new")
        self.status_filter.addItem(QCoreApplication.translate("ReferenceDialog", "Non utilisées"), "unused")
        self.status_filter.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.status_filter)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)
        tools.addWidget(self.status_filter, 2)
        layout.addLayout(tools)

        self._domain_help = make_collapsible_help("")
        self.domain_hint = self._domain_help._help_body
        layout.addWidget(self._domain_help)

        self.table = QTableWidget()
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._edit_colour)
        self.table.currentCellChanged.connect(self._selection_changed)
        layout.addWidget(self.table, 1)

        self.details = QGroupBox(self.tr("Informations avancées"))
        self.details.setCheckable(True)
        self.details.setChecked(False)
        detail_form = QFormLayout(self.details)
        self.normalized_edit = QLineEdit()
        self.normalized_edit.setStyleSheet(INPUT_STYLE)
        self.normalized_edit.setToolTip(self.tr("Regroupement (fichier inchangé)"))
        detail_form.addRow(self.tr("Regroupement"), self.normalized_edit)
        self.rank_spin = QDoubleSpinBox()
        self.rank_spin.setRange(-1_000_000, 1_000_000)
        self.rank_spin.setDecimals(4)
        self.rank_spin.setSpecialValueText(self.tr("Non défini"))
        self.rank_spin.setValue(self.rank_spin.minimum())
        self.rank_spin.setStyleSheet(INPUT_STYLE)
        detail_form.addRow(self.tr("Rang"), self.rank_spin)
        # v2.7.9 — famille d'altération suggérée (taxonomie des 27).
        self.family_label = QLabel(self.tr("—"))
        self.family_label.setObjectName("label_hint")
        self.family_label.setWordWrap(True)
        self.family_label.setToolTip(self.tr("Famille suggérée (fichier inchangé)"))
        detail_form.addRow(self.tr("Famille d'altération"), self.family_label)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(70)
        self.description_edit.setPlaceholderText(self.tr("Description facultative"))
        detail_form.addRow(self.tr("Description"), self.description_edit)
        self.details.toggled.connect(self._toggle_details)
        layout.addWidget(self.details)
        self._toggle_details(False)

        bottom = QHBoxLayout()
        self.count_label = QLabel()
        self.count_label.setObjectName("label_hint")
        bottom.addWidget(self.count_label, 1)
        self.reset_button = QPushButton(self.tr("Rétablir le symbole automatique"))
        self.reset_button.setStyleSheet(BUTTON_SECONDARY)
        self.reset_button.clicked.connect(self._reset_selected)
        bottom.addWidget(self.reset_button)
        self.cleanup_button = QPushButton(self.tr("Retirer les entrées non utilisées"))
        self.cleanup_button.setStyleSheet(BUTTON_SECONDARY)
        self.cleanup_button.setToolTip(self.tr("Retirer entrées auto inutilisées"))
        self.cleanup_button.clicked.connect(self._remove_unused_entries)
        bottom.addWidget(self.cleanup_button)
        # v2.9.151 — assignation de motifs (retour écran « aucun motif,
        # rien ») : les bibliothèques n'en définissent AUCUN ; un clic
        # assigne un motif distinct par code (les choix existants sont
        # conservés), visible coupe 2D + carte + vue 3D.
        self.auto_patterns_button = QPushButton(self.tr("Motifs auto"))
        self.auto_patterns_button.setStyleSheet(BUTTON_SECONDARY)
        self.auto_patterns_button.setToolTip(self.tr(
            "Assigner un motif distinct à chaque code sans motif de ce "
            "domaine\n(les motifs déjà choisis sont conservés). Visible "
            "coupe 2D, carte et vue 3D."))
        self.auto_patterns_button.clicked.connect(self._assign_auto_patterns)
        bottom.addWidget(self.auto_patterns_button)
        # v2.9.156 — couleurs DISTINCTES par style, gérées par le
        # RÉFÉRENTIEL (retour écran : les codes sur les tubes 3D
        # prenaient trop de place → l'identification passe par la
        # couleur ; chaque style une couleur différente, jamais deux
        # pareilles, pour la coupe 2D ET la vue 3D).
        self.auto_colors_button = QPushButton(self.tr("Couleurs auto"))
        self.auto_colors_button.setStyleSheet(BUTTON_SECONDARY)
        self.auto_colors_button.setToolTip(self.tr(
            "Assigner une couleur DISTINCTE à chaque style de ce domaine\n"
            "(les couleurs choisies manuellement sont conservées ; aucune "
            "collision)."))
        self.auto_colors_button.clicked.connect(self._assign_auto_colors)
        bottom.addWidget(self.auto_colors_button)
        layout.addLayout(bottom)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Apply |
            QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(self.tr("OK"))
        buttons.button(QDialogButtonBox.Apply).setText(self.tr("Appliquer"))
        buttons.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._apply)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_details(self, expanded):
        form = self.details.layout()
        for index in range(form.count()):
            widget = form.itemAt(index).widget()
            if widget:
                widget.setVisible(expanded)
        domain = self.repository.domains.get(
            self.domain_combo.currentData()) if hasattr(self, "domain_combo") else None
        rank_visible = expanded and bool(domain and domain.kind == "ordinal")
        self.rank_spin.setVisible(rank_visible)
        rank_label = form.labelForField(self.rank_spin)
        if rank_label:
            rank_label.setVisible(rank_visible)
        self.details.setMaximumHeight(180 if expanded else 28)

    # ------------------------------------------------------------------
    # Domain/table loading
    # ------------------------------------------------------------------
    def _load_domains(self):
        self._loading = True
        self.domain_combo.clear()
        domains = sorted(
            self.repository.domains.items(), key=lambda pair: pair[1].label)
        requested_index = 0
        for key, domain in domains:
            # v2.7.10.4 — le domaine « Minéraux » est retiré de l'éditeur
            # (décision écran : ingérable, on verra plus tard) ; les
            # données restent dans le projet et les infobulles.
            if key == "minerals":
                continue
            # v2.9.258-rendu — labels de domaines traduits au point d'usage
            # (aucun « Type de structure » français en interface anglaise).
            self.domain_combo.addItem(self.tr(domain.label), key)
            if key == self._requested_domain:
                # v2.7.10.13 — la position est mesurée APRÈS l'ajout :
                # l'ancien index d'enumerate comptait les domaines sautés
                # (« minerals ») et ouvrait l'onglet précédent (« Éléments
                # mesurés ») à la place de « Styles de minéralisation ».
                requested_index = self.domain_combo.count() - 1
        self.domain_combo.setCurrentIndex(requested_index)
        self._loading = False
        self._load_current_domain()

    def _change_domain(self, *_args):
        if self._loading:
            return
        self._store_detail()
        self._save_table_to_repository()
        self._load_current_domain()

    def _load_current_domain(self):
        key = self.domain_combo.currentData()
        domain = self.repository.domains.get(key)
        self._loading = True
        self._detail_row = -1
        self._symbol_free_reason = ""
        # v2.7.10.4 — seul le domaine « Styles de minéralisation » est
        # codé par un CODE TEXTE (ex. « MA ») : plus de glyphes minéraux.
        self._pattern_identity_domain = (
            domain is not None
            and domain.key == "mineralization_style")
        self._symbol_domain = (
            domain is not None
            and domain.key == "mineralization_style")
        # v2.7.9.6 — les options avancées (famille d'altération,
        # regroupement, rang, description) sont VISIBLES d'emblée pour
        # l'altération et la minéralisation : fini le groupe replié que
        # personne ne voit.
        if (domain is not None
                and domain.key in ("alteration", "mineralization_style")):
            self.details.setChecked(True)
        self.table.clear()
        self.table.setRowCount(0)
        if not domain:
            self._loading = False
            return

        quantitative = domain.kind == "quantitative_fields"
        columns = self.ELEMENT_COLUMNS if quantitative else self.CATEGORY_COLUMNS
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([self.tr(c) for c in columns])
        # v2.7.10.4 — l'en-tête « Code » s'applique après le jeu
        # d'en-têtes générique (il était écrasé par « Motif »).
        if self._symbol_domain and not quantitative:
            header_item = self.table.horizontalHeaderItem(3)
            if header_item is not None:
                header_item.setText(self.tr("Code"))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setStretchLastSection(False)
        for column, title in enumerate(columns):
            item = self.table.horizontalHeaderItem(column)
            item.setToolTip(title)

        kinds = {
            "categorical": self.tr("Catégories sans ordre imposé"),
            "ordinal": self.tr(
                "Catégories ordonnées ; le rang est facultatif"),
            "multi_label": self.tr(
                "Assemblages ou valeurs multiples conservés tels quels"),
            "quantitative_fields": self.tr(
                "Métadonnées des colonnes mesurées ; les valeurs "
                "numériques et classifications ne sont pas des catégories"),
        }
        usage = self.tr(self.DOMAIN_USAGE.get(
            domain.key,
            "Domaine complémentaire : conservé pour les vues futures."))
        self._symbol_free_reason = (
            self.tr(SYMBOL_FREE_DOMAINS.get(domain.key, ""))
            if SYMBOL_FREE_DOMAINS.get(domain.key) else "")
        hint_parts = [kinds.get(domain.kind, domain.kind),
                      usage, self.tr(self._SHARED_NOTE)]
        self.domain_hint.setText("\n".join(part for part in hint_parts if part))
        entries = sorted(domain.entries.values(), key=lambda value: value.raw_code)
        self.table.setRowCount(len(entries))
        requested_row = -1
        for row, entry in enumerate(entries):
            if quantitative:
                self._fill_element_row(row, entry)
            else:
                self._fill_category_row(row, entry)
            if entry.raw_code == self._requested_code:
                requested_row = row
        rank_visible = self.details.isChecked() and domain.kind == "ordinal"
        self.rank_spin.setVisible(rank_visible)
        label = self.details.layout().labelForField(self.rank_spin)
        if label:
            label.setVisible(rank_visible)
        self.reset_button.setVisible(not quantitative)
        self.cleanup_button.setVisible(not quantitative)
        self._loading = False
        target = requested_row if requested_row >= 0 else (0 if entries else -1)
        if target >= 0:
            self.table.setCurrentCell(target, 0)
            self._load_detail(target)
        self._requested_code = None
        self._apply_filters()

    def _base_item(self, text, raw_code=None, editable=True):
        item = QTableWidgetItem(str(text or ""))
        item.setToolTip(str(text or ""))
        if raw_code is not None:
            item.setData(Qt.UserRole, raw_code)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _fill_category_row(self, row, entry):
        self.table.setItem(row, 0, self._base_item(
            entry.raw_code, entry.raw_code, editable=False))
        self.table.setItem(row, 1, self._base_item(entry.label))
        if self._symbol_free_reason or self._pattern_identity_domain:
            # Colour/pattern would be a fake control here (v2.7.4) : the
            # value drives something else (width, infotip).  "—", disabled.
            # v2.7.8 : la minéralisation est codée par motif — la couleur
            # est désactivée, le motif reste choisi ci-dessous.
            colour = self._base_item("—", editable=False)
            colour.setTextAlignment(Qt.AlignCenter)
            colour.setForeground(QBrush(QColor(COLORS["text_medium"])))
            if getattr(entry, "family", ""):
                colour_tooltip = self.tr(
                    "Famille suggérée : {}").format(entry.family)
            else:
                colour_tooltip = (
                    self.tr(
                        "v2.7.9 — la piste minéralisation est codée par "
                        "symbole (encre neutre unique), pas par couleur.")
                    if self._pattern_identity_domain
                    else self._symbol_free_reason)
            colour.setToolTip(colour_tooltip)
            self.table.setItem(row, 2, colour)
            combo = QComboBox()
            combo.setStyleSheet(INPUT_STYLE)
            if self._symbol_domain:
                # v2.7.10.6 — le CODE du style est un TEXTE LIBRE
                # réellement éditable (double-clic), jamais une liste
                # déroulante (bug : un combo vide écrasait la cellule).
                # Vide = rien n'est dessiné.
                display_text = style_display_code(
                    entry.raw_code, entry.symbol_id or "", entry.pattern)
                code_item = self._base_item(display_text)
                code_item.setFlags(
                    Qt.ItemIsEnabled | Qt.ItemIsSelectable
                    | Qt.ItemIsEditable)
                code_item.setToolTip(self.tr("Code bande (ex. MA) · vide = rien"))
                self.table.setItem(row, 3, code_item)
                self.table.setCellWidget(row, 3, None)
            elif self._pattern_identity_domain:
                # Domaines sans symbole : le MOTIF reste le codage.
                apply_combo_popup_style(combo)
                combo.addItem(QCoreApplication.translate("ReferenceDialog", "Transparent (invisible)"), "none")
                for pattern in PATTERN_KEYS:
                    if not pattern:
                        continue
                    combo.addItem(
                        _pattern_icon(pattern, "#5D6D7E"),
                        PATTERN_LABELS.get(pattern, pattern), pattern)
                index = combo.findData(normalise_pattern(entry.pattern))
                if entry.pattern and normalise_pattern(entry.pattern) == "":
                    index = combo.findData("none")
                combo.setCurrentIndex(max(index, 0))
                combo.setToolTip(self.tr("Motif · Transparent = place sans peinture"))
            else:
                combo.addItem(self.tr("—"))
                combo.setEnabled(False)
                combo.setToolTip(self._symbol_free_reason)
            if not self._symbol_domain:
                # v2.7.10.6 — seul le cas non-symbole pose un combo ;
                # le domaine symbole garde son item texte éditable.
                self.table.setCellWidget(row, 3, combo)
        else:
            colour = self._base_item(entry.color or "#CCCCCC", editable=False)
            colour.setBackground(QBrush(QColor(entry.color or "#CCCCCC")))
            colour.setForeground(QBrush(
                QColor("#FFFFFF") if QColor(entry.color).lightness() < 128
                else QColor("#000000")))
            colour.setTextAlignment(Qt.AlignCenter)
            # v2.9.88 — sélecteur restreint : pastel only / vif only.
            _convention = ""
            _domain_key = self.domain_combo.currentData()
            if _domain_key == "alteration":
                _convention = self.tr(
                    "\nTons pastel uniquement (pas de couleurs vives).")
            elif _domain_key == "lithology":
                _convention = self.tr(
                    "\nTons vifs uniquement (pas de pastels lavés).")
            colour.setToolTip(
                self.tr("Double-cliquez pour choisir la couleur")
                + _convention)
            self.table.setItem(row, 2, colour)
            combo = QComboBox()
            combo.setStyleSheet(INPUT_STYLE)
            apply_combo_popup_style(combo)
            for pattern in PATTERN_KEYS:
                combo.addItem(
                    _pattern_icon(pattern, entry.color or "#85929E"),
                    PATTERN_LABELS.get(pattern, pattern), pattern)
            index = combo.findData(normalise_pattern(entry.pattern))
            combo.setCurrentIndex(max(index, 0))
            self.table.setCellWidget(row, 3, combo)
        # v2.7.9.7 — case « Visible » : décocher retire l'entrée de la
        # coupe, des légendes ET des couches QGIS (synchro immédiate).
        visible_box = QCheckBox()
        visible_box.setToolTip(self.tr("Décoché · masqué partout"))
        visible_box.setChecked(bool(entry.visible))
        visible_box.toggled.connect(
            lambda checked, row=row: self._toggle_row_visible(row, checked))
        wrapper = QWidget()
        wrap_layout = QHBoxLayout(wrapper)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        wrap_layout.setAlignment(Qt.AlignCenter)
        wrap_layout.addWidget(visible_box)
        self.table.setCellWidget(row, 4, wrapper)
        state = (self.tr("Automatique") if entry.automatic
                 else self.tr("Personnalisé"))
        if entry.newly_discovered:
            state = self.tr("Nouveau · {}").format(state.casefold())
        if not entry.usage_count:
            state += self.tr(" · non utilisé")
        state_item = self._base_item(state, editable=False)
        state_item.setData(Qt.UserRole + 1, entry.automatic)
        state_item.setData(Qt.UserRole + 2, entry.usage_count)
        state_item.setData(Qt.UserRole + 3, entry.newly_discovered)
        self.table.setItem(row, 5, state_item)
        uses = self._base_item(str(entry.usage_count), editable=False)
        uses.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 6, uses)

    def _fill_element_row(self, row, entry):
        values = [
            entry.raw_code, entry.label, entry.symbol, entry.source_unit,
            "" if entry.precision is None else str(entry.precision),
            "" if entry.detection_limit is None else str(entry.detection_limit),
            ((self.tr("Nouveau · ") if entry.newly_discovered else "")
             + (self.tr("automatique") if entry.automatic
                else self.tr("personnalisé"))),
        ]
        for column, value in enumerate(values):
            item = self._base_item(
                value, entry.raw_code if column == 0 else None,
                editable=column not in (0, 7))
            if column == 6:
                item.setData(Qt.UserRole + 1, entry.automatic)
                item.setData(Qt.UserRole + 2, entry.usage_count)
                item.setData(Qt.UserRole + 3, entry.newly_discovered)
            self.table.setItem(row, column, item)

    # ------------------------------------------------------------------
    # Editing/filtering
    # ------------------------------------------------------------------
    def _selection_changed(self, current_row, _current_column,
                           _previous_row, _previous_column):
        if self._loading:
            return
        self._store_detail()
        self._load_detail(current_row)

    def _load_detail(self, row):
        key = self.domain_combo.currentData()
        domain = self.repository.domains.get(key)
        if not domain or row < 0 or not self.table.item(row, 0):
            self._detail_row = -1
            return
        raw_code = self.table.item(row, 0).data(Qt.UserRole)
        entry = domain.entries.get(raw_code)
        if not entry:
            return
        self._loading = True
        self.normalized_edit.setText(entry.normalized_code)
        self.description_edit.setPlainText(entry.description)
        self.rank_spin.setValue(
            self.rank_spin.minimum() if entry.rank is None else entry.rank)
        # v2.7.9 — famille d'altération (ou conseil pour les autres domaines)
        self.family_label.setText(
            getattr(entry, "family", "") or "—")
        self._detail_row = row
        self._loading = False

    def _store_detail(self):
        if self._loading or self._detail_row < 0:
            return
        key = self.domain_combo.currentData()
        domain = self.repository.domains.get(key)
        item = self.table.item(self._detail_row, 0)
        if not domain or not item:
            return
        entry = domain.entries.get(item.data(Qt.UserRole))
        if not entry:
            return
        entry.normalized_code = self.normalized_edit.text().strip()
        entry.description = self.description_edit.toPlainText().strip()
        entry.rank = (None if self.rank_spin.value() == self.rank_spin.minimum()
                      else self.rank_spin.value())

    def _save_table_to_repository(self):
        if self._loading:
            return
        key = self.domain_combo.currentData()
        domain = self.repository.domains.get(key)
        if not domain:
            return
        quantitative = domain.kind == "quantitative_fields"
        for row in range(self.table.rowCount()):
            raw_item = self.table.item(row, 0)
            if not raw_item:
                continue
            raw_code = raw_item.data(Qt.UserRole)
            entry = domain.entries.get(raw_code)
            if not entry:
                continue
            if quantitative:
                entry.label = self.table.item(row, 1).text().strip()
                entry.symbol = self.table.item(row, 2).text().strip()
                entry.source_unit = self.table.item(row, 3).text().strip()
                try:
                    precision = self.table.item(row, 4).text().strip()
                    entry.precision = int(precision) if precision else None
                except ValueError:
                    entry.precision = None
                try:
                    detection = self.table.item(row, 5).text().strip()
                    entry.detection_limit = (
                        float(detection.replace(",", "."))
                        if detection else None)
                except ValueError:
                    entry.detection_limit = None
            else:
                entry.label = self.table.item(row, 1).text().strip()
                if domain.key in SYMBOL_FREE_DOMAINS:
                    # Colour/pattern intentionally unused (v2.7.4) : the
                    # "—" placeholders must never overwrite the stored
                    # values.
                    continue
                try:
                    vis_widget = self.table.cellWidget(row, 4)
                    if vis_widget is not None:
                        child = vis_widget.findChild(QCheckBox)
                        if child is not None:
                            entry.visible = bool(child.isChecked())
                except RuntimeError:
                    pass  # widget détruit : valeur conservée
                try:
                    combo = self.table.cellWidget(row, 3)
                except RuntimeError:
                    combo = None  # widget détruit : on garde les valeurs
                if self._symbol_domain:
                    # v2.7.10.4 — le code de style est un texte libre :
                    # vide = « none » (rien n'est dessiné), sinon le texte
                    # en majuscules. La couleur n'est pas gérée ici.
                    code_text = self.table.item(row, 3)
                    entry.symbol_id = (
                        code_text.text().strip().upper()
                        if code_text is not None else "")
                    if not entry.symbol_id:
                        entry.symbol_id = "none"
                    continue
                entry.color = self.table.item(row, 2).text().strip() or "#CCCCCC"
                if not combo:
                    entry.pattern = ""
                else:
                    entry.pattern = normalise_pattern(combo.currentData())
            # Any table change away from the baseline is classified during
            # persistence, avoiding a noisy signal on each keystroke.

    def _edit_colour(self, row, column):
        domain = self.repository.domains.get(self.domain_combo.currentData())
        if not domain or domain.kind == "quantitative_fields" or column != 2:
            return
        # v2.7.10.6 — les domaines à symbole (code texte) n'ont pas de
        # couleur éditable : le double-clic ne doit rien ouvrir.
        if self._symbol_domain or self._pattern_identity_domain:
            return
        if domain.key in SYMBOL_FREE_DOMAINS:
            return
        item = self.table.item(row, column)
        code_label = ""
        try:
            code_label = self.table.item(row, 0).text()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Couleur : _edit_colour", _exc)
            code_label = ""
        # v2.9.88 — litho = VIF only, altéro = PASTEL only (pas de spectre
        # libre : évite conflits de lecture coupe). Autres domaines : QColorDialog.
        if domain.key in ("alteration", "lithology"):
            picker = _DomainColorPicker(
                self, domain.key, item.text() or "#CCCCCC", code_label)
            if not picker.exec_():
                return
            value = picker.selected_hex()
            colour = QColor(value)
        else:
            # v2.7.10.23 — constructeur QColorDialog (initial, parent) only.
            dialog = QColorDialog(QColor(item.text() or "#CCCCCC"), self)
            dialog.setWindowTitle(self.tr("Couleur de {}").format(code_label))
            if not dialog.exec_():
                return
            colour = dialog.selectedColor()
            if not colour.isValid():
                return
            value = colour.name().upper()
        item.setText(value)
        item.setBackground(QBrush(colour))
        item.setForeground(QBrush(
            QColor("#FFFFFF") if colour.lightness() < 128
            else QColor("#000000")))
        combo = self.table.cellWidget(row, 3)
        if combo:
            selected = combo.currentData()
            for index in range(combo.count()):
                pattern = combo.itemData(index)
                combo.setItemIcon(index, _pattern_icon(pattern, value))
            selected_index = combo.findData(selected)
            combo.setCurrentIndex(max(selected_index, 0))

    def _apply_filters(self, *_args):
        if self._loading:
            return
        query = self.search_edit.text().strip().casefold()
        mode = self.status_filter.currentData() or "all"
        visible = 0
        for row in range(self.table.rowCount()):
            raw = self.table.item(row, 0).text().casefold()
            label = self.table.item(row, 1).text().casefold()
            state_column = self.table.columnCount() - 2
            domain = self.repository.domains.get(self.domain_combo.currentData())
            if domain and domain.kind == "quantitative_fields":
                state_column = self.table.columnCount() - 1
            state = self.table.item(row, state_column)
            automatic = bool(state.data(Qt.UserRole + 1)) if state else True
            uses = int(state.data(Qt.UserRole + 2) or 0) if state else 0
            is_new = bool(state.data(Qt.UserRole + 3)) if state else False
            matches_text = not query or query in raw or query in label
            matches_state = (
                mode == "all"
                or (mode == "custom" and not automatic)
                or (mode == "automatic" and automatic)
                or (mode == "new" and is_new)
                or (mode == "unused" and uses == 0))
            hidden = not (matches_text and matches_state)
            self.table.setRowHidden(row, hidden)
            if not hidden:
                visible += 1
        self.count_label.setText(self.tr(
            "{} entrée(s) affichée(s) sur {}").format(
            visible, self.table.rowCount()))

    def _reset_selected(self, *_args):
        row = self.table.currentRow()
        if row < 0:
            return
        raw_code = self.table.item(row, 0).data(Qt.UserRole)
        fallback = ""
        if self.domain_combo.currentData() == "lithology":
            from ..core.section import suggested_litho_color
            fallback = suggested_litho_color(raw_code)
        domain_key = self.domain_combo.currentData()
        self.repository.reset_entry_style(
            domain_key, raw_code, fallback)
        self._reset_entries.add((domain_key, raw_code))
        self._load_current_domain()
        for candidate in range(self.table.rowCount()):
            if self.table.item(candidate, 0).data(Qt.UserRole) == raw_code:
                self.table.setCurrentCell(candidate, 0)
                break

    def _remove_unused_entries(self, *_args):
        """Explicit removal of automatic, zero-usage entries.

        Nothing is ever deleted silently : the action confirms what will
        disappear, operates on the dialog's working copy and is only
        persisted through the normal Appliquer/OK path (Annuler aborts).
        """
        domain_key = self.domain_combo.currentData()
        domain = self.repository.domains.get(domain_key)
        if domain is None:
            return
        # v2.7.9.6 — MÊME définition que le filtre « Non utilisées »
        # (usage_count == 0, personnalisées comprises) : le retrait et le
        # filtre ne peuvent plus se contredire.
        unused = self.repository.unused_entry_codes(domain_key)
        if not unused:
            QMessageBox.information(
                self, QCoreApplication.translate("ReferenceDialog", "Aucune entrée non utilisée"),
                QCoreApplication.translate("ReferenceDialog", "Aucune entrée non utilisée dans ce domaine."))
            return
        shown = "\n".join(f"• {code}" for code in unused[:8])
        if len(unused) > 8:
            shown += self.tr("\n… et {} autre(s).").format(len(unused) - 8)
        answer = QMessageBox.question(
            self, QCoreApplication.translate("ReferenceDialog", "Retirer les entrées non utilisées ?"),
            self.tr("{} entrée(s) non utilisée(s) seront retirées du "
                    "domaine :\n\n{}\n\nElles seront recréées "
                    "automatiquement si elles réapparaissent dans les "
                    "données. Confirmez ensuite avec « Appliquer » ou "
                    "« OK ».").format(len(unused), shown),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        for code in unused:
            domain.entries.pop(code, None)
        self._load_current_domain()

    def _assign_auto_patterns(self, *_args):
        """v2.9.151 — motifs automatiques pour les codes SANS motif.

        Les bibliothèques livrées ne définissent aucun motif : sans cette
        action, les bandes 2D / lignes carte / tubes 3D restent des
        aplats (comportement cohérent, mais « on ne voit rien »).
        Assignation DÉTERMINISTE (ordre alphabétique des codes, liste
        de motifs discriminables) ; les motifs déjà choisis ne sont
        JAMAIS écrasés ; confirmation puis persistance par le chemin
        normal « Appliquer/OK » (Annuler abandonne).
        """
        domain_key = self.domain_combo.currentData()
        if domain_key not in ("lithology", "alteration"):
            QMessageBox.information(
                self, QCoreApplication.translate("ReferenceDialog", "Motifs auto"),
                self.tr("Les motifs s'appliquent aux domaines "
                        "Lithologie et Altérations."))
            return
        domain = self.repository.domains.get(domain_key)
        if domain is None:
            return
        bare = sorted(code for code, entry in domain.entries.items()
                      if not str(getattr(entry, "pattern", "") or "").strip())
        if not bare:
            QMessageBox.information(
                self, QCoreApplication.translate("ReferenceDialog",
                                                 "Motifs auto"),
                self.tr("Tous les codes de ce domaine ont déjà un motif."))
            return
        # Liste ordonnée pour la discriminabilité (familles géométriques
        # d'abord, densités de pointillés ensuite) — PATTERN_KEYS du canon.
        from ..core.reference import PATTERN_KEYS
        cycle = [k for k in ("diagonal", "dots", "backward_diagonal",
                             "vertical", "dots_dense", "cross",
                             "horizontal", "diagonal_cross", "dots_moyen",
                             "dots_fin") if k in PATTERN_KEYS]
        shown = "\n".join(
            f"• {code} → {motif}"
            for code, motif in list(zip(bare, cycle_pattern_list(cycle, len(bare))))[:8])
        if len(bare) > 8:
            shown += self.tr("\n… et {} autre(s).").format(len(bare) - 8)
        answer = QMessageBox.question(
            self, QCoreApplication.translate("ReferenceDialog", "Assigner des motifs automatiques ?"),
            self.tr("{} code(s) sans motif vont recevoir un motif "
                    "distinct (les motifs déjà choisis sont conservés) :"
                    "\n\n{}\n\nConfirmez ensuite avec « Appliquer » "
                    "ou « OK ».").format(len(bare), shown),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        for code, motif in zip(bare, cycle_pattern_list(cycle, len(bare))):
            domain.entries[code].pattern = motif
        self._load_current_domain()

    def _assign_auto_colors(self, *_args):
        """v2.9.156 — couleurs DISTINCTES par style (Référentiel).

        Domaine « Styles de minéralisation » : chaque code reçoit une
        couleur différente (palette distincte, aucune collision, y
        compris avec les couleurs choisies manuellement qui sont
        CONSERVÉES).  Confirmation puis persistance par le chemin
        normal « Appliquer/OK » (Annuler abandonne).
        """
        domain_key = self.domain_combo.currentData()
        if domain_key != "mineralization_style":
            QMessageBox.information(
                self, QCoreApplication.translate("ReferenceDialog", "Couleurs auto"),
                self.tr("Les couleurs auto distinctes s'appliquent au "
                        "domaine « Styles de minéralisation »."))
            return
        domain = self.repository.domains.get(domain_key)
        if domain is None:
            return
        # candidats : entrées sans couleur OU automatiques (pas de
        # choix explicite de l'utilisateur) ; les couleurs explicites
        # restent et servent de contrainte anti-collision.
        kept = [str(getattr(e, "color", "") or "").strip().upper()
                for e in domain.entries.values()
                if str(getattr(e, "color", "") or "").strip()
                and not getattr(e, "automatic", True)]
        targets = sorted(
            code for code, e in domain.entries.items()
            if not str(getattr(e, "color", "") or "").strip()
            or getattr(e, "automatic", True))
        if not targets:
            QMessageBox.information(
                self, QCoreApplication.translate("ReferenceDialog",
                                                 "Couleurs auto"),
                self.tr("Tous les styles ont déjà une couleur choisie "
                        "manuellement."))
            return
        # v2.9.159 — MÊME méthode canonique que la migration au
        # chargement (une seule source : repository).
        colors_preview = {}
        kept_upper = [c.upper() for c in kept]
        remaining = [c for c in targets]
        from ..core.reference import distinct_auto_colors
        for code, col in zip(remaining,
                             distinct_auto_colors(kept_upper, len(remaining))):
            colors_preview[code] = col
        shown = "\n".join(
            f"• {code} → {col}"
            for code, col in list(colors_preview.items())[:8])
        if len(targets) > 8:
            shown += self.tr("\n… et {} autre(s).").format(len(targets) - 8)
        answer = QMessageBox.question(
            self, QCoreApplication.translate("ReferenceDialog", "Assigner des couleurs distinctes ?"),
            self.tr("{} style(s) vont recevoir une couleur DIFFÉRENTE "
                    "(aucun doublon ; les couleurs choisies manuellement "
                    "sont conservées) :\n\n{}\n\nConfirmez ensuite "
                    "avec « Appliquer » ou « OK ».").format(len(targets),
                                                            shown),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self.repository.assign_distinct_style_colors()
        self._load_current_domain()

    def _toggle_row_visible(self, row, checked):
        """v2.7.9.7 — décocher/cocher une entrée s'applique IMMÉDIATEMENT
        partout (coupe, légendes, couches QGIS) : persistance + signal de
        rafraîchissement dans la foulée, sans attendre « OK »."""
        key = self.domain_combo.currentData()
        domain = self.repository.domains.get(key)
        if not domain or row < 0:
            return
        raw_item = self.table.item(row, 0)
        if not raw_item:
            return
        entry = domain.entries.get(raw_item.data(Qt.UserRole))
        if entry is None:
            return
        entry.visible = bool(checked)
        self._persist()

    # ------------------------------------------------------------------
    # Persistence/close
    # ------------------------------------------------------------------
    def _mark_custom_changes(self):
        baseline = ReferenceRepository.from_dict(self._baseline)
        for key, domain in self.repository.domains.items():
            old_domain = baseline.domains.get(key)
            for raw_code, entry in domain.entries.items():
                old = old_domain.entries.get(raw_code) if old_domain else None
                if ((key, raw_code) in self._reset_entries):
                    continue
                if old and entry.to_dict() != old.to_dict():
                    entry.automatic = False

    def _persist(self) -> bool:
        """v2.7.10.1 — sauvegarde blindée ET signal de synchro garanti.

        Cause racine du « rien ne se passe » : en 2.7.9.4, un ``return``
        placé dans le try rendait le code de queue INATTEIGNABLE — le
        signal ``reference_saved`` (qui déclenche le rafraîchissement de
        la coupe, des légendes et des couches QGIS) n'était JAMAIS émis.
        Le dialogue enregistrait sur le disque, mais n'avertissait plus
        personne. L'émission est désormais DANS le try, avant tout
        retour — et un test statique verrouille ce pattern.
        """
        try:
            self._store_detail()
            self._save_table_to_repository()
            self._mark_custom_changes()
            for domain in self.repository.domains.values():
                for entry in domain.entries.values():
                    entry.newly_discovered = False
            self.project.save_reference_repository(self.repository)
            # One-way compatibility mirror; current views read the reference.
            lithology = self.repository.domains.get("lithology")
            if lithology:
                self.project.config["litho_styles"] = {
                    code: {"color": entry.color, "pattern": entry.pattern}
                    for code, entry in lithology.entries.items()
                }
            self.project.save_config()
            self._baseline = self.repository.to_dict()
            self._reset_entries.clear()
            self.reference_saved.emit(self.domain_combo.currentData() or "")
            return True
        except Exception as error:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Référentiel : enregistrement impossible", error)
            QMessageBox.warning(
                self, QCoreApplication.translate("ReferenceDialog", "Enregistrement impossible"),
                self.tr("Le Référentiel n'a pas pu être enregistré :"
                        "\n{}").format(error))
            return False

    def _apply(self, *_args):
        self._persist()
        self._load_current_domain()

    def _accept(self, *_args):
        # v2.7.9.4 — ne fermer que si la persistance a réussi : une
        # erreur d'enregistrement ne fait plus sortir QGIS en silence.
        if self._persist():
            self.accept()

    def _is_dirty(self):
        try:
            self._store_detail()
            self._save_table_to_repository()
            return self.repository.to_dict() != self._baseline
        except RuntimeError:
            # v2.7.9.4 — widget Qt détruit pendant la fermeture : on
            # considère prudemment qu'il n'y a rien à sauvegarder plutôt
            # que de faire planter la fermeture.
            return False

    def reject(self):
        if self._is_dirty():
            answer = QMessageBox.question(
                self, QCoreApplication.translate("ReferenceDialog", "Modifications non enregistrées"),
                QCoreApplication.translate("ReferenceDialog", "Fermer sans enregistrer les modifications du Référentiel ?"),
                QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Cancel)
            if answer != QMessageBox.Discard:
                return
        super().reject()
