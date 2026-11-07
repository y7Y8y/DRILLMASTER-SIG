"""La charte visuelle est une image ; le thème est la vérité.

Ces tests vérifient que la planche de charte ne réinvente aucune valeur.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

THEME = json.loads((RACINE / "specs" / "data" / "theme.json").read_text(
    encoding="utf-8"))
SOURCE = (RACINE / "maquettes" / "23_charte.py").read_text(encoding="utf-8")


class Charte(unittest.TestCase):
    def test_aucune_couleur_en_dur_dans_la_charte(self):
        import re
        # les seules couleurs autorisées sont celles des données (lithologie,
        # teneurs) : elles viennent du Référentiel, pas du thème.
        couleurs = re.findall(r'"#([0-9A-Fa-f]{6})"', SOURCE)
        connues = {"FFFFFF"}
        for section in ("clair", "sombre"):
            connues |= {v.lstrip("#").upper() for v in THEME[section].values()}
        ref = json.loads((RACINE / "specs" / "data" / "referentiel.json")
                         .read_text(encoding="utf-8"))
        connues |= {v.lstrip("#").upper() for v in ref["lithologie"].values()}
        connues |= {v.lstrip("#").upper() for v in ref["teneur"]}
        for c in couleurs:
            self.assertIn(c.upper(), connues,
                          f"couleur {c} sans foyer : ni thème ni référentiel")

    def test_six_tailles_de_police_exactement(self):
        self.assertEqual(len(THEME["typographie"]), 6)

    def test_trois_roles_de_bouton_documentes(self):
        for role in ("primaire", "secondaire", "discret"):
            self.assertIn(role, SOURCE.lower())

    def test_grille_de_4px(self):
        grille = THEME["espacements"]["grille"]
        self.assertEqual(grille, 4)
        for valeur in THEME["espacements"].values():
            self.assertEqual(valeur % grille, 0, f"{valeur} n'est pas multiple de 4")


if __name__ == "__main__":
    unittest.main()
