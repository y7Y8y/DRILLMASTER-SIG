"""Unified, serialisable registry of project data sources and schemas."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DatasetDefinition:
    key: str
    label: str
    kind: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()


DATASET_DEFINITIONS = {
    "collar": DatasetDefinition(
        "collar", "Collets", "points",
        ("hole_id", "collar_x", "collar_y", "collar_z", "depth"),
        ("azimuth", "dip")),
    "survey": DatasetDefinition(
        "survey", "Déviations", "stations",
        ("hole_id", "depth", "azimuth", "dip")),
    "litho": DatasetDefinition(
        "litho", "Lithologie", "intervals",
        ("hole_id", "from", "to", "lithology"),
        ("lithology_role", "lithology_proportion")),
    "assays": DatasetDefinition(
        "assays", "Teneurs", "numeric_intervals",
        ("hole_id", "from", "to")),
    "alterations": DatasetDefinition(
        "alterations", "Altérations", "categorical_intervals",
        ("hole_id", "from", "to", "alteration"), ("intensity",)),
    "mineralizations": DatasetDefinition(
        "mineralizations", "Minéralisations observées", "categorical_intervals",
        ("hole_id", "from", "to", "mineralization_style"),
        ("minerals", "intensity", "confidence")),
    "structure": DatasetDefinition(
        "structure", "Structures observées", "structural_measurements",
        ("hole_id", "depth", "type"),
        ("dip", "dip_direction", "alpha", "beta", "confidence", "comment")),
    "topography": DatasetDefinition(
        "topography", "Topographie", "surface_source", ()),
    "structures": DatasetDefinition(
        "structures", "Structures", "structural_data", ("hole_id",)),
    "rqd": DatasetDefinition(
        "rqd", "RQD", "numeric_intervals",
        ("hole_id", "from", "to", "value"), ("comment",)),
    "recovery": DatasetDefinition(
        "recovery", "Récupération", "numeric_intervals",
        ("hole_id", "from", "to", "value"), ("comment",)),
    "density": DatasetDefinition(
        "density", "Densité", "numeric_points_or_intervals",
        ("hole_id", "value"),
        ("from", "to", "depth", "unit", "comment")),
}


@dataclass
class ComponentColumn:
    """One component encoded in one or more columns of a wide source."""

    code_column: str = ""
    role: str = ""
    proportion_column: str = ""

    def to_dict(self):
        return asdict(self)

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
class ImportStructureProfile:
    """How logical records/components are represented by a source file.

    ``standard`` means one value per row, ``wide_components`` means one row
    with N component columns, ``long_components`` means repeated rows with an
    explicit role column, and ``delimited_components`` means N values in one
    cell.  The profile records an interpretation; it never edits source cells.
    """

    mode: str = "standard"
    component_columns: list[ComponentColumn] = field(default_factory=list)
    code_column: str = ""
    role_column: str = ""
    proportion_column: str = ""
    delimiter: str = ""
    first_component_role: str = ""
    proportion_unit: str = "percent"  # percent | fraction | unknown
    confirmed: bool = False
    confidence: float = 0.0

    # v2.7.11.0 — directive écran du 20/08/2026 : le plugin ne gère QUE le
    # format LARGE ; « long_components » est retiré (legacy refusé par la
    # validation avec la règle écrite).
    MODES = {"standard", "wide_components", "delimited_components"}

    def __post_init__(self):
        if self.mode not in self.MODES:
            self.mode = "standard"
        self.component_columns = [
            ComponentColumn.from_dict(value)
            for value in (self.component_columns or [])
        ]
        if self.proportion_unit not in ("percent", "fraction", "unknown"):
            self.proportion_unit = "unknown"

    @property
    def is_configured(self):
        return bool(
            self.confirmed or self.code_column or self.role_column
            or self.proportion_column or self.component_columns
            or self.delimiter)

    def to_dict(self):
        data = asdict(self)
        data["component_columns"] = [
            component.to_dict() for component in self.component_columns]
        return data

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, cls):
            return data
        allowed = set(cls.__dataclass_fields__)
        payload = {
            key: value for key, value in (data or {}).items()
            if key in allowed
        }
        payload["component_columns"] = [
            ComponentColumn.from_dict(value)
            for value in payload.get("component_columns", [])
        ]
        return cls(**payload)


@dataclass
class DataSourceRecord:
    dataset_type: str
    file_name: str = ""
    source_path: str = ""
    columns: list[str] = field(default_factory=list)
    mappings: dict[str, str] = field(default_factory=dict)
    encoding: str = ""
    separator: str = ""
    decimal_separator: str = "."
    crs: str = ""
    unit: str = ""
    provenance: str = "imported"
    imported_at: str = field(default_factory=lambda: datetime.now().isoformat())
    structure: ImportStructureProfile = field(default_factory=ImportStructureProfile)

    def __post_init__(self):
        self.structure = ImportStructureProfile.from_dict(self.structure)

    def to_dict(self):
        data = asdict(self)
        data["structure"] = self.structure.to_dict()
        return data

    @classmethod
    def from_dict(cls, data):
        allowed = set(cls.__dataclass_fields__)
        payload = {
            key: value for key, value in (data or {}).items()
            if key in allowed
        }
        payload["structure"] = ImportStructureProfile.from_dict(
            payload.get("structure"))
        return cls(**payload)


class DataRegistry:
    """Project-level source catalogue. Unknown dataset types remain accepted."""

    def __init__(self, sources=None):
        self._sources: dict[str, DataSourceRecord] = {}
        for key, value in (sources or {}).items():
            record = (value if isinstance(value, DataSourceRecord)
                      else DataSourceRecord.from_dict(value))
            if not record.dataset_type:
                record.dataset_type = key
            self._sources[key] = record

    def definition(self, dataset_type):
        return DATASET_DEFINITIONS.get(dataset_type)

    def register(self, record: DataSourceRecord):
        self._sources[record.dataset_type] = record
        return record

    def get(self, dataset_type):
        return self._sources.get(dataset_type)

    def remove(self, dataset_type):
        return self._sources.pop(dataset_type, None)

    def dataset_types(self):
        return sorted(self._sources)

    def records(self):
        return [self._sources[key] for key in self.dataset_types()]

    def to_dict(self):
        return {key: record.to_dict() for key, record in self._sources.items()}

    @classmethod
    def from_dict(cls, data):
        return cls(data or {})
