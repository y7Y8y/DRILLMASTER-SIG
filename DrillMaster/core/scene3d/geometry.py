"""
scene3d.geometry — calcul vectorisé de la géométrie partagée.

Tout est numpy : aucune boucle Python par trou ni par intervalle.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .model import DEPTH_KEY, HoleTable, SceneModel, IntervalTable


# ---------------------------------------------------------------- trajectoires
def build_trajectories(holes: HoleTable, step: float = 10.0,
                       drift_az: np.ndarray | None = None,
                       drift_dip: np.ndarray | None = None) -> None:
    """Remplit holes.st_key / holes.st_xyz (stations tous les `step` m).

    drift_az / drift_dip : dérive en deg / 100 m (None = trou droit).
    La dernière station tombe exactement sur `length` : l'interpolation
    ne « déborde » donc jamais sur le trou suivant.
    """
    H = holes.n
    L = holes.length.astype(np.float64)
    n_st = np.ceil(L / step).astype(np.int64) + 1
    hidx = np.repeat(np.arange(H, dtype=np.int64), n_st)
    starts = np.r_[0, np.cumsum(n_st)[:-1]]
    k = np.arange(hidx.size, dtype=np.int64) - starts[hidx]
    depth = np.minimum(k * step, L[hidx])

    seglen = np.zeros_like(depth)
    seglen[1:] = depth[1:] - depth[:-1]
    seglen[starts] = 0.0

    az = np.radians(holes.az.astype(np.float64)[hidx])
    dip = np.radians(np.abs(holes.dip.astype(np.float64))[hidx])
    if drift_az is not None:
        az = az + np.radians(drift_az[hidx]) * depth / 100.0
    if drift_dip is not None:
        dip = np.clip(dip + np.radians(drift_dip[hidx]) * depth / 100.0,
                      np.radians(5.0), np.radians(90.0))

    cd = np.cos(dip)
    d = np.empty((hidx.size, 3), dtype=np.float64)
    d[:, 0] = seglen * np.sin(az) * cd      # est
    d[:, 1] = seglen * np.cos(az) * cd      # nord
    d[:, 2] = -seglen * np.sin(dip)         # élévation (vers le bas)
    c = np.cumsum(d, axis=0)
    c -= c[starts][hidx]                    # repart de 0 à chaque collet
    xyz = c + np.stack([holes.x, holes.y, holes.z], axis=1)[hidx]

    holes.st_key = hidx * DEPTH_KEY + depth
    holes.st_xyz = xyz


def positions(holes: HoleTable, hole_idx: np.ndarray,
              depth: np.ndarray) -> np.ndarray:
    """Positions réelles (N,3) à (trou, profondeur) — un seul np.interp / axe."""
    key = hole_idx.astype(np.float64) * DEPTH_KEY + depth.astype(np.float64)
    out = np.empty((key.size, 3), dtype=np.float64)
    for a in range(3):
        out[:, a] = np.interp(key, holes.st_key, holes.st_xyz[:, a])
    return out


# ------------------------------------------------------------------ segments
@dataclass
class SegmentBuffer:
    """Enregistrements « instances » prêts pour le GPU (28 octets / instance).

    p0, p1 : float32 relatifs à l'origine ; value : teneur ou code.
    Le vertex shader étire un tube unitaire de p0 à p1 : le CPU ne fabrique
    JAMAIS de maillage par intervalle.
    """
    p0: np.ndarray
    p1: np.ndarray
    value: np.ndarray
    hole_idx: np.ndarray

    @property
    def nbytes(self) -> int:
        return self.p0.nbytes + self.p1.nbytes + self.value.nbytes

    @property
    def n(self) -> int:
        return int(self.value.shape[0])


def interval_segments(model: SceneModel, domain: str,
                      lateral_offset: float = 0.0) -> SegmentBuffer:
    """Segments d'un domaine. lateral_offset (m) décale la piste sur le côté
    du trou (comme les pistes de teneurs de la coupe) sans changer de donnée."""
    t: IntervalTable = model.domains[domain]
    holes = model.holes
    a = positions(holes, t.hole_idx, t.d0)
    b = positions(holes, t.hole_idx, t.d1)
    if lateral_offset:
        tang = b - a
        # normale horizontale à la trajectoire (dans le plan horizontal)
        nx, ny = tang[:, 1], -tang[:, 0]
        norm = np.hypot(nx, ny)
        norm[norm == 0] = 1.0
        off = np.stack([nx / norm, ny / norm, np.zeros_like(norm)], axis=1)
        a += off * lateral_offset
        b += off * lateral_offset
    o = model.origin
    return SegmentBuffer((a - o).astype(np.float32),
                         (b - o).astype(np.float32),
                         t.value.astype(np.float32), t.hole_idx)


# ------------------------------------------------------------ index spatial
@dataclass
class SpatialIndex:
    """Grille 2D : les intervalles sont triés par cellule → plages contiguës.
    Sert au frustum/zone culling : on ne dessine que les cellules vues."""
    cell: float
    order: np.ndarray          # permutation des intervalles
    cell_ids: np.ndarray       # (C,) ids de cellules non vides, triés
    starts: np.ndarray         # (C,) début de plage dans `order`
    counts: np.ndarray         # (C,)
    centers: np.ndarray        # (C,2) centre de cellule (relatif à l'origine)


def build_spatial_index(model: SceneModel, seg: SegmentBuffer,
                        cell: float = 250.0) -> SpatialIndex:
    mid = 0.5 * (seg.p0[:, :2] + seg.p1[:, :2])
    cx = np.floor(mid[:, 0] / cell).astype(np.int64)
    cy = np.floor(mid[:, 1] / cell).astype(np.int64)
    key = (cx + 1_000_000) * 2_000_000 + (cy + 1_000_000)
    order = np.argsort(key, kind="stable")
    ks = key[order]
    cell_ids, starts, counts = np.unique(ks, return_index=True,
                                         return_counts=True)
    ccx = cell_ids // 2_000_000 - 1_000_000
    ccy = cell_ids % 2_000_000 - 1_000_000
    centers = np.stack([(ccx + 0.5) * cell, (ccy + 0.5) * cell], axis=1)
    return SpatialIndex(cell, order, cell_ids, starts, counts, centers)


def lod_selection(index: SpatialIndex, cam_xy: np.ndarray,
                  near_radius: float, view_radius: float) -> dict:
    """Quelles cellules dessiner et à quel niveau de détail.

    near : intervalles complets ; mid : 1 enregistrement sur 8 (trous en
    traits) ; hors view_radius : rien. Retourne des comptes (la sélection
    réelle = concaténation des plages, côté rendu).
    """
    d = np.hypot(index.centers[:, 0] - cam_xy[0],
                 index.centers[:, 1] - cam_xy[1])
    near = d <= near_radius
    mid = (d > near_radius) & (d <= view_radius)
    return {
        "cells_total": int(index.counts.size),
        "cells_near": int(near.sum()),
        "cells_mid": int(mid.sum()),
        "rows_near": int(index.counts[near].sum()),
        "rows_mid_decimated": int(index.counts[mid].sum() // 8),
    }


# ---------------------------------------------- repli CPU : maillage de tubes
def expand_tubes(p0: np.ndarray, p1: np.ndarray, radius: float,
                 sides: int = 6):
    """Repli SANS instanciation GPU : fabrique les sommets d'un tube/segment.
    Sert surtout de point de comparaison (coût mémoire d'un maillage)."""
    n = p0.shape[0]
    t = (p1 - p0).astype(np.float32)
    ln = np.linalg.norm(t, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    t /= ln
    up = np.zeros_like(t)
    up[:, 2] = 1.0
    vert = np.abs(t[:, 2]) > 0.99
    up[vert] = (1.0, 0.0, 0.0)
    u = np.cross(t, up)
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    v = np.cross(t, u)
    ang = np.linspace(0, 2 * np.pi, sides, endpoint=False, dtype=np.float32)
    ring = (np.cos(ang)[None, :, None] * u[:, None, :]
            + np.sin(ang)[None, :, None] * v[:, None, :]) * radius
    verts = np.concatenate([p0[:, None, :] + ring,
                            p1[:, None, :] + ring], axis=1)  # (n, 2*sides, 3)
    return verts.reshape(-1, 3)
