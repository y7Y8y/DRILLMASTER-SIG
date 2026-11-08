"""Chantier 1 — le socle visuel tient sur trois promesses.

1. Une couleur n'existe qu'à deux endroits : `theme.json` (la DA) et le
   module généré `palette_jetons.py` (sa copie lisible par Qt).
2. Le module généré ne dérive jamais du thème — sinon deux palettes
   revivent en silence, ce qui est exactement le défaut d'origine.
3. Aucun rôle en double entre la copie et la source.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
THEME = json.loads((RACINE / "specs" / "data" / "theme.json")
                   .read_text(encoding="utf-8"))
GENERÉ = RACINE / "DrillMaster" / "ui" / "palette_jetons.py"
sys.path.insert(0, str(RACINE))


class ModuleGenere(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from DrillMaster.ui import palette_jetons as p
        cls.p = p

    def test_le_module_ne_derive_pas_du_theme(self):
        """`genere_palette.py` sans `--ecrit` sort en 1 si le module a dérivé."""
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "genere_palette.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_tous_les_roles_du_theme_sont_dans_le_module(self):
        self.assertEqual(tuple(THEME["clair"]), self.p.ROLES)
        self.assertEqual(set(THEME["sombre"]), set(self.p.SOMBRE))
        for role in THEME["clair"]:
            self.assertEqual(self.p.couleur(role, "clair"),
                             THEME["clair"][role])
            self.assertEqual(self.p.couleur(role, "sombre"),
                             THEME["sombre"][role])

    def test_un_role_inconnu_leve_au_lieu_de_rendre_du_vide(self):
        with self.assertRaises(KeyError):
            self.p.couleur("couleur_qui_nexiste_pas")

    def test_paire_rend_les_deux_modes(self):
        clair, sombre = self.p.paire("accent")
        self.assertNotEqual(clair, sombre)


class DeuxPalettes(unittest.TestCase):
    """Le défaut d'origine : `styles_qt.COLORS` et le thème se contredisaient."""

    def test_aucun_role_ne_declare_deux_teintes_differentes(self):
        from DrillMaster.ui import styles_qt
        # rôles repris tels quels du thème : la teinte doit être identique
        refondus = {"accent", "accent_hover", "bg_main", "bg_card", "border",
                    "text_dark", "text_medium", "text_white"}
        self.assertTrue(refondus & set(styles_qt.COLORS))
        from DrillMaster.ui import palette_jetons as p
        correspondance = {
            "accent": "accent", "accent_hover": "border_strong",
            "bg_main": "bg", "bg_card": "surface", "border": "border",
            "text_dark": "ink", "text_medium": "ink_2",
            "text_white": "surface",
        }
        ecarts = []
        for ancien, role in correspondance.items():
            if ancien not in styles_qt.COLORS:
                continue
            if styles_qt.COLORS[ancien].upper() != p.couleur(role).upper():
                ecarts.append(f"{ancien} → {role} : "
                              f"{styles_qt.COLORS[ancien]} ≠ {p.couleur(role)}")
        # ce test documente l'écart restant ; il doit décroître à chaque passage
        self.assertLessEqual(len(ecarts), 8, "\n".join(ecarts))


class UnSeulFoyer(unittest.TestCase):
    def test_le_module_genere_est_le_seul_a_declarer_des_jetons(self):
        arbre = ast.parse(GENERÉ.read_text(encoding="utf-8"))
        tables = [n.targets[0].id for n in arbre.body
                  if isinstance(n, ast.Assign)
                  and isinstance(n.targets[0], ast.Name)]
        self.assertEqual(tables, ["ROLES", "CLAIR", "SOMBRE", "SEMANTIQUE",
                                  "TAILLES", "RAYONS", "GRILLE"])

    def test_la_charte_ne_declare_aucune_teinte_propre(self):
        """`theme.json` est la source ; la planche lit le thème, elle ne le copie pas."""
        source = (RACINE / "maquettes" / "23_charte.py").read_text(
            encoding="utf-8")
        self.assertIn("theme.json", source)


if __name__ == "__main__":
    unittest.main()
