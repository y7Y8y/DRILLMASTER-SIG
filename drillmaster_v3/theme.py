"""Thème — lecture unique des jetons visuels (couleurs, typo, rayons, disposition).

`maquettes/ui.py` et le futur plugin Qt lisent **ce même module**. Un seul
hexadécimal dans le dépôt : `specs/data/theme.json`.
"""
from __future__ import annotations

import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
FICHIER = RACINE / "specs" / "data" / "theme.json"


class Theme:
    def __init__(self, sombre=False, chemin=FICHIER):
        donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
        self.donnees = donnees
        self.sombre = sombre
        for cle, valeur in (donnees["sombre" if sombre else "clair"]).items():
            setattr(self, cle, valeur)
        self.typographie = donnees["typographie"]
        self.rayons = donnees["rayons"]
        self.espacements = donnees["espacements"]
        self.disposition = donnees["disposition"]
        self._semantique = donnees["semantique"]

    def couleur_etat(self, cle):
        """Rend la couleur d'un niveau, jamais l'accent de marque (R-19)."""
        jeton = self._semantique[cle]
        return getattr(self, jeton)

    def qss(self):
        """Feuille de style Qt — générée, jamais écrite à la main."""
        return f"""
        QWidget {{ background: {self.bg}; color: {self.ink};
                   font-size: {self.typographie['corps']}px; }}
        QFrame#surface {{ background: {self.surface};
                          border: 1px solid {self.border};
                          border-radius: {self.rayons['surface']}px; }}
        QPushButton {{ background: {self.surface}; color: {self.ink};
                       border: 1px solid {self.border_strong};
                       border-radius: {self.rayons['bouton']}px;
                       padding: 6px 12px; }}
        QPushButton#primaire {{ background: {self.accent}; color: #FFFFFF;
                                border: none; }}
        QLineEdit, QComboBox {{ background: {self.surface};
                                border: 1px solid {self.border_strong};
                                border-radius: {self.rayons['champ']}px;
                                padding: 4px 8px; }}
        QCheckBox::indicator:checked {{ background: {self.accent};
                                        border-radius: 3px; }}
        QToolTip {{ background: {self.surface}; color: {self.ink};
                    border: 1px solid {self.border}; }}
        """


def theme_pour(mode="clair"):
    return Theme(sombre=(mode == "sombre"))


theme = Theme()
