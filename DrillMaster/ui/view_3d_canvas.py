"""
DrillMaster — 3D Drillhole View Widget (v2.9.140)
=================================================
Professional 3D visualization engine for mining geology adhering to JORC / NI 43-101 standards:
  - Factual data segregation: Lithologie, Teneurs (analyses quantitatives), Altérations, Minéralisations (styles).
  - Multi-element assay discretization matching 2D section thresholds and palettes.
  - Clean non-scientific grade formatting (e.g. 5.2 – 110, 110 – 400, 1 100 – 1 400).
  - Exact project referential colors (lithology, alterations, mineral styles) matching 2D.
  - Composite lithology support (secondary barrettes and quartz veins rendered prominently with exact colors).
  - Floating 3D legend (bottom-left) with multi-column support, ample title clearance, and zero overlap with triad gizmo.
  - Prominent golden sleeve highlights and calipers for interval and category selections.
  - Smart auto-flip hover tooltip in clean light theme ("noir sur blanc, simple et efficace").
  - Directional hillshade on 3D topographic terrain surface (enabled by default when available).
  - Graduated XYZ coordinate axes and tick marks on 3D bounding box frame.
  - Seamless floating camera preset dropdown (top-left) and action tools (top-right) over canvas (no dark top bar).
  - Non-invasive selection with click-to-deselect and click-away-to-deselect.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from qgis.PyQt.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal
from qgis.PyQt.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPolygonF,
)
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QScrollArea, QSlider, QSplitter, QVBoxLayout, QWidget,
)

from ..core.data_model import DrillHole, IntervalRecord, TrajectoryPoint
# v2.9.147 — formateur de teneurs partagé (vivant désormais dans
# core/multi_assay : la couche overlays l'importe aussi).
from ..core.multi_assay import format_grade_value
from ..core.section import (
    ASSAY_RAMPS, assay_ramp_rgb, classify_assay, compute_assay_scale,
    suggested_litho_color,
)
from ..core.selection_model import IntervalSelection
from ..core.spatial_model import SpatialModel
from ..core.workspace import WorkspaceState
# v2.9.141 — surface 3D réelle (P1) + relief (P2) : grille interpolée,
# isocontours, interpolation bilinéaire — pure Python (core.topography).
from ..core.topography import (
    build_surface_grid, bounds_from_points, contour_levels,
    contour_segments, grid_from_gridded_samples, smooth_surface_grid,
)
from qgis.PyQt.QtCore import QCoreApplication as _QCA

from .styles_qt import (
    BASE_STYLE, BUTTON_PRIMARY, BUTTON_SECONDARY, COLORS, INPUT_STYLE,
    suppress_button_focus_rects,
)


def _tr(text):
    """Traduction des textes de la vue 3D (contexte View3DCanvas)."""
    return _QCA.translate("View3DCanvas", text)


HELP_3D_TEXT = """NAVIGATION
• Orbite : clic gauche + glisser · Pan : clic droit · Zoom : molette
• Clic sur un tube : sélectionne l'intervalle (synchronisé coupe 2D et carte)
• Clic sur une ligne de légende : met en évidence ce code

DONNÉES SUR FORAGES
• « Domaine affiché » : le domaine PRINCIPAL (tube centré, pleine largeur).
• « Domaines simultanés » (cases à cocher) : domaines additionnels en
  tubes fins décalés à côté du principal — même richesse que le domaine
  seul (motifs, veines « \\ », accessoires « / », barrettes, intensité).
  ⚠ Disponible uniquement en portée « Coupe active seule » ou
  « Sélection seule ».  En « Projet complet » (des centaines de forages),
  un seul domaine pour rester lisible — comme les gros logiciels.

PORTÉE
• Projet complet : tous les forages — vue d'ensemble.
• Coupe active seule : les forages de la coupe 2D — comparaison
  géologique, domaines simultanés disponibles.
• Sélection seule : 1 à quelques forages sélectionnés — examen détaillé.

CONSEILS
• La légende s'adapte aux domaines actifs ; survolez une ligne pour le
  libellé complet, cliquez pour filtrer par code.
• Pendant l'orbite l'affichage s'allège pour rester fluide ; motifs et
  légende reviennent dès que vous relâchez.
• Le soulignement « ★ » en légende marque le code filtré actif.
"""


class View3DCanvas(QWidget):
    """Interactive 3D viewport rendered via QPainter with real-world spatial coordinates."""

    interval_clicked = pyqtSignal(str, float, float)  # hole_id, from_m, to_m
    hover_changed = pyqtSignal(str)                   # tooltip text

    def __init__(self, workspace_state: WorkspaceState, parent=None):
        super().__init__(parent)
        self.workspace_state = workspace_state
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # v2.9.145 (volet 1) — les MATHS de caméra vivent dans
        # core/camera3d.OrbitCamera (pur, zéro Qt, réutilisable) ; ce
        # canvas expose yaw/pitch/zoom/pan/v_exag/pivot comme des
        # PROPRIÉTÉS déléguées (les appels existants ne changent pas).
        from ..core.camera3d import OrbitCamera
        self.camera = OrbitCamera()

        # v2.9.145 (volet 1, D1-1) — résolution visuelle via le résolveur
        # PARTAGÉ coupe 2D / vue 3D (core/style_resolver) : plus de
        # cartes de couleurs privées dans la vue.
        from ..core.style_resolver import StyleResolver
        self._style = StyleResolver()

        # Active Geological Domain on Boreholes (JORC: strictly segregated)
        # v2.9.166 — DOMAINES MULTIPLES : liste des domaines actifs
        # (le PREMIER = domaine principal = tube centré pleine largeur ;
        # les suivants = tubes parallèles plus fins, comme les pistes 2D).
        self._active_domains: list[str] = ["litho"]

        # Assay mapping options
        self.active_assay_element: str = ""
        self.assay_palette: str = "grade"
        self._assay_scale: Optional[dict[str, Any]] = None

        # v2.9.143 — éléments teneurs affichés en 3D, choisis DIRECTEMENT
        # dans le combo à cases de la vue 3D (retour écran : passer par la
        # config 2D « mélangeait » l'utilisateur) :
        # [] = miroir de la coupe 2D (1–3 éléments du style) ;
        # ["Cu_ppm", "Fe_pct"] = affiche ces éléments simultanément.
        self.assay_display_elements: list[str] = []

        # v2.9.141 — multi-teneurs (max 3, comme la coupe 2D) + règles de seuil.
        self._assay_elements: list[str] = []
        self._assay_element_palettes: dict[str, str] = {}
        self._assay_scales: dict[str, dict] = {}
        self._threshold_rules: list[dict] = []

        # Spatial Layers Visibilities
        # v2.9.148 — MNT DÉCOCHÉ par défaut (retour écran) : la surface
        # reste calculée/mise en cache (statut dans la barre), on l'affiche
        # à la demande via la case « Surface du terrain ».
        self.show_topography: bool = False    # 3D Ground surface (MNT)
        self.show_drillholes: bool = True     # Boreholes
        self.show_section_plane: bool = False # Active 2D section slice - False by default
        self.show_corridor: bool = False      # 3D Corridor volume - False by default
        self.show_axes: bool = True           # XYZ bounding box & axes
        self.show_collars: bool = True        # Collar marker discs
        self.show_labels: bool = True         # Borehole ID labels
        self.show_legend: bool = True         # Floating in-canvas 3D legend

        # v2.9.141 — relief (P2) : isocontours + grille drapée sur la surface
        # (réglages INTERNES, plus exposés dans le panneau).
        self.show_contours: bool = False      # Isocontours — retirés (retour écran)
        self.show_grid_drape: bool = False    # Grille X/Y drapée sur le relief

        # v2.9.141 — surface 3D réelle (P1) : grille (X, Y) fournie par le
        # widget (échantillonnage MNT raster / CSV / repli collets).
        self._surface_grid: Optional[list] = None   # lignes de (x, y, z)
        self._surface_source: str = ""              # "dem" | "csv" | "collars"

        self.stroke_width: float = 10.0       # Default thickness 10 px
        # v2.9.263 E3 — largeur (px écran) du plan texturé Imagerie posé
        # le long de la trajectoire.  Pas de piste gauche/droite en 3D :
        # c'est l'épaisseur du ruban photo, pas un décalage de voie.
        self._imagery_3d_width: float = 12.0
        # v2.9.141 — surface 3D OPAQUE par défaut (plus de transparence
        # « bricolée » qui laissait voir les forages au travers).
        self.terrain_opacity_pct: int = 100   # Topography ground opacity
        self.tube_opacity_pct: int = 95       # Borehole tube opacity

        # Scope filter: "all", "section", "selection"
        self.scope_mode: str = "all"

        # Data references
        self._drillholes: list[DrillHole] = []
        self._section_hole_ids: set[str] = set()
        self._active_section_line: Optional[Any] = None
        self._active_section_buffer: float = 20.0
        self.style_resolver: Optional[Any] = None
        self._project_ref: Optional[Any] = None

        # Selection & Highlight state
        self._selected_hole_id: Optional[str] = None
        # v2.9.165 — sélection MULTIPLE depuis la carte QGIS : TOUS les
        # forages sélectionnés (le dernier = _selected_hole_id).
        self._selected_hole_ids: list[str] = []
        self._selected_from_m: Optional[float] = None
        self._selected_to_m: Optional[float] = None
        self._highlight_code: Optional[str] = None

        # Hover state
        self._hover_text: Optional[str] = None
        self._hover_pos: Optional[QPoint] = None

        # Diagnostics
        self.displayed_holes_count: int = 0
        self.ignored_holes_count: int = 0

        # Mouse interaction tracking
        self._mouse_press_pos: Optional[QPoint] = None
        self._mouse_button: Optional[Qt.MouseButton] = None
        self._is_dragging: bool = False
        # v2.9.245 — ZOOM MOLETTE = MOUVEMENT (retour écran : « au zoom
        # et dézoom de 3D c'est grave lent »).  Le LOD d'orbite
        # (v2.9.175) regardait ``_is_dragging``, jamais posé par la
        # molette : chaque cran repeignait la scène en détail COMPLET.
        # Drapeau + minuterie single-shot redémarrée à chaque cran (voir
        # ``_begin_wheel_motion``) : la frame est allégée pendant le
        # défilement, le détail complet revient ~150 ms après le
        # DERNIER cran — exactement le cycle orbite → relâchement.
        self._wheel_motion: bool = False

        # Hit test segment registry: list of (p1_screen, p2_screen, depth_avg, hole_id, from_m, to_m, tip_text)
        self._hit_segments: list[tuple[QPointF, QPointF, float, str, float, float, str]] = []

        # v2.9.263 — badges Imagerie 3D : clic → photo en grand.
        # Liste de (centre QPointF, rayon, hole_id, from_m, to_m, record).
        self._imagery_badge_hits: list[tuple] = []

        # Floating legend clickable rectangles: list of (QRectF, code_or_text)
        self._legend_rects: list[tuple[QRectF, str]] = []

        # ------------------------------------------------------------------
        # Seamless Floating In-Canvas Controls (Top-Left Camera, Top-Right Tools)
        # ------------------------------------------------------------------
        # 1. Floating Camera preset dropdown in top-left
        self.floating_cam_widget = QFrame(self)
        self.floating_cam_widget.setObjectName("FloatingCamWidget")
        # v2.9.141 — translucide : on voit la scène à travers, le contrôle
        # ne « mange » plus le canvas.
        self.floating_cam_widget.setStyleSheet("""
            QFrame#FloatingCamWidget {
                background-color: rgba(23, 29, 34, 170);
                border: 1px solid rgba(52, 73, 94, 220);
                border-radius: 4px;
                padding: 2px 3px;
            }
            QComboBox {
                background-color: rgba(211, 110, 40, 190);
                color: #FFFFFF;
                border: 1px solid rgba(230, 126, 34, 230);
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 7pt;
                font-weight: bold;
            }
            QComboBox:hover {
                background-color: #E67E22;
                border-color: #D35400;
            }
            QComboBox::drop-down {
                border: none;
                width: 14px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #ECF0F1;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #171D22;
                color: #FFFFFF;
                selection-background-color: #5D6D7E;
                border: 1px solid #34495E;
            }
        """)
        cam_l = QHBoxLayout(self.floating_cam_widget)
        cam_l.setContentsMargins(1, 1, 1, 1)
        cam_l.setSpacing(0)
        self.combo_cam = QComboBox(self.floating_cam_widget)
        self.combo_cam.addItem(_tr("⚂ Iso"), (45, 30))
        self.combo_cam.addItem(_tr("⯅ Dessus"), (0, 89))
        self.combo_cam.addItem(_tr("⯈ Face"), (0, 0))
        self.combo_cam.addItem(_tr("⯈ Profil"), (90, 0))
        self.combo_cam.currentIndexChanged.connect(self._on_cam_combo_changed)
        cam_l.addWidget(self.combo_cam)

        # 2. Floating Tools group in top-right
        self.floating_tools_widget = QFrame(self)
        self.floating_tools_widget.setObjectName("FloatingToolsWidget")
        self.floating_tools_widget.setStyleSheet("""
            QFrame#FloatingToolsWidget {
                background-color: rgba(23, 29, 34, 120);
                border: 1px solid rgba(52, 73, 94, 180);
                border-radius: 4px;
                padding: 2px 4px;
            }
            QPushButton {
                background-color: rgba(211, 110, 40, 150);
                color: #FFFFFF;
                border: 1px solid rgba(230, 126, 34, 200);
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 8pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E67E22;
                border-color: #D35400;
                color: #FFFFFF;
            }
        """)
        tools_l = QHBoxLayout(self.floating_tools_widget)
        tools_l.setContentsMargins(2, 2, 2, 2)
        tools_l.setSpacing(6)
        # v2.9.141 — boutons en icône seule (gain de place) ; l'infobulle
        # au survol porte le libellé complet.
        self.btn_zoom_all = QPushButton("⛶", self.floating_tools_widget)
        self.btn_zoom_all.setToolTip(_tr("Recadrer — ajuster la caméra sur l’emprise de tous les forages"))
        self.btn_zoom_all.clicked.connect(self.reset_to_extents)
        tools_l.addWidget(self.btn_zoom_all)

        self.btn_center_sel = QPushButton("🎯", self.floating_tools_widget)
        self.btn_center_sel.setToolTip(_tr("Sélection — centrer la vue sur l’intervalle sélectionné"))
        self.btn_center_sel.clicked.connect(self.center_on_selection)
        tools_l.addWidget(self.btn_center_sel)

        # v2.9.177 — bouton AIDE (retour écran : « ya pas d'aide dans la
        # vue 3D — comment l'utilisateur saura que le multidomaine
        # n'existe qu'en coupe active/sélection ? »).
        self.btn_help = QPushButton("❓", self.floating_tools_widget)
        self.btn_help.setToolTip(
            _tr("Aide de la vue 3D — navigation, portées, domaines simultanés, légende"))
        self.btn_help.clicked.connect(self.show_help)
        tools_l.addWidget(self.btn_help)

        # Subscribe to workspace selection
        self.workspace_state.subscribe("selected_interval", self._on_workspace_interval_selected)
        self.workspace_state.subscribe("selected_hole_id", self._on_workspace_hole_selected)
        # v2.9.165 — sélection multiple depuis la carte QGIS
        self.workspace_state.subscribe("selected_hole_ids", self._on_workspace_holes_selected)
        self.workspace_state.subscribe("highlight_code", self._on_workspace_highlight_code)


    def show_help(self):
        """v2.9.177 — aide de la vue 3D (une page, concise)."""
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.information(
            self, self.tr("Aide — Vue 3D"), self.tr(HELP_3D_TEXT))

    # ------------------------------------------------------------------
    # v2.9.166 — DOMAINES MULTIPLES : propriétés (au niveau CLASSE,
    # après __init__ — avant, elles coupaient __init__ en deux et
    # empêchaient la création des widgets flottants, bug v2.9.167).
    # ------------------------------------------------------------------
    @property
    def geo_domain(self) -> str:
        """Domaine PRINCIPAL (le premier actif) — rétrocompat."""
        return self._active_domains[0] if self._active_domains else "litho"

    @geo_domain.setter
    def geo_domain(self, value: str):
        """Setter rétrocompat : remplace la liste par un domaine seul."""
        if value:
            self._active_domains = [value]

    @property
    def active_domains(self) -> list[str]:
        """TOUS les domaines actifs (ordre : principal d'abord)."""
        return list(self._active_domains)

    @active_domains.setter
    def active_domains(self, domains):
        """Définit la liste des domaines actifs (au moins un)."""
        clean = [d for d in (domains or []) if d and d != "trajectory"]
        if not clean:
            clean = ["litho"]
        self._active_domains = clean[:5]  # plafond : 5 domaines simultanés

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cam_hint = self.floating_cam_widget.sizeHint()
        self.floating_cam_widget.setGeometry(10, 10, max(80, cam_hint.width()), max(22, cam_hint.height()))
        self.floating_cam_widget.raise_()

        tools_hint = self.floating_tools_widget.sizeHint()
        self.floating_tools_widget.setGeometry(
            self.width() - tools_hint.width() - 12, 12,
            tools_hint.width(), max(28, tools_hint.height()),
        )
        self.floating_tools_widget.raise_()

    def _on_cam_combo_changed(self, idx: int):
        data = self.combo_cam.itemData(idx)
        if data and isinstance(data, (tuple, list)) and len(data) == 2:
            self.set_view_preset(data[0], data[1])

    def _clear_cam_preset(self):
        """v2.9.141 — une orbite manuelle n'est plus une vue prédéfinie.

        Quand l'utilisateur fait tourner la caméra à la souris, l'angle
        ne correspond plus à aucun preset : on désélectionne le combo
        (plus de « Vue Dessus » qui reste affiché alors que la caméra a
        bougé).
        """
        try:
            self.combo_cam.blockSignals(True)
            self.combo_cam.setCurrentIndex(-1)
            self.combo_cam.blockSignals(False)
        except (RuntimeError, AttributeError):
            # combo pas encore construit (C++ supprimé / attribut absent)
            # — rien à faire : le preset sera resynchronisé au prochain
            # paint ; SILENCE JUSTIFIÉ (état transitoire du boot).
            pass

    # ------------------------------------------------------------------
    # Data & Context Updates
    # ------------------------------------------------------------------
    def set_drillholes(self, drillholes: list[DrillHole], style_resolver=None, project=None):
        # v2.9.189 — invalide le cache de scène (données/coupe changées)
        self._scene_rev = getattr(self, "_scene_rev", 0) + 1
        """Load drillholes from SpatialModel into the 3D viewport.

        v2.9.141 — ne recadre (reset_to_extents) QUE si le jeu de forages
        a réellement changé. Sinon, revenir sur l'onglet 3D (sync_with_
        project au changement d'onglet) remettait la caméra à zéro et
        perdait l'orbite / le zoom / le pan de l'utilisateur.
        """
        self._drillholes = list(drillholes or [])
        self.style_resolver = style_resolver
        self._project_ref = project
        # v2.9.145 (volet 1, D1-1) — le résolveur partagé suit le projet
        # (couleur/libellé/code court = même source que la coupe 2D).
        self._style.set_project(project)
        signature = tuple(sorted(d.hole_id for d in self._drillholes))
        if signature != getattr(self, "_drillholes_sig", None):
            self._drillholes_sig = signature
            self.reset_to_extents()
        self.recompute_assay_scale(project=project)
        self.update()

    def set_surface_grid(self, grid, source: str = ""):
        # v2.9.189 — invalide le cache de scène (données/coupe changées)
        self._scene_rev = getattr(self, "_scene_rev", 0) + 1
        """v2.9.141 (P1) — remplace la surface interpolée aux collets par la
        grille réelle échantillonnée (MNT raster / CSV), ou la grille collets
        en repli.  ``grid`` = lignes de ``(x, y, z)`` (core.topography).
        """
        self._surface_grid = grid
        self._surface_source = str(source or "")
        self.update()

    def set_active_section(self, section_line, buffer_val: float = 20.0, section_holes: Optional[list[str]] = None):
        # v2.9.189 — invalide le cache de scène (données/coupe changées)
        self._scene_rev = getattr(self, "_scene_rev", 0) + 1
        """Set the active 2D section line and its corridor for 3D display."""
        self._active_section_line = section_line
        self._active_section_buffer = float(buffer_val)
        self._section_hole_ids = set(section_holes or [])
        self.update()

    def get_available_assay_elements(self) -> list[str]:
        """Extract all available numeric assay element names across loaded drillholes."""
        elems = set()
        for dh in self._drillholes:
            for iv in dh.assays:
                for k, v in iv.attributes.items():
                    if k not in ("hole_id", "from", "to", "lithology", "alteration", "intensity", "style", "minerals"):
                        try:
                            float(str(v).replace(",", "."))
                            elems.add(k)
                        except (TypeError, ValueError):
                            # Valeur non numérique ignorée pour les analyses
                            pass
        return sorted(elems)

    def active_assay_elements(self) -> list[str]:
        """Éléments teneurs réellement affichés (v2.9.143).

        - ``assay_display_elements`` vide → miroir de la coupe 2D : les
          1–3 éléments du style projet (``_assay_elements``) ;
        - sinon → les éléments COCHÉS dans le combo 3D (1 à 3, choisis
          directement en 3D — plus besoin d'aller en 2D pour afficher
          plusieurs éléments simultanément).
        """
        if self.assay_display_elements:
            return list(self.assay_display_elements)
        return [e for e in (self._assay_elements or [self.active_assay_element]) if e]

    def sync_assay_elements(self, project) -> str:
        """v2.9.172 — synchronise les éléments teneurs depuis le projet.

        Extrait de ``ui/view_3d.py`` (SPEC : le widget d'assemblage reste
        mince) : éléments affichables (miroir de la coupe 2D ou choix 1–3
        conservé d'une synchronisation à l'autre — v2.9.142/143), élément
        actif, échelles.  Retourne le libellé « miroir » du résumé.
        """
        elems = self.get_available_assay_elements()
        style_elems = []
        if hasattr(project, "get_assay_style"):
            try:
                from ..core.multi_assay import normalize_elements
                style_elems = normalize_elements(
                    (project.get_assay_style() or {}).get("elements"))
            except Exception as exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Vue 3D : lecture des éléments du style de "
                              "teneurs (repli miroir)", exc)
                style_elems = []
        prev_display = [e for e in (self.assay_display_elements or [])
                        if e in set(elems)]
        if not elems:
            prev_display = []
        self.assay_display_elements = prev_display
        n_el = len(style_elems)
        mirror = (_tr("Comme la coupe 2D ({0} élément{1})")
                  .format(n_el, "s" if n_el > 1 else "")
                  if n_el else _tr("Comme la coupe 2D"))
        if elems:
            pref_elem = None
            if hasattr(project, "get_assay_style"):
                try:
                    pref_elem = project.get_assay_style().get("element")
                except Exception as exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Vue 3D : lecture de l'élément préféré "
                                  "du style de teneurs", exc)
                    pref_elem = None
            self.active_assay_element = (
                pref_elem if (pref_elem and pref_elem in elems) else elems[0])
            self.recompute_assay_scale(project=project)
        return mirror

    def recompute_assay_scale(self, project=None):
        """Calculate quantitative assay color breaks matching 2D project style."""
        proj = project or self._project_ref
        if not self.active_assay_element:
            elems = self.get_available_assay_elements()
            if elems:
                self.active_assay_element = elems[0]
            else:
                self._assay_scale = None
                return

        elem = self.active_assay_element
        values: list[float] = []
        for dh in self._drillholes:
            for iv in dh.assays:
                val = iv.attributes.get(elem)
                if val is not None:
                    try:
                        v = float(str(val).replace(",", "."))
                        if math.isfinite(v):
                            values.append(v)
                    except (TypeError, ValueError):
                        # Valeur analytique invalide ignorée
                        pass

        if not values:
            self._assay_scale = None
            return

        proj_style = {}
        if proj and hasattr(proj, "get_assay_style"):
            try:
                proj_style = proj.get_assay_style() or {}
            except Exception as exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Vue 3D : lecture du style de teneurs du "
                              "projet (repli : valeurs par défaut)", exc)

        method = proj_style.get("method") or "jenks"
        n_classes = int(proj_style.get("n_classes") or 5)
        manual_breaks = proj_style.get("manual_breaks")
        round_breaks = bool(proj_style.get("round_breaks", True))
        self.assay_palette = proj_style.get("palette") or "grade"

        # v2.9.141 — multi-teneurs + règles de seuil, lus depuis le MÊME style
        # que la coupe 2D (source unique).
        try:
            from ..core.multi_assay import normalize_elements
            self._assay_elements = normalize_elements(
                proj_style.get("elements") or ([self.active_assay_element]
                                               if self.active_assay_element else []))
        except Exception as exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : normalisation des éléments de teneurs "
                          "(repli : élément actif seul)", exc)
            self._assay_elements = [self.active_assay_element] if self.active_assay_element else []
        self._assay_element_palettes = dict(proj_style.get("element_palettes") or {})
        try:
            from ..core.threshold_rule import normalize_rules
            self._threshold_rules = normalize_rules(proj_style.get("threshold_rules"))
        except Exception as exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : normalisation des règles de seuil "
                          "(repli : aucune règle)", exc)
            self._threshold_rules = []

        # Échelles par élément (chaque élément a sa propre échelle + rampe).
        # v2.9.143 — couvre AUSSI les éléments cochés dans le combo 3D
        # (ils peuvent être hors liste du style 2D).
        self._assay_scales = {}
        scale_elems = list(self._assay_elements)
        for el in self.assay_display_elements:
            if el and el not in scale_elems:
                scale_elems.append(el)
        for el in scale_elems:
            values = []
            for dh in self._drillholes:
                for iv in dh.assays:
                    v = iv.attributes.get(el)
                    if v is not None:
                        try:
                            vv = float(str(v).replace(",", "."))
                            if math.isfinite(vv):
                                values.append(vv)
                        except (TypeError, ValueError):
                            pass  # valeur analytique non numérique ignorée
            if not values:
                continue
            try:
                self._assay_scales[el] = compute_assay_scale(
                    values, method=method, n_classes=n_classes,
                    manual_breaks=manual_breaks, round_breaks=round_breaks,
                )
            except Exception as _scale_exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed(f"Vue 3D : échelle Jenks de l'élément {el} "
                              f"(repli : linéaire min–max)", _scale_exc)
                vmin, vmax = min(values), max(values)
                if vmax <= vmin:
                    vmax = vmin + 1.0
                step = (vmax - vmin) / max(1, n_classes)
                self._assay_scales[el] = {
                    "method": "linear", "n_classes": n_classes,
                    "vmin": vmin, "vmax": vmax,
                    "boundaries": [vmin + i * step for i in range(n_classes + 1)],
                }
        # Échelle du 1er élément (rétrocompat + légende) — ou du 1er
        # élément coché dans le combo 3D (v2.9.143).
        first = (self.assay_display_elements[0] if self.assay_display_elements
                 else (self._assay_elements[0] if self._assay_elements else ""))
        if first:
            self._assay_scale = self._assay_scales.get(first)

    def _on_workspace_interval_selected(self, interval_data):
        if not interval_data:
            self._selected_hole_id = None
            self._selected_from_m = None
            self._selected_to_m = None
        else:
            self._selected_hole_id = interval_data.get("hole_id")
            self._selected_from_m = float(interval_data.get("from_m", interval_data.get("from", 0.0)))
            self._selected_to_m = float(interval_data.get("to_m", interval_data.get("to", 0.0)))
        self.update()

    def _on_workspace_holes_selected(self, hole_ids):
        """v2.9.165 — sélection MULTIPLE depuis la carte QGIS."""
        self._selected_hole_ids = [str(h) for h in (hole_ids or []) if h]
        self.update()

    def _on_workspace_hole_selected(self, hole_id):
        if not self._selected_from_m:
            self._selected_hole_id = hole_id
            self.update()

    def _on_workspace_highlight_code(self, code):
        self._highlight_code = code if code else None
        self.update()

    # ------------------------------------------------------------------
    # Camera Navigation & Presets
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # v2.9.145 — propriétés caméra déléguées à core/camera3d.OrbitCamera
    # (mêmes noms qu'avant : aucun appelant ne change).
    # ------------------------------------------------------------------
    @property
    def yaw_deg(self) -> float:
        return self.camera.yaw_deg

    @yaw_deg.setter
    def yaw_deg(self, value: float):
        self.camera.yaw_deg = value

    @property
    def pitch_deg(self) -> float:
        return self.camera.pitch_deg

    @pitch_deg.setter
    def pitch_deg(self, value: float):
        self.camera.pitch_deg = value

    @property
    def zoom(self) -> float:
        return self.camera.zoom

    @zoom.setter
    def zoom(self, value: float):
        self.camera.zoom = value

    @property
    def pan_x(self) -> float:
        return self.camera.pan_x

    @pan_x.setter
    def pan_x(self, value: float):
        self.camera.pan_x = value

    @property
    def pan_y(self) -> float:
        return self.camera.pan_y

    @pan_y.setter
    def pan_y(self, value: float):
        self.camera.pan_y = value

    @property
    def v_exag(self) -> float:
        return self.camera.v_exag

    @v_exag.setter
    def v_exag(self, value: float):
        self.camera.v_exag = value

    @property
    def pivot(self) -> tuple[float, float, float]:
        return self.camera.pivot

    @pivot.setter
    def pivot(self, value: tuple[float, float, float]):
        self.camera.pivot = value

    def sync_exag_from_2d(self, canvas_2d, widget=None):
        """v2.9.317 — exagération 2D PARTAGÉE vers la 3D : la vue 3D
        s'aligne sur la coupe ; un réglage manuel 3D prime ensuite."""
        try:
            exag_2d = float(getattr(canvas_2d, "_v_exag", 0.0) or 0.0)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : synchro exag 2D", _exc)
            exag_2d = 0.0
        if (exag_2d > 0.01
                and not getattr(self, "_exag_user_touched", False)
                and abs(float(self.v_exag) - exag_2d) > 0.01):
            self.v_exag = exag_2d
            spin = getattr(widget, "spin_exag_side", None)
            if spin is not None:
                spin.blockSignals(True)
                spin.setValue(exag_2d)
                spin.blockSignals(False)

    def set_view_preset(self, yaw: float, pitch: float):
        """Set camera orientation angles directly."""
        self.camera.set_view_preset(yaw, pitch)
        self.update()

    def reset_to_extents(self):
        """Re-center camera pivot on the data bounding box and adjust zoom."""
        min_x, max_x, min_y, max_y, min_z, max_z = self._get_bounds()
        self.pivot = (
            (min_x + max_x) / 2.0,
            (min_y + max_y) / 2.0,
            (min_z + max_z) / 2.0,
        )
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def center_on_selection(self):
        """Center the rotation pivot on the currently selected interval."""
        if not self._selected_hole_id:
            return
        dh = next((d for d in self._drillholes if d.hole_id == self._selected_hole_id), None)
        if not dh or not dh.trajectory:
            return
        mid_depth = (
            (self._selected_from_m + self._selected_to_m) / 2.0
            if (self._selected_from_m is not None and self._selected_to_m is not None)
            else (dh.collar.max_depth / 2.0 if dh.collar else 0.0)
        )
        pt = self._interpolate_dh_point(dh, mid_depth)
        if pt:
            self.pivot = (pt.x, pt.y, pt.z)
            self.pan_x = 0.0
            self.pan_y = 0.0
            self.update()

    # ------------------------------------------------------------------
    # 3D Math & Projection Pipeline (Exact World Coordinates)
    # ------------------------------------------------------------------
    def _get_bounds(self) -> tuple[float, float, float, float, float, float]:
        """Compute real-world bounding box (min_x, max_x, min_y, max_y, min_z, max_z)."""
        valid_holes = [dh for dh in self._get_visible_drillholes() if dh.trajectory]
        if not valid_holes:
            return (-50.0, 50.0, -50.0, 50.0, -50.0, 50.0)

        xs, ys, zs = [], [], []
        for dh in valid_holes:
            if dh.collar:
                xs.append(dh.collar.x)
                ys.append(dh.collar.y)
                zs.append(dh.collar.z)
            for pt in dh.trajectory:
                if math.isfinite(pt.x) and math.isfinite(pt.y) and math.isfinite(pt.z):
                    xs.append(pt.x)
                    ys.append(pt.y)
                    zs.append(pt.z)

        if not xs:
            return (-50.0, 50.0, -50.0, 50.0, -50.0, 50.0)
        return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

    def imagery_status_snippet(self, translate) -> str:
        """Résumé imagerie pour la barre de statut (vide si hors sujet).

        v2.9.263 — diagnostic « X/Y images par forage » : distingue
        immédiatement « 0 donnée / à recharger » (records = 0) de
        « donnée présente mais non affichée » (rendered < records).
        Générique : aucun nom de forage / plage / organisation n'est
        supposé.
        """
        if "imagery" not in (self.active_domains or []):
            return ""
        diag = getattr(self, "_imagery_diag", None) or {}
        if not diag:
            return translate("Imagerie : 0 image affichée")
        parts = []
        for hid in sorted(diag):
            row = diag[hid]
            loaded = row.get("loaded", 0)
            records = row.get("records", 0)
            part = f"{hid} {loaded}/{records}"
            if loaded < records:
                # Code de cause, générique et compact : D=intervalle
                # dégénéré (aucun point 3D/plage nulle), M=fichier
                # manquant, U=illisible, S=sautée par culling.
                flags = []
                _deg = (row.get("no_point", 0) + row.get("zero_len", 0))
                if _deg:
                    flags.append(f"{_deg}D")
                if row.get("missing", 0):
                    flags.append(f"{row.get('missing', 0)}M")
                if row.get("unreadable", 0):
                    flags.append(f"{row.get('unreadable', 0)}U")
                if row.get("skipped_culling", 0):
                    flags.append(f"{row.get('skipped_culling', 0)}S")
                if flags:
                    part += f" ({', '.join(flags)})"
            parts.append(part)
        total_records = sum(row.get("records", 0) for row in diag.values())
        return translate(
            "Imagerie : {} forage(s), {} image(s) — {}").format(
                len(diag), total_records, " · ".join(parts))

    def _get_visible_drillholes(self) -> list[DrillHole]:
        """Filter drillholes according to the active scope."""
        if self.scope_mode == "section":
            return [dh for dh in self._drillholes if dh.hole_id in self._section_hole_ids]
        elif self.scope_mode == "selection":
            # v2.9.165 — sélection MULTIPLE : tous les forages choisis
            # sur la carte QGIS (avant : seulement le dernier).
            if self._selected_hole_ids:
                ids = set(self._selected_hole_ids)
                return [dh for dh in self._drillholes if dh.hole_id in ids]
            return [dh for dh in self._drillholes if dh.hole_id == self._selected_hole_id]
        return self._drillholes

    def _setup_frame(self, scale: float):
        """Précalcule la transformation caméra UNE FOIS par frame.

        v2.9.145 (volet 1) — les maths vivent dans
        ``core/camera3d.OrbitCamera.setup_frame`` (pur, zéro Qt) ; cette
        méthode reste le point d'entrée historique du canvas (elle
        remplissait ``_fc_*`` depuis v2.9.141 quand ``project_3d`` les
        recalculait par point).
        """
        self.camera.setup_frame(scale, self.width(), self.height())
        # Compat _fc_* : certains lecteurs internes y accèdent encore
        # (gizmo, diagnostics) — miroir de l'état caméra.
        self._fc_cx = self.camera._fc_cx
        self._fc_cy = self.camera._fc_cy
        self._fc_cz = self.camera._fc_cz
        self._fc_scale = self.camera._fc_scale
        self._fc_hw = self.camera._fc_hw
        self._fc_hh = self.camera._fc_hh
        self._fc_v_exag = self.camera._fc_v_exag

    def project_3d(
        self,
        x: float, y: float, z: float,
        scale: float,
    ) -> tuple[float, float, float]:
        """Project real-world (X, Y, Z) to 2D viewport coordinates + camera depth.

        RÈGLE ABSOLUE:
        x, y, z are the unmodified source coordinates.
        Vertical exaggeration (v_exag) scales only the relative Z offset for rendering.

        v2.9.145 — délègue à ``OrbitCamera.project`` (core/camera3d).
        """
        return self.camera.project(x, y, z, scale,
                                   self.width(), self.height())

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        """Peint la scène — délégué au renderer (v2.9.148).

        v2.9.195 — BLINDAGE ANTI-GEF (retour écran : « le plugin a
        buggé quand je suis allé en 3D, j'ai dû sortir de QGIS »).
        Une exception dans un paintEvent Qt se RÉPÈTE à l'infini
        (repaint → exception → repaint) : QGIS gèle et seul un
        redémarrage s'en sort.  Désormais : l'exception est capturée,
        JOURNALISÉE UNE FOIS (traceback complet dans le journal de
        diagnostic), et on peint un message d'erreur lisible au lieu
        de relancer la boucle.  Le drapeau retombe quand la scène
        change (nouvelle donnée/caméra), un bug passager se
        rétablit donc tout seul.
        """
        try:
            from .view_3d_renderer import paint_scene
            paint_scene(self, event)
            self._paint_failed = False
        except Exception as _exc:
            if not getattr(self, "_paint_failed", False):
                self._paint_failed = True
                # UNE fois seulement : le traceback COMPLET va dans le
                # journal (catégorie DrillMaster) pour diagnostic.
                from ..core.diagnostics import log_swallowed
                from traceback import format_exc
                log_swallowed(
                    "Vue 3D : rendu échoué (journalisé UNE fois, "
                    "message affiché dans la vue pour éviter le gel "
                    "de QGIS) — traceback : %s" % format_exc(), _exc)
            from qgis.PyQt.QtGui import QColor, QPainter, QPen
            from qgis.PyQt.QtCore import Qt
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor("#171D22"))
            painter.setPen(QPen(QColor("#E74C3C"), 1))
            from qgis.PyQt.QtGui import QFont
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                _tr("Vue 3D : erreur de rendu.\n"
                        "Changez la caméra ou rouvrez l'onglet pour "
                        "réessayer.\nLe détail est dans le journal de "
                        "diagnostic (onglet Journaux de QGIS, catégorie "
                        "DrillMaster)."))
            painter.end()

    def closeEvent(self, event):
        """v2.9.319 (§2.4) — arrête proprement le worker asynchrone.

        Un QThread encore vivant à la destruction du widget = crash au
        fermeture de QGIS (surtout sous Windows : « QThread: Destroyed
        while thread is still running »).  On déconnecte le signal
        (plus d'adoption sur un widget mourant), on demande l'arrêt et
        on attend — borné à 3 s, jamais de blocage infini.
        """
        worker = getattr(self, "_async_worker", None)
        if worker is not None:
            self._async_worker = None
            try:
                worker.scene_ready.disconnect()
            except Exception as _exc:  # noqa: BLE001 — jamais bloquant
                from ..core.diagnostics import log_swallowed
                log_swallowed("Vue 3D : déconnexion du worker de "
                              "rendu à la fermeture", _exc)
            try:
                worker.requestInterruption()
                worker.wait(3000)
            except Exception as _exc:  # noqa: BLE001 — jamais bloquant
                from ..core.diagnostics import log_swallowed
                log_swallowed("Vue 3D : arrêt du worker de rendu à la "
                              "fermeture", _exc)
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # 3D Topographic Ground Surface with Hillshade (P1/P2)
    # ------------------------------------------------------------------
    @staticmethod
    def _hypsometric_color(t: float) -> tuple[int, int, int]:
        """Teinte hypsométrique : vert/brun en bas → pâle en haut.

        ``t`` ∈ [0, 1] (altitude normalisée).  Rendu minier/géo classique.
        """
        t = max(0.0, min(1.0, t))
        # v2.9.141 — palette plus lumineuse (le bas ne doit pas virer au noir).
        stops = ((0.0, (128, 148, 92)), (0.5, (170, 156, 112)),
                 (1.0, (238, 232, 216)))
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                return tuple(int(c0[k] + (c1[k] - c0[k]) * u) for k in range(3))
        return stops[-1][1]

    def _surface_contours(self, grid_3d, zmin: float, zmax: float):
        """Segments d'isocontours (niveaux auto) sur la grille, mis en cache."""
        key = (id(grid_3d), round(zmin, 3), round(zmax, 3))
        if getattr(self, "_contour_cache_key", None) == key:
            return self._contour_cache
        levels = contour_levels(zmin, zmax)
        segs = contour_segments(grid_3d, levels) if levels else {}
        self._contour_cache_key = key
        self._contour_cache = segs
        return segs

    def _draw_topography_surface(self, painter, min_x, max_x, min_y, max_y, scale):
        """Surface MNT — déléguée au renderer (v2.9.148)."""
        from .view_3d_renderer import draw_topography_surface
        draw_topography_surface(self, painter, min_x, max_x, min_y, max_y, scale)
    def _draw_bounding_box(self, painter, min_x, max_x, min_y, max_y, min_z, max_z, scale):
        """Boîte + graduations XYZ — déléguée au renderer (v2.9.148)."""
        from .view_3d_renderer import draw_bounding_box
        draw_bounding_box(self, painter, min_x, max_x, min_y, max_y, min_z, max_z, scale)
    def _draw_section_plane_and_corridor(self, painter, min_z, max_z, scale):
        """Plan de coupe + corridor — délégués au renderer (v2.9.148)."""
        from .view_3d_renderer import draw_section_plane_and_corridor
        draw_section_plane_and_corridor(self, painter, min_z, max_z, scale)
    def _resolve_code_color(self, code: str, domain: str) -> QColor:
        """Couleur exacte du Référentiel — via le résolveur PARTAGÉ
        (v2.9.145, volet 1/D1-1 : ``core/style_resolver``), même chemin que
        la coupe 2D.  Plus de cartes de couleurs privées ici."""
        return QColor(self._style.code_color(code, domain))

    def _resolve_code_label(self, code: str, domain: str) -> str:
        """Libellé résolu du Référentiel (ex. « Hématisation » pour HEM),
        repli sur le code brut.  Sert à la légende 3D (affichage + survol)."""
        return self._style.code_label(code, domain)

    def _short_code(self, code: str, domain: str) -> str:
        """Code COURT affiché en légende — via le résolveur PARTAGÉ
        (``core/style_resolver.StyleResolver.short_code``), même convention
        que la coupe 2D (minéralisations → 2 lettres, altérations →
        segments de 3, teneurs → libellé numérique tel quel)."""
        return self._style.short_code(code, domain)

    def _resolve_domain_color(self, inv: IntervalRecord, domain: str) -> QColor:
        """Resolve interval color strictly according to the project's official referential."""
        if domain == "assays":
            elem = self.active_assay_element
            val_raw = inv.attributes.get(elem) if elem else None
            if val_raw is None and inv.attributes:
                elem = next(iter(inv.attributes.keys()))
                val_raw = inv.attributes.get(elem)
            if val_raw is not None:
                try:
                    v = float(str(val_raw).replace(",", "."))
                    if math.isfinite(v):
                        if self._assay_scale:
                            _, frac = classify_assay(v, self._assay_scale)
                            hex_c = assay_ramp_rgb(frac, self.assay_palette)
                            return QColor(hex_c)
                        else:
                            return QColor("#E67E22")
                except (TypeError, ValueError):
                    return QColor("#7F8C8D")
            return QColor("#7F8C8D")

        code = self._extract_code_from_interval(inv, domain)
        return self._resolve_code_color(code, domain)

    def _interval_codes(self, inv: IntervalRecord, domain: str) -> list[str]:
        """v2.9.141 — TOUS les codes d'un intervalle, même logique que la coupe 2D.

        En minéralisations « organisation large » (colonnes Style_1/_2),
        les styles vivent dans les composants (marque ``_wide_styles``) :
        la vue 3D ne lisait que ``components[0]`` et perdait les styles
        suivants (2 en 3D contre 4 en 2D).  Cette fonction renvoie la
        liste complète, comme :meth:`SectionCanvas._interval_codes`.

        v2.9.172 — teneurs/intercepts : ``[]`` EXPLICITE.  Avant, le
        domaine tombait dans la branche litho et renvoyait des CODES DE
        LITHOLOGIE prélevés sur des passes d'analyses — la légende
        multi-domaines affichait alors du « granite » dans le groupe
        « Teneurs » (retour écran : « je vois des mélanges »).
        """
        if domain in ("assays", "intercepts"):
            return []  # pas des codes : rampe de teneurs / règles de seuil
        if domain == "mineralizations":
            # v2.9.154 — source UNIQUE partagée (core/mesh_builder),
            # verrouillée par test : jusqu'à 4 styles lus, comme la 2D.
            from ..core.mesh_builder import mineralization_style_codes
            return mineralization_style_codes(inv)
        if domain == "alterations":
            if inv.components:
                codes = [c.raw_code for c in inv.components if c.raw_code]
                if codes:
                    return [str(c).strip() for c in codes]
            value = (
                inv.attributes.get("alteration")
                or inv.attributes.get("alteration_type")
                or inv.attributes.get("alt")
            )
            return [str(value).strip()] if value not in (None, "") else []
        # litho : composants (primaire + secondaires)
        if inv.components:
            return [str(c.raw_code).strip() for c in inv.components if c.raw_code]
        value = inv.attributes.get("lithology")
        return [str(value).strip()] if value not in (None, "") else []

    def _extract_code_from_interval(self, inv: IntervalRecord, domain: str) -> str:
        """Extract domain code robustly, strictly segregating factual styles."""
        if domain == "litho":
            code = inv.attributes.get("lithology")
            if not code and inv.components:
                code = inv.components[0].raw_code
            return str(code or "").strip()
        elif domain == "alterations":
            code = (
                inv.attributes.get("alteration")
                or inv.attributes.get("alteration_type")
                or inv.attributes.get("alt")
                or ""
            )
            if not code and inv.components:
                code = inv.components[0].raw_code
            return str(code).strip()
        elif domain == "mineralizations":
            # Segregation stricte : styles de minéralisation uniquement (pas les espèces de minéraux !)
            code = (
                inv.attributes.get("mineralization_style")
                or inv.attributes.get("style_mineralisation")
                or inv.attributes.get("style")
                or ""
            )
            if not code and inv.components and inv.attributes.get("_wide_styles"):
                code = inv.components[0].raw_code
            return str(code).strip()
        return ""

    def _draw_drillhole(self, painter, dh, scale):
        """Dessin d'un forage — délégué au renderer (v2.9.148)."""
        from .view_3d_renderer import draw_drillhole
        draw_drillhole(self, painter, dh, scale)
    def _interval_intensity_factor(self, inv: IntervalRecord) -> float:
        """Facteur de largeur de tube selon l'intensité d'altération (AM-03).

        Intensité PAR CODE (composant, colonne Int_k) prioritaire, sinon
        intensité d'intervalle ; sans intensité → largeur neutre.
        """
        from ..core.track_bands import intensity_factor
        for c in (inv.components or []):
            if getattr(c, "intensity", ""):
                return intensity_factor(c.intensity)
        raw = inv.attributes.get("intensity") or inv.attributes.get("intensite")
        return intensity_factor(raw)

    def _code_intensity_factor(self, inv: IntervalRecord, code: str) -> float:
        """Intensité d'UN code précis (colonne Int_k), comme la coupe 2D.

        v2.9.141 — chaque code d'un intervalle multi-altérations a SA propre
        intensité (Int_1, Int_2…).  Sans composant apparié → intensité
        d'intervalle ; sinon largeur neutre.
        """
        from ..core.track_bands import intensity_factor
        target = str(code or "").strip().casefold()
        for c in (inv.components or []):
            if str(getattr(c, "raw_code", "") or "").strip().casefold() == target:
                if getattr(c, "intensity", ""):
                    return intensity_factor(c.intensity)
                break
        raw = inv.attributes.get("intensity") or inv.attributes.get("intensite")
        return intensity_factor(raw)

    def _element_value(self, inv: IntervalRecord, element: str) -> Optional[float]:
        """Valeur numérique d'un élément précis sur l'intervalle, ou None."""
        raw = inv.attributes.get(element) if element else None
        if raw is None:
            for k, v in inv.attributes.items():
                if str(k).strip() == str(element).strip():
                    raw = v
                    break
        if raw is None:
            return None
        try:
            v = float(str(raw).replace(",", "."))
            return v if math.isfinite(v) else None
        except (TypeError, ValueError):
            return None

    def _bubble_radius(self, element: str, val: float) -> float:
        """Rayon d'une boule de teneur (PETIT) : 2 → 6 px selon la valeur."""
        scale = self._assay_scales.get(element) or self._assay_scale
        vmin, vmax = 0.0, 1.0
        if scale:
            vmin = float(scale.get("vmin", 0.0))
            vmax = float(scale.get("vmax", 1.0))
        if vmax <= vmin:
            vmax = vmin + 1.0
        t = max(0.0, min(1.0, (val - vmin) / (vmax - vmin)))
        r_min, r_max = 2.0, max(4.0, self.stroke_width * 0.6)
        return r_min + (r_max - r_min) * t

    def _draw_assay_bubble(self, painter, hole_id, inv, el, val, p_top, p_bot,
                           lane=0, n_lanes=1):
        """Boule de teneur — déléguée au renderer (v2.9.148).

        v2.9.186 — FIX CRASH : garde DELG (signatures des délégations).
        v2.9.189 — ``show_label`` retiré : l'étiquette par voie
        chevauchait (voies ~8 px) — remplacée par la légende EMPILÉE
        des éléments (une ligne par élément, sans collision).
        """
        from .view_3d_renderer import draw_assay_bubble
        draw_assay_bubble(self, painter, hole_id, inv, el, val, p_top, p_bot,
                          lane=lane, n_lanes=n_lanes)
    def _threshold_rule_matches(self, rule: dict, inv: IntervalRecord, dh) -> bool:
        """Un intervalle matche-t-il une règle de seuil ? (même module que la 2D)."""
        try:
            from ..core.threshold_rule import interval_matches
            return interval_matches(
                rule, attributes=dict(inv.attributes), hole=dh,
                from_depth=inv.from_depth, to_depth=inv.to_depth)
        except ImportError:
            # module seuil absent (pack réduit) — pas d'intercepts : ce
            # n'est pas un échec de matching, c'est une fonctionnalité
            # absente.  SILENCE JUSTIFIÉ (repli documenté).
            return False

    def _interval_highlight_codes(self, inv: IntervalRecord, domain: str) -> list[str]:
        """Codes (EN MAJUSCULE) portés par un intervalle, pour le filtre par
        code (clic légende).  Même source que la légende, pour que l'estompage
        et la légende restent cohérents.
        """
        if domain == "litho":
            codes = []
            if inv.components:
                codes.extend([c.raw_code.upper() for c in inv.components if c.raw_code])
            if inv.attributes.get("lithology"):
                codes.append(str(inv.attributes["lithology"]).upper())
            return codes
        return [str(c).upper() for c in self._interval_codes(inv, domain)]

    def _get_intervals_for_domain(self, dh: DrillHole, domain: str) -> list[IntervalRecord]:
        if domain == "litho":
            return dh.litho
        elif domain in ("assays", "intercepts"):
            return dh.assays
        elif domain == "alterations":
            return dh.alterations
        elif domain == "mineralizations":
            return dh.mineralizations
        return []

    # ------------------------------------------------------------------
    # v2.9.260 étape 3 — `structure` : mesures PONCTUELLES (Depth), pas
    # des intervalles.  Les helpers ci-dessous restent séparés de la
    # logique d'intervalles (aucune réécriture de l'existant) : la vue
    # 3D lit directement ``dh.structure`` au même titre que les autres
    # domaines.
    # ------------------------------------------------------------------
    @staticmethod
    def _structure_record_code(rec) -> str:
        """Code `type` d'une mesure de structure (repli `structure_type`)."""
        return str(
            getattr(rec, "structure_type", None)
            or getattr(rec, "type", None) or "").strip()

    @staticmethod
    def _structure_records_for_domain(dh: DrillHole, domain: str) -> list:
        """Mesures `structure` d'un forage, ou [] pour les autres domaines."""
        if domain != "structure":
            return []
        return sorted(
            getattr(dh, "structure", None) or [],
            key=lambda rec: float(getattr(rec, "depth", 0.0) or 0.0))

    def _assay_element_color(self, element: str, val: float) -> QColor:
        """Couleur d'une valeur d'élément selon sa rampe + son échelle propre."""
        scale = self._assay_scales.get(element)
        pal = self._assay_element_palettes.get(element) or self.assay_palette
        if scale:
            _, frac = classify_assay(val, scale)
            return QColor(assay_ramp_rgb(frac, pal))
        return QColor("#E67E22")

    def _code_with_label(self, code, domain: str) -> str:
        """v2.9.187 — « GR (Granodiorite) » : code brut + LIBELLÉ du
        Référentiel quand il existe (retour écran : « quand il y a
        plusieurs il spécifie pas, il met litho litho » — le code seul
        ne dit rien au géologue ; le libellé précise qui est qui)."""
        code = str(code or "").strip()
        if not code:
            return code
        try:
            label = str(self._resolve_code_label(code, domain) or "").strip()
        except Exception as _exc:
            # règle de l'audit C : capturé et journalisé (code seul).
            from ..core.diagnostics import log_swallowed
            log_swallowed(f"Vue 3D : libellé du code {code!r} pour "
                          f"l'infobulle (code seul affiché)", _exc)
            label = ""
        if label and label.casefold() != code.casefold():
            return f"{code} ({label})"
        return code

    def _build_tooltip(self, hole_id: str, inv: IntervalRecord, domain: str,
                       short: Optional[bool] = None) -> str:
        domain_title = {
            "litho": _tr("Lithologie"),
            "assays": _tr("Teneur / Analyse"),
            "alterations": _tr("Altération"),
            "mineralizations": _tr("Minéralisation"),
        }.get(domain, _tr("Observation"))

        # v2.9.184 — FORMAT COURT en domaines simultanés (validé) :
        # « DD001 · Altération · 12–45 m · ARG+CHL » — un domaine à la
        # fois, le bon, SANS la liste complète des composants (retour
        # écran : « ça fait beaucoup »).  En domaine seul, l'infobulle
        # riche reste (composants, rôles, intensités, minéraux…).
        if short is None:
            short = len(self.active_domains) > 1
        if short:
            if domain == "assays":
                codes = []
                for _k, _v in (inv.attributes or {}).items():
                    if _k not in ("hole_id", "from", "to") and len(codes) < 2:
                        codes.append(f"{_k} {_v}")
            else:
                codes = list(self._interval_codes(inv, domain))
            tip = (f"{hole_id} · {domain_title} · "
                   f"{inv.from_depth:.1f}–{inv.to_depth:.1f} m")
            if codes:
                tip += " · " + "+".join(str(c) for c in codes)
            return tip

        lines = [
            _tr("Forage : {} [{}]").format(hole_id, domain_title),
            _tr("Passe : {0:.2f} – {1:.2f} m ({2:.2f} m)")
            .format(inv.from_depth, inv.to_depth,
                    inv.to_depth - inv.from_depth),
        ]

        if domain == "litho":
            # v2.9.141 — rôles en français, cohérents avec la coupe 2D
            # (« hôte » et non « primary » brut).
            # v2.9.187 — plus de « Litho : » répété à chaque ligne (le
            # domaine est déjà dans l'en-tête) et chaque code porte le
            # LIBELLÉ du Référentiel : « GR (Granodiorite) · hôte 70% ».
            _ROLE_SHORT = {
                "primary": _tr("hôte"), "secondary": _tr("sec."),
                "vein": _tr("veine"), "accessory": _tr("access."),
            }
            if inv.components:
                # v2.9.188 — L'ESSENTIEL : 5 composants visibles, le
                # reste résumé (« … +N composant(s) »).
                _comps = inv.components
                for c in _comps[:5]:
                    role_lbl = (
                        f" · {_ROLE_SHORT.get(c.role, c.role)}" if c.role else "")
                    pct_lbl = f" {c.proportion:.0f}%" if c.proportion else ""
                    lines.append(self._code_with_label(c.raw_code, "litho")
                                 + role_lbl + pct_lbl)
                if len(_comps) > 5:
                    lines.append(f"… +{len(_comps) - 5} composant(s)")
            elif inv.attributes.get("lithology"):
                lines.append(self._code_with_label(
                    inv.attributes["lithology"], "litho"))
        elif domain == "mineralizations":
            # v2.9.141 — tous les styles (organisation large), pas le 1er seul.
            codes = self._interval_codes(inv, domain)
            if codes:
                # v2.9.187 — libellés du Référentiel (« Filonienne +
                # Massive », pas des codes bruts).
                lines.append("Styles : " + " + ".join(
                    self._code_with_label(c, "mineralizations")
                    for c in codes))
            min_val = inv.attributes.get("minerals") or inv.attributes.get("mineraux")
            if min_val:
                lines.append(_tr("Minéraux : {}").format(min_val))
            int_val = inv.attributes.get("intensity") or inv.attributes.get("intensite")
            if int_val:
                lines.append(_tr("Intensité : {}").format(int_val))
        elif domain == "alterations":
            # v2.9.141 — même logique que la coupe 2D : intensité PAR CODE.
            if inv.components:
                # v2.9.187 — plus de « Alt : » répété ; libellé inclus :
                # « ARG (Argilique) · fort ».
                _alts = [c for c in inv.components if c.raw_code]
                for c in _alts[:5]:   # v2.9.188 — l'essentiel
                    int_lbl = f" · {c.intensity}" if getattr(c, "intensity", "") else ""
                    lines.append(self._code_with_label(c.raw_code, "alterations")
                                 + int_lbl)
                if len(_alts) > 5:
                    lines.append(f"… +{len(_alts) - 5} code(s)")
            else:
                codes = self._interval_codes(inv, domain)
                if codes:
                    lines.append(" + ".join(
                        self._code_with_label(c, "alterations")
                        for c in codes))
                int_val = inv.attributes.get("intensity") or inv.attributes.get("intensite")
                if int_val:
                    lines.append(_tr("Intensité : {}").format(int_val))
        else:
            # v2.9.188 — l'essentiel : 4 éléments visibles.
            _kv = [(k, v) for k, v in inv.attributes.items()
                   if k not in ("hole_id", "from", "to")]
            for k, v in _kv[:4]:
                lines.append(f"{k} : {v}")
            if len(_kv) > 4:
                lines.append(_tr("… +{} élément(s)").format(
                    len(_kv) - 4))

        return "\n".join(lines)

    def _interpolate_dh_point(self, dh: DrillHole, depth: float) -> Optional[TrajectoryPoint]:
        """Point exact du forage — délégué au mesh builder (v2.9.146)."""
        from ..core.mesh_builder import interpolate_dh_point
        return interpolate_dh_point(dh, depth)
    # ------------------------------------------------------------------
    # Non-Invasive 3D Selection (Calipers / Rings on Selected Interval)
    # ------------------------------------------------------------------
    def _draw_selection_highlight(self, painter, scale):
        """Étriers de sélection — délégués au renderer (v2.9.148)."""
        from .view_3d_renderer import draw_selection_highlight
        draw_selection_highlight(self, painter, scale)
    # ------------------------------------------------------------------
    # Floating In-Canvas 3D Legend (Clearance Above Gizmo, Multi-Column)
    # ------------------------------------------------------------------
    def _draw_floating_legend(self, painter: QPainter):
        """Légende flottante — déléguée à la couche overlays (v2.9.146)."""
        from .view_3d_overlays import draw_floating_legend
        draw_floating_legend(self, painter)
    @staticmethod
    @staticmethod
    def _elide_text(fm, text: str, max_w: float) -> str:
        """Troncation « … » — déléguée à la couche overlays (v2.9.146)."""
        from .view_3d_overlays import elide_text
        return elide_text(fm, text, max_w)
    def _draw_gizmo(self, painter: QPainter):
        """Gizmo d'orientation — délégué à la couche overlays (v2.9.146)."""
        from .view_3d_overlays import draw_gizmo
        draw_gizmo(self, painter)
    def _draw_exag_badge(self, painter: QPainter):
        """Badge d'exagération — délégué à la couche overlays (v2.9.146)."""
        from .view_3d_overlays import draw_exag_badge
        draw_exag_badge(self, painter)
    def _draw_hover_tooltip(self, painter: QPainter):
        """Infobulle de survol — déléguée à la couche overlays (v2.9.146)."""
        from .view_3d_overlays import draw_hover_tooltip
        draw_hover_tooltip(self, painter)
    # ------------------------------------------------------------------
    # Mouse & Keyboard Event Handlers
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        """Clic — délégué à la couche interaction (v2.9.148)."""
        from .view_3d_interaction import mouse_press
        mouse_press(self, event)
    def mouseMoveEvent(self, event):
        """Déplacement — délégué à la couche interaction (v2.9.148)."""
        from .view_3d_interaction import mouse_move
        mouse_move(self, event)
    def mouseReleaseEvent(self, event):
        """Relâchement — délégué à la couche interaction (v2.9.148)."""
        from .view_3d_interaction import mouse_release
        mouse_release(self, event)
    def wheelEvent(self, event):
        """Molette — déléguée à la couche interaction (v2.9.148)."""
        from .view_3d_interaction import wheel
        wheel(self, event)

    def _begin_wheel_motion(self):
        """v2.9.245 — zoom molette : pose le drapeau « en mouvement » et
        (re)lance la minuterie de fin (retour écran : « au zoom et
        dézoom de 3D c'est grave lent »).

        Chaque cran de molette rendait la scène en DÉTAIL COMPLET : le
        LOD de mouvement (v2.9.175) n'écoutait que ``_is_dragging``,
        que la molette ne pose jamais — l'orbite seule était fluide.
        Le drapeau ``_wheel_motion`` étend le LOD au zoom ; la
        minuterie (redémarrée à chaque cran) la retire ~150 ms après
        le DERNIER cran, avec un repaint final en détail complet.

        Repli sûr : si QTimer n'est pas disponible (harnais de test
        sans Qt complet), le drapeau reste baissé — rendu détaillé,
        comportement d'avant, jamais de LOD permanent par accident.
        """
        try:
            from qgis.PyQt.QtCore import QTimer
            timer = getattr(self, "_wheel_timer", None)
            if timer is None:
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.setInterval(150)
                timer.timeout.connect(self._end_wheel_motion)
                self._wheel_timer = timer
            self._wheel_motion = True
            timer.start()
        except Exception as _exc:
            # Règle audit C : capturé et journalisé (EXC-161/163) — le
            # repli est DOCUMENTÉ : rendu détaillé (comportement
            # d'avant v2.9.245), pas de LOD permanent par accident.
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : minuterie du zoom molette "
                          "(LOD désactivé, rendu détaillé)", _exc)
            self._wheel_motion = False

    def _end_wheel_motion(self):
        """v2.9.245 — fin du zoom molette : drapeau baissé + repaint en
        DÉTAIL COMPLET (le LOD de mouvement a sauté motifs, légende,
        étiquettes — ils reviennent, comme au relâchement de l'orbite
        v2.9.175 ; le drapeau est dans la clé du cache de scène, sinon
        l'image allégée serait resservie — bug de classe v2.9.190).
        v2.9.318 : le zoom « posé » realigne aussi la référence du blit
        (§2.1) — la clé change, le pixmap est reconstruit UNE fois, net."""
        self._wheel_motion = False
        self._render_zoom = float(self.zoom)
        self._render_pan_x = float(self.pan_x)
        self._render_pan_y = float(self.pan_y)
        self.update()

    def _find_hover_tooltip(self, pos):
        """Hit-test de survol — délégué à la couche interaction (v2.9.148)."""
        from .view_3d_interaction import find_hover_tooltip
        return find_hover_tooltip(self, pos)
    def _handle_click_selection(self, pos):
        """Sélection au clic — déléguée à la couche interaction (v2.9.148)."""
        from .view_3d_interaction import handle_click_selection
        handle_click_selection(self, pos)

