"""Chantier 6 — les rangements, tenus par des cliquets.

Un cliquet ne dit pas « c'est bien rangé » : il dit **ça ne peut pas
empirer en silence**. Chaque chiffre ci-dessous est une mesure, pas une
impression ; quand une tranche sort du monolithe, on baisse le cliquet
dans le même commit.
"""
from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PLUGIN = RACINE / "DrillMaster"
DOCK = PLUGIN / "ui" / "section_dock.py"
SOCLE = PLUGIN / "ui" / "coupe_socle.py"

# Cliquet : section_dock.py ne doit jamais remonter au-dessus de cette valeur.
# 11 529 avant le chantier 6
# → 10 515 après la tranche 1 (socle + journal)
# → 10 247 après les tranches 2 et 3 (contours, survol, traits de motif)
PLAFOND_DOCK = 10_290
# Un seul fichier du plugin a le droit de dépasser 3 000 lignes. Quand il
# n'y en aura plus aucun, cette constante passera à 0.
FICHIERS_GEANTS_AUTORISES = 1


def lignes(p: Path) -> int:
    return len(p.read_text(encoding="utf-8").splitlines())


def noms_du_module(p: Path) -> set:
    arbre = ast.parse(p.read_text(encoding="utf-8"))
    out = set()
    for n in arbre.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            out.update(t.id for t in n.targets if isinstance(t, ast.Name))
    return out


class Cliquets(unittest.TestCase):
    def test_le_monolithe_ne_remonte_pas(self):
        n = lignes(DOCK)
        self.assertLessEqual(n, PLAFOND_DOCK, (
            f"section_dock.py fait {n} lignes (plafond {PLAFOND_DOCK}). "
            "Une fonctionnalité ajoutée ici doit sortir dans un module "
            "de tranche, pas gonfler le monolithe."))

    def test_un_seul_fichier_geant(self):
        geants = [p for p in PLUGIN.rglob("*.py")
                  if lignes(p) > 3000]
        self.assertLessEqual(len(geants), FICHIERS_GEANTS_AUTORISES,
                             [str(p.relative_to(PLUGIN)) for p in geants])


class Tranche1(unittest.TestCase):
    """Ce que la tranche 1 a sorti doit rester sorti ET rester accessible."""

    DELEGUES = {
        "SELECTION_HIGHLIGHT_COLOR", "LEGEND_CLICK_COLOR",
        "SELECTION_OUTLINE_PEN_DOCK", "SELECTION_OUTLINE_PEN_EXPORT",
        "_LITHO_BRUSH_PATTERNS", "_LINE_BRUSH_STYLES",
        "_pattern_ink_colour", "_selection_highlight_pen",
        "_selection_chrome_stylesheet", "_export_smallcaps_font",
        "_export_sc_text", "_legend_label", "_PatternPolygonItem",
        "_ClippedStrokeItem", "_ClippedFillItem", "_StyledFillItem",
    }

    def test_les_noms_vivent_dans_le_socle(self):
        manquants = self.DELEGUES - noms_du_module(SOCLE)
        self.assertFalse(manquants, manquants)

    def test_le_monolithe_les_reexporte(self):
        """`from .section_dock import SELECTION_HIGHLIGHT_COLOR` doit marcher."""
        source = DOCK.read_text(encoding="utf-8")
        for nom in self.DELEGUES:
            self.assertIn(nom, source, f"{nom} n'est plus ré-exporté")

    def test_aucun_nom_defini_deux_fois(self):
        """La même définition dans les deux fichiers = deux vérités."""
        communs = noms_du_module(SOCLE) & noms_du_module(DOCK)
        self.assertFalse(communs, communs)

    def test_le_journal_de_versions_a_quitte_le_code(self):
        """Un journal dans une docstring se lit à chaque modification."""
        doc = ast.get_docstring(ast.parse(DOCK.read_text(encoding="utf-8")))
        self.assertNotIn("v2.9.135", doc)
        self.assertLess(len(doc.splitlines()), 60)
        hist = RACINE / "docs" / "HISTORIQUE_section_dock.md"
        self.assertTrue(hist.exists())
        contenu = hist.read_text(encoding="utf-8")
        self.assertIn("v2.9.135", contenu)   # le plus récent
        self.assertIn("v2.7.10.32", contenu)  # le plus ancien conservé


class Mesure(unittest.TestCase):
    def test_l_outil_de_mesure_tourne_toujours(self):
        r = subprocess.run([sys.executable,
                            str(RACINE / "tools" / "audit_rangement.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fichiers", r.stdout)


if __name__ == "__main__":
    unittest.main()


class Tranche2Et3(unittest.TestCase):
    """Ce que les tranches 2 et 3 ont sorti doit rester sorti, et identique.

    Une tranche de rangement ne se juge pas sur le nombre de lignes : elle se
    juge sur le **code déplacé**. Ces tests rejouent les fonctions réelles et
    comparent leur comportement à celui décrit par leur contrat — puis
    vérifient qu'elles ne sont plus dans le monolithe.
    """

    CONTOURS = PLUGIN / "ui" / "coupe_contours.py"
    SORTIS = ("_inset_band_depth_ends", "_exterior_outline_path",
              "_exterior_outline_path_from_poly", "_add_tooltip_hit_pad",
              "_draw_axis_aligned_pattern_lines")

    def test_les_fonctions_vivent_dans_le_module_de_tranche(self):
        noms = noms_du_module(self.CONTOURS)
        manquants = set(self.SORTIS) - noms
        self.assertFalse(manquants, manquants)

    def test_elles_ne_sont_plus_dans_le_monolithe(self):
        """Le contraire ferait deux vérités pour le même contour."""
        arbre = ast.parse(DOCK.read_text(encoding="utf-8"))
        canvas = [c for c in arbre.body
                  if isinstance(c, ast.ClassDef) and c.name == "SectionCanvas"][0]
        restants = {n.name for n in canvas.body
                    if isinstance(n, ast.FunctionDef)} & set(self.SORTIS)
        self.assertFalse(restants, restants)

    def test_la_classe_les_rattache_encore(self):
        """`self._add_tooltip_hit_pad(...)` doit marcher : aucun appelant
        n'a eu à changer."""
        source = DOCK.read_text(encoding="utf-8")
        for nom in self.SORTIS:
            self.assertIn(f"SectionCanvas.{nom}", source,
                          f"{nom} n'est plus rattaché à la classe")

    def test_le_monolithe_a_baisse(self):
        n = lignes(DOCK)
        self.assertLessEqual(n, PLAFOND_DOCK)
        self.assertLess(n, 10_380, f"section_dock.py fait {n} lignes")


class LeContourNeChangePasDeForme(unittest.TestCase):
    """Trois fonctions de géométrie pure : on les exécute pour de vrai.

    (Le monolithe ne s'importe pas sans QGIS ; la tranche, elle, ne demande
    que trois classes Qt — c'est précisément ce que le rangement a gagné.)

    Qt n'est pas installé dans cet environnement, mais ces fonctions ne
    prennent que des points et rendent un chemin. On leur fournit donc un
    double minimal : ce qui est vérifié, c'est la **géométrie** (les bons
    décalages, les bons signes), pas la peinture.
    """

    CONTOURS = PLUGIN / "ui" / "coupe_contours.py"

    @classmethod
    def setUpClass(cls):
        import sys
        from types import SimpleNamespace

        class Point:
            def __init__(self, x, y):
                self._x, self._y = x, y

            def x(self):
                return self._x

            def y(self):
                return self._y

        class Polygone(list):
            def size(self):
                return len(self)

            def at(self, i):
                return self[i]

        class Chemin:
            def __init__(self, autre=None):
                self.points = list(getattr(autre, "points", []))

            def isEmpty(self):
                return not self.points

            def addPolygon(self, poly):
                self.points = list(poly)

        from types import ModuleType
        faux = {
            "qgis": ModuleType("qgis"),
            "qgis.PyQt.QtCore": ModuleType("qgis.PyQt.QtCore"),
            "qgis.PyQt.QtGui": ModuleType("qgis.PyQt.QtGui"),
            "qgis.PyQt.QtWidgets": ModuleType("qgis.PyQt.QtWidgets"),
            "qgis.PyQt.QtGui": SimpleNamespace(QPainterPath=Chemin,
                                               QPainterPathStroker=object,
                                               QPolygonF=Polygone,
                                               QBrush=object, QColor=object,
                                               QPen=object, QFont=object,
                                               QPainter=object),
            "qgis.PyQt": SimpleNamespace(QtCore=None, QtGui=None),
        }
        cœur = faux["qgis.PyQt.QtCore"]
        cœur.QPointF = Point
        class _Enum:
            """Un membre d'énumération qui accepte n'importe quel nom."""
            def __getattr__(self, nom):
                return nom

        class QtFactice:
            BrushStyle = _Enum()
            PenStyle = _Enum()
            PenCapStyle = _Enum()
            PenJoinStyle = _Enum()

        cœur.Qt = QtFactice()
        cœur.QCoreApplication = object
        gui = faux["qgis.PyQt.QtGui"]
        gui.QPainterPath = Chemin
        gui.QPainterPathStroker = object
        gui.QPolygonF = Polygone
        for nom in ("QBrush", "QColor", "QPen", "QFont", "QPainter"):
            setattr(gui, nom, object)
        widgets = faux["qgis.PyQt.QtWidgets"]
        widgets.QGraphicsPolygonItem = object
        widgets.QLabel = object
        pyqt = ModuleType("qgis.PyQt")
        pyqt.QtCore = cœur
        pyqt.QtGui = gui
        pyqt.QtWidgets = widgets
        faux["qgis.PyQt"] = pyqt
        faux["qgis"].PyQt = pyqt
        ajoutes = {}
        for nom, module in faux.items():
            if nom not in sys.modules:
                sys.modules[nom] = module
                ajoutes[nom] = module
        cls.ajoutes = ajoutes
        cls.Point = Point
        cls.Polygone = Polygone

    @classmethod
    def tearDownClass(cls):
        import sys
        for nom in cls.ajoutes:
            sys.modules.pop(nom, None)

    def charge(self):
        """On charge la tranche comme un module de paquet (imports relatifs)."""
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location(
            "DrillMaster.ui.coupe_contours", self.CONTOURS,
            submodule_search_locations=None)
        module = importlib.util.module_from_spec(spec)
        sys.modules["DrillMaster.ui.coupe_contours"] = module
        spec.loader.exec_module(module)
        return module

    def trapeze(self):
        """Une bande de 40 m de profondeur, 2 m de large."""
        P = self.Point
        return self.Polygone([P(0, 0), P(2, 0), P(2, 40), P(0, 40)])

    def test_l_inset_rentre_les_deux_bouts(self):
        m = self.charge()
        sortie = m._inset_band_depth_ends(self.trapeze(), inset=1.0)
        haut = [sortie.at(i) for i in (0, 1)]
        bas = [sortie.at(i) for i in (2, 3)]
        # les deux bouts se rapprochent du centre en profondeur (y)
        self.assertAlmostEqual(haut[0].y(), 1.0, places=6)
        self.assertAlmostEqual(bas[0].y(), 39.0, places=6)
        # les côtés latéraux ne bougent pas en x
        self.assertAlmostEqual(haut[0].x(), 0.0, places=6)
        self.assertAlmostEqual(haut[1].x(), 2.0, places=6)

    def test_l_inset_ne_retourne_pas_une_bande_trop_courte(self):
        m = self.charge()
        plat = self.Polygone([self.Point(0, 0), self.Point(2, 0),
                              self.Point(2, 0.5), self.Point(0, 0.5)])
        sortie = m._inset_band_depth_ends(plat, inset=10.0)
        ys = [sortie.at(i).y() for i in range(4)]
        self.assertLess(max(ys), 0.5, "la bande s'est retournée")

    def test_l_inset_laisse_passer_un_polygone_absent(self):
        m = self.charge()
        self.assertIsNone(m._inset_band_depth_ends(None))
        self.assertIsNone(m._inset_band_depth_ends(None, inset=3))

    def test_le_contour_part_d_un_polygone_nul_sans_lever(self):
        m = self.charge()
        self.assertIsNone(m._exterior_outline_path_from_poly(None))
        self.assertIsNone(m._exterior_outline_path(None))
