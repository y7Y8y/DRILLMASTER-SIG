"""Chantier 4 — aucune fenêtre oubliée, aucun mot interdit.

C'est la comptabilité du chantier : 30 fenêtres dans le plugin, un message à
5 champs pour chacune. Si une fenêtre est ajoutée sans message, ce test le dit.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.lexique import MotInterdit, lexique      # noqa: E402
from drillmaster_v3.core.messages import Niveau                   # noqa: E402
from drillmaster_v3.core.messages_plugin import (convertis,       # noqa: E402
                                                 par_id, restants,
                                                 resume)
from drillmaster_v3.core.messages_plugin.catalogue import CATALOGUE  # noqa: E402


class Comptabilite(unittest.TestCase):
    def test_on_sait_combien_de_fenetres_restent(self):
        r = resume()
        self.assertEqual(r["fenetres_restantes"], len(restants()))
        self.assertGreater(r["fenetres_restantes"], 0,
                           "s'il en reste zéro, retirer ce chantier du plan")

    def test_chaque_fenetre_a_un_message(self):
        rest = {lieu for lieu, _ in restants()}
        conv = {"DrillMaster/ui/" + i for i in convertis()}
        self.assertEqual(rest - conv, set(),
                         "fenêtre(s) sans message à 5 champs")


class QualiteDesMessages(unittest.TestCase):
    def test_les_cinq_champs_sont_presents(self):
        for ident in convertis():
            m = par_id(ident)
            self.assertTrue(m.titre, ident)
            self.assertTrue(m.pourquoi, ident)
            self.assertTrue(m.concernes, ident)
            self.assertTrue(m.resoudre, ident)
            self.assertTrue(m.portee, ident)

    def test_un_blocage_propose_au_moins_deux_sorties(self):
        for ident in convertis():
            m = par_id(ident)
            if m.niveau == Niveau.BLOCAGE:
                self.assertGreaterEqual(len(m.resoudre), 2, ident)

    def test_aucun_mot_interdit(self):
        for ident in convertis():
            m = par_id(ident)
            for texte in (m.titre, m.pourquoi, m.portee, *m.resoudre,
                          *m.concernes):
                with self.subTest(ident=ident, texte=texte[:40]):
                    lexique.verifie(texte)

    def test_aucune_information_ne_dit_simplement_que_ca_a_reussi(self):
        """Une réussite ne mérite pas un message : elle se voit à l'écran."""
        for ident in convertis():
            m = par_id(ident)
            if m.niveau != Niveau.INFO:
                continue
            self.assertNotRegex(m.titre.lower(), r"^(succès|term.iné|r.ussi)",
                                f"{ident} : une réussite ne mérite pas un message")

    def test_un_titre_est_une_phrase_courte(self):
        for ident in convertis():
            self.assertLessEqual(len(par_id(ident).titre), 90, ident)

    def test_chaque_identifiant_correspond_a_un_appel_reel(self):
        """Aucun message inventé : chaque identifiant cite un appel existant."""
        lieux = {lieu for lieu, _ in restants()}
        for ident in convertis():
            self.assertIn("DrillMaster/ui/" + ident, lieux,
                          f"{ident} ne correspond à aucun appel du plugin")

    def test_aucune_fenetre_n_est_oubliee(self):
        lieux = {lieu for lieu, _ in restants()}
        conv = {"DrillMaster/ui/" + i for i in convertis()}
        self.assertEqual(lieux - conv, set(), "fenêtre sans message")


class PointDePassage(unittest.TestCase):
    def test_un_identifiant_inconnu_est_refuse(self):
        with self.assertRaises(KeyError):
            par_id("fichier_qui_n_existe_pas.py:1")

    def test_le_catalogue_est_construit_sans_erreur(self):
        self.assertEqual(len(CATALOGUE), len(convertis()))


if __name__ == "__main__":
    unittest.main()
