"""Les règles R-02 → R-10, vérifiées par exécution, pas par promesse."""
import json
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.tracks import CHAMPS, TrackCatalog  # noqa: E402

SPEC = json.loads((RACINE / "specs/data/tracks.json").read_text(encoding="utf-8"))


class ContratDePiste(unittest.TestCase):
    def setUp(self):
        self.cat = TrackCatalog()

    def test_R02_douze_pistes_et_quatorze_champs(self):
        self.assertEqual(len(self.cat.ids()), 12)
        self.assertEqual(len(CHAMPS), 15)

    def test_R04_familles_fermees(self):
        familles = {p["family"] for p in SPEC["pistes"]}
        self.assertEqual(familles,
                         {"structurelle", "categorielle", "quantitative",
                          "media"})

    def test_R05_chaque_piste_resout_les_14_champs(self):
        for pid in self.cat.ids():
            style = self.cat.resout(pid).to_dict()
            for champ in CHAMPS:
                self.assertIn(champ, style, f"{pid}.{champ} manquant")

    def test_R06_specific_disjoint_du_contrat(self):
        for p in SPEC["pistes"]:
            self.assertFalse(set(p.get("specific", {})) & set(CHAMPS),
                             f"{p['id']} redéclare un champ commun")

    def test_R07_heritage_est_explicite(self):
        style = self.cat.resout("alterations")
        self.assertIn("opacity", style.herite)      # vient de la famille
        self.assertNotIn("width", style.herite)     # forcée par la piste
        style = self.cat.resout("lithology")
        self.assertNotIn("width", style.herite)     # forcée par la piste

    def test_R08_non_usage_motive(self):
        r = self.cat.lit("lithology", "3d", "side")
        self.assertFalse(r["applique"])
        self.assertTrue(r["raison"])

    def test_R09_les_cinq_lecteurs_lisent_la_meme_valeur(self):
        for pid in self.cat.ids():
            for champ in ("width", "opacity", "export", "fill"):
                self.assertTrue(self.cat.coherents(pid, champ),
                                f"{pid}.{champ} diverge entre lecteurs")

    def test_R09_un_seul_proprietaire_par_piste(self):
        for p in SPEC["pistes"]:
            self.assertTrue(p.get("owner"), f"{p['id']} sans propriétaire")

    def test_R10_largeur_2d_3d_meme_proprietaire(self):
        v2d = self.cat.lit("assays", "2d", "width")["valeur"]
        v3d = self.cat.lit("assays", "3d", "width")["valeur"]
        self.assertEqual(v2d, v3d)

    def test_ajouter_une_piste_ne_touche_aucun_python(self):
        """R-03 : la spécification est la seule source."""
        avant = {p.name: p.stat().st_mtime_ns
                 for p in (RACINE / "drillmaster_v3").rglob("*.py")}
        cat = TrackCatalog()
        copie = dict(cat._pistes)
        copie["essai"] = {"id": "essai", "label": "Essai",
                          "family": "media", "order": 999,
                          "owner": "coupe2d.pistes", "specific": {}}
        self.assertEqual(len(copie), 13)   # ajout possible sans code
        apres = {p.name: p.stat().st_mtime_ns
                 for p in (RACINE / "drillmaster_v3").rglob("*.py")}
        self.assertEqual(avant, apres)


if __name__ == "__main__":
    unittest.main()
