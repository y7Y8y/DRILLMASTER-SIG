"""R-24 → R-27 : la complexité progressive, mesurée."""
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.tracks import TrackCatalog                  # noqa: E402
from drillmaster_v3.core.visibilite import TropDeReglages, Visibilite  # noqa: E402


class ComplexiteProgressive(unittest.TestCase):
    def setUp(self):
        self.cat = TrackCatalog()
        self.vis = Visibilite(self.cat)

    def test_R24_six_reglages_visibles_au_maximum(self):
        for pid in self.cat.ids():
            vus = self.vis.essentiels(pid)
            self.assertLessEqual(len(vus), 6, f"{pid} montre {len(vus)} réglages")
            self.vis.verifie_affichage(pid, vus)

    def test_R24_refus_au_dela_de_six(self):
        with self.assertRaises(TropDeReglages):
            self.vis.verifie_affichage("assays", list(range(7)))

    def test_R25_le_mode_guide_montre_moins_que_l_expert(self):
        for pid in self.cat.ids():
            self.assertLessEqual(len(self.vis.essentiels(pid, "guidee")),
                                 len(self.vis.essentiels(pid, "experte")))

    def test_R25_changer_de_mode_ne_change_aucune_valeur(self):
        self.assertTrue(self.vis.modes_ne_changent_rien())

    def test_R26_aucune_fonction_reservee_a_l_expert(self):
        """Tout réglage avancé reste atteignable : il est listé, pas supprimé."""
        for pid in self.cat.ids():
            guidee = set(self.vis.essentiels(pid))
            expert = set(self.vis.essentiels(pid, "experte"))
            self.assertTrue(guidee <= expert)
            self.assertEqual(guidee | set(self.vis.avances(pid)), expert)

    def test_R27_chaque_valeur_automatique_dit_d_ou_elle_vient(self):
        style = self.cat.resout("assays")
        self.assertIn("n_classes", style.specific)
        self.assertIn("method", style.specific)   # « quantiles » est explicite
        self.assertIn("scale_scope", style.specific)


class OrdreImpose(unittest.TestCase):
    def test_tickets_dans_l_ordre(self):
        texte = (RACINE / "specs/TICKETS.md").read_text(encoding="utf-8")
        numeros = [f"T-0{i}" for i in range(10)]
        positions = [texte.find(f"## {n}") for n in numeros]
        self.assertTrue(all(p >= 0 for p in positions), "un ticket manque")
        self.assertEqual(positions, sorted(positions), "ordre des tickets cassé")


if __name__ == "__main__":
    unittest.main()
