"""Chantier 12 — une installation se juge chez l'utilisateur, pas chez l'auteur.

R-64 une promesse de compatibilité se mesure · R-65 une extension embarque ce
qu'elle lit · R-66 un fichier cherché au-dessus du paquet est introuvable.

Le défaut central de ce chantier n'était pas dans la liste de la flotte :
`core/about.py` cherchait `LICENSE` **au-dessus** du dossier du plugin. Dans
le dépôt, cela tombait sur le fichier de la racine — donc « trouvé » à la
compilation, et « introuvable » chez chaque utilisateur. Ces tests installent
le paquet seul, comme QGIS le fait, et lui posent la question.
"""
from __future__ import annotations

import configparser
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PLUGIN = RACINE / "DrillMaster"
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.installation import (          # noqa: E402
    CATEGORIES, CHAMPS_REQUIS, compatible_qgis4, fiche, fenetre,
    paquet_propre, preflight, verifie)


def metadata_du_paquet():
    cp = configparser.ConfigParser()
    with open(PLUGIN / "metadata.txt", encoding="utf-8") as flux:
        cp.read_file(flux)
    return dict(cp.items("general"))


class LaFicheEstComplete(unittest.TestCase):
    """Les huit champs que le dépôt officiel exige, et rien de faux."""

    def test_les_huit_champs_obligatoires_sont_fournis(self):
        f = fiche(metadata_du_paquet())
        self.assertEqual(f["manquants"], [], f["manquants"])
        self.assertEqual(len(f["fournis"]), len(CHAMPS_REQUIS))

    def test_aucun_reproche_sur_la_fiche_reelle(self):
        self.assertEqual(verifie(metadata_du_paquet()), [])

    def test_un_champ_absent_est_nomme(self):
        meta = metadata_du_paquet()
        del meta["email"]
        self.assertIn("email", fiche(meta)["manquants"])
        self.assertTrue(any("email" in r for r in verifie(meta)))

    def test_une_adresse_qui_n_en_est_pas_une_est_refusee(self):
        meta = metadata_du_paquet()
        meta["email"] = "theophileyann.gmail.com"
        self.assertTrue(any("adresse" in r for r in verifie(meta)))

    def test_une_categorie_hors_liste_est_refusee(self):
        """`category=Plugins` n'existe pas : une catégorie fausse vaut moins
        qu'aucune, parce qu'elle annonce un menu où le plugin n'est pas."""
        self.assertNotIn("Plugins", CATEGORIES)
        meta = metadata_du_paquet()
        meta["category"] = "Plugins"
        self.assertTrue(any("catégorie" in r for r in verifie(meta)))

    def test_la_categorie_reelle_est_absente_ou_admise(self):
        categorie = metadata_du_paquet().get("category", "")
        self.assertIn(categorie, CATEGORIES + ("",))


class LaCompatibiliteNeMentPas(unittest.TestCase):
    """R-64 : `qgisMaximumVersion=4.99` est une promesse, pas une case."""

    def test_declarer_qgis4_sans_le_tenir_est_un_mensonge(self):
        f = fenetre("3.28", "4.99", non_qualifies=692, exec_restants=15)
        self.assertTrue(f["declare_qgis4"])
        self.assertFalse(f["tient_qgis4"])
        self.assertTrue(f["mensonge"])

    def test_le_plugin_ne_promet_pas_qgis4_tant_qu_il_ne_le_merite_pas(self):
        """La fenêtre déclarée ne doit jamais dépasser ce que le code tient.

        Avant la migration : 692 formes anciennes, 15 `exec_()`, 53 types de
        champ — et une fenêtre honnêtement arrêtée à 3.99. Après : le code
        suit Qt 6, la fenêtre peut suivre. Ce qui est vérifié ici n'est pas
        un chiffre, c'est la **cohérence** entre les deux.
        """
        audit = json.loads((RACINE / "specs" / "data" / "installation.json")
                           .read_text(encoding="utf-8"))["compatibilite"]
        self.assertFalse(audit["mensonge"],
                         "la fenêtre déclarée promet QGIS 4 sans le tenir")
        if audit["tient_qgis4"]:
            self.assertEqual(audit["sites_a_migrer"], 0)
            self.assertEqual(audit["exec_a_migrer"], 0)
            self.assertEqual(audit["champs_a_migrer"], 0)

    def test_un_code_migre_autorise_la_promesse(self):
        self.assertTrue(compatible_qgis4(0, 0, 0))
        self.assertFalse(compatible_qgis4(1, 0, 0))
        self.assertFalse(compatible_qgis4(0, 1, 0))
        self.assertFalse(compatible_qgis4(0, 0, 1),
                         "un type de champ à l'ancienne forme interdit la "
                         "promesse QGIS 4")

    def test_les_trois_familles_de_sites_sont_comptees(self):
        """Les trois familles sont mesurées — même quand deux valent zéro.

        Une mesure qui disparaît quand elle devient bonne n'est plus une
        mesure : le champ reste, à zéro.
        """
        audit = json.loads((RACINE / "specs" / "data" / "installation.json")
                           .read_text(encoding="utf-8"))["compatibilite"]
        for cle in ("sites_a_migrer", "exec_a_migrer", "champs_a_migrer"):
            self.assertIn(cle, audit)
            self.assertIsInstance(audit[cle], int)
            self.assertGreaterEqual(audit[cle], 0)
        # la mesure des types de champ reste branchée : éprouvée sur un
        # dossier témoin, pas supprimée parce que le plugin est propre
        sys.path.insert(0, str(RACINE / "tools"))
        import audit_installation
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "essai.py").write_text(
                "from qgis.PyQt.QtCore import QVariant\n"
                "f = QVariant.Double\n", encoding="utf-8")
            trouves = audit_installation.champs_anciens(Path(tmp))
        self.assertEqual(len(trouves), 1, "la mesure des types de champ est "
                                          "débranchée")
        self.assertEqual(trouves[0]["forme"], "QVariant.Double")

    def test_la_migration_a_bien_retire_les_formes_anciennes(self):
        """692 formes et 15 `exec_()` au départ : zéro à l'arrivée."""
        audit = json.loads((RACINE / "specs" / "data" / "installation.json")
                           .read_text(encoding="utf-8"))["compatibilite"]
        self.assertEqual(audit["sites_a_migrer"], 0,
                         "des énumérations Qt 5 subsistent")
        self.assertEqual(audit["exec_a_migrer"], 0,
                         "des exec_() subsistent")

    def test_la_fenetre_declaree_ne_depasse_jamais_ce_que_le_code_tient(self):
        """L'invariant n'est pas l'égalité : c'est l'implication.

        On peut tenir QGIS 4 dans le code sans l'annoncer (l'épreuve réelle
        manque). On ne peut pas l'annoncer sans le tenir.
        """
        audit = json.loads((RACINE / "specs" / "data" / "installation.json")
                           .read_text(encoding="utf-8"))["compatibilite"]
        if audit["declare_qgis4"]:
            self.assertTrue(audit["tient_qgis4"],
                            "la fenêtre déclarée promet plus que le code")
        self.assertFalse(audit["mensonge"])

    def test_chaque_site_mesure_donne_sa_forme_qt6(self):
        audit = json.loads((RACINE / "specs" / "data" / "installation.json")
                           .read_text(encoding="utf-8"))["compatibilite"]
        for site in audit["sites"]:
            self.assertIn("forme_qt6", site)
            self.assertNotEqual(site["forme"], site["forme_qt6"])


class LaMigrationEstMecanique(unittest.TestCase):
    """La table qui mesure sert aussi à corriger — et ne devine jamais.

    `tools/migre_qt6.py` est éprouvé sur un texte témoin, puis sur le
    plugin réel **sans écrire** : la mesure doit être reproductible, sinon
    le chiffre du plan ne vaut rien.
    """

    TEMOIN = (
        "from qgis.PyQt.QtCore import Qt\n"
        "label.setAlignment(Qt.AlignCenter)\n"
        "box = QDialogButtonBox(QDialogButtonBox.Ok)\n"
        "if box.exec_():\n"
        "    painter.setRenderHint(QPainter.Antialiasing)\n"
    )

    def texte_migre(self):
        sys.path.insert(0, str(RACINE / "tools"))
        import migre_qt6
        return migre_qt6.corriger(self.TEMOIN)[0]

    def test_la_migration_qualifie_les_enumerations(self):
        migre = self.texte_migre()
        self.assertIn("Qt.AlignmentFlag.AlignCenter", migre)
        self.assertIn("QDialogButtonBox.StandardButton.Ok", migre)
        self.assertIn("QPainter.RenderHint.Antialiasing", migre)

    def test_la_migration_remplace_exec_(self):
        self.assertIn("box.exec()", self.texte_migre())
        self.assertNotIn("exec_()", self.texte_migre())

    def test_la_migration_ne_touche_pas_une_chaine(self):
        sys.path.insert(0, str(RACINE / "tools"))
        import migre_qt6
        texte = 'label.setText("Qt.AlignCenter et exec_()")\n'
        self.assertEqual(migre_qt6.corriger(texte)[0], texte)

    def test_la_migration_est_reversible(self):
        sys.path.insert(0, str(RACINE / "tools"))
        import migre_qt6
        migre, _ = migre_qt6.corriger(self.TEMOIN)
        return_at = migre_qt6.inverse(migre)
        for forme in ("Qt.AlignCenter", "QDialogButtonBox.Ok",
                      "QPainter.Antialiasing", "exec_()"):
            self.assertIn(forme, return_at)

    def test_la_mesure_du_plugin_est_reproductible(self):
        sys.path.insert(0, str(RACINE / "tools"))
        import importlib
        import audit_installation
        importlib.reload(audit_installation)
        enums, exec_, champs = audit_installation.sites_qt6()
        audit = json.loads((RACINE / "specs" / "data" / "installation.json")
                           .read_text(encoding="utf-8"))["compatibilite"]
        self.assertEqual(audit["sites_a_migrer"], len(enums))
        self.assertEqual(audit["exec_a_migrer"], len(exec_))
        self.assertEqual(audit["champs_a_migrer"], len(champs))


class LePaquetNePorteQueCeQuIlLit(unittest.TestCase):
    """R-65 : un paquet n'embarque ni cache compilé ni banc d'essai."""

    def test_les_fichiers_de_developpement_sont_nommes(self):
        fautifs = paquet_propre([
            "DrillMaster/__pycache__/x.cpython-311.pyc",
            "DrillMaster/tools/bench_scene3d.py",
            "DrillMaster/core/section.py",
            "DrillMaster/LICENSE",
        ])
        self.assertEqual(fautifs, ["DrillMaster/__pycache__/x.cpython-311.pyc",
                                   "DrillMaster/tools/bench_scene3d.py"])

    def test_le_paquet_reel_n_a_plus_de_dossier_de_developpement(self):
        self.assertFalse((PLUGIN / "tools").exists(),
                         "le dossier tools est revenu dans le paquet")

    def test_aucun_banc_d_essai_ne_pointe_vers_un_chemin_d_auteur(self):
        """Un banc qui commence par `sys.path.insert(0, "/home/…")` ne peut
        pas tourner ailleurs que sur la machine où il a été écrit."""
        fautifs = []
        for f in PLUGIN.rglob("*.py"):
            texte = f.read_text(encoding="utf-8", errors="ignore")
            if "/home/" in texte:
                fautifs.append(str(f.relative_to(PLUGIN)))
        self.assertEqual(fautifs, [])

    def test_le_cache_compile_n_est_pas_dans_le_depot(self):
        suivis = subprocess.run(["git", "ls-files", "DrillMaster"],
                                cwd=RACINE, capture_output=True,
                                text=True).stdout
        self.assertNotIn("__pycache__", suivis)
        self.assertNotIn(".pyc", suivis)


class LaLicenceSeTrouveChezLUtilisateur(unittest.TestCase):
    """R-66 : un fichier cherché au-dessus du paquet n'existe pas une fois
    installé. On copie donc le paquet seul, et on lui demande."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.cible = Path(cls.tmp.name) / "plugins" / "DrillMaster"
        shutil.copytree(PLUGIN, cls.cible,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        sys.path.insert(0, str(Path(cls.tmp.name) / "plugins"))
        for nom in [m for m in sys.modules if m.startswith("DrillMaster")]:
            del sys.modules[nom]
        from DrillMaster.core.about import about_info
        cls.info = about_info(str(cls.cible))

    @classmethod
    def tearDownClass(cls):
        sys.path.pop(0)
        for nom in [m for m in sys.modules if m.startswith("DrillMaster")]:
            del sys.modules[nom]
        cls.tmp.cleanup()

    def test_la_licence_est_trouvee_dans_le_paquet_installe(self):
        self.assertTrue(self.info["license_installed"],
                        "la licence n'est pas trouvée une fois le paquet seul")
        self.assertTrue(self.info["license_file"].endswith("DrillMaster/LICENSE"))

    def test_le_fichier_existe_vraiment_a_l_endroit_annonce(self):
        self.assertTrue(Path(self.info["license_file"]).is_file())

    def test_le_paquet_installe_ne_manque_de_rien_au_demarrage(self):
        self.assertEqual(preflight(str(self.cible)), [])

    def test_la_version_lue_est_celle_du_paquet(self):
        self.assertEqual(self.info["version"], metadata_du_paquet()["version"])

    def test_la_fenetre_affichee_est_celle_declaree(self):
        meta = metadata_du_paquet()
        self.assertEqual(self.info["qgis_minimum"], meta["qgisminimumversion"])
        self.assertEqual(self.info["qgis_maximum"], meta["qgismaximumversion"])


class Mesure(unittest.TestCase):
    def test_l_outil_de_mesure_tourne_toujours(self):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "audit_installation.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("la fiche d'identité", r.stdout)
        self.assertIn("le démarrage, paquet copié seul", r.stdout)


if __name__ == "__main__":
    unittest.main()


class LesDeuxQtSontEprouves(unittest.TestCase):
    """Une migration doit marcher chez ceux qui ont Qt 5 **et** chez ceux qui
    auront Qt 6. Une table peut se tromper : elle s'est trompée une fois.

    `tools/verifie_qt6.py` rejoue chaque forme employée par le plugin dans un
    PyQt5 réel, puis la confronte aux déclarations `.pyi` livrées par PyQt5
    **et** PyQt6. Ces tests lisent son résultat, et le refont tourner.
    """

    @classmethod
    def setUpClass(cls):
        chemin = RACINE / "specs" / "data" / "qt6.json"
        cls.audit = json.loads(chemin.read_text(encoding="utf-8"))

    def test_aucune_forme_n_est_refusee_par_les_deux_qt(self):
        decl = self.audit["declarations"]
        self.assertEqual(decl["qt5_refusees"], {},
                         "une forme employée n'existe pas sur Qt 5")
        self.assertEqual(decl["qt6_refusees"], {},
                         "une forme employée n'existe pas sur Qt 6")

    def test_les_formes_employees_sont_toutes_qualifiees(self):
        """`Qt.AlignCenter` a disparu du plugin : chaque membre est nommé
        par son énumération, seule forme que Qt 6 accepte."""
        sys.path.insert(0, str(RACINE / "tools"))
        import verifie_qt6
        formes = verifie_qt6.formes_employees()
        self.assertGreater(len(formes), 100)
        for forme in formes:
            self.assertGreaterEqual(
                forme.count("."), 2,
                f"{forme} n'est pas qualifiée par son énumération")

    def test_le_defaut_trouve_par_l_epreuve_ne_revient_pas(self):
        """`AdjustToMinimumContentsLength` existe sur Qt 5 et **plus** sur
        Qt 6 : la seule forme juste sur les deux est celle qui garde le
        suffixe `WithIcon`."""
        textes = "\n".join(
            f.read_text(encoding="utf-8", errors="ignore")
            for f in PLUGIN.rglob("*.py") if "__pycache__" not in str(f))
        self.assertNotIn("AdjustToMinimumContentsLength(", textes)
        self.assertIn("AdjustToMinimumContentsLengthWithIcon", textes)

    def test_l_epreuve_dans_un_qgis4_reel_n_est_pas_affirmee(self):
        self.assertFalse(self.audit["epreuve_reelle_qgis4"],
                         "l'épreuve réelle est affirmée sans avoir eu lieu")

    def test_l_outil_tourne_encore(self):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "verifie_qt6.py")],
                           capture_output=True, text=True)
        self.assertIn("Qt 5", r.stdout)
        self.assertIn("n'est PAS prouvé ici", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-400:])
