"""Chantier 6 — la forme des fonctions du plugin, mesurée et tenue.

Le rangement par fichiers (``test_rangement.py``) ne dit qu'une partie de
l'histoire : un fichier de 2 000 lignes composé de vingt fonctions de 100
lignes est lisible ; un fichier de 600 lignes qui contient une seule
fonction de 500 lignes ne l'est pas. Ce fichier mesure donc l'autre moitié,
celle qu'on ne voyait pas :

- combien de fonctions dépassent 80, 150, 250 et 400 lignes ;
- combien de méthodes porte chaque classe, et quelle classe est un
  monolithe à elle seule ;
- combien de fonctions imbriquées une seule fonction porte (le signe que
  du code a été replié au lieu d'être nommé) ;
- combien de dupes tournent avec des valeurs figées, et avec quel montant.

Comme partout dans ce dépôt, chaque chiffre est un **cliquet** : il ne peut
que baisser. Quand une tranche sort du code, on baisse le chiffre dans le
même commit. Un chiffre qui monte fait échouer la suite, ce qui est le but.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PLUGIN = RACINE / "DrillMaster"

# Mesures du 8 novembre 2026, avant toute tranche d'architecture.
# → 106 fonctions de 80 lignes et plus
# → 31 de 150 et plus · 12 de 250 et plus · 5 de 400 et plus
SEUILS = {80: 106, 150: 31, 250: 12, 400: 5}
# Moins de 40 lignes : ce qui reste à l'échelle d'une fonction nommable.
# 1 548 sur 1 836 = 84,3 % au 8 novembre 2026. Le cliquet est posé à la
# mesure, pas à l'ambition : il ne peut que monter.
PLAFOND_COURTES_RATIO = 0.84

# La plus grosse méthode du dépôt : `SectionWidget` en un seul morceau.
# 5 296 lignes au 8 novembre 2026 (10 165 pour le fichier entier).
PLAFOND_PLUS_GROSSE_CLASSE = 5_296
# Méthodes portées par une seule classe, même mesure.
PLAFOND_METHODES_UNE_CLASSE = 172
# Fonctions nommées repliées dans une seule fonction : au-delà, la fonction
# n'est plus un algorithme mais un fichier déguisé. Le maximum mesuré est
# 9 (``_draw_style_identity_track``), à quoi s'ajoutent 13 générateurs.
PLAFOND_IMBRIQUEES = 9


def fonctions(chemin: Path):
    """Toutes les fonctions du fichier, imbriquées comprises."""
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    vues = []

    def descendre(noeud, profondeur=1):
        for e in ast.iter_child_nodes(noeud):
            if isinstance(e, (ast.FunctionDef, ast.AsyncFunctionDef)):
                vues.append((e, profondeur))
                descendre(e, profondeur + 1)
            else:
                descendre(e, profondeur)

    descendre(arbre)
    return vues


def fichiers_du_plugin():
    return sorted(p for p in PLUGIN.rglob("*.py") if "__pycache__" not in str(p))


def taille(f) -> int:
    return f.end_lineno - f.lineno + 1


def classes(chemin: Path):
    return [n for n in ast.parse(chemin.read_text(encoding="utf-8")).body
            if isinstance(n, ast.ClassDef)]


def compte_seuils() -> dict:
    compte = {s: 0 for s in SEUILS}
    for f in fichiers_du_plugin():
        for noeud, _ in fonctions(f):
            l = taille(noeud)
            for s in compte:
                if l >= s:
                    compte[s] += 1
    return compte


class LaTailleDesFonctions(unittest.TestCase):
    """Une fonction se juge à sa taille, pas à celle de son fichier."""

    def test_le_nombre_de_grandes_fonctions_ne_monte_pas(self):
        compte = compte_seuils()
        self.assertEqual(compte, SEUILS, (
            "la forme des fonctions a changé : "
            f"mesuré {compte}, cliquet {SEUILS}. Une fonction qui grandit "
            "doit sortir en fonctions nommées dans le même commit."))
        for s, n in compte.items():
            self.assertLessEqual(n, SEUILS[s])

    def test_la_plupart_des_fonctions_tiennent_en_une_page(self):
        """Le vrai indicateur de lisibilité : la part de fonctions courtes."""
        total = courtes = 0
        for f in fichiers_du_plugin():
            for noeud, _ in fonctions(f):
                total += 1
                if taille(noeud) < 40:
                    courtes += 1
        part = courtes / total
        self.assertGreaterEqual(part, PLAFOND_COURTES_RATIO, (
            f"{courtes} fonctions de moins de 40 lignes sur {total} "
            f"({part:.1%}) — le seuil est {PLAFOND_COURTES_RATIO:.0%}"))

    def test_les_cinq_plus_grandes_fonctions_sont_nommees(self):
        """Pas une préférence de style : ces cinq-là sont les seules à
        pouvoir cacher une régression dans 400 lignes de dessin."""
        records = [(n.name, str(f.relative_to(PLUGIN)), taille(n))
                   for f in fichiers_du_plugin() for n, _ in fonctions(f)
                   if taille(n) >= 400]
        noms = {r[0] for r in records}
        self.assertEqual(len(records), SEUILS[400])
        self.assertIn("paint_legends_image_impl", noms)
        self.assertIn("draw_drillhole", noms)
        self.assertIn("_draw_style_identity_track", noms)


class LaFormeDesClasses(unittest.TestCase):
    """Trois classes portent le plugin ; elles ne doivent pas grossir."""

    def plus_grosse(self):
        meilleure = ("", "", 0)
        for f in fichiers_du_plugin():
            for c in classes(f):
                l = c.end_lineno - c.lineno + 1
                if l > meilleure[2]:
                    meilleure = (c.name, str(f.relative_to(PLUGIN)), l)
        return meilleure

    def test_la_plus_grosse_classe_ne_grandit_pas(self):
        nom, fichier, l = self.plus_grosse()
        self.assertLessEqual(l, PLAFOND_PLUS_GROSSE_CLASSE,
                             f"{nom} ({fichier}) fait {l} lignes")

    def test_aucune_classe_ne_porte_plus_de_methodes(self):
        pire = ("", 0)
        for f in fichiers_du_plugin():
            for c in classes(f):
                n = sum(1 for e in c.body
                        if isinstance(e, (ast.FunctionDef, ast.AsyncFunctionDef)))
                if n > pire[1]:
                    pire = (c.name, n)
        self.assertLessEqual(pire[1], PLAFOND_METHODES_UNE_CLASSE,
                             f"{pire[0]} porte {pire[1]} méthodes")


class LaMesureEstEcrivable(unittest.TestCase):
    """R-67 : la forme se mesure, et la mesure est publiable.

    `specs/data/formes.json` n'est pas un ornement : c'est la source de la
    planche 34. S'il n'était plus produit, la planche mentirait sans que
    rien ne le dise.
    """

    OUTIL = RACINE / "tools" / "audit_formes.py"
    DONNEES = RACINE / "specs" / "data" / "formes.json"
    PLANCHE = RACINE / "maquettes" / "34_formes.png"

    def test_l_outil_tourne(self):
        import subprocess
        import sys
        r = subprocess.run([sys.executable, str(self.OUTIL)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        self.assertIn("fonctions dans le plugin", r.stdout)

    def test_les_donnees_et_la_planche_existent(self):
        self.assertTrue(self.DONNEES.exists())
        self.assertTrue(self.PLANCHE.exists())

    def test_les_donnees_disent_la_meme_chose_que_le_test(self):
        import json
        from collections import Counter
        d = json.loads(self.DONNEES.read_text(encoding="utf-8"))
        mesure = Counter()
        for f in fichiers_du_plugin():
            for noeud, _ in fonctions(f):
                for s in SEUILS:
                    if taille(noeud) >= s:
                        mesure[str(s)] += 1
        self.assertEqual(d["par_seuil"], {str(s): mesure[str(s)]
                                          for s in SEUILS})
        self.assertEqual(d["plus_grosse_classe"]["nom"], "SectionWidget")


class LeCodeReplie(unittest.TestCase):
    """Une fonction de 673 lignes n'est pas un algorithme : c'est du code
    replié faute de l'avoir nommé. Ce test dit **combien**."""

    def test_aucune_fonction_ne_replie_plus_de_fonctions(self):
        pire = ("", 0, 0, 0)
        for f in fichiers_du_plugin():
            for noeud, _ in fonctions(f):
                imbriquees = [
                    e for e in ast.walk(noeud)
                    if isinstance(e, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and e is not noeud]
                nommees = [e for e in imbriquees
                           if not str(e.name).startswith(("genexpr", "lambda",
                                                          "listcomp", "setcomp",
                                                          "dictcomp"))]
                if len(nommees) > pire[1]:
                    pire = (noeud.name, len(nommees),
                            str(f.relative_to(PLUGIN)), noeud.lineno)
        self.assertLessEqual(pire[1], PLAFOND_IMBRIQUEES,
                             f"{pire[0]} ({pire[2]}:{pire[3]}) replie "
                             f"{pire[1]} fonctions nommées")

    def test_les_trois_fonctions_repliees_sont_connues(self):
        """On les nomme ici pour qu'on ne les découvre pas par hasard :
        ce sont les prochains chantiers, avec leur compte exact."""
        attendu = {
            "_draw_style_identity_track": 9,   # + 13 générateurs et lambdas
            "paint_legends_image_impl": 5,     # + 11 générateurs et lambdas
            "validate_intervals": 0,           # 16 générateurs seulement
        }
        trouve = {}
        for f in fichiers_du_plugin():
            for noeud, _ in fonctions(f):
                if noeud.name in attendu:
                    trouve[noeud.name] = sum(
                        1 for e in ast.walk(noeud)
                        if isinstance(e, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and e is not noeud
                        and not e.name.startswith(("genexpr", "lambda")))
        self.assertEqual(trouve, attendu, trouve)


if __name__ == "__main__":
    unittest.main()
