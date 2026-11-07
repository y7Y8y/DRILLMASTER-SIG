"""
scene3d.zones — zones (campagnes / prospects) détectées automatiquement.

Les collets sont regroupés par proximité (grille + composantes connexes) :
deux amas séparés de plus de `gap` mètres forment deux zones. Chaque zone
reçoit un nom géographique (Nord, Centre, Est…) pour naviguer de l'une à
l'autre sans rien configurer.
"""
from __future__ import annotations

from collections import deque
import numpy as np

_DIRS = ("Est", "Nord-Est", "Nord", "Nord-Ouest", "Ouest", "Sud-Ouest",
         "Sud", "Sud-Est")


def detect_zones(xy: np.ndarray, gap: float = 600.0):
    """Retourne (labels (H,) int, zones) ; zones = liste de dicts
    {id, name, count, center (2,)}, triée de la plus grande à la plus petite."""
    H = xy.shape[0]
    ij = np.floor(xy / gap).astype(np.int64)
    key = (ij[:, 0] + 1_000_000) * 2_000_000 + (ij[:, 1] + 1_000_000)
    ukeys, inv = np.unique(key, return_inverse=True)
    cells = {int(k): i for i, k in enumerate(ukeys)}
    comp = -np.ones(ukeys.size, dtype=np.int64)
    ncomp = 0
    for start in range(ukeys.size):
        if comp[start] >= 0:
            continue
        comp[start] = ncomp
        dq = deque([start])
        while dq:
            c = dq.popleft()
            ci = int(ukeys[c]) // 2_000_000 - 1_000_000
            cj = int(ukeys[c]) % 2_000_000 - 1_000_000
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    nk = (ci + di + 1_000_000) * 2_000_000 + (cj + dj + 1_000_000)
                    n = cells.get(nk)
                    if n is not None and comp[n] < 0:
                        comp[n] = ncomp
                        dq.append(n)
        ncomp += 1
    labels = comp[inv]
    sizes = np.bincount(labels, minlength=ncomp)
    order = np.argsort(-sizes, kind="stable")
    remap = np.empty(ncomp, dtype=np.int64)
    remap[order] = np.arange(ncomp)
    labels = remap[labels]
    centers = np.array([xy[labels == z].mean(axis=0) for z in range(ncomp)])
    names = _name_zones(centers)
    zones = [dict(id=z, name=names[z], count=int((labels == z).sum()),
                  center=centers[z]) for z in range(ncomp)]
    return labels, zones


def _name_zones(centers: np.ndarray) -> list[str]:
    n = centers.shape[0]
    if n == 1:
        return ["Zone unique"]
    mid = centers.mean(axis=0)
    d = centers - mid
    dist = np.hypot(d[:, 0], d[:, 1])
    far = dist.max() or 1.0
    names = []
    for i in range(n):
        if dist[i] / far < 0.3:
            names.append("Centre")
            continue
        ang = (np.degrees(np.arctan2(d[i, 1], d[i, 0])) + 360.0) % 360.0
        names.append(_DIRS[int(((ang + 22.5) % 360.0) // 45.0)])
    seen: dict[str, int] = {}
    for i, nm in enumerate(names):
        seen[nm] = seen.get(nm, 0) + 1
        if names.count(nm) > 1:
            names[i] = f"{nm} {seen[nm]}"
    return names
