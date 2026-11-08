"""Chantier 6 — les rangements, tenus par des cliquets.

Un cliquet ne dit pas « c'est bien rangé » : il dit **ça ne peut pas
empirer en silence**. Chaque chiffre ci-dessous est une mesure, pas une
impression ; quand une tranche sort du monolithe, on baisse le cliquet
dans le même commit.
"""
from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PLUGIN = RACINE / "DrillMaster"
DOCK = PLUGIN / "ui" / "section_dock.py"
SOCLE = PLUGIN / "ui" / "coupe_socle.py"

# Cliquet : section_dock.py ne doit jamais remonter au-dessus de cette valeur.
# 11 529 avant le chantier 6 → 10 515 après la tranche 1 (socle + journal).
PLAFOND_DOCK = 10_560
# Un seul fichier du plugin a le droit de dépasser 3 000 lignes. Quand il
# n'y en aura plus aucun, cette constante passera à 0.
FICHIERS_GEANTS_AUTORISES = 1


def lignes(p: Path) -> int:
    return len(p.read_text(encoding="utf-8").splitlines())


def noms_du_module(p: Path) -> set:
    arbre = ast.parse(p.read_text(encoding="utf-8"))
    out = set()
    for n in arbre.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            out.update(t.id for t in n.targets if isinstance(t, ast.Name))
    return out


class Cliquets(unittest.TestCase):
    def test_le_monolithe_ne_remonte_pas(self):
        n = lignes(DOCK)
        self.assertLessEqual(n, PLAFOND_DOCK, (
            f"section_dock.py fait {n} lignes (plafond {PLAFOND_DOCK}). "
            "Une fonctionnalité ajoutée ici doit sortir dans un module "
            "de tranche, pas gonfler le monolithe."))

    def test_un_seul_fichier_geant(self):
        geants = [p for p in PLUGIN.rglob("*.py")
                  if lignes(p) > 3000]
        self.assertLessEqual(len(geants), FICHIERS_GEANTS_AUTORISES,
                             [str(p.relative_to(PLUGIN)) for p in geants])


class Tranche1(unittest.TestCase):
    """Ce que la tranche 1 a sorti doit rester sorti ET rester accessible."""

    DELEGUES = {
        "SELECTION_HIGHLIGHT_COLOR", "LEGEND_CLICK_COLOR",
        "SELECTION_OUTLINE_PEN_DOCK", "SELECTION_OUTLINE_PEN_EXPORT",
        "_LITHO_BRUSH_PATTERNS", "_LINE_BRUSH_STYLES",
        "_pattern_ink_colour", "_selection_highlight_pen",
        "_selection_chrome_stylesheet", "_export_smallcaps_font",
        "_export_sc_text", "_legend_label", "_PatternPolygonItem",
        "_ClippedStrokeItem", "_ClippedFillItem", "_StyledFillItem",
    }

    def test_les_noms_vivent_dans_le_socle(self):
        manquants = self.DELEGUES - noms_du_module(SOCLE)
        self.assertFalse(manquants, manquants)

    def test_le_monolithe_les_reexporte(self):
        """`from .section_dock import SELECTION_HIGHLIGHT_COLOR` doit marcher."""
        source = DOCK.read_text(encoding="utf-8")
        for nom in self.DELEGUES:
            self.assertIn(nom, source, f"{nom} n'est plus ré-exporté")

    def test_aucun_nom_defini_deux_fois(self):
        """La même définition dans les deux fichiers = deux vérités."""
        communs = noms_du_module(SOCLE) & noms_du_module(DOCK)
        self.assertFalse(communs, communs)

    def test_le_journal_de_versions_a_quitte_le_code(self):
        """Un journal dans une docstring se lit à chaque modification."""
        doc = ast.get_docstring(ast.parse(DOCK.read_text(encoding="utf-8")))
        self.assertNotIn("v2.9.135", doc)
        self.assertLess(len(doc.splitlines()), 60)
        hist = RACINE / "docs" / "HISTORIQUE_section_dock.md"
        self.assertTrue(hist.exists())
        contenu = hist.read_text(encoding="utf-8")
        self.assertIn("v2.9.135", contenu)   # le plus récent
        self.assertIn("v2.7.10.32", contenu)  # le plus ancien conservé


class Mesure(unittest.TestCase):
    def test_l_outil_de_mesure_tourne_toujours(self):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "audit_rangement.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fichiers", r.stdout)


if __name__ == "__main__":
    unittest.main()
