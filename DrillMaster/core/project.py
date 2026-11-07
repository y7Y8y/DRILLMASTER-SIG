"""
DrillMaster — Project Management
================================
Manages the project folder structure and config.json.

Pure Python (json, os, shutil) — testable standalone.
QGIS CRS handling is done at the UI layer via QgsCoordinateReferenceSystem.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime
from typing import Optional

# Default base directory
DEFAULT_BASE_DIR = os.path.expanduser("~/QGIS/DrillMaster")

# Config file version
CONFIG_VERSION = "2.0.0"


def default_section_style() -> dict:
    """Visual defaults for the cross-section property panel."""
    return {
        "show_grid": True,
        "show_elevation_values": True,
        "show_distance_values": True,
        "show_axis_titles": True,
        "grid_color": "#D5DBDB",
        "grid_width": 0.7,
        "grid_style": "dash",
        "grid_opacity": 70,
        "elevation_grid_step": 20.0,  # v2.9.70 défaut 20 m (Auto donnait 10 m)
        "distance_grid_step": 0.0,
        "axis_value_font_size": 7,
        "axis_value_color": "#7F8C8D",
        "axis_value_bold": False,
        "axis_value_decimals": 0,
        "axis_title_font_size": 8,
        "axis_title_color": "#566573",
        "axis_title_bold": True,
        "buffer_mode": "collar",
        # v2.7.8 — décision écran : le corridor QGIS est OFF par défaut,
        # il s'active explicitement (le tracé ne doit rien afficher de
        # surprenant sur la carte).
        "show_buffer_on_map": False,
        "show_collar_labels": True,
        "show_collar_info": True,
        "collar_id_font_size": 8,
        "collar_info_font_size": 7,
        # The annotation block handles spacing; user offsets default to zero.
        "collar_id_position": "top",
        "collar_info_position": "top",
        "collar_id_offset_x": 0.0,
        "collar_id_offset_y": 0.0,
        "collar_info_offset_x": 0.0,
        "collar_info_offset_y": 0.0,
        "collar_marker_size": 6.0,
        "shared_collar_tolerance": 0.1,
        "show_trajectory": True,
        "trajectory_color": "#393939",
        "trajectory_width": 0.5,
        "show_depth": True,
        # v2.7.7.3 — largeurs par défaut calées sur la matrice
        # utilisateur (≈ 17 px litho (v2.9.25), 4 mm ≈ 15 px teneurs,
        # 2 mm ≈ 8 px pistes codées, ticks ≈ 1 mm ≈ 4 px) : l'emprise
        # par forage reste gérable quand plusieurs trous se côtoient.
        # v2.7.7 — backbone de profondeur : graduations tous les 10 m,
        # étiquettes toutes les 2 graduations (20 m) ; 0 = pas automatique.
        "depth_step": 10.0,
        "depth_label_every": 2,
        "depth_font_size": 6,
        # v2.7.8.3 — débord 2 px, texte 6 pt (v2.9.25), opacité 80 % : le trait
        # porte visiblement son étiquette sans devenir criard.
        "depth_tick_length": 2.0,
        "depth_tick_width": 1.0,
        "depth_opacity": 80,
        "depth_side": "left",
        "show_litho": True,
        "litho_width": 10.0,  # v2.9.278 : voies plus fines (retour écran)
        "litho_opacity": 100,  # v2.9.15 — plein par défaut
        # v2.7.9.6 — DÉFAUT DÉCOCHÉ (décision écran) : les hachures sont
        # fixes à l'écran ; « aligné sur l'axe des forages » reste une
        # option dans Pistes pour qui veut la convention log.
        "patterns_follow_hole_axis": False,  # v2.9.28 option UI retirée

        # v2.7.7 — positions des pistes (AUDIT_V2.7.7.md) : teneurs à gauche,
        # altérations puis minéralisations à droite, auto-collapse géré par
        # core.track_layout.
        "assay_side": "left",
        "alter_side": "right",
        "mineral_side": "right",
        # v2.7.2 — coded tracks (AM-01) ; visibility/width/opacity are view
        # properties, symbols stay in the Référentiel.
        # v2.7.3 → v2.7.13.0 — one grouped band per family (le mode
        # « sous-pistes par type » a été supprimé, retour écran).
        "show_alterations": True,
        "alter_width": 12.0,  # v2.9.69 — voie 12 px
        "alter_opacity": 80,
        "show_mineralizations": True,
        "mineral_width": 12.0,  # v2.9.69 — voie 12 px
        "mineral_opacity": 80,
        # v2.9.260 (étape 2) — piste des mesures de structure.
        "show_structures": True,
        "structure_width": 12.0,
        "structure_opacity": 90,
        "structure_side": "right",
        "structure_marker_size": 5.0,
        "structure_min_spacing": 9.0,
        # v2.9.262 (Chantier 2 E2) — piste « Imagerie » : bandes photo/scan.
        # Le cache ≈ 512 px n'est pas exposé en v1 (décision plan §7).
        "show_imagery": True,
        "imagery_width": 28.0,
        "imagery_side": "right",
        "imagery_opacity": 100,
        "show_assays": True,
        "show_intercepts": True,
        "assay_max_width": 15.0,
        "assay_width_mode": "proportional",
        "show_orientation": True,
        "orientation_position": "auto",
        "orientation_font_size": 9,
        "show_scale_bar": True,
        "scale_position": "auto",
        "scale_size": "medium",
        # v2.9.0 — topographie (ligne de sol) : cascade MNT → CSV →
        # collets, ancrage aux collets ; seuil du QC MNT ↔ collets (m).
        "show_surface": True,
        "surface_color": "#8B6F52",
        "surface_qc_threshold": 2.0,
    }


def default_assay_style() -> dict:
    """Shared grade-map defaults used by QGIS and section views."""
    return {
        "element": "",
        # v2.9.92 — multi-teneurs coupe (max 3) ; rétrocompat : liste dérivée de element
        "elements": [],
        "element_palettes": {},
        "method": "jenks",
        "n_classes": 7,
        "manual_breaks": [],
        "round_breaks": True,
        "scale_scope": "project",
        "palette": "grade",
        "opacity": 100,  # v2.9.15 — teneurs pleines par défaut
        "map_line_width": 1.8,
        # v2.9.102 — règle de seuil (affichage only ; jamais écrit dans sources)
        # v2.9.116 — multi-règles (max 3) + couleurs fixes ; threshold_rule = miroir 1ʳᵉ
        "threshold_rule": {
            "enabled": False,
            "element": "",
            "operator": ">",
            "value": None,
            "clauses": [],
            "litho_filter": [],
            "color": "#00E5FF",
            "color_name": "cyan",
        },
        "threshold_rules": [],
    }


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------
def default_config() -> dict:
    """Return a fresh default configuration dict."""
    return {
        "version": CONFIG_VERSION,
        "project_name": "",
        "project_dir": "",
        "crs": "",
        "crs_description": "",
        "units": "meters",            # meters | feet
        "default_sampling_step": 20.0,
        "current_step": 0,             # 0=not started, 1-4 = steps
        "csv_mappings": {
            "collar": {},
            "survey": {},
            "litho": {},
            "assays": {},
            "alterations": {},
            "mineralizations": {},
            "structure": {},
            "imagery": {},
        },
        "imported_files": {
            "collar": "",
            "survey": "",
            "litho": "",
            "assays": "",
            "alterations": "",
            "mineralizations": "",
            "structure": "",
            "imagery": "",
        },
        "imported_encodings": {
            "collar": "",
            "survey": "",
            "litho": "",
            "assays": "",
            "alterations": "",
            "mineralizations": "",
            "structure": "",
            "imagery": "",
        },
        "imported_separators": {
            "collar": "",
            "survey": "",
            "litho": "",
            "assays": "",
            "alterations": "",
            "mineralizations": "",
            "structure": "",
            "imagery": "",
        },
        "imported_decimal_seps": {
            "collar": ".",
            "survey": ".",
            "litho": ".",
            "assays": ".",
            "alterations": ".",
            "mineralizations": ".",
            "structure": ".",
            "imagery": ".",
        },
        # v2.9.262 — stockage des images du projet : "link" (par défaut,
        # chemins relatifs, aucun doublon) ou "copy" (copie dans assets/).
        "image_storage_mode": "link",
        "data_registry": {},
        "reference_style_migration": 0,
        "section_config": {
            "buffer": 50.0,
            "vertical_exaggeration": 1.0,
        },
        "section_style": default_section_style(),
        "assay_style": default_assay_style(),
        "litho_styles": {},
        "sections": [],          # list of saved section lines
        "next_section_id": 1,    # auto-increment for section naming
        "current_section_id": None,
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
class ProjectPaths:
    """Convenience accessor for all project file/folder paths."""

    def __init__(self, base_dir: str, project_name: str):
        self.base_dir = base_dir
        self.project_name = project_name
        self.project_dir = os.path.join(base_dir, project_name)
        self.data_import_dir = os.path.join(self.project_dir, "data_import")
        self.assets_dir = os.path.join(self.project_dir, "assets")
        self.references_dir = os.path.join(self.project_dir, "references")
        self.domains_file = os.path.join(self.references_dir, "domains.json")
        self.styles_file = os.path.join(self.references_dir, "styles.json")
        self.classifications_file = os.path.join(
            self.references_dir, "classifications.json")
        self.geometry_gpkg = os.path.join(self.project_dir, "drillmaster_geometry.gpkg")
        self.data_gpkg = os.path.join(self.project_dir, "drillmaster_data.gpkg")
        self.config_file = os.path.join(self.project_dir, "config.json")

    def imported_file_path(self, original_name: str) -> str:
        """Path where a raw CSV copy is stored."""
        return os.path.join(self.data_import_dir, os.path.basename(original_name))


class DrillMasterProject:
    """
    Manages a DrillMaster project: folder structure, config persistence,
    and imported file copies.
    """

    def __init__(self, base_dir: str = None):
        self.base_dir = os.path.abspath(os.path.expanduser(
            base_dir or DEFAULT_BASE_DIR))
        self.config: dict = default_config()
        self.paths: Optional[ProjectPaths] = None

    @property
    def name(self) -> str:
        """Return the display name of the project."""
        if self.config and self.config.get("project_name"):
            return str(self.config.get("project_name", ""))
        if self.paths and getattr(self.paths, "project_name", None):
            return str(self.paths.project_name)
        return ""

    # -----------------------------------------------------------------------
    # Project lifecycle
    # -----------------------------------------------------------------------
    def create(self, project_name: str, crs: str, units: str,
               sampling_step: float, crs_description: str = "") -> ProjectPaths:
        """Create a new project with the folder structure."""
        # Sanitise project name
        safe_name = self._sanitise_name(project_name)
        paths = ProjectPaths(self.base_dir, safe_name)

        # Create directories
        os.makedirs(paths.project_dir, exist_ok=True)
        os.makedirs(paths.data_import_dir, exist_ok=True)
        os.makedirs(paths.assets_dir, exist_ok=True)
        os.makedirs(paths.references_dir, exist_ok=True)

        # Initialise config
        self.config = default_config()
        self.config["project_name"] = project_name  # keep display name
        self.config["project_dir"] = paths.project_dir
        self.config["crs"] = crs
        self.config["crs_description"] = crs_description
        self.config["units"] = units
        self.config["default_sampling_step"] = sampling_step
        self.config["current_step"] = 1
        self.paths = paths
        self.save_config()
        self.save_reference_repository(self.get_reference_repository())
        for reserved_file in (
                paths.styles_file, paths.classifications_file):
            if not os.path.isfile(reserved_file):
                with open(reserved_file, "w", encoding="utf-8") as stream:
                    json.dump({}, stream, indent=2)
        return paths

    def load(self, project_dir: str) -> bool:
        """Load an existing project from any user-selected directory."""
        project_dir = os.path.abspath(os.path.expanduser(project_dir))
        config_path = os.path.join(project_dir, "config.json")
        if not os.path.isfile(config_path):
            return False
        try:
            with open(config_path, "r", encoding="utf-8") as stream:
                loaded = json.load(stream)
        except (OSError, ValueError, TypeError):
            return False
        if not isinstance(loaded, dict):
            return False
        # v2.7.7 — l'état du style est capturé AVANT la fusion des défauts
        # (qui remplit section_style) pour savoir si les anciens drapeaux
        # show_* doivent y être repliés.
        had_section_style = bool(loaded.get("section_style"))
        defaults = default_config()
        for key, value in defaults.items():
            if key not in loaded:
                loaded[key] = value
            elif isinstance(value, dict) and isinstance(loaded.get(key), dict):
                for child_key, child_value in value.items():
                    loaded[key].setdefault(child_key, child_value)
        self.config = loaded
        # v2.7.6.9 — l'export est retiré définitivement (AUDIT_V2.7.6.9.md) :
        # purge de la disposition d'export mémorisée par les anciennes
        # versions, qui n'a plus de consommateur.
        self.config.pop("export_layout", None)
        # v2.7.7 — « bons paramètres sans redondance » : section_config ne
        # porte plus que le buffer et l'exagération. Les anciens drapeaux
        # show_* (doublons de section_style) sont repliés dans
        # section_style s'il n'existait pas, puis retirés.
        section_cfg = self.config.get("section_config")
        if isinstance(section_cfg, dict):
            legacy = {
                key: section_cfg.pop(key)
                for key in ("show_litho", "show_assays", "show_alterations")
                if key in section_cfg
            }
            if legacy and not had_section_style:
                style = self.config.setdefault("section_style", {})
                for key, value in legacy.items():
                    style[key] = value

        # Rebuild every derived path from the selected folder. The previous
        # implementation only replaced ``project_dir`` and left GPKG/import
        # paths pointing to the default ~/QGIS/DrillMaster location.
        self.base_dir = os.path.dirname(project_dir)
        self.paths = ProjectPaths(self.base_dir, os.path.basename(project_dir))
        self.config["project_dir"] = project_dir
        os.makedirs(self.paths.data_import_dir, exist_ok=True)
        os.makedirs(self.paths.references_dir, exist_ok=True)
        self.migrate_reference_styles()
        # v2.7.10.3 — éclate les entrées composites « minerals » des
        # anciens projets (cause du « ça ne s'applique pas »).
        self.migrate_minerals_tokens()
        # v2.7.10.5 — convertit les anciens symboles de style en codes
        # 2 lettres (stabilisation des projets 2.7.10.2/3).
        self.migrate_style_codes()
        return True

    def open_by_name(self, project_name: str) -> bool:
        """Open a project by name (relative to base_dir)."""
        safe_name = self._sanitise_name(project_name)
        project_dir = os.path.join(self.base_dir, safe_name)
        return self.load(project_dir)

    # -----------------------------------------------------------------------
    # v2.7.6.9 (RESET-01) — reset / definitive project deletion
    # -----------------------------------------------------------------------
    @staticmethod
    def is_drillmaster_project_dir(project_dir: str) -> tuple[bool, str]:
        """Return ``(ok, reason)`` for a folder the plugin may delete.

        The plugin only ever deletes a folder that looks like a DrillMaster
        project: it exists and holds a readable ``config.json`` with a
        non-empty ``project_name``. This is a hard guard against an
        accidental ``rmtree`` on any arbitrary user folder.
        """
        project_dir = os.path.abspath(
            os.path.expanduser(str(project_dir or "")))
        if not project_dir or not os.path.isdir(project_dir):
            return False, "Le dossier n'existe pas."
        config_path = os.path.join(project_dir, "config.json")
        if not os.path.isfile(config_path):
            return False, ("Ce dossier ne contient pas de config.json "
                           "DrillMaster : suppression refusée.")
        try:
            with open(config_path, "r", encoding="utf-8") as stream:
                config = json.load(stream)
        except (OSError, ValueError, TypeError):
            return False, ("Le config.json est illisible : "
                           "suppression refusée.")
        if (not isinstance(config, dict)
                or not str(config.get("project_name", "")).strip()):
            return False, ("Le config.json n'a pas de project_name "
                           "DrillMaster valide : suppression refusée.")
        return True, ""

    def delete_project_folder(self) -> tuple[bool, str]:
        """Delete the open project folder after a strict validation.

        Never deletes the parent base directory and never deletes a folder
        that is not a valid DrillMaster project (see
        :meth:`is_drillmaster_project_dir`). Returns ``(ok, message)``.
        """
        if not self.paths or not self.paths.project_dir:
            return False, "Aucun projet ouvert."
        ok, reason = self.is_drillmaster_project_dir(
            self.paths.project_dir)
        if not ok:
            return False, reason
        try:
            shutil.rmtree(self.paths.project_dir)
        except OSError as error:
            return False, f"Suppression impossible : {error}"
        return True, ""

    # -----------------------------------------------------------------------
    # Config persistence
    # -----------------------------------------------------------------------
    def save_config(self):
        """Save config.json to the project directory."""
        if not self.paths:
            return
        self.config["last_modified"] = datetime.now().isoformat()
        temporary = self.paths.config_file + ".tmp"
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(self.config, stream, indent=2, ensure_ascii=False)
        os.replace(temporary, self.paths.config_file)

    def set_step(self, step: int):
        """Set the current wizard step."""
        self.config["current_step"] = step
        self.save_config()

    def get_step(self) -> int:
        return self.config.get("current_step", 0)

    # -----------------------------------------------------------------------
    # CSV mappings
    # -----------------------------------------------------------------------
    def save_mappings(self, file_type: str, mappings: dict[str, str]):
        """Save header mappings and keep the unified registry synchronized."""
        self.config["csv_mappings"][file_type] = mappings
        registry = self.get_data_registry()
        record = registry.get(file_type)
        if record:
            record.mappings = dict(mappings)
            self.config["data_registry"] = registry.to_dict()
        self.save_config()

    def get_mappings(self, file_type: str) -> dict[str, str]:
        return self.config.get("csv_mappings", {}).get(file_type, {})

    def get_learned_synonyms(self) -> dict[str, list[str]]:
        """Synonymes de colonnes appris par le projet (v2.7.6, IMP-02).

        Toute correction d'association enseigne le projet : l'en-tête brut
        devient synonyme du champ choisi pour les prochains imports (tous
        onglets). Règles de prudence : un même en-tête associé à des champs
        différents selon les onglets n'est **pas** appris (ambigu) ; les
        synonymes déjà connus nativement ne sont pas réappris.
        """
        from .csv_parser import _normalise_header
        from .data_model import FIELD_SYNONYMS
        known = {
            _normalise_header(synonym)
            for synonyms in FIELD_SYNONYMS.values()
            for synonym in synonyms}
        by_header: dict[str, set[str]] = {}
        for mappings in self.config.get("csv_mappings", {}).values():
            for raw_header, canonical in (mappings or {}).items():
                if not raw_header or not canonical:
                    continue
                norm = _normalise_header(str(raw_header))
                if not norm or norm in known or norm == _normalise_header(canonical):
                    continue
                by_header.setdefault(norm, set()).add(canonical)
        learned: dict[str, list[str]] = {}
        for norm, canonicals in by_header.items():
            if len(canonicals) != 1:
                continue  # en-tête ambigu d'un onglet à l'autre : pas appris
            learned.setdefault(next(iter(canonicals)), []).append(norm)
        return learned

    # -----------------------------------------------------------------------
    # Imported file tracking
    # -----------------------------------------------------------------------
    def record_import(self, file_type: str, file_path: str, encoding: str,
                      separator: str, decimal_sep: str, headers=None,
                      mappings=None, crs="", unit="", structure=None):
        """Record that a file has been imported and copy it to data_import."""
        if not self.paths:
            return
        basename = os.path.basename(file_path)
        dest = self.paths.imported_file_path(basename)
        if os.path.abspath(file_path) != os.path.abspath(dest):
            shutil.copy2(file_path, dest)

        self.config.setdefault("imported_files", {})[file_type] = basename
        self.config.setdefault("imported_encodings", {})[file_type] = encoding
        self.config.setdefault("imported_separators", {})[file_type] = separator
        self.config.setdefault("imported_decimal_seps", {})[file_type] = decimal_sep
        from .data_registry import (
            DataRegistry, DataSourceRecord, ImportStructureProfile)
        registry = DataRegistry.from_dict(self.config.get("data_registry", {}))
        previous = registry.get(file_type)
        profile = ImportStructureProfile.from_dict(
            structure if structure is not None
            else (previous.structure if previous else None))
        registry.register(DataSourceRecord(
            dataset_type=file_type,
            file_name=basename,
            source_path=os.path.relpath(dest, self.paths.project_dir),
            columns=list(headers or []),
            mappings=dict(mappings or {}),
            encoding=encoding,
            separator=separator,
            decimal_separator=decimal_sep,
            crs=crs or self.config.get("crs", ""),
            unit=unit or self.config.get("units", ""),
            provenance="imported",
            structure=profile))
        self.config["data_registry"] = registry.to_dict()
        self.save_config()

    def copy_imagery_assets(self, records_by_hole, source_dir: str = ""):
        """Chantier 2 — mode ``copy`` : fichiers images → ``assets/``.

        Mutates each ``CoreImageRecord.image_path`` to a relative path
        ``assets/<nom>.jpg`` when the source file is found.  Relative
        paths are resolved in the same order as the renderer: as-is,
        project dir, ``data_import/``, ``assets/`` then ``source_dir``.
        Missing sources are left untouched (the renderer later shows the
        hatched band + warning, never a blocking error).

        Returns ``(copied, failed)``.
        """
        mode = str(self.config.get("image_storage_mode", "link")).casefold()
        if mode != "copy" or not self.paths:
            return 0, []
        os.makedirs(self.paths.assets_dir, exist_ok=True)
        copied = 0
        failed = []
        bases = [self.paths.project_dir, self.paths.data_import_dir,
                 self.paths.assets_dir]
        if source_dir:
            bases.append(source_dir)
        for hole_id, records in (records_by_hole or {}).items():
            for record in (records or []):
                raw = str(getattr(record, "image_path", "") or "").strip()
                if not raw:
                    continue
                source = None
                if os.path.isabs(raw) and os.path.isfile(raw):
                    source = raw
                elif os.path.isfile(raw):
                    source = os.path.abspath(raw)
                else:
                    for base in bases:
                        candidate = os.path.join(base, str(raw))
                        if os.path.isfile(candidate):
                            source = candidate
                            break
                if not source:
                    continue
                name = self._imagery_asset_name(hole_id, record, source)
                dest = os.path.join(self.paths.assets_dir, name)
                if os.path.abspath(source) != os.path.abspath(dest):
                    try:
                        shutil.copy2(source, dest)
                    except OSError as _exc:
                        failed.append((str(hole_id), str(source), str(_exc)))
                        continue
                rel = os.path.relpath(dest, self.paths.project_dir)
                record.image_path = rel.replace(os.sep, "/")
                copied += 1
        return copied, failed

    @staticmethod
    def _imagery_asset_name(hole_id, record, source: str) -> str:
        """Stable, collision-resistant basename inside ``assets/``."""
        base = os.path.basename(source)
        name, ext = os.path.splitext(base)
        safe_hole = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(hole_id or "hole"))
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_",
                           str(name or "image")) or "image"
        f = float(getattr(record, "from_m", 0.0) or 0.0)
        t = float(getattr(record, "to_m", 0.0) or 0.0)
        suffix = ext or ".img"
        return f"{safe_hole}_{f:g}-{t:g}_{safe_name}{suffix}"

    def get_imported_file_path(self, file_type: str) -> Optional[str]:
        """Get the full path of an imported file, or None."""
        if not self.paths:
            return None
        basename = self.config.get("imported_files", {}).get(file_type, "")
        if not basename:
            return None
        full = self.paths.imported_file_path(basename)
        return full if os.path.isfile(full) else None

    # -----------------------------------------------------------------------
    # Import restoration (reopen an existing project without losing steps)
    # -----------------------------------------------------------------------
    FILE_TYPES = (
        "collar", "survey", "litho", "assays", "alterations",
        "mineralizations", "structure", "imagery",
        # v2.9.266 — la géotechnique participe à la réouverture du projet
        # comme les autres tables (copie data_import/ re-lue au reopen).
        "rqd", "recovery", "density")

    def reparse_imported_files(self) -> dict:
        """
        Re-parse every imported CSV copy stored in data_import/.
        Returns {file_type: ParseResult} for files that exist and parse
        without errors. Used to restore step 2 (and therefore step 3)
        when an existing project is reopened.
        """
        from .csv_parser import parse_csv_file
        results = {}
        learned = self.get_learned_synonyms()
        for ft in self.FILE_TYPES:
            path = self.get_imported_file_path(ft)
            if not path:
                continue
            record = self.get_data_registry().get(ft)
            structure = (
                record.structure
                if record and record.structure.is_configured else None)
            pr = parse_csv_file(
                path, ft, self.get_mappings(ft), structure=structure,
                extra_synonyms=learned)
            if not pr.errors and pr.num_rows >= 0:
                results[ft] = pr
        return results

    def has_imported_files(self) -> bool:
        return any(
            self.config.get("imported_files", {}).get(ft)
            for ft in self.FILE_TYPES
        )

    # -----------------------------------------------------------------------
    # Unified registry and open reference
    # -----------------------------------------------------------------------
    def get_data_registry(self):
        from .data_registry import DataRegistry
        return DataRegistry.from_dict(self.config.get("data_registry", {}))

    def save_import_structure(self, file_type, structure):
        """Persist a structure choice without changing the source file."""
        from .data_registry import (
            DataSourceRecord, ImportStructureProfile)
        registry = self.get_data_registry()
        record = registry.get(file_type)
        if not record:
            basename = self.config.get("imported_files", {}).get(file_type, "")
            record = DataSourceRecord(
                dataset_type=file_type,
                file_name=basename,
                source_path=(
                    os.path.join("data_import", basename) if basename else ""),
                mappings=self.get_mappings(file_type),
                encoding=self.config.get("imported_encodings", {}).get(
                    file_type, ""),
                separator=self.config.get("imported_separators", {}).get(
                    file_type, ""),
                decimal_separator=self.config.get(
                    "imported_decimal_seps", {}).get(file_type, "."))
            registry.register(record)
        record.structure = ImportStructureProfile.from_dict(structure)
        self.config["data_registry"] = registry.to_dict()
        self.save_config()
        return True

    def get_reference_repository(self):
        from .reference import ReferenceRepository
        if not self.paths or not os.path.isfile(self.paths.domains_file):
            return ReferenceRepository()
        try:
            with open(self.paths.domains_file, "r", encoding="utf-8") as stream:
                return ReferenceRepository.from_dict(json.load(stream))
        except (OSError, ValueError, TypeError):
            return ReferenceRepository()

    def save_reference_repository(self, repository):
        if not self.paths:
            return
        os.makedirs(self.paths.references_dir, exist_ok=True)
        temporary = self.paths.domains_file + ".tmp"
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(repository.to_dict(), stream, indent=2, ensure_ascii=False)
        os.replace(temporary, self.paths.domains_file)

    def discover_domain_values(self, domain_key, values, label=None,
                               kind="categorical"):
        repository = self.get_reference_repository()
        added = repository.discover(domain_key, values, label, kind)
        if domain_key == "lithology":
            from .section import suggested_litho_color
            domain = repository.domains.get("lithology")
            for entry in domain.entries.values() if domain else []:
                if entry.automatic:
                    # v2.9.74 — ne pas écraser une suggestion famille ;
                    # biblio/hash seulement si aucune famille (aide).
                    if entry.family:
                        continue
                    entry.color = suggested_litho_color(entry.raw_code)
        self.save_reference_repository(repository)
        return added

    def discover_assay_elements(self, headers):
        """Register measured fields and clean stale cross-domain auto-maps."""
        values = [str(header) for header in (headers or []) if str(header)]
        repository = self.get_reference_repository()
        added = repository.discover(
            "assay_elements", values, "Éléments mesurés",
            kind="quantitative_fields")
        domain = repository.domains.get("assay_elements")
        # v2.7.1 initially allowed every domain synonym while parsing assay
        # headers. A column such as Fe_pct could therefore create the bogus
        # automatic entry ``lithology_proportion``. Remove only known
        # structural keys that are both automatic and absent from this source.
        structural_keys = {
            "hole_id", "from", "to", "lithology", "lithology_primary",
            "lithology_secondary", "lithology_role",
            "lithology_proportion", "secondary_proportion", "alteration",
            "intensity", "mineralization_style", "minerals", "confidence",
        }
        current = set(values)
        if domain:
            for raw_code in list(domain.entries):
                entry = domain.entries[raw_code]
                structural_form = str(raw_code).strip().casefold()
                structural_form = re.sub(
                    r"[\s-]+", "_", structural_form)
                if (structural_form in structural_keys and raw_code not in current
                        and entry.automatic and entry.usage_count == 0):
                    del domain.entries[raw_code]
        self.save_reference_repository(repository)
        assay_style = self.config.get("assay_style", {})
        active_element = assay_style.get("element", "")
        if active_element and active_element not in current:
            assay_style["element"] = values[0] if values else ""
            self.config["assay_style"] = assay_style
            self.save_config()
        return added

    def resolve_category_style(self, domain_key, raw_code):
        """Resolve one shared label/symbol with geological fallback colours."""
        fallback = ""
        if domain_key == "lithology":
            from .section import suggested_litho_color
            fallback = suggested_litho_color(str(raw_code))
        return self.get_reference_repository().resolve(
            domain_key, raw_code, fallback_color=fallback)

    def migrate_minerals_tokens(self):
        """v2.7.10.3 — éclater les entrées composites du domaine « minerals ».

        Cause du « ça ne s'applique pas » : les projets créés avant la
        v2.7.9.4 contenaient une entrée par CHAÎNE brute
        (``MAGNETITE_CHALCOPYRITE``), alors que la coupe dessine par
        MINÉRAL (``MAGNETITE``, ``CHALCOPYRITE``). Éditer la ligne
        composite ne changeait donc jamais rien à l'affichage. La
        migration éclate chaque entrée composite en entrées par jeton
        (symbole hérité, normalisé aux 8 cœurs), sans écraser un jeton
        déjà existant, puis retire la composite.
        """
        if not self.paths:
            return False
        repository = self.get_reference_repository()
        domain = repository.domains.get("minerals")
        if not domain:
            return False
        import re as _re
        from .mineral_symbols import to_core_symbol
        from .reference import DomainEntry
        changed = False
        for raw_code in list(domain.entries):
            if not _re.search(r"[^A-Za-z0-9]", raw_code):
                continue
            composite = domain.entries.pop(raw_code, None)
            if composite is None:
                continue
            changed = True
            tokens = [token for token in _re.split(r"[^A-Za-z0-9]+", raw_code)
                      if token]
            for token in tokens or [raw_code]:
                entry = domain.entries.get(token)
                if entry is None:
                    entry = DomainEntry(
                        raw_code=token,
                        label=composite.label or token,
                        color=composite.color,
                        pattern="",
                        symbol_id=to_core_symbol(composite.symbol_id)
                        if composite.symbol_id else "",
                        visible=composite.visible,
                        automatic=composite.automatic,
                        description=composite.description,
                        usage_count=composite.usage_count,
                    )
                    domain.entries[token] = entry
                else:
                    # le jeton existe déjà : ne jamais écraser un choix
                    # utilisateur, juste reporter l'usage.
                    entry.usage_count = max(
                        int(entry.usage_count or 0),
                        int(composite.usage_count or 0))
                    if not entry.symbol_id and composite.symbol_id:
                        entry.symbol_id = to_core_symbol(
                            composite.symbol_id)
        if changed:
            self.save_reference_repository(repository)
        return changed

    def migrate_style_codes(self):
        """v2.7.10.5 — stabilise les projets enregistrés sous 2.7.10.2/3.

        Les styles de minéralisation stockaient alors un SYMBOLE cœur
        (« square », « cross »…) dans ``symbol_id`` ; la 2.7.10.4 les
        affichait tels quels (« SQUARE », « CROSS ») au lieu des codes
        2 lettres. La migration réécrit chaque ancien symbole en code de
        style (square → MA, cross → VN…) ; les codes libres déjà corrects
        et « none » restent intacts.
        """
        if not self.paths:
            return False
        repository = self.get_reference_repository()
        domain = repository.domains.get("mineralization_style")
        if not domain:
            return False
        from .mineral_symbols import legacy_symbol_to_style
        changed = False
        for entry in domain.entries.values():
            sid = (entry.symbol_id or "").strip()
            if not sid or sid == "none":
                continue
            mapped = legacy_symbol_to_style(sid)
            if mapped and mapped != sid.upper():
                entry.symbol_id = mapped
                changed = True
        if changed:
            self.save_reference_repository(repository)
        return changed

    def migrate_reference_styles(self):
        """Migrate explicit legacy lithology styles exactly once and safely."""
        if not self.paths:
            return False
        repository = self.get_reference_repository()
        legacy = self.config.get("litho_styles", {}) or {}
        changed = False
        from .section import suggested_litho_color
        lithology = repository.domains.get("lithology")
        for entry in lithology.entries.values() if lithology else []:
            if entry.automatic:
                # v2.9.74 — famille suggérée intacte ; sinon biblio/hash
                if entry.family:
                    continue
                expected = suggested_litho_color(entry.raw_code)
                if entry.color != expected:
                    entry.color = expected
                    changed = True
        for raw_code, legacy_style in legacy.items():
            entry = repository.get_entry("lithology", raw_code)
            if entry is None:
                repository.discover("lithology", [raw_code], "Lithologie")
                entry = repository.get_entry("lithology", raw_code)
            if entry.automatic:
                colour = (legacy_style or {}).get("color")
                pattern = (legacy_style or {}).get("pattern", "")
                if colour:
                    repository.update_entry(
                        "lithology", raw_code, color=colour,
                        pattern=pattern)
                    changed = True
        if changed or not os.path.isfile(self.paths.domains_file):
            self.save_reference_repository(repository)
        if int(self.config.get("reference_style_migration", 0) or 0) < 1:
            self.config["reference_style_migration"] = 1
            self.save_config()
        return changed

    # -----------------------------------------------------------------------
    # Section config
    # -----------------------------------------------------------------------
    def save_section_config(self, buffer: float, v_exag: float):
        """v2.7.7 — section_config ne porte que buffer + exagération :
        la visibilité des pistes vit dans section_style (source unique)."""
        self.config["section_config"] = {
            "buffer": buffer,
            "vertical_exaggeration": v_exag,
        }
        self.save_config()

    def get_section_config(self) -> dict:
        return self.config.get("section_config", {
            "buffer": 50.0,
            "vertical_exaggeration": 1.0,
        })

    def get_section_style(self) -> dict:
        style = default_section_style()
        saved = self.config.get("section_style", {})
        # v2.7.7 — la migration du chargement replie les anciens show_* de
        # section_config dans section_style : plus aucune redondance à lire.
        style.update(saved)
        # v2.9.70 elev migrate — Auto (0) donnait ~10 m ; forcer 20 m
        try:
            if float(style.get("elevation_grid_step", 20) or 0) <= 0:
                style["elevation_grid_step"] = 20.0
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Coupe : get_section_style", _exc)
            style["elevation_grid_step"] = 20.0
        # Migrate v2.4's single horizontal placement to the richer v2.5
        # anchors without breaking existing config files.
        legacy_position = saved.get("collar_label_position")
        if legacy_position and "collar_id_position" not in saved:
            style["collar_id_position"] = (
                legacy_position if legacy_position in ("left", "right")
                else "auto")
        # Upgrade the untouched v2.5 automatic defaults to the validated v2.6.2
        # top stack, while preserving any explicit user placement.
        if (saved.get("collar_id_position") == "auto"
                and saved.get("collar_info_position") == "auto"
                and float(saved.get("collar_id_offset_y", 0.0)) == 0.0
                and float(saved.get("collar_info_offset_y", 0.0)) == 0.0):
            style["collar_id_position"] = "top"
            style["collar_info_position"] = "top"
            style["collar_id_offset_y"] = 0.0
        # v2.6.2/v2.6.4 untouched default: top block with ID Y=-11.
        if (saved.get("collar_id_position") == "top"
                and saved.get("collar_info_position") == "top"
                and float(saved.get("collar_id_offset_x", 0.0)) == 0.0
                and float(saved.get("collar_info_offset_x", 0.0)) == 0.0
                and float(saved.get("collar_id_offset_y", 0.0)) == -11.0
                and float(saved.get("collar_info_offset_y", 0.0)) == 0.0):
            style["collar_id_offset_y"] = 0.0
        if saved.get("orientation_position") in ("top_left", "top_right"):
            style["orientation_position"] = saved["orientation_position"].replace(
                "top_", "bottom_")
        return style

    def save_section_style(self, **updates):
        style = self.get_section_style()
        style.update(updates)
        self.config["section_style"] = style
        self.save_config()

    def get_assay_style(self) -> dict:
        style = default_assay_style()
        saved = self.config.get("assay_style", {})
        style.update(saved)
        # Migrate the untouched pre-Jenks default while preserving explicit
        # user choices and already-saved advanced settings.
        if (saved.get("method") == "linear"
                and int(saved.get("n_classes", 5)) == 5
                and "round_breaks" not in saved):
            style["method"] = "jenks"
            style["n_classes"] = 7
            style["round_breaks"] = True
        # v2.9.92 — normalise elements / palettes (legacy element only OK)
        try:
            from .multi_assay import migrate_assay_style
            style = migrate_assay_style(style)
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Piste teneurs : get_assay_style", _exc)
            # multi_assay optionnel hors pack — garde style brut
            pass
        try:
            from .threshold_rule import migrate_threshold_payload
            style = migrate_threshold_payload(style)
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Piste teneurs : get_assay_style", _exc)
            style.setdefault("threshold_rule", {
                "enabled": False, "element": "", "operator": ">",
                "value": None, "clauses": [], "litho_filter": [],
                "color": "#00E5FF", "color_name": "cyan",
            })
            style.setdefault("threshold_rules", [])
        return style

    def save_assay_style(self, **updates):
        style = self.get_assay_style()
        style.update(updates)
        try:
            from .threshold_rule import migrate_threshold_payload
            style = migrate_threshold_payload(style)
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Piste teneurs : save_assay_style", _exc)
            # module seuil indisponible — garde brut
            pass
        self.config["assay_style"] = style
        self.save_config()
    # -----------------------------------------------------------------------
    # Litho styles
    # -----------------------------------------------------------------------
    def get_litho_styles(self) -> dict:
        """Return a compatibility style mapping resolved from the reference."""
        repository = self.get_reference_repository()
        domain = repository.domains.get("lithology")
        if domain and domain.entries:
            from .section import suggested_litho_color
            styles = {}
            for code in domain.entries:
                fallback = suggested_litho_color(code)
                resolved = repository.resolve(
                    "lithology", code, fallback_color=fallback)
                styles[code] = {
                    "color": resolved.color,
                    "pattern": resolved.pattern,
                    "label": resolved.label,
                    "visible": resolved.visible,
                }
            return styles
        return self.config.get("litho_styles", {})

    # -----------------------------------------------------------------------
    # Sections persistence
    # -----------------------------------------------------------------------
    def get_next_section_display_name(self) -> str:
        """Return the first free visible Section NNN name.

        Internal IDs remain monotonic and are never reused. Only this display
        label fills gaps left by deleted sections.
        """
        used = set()
        for section in self.config.get("sections", []):
            match = re.fullmatch(
                r"Section\s+(\d+)", str(section.get("name", "")).strip(),
                flags=re.IGNORECASE)
            if match:
                used.add(int(match.group(1)))
        number = 1
        while number in used:
            number += 1
        return f"Section {number:03d}"

    def save_section(self, x1, y1, x2, y2, name, direction, azimuth, length, buffer):
        """Save a section line to config.json."""
        if "sections" not in self.config:
            self.config["sections"] = []
        sid = self.config.get("next_section_id", 1)
        section = {
            "id": sid, "name": name,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "direction": direction, "azimuth": azimuth,
            "length": length, "buffer": buffer,
        }
        self.config["sections"].append(section)
        self.config["next_section_id"] = sid + 1
        self.save_config()
        return sid

    def get_sections(self) -> list[dict]:
        return self.config.get("sections", [])

    def update_section(self, section_id: int, **updates) -> bool:
        """Update persisted section metadata (name, buffer, etc.)."""
        # v2.9.179 — excluded_holes : exclusions de forages par coupe
        # (proposition validée — jamais de perte des clés existantes).
        allowed = {"name", "buffer", "direction", "azimuth", "length",
                   "excluded_holes",
                   "x1", "y1", "x2", "y2"}   # 338 : flip P1/P2
        for section in self.config.get("sections", []):
            if section.get("id") == section_id:
                for key, value in updates.items():
                    if key in allowed:
                        section[key] = value
                self.save_config()
                return True
        return False

    def rename_section(self, section_id: int, new_name: str) -> bool:
        new_name = (new_name or "").strip()
        return bool(new_name) and self.update_section(section_id, name=new_name)

    def set_current_section(self, section_id: int = None):
        self.config["current_section_id"] = section_id
        self.save_config()

    def get_current_section_id(self):
        return self.config.get("current_section_id")

    def delete_section(self, section_id: int):
        self.config["sections"] = [
            s for s in self.config.get("sections", []) if s.get("id") != section_id
        ]
        if self.config.get("current_section_id") == section_id:
            self.config["current_section_id"] = None
        self.save_config()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    @staticmethod
    def _sanitise_name(name: str) -> str:
        """Sanitise a project name for use as a directory name."""
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return safe or "unnamed"
