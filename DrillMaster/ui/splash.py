"""DrillMaster — Écran de démarrage du plugin (v2.9.220).

Retour écran : « je veux qu'il fasse un démarreur de plugin qui
affiche l'icône, le nom et un chargement ».  Affiché au PREMIER
clic sur le bouton DrillMaster (jamais au lancement de QGIS —
aucune animation imposée à ceux qui ne s'en servent pas), il suit
la progression RÉELLE de la création des docks — pas de délai
artificiel : quand la barre est pleine, le plugin est prêt.

Langage visuel : fond de marque #171D22 (celui de la vue 3D),
accent cyan sélection #00E5FF, icône « Carotte / Stratification ».
"""

from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog, QLabel, QProgressBar, QVBoxLayout, QWidget,
)

# v2.9.226 — CONSTANTES DE MARQUE LOCALES : le démarreur est une
# surface de MARQUE (comme l'icône) — il ne dépend PLUS de
# COLORS['accent'] (le passage au chrome neutre v2.9.225 l'avait
# rendu invisible : anthracite sur fond sombre).  Le cyan est la
# couleur SIGNAL réservée (celle du contour de sélection 2D) : une
# barre de chargement EST un signal — règle « couleur = données ou
# alerte » respectée.
BRAND_BG = "#171D22"        # fond de marque (vue 3D)
BRAND_SIGNAL = "#00E5FF"    # cyan signal (sélection 2D/3D)
BRAND_TEXT_DIM = "#95A5A6"  # texte secondaire sur sombre


class PluginSplash(QDialog):
    """Démarreur : icône + nom + version + barre de chargement."""

    def __init__(self, parent=None, version: str = "", n_steps: int = 6):
        # v2.9.223 — le NOMBRE DE MARCHES est donné par l'appelant :
        # la barre doit finir PLEINE (retour écran : « le chargement
        # ne charge pas jusqu'à la fin » — la v2.9.222 mettait 8
        # marches pour 6 étapes : la barre s'arrêtait à 75 %).
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        # v2.9.221 — FOND PLEIN, RECTANGLE NET (retour écran : « je
        # croyais qu'il allait être plus visible — mets-lui un fond
        # visible, rectangle avec le logo »).  La transparence de la
        # v2.9.220 rendait mal sous Windows/QGIS (fenêtre fantôme) :
        # rectangle opaque #171D22 + bordure CYAN 2 px — impossible
        # à manquer, sur n'importe quel thème.
        self.setModal(False)
        self._n_steps = max(1, int(n_steps))
        self._step = 0

        self.setObjectName("DrillMasterSplash")
        self.setStyleSheet(f"""
            QDialog {{
                background: {BRAND_BG};
                border: 2px solid {BRAND_SIGNAL};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(44, 34, 44, 30)
        lay.setSpacing(10)

        # icône (badge arrondi déjà transparent)
        icon_label = QLabel()
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "icon.png")
        if os.path.isfile(icon_path):
            pm = QPixmap(icon_path)
            if not pm.isNull():
                icon_label.setPixmap(
                    pm.scaled(128, 128,
                              Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon_label)

        title = QLabel(self.tr("DrillMaster"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #FDFEFE; font-size: 24pt; font-weight: bold; "
            "letter-spacing: 2px;")
        lay.addWidget(title)

        # v2.9.227 — Lot 1a : sous-titre traduisible (contexte =
        # PluginSplash).
        from qgis.PyQt.QtCore import QCoreApplication as _QCA
        sub = QLabel(_QCA.translate(
            "PluginSplash", "Modélisation de forages miniers"))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(
            f"color: {BRAND_TEXT_DIM}; font-size: 8.5pt;")
        lay.addWidget(sub)

        if version:
            ver = QLabel(f"v{version}")
            ver.setAlignment(Qt.AlignCenter)
            # v2.9.226 — cyan SIGNAL : lisible sur le fond de marque
            # (contraste ~13:1) — plus jamais COLORS['accent']
            ver.setStyleSheet(
                f"color: {BRAND_SIGNAL}; font-size: 8pt;")
            lay.addWidget(ver)

        self.bar = QProgressBar()
        self.bar.setRange(0, self._n_steps)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background: #26313A; border: none; border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {BRAND_SIGNAL}; border-radius: 3px;
            }}
        """)
        lay.addSpacing(6)
        lay.addWidget(self.bar)

        self.status = QLabel(self.tr("Initialisation…"))
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(
            f"color: {BRAND_TEXT_DIM}; font-size: 8pt;")
        lay.addWidget(self.status)

        self.setFixedWidth(400)

        # 356 — ANTI-RELIQUAT : quoi que fasse la boucle d'événements
        # du PC (saturée, lente), le démarreur s'autodétruit au bout
        # de 15 s MAXIMUM.  Plus jamais de logo figé par-dessus QGIS
        # (ou le navigateur, vu en retour écran).
        from qgis.PyQt.QtCore import QTimer
        self._watchdog = QTimer(self)
        self._watchdog.setSingleShot(True)
        self._watchdog.timeout.connect(self._force_gone)
        self._watchdog.start(15000)

    def _force_gone(self) -> None:
        """356 : caché + détruit, sans jamais lever."""
        try:
            if self.isVisible():
                self.hide()
            self.deleteLater()
        except Exception as _exc:
            # watchdog de secours : un échec ici ne doit JAMAIS
            # remonter (on est déjà dans le filet de sécurité).
            from ..core.diagnostics import log_swallowed
            log_swallowed("Démarreur : watchdog anti-reliquat", _exc)

    def finish(self, message: str = ""):
        """v2.9.223 — barre PLEINE garantie à la fin, quoi qu'il
        arrive (étape sautée, chemin court) : le chargement finit
        toujours à 100 %."""
        self._step = self._n_steps
        self.bar.setValue(self._n_steps)
        if message:
            self.status.setText(message)
        # 356 — chargé = plus « au-dessus de tout » : même si un
        # reliquat tardait, il ne couvre plus les autres fenêtres.
        try:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        except Exception as _exc:
            # cosmétique : si le backend refuse, le watchdog et la
            # fermeture planifiée restent les filets principaux.
            from ..core.diagnostics import log_swallowed
            log_swallowed("Démarreur : fin d'au-dessus-de-tout", _exc)
        try:
            from qgis.PyQt.QtWidgets import QApplication
            QApplication.processEvents()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Démarreur : fin de barre (ignorée)", _exc)

    def step(self, message: str):
        """Avance la progression d'un cran et affiche le message."""
        self._step = min(self._step + 1, self._n_steps)
        self.bar.setValue(self._step)
        if message:
            self.status.setText(message)
        try:
            from qgis.PyQt.QtWidgets import QApplication
            QApplication.processEvents()
        except Exception as _exc:
            # SILENCE JUSTIFIÉ (v2.9.220) : hors QGIS (tests), le
            # splash n'est pas peint — la création continue.
            from ..core.diagnostics import log_swallowed
            log_swallowed("Démarreur : rafraîchissement de l'écran "
                          "de démarrage (ignoré)", _exc)


def make_splash(parent=None, version: str = "", n_steps: int = 6):
    """Construit le splash SANS jamais faire échouer le démarrage :
    en cas de problème (environnement têteu), retourne None et le
    plugin démarre sans écran."""
    try:
        return PluginSplash(parent, version=version, n_steps=n_steps)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Démarreur : création de l'écran de démarrage "
                      "(plugin démarré sans splash)", _exc)
        return None
