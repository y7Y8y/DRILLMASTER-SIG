"""Chantier 7 — les écrans neufs, éprouvés sur des cas réels.

Ce que ces tests protègent : aucune promesse de maquette n'est cochée
« tenue » sans un cas réel derrière elle. Et là où le code ne sait pas
encore, le test **exige que ce soit dit** — jamais un silence.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.donnees.lecture import lit_collets, verifie   # noqa: E402
from drillmaster_v3.core.ecrans import ECRANS, ecarts, fiche_source    # noqa: E402
from drillmaster_v3.projet import Projet                               # noqa: E402

COL = "ID;X;Y;Z;PROF;DATE\n"


def texte(*lignes):
    return COL + "\n".join(lignes) + "\n"


class Cas18_Import(unittest.TestCase):
    """Écran 18 — quatre fichiers réels, quatre lectures différentes."""

    def test_fichier_propre(self):
        f = fiche_source("propre.csv", texte=texte(
            "A;512000.5;731800.2;219.8;110;2024-03-11",
            "B;512024.1;731809.3;219.6;118;2024-03-12"))
        self.assertEqual(f.forages, 2)
        self.assertEqual(f.colonnes, 6)
        self.assertEqual(f.colonnes_reconnues, 6)
        self.assertFalse(f.bloquant)
        self.assertEqual(f.doublons, ())

    def test_fichier_avec_virgule_decimale(self):
        f = fiche_source("fr.csv", texte="ID;X;Y;Z;PROF\nA;512 000,5;731 800,2"
                         ";219,8;110\n")
        self.assertEqual(f.forages, 1)

    def test_fichier_avec_separateur_virgule(self):
        f = fiche_source("virgules.csv", texte="ID,X,Y,Z\nA,1,2,3\nB,4,5,6\n")
        self.assertEqual(f.forages, 2)

    def test_fichier_avec_accents_non_utf8(self):
        # « été » en européen occidental : deux octets que l'UTF-8 refuse
        brut = "ID;X;Y;Z\nForage été;1;2;3\n".encode("cp1252")
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "accents.csv"
            chemin.write_bytes(brut)
            lec = lit_collets(chemin)
        self.assertEqual(len(lec.colliers), 1)
        self.assertTrue(any("UTF-8" in m.titre for m in lec.messages))

    def test_colonnes_montrees_avec_exemple_et_role(self):
        lec = lit_collets("c.csv", texte=texte("A;1;2;3;10;2024-03-11"))
        self.assertEqual(len(lec.colonnes), 6)
        self.assertTrue(all(c.exemple for c in lec.colonnes))
        roles = {c.role for c in lec.colonnes if c.reconnue}
        self.assertIn("identifiant du forage", roles)
        self.assertIn("date de fin", roles)

    def test_un_type_absent_est_dit_absent(self):
        f = fiche_source("a.csv", texte=texte("A;1;2;3;10;2024-03-11"))
        self.assertEqual(list(f.types_absents), ["recovery", "density"])


class Cas19_Blocage(unittest.TestCase):
    """Écran 19 — les cinq contrôles, sur un fichier qui a deux défauts."""

    def setUp(self):
        self.lec = lit_collets("d.csv", texte=texte(
            "ISBRC001;512000;731800;219;110;2024-03-11",
            "ISBRC002;512024;731809;219;118;2024-03-12",
            "ISBRC002;512026;731811;219;118;2024-03-12"))

    def test_le_doublon_bloque(self):
        self.assertTrue(self.lec.bloquant)
        m = [x for x in self.lec.messages if "deux fois" in x.titre][0]
        self.assertIn("ISBRC002", m.concernes)
        self.assertGreaterEqual(len(m.resoudre), 2)

    def test_cinq_controles_sont_calcules(self):
        c = {x.cle: x for x in self.lec.verifications.controles}
        self.assertEqual(set(c), {"identifiants", "coordonnees", "profondeurs",
                                  "analyses", "dates"})
        self.assertEqual(c["identifiants"].reussi, 2)   # 2 identifiants pour 3 lignes
        self.assertEqual(c["identifiants"].etat, "avertissement")
        self.assertEqual(c["coordonnees"].etat, "ok")

    def test_une_colonne_de_date_non_reconnue_ne_fait_pas_semblant(self):
        lec = lit_collets("sans_date.csv", texte="ID;X;Y;Z\nA;1;2;3\n")
        c = {x.cle: x for x in lec.verifications.controles}
        self.assertEqual(c["dates"].total, 0)          # rien à vérifier
        self.assertEqual(c["dates"].etat, "info")      # donc on le dit

    def test_decider_n_a_qu_un_seul_objet(self):
        self.assertEqual(self.lec.verifications.avant_de_demander(),
                         ("Identifiants uniques",))

    def test_coordonnees_impossibles_sont_comptees(self):
        lec = lit_collets("fou.csv", texte=texte(
            "A;999999999;1;2;10;2024-03-11",
            "B;1;2;3;10;2024-03-11"))
        c = {x.cle: x for x in lec.verifications.controles}
        self.assertEqual(c["coordonnees"].reussi, 1)


class Cas20_Coupe(unittest.TestCase):
    def test_une_piste_n_a_qu_un_proprietaire(self):
        p = Projet()
        p.reglages.modifie("assays", "width", 24, par="test")
        lu = p.reglages.lecture("assays", "width")
        self.assertEqual(lu["valeur"], 24)
        # les 5 vues lisent la MÊME valeur : elles ne peuvent pas diverger
        self.assertEqual({v["valeur"] for v in lu["vues"].values()}, {24})


class Cas21_Exclusions(unittest.TestCase):
    def setUp(self):
        self.p = Projet()
        self.p.importe("a.csv", texte=texte(
            "A;1;2;3;10;2024-03-11", "B;3;4;5;11;2024-03-12"))

    def test_le_forage_ecarte_reste_disponible_au_dessin(self):
        self.p.exclut("B", "doublon de saisie", par="A. Koné")
        ecartes = self.p.forages_ecartes()
        self.assertEqual([f.id for f, _ in ecartes], ["B"])
        self.assertEqual(ecartes[0][1], "doublon de saisie")
        self.assertEqual([f.id for f in self.p.forages_actifs()], ["A"])

    def test_le_journal_garde_qui_quand_pourquoi(self):
        self.p.exclut("B", "doublon", par="A. Koné")
        self.p.reintegre("B", par="M. Traoré")
        j = self.p.journal_des_decisions()
        self.assertEqual([d["action"] for d in j], ["écarté", "réintégré"])
        self.assertEqual(j[0]["par"], "A. Koné")
        self.assertEqual(j[1]["par"], "M. Traoré")
        self.assertTrue(all(d["quand"] and d["motif"] for d in j))

    def test_reintegrer_conserve_le_motif_d_origine(self):
        self.p.exclut("B", "hors emprise", par="A. Koné")
        self.p.reintegre("B", par="A. Koné")
        self.assertEqual(self.p.journal_des_decisions()[-1]["motif"],
                         "hors emprise")


class Promesses(unittest.TestCase):
    """Aucune promesse ne se prétend tenue sans preuve nommée."""

    def test_chaque_promesse_nomme_sa_preuve(self):
        for e in ECRANS:
            for p in e.promesses:
                self.assertTrue(p.preuve, f"{e.numero} : « {p.phrase} » sans preuve")
                self.assertIn(p.etat, ("tenu", "bloque", "sans_code"))

    def test_ce_qui_reste_est_numerote_et_nomme(self):
        reste = ecarts()
        self.assertTrue(reste)
        for numero, nom, etat, phrase, preuve in reste:
            self.assertEqual(etat, "sans_code")
            self.assertTrue(preuve, f"{numero} {nom} : reste sans raison")

    def test_aucune_promesse_ne_reste_sans_ecran(self):
        numeros = [e.numero for e in ECRANS]
        self.assertEqual(numeros, [18, 19, 20, 21])


if __name__ == "__main__":
    unittest.main()
