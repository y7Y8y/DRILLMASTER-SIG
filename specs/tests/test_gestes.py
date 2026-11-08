"""Chantier 5 — boutons et gestes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.gestes import (Geste, GesteRefuse,   # noqa: E402
                                        barre, un_seul_primaire)


def supprimer():
    return (Geste("Supprimer le projet", destructive=True, role="discret")
            .portee("le dossier du projet")
            .perd("les fichiers importés", "les coupes enregistrées")
            .sortie("confirmer par écrit")
            .exige_motif())


class RolesTest(unittest.TestCase):
    def test_un_role_inconnu_est_refuse(self):
        with self.assertRaises(GesteRefuse) as ctx:
            Geste("Calculer", role="principal")
        self.assertIn("les rôles sont", str(ctx.exception))

    def test_un_mot_creux_est_refuse(self):
        for mot in ("OK", "Valider", "go"):
            with self.assertRaises(GesteRefuse):
                Geste(mot, role="primaire")

    def test_une_destruction_n_est_jamais_le_bouton_principal(self):
        with self.assertRaises(GesteRefuse) as ctx:
            Geste("Supprimer", destructive=True, role="primaire")
        self.assertIn("jamais le bouton principal", str(ctx.exception))

    def test_un_seul_primaire_par_barre(self):
        a = Geste("Importer", role="primaire")
        b = Geste("Importer aussi", role="primaire")
        with self.assertRaises(GesteRefuse):
            un_seul_primaire([a, b])

    def test_la_barre_nomme_les_trois_poids(self):
        b = barre("Actions", [Geste("Importer", role="primaire"),
                              Geste("Comparer", role="secondaire"),
                              Geste("Plus tard", role="discret")])
        self.assertEqual(b["primaire"], "Importer")
        self.assertEqual(b["secondaires"], ["Comparer"])
        self.assertEqual(b["discrets"], ["Plus tard"])
        self.assertTrue(b["couleur_primaire"].startswith("#"))


class AnnonceTest(unittest.TestCase):
    def test_une_action_informative_s_annonce_par_son_libelle(self):
        g = Geste("Calculer la coupe", role="primaire")
        self.assertEqual(g.annonce(), "Calculer la coupe")

    def test_une_action_destructrice_dit_ce_qui_sera_perdu(self):
        texte = supprimer().annonce()
        self.assertIn("sera perdu", texte)
        self.assertIn("les fichiers importés", texte)
        self.assertIn("coupes enregistrées", texte)

    def test_sans_pertes_declarees_une_destruction_est_refusee(self):
        g = Geste("Supprimer tout", destructive=True, role="discret")
        with self.assertRaises(GesteRefuse) as ctx:
            g.annonce()
        self.assertIn("ne dit pas ce qui sera perdu", str(ctx.exception))

    def test_sans_sortie_une_destruction_est_refusee(self):
        g = (Geste("Supprimer tout", destructive=True, role="discret")
             .perd("tout"))
        with self.assertRaises(GesteRefuse) as ctx:
            g.annonce()
        self.assertIn("aucune sortie", str(ctx.exception))


class AccordTest(unittest.TestCase):
    def test_sans_nom_rien_ne_s_execute(self):
        with self.assertRaises(GesteRefuse) as ctx:
            supprimer().verifie(signe="", motif="x", ecrit=True)
        self.assertIn("qui agit", str(ctx.exception))

    def test_sans_motif_quand_il_est_exige(self):
        with self.assertRaises(GesteRefuse) as ctx:
            supprimer().verifie(signe="A. Koné", motif="", ecrit=True)
        self.assertIn("demande un motif", str(ctx.exception))

    def test_une_destruction_exige_une_confirmation_ecrite(self):
        with self.assertRaises(GesteRefuse) as ctx:
            supprimer().verifie(signe="A. Koné", motif="fini", ecrit=False)
        self.assertIn("confirmation écrite", str(ctx.exception))

    def test_le_geste_complet_passe(self):
        self.assertTrue(supprimer().verifie(signe="A. Koné",
                                            motif="projet abandonné",
                                            ecrit=True))

    def test_une_action_ordinaire_ne_demande_pas_de_motif(self):
        g = Geste("Calculer la coupe", role="primaire")
        self.assertTrue(g.verifie(signe="A. Koné"))


if __name__ == "__main__":
    unittest.main()
