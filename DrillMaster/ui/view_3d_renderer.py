"""DrillMaster — Renderer 3D (volet 1, tranche 3, v2.9.148).

Couche DESSIN extraite de ``ui/view_3d.py`` (SPEC) : peint la scène via
QPainter en consommant la caméra (core/camera3d), le mesh builder
(core/mesh_builder) et l'état du canvas.  Ne calcule AUCUNE géométrie
lui-même — il projette et peint.

Le canvas délègue chaque méthode à une ligne ; les méthodes du canvas
restent le point d'entrée (aucun appelant externe ne change).
"""

from __future__ import annotations

import math
import os
import time

from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen,
    QPixmap, QPolygonF,
)

from ..core.data_model import DrillHole, IntervalRecord
from ..core.mesh_builder import interpolate_dh_point  # v2.9.198 (cache)
from ..core.structure_classify import structure_family

_MISSING = object()   # sentinelle du cache d'interpolation (v2.9.198)
from ..core.multi_assay import format_grade_value
from ..core.topography import bounds_from_points, build_surface_grid
from .styles_qt import COLORS


# v2.9.276 — seuil de décimation (px) des intervalles 3D.
_PIXEL_CULL = 1.0


def _tr(text):
    """v2.9.236 — Lot 4 : texte dessiné 3D traduisible."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("View3DRenderer", text)


def _in_motion(canvas):
    """v2.9.245 — en MOUVEMENT : orbite (glisser) OU zoom molette.

    Retour écran : « au zoom et dézoom de 3D c'est grave lent » (alors
    que l'orbite, elle, restait fluide).  Cause : TOUT le LOD de
    mouvement (v2.9.175) regardait ``_is_dragging`` — un drapeau que
    la molette ne pose JAMAIS : chaque cran de molette rendait la
    scène en DÉTAIL COMPLET (marques de motifs par intervalle, légende
    qui itère tous les forages, drawText par collet, double liseré par
    tube…).  Un seul prédicat partagé désormais : les deux mouvements
    allègent la frame ; le détail complet revient à l'arrêt (repaint
    dédié au relâchement pour l'orbite, minuterie ~150 ms après le
    DERNIER cran pour la molette).
    """
    return bool(getattr(canvas, "_is_dragging", False)
                or getattr(canvas, "_wheel_motion", False))


def _scene_cache_key(canvas):
    """v2.9.189 — CLÉ du cache de scène : TOUT ce qui change le rendu,
    SAUF le survol (``_hover_text``/``_hover_pos`` — c'est tout le
    point : au survol, seule l'infobulle change, on reblitte la scène
    cachée au lieu de la redessiner).
    """
    rules = getattr(canvas, "_threshold_rules", None) or []
    # v2.9.263 E4 — la signature imagerie (from/to/chemin) est RETIRÉE
    # de la clé : elle reconstruisait un tuple trié sur TOUS les forages ×
    # TOUTES les lignes imagerie à CHAQUE paint (y compris au survol où
    # le cache allait servir) — O(images × forages) par mouseMove.  La
    # mutation des données/référentiel incrémente déjà ``_scene_rev`` et
    # le cache inclut ``id(canvas._drillholes)`` : l'invalidation reste
    # correcte, sans coût proportionnel aux photos.
    return (
        # v2.9.190 — le LOD d'orbite fait partie de la clé : sans lui,
        # le relâchement (caméra inchangée) resservait l'image DU
        # MOUVEMENT (sans labels ni légende) jusqu'au prochain clic —
        # retour écran : « quand on relâche ils sont censés être là
        # mais non ».
        # v2.9.245 — idem pour le LOD du ZOOM MOLETTE : l'image allégée
        # du défilement ne doit jamais être resservie une fois la
        # minuterie écoulée (même classe de bug que v2.9.190).
        bool(getattr(canvas, "_is_dragging", False)),  # v318 : LOD orbite
        round(float(canvas.yaw_deg), 3), round(float(canvas.pitch_deg), 3),
        # v2.9.318 (§2.1) — pan/zoom sortent de la clé : blit 2D du
        # pixmap ; le zoom « posé » revient via _render_zoom.
        round(float(getattr(canvas, "_render_zoom", 1.0) or 1.0), 4),
        round(float(canvas.v_exag), 3), round(float(canvas.stroke_width), 2),
        int(canvas.tube_opacity_pct),
        tuple(canvas.active_domains or []),
        repr(rules),
        bool(canvas.show_drillholes), bool(canvas.show_collars),
        bool(canvas.show_labels),
        bool(getattr(canvas, "show_section_plane", False)),
        bool(getattr(canvas, "show_corridor", False)),
        bool(getattr(canvas, "show_topography", False)),
        bool(getattr(canvas, "show_axes", True)),
        bool(getattr(canvas, "show_legend", True)),
        bool(getattr(canvas, "show_grid_drape", False)),
        bool(getattr(canvas, "show_contours", False)),
        int(getattr(canvas, "terrain_opacity_pct", 100)),
        str(canvas._highlight_code or ""),
        canvas._selected_hole_id, canvas._selected_from_m,
        canvas._selected_to_m,
        # v2.9.211 — la sélection MULTIPLE aussi : sans elle, ajouter
        # un forage à la sélection (depuis la carte) ne re-rendait
        # pas la scène → pas d'estompage des autres.
        tuple(getattr(canvas, "_selected_hole_ids", None) or []),
        str(getattr(canvas, "scope_mode", "all")),
        tuple(canvas.assay_display_elements or []),
        str(canvas.assay_palette),
        repr(getattr(canvas, "_assay_scales", None) or {}),
        repr(getattr(canvas, "_assay_element_palettes", None) or {}),
        repr(getattr(canvas, "_assay_scale", None)),
        id(canvas._drillholes), len(canvas._drillholes or []),
        id(getattr(canvas, "_surface_grid", None)),
        id(getattr(canvas, "_active_section_line", None)),
        float(getattr(canvas, "_active_section_buffer", 0.0) or 0.0),
        int(getattr(canvas, "_scene_rev", 0)),
        canvas.width(), canvas.height(),
    )


def _blit_cached(canvas, cached):
    """v2.9.318/319 — blit 2D du pixmap caché (§2.1) + infobulle.

    Partagé par le chemin caché (survol) et l'attente asynchrone :
    pan/zoom pendant le geste = translation+échelle du pixmap, pas de
    reconstruction.
    """
    cam = getattr(canvas, "camera", None)
    if cam is not None:
        s_f, tx, ty = cam.view_blit(
            canvas.width(), canvas.height(),
            getattr(canvas, "_render_zoom", 1.0),
            getattr(canvas, "_render_pan_x", 0.0),
            getattr(canvas, "_render_pan_y", 0.0))
    else:  # harnais sans caméra : blit identité
        s_f, tx, ty = 1.0, 0.0, 0.0
    painter = QPainter(canvas)
    if s_f != 1.0 or tx or ty:
        painter.translate(tx, ty)
        painter.scale(s_f, s_f)
    painter.drawPixmap(0, 0, cached[1])
    painter.resetTransform()  # infobulle en espace écran
    canvas._draw_hover_tooltip(painter)
    painter.end()


def _async_ok(canvas):
    """v2.9.319 (§2.4) — le rendu asynchrone est-il utilisable ?

    Drapeau de secours (UNE version) : ``DRILLMASTER_3D_ASYNC=0`` ou
    ``canvas._async_render = False`` → 100 % synchrone (comportement
    d'avant 319).  ImportError (harnais sans QThread) → synchrone.
    """
    if os.getenv("DRILLMASTER_3D_ASYNC", "1") == "0":
        return False
    if not bool(getattr(canvas, "_async_render", True)):
        return False
    try:
        from .view_3d_async import SceneRenderWorker  # noqa: F401
    except Exception as _exc:  # harnais sans QThread : synchrone
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : module de rendu asynchrone indisponible "
                      "(synchrone)", _exc)
        return False
    return True


def _start_async_render(canvas, key):
    """v2.9.319 — lance le worker de scène (détail posé, hors GUI)."""
    try:
        from .view_3d_async import SceneRenderWorker
        worker = SceneRenderWorker(canvas, key)
        worker.scene_ready.connect(
            lambda k, img, z, px, py, c=canvas:
            _on_scene_ready(c, k, img, z, px, py))
        canvas._async_worker = worker
        worker.start()
    except Exception as exc:  # noqa: BLE001 — repli synchrone
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : lancement du rendu asynchrone "
                      "(repli synchrone)", exc)
        canvas._async_worker = None


def _on_scene_ready(canvas, key, img, ref_zoom, ref_pan_x, ref_pan_y):
    """v2.9.319 — arrivée du worker (thread GUI, via signal).

    Adoption seulement si la clé de scène n'a pas bougé (sinon image
    périmée jetée — classe de bug v2.9.190).  Les références du blit
    (§2.1) sont celles du LANCEMENT : le pixmap correspond à la
    caméra du début de rendu.
    """
    canvas._async_worker = None
    try:
        if img is None:  # échec worker journalisé → repli synchrone
            canvas.update()
            return
        if _scene_cache_key(canvas) != key:  # scène périmée
            canvas.update()
            return
        canvas._scene_cache = (key, QPixmap.fromImage(img))
        canvas._render_zoom = float(ref_zoom)
        canvas._render_pan_x = float(ref_pan_x)
        canvas._render_pan_y = float(ref_pan_y)
        _emit_render_status(canvas)
    except Exception as exc:  # noqa: BLE001 — repli synchrone
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : adoption du rendu asynchrone "
                      "(repli synchrone)", exc)
    canvas.update()


def paint_scene(canvas, event):
    """v2.9.189 — CACHE DE SCÈNE (retour écran : « en multi-domaine le
    survol devient très très lent »).

    Chaque changement d'infobulle redessinait TOUTE la scène en détail
    complet (motifs, composants, MNT…) — en domaines simultanés, une
    simple traversée de la souris coûtait des dizaines de rendus
    complets.  La scène est maintenant rendue dans un QPixmap CACHÉ :
    au survol, on blitte l'image + l'infobulle par-dessus
    (microsecondes).  La clé couvre tout ce qui change le rendu, SAUF
    le survol ; ``_scene_rev`` est incrémenté par les mutations hors
    caméra (données, référentiel, coupe active…).
    """
    key = _scene_cache_key(canvas)
    cached = getattr(canvas, "_scene_cache", None)
    if cached is not None and cached[0] == key:
        _blit_cached(canvas, cached)
        return

    # v2.9.319 (§2.4) — rendu ASYNCHRONE du détail posé : la scène
    # complète (~144 ms / 500 forages) part dans un QThread ; le GUI
    # blitte l'ancienne scène en attendant, puis adopte l'image si la
    # clé n'a pas bougé.  Le MOUVEMENT (orbite/molette) reste
    # SYNCHRONE en LOD (frames légères, ~10 ms) — l'asynchrone ne
    # sert qu'au détail à l'arrêt.  Drapeau de secours (une version) :
    # DRILLMASTER_3D_ASYNC=0 ou canvas._async_render = False.
    if cached is not None and not _in_motion(canvas):
        if (getattr(canvas, "_async_worker", None) is None
                and _async_ok(canvas)):
            _start_async_render(canvas, key)
        if getattr(canvas, "_async_worker", None) is not None:
            _blit_cached(canvas, cached)
            return

    try:
        dpr = float(canvas.devicePixelRatioF())
    except Exception as _exc:
        # écran sans ratio (tests) : rendu 1:1.  Règle audit C :
        # capturé et journalisé.
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : ratio d'écran du cache de scène "
                      "(rendu 1:1)", _exc)
        dpr = 1.0
    if not (dpr and math.isfinite(dpr)) or dpr <= 0.0:
        dpr = 1.0
    pix = QPixmap(max(1, int(canvas.width() * dpr)),
                  max(1, int(canvas.height() * dpr)))
    if dpr != 1.0:
        pix.setDevicePixelRatio(dpr)
    painter = QPainter(pix)
    # v2.9.318 — AA sélectif (§2.2) : plus d'AA global ; seules les
    # passes texte/UI réactivent l'AA via _aa_layer.
    _render_scene(canvas, painter)
    painter.end()
    canvas._scene_cache = (key, pix)
    # v2.9.318 — pixmap rendu à (zoom, pan) courants = référence du blit.
    canvas._render_zoom = float(canvas.zoom)
    canvas._render_pan_x = float(canvas.pan_x)
    canvas._render_pan_y = float(canvas.pan_y)
    _emit_render_status(canvas)

    blit = QPainter(canvas)
    blit.drawPixmap(0, 0, pix)
    canvas._draw_hover_tooltip(blit)
    blit.end()


def _emit_render_status(canvas):
    """v2.9.263 — après un rendu réel, le diagnostic imagerie est à
    jour : on prévient le widget (barre de statut) sans attendre un
    survol.  v2.9.263 E4 — seulement si le CONTENU a changé : pendant
    l'orbite/zoom, `render` recrée cette liste de compteurs À CHAQUE
    frame (ils ne changent presque jamais).  Émettre le signal pour
    rien force `_on_hover_changed` à
    reformater la barre de statut à chaque image.  v2.9.319 — partagé
    avec l'adoption asynchrone
    (même signal, même dédoublonnage).
    """
    try:
        _sig = (str(getattr(canvas, "_hover_text", "") or ""),
                repr(getattr(canvas, "_imagery_diag", None)),
                int(getattr(canvas, "_scene_rev", 0)))
        if _sig != getattr(canvas, "_last_render_status_sig", None):
            canvas._last_render_status_sig = _sig
            canvas.hover_changed.emit(_sig[0])
    except Exception as _sig_exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : rafraîchissement barre de statut", _sig_exc)


def _aa_layer(canvas, label, fn, *args):
    """v2.9.318 — comme _safe_layer mais AA activé (passes texte/UI)."""
    painter = args[0] if args else None
    if painter is not None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
    try:
        fn(*args)
    except Exception as _exc:
        seen = getattr(canvas, "_layer_fail_seen", None)
        if seen is None:
            seen = canvas._layer_fail_seen = set()
        if label not in seen:
            seen.add(label)
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : couche « %s » sautée (rendu "
                          "partiel conservé)" % label, _exc)
    finally:
        if painter is not None:
            painter.restore()


def _safe_layer(canvas, label, fn, *args):
    """v2.9.317 — une couche qui lève une exception est SAUTÉE ce
    frame, journalisée UNE fois : plus de scène entière tuée (ni de
    message d'erreur global) parce qu'une seule couche échoue au zoom.
    C'est le blindage « lead dev » : le rendu reste partiel mais
    utilisable, et le diagnostic reste complet."""
    try:
        fn(*args)
    except Exception as _exc:
        seen = getattr(canvas, "_layer_fail_seen", None)
        if seen is None:
            seen = canvas._layer_fail_seen = set()
        if label not in seen:
            seen.add(label)
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : couche « %s » sautée (rendu "
                          "partiel conservé)" % label, _exc)


def _render_scene(canvas, painter):
    # Deep slate background (mining CAD standard)
    painter.fillRect(canvas.rect(), QColor("#171D22"))

    visible_holes = canvas._get_visible_drillholes()
    canvas.displayed_holes_count = len(visible_holes)
    canvas.ignored_holes_count = len(canvas._drillholes) - len(visible_holes)

    if not canvas._drillholes:
        painter.setPen(QColor(COLORS["text_medium"]))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(
            canvas.rect(), Qt.AlignCenter,
            _tr("Aucun forage dans le modèle spatial 3D.\n"
                "Importez des données et calculez la géométrie à "
                "l’étape 3."),
        )
        return

    min_x, max_x, min_y, max_y, min_z, max_z = canvas._get_bounds()
    extent = max(
        max_x - min_x,
        max_y - min_y,
        (max_z - min_z) * max(1.0, canvas.v_exag),
        10.0,
    )
    viewport_min = min(canvas.width(), canvas.height())
    scale = (viewport_min * 0.65) / extent

    # v2.9.141 — précalcule la transformation caméra (trig une fois).
    canvas._setup_frame(scale)

    canvas._hit_segments = []
    # v2.9.263 — DIAGNOSTIC IMAGERIE : compteurs par forage mis à jour à
    # chaque rendu (records présents vs affichés, chargées/absentes/
    # illisibles).  Consommé par la barre de statut de la vue 3D pour
    # distinguer « aucune donnée/rechargement » d'« image présente mais
    # non affichée ».
    # E4 perf — en MOUVEMENT on ne réinitialise PAS `_imagery_diag` : les
    # compteurs (X/Y par forage) restent ceux du dernier rendu À L'ARRÊT
    # (la barre de statut ne clignote pas « 0 image » pendant l'orbite).
    if not _in_motion(canvas):
        canvas._imagery_diag = {}
    # et on ne rallume pas `_imagery_badge_hits` pendant un drag (pas de
    # clic possible) : `_draw_imagery_strips` ne collecte qu'à l'arrêt.
    canvas._imagery_badge_hits = []

    # v2.9.141 — filtre par code : précalcule si le code surligné est
    # présent dans le domaine courant (sinon, pas d'estompage — un code
    # d'un autre domaine ne doit pas griser toute la scène).
    canvas._highlight_target = (
        canvas._highlight_code.strip().upper() if canvas._highlight_code else None)
    canvas._highlight_applies = False
    canvas._highlight_domain = None
    if canvas._highlight_target:
        for dh in visible_holes:
            for inv in canvas._get_intervals_for_domain(dh, canvas.geo_domain):
                if canvas._highlight_target in canvas._interval_highlight_codes(inv, canvas.geo_domain):
                    canvas._highlight_applies = True
                    canvas._highlight_domain = canvas.geo_domain
                    break
            if canvas._highlight_applies:
                break
        # v2.9.260 — SYNC LÉGENDE `structure` : les mesures sont
        # PONCTUELLES (``dh.structure``), donc absentes des intervalles.
        # Sans ce passage, `_highlight_applies` reste False et le filtre
        # par code ne s'estompe JAMAIS dans la vue 3D (retour écran :
        # « je sélectionne en légende structure et rien ne change »).
        if not canvas._highlight_applies:
            # v2.9.260 — FakeCanvas/harnais hors QGIS n'ont pas les
            # helpers structure : repli silencieux (pas de filtre).
            _struct_getter = getattr(
                canvas, "_structure_records_for_domain", None)
            _code_getter = getattr(canvas, "_structure_record_code", None)
            if callable(_struct_getter) and callable(_code_getter):
                for dh in visible_holes:
                    for rec in _struct_getter(dh, "structure"):
                        code = _code_getter(rec)
                        if (code and canvas._highlight_target
                                == str(code).strip().upper()):
                            canvas._highlight_applies = True
                            canvas._highlight_domain = "structure"
                            break
                    if canvas._highlight_applies:
                        break

    # 1. 3D Bounding Box and Graduated Coordinate Axes (XYZ)
    if canvas.show_axes:
        _aa_layer(canvas, "axes_en", canvas._draw_bounding_box,
                    painter, min_x, max_x, min_y, max_y, min_z, max_z, scale)

    # 2. 3D Topographic Surface with Directional Hillshade
    if canvas.show_topography:
        _safe_layer(canvas, "topo", canvas._draw_topography_surface,
                    painter, min_x, max_x, min_y, max_y, scale)

    # 3. Active Section Plane & 3D Corridor Volume Box
    if canvas._active_section_line and (canvas.show_section_plane or canvas.show_corridor):
        _safe_layer(canvas, "section_plane", canvas._draw_section_plane_and_corridor,
                    painter, min_z, max_z, scale)

    # 4. Drillholes (Trajectories & Active Geological Domain)
    if canvas.show_drillholes:
        # v2.9.174 — direction de référence des voies secondaires pour
        # CE frame (la plus longue trajectoire projetée — jamais un
        # forage vu en bout : décalage jamais nul, domaines jamais
        # superposés, retour écran « la 3D bug de malade »).
        canvas._secondary_lane_dir = _frame_lane_direction(
            canvas, visible_holes, scale)
        for dh in visible_holes:
            # v2.9.317 — un forage malformé ne tue plus la scène.
            _safe_layer(canvas, "hole:%s" % getattr(dh, "hole_id", "?"),
                        canvas._draw_drillhole, painter, dh, scale)

    # 5. Non-invasive Selection Calipers (FROM & TO rings on selected interval)
    _safe_layer(canvas, "selection", canvas._draw_selection_highlight,
                painter, scale)

    # 6. Floating in-viewport 3D Legend (Clearance above gizmo)
    # v2.9.175 — LOD orbite : la légende saute pendant le mouvement
    # (sa CONSTRUCTION itère tous les forages × intervalles — retour
    # écran : « très lent, du mal à tourner »).  Elle revient à l'arrêt.
    # v2.9.245 — idem en zoom molette (prédicat partagé _in_motion).
    if canvas.show_legend and not _in_motion(canvas):
        _aa_layer(canvas, "legend", canvas._draw_floating_legend, painter)

    # 7. Orientation Gizmo & Vertical Exaggeration Indicator
    _aa_layer(canvas, "gizmo_en", canvas._draw_gizmo, painter)
    if abs(canvas.v_exag - 1.0) > 0.01:
        _aa_layer(canvas, "exag_badge", canvas._draw_exag_badge, painter)
    # (l'infobulle de survol n'est PAS dans le cache : paint_scene la
    # dessine par-dessus, à chaque image, sans invalider la scène)


def draw_topography_surface(canvas, painter: QPainter, min_x: float, max_x: float, min_y: float, max_y: float, scale: float):
    """Draw 3D topographic ground surface mesh with directional hillshade,
    hypsometric tint, draped grid and optional contour lines (P1/P2).

    v2.9.141 — la grille peut être la SURFACE RÉELLE (MNT raster / CSV
    échantillonné par le widget) ou, en repli, l'interpolation des
    collets (comportement historique).
    """
    grid_3d = canvas._surface_grid
    if not grid_3d:
        # Repli : interpolation IDW sur les collets (aucun MNT fourni),
        # mise en cache par signature des collets (pas de recalcul à
        # chaque image pendant l'orbite).
        sig = tuple(sorted(
            (round(dh.collar.x, 3), round(dh.collar.y, 3),
             round(dh.collar.z, 3))
            for dh in canvas._drillholes
            if dh.collar and math.isfinite(dh.collar.x)
            and math.isfinite(dh.collar.y) and math.isfinite(dh.collar.z)
        ))
        if not sig:
            return
        if sig == getattr(canvas, "_collar_grid_sig", None):
            grid_3d = canvas._collar_grid_cache
        else:
            collars = [(x, y, z) for x, y, z in sig]
            grid_3d = build_surface_grid(
                collars, bounds=bounds_from_points(collars), nx=48, ny=48)
            canvas._collar_grid_sig = sig
            canvas._collar_grid_cache = grid_3d
        if not grid_3d:
            return

    ny = len(grid_3d) - 1
    nx = len(grid_3d[0]) - 1
    if nx < 1 or ny < 1:
        return

    # Altitudes de la surface pour la teinte hypsométrique.
    zs = [grid_3d[i][j][2] for i in range(ny + 1) for j in range(nx + 1)]
    zmin, zmax = min(zs), max(zs)
    zspan = max(zmax - zmin, 1e-6)

    topo_alpha = int(canvas.terrain_opacity_pct * 2.55)
    light_dir = (-0.7071, 0.7071, 1.0)
    l_mag = math.hypot(light_dir[0], math.hypot(light_dir[1], light_dir[2]))
    lx, ly, lz = light_dir[0] / l_mag, light_dir[1] / l_mag, light_dir[2] / l_mag

    # v2.9.141 — ombrage LISSÉ : normales PAR SOMMET (moyenne des faces
    # adjacentes), teinte par quad = moyenne des 4 normales de sommet.
    # Fini l'effet « carré » des facettes plates.  Calculé une fois par
    # grille (mis en cache), indépendant de la caméra.
    cache_key = id(grid_3d)
    if getattr(canvas, "_surface_shade_key", None) != cache_key:
        # 1) normale par face
        face_n = [[(0.0, 0.0, 1.0)] * nx for _ in range(ny)]
        for i in range(ny):
            for j in range(nx):
                p00 = grid_3d[i][j]
                p10 = grid_3d[i + 1][j]
                p01 = grid_3d[i][j + 1]
                v1 = (p10[0] - p00[0], p10[1] - p00[1], p10[2] - p00[2])
                v2 = (p01[0] - p00[0], p01[1] - p00[1], p01[2] - p00[2])
                nx_ = v1[1] * v2[2] - v1[2] * v2[1]
                ny_ = v1[2] * v2[0] - v1[0] * v2[2]
                nz = v1[0] * v2[1] - v1[1] * v2[0]
                m = math.hypot(nx_, math.hypot(ny_, nz))
                if m > 1e-6:
                    face_n[i][j] = (nx_ / m, ny_ / m, nz / m)
        # 2) normale par sommet (somme des 4 faces voisines)
        vert_n = [[(0.0, 0.0, 1.0)] * (nx + 1) for _ in range(ny + 1)]
        for i in range(ny + 1):
            for j in range(nx + 1):
                ax = ay = az = 0.0
                for di in (0, -1):
                    for dj in (0, -1):
                        fi, fj = i + di, j + dj
                        if 0 <= fi < ny and 0 <= fj < nx:
                            ax += face_n[fi][fj][0]
                            ay += face_n[fi][fj][1]
                            az += face_n[fi][fj][2]
                m = math.hypot(ax, math.hypot(ay, az))
                if m > 1e-6:
                    vert_n[i][j] = (ax / m, ay / m, az / m)
        # 3) teinte hypsométrique + ombrage lissé, par quad — couleurs RGB
        #    finales PRÉCALCULÉES (une fois par grille, pas par frame).
        shades = [[0.0] * nx for _ in range(ny)]
        rgb = [[(0, 0, 0)] * nx for _ in range(ny)]
        for i in range(ny):
            for j in range(nx):
                s00, s10 = vert_n[i][j], vert_n[i + 1][j]
                s11, s01 = vert_n[i + 1][j + 1], vert_n[i][j + 1]
                nx_ = (s00[0] + s10[0] + s11[0] + s01[0]) / 4.0
                ny_ = (s00[1] + s10[1] + s11[1] + s01[1]) / 4.0
                nz = (s00[2] + s10[2] + s11[2] + s01[2]) / 4.0
                m = math.hypot(nx_, math.hypot(ny_, nz))
                if m > 1e-6:
                    nx_, ny_, nz = nx_ / m, ny_ / m, nz / m
                hillshade = max(0.0, min(1.0, nx_ * lx + ny_ * ly + nz * lz))
                shades[i][j] = hillshade
                z00, z10 = grid_3d[i][j][2], grid_3d[i + 1][j][2]
                z11, z01 = grid_3d[i + 1][j + 1][2], grid_3d[i][j + 1][2]
                z_avg = (z00 + z10 + z11 + z01) / 4.0
                hr, hg, hb = canvas._hypsometric_color((z_avg - zmin) / zspan)
                shade = max(0.62, 0.6 + 0.4 * hillshade)
                rgb[i][j] = (int(hr * shade), int(hg * shade), int(hb * shade))
        canvas._surface_shade_key = cache_key
        canvas._surface_shades = shades
        canvas._surface_quad_rgb = rgb
        canvas._surface_zmin, canvas._surface_zmax = zmin, zmax

    # Projection des SOMMETS une seule fois (partagée entre quads).
    # v2.9.176 — LOD orbite : en mouvement, 1 sommet sur 2 dans CHAQUE
    # direction → 4× moins de sommets projetés ET de quads triés/dessinés
    # (retour écran : « le MNT est trop lent »).  Le relief complet
    # revient à l'arrêt (repaint dédié au relâchement, v2.9.175).
    _step = 2 if _in_motion(canvas) else 1
    proj = [[None] * (nx + 1) for _ in range(ny + 1)]
    for i in range(0, ny + 1, _step):
        for j in range(0, nx + 1, _step):
            x, y, z = grid_3d[i][j]
            sx, sy, sd = canvas.project_3d(x, y, z, scale)
            proj[i][j] = (sx, sy, sd)

    quads = []
    for i in range(0, ny, _step):
        for j in range(0, nx, _step):
            r, g, b = canvas._surface_quad_rgb[i][j]
            quad_color = QColor(r, g, b, topo_alpha)

            s00 = proj[i][j]
            s10 = proj[i + _step][j]
            s11 = proj[i + _step][j + _step]
            s01 = proj[i][j + _step]
            poly = QPolygonF([
                QPointF(s00[0], s00[1]), QPointF(s10[0], s10[1]),
                QPointF(s11[0], s11[1]), QPointF(s01[0], s01[1]),
            ])
            depth_avg = (s00[2] + s10[2] + s11[2] + s01[2]) / 4.0
            quads.append((depth_avg, quad_color, poly))

    # Peintre : du plus loin (grand depth) au plus proche.  SANS liseré
    # (NoPen) et SANS antialiasing → pas de grille de carrés, pas de
    # couture entre facettes, et plus rapide pendant l'orbite.
    quads.sort(key=lambda q: q[0], reverse=True)
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, False)
    painter.setPen(QPen(Qt.NoPen))
    for _depth, quad_color, poly in quads:
        painter.setBrush(QBrush(quad_color))
        painter.drawPolygon(poly)
    painter.restore()

    # Grille drapée sur le relief (parallaxe quand la caméra bouge).
    if canvas.show_grid_drape:
        grid_pen = QPen(QColor(255, 255, 255, 60), 0.6)
        painter.setPen(grid_pen)
        for i in range(ny + 1):
            for j in range(nx):
                p0 = grid_3d[i][j]
                p1 = grid_3d[i][j + 1]
                s0 = canvas.project_3d(p0[0], p0[1], p0[2], scale)
                s1 = canvas.project_3d(p1[0], p1[1], p1[2], scale)
                painter.drawLine(QPointF(s0[0], s0[1]), QPointF(s1[0], s1[1]))
        for j in range(nx + 1):
            for i in range(ny):
                p0 = grid_3d[i][j]
                p1 = grid_3d[i + 1][j]
                s0 = canvas.project_3d(p0[0], p0[1], p0[2], scale)
                s1 = canvas.project_3d(p1[0], p1[1], p1[2], scale)
                painter.drawLine(QPointF(s0[0], s0[1]), QPointF(s1[0], s1[1]))

    # Isocontours (isohypses) activables.
    if canvas.show_contours:
        contour_pen = QPen(QColor(255, 255, 255, 150), 0.9, Qt.SolidLine)
        painter.setPen(contour_pen)
        segs = canvas._surface_contours(grid_3d, zmin, zmax)
        for lv, segments in segs.items():
            for x0, y0, x1, y1 in segments:
                s0 = canvas.project_3d(x0, y0, lv, scale)
                s1 = canvas.project_3d(x1, y1, lv, scale)
                painter.drawLine(QPointF(s0[0], s0[1]), QPointF(s1[0], s1[1]))


def draw_bounding_box(canvas, painter: QPainter, min_x: float, max_x: float, min_y: float, max_y: float, min_z: float, max_z: float, scale: float):
    """Draw 3D bounding box frame and graduated XYZ coordinate axes."""
    corners = [
        (min_x, min_y, min_z), (max_x, min_y, min_z),
        (max_x, max_y, min_z), (min_x, max_y, min_z),
        (min_x, min_y, max_z), (max_x, min_y, max_z),
        (max_x, max_y, max_z), (min_x, max_y, min_z),
    ]
    sc = [canvas.project_3d(x, y, z, scale) for x, y, z in corners]

    grid_pen = QPen(QColor("#2C3A44"), 1, Qt.DashLine)
    painter.setPen(grid_pen)
    for i in range(4):
        painter.drawLine(QPointF(sc[i][0], sc[i][1]), QPointF(sc[(i + 1) % 4][0], sc[(i + 1) % 4][1]))
        painter.drawLine(QPointF(sc[i + 4][0], sc[i + 4][1]), QPointF(sc[((i + 1) % 4) + 4][0], sc[((i + 1) % 4) + 4][1]))
        painter.drawLine(QPointF(sc[i][0], sc[i][1]), QPointF(sc[i + 4][0], sc[i + 4][1]))

    # v2.9.175 — LOD orbite : graduations et étiquettes texte (les
    # drawText sont les appels QPainter les plus chers) sautées pendant
    # le mouvement ; le cadre et le triède restent.
    if _in_motion(canvas):
        return
    # Graduations / Ticks along X (Easting), Y (Northing), Z (Elevation)
    # v2.9.142 — VALEURS SEULES en 6 pt : plus de lettre d'axe (« X »,
    # « Y », « Z ») répétée sur CHAQUE graduation — l'axe est légendé
    # UNE SEULE fois (« X (m) » au milieu de l'axe), comme demandé
    # en retour écran.
    painter.setFont(QFont("Segoe UI", 6))
    tick_pen = QPen(QColor("#4A5F70"), 1)
    text_pen = QColor("#85929E")

    def _calc_step(span: float) -> float:
        if span <= 1e-3:
            return 10.0
        raw = span / 3.5
        pw = 10.0 ** math.floor(math.log10(raw))
        frac = raw / pw
        if frac < 1.5:
            return 1.0 * pw
        elif frac < 3.5:
            return 2.0 * pw
        elif frac < 7.5:
            return 5.0 * pw
        return 10.0 * pw

    step_x = _calc_step(max_x - min_x)
    step_y = _calc_step(max_y - min_y)
    step_z = _calc_step(max_z - min_z)

    # v2.9.141 — étiquettes X / Y VERTICALES (lisibles de haut en bas),
    # plus horizontales qui se chevauchaient le long des bords.
    def _vlabel(tx, ty, text):
        painter.save()
        painter.translate(tx, ty)
        painter.rotate(90)
        painter.drawText(0, 0, text)
        painter.restore()

    # 1. Graduations X (along bottom South edge: Y = min_y, Z = min_z)
    cur_x = math.ceil(min_x / step_x) * step_x
    while cur_x <= max_x:
        sx, sy, _ = canvas.project_3d(cur_x, min_y, min_z, scale)
        stx, sty, _ = canvas.project_3d(cur_x, min_y - (max_y - min_y) * 0.02, min_z, scale)
        painter.setPen(tick_pen)
        painter.drawLine(QPointF(sx, sy), QPointF(stx, sty))
        painter.setPen(text_pen)
        _vlabel(stx - 4, sty + 10, f"{cur_x:,.0f}".replace(",", " "))
        cur_x += step_x

    # 2. Graduations Y (along bottom West edge: X = min_x, Z = min_z)
    cur_y = math.ceil(min_y / step_y) * step_y
    while cur_y <= max_y:
        sx, sy, _ = canvas.project_3d(min_x, cur_y, min_z, scale)
        stx, sty, _ = canvas.project_3d(min_x - (max_x - min_x) * 0.02, cur_y, min_z, scale)
        painter.setPen(tick_pen)
        painter.drawLine(QPointF(sx, sy), QPointF(stx, sty))
        painter.setPen(text_pen)
        _vlabel(stx - 24, sty + 10, f"{cur_y:,.0f}".replace(",", " "))
        cur_y += step_y

    # 3. Graduations Z (along vertical pillar: X = min_x, Y = min_y)
    cur_z = math.ceil(min_z / step_z) * step_z
    while cur_z <= max_z:
        sx, sy, _ = canvas.project_3d(min_x, min_y, cur_z, scale)
        stx, sty, _ = canvas.project_3d(min_x - (max_x - min_x) * 0.02, min_y, cur_z, scale)
        painter.setPen(tick_pen)
        painter.drawLine(QPointF(sx, sy), QPointF(stx, sty))
        painter.setPen(text_pen)
        painter.drawText(QPointF(stx - 30, sty + 3), f"{cur_z:,.0f}".replace(",", " "))
        cur_z += step_z

    # v2.9.142 — légende d'axe UNE SEULE FOIS par axe (lettre + unité),
    # au milieu de chaque axe, décalée au-delà des valeurs.
    painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
    cap_pen = QColor("#AEB6BF")
    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0
    mid_z = (min_z + max_z) / 2.0
    # X : milieu de l'arête sud.
    ax, ay, _ = canvas.project_3d(mid_x, min_y - (max_y - min_y) * 0.02, min_z, scale)
    painter.setPen(cap_pen)
    _vlabel(ax - 16, ay + 10, "X (m)")
    # Y : milieu de l'arête ouest.
    bx, by, _ = canvas.project_3d(min_x - (max_x - min_x) * 0.02, mid_y, min_z, scale)
    painter.setPen(cap_pen)
    _vlabel(bx - 36, by + 10, "Y (m)")
    # Z : milieu du pilier vertical.
    zx, zy, _ = canvas.project_3d(min_x - (max_x - min_x) * 0.02, min_y, mid_z, scale)
    painter.setPen(cap_pen)
    painter.drawText(QPointF(zx - 44, zy + 3), _tr("Z (m)"))

    # Origin axes triad
    ox, oy, _ = canvas.project_3d(min_x, min_y, min_z, scale)
    alen_x = (max_x - min_x) * 0.18
    alen_y = (max_y - min_y) * 0.18
    alen_z = (max_z - min_z) * 0.18

    xx, xy, _ = canvas.project_3d(min_x + alen_x, min_y, min_z, scale)
    painter.setPen(QPen(QColor("#E74C3C"), 2))
    painter.drawLine(QPointF(ox, oy), QPointF(xx, xy))

    yx, yy, _ = canvas.project_3d(min_x, min_y + alen_y, min_z, scale)
    painter.setPen(QPen(QColor("#2ECC71"), 2))
    painter.drawLine(QPointF(ox, oy), QPointF(yx, yy))

    zx, zy, _ = canvas.project_3d(min_x, min_y, min_z + alen_z, scale)
    painter.setPen(QPen(QColor("#3498DB"), 2))
    painter.drawLine(QPointF(ox, oy), QPointF(zx, zy))


def draw_section_plane_and_corridor(canvas, painter: QPainter, min_z: float, max_z: float, scale: float):
    """Draw active section plane and 3D corridor volume box."""
    line = canvas._active_section_line
    if not line:
        return
    p1x = getattr(line, "x1", getattr(getattr(line, "p1", None), "x", None))
    p1y = getattr(line, "y1", getattr(getattr(line, "p1", None), "y", None))
    p2x = getattr(line, "x2", getattr(getattr(line, "p2", None), "x", None))
    p2y = getattr(line, "y2", getattr(getattr(line, "p2", None), "y", None))
    if p1x is None or p1y is None or p2x is None or p2y is None:
        return

    dx = p2x - p1x
    dy = p2y - p1y
    length = math.hypot(dx, dy)
    if length <= 1e-4:
        return

    # 1. 3D Corridor Volume Box
    if canvas.show_corridor and canvas._active_section_buffer > 0:
        buf = canvas._active_section_buffer
        nx = -dy / length * buf
        ny = dx / length * buf

        c_pts = [
            (p1x - nx, p1y - ny, min_z), (p2x - nx, p2y - ny, min_z),
            (p2x + nx, p2y + ny, min_z), (p1x + nx, p1y + ny, min_z),
            (p1x - nx, p1y - ny, max_z), (p2x - nx, p2y - ny, max_z),
            (p2x + nx, p2y + ny, max_z), (p1x + nx, p1y + ny, max_z),
        ]
        sc_c = [canvas.project_3d(x, y, z, scale) for x, y, z in c_pts]

        faces = [
            [0, 1, 5, 4],
            [1, 2, 6, 5],
            [2, 3, 7, 6],
            [3, 0, 4, 7],
            [4, 5, 6, 7],
            [0, 1, 2, 3],
        ]
        painter.setBrush(QBrush(QColor(230, 126, 34, 26)))
        painter.setPen(QPen(QColor(230, 126, 34, 130), 1, Qt.DotLine))
        for f in faces:
            poly = QPolygonF([QPointF(sc_c[idx][0], sc_c[idx][1]) for idx in f])
            painter.drawPolygon(poly)

    # 2. Section Vertical Plane
    if canvas.show_section_plane:
        c1 = canvas.project_3d(p1x, p1y, max_z, scale)
        c2 = canvas.project_3d(p2x, p2y, max_z, scale)
        c3 = canvas.project_3d(p2x, p2y, min_z, scale)
        c4 = canvas.project_3d(p1x, p1y, min_z, scale)

        poly = QPolygonF([
            QPointF(c1[0], c1[1]), QPointF(c2[0], c2[1]),
            QPointF(c3[0], c3[1]), QPointF(c4[0], c4[1]),
        ])
        painter.setBrush(QBrush(QColor(189, 195, 199, 60)))
        painter.setPen(QPen(QColor(52, 152, 219, 210), 1.8, Qt.DashLine))
        painter.drawPolygon(poly)

        mid_x = (c1[0] + c2[0]) / 2.0
        mid_y = (c1[1] + c2[1]) / 2.0
        painter.setPen(QColor("#5DADE2"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        sec_title = getattr(line, "name", _tr("Plan de coupe"))
        painter.drawText(QPointF(mid_x + 5, mid_y - 4), _tr("Coupe : {}").format(sec_title))


def _pattern_tube_marks(canvas, painter, code, domain, base_color,
                        p_top, p_bot, tube_w, alpha):
    """Motif du Référentiel sur un tube 3D (v2.9.152 — SPEC B-2/D2).

    Marques PERPENDICULAIRES à l'axe (échelons obliques, croix, points)
    en encre contrastée — JAMAIS de traits parallèles : un trait
    parallèle se lit comme une barrette litho (retour écran : « il
    confond barrette avec veine/accessoire »).  La spéc vient de la
    source unique ``core.styles.tube_pattern_render`` (la légende 3D
    consomme la même).  Sans motif → tube plein, rien ici.
    """
    # v2.9.175 — LOD orbite : les marques (≈ 2–10 traits PAR intervalle,
    # principal ET secondaires) sont la 1re source de lenteur à l'orbite.
    # Couleurs et tubes restent ; le détail revient au relâchement.
    if _in_motion(canvas):
        return
    try:
        from ..core.styles import tube_pattern_render
        spec = tube_pattern_render(canvas._style.code_pattern(code, domain))
        if not spec:
            return
        dx = p_bot.x() - p_top.x()
        dy = p_bot.y() - p_top.y()
        length = math.hypot(dx, dy)
        if length < 1e-4:
            return
        ux, uy = dx / length, dy / length          # axe du tube
        nx, ny = -uy, ux                            # perpendiculaire
        # Encre contrastée : foncée sur couleur claire, claire sur foncée.
        ink = base_color.lighter(165) if base_color.lightness() < 110 \
            else base_color.darker(210)
        ink.setAlpha(alpha)
        # v2.9.156 — géométrie PURE et BORNÉE (core/styles.
        # pattern_mark_geometry) : les 10 motifs s'affichent proprement
        # sur tout segment/tube — marques visibles (planchers), jamais
        # hors du segment le long de l'axe (retour écran : « sur
        # certains intervalles moins larges les motifs sortent ou ne
        # s'affichent pas — gère bien nos 10 motifs »).
        from ..core.styles import pattern_mark_geometry
        geo = pattern_mark_geometry(length, tube_w, spec)
        n_marks = geo["n_marks"]
        half = geo["half"]
        axial = geo["axial"]
        mark_w = geo["mark_w"]
        dot_r = geo["dot_r"]
        painter.setPen(QPen(ink, mark_w, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(QBrush(Qt.NoBrush))
        kind = spec.get("kind")
        for i in range(n_marks):
            f = (i + 0.5) / n_marks
            cx = p_top.x() + dx * f
            cy = p_top.y() + dy * f
            if kind == "dot":
                painter.drawEllipse(QPointF(cx, cy), dot_r, dot_r)
                continue
            if kind == "tick":
                tilt = axial * (1.0 if spec.get("tilt", 0.0) >= 0 else -1.0)
                painter.drawLine(
                    QPointF(cx - nx * half - ux * tilt, cy - ny * half - uy * tilt),
                    QPointF(cx + nx * half + ux * tilt, cy + ny * half + uy * tilt))
            elif kind == "double_tick":
                for off in (-tube_w * 0.14, tube_w * 0.14):
                    painter.drawLine(
                        QPointF(cx + ux * off - nx * half, cy + uy * off - ny * half),
                        QPointF(cx + ux * off + nx * half, cy + uy * off + ny * half))
            elif kind == "plus":
                painter.drawLine(
                    QPointF(cx - nx * half, cy - ny * half),
                    QPointF(cx + nx * half, cy + ny * half))
                painter.drawLine(
                    QPointF(cx - ux * axial, cy - uy * axial),
                    QPointF(cx + ux * axial, cy + uy * axial))
            elif kind == "cross_x":
                d = min(half * 0.8, axial if axial > 0 else half * 0.8)
                painter.drawLine(
                    QPointF(cx - nx * d - ux * d, cy - ny * d - uy * d),
                    QPointF(cx + nx * d + ux * d, cy + ny * d + uy * d))
                painter.drawLine(
                    QPointF(cx - nx * d + ux * d, cy - ny * d + uy * d),
                    QPointF(cx + nx * d - ux * d, cy + ny * d - uy * d))
    except Exception as _pattern_exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed(f"Vue 3D : motif sur tube (code={code!r}) — "
                      f"tube plein, dessin poursuivi", _pattern_exc)
        return


def _cached_pen(canvas, color, width, style, alpha=255):
    """v2.9.198 — QPen CACHÉ : en multi-domaines, chaque intervalle
    créait 2-3 QPen (×N domaines ×N forages par image — des dizaines
    de milliers d'allocations Qt pendant l'orbite).  Même clé → même
    objet (setPen copie en interne : le partage est sûr)."""
    cache = getattr(canvas, "_pen_cache", None)
    if cache is None:
        cache = {}
        canvas._pen_cache = cache
    # v2.9.217 — FIX CACHE GELÉ (retour écran : « je clique latérite :
    # rien ne s'estompe, c'est le motif qui brille ; en orbite c'est
    # correct ; peu importe ce que je sélectionne c'est TOUJOURS
    # latérite — 2.9.190 était bien »).  La clé ignorait le VRAI
    # alpha de la couleur : QColor.name() = "#RRGGBB" SANS alpha, et
    # un QColor réel n'a pas d'attribut _alpha (c'était le stub du
    # harnais, plus riche que Qt sur ce point précis — le harnais
    # testait une fiction).  Deux couleurs de même RGB mais d'alphas
    # différents partageaient le MÊME stylo : l'estompage (filtre
    # légende, sélection) était GELÉ au premier rendu.  Correct en
    # orbite seulement — les largeurs LOD diffèrent → autres entrées
    # de cache, gelées à un autre moment.  Bug introduit v2.9.198.
    try:
        c_alpha = int(color.alpha())       # le VRAI alpha (API Qt)
    except AttributeError:
        # objet sans alpha() (stubs) — repli documenté
        c_alpha = int(getattr(color, "_alpha", 255))
    key = (color.name(), c_alpha,
           round(width, 2), int(style), int(alpha))
    pen = cache.get(key)
    if pen is None:
        from qgis.PyQt.QtGui import QPen as _QP
        pen = _QP(color, width, style, Qt.RoundCap)
        cache[key] = pen
    return pen


def _frame_lane_direction(canvas, holes, scale):
    """v2.9.174 — direction de décalage des tubes secondaires, niveau FRAME.

    La PLUS LONGUE trajectoire projetée des forages visibles : jamais
    un forage vu en bout (projection ≈ un point), qui donnerait un
    décalage NUL et superposerait les domaines les uns sur les autres.
    Repli final (1, 0) — horizontal, comme les pistes 2D vues de dessus.
    """
    # seuil 8 px : en dessous, un segment projeté ne porte pas de
    # direction fiable (forage vu en bout) — on garde le repli (1, 0),
    # STABLE d'une frame à l'autre (pas de direction qui saute en orbite)
    best_dx, best_dy, best_len = 1.0, 0.0, 8.0
    for dh in holes or []:
        tr = dh.trajectory or []
        if len(tr) < 2:
            continue
        p0, p1 = tr[0], tr[-1]
        s0 = canvas.project_3d(p0.x, p0.y, p0.z, scale)
        s1 = canvas.project_3d(p1.x, p1.y, p1.z, scale)
        d = math.hypot(s1[0] - s0[0], s1[1] - s0[1])
        if d > best_len:
            best_len = d
            best_dx, best_dy = (-(s1[1] - s0[1]) / d, (s1[0] - s0[0]) / d)
    return (best_dx, best_dy)


def _draw_component_bands(canvas, painter, inv, p_top, p_bot, w, alpha):
    """Composants lithologiques secondaires (v2.9.157) : MÊME GRAMMAIRE
    que la coupe 2D via le layout PARTAGÉ (``core.track_bands.
    component_band_layout``) — retour écran : « il confond
    veine/accessoire et barrette car ils ont le même positionnement ».

      - overlay VEINE      → FILET DIAGONAL « \\ » (bord interne au
        from → bord externe au to) ;
      - overlay ACCESSOIRE → filet « / » de sens OPPOSÉ — deux
        structures ensemble se CROISENT (convention 2D v2.7.11.3) ;
      - reduced (secondaire) → BARRETTE (bande fine parallèle,
        décalée à côté du tube) ;
      - base/split → représentés par le tube principal.

    v2.9.173 — extrait du bloc principal et PARTAGÉ avec les domaines
    SECONDAIRES (retour écran : « tu as volontairement enlevé les
    barrettes, veines, accessoires ? »).  ``w`` = largeur du tube
    porteur (principal : pleine largeur ; secondaire : ×0.5).
    """
    # v2.9.175 — LOD orbite : filets et barrettes sautés pendant le
    # mouvement (retour écran : « très lent, du mal à tourner »).
    if _in_motion(canvas):
        return
    dx = p_bot.x() - p_top.x()
    dy = p_bot.y() - p_top.y()
    length = math.hypot(dx, dy)
    if length <= 1e-4:
        return
    nx = -dy / length
    ny = dx / length
    from ..core.track_bands import component_band_layout
    bands = component_band_layout(inv.components)
    tube_half = w * 0.5
    bar_idx = 0
    for spec in bands:
        if spec.kind in ("base", "split") or not spec.raw_code:
            continue
        s_col = canvas._resolve_code_color(spec.raw_code, "litho")

        # estompage PAR COMPOSANT (règle v2.9.141) : le composant
        # ciblé reste plein, les autres baissent.
        # v2.9.260 — un surlignage `structure` ne doit PAS estomper les
        # composants litho (le filtre ne s'applique qu'à son domaine).
        comp_dim = 1.0
        if (canvas._highlight_applies and canvas._highlight_target
                and getattr(canvas, "_highlight_domain", None) != "structure"):
            if canvas._highlight_target != str(spec.raw_code).strip().upper():
                comp_dim = 0.25
        # v2.9.213 — hors de la plage sélectionnée → estompé
        comp_dim = min(comp_dim, _selection_dim(
            canvas, getattr(inv, "hole_id", ""), inv))
        comp_alpha = int(alpha * comp_dim)

        if spec.kind == "overlay":
            # FILET DIAGONAL — veine « \\ », accessoire « / »
            direction = 1.0 if spec.role == "vein" else -1.0
            a = QPointF(p_top.x() - nx * tube_half * direction,
                        p_top.y() - ny * tube_half * direction)
            b = QPointF(p_bot.x() + nx * tube_half * direction,
                        p_bot.y() + ny * tube_half * direction)
            fw = max(1.6, w * 0.30)
            painter.setPen(QPen(
                QColor(15, 20, 25, int(220 * comp_dim)),
                fw + 1.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(a, b)
            fc = s_col.lighter(115)
            fc.setAlpha(comp_alpha)
            painter.setPen(QPen(fc, max(1.2, fw - 0.6),
                                Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(a, b)
        else:
            # BARRETTE (secondaire) — bande fine parallèle
            side = 1.0 if bar_idx % 2 == 0 else -1.0
            bar_idx += 1
            off_dist = side * (w * 0.28)
            ox = nx * off_dist
            oy = ny * off_dist
            sp_top = QPointF(p_top.x() + ox, p_top.y() + oy)
            sp_bot = QPointF(p_bot.x() + ox, p_bot.y() + oy)
            bar_w = max(2.5, w * 0.35)
            painter.setPen(QPen(
                QColor(15, 20, 25, int(220 * comp_dim)),
                bar_w + 1.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(sp_top, sp_bot)
            s_col.setAlpha(comp_alpha)
            painter.setPen(QPen(s_col, bar_w,
                                Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(sp_top, sp_bot)


def _draw_intercept_sleeves(canvas, painter, dh: DrillHole, scale: float,
                            w: float, offset=(0.0, 0.0)):
    """Manchons d'intercepts : UNE VOIE PAR RÈGLE (v2.9.144/D5).

    v2.9.172 — réutilisable en domaine SECONDAIRE : ``offset`` décale
    toute la voie en écran (tube parallèle au principal), ``w`` module
    l'épaisseur des manchons (principal : pleine largeur ; secondaire :
    ×0.5, comme les autres tubes secondaires).

    Retour sans bruit si le module de seuils est absent (pack réduit)
    — SILENCE JUSTIFIÉ : fonctionnalité optionnelle.
    """
    try:
        from ..core.threshold_rule import (
            active_rules as _active_rules,
            intercept_lane_offsets as _lane_offsets)
        rules_3d = _active_rules(canvas._threshold_rules)
    except ImportError:
        return
    n_rules = len(rules_3d)
    if not n_rules:
        return
    lane_offsets = _lane_offsets(n_rules)
    ox, oy = offset
    for inv in canvas._get_intervals_for_domain(dh, "intercepts"):
        for k, rule in enumerate(rules_3d):
            if not canvas._threshold_rule_matches(rule, inv, dh):
                continue
            pt_top = canvas._interpolate_dh_point(dh, inv.from_depth)
            pt_bot = canvas._interpolate_dh_point(dh, inv.to_depth)
            if not pt_top or not pt_bot:
                continue
            s_top = canvas.project_3d(pt_top.x, pt_top.y, pt_top.z, scale)
            s_bot = canvas.project_3d(pt_bot.x, pt_bot.y, pt_bot.z, scale)
            p_top = QPointF(s_top[0] + ox, s_top[1] + oy)
            p_bot = QPointF(s_bot[0] + ox, s_bot[1] + oy)
            # Voie de la règle k : décalage perpendiculaire (écran).
            dx = p_bot.x() - p_top.x()
            dy = p_bot.y() - p_top.y()
            seg_len = math.hypot(dx, dy)
            nx = -dy / seg_len if seg_len > 1e-4 else 0.0
            ny = dx / seg_len if seg_len > 1e-4 else 1.0
            # Manchon plus fin quand il y a plusieurs règles.
            ring_w = max(1.8, w * 0.30 / (1.0 + 0.25 * (n_rules - 1)))
            lane_gap = ring_w + max(2.5, w * 0.22)
            off = lane_offsets[k] * lane_gap
            q_top = QPointF(p_top.x() + nx * off, p_top.y() + ny * off)
            q_bot = QPointF(p_bot.x() + nx * off, p_bot.y() + ny * off)
            rcol = QColor(rule.get("color") or "#00E5FF")
            painter.setPen(QPen(rcol, ring_w, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(q_top, q_bot)
            # anneaux aux extrémités (repère From/To)
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.setPen(QPen(rcol, 1.2))
            painter.drawEllipse(q_top, ring_w * 0.9, ring_w * 0.9)
            painter.drawEllipse(q_bot, ring_w * 0.9, ring_w * 0.9)


def _selection_dim(canvas, hole_id, inv) -> float:
    """v2.9.213 — estompage PAR INTERVALLE dans le forage sélectionné.

    Retour écran : « quand je sélectionne altération basalte, au lieu
    de basalte bien visible ça met en évidence d'autres trucs » — le
    forage ENTIER restait plein (ses autres lithologies comprises).
    Désormais, dans le forage choisi, SEULS les intervalles qui
    chevauchent la plage sélectionnée (FROM–TO) restent pleins ; le
    reste du forage s'estompe comme les autres forages (25 % —
    convention maison v2.9.141/212).  Sans plage (forage sélectionné
    seul, p. ex. depuis la carte) → tout le forage reste plein.
    """
    # v2.9.216 — LE FILTRE LÉGENDE A LA PRIORITÉ (retour écran : «
    # je sélectionne un code dans la liste mais ça met en évidence
    # que les motifs, veines ou barrettes — 2.9.190 était bien »).
    # Les DEUX estompages se marchaient dessus : une sélection
    # restée active (clic précédent dans la scène ou sur la coupe
    # 2D) plafonnait TOUT à 25 % hors de sa plage — les tubes que le
    # filtre devait allumer restaient éteints, seuls les filets de
    # la zone sélectionnée brillaient.  En 2.9.190 l'estompage de
    # sélection n'existait pas : le filtre régnait seul.  Désormais
    # UN SEUL estompage à la fois : clic légende = le filtre règne
    # (la sélection ne garde que sa manchette dorée) ; sans filtre,
    # la sélection estompe comme avant.
    if getattr(canvas, "_highlight_code", None):
        return 1.0
    sel_id = canvas._selected_hole_id
    if not sel_id or str(hole_id) != str(sel_id):
        return 1.0
    f = canvas._selected_from_m
    t = canvas._selected_to_m
    if f is None or t is None:
        return 1.0
    try:
        if getattr(inv, "from_depth", None) is None and getattr(
                inv, "depth", None) is not None:
            # v2.9.260 étape 3 — mesures PONCTUELLES `structure` :
            # le record n'a qu'une profondeur, pas un intervalle.
            d = float(inv.depth)
            return 1.0 if (float(f) <= d <= float(t)) else 0.25
        # v2.9.268 — sélection PONCTUELLE : un clic sur une mesure
        # géotechnique à profondeur seule (densité) donne from == to.
        # Un intervalle de longueur NULLE ne « recouvre » jamais rien
        # (overlap = 0 → tout le reste estompé à 25 %).  On compare
        # donc par CONTENU du point, comme pour `structure`.
        if abs(float(t) - float(f)) < 1e-6:
            return (1.0 if float(inv.from_depth) <= float(f)
                    <= float(inv.to_depth) else 0.25)
        overlap = (min(float(inv.to_depth), float(t))
                   - max(float(inv.from_depth), float(f)))
    except (TypeError, ValueError, AttributeError):
        return 1.0
    return 1.0 if overlap > 0.0 else 0.25


# ---------------------------------------------------------------------------
# v2.9.260 étape 3 — STRUCTURES en 3D (mesures ponctuelles sur trajectoire).
#
# Les symboles sont calculés dans les COORDONNÉES RÉELLES (X Est, Y Nord,
# Z haut) à partir de dip/dip_direction.  Ils ne dépendent JAMAIS de
# l'azimut/pendage du forage : deux mesures avec le même dip/dip_direction
# sur deux forages différents ont exactement la même inclinaison réelle.
# alpha/beta seuls ne définissent pas un plan dans le repère monde sans la
# référence d'orientation du carotte : comme en étape 2, ils restent dans
# l'infobulle et la mesure est dessinée en point neutre (aucune invention).
# ---------------------------------------------------------------------------
def _structure_world_dip_vector(dip: float, dip_direction: float):
    """Vecteur unitaire monde du bas-pendage / de la plongée (sens positif
    vers le bas).

    Convention : azimut mesuré depuis le Nord, sens horaire (X = Est,
    Y = Nord, Z = haut).  Le vecteur pointe vers le bas-pendage (Z < 0),
    exactement la géométrie dessinée en 2D.
    """
    dip_rad = math.radians(float(dip))
    dd_rad = math.radians(float(dip_direction))
    cos_dip = math.cos(dip_rad)
    return (
        math.sin(dd_rad) * cos_dip,
        math.cos(dd_rad) * cos_dip,
        -math.sin(dip_rad),
    )


def _structure_tooltip(canvas, dh: DrillHole, rec, code: str) -> str:
    """Infobulle compacte d'une mesure de structure (données réellement
    saisies, aucune valeur inventée)."""
    label = str(canvas._resolve_code_label(code, "structure") or "").strip()
    type_label = (
        f"{code} · {label}"
        if label and label.casefold() != code.casefold() else str(code))
    lines = [
        _tr("Forage : {} [Structures]").format(dh.hole_id),
        _tr("Profondeur : {0:.2f} m").format(float(rec.depth)),
        _tr("Type : {}").format(type_label),
    ]
    if rec.dip is not None and rec.dip_direction is not None:
        lines.append(_tr(
            "Pendage {dip}° / direction {dd}°").format(
                dip=float(rec.dip), dd=float(rec.dip_direction)))
    elif rec.alpha is not None and rec.beta is not None:
        lines.append(_tr(
            "Alpha {a}° / bêta {b}°").format(
                a=float(rec.alpha), b=float(rec.beta)))
    if str(getattr(rec, "confidence", "") or "").strip():
        lines.append(_tr("Confiance : {value}").format(
            value=str(getattr(rec, "confidence", "")).strip()))
    if str(getattr(rec, "comment", "") or "").strip():
        lines.append(_tr("Commentaire : {}").format(
            str(getattr(rec, "comment", "")).strip()))
    return "\n".join(lines)


def _structure_hole_normal(dh: DrillHole, point) -> tuple:
    """Normale horizontale monde de la trajectoire du forage à ce point.

    Sert à décaler les symboles trop rapprochés (règle de densité) SANS
    toucher à leur orientation : le décalage est purement latéral dans le
    plan horizontal.
    """
    tr = getattr(dh, "trajectory", None) or []
    if len(tr) < 2:
        return (1.0, 0.0, 0.0)
    depth = float(getattr(point, "depth", 0.0) or 0.0)
    p0, p1 = tr[0], tr[-1]
    for i in range(len(tr) - 1):
        a, b = tr[i], tr[i + 1]
        da, db = float(getattr(a, "depth", 0.0)), float(getattr(b, "depth", 0.0))
        if (da <= depth <= db) or (db <= depth <= da):
            p0, p1 = a, b
            break
    dx = float(p1.x - p0.x)
    dy = float(p1.y - p0.y)
    norm = math.hypot(dx, dy)
    if norm < 1e-9:
        return (1.0, 0.0, 0.0)
    return (dy / norm, -dx / norm, 0.0)


def _draw_structure_marker(
        canvas, painter, wx, wy, wz, family, down, colour,
        seg_world, arrow_world, radius_px, scale, offset, record_hits,
        rec, tip, alpha):
    """Dessine un symbole de structure (point/trait/flèche) à la position
    monde (wx, wy, wz), auquel on ajoute le décalage écran ``offset``.

    - planaire/inconnu orienté : POINT + TRAIT 3D court et ÉPAIS, orienté
      selon la ligne de plus grande pente (bas-pendage réel).  Pas de
      disque : c'est trop volumineux avec beaucoup de forages.
    - linéaire : flèche 3D courte et ÉPAISSE selon plongée/azimut réel.
    - composite/non-orientable/sans orientation : point simple.

    La taille est calée en PIXELS (indépendante de l'échelle monde) :
    ``seg_world``/``arrow_world`` sont convertis par l'appelant pour que
    le trait mesure ~``seg_px`` et la flèche ~``arrow_px`` à l'écran.
    Les traits sont volontairement COURTS mais ÉPAIS : petit et gras se
    lit mieux de loin qu'une grande forme à trait fin (100 forages).
    """
    sx, sy, sz = canvas.project_3d(wx, wy, wz, scale)
    cx = sx + offset[0]
    cy = sy + offset[1]
    colour = QColor(colour)
    colour.setAlpha(alpha)
    m = QPointF(cx, cy)
    ink_light = colour.lighter(155)
    ink_dark = colour.darker(210)

    # Forme pleine selon la famille / les données disponibles.
    if family in ("planar", "unknown") and down is not None:
        # Trait 3D court au bas-pendage (segment réel, pas écran fixe) :
        # même dip/dip_direction = même inclinaison, quel que soit l'axe
        # du forage ou l'angle de caméra.
        ex, ey, _ = canvas.project_3d(
            wx + down[0] * seg_world, wy + down[1] * seg_world,
            wz + down[2] * seg_world, scale)
        e = QPointF(ex + offset[0], ey + offset[1])
        painter.setPen(QPen(ink_light, max(2.4, 3.0),
                            Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(m, e)

    elif family == "linear" and down is not None:
        # Flèche courte selon la plongée réelle (trend/plunge).
        ex, ey, _ = canvas.project_3d(
            wx + down[0] * arrow_world, wy + down[1] * arrow_world,
            wz + down[2] * arrow_world, scale)
        e = QPointF(ex + offset[0], ey + offset[1])
        u = e - m
        ulen = math.hypot(u.x(), u.y())
        if ulen > 1e-6:
            u = u / ulen
        painter.setPen(QPen(ink_light, max(2.4, 3.0),
                            Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(m, e)
        head = max(6.5, radius_px * 1.9)
        side = head * 0.5
        bx, by = e.x() - u.x() * head, e.y() - u.y() * head
        painter.setBrush(QBrush(colour))
        painter.setPen(QPen(ink_light, 1.2))
        painter.drawPolygon(QPolygonF([
            e,
            QPointF(bx - u.y() * side, by + u.x() * side),
            QPointF(bx + u.y() * side, by - u.x() * side)]))

    # Éventuel point de base / point neutre (composite, non-orientable,
    # alpha/bêta seuls, LOD en mouvement).
    if (family in ("planar", "unknown") or family != "linear"
            or down is None):
        pr = max(2.5, (radius_px * 0.85 if down is not None else radius_px))
        painter.setBrush(QBrush(colour))
        painter.setPen(QPen(ink_dark, max(0.9, 1.1)))
        painter.drawEllipse(m, pr, pr)

    if record_hits:
        hit_r = max(5.0, radius_px + 1.0)
        hole_id = str(getattr(canvas, "_structure_current_hole_id", "") or "")
        canvas._hit_segments.append((
            QPointF(cx - hit_r, cy), QPointF(cx + hit_r, cy), sz,
            hole_id, float(rec.depth), float(rec.depth), tip))


def draw_structure_markers(canvas, painter, dh: DrillHole, scale: float,
                           w: float, alpha: int, offset=(0.0, 0.0),
                           ipt=None, record_hits=True):
    """Dessine les mesures `structure` d'un forage (étape 3).

    - position : point exact ``depth`` interpolé sur la trajectoire ;
    - orientation : monde (N/E/Z), jamais relative au forage ;
    - familles : planaire/inconnu-orienté = point + trait 3D court,
      linéaire = flèche compacte, composite/non-orientable = point ;
    - taille : COMPACTE (traits épais), pour rester lisible avec beaucoup
      de forages sans envahir la scène ;
    - densité : les symboles trop rapprochés sont décalés latéralement
      dans le plan horizontal, ou réduits en dernier recours.
    """
    records = canvas._structure_records_for_domain(dh, "structure")
    if not records:
        return
    ipt = ipt or (lambda depth: canvas._interpolate_dh_point(dh, depth))
    # v2.9.260 — LOD : seuls les MOUVEMENTS de caméra simplifient la
    # scène (structure → point, comme les tubes passent à un trait
    # simple).  À L'ARRÊT, on garde TOUJOURS le trait/flèche orienté,
    # même en « Projet complet » : la légende (dessinée à l'arrêt) reste
    # ainsi fidèle au rendu.  Pas de simplification « >X forages » propre
    # à `structure` : les litho/altérations/minéralisations ne se
    # réduisent pas en points à l'arrêt, donc autant rester cohérent —
    # c'est la portée (``_get_visible_drillholes``) qui limite déjà le
    # nombre d'éléments dessinés.
    _simplified = _in_motion(canvas)
    # v2.9.260 — SYMBOLE COMPACT + GRAS : longueur réduite, trait épais.
    # (retour écran : « trop gros pour 100 forages ; il faut réduire les
    # symboles et épaissir les traits »).  Un petit trait de 2–3 px bien
    # épais reste identifiable sans occuper d'espace visuel.
    radius_px = max(2.5, min(5.0, w * 0.45))
    seg_px = max(8.0, min(14.0, w * 1.8))
    arrow_px = max(10.0, min(16.0, w * 2.0))
    seg_world = max(0.6, seg_px / max(float(scale), 1e-9))
    arrow_world = max(0.8, arrow_px / max(float(scale), 1e-9))
    min_gap = max(9.0, seg_px * 0.65)
    occupied = []
    canvas._structure_current_hole_id = dh.hole_id
    for rec in records:
        depth = float(getattr(rec, "depth", 0.0) or 0.0)
        pt = ipt(depth)
        if pt is None:
            continue
        code = canvas._structure_record_code(rec)
        if not code:
            continue
        family = structure_family(code)
        has_orient = (
            getattr(rec, "dip", None) is not None
            and getattr(rec, "dip_direction", None) is not None)
        down = (_structure_world_dip_vector(
            float(rec.dip), float(rec.dip_direction)) if has_orient else None)
        wx, wy, wz = float(pt.x), float(pt.y), float(pt.z)
        offvec = _structure_hole_normal(dh, pt)
        sx, sy, sz = canvas.project_3d(wx, wy, wz, scale)
        cx = sx + offset[0]
        cy = sy + offset[1]
        for _attempt in range(8):
            free = all(math.hypot(cx - ox, cy - oy) >= min_gap
                       for ox, oy in occupied)
            if free:
                break
            step_world = (radius_px + 4.0) / max(float(scale), 1e-9)
            sign = 1.0 if _attempt % 2 == 0 else -1.0
            wx += offvec[0] * step_world * sign
            wy += offvec[1] * step_world * sign
            sx, sy, sz = canvas.project_3d(wx, wy, wz, scale)
            cx = sx + offset[0]
            cy = sy + offset[1]
        occupied.append((cx, cy))
        colour = canvas._resolve_code_color(code, "structure")
        tip = _structure_tooltip(canvas, dh, rec, code)
        # v2.9.141/216 — filtre par code (clic légende) PARITÉ 2D : une
        # structure d'une autre famille s'estompe quand son code n'est
        # pas le code surligné.
        # v2.9.260 — le filtre `structure` ne s'applique que si le code
        # surligné appartient bien au domaine structure (un clic litho ne
        # doit pas estomper les structures).
        dim = 1.0
        if (getattr(canvas, "_highlight_applies", False)
                and getattr(canvas, "_highlight_domain", None) == "structure"
                and getattr(canvas, "_highlight_target", None)):
            if str(canvas._highlight_target).strip().upper() != str(code).upper():
                dim = 0.25
        dim = min(dim, _selection_dim(canvas, dh.hole_id, rec))
        alpha_dim = int(alpha * dim)
        # LOD mouvement + échelle projet : point simple (rapide) ; les
        # traits/flèches reviennent à l'arrêt en coupe/sélection ou sur
        # une scène légère (même principe que motifs/légende).
        if _simplified:
            down = None
        _draw_structure_marker(
            canvas, painter, wx, wy, wz, family, down, colour,
            seg_world, arrow_world, radius_px, scale, offset,
            record_hits, rec, tip, alpha_dim)


# ---------------------------------------------------------------------------
# E3 — Imagerie 3D : repère-badge sur la trajectoire, photo au clic.
# v2.9.263 — le ruban texturé est abandonné (positionnement 3D / clipping
# illisible en détail et coûteux).  Seul le badge-lettre matériau reste
# sur le trou (gris = fichier trouvé, orange = absent) ; cliquer ouvre la
# photo en grand (ui/view_3d_imagery_viewer.py).  Générique : aucun nom,
# plage, matériau, organisation ni taille d'image n'est supposé.
# ---------------------------------------------------------------------------
def draw_geotech_3d(canvas, painter, dh: DrillHole, scale: float,
                    w: float, alpha: int, kind: str, ipt=None,
                    offset=(0.0, 0.0), record_hits=True):
    """RQD / récupération / densité le long de la trajectoire 3D (v2.9.267).

    Même échelle et mêmes couleurs que la coupe 2D : ``geotech_legend_scale``
    + ``geotech_colour`` — une seule convention, donc la 3D dit la même
    chose que la 2D.  Additif : aucun autre domaine n'est touché.

    - intervalle (``from``/``to``) : segment épais colorié entre les bornes ;
    - point (``depth``) : disque colorié à la profondeur exacte ;
    - SURVOL / CLIC : mêmes segments que les autres domaines
      (``canvas._hit_segments``) → infobulle au survol et sélection
      d'intervalle au clic (retour écran : « pas de survol comme les
      autres tables »).
    """
    from ..core.geotech import (
        geotech_anchor, geotech_colour, geotech_depth_text, geotech_kind,
        geotech_label, geotech_legend_scale, geotech_unit_for,
        geotech_value_text)
    kind = geotech_kind(kind)
    if not kind:
        return
    records = [
        record for record in (getattr(dh, "geotech", None) or [])
        if geotech_kind(getattr(record, "kind", "")) == kind]
    if not records:
        return
    ipt = ipt or (lambda depth: canvas._interpolate_dh_point(dh, depth))
    visible = getattr(canvas, "_get_visible_drillholes", None)
    allrecs = [
        record for hole in (visible() if callable(visible) else [])
        for record in (getattr(hole, "geotech", None) or [])
        if geotech_kind(getattr(record, "kind", "")) == kind]
    lo, hi, _unit = geotech_legend_scale(kind, allrecs or records)
    radius = max(2.0, min(4.0, float(w) * 0.5))
    pen_w = max(2.0, float(w) * 0.8)
    # Infobulle = MÊMES lignes que la coupe 2D (``geotech_tooltip``) :
    # « DH01 · 0–10 m » puis « RQD : 92 % », commentaire éventuel.
    label = _tr(geotech_label(kind))
    for record in records:
        colour = QColor(geotech_colour(float(record.value), kind, lo, hi))
        colour.setAlpha(alpha)
        tip = ""
        if record_hits:
            unit = geotech_unit_for(kind, record)
            lines = [
                f"{dh.hole_id} · {geotech_depth_text(record)}",
                _tr("{label} : {value}").format(
                    label=label,
                    value=geotech_value_text(
                        float(record.value), kind, unit))]
            if kind == "density" and not str(unit or "").strip():
                lines.append(_tr("Unité par défaut : g/cm³"))
            comment = str(getattr(record, "comment", "") or "").strip()
            if comment:
                lines.append(comment)
            tip = "\n".join(lines)
        if getattr(record, "is_interval", False):
            top = ipt(float(record.from_m))
            bot = ipt(float(record.to_m))
            if top is None or bot is None:
                continue
            st = canvas.project_3d(top.x, top.y, top.z, scale)
            sb = canvas.project_3d(bot.x, bot.y, bot.z, scale)
            p_top = QPointF(st[0] + offset[0], st[1] + offset[1])
            p_bot = QPointF(sb[0] + offset[0], sb[1] + offset[1])
            painter.setPen(QPen(colour, pen_w))
            painter.drawLine(p_top, p_bot)
            if record_hits:
                canvas._hit_segments.append((
                    p_top, p_bot,
                    (float(record.from_m) + float(record.to_m)) / 2.0,
                    dh.hole_id, float(record.from_m), float(record.to_m), tip))
        else:
            anchor = geotech_anchor(record)
            if anchor is None:
                continue
            pt = ipt(float(anchor))
            if pt is None:
                continue
            sp = canvas.project_3d(pt.x, pt.y, pt.z, scale)
            p_pt = QPointF(sp[0] + offset[0], sp[1] + offset[1])
            painter.setPen(QPen(colour, 1.0))
            painter.setBrush(QBrush(colour))
            painter.drawEllipse(p_pt, radius, radius)
            if record_hits:
                # marqueur ponctuel : court segment horizontal (même
                # astuce que les mesures `structure`) — un segment de
                # longueur NULLE ne serait jamais survolé par
                # ``find_hover_tooltip`` (il exige ``len_sq > 0``).
                hit_r = max(5.0, radius + 1.0)
                canvas._hit_segments.append((
                    QPointF(p_pt.x() - hit_r, p_pt.y()),
                    QPointF(p_pt.x() + hit_r, p_pt.y()), float(anchor),
                    dh.hole_id, float(anchor), float(anchor), tip))


_IMAGERY_BADGE_PX = 16.0


def _imagery_3d_source_dir(canvas) -> str:
    """Dossier de référence pour les liens relatifs (repli : projet).

    v2.9.263 — la 2D résout via ``imagery_source_dir_provider`` (le
    dossier du CSV courant) ; la 3D lisait seulement l'attribut direct
    ``_imagery_source_dir`` (jamais posé) → mêmes fichiers, chemins
    résolus différemment.  On passe par le même provider que la 2D.
    """
    provider = getattr(canvas, "imagery_source_dir_provider", None)
    if callable(provider):
        try:
            return str(provider() or "")
        except Exception as _src_exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : dossier source imagerie", _src_exc)
    return str(getattr(canvas, "_imagery_source_dir", "") or "")


def _draw_imagery_badge(painter, mid_xy, record, has_image):
    """Badge-lettre matériau sur la trajectoire, toujours lisible.

    Gris-bleu = fichier résolu ; orange = fichier absent (le clic montre
    l'erreur dans le visualiseur).  Aucune valeur/plage codée en dur.
    """
    try:
        from .section_imagery import _material_badge_letter
        letter = _material_badge_letter(
            getattr(record, "material_label", "") or "")
    except Exception as _badge_exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : badge imagerie — fallback lettres",
                      _badge_exc)
        _BADGE = {"core": "C", "rc": "R", "auger": "A",
                  "pit": "P", "other": "O"}
        letter = str(_BADGE.get(
            str(getattr(record, "material_label", "") or "").casefold(), ""))
    if not letter:
        letter = "?"
    try:
        size = _IMAGERY_BADGE_PX
        rect = QRectF(mid_xy[0] - size / 2.0, mid_xy[1] - size / 2.0,
                      size, size)
        color = QColor("#5D6D7E") if has_image else QColor("#F39C12")
        painter.save()
        pen = QPen(color, 1.4, Qt.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(18, 20, 26, 205)))
        painter.drawRoundedRect(rect, 3.0, 3.0)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(max(8, int(size * 0.58)))
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect, Qt.AlignCenter, letter)
        painter.restore()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : badge imagerie", _exc)


def _imagery_file_present(canvas, project, raw_path, source_dir) -> bool:
    """Présence du fichier photo, mise en cache pendant l'interaction.

    v2.9.263 — la boucle 3D tourne à chaque frame d'orbite/zoom.  Statuer
    chaque fichier à chaque frame coûte (disque local, mais surtout
    antivirus/réseau — retour écran « ça rame »).  Le cache est invalidé
    quand la scène change (`_scene_rev` : import, référentiel, données) ;
    sans changement, on ne refait jamais `os.path.isfile`.
    """
    rev = int(getattr(canvas, "_scene_rev", 0) or 0)
    cache = getattr(canvas, "_imagery_presence_cache", None)
    if cache is None or cache.get("_rev") != rev:
        cache = {"_rev": rev}
        canvas._imagery_presence_cache = cache
    key = tuple(sorted(
        str(getattr(paths, attr, None) or "")
        for paths in ([getattr(project, "paths", None)] if project else [])
        for attr in ("project_dir", "data_import_dir", "assets_dir"))) \
        + (str(source_dir or ""), str(raw_path or ""))
    if key in cache:
        present, ts = cache[key]
        if time.monotonic() - ts < 0.25:
            return bool(present)
    from ..core.image_paths import resolve_image_path
    present = bool(resolve_image_path(project, raw_path, source_dir))
    cache[key] = (present, time.monotonic())
    return present


def _imagery_secondary_offset(canvas, dh, scale):
    """Décalage écran des badges quand l'Imagerie est un domaine secondaire.

    En « Coupe active »/« Sélection seule », les domaines simultanés sont
    dessinés côte à côte.  Si l'Imagerie est le domaine principal, ses
    badges restent sur la trajectoire ; si elle est secondaire, ils sont
    décalés perpendiculairement comme les autres voies (même direction de
    référence du frame, même parité) — jamais superposés au tube.

    Générique : ne dépend d'aucun nom/plage/matériau/fichier.
    """
    doms = getattr(canvas, "active_domains", None) or []
    if (getattr(canvas, "scope_mode", "all") not in ("section", "selection")
            or "imagery" not in doms or doms[0] == "imagery"):
        return 0.0, 0.0
    idx = doms.index("imagery")
    sign = 1.0 if idx % 2 == 1 else -1.0
    slot = (idx + 1) // 2
    gap = max(1.5, float(getattr(canvas, "stroke_width", 10.0) or 10.0)) * 2.2
    off = sign * slot * gap
    fdx, fdy = getattr(canvas, "_secondary_lane_dir", (1.0, 0.0))
    dx0, dy0 = fdx, fdy
    tr = dh.trajectory or []
    if len(tr) >= 2:
        st = canvas.project_3d(tr[0].x, tr[0].y, tr[0].z, scale)
        sb = canvas.project_3d(tr[-1].x, tr[-1].y, tr[-1].z, scale)
        dt = math.hypot(sb[0] - st[0], sb[1] - st[1])
        if dt > 8.0:
            dx0 = -(sb[1] - st[1]) / dt
            dy0 = (sb[0] - st[0]) / dt
            if dx0 * fdx + dy0 * fdy < 0.0:
                dx0, dy0 = -dx0, -dy0
    return dx0 * off, dy0 * off


def _draw_imagery_strips(canvas, painter, dh, scale, ipt,
                         offset=(0.0, 0.0)):
    """Badges Imagerie 3D (un par intervalle) le long de la trajectoire.

    ``offset`` = décalage écran en pixels (0,0 = centré sur le trou ;
    sinon voie secondaire côte à côte).
    """
    ox, oy = float(offset[0]), float(offset[1])
    records = sorted(
        getattr(dh, "imagery", None) or [],
        key=lambda rec: (float(rec.from_m), float(rec.to_m)))
    diag = getattr(canvas, "_imagery_diag", None)
    if diag is None:
        diag = {}
        canvas._imagery_diag = diag
    if dh.hole_id not in diag:
        diag[dh.hole_id] = {
            "records": len(records), "rendered": 0, "loaded": 0,
            "missing": 0, "unreadable": 0, "skipped_culling": 0,
            "no_point": 0, "zero_len": 0}
    if not records:
        return
    # E4 perf — LOD : pendant l'orbite/zoom, les badges (gros poste de
    # dessin : N badges × projection + cercle + texte) sont des MARQUES
    # de détail, comme les motifs/labels.  On les saute pendant le
    # mouvement ; ils reviennent au relâchement (même règle de LOD que
    # la légende).  Le diagnostic `_imagery_diag` reste celui de l'arrêt.
    if _in_motion(canvas):
        return
    entry = diag[dh.hole_id]
    project = getattr(canvas, "_project_ref", None)
    source_dir = _imagery_3d_source_dir(canvas)
    for record in records:
        f = min(float(record.from_m), float(record.to_m))
        t = max(float(record.from_m), float(record.to_m))
        if t - f < 1e-6:
            entry["zero_len"] += 1
            continue
        mid = (f + t) / 2.0
        pt = ipt(mid)
        if not pt:
            entry["no_point"] += 1
            continue
        sp = canvas.project_3d(pt.x, pt.y, pt.z, scale)
        bx = float(sp[0]) + ox
        by = float(sp[1]) + oy
        has_image = _imagery_file_present(
            canvas, project, getattr(record, "image_path", ""), source_dir)
        if has_image:
            entry["loaded"] += 1
        else:
            entry["missing"] += 1
        _draw_imagery_badge(painter, (bx, by), record, has_image)
        entry["rendered"] += 1
        # E4 perf — la colle des badges (QPointF + enregistrement par
        # image) se fait À L'ARRÊT seulement ; en mouvement la fonction
        # a déjà retourné juste au-dessus (LOD badge), donc il ne reste
        # que les tuples utiles au clic/survol.
        hits = getattr(canvas, "_imagery_badge_hits", None)
        if hits is not None:
            mid_xy = QPointF(bx, by)
            hits.append((
                mid_xy, _IMAGERY_BADGE_PX / 2.0 + 4.0,
                dh.hole_id, f, t, record))
        # Infobulle 3D (réutilise le mécanisme de survol des segments).
        if not _in_motion(canvas):
            try:
                mat = str(getattr(record, "material_label", "") or "other")
                tip = (f"{dh.hole_id} · {f:g}–{t:g} m"
                       f"\n{_tr('Imagerie')} · {mat} · "
                       f"{_tr('Clic : ouvrir la photo')}")
                canvas._hit_segments.append((
                    QPointF(bx - 2.0, by),
                    QPointF(bx + 2.0, by),
                    float(sp[2]), dh.hole_id, f, t, tip))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Vue 3D : survol badge imagerie", _exc)



def _imagery_label_clear(canvas, hole_id, label_rect) -> bool:
    """Vrai si ``label_rect`` ne recouvre aucun badge Imagerie du forage.

    v2.9.263 — le badge C/P/O/A/R est posé sur la trajectoire ; le nom du
    forage ne doit pas le masquer.  Test d'intersection écran générique :
    ne dépend d'aucune profondeur, plage, nom de fichier ni matériau.
    """
    for center, radius, hid, _f, _t, _rec in (
            getattr(canvas, "_imagery_badge_hits", None) or []):
        if hid != hole_id:
            continue
        badge = QRectF(
            float(center.x()) - float(radius),
            float(center.y()) - float(radius),
            float(radius) * 2.0, float(radius) * 2.0)
        if badge.intersects(label_rect):
            return False
    return True


def _short_label(canvas, hole_id):
    """v2.9.285 — étiquette compacte 3D (source unique core.short_ids)."""
    sig = tuple(sorted(
        h.hole_id for h in getattr(canvas, "_drillholes", []) or []))
    cache = getattr(canvas, "_short_label_cache", None)
    if cache is None or cache[0] != sig:
        from ..core.short_ids import compact_labels
        cache = (sig, compact_labels(sig))
        canvas._short_label_cache = cache
    return cache[1].get(hole_id, hole_id)


def draw_drillhole(canvas, painter: QPainter, dh: DrillHole, scale: float):
    """Draw a drillhole with exact geological referential styles (JORC standards)."""
    if not dh.trajectory:
        return

    # v2.9.245 — prédicat de mouvement partagé (orbite OU zoom molette)
    _dragging = _in_motion(canvas)

    # v2.9.198 — CACHE D'INTERPOLATION par forage : la même profondeur
    # est interpolée par CHAQUE domaine (principal + N secondaires) —
    # en multi-domaines, 3× le même calcul et 3× les allocations.
    # v2.9.318 (§2.3) : le cache SURVIT aux frames — attaché au canvas,
    # invalidé seulement par _scene_rev ou un changement de jeu de
    # forages ; plus reconstruit à chaque rendu.
    _ipt_cache = getattr(canvas, "_ipt_cache_persist", None)
    if (_ipt_cache is None
            or getattr(canvas, "_ipt_rev", None)
            != getattr(canvas, "_scene_rev", 0)
            or getattr(canvas, "_ipt_holes_id", None)
            != id(canvas._drillholes)):
        _ipt_cache = canvas._ipt_cache_persist = {}
        canvas._ipt_rev = getattr(canvas, "_scene_rev", 0)
        canvas._ipt_holes_id = id(canvas._drillholes)
    _ipt_cached = getattr(canvas, "_ipt_stats", None)

    def _ipt(depth):
        # v2.9.320 — CLÉ = FORAGE + profondeur.  La persistance v2.9.318
        # avait gardé la clé « profondeur seule » de v2.9.198 (qui était
        # LOCALE à chaque forage) : à profondeur égale, le forage B
        # recevait le point 3D du forage A → tubes qui reliaient deux
        # amas de forages (« trait imaginaire ») et domaines hors
        # trajectoire.  La persistance exige le forage dans la clé.
        key = (getattr(dh, "hole_id", None) or id(dh), round(depth, 3))
        pt = _ipt_cache.get(key, _MISSING)
        if pt is _MISSING:
            pt = interpolate_dh_point(dh, depth)
            _ipt_cache[key] = pt
            if _ipt_cached is not None:
                _ipt_cached[0] += 1
        return pt

    # v2.9.175 — CULLING écran : la trajectoire ENTÈREEMENT hors champ
    # (avec marge) → forage sauté.  En orbite sur un projet de 300
    # forages, la moitié est souvent hors cadre : moitié de travail
    # par frame (retour écran : « très lent, du mal à tourner »).
    try:
        _vpw = float(canvas.width())
        _vph = float(canvas.height())
        _minx = _miny = 1e18
        _maxx = _maxy = -1e18
        for _pt in dh.trajectory:
            _sx, _sy, _ = canvas.project_3d(_pt.x, _pt.y, _pt.z, scale)
            if _sx < _minx: _minx = _sx
            if _sx > _maxx: _maxx = _sx
            if _sy < _miny: _miny = _sy
            if _sy > _maxy: _maxy = _sy
        if (_maxx < -60.0 or _minx > _vpw + 60.0
                or _maxy < -60.0 or _miny > _vph + 60.0):
            return
    except Exception as _exc:
        # dimensions/projection indisponibles (ex. tests hors QGIS) :
        # prudence — on dessine le forage complet plutôt que le sauter.
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : culling écran du forage "
                      f"{getattr(dh, 'hole_id', '?')} (dessin complet)", _exc)

    alpha = int(canvas.tube_opacity_pct * 2.55)
    # v2.9.211/212 — MISE EN ÉVIDENCE PAR SÉLECTION (retour écran : «
    # réduire l'opacité des autres et mettre le choisi en évidence »).
    # Quand un intervalle/forage est sélectionné, les AUTRES forages
    # s'estompent : le sélectionné garde sa pleine force (l'opacité
    # des tubes — 95 % par défaut) et sa manchette dorée le couronne.
    # v2.9.212 — 25 %, la MÊME valeur que le filtre par clic légende
    # (v2.9.141) : une seule convention d'estompage dans la vue —
    # l'archéologie Git a confirmé que c'était la valeur que
    # l'utilisateur connaissait déjà.  Le réflexe 2D s'applique : on
    # distingue en baissant le fond, pas en criant plus fort.
    # Un clic dans le vide / re-clic ramène tout à l'égalité.
    _sel_id = canvas._selected_hole_id
    _sel_ids = getattr(canvas, "_selected_hole_ids", None) or []
    # v2.9.216 — priorité au filtre légende (cf. _selection_dim) :
    # avec un code surligné, TOUS les forages restent visibles — le
    # filtre montre le code PARTOUT, il ne doit pas être écrasé par
    # une sélection restée active.
    if (_sel_id or _sel_ids) and not getattr(canvas, "_highlight_code",
                                             None):
        _focused = (dh.hole_id == _sel_id) or (dh.hole_id in _sel_ids)
        if not _focused:
            alpha = max(18, int(alpha * 0.25))
    w = max(1.5, canvas.stroke_width)

    # 1. Base Trajectory Axis
    for i in range(len(dh.trajectory) - 1):
        p0, p1 = dh.trajectory[i], dh.trajectory[i + 1]
        s0 = canvas.project_3d(p0.x, p0.y, p0.z, scale)
        s1 = canvas.project_3d(p1.x, p1.y, p1.z, scale)
        pt0, pt1 = QPointF(s0[0], s0[1]), QPointF(s1[0], s1[1])
        painter.setPen(QPen(QColor(120, 135, 145, int(alpha * 0.6)), max(1.0, w * 0.35)))
        painter.drawLine(pt0, pt1)

    # 2. Intervals — v2.9.166 DOMAINES MULTIPLES
    # Le domaine PRINCIPAL (canvas.geo_domain) est dessiné par le code
    # existant ci-dessous (tube centré, pleine largeur).  Les domaines
    # SECONDAIRES sont dessinés ICI, avant (sous le principal), avec
    # un tube plus fin et un décalage perpendiculaire — comme les
    # pistes de la coupe 2D.
    _all_domains = canvas.active_domains
    # v2.9.173 — garde de RENDU : les domaines simultanés n'existent
    # qu'en scope « Coupe active »/« Sélection seule » (v2.9.171).  En
    # « Projet complet », UNE seule voie même si un ancien état traînait
    # (retour écran : « en projet complet ça s'affiche en double, comme
    # si c'était en coupe active »).
    if getattr(canvas, "scope_mode", "all") not in ("section", "selection"):
        _all_domains = _all_domains[:1]
    if len(_all_domains) > 1:
        _w0 = max(1.5, canvas.stroke_width)
        _gap = _w0 * 2.2
        # v2.9.174 — normale PAR FORAGE : SA propre trajectoire projetée
        # (collet → fond).  Avant : la direction venait du PREMIER forage
        # visible — vu en bout (projection ≈ un point, typique en orbite
        # sur des forages quasi verticaux), le décalage retombait à ZÉRO
        # et TOUS les domaines secondaires se dessinaient PILE sur le
        # tube principal (retour écran : « la 3D bug de malade »).  La
        # direction est maintenant recalculée par forage, avec repli sur
        # la direction de référence du frame, et le SIGNE est aligné sur
        # elle (les secondaires restent du même côté d'un forage à
        # l'autre, comme des pistes).
        _fdx, _fdy = getattr(canvas, "_secondary_lane_dir", (1.0, 0.0))
        _dx0, _dy0 = _fdx, _fdy
        _tr = dh.trajectory or []
        if len(_tr) >= 2:
            _st = canvas.project_3d(_tr[0].x, _tr[0].y, _tr[0].z, scale)
            _sb = canvas.project_3d(_tr[-1].x, _tr[-1].y, _tr[-1].z, scale)
            _dt = math.hypot(_sb[0] - _st[0], _sb[1] - _st[1])
            if _dt > 8.0:  # assez long pour une direction stable
                _dx0 = -(_sb[1] - _st[1]) / _dt
                _dy0 = (_sb[0] - _st[0]) / _dt
                # même côté que la référence (pas de miroir entre forages)
                if _dx0 * _fdx + _dy0 * _fdy < 0.0:
                    _dx0, _dy0 = -_dx0, -_dy0
        for _di, _dom in enumerate(_all_domains[1:], start=1):
            if _dom == "trajectory":
                continue
            # E3 — Imagerie secondaire : déjà dessinée centrée sur la
            # trajectoire (pas de piste gauche/droite) ; on ne la
            # redessine pas en tube décalé.
            if _dom == "imagery":
                continue
            _sign = 1.0 if _di % 2 == 1 else -1.0
            _slot = (_di + 1) // 2
            _off = _sign * _slot * _gap
            _ox = _dx0 * _off
            _oy = _dy0 * _off
            # v2.9.260 étape 3 — STRUCTURES SECONDAIRES : symboles fins
            # décalés à côté du domaine principal (comme les autres
            # familles) ; le rendu passe par le même helper point-wise.
            # v2.9.267 — GÉOTECH SECONDAIRE : piste fine décalée à côté du
            # domaine principal (mêmes couleurs, mêmes infobulles).
            if _dom in ("rqd", "recovery", "density"):
                draw_geotech_3d(
                    canvas, painter, dh, scale,
                    max(2.0, _w0 * 0.65), alpha, _dom,
                    ipt=_ipt, offset=(_ox, _oy),
                    record_hits=not _dragging)
                continue
            if _dom == "structure":
                draw_structure_markers(
                    canvas, painter, dh, scale,
                    max(2.0, _w0 * 0.65), alpha,
                    offset=(_ox, _oy), ipt=_ipt,
                    record_hits=not _dragging)
                continue
            # v2.9.172 — INTERCEPTS SECONDAIRES : manchons fins décalés
            # (avant : ``continue`` silencieux → cocher « Intercepts »
            # en secondaire ne dessinait RIEN, retour écran « je
            # sélectionne intercept et litho je vois des mélanges »).
            if _dom == "intercepts":
                _draw_intercept_sleeves(
                    canvas, painter, dh, scale,
                    max(2.0, _w0 * 0.65), offset=(_ox, _oy))
                continue
            _ivs2 = canvas._get_intervals_for_domain(dh, _dom)
            # v2.9.176 — ×0.65 (avant ×0.5) : retour écran « les motifs et
            # autres ont du mal à sortir en multidomaines, la taille est
            # passée à ×0.5 ».  À ×0.5 (5 px), les marques de motif
            # s'étalent sur 5 px et les filets/barrettes fondent — plus
            # fins que le principal, mais LISIBLES.
            _cw = max(2.0, _w0 * 0.65)
            for inv in _ivs2:
                pt_top = _ipt(inv.from_depth)
                pt_bot = _ipt(inv.to_depth)
                if not pt_top or not pt_bot:
                    continue
                s_top = canvas.project_3d(pt_top.x, pt_top.y, pt_top.z, scale)
                s_bot = canvas.project_3d(pt_bot.x, pt_bot.y, pt_bot.z, scale)
                p_top = QPointF(s_top[0] + _ox, s_top[1] + _oy)
                p_bot = QPointF(s_bot[0] + _ox, s_bot[1] + _oy)

                # v2.9.214 — ALPHA PAR INTERVALLE pour les pistes
                # secondaires (retour écran : « quand je clique sur une
                # litho ou altération, c'est la veine ou le motif qui
                # est mis en évidence »).  Les tubes de voies et leurs
                # MOTIFS recevaient l'alpha PLEIN du forage — sur le
                # forage sélectionné, hors de la plage choisie, ils
                # restaient brillants pendant que le principal
                # s'estompait.  Même règle que le principal désormais :
                # hors plage → 25 % (les composants « \ »/« / » ont
                # déjà leur propre estompage interne via comp_dim).
                _ivl_alpha = int(alpha * _selection_dim(
                    canvas, dh.hole_id, inv))
                # v2.9.173 — richesse COMPLÈTE restaurée (retour écran :
                # « tu as volontairement enlevé les motifs, les barrettes,
                # veines, accessoires ? »).  v2.9.170 les avait simplifiés
                # (retour « surchargé » de l'époque) ; depuis v2.9.171 le
                # simultané est LIMITÉ aux scopes Coupe/Sélection (peu de
                # forages) : le détail y est la raison d'être.  MÊMES voies
                # multi-codes, MÊMES motifs, MÊME intensité, MÊME grammaire
                # de composants que le mode domaine seul — juste plus fin
                # (×0.5) et décalé.
                _mc = canvas._interval_codes(inv, _dom)
                _lanes = None
                # v2.9.177 — LITHO EXCLUE des voies parallèles : ses
                # multi-codes sont les COMPOSANTS (hôte + veine +
                # accessoire + secondaire) dont la grammaire est le TUBE
                # + filets « \ »/« / » + barrettes
                # (_draw_component_bands), comme en domaine seul.  Avant,
                # un intervalle litho à 2 composants se séparait en 2
                # tubes parallèles (retour écran : « il sépare en deux
                # tubes ce qui n'existait pas »).  Les voies restent la
                # grammaire des altérations/minéralisations (AM-06).
                if _dom in ("alterations", "mineralizations") and len(_mc) > 1:
                    _lanes = [
                        (c, canvas._resolve_code_color(c, _dom),
                         # intensité PAR CODE (altérations), comme le principal
                         canvas._code_intensity_factor(inv, c)
                         if _dom == "alterations" else 1.0)
                        for c in _mc]

                if _lanes and len(_lanes) > 1:
                    _n = len(_lanes)
                    _dx2 = p_bot.x() - p_top.x()
                    _dy2 = p_bot.y() - p_top.y()
                    _l2 = math.hypot(_dx2, _dy2)
                    _nx2 = -_dy2 / _l2 if _l2 > 1e-4 else 0.0
                    _ny2 = _dx2 / _l2 if _l2 > 1e-4 else 1.0
                    for _k, (_lc, _lcol, _lfac) in enumerate(_lanes):
                        _frac = _k - (_n - 1) / 2.0
                        _lw = max(1.0, _cw * float(_lfac or 1.0))
                        _lo = _frac * (_cw * 1.2)
                        _lt = QPointF(p_top.x() + _nx2 * _lo, p_top.y() + _ny2 * _lo)
                        _lb = QPointF(p_bot.x() + _nx2 * _lo, p_bot.y() + _ny2 * _lo)
                        # v2.9.175 — LOD orbite : trait unique par voie.
                        if _dragging:
                            _lc2 = _lcol.lighter(115)
                            _lc2.setAlpha(_ivl_alpha)
                            painter.setPen(_cached_pen(
                                canvas, _lc2, _lw, Qt.SolidLine))
                            painter.drawLine(_lt, _lb)
                        else:
                            _lb2 = _lcol.darker(135)
                            _lb2.setAlpha(_ivl_alpha)
                            painter.setPen(_cached_pen(
                                canvas, _lb2, _lw + 0.6, Qt.SolidLine))
                            painter.drawLine(_lt, _lb)
                            _lc2 = _lcol.lighter(115)
                            _lc2.setAlpha(_ivl_alpha)
                            painter.setPen(_cached_pen(
                                canvas, _lc2, max(0.8, _lw - 0.4),
                                Qt.SolidLine))
                            painter.drawLine(_lt, _lb)
                        # MOTIF sur CHAQUE voie (v2.9.173 : restauré) —
                        # v2.9.176 : plancher 7 px pour la GÉOMÉTRIE des
                        # marques (sinon elles fondent sur un tube fin).
                        if _dom in ("litho", "alterations"):
                            _pattern_tube_marks(
                                canvas, painter, _lc, _dom, _lcol,
                                _lt, _lb, max(_lw, 7.0), _ivl_alpha)
                else:
                    # intensité d'intervalle (altérations), comme le principal
                    _fac = (canvas._interval_intensity_factor(inv)
                            if _dom == "alterations" else 1.0)
                    _cw_eff = max(1.2, _cw * float(_fac or 1.0))
                    col = canvas._resolve_domain_color(inv, _dom)
                    # v2.9.175 — LOD orbite : trait unique.
                    if _dragging:
                        cc = col.lighter(115)
                        cc.setAlpha(_ivl_alpha)
                        painter.setPen(_cached_pen(
                            canvas, cc, _cw_eff, Qt.SolidLine))
                        painter.drawLine(p_top, p_bot)
                    else:
                        cb = col.darker(135)
                        cb.setAlpha(_ivl_alpha)
                        painter.setPen(_cached_pen(
                            canvas, cb, _cw_eff + 0.6, Qt.SolidLine))
                        painter.drawLine(p_top, p_bot)
                        cc = col.lighter(115)
                        cc.setAlpha(_ivl_alpha)
                        painter.setPen(_cached_pen(
                            canvas, cc, max(0.8, _cw_eff - 0.3),
                            Qt.SolidLine))
                        painter.drawLine(p_top, p_bot)
                    # MOTIF du code principal de l'intervalle (v2.9.173)
                    # v2.9.176 : plancher 7 px (marques lisibles).
                    if _dom in ("litho", "alterations"):
                        _pattern_tube_marks(
                            canvas, painter,
                            canvas._extract_code_from_interval(inv, _dom),
                            _dom, col, p_top, p_bot, max(_cw_eff, 7.0),
                            _ivl_alpha)

                # v2.9.173 — COMPOSANTS litho en secondaire : veine « \ »,
                # accessoire « / », barrette — MÊME grammaire que le
                # principal (helper partagé `_draw_component_bands`).
                if _dom == "litho" and inv.components and len(inv.components) > 1:
                    # v2.9.176 : plancher 7 px — filets veine/accessoire et
                    # barrettes lisibles sur un tube secondaire fin.
                    _draw_component_bands(
                        canvas, painter, inv, p_top, p_bot, max(_cw, 7.0), alpha)

                # v2.9.183 — SEGMENTS DE SURVOL du domaine secondaire :
                # avant, AUCUN n'était enregistré — survoler le tube
                # d'altération montrait l'infobulle du domaine PRINCIPAL
                # (ou rien) : « le survol ne passe pas sur le domaine
                # associé ».  L'infobulle suit maintenant le tube SOUS
                # le curseur, comme les pistes de la coupe 2D.
                if not _dragging:
                    canvas._hit_segments.append((
                        p_top, p_bot, (s_top[2] + s_bot[2]) / 2.0,
                        dh.hole_id, inv.from_depth, inv.to_depth,
                        canvas._build_tooltip(dh.hole_id, inv, _dom)))

    # 2. Intervals for the Active Geological Domain (principal)
    domain = canvas.geo_domain
    intervals = canvas._get_intervals_for_domain(dh, domain)
    # v2.9.185/189 — légende d'éléments déjà posée pour ce forage.
    _assay_lanes_labeled = set()

    if intervals and domain not in ("trajectory", "intercepts"):
        for inv in intervals:
            pt_top = _ipt(inv.from_depth)
            pt_bot = _ipt(inv.to_depth)
            if pt_top and pt_bot:
                s_top = canvas.project_3d(pt_top.x, pt_top.y, pt_top.z, scale)
                s_bot = canvas.project_3d(pt_bot.x, pt_bot.y, pt_bot.z, scale)
                p_top, p_bot = QPointF(s_top[0], s_top[1]), QPointF(s_bot[0], s_bot[1])
                depth_avg = (s_top[2] + s_bot[2]) / 2.0

                # v2.9.276 — DÉCIMATION SOUS LE PIXEL (retour écran : 369 trous,
                # « ça bug de fou, je peux pas zoomer »).  Zoom arrière, un
                # intervalle de <1 px à l'écran est invisible : le tracer en
                # tube (contour + remplissage) coûte un appel QPainter pour
                # rien, des dizaines de milliers de fois.  On le saute ; la
                # trajectoire du forage (boucle 1) reste tracée, donc le trou
                # demeure visible.  Zoom avant, l'intervalle redevient ≥1 px et
                # se dessine normalement.  Purement visuel, dégradé gracieux.
                if (p_top - p_bot).manhattanLength() < _PIXEL_CULL:
                    continue

                # v2.9.141 — TENEURS : UNE boule PAR ÉLÉMENT (multi-teneurs
                # comme la 2D), décalées côte à côte perpendiculairement au
                # forage.  Plus « à part Cu le reste ne s'affiche pas ».
                # v2.9.142 — elems = choix unitaire du combo OU miroir 2D.
                if domain == "assays":
                    elems = canvas.active_assay_elements()
                    n_elem = len(elems)
                    # v2.9.189 — légende des éléments UNE fois par forage
                    # (empilée, sans chevauchement), pas par boule.
                    if (not _assay_lanes_labeled
                            and getattr(canvas, "show_labels", True)
                            and not _dragging):
                        _draw_element_key(canvas, painter, elems, p_top)
                    for k, el in enumerate(elems):
                        val = canvas._element_value(inv, el)
                        if val is None:
                            continue
                        canvas._draw_assay_bubble(
                            painter, dh.hole_id, inv, el, val,
                            p_top, p_bot, lane=k, n_lanes=n_elem)
                        _assay_lanes_labeled.add(k)
                    continue

                # v2.9.141/218 — filtre par code (clic légende) : le TUBE
                # répond à son code PRIMAIRE, les COMPOSANTS aux leurs —
                # PARITÉ 2D (retour écran : « quand je sélectionne QTZ
                # vein, en 2D c'est bien LA VEINE ; en 3D il sélectionne
                # aussi la litho hôte — pareil pour une double litho ou
                # une barrette »).  Cliquer une veine QTZ : le tube hôte
                # s'estompe, SEULS ses filets « \ » brillent — comme la
                # coupe 2D.  Cliquer un code primaire (GMS) : ses tubes
                # restent pleins.  (Le passage v2.9.215 « tous les codes »
                # avait été motivé par le bug du cache gelé v2.9.217 —
                # le vrai coupable — et suréclairait l'hôte.)
                dim = 1.0
                if (canvas._highlight_applies and canvas._highlight_target
                        and getattr(canvas, "_highlight_domain", None)
                        != "structure"):
                    primary = canvas._extract_code_from_interval(
                        inv, domain).strip().upper()
                    if primary and canvas._highlight_target != primary:
                        dim = 0.25
                # v2.9.213 — hors de la plage sélectionnée → estompé
                dim = min(dim, _selection_dim(canvas, dh.hole_id, inv))
                alpha_dim = int(alpha * dim)

                # v2.9.141 — MULTI : minéralisations/altérations (plusieurs
                # codes) → tubes parallèles CÔTE À CÔTE, nettement séparés,
                # comme les voies de la 2D.  Chaque voie = (code, QColor,
                # facteur_intensité).
                lanes = None
                if domain == "alterations":
                    mc = canvas._interval_codes(inv, domain)
                    if len(mc) > 1:
                        lanes = [(c, canvas._resolve_code_color(c, domain),
                                  canvas._code_intensity_factor(inv, c)) for c in mc]
                elif domain == "mineralizations":
                    mc = canvas._interval_codes(inv, domain)
                    if len(mc) > 1:
                        lanes = [(c, canvas._resolve_code_color(c, domain), 1.0) for c in mc]

                if lanes and len(lanes) > 1:
                    n = len(lanes)
                    dx = p_bot.x() - p_top.x()
                    dy = p_bot.y() - p_top.y()
                    length = math.hypot(dx, dy)
                    nx = -dy / length if length > 1e-4 else 0.0
                    ny = dx / length if length > 1e-4 else 1.0
                    # v2.9.141 — MÊME base que le tube simple : largeur =
                    # stroke_width × intensité.  « Fort » séparé est donc
                    # toujours ≥ « modéré » simple (cohérence 2D).
                    for k, (lane_code, mcol, factor) in enumerate(lanes):
                        frac = k - (n - 1) / 2.0
                        lane_w = max(1.5, w * float(factor or 1.0))
                        off = frac * (w * 1.5)
                        ox, oy = nx * off, ny * off
                        mt_top = QPointF(p_top.x() + ox, p_top.y() + oy)
                        mt_bot = QPointF(p_bot.x() + ox, p_bot.y() + oy)
                        # v2.9.141 — estompage PAR VOIE : la voie ciblée
                        # reste pleine, les autres baissent (avant, les
                        # voies restaient toutes pleines : alpha forcé à
                        # 255 et dim calculé sur l'intervalle entier).
                        lane_dim = 1.0
                        if (canvas._highlight_applies
                                and canvas._highlight_target
                                and getattr(canvas, "_highlight_domain",
                                            None) != "structure"):
                            if canvas._highlight_target != str(lane_code).strip().upper():
                                lane_dim = 0.25
                        # v2.9.213 — hors de la plage sélectionnée → estompé
                        lane_dim = min(lane_dim,
                                       _selection_dim(canvas, dh.hole_id, inv))
                        lane_alpha = int(alpha * lane_dim)
                        # v2.9.175 — LOD orbite : trait unique par voie.
                        if _dragging:
                            cc = mcol.lighter(115)
                            cc.setAlpha(lane_alpha)
                            painter.setPen(QPen(cc, lane_w, Qt.SolidLine, Qt.RoundCap))
                            painter.drawLine(mt_top, mt_bot)
                        else:
                            painter.setPen(QPen(QColor(15, 20, 25, lane_alpha),
                                                lane_w + 1.4, Qt.SolidLine, Qt.RoundCap))
                            painter.drawLine(mt_top, mt_bot)
                            cb = mcol.darker(135)
                            cb.setAlpha(lane_alpha)
                            painter.setPen(QPen(cb, lane_w + 0.6, Qt.SolidLine, Qt.RoundCap))
                            painter.drawLine(mt_top, mt_bot)
                            cc = mcol.lighter(115)
                            cc.setAlpha(lane_alpha)
                            painter.setPen(QPen(cc, max(1.0, lane_w - 0.6), Qt.SolidLine, Qt.RoundCap))
                            painter.drawLine(mt_top, mt_bot)
                        # v2.9.158 — MOTIF SUR CHAQUE VOIE (son code, sa
                        # couleur) : avant, le ``continue`` des voies
                        # multiples sautait les motifs — les altérations
                        # multi-codes n'en affichaient AUCUN (retour
                        # écran : « certaines altérations n'ont rien »).
                        if domain in ("litho", "alterations"):
                            _pattern_tube_marks(
                                canvas, painter, lane_code, domain, mcol,
                                mt_top, mt_bot, lane_w, lane_alpha)
                    # v2.9.198 — segments de survol SAUTÉS pendant
                    # l'orbite (aucun survol en mouvement : des
                    # milliers de tuples par image pour rien).
                    if not _dragging:
                        tip = canvas._build_tooltip(dh.hole_id, inv, domain)
                        canvas._hit_segments.append((
                            p_top, p_bot, depth_avg,
                            dh.hole_id, inv.from_depth, inv.to_depth, tip,
                        ))
                    continue

                color = canvas._resolve_domain_color(inv, domain)

                # v2.9.141 — altérations : largeur du tube selon l'intensité
                # (faible → fin, forte → épais), comme la coupe 2D (AM-03).
                w_eff = w
                if domain == "alterations":
                    w_eff = max(1.5, w * canvas._interval_intensity_factor(inv))

                # 3D cylindrical shading (darker border + lighter core = true 3D cylinder)
                # v2.9.175 — LOD orbite : trait unique pendant le mouvement
                # (le liseré double les appels — il revient à l'arrêt).
                if _dragging:
                    c_core = color.lighter(115)
                    c_core.setAlpha(alpha_dim)
                    painter.setPen(_cached_pen(
                        canvas, c_core, w_eff, Qt.SolidLine))
                    painter.drawLine(p_top, p_bot)
                else:
                    c_border = color.darker(135)
                    c_border.setAlpha(alpha_dim)
                    painter.setPen(_cached_pen(
                        canvas, c_border, w_eff + 1.2, Qt.SolidLine))
                    painter.drawLine(p_top, p_bot)

                    c_core = color.lighter(115)
                    c_core.setAlpha(alpha_dim)
                    painter.setPen(_cached_pen(
                        canvas, c_core, max(1.0, w_eff - 0.8),
                        Qt.SolidLine))
                    painter.drawLine(p_top, p_bot)

                # v2.9.150 (SPEC B-2/D2) — MOTIF du Référentiel sur le tube :
                # surcharge en tirets (même source que la carte QGIS —
                # core.styles.line_dash_pattern) en encre contrastée.
                # Accessibilité daltoniens : la lithologie ne se lit plus
                # uniquement par la couleur.
                if domain in ("litho", "alterations"):
                    _pattern_tube_marks(
                        canvas, painter,
                        canvas._extract_code_from_interval(inv, domain),
                        domain, color, p_top, p_bot, w_eff, alpha_dim)

                # Composants lithologiques secondaires (v2.9.157) :
                # MÊME GRAMMAIRE QUE LA COUPE 2D via le layout PARTAGÉ
                # (core/track_bands.component_band_layout) — veine « \\ »,
                # accessoire « / », barrette.  v2.9.173 — dessin extrait
                # dans `_draw_component_bands` (PARTAGÉ avec les domaines
                # secondaires, même grammaire partout).
                if domain == "litho" and inv.components and len(inv.components) > 1:
                    _draw_component_bands(
                        canvas, painter, inv, p_top, p_bot, w, alpha)

                if not _dragging:
                    tip = canvas._build_tooltip(dh.hole_id, inv, domain)
                    canvas._hit_segments.append((
                        p_top, p_bot, depth_avg,
                        dh.hole_id, inv.from_depth, inv.to_depth, tip,
                    ))

    # 2bis. Intercepts (règles de seuil) — v2.9.143 : UNE VOIE PAR RÈGLE.
    # Avant, chaque règle matchante dessinait son manchon AU MÊME
    # endroit → 2 règles = tubes superposés, illisibles.  La coupe 2D
    # donne à chaque règle SA colonne (``intercept_slot_layout``) ; la
    # 3D fait pareil : voies parallèles côte à côte, décalées
    # perpendiculairement au forage, la règle k garde TOUJOURS la même
    # voie d'un forage à l'autre (couleur de slot cohérente).
    # v2.9.144 (D5) — positions de voies via ``intercept_lane_offsets``
    # (core.threshold_rule, source unique partagée 2D/3D).
    # v2.9.172 — dessin extrait dans ``_draw_intercept_sleeves``
    # (partagé principal/secondaire).
    if domain == "intercepts":
        _draw_intercept_sleeves(canvas, painter, dh, scale, w)

    # 2ter. STRUCTURES (domaine principal) — v2.9.260 étape 3 : mesures
    # ponctuelles à la profondeur exacte, disques/flèches monde.
    if domain == "structure":
        draw_structure_markers(
            canvas, painter, dh, scale, w, alpha,
            offset=(0.0, 0.0), ipt=_ipt, record_hits=not _dragging)

    # v2.9.267 — géotechnique 3D : RQD / récupération / densité le long de
    # la trajectoire, mêmes couleurs que la coupe 2D (additif).
    if domain in ("rqd", "recovery", "density"):
        draw_geotech_3d(canvas, painter, dh, scale, w, alpha, domain,
                        ipt=_ipt, record_hits=not _dragging)

    # E3 — Imagerie 3D : ruban texturé centré sur la trajectoire.
    # v2.9.263 — dessiné APRÈS les tubes/domaines : les photos et les
    # contours « image manquante » restent lisibles au lieu d'être
    # recouverts par le tube gris (retour écran « la majorité des images
    # ne s'affichent pas en 3D »).  Une seule fois, même si « imagery »
    # est principal ou secondaire ; en portée « Projet complet », la
    # règle « un seul domaine » s'applique aussi.
    if (getattr(canvas, "scope_mode", "all") in ("section", "selection")
            and "imagery" in canvas.active_domains) or (
            (canvas.active_domains or ["litho"])[0] == "imagery"):
        _imagery_off = _imagery_secondary_offset(canvas, dh, scale)
        _draw_imagery_strips(
            canvas, painter, dh, scale, _ipt, offset=_imagery_off)

    # 3. Collar Marker Disc
    if canvas.show_collars and dh.collar:
        sc = canvas.project_3d(dh.collar.x, dh.collar.y, dh.collar.z, scale)
        c_pt = QPointF(sc[0], sc[1])
        is_in_section = dh.hole_id in canvas._section_hole_ids
        collar_color = QColor("#E67E22") if is_in_section else QColor("#F1C40F")
        painter.setBrush(QBrush(collar_color))
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawEllipse(c_pt, 4.0, 4.0)

        # Borehole ID label — v2.9.141 : placé SOUS le collet (vers le bas),
        # centré, pour ne pas gêner la lecture du trou.
        # v2.9.175 — LOD orbite : un drawText PAR forage (300 forages =
        # 300 textes/frame) — sauté pendant le mouvement.
        # v2.9.263 — badge Imagerie : le label ne doit JAMAIS recouvrir les
        # premiers badges (retour écran « les noms masquent les 1ers m »).
        # On choisit dynamiquement le côté libre (bas par défaut, haut en
        # repli) — générique, aucune profondeur/nom codé en dur.
        if canvas.show_labels and not _dragging:
            try:
                painter.setPen(QColor("#FFFFFF"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                fm = painter.fontMetrics()
                label = _short_label(canvas, dh.hole_id)
                tw = fm.horizontalAdvance(label)
                lh = float(max(10.0, fm.height()))
                label_pt = c_pt + QPointF(-tw / 2.0, 16)
                label_rect = QRectF(
                    c_pt.x() - tw / 2.0,
                    float(label_pt.y()) - lh,
                    tw, lh)
                # Ouvre-t-on sous le label ?  Si non, on passe au-dessus.
                if _imagery_label_clear(canvas, dh.hole_id, label_rect):
                    painter.drawText(label_pt, label)
                else:
                    alt_pt = c_pt + QPointF(-tw / 2.0, -8)
                    alt_rect = QRectF(
                        c_pt.x() - tw / 2.0,
                        float(alt_pt.y()) - lh,
                        tw, lh)
                    if _imagery_label_clear(canvas, dh.hole_id, alt_rect):
                        painter.drawText(alt_pt, label)
                    else:
                        painter.drawText(label_pt, label)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed(
                    "Vue 3D : étiquette forage avec badges imagerie", _exc)


def _draw_assay_marker(painter, cx, cy, lane, r):
    """v2.9.189 — forme de la voie (cercle/carré/losange), partagée par
    les boules ET la légende d'éléments."""
    shape = lane % 3
    if shape == 1:
        painter.drawRect(QRectF(cx - r, cy - r, 2.0 * r, 2.0 * r))
    elif shape == 2:
        painter.drawPolygon(QPolygonF([
            QPointF(cx, cy - r), QPointF(cx + r, cy),
            QPointF(cx, cy + r), QPointF(cx - r, cy),
        ]))
    else:
        painter.drawEllipse(QPointF(cx, cy), r, r)


def _draw_element_key(canvas, painter, elems, p_top):
    """v2.9.189 — légende des ÉLÉMENTS au sommet de la colonne de
    teneurs : UNE LIGNE PAR ÉLÉMENT (forme + libellé), empilée vers le
    haut — plus AUCUN chevauchement.

    Avant (v2.9.185) : une étiquette PAR VOUE, centrée sur sa boule —
    mais les voies ne sont qu'à ~8 px d'écart : « quand y a plusieurs
    labels se chevauchent » (retour écran).  La légende empilée + la
    forme par élément règle l'identification sans collision.
    """
    try:
        from ..core.multi_assay import column_caption
        f = QFont("Segoe UI", 6)
        f.setCapitalization(QFont.SmallCaps)
        painter.setFont(f)
        fm = painter.fontMetrics()
        line_h = fm.height() + 1.0
        n = len(elems)
        base_y = p_top.y() - 7.0
        for k, el in enumerate(elems):
            cy = base_y - (n - 1 - k) * line_h
            painter.setPen(QPen(QColor("#ECF0F1"), 0.8))
            painter.setBrush(QBrush(QColor("#ECF0F1")))
            _draw_assay_marker(painter, p_top.x(), cy, k, 3.0)
            painter.setPen(QColor("#ECF0F1"))
            painter.drawText(
                QPointF(p_top.x() + 6.0, cy + fm.height() / 2.0 - 2.0),
                column_caption(el) or str(el))
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : légende des éléments de teneurs "
                      "(sans légende)", _exc)


def draw_assay_bubble(canvas, painter, hole_id, inv, el, val, p_top, p_bot,
                      lane=0, n_lanes=1):
    """Boule de teneur : taille = valeur, couleur = rampe (une par élément).

    ``lane`` / ``n_lanes`` décalent les boules des différents éléments
    côte à côte, perpendiculairement au forage (multi-teneurs).

    v2.9.185 — QUI EST QUI (retour écran : « quand y a 2 ou plus
    teneurs on sait pas qui est qui ») :

    - **forme PAR élément** : 1ᵉʳ = cercle, 2ᵉ = carré, 3ᵉ = losange
      (comme les symboles par élément des logiciels miniers —
      identifiable même étiquettes masquées) ;
    - **étiquette d'élément** au sommet de SA colonne (comme l'en-tête
      des pistes 2D) : « Au ppm » en petites majuscules, dessiné sur la
      première boule de la voie (``show_label``), lié à « Collets et
      noms » et sauté pendant l'orbite (LOD v2.9.175).
    """
    col = QColor(canvas._assay_element_color(el, val))
    r = canvas._bubble_radius(el, val)
    dx = p_bot.x() - p_top.x()
    dy = p_bot.y() - p_top.y()
    length = math.hypot(dx, dy)
    nx = -dy / length if length > 1e-4 else 0.0
    ny = dx / length if length > 1e-4 else 1.0
    frac = lane - (n_lanes - 1) / 2.0
    off = frac * max(5.0, canvas.stroke_width * 0.8)
    mid = (p_top + p_bot) / 2.0 + QPointF(nx * off, ny * off)
    painter.setBrush(QBrush(col))
    painter.setPen(QPen(col.darker(125), 0.7))
    # v2.9.185 — forme par élément ; v2.9.189 — marqueur partagé avec
    # la légende empilée (l'étiquette par voie chevauchait : voies ~8 px)
    _draw_assay_marker(painter, mid.x(), mid.y(), lane, r)

    if not _in_motion(canvas):
        tip = "\n".join([
            _tr("Forage : {} [Teneur]").format(hole_id),
            _tr("Passe : {0:.2f} – {1:.2f} m")
            .format(inv.from_depth, inv.to_depth),
            f"{el} : {format_grade_value(val)}",
        ])
        canvas._hit_segments.append((
            mid, mid, 0.0,
            hole_id, inv.from_depth, inv.to_depth, tip,
        ))


def draw_selection_highlight(canvas, painter: QPainter, scale: float):
    """Draw fine, elegant metallic gold caliper brackets around selected interval."""
    if not canvas._selected_hole_id or canvas._selected_from_m is None or canvas._selected_to_m is None:
        return
    dh = next((d for d in canvas._drillholes if d.hole_id == canvas._selected_hole_id), None)
    if not dh:
        return

    pt_top = canvas._interpolate_dh_point(dh, canvas._selected_from_m)
    pt_bot = canvas._interpolate_dh_point(dh, canvas._selected_to_m)
    if not pt_top or not pt_bot:
        return

    s_top = canvas.project_3d(pt_top.x, pt_top.y, pt_top.z, scale)
    s_bot = canvas.project_3d(pt_bot.x, pt_bot.y, pt_bot.z, scale)
    p0 = QPointF(s_top[0], s_top[1])
    p1 = QPointF(s_bot[0], s_bot[1])

    # 1. Subtle, non-invasive glow
    painter.setPen(QPen(QColor(241, 196, 15, 60), canvas.stroke_width + 7.0, Qt.SolidLine, Qt.RoundCap))
    painter.drawLine(p0, p1)

    # 2. Golden caliper rings at FROM and TO
    gold_c = QColor("#F1C40F")
    painter.setBrush(QBrush(Qt.NoBrush))
    painter.setPen(QPen(gold_c, 2.0, Qt.SolidLine))
    painter.drawEllipse(p0, 5.0, 5.0)
    painter.drawEllipse(p1, 5.0, 5.0)

    # 3. Parallel caliper dashed guidelines
    vec = p1 - p0
    v_len = math.hypot(vec.x(), vec.y())
    if v_len > 1e-4:
        nx = -vec.y() / v_len * 6.0
        ny = vec.x() / v_len * 6.0
        painter.setPen(QPen(gold_c, 1.2, Qt.DashLine))
        painter.drawLine(p0 + QPointF(nx, ny), p1 + QPointF(nx, ny))
        painter.drawLine(p0 - QPointF(nx, ny), p1 - QPointF(nx, ny))

    # 4. Clean dark badge tag with depth
    mid_pt = (p0 + p1) / 2.0
    tag_text = f"★ {canvas._selected_hole_id} [{canvas._selected_from_m:.1f}–{canvas._selected_to_m:.1f} m]"
    painter.setPen(QPen(Qt.NoPen))
    painter.setBrush(QBrush(QColor(23, 29, 34, 210)))
    fm = painter.fontMetrics()
    txt_w = fm.horizontalAdvance(tag_text) + 8
    painter.drawRoundedRect(QRectF(mid_pt.x() + 8, mid_pt.y() - 10, txt_w, 18), 3, 3)
    painter.setPen(QColor("#F1C40F"))
    painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
    painter.drawText(mid_pt + QPointF(12, 3), tag_text)
