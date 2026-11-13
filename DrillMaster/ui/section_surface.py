"""DrillMaster — Surface / topographie de la coupe 2D (volet 3, v2.9.149).

Première tranche du découpage de ``ui/section_dock.py`` (12 237 lignes,
le plus gros fichier du plugin — SPEC de restructuration) : tout ce qui
LIT les sources du sol (raster QGIS, CSV x;y;z) vit ici, sans widget.

Le dock délègue à une ligne — comportement identique, code séparé pour
arrêter de surcharger le monolithe (retour écran : « sépare les
fonctions pour éviter les bugs incessants »).
"""

from __future__ import annotations

import csv
from qgis.PyQt.QtCore import QCoreApplication
import math
import os

from ..core.crs_math import conversion_between
from ..core.section import (
    drillhole_buffer_status, project_point_onto_section,
)


def _tr(text):
    """v2.9.256 — traduction pour les fonctions module (dock section)."""
    return QCoreApplication.translate("SectionWidget", text)
from ..core.topography import (
    collar_deviations, profile_from_collars, refine_surface_profile,
)
from .styles_qt import COLORS


def qgis_raster_layers():
    """Rasters du projet QGIS actif, en ``(id, couche)``.

    v2.9.4 — détection ROBUSTE : ``isinstance(lyr, QgsRasterLayer)``
    d'abord (indépendant de la valeur du ``type()``), ``type()`` en
    secours pour un QGIS sans QgsRasterLayer exposé.  ``[]`` si QGIS
    est indisponible ou si le projet ne porte aucun raster.  (Le
    filtre ``type() == 0`` seul listait des VECTEURS sous QGIS 3.44
    — retour écran 24/08/2026 : le DEM raster n'apparaissait pas,
    les vecteurs si.)
    """
    try:
        from qgis.core import QgsProject
    except ImportError:
        return []
    try:
        all_layers = list(QgsProject.instance().mapLayers().items())
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : listing des couches raster QGIS", _exc)
        return []
    try:
        from qgis.core import QgsRasterLayer
    except ImportError:
        QgsRasterLayer = None
    if QgsRasterLayer is not None:
        return [(lid, lyr) for lid, lyr in all_layers
                if isinstance(lyr, QgsRasterLayer)]
    out = []
    for lid, lyr in all_layers:
        try:
            if lyr.type() == 0:
                out.append((lid, lyr))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Cascade MNT : listing des couches raster QGIS", _exc)
            # couche sans .type() exploitable : ignorée (pas un raster
            # certain, on ne l'offre pas comme MNT)
            pass
    return out


def surface_raster_layer(dock):
    """Le MNT à échantillonner selon le combo (auto = 1ᵉ raster).

    None si QGIS est indisponible, si aucun raster est chargé, ou si
    l'utilisateur a choisi « Aucun raster ».  Toute indisponibilité
    retombe silencieusement sur la suite de la cascade.
    """
    choice = dock.surface_combo.currentData()
    if choice == "none":
        return None
    rasters = dock._qgis_raster_layers()
    if not rasters:
        return None
    if choice == "auto":
        return rasters[0][1]
    for lid, lyr in rasters:
        if lid == choice:
            return lyr
    return None


def extract_raster_sample(result, band=1):
    """Extrait une élévation finie d'un résultat ``identify``.

    v2.9.9 — sous QGIS 3.x l'API n'est PAS uniforme :
      - ``QgsRasterIdentifyResult.value(0)`` est une clé d'ORDRE
        (1er résultat), PAS le numéro de bande — ``value(1)`` est la
        1ʳᵉ bande.  L'ancien code lisait ``value(0)`` → toujours
        ``None`` → message trompeur « 0/257 points valides… hors
        étendue / NoData » alors que la ligne ET le CRS étaient OK
        (retour écran 23/08/2026, MNT « MNT »).
      - ``results()`` renvoie ``{bande: valeur}`` (clés 1-based) ou,
        selon le format, un dict imbriqué / une liste.
    Retourne ``float`` ou ``None``.
    """
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
                    log_swallowed("Cascade MNT : extraction valeur raster", _exc)
                    # isValid() peut lever sur certains QVariant
                    pass
            if hasattr(raw, "value") and callable(raw.value) and not isinstance(
                    raw, (int, float)):
                try:
                    raw = raw.value()
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Cascade MNT : extraction valeur raster", _exc)
                    # QVariant.value() indisponible → garder raw tel quel
                    pass
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
        log_swallowed("Cascade MNT : extraction d'une élévation identify()", _exc)
        # QVariant/isValid parfois absent ou non appelable selon build
        pass

    # 1) results() — dict {band: value} (préféré)
    try:
        res_map = result.results() if hasattr(result, "results") else None
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : extraction d'une élévation identify()", _exc)
        res_map = None
    if isinstance(res_map, dict) and res_map:
        if band in res_map:
            _push(res_map.get(band))
        if not candidates and str(band) in res_map:
            _push(res_map.get(str(band)))
        if not candidates:
            for key in sorted(res_map.keys(), key=lambda k: (str(type(k)), str(k))):
                _push(res_map.get(key))
                if candidates:
                    break

    # 2) value(band) puis value(0) en secours (clé d'ordre — 1er hit)
    if not candidates and hasattr(result, "value"):
        for key in (band, 0, 1):
            try:
                _push(result.value(key))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Cascade MNT : extraction d'une élévation identify()", _exc)
                continue
            if candidates:
                break

    return candidates[0] if candidates else None


def sample_raster_along_line(layer, line, a_min, a_max, n=256):
    """Échantillonne la bande 1 du MNT le long de la ligne de coupe.

    Opération GDAL standard (comme Leapfrog/Datamine) : lecture de la
    valeur du MNT aux N points de ``[a_min, a_max]`` — PAS de
    reconstruction de surface ici ; l'ancrage et le QC vivent dans
    core.topography.  Les NoData sont ignorés (le profil passe au
    dessus par interpolation droite, signalé dans le statut).

    v2.9.3 — retour ``(samples, why)`` : ``why`` = "" dès qu'il y a
    ≥ 2 points valides, sinon la raison de l'écart (CRS, étendue,
    NoData…) — un MNT écarté est TOUJOURS expliqué dans le statut,
    jamais silencieux (« j'ai un DEM, est-ce qu'il le prend en
    compte ? »).

    v2.9.9 — lecture de la valeur CORRIGÉE (retour écran 23/08/2026 :
    ligne dans l'emprise, même SCR, source = mon MNT, et pourtant
    « 0/257 points valides… hors étendue / NoData ») :
      1. ``dataProvider().sample(pt, 1)`` en premier (API la plus
         fiable pour un MNT mono-bande) ;
      2. repli ``layer.identify`` + extraction robuste via
         :meth:`_extract_raster_sample` (``results()[1]`` /
         ``value(1)``, plus jamais ``value(0)`` seul qui renvoyait
         toujours None) ;
      3. message d'échec enrichi (hors-emprise vs NoData, CRS des
         deux côtés) pour ne plus confondre un bug d'API avec un
         vrai hors-emprise.
    """
    try:
        from qgis import core as _qcore
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        return [], "QGIS indisponible (qgis.core non importable)"
    _need = ("QgsPointXY", "QgsRaster", "QgsCoordinateTransform",
             "QgsProject")
    _missing = [c for c in _need if not hasattr(_qcore, c)]
    if _missing:
        return [], ("classes QGIS manquantes : "
                    + ", ".join(_missing))
    (QgsPointXY, QgsRaster, QgsCoordinateTransform,
     QgsProject) = (getattr(_qcore, c) for c in _need)
    # v2.9.5 — API haut niveau QgsRasterLayer.identify() : NE PASSE
    # par QgsRasterIdentifyRequest (classe non exposée par qgis.core
    # sous certaines versions, ex. QGIS 3.44 — retour écran
    # 24/08/2026 : « classes QGIS manquantes :
    # QgsRasterIdentifyRequest »).  IdentifyValue == 1.
    _identify_value = getattr(QgsRaster, "IdentifyValue", 1)
    try:
        provider = layer.dataProvider()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        provider = None
    if provider is None:
        return [], "pas de dataProvider"
    band = 1
    project = QgsProject.instance()
    project_crs = project.crs()
    layer_crs = layer.crs()
    # Diagnostic par CÔTÉ (v2.9.6, retour écran 24/08/2026) : entre
    # deux CRS VALIDES et différents, QGIS trouve TOUJOURS une
    # transformation — donc « transformation impossible » = un des
    # deux CRS n'est pas défini (MNT sans géoréférencement, projet
    # sans CRS).  Le message dit lequel, et comment le corriger.
    try:
        project_crs_ok = project_crs.isValid()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        project_crs_ok = False
    try:
        layer_crs_ok = layer_crs.isValid()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        layer_crs_ok = False
    if not project_crs_ok:
        return [], _tr("CRS du projet QGIS non défini — impossible de "
                       "positionner le MNT.  Dans QGIS : Projet → "
                       "Propriétés → CRS → définir le CRS du projet.")
    if not layer_crs_ok:
        return [], _tr(
            "MNT « {} » sans CRS valide (raster sans métadonnées "
            "géoréférencées) — QGIS ne peut pas convertir les "
            "coordonnées.  Dans QGIS : clic droit sur la couche → "
            "Définir le CRS → choisir le vrai CRS du MNT (ou "
            "réprojeter le raster).").format(layer.name() or '?')
    # v2.9.7 — comparaison PROPRE des CRS (retour écran 25/08/2026 :
    # « mon DEM a le même CRS que le projet (32629) » mais message
    # « CRS du projet ≠ CRS du MNT ») : pas de comparaison de
    # chaînes d'authid — EPSG:32629, IGNF:ETRS89-UTM-29 ou une
    # définition WKT peuvent être le MÊME système.  Et si les CRS
    # sont identiques : AUCUNE transformation n'est construite — on
    # échantillonne directement (l'API de transformation est
    # instable sous certaines versions de QGIS, ex. 3.44).
    crs_same = False
    try:
        crs_same = (project_crs == layer_crs)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        try:
            crs_same = (project_crs.authid().strip().upper()
                        == layer_crs.authid().strip().upper())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
            crs_same = False
    transform = None
    builtin = None
    if not crs_same:
        transform_ok = False
        try:
            transform = QgsCoordinateTransform(
                project_crs, layer_crs, project)
            transform_ok = (transform is not None
                            and not transform.isNull())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
            transform_ok = False
        if not transform_ok:
            # v2.9.8 — repli INTÉGRÉ WGS84 ↔ UTM (retour écran
            # 25/08/2026 : projet EPSG:32629 / MNT EPSG:4326 —
            # la paire la plus standard de la géologie — et
            # QgsCoordinateTransform échoue sous QGIS 3.44) :
            # quand la transform QGIS est indisponible et que la
            # paire est WGS84 ↔ UTM, chaque point est converti
            # avec les formules de Mercator transverse (pure
            # Python, QGIS-free — core/crs_math.py, vérifiées à
            # < 1 mm contre pyproj) au lieu d'écarter le MNT.
            try:
                builtin = conversion_between(
                    project_crs.authid(), layer_crs.authid())
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
                builtin = None
            if builtin is None:
                return [], _tr(
                    "transformation CRS impossible (projet : {} / "
                    "MNT : {}) — vérifiez les deux CRS (Projet → "
                    "Propriétés → CRS ; clic droit sur la couche MNT → "
                    "Propriétés → CRS) ; le MNT n'est pas "
                    "rééchantillonné silencieusement").format(
                        project_crs.authid(), layer_crs.authid())
    x1, y1, x2, y2 = (float(line.x1), float(line.y1),
                      float(line.x2), float(line.y2))
    length = max(line.length, 1e-9)
    samples = []
    n_tried = 0
    n_outside = 0
    n_nodata = 0
    n_error = 0
    layer_extent = None
    try:
        layer_extent = layer.extent()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        layer_extent = None
    has_sample_api = hasattr(provider, "sample")
    for i in range(n + 1):
        t = i / n
        along = a_min + (a_max - a_min) * t
        # Position le long du segment P1→P2 (extrapolé aux bords).
        u = along / length
        mx = x1 + (x2 - x1) * u
        my = y1 + (y2 - y1) * u
        try:
            if transform is not None and not transform.isNull():
                pt = transform.transform(QgsPointXY(mx, my))
                # certaines builds renvoient (QgsPointXY, error)
                if isinstance(pt, tuple):
                    pt = pt[0]
            elif builtin is not None:
                lx, ly = builtin(mx, my)
                pt = QgsPointXY(lx, ly)
            else:
                pt = QgsPointXY(mx, my)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
            n_error += 1
            continue
        n_tried += 1
        # Diagnostic hors-emprise (n'empêche PAS la lecture : un
        # extent mal renseigné ne doit pas bloquer un MNT lisible).
        if layer_extent is not None:
            try:
                if (hasattr(layer_extent, "contains")
                        and not layer_extent.contains(pt)):
                    n_outside += 1
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
                # extent.contains peut échouer selon type de pt
                pass
        value = None
        # 1) dataProvider().sample — chemin le plus fiable (MNT
        # mono-bande).  Renvoie (valeur, ok) ou valeur selon build.
        if has_sample_api:
            try:
                sampled = provider.sample(pt, band)
                ok_flag = True
                raw = sampled
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
                log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
                value = None
        # 2) identify + extraction robuste (results/value bande 1)
        if value is None:
            result = None
            try:
                result = layer.identify(pt, _identify_value, band)
            except TypeError:
                try:
                    result = layer.identify(pt, _identify_value)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
                    result = None
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
                result = None
            value = extract_raster_sample(result, band=band)
        if value is None:
            n_nodata += 1
            continue
        samples.append((along, float(value)))
    if len(samples) >= 2:
        return samples, ""
    # Message d'échec ENRICHI (v2.9.9) : distinguer hors-emprise
    # réel, NoData, et échec de lecture.
    try:
        p_auth = project_crs.authid() or "?"
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        p_auth = "?"
    try:
        l_auth = layer_crs.authid() or "?"
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        l_auth = "?"
    try:
        name = layer.name() or "?"
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : échantillonnage raster le long de la coupe", _exc)
        name = "?"
    detail = _tr("{} points valides le long de la coupe").format(
        f"{len(samples)}/{n + 1}")
    if n_outside and n_outside >= (n + 1) * 0.9:
        detail += _tr(" — corridor hors emprise du MNT « {} » "
                      "(CRS projet {} / MNT {})").format(
                          name, p_auth, l_auth)
    elif n_nodata and n_nodata >= (n + 1) * 0.9:
        detail += _tr(" — MNT « {} » lit des NoData / valeurs non "
                      "finies sur le corridor (bande {} ; CRS "
                      "projet {} / MNT {})").format(
                          name, band, p_auth, l_auth)
    else:
        detail += _tr(" — ligne hors étendue du MNT, ou MNT 100 % "
                      "NoData sur le corridor (tentés={}, "
                      "hors_emprise≈{}, vides={}, erreurs={} ; "
                      "CRS projet {} / MNT {})").format(
                          n_tried, n_outside, n_nodata, n_error,
                          p_auth, l_auth)
    return samples, detail


def topography_csv_path(dock):
    """Le CSV x;y;z du projet (importé comme topography), ou None."""
    project = dock._project()
    if not project:
        return None
    path = project.get_imported_file_path("topography")
    return path if path and os.path.isfile(path) else None


def topography_csv_points(dock):
    """Points ``(along, offset, z)`` du CSV topographie projetés sur
    la ligne de coupe.  None si absent / illisible / sans X;Y;Z.
    Plafonné à 20 000 points (signalé dans le statut).
    """
    path = dock._topography_csv_path()
    if not path or dock._line is None:
        return None
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    cache = getattr(dock, "_topo_csv_cache", None)
    if cache and cache[0] == path and cache[1] == mtime:
        return cache[2]
    from ..core.csv_parser import (
        detect_encoding, detect_separator, header_match_details)
    points = []
    try:
        encoding = detect_encoding(path)
        with open(path, "r", encoding=encoding, newline="") as handle:
            head = handle.read(65536)
            handle.seek(0)
            separator = detect_separator(head.splitlines()[:20])
            rows = list(csv.reader(handle, delimiter=separator))
    except (OSError, UnicodeDecodeError, csv.Error):
        return None
    if len(rows) < 2:
        return None
    headers = [str(h).strip() for h in rows[0]]
    indexes = {}
    for index, header in enumerate(headers):
        canonical = header_match_details(header).get("canonical")
        if canonical in ("collar_x", "collar_y", "collar_z") \
                and canonical not in indexes:
            indexes[canonical] = index
    if len(indexes) < 3:
        return None
    line = dock._line
    for row in rows[1:20001]:
        try:
            x = float(str(row[indexes["collar_x"]]).strip().replace(",", "."))
            y = float(str(row[indexes["collar_y"]]).strip().replace(",", "."))
            z = float(str(row[indexes["collar_z"]]).strip().replace(",", "."))
        except (IndexError, ValueError):
            continue
        if not all(math.isfinite(v) for v in (x, y, z)):
            continue
        along, offset = project_point_onto_section(x, y, line)
        points.append((along, offset, z))
    dock._topo_csv_cache = (path, mtime, points)
    return points


def surface_provider(dock):
    """Provider appelé par le canvas à chaque régénération.

    Retourne ``(profil, source, infobulle)``.  Le profil est ANCRÉ aux
    collets de la coupe (core.topography) et couvre le corridor
    ``[-buffer, longueur+buffer]``.  Met à jour le statut du panneau
    en effet de bord.  Toute exception est avalée par le canvas :
    la coupe ne doit jamais être bloquée par la topographie.
    """
    _md = getattr(dock, "main_dock", None)
    _proj = getattr(_md, "project", None) if _md else None
    # v2.9.314 — ancrage aux collets au choix (défaut ON = comportement
    # historique) ; OFF = MNT mesuré seul, stable quel que soit le jeu.
    anchor = bool(((_proj.config.get("section_surface") or {})
                   if _proj else {}).get("anchor_collars", True))
    line = dock._line
    if line is None or not dock._drillholes:
        dock._update_surface_status("", None, [])
        return (None, "", "")
    buffer = dock.buffer_spin.value()
    buffer_mode = dock.buffer_mode_combo.currentData() or "collar"
    a_min = -buffer
    a_max = line.length + buffer

    # Collets de la coupe (même règle de buffer que la section).
    # v2.9.179 — D1 validé : un forage EXCLUT est absent de la coupe,
    # donc sa ligne de sol non plus (elle ne l'ancre plus).
    excluded = set(getattr(dock, "_excluded_holes", None) or set())
    collars = []
    for dh in dock._drillholes:
        if not dh.trajectory or not dh.collar:
            continue
        if dh.hole_id in excluded:
            continue
        status = drillhole_buffer_status(dh, line, buffer, buffer_mode)
        if not status["included"]:
            continue
        along, _off = project_point_onto_section(
            dh.collar.x, dh.collar.y, line)
        collars.append((along, dh.collar.z, dh.hole_id))

    # v2.9.3 — le combo suit les rasters du projet QGIS actif (un
    # DEM chargé après l'ouverture de la vue apparaît ici).
    dock._refresh_surface_combo()

    source = ""
    profile = None
    qc = []
    dem_reject = ""
    raw_samples = 0
    # 1) RASTER MNT du projet QGIS — toujours prioritaire (décision).
    layer = dock._surface_raster_layer()
    if layer is not None:
        sampled, why = dock._sample_raster_along_line(
            layer, line, a_min, a_max)
        raw_samples = len(sampled)
        if len(sampled) >= 2:
            profile, source = sampled, "dem"
        else:
            dem_reject = _tr(
                "MNT « {} » détecté mais non utilisé : {}.").format(
                    layer.name() or '?', why)
    # 2) CSV x;y;z fourni dans le projet.
    if profile is None:
        csv_pts = dock._topography_csv_points()
        if csv_pts:
            in_corridor = [
                (along, z)
                for (along, _off, z) in csv_pts
                if abs(_off) <= buffer]
            if len(in_corridor) >= 2:
                profile = profile_from_collars(
                    in_corridor, a_min, a_max)
                source = "csv"
    # 3) COLLETS SEULEMENT — filet de sécurité universel.
    if profile is None:
        profile = profile_from_collars(
            [(a, z) for (a, z, _id) in collars], a_min, a_max)
        source = "collars" if profile else ""

    if not profile:
        dock._update_surface_status("", None, [])
        return (None, "", "")

    # QC + ancrage aux collets (sources mesurées uniquement : pour
    # « collets seulement » le profil passe déjà exactement par eux).
    if source in ("dem", "csv"):
        # QC sur le profil BRUT (avant lissage) — source unique des
        # écarts affichés (TOPO-33).
        if collars:
            qc = collar_deviations(profile, collars)
        # v2.9.10 — anti-escalier : densifier + lisser la forme MNT,
        # puis ré-ancrer EXACTEMENT aux collets (priorité levé).
        # Sans ça, un MNT pixelisé donne une ligne « en marches »
        # (retour écran).
        profile = refine_surface_profile(profile, collars if anchor else [])
    elif source == "collars" and profile:
        # Collets-only : déjà linéaire — densifier seulement pour un
        # trait plus propre (pas de lissage qui arrondirait les
        # sommets collets ; refine ré-ancre).
        profile = refine_surface_profile(profile, collars if anchor else [])

    threshold = dock.surface_qc_threshold.value()
    tooltip = dock._surface_tooltip_text(source, profile, collars, qc,
                                          threshold,
                                          reject=dem_reject)
    dock._update_surface_status(source, layer if source == "dem" else None,
                                qc, threshold, n_collars=len(collars),
                                n_samples=(raw_samples
                                           if source == "dem"
                                           else len(profile)),
                                note=dem_reject)
    return (profile, source, tooltip)


def surface_tooltip_text(dock, source, profile, collars, qc, threshold, reject=''):
    if not source and not reject:
        return _tr("Topo · aucune surface")
    if source == "dem":
        lines = [_tr("Topo · MNT · {} pts").format(len(profile))]
    elif source == "csv":
        name = ""
        path = dock._topography_csv_path()
        if path:
            name = os.path.basename(path)
        lines = [_tr("Topo · CSV {} · {} pts").format(name, len(profile))
                 if name
                 else _tr("Topo · CSV · {} pts").format(len(profile))]
    else:
        lines = [_tr("Topo · collets ({}) · interpolé")
                 .format(len(collars))]
    if source in ("dem", "csv") and qc:
        flagged = [d for d in qc if d["diff"] is not None
                   and abs(d["diff"]) > threshold]
        if flagged:
            worst = max(flagged, key=lambda d: abs(d["diff"]))
            lines.append(
                _tr("QC · {} écart(s) > {} m · {} {:+.1f} m").format(
                    len(flagged), f"{threshold:g}",
                    worst["hole_id"], worst["diff"]))
        else:
            lines.append(QCoreApplication.translate(
                "SectionWidget", "QC · OK ≤ {} m").format(f"{threshold:g}"))
    if reject:
        # garder court
        short = reject if len(reject) <= 60 else reject[:57] + "…"
        lines.append(_tr("⚠ {}").format(short))
    return "\n".join(lines)


def update_surface_status(dock, source, layer, qc, threshold=None, n_collars=0, n_samples=0, note=''):
    if not source:
        dock.surface_status.setText(
            QCoreApplication.translate(
                "SectionWidget",
                "Aucune source de surface (ni MNT chargé, ni CSV "
                "topographie, ni collet dans le buffer)."))
        dock.surface_status.setStyleSheet(
            f"font-size:8pt; color:{COLORS['text_light']};")
        return
    if source == "dem":
        name = layer.name() if layer is not None else "?"
        head = _tr("Sol : MNT « {} » ({} pts) ancré à {} "
                   "collet(s) — trait plein.").format(
                       name, n_samples, n_collars)
    elif source == "csv":
        head = _tr("Sol : CSV topographie ({} pts) ancré à {} "
                   "collet(s) — trait plein.").format(
                       n_samples, n_collars)
    else:
        head = _tr("Sol : interpolation collet-à-collet ({} collets) "
                   "— trait pointillé.").format(n_collars)
    def _emit(text, colour):
        # v2.9.3 — un MNT écarté est TOUJOURS signalé dans le statut
        # (affiché, jamais masqué), quelle que soit la source retenue.
        if note:
            text += _tr(" ⚠ {}").format(note)
            colour = "#B9770E"
        dock.surface_status.setText(text)
        dock.surface_status.setStyleSheet(
            f"font-size:8pt; color:{colour};")

    if source == "collars" or not qc:
        _emit(head, COLORS["text_medium"])
        return
    threshold = threshold if threshold is not None else 2.0
    flagged = [d for d in qc if d["diff"] is not None
               and abs(d["diff"]) > threshold]
    if flagged:
        names = ", ".join(
            f"{d['hole_id']} {d['diff']:+.1f} m" for d in flagged[:4])
        if len(flagged) > 4:
            names += f" (+{len(flagged) - 4})"
        _emit(_tr("{} ⚠ {} écart(s) MNT↔collets > {} m : {}").format(
            head, len(flagged), f"{threshold:g}", names), "#B9770E")
    else:
        _emit(_tr("{} QC : écarts MNT↔collets ≤ {} m.").format(
            head, f"{threshold:g}"), COLORS["success"])


def update_surface_detection_status(dock):
    """v2.9.2 — le statut « MNT chargé ou détecté » est VISIBLE EN
    PERMANENCE (même avant la 1ʳᵉ génération) : quel MNT la cascade
    prend, si le projet porte un CSV topographie.

    Après qu'une coupe a été RENDUE, le statut du provider (source
    ancrée + QC MNT↔collets) est plus riche et reste en place —
    cette méthode ne l'écrase jamais (garde ``_result``)."""
    if dock.canvas._result is not None:
        return
    layers = [lyr for _lid, lyr in dock._qgis_raster_layers()]
    choice = dock.surface_combo.currentData() or "auto"
    if choice == "none":
        head = _tr("MNT hors jeu (choix « Aucun raster ») → CSV "
                   "x;y;z / collets.")
    elif layers:
        if choice == "auto":
            name = layers[0].name() or "?"
            extra = (_tr(" — {} rasters dans le projet")
                     .format(len(layers)) if len(layers) > 1 else "")
        else:
            layer = next((l for l in layers if l.id() == choice),
                         None)
            name = (layer.name() or choice) if layer is not None else choice
            extra = ""
        head = _tr("MNT détecté : « {} »{}.").format(name, extra)
    else:
        head = _tr("Aucun MNT raster dans le projet QGIS (un DEM doit "
                   "être une couche RASTER — ni vecteur, ni maillage) "
                   "→ cascade CSV x;y;z / collets.")
    csv_path = dock._topography_csv_path()
    if csv_path:
        head += f" CSV topographie : {os.path.basename(csv_path)}."
    dock.surface_status.setText(head)
    dock.surface_status.setStyleSheet(
        f"font-size:8pt; color:{COLORS['text_medium']};")


def on_surface_source_change(dock, *_args):
    if dock._loading_settings:
        return
    dock._populate_surface_combo()
    try:
        dock.canvas._surface_choice = str(
            dock.surface_combo.currentData() or "")
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Cascade MNT : changement de source (recalcul surface)", _exc)
        # combo pas prêt
        pass
    if dock.canvas._drillholes and dock.canvas._line:
        dock.canvas._regenerate()
    dock._persist_section = True
    dock._persist_timer.start()


def on_surface_qc_change(dock, *_args):
    if dock._loading_settings:
        return
    # Le seuil ne change que l'affichage du QC (et l'infobulle) ;
    # on re-rend sans re-projeter.
    if dock.canvas._result:
        dock.canvas._render()
    dock._persist_section = True
    dock._persist_timer.start()


def refresh_surface_combo(dock):
    """v2.9.3 — le combo « Source MNT » suit les COUCHES DU PROJET
    QGIS ACTIF : un DEM ajouté après l'ouverture de la vue apparaît
    sans rechargement (appelé à chaque régénération, par le
    provider).  Reconstruit seulement si la liste a changé — et le
    statut « MNT détecté » est mis à jour avec elle."""
    layers = dock._qgis_raster_layers()
    keys = [(lid, lyr.name() or lid) for lid, lyr in layers]
    if getattr(dock, "_surface_combo_keys", None) == keys:
        return
    dock._surface_combo_keys = keys
    dock._populate_surface_combo()


def populate_surface_combo(dock):
    """Rasters du projet QGIS dans le combo « Source MNT ».

    Conserve la sélection (par id de couche) ; « auto » par défaut.
    """
    current = dock.surface_combo.currentData()
    dock.surface_combo.blockSignals(True)
    dock.surface_combo.clear()
    dock.surface_combo.addItem(QCoreApplication.translate("SectionWidget", "Automatique (MNT du projet)"), "auto")
    for lid, lyr in dock._qgis_raster_layers():
        dock.surface_combo.addItem(lyr.name() or lid, lid)
    dock.surface_combo.addItem(QCoreApplication.translate("SectionWidget", "Aucun raster (CSV / collets)"), "none")
    target = "auto"
    if current and dock.surface_combo.findData(current) >= 0:
        target = current
    dock._set_combo_data(dock.surface_combo, target)
    dock.surface_combo.blockSignals(False)
    # v2.9.2 — statut MNT détecté visible en permanence (après un
    # rendu, le statut provider ancrage+QC reprend la main).
    dock._update_surface_detection_status()

