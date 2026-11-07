"""DrillMaster — Surface MNT de la Vue 3D (volet 1, tranche 4, v2.9.149).

Calcul de la grille de sol 3D, extrait de ``ui/view_3d.py`` (SPEC) :
MÊME cascade de sources que la coupe 2D (raster choisi en 2D → CSV
topographie → collets), grille 96×96 + lissage léger, source affichée
dans la barre de statut.
"""

from __future__ import annotations

import math

from ..core.topography import (
    build_surface_grid, grid_from_gridded_samples, smooth_surface_grid,
)


def _tr(text):
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("View3DPanel", text)


def section_mnt_choice(widget):
    """v2.9.142 — choix « Source MNT » de la coupe 2D (combo du panneau"""
    """v2.9.142 — choix « Source MNT » de la coupe 2D (combo du panneau
    Topographie) : ``"auto"`` / id de couche / ``"none"`` ; ``None`` si
    la coupe 2D n'est pas accessible (comportement historique : tous
    les rasters)."""
    try:
        sw = getattr(widget.main_dock, "section_widget", None) \
            if widget.main_dock else None
        combo = getattr(sw, "surface_combo", None)
        if combo is not None:
            data = combo.currentData()
            if data is not None:
                return str(data)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Vue 3D : lecture du combo « Source MNT » de la "
                      "coupe 2D (repli : tous les rasters)", _exc)
    return None


def compute_surface_grid(widget):
    """v2.9.142 — surface 3D : MÊME cascade de sources que la coupe 2D."""
    """v2.9.142 — surface 3D : MÊME cascade de sources que la coupe 2D.

    1. MNT **raster** du projet QGIS — en suivant le combo « Source
       MNT » de la coupe 2D (« auto » = 1ᵉ raster, « Aucun raster » =
       aucun, id de couche = cette couche) ;
    2. **CSV x;y;z** topographie importé dans le projet (la 2ᵉ source
       de la cascade 2D, ignorée par la 3D jusqu'ici — c'était la
       cause du « MNT plat » quand la topo venait d'un CSV) ;
    3. collets (repli).

    La source retenue est AFFICHÉE dans la barre de statut (fini le
    repli collets silencieux qui se faisait passer pour une topo).
    """
    from .raster_surface import (
        csv_topography_points, qgis_raster_layers, sample_raster_grid)

    # v2.9.141 — emprise explicite : « Tous les forages » (bbox complète)
    # ou « Coupe active » (collets de la coupe).  UNE marge cohérente est
    # appliquée UNE SEULE FOIS, et l'échantillonnage du MNT utilise
    # EXACTEMENT la même emprise que la grille (plus de décalage
    # échantillon ↔ grille qui « plafonnait » les bords de la surface).
    mode = "all"
    try:
        mode = widget.combo_mnt_extent.itemData(
            widget.combo_mnt_extent.currentIndex()) or "all"
    except (RuntimeError, AttributeError):
        # combo pas encore construit (boot) — SILENCE JUSTIFIÉ : repli
        # « tous les forages », l'état transitoire est attendu.
        mode = "all"

    all_holes = widget.canvas._drillholes
    buf = float(getattr(widget.canvas, "_active_section_buffer", 20.0) or 20.0)
    if mode == "section" and widget.canvas._section_hole_ids:
        holes = [d for d in all_holes if d.hole_id in widget.canvas._section_hole_ids]
    else:
        holes = all_holes

    collars = []
    for dh in holes:
        c = getattr(dh, "collar", None)
        if c and math.isfinite(c.x) and math.isfinite(c.y) and math.isfinite(c.z):
            collars.append((c.x, c.y, c.z))
    if not collars:
        widget.canvas.set_surface_grid(None, "")
        widget._mnt_status = _tr("MNT : indisponible (aucun collet)")
        widget._on_hover_changed("")
        return

    # Emprise BRUTE des collets (X, Y), puis UNE marge.
    xs = [c[0] for c in collars]
    ys = [c[1] for c in collars]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x
    span_y = max_y - min_y
    if mode == "section":
        mx = my = max(buf, 10.0)
    else:
        # marge ≥ 10 m, 5 % de l'emprise, et ≥ buffer de coupe → « tous »
        # n'est jamais plus petit que « coupe active ».
        mx = max(span_x * 0.05, buf, 10.0)
        my = max(span_y * 0.05, buf, 10.0)
    # zone minuscule (collets superposés) : marge minimale pour ne pas
    # produire une grille dégénérée.
    if span_x < 1.0:
        mx = max(mx, 15.0)
    if span_y < 1.0:
        my = max(my, 15.0)
    min_x -= mx
    max_x += mx
    min_y -= my
    max_y += my
    bounds = (min_x, max_x, min_y, max_y)
    # v2.9.146 — grille 96×96 + UN passage de lissage léger (retour
    # écran de l'époque : « trop pixelisé mais ne lisse pas trop »).
    # v2.9.176 — retour à 48×48 (retour écran : « le MNT est trop lent,
    # mets juste le relief et une fine couche ») : 96×96 = 9 216 quads
    # triés + dessinés et 9 409 sommets projetés à CHAQUE image ; 48×48
    # = 4× moins, et l'ombrage LISSÉ par sommet (v2.9.141) — pas la
    # résolution — est ce qui tue l'effet « pixelisé ».  Le lissage
    # gaussien 3×3 (centre 4) reste : relief naturel.
    N = 48

    # v2.9.142 — le raster suit le combo « Source MNT » de la coupe 2D.
    rasters = qgis_raster_layers()
    mnt_choice = widget._section_mnt_choice()
    if mnt_choice == "none":
        rasters = []
    elif mnt_choice not in (None, "", "auto"):
        rasters = [(lid, lyr) for lid, lyr in rasters if lid == mnt_choice]
    # sinon (« auto » / coupe 2D indisponible) : tous les rasters,
    # le 1ᵉ exploitable gagne (comportement v2.9.141).

    grid = None
    source = ""
    dem_name = ""
    for _lid, layer in rasters:
        try:
            # v2.9.141 — même emprise (min_x..max_y) pour l'échantillonnage
            # ET pour la grille : plus de décalage échantillon ↔ grille.
            pts, _reason = sample_raster_grid(
                layer, min_x, max_x, min_y, max_y, n=N)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed(f"Vue 3D : échantillonnage du MNT raster "
                          f"« {layer.name() if hasattr(layer, 'name') else '?'} » "
                          f"— couche suivante de la cascade", _exc)
            continue
        if len(pts) >= 3:
            # v2.9.141 — échantillons DÉJÀ sur une grille : construction
            # directe O(n²), plus d'interpolation IDW O(n⁴) qui prenait
            # des secondes à l'ouverture de la Vue 3D.
            grid = grid_from_gridded_samples(pts, bounds, N)
            if grid:
                source = "dem"
                try:
                    dem_name = str(layer.name() or "?")
                except (RuntimeError, AttributeError):
                    # couche C++ supprimée entre-temps — le nom est
                    # purement décoratif (statut).  SILENCE JUSTIFIÉ.
                    dem_name = "?"
                break

    csv_count = 0
    if grid is None:
        # v2.9.142 — 2ᵉ source de la cascade 2D : le CSV topographie du
        # projet (x;y;z).  Points retenus dans l'emprise de la surface ;
        # peu de points → IDW lissé, beaucoup → binning O(n²) rapide.
        csv_pts = None
        try:
            proj = getattr(widget, "_project", None)
            if proj is not None and hasattr(proj, "get_imported_file_path"):
                path = proj.get_imported_file_path("topography")
                if path:
                    csv_pts = csv_topography_points(path)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : lecture du CSV topographie "
                          "(cascade → collets)", _exc)
            csv_pts = None
        if csv_pts:
            inside = [(x, y, z) for (x, y, z) in csv_pts
                      if min_x <= x <= max_x and min_y <= y <= max_y]
            if len(inside) >= 3:
                if len(inside) <= 400:
                    grid = build_surface_grid(
                        inside, bounds=bounds, nx=N, ny=N)
                else:
                    grid = grid_from_gridded_samples(inside, bounds, N)
                if grid:
                    source = "csv"
                    csv_count = len(inside)

    if grid is None:
        grid = build_surface_grid(collars, bounds=bounds, nx=N, ny=N)
        if grid:
            source = "collars"

    # v2.9.141 — PAS d'ancrage aux collets en 3D : la surface reste le
    # DEM RÉEL (non déformé).  L'ancrage créait des « fossés »/bosses
    # artificiels autour des forages.  Un écart collet↔MNT est une vraie
    # information (terrassement / levé), déjà signalée par le QC 2D —
    # on ne la masque pas en déformant la surface.

    # v2.9.146 — lissage LÉGER (1 seul passage, gaussien 3×3) :
    # cosmétique rendu uniquement — le relief reste naturel.
    if grid:
        grid = smooth_surface_grid(grid, passes=1)

    widget.canvas.set_surface_grid(grid, source)

    # v2.9.142 — source du MNT VISIBLE (le « MNT plat » venait du repli
    # collets silencieux : on ne peut plus confondre l'interpolation
    # des collets avec une vraie topo).
    if source == "dem":
        widget._mnt_status = _tr("MNT : DEM « {} »").format(dem_name)
    elif source == "csv":
        widget._mnt_status = _tr("MNT : CSV topographie ({} pts)").format(
            csv_count)
    elif source == "collars":
        widget._mnt_status = _tr(
            "MNT : collets seuls (aucun DEM/CSV — interpolé)")
    else:
        widget._mnt_status = _tr("MNT : indisponible")
    widget._on_hover_changed("")

