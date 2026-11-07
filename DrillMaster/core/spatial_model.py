"""
DrillMaster — Unified Spatial Model (v2.9.136)
==============================================
Central spatial data repository and coordinate authority shared between
Contrôle (Step 3/4) and Visualisation (Coupe 2D, Vue 3D).

COORDINATE CONVENTIONS (RÈGLE ABSOLUE):
  - All coordinates in SpatialModel are REAL-WORLD coordinates in the project projected CRS.
  - X: Easting (m or ft, strictly positive/projected).
  - Y: Northing (m or ft, strictly positive/projected).
  - Z: Elevation / RL (positive upwards, ground above sea level).
  - Depth: Downhole distance from collar (m or ft, strictly >= 0).
  - Azimuth: Degrees from North [0°, 360°[.
  - Dip: Degrees from horizontal (0° = horizontal, 90° = vertical downwards).
  - Exaggeration (vertical exaggeration) is purely a rendering parameter in views;
    it MUST NEVER alter the source coordinates stored in this spatial model.

Pure Python, no QGIS dependency — testable standalone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from .data_model import CollarRecord, DrillHole, IntervalRecord, SurveyRecord, TrajectoryPoint
from .geometry import depth_to_xyz
from .selection_model import IntervalSelection


@dataclass
class SpatialCoordinateSystem:
    """Explicitly documents and locks the project spatial reference system conventions."""

    crs_authid: str = "EPSG:32630"
    crs_description: str = "WGS 84 / UTM zone 30N"
    units: str = "meters"  # "meters" or "feet"
    axis_x: str = "Easting (X)"
    axis_y: str = "Northing (Y)"
    axis_z: str = "Elevation (Z, positive up)"
    depth_direction: str = "Downhole distance from collar"


class SpatialModel:
    """Central spatial repository for 3D drillhole geometries and spatial queries.

    Does NOT contain geological interpretation logic. Prepares common spatial
    geometries for 2D sections and the 3D view.
    """

    def __init__(
        self,
        drillholes: list[DrillHole] | dict[str, DrillHole] | None = None,
        coordinate_system: Optional[SpatialCoordinateSystem] = None,
    ):
        self.crs_info = coordinate_system or SpatialCoordinateSystem()
        self._drillholes: dict[str, DrillHole] = {}
        if drillholes:
            self.set_drillholes(drillholes)

    def set_drillholes(self, drillholes: list[DrillHole] | dict[str, DrillHole]):
        """Populate the spatial model with validated drillhole objects."""
        if isinstance(drillholes, dict):
            self._drillholes = dict(drillholes)
        elif isinstance(drillholes, (list, tuple)):
            self._drillholes = {h.hole_id: h for h in drillholes if h and h.hole_id}
        else:
            self._drillholes = {}

    def get_drillhole(self, hole_id: str) -> Optional[DrillHole]:
        """Return the drillhole object by ID."""
        return self._drillholes.get(hole_id)

    def get_all_drillholes(self) -> list[DrillHole]:
        """Return all drillholes in the spatial model."""
        return list(self._drillholes.values())

    def hole_ids(self) -> list[str]:
        """Return sorted list of all drillhole IDs."""
        return sorted(self._drillholes.keys())

    def count(self) -> int:
        """Return total number of drillholes in the spatial model."""
        return len(self._drillholes)

    # ------------------------------------------------------------------
    # Collars & Stations Access
    # ------------------------------------------------------------------
    def get_collar(self, hole_id: str) -> Optional[CollarRecord]:
        """Return the collar record for a specific drillhole."""
        dh = self.get_drillhole(hole_id)
        return dh.collar if dh else None

    def get_all_collars(self) -> list[CollarRecord]:
        """Return collar records for all drillholes."""
        return [dh.collar for dh in self._drillholes.values() if dh.collar]

    def get_trajectory(self, hole_id: str) -> list[TrajectoryPoint]:
        """Return the 3D trajectory polyline points for a specific drillhole."""
        dh = self.get_drillhole(hole_id)
        return dh.trajectory if dh else []

    def get_survey(self, hole_id: str) -> list[SurveyRecord]:
        """Return the deviation survey stations for a specific drillhole."""
        dh = self.get_drillhole(hole_id)
        return dh.survey if dh else []

    # ------------------------------------------------------------------
    # 3D Coordinate Computations & Interpolations
    # ------------------------------------------------------------------
    def depth_to_xyz(self, hole_id: str, depth: float) -> Optional[tuple[float, float, float]]:
        """Compute real-world (X, Y, Z) coordinates at a given downhole depth.

        Uses the trajectory calculated by minimum-curvature / average-angle.
        """
        dh = self.get_drillhole(hole_id)
        if not dh:
            return None
        if not dh.trajectory:
            if dh.collar:
                return (dh.collar.x, dh.collar.y, dh.collar.z - depth)
            return None
        return depth_to_xyz(dh.trajectory, depth)

    def get_interval_selection(
        self,
        hole_id: str,
        from_m: float,
        to_m: float,
        domain: str = "",
        attributes: Optional[dict[str, Any]] = None,
        source: str = "",
    ) -> IntervalSelection:
        """Construct an IntervalSelection with real 3D top and bottom coordinates computed."""
        coords_from = self.depth_to_xyz(hole_id, from_m)
        coords_to = self.depth_to_xyz(hole_id, to_m)
        return IntervalSelection(
            hole_id=hole_id,
            from_m=from_m,
            to_m=to_m,
            domain=domain,
            attributes=dict(attributes or {}),
            source=source,
            coords_from=coords_from,
            coords_to=coords_to,
        )

    # ------------------------------------------------------------------
    # Spatial Extents & Bounding Boxes
    # ------------------------------------------------------------------
    def bounds_3d(self) -> dict[str, float]:
        """Calculate the exact 3D bounding box enclosing all collars and trajectories.

        Returns real unscaled coordinates in project units (m or ft).
        """
        if not self._drillholes:
            return {
                "min_x": 0.0, "max_x": 0.0,
                "min_y": 0.0, "max_y": 0.0,
                "min_z": 0.0, "max_z": 0.0,
            }

        xs: list[float] = []
        ys: list[float] = []
        zs: list[float] = []

        for dh in self._drillholes.values():
            if dh.collar:
                xs.append(dh.collar.x)
                ys.append(dh.collar.y)
                zs.append(dh.collar.z)
            for pt in dh.trajectory:
                xs.append(pt.x)
                ys.append(pt.y)
                zs.append(pt.z)

        if not xs:
            return {
                "min_x": 0.0, "max_x": 0.0,
                "min_y": 0.0, "max_y": 0.0,
                "min_z": 0.0, "max_z": 0.0,
            }

        return {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
            "min_z": min(zs),
            "max_z": max(zs),
        }

    def drillhole_extent(self, hole_id: str) -> Optional[dict[str, float]]:
        """Calculate the 3D bounding box of a single drillhole."""
        dh = self.get_drillhole(hole_id)
        if not dh:
            return None
        xs = [dh.collar.x] if dh.collar else []
        ys = [dh.collar.y] if dh.collar else []
        zs = [dh.collar.z] if dh.collar else []
        for pt in dh.trajectory:
            xs.append(pt.x)
            ys.append(pt.y)
            zs.append(pt.z)
        if not xs:
            return None
        return {
            "min_x": min(xs), "max_x": max(xs),
            "min_y": min(ys), "max_y": max(ys),
            "min_z": min(zs), "max_z": max(zs),
        }

    # ------------------------------------------------------------------
    # Spatial Queries & Relations
    # ------------------------------------------------------------------
    def find_drillholes_in_box(
        self,
        min_x: float, max_x: float,
        min_y: float, max_y: float,
        min_z: Optional[float] = None, max_z: Optional[float] = None,
    ) -> list[str]:
        """Find IDs of drillholes whose collars or trajectories intersect a 2D/3D box."""
        matched: list[str] = []
        for dh in self._drillholes.values():
            points = []
            if dh.collar:
                points.append((dh.collar.x, dh.collar.y, dh.collar.z))
            for pt in dh.trajectory:
                points.append((pt.x, pt.y, pt.z))

            for x, y, z in points:
                if min_x <= x <= max_x and min_y <= y <= max_y:
                    if min_z is not None and z < min_z:
                        continue
                    if max_z is not None and z > max_z:
                        continue
                    matched.append(dh.hole_id)
                    break
        return sorted(matched)

    def find_drillholes_near_point(
        self,
        x: float,
        y: float,
        radius: float,
    ) -> list[tuple[str, float]]:
        """Find drillholes whose collars are within radius of (x, y).

        Returns sorted list of (hole_id, horizontal_distance).
        """
        results: list[tuple[str, float]] = []
        for dh in self._drillholes.values():
            if dh.collar:
                dist = math.hypot(dh.collar.x - x, dh.collar.y - y)
                if dist <= radius:
                    results.append((dh.hole_id, dist))
        return sorted(results, key=lambda r: r[1])

    def find_intervals_at_depth(
        self,
        hole_id: str,
        depth: float,
    ) -> dict[str, list[IntervalRecord]]:
        """Return all interval records (litho, assays, alterations, etc.) covering depth."""
        dh = self.get_drillhole(hole_id)
        if not dh:
            return {}

        res: dict[str, list[IntervalRecord]] = {
            "litho": [],
            "assays": [],
            "alterations": [],
            "mineralizations": [],
        }
        for inv in dh.litho:
            if inv.from_depth <= depth <= inv.to_depth:
                res["litho"].append(inv)
        for inv in dh.assays:
            if inv.from_depth <= depth <= inv.to_depth:
                res["assays"].append(inv)
        for inv in dh.alterations:
            if inv.from_depth <= depth <= inv.to_depth:
                res["alterations"].append(inv)
        for inv in dh.mineralizations:
            if inv.from_depth <= depth <= inv.to_depth:
                res["mineralizations"].append(inv)
        return res
