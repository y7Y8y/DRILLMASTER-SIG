"""Chantier 9 — l'architecture tient sur trois promesses vérifiables.

R-40 le noyau ne connaît pas l'interface · R-41 une vue ne calcule pas ·
R-59 ce qui n'est branché par personne est nommé, jamais oublié.

Ces tests lisent le **plugin réel**, pas le registre : une règle qui ne
s'applique qu'aux fichiers qu'on veut bien lui donner ne vaut rien.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.vocabulaire_interdit import (      # noqa: E402
    SIGNAUX_DE_CALCUL, calculs, import_interdit)

PLUGIN = RACINE / "DrillMaster"
# plafond : le nombre de calculs écrits dans les vues. Il ne remonte pas.
PLAFOND_CALCULS_VUES = 77
# plafond : modules du plugin que rien n'importe. Il ne remonte pas.
PLAFOND_ORPHELINS = 5


def modules_du_plugin():
    for f in sorted(PLUGIN.rglob("*.py")):
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        if rel.startswith("tools/") or "__pycache__" in rel:
            continue
        yield "DrillMaster." + rel[:-3].replace("/", "."), f


def imports_de(chemin: Path):
    """Les cibles d'import, résolues comme le fait Python."""
    arbre = ast.parse(chemin.read_text(encoding="utf-8", errors="ignore"))
    rel = str(chemin.relative_to(PLUGIN)).replace("\\", "/")
    paquet = ("DrillMaster." + rel[:-3].replace("/", ".")).rsplit(".", 1)[0]
    out = []
    for n in ast.walk(arbre):
        if isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if n.level:
                base = paquet.split(".")
                if n.level > 1:
                    base = base[: len(base) - (n.level - 1)]
                cible = ".".join(base + ([mod] if mod else []))
            else:
                cible = mod
            for a in n.names:
                out.append(cible + "." + a.name)
            out.append(cible)
        elif isinstance(n, ast.Import):
            out.extend(a.name for a in n.names)
    return out


class LeNoyauIgnoreLInterface(unittest.TestCase):
    def test_aucun_module_du_noyau_n_importe_un_widget(self):
        coupables = []
        for nom, f in modules_du_plugin():
            if not nom.startswith("DrillMaster.core"):
                continue
            for cible in imports_de(f):
                raison = import_interdit(nom, cible)
                if raison:
                    coupables.append(raison)
        self.assertEqual(coupables, [])

    def test_la_regle_est_dans_le_code_pas_dans_un_document(self):
        self.assertEqual(
            import_interdit("DrillMaster.core.x", "qgis.PyQt.QtWidgets") is None,
            False)

    def test_qt_pour_peindre_reste_permis_et_mesure(self):
        """Interdire Qt au noyau serait faux : les couleurs et les polices."""
        self.assertIsNone(import_interdit("DrillMaster.core.styles",
                                          "qgis.PyQt.QtGui"))


class LesVuesNeCalculentPas(unittest.TestCase):
    def test_le_plafond_de_calculs_ne_remonte_pas(self):
        total, par_fichier = 0, {}
        for nom, f in modules_du_plugin():
            if ".ui." not in nom:
                continue
            n = calculs(f.read_text(encoding="utf-8", errors="ignore"))
            if n:
                par_fichier[nom] = n
                total += n
        self.assertLessEqual(total, PLAFOND_CALCULS_VUES,
                             f"{total} calculs dans les vues : "
                             f"{sorted(par_fichier.items(), key=lambda kv: -kv[1])[:3]}")

    def test_les_signaux_sont_connus(self):
        """Un calcul ajouté hors de cette liste échappe au compte."""
        self.assertIn("math.atan2", SIGNAUX_DE_CALCUL)
        self.assertIn("math.hypot", SIGNAUX_DE_CALCUL)

    def test_le_noyau_sait_deja_faire_les_trajectoires(self):
        """Ce qui doit sortir des vues existe déjà côté noyau."""
        from drillmaster_v3.core.geometrie.trajectoire import calcule
        pts = calcule(0, 0, 100, [(0, 0, -90), (100, 0, -90)])
        self.assertEqual(len(pts), 2)
        self.assertAlmostEqual(pts[1].z, 0.0, places=6)


class NommesJamaisOublies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "audit_architecture.py"),
                            "--ecrit"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        cls.audit = json.loads(
            (RACINE / "specs" / "data" / "architecture.json")
            .read_text(encoding="utf-8"))

    def test_aucune_fuite_du_noyau(self):
        self.assertEqual(self.audit["fuites_noyau"], [])

    def test_les_orphelins_ne_sont_pas_plus_nombreux(self):
        orphelins = self.audit["modules_jamais_importes"]
        self.assertLessEqual(len(orphelins), PLAFOND_ORPHELINS, orphelins)
        # chacun est nommé : ce ne sont que des outils ou des points d'entrée
        self.assertTrue(set(orphelins) <= {
            "core.benchmark", "core.scene3d.synthetic", "core.ui_audit",
            "ui.palette_jetons", "ui.view_3d"},
            orphelins)


if __name__ == "__main__":
    unittest.main()
