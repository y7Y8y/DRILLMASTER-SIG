"""
DrillMaster — Unified Selection Model (v2.9.136)
=================================================
Common selection model shared across Coupe 2D, Vue 3D, and QGIS.
Canonical format: HOLE_ID:FROM-TO (e.g. DDH-024:125.40-137.80).
Pure Python, no QGIS dependency — testable standalone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class IntervalSelection:
    """Represents a universal downhole interval selection across any domain."""

    hole_id: str
    from_m: float
    to_m: float
    domain: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    source: str = ""  # "section_2d", "view_3d", "interpretation", "qgis", "manual"
    coords_from: Optional[tuple[float, float, float]] = None  # (X, Y, Z) real world top
    coords_to: Optional[tuple[float, float, float]] = None    # (X, Y, Z) real world bottom

    @property
    def key(self) -> str:
        """Canonical identifier for the interval: HOLE_ID:FROM-TO."""
        return f"{self.hole_id}:{self.from_m:.2f}-{self.to_m:.2f}"

    @property
    def length(self) -> float:
        """Apparent drill length of the interval in project units."""
        return max(0.0, self.to_m - self.from_m)

    def contains_depth(self, depth: float) -> bool:
        """Return True if depth falls within [from_m, to_m]."""
        return self.from_m <= depth <= self.to_m

    @staticmethod
    def parse_key(key: str) -> tuple[str, float, float]:
        """Parse a canonical key string 'HOLE_ID:FROM-TO' into (hole_id, from_m, to_m)."""
        match = re.match(r"^([^:]+):([0-9\.\,]+)-([0-9\.\,]+)$", key.strip())
        if not match:
            raise ValueError(f"Invalid canonical interval key format: '{key}' (expected 'HOLE_ID:FROM-TO')")
        hole_id = match.group(1).strip()
        from_m = float(match.group(2).replace(",", "."))
        to_m = float(match.group(3).replace(",", "."))
        return hole_id, from_m, to_m

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (backward compatible with legacy dicts)."""
        return {
            "hole_id": self.hole_id,
            "from": self.from_m,
            "to": self.to_m,
            "from_m": self.from_m,
            "to_m": self.to_m,
            "domain": self.domain,
            "attributes": dict(self.attributes),
            "source": self.source,
            "coords_from": self.coords_from,
            "coords_to": self.coords_to,
            "key": self.key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | IntervalSelection) -> IntervalSelection:
        """Deserialize from dictionary or return instance directly."""
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")

        hole_id = str(data.get("hole_id") or "")
        from_m = float(data.get("from_m") if data.get("from_m") is not None else data.get("from", 0.0))
        to_m = float(data.get("to_m") if data.get("to_m") is not None else data.get("to", 0.0))
        domain = str(data.get("domain") or "")
        attributes = dict(data.get("attributes") or {})
        source = str(data.get("source") or "")
        coords_from = data.get("coords_from")
        if coords_from is not None:
            coords_from = tuple(float(v) for v in coords_from)
        coords_to = data.get("coords_to")
        if coords_to is not None:
            coords_to = tuple(float(v) for v in coords_to)

        return cls(
            hole_id=hole_id,
            from_m=from_m,
            to_m=to_m,
            domain=domain,
            attributes=attributes,
            source=source,
            coords_from=coords_from,
            coords_to=coords_to,
        )


@dataclass
class EntitySelection:
    """Generic representation of an interpreted geological entity (domain, zone, structure, etc.)."""

    entity_id: str  # Unique ID: "DOM-01", "ZM-01", "F-01"
    name: str = ""
    entity_type: str = "generic"  # "domain", "zone", "structure", "surface", "volume", "generic"
    confidence: Optional[float] = None  # Optional confidence score (e.g. 0.87)
    contributing_intervals: list[IntervalSelection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = self.entity_id
        # Normalize intervals
        normalized = []
        for item in self.contributing_intervals:
            if isinstance(item, dict):
                normalized.append(IntervalSelection.from_dict(item))
            elif isinstance(item, IntervalSelection):
                normalized.append(item)
        self.contributing_intervals = normalized

    @property
    def hole_ids(self) -> list[str]:
        """Sorted list of unique drillhole IDs contributing to this entity."""
        return sorted({i.hole_id for i in self.contributing_intervals if i.hole_id})

    @property
    def total_drill_length(self) -> float:
        """Sum of interval lengths contributing to this entity."""
        return sum(i.length for i in self.contributing_intervals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type,
            "confidence": self.confidence,
            "contributing_intervals": [i.to_dict() for i in self.contributing_intervals],
            "metadata": dict(self.metadata),
            "source": self.source,
            "hole_ids": self.hole_ids,
            "total_drill_length": self.total_drill_length,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | EntitySelection) -> EntitySelection:
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")

        conf = data.get("confidence")
        conf_val = float(conf) if conf is not None else None

        return cls(
            entity_id=str(data.get("entity_id") or ""),
            name=str(data.get("name") or ""),
            entity_type=str(data.get("entity_type") or "generic"),
            confidence=conf_val,
            contributing_intervals=data.get("contributing_intervals") or [],
            metadata=dict(data.get("metadata") or {}),
            source=str(data.get("source") or ""),
        )
