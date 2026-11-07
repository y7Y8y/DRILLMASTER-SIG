"""Les règles R-16 → R-22 : vocabulaire, états, messages."""
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.lexique import MotInterdit, lexique       # noqa: E402
from drillmaster_v3.core.messages import (Message, MessageIncomplet,  # noqa: E402
                                         Niveau, avertissement, blocage,
                                         question)


class Vocabulaire(unittest.TestCase):
    def test_R16_cinq_niveaux_meme_vocabulaire_deux_voix(self):
        m = avertissement("3 forages sans déviation",
                          "la trajectoire est supposée verticale",
                          ["ISBRC003"], ["ajouter les déviations"],
                          "ISSIA_SURVEY.csv")
        guidee, experte = m.rendu("guidee"), m.rendu("experte")
        self.assertEqual(guidee["niveau"], experte["niveau"])
        self.assertGreaterEqual(len(experte), len(guidee))

    def test_R17_mot_interdit_refuse(self):
        with self.assertRaises(MotInterdit):
            lexique.verifie("Conserver le cache JSON")

    def test_R17_mot_ordinaire_accepte(self):
        self.assertEqual(lexique.verifie("Dernier calcul"), "Dernier calcul")

    def test_R18_trois_phrases_dans_l_ordre(self):
        m = question("Cellule à deux codes",
                     "la coupe ne peut pas trancher", "LAT;SAP",
                     ["garder LAT", "garder SAP"], "litho.csv ligne 412")
        bloc = m.rendu()
        self.assertEqual(list(bloc),
                         ["niveau", "titre", "ce_qui_se_passe",
                          "ce_que_vous_pouvez_faire", "ce_qui_continue"])

    def test_R19_couleurs_d_etat_reservees(self):
        couleurs = {lexique.niveau(n.value, "couleur") for n in Niveau}
        self.assertEqual(len(couleurs), 5)
        self.assertNotIn("#2E5BFF", couleurs)   # l'accent n'exprime pas un état


class ContratDeMessage(unittest.TestCase):
    def test_R20_message_sans_pourquoi_refuse(self):
        with self.assertRaises(MessageIncomplet):
            Message(Niveau.BLOCAGE, "titre", "", ("a",), ("b", "c"), "f")

    def test_R20_message_sans_resoudre_refuse(self):
        with self.assertRaises(MessageIncomplet):
            Message(Niveau.BLOCAGE, "titre", "pourquoi", ("a",), (), "f")

    def test_R20_message_sans_portee_refuse(self):
        with self.assertRaises(MessageIncomplet):
            Message(Niveau.BLOCAGE, "titre", "pourquoi", ("a",), ("b",), "")

    def test_R22_blocage_trois_sorties(self):
        m = blocage("2 forages portent le même nom",
                    "la trajectoire serait ambiguë",
                    ["ISBRC045", "ISBRC088"],
                    ["corriger à la source", "fusionner", "exclure"],
                    "ISSIA_COLLAR.csv ligne 45")
        self.assertEqual(len(m.resoudre), 3)

    def test_R22_blocage_une_seule_sortie_refuse(self):
        with self.assertRaises(MessageIncomplet):
            blocage("x", "y", ["a"], ["corriger"], "f")

    def test_suite_par_niveau(self):
        self.assertEqual(blocage("x", "y", ["a"], ["b", "c"], "f").suite,
                         "arrête l'étape suivante")


if __name__ == "__main__":
    unittest.main()
