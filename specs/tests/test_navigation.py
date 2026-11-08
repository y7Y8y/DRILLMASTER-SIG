"""Chantier 8 — la navigation : une action, un chemin, aucune trappe.

R-56 un seul chemin · R-57 pas d'écran sans porte · R-58 pas de raccourci
muet. Les trois sont tenus ici, sur le registre ET sur le plugin mesuré.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.navigation import (Chemin, Navigation, ZONES,   # noqa: E402
                                            navigation_du_plugin)


class UnSeulChemin(unittest.TestCase):
    def test_deux_entrees_pour_la_meme_action_sont_refusees(self):
        n = Navigation()
        e = n.ecran("Essai")
        e.ajoute("panneau", "bouton", "faire quelque chose")
        with self.assertRaises(ValueError) as ctx:
            e.ajoute("panneau", "bouton", "faire quelque chose")
        self.assertIn("R-56", str(ctx.exception))

    def test_la_meme_action_dans_deux_zones_est_permise(self):
        """Voir la largeur au panneau ET au menu contextuel : deux usages."""
        n = Navigation()
        e = n.ecran("Essai")
        e.ajoute("panneau", "curseur", "régler la largeur")
        e.ajoute("menu contextuel", "bouton", "régler la largeur")
        self.assertEqual(len(e.chemins), 2)

    def test_une_zone_inconnue_est_refusee(self):
        with self.assertRaises(ValueError):
            Chemin("X", "barre du milieu", "bouton", "essai")

    def test_un_geste_inconnu_est_refuse(self):
        with self.assertRaises(ValueError):
            Chemin("X", "panneau", "clic du milieu", "essai")


class PasDeTrappe(unittest.TestCase):
    def test_un_raccourci_sans_touche_affichee_est_refuse(self):
        """R-58 : un pouvoir invisible n'est pas un raccourci."""
        with self.assertRaises(ValueError) as ctx:
            Chemin("X", "panneau", "bouton", "essai", "Ctrl+K")
        self.assertIn("R-58", str(ctx.exception))

    def test_le_registre_du_plugin_n_a_aucun_doublon(self):
        n = navigation_du_plugin()
        self.assertEqual(n.doublons(), [])

    def test_le_registre_du_plugin_n_a_aucune_trappe(self):
        self.assertEqual(navigation_du_plugin().sans_raccourci_isole(), [])

    def test_les_quatre_ecrans_ont_chacun_au_moins_deux_chemins(self):
        n = navigation_du_plugin()
        self.assertEqual(len(n.ecrans), 4)
        for e in n.ecrans.values():
            self.assertGreaterEqual(len(e.chemins), 2, e.nom)

    def test_chaque_zone_est_utilisee_ou_nommee_vide(self):
        n = navigation_du_plugin()
        utilisees = {c.zone for e in n.ecrans.values() for c in e.chemins}
        self.assertTrue(utilisees <= set(ZONES))
        self.assertEqual(n.resume()["zones_vides"], ["menu contextuel"])


class MesureDuPlugin(unittest.TestCase):
    """Ce que l'outil trouve dans le vrai code — et qui doit rester vrai."""

    @classmethod
    def setUpClass(cls):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "audit_navigation.py"),
                            "--ecrit"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        cls.audit = json.loads(
            (RACINE / "specs" / "data" / "navigation.json")
            .read_text(encoding="utf-8"))

    def test_chaque_raccourci_du_plugin_est_compte(self):
        self.assertGreaterEqual(len(self.audit["raccourcis"]), 6)
        for r in self.audit["raccourcis"]:
            self.assertIn("affiche", r)
            self.assertTrue(r["touche"], r)

    def test_les_raccourcis_muets_sont_nommes_pas_oublies(self):
        muets = [r for r in self.audit["raccourcis"] if not r["affiche"]]
        self.assertEqual(len(muets), self.audit["raccourcis_muets"])
        # tant qu'ils existent, ils sont dans la liste à corriger (R-58)
        self.assertLessEqual(len(muets), 4)

    def test_aucun_reglage_fantome(self):
        """Une valeur lue et jamais écrite n'existe pas pour l'utilisateur."""
        self.assertEqual(self.audit["fantomes"], [])

    def test_les_reglages_morts_sont_nommes(self):
        self.assertTrue(set(self.audit["morts"]) <= {
            "DrillMaster/view3d/bg", "DrillMaster/view3d/detail",
            "DrillMaster/view3d_enabled"})


if __name__ == "__main__":
    unittest.main()
