"""Chantier 11 — la vitesse se mesure sur le vrai travail, et se publie.

R-62 une mesure qui n'est pas publiée n'existe pas · R-63 un travail long
s'annonce avant de commencer. Les chiffres de référence sont mesurés par
`tools/audit_vitesse.py`, pas inventés.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.coupe2d.coupe import (Ligne, inclusion,   # noqa: E402
                                               intercepts, projette)
from drillmaster_v3.core.donnees.lecture import Forage              # noqa: E402
from drillmaster_v3.core.vitesse import (                           # noqa: E402
    BUDGET_FRAME_MS, SEUIL_ATTENTE_MS, annonce, chronometre,
    doit_passer_en_tache_de_fond, experience, verdict)

import math                                                          # noqa: E402

A = math.radians(45)


def coupe(n_forages, par_forage=50, buffer=800):
    ligne = Ligne(512000, 731800, 512000 + 195 * math.sin(A),
                  731800 + 195 * math.cos(A))
    forages = [Forage(id=f"F{i}", x=512000 + (i * 0.09) * math.sin(A),
                      y=731800 + (i * 0.09) * math.cos(A), z=219.0,
                      profondeur=110) for i in range(n_forages)]
    analyses = [(f.id, j * 2.0, j * 2.0 + 2.0, 0.1 + j % 9)
                for f in forages for j in range(par_forage)]
    inc = inclusion(forages, ligne, buffer)
    traces = projette(inc.inclus, ligne)
    inter = intercepts(analyses, [1.0, 5.0])
    return inc, traces, inter


class LeCalculTientSesPromesses(unittest.TestCase):
    def test_64_forages_tiennent_dans_une_frame(self):
        with chronometre("coupe 64") as c:
            inc, traces, inter = coupe(64)
        self.assertEqual(len(traces), 64)
        self.assertLess(c.ms, BUDGET_FRAME_MS, c.publie())

    def test_le_cout_croit_avec_la_taille_et_on_le_dit(self):
        with chronometre("coupe 2000") as c:
            coupe(2000)
        self.assertGreater(c.ms, BUDGET_FRAME_MS)
        self.assertIn("annoncer", annonce(c.ms) or "annoncé")  \
            if c.ms > SEUIL_ATTENTE_MS else None

    def test_un_forage_hors_coupe_est_annonce(self):
        """R-14 : un forage écarté de la coupe n'est jamais silencieusement absent."""
        ligne = Ligne(512000, 731800, 512000 + 195 * math.sin(A),
                      731800 + 195 * math.cos(A))
        # un forage posé à 400 m de l'axe, tolérance 10 m
        loin = Forage(id="LOIN", x=512000 + 60, y=731800 - 400, z=200.0)
        inc = inclusion([loin], ligne, 10)
        self.assertEqual(inc.inclus, [])
        self.assertEqual(len(inc.exclus), 1)
        self.assertIn("m de l'axe", inc.exclus[0][1])
        self.assertTrue(inc.messages)


class LaMesureSePublie(unittest.TestCase):
    def test_un_chronometre_rend_une_phrase_lisible(self):
        with chronometre("essai") as c:
            time.sleep(0.005)
        phrase = c.publie()
        self.assertIn("essai", phrase)
        self.assertIn("ms", phrase)
        self.assertGreater(c.ms, 0)

    def test_la_publication_peut_sortir_du_module(self):
        vues = []
        with chronometre("coupe") as c:
            pass
        c.publie(publicateur=vues.append)
        self.assertEqual(len(vues), 1)

    def test_un_temps_nul_est_dit_non_mesure(self):
        self.assertEqual(verdict(0), "non mesuré")


class UnTravailLongSAnnonce(unittest.TestCase):
    def test_sous_le_seuil_aucune_annonce(self):
        self.assertEqual(annonce(20), "")
        self.assertFalse(doit_passer_en_tache_de_fond(12))

    def test_au_dela_du_seuil_l_annonce_dit_la_duree(self):
        phrase = annonce(830)
        self.assertIn("secondes", phrase)
        self.assertIn("environ", phrase)

    def test_une_tache_de_fond_ne_sert_a_rien_sous_une_frame(self):
        self.assertTrue(doit_passer_en_tache_de_fond(17))
        self.assertFalse(doit_passer_en_tache_de_fond(3))

    def test_l_experience_est_dite_sans_chiffre_technique(self):
        self.assertEqual(experience(1.8), "instantané")
        self.assertEqual(experience(16.7), "un court silence")
        self.assertEqual(experience(79.0), "une attente visible")


class MesureDuPlugin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "audit_vitesse.py"),
                            "--ecrit"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        cls.audit = json.loads(
            (RACINE / "specs" / "data" / "vitesse.json")
            .read_text(encoding="utf-8"))

    def test_la_coupe_de_reference_est_mesuree(self):
        self.assertEqual(self.audit["coupe"]["forages"], 64)
        self.assertGreater(self.audit["coupe"]["analyses"], 3000)
        self.assertLess(self.audit["coupe"]["median_ms"], BUDGET_FRAME_MS)

    def test_les_boucles_imbriquees_ne_remontent_pas(self):
        # plafond : mesuré à 119. Il ne peut que diminuer.
        self.assertLessEqual(self.audit["boucles_imbriquees_total"], 119)

    def test_les_modules_qui_mesurent_sont_nommes(self):
        self.assertGreaterEqual(len(self.audit["modules_qui_mesurent"]), 5)

    def test_le_defaut_constate_est_chiffre(self):
        """Sept modules mesurent, un seul publie : c'est le défaut d'origine."""
        self.assertEqual(
            len(self.audit["modules_qui_publient"]),
            1, self.audit["modules_qui_publient"])


if __name__ == "__main__":
    unittest.main()
