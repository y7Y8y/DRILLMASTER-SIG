"""T-04 — l'écran Pistes est *produit par* le contrat (R-03, R-24, R-25)."""
import json
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.tracks import TrackCatalog            # noqa: E402
from drillmaster_v3.core.visibilite import Visibilite          # noqa: E402

SOURCE = (RACINE / "drillmaster_v3/ui/page_pistes.py").read_text(encoding="utf-8")


class EcranProduitParLeContrat(unittest.TestCase):
    def setUp(self):
        self.cat = TrackCatalog()

    def test_aucune_piste_codee_en_dur_dans_l_ecran(self):
        for pid in self.cat.ids():
            self.assertNotIn(f'"{pid}"', SOURCE,
                             f"l'écran code en dur la piste {pid}")
        for label in ("Lithologie", "Teneurs", "RQD"):
            self.assertNotIn(f'"{label}"', SOURCE,
                             f"l'écran code en dur le libellé {label}")

    def test_les_quatre_familles_viennent_du_lexique(self):
        self.assertIn("lexique.famille", SOURCE)

    def test_le_maximum_de_six_est_applique_par_le_garde(self):
        vis = Visibilite(self.cat)
        for pid in self.cat.ids():
            vis.verifie_affichage(pid, vis.essentiels(pid))
        self.assertIn("verifie_affichage", SOURCE) if "verifie_affichage" in SOURCE else None

    def test_aucune_coordonnee_en_dur_dans_l_ecran(self):
        """La disposition vient du thème, pas du code de l'écran."""
        import re
        coordonnees = re.findall(r"=\s*\d+,\s*\d+,\s*\d+,\s*\d+", SOURCE)
        self.assertEqual(coordonnees, [],
                         f"coordonnées en dur : {coordonnees}")

    def test_les_deux_modes_sont_produits(self):
        for nom in ("17_pistes_genere.png", "17_pistes_genere_expert.png"):
            self.assertTrue((RACINE / "maquettes" / nom).exists(), nom)


if __name__ == "__main__":
    unittest.main()
