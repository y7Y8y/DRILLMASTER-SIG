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
# → 10 163 après la tranche 4 (rose de localisation)
PLAFOND_DOCK = 10_195
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


class Tranche4(unittest.TestCase):
    """La rose de localisation : sortie, rattachée, et toujours la même.

    Particularité de cette tranche : elle est la première à dépendre de
    ``styles_qt`` (les couleurs de la charte). C'est ce qui la rend
    vérifiable sans Qt : on substitue une charte connue et une scène qui
    **note** ce qu'on lui demande, puis on relit le dessin.
    """

    ROSE = PLUGIN / "ui" / "coupe_rose.py"
    SORTIE = "_draw_north_badge"

    def test_la_fonction_vit_dans_le_module_de_tranche(self):
        self.assertIn(self.SORTIE, noms_du_module(self.ROSE))

    def test_elle_n_est_plus_dans_le_monolithe(self):
        arbre = ast.parse(DOCK.read_text(encoding="utf-8"))
        canvas = [c for c in arbre.body
                  if isinstance(c, ast.ClassDef) and c.name == "SectionCanvas"][0]
        self.assertNotIn(self.SORTIE,
                         {n.name for n in canvas.body
                          if isinstance(n, ast.FunctionDef)})

    def test_la_classe_la_rattache_encore(self):
        self.assertIn(self.SORTIE, DOCK.read_text(encoding="utf-8")
                      .replace("SectionCanvas._draw_north_badge", ""))

    def test_elle_ne_lit_plus_la_vue(self):
        """Le critère de la tranche : plus une seule lecture de ``self``."""
        arbre = ast.parse(self.ROSE.read_text(encoding="utf-8"))
        f = [n for n in arbre.body
             if isinstance(n, ast.FunctionDef) and n.name == self.SORTIE][0]
        self.assertEqual([a.arg for a in f.args.args], ["widget", "scene", "line"])
        attrs = {n.attr for n in ast.walk(f)
                 if isinstance(n, ast.Attribute)
                 and isinstance(n.value, ast.Name) and n.value.id == "self"}
        self.assertFalse(attrs, attrs)


class LaRoseDessineToujoursLaMemeChose(unittest.TestCase):
    """On exécute le dessin avec une scène qui note les appels.

    Ce qui est vérifié : le **contrat du dessin** (sept items, leur ordre
    d'empilement, les textes affichés, l'infobulle commune). Ce qui ne
    l'est pas : la peinture — Qt n'est pas installé ici.
    """

    ROSE = PLUGIN / "ui" / "coupe_rose.py"

    @classmethod
    def setUpClass(cls):
        cls.ajoutes = []

    @classmethod
    def tearDownClass(cls):
        for nom in cls.ajoutes:
            sys.modules.pop(nom, None)

    # ── doubles ────────────────────────────────────────────────────────
    class Objet:
        """Tout ce que la rose touche sur un item de scène."""

        def __init__(self, genre, *args):
            self.genre = genre
            self.args = args
            self.z = None
            self.tip = None
            self.pos = None
            self.texte = args[0] if genre == "texte" else None
            self.couleur = None

        def setZValue(self, z):
            self.z = z

        def setToolTip(self, t):
            self.tip = t

        def setPos(self, x, y):
            self.pos = (x, y)

        def setDefaultTextColor(self, c):
            self.couleur = c

        def boundingRect(self):
            class R:
                def width(self):
                    return 10

                def height(self):
                    return 6
            return R()

    class Scene:
        def __init__(self):
            self.items = []

        def _note(self, genre, *a):
            o = LaRoseDessineToujoursLaMemeChose.Objet(genre, *a)
            self.items.append(o)
            return o

        def addEllipse(self, *a):
            return self._note("ellipse", *a)

        def addLine(self, *a):
            return self._note("ligne", *a)

        def addPolygon(self, *a):
            return self._note("polygone", *a)

        def addText(self, texte, *a):
            return self._note("texte", texte, *a)

    class Traduction:
        """``widget.tr`` : la chaîne est rendue telle quelle."""

        def tr(self, texte):
            return texte

    class Ligne:
        def __init__(self, x1, y1, x2, y2):
            self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

    def charge(self):
        """On charge la tranche avec de faux Qt et une charte connue."""
        import importlib.util
        from types import ModuleType

        charte = ModuleType("DrillMaster.ui.styles_qt")
        charte.COLORS = {"primary": "#PRIMAIRE", "border": "#BORD",
                         "text_medium": "#TEXTE"}
        sys.modules["DrillMaster.ui.styles_qt"] = charte
        self.ajoutes.append("DrillMaster.ui.styles_qt")

        class Point:
            def __init__(self, x, y):
                self._x, self._y = x, y

            def x(self):
                return self._x

            def y(self):
                return self._y

        import types
        for nom in ("qgis", "qgis.PyQt", "qgis.PyQt.QtCore", "qgis.PyQt.QtGui"):
            if nom not in sys.modules:
                sys.modules[nom] = types.ModuleType(nom)
                self.ajoutes.append(nom)
        sys.modules["qgis.PyQt.QtCore"].QPointF = Point
        gui = sys.modules["qgis.PyQt.QtGui"]

        class Enum:
            """Une énumération qui accepte n'importe quel nom, comme Qt 5/6."""

            def __getattr__(self, nom):
                return nom

        class Fonte:
            Weight = Enum()
            Style = Enum()

            def __init__(self, *a):
                self.args = a

        for nom in ("QBrush", "QColor", "QPen"):
            setattr(gui, nom, type(nom, (), {"__init__": lambda self, *a: None}))
        gui.QFont = Fonte
        gui.QPolygonF = lambda points: list(points)
        sys.modules["qgis"].PyQt = sys.modules["qgis.PyQt"]
        sys.modules["qgis.PyQt"].QtCore = sys.modules["qgis.PyQt.QtCore"]
        sys.modules["qgis.PyQt"].QtGui = gui

        nom_module = "DrillMaster.ui.coupe_rose"
        spec = importlib.util.spec_from_file_location(nom_module, self.ROSE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[nom_module] = module
        spec.loader.exec_module(module)
        return module

    def dessine(self, azimut_est=290.0):
        """Une coupe fictive dirigée vers 290° (WNW), dessinée pour de vrai."""
        module = self.charge()
        import math
        rad = math.radians(azimut_est)
        ligne = self.Ligne(0.0, 0.0, 200 * math.sin(rad), 200 * math.cos(rad))
        scene = self.Scene()
        module._draw_north_badge(self.Traduction(), scene, ligne)
        return scene.items

    # ── tests ──────────────────────────────────────────────────────────
    def test_huit_items_et_dans_cet_ordre(self):
        """Disque, trace, pointe, aiguille sud et nord, puis les quatre
        textes : N, P1, P2 et la légende. L'ordre d'empilement suit
        l'ordre de création, d'où l'intérêt de le figer ici."""
        genres = [i.genre for i in self.dessine()]
        self.assertEqual(genres, ["ellipse", "ligne", "polygone", "polygone",
                                  "polygone", "texte", "texte", "texte",
                                  "texte"])

    def test_la_trace_va_de_p1_vers_p2(self):
        """La rose est une vue de plan **schématique** : la trace ne reprend
        pas les coordonnées de la ligne, elle va du bout P1 au bout P2 du
        petit disque. Ce qui compte est le sens : P2 est du côté de
        l'azimut (ici 290°, donc ouest et nord)."""
        items = self.dessine()
        trace = items[1]
        self.assertEqual(trace.genre, "ligne")
        x1, y1, x2, y2 = trace.args[:4]
        # P1 en haut à droite du disque (centre 30, 32), P2 à l'opposé
        self.assertAlmostEqual(x1, 30.0 + 11 * 1.05 * 0.9397, places=2)
        self.assertAlmostEqual(y1, 32.0 + 11 * 1.05 * 0.3420, places=2)
        # cap 290° : P2 est à l'ouest (x plus petit) et au nord (y plus petit)
        self.assertLess(x2, x1)
        self.assertLess(y2, y1)
        # la trace fait exactement le diamètre utile du disque
        self.assertAlmostEqual(
            ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 2 * 11 * 1.05, places=6)

    def test_les_trois_textes_restent_ceux_de_la_charte(self):
        textes = [i.texte for i in self.dessine() if i.genre == "texte"]
        self.assertIn("N", textes)
        self.assertIn("P1", textes)
        self.assertIn("P2", textes)

    def test_la_legende_dit_l_azimut_et_le_sens_en_toutes_lettres(self):
        textes = [i.texte for i in self.dessine() if i.genre == "texte"]
        legende = [t for t in textes if t.startswith("coupe ")]
        self.assertEqual(len(legende), 1, textes)
        self.assertIn("N290°", legende[0])
        self.assertIn("WNW", legende[0])
        self.assertIn("ESE", legende[0])

    def test_l_infobulle_est_la_meme_sur_tous_les_items(self):
        items = self.dessine()
        bulles = {i.tip for i in items}
        self.assertEqual(len(bulles), 1, bulles)
        self.assertIn("Nord", bulles.pop())

    def test_sans_ligne_de_coupe_rien_n_est_dessine(self):
        module = self.charge()
        scene = self.Scene()
        module._draw_north_badge(self.Traduction(), scene, None)
        self.assertEqual(scene.items, [])
