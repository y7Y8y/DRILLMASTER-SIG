"""
DrillMaster — QGIS Layer Management
====================================
Uses memory layers for reliable display, saves to GeoPackage.
"""

from __future__ import annotations

import math

from .data_model import DrillHole
from .geometry import depth_to_xyz

# Group names — v2.7.4 : clean sequential numbering (feedback 18/08/2026 :
# the intermediate "03b/03c" names were judged unreadable).
GROUP_ROOT_TEMPLATE = "FORAGES - {name}"
GROUP_GEOMETRY = "01_Implantation_et_trajectoires"
GROUP_LITHO = "02_Lithologie"
GROUP_ASSAYS = "03_Teneurs"
GROUP_ALTERATIONS = "04_Altérations"
GROUP_MINERALIZATIONS = "05_Minéralisations"
GROUP_STRUCTURE = "06_Structures"
GROUP_SECTIONS = "07_Coupes"

# Names used by earlier versions (and before for Coupes).  Existing groups
# are RENAMED in place so the user's layer tree keeps its content — nothing
# is recreated empty next to a stale group.
GROUP_RENAMES = {
    "03b_Altérations": GROUP_ALTERATIONS,
    "03c_Minéralisations": GROUP_MINERALIZATIONS,
    "04_Coupes": GROUP_SECTIONS,
    "06_Coupes": GROUP_SECTIONS,
}

# Stable storage layer names (GeoPackage backward compatibility).
LAYER_COLLARS = "Collets"
LAYER_SURVEY = "Survey"
LAYER_LITHO = "Lithologie"
LAYER_ASSAYS = "Assays"
LAYER_ALTERATIONS = "Alterations"
LAYER_MINERALIZATIONS = "Mineralizations"
LAYER_STRUCTURE = "Structures"
# Truthful names displayed in the QGIS layer tree.
DISPLAY_SURVEY = "Trajectoires des forages"
DISPLAY_ASSAYS = "Teneurs"
LAYER_SURVEY_STATIONS = "Survey_Stations"
LAYER_SECTION_LINE = "Ligne de coupe"


def get_or_create_root_group(project_name):
    from qgis.core import QgsProject
    root = QgsProject.instance().layerTreeRoot()
    name = GROUP_ROOT_TEMPLATE.format(name=project_name)
    g = root.findGroup(name)
    if g is None:
        g = root.insertGroup(0, name)
    return g


def create_group_hierarchy(project_name):
    root = get_or_create_root_group(project_name)
    # v2.7.4 migration : rename groups created with the intermediate
    # v2.7.3 numbering ("03b_…", "03c_…", "04_Coupes") in place.
    for old_name, new_name in GROUP_RENAMES.items():
        old_group = root.findGroup(old_name)
        if old_group is not None and root.findGroup(new_name) is None:
            old_group.setName(new_name)
    def _goc(p, n):
        g = p.findGroup(n)
        return g if g else p.addGroup(n)
    return {
        "root": root,
        "geometry": _goc(root, GROUP_GEOMETRY),
        "litho": _goc(root, GROUP_LITHO),
        "assays": _goc(root, GROUP_ASSAYS),
        "alterations": _goc(root, GROUP_ALTERATIONS),
        "mineralizations": _goc(root, GROUP_MINERALIZATIONS),
        "structure": _goc(root, GROUP_STRUCTURE),
        "sections": _goc(root, GROUP_SECTIONS),
    }


# --- Memory layer creation ---
def _create_mem_layer(name, wkb_type_str, crs, fields):
    from qgis.core import QgsVectorLayer
    uri = f"{wkb_type_str}?crs={crs.authid()}"
    layer = QgsVectorLayer(uri, name, "memory")
    if not layer.isValid():
        # Fallback without Z
        base = wkb_type_str.replace("Z", "")
        uri = f"{base}?crs={crs.authid()}"
        layer = QgsVectorLayer(uri, name, "memory")
    layer.dataProvider().addAttributes(fields)
    layer.updateFields()
    return layer


def _collar_fields():
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    return [
        QgsField("hole_id", QVariant.String, len=50),
        QgsField("x", QVariant.Double),
        QgsField("y", QVariant.Double),
        QgsField("z", QVariant.Double),
        QgsField("max_depth", QVariant.Double),
        QgsField("azimuth", QVariant.Double),
        QgsField("dip", QVariant.Double),
        QgsField("hole_type", QVariant.String, len=20),  # v2.9.289
        QgsField("short_id", QVariant.String, len=10),  # v2.9.307
    ]


def _survey_fields():
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    return [QgsField("hole_id", QVariant.String, len=50)]


def _litho_fields():
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    return [
        QgsField("hole_id", QVariant.String, len=50),
        QgsField("from_depth", QVariant.Double),
        QgsField("to_depth", QVariant.Double),
        QgsField("lithology", QVariant.String, len=100),
        QgsField("component_role", QVariant.String, len=40),
        QgsField("raw_role", QVariant.String, len=80),
        QgsField("proportion", QVariant.Double),
        QgsField("proportion_unit", QVariant.String, len=20),
        QgsField("source_line", QVariant.Int),
        QgsField("is_primary", QVariant.Bool),
    ]


def _survey_station_fields():
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    return [
        QgsField("hole_id", QVariant.String, len=50),
        QgsField("depth", QVariant.Double),
        QgsField("azimuth", QVariant.Double),
        QgsField("dip", QVariant.Double),
    ]


def _structure_fields():
    """v2.9.258-rendu — fields of the point-wise ``structure`` layer."""
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    return [
        QgsField("hole_id", QVariant.String, len=50),
        QgsField("depth", QVariant.Double),
        QgsField("type", QVariant.String, len=100),
        QgsField("dip", QVariant.Double),
        QgsField("dip_direction", QVariant.Double),
        QgsField("alpha", QVariant.Double),
        QgsField("beta", QVariant.Double),
        QgsField("confidence", QVariant.String, len=40),
        QgsField("comment", QVariant.String, len=255),
    ]


def _alteration_fields():
    """v2.7.3 — one row per alteration component, mirroring Lithologie.

    ``raw_cell`` always carries the untouched source cell so an explicit
    delimited split stays fully recoverable when the project is reloaded
    from the GeoPackage (source values are never modified nor lost).
    """
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    return [
        QgsField("hole_id", QVariant.String, len=50),
        QgsField("from_depth", QVariant.Double),
        QgsField("to_depth", QVariant.Double),
        QgsField("alteration", QVariant.String, len=100),
        QgsField("raw_cell", QVariant.String, len=200),
        QgsField("component_role", QVariant.String, len=40),
        QgsField("raw_role", QVariant.String, len=80),
        QgsField("intensity", QVariant.String, len=40),
        QgsField("source_line", QVariant.Int),
    ]


def _mineralization_fields():
    """v2.7.3 — one row per observed mineralization interval (raw style,
    raw minerals text, intensity).  Minerals are never auto-split (AM-05).
    """
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    return [
        QgsField("hole_id", QVariant.String, len=50),
        QgsField("from_depth", QVariant.Double),
        QgsField("to_depth", QVariant.Double),
        QgsField("mineralization_style", QVariant.String, len=100),
        QgsField("minerals", QVariant.String, len=200),
        QgsField("intensity", QVariant.String, len=40),
        QgsField("source_line", QVariant.Int),
    ]


def _assay_fields(element_columns):
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QVariant
    f = [
        QgsField("hole_id", QVariant.String, len=50),
        QgsField("from_depth", QVariant.Double),
        QgsField("to_depth", QVariant.Double),
    ]
    for c in (element_columns or []):
        f.append(QgsField(c, QVariant.Double))
    return f


# --- Geometry helpers ---
def _ptz(x, y, z):
    from qgis.core import QgsPoint
    return QgsPoint(x, y, z)


def _linez(pts3d):
    from qgis.core import QgsLineString, QgsPoint
    return QgsLineString([QgsPoint(x, y, z) for x, y, z in pts3d])


def _seg(dh, fd, td):
    t = depth_to_xyz(dh.trajectory, fd)
    b = depth_to_xyz(dh.trajectory, td)
    if t is None or b is None:
        return None
    return [t, b]


# --- Populate functions ---
def _add_feats(layer, feats):
    layer.dataProvider().addFeatures(feats)
    layer.updateExtents()


def _populate_collars(layer, dhs):
    from qgis.core import QgsFeature, QgsGeometry
    from .short_ids import compact_label, label_width
    width = label_width([d.hole_id for d in dhs])
    fs = []
    for dh in dhs:
        f = QgsFeature()
        f.setFields(layer.fields())
        f.setGeometry(QgsGeometry(_ptz(dh.collar.x, dh.collar.y, dh.collar.z)))
        f.setAttributes([dh.hole_id, dh.collar.x, dh.collar.y, dh.collar.z,
                         dh.collar.max_depth,
                         dh.collar.azimuth, dh.collar.dip,
                         getattr(dh.collar, "hole_type", None) or "",
                         compact_label(dh.hole_id, width)])
        fs.append(f)
    _add_feats(layer, fs)


def _populate_survey(layer, dhs):
    from qgis.core import QgsFeature, QgsGeometry
    fs = []
    for dh in dhs:
        if not dh.trajectory:
            continue
        pts = [(tp.x, tp.y, tp.z) for tp in dh.trajectory]
        f = QgsFeature()
        f.setFields(layer.fields())
        f.setGeometry(QgsGeometry(_linez(pts)))
        f.setAttributes([dh.hole_id])
        fs.append(f)
    _add_feats(layer, fs)


def _populate_survey_stations(layer, dhs):
    """Save the real survey stations (depth/az/dip) for faithful restore."""
    from qgis.core import QgsFeature, QgsGeometry
    from .geometry import depth_to_xyz
    fs = []
    for dh in dhs:
        for st in dh.survey:
            xyz = depth_to_xyz(dh.trajectory, st.depth)
            if xyz is None:
                continue
            f = QgsFeature()
            f.setFields(layer.fields())
            f.setGeometry(QgsGeometry(_ptz(xyz[0], xyz[1], xyz[2])))
            f.setAttributes([dh.hole_id, st.depth, st.azimuth, st.dip])
            fs.append(f)
    _add_feats(layer, fs)


def _populate_structure(layer, dhs):
    """v2.9.258-rendu — one PointZ feature per structure measurement.

    Position is interpolated on the drillhole trajectory at the measured
    depth, exactly like the survey stations.
    """
    from qgis.core import QgsFeature, QgsGeometry
    fs = []
    for dh in dhs:
        for st in dh.structure:
            xyz = depth_to_xyz(dh.trajectory, st.depth)
            if xyz is None:
                continue
            f = QgsFeature()
            f.setFields(layer.fields())
            f.setGeometry(QgsGeometry(_ptz(xyz[0], xyz[1], xyz[2])))
            f.setAttributes([
                dh.hole_id,
                float(st.depth),
                str(st.type or ""),
                st.dip,
                st.dip_direction,
                st.alpha,
                st.beta,
                str(st.confidence or "") or None,
                str(st.comment or ""),
            ])
            fs.append(f)
    _add_feats(layer, fs)


def _populate_litho(layer, dhs):
    from qgis.core import QgsFeature, QgsGeometry
    from .data_model import LithologyComponent
    fs = []
    for dh in dhs:
        for iv in dh.litho:
            s = _seg(dh, iv.from_depth, iv.to_depth)
            if s is None:
                continue
            components = list(iv.components)
            if not components:
                components = [LithologyComponent(
                    raw_code=iv.attributes.get("lithology", ""),
                    role="primary", raw_role="primary",
                    source_line=iv.source_line)]
            explicit_primary = iv.primary_component
            for component in components:
                is_primary = component is explicit_primary
                f = QgsFeature()
                f.setFields(layer.fields())
                # Secondary/accessory rows persist their provenance without
                # being drawn as an overlapping primary line in v2.7.1.
                if is_primary:
                    f.setGeometry(QgsGeometry(_linez(s)))
                f.setAttributes([
                    dh.hole_id, iv.from_depth, iv.to_depth,
                    component.raw_code, component.role,
                    component.raw_role, component.proportion,
                    component.proportion_unit, component.source_line,
                    is_primary,
                ])
                fs.append(f)
    _add_feats(layer, fs)


def _populate_assays(layer, dhs, elem_cols):
    from qgis.core import QgsFeature, QgsGeometry
    fs = []
    for dh in dhs:
        for iv in dh.assays:
            s = _seg(dh, iv.from_depth, iv.to_depth)
            if s is None:
                continue
            f = QgsFeature()
            f.setFields(layer.fields())
            f.setGeometry(QgsGeometry(_linez(s)))
            attrs = [dh.hole_id, iv.from_depth, iv.to_depth]
            for c in elem_cols:
                attrs.append(iv.attributes.get(c))
            f.setAttributes(attrs)
            fs.append(f)
    _add_feats(layer, fs)


def _domain_interval_codes(iv, attribute):
    """Codes carried by one coded-track interval (components first)."""
    codes = [c.raw_code for c in (iv.components or []) if c.raw_code]
    if codes:
        return codes
    value = iv.attributes.get(attribute)
    return [value] if value not in (None, "") else []


def _populate_alterations(layer, dhs):
    """v2.7.3 — one row per alteration component (AM-06 split included),
    raw cell always preserved in ``raw_cell``."""
    from qgis.core import QgsFeature, QgsGeometry
    fs = []
    for dh in dhs:
        for iv in getattr(dh, "alterations", []) or []:
            s = _seg(dh, iv.from_depth, iv.to_depth)
            if s is None:
                continue
            raw_cell = str(iv.attributes.get("alteration", "") or "")
            intensity = str(iv.attributes.get("intensity", "") or "")
            codes = _domain_interval_codes(iv, "alteration")
            components = {id(c): c for c in (iv.components or [])}
            for code in codes:
                component = next(
                    (c for c in components.values() if c.raw_code == code),
                    None)
                if component is None and len(codes) == 1:
                    role, raw_role = "", ""
                    source_line = iv.source_line
                else:
                    role = component.role if component else ""
                    raw_role = component.raw_role if component else ""
                    source_line = (component.source_line if component
                                   else iv.source_line)
                f = QgsFeature()
                f.setFields(layer.fields())
                f.setGeometry(QgsGeometry(_linez(s)))
                f.setAttributes([
                    dh.hole_id, iv.from_depth, iv.to_depth,
                    code, raw_cell, role, raw_role, intensity,
                    int(source_line or 0),
                ])
                fs.append(f)
    _add_feats(layer, fs)


def _populate_mineralizations(layer, dhs):
    """v2.7.3 — one row per mineralization interval; raw style, raw
    minerals text and intensity stay exactly as read from the CSV."""
    from qgis.core import QgsFeature, QgsGeometry
    fs = []
    for dh in dhs:
        for iv in getattr(dh, "mineralizations", []) or []:
            s = _seg(dh, iv.from_depth, iv.to_depth)
            if s is None:
                continue
            f = QgsFeature()
            f.setFields(layer.fields())
            f.setGeometry(QgsGeometry(_linez(s)))
            f.setAttributes([
                dh.hole_id, iv.from_depth, iv.to_depth,
                str(iv.attributes.get("mineralization_style", "") or ""),
                str(iv.attributes.get("minerals", "") or ""),
                str(iv.attributes.get("intensity", "") or ""),
                int(iv.source_line or 0),
            ])
            fs.append(f)
    _add_feats(layer, fs)


# --- Save memory layer to GPKG ---
def _writer_result_status(result):
    """Normalise QGIS writer results across QGIS 3.x releases.

    Depending on the QGIS version, ``writeAsVectorFormatV3`` returns two,
    three or four values. Older DrillMaster code unpacked exactly two values,
    causing a false write error on versions returning four.
    """
    if isinstance(result, (tuple, list)):
        if not result:
            return -1, "Résultat d’écriture vide"
        error = result[0]
        message = ""
        if len(result) > 1 and result[1] not in (None, ""):
            message = str(result[1])
        return error, message
    return result, ""


def _save_to_gpkg(layer, gpkg_path, layer_name):
    from qgis.core import (
        QgsVectorFileWriter, QgsCoordinateTransformContext, QgsVectorLayer,
    )
    import os
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.fileEncoding = "UTF-8"
    opts.layerName = layer_name
    if os.path.isfile(gpkg_path):
        opts.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    ctx = QgsCoordinateTransformContext()
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, gpkg_path, ctx, opts)
    err, msg = _writer_result_status(result)
    if err not in (QgsVectorFileWriter.NoError, 0):
        detail = msg or f"code erreur {err}"
        raise RuntimeError(f"GPKG {layer_name}: {detail}")

    # Do not trust only the return code: verify the file and layer can be read.
    if not os.path.isfile(gpkg_path):
        raise RuntimeError(f"GPKG {layer_name} : fichier non créé")
    check = QgsVectorLayer(
        f"{gpkg_path}|layername={layer_name}", layer_name, "ogr")
    if not check.isValid():
        raise RuntimeError(
            f"GPKG {layer_name}: couche ecrite mais illisible")


# --- Main setup ---
def setup_all_layers(project_name, geometry_gpkg, data_gpkg, crs, drillholes,
                     element_columns=None, litho_colors=None, assay_style=None,
                     save_gpkg=True, domain_style_resolver=None):
    from qgis.core import QgsProject
    from .styles import (create_collar_style, create_survey_style,
                         create_litho_style, create_assay_style,
                         create_domain_style, create_structure_style)
    from .section import get_all_litho_codes

    def _domain_styles(domain, codes):
        """Referential styles {code: {color, label, pattern}} for the QGIS
        categorized renderer — same source as the 2D section view."""
        styles = {}
        resolver = domain_style_resolver
        for code in codes:
            info = None
            if resolver is not None:
                try:
                    info = resolver(domain, code)
                except Exception as _exc:
                    from .diagnostics import log_swallowed
                    log_swallowed("layers : _domain_styles", _exc)
                    info = None
            if info is not None and (getattr(info, "color", "") or
                                     getattr(info, "label", "")):
                styles[code] = {
                    "color": getattr(info, "color", "") or "",
                    "label": getattr(info, "label", "") or code,
                    "pattern": getattr(info, "pattern", "") or "",
                    "visible": bool(getattr(info, "visible", True)),
                }
        return styles

    groups = create_group_hierarchy(project_name)
    layers = {}

    # Collars
    cl = _create_mem_layer(LAYER_COLLARS, "PointZ", crs, _collar_fields())
    _populate_collars(cl, drillholes)
    cl.setRenderer(create_collar_style())
    try:  # v2.9.304 — id trou lisible au zoom, discret en vue large.
        from qgis.core import (QgsPalLayerSettings,
                               QgsVectorLayerSimpleLabeling)
        ps = QgsPalLayerSettings()
        ps.fieldName = "short_id"  # v2.9.307 même règle courte que le plugin
        ps.dist = 0.8
        ps.scaleVisibility = True
        ps.minimumScale = 50000
        ps.maximumScale = 1
        cl.setLabeling(QgsVectorLayerSimpleLabeling(ps))
        cl.setLabelsEnabled(True)
    except Exception as _exc:  # jamais bloquant pour la couche
        from .diagnostics import log_swallowed
        log_swallowed("layers : étiquettes collets", _exc)
    QgsProject.instance().addMapLayer(cl, False)
    groups["geometry"].addLayer(cl)
    layers["collars"] = cl

    # Survey
    sl = _create_mem_layer(DISPLAY_SURVEY, "LineStringZ", crs, _survey_fields())
    _populate_survey(sl, drillholes)
    sl.setRenderer(create_survey_style())
    QgsProject.instance().addMapLayer(sl, False)
    groups["geometry"].addLayer(sl)
    layers["survey"] = sl

    # Litho - only if data exists
    if any(dh.litho for dh in drillholes):
        ll = _create_mem_layer(LAYER_LITHO, "LineStringZ", crs, _litho_fields())
        _populate_litho(ll, drillholes)
        # Only create categories for codes that actually exist in the data
        actual_codes = get_all_litho_codes(drillholes)
        ll.setRenderer(create_litho_style(actual_codes, litho_colors))
        QgsProject.instance().addMapLayer(ll, False)
        groups["litho"].addLayer(ll)
        layers["litho"] = ll

    # Assays - one shared grade map for the map and all section views.
    if any(dh.assays for dh in drillholes):
        elem_cols = element_columns or []
        al = _create_mem_layer(DISPLAY_ASSAYS, "LineStringZ", crs, _assay_fields(elem_cols))
        _populate_assays(al, drillholes, elem_cols)
        assay_cfg = assay_style or {}
        element = assay_cfg.get("element")
        if element not in elem_cols:
            element = elem_cols[0] if elem_cols else None
        values = []
        if element:
            for dh in drillholes:
                for iv in dh.assays:
                    value = iv.attributes.get(element)
                    if isinstance(value, (int, float)):
                        values.append(value)
        al.setRenderer(create_assay_style(element, values, assay_cfg))
        QgsProject.instance().addMapLayer(al, False)
        groups["assays"].addLayer(al)
        layers["assays"] = al

    # Altérations & Minéralisations (v2.7.3) — same contract as the litho :
    # own memory layers, categorized by the referential styles, persisted
    # to the data GeoPackage and restorable on project reopen.
    if any(getattr(dh, "alterations", None) for dh in drillholes):
        alt_codes = sorted({
            code for dh in drillholes
            for iv in dh.alterations
            for code in _domain_interval_codes(iv, "alteration")},
            key=str.casefold)
        al = _create_mem_layer(
            LAYER_ALTERATIONS, "LineStringZ", crs, _alteration_fields())
        _populate_alterations(al, drillholes)
        al.setRenderer(create_domain_style(
            "alteration", alt_codes,
            _domain_styles("alteration", alt_codes)))
        QgsProject.instance().addMapLayer(al, False)
        groups["alterations"].addLayer(al)
        layers["alterations"] = al

    if any(getattr(dh, "mineralizations", None) for dh in drillholes):
        min_codes = sorted({
            str(iv.attributes.get("mineralization_style", "") or "")
            for dh in drillholes for iv in dh.mineralizations
            if str(iv.attributes.get("mineralization_style", "")
                   or "").strip()},
            key=str.casefold)
        ml = _create_mem_layer(
            LAYER_MINERALIZATIONS, "LineStringZ", crs,
            _mineralization_fields())
        _populate_mineralizations(ml, drillholes)
        ml.setRenderer(create_domain_style(
            "mineralization_style", min_codes,
            _domain_styles("mineralization_style", min_codes)))
        QgsProject.instance().addMapLayer(ml, False)
        groups["mineralizations"].addLayer(ml)
        layers["mineralizations"] = ml

    # Structures observées — point-wise measurements (v2.9.258-rendu).
    # PointZ, one feature per measurement, coloured by `type` from the
    # project Référentiel (no separate frozen palette).
    if any(getattr(dh, "structure", None) for dh in drillholes):
        structure_codes = sorted({
            str(st.type or "").strip()
            for dh in drillholes for st in dh.structure
            if str(st.type or "").strip()},
            key=str.casefold)
        stl = _create_mem_layer(
            LAYER_STRUCTURE, "PointZ", crs, _structure_fields())
        _populate_structure(stl, drillholes)
        stl.setRenderer(create_structure_style(
            structure_codes,
            _domain_styles("structure", structure_codes)))
        QgsProject.instance().addMapLayer(stl, False)
        groups["structure"].addLayer(stl)
        layers["structure"] = stl

    # Survey stations table (for faithful project restore from GPKG)
    st_layer = None
    if any(dh.survey for dh in drillholes):
        st_layer = _create_mem_layer(LAYER_SURVEY_STATIONS, "PointZ", crs,
                                     _survey_station_fields())
        _populate_survey_stations(st_layer, drillholes)

    # Save to GPKG — with an explicit report (no more silent failures)
    import os
    gpkg_report = {"geometry": [], "data": [], "errors": [],
                   "restored": not save_gpkg}
    if save_gpkg:
        for layer, gpkg, name in (
            (cl, geometry_gpkg, LAYER_COLLARS),
            (sl, geometry_gpkg, LAYER_SURVEY),
            (layers.get("litho"), data_gpkg, LAYER_LITHO),
            (layers.get("assays"), data_gpkg, LAYER_ASSAYS),
            (layers.get("alterations"), data_gpkg, LAYER_ALTERATIONS),
            (layers.get("mineralizations"), data_gpkg,
             LAYER_MINERALIZATIONS),
            (layers.get("structure"), data_gpkg, LAYER_STRUCTURE),
            (st_layer, data_gpkg, LAYER_SURVEY_STATIONS),
        ):
            if layer is None:
                continue
            try:
                _save_to_gpkg(layer, gpkg, name)
                key = "geometry" if gpkg == geometry_gpkg else "data"
                gpkg_report[key].append(name)
            except Exception as e:
                from .diagnostics import log_swallowed
                log_swallowed(f"Couches GeoPackage : écriture de {name}", e)
                gpkg_report["errors"].append(f"{name}: {e}")

    gpkg_report["geometry_file"] = os.path.basename(geometry_gpkg)
    gpkg_report["data_file"] = os.path.basename(data_gpkg)

    # Compute combined extent and zoom
    combined_ext = None
    if "collars" in layers:
        combined_ext = layers["collars"].extent()
        for key in ("survey", "litho", "assays", "alterations",
                    "mineralizations", "structure"):
            if key in layers:
                combined_ext.combineExtentWith(layers[key].extent())

    return layers, combined_ext, gpkg_report


def create_section_line_layer(line_coords, crs, group, layer_name=None):
    from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry,
                           QgsLineString, QgsPoint, QgsProject)
    from .styles import create_section_line_style

    name = layer_name or LAYER_SECTION_LINE
    layer = QgsVectorLayer(f"LineString?crs={crs.authid()}", name, "memory")
    f = QgsFeature()
    pts = [QgsPoint(line_coords[0][0], line_coords[0][1]),
           QgsPoint(line_coords[1][0], line_coords[1][1])]
    f.setGeometry(QgsGeometry(QgsLineString(pts)))
    layer.dataProvider().addFeature(f)
    layer.setRenderer(create_section_line_style())
    layer.updateExtents()
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)
    return layer


# ---------------------------------------------------------------------------
# Load drillholes from GeoPackage (project restore)
# ---------------------------------------------------------------------------
def load_drillholes_from_gpkg(geometry_gpkg, data_gpkg, crs,
                              dip_convention: str = "standard"):
    """
    Reload DrillHole objects from a saved GeoPackage.
    This allows reopening a project without re-importing CSV files.
    """
    from qgis.core import QgsVectorLayer
    import os

    drillholes = []

    # Load collars
    collar_uri = f"{geometry_gpkg}|layername={LAYER_COLLARS}"
    collar_layer = QgsVectorLayer(collar_uri, LAYER_COLLARS, "ogr")
    if not collar_layer.isValid():
        return []

    # Load survey
    survey_uri = f"{geometry_gpkg}|layername={LAYER_SURVEY}"
    survey_layer = QgsVectorLayer(survey_uri, LAYER_SURVEY, "ogr")

    # Load litho
    litho_uri = f"{data_gpkg}|layername={LAYER_LITHO}"
    litho_layer = QgsVectorLayer(litho_uri, LAYER_LITHO, "ogr") if os.path.isfile(data_gpkg) else None

    # Load assays
    assay_uri = f"{data_gpkg}|layername={LAYER_ASSAYS}"
    assay_layer = QgsVectorLayer(assay_uri, LAYER_ASSAYS, "ogr") if os.path.isfile(data_gpkg) else None

    # Load alterations & mineralizations (v2.7.3).  Older GeoPackages simply
    # do not contain these layers : they are skipped, never invented.
    alterations_uri = f"{data_gpkg}|layername={LAYER_ALTERATIONS}"
    alterations_layer = (QgsVectorLayer(alterations_uri, LAYER_ALTERATIONS, "ogr")
                         if os.path.isfile(data_gpkg) else None)
    mineralizations_uri = f"{data_gpkg}|layername={LAYER_MINERALIZATIONS}"
    mineralizations_layer = (QgsVectorLayer(mineralizations_uri, LAYER_MINERALIZATIONS, "ogr")
                             if os.path.isfile(data_gpkg) else None)

    # Structure measurements (v2.9.258-rendu) — older GeoPackages simply do
    # not contain this layer; it is skipped, never invented.
    structure_uri = f"{data_gpkg}|layername={LAYER_STRUCTURE}"
    structure_layer = (QgsVectorLayer(structure_uri, LAYER_STRUCTURE, "ogr")
                       if os.path.isfile(data_gpkg) else None)

    from .data_model import (
        CollarRecord, SurveyRecord, IntervalRecord, LithologyComponent,
        StructureRecord, DrillHole)
    from .geometry import compute_trajectory

    # Build collars
    collars = {}
    collar_field_names = {f.name() for f in collar_layer.fields()}
    for fet in collar_layer.getFeatures():
        hid = fet["hole_id"]
        x = fet["x"]
        y = fet["y"]
        z = fet["z"]
        depth = fet["max_depth"]
        az = fet["azimuth"] if fet["azimuth"] is not None else None
        dip = fet["dip"] if fet["dip"] is not None else None
        # v2.9.289 — anciens GeoPackages sans colonne = None (rétrocompat).
        ht_raw = (fet["hole_type"] if "hole_type" in collar_field_names
                  else None)
        ht = str(ht_raw).strip() if ht_raw else None
        cr = CollarRecord(hole_id=hid, x=x, y=y, z=z, max_depth=depth,
                          azimuth=az, dip=dip, hole_type=ht)
        collars[hid] = cr

    # Load real survey stations (depth/azimuth/dip) from the stations table
    surveys = {}
    stations_uri = f"{data_gpkg}|layername={LAYER_SURVEY_STATIONS}"
    stations_layer = (QgsVectorLayer(stations_uri, LAYER_SURVEY_STATIONS, "ogr")
                      if os.path.isfile(data_gpkg) else None)
    if stations_layer and stations_layer.isValid():
        from .data_model import SurveyRecord
        for fet in stations_layer.getFeatures():
            hid = fet["hole_id"]
            surveys.setdefault(hid, []).append(SurveyRecord(
                hole_id=hid,
                depth=float(fet["depth"] or 0.0),
                azimuth=float(fet["azimuth"] or 0.0),
                dip=float(fet["dip"] if fet["dip"] is not None else -90.0),
            ))
        for hid in surveys:
            surveys[hid].sort(key=lambda s: s.depth)
    # v2.9.286 — projets pré-286 saisis « positif = bas » : conversion en
    # convention interne signée (négatif = bas) si l'import l'a déclarée.
    if str(dip_convention) == "historique":
        for recs in surveys.values():
            for rec in recs:
                rec.dip = -abs(float(rec.dip))
        for cr in collars.values():
            if cr.dip is not None:
                cr.dip = -abs(float(cr.dip))

    # Build lithology intervals, including v2.7.1 component metadata when
    # present. Legacy GeoPackages remain readable as one primary component.
    litho_by_hole = {}
    if litho_layer and litho_layer.isValid():
        field_names = {field.name() for field in litho_layer.fields()}
        grouped_lithology = {}
        for fet in litho_layer.getFeatures():
            hid = fet["hole_id"]
            fd = float(fet["from_depth"])
            td = float(fet["to_depth"])
            code = fet["lithology"] or ""
            key = (hid, round(fd, 7), round(td, 7))
            if key not in grouped_lithology:
                grouped_lithology[key] = IntervalRecord(
                    hole_id=hid, from_depth=fd, to_depth=td,
                    attributes={}, components=[])
            if "component_role" in field_names:
                role = fet["component_role"] or ""
                raw_role = fet["raw_role"] or "" if "raw_role" in field_names else role
                raw_proportion = (fet["proportion"]
                                  if "proportion" in field_names else None)
                try:
                    proportion = float(raw_proportion)
                    if not math.isfinite(proportion):
                        proportion = None
                except (TypeError, ValueError):
                    proportion = None
                unit = (fet["proportion_unit"] or "unknown"
                        if "proportion_unit" in field_names else "unknown")
                try:
                    source_line = int(fet["source_line"] or 0) if "source_line" in field_names else 0
                except (TypeError, ValueError):
                    source_line = 0
            else:
                role, raw_role = "primary", "primary"
                proportion, unit, source_line = None, "unknown", 0
            grouped_lithology[key].components.append(LithologyComponent(
                raw_code=code, role=role, raw_role=raw_role,
                proportion=proportion,
                proportion_unit=unit, source_line=source_line))
        for interval in grouped_lithology.values():
            interval.sync_primary_attribute()
            litho_by_hole.setdefault(interval.hole_id, []).append(interval)

    # Build assay intervals
    assays_by_hole = {}
    if assay_layer and assay_layer.isValid():
        # Get element column names from fields
        elem_cols = []
        for field in assay_layer.fields():
            fname = field.name()
            if fname not in ("hole_id", "from_depth", "to_depth"):
                elem_cols.append(fname)

        for fet in assay_layer.getFeatures():
            hid = fet["hole_id"]
            fd = fet["from_depth"]
            td = fet["to_depth"]
            attrs = {}
            for col in elem_cols:
                val = fet[col]
                if val is not None:
                    attrs[col] = float(val)
            iv = IntervalRecord(
                hole_id=hid, from_depth=fd, to_depth=td,
                attributes=attrs)
            assays_by_hole.setdefault(hid, []).append(iv)

    # Build alteration intervals (v2.7.3).  Rows sharing the same
    # (hole, from, to) are the components of ONE interval; ``raw_cell``
    # restores the untouched source cell in the ``alteration`` attribute.
    alterations_by_hole = {}
    if alterations_layer and alterations_layer.isValid():
        alt_fields = {field.name() for field in alterations_layer.fields()}
        grouped = {}
        for fet in alterations_layer.getFeatures():
            hid = fet["hole_id"]
            fd = float(fet["from_depth"])
            td = float(fet["to_depth"])
            key = (hid, round(fd, 7), round(td, 7))
            if key not in grouped:
                grouped[key] = IntervalRecord(
                    hole_id=hid, from_depth=fd, to_depth=td,
                    attributes={}, components=[])
            interval = grouped[key]
            code = fet["alteration"] or ""
            raw_cell = (fet["raw_cell"] or ""
                        if "raw_cell" in alt_fields else "")
            intensity = (fet["intensity"] or ""
                         if "intensity" in alt_fields else "")
            if not interval.attributes:
                interval.attributes["alteration"] = raw_cell or code
                interval.attributes["intensity"] = intensity
            try:
                source_line = int(fet["source_line"] or 0)
            except (TypeError, ValueError):
                source_line = 0
            interval.source_line = interval.source_line or source_line
            role = fet["component_role"] or "" if "component_role" in alt_fields else ""
            raw_role = fet["raw_role"] or "" if "raw_role" in alt_fields else role
            interval.components.append(LithologyComponent(
                raw_code=code, role=role, raw_role=raw_role,
                proportion_unit="unknown", source_line=source_line))
        for interval in grouped.values():
            alterations_by_hole.setdefault(
                interval.hole_id, []).append(interval)

    # Build mineralization intervals (v2.7.3) : raw style / minerals /
    # intensity, one row per interval — nothing is ever split here (AM-05).
    mineralizations_by_hole = {}
    if mineralizations_layer and mineralizations_layer.isValid():
        for fet in mineralizations_layer.getFeatures():
            hid = fet["hole_id"]
            try:
                source_line = int(fet["source_line"] or 0)
            except (TypeError, ValueError):
                source_line = 0
            iv = IntervalRecord(
                hole_id=hid,
                from_depth=float(fet["from_depth"]),
                to_depth=float(fet["to_depth"]),
                attributes={
                    "mineralization_style":
                        fet["mineralization_style"] or "",
                    "minerals": fet["minerals"] or "",
                    "intensity": fet["intensity"] or "",
                },
                source_line=source_line)
            mineralizations_by_hole.setdefault(hid, []).append(iv)

    # Build structure measurements (v2.9.258-rendu).
    structure_by_hole = {}
    if structure_layer and structure_layer.isValid():
        for fet in structure_layer.getFeatures():
            hid = fet["hole_id"]
            try:
                depth = float(fet["depth"] or 0.0)
            except (TypeError, ValueError):
                continue
            def _opt_float(value):
                if value is None:
                    return None
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None
            structure_by_hole.setdefault(hid, []).append(StructureRecord(
                hole_id=hid,
                depth=depth,
                type=str(fet["type"] or ""),
                dip=_opt_float(fet["dip"]),
                dip_direction=_opt_float(fet["dip_direction"]),
                alpha=_opt_float(fet["alpha"]),
                beta=_opt_float(fet["beta"]),
                confidence=(str(fet["confidence"] or "")
                            if fet["confidence"] is not None else None),
                comment=str(fet["comment"] or ""),
            ))
        for records in structure_by_hole.values():
            records.sort(key=lambda record: record.depth)

    # Assemble drillholes with trajectories
    for hid, collar in collars.items():
        survey = surveys.get(hid, [])
        if not survey:
            from .validation import auto_survey_for_vertical
            survey = auto_survey_for_vertical(collar)

        trajectory = compute_trajectory(collar, survey, subdivide=True, max_segment=5.0)

        dh = DrillHole(
            hole_id=hid,
            collar=collar,
            survey=survey,
            litho=litho_by_hole.get(hid, []),
            assays=assays_by_hole.get(hid, []),
            trajectory=trajectory,
            alterations=alterations_by_hole.get(hid, []),
            mineralizations=mineralizations_by_hole.get(hid, []),
            structure=structure_by_hole.get(hid, []),
        )
        drillholes.append(dh)

    return drillholes
