"""
DrillMaster — Data Model
========================
Defines the core data structures used throughout the plugin.
Pure Python, no QGIS dependency — testable standalone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Canonical field names recognised by the fuzzy header matcher.
# Each entry maps a canonical name to a list of known synonyms (lowercased).
# ---------------------------------------------------------------------------
FIELD_SYNONYMS: dict[str, list[str]] = {
    # Collar
    "hole_id": [
        "hole_id", "holeid", "hole", "drillhole", "dh_id", "dhid",
        "id", "forage", "trou", "name", "borehole_id", "borehole",
        "collar_id", "drill_hole",
    ],
    "collar_x": [
        "collar_x", "x", "easting", "x_survey", "x_collar", "east",
        "est", "collar_east", "xcoord", "x_coord", "longitude_x",
        "pos_x", "position_x",
    ],
    "collar_y": [
        "collar_y", "y", "northing", "y_survey", "y_collar", "north",
        "nord", "collar_north", "ycoord", "y_coord", "latitude_y",
        "pos_y", "position_y",
    ],
    "collar_z": [
        "collar_z", "z", "elevation", "z_survey", "z_collar", "elev",
        "altitude", "rl", "collar_rl", "zcoord", "z_coord",
        "collar_elevation", "height",
    ],
    "depth": [
        "depth", "total_depth", "max_depth", "eoh", "end_depth",
        "profondeur", "profondeur_totale", "final_depth", "hole_depth",
        "totaldepth", "maxdepth",
    ],
    # Survey
    "azimuth": [
        "azimuth", "azimut", "az", "dir", "direction", "bearing",
        "azi", "azimuth_deg", "compass",
    ],
    "dip": [
        "dip", "plunge", "pendage", "inclinaison", "inclination",
        "dip_deg", "zenith", "dip_angle",
    ],
    # Intervals (litho / assays / alterations)
    "from": [
        "from", "from_depth", "depth_from", "debut", "depuis",
        "start", "start_depth", "from_m", "depth1", "top",
    ],
    "to": [
        "to", "to_depth", "depth_to", "fin", "jusqu",
        "end", "end_depth", "to_m", "depth2", "bottom",
    ],
    # Lithology
    "lithology": [
        "lithology", "litho", "rock", "roche", "code_litho",
        "lithology_code", "lith_code", "geology", "lithologie",
        "rock_type", "lithology_desc", "description",
    ],
    "lithology_primary": [
        "lithology_primary", "litho_primary", "primary_lithology",
        "lithologie_principale", "litho_principale", "roche_principale",
        "main_lithology", "main_rock", "litho1", "lithology1",
    ],
    "lithology_secondary": [
        "lithology_secondary", "litho_secondary", "secondary_lithology",
        "lithologie_secondaire", "litho_secondaire", "roche_secondaire",
        "second_lithology", "secondary_rock", "litho2", "lithology2",
    ],
    "lithology_role": [
        "lithology_role", "litho_role", "role_lithology", "role_litho",
        "role_lithologie", "role", "component_role", "type_composant",
    ],
    "lithology_proportion": [
        "lithology_proportion", "litho_proportion", "proportion_lithology",
        "proportion_litho", "proportion", "pourcentage", "percent",
        "percentage", "pct", "component_pct",
    ],
    "secondary_proportion": [
        "secondary_proportion", "secondary_pct", "secondary_percent",
        "proportion_secondaire", "pourcentage_secondaire", "pct_secondaire",
        "litho2_pct", "lithology2_pct",
    ],
    # Alteration
    "alteration": [
        "alteration", "alter", "alteration_type", "alteration_code",
        "alt", "alt_code", "alt_type", "alteration_style",
        "alteration_desc",
    ],
    "intensity": [
        "intensity", "intensite", "intensité", "alteration_intensity",
        "mineralization_intensity", "intens", "strength", "rank",
    ],
    # Observed mineralization
    "mineralization_style": [
        "mineralization_style", "mineralisation_style",
        "style_mineralisation", "style_mineralization", "mineralisation",
        "mineralization", "min_style", "ore_style",
    ],
    "minerals": [
        # v2.7.11.7 — retour écran : « Min »/« Mineral » seuls (sans
        # chiffre) sont le canonique minéraux.  AVANT, « Min » seul était
        # fuzzy-matché sur « to » (Levenshtein 0,67 ≥ seuil) — colonne de
        # minéraux lue comme profondeur de fin d'intervalle !
        # Les synonymes courts sont exacts (garde len<=3 ci-dessous), pas
        # de raccourci flou.
        "minerals", "mineraux", "minéraux", "mineral_assemblage",
        "assemblage_mineral", "mineralogy", "mineralogie",
        "min", "mineral",
    ],
    "confidence": [
        "confidence", "confiance", "quality", "qualite", "fiabilite",
    ],
    # Structure measurements (point-wise, v2.9.258)
    "type": [
        "type", "structure_type", "geol_type", "type_de_structure",
        "structure", "measurement_type", "type_mesure",
        "discontinuity_type", "discontinuite", "discontinuity",
    ],
    "dip_direction": [
        "dip_direction", "dipdirection", "direction_dip", "dir_dip",
        "dip_azimuth", "azimuth_dip", "pendage_direction",
        "sens_pendage", "direction_pendage",
    ],
    "alpha": [
        "alpha", "alpha_angle", "angle_alpha", "alpha_deg",
    ],
    "beta": [
        "beta", "beta_angle", "angle_beta", "beta_deg",
    ],
    # Imagery (v2.9.262) — path and optional material label.
    "image_path": [
        "image_path", "imagepath", "photo_path", "photopath", "path",
        "file", "photo", "photo_scan", "scan", "image", "core_photo",
        "photo_file", "image_file", "scan_path", "fichier_image",
        "chemin_image", "photo_image",
    ],
    "material": [
        "material", "matériau", "matiere", "matière", "sample_type",
        "sampletype", "method", "methode", "méthode", "nature_materiau",
        "type_materiau", "type_materiel", "drill_method", "litho_type",
    ],
    "comment": [
        "comment", "comments", "commentaire", "commentaires",
        "note", "notes", "comment_text", "observation",
        "observations",
    ],
    "orientation": [
        "orientation", "orient", "photo_orientation", "position",
    ],
    # Geotech (RQD / recovery / density, v2.9.264) — numerical value column.
    "value": [
        "value", "val", "valeur", "measurement", "mesure", "result",
        "resultat", "résultat",
    ],
    "unit": [
        "unit", "units", "unite", "unité", "unit_of_measure",
        "measurement_unit",
    ],
    "kind": [
        "kind", "parameter", "parametre", "paramètre", "indicator",
        "indicateur", "code_geotech",
    ],
    # Assays — these are dynamic, handled separately
}

# Fields expected for each file type
REQUIRED_FIELDS: dict[str, list[str]] = {
    "collar":   ["hole_id", "collar_x", "collar_y", "collar_z", "depth"],
    "survey":   ["hole_id", "depth", "azimuth", "dip"],
    "litho":    ["hole_id", "from", "to", "lithology"],
    "assays":   ["hole_id", "from", "to"],
    "alterations": ["hole_id", "from", "to", "alteration"],
    "mineralizations": ["hole_id", "from", "to", "mineralization_style"],
    "structure": ["hole_id", "depth", "type"],
    "imagery": ["hole_id", "from", "to", "image_path"],
    "rqd": ["hole_id", "from", "to", "value"],
    "recovery": ["hole_id", "from", "to", "value"],
    # densité : profondeur OU bornes FROM/TO (contrôlé ligne à ligne par
    # validate_geotech) — le badge ne bloque pas un fichier par points
    # sur l'absence de la colonne depth.
    "density": ["hole_id", "value"],
}

# Numeric fields per file type
NUMERIC_FIELDS: dict[str, list[str]] = {
    "collar":      ["collar_x", "collar_y", "collar_z", "depth", "azimuth", "dip"],
    "survey":      ["depth", "azimuth", "dip"],
    "litho":       ["from", "to"],
    "assays":      ["from", "to"],
    "alterations": ["from", "to"],
    "mineralizations": ["from", "to"],
    "structure": ["depth", "dip", "dip_direction", "alpha", "beta"],
    "imagery": ["from", "to"],
    "rqd": ["from", "to", "value"],
    "recovery": ["from", "to", "value"],
    "density": ["from", "to", "depth", "value"],
}


@dataclass
class CollarRecord:
    """Single collar (hole collar) entry."""
    hole_id: str
    x: float
    y: float
    z: float
    max_depth: float
    azimuth: Optional[float] = None   # initial azimuth from collar file (optional)
    dip: Optional[float] = None       # initial dip from collar file (optional)
    hole_type: Optional[str] = None   # v2.9.289 — RC/DD/AUGER/PUITS/CUSTOM…


@dataclass
class SurveyRecord:
    """Single survey station."""
    hole_id: str
    depth: float
    azimuth: float
    dip: float


@dataclass
class StructureRecord:
    """One down-hole structure measurement (point-wise, v2.9.258).

    ``dip``/``dip_direction`` and ``alpha``/``beta`` are the two accepted
    ways to describe a structure plane.  Either the first pair or the
    second pair should be complete; an incomplete or absent pair is
    reported as a warning, never silently corrected.
    """
    hole_id: str
    depth: float
    type: str = ""
    dip: Optional[float] = None
    dip_direction: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    confidence: Optional[str] = None  # qualitative (BONNE/MOYENNE/FAIBLE…)
    comment: str = ""
    source_line: int = 0

    def to_dict(self):
        return {
            "hole_id": self.hole_id,
            "depth": self.depth,
            "type": self.type,
            "dip": self.dip,
            "dip_direction": self.dip_direction,
            "alpha": self.alpha,
            "beta": self.beta,
            "confidence": self.confidence,
            "comment": self.comment,
            "source_line": self.source_line,
        }

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, cls):
            return data
        allowed = set(cls.__dataclass_fields__)
        return cls(**{
            key: value for key, value in (data or {}).items()
            if key in allowed
        })


# v2.9.262 — Imagerie de trou : photos / scans le long d'un ouvrage de
# type trou (DD, RC, Auger, puits droit).  Le champ ``material`` est une
# étiquette informationnelle ("core" | "rc" | "auger" | "pit" | "other"),
# jamais une contrainte d'affichage : un matériau inconnu reste accepté.
# ``image_path`` est TOUJOURS le chemin canonique ; il est stocké tel que
# fourni (relatif ou absolu) et résolu à l'affichage (voir CHANTIER 2).
CORE_IMAGE_MATERIALS = ("core", "rc", "auger", "pit", "other")
CORE_IMAGE_DEFAULT_MATERIAL = ""


@dataclass
class CoreImageRecord:
    """An imagery interval: a photo/scan covering ``from_m``..``to_m``.

    A cutting-box of 15 m can be described either as:
      - one row (from=0, to=15, path=cuts/bx15.jpg), or
      - fifteen rows (0–1, 1–2, …, 14–15, one path per metre).
    The renderer tiles the rows along depth in the order given; it never
    splits or guesses an interval.
    """
    hole_id: str
    from_m: float
    to_m: float
    image_path: str = ""
    material: Optional[str] = None
    orientation: Optional[str] = None
    comment: str = ""
    source_line: int = 0

    @property
    def span(self) -> float:
        return max(0.0, float(self.to_m) - float(self.from_m))

    @property
    def span_text(self) -> str:
        return f"{self.from_m:g}–{self.to_m:g}"

    @property
    def material_label(self) -> str:
        """Clé normale : core/rc/auger/pit/other ; vide → '—'."""
        value = str(self.material or "").strip().casefold()
        if value in CORE_IMAGE_MATERIALS:
            return value
        return "other" if value else ""

    def to_dict(self):
        return {
            "hole_id": self.hole_id,
            "from_m": self.from_m,
            "to_m": self.to_m,
            "image_path": self.image_path,
            "material": self.material,
            "orientation": self.orientation,
            "comment": self.comment,
            "source_line": self.source_line,
        }

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, cls):
            return data
        allowed = set(cls.__dataclass_fields__)
        return cls(**{
            key: value for key, value in (data or {}).items()
            if key in allowed
        })


@dataclass
class GeotechRecord:
    """One geotechnical measurement (RQD / recovery / density, v2.9.264).

    ``kind`` discrimine l'indicateur : ``rqd``, ``recovery`` ou
    ``density``.  Les RQD et récupération sont des intervalles
    (``from_m``/``to_m``) ; la densité est PONCTUELLE par défaut
    (``depth``) mais accepte aussi des bornes si ``from``/``to`` sont
    présents et ``depth`` absent.  ``value`` est toujours numérique ;
    ``unit`` est affichée telle quelle (jamais convertie).
    """
    hole_id: str
    kind: str = ""           # rqd | recovery | density
    from_m: Optional[float] = None
    to_m: Optional[float] = None
    depth: Optional[float] = None
    value: float = 0.0
    unit: str = ""
    comment: str = ""
    source_line: int = 0

    @property
    def is_interval(self) -> bool:
        return self.from_m is not None and self.to_m is not None

    @property
    def is_point(self) -> bool:
        return self.depth is not None and not self.is_interval

    @property
    def span(self) -> float:
        if self.is_interval:
            return max(0.0, float(self.to_m) - float(self.from_m))
        return 0.0

    def between(self, depth: float) -> bool:
        if self.is_interval:
            return (self.from_m - 1e-7 <= float(depth)
                    <= self.to_m + 1e-7)
        if self.depth is not None:
            return abs(float(self.depth) - float(depth)) < 1e-6
        return False

    def to_dict(self):
        return {
            "hole_id": self.hole_id,
            "kind": self.kind,
            "from_m": self.from_m,
            "to_m": self.to_m,
            "depth": self.depth,
            "value": self.value,
            "unit": self.unit,
            "comment": self.comment,
            "source_line": self.source_line,
        }

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, cls):
            return data
        allowed = set(cls.__dataclass_fields__)
        return cls(**{
            key: value for key, value in (data or {}).items()
            if key in allowed
        })


@dataclass
class LithologyComponent:
    """One raw lithological component attached to an interval.

    ``raw_role`` and ``raw_proportion`` preserve source semantics while the
    canonical fields support validation/rendering.  No role or proportion is
    invented when the source does not provide one.

    ``intensity`` (v2.7.11.1 — CM-03) : intensité brute lue dans la colonne
    appariée par suffixe (``Int_k ≡ colonne k``, altérations en
    organisation large).  Chaîne brute, jamais jugée ni transformée ;
    vide = repli sur l'intensité d'intervalle (AM-03).
    """

    raw_code: str
    role: str = ""
    raw_role: str = ""
    proportion: Optional[float] = None
    raw_proportion: str = ""
    proportion_unit: str = "unknown"
    source_line: int = 0
    source_column: int = -1
    source_header: str = ""
    intensity: str = ""

    def to_dict(self):
        return {
            "raw_code": self.raw_code,
            "role": self.role,
            "raw_role": self.raw_role,
            "proportion": self.proportion,
            "raw_proportion": self.raw_proportion,
            "proportion_unit": self.proportion_unit,
            "source_line": self.source_line,
            "source_column": self.source_column,
            "source_header": self.source_header,
            "intensity": self.intensity,
        }

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, cls):
            return data
        allowed = set(cls.__dataclass_fields__)
        return cls(**{
            key: value for key, value in (data or {}).items()
            if key in allowed
        })


@dataclass
class IntervalRecord:
    """Generic down-hole interval (lithology, teneur, altération, etc.)."""
    hole_id: str
    from_depth: float
    to_depth: float
    attributes: dict = field(default_factory=dict)
    source_line: int = 0
    components: list[LithologyComponent] = field(default_factory=list)

    def __post_init__(self):
        self.components = [
            LithologyComponent.from_dict(value)
            for value in (self.components or [])
        ]

    @property
    def primary_component(self) -> Optional[LithologyComponent]:
        """Return an explicit primary component, or the sole component."""
        for component in self.components:
            if component.role == "primary":
                return component
        if len(self.components) == 1:
            return self.components[0]
        return None

    def sync_primary_attribute(self):
        """Expose the primary code through the legacy ``lithology`` key."""
        component = self.primary_component
        if component is not None:
            self.attributes["lithology"] = component.raw_code
        return component


@dataclass
class TrajectoryPoint:
    """A 3D point along a drillhole trajectory."""
    x: float
    y: float
    z: float
    depth: float


@dataclass
class DrillHole:
    """Aggregated drillhole data after import and geometrisation."""
    hole_id: str
    collar: CollarRecord
    survey: list[SurveyRecord] = field(default_factory=list)
    litho: list[IntervalRecord] = field(default_factory=list)
    assays: list[IntervalRecord] = field(default_factory=list)
    alterations: list[IntervalRecord] = field(default_factory=list)
    mineralizations: list[IntervalRecord] = field(default_factory=list)
    structure: list[StructureRecord] = field(default_factory=list)
    imagery: list[CoreImageRecord] = field(default_factory=list)
    geotech: list[GeotechRecord] = field(default_factory=list)
    trajectory: list[TrajectoryPoint] = field(default_factory=list)

    @property
    def total_depth(self) -> float:
        return self.collar.max_depth

    @property
    def collar_xyz(self) -> tuple[float, float, float]:
        return (self.collar.x, self.collar.y, self.collar.z)

    @property
    def num_litho_intervals(self) -> int:
        return len(self.litho)

    @property
    def trajectory_length(self) -> float:
        """Total 3D length of the trajectory."""
        total = 0.0
        for i in range(1, len(self.trajectory)):
            p0 = self.trajectory[i - 1]
            p1 = self.trajectory[i]
            total += (
                (p1.x - p0.x) ** 2
                + (p1.y - p0.y) ** 2
                + (p1.z - p0.z) ** 2
            ) ** 0.5
        return total
