"""
scene3d.adapter — DrillHole (données du projet) → SceneModel.

C'est LE point de partage coupe/3D : la 3D lit les mêmes `DrillHole`
(`main_dock.drillholes`) que la coupe, avec les mêmes trajectoires, les
mêmes intervalles et les mêmes couleurs (référentiel projet).

Pur Python + numpy ; lit les objets par attributs (duck typing), donc
testable sans QGIS avec les dataclasses de core.data_model.
"""
from __future__ import annotations

import math
from typing import Callable, Iterable, Optional

import numpy as np

from .model import DEPTH_KEY, HoleTable, IntervalTable, SceneModel
from .geometry import build_trajectories

MAX_ASSAY_ELEMENTS = 3
ERR_NO_TRAJECTORY = "aucun forage avec trajectoire exploitable"


def _lith_code(iv) -> str:
    attrs = getattr(iv, "attributes", None) or {}
    code = attrs.get("lithology")
    if not code:
        pc = getattr(iv, "primary_component", None)
        code = getattr(pc, "raw_code", "") if pc is not None else ""
    return str(code or "").strip()


def _alter_code(iv) -> str:
    attrs = getattr(iv, "attributes", None) or {}
    return str(attrs.get("alteration") or attrs.get("alteration_type")
               or "").strip()


def _num(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    return None


def detect_assay_elements(drillholes: Iterable, wanted: Iterable[str] = (),
                          limit: int = MAX_ASSAY_ELEMENTS,
                          scan: int = 4000) -> list[str]:
    """Éléments chiffrés présents dans les analyses. `wanted` (ordre de
    l'utilisateur, ex. éléments actifs de la coupe) passe en premier."""
    found: dict[str, int] = {}
    seen = 0
    for dh in drillholes:
        for iv in getattr(dh, "assays", None) or []:
            for k, v in (getattr(iv, "attributes", None) or {}).items():
                if _num(v) is not None:
                    found[k] = found.get(k, 0) + 1
            seen += 1
            if seen >= scan:
                break
        if seen >= scan:
            break
    out = [e for e in wanted if e in found]
    for k, _n in sorted(found.items(), key=lambda kv: -kv[1]):
        if k not in out:
            out.append(k)
    return out[:limit]


def _hole_stations(dh, step: float = 10.0):
    """(depths, xyz) d'un trou : trajectoire du projet, sinon droite collet."""
    traj = getattr(dh, "trajectory", None) or []
    if len(traj) >= 2:
        d = np.fromiter((p.depth for p in traj), float, len(traj))
        xyz = np.array([(p.x, p.y, p.z) for p in traj], float)
        order = np.argsort(d, kind="stable")
        d, xyz = d[order], xyz[order]
        keep = np.r_[True, np.diff(d) > 1e-6]
        return d[keep], xyz[keep]
    c = dh.collar
    az = getattr(c, "azimuth", None)
    dip = getattr(c, "dip", None)
    length = float(getattr(c, "max_depth", 0.0) or 0.0)
    if az is None or dip is None or length <= 0:
        return None
    n = int(math.ceil(length / step)) + 1
    d = np.minimum(np.arange(n) * step, length)
    a, p = math.radians(az), math.radians(abs(dip))
    dirv = np.array([math.sin(a) * math.cos(p), math.cos(a) * math.cos(p),
                     -math.sin(p)])
    xyz = np.array([c.x, c.y, c.z]) + d[:, None] * dirv[None, :]
    return d, xyz


def scene_from_drillholes(drillholes: list, assay_elements: Iterable[str] = (),
                          progress: Optional[Callable[[float], None]] = None,
                          ) -> SceneModel:
    """Construit le modèle partagé. Les trous sans trajectoire exploitable
    sont ignorés (comptés dans model.skipped)."""
    holes_ok, stations = [], []
    skipped = 0
    for dh in drillholes:
        st = _hole_stations(dh)
        if st is None:
            skipped += 1
            continue
        holes_ok.append(dh)
        stations.append(st)
    H = len(holes_ok)
    if H == 0:
        raise ValueError(ERR_NO_TRAJECTORY)

    ids = np.array([dh.hole_id for dh in holes_ok])
    cx = np.array([dh.collar.x for dh in holes_ok], float)
    cy = np.array([dh.collar.y for dh in holes_ok], float)
    cz = np.array([dh.collar.z for dh in holes_ok], float)
    length = np.array([s[0][-1] for s in stations], np.float32)
    hidx = np.repeat(np.arange(H, dtype=np.int64),
                     [s[0].size for s in stations])
    depth = np.concatenate([s[0] for s in stations])
    xyz = np.concatenate([s[1] for s in stations], axis=0)
    holes = HoleTable(ids, cx, cy, cz,
                      np.zeros(H, np.float32), np.zeros(H, np.float32),
                      length, np.zeros(H, np.int8))
    holes.st_key = hidx * DEPTH_KEY + depth
    holes.st_xyz = xyz
    origin = np.array([cx.mean(), cy.mean(), cz.mean()])
    model = SceneModel(origin=origin, holes=holes)
    model.skipped = skipped

    elements = list(assay_elements) or detect_assay_elements(holes_ok)
    elements = elements[:MAX_ASSAY_ELEMENTS]

    lith_h, lith_a, lith_b, lith_c = [], [], [], []
    alt_h, alt_a, alt_b, alt_c = [], [], [], []
    as_h, as_a, as_b = [], [], []
    as_v = {e: [] for e in elements}
    lith_names: dict[str, int] = {}
    alt_names: dict[str, int] = {}

    for i, dh in enumerate(holes_ok):
        for iv in getattr(dh, "litho", None) or []:
            code = _lith_code(iv)
            lith_h.append(i); lith_a.append(iv.from_depth); lith_b.append(iv.to_depth)
            lith_c.append(lith_names.setdefault(code, len(lith_names)))
        for iv in getattr(dh, "alterations", None) or []:
            code = _alter_code(iv)
            if not code:
                continue
            alt_h.append(i); alt_a.append(iv.from_depth); alt_b.append(iv.to_depth)
            alt_c.append(alt_names.setdefault(code, len(alt_names)))
        for iv in getattr(dh, "assays", None) or []:
            attrs = getattr(iv, "attributes", None) or {}
            vals = [_num(attrs.get(e)) for e in elements]
            if all(v is None for v in vals):
                continue
            as_h.append(i); as_a.append(iv.from_depth); as_b.append(iv.to_depth)
            for e, v in zip(elements, vals):
                as_v[e].append(np.nan if v is None else v)
        if progress and (i & 255) == 0:
            progress(i / H)

    def _table(name, kind, h, a, b, v, **kw):
        if not h:
            return
        d0 = np.asarray(a, np.float32)
        d1 = np.asarray(b, np.float32)
        d1 = np.maximum(d1, d0)
        hh = np.asarray(h, np.int32)
        top = holes.length[hh]
        d0 = np.minimum(d0, top)
        d1 = np.minimum(d1, top)
        model.add_domain(IntervalTable(name, kind, hh, d0, d1,
                                       np.asarray(v, np.float32), **kw))

    _table("Lithologie", "cat", lith_h, lith_a, lith_b, lith_c,
           categories=tuple(lith_names))
    _table("Altération", "cat", alt_h, alt_a, alt_b, alt_c,
           categories=tuple(alt_names))
    for e in elements:
        _table(e, "num", as_h, as_a, as_b, as_v[e])
    return model
