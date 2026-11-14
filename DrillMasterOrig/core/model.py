"""
DrillMaster ORIG — modèle de données (pur).

Les enregistrements SOURCES sont gelés : une donnée importée ne se mute
pas, elle se remplace (traçabilité, RÈGLE ABSOLUE n°5). La trajectoire
est un ARTEFACT calculé porté par le trou : elle se recalcule, elle ne
s'édite pas.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Collar:
    hole_id: str
    x: float
    y: float
    elevation: float
    total_depth: float
    source_row: int = -1


@dataclass(frozen=True, slots=True)
class SurveyStation:
    hole_id: str
    depth: float
    azimuth: float
    dip: float
    source_row: int = -1


@dataclass(frozen=True, slots=True)
class Interval:
    hole_id: str
    from_depth: float
    to_depth: float
    domain: str
    code: str
    source_row: int = -1

    @property
    def thickness(self) -> float:
        return self.to_depth - self.from_depth


@dataclass(slots=True)
class DrillHole:
    """Agrégat mutable : sources gelées + artefacts calculés."""

    collar: Collar
    surveys: list[SurveyStation] = field(default_factory=list)
    intervals: dict[str, list[Interval]] = field(default_factory=dict)
    trajectory: list["TrajectoryPoint"] = field(default_factory=list)

    @property
    def hole_id(self) -> str:
        return self.collar.hole_id


@dataclass(frozen=True, slots=True)
class TrajectoryPoint:
    """Point calculé de la trajectoire (depth_to_xyz)."""

    depth: float
    x: float
    y: float
    z: float
    azimuth: float
    dip: float


def sort_surveys(surveys: list[SurveyStation]) -> list[SurveyStation]:
    """Stations triées par profondeur (le CSV source est rarement trié)."""
    return sorted(surveys, key=lambda s: s.depth)
