"""DrillMaster — Échantillonnage MNT raster sur une GRILLE 2D (vue 3D).

v2.9.141 (P1) — partage du VRAI MNT entre la coupe 2D et la vue 3D.

La coupe 2D échantillonne le MNT le LONG d'une ligne de coupe
(``SectionWidget._sample_raster_along_line``) ; la vue 3D a besoin d'une
SURFACE : on échantillonne le MÊME MNT du projet QGIS sur une grille
régulière (X, Y) couvrant l'emprise des forages.  Même cascade que la 2D :
MNT raster QGIS → CSV x;y;z → collets (la vue 3D fait le repli collets
dans ``View3DWidget._compute_surface_grid``).

v2.9.142 — 2ᵉ source de la cascade : le CSV topographie du projet est
lu ici (``csv_topography_points``, même parsing que la coupe 2D), plus
le choix du raster suit le combo « Source MNT » de la coupe 2D.

Garde-fous repris de la 2D : CRS projet ≠ CRS raster (transformation QGIS,
repli WGS84↔UTM intégré), lecture robuste ``dataProvider().sample`` puis
``identify``, NoData ignorés.  La raison d'un échec est retournée, jamais
masquée.

v2.9.141 — interpolation BILINÉAIRE : un bloc raster est lu une seule fois
(résolution native, bornée) puis chaque nœud est interpolé entre ses 4
pixels voisins, au lieu du plus-proche-voisin qui produisait un relief
« carré » (retour écran).  Repli sur ``sample``/``identify`` si la lecture
de bloc échoue.
"""

from __future__ import annotations

import csv
import math
import os

from ..core.crs_math import conversion_between


def _tr(text):
    """v2.9.256 — traduction des messages de la surface 3D."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("View3DPanel", text)


# v2.9.142 — cache (path, mtime, plafond) → points du CSV topographie.
_CSV_TOPO_CACHE: dict = {}


def csv_topography_points(path, max_points: int = 20000):
    """Points ``(x, y, z)`` d'un CSV topographie — même lecture que la 2D.

    v2.9.142 — la vue 3D réutilise la 2ᵉ source de la cascade de la coupe
    2D : le CSV x;y;z importé dans le projet (``topography``).  En-têtes
    reconnus exactement comme la coupe 2D (``header_match_details`` →
    ``collar_x`` / ``collar_y`` / ``collar_z``), séparateur et encodage
    auto-détectés, plafonné à ``max_points`` points.

    Retourne la liste des points valides, ou ``None`` si absent / illisible
    / sans colonnes X;Y;Z exploitables.
    """
    if not path or not os.path.isfile(path):
        return None
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    key = (str(path), mtime, int(max_points))
    if key in _CSV_TOPO_CACHE:
        return _CSV_TOPO_CACHE[key]

    from ..core.csv_parser import (
        detect_encoding, detect_separator, header_match_details)

    points = None
    try:
        encoding = detect_encoding(path)
        with open(path, "r", encoding=encoding, newline="") as handle:
            head = handle.read(65536)
            handle.seek(0)
            separator = detect_separator(head.splitlines()[:20])
            rows = list(csv.reader(handle, delimiter=separator))
    except (OSError, UnicodeDecodeError, csv.Error):
        rows = None
    if rows and len(rows) >= 2:
        headers = [str(h).strip() for h in rows[0]]
        indexes = {}
        for index, header in enumerate(headers):
            canonical = header_match_details(header).get("canonical")
            if canonical in ("collar_x", "collar_y", "collar_z") \
                    and canonical not in indexes:
                indexes[canonical] = index
        if len(indexes) >= 3:
            pts = []
            for row in rows[1:max_points + 1]:
                try:
                    x = float(str(row[indexes["collar_x"]]).strip().replace(",", "."))
                    y = float(str(row[indexes["collar_y"]]).strip().replace(",", "."))
                    z = float(str(row[indexes["collar_z"]]).strip().replace(",", "."))
                except (IndexError, ValueError):
                    continue
                if not all(math.isfinite(v) for v in (x, y, z)):
                    continue
                pts.append((x, y, z))
            points = pts or None

    # Cache borné (quelques projets récents).
    if len(_CSV_TOPO_CACHE) > 8:
        _CSV_TOPO_CACHE.pop(next(iter(_CSV_TOPO_CACHE)))
    _CSV_TOPO_CACHE[key] = points
    return points


def qgis_raster_layers():
    """Rasters du projet QGIS actif, en ``(id, couche)`` ; ``[]`` sinon."""
    try:
        from qgis.core import QgsProject, QgsRasterLayer
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : qgis_raster_layers", _exc)
        return []
    try:
        all_layers = list(QgsProject.instance().mapLayers().items())
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : qgis_raster_layers", _exc)
        return []
    return [(lid, lyr) for lid, lyr in all_layers
            if isinstance(lyr, QgsRasterLayer)]


def _extract_value(result, band=1):
    """Extrait une élévation finie d'un résultat ``identify`` (voir 2D)."""
    candidates = []

    def _push(raw):
        if raw is None:
            return
        if isinstance(raw, complex):
            return
        if isinstance(raw, (list, tuple)):
            for item in raw:
                _push(item)
            return
        if isinstance(raw, dict):
            for item in raw.values():
                _push(item)
            return
        try:
            if hasattr(raw, "isValid") and callable(raw.isValid):
                try:
                    if not raw.isValid():
                        return
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("raster_surface : _push", _exc)
                    pass  # isValid() peut lever selon le build QGIS
            if (hasattr(raw, "value") and callable(raw.value)
                    and not isinstance(raw, (int, float))):
                try:
                    raw = raw.value()
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("raster_surface : _push", _exc)
                    pass  # QVariant.value() indisponible → garder raw
            val = float(raw)
        except (TypeError, ValueError):
            return
        if math.isfinite(val):
            candidates.append(val)

    if result is None:
        return None
    try:
        if hasattr(result, "isValid") and not result.isValid():
            return None
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("raster_surface : _extract_value", _exc)
        pass  # QVariant/isValid absent selon le build QGIS
    try:
        res_map = result.results() if hasattr(result, "results") else None
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("raster_surface : _extract_value", _exc)
        res_map = None  # API results() indisponible → repli value()
    if isinstance(res_map, dict) and res_map:
        if band in res_map:
            _push(res_map.get(band))
        if not candidates and str(band) in res_map:
            _push(res_map.get(str(band)))
        if not candidates:
            for key in sorted(res_map.keys(),
                              key=lambda k: (str(type(k)), str(k))):
                _push(res_map.get(key))
                if candidates:
                    break
    if not candidates and hasattr(result, "value"):
        for key in (band, 0, 1):
            try:
                _push(result.value(key))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("raster_surface : _extract_value", _exc)
                continue
            if candidates:
                break
    return candidates[0] if candidates else None


def _bilinear_at(block, bw, bh, ext, lx, ly):
    """Élévation par interpolation bilinéaire dans un ``QgsRasterBlock``.

    ``ext`` = étendue (CRS couche) couverte par le bloc ``(bw × bh)`` ;
    ``(lx, ly)`` = point dans ce même CRS.  Retourne ``None`` si hors bloc
    ou si l'un des 4 coins est NoData (le repli ``sample`` prend le relais).
    """
    w = ext.width()
    h = ext.height()
    if w <= 0 or h <= 0 or bw < 2 or bh < 2:
        return None
    fx = (lx - ext.xMinimum()) / w * (bw - 1)
    fy = (ext.yMaximum() - ly) / h * (bh - 1)
    x0 = int(math.floor(fx))
    y0 = int(math.floor(fy))
    tx = fx - x0
    ty = fy - y0

    def _v(r, c):
        r = max(0, min(bh - 1, r))
        c = max(0, min(bw - 1, c))
        try:
            if block.isNoData(r, c):
                return None
            return float(block.value(r, c))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("raster_surface : _v", _exc)
            return None

    z00 = _v(y0, x0)
    z01 = _v(y0, x0 + 1)
    z10 = _v(y0 + 1, x0)
    z11 = _v(y0 + 1, x0 + 1)
    if None in (z00, z01, z10, z11):
        return None
    ztop = z00 * (1.0 - tx) + z01 * tx
    zbot = z10 * (1.0 - tx) + z11 * tx
    return ztop * (1.0 - ty) + zbot * ty


def raster_block_dims(extent_w, extent_h, raster_xsize, raster_ysize,
                      raster_extent_w, raster_extent_h, fallback):
    """Dimensions (bw, bh) du bloc raster à lire — à la RÉSOLUTION RÉELLE.

    v2.9.145 — corrige le bug « MNT plat » (retour écran : « plat total,
    aucune ondulation alors que le relief devrait être réel ») :
    l'ancien code divisait la LARGEUR de l'emprise (m) par le NOMBRE de
    pixels du raster (sans unité) → bloc 2×2 systématique → interpolation
    bilinéaire entre 4 coins → surface sans relief.

    La taille réelle du pixel = largeur du raster / nombre de colonnes ;
    on en déduit le nombre de colonnes à lire sur l'emprise demandée.
    ``fallback`` (n+1) si les dimensions du raster sont indisponibles.
    """
    try:
        if (raster_xsize and raster_xsize > 0 and raster_ysize > 0
                and raster_extent_w and raster_extent_w > 0
                and raster_extent_h and raster_extent_h > 0):
            xres = float(raster_extent_w) / float(raster_xsize)
            yres = float(raster_extent_h) / float(raster_ysize)
            if xres > 0 and yres > 0:
                bw = int(math.ceil(float(extent_w) / xres)) + 1
                bh = int(math.ceil(float(extent_h) / yres)) + 1
                return bw, bh
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : raster_block_dims", _exc)
        pass  # dimensions indisponibles — repli sur la grille n+1
    return int(fallback), int(fallback)


def sample_raster_grid(layer, min_x, max_x, min_y, max_y, n=64):
    """Échantillonne la bande 1 du MNT sur une grille ``(n+1)×(n+1)``.

    Coordonnées d'entrée en CRS PROJET ; la transformation projet→raster
    est gérée comme dans la coupe 2D (repli WGS84↔UTM intégré).

    Retourne ``(points, reason)`` : ``points`` = liste ``(x, y, z)``
    valides (CRS projet, z = altitude), ``reason`` = "" si ≥ 3 points,
    sinon la raison de l'échec.
    """
    try:
        from qgis import core as _qcore
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
        return [], "QGIS indisponible (qgis.core non importable)"
    _need = ("QgsPointXY", "QgsRectangle", "QgsRaster",
             "QgsCoordinateTransform", "QgsProject")
    _missing = [c for c in _need if not hasattr(_qcore, c)]
    if _missing:
        return [], "classes QGIS manquantes : " + ", ".join(_missing)
    (QgsPointXY, QgsRectangle, QgsRaster, QgsCoordinateTransform,
     QgsProject) = (getattr(_qcore, c) for c in _need)
    _identify_value = getattr(QgsRaster, "IdentifyValue", 1)
    try:
        provider = layer.dataProvider()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
        provider = None
    if provider is None:
        return [], "pas de dataProvider"
    band = 1
    project = QgsProject.instance()
    project_crs = project.crs()
    layer_crs = layer.crs()
    try:
        project_crs_ok = project_crs.isValid()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
        project_crs_ok = False
    try:
        layer_crs_ok = layer_crs.isValid()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
        layer_crs_ok = False
    if not project_crs_ok:
        return [], _tr("CRS du projet QGIS non défini")
    if not layer_crs_ok:
        return [], _tr("MNT « {} » sans CRS valide").format(
            layer.name() or '?')

    crs_same = False
    try:
        crs_same = (project_crs == layer_crs)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
        try:
            crs_same = (project_crs.authid().strip().upper()
                        == layer_crs.authid().strip().upper())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
            crs_same = False
    transform = None
    builtin = None
    if not crs_same:
        try:
            transform = QgsCoordinateTransform(project_crs, layer_crs, project)
            if transform is None or transform.isNull():
                transform = None
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
            transform = None
        if transform is None:
            try:
                builtin = conversion_between(
                    project_crs.authid(), layer_crs.authid())
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
                builtin = None
            if builtin is None:
                return [], _tr(
                    "transformation CRS impossible (projet : {} / "
                    "MNT : {})").format(project_crs.authid(),
                                       layer_crs.authid())

    def _to_layer(gx, gy):
        """Point projet → CRS couche ``(lx, ly)`` ; None si échec."""
        try:
            if transform is not None:
                pt = transform.transform(QgsPointXY(gx, gy))
                if isinstance(pt, tuple):
                    pt = pt[0]
                return pt.x(), pt.y()
            if builtin is not None:
                return builtin(gx, gy)
            return gx, gy
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Couches QGIS : _to_layer", _exc)
            return None

    # --- Bloc raster (résolution native, bornée) pour le bilinéaire ---
    block = None
    bw = bh = 0
    ext = None
    try:
        corners = [_to_layer(min_x, min_y), _to_layer(max_x, min_y),
                   _to_layer(max_x, max_y), _to_layer(min_x, max_y)]
        corners = [c for c in corners if c is not None]
        if len(corners) == 4:
            lxs = [c[0] for c in corners]
            lys = [c[1] for c in corners]
            ext = QgsRectangle(min(lxs), min(lys), max(lxs), max(lys))
            # v2.9.145 — dimensions du bloc à la RÉSOLUTION RÉELLE du
            # raster (l'ancien code mélangeait mètres et pixels → bloc
            # 2×2 → MNT plat ; voir raster_block_dims).
            try:
                xsz = provider.xSize()
                ysz = provider.ySize()
                pext = provider.extent()
                raster_w, raster_h = pext.width(), pext.height()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
                xsz = ysz = 0
                raster_w = raster_h = 0.0
            bw, bh = raster_block_dims(
                ext.width(), ext.height(), xsz, ysz,
                raster_w, raster_h, n + 1)
            bw = max(2, min(int(bw), 1500))
            bh = max(2, min(int(bh), 1500))
            try:
                blk = provider.block(band, ext, bw, bh)
                if blk is None or not blk.isValid():
                    blk = None
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
                blk = None
            if blk is not None:
                block = blk
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
        block = None

    has_sample_api = hasattr(provider, "sample")
    pts = []
    span_x = (max_x - min_x) or 1.0
    span_y = (max_y - min_y) or 1.0
    for i in range(n + 1):
        gy = min_y + span_y * i / n
        for j in range(n + 1):
            gx = min_x + span_x * j / n
            lxy = _to_layer(gx, gy)
            if lxy is None:
                continue
            lx, ly = lxy
            value = None
            if block is not None and ext is not None:
                value = _bilinear_at(block, bw, bh, ext, lx, ly)
            if value is None:
                pt = QgsPointXY(lx, ly)
                if has_sample_api:
                    try:
                        sampled = provider.sample(pt, band)
                        raw = sampled
                        ok_flag = True
                        if isinstance(sampled, tuple):
                            if len(sampled) >= 2:
                                raw, ok_flag = sampled[0], sampled[1]
                            elif len(sampled) == 1:
                                raw = sampled[0]
                        if ok_flag is False:
                            raw = None
                        if raw is not None:
                            try:
                                val = float(raw)
                                if math.isfinite(val):
                                    value = val
                            except (TypeError, ValueError):
                                value = None
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
                        value = None
            if value is None:
                result = None
                try:
                    result = layer.identify(pt, _identify_value, band)
                except TypeError:
                    try:
                        result = layer.identify(pt, _identify_value)
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
                        result = None
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Échantillonnage raster : sample_raster_grid", _exc)
                    result = None
                value = _extract_value(result, band=band)
            if value is None:
                continue
            pts.append((gx, gy, float(value)))

    if len(pts) >= 3:
        return pts, ""
    return pts, _tr("{} points valides sur {} (hors emprise / NoData)"
                    ).format(len(pts), (n + 1) * (n + 1))
