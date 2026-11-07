"""Chantier 2 — un réglage, un propriétaire.

Ce que ces tests prouvent : régler une fois suffit, et aucune vue ne peut
garder une valeur différente de celle des autres.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.reglages import (LECTEURS, RefusReglage,  # noqa: E402
                                          Reglages)


class UnSeulProprietaire(unittest.TestCase):
    def setUp(self):
        self.r = Reglages()

    def test_regler_une_fois_change_les_cinq_vues(self):
        self.r.modifie("assays", "width", 24, par="A. Koné")
        lu = self.r.lecture("assays", "width")
        vues = {k: v["valeur"] for k, v in lu["vues"].items()
                if v["raison"] is None}
        self.assertEqual(set(vues.values()), {24})
        self.assertEqual(len(vues), 5)

    def test_une_vue_sans_objet_le_dit_et_ne_ment_pas(self):
        lu = self.r.lecture("assays", "side")
        self.assertEqual(lu["vues"]["2d"]["valeur"], lu["valeur"])
        self.assertIsNone(lu["vues"]["3d"]["valeur"])
        self.assertIn("tourne", lu["vues"]["3d"]["raison"])

    def test_coherence_apres_chaque_changement(self):
        for champ, val in (("width", 30), ("opacity", 55), ("side", "left")):
            self.r.modifie("lithology", champ, val, par="M. Traoré")
            self.assertTrue(self.r.coherent("lithology", champ))

    def test_sans_nom_pas_de_changement(self):
        with self.assertRaises(RefusReglage) as ctx:
            self.r.modifie("assays", "width", 20, par="  ")
        self.assertIn("qui l'a modifié", str(ctx.exception))
        self.assertEqual(self.r.surcharges(), {})

    def test_hors_bornes_refuse_avec_les_bornes_du_contrat(self):
        regle = self.r.catalogue.contrat["width"]
        with self.assertRaises(RefusReglage) as ctx:
            self.r.modifie("assays", "width", 900, par="A. Koné")
        self.assertIn(f"{regle['min']} à {regle['max']}", str(ctx.exception))

    def test_les_bornes_viennent_du_contrat_pas_du_code(self):
        """Si le contrat change, le refus change : rien n'est écrit en dur."""
        import inspect
        from drillmaster_v3.core import reglages as module
        source = inspect.getsource(module.Reglages._verifie)
        self.assertNotIn("64", source)
        self.assertNotIn("gauche", source)

    def test_valeur_enumeree_inconnue_refusee(self):
        with self.assertRaises(RefusReglage) as ctx:
            self.r.modifie("assays", "side", "milieu", par="A. Koné")
        self.assertIn("« left »", str(ctx.exception))

    def test_piste_inconnue_refusee(self):
        with self.assertRaises(RefusReglage) as ctx:
            self.r.modifie("couleurs_pistes", "width", 20, par="A. Koné")
        self.assertIn("12 pistes", str(ctx.exception))

    def test_champ_inconnu_refuse(self):
        with self.assertRaises(RefusReglage) as ctx:
            self.r.modifie("assays", "couleur_petit", 3, par="A. Koné")
        self.assertIn("n'est pas un champ", str(ctx.exception))

    def test_meme_valeur_n_ecrit_pas_au_journal(self):
        self.r.modifie("assays", "width", 24, par="A. Koné")
        n = len(self.r.journal())
        self.assertIsNone(self.r.modifie("assays", "width", 24, par="A. Koné"))
        self.assertEqual(len(self.r.journal()), n)

    def test_journal_dit_qui_quoi_pourquoi(self):
        self.r.modifie("assays", "width", 24, par="A. Koné",
                       motif="lecture au bureau")
        c = self.r.journal("assays")[-1]
        self.assertEqual((c.piste, c.champ, c.apres), ("assays", "width", 24))
        self.assertIn("A. Koné", c.phrase())
        self.assertEqual(c.motif, "lecture au bureau")

    def test_retablit_revient_a_la_famille(self):
        avant = self.r.valeur("assays", "width")
        self.r.modifie("assays", "width", 40, par="A. Koné")
        self.r.retablit("assays", "width")
        self.assertEqual(self.r.valeur("assays", "width"), avant)
        self.assertTrue(self.r.herite("assays", "width"))

    def test_une_vue_inconnue_ne_s_abonne_pas(self):
        with self.assertRaises(RefusReglage):
            self.r.abonne("vue_maison")

    def test_les_cinq_vues_sont_connues(self):
        self.assertEqual(len(LECTEURS), 5)
        for vue in LECTEURS:
            self.r.abonne(vue)


if __name__ == "__main__":
    unittest.main()
