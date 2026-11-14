"""Structured, source-safe validation for DrillMaster imports."""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from .data_model import (
    CollarRecord, CoreImageRecord, DrillHole, GeotechRecord,
    IntervalRecord, LithologyComponent, StructureRecord, SurveyRecord,
)
from .csv_parser import (
    ParseResult, canonical_lithology_role, parse_number,
)
from .geotech import (
    DENSITY_KNOWN_UNITS, GEOTECH_DENSITY_UNIT, GEOTECH_KINDS,
    GEOTECH_RANGE, GEOTECH_UNUSUAL_DENSITY_THRESHOLD,
    geotech_kind, geotech_known_unit, geotech_rqd_over_recovery,
)
from .track_bands import SPLIT_CONTENT_FIELDS, split_delimited_codes


@dataclass
class ValidationIssue:
    """Machine-readable issue shared by import UI, editor and future views."""

    file_type: str
    severity: str  # error | warning | info
    code: str
    message: str
    row: int | None = None       # zero-based data row (header excluded)
    column: int | None = None    # zero-based raw column
    suggestion: str = ""
    locations: list[dict] = field(default_factory=list)

    def __post_init__(self):
        cleaned = []
        for location in self.locations or []:
            if isinstance(location, dict):
                cleaned.append({
                    "row": location.get("row"),
                    "column": location.get("column"),
                })
            elif isinstance(location, (tuple, list)) and location:
                cleaned.append({
                    "row": location[0],
                    "column": location[1] if len(location) > 1 else None,
                })
        if not cleaned and (self.row is not None or self.column is not None):
            cleaned.append({"row": self.row, "column": self.column})
        self.locations = cleaned
        if self.locations:
            self.row = self.locations[0].get("row")
            self.column = self.locations[0].get("column")

    def to_dict(self):
        return {
            "file_type": self.file_type,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "row": self.row,
            "column": self.column,
            "suggestion": self.suggestion,
            "locations": list(self.locations),
        }


@dataclass
class ValidationResult:
    """Validation result with legacy text lists plus structured issues."""

    file_type: str
    file_name: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    num_records: int = 0

    def add_issue(self, severity, code, message, row=None, column=None,
                  suggestion="", locations=None):
        issue = ValidationIssue(
            self.file_type, severity, code, message,
            row=row, column=column, suggestion=suggestion,
            locations=list(locations or []))
        self.issues.append(issue)
        if severity == "error" and message not in self.errors:
            self.errors.append(message)
        elif severity == "warning" and message not in self.warnings:
            self.warnings.append(message)
        return issue

    def get_issues(self, parse_result=None):
        """Return structured issues, adapting untouched legacy messages."""
        result = list(self.issues)
        known = {(issue.severity, issue.message) for issue in result}
        headers = parse_result.raw_headers if parse_result else []
        mappings = parse_result.effective_mappings if parse_result else {}
        from .csv_parser import extract_validation_locations
        for severity, messages in (("error", self.errors),
                                   ("warning", self.warnings)):
            locations = extract_validation_locations(messages, headers, mappings)
            for location in locations:
                key = (severity, location["message"])
                if key in known:
                    continue
                result.append(ValidationIssue(
                    file_type=self.file_type,
                    severity=severity,
                    code="LEGACY_ERROR" if severity == "error" else "LEGACY_WARNING",
                    message=location["message"],
                    row=location["row"],
                    column=location["column"]))
                known.add(key)
        return result

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class ImportBundle:
    """Aggregates all parsed data for a project."""

    collars: dict[str, CollarRecord] = field(default_factory=dict)
    surveys: dict[str, list[SurveyRecord]] = field(default_factory=dict)
    litho: dict[str, list[IntervalRecord]] = field(default_factory=dict)
    assays: dict[str, list[IntervalRecord]] = field(default_factory=dict)
    alterations: dict[str, list[IntervalRecord]] = field(default_factory=dict)
    mineralizations: dict[str, list[IntervalRecord]] = field(default_factory=dict)
    structure: dict[str, list[StructureRecord]] = field(default_factory=dict)
    imagery: dict[str, list[CoreImageRecord]] = field(default_factory=dict)
    geotech: dict[str, list[GeotechRecord]] = field(default_factory=dict)

    def get_collar_ids(self) -> set[str]:
        return set(self.collars)


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------
def _basename(path):
    return os.path.basename(path) if path else ""


def _column_indexes(pr: ParseResult) -> dict[str, int]:
    indexes = {}
    for index, header in enumerate(pr.raw_headers):
        canonical = pr.effective_mappings.get(header)
        if canonical and canonical not in indexes:
            indexes[canonical] = index
    return indexes


def _header_index(pr: ParseResult, header: str) -> int | None:
    if not header:
        return None
    try:
        return pr.raw_headers.index(header)
    except ValueError:
        folded = str(header).casefold()
        for index, candidate in enumerate(pr.raw_headers):
            if candidate.casefold() == folded:
                return index
    return None


def _source_line(row_index):
    return row_index + 2


def _message_prefix(result, row_index):
    return f"[{result.file_name}] Ligne {_source_line(row_index)}"


def _check_mapping_safety(pr: ParseResult, result: ValidationResult,
                          required: list[str]) -> dict[str, int]:
    indexes = _column_indexes(pr)
    reverse = {}
    for raw, canonical in pr.effective_mappings.items():
        if not canonical:
            continue
        reverse.setdefault(canonical, []).append(raw)
    # v2.7.11.6 — retour écran (mineralisation.csv : Mineral_1/2/3) : les
    # colonnes d'une organisation LARGE partagent un même canonique par
    # construction (elles seront JOINTES dans les composants ou « Minéraux »,
    # jamais écrasées) — ce n'est pas un doublon.
    # v2.7.12.1 — le correctif Levenshtein rend ces correspondances réelles
    # (Alt1/Alt2 → « alteration », Int1/Int2 → « intensité », LithoA/LithoB
    # → « lithology », PctA/PctB → « proportion »…).  Deux exemptions :
    #   (1) organisation LARGE confirmée : les colonnes DÉCLARÉES dans le
    #       profil (codes + proportions) partagent leur canonique légitimement,
    #       quel que soit le type de fichier ;
    #   (2) colonnes numérotées détectées (ALT1/ALT2/INT1/INT2, Style1/2,
    #       Min1/2/3) sur les pistes codées : même partage par construction —
    #       avant confirmation, l'organisation est précisément en cours
    #       d'arbitrage par la question ciblée (CM-01) ; après confirmation
    #       STANDARD (« une seule colonne porte le code »), la décision est
    #       rendue : la PREMIÈRE colonne est le code, les colonnes numérotées
    #       restantes ne sont pas lues comme contenu (jamais écrasées).
    # Des doublons sur des colonnes NON numérotées restent une erreur, quelle
    # que soit l'organisation confirmée.
    wide_exempt: set[str] = set()
    _prof0 = getattr(pr, "structure", None)
    _wide_headers = set()
    if (_prof0 is not None and _prof0.mode == "wide_components"
            and _prof0.confirmed):
        for _cc in _prof0.component_columns or ():
            if _cc.code_column:
                _wide_headers.add(_cc.code_column)
            if _cc.proportion_column:
                _wide_headers.add(_cc.proportion_column)
        if _wide_headers:
            wide_exempt = {
                "lithology", "lithology_primary", "lithology_secondary",
                "lithology_role", "lithology_proportion",
                "secondary_proportion",
                "alteration", "intensity",
                "mineralization_style", "minerals", "confidence",
            }
    if pr.file_type in ("alterations", "mineralizations"):
        from .import_detect import detect_wide_component_columns
        _wide_comps, _wide_ints, _wide_mins = detect_wide_component_columns(
            pr.raw_headers, pr.file_type)
        if _wide_comps:
            _wide_headers |= ({h for h, _s in _wide_comps}
                              | {h for h, _s in _wide_ints}
                              | {h for h, _s in _wide_mins})
            wide_exempt |= (
                {"alteration", "intensity"}
                if pr.file_type == "alterations"
                else {"mineralization_style", "minerals", "intensity"})
    for canonical, headers in reverse.items():
        wide_org_dup = (
            canonical in wide_exempt
            and set(headers) and set(headers) <= _wide_headers)
        if len(headers) > 1 and canonical not in {
                "lithology_primary", "lithology_secondary"
        } and not wide_org_dup:
            locations = [
                {"row": None, "column": _header_index(pr, header)}
                for header in headers]
            result.add_issue(
                "error", "DUPLICATE_MAPPING",
                f"Plusieurs colonnes sont associées au champ '{canonical}' : "
                f"{', '.join(headers)}.",
                locations=locations,
                suggestion="Conservez une seule correspondance ou définissez une structure multi-composants.")
    for canonical in required:
        if canonical not in indexes:
            result.add_issue(
                "error", "REQUIRED_MAPPING_MISSING",
                f"Champ requis '{canonical}' non associé. Vérifiez les en-têtes : "
                f"{', '.join(pr.raw_headers)}.",
                suggestion="Choisissez la colonne source correspondant à ce champ.")
    for issue in pr.row_width_issues:
        result.add_issue(
            "error", "ROW_WIDTH_MISMATCH",
            f"Ligne {issue['line']} : {issue['actual']} cellule(s) pour "
            f"{issue['expected']} en-tête(s).",
            row=max(issue["line"] - 2, 0),
            suggestion="Corrigez la ligne ; DrillMaster ne tronquera aucune valeur.")
    return indexes


def _cell(row, column):
    return row[column] if column is not None and column < len(row) else ""


def _parse_numeric(pr, result, row, row_index, column, field_label,
                   required=True):
    raw = _cell(row, column).strip()
    if not raw:
        if required:
            result.add_issue(
                "error", "EMPTY_NUMERIC_VALUE",
                f"{_message_prefix(result, row_index)}, colonne '{field_label}' : valeur vide.",
                row=row_index, column=column,
                suggestion="Saisissez une valeur numérique.")
        return None
    value = parse_number(raw, pr.decimal_sep)
    if value is None or not math.isfinite(value):
        result.add_issue(
            "error", "INVALID_NUMBER",
            f"{_message_prefix(result, row_index)}, colonne '{field_label}' : "
            f"valeur '{raw}' non numérique.",
            row=row_index, column=column,
            suggestion=(
                f"Utilisez le séparateur décimal '{pr.decimal_sep}' de ce fichier. "
                "Les conventions mélangées ne sont pas converties automatiquement."))
        return None
    return value


def _collar_ids_and_depths(collar_ids, collars=None):
    if isinstance(collar_ids, dict):
        collars = collar_ids
        collar_ids = set(collars)
    ids = set(collar_ids or [])
    depths = {}
    for hole_id, collar in (collars or {}).items():
        depth = getattr(collar, "max_depth", None)
        if isinstance(depth, (int, float)):
            depths[hole_id] = float(depth)
    return ids, depths


def _hole_similarity_warnings(raw_ids, result, id_column):
    groups = {}
    for row_index, raw in raw_ids:
        key = raw.strip().casefold()
        groups.setdefault(key, []).append((row_index, raw))
    for values in groups.values():
        distinct = {raw for _row, raw in values}
        if len(distinct) < 2:
            continue
        result.add_issue(
            "warning", "SIMILAR_HOLE_IDS",
            "Identifiants de forage très proches mais différents : "
            + ", ".join(repr(value) for value in sorted(distinct)) + ".",
            locations=[
                {"row": row, "column": id_column} for row, _raw in values],
            suggestion="Vérifiez la casse et les espaces ; aucune fusion automatique n'est appliquée.")


# ---------------------------------------------------------------------------
# Collets
# ---------------------------------------------------------------------------
def validate_collar(pr: ParseResult) -> tuple[list[CollarRecord], ValidationResult]:
    result = ValidationResult("collar", _basename(pr.file_path))
    required = ["hole_id", "collar_x", "collar_y", "collar_z", "depth"]
    indexes = _check_mapping_safety(pr, result, required)
    if result.errors:
        return [], result

    records = []
    seen = {}
    raw_ids = []
    positions = {}
    for row_index, row in enumerate(pr.rows):
        if not any(str(value).strip() for value in row):
            continue
        id_col = indexes["hole_id"]
        hole_id = _cell(row, id_col)
        raw_ids.append((row_index, hole_id))
        if not hole_id.strip():
            result.add_issue(
                "error", "EMPTY_HOLE_ID",
                f"Ligne {_source_line(row_index)} : HOLE_ID vide.",
                row=row_index, column=id_col)
            continue
        if hole_id in seen:
            first = seen[hole_id]
            result.add_issue(
                "error", "DUPLICATE_HOLE_ID",
                f"Ligne {_source_line(row_index)} : HOLE_ID '{hole_id}' en doublon.",
                locations=[
                    {"row": first, "column": id_col},
                    {"row": row_index, "column": id_col}],
                suggestion="Conservez une seule ligne ou corrigez explicitement l'identifiant.")
            continue
        seen[hole_id] = row_index

        x = _parse_numeric(pr, result, row, row_index, indexes["collar_x"], "collar_x")
        y = _parse_numeric(pr, result, row, row_index, indexes["collar_y"], "collar_y")
        z = _parse_numeric(pr, result, row, row_index, indexes["collar_z"], "collar_z")
        depth = _parse_numeric(pr, result, row, row_index, indexes["depth"], "depth")
        if None in (x, y, z, depth):
            continue
        if depth <= 0:
            result.add_issue(
                "error", "NON_POSITIVE_DEPTH",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : profondeur totale ({depth}) doit être > 0.",
                row=row_index, column=indexes["depth"])

        position = (x, y, z)
        if position in positions:
            first = positions[position]
            result.add_issue(
                "warning", "DUPLICATE_COLLAR_POSITION",
                f"Les forages '{first[1]}' et '{hole_id}' ont le même collet.",
                locations=[
                    {"row": first[0], "column": indexes["collar_x"]},
                    {"row": row_index, "column": indexes["collar_x"]}],
                suggestion="Vérifiez les coordonnées si ces forages ne partagent pas réellement le même départ.")
        else:
            positions[position] = (row_index, hole_id)

        azimuth = (_parse_numeric(
            pr, result, row, row_index, indexes.get("azimuth"), "azimuth",
            required=False) if "azimuth" in indexes else None)
        dip = (_parse_numeric(
            pr, result, row, row_index, indexes.get("dip"), "dip",
            required=False) if "dip" in indexes else None)
        # v2.9.289 — type d'ouvrage optionnel (colonne « hole_type »).
        ht_idx = indexes.get("hole_type")
        hole_type = (str(row[ht_idx]).strip()
                     if ht_idx is not None and ht_idx < len(row)
                     and str(row[ht_idx]).strip() else None)
        records.append(CollarRecord(
            hole_id=hole_id, x=x, y=y, z=z, max_depth=depth,
            azimuth=azimuth, dip=dip, hole_type=hole_type))

    _hole_similarity_warnings(raw_ids, result, indexes["hole_id"])
    result.num_records = len(records)
    return records, result


# ---------------------------------------------------------------------------
# Déviations
# ---------------------------------------------------------------------------
def validate_survey(pr: ParseResult, collar_ids: set[str], collars=None):
    result = ValidationResult("survey", _basename(pr.file_path))
    indexes = _check_mapping_safety(
        pr, result, ["hole_id", "depth", "azimuth", "dip"])
    if result.errors:
        return {}, result
    valid_ids, max_depths = _collar_ids_and_depths(collar_ids, collars)
    by_hole = {}
    source_by_hole = {}
    seen_depths = {}
    raw_ids = []

    for row_index, row in enumerate(pr.rows):
        if not any(str(value).strip() for value in row):
            continue
        id_col = indexes["hole_id"]
        hole_id = _cell(row, id_col)
        raw_ids.append((row_index, hole_id))
        if not hole_id.strip():
            result.add_issue("error", "EMPTY_HOLE_ID",
                             f"Ligne {_source_line(row_index)} : HOLE_ID vide.",
                             row=row_index, column=id_col)
            continue
        if valid_ids and hole_id not in valid_ids:
            result.add_issue(
                "error", "UNKNOWN_HOLE_ID",
                f"[{result.file_name}] Ligne {_source_line(row_index)} : HOLE_ID '{hole_id}' inexistant dans le fichier Collets.",
                row=row_index, column=id_col,
                suggestion="Corrigez l'identifiant ou ajoutez le collet correspondant.")
            continue

        depth = _parse_numeric(pr, result, row, row_index, indexes["depth"], "depth")
        azimuth = _parse_numeric(pr, result, row, row_index, indexes["azimuth"], "azimuth")
        dip = _parse_numeric(pr, result, row, row_index, indexes["dip"], "dip")
        if None in (depth, azimuth, dip):
            continue
        if depth < 0:
            result.add_issue(
                "error", "NEGATIVE_SURVEY_DEPTH",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : profondeur ({depth}) négative.",
                row=row_index, column=indexes["depth"])
        if hole_id in max_depths and depth > max_depths[hole_id] + 1e-7:
            result.add_issue(
                "error", "SURVEY_BEYOND_HOLE_DEPTH",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : station ({depth}) au-delà de la profondeur totale ({max_depths[hole_id]}).",
                row=row_index, column=indexes["depth"])
        if not 0 <= azimuth <= 360:
            result.add_issue(
                "error", "AZIMUTH_OUT_OF_RANGE",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : azimuth ({azimuth}) hors plage [0–360].",
                row=row_index, column=indexes["azimuth"])
        if not -90 <= dip <= 90:
            result.add_issue(
                "error", "DIP_OUT_OF_RANGE",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : pendage ({dip}) hors plage [-90–90].",
                row=row_index, column=indexes["dip"])

        depth_key = (hole_id, round(depth, 7))
        if depth_key in seen_depths:
            first = seen_depths[depth_key]
            result.add_issue(
                "error", "DUPLICATE_SURVEY_DEPTH",
                f"Forage '{hole_id}' : profondeur de déviation {depth} répétée.",
                locations=[
                    {"row": first, "column": indexes["depth"]},
                    {"row": row_index, "column": indexes["depth"]}])
        else:
            seen_depths[depth_key] = row_index

        by_hole.setdefault(hole_id, []).append(SurveyRecord(
            hole_id=hole_id, depth=depth, azimuth=azimuth, dip=dip))
        source_by_hole.setdefault(hole_id, []).append((row_index, depth))

    for hole_id, sources in source_by_hole.items():
        depths = [value for _row, value in sources]
        if depths != sorted(depths):
            result.add_issue(
                "warning", "UNSORTED_SURVEY",
                f"Forage '{hole_id}' : les stations de déviation ne sont pas triées par profondeur.",
                locations=[
                    {"row": row, "column": indexes["depth"]}
                    for row, _value in sources],
                suggestion="Le calcul triera une copie interne ; le CSV restera inchangé.")
        if depths and min(depths) > 1e-7:
            first_row = min(sources, key=lambda value: value[1])[0]
            result.add_issue(
                "warning", "SURVEY_DOES_NOT_START_AT_ZERO",
                f"Forage '{hole_id}' : la première station de déviation est à {min(depths)}, pas à 0.",
                row=first_row, column=indexes["depth"])
        by_hole[hole_id].sort(key=lambda station: station.depth)

    _hole_similarity_warnings(raw_ids, result, indexes["hole_id"])
    result.num_records = sum(len(records) for records in by_hole.values())
    return by_hole, result


# ---------------------------------------------------------------------------
# Structure measurements (v2.9.258 — import + validation only)
# ---------------------------------------------------------------------------
# Open list of well-known structural codes.  The list is deliberately NOT
# exhaustive: an unknown code only warns (the project convention for the
# structure domain), it never blocks the measurement.
_STRUCTURE_TYPE_WORDS = {
    # Foliation et fabrique pénétrative
    "foliation", "foliée", "folié", "schistosite", "schistosity",
    "schiste", "schist", "clivage", "cleavage", "clivage ardoisier",
    "slaty cleavage", "clivage de crénulation", "crenulation cleavage",
    "gneissosité", "gneissosity", "litage", "bedding",
    "stratification", "layering", "fabric", "linéation", "lineation",
    "linéation d'étirement", "stretching lineation",
    # Fractures, diaclases, fissures
    "fracture", "diaclase", "joint", "joint set", "famille de diaclases",
    "fissure", "fissuration", "crack", "cassure",
    # Veines et filons
    "veine", "vein", "veinule", "veinlet", "filon", "vein",
    "filonnet", "quartz vein", "veine de quartz", "veine de pegmatite",
    "pegmatite vein", "gash vein", "veine en échelon", "en echelon vein",
    "veine de calcite", "calcite vein", "veine de sulfures",
    "sulfide vein",
    # Failles et zones de cisaillement
    "faille", "fault", "faille normale", "normal fault",
    "faille inverse", "reverse fault", "faille de décrochement",
    "strike-slip fault", "chevauchement", "thrust", "thrust fault",
    "cisaillement", "shear", "zone de cisaillement", "shear zone",
    "mylonite", "mylonitic", "mylonitique", "cataclasite",
    "cataclastique", "brèche", "breccia", "brèche de faille",
    "fault breccia", "brèche tectonique", "tectonic breccia",
    "miroir de faille", "slickenside", "slickensides", "stries de faille",
    "fault striation", "gouge de faille", "fault gouge",
    # Plis et déformation souple
    "pli", "fold", "anticlinal", "anticline", "synclinal", "syncline",
    "axe de pli", "fold axis", "plissement", "folding",
    "plis en genou", "kink band", "bande de kink", "kink",
    "boudinage", "boudin", "boudiné", "boudinée",
    "schistosité de flux", "flow cleavage",
    # Contacts et discontinuités sédimentaires / magmatiques
    "contact", "contact intrusif", "intrusive contact",
    "contact sédimentaire", "sedimentary contact",
    "contact magmatique", "magmatic contact",
    "discordance", "unconformity", "surface de discordance",
    "angular unconformity", "discordance angulaire",
    "contact fautif", "fault contact",
    # Autres structures
    "stylolite", "stylolites", "stylolithe", "stylolithic",
    "nodule", "concrétion", "concretion", "géode", "geode",
    "lit", "lens", "lentille", "lentille tectonique",
    "vein de tension", "tension vein",
}


def validate_structure(pr: ParseResult, collar_ids: set[str], collars=None):
    """Validate a point-wise structure table (v2.9.258).

    Returns ``(by_hole, result)`` where ``by_hole[hole_id]`` is the list of
    ``StructureRecord`` for that hole, sorted by depth.  Import + validation
    only: no 2D/3D consumption is wired in this step.
    """
    result = ValidationResult("structure", _basename(pr.file_path))
    indexes = _check_mapping_safety(
        pr, result, ["hole_id", "depth", "type"])
    if result.errors:
        return {}, result
    valid_ids, max_depths = _collar_ids_and_depths(collar_ids, collars)
    by_hole = {}
    seen = {}
    raw_ids = []

    for row_index, row in enumerate(pr.rows):
        if not any(str(value).strip() for value in row):
            continue
        id_col = indexes["hole_id"]
        hole_id = _cell(row, id_col)
        raw_ids.append((row_index, hole_id))
        if not hole_id.strip():
            result.add_issue(
                "error", "EMPTY_HOLE_ID",
                f"Ligne {_source_line(row_index)} : HOLE_ID vide.",
                row=row_index, column=id_col)
            continue
        if valid_ids and hole_id not in valid_ids:
            result.add_issue(
                "error", "UNKNOWN_HOLE_ID",
                f"[{result.file_name}] Ligne {_source_line(row_index)} : "
                f"HOLE_ID '{hole_id}' inexistant dans le fichier Collets.",
                row=row_index, column=id_col,
                suggestion="Corrigez l'identifiant ou ajoutez le collet "
                           "correspondant.")
            continue

        depth = _parse_numeric(
            pr, result, row, row_index, indexes["depth"], "depth")
        if depth is None:
            continue
        type_text = _cell(row, indexes["type"]).strip()
        type_code = type_text
        if not type_code:
            result.add_issue(
                "warning", "EMPTY_STRUCTURE_TYPE",
                f"{_message_prefix(result, row_index)}, forage "
                f"'{hole_id}' : type de structure vide.",
                row=row_index, column=indexes["type"],
                suggestion="Le code reste ouvert ; renseignez-le pour "
                           "améliorer la lecture des mesures.")
        elif type_code.casefold() not in {
                word.casefold() for word in _STRUCTURE_TYPE_WORDS}:
            result.add_issue(
                "warning", "UNKNOWN_STRUCTURE_TYPE",
                f"{_message_prefix(result, row_index)}, forage "
                f"'{hole_id}' : type de structure '{type_code}' non "
                f"préconnu.",
                row=row_index, column=indexes["type"],
                suggestion="Le code est conservé tel quel ; la liste est "
                           "ouverte (foliation, veine, fracture, faille, "
                           "contact, litage, joint…).")

        dip = _parse_numeric(
            pr, result, row, row_index, indexes.get("dip"), "dip",
            required=False)
        dip_direction = _parse_numeric(
            pr, result, row, row_index, indexes.get("dip_direction"),
            "dip_direction", required=False)
        alpha = _parse_numeric(
            pr, result, row, row_index, indexes.get("alpha"), "alpha",
            required=False)
        beta = _parse_numeric(
            pr, result, row, row_index, indexes.get("beta"), "beta",
            required=False)
        # v2.9.258 — confidence is QUALITATIVE (BONNE/MOYENNE/FAIBLE…),
        # not a numeric field.  It is preserved verbatim, never parsed.
        confidence = (
            _cell(row, indexes.get("confidence")).strip() or None
            if indexes.get("confidence") is not None else None)

        if dip is not None and not 0 <= dip <= 90:
            result.add_issue(
                "error", "STRUCTURE_DIP_OUT_OF_RANGE",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"pendage ({dip}) hors plage [0–90].",
                row=row_index, column=indexes["dip"])
        if (dip_direction is not None
                and not 0 <= dip_direction <= 360):
            result.add_issue(
                "error", "STRUCTURE_DIP_DIRECTION_OUT_OF_RANGE",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"direction du pendage ({dip_direction}) hors plage "
                f"[0–360].",
                row=row_index, column=indexes["dip_direction"])

        has_dip_pair = dip is not None and dip_direction is not None
        has_alpha_beta_pair = alpha is not None and beta is not None
        if has_dip_pair or has_alpha_beta_pair:
            pass
        elif dip is not None or dip_direction is not None:
            result.add_issue(
                "warning", "INCOMPLETE_DIP_PAIR",
                f"{_message_prefix(result, row_index)}, forage "
                f"'{hole_id}' : paire pendage / direction du pendage "
                f"incomplète.",
                row=row_index,
                column=indexes.get("dip") if dip is None
                else indexes.get("dip_direction"),
                suggestion="Renseignez les deux valeurs ou utilisez la "
                           "paire alpha / bêta.")
        elif alpha is not None or beta is not None:
            result.add_issue(
                "warning", "INCOMPLETE_ALPHA_BETA_PAIR",
                f"{_message_prefix(result, row_index)}, forage "
                f"'{hole_id}' : paire alpha / bêta incomplète.",
                row=row_index,
                column=indexes.get("alpha") if beta is None
                else indexes.get("beta"),
                suggestion="Renseignez les deux valeurs ou utilisez la "
                           "paire pendage / direction du pendage.")
        else:
            # v2.9.260 patch — non-orientable structures (nodule,
            # concrétion, géode, lentille, boudinage, stylolite) normally
            # carry no dip/alpha pair: do not penalise them for the
            # orientation they are not expected to describe.
            from .structure_classify import orientation_expected
            if orientation_expected(type_code):
                result.add_issue(
                    "warning", "NO_STRUCTURE_ORIENTATION",
                    f"{_message_prefix(result, row_index)}, forage "
                    f"'{hole_id}' : aucune orientation de structure "
                    f"(pendage / direction ou alpha / bêta).",
                    row=row_index,
                    column=indexes["type"] if indexes["type"] is not None
                    else indexes["depth"],
                    suggestion="Ajoutez une paire d'orientation ; la "
                               "mesure reste importée avec un avertissement.")

        if depth < 0:
            result.add_issue(
                "error", "NEGATIVE_STRUCTURE_DEPTH",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"profondeur ({depth}) négative.",
                row=row_index, column=indexes["depth"])
        if hole_id in max_depths and depth > max_depths[hole_id] + 1e-7:
            result.add_issue(
                "error", "STRUCTURE_BEYOND_HOLE_DEPTH",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"mesure ({depth}) au-delà de la profondeur totale "
                f"({max_depths[hole_id]}).",
                row=row_index, column=indexes["depth"])

        comment = _cell(row, indexes["comment"]).strip() \
            if indexes.get("comment") is not None else ""
        duplicate_key = (
            hole_id, round(depth, 7), type_code,
            round(dip, 7) if dip is not None else None,
            round(dip_direction, 7) if dip_direction is not None else None,
            round(alpha, 7) if alpha is not None else None,
            round(beta, 7) if beta is not None else None)
        if duplicate_key in seen:
            first = seen[duplicate_key]
            result.add_issue(
                "error", "DUPLICATE_STRUCTURE",
                f"Forage '{hole_id}' : mesure de structure dupliquée à "
                f"{depth} (type '{type_code}').",
                locations=[
                    {"row": first, "column": indexes["type"]},
                    {"row": row_index, "column": indexes["type"]}],
                suggestion="Conservez une seule ligne par mesure ; aucune "
                           "ligne n'est supprimée automatiquement.")
        else:
            seen[duplicate_key] = row_index

        by_hole.setdefault(hole_id, []).append(StructureRecord(
            hole_id=hole_id, depth=depth, type=type_code,
            dip=dip, dip_direction=dip_direction, alpha=alpha, beta=beta,
            confidence=confidence, comment=comment,
            source_line=_source_line(row_index)))

    _hole_similarity_warnings(raw_ids, result, indexes["hole_id"])
    for records in by_hole.values():
        records.sort(key=lambda record: record.depth)
    result.num_records = sum(len(records) for records in by_hole.values())
    return by_hole, result


# ---------------------------------------------------------------------------
# Imagerie de trou (v2.9.262)
# ---------------------------------------------------------------------------
_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp",
}


def _is_image_file(path: str) -> bool:
    return os.path.splitext(str(path or "").strip())[1].casefold() in \
        _IMAGE_EXTENSIONS


def validate_imagery(pr: ParseResult, collar_ids: set[str], collars=None):
    """Import chemin de photo/scan par intervalle le long d'un trou.

    Retourne ``(by_hole, result)``.  Une ligne = un intervalle d'image
    (une boîte à carottes d'un mètre, ou une vue de 0–15 m).  Aucune
    découpe ni déduction : les bornes sont celles du fichier ; sans
    ``from``/``to`` la ligne est rejetée (une seule image mais plusieurs
    boîtes → plusieurs lignes).
    """
    result = ValidationResult("imagery", _basename(pr.file_path))
    indexes = _check_mapping_safety(
        pr, result, ["hole_id", "from", "to", "image_path"])
    if result.errors:
        return {}, result
    valid_ids, max_depths = _collar_ids_and_depths(collar_ids, collars)
    by_hole = {}
    seen = {}
    raw_ids = []

    for row_index, row in enumerate(pr.rows):
        if not any(str(value).strip() for value in row):
            continue
        id_col = indexes["hole_id"]
        hole_id = _cell(row, id_col)
        raw_ids.append((row_index, hole_id))
        if not hole_id.strip():
            result.add_issue(
                "error", "EMPTY_HOLE_ID",
                f"Ligne {_source_line(row_index)} : HOLE_ID vide.",
                row=row_index, column=id_col)
            continue
        if valid_ids and hole_id not in valid_ids:
            result.add_issue(
                "error", "UNKNOWN_HOLE_ID",
                f"[{result.file_name}] Ligne {_source_line(row_index)} : "
                f"HOLE_ID '{hole_id}' inexistant dans le fichier Collets.",
                row=row_index, column=id_col,
                suggestion="Corrigez l'identifiant ou ajoutez le collet "
                           "correspondant.")
            continue

        from_m = _parse_numeric(
            pr, result, row, row_index, indexes["from"], "from")
        to_m = _parse_numeric(
            pr, result, row, row_index, indexes["to"], "to")
        if from_m is None or to_m is None:
            continue
        image_path = _cell(row, indexes["image_path"]).strip()
        path_col = indexes["image_path"]
        if not image_path:
            result.add_issue(
                "error", "EMPTY_IMAGE_PATH",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"chemin d'image vide.",
                row=row_index, column=path_col,
                suggestion="Renseignez une colonne chemin ou corrigez la "
                           "ligne (une ligne est conservée seulement si "
                           "elle a un chemin valide).")
            continue
        if not _is_image_file(image_path):
            result.add_issue(
                "warning", "IMAGE_PATH_WITHOUT_IMAGE_EXTENSION",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"'{image_path}' ne semble pas être une image.",
                row=row_index, column=path_col,
                suggestion="Ligne conservée ; vérifiez le format (jpg/png/"
                           "tif/bmp).")
        if from_m > to_m:
            result.add_issue(
                "error", "IMAGE_FROM_AFTER_TO",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"FROM ({from_m:g}) > TO ({to_m:g}).",
                row=row_index, column=indexes["to"],
                suggestion="Inversez les bornes ou corrigez la ligne.")
            continue
        if hole_id in max_depths and to_m > max_depths[hole_id] + 1e-7:
            result.add_issue(
                "error", "IMAGE_BEYOND_HOLE_DEPTH",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"l'image dépasse la profondeur totale "
                f"({max_depths[hole_id]:g}).",
                row=row_index, column=indexes["to"])
            continue
        material = (
            _cell(row, indexes["material"]).strip()
            if indexes.get("material") is not None else None)
        orientation = (
            _cell(row, indexes["orientation"]).strip()
            if indexes.get("orientation") is not None else None)
        comment = (
            _cell(row, indexes["comment"]).strip()
            if indexes.get("comment") is not None else "")

        duplicate_key = (
            hole_id, round(from_m, 7), round(to_m, 7), image_path)
        if duplicate_key in seen:
            result.add_issue(
                "warning", "DUPLICATE_IMAGE",
                f"Forage '{hole_id}' : image dupliquée "
                f"[{from_m:g}–{to_m:g}] ({image_path}).",
                locations=[
                    {"row": seen[duplicate_key], "column": path_col},
                    {"row": row_index, "column": path_col}],
                suggestion="Une seule ligne conservée.")
            continue
        seen[duplicate_key] = row_index

        by_hole.setdefault(hole_id, []).append(CoreImageRecord(
            hole_id=hole_id, from_m=from_m, to_m=to_m,
            image_path=image_path, material=material,
            orientation=orientation, comment=comment,
            source_line=_source_line(row_index)))

    _hole_similarity_warnings(raw_ids, result, indexes["hole_id"])
    for records in by_hole.values():
        records.sort(key=lambda record: (record.from_m, record.to_m))
    result.num_records = sum(len(records) for records in by_hole.values())
    return by_hole, result


# ---------------------------------------------------------------------------
# Géotechnique groupée : RQD, récupération, densité (v2.9.264)
# ---------------------------------------------------------------------------
def validate_geotech(pr: ParseResult, file_type: str,
                     collar_ids: set[str], collars=None):
    """Import des trois indicateurs géotechniques.

    ``file_type`` ∈ ``rqd`` / ``recovery`` / ``density``.  RQD et
    récupération sont des intervalles (``from``/``to``), la densité est
    ponctuelle (``depth``) mais accepte ``from``/``to`` si ``depth`` est
    absent.  Valeur hors plage, profondeur hors trou et doublons exacts
    sont bloquants ; unités inconnues et densités inhabituelles restent
    des avertissements (données conservées).  Retourne ``(by_hole, result)``.
    """
    result = ValidationResult(file_type, _basename(pr.file_path))
    kind = geotech_kind(file_type)
    required = ["hole_id", "value"]
    if kind in ("rqd", "recovery"):
        required += ["from", "to"]
    # densité : depth OU from/to — la présence est vérifiée ligne à ligne.
    indexes = _check_mapping_safety(pr, result, required)
    if result.errors:
        return {}, result
    valid_ids, max_depths = _collar_ids_and_depths(collar_ids, collars)
    by_hole = {}
    seen = {}
    raw_ids = []

    for row_index, row in enumerate(pr.rows):
        if not any(str(value).strip() for value in row):
            continue
        id_col = indexes["hole_id"]
        hole_id = _cell(row, id_col)
        raw_ids.append((row_index, hole_id))
        if not hole_id.strip():
            result.add_issue(
                "error", "EMPTY_HOLE_ID",
                f"Ligne {_source_line(row_index)} : HOLE_ID vide.",
                row=row_index, column=id_col)
            continue
        if valid_ids and hole_id not in valid_ids:
            result.add_issue(
                "error", "UNKNOWN_HOLE_ID",
                f"[{result.file_name}] Ligne {_source_line(row_index)} : "
                f"HOLE_ID '{hole_id}' inexistant dans le fichier Collets.",
                row=row_index, column=id_col,
                suggestion="Corrigez l'identifiant ou ajoutez le collet "
                           "correspondant.")
            continue

        from_m = to_m = depth = None
        if kind == "density":
            # v2.9.264 (revue) — règle XOR ligne à ligne : chaque ligne de
            # densité est EITHER point (depth), EITHER intervalle
            # (from/to).  Les cellules vides du mode non utilisé ne sont
            # JAMAIS marquées individuellement ; si aucun mode n'est
            # renseigné, on porte une seule erreur générique.
            depth_index = indexes.get("depth")
            from_index = indexes.get("from")
            to_index = indexes.get("to")
            depth_raw = _cell(row, depth_index).strip() if depth_index is not None else ""
            from_raw = _cell(row, from_index).strip() if from_index is not None else ""
            to_raw = _cell(row, to_index).strip() if to_index is not None else ""
            using_point = bool(depth_raw)
            using_interval = (not using_point) and bool(from_raw or to_raw)
            if not using_point and not using_interval:
                result.add_issue(
                    "error", "GEOTECH_MISSING_DEPTH_OR_INTERVAL",
                    f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                    f"profondeur (depth) ou bornes FROM/TO manquantes.",
                    row=row_index, column=id_col)
                continue
            if using_point:
                depth = _parse_numeric(
                    pr, result, row, row_index, depth_index, "depth")
                if depth is None:
                    continue
                # depth prioritaire : les bornes éventuelles restent vides
                # de marquage, mais le mélange est signalé.
                if from_raw or to_raw:
                    result.add_issue(
                        "warning", "GEOTECH_MIXED_DEPTH_INTERVAL",
                        f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                        f"profondeur (depth={depth:g}) et bornes "
                        f"({from_raw or '?'}–{to_raw or '?'}) toutes deux "
                        f"présentes ; le mode ponctuel est conservé.",
                        row=row_index, column=depth_index)
            else:
                from_m = _parse_numeric(
                    pr, result, row, row_index, from_index, "from")
                to_m = _parse_numeric(
                    pr, result, row, row_index, to_index, "to")
                if from_m is None or to_m is None:
                    continue
                if from_m > to_m:
                    result.add_issue(
                        "error", "GEOTECH_FROM_GT_TO",
                        f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                        f"FROM ({from_m:g}) > TO ({to_m:g}).",
                        row=row_index, column=to_index,
                        suggestion="Inversez les bornes ou corrigez la ligne.")
                    continue
        else:
            # RQD / récupération : toujours des intervalles.
            from_m = _parse_numeric(
                pr, result, row, row_index, indexes["from"], "from")
            to_m = _parse_numeric(
                pr, result, row, row_index, indexes["to"], "to")
            if from_m is None or to_m is None:
                continue
            if from_m > to_m:
                result.add_issue(
                    "error", "GEOTECH_FROM_GT_TO",
                    f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                    f"FROM ({from_m:g}) > TO ({to_m:g}).",
                    row=row_index, column=indexes["to"],
                    suggestion="Inversez les bornes ou corrigez la ligne.")
                continue

        value = _parse_numeric(
            pr, result, row, row_index, indexes["value"], "value")
        if value is None:
            continue
        lo, hi = GEOTECH_RANGE.get(kind, (0.0, 0.0))
        if kind in GEOTECH_RANGE and not (lo <= value <= hi):
            result.add_issue(
                "error", "GEOTECH_VALUE_OUT_OF_RANGE",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"valeur {value:g} hors plage {lo:g}–{hi:g} %.",
                row=row_index, column=indexes["value"])
            continue
        if kind == "density" and value <= 0.0:
            result.add_issue(
                "error", "GEOTECH_VALUE_OUT_OF_RANGE",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"densité {value:g} ≤ 0 (physiquement impossible).",
                row=row_index, column=indexes["value"])
            continue
        # v2.9.264 — densité élevée : avertissement SEULEMENT (jamais
        # bloquant) — des minéraux denses peuvent dépasser 5 g/cm³.
        if (kind == "density"
                and value > GEOTECH_UNUSUAL_DENSITY_THRESHOLD):
            result.add_issue(
                "warning", "GEOTECH_UNUSUAL_DENSITY",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"densité {value:g} > "
                f"{GEOTECH_UNUSUAL_DENSITY_THRESHOLD:g} g/cm³ — "
                f"vérifiez l'unité (mesure non bloquée).",
                row=row_index, column=indexes["value"])
        unit = ""
        if indexes.get("unit") is not None:
            unit = _cell(row, indexes["unit"]).strip()
        if kind == "density":
            if unit and not geotech_known_unit(unit, kind):
                result.add_issue(
                    "warning", "GEOTECH_UNKNOWN_UNIT",
                    f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                    f"unité '{unit}' non reconnue — affichée telle quelle.",
                    row=row_index, column=indexes.get("unit", id_col))
            # unité reconnue conservée telle quelle (jamais réécrite) ;
            # sans unité, on pose la valeur par défaut de la densité.
            if not unit:
                unit = GEOTECH_DENSITY_UNIT

        if kind != "density":
            depth = None
        effective_from = from_m if depth is None else None
        effective_to = to_m if depth is None else None
        if kind == "density" and depth is None and (
                from_m is None or to_m is None):
            result.add_issue(
                "error", "GEOTECH_MISSING_DEPTH_OR_INTERVAL",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"profondeur (depth) ou bornes FROM/TO manquantes.",
                row=row_index, column=id_col)
            continue
        if kind != "density" and (from_m is None or to_m is None):
            result.add_issue(
                "error", "GEOTECH_MISSING_INTERVAL",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"bornes FROM/TO manquantes pour {kind}.",
                row=row_index, column=id_col)
            continue

        anchor = (depth if depth is not None else to_m)
        if hole_id in max_depths and anchor is not None:
            if float(anchor) > max_depths[hole_id] + 1e-7:
                result.add_issue(
                    "error", "GEOTECH_DEPTH_OUTSIDE_HOLE",
                    f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                    f"profondeur ({anchor:g}) au-delà de la profondeur "
                    f"totale ({max_depths[hole_id]:g}).",
                    row=row_index,
                    column=indexes.get("depth", indexes["to"]))
                continue

        comment = (
            _cell(row, indexes["comment"]).strip()
            if indexes.get("comment") is not None else "")
        duplicate_key = (hole_id, kind, round(from_m or -1, 7),
                         round(to_m or -1, 7), round(depth or -1, 7))
        if duplicate_key in seen:
            result.add_issue(
                "error", "GEOTECH_DUPLICATE",
                f"Ligne {_source_line(row_index)}, forage '{hole_id}' : "
                f"{kind} dupliqué.", locations=[
                    {"row": seen[duplicate_key], "column": id_col},
                    {"row": row_index, "column": id_col}],
                suggestion="Supprimez la ligne en double.")
            continue
        seen[duplicate_key] = row_index
        by_hole.setdefault(hole_id, []).append(GeotechRecord(
            hole_id=hole_id, kind=kind,
            from_m=effective_from, to_m=effective_to,
            depth=depth, value=value, unit=unit,
            comment=comment, source_line=_source_line(row_index)))

    _hole_similarity_warnings(raw_ids, result, indexes["hole_id"])
    key = (lambda rec: (
        rec.depth if rec.depth is not None else rec.from_m or 0.0,
        rec.from_m or 0.0, rec.to_m or 0.0))
    for records in by_hole.values():
        records.sort(key=key)
    result.num_records = sum(len(records) for records in by_hole.values())
    return by_hole, result


def validate_geotech_cross(geotech_by_hole) -> ValidationResult:
    """Contrôles croisés géotechniques (RQD vs récupération de carotte).

    Une seule vue porte les deux tables à la fois : le bundle.  Le RQD ne
    compte que de la carotte réellement remontée, donc RQD ≤ récupération
    — un écart dans l'autre sens est une erreur de saisie, signalée en
    **avertissement** (jamais bloquant, comme toute la géotechnique).
    """
    result = ValidationResult("rqd", "")
    flat = [
        record for records in (geotech_by_hole or {}).values()
        for record in (records or [])
    ]
    rqd = [
        record for record in flat
        if geotech_kind(getattr(record, "kind", "")) == "rqd"]
    recovery = [
        record for record in flat
        if geotech_kind(getattr(record, "kind", "")) == "recovery"]
    for item in geotech_rqd_over_recovery(rqd, recovery):
        result.add_issue(
            "warning", "GEOTECH_RQD_GT_RECOVERY",
            f"Forage '{item['hole_id']}', "
            f"{item['from_m']:g}–{item['to_m']:g} m : RQD "
            f"{item['rqd']:g} % > récupération {item['recovery']:g} % — "
            f"physiquement impossible, vérifiez les deux tables.",
            suggestion="Le RQD ne compte que la carotte récupérée.")
    result.num_records = len(rqd)
    return result


# ---------------------------------------------------------------------------
# Lithologie multi-composants
# ---------------------------------------------------------------------------
def _parse_proportion(pr, result, row, row_index, column, unit):
    if column is None:
        return None, ""
    raw = _cell(row, column).strip()
    if not raw:
        return None, ""
    numeric_text = raw[:-1].strip() if raw.endswith("%") else raw
    value = parse_number(numeric_text, pr.decimal_sep)
    if value is None:
        result.add_issue(
            "error", "INVALID_PROPORTION",
            f"{_message_prefix(result, row_index)} : proportion '{raw}' non numérique.",
            row=row_index, column=column)
        return None, raw
    if unit == "unknown":
        result.add_issue(
            "warning", "UNKNOWN_PROPORTION_UNIT",
            f"{_message_prefix(result, row_index)} : unité de proportion inconnue pour '{raw}'.",
            row=row_index, column=column,
            suggestion="Indiquez si la colonne utilise 0–100 ou 0–1 ; aucune conversion n'est appliquée.")
        return value, raw
    maximum = 1.0 if unit == "fraction" else 100.0
    if value < 0 or value > maximum:
        result.add_issue(
            "error", "PROPORTION_OUT_OF_RANGE",
            f"{_message_prefix(result, row_index)} : proportion {raw} hors plage "
            f"[0–{maximum:g}].",
            row=row_index, column=column)
    return value, raw


def _component(pr, result, row, row_index, code_column, role="",
               role_column=None, proportion_column=None,
               proportion_unit="unknown"):
    code_index = _header_index(pr, code_column)
    if code_index is None:
        return None
    raw_code = _cell(row, code_index).strip()
    if not raw_code:
        return None
    raw_role = _cell(row, role_column).strip() if role_column is not None else role
    canonical_role = canonical_lithology_role(raw_role) or canonical_lithology_role(role)
    proportion, raw_proportion = _parse_proportion(
        pr, result, row, row_index, proportion_column, proportion_unit)
    if raw_role and not canonical_role:
        result.add_issue(
            "warning", "UNKNOWN_COMPONENT_ROLE",
            f"{_message_prefix(result, row_index)} : rôle lithologique '{raw_role}' non reconnu et conservé tel quel.",
            row=row_index, column=role_column,
            suggestion="Associez explicitement ce rôle s'il doit autoriser un recouvrement.")
    return LithologyComponent(
        raw_code=raw_code,
        role=canonical_role,
        raw_role=raw_role,
        proportion=proportion,
        raw_proportion=raw_proportion,
        proportion_unit=proportion_unit,
        source_line=_source_line(row_index),
        source_column=code_index,
        source_header=code_column)


def validate_lithology(pr: ParseResult, collar_ids, collars=None):
    result = ValidationResult("litho", _basename(pr.file_path))
    indexes = _check_mapping_safety(pr, result, ["hole_id", "from", "to"])
    valid_ids, max_depths = _collar_ids_and_depths(collar_ids, collars)
    profile = pr.structure
    if profile.mode == "standard" and not profile.code_column:
        profile.code_column = next((
            raw for raw, canonical in pr.effective_mappings.items()
            if canonical == "lithology"), "")
    # v2.7.12.3 — CM-01 appliqué à la lithologie : le large DÉTECTÉ au
    # parsing (colonnes de rôles litho1/litho2 → wide_components non
    # confirmé) n'est plus LU sans réponse explicite — même régime
    # d'état que les pistes codées (v2.7.12.1). Avant, ce profil passait
    # la validation en silence : deux régimes pour la même logique, la
    # revue d'architecture du 22/08/2026 a fusionné les deux.
    if (profile.mode == "wide_components"
            and profile.component_columns and not profile.confirmed):
        from .organisation import (
            organisation_question, unconfirmed_wide_error_code)
        _q_litho = organisation_question(
            "litho", profile, pr.raw_headers, rows=pr.rows)
        result.add_issue(
            "error", unconfirmed_wide_error_code("litho"),
            "Organisation large détectée : "
            + ", ".join(_q_litho.evidence)
            + ".",
            suggestion=("Confirmez l'organisation dans « Options "
                        "avancées… » : lire chaque colonne comme une "
                        "lithologie, ou une seule colonne porte la "
                        "lithologie (CM-01)."))
        return {}, result
    if profile.mode in ("standard", "delimited_components") and not profile.code_column:
        result.add_issue(
            "error", "LITHOLOGY_COLUMN_MISSING",
            "Aucune colonne de lithologie n'est définie pour cette structure.",
            suggestion="Associez une colonne Lithologie ou modifiez la structure du fichier.")
    if profile.mode == "long_components":
        # v2.7.11.0 — le format long est RETIRÉ du plugin (directive écran
        # du 20/08/2026 : « une règle, un format large »). Un ancien profil
        # sauvegardé tombe ici : on refuse par écrit, jamais en silence.
        result.add_issue(
            "error", "LONG_FORMAT_RETIRED",
            "Format long retiré : les lignes répétées par intervalle ne "
            "sont plus lises (règle du projet du 20/08/2026).",
            suggestion="Un code par colonne (format large) ou une cellule délimitée « / ».")
        return {}, result
    if profile.mode == "wide_components" and not profile.component_columns:
        result.add_issue(
            "error", "WIDE_COMPONENTS_MISSING",
            "Le format large ne contient aucun groupe de composant.")
    if profile.mode == "wide_components":
        component_headers = [
            component.code_column for component in profile.component_columns]
        if len(component_headers) != len(set(component_headers)):
            result.add_issue(
                "error", "DUPLICATE_COMPONENT_COLUMN",
                "Une même colonne est utilisée par plusieurs composants lithologiques.")
        # v2.7.11.1 — CM-03 : plafond géologique/lisibilité (1 primaire +
        # 3 secondaires, veines et accessoires compris).  Bloquant et
        # nommant — aucune troncation silencieuse.
        from .component_caps import MAX_LITHOLOGY_COMPONENTS, cap_excess
        excess = cap_excess(component_headers, MAX_LITHOLOGY_COMPONENTS)
        if excess:
            result.add_issue(
                "error", "TOO_MANY_COMPONENTS",
                f"Organisation des lithologies : {len(component_headers)} "
                f"colonnes de composant — maximum {MAX_LITHOLOGY_COMPONENTS} "
                f"(1 primaire + 3 secondaires/veines, arbitrage CM-03). "
                f"Colonnes en trop : {', '.join(excess)}.",
                suggestion=(
                    "Allégez le fichier ou le profil ; aucune colonne "
                    "n'est lue à moitié."))
    if result.errors:
        return {}, result

    row_records = []
    id_col, from_col, to_col = (
        indexes["hole_id"], indexes["from"], indexes["to"])
    for row_index, row in enumerate(pr.rows):
        if not any(str(value).strip() for value in row):
            continue
        hole_id = _cell(row, id_col)
        if not hole_id.strip():
            result.add_issue("error", "EMPTY_HOLE_ID",
                             f"Ligne {_source_line(row_index)} : HOLE_ID vide.",
                             row=row_index, column=id_col)
            continue
        if valid_ids and hole_id not in valid_ids:
            result.add_issue(
                "error", "UNKNOWN_HOLE_ID",
                f"[{result.file_name}] Ligne {_source_line(row_index)} : HOLE_ID '{hole_id}' inexistant dans le fichier Collets.",
                row=row_index, column=id_col)
            continue
        start = _parse_numeric(pr, result, row, row_index, from_col, "from")
        end = _parse_numeric(pr, result, row, row_index, to_col, "to")
        if start is None or end is None:
            continue
        if start < 0:
            result.add_issue(
                "error", "NEGATIVE_FROM",
                f"{_message_prefix(result, row_index)}, forage '{hole_id}' : FROM ({start}) négatif.",
                row=row_index, column=from_col)
        if start >= end:
            result.add_issue(
                "error", "FROM_GE_TO",
                f"{_message_prefix(result, row_index)}, forage '{hole_id}' : FROM ({start}) >= TO ({end}).",
                locations=[
                    {"row": row_index, "column": from_col},
                    {"row": row_index, "column": to_col}],
                suggestion="Vérifiez les deux limites ; aucune valeur ne sera corrigée automatiquement.")
        if hole_id in max_depths and end > max_depths[hole_id] + 1e-7:
            result.add_issue(
                "error", "INTERVAL_BEYOND_HOLE_DEPTH",
                f"{_message_prefix(result, row_index)}, forage '{hole_id}' : TO ({end}) dépasse la profondeur totale ({max_depths[hole_id]}).",
                row=row_index, column=to_col)

        components = []
        if profile.mode == "standard":
            component = _component(
                pr, result, row, row_index, profile.code_column,
                role="primary", proportion_unit=profile.proportion_unit)
            if component:
                components.append(component)
        elif profile.mode == "wide_components":
            for definition in profile.component_columns:
                component = _component(
                    pr, result, row, row_index, definition.code_column,
                    role=definition.role,
                    proportion_column=_header_index(
                        pr, definition.proportion_column),
                    proportion_unit=profile.proportion_unit)
                if component:
                    components.append(component)
        elif profile.mode == "delimited_components":
            code_index = _header_index(pr, profile.code_column)
            raw = _cell(row, code_index).strip()
            if (profile.confirmed and profile.delimiter
                    and profile.delimiter in raw):
                values = [value.strip() for value in raw.split(profile.delimiter)]
                if any(not value for value in values):
                    result.add_issue(
                        "error", "EMPTY_DELIMITED_COMPONENT",
                        f"{_message_prefix(result, row_index)} : composant vide dans '{raw}'.",
                        row=row_index, column=code_index)
                non_empty = [value for value in values if value]
                from .component_caps import (
                    MAX_LITHOLOGY_COMPONENTS, cap_excess)
                excess_values = cap_excess(non_empty, MAX_LITHOLOGY_COMPONENTS)
                if excess_values:
                    result.add_issue(
                        "error", "TOO_MANY_COMPONENTS",
                        f"{_message_prefix(result, row_index)} : "
                        f"{len(non_empty)} lithologies dans '{raw}' — "
                        f"maximum {MAX_LITHOLOGY_COMPONENTS} "
                        f"(arbitrage CM-03). "
                        f"Codes en trop : {', '.join(excess_values)}.",
                        row=row_index,
                        suggestion=(
                            "Allégez la cellule ; aucun code n'est "
                            "tronqué silencieusement."))
                for index, value in enumerate(value for value in values if value):
                    role = ""
                    if profile.first_component_role == "primary":
                        role = "primary" if index == 0 else "secondary"
                    components.append(LithologyComponent(
                        raw_code=value, role=role, raw_role=role,
                        proportion_unit="unknown",
                        source_line=_source_line(row_index),
                        source_column=code_index,
                        source_header=profile.code_column))
            elif raw:
                components.append(LithologyComponent(
                    raw_code=raw, role="primary", raw_role="primary",
                    proportion_unit="unknown",
                    source_line=_source_line(row_index),
                    source_column=code_index,
                    source_header=profile.code_column))
                if profile.delimiter and profile.delimiter in raw:
                    result.add_issue(
                        "info", "COMPOSITE_VALUE_PRESERVED",
                        f"{_message_prefix(result, row_index)} : valeur composite '{raw}' conservée sans séparation.",
                        row=row_index, column=code_index)

        if not components:
            result.add_issue(
                "error", "EMPTY_LITHOLOGY",
                f"{_message_prefix(result, row_index)} : aucune lithologie renseignée.",
                row=row_index,
                suggestion="Renseignez un composant ou corrigez le profil de structure.")
        record = IntervalRecord(
            hole_id=hole_id, from_depth=start, to_depth=end,
            attributes={}, source_line=_source_line(row_index),
            components=components)
        record.sync_primary_attribute()
        row_records.append((row_index, record))

    # v2.7.11.0 — plus de lecture de lignes répétées (format long retiré,
    # règle du projet du 20/08/2026) : une ligne porte son intervalle ; un
    # même support répété est un doublon refusé (comportement historique).
    grouped = {}
    source_rows = {}
    for row_index, record in row_records:
        key = (record.hole_id, round(record.from_depth, 7),
               round(record.to_depth, 7))
        if key in grouped:
            first_row = source_rows[key][0]
            result.add_issue(
                "error", "DUPLICATE_INTERVAL",
                f"Forage '{record.hole_id}' : intervalle dupliqué "
                f"[{record.from_depth}–{record.to_depth}].",
                locations=[
                    {"row": first_row, "column": from_col},
                    {"row": row_index, "column": from_col}],
                suggestion="Une ligne représente déjà l'intervalle complet.")
        else:
            grouped[key] = record
            source_rows[key] = [row_index]

    for key, record in grouped.items():
        # v2.7.11.1 — CM-03 : aucun intervalle ne dépasse le plafond,
        # quelle que soit la voie de lecture (large, délimitée, standard).
        from .component_caps import MAX_LITHOLOGY_COMPONENTS, cap_excess
        if len(record.components) > MAX_LITHOLOGY_COMPONENTS:
            excess_codes = cap_excess(
                [c.raw_code for c in record.components],
                MAX_LITHOLOGY_COMPONENTS)
            result.add_issue(
                "error", "TOO_MANY_COMPONENTS",
                f"Forage '{record.hole_id}' "
                f"[{record.from_depth:g}–{record.to_depth:g}] : "
                f"{len(record.components)} composants — maximum "
                f"{MAX_LITHOLOGY_COMPONENTS} (arbitrage CM-03). "
                f"En trop : {', '.join(excess_codes)}.",
                suggestion=("Réduisez le nombre de composants ; aucun "
                            "composant n'est tronqué silencieusement."))
        seen_components = {}
        primary = []
        total_percent = 0.0
        all_proportions = bool(record.components)
        for component in record.components:
            component_key = (component.raw_code, component.role, component.raw_role)
            row_index = max(component.source_line - 2, 0)
            if component_key in seen_components:
                first = seen_components[component_key]
                result.add_issue(
                    "error", "DUPLICATE_COMPONENT",
                    f"Forage '{record.hole_id}' [{record.from_depth}–{record.to_depth}] : composant '{component.raw_code}' répété.",
                    locations=[
                        {"row": first.source_line - 2,
                         "column": first.source_column},
                        {"row": row_index,
                         "column": component.source_column}])
            else:
                seen_components[component_key] = component
            if component.role == "primary":
                primary.append(component)
            if (component.proportion is None
                    or component.proportion_unit == "unknown"):
                all_proportions = False
            else:
                converted = (component.proportion * 100.0
                             if component.proportion_unit == "fraction"
                             else component.proportion)
                total_percent += converted
        if len(primary) > 1:
            result.add_issue(
                "error", "MULTIPLE_PRIMARY_COMPONENTS",
                f"Forage '{record.hole_id}' [{record.from_depth}–{record.to_depth}] : plusieurs composants principaux.",
                locations=[
                    {"row": component.source_line - 2,
                     "column": component.source_column}
                    for component in primary],
                suggestion="Conservez un seul composant principal ou corrigez les rôles.")
        if total_percent > 100.0 + 1e-7:
            result.add_issue(
                "error", "PROPORTION_SUM_OVER_100",
                f"Forage '{record.hole_id}' [{record.from_depth}–{record.to_depth}] : somme des proportions {total_percent:g} % supérieure à 100 %.",
                locations=[
                    {"row": component.source_line - 2,
                     "column": component.source_column}
                    for component in record.components])
        elif (len(record.components) > 1 and all_proportions
              and total_percent < 100.0 - 1e-7):
            result.add_issue(
                "warning", "PROPORTION_SUM_UNDER_100",
                f"Forage '{record.hole_id}' [{record.from_depth}–{record.to_depth}] : somme des proportions {total_percent:g} % inférieure à 100 %.",
                locations=[
                    {"row": component.source_line - 2,
                     "column": component.source_column}
                    for component in record.components])
        record.sync_primary_attribute()

    # Primary intervals are mutually exclusive. Secondary/vein components do
    # not enter this overlap test.
    by_hole_primary = {}
    for key, record in grouped.items():
        primary = record.primary_component
        has_unknown_role = any(
            not component.role for component in record.components)
        if ((primary and (primary.role == "primary"
                          or len(record.components) == 1))
                or has_unknown_role):
            by_hole_primary.setdefault(record.hole_id, []).append((key, record))
    for hole_id, intervals in by_hole_primary.items():
        intervals.sort(key=lambda pair: (pair[1].from_depth, pair[1].to_depth))
        previous_key, previous = intervals[0] if intervals else (None, None)
        for current_key, current in intervals[1:]:
            previous_rows = source_rows[previous_key]
            current_rows = source_rows[current_key]
            if current.from_depth < previous.to_depth - 1e-7:
                overlap_start = current.from_depth
                overlap_end = min(previous.to_depth, current.to_depth)
                result.add_issue(
                    "error", "PRIMARY_INTERVAL_OVERLAP",
                    f"Forage '{hole_id}' : chevauchement lithologique "
                    f"[{overlap_start:g}–{overlap_end:g}].",
                    locations=[
                        {"row": previous_rows[-1], "column": to_col},
                        {"row": current_rows[0], "column": from_col}],
                    suggestion="Vérifiez le TO du premier intervalle ou le FROM du second.")
            elif current.from_depth > previous.to_depth + 1e-7:
                result.add_issue(
                    "warning", "PRIMARY_INTERVAL_GAP",
                    f"Forage '{hole_id}' : lacune lithologique "
                    f"[{previous.to_depth:g}–{current.from_depth:g}].",
                    locations=[
                        {"row": previous_rows[-1], "column": to_col},
                        {"row": current_rows[0], "column": from_col}],
                    suggestion="Une lacune peut être valide ; vérifiez simplement qu'elle est volontaire.")
            if current.to_depth > previous.to_depth:
                previous_key, previous = current_key, current

    by_hole = {}
    for record in grouped.values():
        by_hole.setdefault(record.hole_id, []).append(record)
    for records in by_hole.values():
        records.sort(key=lambda item: (item.from_depth, item.to_depth))
    result.num_records = sum(len(records) for records in by_hole.values())
    return by_hole, result


# ---------------------------------------------------------------------------
# Generic interval domains
# ---------------------------------------------------------------------------
def validate_intervals(pr: ParseResult, file_type: str, collar_ids: set[str],
                       content_field: str = None, collars=None):
    if file_type == "structure":
        return validate_structure(pr, collar_ids, collars)
    if file_type == "imagery":
        return validate_imagery(pr, collar_ids, collars)
    if file_type in ("rqd", "recovery", "density"):
        return validate_geotech(pr, file_type, collar_ids, collars)
    if file_type == "litho":
        return validate_lithology(pr, collar_ids, collars)

    result = ValidationResult(file_type, _basename(pr.file_path))
    if file_type == "assays" and pr.detected_layout == "long_values":
        result.add_issue(
            "error", "ASSAY_LONG_FORMAT_NOT_ENABLED",
            "Format LONG des Teneurs détecté (une ligne par élément et "
            "valeur) — DrillMaster n'accepte que le format LARGE, par "
            "règle du projet (décision du 20/08/2026).",
            suggestion=(
                "Exportez ce fichier en format large : une colonne par "
                "élément (Au_ppm, Cu_pct…). « Une règle, un format » — "
                "aucune conversion silencieuse n'est tentée."))
        return {}, result
    required = ["hole_id", "from", "to"]
    # v2.7.11.6 — retour écran (alteration.csv : Alteration_1/_2 +
    # Intensite_1/_2, capture « Champ requis 'alteration' non associé ») :
    # quand les codes d'un domaine viennent d'une ORGANISATION confirmée
    # (large = colonnes parallèles, ou délimitée = cellule multi-codes),
    # exiger EN PLUS une colonne mappée au champ canonique refusait des
    # fichiers parfaitement structurés.  Même règle qu'en lithologie
    # (jamais de champ canonique obligatoire là-bas).
    _profile_req = getattr(pr, "structure", None)
    structured_codes = bool(
        _profile_req is not None
        and _profile_req.confirmed
        and (_profile_req.mode == "wide_components"
             and _profile_req.component_columns
             or _profile_req.mode == "delimited_components"
             and _profile_req.code_column))
    if content_field and not structured_codes:
        required.append(content_field)
    indexes = _check_mapping_safety(pr, result, required)
    if result.errors:
        return {}, result
    # v2.7.12.1 — le correctif Levenshtein mappe désormais les colonnes
    # numérotées (Alt1/Alt2, Style1/2, Min1/2…) sur leur canonique.  Sans
    # organisation confirmée, le mode standard ne lirait que la PREMIÈRE
    # colonne et ignorerait les autres SILENCIEUSEMENT : le fichier est
    # bloqué jusqu'à confirmation explicite (CM-01) — la question ciblée de
    # l'étape 2 propose les deux lectures, le choix ne se devine jamais.
    if (content_field and file_type in ("alterations", "mineralizations")
            and _profile_req is not None and not _profile_req.confirmed):
        from .import_detect import detect_wide_component_columns
        _wcomps_u, _wints_u, _wmins_u = detect_wide_component_columns(
            pr.raw_headers, file_type)
        if _wcomps_u:
            result.add_issue(
                "error", "WIDE_ORGANISATION_UNCONFIRMED",
                "Organisation large détectée : "
                + ", ".join(h for h, _s in _wcomps_u)
                + (" ("
                   + ", ".join(h for h, _s in _wints_u)
                   + " appariées)" if _wints_u else "")
                + ".",
                suggestion=("Confirmez l'organisation dans « Options "
                            "avancées… » : une seule colonne porte le code, "
                            "ou chaque colonne est un code (CM-01)."))
            return {}, result
    valid_ids, max_depths = _collar_ids_and_depths(collar_ids, collars)
    by_hole = {}
    seen = {}
    qaqc_index = _find_qaqc_column(pr) if file_type == "assays" else -1
    qaqc_skipped = 0
    assay_numeric_cols = set()
    assay_text_cells = {}
    assay_censored_cols = set()

    # v2.7.10.38 — CM-01 : en minéralisations au mode large, les colonnes
    # « min1/min2 » (minéraux) sont lues une fois par fichier et JOINTES
    # dans l'attribut « minerals » de l'intervalle (infobulle) — jamais
    # dans la bande de style (AM-05).
    _profile0 = getattr(pr, "structure", None)
    wide_minerals_headers = []
    if (file_type == "mineralizations" and _profile0 is not None
            and _profile0.mode == "wide_components"
            and _profile0.confirmed):
        from .import_detect import detect_wide_component_columns
        wide_minerals_headers = [
            header for header, _suffix in detect_wide_component_columns(
                pr.raw_headers, file_type)[2]]

    # v2.7.11.1 — CM-03 : plafonds d'organisation FIXES par domaine
    # (arbitrage du 21/08/2026, fondé sur les réalités géologiques et la
    # lisibilité de la coupe).  Un dépassement est une ERREUR bloquante
    # qui nomme les colonnes en trop — jamais de troncation silencieuse.
    from .component_caps import (
        MAX_ALTERATION_CODES, MAX_INTENSITY_COLUMNS, MAX_MINERALS,
        MAX_MINERALIZATION_STYLES, cap_excess)
    if (_profile0 is not None and _profile0.mode == "wide_components"
            and _profile0.confirmed and _profile0.component_columns):
        comp_headers = [
            str(c.code_column) for c in _profile0.component_columns]
        if file_type == "alterations":
            excess = cap_excess(comp_headers, MAX_ALTERATION_CODES)
            if excess:
                result.add_issue(
                    "error", "TOO_MANY_COMPONENTS",
                    f"Organisation des altérations : {len(comp_headers)} "
                    f"colonnes de code — maximum {MAX_ALTERATION_CODES}. "
                    f"Colonnes en trop : {', '.join(excess)}.",
                    suggestion=(
                        "Allégez le fichier ou le profil ; aucune colonne "
                        "n'est lue à moitié (arbitrage CM-03)."))
            from .import_detect import (
                detect_wide_component_columns as _dwc)
            int_headers = [
                header for header, _suffix in _dwc(
                    pr.raw_headers, file_type)[1]]
            excess_int = cap_excess(int_headers, MAX_INTENSITY_COLUMNS)
            if excess_int:
                result.add_issue(
                    "error", "TOO_MANY_COMPONENTS",
                    f"Organisation des altérations : {len(int_headers)} "
                    f"colonnes d'intensité appariées — maximum "
                    f"{MAX_INTENSITY_COLUMNS}. "
                    f"Colonnes en trop : {', '.join(excess_int)}.",
                    suggestion=(
                        "Allégez le fichier ou le profil ; aucune colonne "
                        "n'est lue à moitié (arbitrage CM-03)."))
        elif file_type == "mineralizations":
            excess = cap_excess(comp_headers, MAX_MINERALIZATION_STYLES)
            if excess:
                result.add_issue(
                    "error", "TOO_MANY_COMPONENTS",
                    f"Organisation des minéralisations : "
                    f"{len(comp_headers)} colonnes de style — maximum "
                    f"{MAX_MINERALIZATION_STYLES} (dominant + subordonné, "
                    f"arbitrage CM-03). "
                    f"Colonnes en trop : {', '.join(excess)}.",
                    suggestion=(
                        "Allégez le fichier ou le profil ; aucune colonne "
                        "n'est lue à moitié (arbitrage CM-03)."))
            excess_min = cap_excess(wide_minerals_headers, MAX_MINERALS)
            if excess_min:
                result.add_issue(
                    "error", "TOO_MANY_COMPONENTS",
                    f"Organisation des minéralisations : "
                    f"{len(wide_minerals_headers)} colonnes de minéraux — "
                    f"maximum {MAX_MINERALS} (arbitrage CM-03). "
                    f"Colonnes en trop : {', '.join(excess_min)}.",
                    suggestion=(
                        "Allégez le fichier ou le profil ; aucune colonne "
                        "n'est lue à moitié (arbitrage CM-03)."))

    for row_index, row in enumerate(pr.rows):
        if not any(str(value).strip() for value in row):
            continue
        # v2.7.10.39 — les lignes de contrôle qualité (blancs, standards,
        # duplicatas…) sont identifiées AVANT toute validation : elles ne
        # portent pas d'intervalle de teneur (ni de HOLE_ID obligatoire).
        # Jamais silencieux : le compte est averti à la fin du fichier.
        if qaqc_index >= 0:
            qc_value = _cell(row, qaqc_index).strip().casefold()
            if any(qc_value.startswith(p) for p in _QAQC_VALUE_PREFIXES):
                qaqc_skipped += 1
                continue
        id_col, from_col, to_col = (
            indexes["hole_id"], indexes["from"], indexes["to"])
        hole_id = _cell(row, id_col)
        if not hole_id.strip():
            result.add_issue("error", "EMPTY_HOLE_ID",
                             f"Ligne {_source_line(row_index)} : HOLE_ID vide.",
                             row=row_index, column=id_col)
            continue
        if valid_ids and hole_id not in valid_ids:
            result.add_issue(
                "error", "UNKNOWN_HOLE_ID",
                f"[{result.file_name}] Ligne {_source_line(row_index)} : HOLE_ID '{hole_id}' inexistant dans le fichier Collets.",
                row=row_index, column=id_col)
            continue
        start = _parse_numeric(pr, result, row, row_index, from_col, "from")
        end = _parse_numeric(pr, result, row, row_index, to_col, "to")
        if start is None or end is None:
            continue
        if start < 0:
            result.add_issue("error", "NEGATIVE_FROM",
                             f"{_message_prefix(result, row_index)} : FROM ({start}) négatif.",
                             row=row_index, column=from_col)
        if start >= end:
            result.add_issue(
                "error", "FROM_GE_TO",
                f"{_message_prefix(result, row_index)}, forage '{hole_id}' : FROM ({start}) >= TO ({end}).",
                locations=[
                    {"row": row_index, "column": from_col},
                    {"row": row_index, "column": to_col}],
                suggestion="Vérifiez les deux limites.")
        if hole_id in max_depths and end > max_depths[hole_id] + 1e-7:
            result.add_issue(
                "error", "INTERVAL_BEYOND_HOLE_DEPTH",
                f"{_message_prefix(result, row_index)}, forage '{hole_id}' : TO ({end}) dépasse la profondeur totale ({max_depths[hole_id]}).",
                row=row_index, column=to_col)

        # v2.7.11.6 — les colonnes de minéraux absorbées par une
        # organisation large ne sont pas écrites une à une dans
        # « minerals » (la dernière écrasait les autres) : la jointure
        # « Minéraux » les réunit UNE fois, plus bas.
        skip_wide_minerals = (
            file_type == "mineralizations"
            and _profile0 is not None
            and _profile0.mode == "wide_components"
            and _profile0.confirmed)
        attrs = {}
        for column, raw_header in enumerate(pr.raw_headers):
            canonical = pr.effective_mappings.get(raw_header)
            if canonical in ("hole_id", "from", "to") or column >= len(row):
                continue
            if (skip_wide_minerals and canonical == "minerals"
                    and raw_header in wide_minerals_headers):
                continue
            raw = row[column].strip()
            if not raw:
                continue
            key = canonical or raw_header
            # v2.7.12.1 — le correctif Levenshtein mappe ALT1/ALT2 (ou
            # INT1/INT2) sur le même canonique : l'attribut d'intervalle est
            # celui du PREMIER code (AM-03, affichage historique) — la
            # première colonne gagne, les autres colonnes sont portées par
            # les composants, jamais écrasées ici.
            if (canonical and key in attrs
                    and file_type in ("alterations", "mineralizations")):
                continue
            if file_type == "assays":
                # v2.9.273 — colonne « Ignorer » respectée ; métadonnées texte
                # ignorées ; valeurs censurées légitimes ; cellule illisible
                # dans une vraie colonne d'élément = avertissement, plus
                # d'erreur bloquante (retour écran : export Excel brut).
                if canonical == "":
                    continue
                kind, value = _classify_assay_value(raw, pr.decimal_sep)
                if kind == "number":
                    attrs[key] = value
                    assay_numeric_cols.add(raw_header)
                elif kind == "censored":
                    attrs[key] = None
                    assay_censored_cols.add(raw_header)
                    assay_numeric_cols.add(raw_header)
                else:
                    assay_text_cells[raw_header] = (
                        assay_text_cells.get(raw_header, 0) + 1)
                continue
            else:
                attrs[key] = raw

        # v2.7.11.6 — la jointure « Minéraux » a lieu ICI : AVANT le
        # contrôle STERILE_WITH_MINERALS, sinon ce dernier lisait un vide
        # qui n'existe pas (colonnes d'organisation écartées du canonique
        # et jointes plus bas).
        if (file_type == "mineralizations"
                and _profile0 is not None
                and _profile0.mode == "wide_components"
                and _profile0.confirmed and wide_minerals_headers
                and "minerals" not in attrs):
            minerals_parts0 = []
            for header in wide_minerals_headers:
                minerals_index0 = _header_index(pr, header)
                value0 = _cell(row, minerals_index0).strip()
                if value0:
                    minerals_parts0.append(value0)
            if minerals_parts0:
                attrs["minerals"] = ", ".join(minerals_parts0)
        content_value = attrs.get(content_field, "") if content_field else ""
        if file_type == "mineralizations":
            style_text = str(attrs.get("mineralization_style", "")).strip().casefold()
            minerals_text = str(attrs.get("minerals", "")).strip()
            if ("sterile" in style_text
                    and minerals_text
                    and minerals_text.casefold() not in {"sterile", "aucun", "none"}):
                style_column = indexes.get("mineralization_style")
                minerals_column = indexes.get("minerals")
                result.add_issue(
                    "warning", "STERILE_WITH_MINERALS",
                    f"{_message_prefix(result, row_index)} : style stérile avec minéraux '{minerals_text}'.",
                    locations=[
                        {"row": row_index, "column": style_column},
                        {"row": row_index, "column": minerals_column}],
                    suggestion="Vérifiez cette combinaison ; aucune valeur n'est modifiée.")
        support = (hole_id, round(start, 7), round(end, 7))
        duplicate_key = (support, content_value) if file_type in {
            "alterations", "mineralizations"} else support
        if duplicate_key in seen:
            first = seen[duplicate_key]
            result.add_issue(
                "error", "DUPLICATE_INTERVAL",
                f"Forage '{hole_id}' : intervalle dupliqué [{start}–{end}].",
                locations=[
                    {"row": first, "column": from_col},
                    {"row": row_index, "column": from_col}])
        else:
            seen[duplicate_key] = row_index

        # AM-06 — explicit delimited convention outside lithology: the raw
        # attribute is preserved untouched; the declared codes additionally
        # ride as components so views can draw each phenomenon.
        components = []
        split_field = SPLIT_CONTENT_FIELDS.get(file_type, "")
        profile = getattr(pr, "structure", None)
        if (split_field and profile is not None
                and profile.mode == "delimited_components"
                and profile.confirmed and profile.delimiter):
            target = split_field
            if profile.code_column:
                # v2.7.11.6 — retour écran : la colonne de codes n'est pas
                # toujours mappée à la cible canonique (Alteration_1 &
                # co. ne matchent pas « alteration »).  Sans mapping,
                # lire la clé attribuée BRUTE (attrs retient l'en-tête
                # source) au lieu de tomber sur un canonique absent → la
                # cellule délimitée était perdue en silence.
                mapped_target = pr.effective_mappings.get(
                    profile.code_column)
                target = mapped_target or profile.code_column
            raw_cell = str(attrs.get(target, "")).strip()
            # v2.7.11.6 — retour écran : colonne d'intensité restée
            # immaquée canoniquement (Intensite_1 ne matche pas
            # « intensity » à confiance suffisante).  S'il n'y a QU'UNE
            # colonne candidate d'intensité (socle int/intens), sa valeur
            # brute alimente l'attribut d'intervalle — lecture honnête,
            # rien d'inventé.
            if "intensity" not in attrs:
                from .import_detect import (
                    detect_wide_component_columns as _dwci)
                int_cands = _dwci(
                    pr.raw_headers, file_type)[1]
                if len(int_cands) == 1:
                    int_text = _cell(
                        row, _header_index(pr, int_cands[0][0])).strip()
                    if int_text:
                        attrs["intensity"] = int_text
            if raw_cell and profile.delimiter in raw_cell:
                parts = split_delimited_codes(raw_cell, profile.delimiter)
                # v2.7.11.1 — CM-03 : plafond de codes par intervalle
                # (arbitrage géologique + lisibilité) ; le dépassement
                # bloque et nomme la cellule, rien n'est tronqué.
                from .component_caps import (
                    MAX_ALTERATION_CODES, MAX_MINERALS, cap_excess)
                codes_cap = (MAX_ALTERATION_CODES if file_type == "alterations"
                             else MAX_MINERALS)
                excess_parts = cap_excess(parts, codes_cap)
                if excess_parts:
                    result.add_issue(
                        "error", "TOO_MANY_COMPONENTS",
                        f"{_message_prefix(result, row_index)} : "
                        f"{len(parts)} codes dans '{raw_cell}' — maximum "
                        f"{codes_cap} (arbitrage CM-03). "
                        f"Codes en trop : {', '.join(excess_parts)}.",
                        row=row_index,
                        suggestion=(
                            "Allégez la cellule ; aucun code n'est "
                            "tronqué silencieusement."))
                split_column = next(
                    (i for i, raw_h in enumerate(pr.raw_headers)
                     if pr.effective_mappings.get(raw_h) == target), -1)
                if any(not part.strip()
                       for part in raw_cell.split(profile.delimiter)):
                    result.add_issue(
                        "error", "EMPTY_DELIMITED_COMPONENT",
                        f"{_message_prefix(result, row_index)} : "
                        f"composant vide dans '{raw_cell}'.",
                        row=row_index, column=split_column)
                for index, value in enumerate(parts):
                    role = ""
                    if profile.first_component_role == "primary":
                        role = "primary" if index == 0 else "secondary"
                    components.append(LithologyComponent(
                        raw_code=value, role=role, raw_role=role,
                        proportion_unit="unknown",
                        source_line=_source_line(row_index),
                        source_column=split_column,
                        source_header=profile.code_column or target))
        # v2.7.10.37 — CM-01 : organisation « LARGE » (alt1/alt2/int1/int2,
        # style1/style2…) : CHAQUE colonne déclarée porte un code du MÊME
        # intervalle — vide = ignoré, jamais inventé ; aucun rôle ni
        # proportion n'est supposé (AM-05). L'intensité de l'intervalle
        # s'appaire par suffixe (int1 ≡ colonne 1), priorité à une vraie
        # colonne mappée « Intensité ». En minéralisations, les composants
        # du mode large portent le STYLE — marqués pour que la piste de
        # style les lise, ceux du split « Minéraux » restent hors bandes.
        if (split_field and profile is not None
                and profile.mode == "wide_components"
                and profile.confirmed and profile.component_columns):
            import re as _re
            paired = []  # (definition, composant lu ou None si cellule vide)
            for definition in profile.component_columns:
                col_index = _header_index(pr, definition.code_column)
                value = _cell(row, col_index).strip()
                if not value:
                    paired.append((definition, None))
                    continue
                component = LithologyComponent(
                    raw_code=value, role="", raw_role="",
                    proportion_unit="unknown",
                    source_line=_source_line(row_index),
                    source_column=col_index,
                    source_header=definition.code_column)
                components.append(component)
                paired.append((definition, component))
            # v2.7.11.1 — CM-03 : intensité PAR CODE (altérations).  La
            # colonne Int_k appariée par suffixe porte l'intensité DU code
            # de la colonne k (brute, jamais jugée) ; sans appairage, le
            # code hérite de l'intensité d'intervalle à l'affichage
            # (AM-03 — repli identique à l'historique).  Minéralisation :
            # jamais d'intensité par code (modèle strict).
            if file_type == "alterations":
                for definition, component in paired:
                    if component is None:
                        continue
                    suffix_match = _re.match(
                        r"^.*?([0-9]+)$",
                        str(definition.code_column).strip())
                    if not suffix_match:
                        continue
                    k_suffix = suffix_match.group(1)
                    k_index = next(
                        (i for i, raw_h in enumerate(pr.raw_headers)
                         if "int" in str(raw_h).strip().casefold()
                         and str(raw_h).strip().casefold()
                         .rstrip().endswith(k_suffix)),
                        -1)
                    if k_index >= 0:
                        k_text = _cell(row, k_index).strip()
                        if k_text:
                            component.intensity = k_text
            numeric_suffix = _re.match(
                r"^.*?([0-9]+)$",
                str(profile.component_columns[0].code_column).strip())
            if numeric_suffix:
                suffix = numeric_suffix.group(1)
                intensity_index = next(
                    (i for i, raw_h in enumerate(pr.raw_headers)
                     if "int" in str(raw_h).strip().casefold()
                     and str(raw_h).strip().casefold().rstrip().endswith(suffix)),
                    -1)
                if "intensity" not in attrs and intensity_index >= 0:
                    intensity_text = _cell(row, intensity_index).strip()
                    if intensity_text:
                        attrs["intensity"] = intensity_text
        if components and file_type == "mineralizations" \
                and profile is not None:
            styleish = False
            if profile.mode == "wide_components":
                styleish = True
            elif profile.mode == "delimited_components":
                # v2.7.11.7 — retour écran : colonne de STYLES séparée
                # sur « / » (ex. MASSIVE/DISSEMINEE).  La piste doit lire
                # ces composants, PAS le texte brut joint — le marqueur
                # AM-05 s'applique aussi aux splits de style déclarés.
                # Règle exacte : une colonne est « minéraux » si elle est
                # MAPPÉE au canonique, ou détectée candidate minéraux de
                # l'organisation large (socle « min » + chiffre, CM-01).
                # Toute autre colonne déclarée porte des STYLES — « min »
                # dans le nom ne suffit pas (le fichier de l'utilisateur
                # nomme sa colonne de styles « StyleMin »).
                code_target = pr.effective_mappings.get(
                    profile.code_column or "")
                minerals_candidates = set()
                if profile.code_column:
                    from .import_detect import (
                        detect_wide_component_columns)
                    minerals_candidates = {
                        header for header, _suffix in
                        detect_wide_component_columns(
                            pr.raw_headers, "mineralizations")[2]}
                styleish = not (
                    code_target == "minerals"
                    or profile.code_column in minerals_candidates)
            if styleish:
                attrs["_wide_styles"] = "1"

        by_hole.setdefault(hole_id, []).append(IntervalRecord(
            hole_id=hole_id, from_depth=start, to_depth=end,
            attributes=attrs, source_line=_source_line(row_index),
            components=components))

    if file_type == "assays":
        metadata_cols = sorted(h for h in assay_text_cells
                               if h not in assay_numeric_cols)
        mixed_cols = sorted(h for h in assay_text_cells
                            if h in assay_numeric_cols)
        if metadata_cols:
            result.add_issue(
                "warning", "ASSAY_TEXT_COLUMNS_IGNORED",
                f"{len(metadata_cols)} colonne(s) de métadonnées texte "
                f"ignorée(s) comme éléments : {', '.join(metadata_cols)}.",
                suggestion="Ce sont des colonnes descriptives, pas des "
                           "teneurs. « Champ cible → Ignorer » si le choix "
                           "automatique ne convient pas.")
        if mixed_cols:
            result.add_issue(
                "warning", "ASSAY_UNREADABLE_VALUES",
                "Valeur(s) non numérique(s) ignorée(s) — conservée(s) telle(s) "
                f"quelle(s) — dans : {', '.join(mixed_cols)}.",
                suggestion="Une cellule illisible dans une colonne de teneur "
                           "n'est plus une erreur bloquante ; corrigez-la dans "
                           "l'éditeur CSV si besoin.")
    if file_type == "assays" and assay_censored_cols:
        result.add_issue(
            "warning", "ASSAY_CENSORED_VALUES",
            "Valeurs censurées (seuil de détection, ex. « <0,01 ») dans : "
            f"{', '.join(sorted(assay_censored_cols))}. Conservées comme non "
            "quantifiées — un résultat d'analyse légitime, jamais une erreur.")
    if qaqc_index >= 0 and qaqc_skipped:
        result.add_issue(
            "warning", "QAQC_SAMPLES_SET_ASIDE",
            f"{qaqc_skipped} ligne(s) QA/QC (blancs, standards, CRM, "
            "duplicatas…) identifiées par la colonne de type d'échantillon "
            "et écartées des teneurs. Les données sources restent intactes ; "
            "le contrôle qualité proprement dit arrive en v2.9.")
    for records in by_hole.values():
        records.sort(key=lambda item: (item.from_depth, item.to_depth))
    result.num_records = sum(len(records) for records in by_hole.values())
    return by_hole, result


# ---------------------------------------------------------------------------
# v2.7.10.39 — QA/QC minimal (directive écran 20/08/2026) : si le fichier
# des teneurs porte une colonne de TYPE d'échantillon (blank/standard/
# CRM/duplicata…), les lignes QC sont ÉCARTÉES des teneurs avec
# avertissement — les données sources restent intactes, le contrôle
# qualité proprement dit vient ensuite.
_QAQC_COLUMN_ALIASES = {
    "sampletype", "sample_type", "sample.type", "sample_type_raw",
    "qa_qc", "qaqc", "qc", "controltype", "control_type",
    "analysistype", "analysis_type", "assaytype",
}
_QAQC_VALUE_PREFIXES = (
    "blank", "std", "standard", "crm", "dup", "duplicate", "check",
    "qc", "control",
)


def _find_qaqc_column(pr):
    """Index of a sample-type control column, or -1 (exact match only :
    jamais de sous-chaîne — éviter toute usurpation d'une vraie colonne)."""
    for index, raw in enumerate(pr.raw_headers or []):
        folded = str(raw).strip().casefold().replace(" ", "").replace("_", "").replace(".", "")
        if folded in _QAQC_COLUMN_ALIASES:
            return index
    return -1


# ---------------------------------------------------------------------------
# v2.9.273 — Teneurs : lecture tolérante d'un export BRUT.  Trois catégories :
#   « number »   → valeur d'élément normale ;
#   « censored » → « <0,01 », « >10000 »… : résultat d'analyse LÉGITIME
#                  (sous/au-dessus du seuil) — avertissement, jamais erreur ;
#   « text »     → colonne descriptive (pays, projet, permis…) : ignorée
#                  comme élément, avec UN avertissement agrégé par fichier.
# ---------------------------------------------------------------------------
_CENSORED_VALUE_RE = re.compile(r"^[<≤>≥]\s*\d+(?:[.,]\d+)?$")


def _classify_assay_value(raw, decimal_sep):
    """(« number »|« censored »|« text », valeur float ou None)."""
    text = (raw or "").strip()
    if _CENSORED_VALUE_RE.match(text):
        return "censored", None
    value = parse_number(text, decimal_sep)
    if value is not None and math.isfinite(value):
        return "number", value
    return "text", None


# ---------------------------------------------------------------------------
# Cross-file validation and automatic vertical trajectories
# ---------------------------------------------------------------------------
def auto_survey_for_vertical(collar: CollarRecord) -> list[SurveyRecord]:
    azimuth = collar.azimuth if collar.azimuth is not None else 0.0
    dip = collar.dip if collar.dip is not None else -90.0
    return [SurveyRecord(
        hole_id=collar.hole_id, depth=0.0,
        azimuth=azimuth, dip=dip)]
