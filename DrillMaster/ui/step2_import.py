"""
DrillMaster — Step 2: CSV Import
"""
from __future__ import annotations

import os
from typing import Optional

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QGroupBox, QFrame, QFileDialog, QDialog, QScrollArea,
    QSplitter, QSizePolicy, QRadioButton,
)
from qgis.PyQt.QtGui import QDragEnterEvent, QDropEvent, QColor

from ..core.csv_parser import (
    parse_csv_file, infer_lithology_structure,
    ParseResult)
from ..core.data_model import NUMERIC_FIELDS, REQUIRED_FIELDS
from ..core.import_detect import (
    FILE_TYPE_LABELS, detect_file_type, expand_dropped_paths)
from ..core.organisation import organisation_question
from ..core.family_status import (
    EMPTY, WARNING, BLOCKING, QUESTION, FamilyStatus,
    MAPPING, ERRORS, WARNINGS, QUESTION_ORGANISATION,
    SEVERITY_BORDER, SEVERITY_TEXT,
    badge_count, badge_rendu, combine)
from ..core.track_bands import SPLIT_CONTENT_FIELDS
from ..core.data_registry import ImportStructureProfile
from ..core.validation import (
    validate_collar, validate_survey, validate_intervals,
    validate_structure, validate_imagery, validate_geotech,
    validate_geotech_cross,
    auto_survey_for_vertical, ImportBundle, ValidationResult,
)
from ..core.validation_groups import (
    SEVERITY_FILTERS, cap_groups, count_by_severity, filter_by_severity,
    filter_labels, group_issues, normalise_severity, overflow_summary,
    show_info_lines)
from .styles_qt import (
    apply_combo_popup_style, COLORS, BUTTON_COMPACT, BUTTON_SECONDARY,
    TAB_STYLE, TABLE_STYLE, INPUT_STYLE, TOOLTIP_STYLE,
)
from .csv_editor import CsvEditorDialog
from .lithology_structure_dialog import LithologyStructureDialog

MAPPABLE_FIELDS = {
    "collar":      ["hole_id", "collar_x", "collar_y", "collar_z", "depth", "azimuth", "dip", "hole_type"],
    "survey":      ["hole_id", "depth", "azimuth", "dip"],
    "litho":       [
        "hole_id", "from", "to", "lithology", "lithology_primary",
        "lithology_secondary", "lithology_role",
        "lithology_proportion", "secondary_proportion"],
    "assays":      ["hole_id", "from", "to"],
    "alterations": ["hole_id", "from", "to", "alteration", "intensity"],
    "mineralizations": [
        "hole_id", "from", "to", "mineralization_style", "minerals",
        "intensity", "confidence"],
    "structure": [
        "hole_id", "depth", "type", "dip", "dip_direction", "alpha",
        "beta", "confidence", "comment"],
    "imagery": [
        "hole_id", "from", "to", "image_path", "material", "orientation",
        "comment"],
}
TAB_LABELS = {
    "collar": "Collets", "survey": "Déviations", "litho": "Lithologie",
    "assays": "Teneurs", "alterations": "Altérations",
    "mineralizations": "Minéralisations",
    "structure": "Structures observées",
    "imagery": "Imagerie",
    "rqd": "RQD",
    "recovery": "Récupération",
    "density": "Densité",
}
TAB_ORDER = [
    "collar", "survey", "litho", "assays", "alterations",
    "mineralizations", "structure", "imagery",
    "rqd", "recovery", "density"]

# v2.9.269 — AFFICHAGE des cartes de statut (pastilles) de l'étape 2 :
# regroupement par CATÉGORIE MÉTIER (retour écran : 11 domaines rangés en
# ordre chronologique d'ajout au projet = difficile à scanner d'un coup
# d'œil).  PUREMENT VISUEL : ni l'ordre des onglets (``TAB_ORDER``), ni la
# validation, ni les données ne changent — seule la présentation des
# pastilles est groupée, avec un sous-titre par catégorie.
# Toute famille absente de ces groupes retombe dans « Autres » : ajouter un
# domaine au plugin ne peut jamais faire disparaître sa pastille.
CHIP_GROUPS = (
    ("Géométrie du forage", ("collar", "survey")),
    ("Géologie", ("litho", "alterations", "mineralizations", "structure")),
    ("Géochimie", ("assays",)),
    ("Géotechnique", ("rqd", "recovery", "density")),
    ("Média", ("imagery",)),
)
# File types offering the explicit "several codes in one cell" question
# (AM-06) : lithology has the full 4-mode dialog; these get the targeted
# question only.
SPLIT_QUESTION_TYPES = tuple(SPLIT_CONTENT_FIELDS.keys())
DOMAIN_QUESTION_WORDS = {
    "litho": "plusieurs lithologies",
    "alterations": "plusieurs altérations",
    "mineralizations": "plusieurs minéraux",
}
# v2.7.12.3 — phrases de la question large par famille (accord de genre :
# la lithologie est féminine, le code masculin).
DOMAIN_WIDE_PHRASES = {
    "litho": ("Une seule lithologie par intervalle", "porte la lithologie",
              "comme une lithologie"),
    "alterations": ("Un seul code par intervalle", "porte le code",
                    "comme un code"),
    "mineralizations": ("Un seul code par intervalle", "porte le code",
                        "comme un code"),
}
STRUCTURE_TYPES = ("litho",) + SPLIT_QUESTION_TYPES

FIELD_LABELS = {
    "hole_id": "Identifiant du forage",
    "collar_x": "Coordonnée X du collet",
    "collar_y": "Coordonnée Y du collet",
    "collar_z": "Altitude Z du collet",
    "depth": "Profondeur",
    "azimuth": "Azimut",
    "dip": "Pendage",
    "from": "Depuis (FROM)",
    "to": "Jusqu’à (TO)",
    "lithology": "Lithologie",
    "lithology_primary": "Lithologie principale",
    "lithology_secondary": "Lithologie secondaire",
    "lithology_role": "Rôle du composant",
    "lithology_proportion": "Proportion du composant",
    "secondary_proportion": "Proportion secondaire",
    "alteration": "Altération",
    "intensity": "Intensité",
    "mineralization_style": "Style de minéralisation",
    "minerals": "Minéraux",
    "confidence": "Confiance",
    "type": "Type de structure",
    "dip_direction": "Direction du pendage",
    "alpha": "Angle alpha",
    "beta": "Angle bêta",
    "comment": "Commentaire",
    # v2.9.262 — imagerie (Chantier 2).
    "image_path": "Chemin de l'image",
    "material": "Matériau (étiquette)",
    "orientation": "Orientation de l'image",
    # v2.9.264 — géotechnique (Chantier 3).
    "value": "Valeur",
    "unit": "Unité de mesure",
    "kind": "Indicateur (RQD / récupération / densité)",
}


class DropZone(QFrame):
    file_dropped = pyqtSignal(str)
    files_dropped = pyqtSignal(list)  # v2.7.6 — dépôt groupé / dossier

    def __init__(self, parent=None, multi=False, empty_label=None):
        super().__init__(parent)
        self.multi = multi
        self._empty_label = empty_label or self.tr(
            "Glissez un fichier CSV ici ou cliquez sur Parcourir")
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        # v2.9.99 — zone compacte, hauteur alignée sur le bouton Parcourir
        # (plus de bande trop haute vs pastilles / dock étroit).
        if self.multi:
            self.setMinimumHeight(40)
            self.setMaximumHeight(48)
        else:
            self.setMinimumHeight(34)
            self.setMaximumHeight(40)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px dashed {COLORS['border_dark']};
                border-radius: 3px;
                background-color: {COLORS['bg_card']};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 6, 4)
        layout.setSpacing(8)

        self.label = QLabel(self._empty_label)
        self.label.setWordWrap(True)
        self.label.setMinimumWidth(80)
        self.label.setStyleSheet(
            f"color: {COLORS['text_light']}; font-size: 8pt; "
            f"background: transparent;")
        layout.addWidget(self.label, 1)

        self.btn = QPushButton(self.tr("Parcourir"))
        # v2.7.6.4 (UI-02) : INPUT_STYLE ne décrit aucun QPushButton — le
        # bouton retombait sur le thème sombre de QGIS et apparaissait noir.
        # v2.9.99 — bouton compact, même hauteur visuelle que la zone.
        self.btn.setStyleSheet(
            BUTTON_SECONDARY
            + "QPushButton { padding: 3px 10px; font-size: 8pt; "
            "min-height: 22px; max-height: 26px; }")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setMinimumWidth(78)
        self.btn.setMaximumWidth(96)
        self.btn.setFixedHeight(26)
        self.btn.clicked.connect(self._browse)
        layout.addWidget(self.btn, 0, Qt.AlignVCenter)

    def _browse(self, *_args):
        if self.multi:
            paths, _ = QFileDialog.getOpenFileNames(
                self, self.tr("Importer des CSV"), "",
                self.tr("CSV (*.csv *.txt);;Tous fichiers (*)"))
            if paths:
                self.files_dropped.emit(paths)
            return
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Importer CSV"), "",
            self.tr("CSV (*.csv *.txt);;Tous fichiers (*)"))
        if path:
            self.file_dropped.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"QFrame {{ border: 1px solid {COLORS['success']}; border-radius: 3px; background: #EAFAF1; }}")

    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"QFrame {{ border: 1px dashed {COLORS['border_dark']}; border-radius: 3px; background: {COLORS['bg_card']}; }}")

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [
            url.toLocalFile() for url in urls if url.toLocalFile()]
        if self.multi:
            if paths:
                self.files_dropped.emit(paths)
        elif len(paths) > 1:
            # Plusieurs fichiers sur une zone d'onglet : on délègue à la
            # répartition automatique plutôt que d'en ignorer.
            self.files_dropped.emit(paths)
        elif paths:
            path = paths[0]
            if path.lower().endswith(('.csv', '.txt')):
                self.file_dropped.emit(path)
        event.acceptProposedAction()
        self.dragLeaveEvent(event)

    def set_loaded(self, fn):
        self.label.setText(os.path.basename(fn))

    def reset(self):
        """Restore the empty drop zone (new or switched project)."""
        self.label.setText(self._empty_label)


def _tr(text):
    """v2.9.247 — Lot i18n : traduction des fonctions MODULE de ce
    fichier (contexte ImportTab — les mêmes textes que la classe)."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("ImportTab", text)


def _validation_group_translate(text):
    """v2.9.258 — messages de validation groupée (labels/infobulles)
    traduits via Qt (contexte ValidationMessages, i18n/drillmaster_en.ts).
    En français, aucun traducteur n'est installé → texte source.
    En anglais, une entrée manquante rendrait le français : la garde de
    complétude du .ts couvre chaque libellé de core.validation_groups."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("ValidationMessages", text)


def _validation_english_mode() -> bool:
    """Vrai si l'interface anglaise est active (QSettings).

    ``load_language_setting()`` est volontairement sans échec (repli
    français) ; aucun except large à poser ici."""
    from ..core.i18n import load_language_setting
    return load_language_setting() == "en"


# v2.9.258 — messages du PARSEUR CSV (pr.errors) utilisés tels quels par
# la ligne de statut de l'onglet.  En anglais, ils sont traduits à
# l'affichage (mêmes gabarits que i18n/drillmaster_en.ts).
import re as _re_parse

_PARSE_ERROR_TEMPLATES = (
    (
        "Ligne {line}: {actual} cellule(s) pour {expected} en-tête(s). "
        "Aucune valeur ne sera tronquée.",
        "Ligne {line}: {actual} cellule(s) pour {expected} en-tête(s). "
        "Aucune valeur ne sera tronquée.",
        (("line", r"\d+"), ("actual", r"\d+"), ("expected", r"\d+")),
    ),
    (
        "Fichier introuvable : {path}",
        "Fichier introuvable : {path}",
        (("path", r".+"),),
    ),
    (
        "Fichier vide.",
        "Fichier vide.",
        (),
    ),
    (
        "Fichier vide (aucune ligne).",
        "Fichier vide (aucune ligne).",
        (),
    ),
    (
        "En-tête dupliqué '{header}' aux colonnes {first} et {second}.",
        "En-tête dupliqué '{header}' aux colonnes {first} et {second}.",
        (("header", r".+"), ("first", r"\d+"), ("second", r"\d+")),
    ),
)


def _regex_from_template(template: str, captures):
    """Construit l'expression de correspondance de la source française.

    Le gabarit est celui traduit dans ``drillmaster_en.ts`` ; les
    ``{}`` deviennent leurs groupes d'extraction.  Les littéraux
    français restent donc les SOURCES du .ts (jamais des chaînes
    flottantes en alpha).
    """
    escaped = _re_parse.escape(template)
    for name, pattern in captures:
        escaped = escaped.replace(r"\{%s\}" % name, "(%s)" % pattern)
    return _re_parse.compile("^" + escaped + "$")


_PARSE_ERROR_PATTERNS = tuple(
    (
        _regex_from_template(regex_template, captures),
        translation,
        tuple(name for name, _pattern in captures),
    )
    for regex_template, translation, captures in _PARSE_ERROR_TEMPLATES
)


def _translate_parse_message(message: str) -> str:
    """Traduit un message de ParseResult.errors en mode anglais en le
    rapprochant d'un gabarit connu (repli : message source français)."""
    if not _validation_english_mode():
        return message
    for pattern, template, names in _PARSE_ERROR_PATTERNS:
        match = pattern.match(message or "")
        if match:
            values = dict(zip(names, match.groups()))
            parsed = _validation_group_translate(template)
            try:
                return parsed.format(**values)
            except (KeyError, IndexError, ValueError):
                return message
    return message


def _preview_hint_text(num_rows: int, suffix: str = "") -> str:
    """v2.7.12.6 — revue écran : « Aperçu 10 / 3 ligne(s) » était absurde
    quand le fichier contient MOINS de 10 lignes ; on ne montre la
    fraction que quand il y a une fraction."""
    if num_rows <= 10:
        base = _tr("Aperçu — {} ligne(s)").format(num_rows)
    else:
        base = _tr("Aperçu 10 / {} lignes").format(num_rows)
    return f"{base}{suffix}" if suffix else base


class ImportTab(QWidget):
    def __init__(self, file_type, main_dock, parent=None, router=None):
        super().__init__(parent)
        self.file_type = file_type
        self.main_dock = main_dock
        # v2.7.6 — multi-file drops are forwarded to the step's router.
        self.router = router
        self.parse_result: Optional[ParseResult] = None
        self.validation_result: Optional[ValidationResult] = None
        self.editor_dialog: Optional[CsvEditorDialog] = None
        self.current_path = ""
        # v2.7.10.26 — Step2 est notifié dès que la visibilité de la
        # question d'organisation change (surlignage jaune de l'onglet).
        self.attention_callback = None
        self._build()

    def _build(self):
        # v2.7.6.2 (UI-01) — le contenu d'un onglet défile : dans un dock
        # court, zone de dépôt, organisation, aperçu et statut ne se
        # chevauchent plus, ils se parcourent.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.tab_scroll = QScrollArea()
        self.tab_scroll.setWidgetResizable(True)
        self.tab_scroll.setFrameShape(QFrame.NoFrame)
        # Jamais de défilement horizontal : c'est lui qui donnait
        # l'impression de textes coupés et superposés (revue écran).
        self.tab_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tab_scroll.setStyleSheet("background: transparent;")
        content = QWidget()
        # v2.7.12.8 — REVUE ÉCRAN (« infobulle noir sur noir ») : le
        # contexte de style d'une infobulle est le widget STYLÉ le plus
        # proche de l'élément survolé — pour le groupe « Colonnes à
        # vérifier », c'est CE cadre (ancêtre stylé) : sans la règle,
        # l'infobulle retombait sur la palette QGIS (noir sur noir).
        # TOOLTIP_STYLE est la définition unique (styles_qt). Ordre : la
        # règle d'infobulle en PREMIER — une déclaration sans sélecteur
        # (« background: transparent; ») placée AVANT l'ombrerait (vérifié
        # au rendu ; le CSS normal voudrait le contraire).
        content.setStyleSheet(TOOLTIP_STYLE + "background: transparent;")
        self.tab_scroll.setWidget(content)
        outer.addWidget(self.tab_scroll)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self._on_file)
        self.drop_zone.files_dropped.connect(self._on_files)
        layout.addWidget(self.drop_zone)

        self.info_label = QLabel(self.tr("Aucun fichier importé."))
        self.info_label.setObjectName("label_hint")
        # v2.7.12.8 — REVUE ÉCRAN (« chevauchements, éléments rognés au
        # bord du dock ») : sans wrap, la ligne « Encodage : … »
        # (≈ 500 px de sizeHint) ÉTIRAIT tout le contenu de l'onglet au-
        # delà de la largeur du dock — bouton « Parcourir », colonne
        # « Champ cible » et bouton « Options avancées » partaient dans
        # le mur (pas de défilement horizontal par conception). Le
        # texte passe sur deux lignes au lieu de casser la disposition.
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Mapping
        mg = QGroupBox(self.tr("▸ Colonnes reconnues — détails avancés"))
        self.mapping_group = mg
        mg.setCheckable(True)
        mg.setChecked(False)
        mg.setToolTip(self.tr("Colonnes · vérifier / corriger"))
        ml = QVBoxLayout(mg)
        ml.setContentsMargins(6, 6, 6, 6)
        self.mapping_table = QTableWidget(0, 2)
        self.mapping_table.setHorizontalHeaderLabels(
            [self.tr("En-tête"), self.tr("Champ cible")])
        # v2.7.12.8 — revue écran : les deux colonnes partagent la largeur
        # disponible (ResizeToContents laissait la colonne « Champ cible »
        # se rognée au bord du dock sur tableau large).
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # v2.7.11.6 / v2.7.12.8 — infobulles : la règle QToolTip a été
        # remontée à la racine (BASE_STYLE, cascade) — avant, elle était
        # déclarée ici ET dans TABLE_STYLE (double) ; le groupe
        # « Colonnes à vérifier » (hors table) restait sans règle
        # → encre noire sur fond sombre hérité du thème QGIS.
        self.mapping_table.setStyleSheet(TABLE_STYLE)
        self.mapping_table.setMaximumHeight(120)
        ml.addWidget(self.mapping_table)
        self.mapping_table.hide()
        mg.toggled.connect(self._toggle_mapping_details)
        layout.addWidget(mg)

        if self.file_type == "survey":
            # v2.9.286 — convention signée : choix explicite à l'import.
            dg = QGroupBox(self.tr("Convention du dip dans ce fichier"))
            dl = QVBoxLayout(dg)
            dl.setContentsMargins(6, 4, 6, 4)
            self.dip_standard = QRadioButton(self.tr(
                "Standard (négatif = bas, positif = haut)"))
            self.dip_historic = QRadioButton(self.tr(
                "Historique DrillMaster (positif = bas)"))
            self.dip_standard.setChecked(True)
            self.dip_choice_made = False
            self.dip_standard.toggled.connect(self._on_dip_choice)
            self.dip_historic.toggled.connect(self._on_dip_choice)
            dl.addWidget(self.dip_standard)
            dl.addWidget(self.dip_historic)
            self.dip_warning = QLabel("")
            self.dip_warning.setWordWrap(True)
            self.dip_warning.hide()
            dl.addWidget(self.dip_warning)
            layout.addWidget(dg)

        if self.file_type in STRUCTURE_TYPES:
            self.structure_widget = QFrame()
            self.structure_widget.setStyleSheet(
                f"QFrame {{ background:{COLORS['bg_card']}; "
                f"border:1px solid {COLORS['border']}; border-radius:3px; }}")
            structure_layout = QVBoxLayout(self.structure_widget)
            structure_layout.setContentsMargins(7, 6, 7, 6)
            structure_layout.setSpacing(5)

            structure_row = QHBoxLayout()
            self.structure_label = QLabel(
                self.tr("Organisation : en attente d’un fichier"))
            self.structure_label.setWordWrap(True)
            self.structure_label.setStyleSheet(
                f"color:{COLORS['text_medium']}; background:transparent;")
            structure_row.addWidget(self.structure_label, 1)
            self.structure_button = QPushButton(self.tr("Options avancées…"))
            self.structure_button.setStyleSheet(BUTTON_SECONDARY)
            self.structure_button.setEnabled(False)
            self.structure_button.setToolTip(self.tr("Organisation · si détection incorrecte"))
            self.structure_button.clicked.connect(self._edit_structure)
            # v2.7.11.6 — retour écran (« ya pas options avancés pour
            # mineralisation et alteration ? ») : les pistes codées ont
            # leur propre dialogue d'organisation (DomainStructureDialog,
            # sans rôles ni proportions — AM-05).  Lithologie garde le
            # dialogue complet 4 modes.
            self.structure_button.setVisible(
                self.file_type in STRUCTURE_TYPES)
            structure_row.addWidget(self.structure_button)
            structure_layout.addLayout(structure_row)

            self.composite_widget = QFrame()
            self.composite_widget.setStyleSheet(
                "QFrame { background:#FEF9E7; border:1px solid #F7DC6F; "
                "border-radius:3px; }")
            composite_layout = QVBoxLayout(self.composite_widget)
            composite_layout.setContentsMargins(7, 6, 7, 6)
            composite_layout.setSpacing(5)
            self.composite_label = QLabel()
            self.composite_label.setWordWrap(True)
            self.composite_label.setStyleSheet(
                f"color:{COLORS['text_dark']}; background:transparent;")
            composite_layout.addWidget(self.composite_label)
            # v2.7.12.8 — revue écran (« certains éléments prennent trop
            # d'espaces, chevauchements ») : les deux boutons de la
            # question d'organisation côte à côte exigeaient ≈ 590 px de
            # LARGEUR MINIMUM (« Une seule colonne porte le code » +
            # « Lire chaque colonne comme un code ») — l'onglet entier
            # dépassait le dock étroit. Empilés, un seul bouton à la
            # fois (≈ 290 px max) : toujours lisible, jamais rogné.
            composite_actions = QVBoxLayout()
            composite_actions.setSpacing(4)
            self.keep_composite_button = QPushButton(self.tr("Conserver comme un code"))
            self.keep_composite_button.setStyleSheet(BUTTON_SECONDARY)
            self.keep_composite_button.clicked.connect(
                self._keep_composite_values)
            composite_actions.addWidget(self.keep_composite_button)
            self.split_composite_button = QPushButton(self.tr("Séparer sur « / »…"))
            self.split_composite_button.setStyleSheet(BUTTON_SECONDARY)
            self.split_composite_button.clicked.connect(
                self._configure_composite_values)
            composite_actions.addWidget(self.split_composite_button)
            composite_layout.addLayout(composite_actions)
            structure_layout.addWidget(self.composite_widget)
            self.composite_widget.hide()
            layout.addWidget(self.structure_widget)

        # Preview
        # v2.7.12.10 — retour écran (« pq mineralisations me dit dans
        # Données CSV ? ») : le libellé « Données CSV » ne disait pas ce
        # que c'était. Le groupe est un APERÇU LECTURE SEULE du fichier —
        # dit en clair dans le titre (le détail est dans le libellé
        # d'aperçu et le bouton « Éditeur CSV »).
        pg = QGroupBox(self.tr("Aperçu du fichier — lecture seule"))
        pl = QVBoxLayout(pg)
        pl.setContentsMargins(6, 6, 6, 6)
        editor_row = QHBoxLayout()
        self.preview_hint = QLabel(self.tr("Aperçu des 10 premières lignes"))
        self.preview_hint.setObjectName("label_hint")
        # v2.7.12.8 — revue écran : sans wrap, « Aperçu 10 / 443 lignes —
        # édition complète disponible » (≈ 330 px de minimum) forçait le
        # groupe « Données CSV » à 467 px de largeur mini — tout le
        # contenu de l'onglet dépassait le dock étroit.
        self.preview_hint.setWordWrap(True)
        editor_row.addWidget(self.preview_hint)
        editor_row.addStretch()
        # v2.7.12.6 — revue écran : « Ouvrir l'éditeur complet » était
        # tronqué (« Ouvrir l'éditeur compl… ») ; libellé court stable.
        self.editor_btn = QPushButton(self.tr("Éditeur CSV"))
        self.editor_btn.setStyleSheet(BUTTON_SECONDARY)
        self.editor_btn.setEnabled(False)
        self.editor_btn.clicked.connect(self._open_editor)
        editor_row.addWidget(self.editor_btn)
        pl.addLayout(editor_row)
        self.preview_table = QTableWidget(0, 0)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # v2.7.12.10 — revue écran (« on voit pas bien les noms de
        # colonnes ») : 8 colonnes partagées sur ~400 px, les en-têtes
        # rogeaient à 42 px. Largeur MINIMUM par colonne (56 px) : quand
        # la somme dépasse le dock, la TABLE fait défiler HORIZONTALEMENT
        # elle-même (le tab reste sans défilement horizontal) — chaque
        # nom se lit en entier, plus l'infobulle d'en-tête (v2.7.12.9).
        self.preview_table.horizontalHeader().setMinimumSectionSize(56)
        self.preview_table.setStyleSheet(TABLE_STYLE)
        self.preview_table.setMaximumHeight(160)
        # v2.7.12.9 — RETOUR ÉCRAN (« on peut modifier comme on veut, c'est
        # normal ? ») : l'aperçu héritait des drapeaux Qt par défaut —
        # les cellules semblaient ÉDITABLES, mais aucune modification
        # n'était enregistrée : elle disparaissait au prochain remplissage,
        # sans aucune annonce. Un grille « éditable » qui ne fait rien est
        # un piège : l'aperçu est en LECTURE SEULE, et l'outil de
        # modification réel est le bouton « Éditeur CSV » (au-dessus).
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview_table.setToolTip(self.tr("Aperçu lecture seule · édition = Éditeur CSV"))
        pl.addWidget(self.preview_table)
        layout.addWidget(pg)

        self.status_label = QLabel(self.tr(""))
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 9pt; background: transparent;")
        layout.addWidget(self.status_label)
        layout.addStretch()

    def _toggle_mapping_details(self, expanded):
        self.mapping_table.setVisible(bool(expanded))
        # Chevron explicite : on voit d'un coup d'œil si le bloc est
        # ouvert, même si le thème dessine mal la case (UI-02).
        title = self.mapping_group.title().lstrip("▸▾ ").strip()
        self.mapping_group.setTitle(
            f"{'▾' if expanded else '▸'} {title}")

    def _mapping_needs_attention(self):
        if not self.parse_result:
            return False
        mapped = set(self.parse_result.effective_mappings.values())
        required = set(REQUIRED_FIELDS.get(self.file_type, ()))
        structure = self.parse_result.structure
        if structure.mode in {"wide_components", "delimited_components"}:
            required.discard("lithology")
            # v2.7.11.6 — même exemption pour les pistes codées à
            # organisation confirmée : le contenu vient des colonnes de
            # l'organisation, l'écran ne réclame plus le champ canonique.
            if structure.confirmed and self.file_type in {
                    "alterations", "mineralizations"}:
                required.discard(SPLIT_CONTENT_FIELDS[self.file_type]
                                 if self.file_type == "alterations"
                                 else "mineralization_style")
        # v2.9.302 — conflit VIVANT : une colonne tranchée par
        # l'utilisateur (mappée OU « Ignorer ») n'est plus « en conflit » ;
        # le flou initial du fuzzy-match ne survit pas au choix (retour
        # écran : Litho_Source à Ignorer mais bandeau « en conflit »).
        return bool(required - mapped or self._live_conflicts())

    def _live_conflicts(self):
        # v2.9.311 — délégué à core.csv_parser.live_mapping_conflicts :
        # une colonne d'une organisation CONFIRMÉE a un rôle (code) :
        # elle n'est ni ambiguë ni « deux colonnes sur le même champ ».
        from ..core.csv_parser import live_mapping_conflicts
        return live_mapping_conflicts(self.parse_result)

    def _refresh_mapping_attention_ui(self):
        """v2.7.12.11 — UNIQUE écrivain du TITRE du bloc et de la LIGNE
        DE STATUT (état des colonnes) — même principe que
        ``_refresh_tab_badges`` pour la pastille.

        Appelé par TOUS les chemins qui peuvent changer l'état des
        colonnes : l'import (``show_parse_result``), le changement de
        colonne (``_on_map_change``) et la RÉPONSE à la question
        d'organisation (``_save_structure_profile``).

        Avant v2.7.12.11, seul l'import et le changement de colonne
        mettaient à jour : après avoir répondu à la question (ex.
        « lire chaque colonne comme un code » pour Style_1/Style_2), le
        fichier était PROPRE mais le bloc continuait d'afficher
        « Colonnes à vérifier / ouvrez le bloc » — obsolète (retour
        écran : « l'organisation que j'ai validée, c'est quoi ? »).
        """
        if not self.parse_result:
            return
        needs_attention = self._mapping_needs_attention()
        # v2.7.12.8 — le chevron reflète l'ÉTAT RÉEL du bloc (l'usage
        # contrôle l'ouverture), jamais l'attention ; le bloc ne s'ouvre
        # plus tout seul.
        marker = "▾" if self.mapping_group.isChecked() else "▸"
        self.mapping_group.setTitle(
            self.tr("{} Colonnes à vérifier").format(marker)
            if needs_attention
            else self.tr("{} Colonnes reconnues — détails avancés")
            .format(marker))
        pr = self.parse_result
        # v2.7.6 — coche verte lisible sans ouvrir les détails (critère
        # du jalon : « toutes les colonnes sont reconnues »).
        if needs_attention:
            # v2.9.300 — « y'a une incohérence » : le bandeau parlait des
            # COLONNES (mappage) pendant que l'Éditeur CSV disait
            # « Validation OK » (données) → lu comme une contradiction.
            # Désormais : NOMMER les colonnes en cause + état des données,
            # les deux vérifications sont explicites et complémentaires.
            mapped = set(pr.effective_mappings.values())
            required = set(REQUIRED_FIELDS.get(self.file_type, ()))
            missing = sorted(required - mapped)
            amb = self._live_conflicts()
            why = []
            if missing:
                why.append(self.tr("manquantes : {}")
                           .format(", ".join(missing)))
            if amb:
                why.append(self.tr("en conflit : {}")
                           .format(", ".join(amb)))
            message = self.tr("⚠ Colonnes à vérifier (mappage)")
            if why:
                message += " — " + " · ".join(why)
            message += " " + self.tr(
                "— ouvrez le bloc « Colonnes à vérifier » ci-dessus.")
            vr = getattr(self, "validation_result", None)
            if vr is not None:
                n_err = sum(1 for i in vr.issues if i.severity == "error")
                n_warn = sum(1 for i in vr.issues
                             if i.severity == "warning")
                message += " " + self.tr(
                    "· données ({} enreg.) : {} erreur(s) · {} "
                    "avertissement(s) — voir l'Éditeur CSV").format(
                        pr.num_rows, n_err, n_warn)
            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"font-size: 9pt; color: {COLORS['warning']}; background: transparent;")
        else:
            # v2.9.273 — retour écran : « Toutes les colonnes sont reconnues »
            # (mappage) alors que la pastille comptait des avertissements.  On
            # affiche AUSSI le compte de validation pour que le badge et le
            # pied de page ne se contredisent plus.
            message = self.tr("✓ Toutes les colonnes sont reconnues — "
                              "{} enregistrements.").format(pr.num_rows)
            colour = COLORS["success"]
            vr = getattr(self, "validation_result", None)
            if vr is not None:
                n_err = sum(1 for i in vr.issues if i.severity == "error")
                n_warn = sum(1 for i in vr.issues if i.severity == "warning")
                if n_err or n_warn:
                    message += " " + self.tr(
                        "· {} erreur(s) · {} avertissement(s) — voir le "
                        "panneau Validation.").format(n_err, n_warn)
                    colour = COLORS["danger"] if n_err else COLORS["warning"]
            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"font-size: 9pt; color: {colour}; background: transparent;")

    def reset(self):
        """Return the tab to its initial empty state.

        Without this, creating or opening another project kept showing the
        previous project's file, preview, mapping and organisation summary.
        """
        if self.editor_dialog:
            self.editor_dialog.close()
            self.editor_dialog = None
        self.parse_result = None
        self.validation_result = None
        self.current_path = ""
        self.drop_zone.reset()
        self.info_label.setText(self.tr("Aucun fichier importé."))
        self.info_label.setStyleSheet("")
        self.mapping_group.setTitle(self.tr("▸ Colonnes reconnues — détails avancés"))
        self.mapping_group.setChecked(False)
        self.mapping_table.setRowCount(0)
        if self.file_type in STRUCTURE_TYPES:
            self.structure_label.setText(
                self.tr("Organisation : en attente d’un fichier"))
            self.structure_button.setEnabled(False)
            self.composite_widget.hide()
        self.preview_hint.setText(self.tr("Aperçu des 10 premières lignes"))
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.editor_btn.setEnabled(False)
        self.status_label.setText(self.tr(""))
        # v2.7.12.6 — la pastille repasse à l'état « pas de fichier ».
        cb = getattr(self, "attention_callback", None)
        if cb:
            cb()

    def show_parse_result(self, path, pr, validate=True):
        """Display an already-computed ParseResult in the tab UI."""
        self.parse_result = pr
        self.current_path = path or pr.file_path
        self.editor_btn.setEnabled(True)
        self.preview_hint.setText(
            _preview_hint_text(
                pr.num_rows, self.tr(" — édition complète disponible")))
        self.drop_zone.set_loaded(path)
        self.info_label.setText(
            self.tr("Encodage : {} | Séparateur : {} | "
                    "Décimale : {} | {} lignes").format(
                pr.encoding, repr(pr.separator),
                pr.decimal_sep, pr.num_rows))
        self.info_label.setStyleSheet(f"font-size: 8pt; color: {COLORS['text_dark']}; background: transparent;")
        self._fill_mapping()
        # v2.7.12.11 — titre du bloc + ligne de statut : un seul écrivain
        # (_refresh_mapping_attention_ui), appelé aussi par la réponse à
        # la question d'organisation (avant, c'est là qu'ils
        # vieillissaient — « ouvrez le bloc » alors que tout était réglé).
        self._refresh_mapping_attention_ui()
        self._fill_preview()
        if self.file_type in STRUCTURE_TYPES:
            self.structure_button.setEnabled(
                self.file_type in STRUCTURE_TYPES)
            self._update_structure_ui()
        # v2.7.12.6 — le badge (pastille) réagit au DÉPÔT du fichier
        # (état des colonnes), pas seulement à la validation : un
        # problème est visible dès qu'il existe.
        cb = getattr(self, "attention_callback", None)
        if cb:
            cb()
        if validate:
            self.main_dock.step2_validate_all()

    def _on_files(self, paths):
        """Multi-file / folder drop : route via the step-level assistant."""
        paths = [path for path in paths if path]
        if not paths:
            return
        if len(paths) == 1:
            self._on_file(paths[0])
        elif self.router:
            self.router(paths)
        else:
            self._on_file(paths[0])

    def _reject_file(self, path, *messages):
        """Refuse un fichier en nommant clairement celui qui est rejeté.

        v2.9.258 — RETOUR ÉCRAN : quand on « Browse » un fichier qui
        échoue à la lecture, l'onglet conservait le nom de l'ancien
        fichier valide (ex. « structure.csv ») alors que la ligne de
        statut parlait du NOUVEAU fichier.  L'utilisateur croyait donc
        que le plugin restait bloqué sur un fichier qui n'était pas le
        sien.  Ici le nom du fichier tenté, le compteur et l'aperçu
        sont remis à l'état « rejeté » : statut + nom concordent.
        """
        name = os.path.basename(path) if path else ""
        self.current_path = path or ""
        self.parse_result = None
        self.validation_result = None
        if self.editor_dialog:
            self.editor_dialog.close()
            self.editor_dialog = None
        self.drop_zone.set_loaded(path) if path else self.drop_zone.reset()
        self.mapping_group.setTitle(self.tr("▸ Colonnes reconnues — détails avancés"))
        self.mapping_group.setChecked(False)
        self.mapping_table.setRowCount(0)
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.preview_hint.setText(self.tr("Aperçu indisponible"))
        self.editor_btn.setEnabled(False)
        if self.file_type in STRUCTURE_TYPES:
            self.structure_button.setEnabled(False)
            self.structure_label.setText(
                self.tr("Organisation — fichier rejeté"))
            self.composite_widget.hide()
        self.info_label.setText(
            self.tr("Lecture impossible — {}").format(name)
            if name else self.tr("Aucun fichier importé."))
        self.info_label.setStyleSheet(
            f"font-size: 8pt; color: {COLORS['danger']}; background: transparent;")
        self.status_label.setText(" ".join(messages))
        self.status_label.setStyleSheet(
            f"font-size: 9pt; color: {COLORS['danger']}; background: transparent;")
        cb = getattr(self, "attention_callback", None)
        if cb:
            cb()

    def _on_dip_choice(self, *_):
        self.dip_choice_made = True
        self._refresh_dip_warning()

    def survey_dip_convention(self) -> str:
        hist = getattr(self, "dip_historic", None)
        return ("historique"
                if hist is not None and hist.isChecked() else "standard")

    def _survey_dip_values(self, pr) -> list:
        maps = pr.effective_mappings
        idx = None
        for i, h in enumerate(pr.raw_headers):
            if str(maps.get(h) or h).casefold() == "dip":
                idx = i
        out = []
        if idx is None:
            return out
        for row in pr.rows or []:
            if isinstance(row, (list, tuple)) and idx < len(row):
                try:
                    out.append(float(str(row[idx]).strip()))
                except ValueError:
                    continue
        return out

    def dip_hint(self) -> str:
        pr = self.parse_result
        if pr is None or self.file_type != "survey":
            return ""
        dips = self._survey_dip_values(pr)
        if not dips:
            return ""
        if all(d > 0 for d in dips):
            return "all_positive"
        if any(d > 0 for d in dips):
            return "mixed"
        return "all_negative"

    def _refresh_dip_warning(self):
        warn = getattr(self, "dip_warning", None)
        if warn is None:
            return
        if self.dip_hint() == "all_positive":
            warn.setText(self.tr(
                "Tous les dips de ce fichier sont positifs. S'agit-il de "
                "trous vers le bas (convention historique) ou de trous "
                "réellement remontants ? Confirmez la convention avant "
                "de continuer."))
            warn.setStyleSheet("color:#D68910;")
            warn.show()
        else:
            warn.hide()

    def _on_file(self, path):
        if not os.path.isfile(path):
            self._reject_file(
                path, self.tr("Fichier introuvable."))
            return

        project = self.main_dock.project
        saved = project.get_mappings(self.file_type) if project else {}
        record = project.get_data_registry().get(self.file_type) if project else None
        structure = (
            record.structure
            if record and record.structure.is_configured else None)
        # v2.7.6 (IMP-02) : les corrections passées enseignent le projet.
        learned = project.get_learned_synonyms() if project else None
        pr = parse_csv_file(
            path, self.file_type, saved, structure=structure,
            extra_synonyms=learned)

        if pr.errors:
            self._reject_file(
                path,
                *( _translate_parse_message(error)
                   for error in pr.errors))
            return

        if self.main_dock.project:
            self.main_dock.project.record_import(
                self.file_type, path, pr.encoding,
                pr.separator, pr.decimal_sep,
                headers=pr.raw_headers,
                mappings=pr.effective_mappings,
                structure=pr.structure)
            self.main_dock.project.save_mappings(
                self.file_type, pr.effective_mappings)

        self.show_parse_result(path, pr)
        if self.file_type == "survey":
            self.dip_choice_made = False
            self._refresh_dip_warning()

    def _fill_mapping(self):
        pr = self.parse_result
        if not pr:
            return
        mappable = MAPPABLE_FIELDS.get(self.file_type, [])
        # v2.7.11.6 — retour écran (« champs cible est ignorés pour
        # Alteration_1/…, on comprend pas ») : une colonne qui appartient
        # à l'organisation confirmée n'est pas « à mapper » — la cible
        # affiche son rôle structurel au lieu de « — Ignorer — ».
        organisation_headers = {}
        profile = pr.structure
        if profile.confirmed and profile.mode == "wide_components":
            for order, component in enumerate(profile.component_columns,
                                              start=1):
                organisation_headers[str(component.code_column)] = (
                    self.tr("Colonne de codes n°{} (organisation large)")
                    .format(order))
        elif profile.confirmed and profile.mode == "delimited_components":
            if profile.code_column:
                organisation_headers[str(profile.code_column)] = (
                    self.tr("Colonne de codes — séparés sur « {} »")
                    .format(profile.delimiter or '/'))
        self.mapping_table.setRowCount(len(pr.raw_headers))
        for row, raw_h in enumerate(pr.raw_headers):
            item = QTableWidgetItem(raw_h)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            details = pr.mapping_details.get(raw_h, {})
            if details:
                confidence = round(float(details.get("confidence", 0.0)) * 100)
                if details.get("ambiguous"):
                    item.setToolTip(
                        f"Ambigu · {confidence} %")
                elif details.get("canonical"):
                    item.setToolTip(
                        f"Auto · {confidence} %")
            self.mapping_table.setItem(row, 0, item)
            if raw_h in organisation_headers:
                # Colonne absorbée par l'organisation : le rôle est écrit
                # noir sur blanc au lieu d'un combo trompeur « Ignorer ».
                from qgis.PyQt.QtWidgets import QLabel as _QLabel
                role_lbl = _QLabel(organisation_headers[raw_h])
                role_lbl.setStyleSheet(
                    "color:#7D6608; font-weight:bold; background:transparent;")
                self.mapping_table.setCellWidget(row, 1, role_lbl)
                continue
            combo = QComboBox()
            combo.setStyleSheet(INPUT_STYLE)
            apply_combo_popup_style(combo)
            combo.addItem(self.tr("— Ignorer —"), "")
            for c in mappable:
                # v2.9.247 — Lot i18n : FIELD_LABELS porte le texte
                # SOURCE ; traduit au point d'usage (« Colonnes
                # reconnues » — retour écran : « colonnes reconnues en
                # fr »).
                combo.addItem(self.tr(FIELD_LABELS.get(c, c)), c)
            mapped = pr.effective_mappings.get(raw_h, "")
            if mapped:
                idx = combo.findData(mapped)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(self._on_map_change)
            self.mapping_table.setCellWidget(row, 1, combo)

    def _on_map_change(self, *_args):
        if not self.parse_result:
            return
        um = {}
        for row in range(self.mapping_table.rowCount()):
            raw_h = self.mapping_table.item(row, 0).text()
            combo = self.mapping_table.cellWidget(row, 1)
            if not isinstance(combo, QComboBox):
                # v2.7.11.6 — ligne d'organisation (label fixe) : elle
                # n'a pas de combo ; on ne touche pas à son mapping.
                continue
            c = combo.currentData()
            # An empty value is an explicit « Ignorer », not an absence
            # d’override : il doit pouvoir neutraliser une auto-détection.
            um[raw_h] = c or ""
        self.parse_result.user_mappings = um
        if self.file_type == "litho" and not self.parse_result.structure.confirmed:
            self.parse_result.structure = infer_lithology_structure(
                self.parse_result)
        if self.main_dock.project:
            self.main_dock.project.save_mappings(
                self.file_type, self.parse_result.effective_mappings)
            self.main_dock.project.save_import_structure(
                self.file_type, self.parse_result.structure)
        # v2.7.12.11 — titre du bloc + ligne de statut via l'écrivain
        # unique (le bloc reste dans l'état où l'utilisateur l'a laissé).
        self._refresh_mapping_attention_ui()
        if self.file_type == "litho":
            self._update_structure_ui()
        self.main_dock.step2_validate_all()

    def _domain_code_column(self):
        """Raw header holding the domain codes (lithology, alteration…)."""
        if not self.parse_result:
            return ""
        profile = self.parse_result.structure
        if profile.code_column:
            return profile.code_column
        wanted = ("lithology" if self.file_type == "litho"
                  else SPLIT_CONTENT_FIELDS.get(self.file_type, ""))
        return next((
            raw for raw, canonical
            in self.parse_result.effective_mappings.items()
            if canonical == wanted), "")

    def _update_structure_ui(self):
        if self.file_type not in STRUCTURE_TYPES or not self.parse_result:
            return
        # v2.9.247 — Lot i18n : modes d'organisation traduits au point
        # d'usage (les valeurs ci-dessous sont les SOURCES françaises).
        if self.file_type == "litho":
            labels = {
                "standard": self.tr(
                    "Une lithologie est lue par intervalle."),
                "wide_components": self.tr(
                    "Plusieurs colonnes lithologiques sont regroupées "
                    "par intervalle."),
                "delimited_components": self.tr(
                    "Les codes d’une cellule sont séparés explicitement."),
            }
        else:
            labels = {
                "standard": self.tr("Une valeur est lue par cellule."),
                "delimited_components": self.tr(
                    "Les codes d’une cellule sont séparés explicitement."),
                # v2.7.10.37 — CM-01
                "wide_components": self.tr(
                    "Plusieurs colonnes par intervalle (une par code)."),
            }
        profile = self.parse_result.structure
        origin = (self.tr(" — choix enregistré") if profile.confirmed
                  else self.tr(" — détection automatique"))
        text = self.tr("Organisation : {}{}").format(
            labels.get(profile.mode,
                       self.tr("organisation personnalisée")),
            origin)
        # v2.7.11.6 — retour écran « on comprend pas » : nommer les
        # colonnes réellement lues, pas seulement le mode.
        if profile.mode == "wide_components" and profile.component_columns:
            names = " ; ".join(str(c.code_column)
                               for c in profile.component_columns)
            text += self.tr(" — colonnes lues : {}.").format(names)
        elif profile.mode == "delimited_components" and profile.code_column:
            text += self.tr(
                " — colonne « {} » séparée sur « {} ».").format(
                profile.code_column, profile.delimiter or '/')
        self.structure_label.setText(text)
        # v2.7.12.3 — REVUE D'ARCHITECTURE : la question est calculée UNE
        # SEULE FOIS dans core.organisation (source unique de vérité),
        # lue ici pour l'affichage et dans organization_pending() pour le
        # badge ⚠ de l'onglet. Avant, l'affichage et le badge faisaient
        # chacun leur calcul — et le large des pistes codées (sans cellule
        # « / ») passait au travers du badge : « on la swipe ». Le large
        # litho (colonnes de rôles) entre dans la même question.
        question = organisation_question(
            self.file_type, profile, self.parse_result.raw_headers,
            rows=self.parse_result.rows,
            code_column=self._domain_code_column())
        show_question = question.pending
        self._composite_kind = "wide" if question.kind == "wide" else "delimited"
        self._wide_columns = list(question.evidence)
        self.composite_widget.setVisible(show_question)
        if show_question:
            if self._composite_kind == "wide":
                shown = " ; ".join(question.evidence)
                # v2.9.247 — Lot i18n : les dictionnaires portent le
                # texte SOURCE (français) ; la traduction se fait au
                # point d'usage via self.tr (garde dédiée dans les
                # tests : chaque valeur a sa paire dans le .ts).
                words = self.tr(DOMAIN_QUESTION_WORDS.get(
                    self.file_type, "plusieurs codes"))
                # v2.7.11.1 — CM-03 : plafond d'organisation annoncé AVANT
                # la réponse (arbitrage du 21/08/2026) ; le dépassement
                # devient une erreur bloquante écrite, jamais une
                # troncation.
                from ..core.component_caps import (
                    MAX_MINERALS, cap_for)
                cap = cap_for(self.file_type)
                count = len(question.evidence)
                cap_note = (self.tr(
                    " (maximum {} colonnes de code par intervalle")
                    .format(cap) if cap else "")
                if cap and self.file_type == "mineralizations":
                    cap_note += self.tr(
                        " et {} colonnes de minéraux").format(MAX_MINERALS)
                cap_note += ")" if cap else ""
                overflow = (self.tr(
                    " ⚠ {} colonnes détectées — au-delà du maximum, "
                    "la validation bloquera en nommant les colonnes "
                    "en trop.").format(count)
                    if cap and count > cap else "")
                # v2.7.12.3 — les phrases s'adaptent à la famille
                # (lithologie, pas « code », pour la litho).
                single, porte, comme = (
                    self.tr(s) for s in DOMAIN_WIDE_PHRASES.get(
                        self.file_type,
                        ("Un seul code par intervalle", "porte le code",
                         "comme un code")))
                self.composite_label.setText(
                    self.tr("Plusieurs colonnes détectées : {}. {}, ou "
                            "{} sont lus dans les colonnes parallèles "
                            "?{}{}").format(
                        shown, single, words, cap_note, overflow))
                self.keep_composite_button.setText(
                    self.tr("Une seule colonne {}").format(porte))
                self.split_composite_button.setText(
                    self.tr("Lire chaque colonne {}").format(comme))
            else:
                shown = " ; ".join(question.evidence)
                words = self.tr(DOMAIN_QUESTION_WORDS.get(
                    self.file_type, "plusieurs codes"))
                # v2.7.11.1 — CM-03 : plafond annoncé (altérations 5 codes,
                # minéraux 5) ; au-delà, validation bloquante écrite.
                from ..core.component_caps import (
                    MAX_ALTERATION_CODES, MAX_MINERALS)
                dcaps = {"alterations": MAX_ALTERATION_CODES,
                         "mineralizations": MAX_MINERALS}
                dcap = dcaps.get(self.file_type)
                cap_note = (self.tr(" (maximum {} codes par intervalle, "
                                    "arbitrage CM-03)").format(dcap)
                            if dcap else "")
                self.composite_label.setText(
                    self.tr("Valeur avec « / » détectée : {}. Est-ce un "
                            "code unique ou {} ?{}").format(
                        shown, words, cap_note))
                self.keep_composite_button.setText(self.tr("Conserver comme un code"))
                self.split_composite_button.setText(self.tr("Séparer sur « / »…"))
        # v2.7.10.26 — l'onglet se surligne en jaune tant qu'une question
        # d'organisation attend une réponse (sinon on la « swipe » et la
        # synchro devenait déficiente après génération — bug écran).
        callback = getattr(self, "attention_callback", None)
        if callback:
            callback()

    def family_status(self):
        """État de la famille — source unique du badge et de toute
        attention (revue d'architecture du 22/08/2026).

        Famille → État → Attention : cette méthode rassemble les
        sources d'attention GÉNÉRIQUES, sans aucune branche par
        famille (les différences de familles sont dans les DONNÉES —
        REQUIRED_FIELDS, organisation_question — jamais dans des
        « if family == ... ») :

        1. question d'organisation en attente (litho/alt/min ; les
           autres familles reçoivent « none » de la même source) ;
        2. colonnes requises non mappées ou mapping ambigu ;
        3. erreurs de validation (incohérences, erreurs de traitement) ;
        4. avertissements de validation (non bloquants, visibles).

        POINT D'EXTENSION : une famille au besoin réellement différent
        surcharge cette méthode et combine son état propre :
        ``combine(super().family_status(), FamilyStatus(...))`` — le
        rendu et la priorité restent partagés (core.family_status).
        """
        if self.parse_result is None:
            return FamilyStatus(EMPTY)
        parts = []
        question = organisation_question(
            self.file_type, self.parse_result.structure,
            self.parse_result.raw_headers, rows=self.parse_result.rows,
            code_column=self._domain_code_column())
        if question.pending:
            parts.append(FamilyStatus(
                QUESTION, (QUESTION_ORGANISATION,), len(question.evidence)))
        if self._mapping_needs_attention():
            parts.append(FamilyStatus(BLOCKING, (MAPPING,), 0))
        vr = self.validation_result
        if vr is not None:
            if vr.errors:
                parts.append(FamilyStatus(BLOCKING, (ERRORS,), len(vr.errors)))
            if vr.warnings:
                parts.append(FamilyStatus(WARNING, (WARNINGS,),
                                          len(vr.warnings)))
        return combine(*parts)

    def organization_pending(self):
        """True tant qu'une réponse d'organisation est attendue ici.

        v2.7.10.31 — lit l'ÉTAT DES DONNÉES, pas l'état d'affichage du
        widget : en Qt, les widgets d'un onglet non courant rapportent une
        visibilité fausse, et la course badge/affichage du cadre faisait
        perdre l'avertissement (l'onglet passait à ✓ alors que la
        question attendait — constaté à l'écran).

        v2.7.12.3 — délègue à la source unique core.organisation ;
        v2.7.12.5 — délègue à l'ÉTAT DE LA FAMILLE (family_status) :
        une seule chaîne Famille → État → Attention, pour l'affichage
        de la question, le badge et ce prédicat."""
        return self.family_status().severity == QUESTION

    def _save_structure_profile(self, profile):
        self.parse_result.structure = ImportStructureProfile.from_dict(profile)
        self._update_structure_ui()
        # v2.7.11.6 — la table « Colonnes reconnues » affiche le rôle
        # structurel des colonnes absorbées par l'organisation (au lieu
        # de « — Ignorer — ») : il faut la repeindre après chaque réponse.
        self._fill_mapping()
        # v2.7.12.11 — RETOUR ÉCRAN (« l'organisation que j'ai validée,
        # c'est quoi ? ») : répondre à la question change l'interprétation
        # des colonnes (les colonnes de codes ne sont plus « à mapper »)
        # — titre du bloc et ligne de statut DOIVENT être re-évalués :
        # avant, ils restaient sur l'état de l'import (« ouvrez le bloc
        # Colonnes à vérifier » alors que tout était réglé).
        self._refresh_mapping_attention_ui()
        if self.main_dock.project:
            self.main_dock.project.save_import_structure(
                self.file_type, self.parse_result.structure)
        # v2.7.10.26 — BUG de synchro (retour écran) : répondre à la
        # question d'organisation — même APRÈS la génération des coupes —
        # change l'interprétation des données. Comme toute édition, la
        # géométrie 3D générée devient obsolète : invalidation +
        # revalidation immédiates (le référentiel suit, les coupes se
        # régénèrent au lieu de rester sur l'ancienne lecture).
        self.main_dock.step2_on_data_edited(self.file_type)

    def _keep_composite_values(self, *_args):
        """Réponse « une seule colonne porte le contenu » (toutes
        familles — v2.7.12.3 : la litho y est incluse).

        Colonne retenue, par ordre : la colonne de codes du profil,
        sinon (large litho déduit des rôles, sans colonne de codes) le
        PREMIER composant du profil — la roche hôte, jamais une devine
        — sinon la colonne canonique mappée."""
        if not self.parse_result:
            return
        current = self.parse_result.structure
        code = current.code_column
        if not code and (current.mode == "wide_components"
                         and current.component_columns):
            code = str(current.component_columns[0].code_column)
        profile = ImportStructureProfile(
            mode="standard",
            code_column=code or self._domain_code_column(),
            proportion_unit="unknown",
            confirmed=True,
            confidence=1.0)
        self._save_structure_profile(profile)

    def _configure_composite_values(self, *_args):
        if not self.parse_result:
            return
        # v2.7.10.37 — CM-01 : « lire chaque colonne comme un code » →
        # profil d'organisation large confirmé (composants nés de la
        # DECISION explicite, jamais d'une supposition).
        # v2.7.12.3 — les noms des colonnes viennent de la source unique
        # (evidence de la question) ; la litho y ajoute la particularité
        # familiale : son profil large porte déjà RÔLES et PROPORTIONS
        # (rôles litho1/litho2) — la confirmation les conserve tels quels,
        # on ne les réécrit pas.
        if getattr(self, "_composite_kind", "delimited") == "wide":
            current = self.parse_result.structure
            if (current.mode == "wide_components"
                    and current.component_columns):
                profile = ImportStructureProfile.from_dict(
                    current.to_dict())
                profile.confirmed = True
                profile.confidence = 1.0
            else:
                from ..core.data_registry import ComponentColumn
                profile = ImportStructureProfile(
                    mode="wide_components",
                    component_columns=[
                        ComponentColumn(code_column=str(name))
                        for name in getattr(self, "_wide_columns", [])],
                    code_column=self._domain_code_column(),
                    delimiter="",
                    proportion_unit="unknown",
                    confirmed=True,
                    confidence=1.0)
            self._save_structure_profile(profile)
            return
        profile = ImportStructureProfile(
            mode="delimited_components",
            code_column=self._domain_code_column(),
            delimiter="/",
            first_component_role="",
            proportion_unit="unknown",
            confirmed=False,
            confidence=1.0)
        if self.file_type == "litho":
            self._edit_structure(initial_profile=profile)
        else:
            # Alterations/minerals (AM-06) : no hierarchy is ever assumed and
            # the preview already came from the targeted question, so the
            # explicit convention applies immediately.
            profile.confirmed = True
            self._save_structure_profile(profile)

    def _edit_structure(self, *_args, initial_profile=None):
        if not self.parse_result:
            return
        if self.file_type in SPLIT_QUESTION_TYPES:
            # v2.7.11.6 — dialogue propre aux pistes codées (sans rôles
            # ni proportions, AM-05) ; avant, ce bouton n'existait que
            # pour la lithologie.
            from .domain_structure_dialog import DomainStructureDialog
            dialog = DomainStructureDialog(
                self.file_type, self.parse_result.raw_headers,
                initial_profile or self.parse_result.structure,
                parent=self)
            if dialog.exec_() != QDialog.Accepted:
                return
            self._save_structure_profile(dialog.profile())
            return
        if self.file_type != "litho":
            return
        dialog = LithologyStructureDialog(
            self.parse_result.raw_headers,
            initial_profile or self.parse_result.structure,
            self.parse_result.rows,
            mappings=self.parse_result.effective_mappings,
            parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return
        self._save_structure_profile(dialog.profile())

    def _fill_preview(self):
        pr = self.parse_result
        if not pr:
            return
        self.preview_table.setColumnCount(len(pr.raw_headers))
        self.preview_table.setRowCount(len(pr.preview_rows))
        self.preview_table.setHorizontalHeaderLabels(pr.raw_headers)
        # v2.7.12.9 — revue écran (« on voit pas certains noms de
        # colonnes ») : les en-têtes sont les EN-TÊTES BRUTS du fichier,
        # partagés en Stretch — nombreux, ils se rognent dans le dock
        # étroit. Le nom COMPLET passe en infobulle sur chaque en-tête
        # (jamais de troncature silencieuse — même principe que les
        # badges/étiquettes de ce plugin).
        for c, raw_h in enumerate(pr.raw_headers):
            header_item = self.preview_table.horizontalHeaderItem(c)
            if header_item is not None:
                header_item.setToolTip(raw_h)
            # v2.7.12.10 — base de largeur = largeur du NOM (le Stretch
            # distribue l'espace en proportion des bases : les colonnes à
            # nom long sont plus larges dans un dock large ; en dock
            # étroit, le minimum de 56 px + défilement de la table
            # prennent le relais).
            fm = self.preview_table.fontMetrics()
            self.preview_table.setColumnWidth(
                c, max(56, fm.horizontalAdvance(str(raw_h)) + 18))
        for r, row in enumerate(pr.preview_rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                # v2.7.12.9 — lecture seule explicite (drapeau, en plus de
                # NoEditTriggers) : plus de fausse impression d'édition.
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(r, c, item)

    def _open_editor(self, *_args):
        if not self.parse_result:
            return
        # v2.9.273 — retour écran : l'éditeur affichait « Validation OK »
        # alors que la pastille comptait des avertissements (résultat absent
        # ou antérieur).  On valide avant d'ouvrir : même état partout.
        if getattr(self, "validation_result", None) is None:
            self.main_dock.step2_validate_all()
        if self.editor_dialog and self.editor_dialog.isVisible():
            self.editor_dialog.raise_()
            self.editor_dialog.activateWindow()
            return
        self.editor_dialog = CsvEditorDialog(self, self)
        self.editor_dialog.show()
        self.editor_dialog.raise_()

    def set_validation_result(self, result):
        self.validation_result = result
        if self.editor_dialog:
            self.editor_dialog.set_validation_result(result)

    def on_editor_data_changed(self):
        if not self.parse_result:
            return
        self._fill_preview()
        self.preview_hint.setText(
            _preview_hint_text(
                self.parse_result.num_rows,
                self.tr(" — modifications en mémoire")))
        # v2.7.12.12 — l'éditeur réécrit pr.num_rows (lignes ajoutées ou
        # supprimées) : la ligne de statut affiche « N enregistrements »,
        # donc elle passe par l'écrivain unique comme tout autre chemin
        # qui modifie l'état des colonnes (import, colonne, réponse,
        # ÉDITION — le dernier manquant avant ce correctif).
        self._refresh_mapping_attention_ui()
        self.main_dock.step2_on_data_edited(self.file_type)

    def is_numeric_column(self, column):
        if not self.parse_result or not (0 <= column < len(self.parse_result.raw_headers)):
            return False
        raw_header = self.parse_result.raw_headers[column]
        canonical = self.parse_result.effective_mappings.get(raw_header)
        if self.file_type == "assays":
            return canonical != "hole_id"
        return canonical in set(NUMERIC_FIELDS.get(self.file_type, []))

    def get_project_copy_path(self):
        project = self.main_dock.project
        if project:
            return project.get_imported_file_path(self.file_type)
        return None

    def on_project_copy_saved(self, path):
        self.current_path = path
        self.drop_zone.set_loaded(path)
        self.preview_hint.setText(
            _preview_hint_text(
                self.parse_result.num_rows,
                self.tr(" — copie du projet enregistrée")))

    def clear(self):
        if self.editor_dialog:
            self.editor_dialog.close()
            self.editor_dialog = None
        self.parse_result = None
        self.validation_result = None
        self.current_path = ""
        self.editor_btn.setEnabled(False)
        self.drop_zone.reset()
        self.info_label.setText(self.tr("Aucun fichier importé."))
        self.mapping_table.setRowCount(0)
        self.mapping_group.setTitle(self.tr("▸ Colonnes reconnues — détails avancés"))
        self.mapping_group.setChecked(False)
        if self.file_type == "litho":
            self.structure_button.setEnabled(False)
            self.structure_label.setText(
                self.tr("Organisation : en attente d’un fichier"))
            self.composite_widget.hide()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.status_label.setText(self.tr(""))


class GroupedValidationPanel(QWidget):
    """v2.7.6 (VAL-01) — une ligne par type de problème, compteurs exacts.

    Remarque du 18/08/2026 : « à la longue, tout ça sera gérable ? ».
    Oui : des milliers de messages deviennent quelques lignes groupées
    (« FROM ≥ TO — 342 occurrences »), filtrables par gravité, chaque
    ligne menant à la première cellule fautive dans l'éditeur. L'affichage
    est borné par fichier mais les totaux cachés sont toujours annoncés —
    jamais de troncature silencieuse.
    """

    SEVERITY_FILTERS = SEVERITY_FILTERS

    def __init__(self, step2, parent=None):
        super().__init__(parent)
        self.step2 = step2
        self._results = {}
        self._info_lines = []
        self._missing_collar = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_label = QLabel(self.tr("Afficher :"))
        filter_label.setStyleSheet(
            f"font-size: 8.5pt; color:{COLORS['text_medium']}; background:transparent;")
        filter_row.addWidget(filter_label)
        self.filter_combo = QComboBox()
        for label, key in self.SEVERITY_FILTERS:
            self.filter_combo.addItem(self.tr(label), key)
        self.filter_combo.setStyleSheet(INPUT_STYLE)
        apply_combo_popup_style(self.filter_combo)
        self.filter_combo.currentIndexChanged.connect(self._render)
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # v2.7.6.2 : plus de hauteur figée — le séparateur de l'étape 2
        # décide du partage, la liste occupe la place qu'on lui donne.
        self.scroll.setMinimumHeight(64)
        self.scroll.setStyleSheet("background: transparent;")
        self._content = QWidget()
        # v2.7.12.8 — même contexte d'infobulle que le contenu d'onglet :
        # les lignes du panneau (labels sans style) ont pour ancêtre stylé
        # le PLUS PROCHE ce cadre — il porte la règle TOOLTIP_STYLE
        # (en premier, cf. contenu d'onglet).
        self._content.setStyleSheet(TOOLTIP_STYLE + "background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(2)
        self._content_layout.addStretch()
        self.scroll.setWidget(self._content)
        layout.addWidget(self.scroll)

    def update_from_validation(self, results, info_lines, missing_collar):
        self._results = dict(results or {})
        self._info_lines = list(info_lines or [])
        self._missing_collar = bool(missing_collar)
        self._refresh_filter_labels()
        self._render()

    def _all_groups(self):
        """Tous les groupes de problèmes, tous fichiers confondus."""
        groups = []
        for ft in TAB_ORDER:
            vr = self._results.get(ft)
            if vr is None:
                continue
            tab = self.step2.tabs.get(ft)
            issues = vr.get_issues(getattr(tab, "parse_result", None))
            groups.extend(group_issues(issues))
        return groups

    def _refresh_filter_labels(self):
        """Compteurs exacts dans le sélecteur — on sait avant de filtrer."""
        totals = count_by_severity(self._all_groups())
        totals["info"] = totals.get("info", 0) + len(self._info_lines)
        current = self.filter_combo.currentData() or "all"
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        for label, key in filter_labels(totals):
            if " (" in label and label.endswith(")"):
                base, _tail = label.rsplit(" (", 1)
                count = _tail[:-1]
                text = self.tr("{0} ({1})").format(
                    self.tr(base), count)
            else:
                text = self.tr(label)
            self.filter_combo.addItem(text, key)
        index = self.filter_combo.findData(current)
        self.filter_combo.setCurrentIndex(max(0, index))
        self.filter_combo.blockSignals(False)

    def _clear(self):
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _append(self, widget):
        self._content_layout.insertWidget(
            self._content_layout.count() - 1, widget)

    def _render(self, *_args):
        self._clear()
        severity = normalise_severity(self.filter_combo.currentData())
        en_mode = _validation_english_mode()
        shown_info = show_info_lines(severity)
        if shown_info:
            for text in self._info_lines:
                label = QLabel(text)
                label.setWordWrap(True)
                label.setStyleSheet("font-size:9pt; background:transparent;")
                self._append(label)
        any_problem = False
        if self._missing_collar and severity in ("all", "error"):
            self._add_row(
                "error",
                self.tr("Collets : fichier manquant (obligatoire)"),
                self.tr("L'étape 3 a besoin du fichier des collets pour "
                        "calculer les trajectoires."),
                tab_key="collar")
            any_problem = True
        for ft in TAB_ORDER:
            vr = self._results.get(ft)
            if vr is None:
                continue
            tab = self.step2.tabs.get(ft)
            parse_result = getattr(tab, "parse_result", None)
            issues = vr.get_issues(parse_result)
            groups = filter_by_severity(group_issues(issues), severity)
            if not groups:
                continue
            header = QLabel(
                self.tr("<b>{}</b> — {}")
                .format(self.tr(TAB_LABELS.get(ft, ft)), vr.file_name))
            header.setStyleSheet(
                "font-size:9pt; background:transparent; padding-top:4px;")
            self._append(header)
            shown, hidden_groups, hidden_occ = cap_groups(groups)
            for group in shown:
                any_problem = True
                # v2.9.258 — interface anglaise : la ligne affiche le
                # libellé traduit (le détail français de
                # `sample_message`/`suggestion` est volontairement
                # remplacé pour ne jamais exposer de français).
                if en_mode:
                    label = _validation_group_translate(group.label) \
                        or group.label
                    headline = (
                        f"{label} — {group.count} occurrence(s)")
                    tooltip = label
                    suggestion = ""
                else:
                    headline = group.headline
                    tooltip = group.sample_message
                    suggestion = group.suggestion
                self._add_row(
                    group.severity, headline, tooltip, suggestion,
                    tab_key=ft, location=group.first_location)
            if hidden_groups:
                any_problem = True
                row_severity = normalise_severity(severity)
                if row_severity == "all":
                    row_severity = "info"
                sever_words = {
                    "error": (self.tr("type(s) d'erreur"),
                              self.tr("erreur(s)")),
                    "warning": (self.tr("type(s) d'avertissement"),
                                self.tr("avertissement(s)")),
                    "info": (self.tr("type(s) d'information"),
                             self.tr("information(s)")),
                }
                types_word, occ_word = sever_words.get(
                    row_severity,
                    (self.tr("type(s) de problème"),
                     self.tr("occurrence(s)")))
                text = self.tr(
                    "… et {} autre(s) {} — {} {} au total pour ce "
                    "fichier").format(hidden_groups, types_word,
                                      hidden_occ, occ_word)
                self._add_row(
                    row_severity, text,
                    self.tr("Le détail complet est disponible dans l'éditeur."),
                    tab_key=ft)
        if not any_problem:
            if severity == "all" and not self._info_lines:
                message = self.tr(
                    "Importez des fichiers pour lancer la validation.")
            elif severity == "all":
                message = ""
            else:
                # v2.9.247 — libellés de sévérité traduits au point
                # d'usage (garde dédiée dans les tests).
                labels = {"error": self.tr("erreur"),
                          "warning": self.tr("avertissement"),
                          "info": self.tr("information")}
                message = self.tr(
                    "Aucun(e) {} — changez le filtre pour voir le "
                    "reste.").format(labels[severity])
            if message:
                empty = QLabel(message)
                empty.setWordWrap(True)
                empty.setStyleSheet(
                    f"color:{COLORS['text_light']}; font-size:9pt; "
                    "background:transparent;")
                self._append(empty)

    def _add_row(self, severity, headline, tooltip, suggestion="",
                 tab_key=None, location=(None, None)):
        colors = {"error": "#E74C3C", "warning": "#D68910", "info": "#5DADE2"}
        icons = {"error": "✗", "warning": "⚠", "info": "ℹ"}
        row_widget = QWidget()
        row_widget.setStyleSheet("background:transparent;")
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(4, 0, 0, 0)
        row.setSpacing(5)
        icon = QLabel(icons.get(severity, "•"))
        icon.setFixedWidth(14)
        icon.setStyleSheet(
            f"color:{colors.get(severity, '#888')}; font-weight:bold; "
            "background:transparent;")
        row.addWidget(icon)
        text = QLabel(headline)
        text.setWordWrap(True)
        tip = tooltip or ""
        if suggestion:
            # v2.9.258 — « Suggestion : » suit la langue active (le
            # contexte translation est ValidationMessages).
            prefix = _validation_group_translate("Suggestion : {}")
            tip = (f"{tip}\n{prefix.format(suggestion)}" if tip
                   else prefix.format(suggestion))
        text.setToolTip(tip)
        text.setStyleSheet(
            f"font-size:9pt; color:{colors.get(severity, '#555')}; "
            "background:transparent;")
        row.addWidget(text, 1)
        if tab_key is not None:
            row_v, col_v = location
            button = QPushButton(self.tr("Éditeur ›"))
            # v2.7.6.5 (UI-03) : texte lisible dans une ligne compacte.
            button.setStyleSheet(BUTTON_COMPACT)
            button.setFixedHeight(22)
            button.setMinimumWidth(74)
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(self.tr("Éditeur CSV · cellule concernée"))
            button.clicked.connect(
                lambda _checked=False, key=tab_key, r=row_v, c=col_v:
                self._open_editor_at(key, r, c))
            row.addWidget(button)
        self._append(row_widget)

    def _open_editor_at(self, ft, row, column):
        tab = self.step2.tabs.get(ft)
        if tab is None:
            return
        tab._open_editor()
        dialog = getattr(tab, "editor_dialog", None)
        if dialog is not None and hasattr(dialog, "focus_location"):
            dialog.focus_location(row, column)


class FamilyChip(QPushButton):
    """Pastille de famille (v2.9.99 compacte ; v2.9.98 sans carre focus) — sélecteur enroulant (v2.7.12.6, revue écran).

    Remplace la rangée d'onglets native, qui TRONQUAIT (« Alt… ») et
    MASQUAIT (« Minéralisations ») dès que le dock était étroit — or un
    badge caché annule le système d'attention (v2.7.12.5) : les pastilles
    passent à la ligne, donc TOUTES les familles et leurs états restent
    visibles, et une famille ajoutée plus tard ne casse plus la rangée.

    Apparence = la MÊME source que le badge (core.family_status) :
    badge_rendu pour le texte/infobulle, SEVERITY_BORDER/TEXT pour la
    couleur, badge_count pour le compte (P2 : « Déviations ⚠ 3 »).
    L'état arrive par ``set_status(FamilyStatus)`` — la pastille ne
    calcule rien, elle rend (principe Famille → État → Attention)."""

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self._base_label = label
        self._title = label
        self._tooltip = ""
        self._status = FamilyStatus(EMPTY)
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        # v2.9.99 — pastilles plus petites (moins d'espace vertical)
        # v2.9.273 — pastilles 2 px plus basses (lisibilité/hauteur)
        self.setMinimumHeight(22)
        self.setMaximumHeight(26)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # v2.9.98 — pastille plate : pas de relief natif ni carre de focus
        # Qt (le carre a l'interieur au clic / selection clavier).
        self.setFlat(True)
        self.setAutoDefault(False)
        self.setDefault(False)
        self.setFocusPolicy(Qt.NoFocus)
        self._refresh_paint()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._refresh_paint()

    def set_status(self, status: FamilyStatus):
        self._status = status
        text, _colour, tooltip = badge_rendu(status, self._base_label)
        count = badge_count(status)
        self._title = f"{text} {count}" if count else text
        self._tooltip = tooltip
        self._refresh_paint()

    def _refresh_paint(self):
        severity = self._status.severity
        border = SEVERITY_BORDER.get(severity, "")
        colour = SEVERITY_TEXT.get(severity, "#2C3E50")
        background = "#D6EAF8" if self._selected else "#FFFFFF"
        # L'attention (bordure couleur de gravité) reste visible même si
        # la pastille est sélectionnée : la sélection teinte le fond.
        border_colour = border or ("#1C2833" if self._selected
                                   else "#D5DBDB")
        self.setText(self._title)
        self.setToolTip(self._tooltip)
        # v2.7.12.8 — la pastille est stylée en propre : son infobulle
        # (le détail du badge) a la pastille comme contexte de style —
        # la règle TOOLTIP_STYLE y est donc requise (jamais noir sur noir).
        # v2.9.98 — pas d'outline / focus rect / inset press
        self.setStyleSheet(
            TOOLTIP_STYLE
            + f"QPushButton {{ background-color: {background}; "
            f"color: {colour}; border: 1px solid {border_colour}; "
            f"border-radius: 11px; font-weight: bold; font-size: 8pt; "
            f"outline: none; padding: 2px 8px; min-height: 20px; }}"
            f"QPushButton:focus {{ outline: none; border: 1px solid "
            f"{border_colour}; background-color: {background}; }}"
            f"QPushButton:pressed {{ background-color: {background}; "
            f"border: 1px solid {border_colour}; padding: 2px 8px; }}"
            f"QPushButton:hover {{ background-color: "
            f"{'#D6EAF8' if self._selected else '#F4F6F7'}; }}")


class Step2Import(QWidget):
    validity_changed = pyqtSignal(bool)

    def __init__(self, main_dock, parent=None):
        super().__init__(parent)
        self.main_dock = main_dock
        self.tabs: dict[str, ImportTab] = {}
        self.bundle = ImportBundle()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        intro_row = QHBoxLayout()
        # v2.7.12.6 — revue écran : une seule consigne, pas de répétition
        # de la zone de dépôt ; v2.7.12.8 — revue écran (« trop d'écritures,
        # certains éléments prennent trop d'espace ») : consigne resserrée
        # sur deux lignes — le détail du dépôt de dossier est déjà porté
        # par l'étiquette de la zone de dépôt elle-même.
        sub = QLabel(
            self.tr(
                "Importez vos fichiers CSV un par onglet, ou glissez-en "
                "plusieurs (ou un dossier) : chaque fichier est reconnu "
                "par ses en-têtes et les colonnes sont détectées "
                "automatiquement."))
        sub.setObjectName("label_subtitle")
        sub.setWordWrap(True)
        intro_row.addWidget(sub, 1)
        layout.addLayout(intro_row)

        # v2.7.6 (IMP-01) — dépôt groupé avec répartition automatique.
        # v2.7.12.6 — la zone de dépôt ne répète plus l'explication
        # (désormais une seule phrase au-dessus) : ici, l'action.
        self.router_zone = DropZone(
            multi=True,
            empty_label=self.tr(
                "Glisser des fichiers CSV ou un dossier ici"))
        self.router_zone.files_dropped.connect(self.route_files)
        layout.addWidget(self.router_zone)

        # Bannière d'annonce : ce qui a été rangé où, et pourquoi.
        self._routing_log: list[dict] = []
        self.routing_frame = QFrame()
        self.routing_frame.setStyleSheet(
            f"QFrame {{ background:#FEF9E7; border:1px solid #F0C36D; "
            f"border-radius:3px; }}")
        self.routing_layout = QVBoxLayout(self.routing_frame)
        self.routing_layout.setContentsMargins(7, 5, 7, 5)
        self.routing_layout.setSpacing(3)
        self.routing_frame.hide()
        layout.addWidget(self.routing_frame)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(TAB_STYLE)
        for ft in TAB_ORDER:
            tab = ImportTab(ft, self.main_dock, router=self.route_files)
            self.tabs[ft] = tab
            # v2.9.247 — TAB_LABELS porte le texte SOURCE ; traduit ici
            # (garde dédiée : chaque valeur a sa paire dans le .ts).
            self.tab_widget.addTab(tab, self.tr(TAB_LABELS[ft]))
            # v2.7.10.26 — surlignage jaune tant qu'une question attend.
            tab.attention_callback = (
                lambda ft=ft: self._mark_tab_attention(ft))

        # v2.7.12.6 — REVUE ÉCRAN : la rangée d'onglets native tronquait
        # (« Alt… ») et masquait (« Minéralisations ») sur dock étroit —
        # un badge caché annule le système d'attention. Les pastilles
        # (3 par rangée, enroulement automatique) gardent TOUTES les
        # familles et leurs états visibles ; les pages restent les
        # widgets de QTabWidget, seul le sélecteur change.
        self.tab_widget.tabBar().hide()
        self.chips_bar = QWidget()
        # v2.9.274 — retour écran : « on peut replier certains ? ».  La barre
        # devient une PILE de widgets par catégorie : chaque en-tête est un
        # petit bouton ▾/▸ qui replie son groupe (la hauteur s'effondre
        # vraiment, pas juste masquée).  Le lien pastille → onglet reste
        # l'index dans TAB_ORDER ; `_sync_chips` et les badges ne bougent pas.
        bar_layout = QVBoxLayout(self.chips_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(2)
        self.chips = {}
        self._category_chips = {}
        grouped = [ft for _t, members in CHIP_GROUPS for ft in members]
        groups = [(title, [ft for ft in members if ft in TAB_ORDER])
                  for title, members in CHIP_GROUPS]
        leftover = [ft for ft in TAB_ORDER if ft not in grouped]
        if leftover:
            groups.append(("Autres", leftover))
        first_group = True
        for title, members in groups:
            if not members:
                continue
            if not first_group:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet(
                    f"color:{COLORS['border']}; "
                    f"background:{COLORS['border']}; border:none;")
                bar_layout.addWidget(sep)
            first_group = False
            box = QWidget()
            grid = QGridLayout(box)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(2)
            grid.setColumnStretch(0, 0)
            toggle = QPushButton("▾ " + self.tr(title))
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setStyleSheet(
                f"QPushButton {{ text-align:left; border:none; background:"
                f"transparent; color:{COLORS['text_medium']}; font-size:7pt; "
                "font-weight:bold; padding:1px 0 0 0; }}"
                "QPushButton:hover { color:" + COLORS["accent"] + "; }")
            grid.addWidget(toggle, 0, 0)
            chip_widgets = []
            for pos, ft in enumerate(members):
                chip = FamilyChip(self.tr(TAB_LABELS[ft]))
                index = TAB_ORDER.index(ft)
                chip.clicked.connect(
                    lambda _checked=False, i=index:
                        self.tab_widget.setCurrentIndex(i))
                self.chips[ft] = chip
                chip_widgets.append(chip)
                grid.addWidget(chip, pos // 3, 1 + pos % 3)
            self._category_chips[title] = chip_widgets
            toggle.clicked.connect(
                lambda _checked=False, t=title, b=box, cw=chip_widgets,
                       tg=toggle: self._toggle_category(t, b, cw, tg))
            bar_layout.addWidget(box)
        bar_layout.addStretch(1)
        self.tab_widget.currentChanged.connect(self._sync_chips)
        self._sync_chips(self.tab_widget.currentIndex())
        layout.addWidget(self.chips_bar)

        # Validation status panel
        lg = QGroupBox(self.tr("Validation"))
        ll = QVBoxLayout(lg)
        ll.setContentsMargins(6, 6, 6, 6)

        # Summary line (replaces the button)
        self.summary_label = QLabel(self.tr("En attente d’import..."))
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(f"font-size: 10pt; font-weight: bold; color: {COLORS['text_medium']}; background: transparent; padding: 4px;")
        ll.addWidget(self.summary_label)

        # v2.7.6 (VAL-01) — problèmes regroupés par type avec compteurs.
        self.validation_panel = GroupedValidationPanel(self)
        ll.addWidget(self.validation_panel)

        # v2.7.6.2 (UI-01) — revue écran : « superposition d'éléments ».
        # Dans un dock étroit et peu haut, les onglets et le bloc Validation
        # se disputaient la hauteur et finissaient par se chevaucher. Un
        # séparateur mobile donne la priorité aux onglets, laisse toujours
        # une hauteur minimale à chacun et rend le partage réglable.
        self.import_splitter = QSplitter(Qt.Vertical)
        self.import_splitter.setChildrenCollapsible(False)
        self.import_splitter.setHandleWidth(6)
        self.tab_widget.setMinimumHeight(240)
        lg.setMinimumHeight(96)
        self.import_splitter.addWidget(self.tab_widget)
        self.import_splitter.addWidget(lg)
        self.import_splitter.setStretchFactor(0, 3)
        self.import_splitter.setStretchFactor(1, 1)
        self.import_splitter.setSizes([420, 170])
        layout.addWidget(self.import_splitter, 1)

    # ------------------------------------------------------------------
    # v2.7.6 (IMP-01) — répartition automatique des fichiers déposés
    # ------------------------------------------------------------------
    def route_files(self, paths):
        """Détecte le type de chaque fichier et le range dans son onglet.

        Tout est annoncé dans la bannière jaune ; les vraies ambiguïtés
        proposent des boutons de choix (jamais de placement silencieux).
        """
        files, ignored = expand_dropped_paths(list(paths))
        project = self.main_dock.project
        learned = project.get_learned_synonyms() if project else None
        for name in ignored:
            self._routing_log.append({
                "kind": "ignored",
                "text": self.tr(
                    "« {} » ignoré : ce n'est pas un fichier CSV."
                ).format(name)})
        for path in files:
            name = os.path.basename(path)
            guess = detect_file_type(path, extra_synonyms=learned)
            if guess.confident:
                if guess.file_type == "topography":
                    # v2.9.0 — la topographie n'a PAS d'onglet d'import :
                    # c'est une source de la ligne de sol de la coupe
                    # (cascade MNT → CSV → collets), pas une donnée de
                    # forage. Annoncé, placé dans le projet (data_import)
                    # pour que la coupe le retrouve.
                    why = ", ".join((guess.reasons or [])[:3])
                    self._routing_log.append({
                        "kind": "topography", "path": path,
                        "text": (self.tr(
                                     "« {} » reconnu comme Topographie")
                                 .format(name)
                                 + (self.tr(" — {}.").format(why)
                                    if why else ".")
                                 + self.tr(
                                     " Pas d'onglet d'import : il sera "
                                     "utilisé automatiquement comme ligne "
                                     "de sol de la coupe (cascade MNT → "
                                     "CSV → collets)."))})
                    if project:
                        from ..core.import_detect import read_header_sample
                        sample = read_header_sample(path)
                        if not sample.error:
                            project.record_import(
                                "topography", path, sample.encoding,
                                sample.separator, ".",
                                headers=sample.headers)
                else:
                    self._route_to_tab(path, guess.file_type, guess.reasons)
            elif guess.alternatives:
                self._routing_log.append({
                    "kind": "ambiguous", "path": path,
                    "alternatives": list(guess.alternatives),
                    "best": guess.file_type,
                    "reason": self.tr(
                        "La signature d'en-têtes hésite entre plusieurs "
                        "types.")})
            else:
                self._routing_log.append({
                    "kind": "unknown", "path": path,
                    "reason": guess.error
                    or self.tr(
                        "Type de fichier non reconnu sur les en-têtes.")})
        self._render_routing_log()

    def _route_to_tab(self, path, target, reasons, user_choice=False,
                      replace=False):
        tab = self.tabs.get(target)
        name = os.path.basename(path)
        label = self.tr(TAB_LABELS.get(target, target))
        if tab is None:
            return
        already = tab.parse_result is not None
        if already and not replace and os.path.abspath(
                tab.current_path or "") != os.path.abspath(path):
            self._routing_log.append({
                "kind": "occupied", "path": path, "target": target,
                "reasons": list(reasons or [])})
            return
        old_name = (os.path.basename(tab.current_path)
                    if already and tab.current_path else "")
        tab._on_file(path)
        if tab.parse_result is None:
            self._routing_log.append({
                "kind": "unknown", "path": path,
                "reason": self.tr(
                    "Lecture impossible — voir le message dans "
                    "l'onglet {}.").format(label)})
            return
        why = ", ".join((reasons or [])[:4])
        if reasons and len(reasons) > 4:
            why += "…"
        note = (self.tr(" — votre choix") if user_choice else "")
        replaced = (self.tr(" (a remplacé « {} »)").format(old_name)
                    if old_name else "")
        self._routing_log.append({
            "kind": "success",
            "text": self.tr("« {} » → onglet {}{}{}").format(
                        name, label, note, replaced)
                    + (self.tr(" — reconnu grâce à : {}.").format(why)
                       if why else ".")})

    def _render_routing_log(self):
        while self.routing_layout.count():
            item = self.routing_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        entries = self._routing_log[-12:]
        if not entries:
            self.routing_frame.hide()
            return
        self.routing_frame.show()
        if len(self._routing_log) > len(entries):
            head = QLabel(
                self.tr("… et {} message(s) plus ancien(s)").format(
                    len(self._routing_log) - len(entries)))
            head.setStyleSheet(
                f"font-size:8.5pt; color:{COLORS['text_light']}; background:transparent;")
            self.routing_layout.addWidget(head)
        for entry_index, entry in enumerate(entries):
            absolute_index = len(self._routing_log) - len(entries) + entry_index
            self.routing_layout.addWidget(
                self._routing_row(entry, absolute_index))
        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_btn = QPushButton(self.tr("Effacer ces messages"))
        clear_btn.setStyleSheet(BUTTON_COMPACT)
        clear_btn.setFixedHeight(22)
        clear_btn.clicked.connect(self._clear_routing_log)
        clear_row.addWidget(clear_btn)
        self.routing_layout.addLayout(clear_row)

    def _routing_row(self, entry, absolute_index):
        row_widget = QWidget()
        row_widget.setStyleSheet("background:transparent;")
        # v2.9.273 — retour écran : la ligne « le type hésite » mettait TOUS
        # les boutons candidats dans la même HBox que l'étiquette → sur dock
        # étroit chaque bouton était comprimé (« ecover », « )ensit »).  On
        # passe en VBoxLayout : étiquette sur sa ligne, candidats sur une
        # grille qui revient à la ligne.
        outer = QVBoxLayout(row_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(3)
        row = QHBoxLayout()
        row.setSpacing(5)
        outer.addLayout(row)
        kind = entry.get("kind")
        styles = {
            "success": ("✓", COLORS["success"]),
            "topography": ("✓", COLORS["success"]),
            "ambiguous": ("⚠", "#B9770E"),
            "occupied": ("⚠", "#B9770E"),
            "unknown": ("ℹ", "#5D6D7E"),
            "ignored": ("ℹ", "#909497"),
        }
        icon, color = styles.get(kind, ("ℹ", "#909497"))
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(14)
        icon_label.setStyleSheet(
            f"color:{color}; font-weight:bold; background:transparent;")
        row.addWidget(icon_label)
        name = os.path.basename(entry.get("path", ""))
        if kind in ("success", "topography"):
            text = entry.get("text", "")
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(
                f"font-size:9pt; color:#1E8449; background:transparent;")
            row.addWidget(label, 1)
        elif kind == "ambiguous":
            # v2.7.11.5 — le meilleur candidat est présenté et marqué ;
            # avant, seuls les PIRES types obtenaient un bouton (retour
            # écran : « il n'arrive pas à déterminer alteration comme
            # alteration » — la bonne réponse n'était pas cliquable).
            best = entry.get("best")
            best_label = (self.tr(FILE_TYPE_LABELS.get(best, ""))
                          if best else "")
            best_part = (self.tr("le plus probable est {} ;").format(
                             best_label) + " "
                         if best_label else "")
            label = QLabel(
                self.tr("« {} » : le type hésite — {}cliquez pour "
                        "choisir :").format(name, best_part))
            label.setWordWrap(True)
            label.setStyleSheet(
                "font-size:9pt; color:#7D6608; background:transparent;")
            row.addWidget(label, 1)
            # v2.9.273 — candidats sur une grille (2 par rangée, texte
            # intégral + infobulle) : plus jamais comprimés ni superposés,
            # quel que soit le nombre de domaines candidats.
            cand_grid = QGridLayout()
            cand_grid.setContentsMargins(14, 0, 0, 0)
            cand_grid.setHorizontalSpacing(6)
            cand_grid.setVerticalSpacing(4)
            for pos, (candidate, _score) in enumerate(
                    entry.get("alternatives", [])):
                caption = self.tr(FILE_TYPE_LABELS.get(candidate,
                                                      candidate))
                if candidate == best:
                    caption = self.tr("{} ✓ suggéré").format(caption)
                button = QPushButton(caption)
                button.setStyleSheet(BUTTON_COMPACT)
                button.setFixedHeight(24)
                button.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Fixed)
                button.setToolTip(caption)
                button.setCursor(Qt.PointingHandCursor)
                button.clicked.connect(
                    lambda _checked=False, idx=absolute_index,
                           cand=candidate:
                    self._choose_routed_type(idx, cand))
                cand_grid.addWidget(button, pos // 2, pos % 2)
            cand_grid.setColumnStretch(0, 1)
            cand_grid.setColumnStretch(1, 1)
            outer.addLayout(cand_grid)
        elif kind == "occupied":
            target = entry.get("target")
            label = QLabel(
                self.tr("« {} » ressemble à {}, mais cet onglet est "
                        "déjà rempli —").format(
                    name, self.tr(TAB_LABELS.get(target, target))))
            label.setWordWrap(True)
            label.setStyleSheet(
                "font-size:9pt; color:#7D6608; background:transparent;")
            row.addWidget(label, 1)
            replace_btn = QPushButton(self.tr("Remplacer"))
            replace_btn.setStyleSheet(BUTTON_COMPACT)
            replace_btn.setFixedHeight(22)
            replace_btn.setToolTip(self.tr("Remplacer le fichier de l'onglet"))
            replace_btn.clicked.connect(
                lambda _checked=False, idx=absolute_index:
                self._replace_routed_file(idx))
            row.addWidget(replace_btn)
        else:
            label = QLabel(
                self.tr("« {} » : {} Glissez-le directement dans le bon "
                        "onglet.").format(name, entry.get('reason', '')))
            label.setWordWrap(True)
            label.setStyleSheet(
                "font-size:9pt; color:#5D6D7E; background:transparent;")
            row.addWidget(label, 1)
        return row_widget

    def _choose_routed_type(self, log_index, candidate):
        try:
            entry = self._routing_log[log_index]
        except IndexError:
            return
        if entry.get("kind") != "ambiguous":
            return
        self._routing_log.pop(log_index)
        self._route_to_tab(
            entry["path"], candidate,
            reasons=["choix de l'utilisateur"], user_choice=True)
        self._render_routing_log()

    def _replace_routed_file(self, log_index):
        try:
            entry = self._routing_log[log_index]
        except IndexError:
            return
        if entry.get("kind") != "occupied":
            return
        self._routing_log.pop(log_index)
        self._route_to_tab(
            entry["path"], entry["target"],
            reasons=entry.get("reasons", []), replace=True)
        self._render_routing_log()

    def _clear_routing_log(self, *_args):
        self._routing_log = []
        self._render_routing_log()

    def _refresh_tab_badges(self):
        """Rendu des badges — la seule fonction qui écrit les titres
        d'onglets (principe v2.7.10.27 : un seul écrivain).

        v2.7.12.5 — REVUE D'ARCHITECTURE (système de badge générique) :
        cette fonction ne sait PLUS RIEN du contenu d'une famille. Elle
        lit l'état (``tab.family_status()``) et pose le rendu
        (``badge_rendu``) — tout le reste vit dans core.family_status.
        Ajouter une famille au plugin ne nécessite AUCUN changement ici :
        la nouvelle famille hérite du badge par family_status()."""
        for index, ft in enumerate(TAB_ORDER):
            status = self.tabs[ft].family_status()
            text, colour, tooltip = badge_rendu(
                status, self.tr(TAB_LABELS[ft]))
            # Titres natifs (masqués, conservés pour l'accessibilité)
            # + pastilles : le MÊME état rend les deux (un seul
            # écrivain, principe v2.7.10.27 conservé).
            self.tab_widget.setTabText(index, text)
            bar = self.tab_widget.tabBar()
            bar.setTabTextColor(index, QColor(colour) if colour else QColor())
            bar.setTabToolTip(index, tooltip)
            self.chips[ft].set_status(status)

    def _toggle_category(self, title, box, chip_widgets, toggle):
        """v2.9.274 — replie/déplie une catégorie de la barre de pastilles."""
        collapsed = any(c.isVisibleTo(box) for c in chip_widgets)
        for c in chip_widgets:
            c.setVisible(not collapsed)
        toggle.setText(("▸ " if collapsed else "▾ ") + self.tr(title))

    def _sync_chips(self, index):
        """v2.7.12.6 — pastille sélectionnée = page courante."""
        for i, ft in enumerate(TAB_ORDER):
            self.chips[ft].set_selected(i == index)

    def _discover_interval_domain(self, domain_key, intervals_by_hole,
                                  attribute, label, kind="categorical",
                                  component_scoped=False):
        project = self.main_dock.project
        if not project:
            return []
        values = []
        for intervals in intervals_by_hole.values():
            for interval in intervals:
                # After an explicit split (AM-06), each declared code counts
                # individually; untouched cells keep their raw value.
                # v2.7.10.37 — CM-01 : en minéralisations, les composants
                # écrits par le split « Minéraux » ne sont JAMAIS des styles
                # d'intervalle (AM-05) ; seuls les styles du mode large les
                # portent vers le domaine (marqueur « _wide_styles »).
                if (domain_key == "mineralization_style" and component_scoped
                        and interval.components):
                    interval_components = interval.components if (
                        interval.attributes.get("_wide_styles")) else []
                else:
                    interval_components = (
                        interval.components if component_scoped else [])
                if interval_components:
                    values.extend(
                        component.raw_code
                        for component in interval_components
                        if component.raw_code)
                    continue
                value = interval.attributes.get(attribute)
                if value not in (None, ""):
                    values.append(value)
        return project.discover_domain_values(
            domain_key, values, label=label, kind=kind)

    def _mark_tab_attention(self, file_type):
        """v2.7.10.27 — le point d'entrée du surlignage (appelé dès qu'une
        question apparaît/disparaît) délègue au badge unifié : une SEULE
        fonction écrit le titre d'un onglet (les deux systèmes
        s'écrasaient en v2.7.10.26 ; « ✓ valide » mettait la question
        sous le tapis)."""
        _unused = file_type  # le badge unifié rafraîchit le tout, à pas cher.
        self._refresh_tab_badges()

    def step2_validate_all(self):
        self.bundle = ImportBundle()
        self._vr_map = {}
        log_lines = []
        all_valid = True
        total = 0
        errors = 0
        warnings_count = 0

        # Collar
        ct = self.tabs.get("collar")
        if ct and ct.parse_result:
            recs, vr = validate_collar(ct.parse_result)
            self.bundle.collars = {r.hole_id: r for r in recs}
            total += vr.num_records
            errors += len(vr.errors)
            ct.set_validation_result(vr)
            self._vr_map["collar"] = vr
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; COLLETS '
                    '({}):</span>').format(vr.file_name))
                for e in vr.errors: log_lines.append(f'  <span style="color:#E74C3C;">&#10060; {e}</span>')
            else:
                # v2.7.12.8 — REVUE ÉCRAN (« incohérent : 38 enregistrements
                # ✓ alors que question/colonnes en attente ») : le ✅ passe
                # au MÊME critère que la pastille (family_status) — plus de
                # ligne verte quand la famille a une attention : les
                # problèmes sont déjà visibles dans le panneau groupé.
                if not ct.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; Collets: '
                        '{} forages</span>').format(vr.num_records))
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')
        else:
            log_lines.append(self.tr(
                '<span style="color:#E74C3C;">&#10060; Collets: '
                'non importé</span>'))
            all_valid = False

        cids = set(self.bundle.collars.keys())

        # Déviations
        st = self.tabs.get("survey")
        if st and st.parse_result:
            bh, vr = validate_survey(
                st.parse_result, cids, self.bundle.collars)
            self.bundle.surveys = bh
            total += vr.num_records
            errors += len(vr.errors)
            st.set_validation_result(vr)
            self._vr_map["survey"] = vr
            # v2.9.286 — convention signée : blocage si ambiguïté,
            # conversion « Historique » sinon, choix mémorisé au projet.
            st._refresh_dip_warning()
            if (st.dip_hint() == "all_positive"
                    and not getattr(st, "dip_choice_made", False)):
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; DÉVIATIONS : '
                    'convention du dip à confirmer (dips tous positifs).'
                    '</span>'))
            elif st.survey_dip_convention() == "historique":
                for recs in self.bundle.surveys.values():
                    for rec in recs:
                        rec.dip = -abs(float(rec.dip))
                for col in self.bundle.collars.values():
                    if col.dip is not None:
                        col.dip = -abs(float(col.dip))
            if self.main_dock.project:
                self.main_dock.project.config["dip_convention"] = (
                    st.survey_dip_convention())
                self.main_dock.project.save_config()
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; DÉVIATIONS '
                    '({}):</span>').format(vr.file_name))
                for e in vr.errors: log_lines.append(f'  <span style="color:#E74C3C;">&#10060; {e}</span>')
            else:
                # v2.7.12.8 — ✅ sur le critère family_status (cf. Collets).
                if not st.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; Déviations: '
                        '{} stations</span>').format(vr.num_records))
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')
        else:
            if cids:
                warnings_count += len(cids)
                log_lines.append(self.tr(
                    '<span style="color:#F39C12;">&#9888; Déviations: non '
                    'importées ({} forages seront traités comme '
                    'verticaux)</span>').format(len(cids)))

        # Litho
        lt = self.tabs.get("litho")
        if lt and lt.parse_result:
            bh, vr = validate_intervals(
                lt.parse_result, "litho", cids, "lithology",
                collars=self.bundle.collars)
            self.bundle.litho = bh
            total += vr.num_records
            errors += len(vr.errors)
            lt.set_validation_result(vr)
            self._vr_map["litho"] = vr
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; LITHO '
                    '({}):</span>').format(vr.file_name))
                for e in vr.errors: log_lines.append(f'  <span style="color:#E74C3C;">&#10060; {e}</span>')
            else:
                # v2.7.12.8 — ✅ sur le critère family_status (cf. Collets).
                if not lt.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; Lithologie: '
                        '{} intervalles</span>').format(vr.num_records))
                values = [
                    component.raw_code
                    for intervals in bh.values()
                    for interval in intervals
                    for component in interval.components
                ]
                added = self.main_dock.project.discover_domain_values(
                    "lithology", values, self.tr("Lithologie")
                ) if self.main_dock.project else []
                if added:
                    log_lines.append(self.tr(
                        '<span style="color:#5DADE2;">&#8505; {} nouveau(x) '
                        'code(s) lithologique(s) ajouté(s) au '
                        'référentiel</span>').format(len(added)))
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Teneurs
        at = self.tabs.get("assays")
        if at and at.parse_result:
            bh, vr = validate_intervals(
                at.parse_result, "assays", cids, None,
                collars=self.bundle.collars)
            self.bundle.assays = bh
            total += vr.num_records
            errors += len(vr.errors)
            at.set_validation_result(vr)
            self._vr_map["assays"] = vr
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; TENEURS '
                    '({}):</span>').format(vr.file_name))
                for e in vr.errors: log_lines.append(f'  <span style="color:#E74C3C;">&#10060; {e}</span>')
            else:
                # v2.7.12.8 — ✅ sur le critère family_status (cf. Collets).
                if not at.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; Teneurs: '
                        '{} échantillons</span>').format(vr.num_records))
                if self.main_dock.project:
                    self.main_dock.project.discover_assay_elements(
                        self.get_assay_element_columns())
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Altérations (optional geological intervals)
        alt = self.tabs.get("alterations")
        if alt and alt.parse_result:
            bh, vr = validate_intervals(
                alt.parse_result, "alterations", cids, "alteration",
                collars=self.bundle.collars)
            self.bundle.alterations = bh
            total += vr.num_records
            errors += len(vr.errors)
            alt.set_validation_result(vr)
            self._vr_map["alterations"] = vr
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; ALTÉRATIONS '
                    '({}):</span>').format(vr.file_name))
                for error in vr.errors:
                    log_lines.append(
                        f'  <span style="color:#E74C3C;">&#10060; {error}</span>')
            else:
                # v2.7.12.8 — ✅ sur le critère family_status (cf. Collets).
                if not alt.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; '
                        'Altérations: {} intervalles</span>'
                        ).format(vr.num_records))
                self._discover_interval_domain(
                    "alteration", bh, "alteration",
                    self.tr("Altération"), component_scoped=True)
                self._discover_interval_domain(
                    "alteration_intensity", bh, "intensity",
                    self.tr("Intensité d’altération"), kind="ordinal")
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Minéralisation observée (facultative)
        mineral = self.tabs.get("mineralizations")
        if mineral and mineral.parse_result:
            bh, vr = validate_intervals(
                mineral.parse_result, "mineralizations", cids,
                "mineralization_style", collars=self.bundle.collars)
            self.bundle.mineralizations = bh
            total += vr.num_records
            errors += len(vr.errors)
            mineral.set_validation_result(vr)
            self._vr_map["mineralizations"] = vr
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; '
                    'MINÉRALISATIONS ({}):</span>').format(vr.file_name))
                for error in vr.errors:
                    log_lines.append(
                        f'  <span style="color:#E74C3C;">&#10060; {error}</span>')
            else:
                # v2.7.12.8 — ✅ sur le critère family_status (cf. Collets).
                if not mineral.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; Minéralisations '
                        'observées: {} intervalles</span>'
                        ).format(vr.num_records))
                self._discover_interval_domain(
                    "mineralization_style", bh, "mineralization_style",
                    # CM-01 : les styles d'un mode large comptent chacun.
                    self.tr("Style de minéralisation"),
                    component_scoped=True)
                self._discover_interval_domain(
                    "minerals", bh, "minerals", self.tr("Minéraux"),
                    kind="multi_label", component_scoped=True)
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Structures observées (facultatives, mesures ponctuelles)
        structure = self.tabs.get("structure")
        if structure and structure.parse_result:
            bh, vr = validate_structure(
                structure.parse_result, cids,
                collars=self.bundle.collars)
            self.bundle.structure = bh
            total += vr.num_records
            errors += len(vr.errors)
            structure.set_validation_result(vr)
            self._vr_map["structure"] = vr
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; STRUCTURES '
                    'OBSERVÉES ({}):</span>').format(vr.file_name))
                for error in vr.errors:
                    log_lines.append(
                        f'  <span style="color:#E74C3C;">&#10060; {error}</span>')
            else:
                # v2.7.12.8 — ✅ sur le critère family_status (cf. Collets).
                if not structure.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; Structures '
                        'observées: {} mesures</span>'
                        ).format(vr.num_records))
                # v2.9.258-rendu — types de structure découverts dans le
                # Référentiel (même mécanisme que lithologie/altérations) :
                # la couleure des points QGIS vient de ce domaine partagé.
                if self.main_dock.project:
                    values = [
                        str(record.type or "").strip()
                        for records in bh.values()
                        for record in records
                        if str(record.type or "").strip()]
                    added = self.main_dock.project.discover_domain_values(
                        "structure", values,
                        label=self.tr("Type de structure"))
                    if added:
                        log_lines.append(self.tr(
                            '<span style="color:#5DADE2;">&#8505; {} '
                            'nouveau(x) type(s) de structure ajouté(s) '
                            'au référentiel</span>').format(len(added)))
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Imagerie de trou (facultative, Chantier 2)
        imagery = self.tabs.get("imagery")
        if imagery and imagery.parse_result:
            bh, vr = validate_imagery(
                imagery.parse_result, cids, self.bundle.collars)
            self.bundle.imagery = bh
            total += vr.num_records
            errors += len(vr.errors)
            imagery.set_validation_result(vr)
            self._vr_map["imagery"] = vr
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; IMAGERIE '
                    '({}):</span>').format(vr.file_name))
                for error in vr.errors:
                    log_lines.append(
                        f'  <span style="color:#E74C3C;">&#10060; {error}</span>')
            else:
                # v2.9.262 — mode `copy` : duplique les photos dans
                # assets/ et réécrit les chemins en relatif projet.
                copied = 0
                try:
                    if self.main_dock.project:
                        source_dir = os.path.dirname(
                            str(imagery.parse_result.file_path or ""))
                        copied, _failed = \
                            self.main_dock.project.copy_imagery_assets(
                                bh, source_dir=source_dir)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed(
                        "Import : copie assets imagerie", _exc)
                if not imagery.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; Imagerie: '
                        '{} image(s)</span>').format(vr.num_records))
                if copied:
                    log_lines.append(self.tr(
                        '<span style="color:#5DADE2;">&#8505; {} image(s) '
                        'copiée(s) dans assets/ (mode copy)</span>'
                    ).format(copied))
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Géotechnique groupée (facultative, Chantier 3)
        for gft in ("rqd", "recovery", "density"):
            gtab = self.tabs.get(gft)
            if not (gtab and gtab.parse_result):
                continue
            bh, vr = validate_geotech(
                gtab.parse_result, gft, cids, self.bundle.collars)
            for hyd, records in bh.items():
                self.bundle.geotech.setdefault(hyd, []).extend(records)
            total += vr.num_records
            errors += len(vr.errors)
            gtab.set_validation_result(vr)
            self._vr_map[gft] = vr
            gname = self.tr(TAB_LABELS.get(gft, gft)).upper()
            if vr.errors:
                all_valid = False
                log_lines.append(self.tr(
                    '<span style="color:#E74C3C;">&#10060; {} '
                    '({}):</span>').format(gname, vr.file_name))
                for error in vr.errors:
                    log_lines.append(
                        f'  <span style="color:#E74C3C;">&#10060; {error}</span>')
            else:
                if not gtab.family_status().needs_attention:
                    log_lines.append(self.tr(
                        '<span style="color:#27AE60;">&#9989; {}: '
                        '{} mesure(s)</span>').format(gname, vr.num_records))
            warnings_count += len(vr.warnings)
            for warning in vr.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Contrôle croisé géotechnique : RQD ≤ récupération (avertissement,
        # jamais bloquant).  Les deux tables ne sont comparables qu'une
        # fois importées ensemble — d'où ce passage après la boucle.
        cross = validate_geotech_cross(self.bundle.geotech)
        if cross.issues:
            rqd_vr = self._vr_map.get("rqd")
            rqd_tab = self.tabs.get("rqd")
            if rqd_vr is not None and rqd_tab is not None:
                for issue in cross.issues:
                    rqd_vr.add_issue(
                        issue.severity, issue.code, issue.message,
                        suggestion=issue.suggestion)
                rqd_tab.set_validation_result(rqd_vr)
            warnings_count += len(cross.warnings)
            for warning in cross.warnings:
                log_lines.append(
                    f'<span style="color:#D68910;">&#9888; {warning}</span>')

        # Déviations verticales automatiques
        auto_count = 0
        for hid in cids:
            if hid not in self.bundle.surveys:
                self.bundle.surveys[hid] = auto_survey_for_vertical(self.bundle.collars[hid])
                auto_count += 1
        if auto_count:
            log_lines.append(self.tr(
                '<span style="color:#5DADE2;">&#8505; {} forage(s) sans '
                'mesure de déviation : trajectoires '
                'verticales automatiques</span>').format(auto_count))

        # Summary with hierarchy
        if all_valid and cids:
            message = self.tr(
                '✓ {} forages | {} enregistrements | 0 erreur').format(
                len(cids), total)
            if warnings_count:
                message += self.tr(
                    ' | {} avertissement(s)').format(warnings_count)
            self.summary_label.setText(message)
            colour = COLORS['warning'] if warnings_count else COLORS['success']
            self.summary_label.setStyleSheet(
                f"font-size: 10pt; font-weight: bold; color: {colour}; background: transparent; padding: 4px;")
        else:
            msg = self.tr('✗ {} erreur(s) | {} enregistrements').format(
                errors, total)
            if warnings_count:
                msg += self.tr(' | {} avertissement(s)').format(warnings_count)
            self.summary_label.setText(msg)
            self.summary_label.setStyleSheet(
                f"font-size: 10pt; font-weight: bold; color: {COLORS['danger']}; background: transparent; padding: 4px;")

        # v2.7.6 (VAL-01) : les erreurs/avertissements détaillés passent
        # par le panneau regroupé ; ici on ne garde que les lignes
        # d'information (succès, découvertes, déviations manquantes).
        info_lines = [
            line for line in log_lines
            if "&#10060;" not in line and "#D68910" not in line]
        self.validation_panel.update_from_validation(
            dict(self._vr_map), info_lines,
            missing_collar=not bool(self.bundle.collars))
        self._refresh_tab_badges()
        self.validity_changed.emit(all_valid and bool(cids))

    def restore_from_project(self) -> bool:
        """
        Restore step 2 UI + import bundle from the project's saved CSV
        copies (data_import/). Returns True if at least the collars were
        restored and validated.
        """
        proj = self.main_dock.project
        if not proj or not proj.has_imported_files():
            return False

        results = proj.reparse_imported_files()
        if not results:
            return False

        for ft in TAB_ORDER:
            tab = self.tabs.get(ft)
            if not tab:
                continue
            if ft in results:
                path = proj.get_imported_file_path(ft)
                tab.show_parse_result(path, results[ft], validate=False)
                proj.save_mappings(ft, results[ft].effective_mappings)
                if ft in STRUCTURE_TYPES:
                    proj.save_import_structure(ft, results[ft].structure)
            elif proj.config.get("imported_files", {}).get(ft):
                expected = proj.config["imported_files"][ft]
                tab.status_label.setText(
                    self.tr("Copie du projet introuvable ou "
                            "illisible : {}").format(expected))
                tab.status_label.setStyleSheet(
                    f"font-size: 9pt; color: {COLORS['danger']}; background: transparent;")

        self.step2_validate_all()
        return bool(self.bundle.collars)

    def reset_all(self):
        """Clear every tab and the shared validation panel."""
        for tab in self.tabs.values():
            tab.reset()
        self.bundle = ImportBundle()
        self._vr_map = {}
        self.summary_label.setText(self.tr("En attente d’import..."))
        self.validation_panel.update_from_validation({}, [], False)
        self._routing_log = []
        self._render_routing_log()
        self.router_zone.reset()
        self._refresh_tab_badges()

    def get_bundle(self):
        return self.bundle

    def get_assay_element_columns(self):
        at = self.tabs.get("assays")
        if not at or not at.parse_result:
            return []
        pr = at.parse_result
        maps = pr.effective_mappings
        from ..core.multi_assay import numeric_fraction
        elems = []
        for i, raw_h in enumerate(pr.raw_headers):
            canonical = maps.get(raw_h)
            if canonical and canonical in ("hole_id", "from", "to"):
                continue
            # v2.9.285 — seules les colonnes CHIFFRÉES deviennent teneurs
            if numeric_fraction(pr.rows, i) < 0.5:
                continue
            elems.append(canonical or raw_h)
        return elems
