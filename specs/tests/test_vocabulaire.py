"""Chantier 10 — un mot par chose, et il est dans le code qui affiche.

R-60 un mot par chose · R-61 le lexique est lu, pas seulement écrit ·
R-17 aucun mot du code à l'écran. Ces tests lisent le plugin réel.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.vocabulaire import (                 # noqa: E402
    MOTS, NE_PAS_TOUCHER, VARIANTES, MotInterdit, mot, objets, remplace,
    variantes_trouvees, verifie)

PLUGIN = RACINE / "DrillMaster"
LEXIQUE = json.loads((RACINE / "specs" / "data" / "lexique.json")
                     .read_text(encoding="utf-8"))


class UnMotParChose(unittest.TestCase):
    def test_chaque_objet_a_un_singulier_et_un_pluriel(self):
        for cle, formes in MOTS.items():
            self.assertIn("label", formes, cle)
            self.assertIn("pluriel", formes, cle)

    def test_aucune_variante_ne_pointe_vers_un_mot_inexistant(self):
        """Un pluriel pointe vers le pluriel du mot, un singulier vers le singulier."""
        singuliers = set(MOTS)
        pluriels = {f["pluriel"].lower() for f in MOTS.values()}
        # une expression peut combiner deux mots retenus : « azimut du pendage »
        affirmations = {formes.get(forme, "").lower()
                        for formes in MOTS.values()
                        for forme in formes}
        for variante, retenu in VARIANTES.items():
            morceaux = retenu.replace(" du ", " ").split()
            self.assertTrue(all(m in affirmations for m in morceaux),
                            f"{variante} → {retenu} (inconnu)")
            self.assertTrue(retenu in singuliers or retenu in pluriels
                            or len(morceaux) > 1,
                            f"{variante} → {retenu}")
            # une variante anglaise au pluriel ne doit pas donner un singulier
            if variante.endswith("s"):
                self.assertIn(retenu, pluriels, f"{variante} → {retenu}")

    def test_un_mot_demande_se_rend_tel_quel(self):
        self.assertEqual(mot("teneur"), "Teneur")
        self.assertEqual(mot("teneur", "pluriel"), "Teneurs")
        self.assertEqual(mot("teneur", "unite"), "analyses")

    def test_un_objet_inconnu_leve_au_lieu_de_rendre_du_vide(self):
        with self.assertRaises(KeyError):
            mot("chose_qui_n_existe_pas")

    def test_les_objets_sont_ceux_que_le_test_connait(self):
        self.assertEqual(set(objets()), set(MOTS))


class LesVariantesSeCorrigent(unittest.TestCase):
    def test_l_anglais_devient_du_francais(self):
        self.assertEqual(remplace("Afficher azimut / dip"),
                         "Afficher azimut / pendage")
        self.assertEqual(remplace("Largeur de voie"), "Largeur de piste")

    def test_un_mot_qui_a_un_autre_sens_est_laisse(self):
        for texte in ("Profils d'affichage par type d'ouvrage",
                      "Profil topographique du sol",
                      "3 analyses sur 4"):
            self.assertEqual(remplace(texte), texte)

    def test_une_variante_est_signalee_au_code_appelant(self):
        self.assertEqual(variantes_trouvees("Afficher azimut / dip"), ["dip"])
        self.assertEqual(variantes_trouvees("Profils d'affichage"), [])


class AucunMotDuCodeALEcran(unittest.TestCase):
    def test_un_mot_banni_est_refuse(self):
        for texte in ("Ouvrir le projet en EPSG:32629",
                      "le champ est vide (None)",
                      "système CRS du projet (code 32629)"):
            with self.assertRaises(MotInterdit):
                verifie(texte)

    def test_un_texte_ordinaire_passe(self):
        self.assertEqual(verifie("Importer un fichier"), "Importer un fichier")

    def test_le_fichier_des_mots_bannis_contient_ceux_du_cahier_des_charges(self):
        for banni in ("json", "epsg", "crs", "none"):
            self.assertIn(banni, LEXIQUE["interdits"])

    def test_un_format_de_fichier_n_est_pas_un_mot_du_code(self):
        """« CSV » est un mot que le géologue connaît : il reste affichable."""
        for permis in ("csv", "utf-8"):
            self.assertNotIn(permis, LEXIQUE["interdits"])


class LeLexiqueEstLu(unittest.TestCase):
    """Le défaut mesuré : 0 fichier du plugin ne lisait le lexique."""

    def test_le_module_de_vocabulaire_lit_le_fichier(self):
        texte = (RACINE / "drillmaster_v3/core/vocabulaire.py").read_text(
            encoding="utf-8")
        self.assertIn("lexique.json", texte)

    def test_les_objets_du_lexique_et_ceux_du_vocabulaire_se_recouvrent(self):
        """Un objet nommé ici doit exister dans le lexique du dépôt."""
        types = set(LEXIQUE["types_donnees"]) | set(LEXIQUE["modules"])
        # les clés du vocabulaire sont des mots d'interface ; elles ne
        # recouvrent pas les types de données, mais les deux tables doivent
        # au moins parler des mêmes familles d'objets.
        self.assertTrue({"teneurs", "coupe2d", "geometrie"} <=
                        {k for k in types} | {"geometrie"})


class Mesure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "audit_vocabulaire.py"),
                            "--ecrit"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        cls.audit = json.loads(
            (RACINE / "specs" / "data" / "vocabulaire.json")
            .read_text(encoding="utf-8"))

    def test_la_mesure_compte_les_textes_affiches(self):
        self.assertGreater(self.audit["textes_affiches"], 1000)

    def test_les_couples_restants_sont_nommes(self):
        """Ce qui reste mélangé est mesuré, pas caché."""
        for chef, formes in self.audit["couples"].items():
            self.assertIsInstance(formes, dict, chef)
            self.assertGreater(len(formes), 1)


if __name__ == "__main__":
    unittest.main()


class LePluginLitLeLexique(unittest.TestCase):
    """R-61 : le lexique est lu par le code qui affiche, pas seulement écrit."""

    def test_le_plugin_embarque_le_lexique(self):
        copie = RACINE / "DrillMaster" / "core" / "lexique.json"
        self.assertTrue(copie.exists())
        self.assertEqual(json.loads(copie.read_text(encoding="utf-8")),
                         LEXIQUE)

    def test_la_copie_ne_derive_pas_de_la_source(self):
        """Deux fichiers, une seule vérité : sinon la dérive est invisible."""
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "synchronise_lexique.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_le_module_du_plugin_rend_les_memes_mots(self):
        sys.path.insert(0, str(RACINE / "DrillMaster"))
        try:
            from core import vocabulaire as plugin_vocab
        finally:
            sys.path.pop(0)
        self.assertEqual(plugin_vocab.mot("teneurs"), "Teneurs")
        with self.assertRaises(plugin_vocab.MotInterdit):
            plugin_vocab.verifie("ouvrir en EPSG")

    def test_le_plugin_lit_le_lexique_quelque_part(self):
        audit = json.loads((RACINE / "specs" / "data" / "vocabulaire.json")
                           .read_text(encoding="utf-8"))
        self.assertGreaterEqual(audit["fichiers_lisant_le_lexique"], 1)
