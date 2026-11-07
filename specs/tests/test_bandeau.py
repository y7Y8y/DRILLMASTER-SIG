"""Chantier 4 — le bandeau remplace les fenêtres."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.bandeau import Bandeau                     # noqa: E402
from drillmaster_v3.core.messages import (Niveau, avertissement,    # noqa: E402
                                          blocage, information, question)


class BandeauTest(unittest.TestCase):
    def setUp(self):
        self.b = Bandeau()

    def _blocage(self):
        return blocage("Deux forages portent le même nom",
                       "la coupe afficherait un forage fusionné",
                       ("ISBRC045, ligne 46",),
                       ("corriger l'identifiant", "exclure un des deux"),
                       "colliers")

    def test_un_seul_message_ne_bloque_rien(self):
        self.b.ajoute(information("65 forages lus", "lecture terminée en "
                                  "utf-8", "colliers"))
        self.assertFalse(self.b.doit_arreter())
        self.assertFalse(self.b.doit_demander())

    def test_un_blocage_arrete_l_etape_suivante(self):
        self.b.ajoute(self._blocage())
        self.assertTrue(self.b.doit_arreter())
        self.assertTrue(self.b.visible()[0]["arrete"])

    def test_une_question_met_en_attente_sans_arreter(self):
        self.b.ajoute(question("Quel forage garder ?", "les deux lignes "
                               "diffèrent de 2 m", "ISBRC045",
                               ("garder la ligne 46", "garder la ligne 47"),
                               "colliers"))
        self.assertTrue(self.b.doit_demander())
        self.assertFalse(self.b.doit_arreter())

    def test_l_ordre_met_le_blocage_devant(self):
        self.b.ajoute(information("65 forages lus", "fin de lecture",
                                  "colliers"))
        self.b.ajoute(avertissement("3 colonnes ignorées", "les colonnes DATE, "
                                    "OP, TYPE ne sont pas utilisées",
                                    ("DATE", "OP", "TYPE"),
                                    ("renommer les colonnes",), "colliers"))
        self.b.ajoute(self._blocage())
        self.assertEqual(self.b.tries()[0].niveau, Niveau.BLOCAGE)

    def test_le_meme_sujet_ne_s_empile_pas(self):
        self.b.ajoute(self._blocage())
        self.b.remplace(self._blocage())
        self.assertEqual(len(self.b.messages), 1)

    def test_deux_sujets_differents_cohabitent(self):
        self.b.ajoute(self._blocage())
        self.b.ajoute(information("65 forages lus", "fin de lecture",
                                  "analyses"))
        self.assertEqual(len(self.b.messages), 2)

    def test_un_titre_trop_long_est_refuse(self):
        from drillmaster_v3.core.messages import MessageIncomplet
        with self.assertRaises(MessageIncomplet) as ctx:
            self.b.ajoute(information("x" * 120, "peu importe", "colliers"))
        self.assertIn("un titre annonce un fait", str(ctx.exception))

    def test_on_n_ecrit_pas_dans_le_bandeau_autre_chose_qu_un_message(self):
        from drillmaster_v3.core.messages import MessageIncomplet
        with self.assertRaises(MessageIncomplet):
            self.b.ajoute("erreur : colonne absente")

    def test_deux_voix_meme_contenu(self):
        self.b.ajoute(self._blocage())
        guidee, experte = self.b.visible("guidee"), self.b.visible("experte")
        self.assertEqual(len(guidee), len(experte))
        self.assertEqual(guidee[0]["titre"], experte[0]["titre"])
        self.assertNotIn("concerne", guidee[0])
        self.assertIn("concerne", experte[0])

    def test_la_couleur_vient_du_theme(self):
        self.b.ajoute(self._blocage())
        self.assertIn("couleur", self.b.visible()[0])

    def test_resume_tient_en_une_ligne(self):
        self.b.ajoute(self._blocage())
        self.b.ajoute(information("65 forages lus", "fin de lecture",
                                  "analyses"))
        self.assertIn("2 messages", self.b.resume())

    def test_sortie_pour_le_support_contient_les_cinq_champs(self):
        self.b.ajoute(self._blocage())
        texte = self.b.pour_le_support(version="3.0.0", chemin="ISSIA_COLLAR.csv")
        for attendu in ("pourquoi", "concerné", "sorties", "3.0.0",
                        "ISSIA_COLLAR.csv"):
            self.assertIn(attendu, texte)


if __name__ == "__main__":
    unittest.main()
