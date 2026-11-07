"""
DrillMaster — Core package.
"""

from .data_model import (
    CollarRecord, SurveyRecord, IntervalRecord, StructureRecord,
    TrajectoryPoint, DrillHole,
    FIELD_SYNONYMS, REQUIRED_FIELDS, NUMERIC_FIELDS,
)

from .csv_parser import (
    parse_csv_file, ParseResult,
    detect_encoding, detect_separator, fuzzy_match_header,
    parse_number, levenshtein,
)

from .validation import (
    ValidationResult, ImportBundle,
    validate_collar, validate_survey, validate_intervals,
    validate_structure, validate_imagery,
    auto_survey_for_vertical,
)

from .data_model import CoreImageRecord

from .geometry import (
    compute_trajectory, validate_trajectory,
    depth_to_xyz, build_drillhole,
)
