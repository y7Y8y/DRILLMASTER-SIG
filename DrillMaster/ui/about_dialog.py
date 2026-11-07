"""DrillMaster — dialogue « À propos » (v2.9.272).

Vue seule : **toutes** les valeurs affichées viennent de
``core.about.about_info()`` — aucune lecture de fichier, aucune constante
d'attribution et aucune logique dans ce module (règle « pas de logique
dans la vue »).  Le dialogue peut donc être testé en injectant un
dictionnaire ``info`` fictif, sans QGIS ni fichier de métadonnées.

Accès : menu QGIS « &DrillMaster ▸ À propos » ET le bouton ⓘ de l'en-tête
de l'atelier (même dialogue, deux portes d'entrée).

Chrome neutre (v2.9.225, DA-1) : la couleur est un canal réservé aux
données — cette fenêtre travaille en noir/gris/blanc uniquement.
"""

from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QVBoxLayout,
    QWidget,
)

from ..core.about import about_info
from .styles_qt import COLORS


class AboutDialog(QDialog):
    """Fiche d'identité du plugin : auteur, version, licence, dépôt."""

    def __init__(self, parent=None, info=None):
        super().__init__(parent)
        self.info = dict(info or about_info())
        self.setObjectName("DrillMasterAboutDialog")
        self.setWindowTitle(self.tr("À propos de DrillMaster"))
        self.setMinimumWidth(470)
        self.setModal(True)
        self._build()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(10)

        # ── En-tête : icône + nom + version ──────────────────────────
        head = QHBoxLayout()
        head.setSpacing(10)
        icon_label = QLabel(self)
        icon_label.setObjectName("about_icon")
        icon_label.setFixedSize(48, 48)
        icon_label.setScaledContents(True)
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "icon.png")
        if os.path.isfile(icon_path):
            icon_label.setPixmap(QPixmap(icon_path))
        head.addWidget(icon_label)

        titles = QVBoxLayout()
        titles.setSpacing(1)
        name = QLabel(str(self.info.get("name") or "DrillMaster"), self)
        name.setObjectName("about_name")
        name.setStyleSheet(
            f"font-size:15pt; font-weight:bold; color:{COLORS['primary']};")
        titles.addWidget(name)
        version = QLabel(
            self.tr("Version {}").format(self.info.get("version") or "—"),
            self)
        version.setObjectName("about_version")
        version.setStyleSheet(
            f"color:{COLORS['text_medium']}; font-size:9pt;")
        titles.addWidget(version)
        head.addLayout(titles)
        head.addStretch()
        lay.addLayout(head)

        lay.addWidget(self._separator())

        # ── Attribution & droits ─────────────────────────────────────
        lay.addWidget(self._row(self.tr("Auteur"),
                                str(self.info.get("author") or "—"),
                                "about_author"))
        lay.addWidget(self._row(self.tr("Droits"),
                                str(self.info.get("copyright") or "—"),
                                "about_copyright"))
        lay.addWidget(self._row(
            self.tr("Licence"),
            "{} ({})".format(self.info.get("license_name") or "—",
                             self.info.get("license_id") or "—"),
            "about_license"))
        lay.addWidget(self._row(self.tr("Dépôt"),
                                str(self.info.get("repository") or "—"),
                                "about_repository", link=True))
        if self.info.get("qgis_minimum") or self.info.get("qgis_maximum"):
            lay.addWidget(self._row(
                self.tr("Versions QGIS prises en charge"),
                self.tr("{} à {}").format(
                    self.info.get("qgis_minimum") or "—",
                    self.info.get("qgis_maximum") or "—"),
                "about_qgis_range"))

        lay.addWidget(self._separator())

        # ── Description reprise des métadonnées du paquet ────────────
        description = str(self.info.get("description") or "")
        if description:
            label = QLabel(description, self)
            label.setObjectName("about_description")
            label.setWordWrap(True)
            label.setStyleSheet(f"color:{COLORS['text_dark']};")
            lay.addWidget(label)

        # ── Avis de licence (texte libre, jamais inventé) ────────────
        notice = QLabel(
            self.tr("Ce plugin est un logiciel libre : vous pouvez le "
                    "redistribuer et/ou le modifier selon les termes de "
                    "la Licence Publique Générale GNU publiée par la Free "
                    "Software Foundation, soit la version 2 de la licence, "
                    "soit (à votre convenance) toute version ultérieure."),
            self)
        notice.setObjectName("about_license_notice")
        notice.setWordWrap(True)
        notice.setStyleSheet(
            f"color:{COLORS['text_medium']}; font-size:8pt;")
        lay.addWidget(notice)

        warranty = QLabel(
            self.tr("Ce plugin est distribué dans l'espoir qu'il sera "
                    "utile, mais SANS AUCUNE GARANTIE, sans même la garantie "
                    "implicite de qualité marchande ou d'adéquation à un "
                    "usage particulier."),
            self)
        warranty.setObjectName("about_warranty")
        warranty.setWordWrap(True)
        warranty.setStyleSheet(
            f"color:{COLORS['text_medium']}; font-size:8pt;")
        lay.addWidget(warranty)

        if self.info.get("license_installed"):
            source = QLabel(
                self.tr("Le texte intégral de la licence figure dans le "
                        "fichier LICENSE à la racine du dépôt."),
                self)
            source.setObjectName("about_license_file")
        else:
            source = QLabel(
                self.tr("Fichier LICENSE introuvable à la racine du dépôt."),
                self)
            source.setObjectName("about_license_missing")
        source.setWordWrap(True)
        source.setStyleSheet(
            f"color:{COLORS['text_light']}; font-size:8pt;")
        lay.addWidget(source)

        lay.addWidget(self._separator())

        # ── Portée (règle projet : aucune déclaration de conformité) ─
        scope = QLabel(
            self.tr("Les sorties de DrillMaster sont des aides à la "
                    "documentation géologique : elles ne constituent ni une "
                    "déclaration de ressources, ni un rapport de personne "
                    "compétente."),
            self)
        scope.setObjectName("about_scope")
        scope.setWordWrap(True)
        scope.setStyleSheet(
            f"color:{COLORS['text_dark']}; font-size:8pt; "
            f"background:{COLORS['bg_main']}; border:1px solid "
            f"{COLORS['border']}; border-radius:3px; padding:6px;")
        lay.addWidget(scope)

        lay.addStretch()

        # ── Bouton Fermer ────────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.setObjectName("about_buttons")
        close = buttons.button(QDialogButtonBox.Close)
        if close is not None:
            close.setText(self.tr("Fermer"))
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        lay.addWidget(buttons)

    # ------------------------------------------------------------------
    # Petits helpers de mise en page (aucune donnée, aucune règle métier)
    # ------------------------------------------------------------------
    def _separator(self) -> QFrame:
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(
            f"background-color:{COLORS['border']}; border:none;")
        return line

    def _row(self, caption: str, value: str, object_name: str,
             link: bool = False) -> QWidget:
        """Une ligne « libellé : valeur » (libellé en gris, valeur en noir)."""
        row = QWidget(self)
        row.setObjectName(object_name)
        grid = QHBoxLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        key = QLabel(caption, row)
        key.setStyleSheet(
            f"color:{COLORS['text_medium']}; font-size:9pt;")
        key.setMinimumWidth(190)
        grid.addWidget(key)
        val = QLabel(value, row)
        val.setWordWrap(True)
        val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if link and value.startswith("http"):
            val.setTextInteractionFlags(
                Qt.TextBrowserInteraction)
            val.setText(f'<a href="{value}">{value}</a>')
            val.setOpenExternalLinks(True)
        val.setStyleSheet(f"color:{COLORS['text_dark']}; font-size:9pt;")
        grid.addWidget(val, 1)
        return row


def make_about_icon() -> QIcon:
    """Icône du plugin pour l'entrée de menu (vide si icon.png absent)."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "icon.png")
    if os.path.isfile(path):
        return QIcon(path)
    return QIcon()
