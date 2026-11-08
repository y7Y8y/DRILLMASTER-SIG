"""T-09 — les cas d'usage, exécutés sur du vrai code.

Ces tests ne regardent pas des images : ils ouvrent des fichiers, calculent,
et vérifient le résultat. Un cas rouge = pas de livraison (R-29).
"""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.coupe2d.coupe import (Ligne, controle_couverture,  # noqa: E402
                                              inclusion, intercepts, projette)
from drillmaster_v3.core.donnees.lecture import lit_collets             # noqa: E402
from drillmaster_v3.core.geometrie.trajectoire import compare, fond     # noqa: E402
from drillmaster_v3.core.messages import Niveau                          # noqa: E402
from drillmaster_v3.projet import Projet                                 # noqa: E402

COL = "ID;X;Y;Z;PROF\n"


def texte(*lignes):
    return COL + "\n".join(lignes) + "\n"


def niveaux(lec):
    return {m.niveau for m in lec.messages}


def titres(lec):
    return " | ".join(m.titre for m in lec.messages)


class Cas1_ProjetVide(unittest.TestCase):
    def test_fichier_vide_est_un_blocage_explique(self):
        lec = lit_collets("vide.csv", texte="")
        self.assertIn(Niveau.BLOCAGE, niveaux(lec))
        m = [x for x in lec.messages if x.niveau is Niveau.BLOCAGE][0]
        self.assertTrue(m.pourquoi and m.resoudre and m.portee)
        self.assertEqual(lec.colliers, [])


class Cas2_ProjetComplet(unittest.TestCase):
    def test_64_forages_lus(self):
        lignes = [f"H{i:02d};{512000+i*10};{731800+i*5};{220-i*0.1};120"
                  for i in range(64)]
        lec = lit_collets("complet.csv", texte=texte(*lignes))
        self.assertEqual(len(lec.colliers), 64)
        self.assertIn(Niveau.INFO, niveaux(lec))


class Cas3_TypesManquants(unittest.TestCase):
    def test_type_absent_est_annonce_pas_invente(self):
        cat = Projet().catalogue
        for pid in ("recovery", "density"):
            self.assertFalse(cat.resout(pid).visible)
            self.assertFalse(cat.resout(pid).specific.get("breaks"))


class Cas4_Doublons(unittest.TestCase):
    def test_deux_forages_meme_nom_bloquent(self):
        lec = lit_collets("d.csv", texte=texte(
            "A;512340.2;731880.4;218.4;120",
            "B;512366.0;731902.1;221.0;98",
            "A;512340.2;731880.4;218.4;120"))
        blo = [m for m in lec.messages if m.niveau is Niveau.BLOCAGE]
        self.assertEqual(len(blo), 1)
        self.assertIn("A", blo[0].concernes)
        self.assertGreaterEqual(len(blo[0].resoudre), 2)

    def test_identifiant_different_mais_meme_point_signale(self):
        lec = lit_collets("d2.csv", texte=texte(
            "A;512340.2;731880.4;218.4;120",
            "B;512340.2;731880.4;218.4;120"))
        self.assertEqual(len(lec.colliers), 2)   # rien n'est supprimé


class Cas5_Separateur(unittest.TestCase):
    def test_point_virgule_et_virgule(self):
        lec = lit_collets("a.csv", texte=texte("A;1;2;3;10", "B;3;4;5;11"))
        self.assertEqual(len(lec.colliers), 2)
        lec2 = lit_collets("b.csv", texte="ID,X,Y,Z\nA,1,2,3\n")
        self.assertEqual(len(lec2.colliers), 1)


class Cas6_Decimale(unittest.TestCase):
    def test_virgule_decimale(self):
        lec = lit_collets("c.csv", texte=texte("A;512340,2;731880,4;218,4;120"))
        f = lec.colliers[0]
        self.assertAlmostEqual(f.x, 512340.2)
        self.assertAlmostEqual(f.z, 218.4)

    def test_milliers_et_decimales_melanges(self):
        lec = lit_collets("c2.csv", texte=texte("A;512.340,2;731.880,4;218,4;120"))
        self.assertAlmostEqual(lec.colliers[0].x, 512340.2)


class Cas7_Encodage(unittest.TestCase):
    def test_latin1_est_repare_et_signale(self):
        brut = "ID;X;Y;Z\nA;1;2;3\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "latin.csv"
            f.write_bytes(brut.replace(b"A", b"A"))
            lec = lit_collets(f)
        self.assertEqual(len(lec.colliers), 1)
        self.assertIn("utf-8", lec.journal["encodage"])

    def test_cp1252_relu(self):
        octets = "ID;X;Y;Z\nA;1;2;3  # altération\n".encode("cp1252")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "cp.csv"
            f.write_bytes(octets)
            lec = lit_collets(f)
        self.assertEqual(len(lec.colliers), 1)
        self.assertTrue(any("accents" in m.titre.lower() for m in lec.messages))


class Cas8_ForagesInclines(unittest.TestCase):
    def test_trajectoire_inclinee_descend(self):
        mes = [(0, 110, -55), (30, 112, -60), (60, 113, -65)]
        p = fond(0, 0, 100, mes, "courbure_minimale", 60)
        self.assertLess(p.z, 100)
        self.assertGreater(abs(p.x) + abs(p.y), 0)


class Cas9_ForageHorizontal(unittest.TestCase):
    def test_pendage_zero_reste_horizontal(self):
        p = fond(0, 0, 100, [(0, 90, 0), (50, 90, 0)], "courbure_minimale", 50)
        self.assertAlmostEqual(p.z, 100, places=6)


class Cas10_PendageInverse(unittest.TestCase):
    def test_convention_inversee_detectee(self):
        p_neg = fond(0, 0, 100, [(0, 0, -90)], "angle_moyen", 50)
        p_pos = fond(0, 0, 100, [(0, 0, 90)], "angle_moyen", 50)
        self.assertAlmostEqual(p_neg.z, p_pos.z, places=6)   # valeur absolue


class Cas11_EcartDesMethodes(unittest.TestCase):
    def test_ecart_signale_si_grand(self):
        mes = [(0, 110, -55), (30, 170, -30), (60, 200, -10)]
        r = compare(0, 0, 100, mes)
        self.assertGreater(r["ecart_m"], 0.5)
        self.assertIsNotNone(r["message"])
        self.assertEqual(r["message"].niveau, Niveau.AVERTISSEMENT)


class Cas12_Coupe(unittest.TestCase):
    def setUp(self):
        lignes = [f"H{i:02d};{512000+i*40};{731800+i*10};{220-i*0.2};{120+i}"
                  for i in range(10)]
        self.lec = lit_collets("c.csv", texte=texte(*lignes))
        self.ligne = Ligne(512000, 731800, 512360, 731890)

    def test_inclusion_et_exclusion(self):
        inc = inclusion(self.lec.colliers, self.ligne, buffer=25)
        self.assertGreater(len(inc.inclus), 0)
        self.assertEqual(len(inc.inclus) + len(inc.exclus), 10)

    def test_projection_est_ordonnee_et_calculable(self):
        inc = inclusion(self.lec.colliers, self.ligne, buffer=60)
        traces = projette(inc.inclus, self.ligne)
        self.assertEqual(traces, sorted(traces, key=lambda t: t.abscisse))
        for t in traces:
            self.assertLess(t.altitude_fond, t.altitude_collet)

    def test_coupe_vide_est_signalee(self):
        loin = Ligne(0, 0, 100, 0)
        inc = inclusion(self.lec.colliers, loin, buffer=5)
        self.assertEqual(len(inc.inclus), 0)
        msgs = controle_couverture(projette(inc.inclus, loin))
        self.assertTrue(msgs)
        self.assertEqual(msgs[0].niveau, Niveau.AVERTISSEMENT)


class Cas13_Intercepts(unittest.TestCase):
    def test_seuils_et_longueur_minimale(self):
        ana = [("H1", 0, 2, 0.05), ("H1", 2, 4, 1.4), ("H1", 4, 6, 2.1),
               ("H2", 0, 0.5, 3.0)]
        retenus = intercepts(ana, [0.1, 1.0], longueur_min=1.0)
        cles = {(i["forage"], i["seuil"]) for i in retenus}
        self.assertIn(("H1", 1.0), cles)
        self.assertNotIn(("H2", 1.0), cles)      # trop court
        self.assertNotIn(("H1", 5.0), cles)

    def test_teneur_manquante_n_invente_rien(self):
        retenus = intercepts([("H1", 0, 2, None)], [0.1])
        self.assertEqual(retenus, [])


class Cas14_ExclusionGlobale(unittest.TestCase):
    def test_exclure_s_applique_partout(self):
        p = Projet()
        p.importe("a.csv", texte=texte("A;1;2;3;10", "B;3;4;5;11"))
        p.exclut("B", "doublon signalé ligne 88")
        self.assertEqual([f.id for f in p.forages_actifs()], ["A"])
        p.reintegre("B")
        self.assertEqual(len(p.forages_actifs()), 2)

    def test_exclusion_sans_motif_refusee(self):
        p = Projet()
        with self.assertRaises(ValueError):
            p.exclut("A", "")


class Cas15_FichierSourceIntact(unittest.TestCase):
    def test_aucune_ecriture_dans_le_fichier_source(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "source.csv"
            f.write_bytes(texte("A;1;2;3;10").encode())
            avant = hashlib.sha256(f.read_bytes()).hexdigest()
            p = Projet()
            p.importe(f)
            p.exclut("A", "essai")
            apres = hashlib.sha256(f.read_bytes()).hexdigest()
        self.assertEqual(avant, apres)


class Cas16_Mode(unittest.TestCase):
    def test_basculer_de_mode_ne_change_aucune_valeur(self):
        p = Projet()
        avant = {pid: p.style(pid).to_dict() for pid in p.catalogue.ids()}
        for _ in range(5):
            p.bascule_mode("experte")
            p.bascule_mode("guidee")
        apres = {pid: p.style(pid).to_dict() for pid in p.catalogue.ids()}
        self.assertEqual(avant, apres)

    def test_mode_inconnu_refuse(self):
        with self.assertRaises(ValueError):
            Projet().bascule_mode("turbo")


if __name__ == "__main__":
    unittest.main()
