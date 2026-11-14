"""
DrillMaster — Shared UI Styles
===============================
Centralised, sober, professional colour palette and stylesheet helpers.
Geological aesthetic: earth tones, muted greys, clean lines.
v2.9.100 — densite UI fine (assistant steps + boutons + titres).
v2.9.101 — plus de carre bleu de focus Qt au milieu des boutons.
v2.9.395 — Lot DA-0 : les constantes vivent dans design_tokens.py
(source de vérité unique) ; ce module n'est que la traduction QSS
des tokens + les helpers. Corrections d'états : survol et désactivé
passent en VALEURS DE GRIS (les bleus #D6EAF8 / #AED6F1 étaient en
concurrence avec les teintes de données) ; échelle typographique
fermée (TYPE).
"""

from .design_tokens import COLORS, TYPE, FONT_FAMILY, FONT_MONO

# ---------------------------------------------------------------------------
# Colour palette — sober, geological (définie dans design_tokens.py)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Stylesheets
# ---------------------------------------------------------------------------
# v2.7.12.8 — REVUE ÉCRAN (« infobulle noir sur noir ») : sans règle
# explicite, l'infobulle hérite de la palette de QGIS — sous thème
# sombre, fond sombre et encre NOIRE (illisible). Le contexte de
# style d'une infobulle est le widget STYLÉ le PLUS PROCHE de l'élément
# survolé (lui-même ou un ancêtre) : chaque « contexte » du plugin
# porte donc cette règle — définie UNE SEULE FOIS ici et référencée :
#   • BASE_STYLE (racines des docks) ; les constantes de boutons,
#     champs et tables (widgets stylés en propre) ; les cadres de
#     scroll transparent (ancêtres stylés des groupes/lignes) ;
#   • TOOLTIP_STYLE à la racine de chaque dialogue ; les pastilles et
#     listes stylées en propre (step2, section dock).
TOOLTIP_STYLE = (
    f"QToolTip {{ color: {COLORS['ink_on_dark_hi']};"
    f" background-color: {COLORS['surface_dark']};"
    f" border: 1px solid {COLORS['primary_lt']}; padding: 3px;"
    " font-variant: small-caps; }")

BASE_STYLE = f"""
    QWidget {{
        background-color: {COLORS['bg_main']};
        font-family: {FONT_FAMILY};
        font-size: {TYPE['body']};
        color: {COLORS['text_dark']};
    }}
    QGroupBox {{
        font-weight: bold;
        color: {COLORS['primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 6px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }}
    /* v2.7.6.4 (UI-02) — revue écran : « on ne voit pas la case pour cocher
       ou décocher », « le bouton Parcourir est en fond noir ». Sous certains
       thèmes QGIS/Windows, un indicateur ou un bouton sans style explicite
       retombait sur la palette sombre de l'application hôte. */
    QGroupBox::indicator {{
        width: 13px;
        height: 13px;
        border: 1px solid {COLORS['border_dark']};
        border-radius: 2px;
        background: {COLORS['bg_card']};
    }}
    QGroupBox::indicator:checked {{
        background: {COLORS['accent']};
        border: 1px solid {COLORS['accent_hover']};
    }}
    QGroupBox::indicator:hover {{ border: 1px solid {COLORS['accent']}; }}
    QCheckBox {{ background: transparent; color: {COLORS['text_dark']}; }}
    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        border: 1px solid {COLORS['border_dark']};
        border-radius: 2px;
        background: {COLORS['bg_card']};
    }}
    QCheckBox::indicator:checked {{
        background: {COLORS['accent']};
        border: 1px solid {COLORS['accent_hover']};
    }}
    QCheckBox::indicator:disabled {{
        background: {COLORS['disabled_bg']};
        border: 1px solid {COLORS['border']};
    }}
    QPushButton {{
        background-color: {COLORS['bg_card']};
        color: {COLORS['text_dark']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 3px;
        padding: 3px 10px;
        font-size: {TYPE['body']};
        outline: none;
    }}
    QPushButton:hover {{ background-color: {COLORS['border']}; }}
    QPushButton:focus {{
        outline: none;
        border: 1px solid {COLORS['border_dark']};
        background-color: {COLORS['bg_card']};
    }}
    QPushButton:pressed {{
        outline: none;
        background-color: {COLORS['border']};
        border: 1px solid {COLORS['border_dark']};
    }}
    QPushButton:disabled {{
        color: {COLORS['text_light']};
        border-color: {COLORS['border']};
    }}
    QToolButton {{
        outline: none;
    }}
    QToolButton:focus {{
        outline: none;
        border: 1px solid {COLORS['border_dark']};
    }}
    QScrollArea {{ background: transparent; border: none; }}
    QLabel {{
        background: transparent;
        color: {COLORS['text_dark']};
    }}
    QLabel#label_hint {{
        color: {COLORS['text_light']};
        font-size: {TYPE['small']};
    }}
    QLabel#label_title {{
        font-size: {TYPE['title']};
        font-weight: bold;
        color: {COLORS['primary']};
    }}
    QLabel#label_subtitle {{
        color: {COLORS['text_medium']};
        font-size: {TYPE['small']};
    }}
    QLabel#label_section {{
        font-size: {TYPE['body']};
        font-weight: bold;
        color: {COLORS['primary']};
        padding: 1px 0px;
    }}
""" + TOOLTIP_STYLE

BUTTON_PRIMARY = f"""
    QPushButton {{
        background-color: {COLORS['accent']};
        color: white;
        border: none;
        border-radius: 3px;
        padding: 4px 12px;
        font-size: {TYPE['body']};
        min-height: 24px;
        outline: none;
    }}
    QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}
    QPushButton:focus {{
        outline: none;
        border: none;
        background-color: {COLORS['accent']};
    }}
    QPushButton:pressed {{
        outline: none;
        background-color: {COLORS['primary']};
        border: none;
    }}
    QPushButton:disabled {{
        background-color: {COLORS['disabled_bg']};
        color: {COLORS['disabled_ink']};
    }}
""" + TOOLTIP_STYLE

BUTTON_SECONDARY = f"""
    QPushButton {{
        background-color: {COLORS['bg_card']};
        color: {COLORS['text_dark']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 3px;
        padding: 4px 12px;
        font-size: 9pt;
        min-height: 24px;
        outline: none;
    }}
    QPushButton:hover {{ background-color: {COLORS['border']}; }}
    QPushButton:focus {{
        outline: none;
        border: 1px solid {COLORS['border_dark']};
        background-color: {COLORS['bg_card']};
    }}
    QPushButton:pressed {{
        outline: none;
        background-color: {COLORS['border']};
        border: 1px solid {COLORS['border_dark']};
    }}
    QPushButton:disabled {{ color: {COLORS['text_light']};
                            border-color: {COLORS['border']};
                            background-color: {COLORS['bg_main']}; }}
    QToolButton {{
        outline: none;
    }}
    QToolButton:focus {{
        outline: none;
        border: 1px solid {COLORS['border_dark']};
        background-color: {COLORS['bg_card']};
    }}
""" + TOOLTIP_STYLE

# v2.7.6.5 (UI-03) — bouton compact des listes de validation : la version
# standard (padding 8/16 px) tronquait son texte dans une ligne de 20 px.
BUTTON_COMPACT = f"""
    QPushButton {{
        background-color: {COLORS['bg_card']};
        color: {COLORS['text_dark']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 3px;
        padding: 1px 8px;
        font-size: {TYPE['compact']};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent']};
        color: {COLORS['text_white']};
        border-color: {COLORS['accent_hover']};
    }}
    QPushButton:focus {{
        outline: none;
        border: 1px solid {COLORS['border_dark']};
        background-color: {COLORS['bg_card']};
    }}
    QPushButton:pressed {{
        outline: none;
        background-color: {COLORS['border']};
    }}
""" + TOOLTIP_STYLE

BUTTON_SUCCESS = f"""
    QPushButton {{
        background-color: {COLORS['success']};
        color: white;
        border: none;
        border-radius: 3px;
        padding: 4px 12px;
        font-size: {TYPE['body']};
        min-height: 24px;
        outline: none;
    }}
    QPushButton:hover {{ background-color: #229954; }}
    QPushButton:focus {{
        outline: none;
        border: none;
        background-color: {COLORS['success']};
    }}
    QPushButton:pressed {{
        outline: none;
        background-color: #1E8449;
        border: none;
    }}
    QPushButton:disabled {{
        background-color: {COLORS['disabled_bg']};
        color: {COLORS['disabled_ink']};
    }}
""" + TOOLTIP_STYLE

INPUT_STYLE = f"""
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_dark']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 3px;
        padding: 3px 6px;
        font-size: 9pt;
        min-height: 22px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1px solid {COLORS['accent']};
    }}
    QComboBox QListView {{
        background-color: {COLORS['bg_card']};
        color: {COLORS['text_dark']};
        border: 1px solid {COLORS['border_dark']};
        outline: 0;
        selection-background-color: {COLORS['accent']};
        selection-color: {COLORS['text_white']};
    }}
    QComboBox QListView::item {{
        min-height: 20px;
        padding: 2px 6px;
        color: {COLORS['text_dark']};
    }}
    QComboBox QListView::item:selected {{
        background-color: {COLORS['accent']};
        color: {COLORS['text_white']};
    }}
    QComboBox QListView::item:hover {{
        background-color: {COLORS['hover_subtle']};
        color: {COLORS['text_dark']};
    }}
""" + TOOLTIP_STYLE


def apply_combo_popup_style(combo):
    """Force readable combo colours independently of the QGIS/OS palette.

    Some Windows themes ignore inherited QSS selection colours for the private
    QComboBox list view. Applying both a direct view stylesheet and palette
    prevents a selected label from becoming white on white.
    """
    if combo is None:
        return
    from qgis.PyQt.QtGui import QColor, QPalette
    from qgis.PyQt.QtWidgets import (
        QStyle, QStyledItemDelegate, QStyleOptionViewItem)

    class _ReadableComboDelegate(QStyledItemDelegate):
        def paint(self, painter, option, index):
            styled = QStyleOptionViewItem(option)
            selected = bool(styled.state & QStyle.State_Selected)
            hovered = bool(styled.state & QStyle.State_MouseOver)
            painter.save()
            if selected:
                painter.fillRect(styled.rect, QColor(COLORS["accent"]))
                text_colour = QColor(COLORS["text_white"])
            elif hovered:
                painter.fillRect(styled.rect, QColor(COLORS["hover_subtle"]))
                text_colour = QColor(COLORS["text_dark"])
            else:
                text_colour = QColor(COLORS["text_dark"])
            # Background is painted explicitly. Removing native state flags
            # prevents Windows/QGIS themes from repainting it white-on-white.
            styled.state &= ~QStyle.State_Selected
            styled.state &= ~QStyle.State_MouseOver
            styled.palette.setColor(QPalette.Text, text_colour)
            styled.palette.setColor(QPalette.WindowText, text_colour)
            super().paint(painter, styled, index)
            painter.restore()

    combo_palette = combo.palette()
    combo_palette.setColor(QPalette.Text, QColor(COLORS["text_dark"]))
    combo_palette.setColor(QPalette.ButtonText, QColor(COLORS["text_dark"]))
    combo_palette.setColor(QPalette.Highlight, QColor(COLORS["accent"]))
    combo_palette.setColor(
        QPalette.HighlightedText, QColor(COLORS["text_white"]))
    combo.setPalette(combo_palette)

    view = combo.view()
    view_palette = view.palette()
    view_palette.setColor(QPalette.Base, QColor(COLORS["bg_card"]))
    view_palette.setColor(QPalette.Window, QColor(COLORS["bg_card"]))
    view_palette.setColor(QPalette.Text, QColor(COLORS["text_dark"]))
    view_palette.setColor(QPalette.WindowText, QColor(COLORS["text_dark"]))
    view_palette.setColor(QPalette.Highlight, QColor(COLORS["accent"]))
    view_palette.setColor(
        QPalette.HighlightedText, QColor(COLORS["text_white"]))
    view.setPalette(view_palette)
    view.setStyleSheet(f"""
        QListView {{
            background: {COLORS['bg_card']};
            color: {COLORS['text_dark']};
            outline: 0;
            selection-background-color: {COLORS['accent']};
            selection-color: {COLORS['text_white']};
        }}
        QListView::item {{
            min-height: 20px;
            padding: 2px 6px;
            color: {COLORS['text_dark']};
        }}
        QListView::item:selected {{
            background: {COLORS['accent']};
            color: {COLORS['text_white']};
        }}
        QListView::item:hover:!selected {{
            background: {COLORS['hover_subtle']};
            color: {COLORS['text_dark']};
        }}
    """)
    delegate = _ReadableComboDelegate(combo)
    combo.setItemDelegate(delegate)
    # Keep a Python reference because Qt otherwise owns only the C++ wrapper.
    combo._drillmaster_combo_delegate = delegate

TABLE_STYLE = f"""
    /* v2.7.12.3 — retour écran (tache noire à côté de Hole_ID, toujours
       présente en v2.7.12.2) : le coin haut-gauche de la table est un
       CHILD WIDGET de la table ; son fond se résout sur la règle
       ``QWidget`` (classe de base) du style de la table — et si elle
       manque, QGIS réinjecte SA règle ``QWidget`` sombre. Vérifié au
       rendu : les règles ``QTableWidget``/``QHeaderView`` ne couvrent
       PAS le coin, seule ``QWidget`` fonctionne. */
    QWidget {{
        background-color: {COLORS['bg_main']};
    }}
    QTableWidget {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        gridline-color: {COLORS['border']};
        font-size: {TYPE['small']};
    }}
    /* v2.7.12.2 — le coin haut-gauche (au-dessus des numéros de ligne)
       — la règle ::section seule ne le couvre PAS, il faut aussi le
       niveau widget. */
    QHeaderView {{
        background-color: {COLORS['bg_main']};
    }}
    QHeaderView::section {{
        background-color: {COLORS['bg_main']};
        color: {COLORS['primary']};
        font-weight: bold;
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        padding: 3px 6px;
    }}
    /* v2.7.12.8 — l'infobulle est portée par TOOLTIP_STYLE (constante
       unique, ajoutée en fin de chaîne) : le contexte de style d'une
       infobulle est le widget stylé le plus proche de l'élément survolé,
       une table stylée est donc son propre contexte. */
""" + TOOLTIP_STYLE

TAB_STYLE = f"""
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        background: {COLORS['bg_card']};
    }}
    QTabBar::tab {{
        padding: 4px 10px;
        margin-right: 2px;
        font-size: {TYPE['small']};
        border: 1px solid {COLORS['border']};
        border-bottom: none;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
        background: {COLORS['bg_main']};
        color: {COLORS['text_medium']};
    }}
    QTabBar::tab:selected {{
        background: {COLORS['accent']};
        color: white;
        border-color: {COLORS['accent']};
    }}
    QTabBar::tab:!selected {{
        background: {COLORS['bg_main']};
        margin-top: 2px;
    }}
"""

LOG_STYLE = f"""
    QTextEdit {{
        background-color: {COLORS['surface_code']};
        color: {COLORS['ink_on_dark']};
        font-family: {FONT_MONO};
        font-size: {TYPE['body']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 3px;
    }}
"""

PROGRESS_STYLE = f"""
    QProgressBar {{
        border: 1px solid {COLORS['border_dark']};
        border-radius: 3px;
        text-align: center;
        height: 16px;
        font-size: {TYPE['small']};
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['accent']};
        border-radius: 2px;
    }}
"""

CHECKBOX_STYLE = f"""
    QCheckBox {{
        font-size: {TYPE['compact']};
        color: {COLORS['text_dark']};
        spacing: 5px;
    }}
"""


def suppress_button_focus_rects(root_widget) -> None:
    """v2.9.101 — retire le rectangle de focus natif (carre bleu) des boutons.

    Le QSS ``outline: none`` ne suffit pas toujours sous les themes QGIS /
    Windows : le style natif dessine encore un focus rect.  On coupe le
    focus clavier des boutons d'action (pas des champs de saisie).
    """
    try:
        from qgis.PyQt.QtCore import QCoreApplication, Qt
        from qgis.PyQt.QtWidgets import QPushButton, QToolButton, QWidget
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("styles_qt : suppress_button_focus_rects", _exc)
        return
    if root_widget is None:
        return
    for cls in (QPushButton, QToolButton):
        for btn in root_widget.findChildren(cls):
            try:
                btn.setFocusPolicy(Qt.NoFocus)
                # macOS / certains styles
                btn.setAttribute(Qt.WA_MacShowFocusRect, False)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("styles_qt : suppress_button_focus_rects", _exc)
                # style natif sans WA_MacShowFocusRect
                pass


def make_collapsible_help(text: str, parent=None):
    """ⓘ Aide repliée par défaut — pattern unique (v2.9.124).

    Tous les longs textes d'aide du plugin passent par ici : pas de
    surcharge permanente, dépliable au clic. Retourne le widget
    conteneur ; ``._help_body`` = QLabel (texte encore mutable).
    """
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtCore import QCoreApplication
    from qgis.PyQt.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QToolButton)

    wrap = QWidget(parent)
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(2)
    hint_btn = QToolButton(wrap)
    hint_btn.setText(QCoreApplication.translate("StylesQt", "ⓘ Aide"))
    hint_btn.setCheckable(True)
    hint_btn.setChecked(False)
    hint_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
    hint_btn.setCursor(Qt.PointingHandCursor)
    hint_btn.setToolTip(QCoreApplication.translate("StylesQt", "Afficher l'aide"))
    hint_btn.setStyleSheet(
        f"QToolButton {{ color:{COLORS['text_medium']}; border:none; "
        f"padding:2px 0; font-size:{TYPE['small']}; text-align:left; }}"
        f"QToolButton:checked {{ font-weight:bold; }}")
    hint_lab = QLabel(str(text or ""), wrap)
    hint_lab.setObjectName("label_hint")
    hint_lab.setWordWrap(True)
    hint_lab.setVisible(False)
    hint_btn.toggled.connect(hint_lab.setVisible)
    # CHK-35 — rallumeur : même setter, argument non-const
    hint_lab.setVisible(hint_btn.isChecked())
    lay.addWidget(hint_btn, 0, Qt.AlignLeft)
    lay.addWidget(hint_lab)
    wrap._help_btn = hint_btn
    wrap._help_body = hint_lab
    return wrap
