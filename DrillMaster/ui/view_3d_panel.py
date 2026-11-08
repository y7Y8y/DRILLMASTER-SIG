"""DrillMaster — Panneau latéral de la Vue 3D (volet 1, tranche 4, v2.9.149).

Construction de l'UI latérale (domaine, éléments teneurs, objets
spatiaux, portée, rendu), extraite de ``ui/view_3d.py`` (SPEC) :
le widget assemble, ce module construit.  Les handlers restent des
méthodes du widget — le panneau ne fait que les référencer.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt

from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QSlider, QVBoxLayout,
    QWidget,
)

from .styles_qt import BUTTON_SECONDARY, COLORS, INPUT_STYLE


def _tr(text):
    """v2.9.229 — Lot 1c : traduction du panneau 3D (contexte
    View3DPanel — le panneau est construit par une fonction, pas
    une classe : contexte explicite)."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("View3DPanel", text)


def build_side_panel(widget):
    """Construit le panneau latéral de la vue 3D (tranche 4)."""
    """Panneau latéral 3D (v2.9.141).

    On expose les contrôles utiles (domaine + objet spatiaux + portée +
    rendu), mais PAS le détail du relief MNT : les isocontours et la
    grille drapée restent des réglages internes (défauts propres).
    """
    panel_scroll = QScrollArea()
    panel_scroll.setWidgetResizable(True)
    panel_scroll.setFrameShape(QFrame.Shape.NoFrame)
    panel_scroll.setMaximumWidth(260)

    panel = QWidget()
    # v2.9.246 — FIX ÉTAT COCHÉ INVISIBLE (retour écran : « quand on
    # clique sur un bouton [du] panneau droite 3D on sait pas si c'est
    # pris ou pas ou sélectionné »).  La feuille locale (v2.9.220)
    # peignait la case cochée en BLANC (#FDFEFE) sur fond décoché
    # BLANC (#FFFFFF) avec une bordure PLUS CLAIRE — le QSS remplace
    # la coche native : l'état coché était INDISTINGUABLE du décoché.
    # Désormais coché = REMPLISSAGE ANTHRACITE (COLORS['accent'],
    # #1C2833), la MÊME convention que le chrome neutre v2.9.225 et
    # toutes les cases du plugin (contraste ~14:1 sur carte claire) ;
    # le survol annonce la zone cliquable (bordure anthracite).
    panel.setStyleSheet(f"""
        QGroupBox {{
            font-weight: bold;
            font-size: 8.5pt;
            color: #2C3E50;
            border: 1px solid #D5DBDB;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }}
        QCheckBox {{
            color: #2C3E50;
            spacing: 6px;
            font-size: 8.5pt;
        }}
        QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid #95A5A6;
            border-radius: 3px;
            background: #FFFFFF;
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {COLORS['accent']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLORS['accent']};
            border: 1px solid {COLORS['accent_hover']};
        }}
        QCheckBox::indicator:checked:hover {{
            border: 1px solid {COLORS['accent_hover']};
        }}
        QCheckBox::indicator:disabled {{
            background: #ECF0F1;
            border: 1px solid #D5DBDB;
        }}
    """)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(6, 4, 6, 4)
    layout.setSpacing(6)

    title = QLabel(_tr("AFFICHAGE 3D"))
    title.setStyleSheet(f"color:{COLORS['primary']}; font-size:8.5pt; font-weight:bold; padding:2px 0;")
    layout.addWidget(title)

    # 1. Portée (Scope) — v2.9.188 : EN PREMIER (retour écran : on
    # choisit D'ABORD quels forages on regarde, puis le domaine.
    gb_scope = QGroupBox(_tr("Portée"))
    gb_scope_l = QVBoxLayout(gb_scope)
    gb_scope_l.setContentsMargins(6, 6, 6, 6)

    widget.combo_scope = QComboBox()
    # v2.9.188 — signaux bloqués PENDANT la construction : le premier
    # addItem déclenche currentIndexChanged → _on_scope_changed lit
    # combo_geo_mode (pas encore construit maintenant que Portée vient
    # en premier).
    widget.combo_scope.blockSignals(True)
    widget.combo_scope.addItem(_tr("Projet complet"), "all")
    widget.combo_scope.addItem(_tr("Coupe active seule"), "section")
    widget.combo_scope.addItem(_tr("Sélection seule"), "selection")
    widget.combo_scope.blockSignals(False)
    widget.combo_scope.setStyleSheet(INPUT_STYLE)
    # v2.9.177 — la portée EXPLIQUE (où sont les domaines simultanés).
    widget.combo_scope.setToolTip(_tr(
        "Projet complet : tous les forages, un seul domaine — lisible à "
        "grande échelle.\n"
        "Coupe active seule : forages de la coupe 2D — les cases "
        "« Domaines simultanés » sont disponibles.\n"
        "Sélection seule : forages sélectionnés — idem."))
    widget.combo_scope.currentIndexChanged.connect(widget._on_scope_changed)
    gb_scope_l.addWidget(widget.combo_scope)
    # v2.9.177 — astuce visible SEULEMENT en « Projet complet » : elle
    # dit où débloquer les domaines simultanés (les cases y sont cachées).
    widget.lbl_multi_hint = QLabel(_tr(
        "Domaines simultanés : disponibles en « Coupe active » ou "
        "« Sélection seule »"))
    widget.lbl_multi_hint.setStyleSheet(
        "color: #95A5A6; font-size: 7.5pt; font-style: italic;")
    widget.lbl_multi_hint.setWordWrap(True)
    gb_scope_l.addWidget(widget.lbl_multi_hint)
    layout.addWidget(gb_scope)

    # 1. Domaine affiché (ségrégation stricte des styles, standards JORC).
    gb_domain = QGroupBox(_tr("Données sur forages"))
    gb_domain_l = QVBoxLayout(gb_domain)
    gb_domain_l.setContentsMargins(6, 6, 6, 6)
    gb_domain_l.setSpacing(5)

    lbl_dom = QLabel(_tr("Domaine affiché :"))
    lbl_dom.setStyleSheet("color: #7F8C8D; font-size: 8pt;")
    gb_domain_l.addWidget(lbl_dom)

    widget.combo_geo_mode = QComboBox()
    # v2.9.270 — combo rangé par CATÉGORIE MÉTIER (même plan que l'étape 2
    # et la liste Pistes 2D) : Géologie → Géochimie → Géotechnique → Média,
    # « Trajectoires seules » en dernier (mode d'affichage, pas un domaine).
    widget.combo_geo_mode.addItem(_tr("Lithologie (roches)"), "litho")
    widget.combo_geo_mode.addItem(_tr("Altérations"), "alterations")
    widget.combo_geo_mode.addItem(
        _tr("Styles de minéralisation"), "mineralizations")
    # v2.9.260 étape 3 — mesures ponctuelles `structure` : disques/flèches
    # le long des trajectoires, couleurs/libellés du Référentiel.
    widget.combo_geo_mode.addItem(_tr("Structures"), "structure")
    widget.combo_geo_mode.addItem(_tr("Teneurs (analyses)"), "assays")
    widget.combo_geo_mode.addItem(_tr("Intercepts (seuils)"), "intercepts")
    # v2.9.267 — géotechnique 3D : mêmes couleurs que la coupe 2D.
    widget.combo_geo_mode.addItem(_tr("RQD"), "rqd")
    widget.combo_geo_mode.addItem(_tr("Récupération"), "recovery")
    widget.combo_geo_mode.addItem(_tr("Densité"), "density")
    # v2.9.263 E3 — Imagerie 3D : ruban texturé le long de la trajectoire.
    widget.combo_geo_mode.addItem(_tr("Imagerie"), "imagery")
    widget.combo_geo_mode.addItem(_tr("Trajectoires seules"), "trajectory")
    widget.combo_geo_mode.setStyleSheet(INPUT_STYLE)
    # v2.9.178 — le combo explique son rôle (question réelle v2.9.172 :
    # « domaine affiché est là aussi »), court (convention TT-17).
    widget.combo_geo_mode.setToolTip(_tr(
        "Domaine PRINCIPAL · tube centré pleine largeur · les cases "
        "« Domaines simultanés » ajoutent les autres en tubes fins "
        "(portée Coupe/Sélection)"))
    widget.combo_geo_mode.currentIndexChanged.connect(widget._on_geo_domain_changed)
    gb_domain_l.addWidget(widget.combo_geo_mode)
    # v2.9.166 — DOMAINES MULTIPLES : cases à cocher par domaine, comme
    # les pistes de la coupe 2D.  Le PREMIER coché = domaine principal
    # (tube centré, pleine largeur) ; les suivants = tubes parallèles
    # plus fins, décalés perpendiculairement au forage.
    # v2.9.172 — INTERCEPT A SA CASE (retour écran : « intercept n'est
    # pas dans domaines simultané ? »).  Avant, intercepts n'existait
    # qu'en combo : le cocher ailleurs supprimait le domaine principal
    # silencieusement (désynchro combo ↔ cases = « mélanges »).
    sub_multi = QLabel(_tr("Domaines simultanés :"))
    sub_multi.setStyleSheet("color: #7F8C8D; font-size: 7.5pt; padding: 3px 0 0 0;")
    # v2.9.177 — aide en contexte (retour écran : « comment l'utilisateur
    # saura que le multidomaine n'existe qu'en coupe/sélection ? »).
    sub_multi.setToolTip(_tr(
        "Domaines additionnels en tubes fins à côté du domaine principal\n"
        "(même richesse : motifs, veines/accessoires, barrettes, intensité).\n"
        "Disponible en portée « Coupe active seule » ou « Sélection seule »."))
    gb_domain_l.addWidget(sub_multi)
    widget._sub_multi_lbl = sub_multi
    widget.domain_checks = {}
    # v2.9.270 — cases rangées par CATÉGORIE MÉTIER, dans le MÊME ordre que
    # le combo (avant : combo et cases n'avaient pas le même ordre).
    for key, label in (
        ("litho", _tr("Lithologie")),
        ("alterations", _tr("Altérations")),
        ("mineralizations", _tr("Minéralisations")),
        ("structure", _tr("Structures")),
        ("assays", _tr("Teneurs")),
        ("intercepts", _tr("Intercepts (seuils)")),
        # v2.9.267 — géotechnique en domaine SIMULTANÉ (piste fine décalée
        # à côté du domaine principal), en portée Coupe/Sélection.
        ("rqd", _tr("RQD")),
        ("recovery", _tr("Récupération")),
        ("density", _tr("Densité")),
        # v2.9.263 E3 — imagerie en domaine simultané possible, mais rendu
        # centré sur la trajectoire (pas de tube décalé).
        ("imagery", _tr("Imagerie")),
    ):
        chk = QCheckBox(label)
        chk.setChecked(key == "litho")
        chk.stateChanged.connect(
            lambda state, k=key: widget._on_domain_toggled(k, state))
        gb_domain_l.addWidget(chk)
        widget.domain_checks[key] = chk

    # Éléments affichés (visible seulement pour « Teneurs »).
    # v2.9.143 — combo à CASES COCHÉES : 1 à 3 éléments affichables
    # SIMULTANÉMENT directement en 3D (plus besoin de passer par la
    # config de la coupe 2D — retour écran v2.9.142).
    widget.lbl_assay_elem = QLabel(_tr("Éléments affichés :"))
    widget.lbl_assay_elem.setStyleSheet("color: #7F8C8D; font-size: 8pt;")
    widget.lbl_assay_elem.setVisible(False)
    gb_domain_l.addWidget(widget.lbl_assay_elem)

    # v2.9.146 — résumé + bouton ouvrant un DIALOGUE (le combo à
    # cases de la v2.9.143 ne se cochait pas de façon fiable dans
    # QGIS : popup stylé, texte écrasé au retour).
    from ..core.multi_assay import assay_selection_summary
    widget._assay_mirror_label = _tr("Comme la coupe 2D")
    widget.lbl_assay_summary = QLabel(
        assay_selection_summary([], widget._assay_mirror_label))
    widget.lbl_assay_summary.setStyleSheet(
        "color: #2C3E50; font-size: 8pt; font-weight: bold;")
    widget.lbl_assay_summary.setWordWrap(True)
    widget.lbl_assay_summary.setVisible(False)
    gb_domain_l.addWidget(widget.lbl_assay_summary)

    widget.btn_assay_choose = QPushButton(_tr("Choisir les éléments…"))
    widget.btn_assay_choose.setStyleSheet(BUTTON_SECONDARY)
    widget.btn_assay_choose.setToolTip(_tr(
        "Choisir 1 à 3 éléments affichés simultanément en 3D.\n"
        "« Comme la coupe 2D » reprend les éléments configurés en 2D."))
    widget.btn_assay_choose.clicked.connect(widget._open_assay_element_dialog)
    widget.btn_assay_choose.setVisible(False)
    gb_domain_l.addWidget(widget.btn_assay_choose)

    layout.addWidget(gb_domain)

    # 2. Objets spatiaux — regroupés par famille (v2.9.141).
    gb_spatial = QGroupBox(_tr("Objets spatiaux"))
    gb_spatial_l = QVBoxLayout(gb_spatial)
    gb_spatial_l.setContentsMargins(6, 6, 6, 6)
    gb_spatial_l.setSpacing(3)

    def _sub_lbl(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #95A5A6; font-size: 7.5pt; font-weight: bold; "
                          "padding: 4px 0 1px 0;")
        return lbl

    # — Forages —
    gb_spatial_l.addWidget(_sub_lbl(_tr("Forages")))
    widget.chk_holes = QCheckBox(_tr("Trajectoires"))
    widget.chk_holes.setChecked(True)
    widget.chk_holes.stateChanged.connect(lambda s: setattr(widget.canvas, "show_drillholes", bool(s)) or widget.canvas.update())
    gb_spatial_l.addWidget(widget.chk_holes)

    widget.chk_collars = QCheckBox(_tr("Collets et noms"))
    widget.chk_collars.setChecked(True)
    widget.chk_collars.stateChanged.connect(lambda s: setattr(widget.canvas, "show_collars", bool(s)) or setattr(widget.canvas, "show_labels", bool(s)) or widget.canvas.update())
    gb_spatial_l.addWidget(widget.chk_collars)

    # — Coupe —
    gb_spatial_l.addWidget(_sub_lbl(_tr("Coupe")))
    widget.chk_plane = QCheckBox(_tr("Plan de coupe"))
    widget.chk_plane.setChecked(False)
    widget.chk_plane.setToolTip(_tr(
        "Plaque semi-transparente marquant la coupe 2D active"))
    widget.chk_plane.stateChanged.connect(lambda s: setattr(widget.canvas, "show_section_plane", bool(s)) or widget.canvas.update())
    gb_spatial_l.addWidget(widget.chk_plane)

    widget.chk_corridor = QCheckBox(_tr("Corridor (buffer)"))
    widget.chk_corridor.setChecked(False)
    widget.chk_corridor.setToolTip(
        _tr("Volume tampon 3D entourant la coupe"))
    widget.chk_corridor.stateChanged.connect(lambda s: setattr(widget.canvas, "show_corridor", bool(s)) or widget.canvas.update())
    gb_spatial_l.addWidget(widget.chk_corridor)

    # — Surface (MNT) — UNE SEULE case (le relief détaillé est interne).
    gb_spatial_l.addWidget(_sub_lbl(_tr("Surface (MNT)")))
    widget.chk_topo = QCheckBox(_tr("Surface du terrain"))
    widget.chk_topo.setChecked(False)   # v2.9.148 — décochée par défaut
    widget.chk_topo.setToolTip(_tr(
        "Surface 3D de sol (MNT réel, teinte par altitude + "
        "ombrage de relief)"))
    widget.chk_topo.stateChanged.connect(lambda s: setattr(widget.canvas, "show_topography", bool(s)) or widget.canvas.update())
    gb_spatial_l.addWidget(widget.chk_topo)

    # — Cadre —
    gb_spatial_l.addWidget(_sub_lbl("Cadre"))
    widget.chk_axes = QCheckBox(_tr("Repère et boîte 3D"))
    widget.chk_axes.setChecked(True)
    widget.chk_axes.stateChanged.connect(lambda s: setattr(widget.canvas, "show_axes", bool(s)) or widget.canvas.update())
    gb_spatial_l.addWidget(widget.chk_axes)

    layout.addWidget(gb_spatial)

    # 4. Rendu (Épaisseur, Exagération Z, Opacité & Emprise MNT)
    gb_rend = QGroupBox(_tr("Rendu"))
    gb_rend_l = QGridLayout(gb_rend)
    gb_rend_l.setContentsMargins(6, 6, 6, 6)

    gb_rend_l.addWidget(QLabel(_tr("Épaisseur :")), 0, 0)
    widget.spin_width = QDoubleSpinBox()
    widget.spin_width.setRange(1.5, 20.0)
    widget.spin_width.setValue(10.0)  # Default 10 px
    widget.spin_width.setSuffix(" px")
    widget.spin_width.setStyleSheet(INPUT_STYLE)
    widget.spin_width.setToolTip(_tr(
        "Épaisseur des tubes · principal et voies (secondaires plus fins)"))
    widget.spin_width.valueChanged.connect(lambda v: setattr(widget.canvas, "stroke_width", v) or widget.canvas.update())
    gb_rend_l.addWidget(widget.spin_width, 0, 1)

    gb_rend_l.addWidget(QLabel(_tr("Exag. Z :")), 1, 0)
    widget.spin_exag_side = QDoubleSpinBox()
    widget.spin_exag_side.setRange(0.5, 10.0)
    widget.spin_exag_side.setSingleStep(0.5)
    widget.spin_exag_side.setValue(1.0)
    widget.spin_exag_side.setSuffix("x")
    widget.spin_exag_side.setStyleSheet(INPUT_STYLE)
    widget.spin_exag_side.setToolTip(_tr(
        "Exag. verticale ×N · visuelle, coordonnées réelles intactes"))
    widget.spin_exag_side.valueChanged.connect(widget._on_exag_changed)
    gb_rend_l.addWidget(widget.spin_exag_side, 1, 1)

    # v2.9.141 — opacité du MNT : 100 = opaque par défaut (le user ne
    # veut plus d'une surface « en transparence » par défaut).
    gb_rend_l.addWidget(QLabel(_tr("Opacité MNT :")), 2, 0)
    widget.slider_terrain = QSlider(Qt.Orientation.Horizontal)
    widget.slider_terrain.setRange(0, 100)
    widget.slider_terrain.setValue(100)
    widget.slider_terrain.setToolTip(_tr(
        "Opacité MNT · 100 = opaque (baissez pour voir sous le relief)"))
    widget.slider_terrain.valueChanged.connect(lambda v: setattr(widget.canvas, "terrain_opacity_pct", v) or widget.canvas.update())
    gb_rend_l.addWidget(widget.slider_terrain, 2, 1)

    # v2.9.141 — emprise du MNT (dans « Rendu », près de la surface).
    gb_rend_l.addWidget(QLabel(_tr("Emprise MNT :")), 3, 0)
    widget.combo_mnt_extent = QComboBox()
    widget.combo_mnt_extent.addItem(_tr("Tous les forages"), "all")
    widget.combo_mnt_extent.addItem(_tr("Coupe active"), "section")
    widget.combo_mnt_extent.setStyleSheet(INPUT_STYLE)
    widget.combo_mnt_extent.setToolTip(_tr(
        "Zone couverte par la surface 3D : tout le projet, ou le corridor "
        "de la coupe active (buffer 2D)."))
    widget.combo_mnt_extent.currentIndexChanged.connect(widget._on_mnt_extent_changed)
    gb_rend_l.addWidget(widget.combo_mnt_extent, 3, 1)

    layout.addWidget(gb_rend)
    layout.addStretch(1)

    panel_scroll.setWidget(panel)
    return panel_scroll

