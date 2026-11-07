"""Shared workspace state for map, 2D section, 3D view and interpretation."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Optional

from .selection_model import EntitySelection, IntervalSelection


class WorkspaceState:
    """Observable store with no QGIS dependency.

    Views subscribe to semantic events instead of calling one another. This is
    the foundation for Carte QGIS ↔ Coupe 2D ↔ Vue 3D ↔ Interprétation sync.
    """

    DEFAULTS = {
        "active_view": "map",
        "project_path": None,
        "project_name": None,
        "selected_hole_id": None,
        "selected_interval": None,
        "selected_entity": None,
        "current_section_id": None,
        "active_element": None,
        "filters": {},
        "visibility": {},
    }

    def __init__(self):
        self._values = dict(self.DEFAULTS)
        self._values["filters"] = {}
        self._values["visibility"] = {}
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        previous = self._values.get(key)
        if previous == value:
            return False
        self._values[key] = value
        for callback in tuple(self._subscribers.get(key, ())):
            callback(value)
        for callback in tuple(self._subscribers.get("*", ())):
            callback(key, value)
        return True

    def subscribe(self, key: str, callback: Callable, emit_current: bool = False):
        if callback not in self._subscribers[key]:
            self._subscribers[key].append(callback)
        if emit_current:
            if key == "*":
                for current_key, value in self._values.items():
                    callback(current_key, value)
            else:
                callback(self._values.get(key))

        def unsubscribe():
            self.unsubscribe(key, callback)
        return unsubscribe

    def unsubscribe(self, key: str, callback: Callable):
        callbacks = self._subscribers.get(key, [])
        if callback in callbacks:
            callbacks.remove(callback)

    # ------------------------------------------------------------------
    # First-class selection model API (2D ↔ 3D ↔ Interprétation ↔ QGIS)
    # ------------------------------------------------------------------
    def select_interval(
        self,
        hole_id: str,
        from_m: float,
        to_m: float,
        domain: str = "",
        attributes: Optional[dict[str, Any]] = None,
        source: str = "",
        coords_from: Optional[tuple[float, float, float]] = None,
        coords_to: Optional[tuple[float, float, float]] = None,
    ) -> IntervalSelection:
        """Select a downhole interval and notify all listening components."""
        sel = IntervalSelection(
            hole_id=hole_id,
            from_m=from_m,
            to_m=to_m,
            domain=domain,
            attributes=dict(attributes or {}),
            source=source,
            coords_from=coords_from,
            coords_to=coords_to,
        )
        self.set("selected_hole_id", hole_id)
        # Store both serialized dict (for backward compatibility) and object access
        self.set("selected_interval", sel.to_dict())
        return sel

    def get_selected_interval(self) -> Optional[IntervalSelection]:
        """Return the currently selected interval as an IntervalSelection."""
        raw = self._values.get("selected_interval")
        if not raw:
            return None
        if isinstance(raw, IntervalSelection):
            return raw
        if isinstance(raw, dict):
            try:
                return IntervalSelection.from_dict(raw)
            except Exception as _exc:
                from .diagnostics import log_swallowed
                log_swallowed("État/sélection : get_selected_interval", _exc)
                return None
        return None

    def select_entity(
        self,
        entity: EntitySelection | dict[str, Any],
        source: str = "interpretation",
    ) -> EntitySelection:
        """Select an interpreted geological entity (e.g. ZM-03)."""
        if isinstance(entity, dict):
            obj = EntitySelection.from_dict(entity)
        else:
            obj = entity
        if source:
            obj.source = source
        self.set("selected_entity", obj.to_dict())
        # If the entity has contributing intervals, focus the first one
        if obj.contributing_intervals:
            first = obj.contributing_intervals[0]
            self.set("selected_hole_id", first.hole_id)
            self.set("selected_interval", first.to_dict())
        return obj

    def get_selected_entity(self) -> Optional[EntitySelection]:
        raw = self._values.get("selected_entity")
        if not raw:
            return None
        if isinstance(raw, EntitySelection):
            return raw
        if isinstance(raw, dict):
            try:
                return EntitySelection.from_dict(raw)
            except Exception as _exc:
                from .diagnostics import log_swallowed
                log_swallowed("État/sélection : get_selected_entity", _exc)
                return None
        return None

    def clear_selection(self):
        self.set("selected_hole_id", None)
        self.set("selected_interval", None)
        self.set("selected_entity", None)

    def update_filters(self, **updates):
        filters = dict(self._values.get("filters", {}))
        filters.update(updates)
        self.set("filters", filters)

    def update_visibility(self, **updates):
        visibility = dict(self._values.get("visibility", {}))
        visibility.update(updates)
        self.set("visibility", visibility)

    def snapshot(self):
        snapshot = dict(self._values)
        snapshot["filters"] = dict(snapshot.get("filters", {}))
        snapshot["visibility"] = dict(snapshot.get("visibility", {}))
        return snapshot
