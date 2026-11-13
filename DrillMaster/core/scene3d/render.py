"""
scene3d.render — rendu logiciel numpy (aucune dépendance OpenGL ni Qt).

Pourquoi un rastériseur numpy : il tourne PARTOUT (QGIS Windows/Mac/Linux,
sans pilote GPU particulier), il est testable hors QGIS, et il n'a aucune
boucle Python par segment. Le widget Qt ne fait que copier l'image obtenue.

Stratégie de fluidité :
  * budget de segments par image (les cellules les plus proches d'abord) ;
  * mode « rapide » pendant l'interaction (budget réduit, traits grossiers),
    mode « complet » au repos ;
  * tri par profondeur des SEGMENTS (pas des pixels) puis écriture dans
    l'ordre : le dernier écrit (le plus proche) gagne.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from .model import DEPTH_KEY, SceneModel
from .geometry import (SegmentBuffer, SpatialIndex, build_spatial_index,
                       interval_segments)
from .camera import OrbitCamera

BG = (244, 246, 248)
TRACE_RGB = (120, 128, 140)
COLLAR_RGB = (28, 40, 70)

# Rampe teneurs : même famille de couleurs que les légendes de la coupe.
GRADE_RAMP = ((0, 204, 0), (85, 212, 0), (170, 212, 0), (255, 221, 0),
              (255, 153, 0), (255, 77, 0), (255, 0, 0))


# ------------------------------------------------------------------ couleurs
def hex_to_rgb(color: str, default=(150, 150, 150)):
    c = (color or "").strip().lstrip("#")
    if len(c) == 6:
        try:
            return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
        except ValueError:
            return default
    return default


def categorical_colors(values: np.ndarray, palette: dict,
                       default=(150, 150, 150)) -> np.ndarray:
    """values = codes entiers → (N,3) uint8 via palette {code: (r,g,b)}."""
    lut = np.zeros((int(max(values.max(initial=0), max(palette, default=0))) + 2, 3),
                   dtype=np.uint8)
    lut[:] = default
    for code, rgb in palette.items():
        lut[int(code)] = rgb
    idx = np.clip(values.astype(np.int64), 0, lut.shape[0] - 1)
    return lut[idx]


def numeric_breaks(values: np.ndarray, n: int = 7) -> np.ndarray:
    """Seuils par défaut : quantiles log (teneurs très asymétriques)."""
    v = values[np.isfinite(values) & (values > 0)]
    if v.size == 0:
        return np.linspace(0, 1, n + 1)[1:-1]
    qs = np.quantile(v, np.linspace(0, 1, n + 1)[1:-1])
    return np.unique(qs)


def numeric_colors(values: np.ndarray, breaks: np.ndarray,
                   ramp=GRADE_RAMP) -> np.ndarray:
    cls = np.searchsorted(breaks, values, side="right")
    lut = np.array(ramp, dtype=np.uint8)
    cls = np.clip(cls, 0, len(lut) - 1)
    out = lut[cls]
    out[~np.isfinite(values)] = (190, 190, 190)   # absent / non analysé : gris
    return out


# ------------------------------------------------------------------ réglages
@dataclass
class RenderStyle:
    """Réglages d'affichage de la 3D (tous modifiables dans le panneau)."""
    dark: bool = False
    trace_px: int = 0              # épaisseur des trajectoires ; 0 = automatique
    tube_scale: float = 1.0        # multiplicateur d'épaisseur des intervalles
    tube_max_px: int = 6           # plafond d'épaisseur écran (coût de rendu)
    collar_half: int = 1           # demi-taille des collets (px)
    budget_full: int = 220_000     # segments max au repos
    budget_fast: int = 40_000      # segments max pendant le mouvement

    @property
    def bg(self):
        return (24, 28, 34) if self.dark else BG

    @property
    def trace_rgb(self):
        return (150, 160, 175) if self.dark else TRACE_RGB

    @property
    def collar_rgb(self):
        return (255, 214, 102) if self.dark else COLLAR_RGB

    @property
    def text_rgb(self):
        return (225, 230, 238) if self.dark else (40, 48, 58)


# -------------------------------------------------------------- données rendu
@dataclass
class Layer:
    name: str
    seg: SegmentBuffer
    rgb: np.ndarray                 # (N,3) uint8
    radius: float                   # rayon monde du tube (m)
    index: SpatialIndex = None


@dataclass
class FrameStats:
    segments: int = 0
    ms: float = 0.0
    quality: str = "full"


class RenderScene:
    """Géométrie prête à dessiner + index spatiaux (construits une fois)."""

    def __init__(self, model: SceneModel, cell: float = 250.0) -> None:
        self.model = model
        self.cell = cell
        self.layers: dict[str, Layer] = {}
        self._build_traces()
        o = model.origin
        self.collars = np.stack([model.holes.x - o[0], model.holes.y - o[1],
                                 model.holes.z - o[2]], axis=1).astype(np.float32)
        st = model.holes.st_xyz - o
        self.lo = st.min(axis=0)
        self.hi = st.max(axis=0)

    # ---------------------------------------------------------- traces
    def _build_traces(self) -> None:
        h = self.model.holes
        o = self.model.origin
        pts = (h.st_xyz - o).astype(np.float32)
        hidx = (h.st_key // DEPTH_KEY).astype(np.int64)
        same = hidx[:-1] == hidx[1:]
        i0 = np.nonzero(same)[0]
        self.trace_full = SegmentBuffer(pts[i0], pts[i0 + 1],
                                        np.zeros(i0.size, np.float32),
                                        hidx[i0].astype(np.int32))
        H = h.n
        starts = np.searchsorted(hidx, np.arange(H))
        ends = np.r_[starts[1:], hidx.size] - 1
        mids = (starts + ends) // 2
        a = np.concatenate([starts, mids])
        b = np.concatenate([mids, ends])
        self.trace_coarse = SegmentBuffer(
            pts[a], pts[b], np.zeros(a.size, np.float32),
            np.concatenate([np.arange(H), np.arange(H)]).astype(np.int32))
        self.idx_full = build_spatial_index(self.model, self.trace_full, self.cell)
        self.idx_coarse = build_spatial_index(self.model, self.trace_coarse,
                                              self.cell * 2)

    # ---------------------------------------------------------- couches
    def set_layer(self, name: str, rgb: np.ndarray, radius: float,
                  lateral_offset: float = 0.0) -> Layer:
        seg = interval_segments(self.model, name, lateral_offset)
        lay = Layer(name, seg, rgb, radius)
        lay.index = build_spatial_index(self.model, seg, self.cell)
        self.layers[name] = lay
        return lay

    def clear_layers(self) -> None:
        self.layers.clear()


# ------------------------------------------------------------------ sélection
def select_rows(index: SpatialIndex, eye_xy: np.ndarray, budget: int,
                view_dir_xy: np.ndarray | None = None) -> np.ndarray:
    """Indices de lignes à dessiner : cellules proches d'abord, jusqu'au budget."""
    if index.counts.size == 0:
        return np.empty(0, dtype=np.int64)
    d = np.hypot(index.centers[:, 0] - eye_xy[0], index.centers[:, 1] - eye_xy[1])
    keep = np.ones(d.size, dtype=bool)
    if view_dir_xy is not None:
        n = float(np.hypot(*view_dir_xy))
        if n > 0.35:   # vue assez horizontale : on écarte ce qui est derrière
            fx, fy = view_dir_xy / n
            front = ((index.centers[:, 0] - eye_xy[0]) * fx
                     + (index.centers[:, 1] - eye_xy[1]) * fy)
            keep = front > -index.cell * 1.5
    cand = np.nonzero(keep)[0]
    cand = cand[np.argsort(d[cand], kind="stable")]
    cum = np.cumsum(index.counts[cand])
    last = int(np.searchsorted(cum, budget, side="right"))
    take = cand[:max(last, 1)]
    parts = [index.order[index.starts[c]:index.starts[c] + index.counts[c]]
             for c in take]
    return np.concatenate(parts) if parts else np.empty(0, dtype=np.int64)


# ------------------------------------------------------------- rastérisation
def _raster(img: np.ndarray, sx0, sy0, sx1, sy1, depth, rgb, width) -> int:
    """Dessine des segments (écran) ; ordre lointain→proche ; retourne n tracés."""
    h, w = img.shape[:2]
    m = 2.0
    inside = ~(((sx0 < -m) & (sx1 < -m)) | ((sx0 > w + m) & (sx1 > w + m))
               | ((sy0 < -m) & (sy1 < -m)) | ((sy0 > h + m) & (sy1 > h + m)))
    if not inside.any():
        return 0
    sel = np.nonzero(inside)[0]
    sel = sel[np.argsort(-depth[sel], kind="stable")]       # loin → près
    sx0, sy0, sx1, sy1 = sx0[sel], sy0[sel], sx1[sel], sy1[sel]
    rgb = rgb[sel]
    width = width[sel]
    n_seg = sel.size
    dx, dy = sx1 - sx0, sy1 - sy0
    ns = np.clip(np.ceil(np.maximum(np.abs(dx), np.abs(dy))), 1, 96).astype(np.int64) + 1
    for wpx in np.unique(width):
        g = np.nonzero(width == wpx)[0]
        cnt = ns[g]
        tot = int(cnt.sum())
        seg_of = np.repeat(np.arange(g.size), cnt)
        first = np.cumsum(cnt) - cnt
        t = (np.arange(tot) - first[seg_of]) / np.maximum(cnt[seg_of] - 1, 1)
        gi = g[seg_of]
        x = sx0[gi] + dx[gi] * t
        y = sy0[gi] + dy[gi] * t
        col = rgb[gi]
        half = int(wpx) // 2
        for oy in range(-half, int(wpx) - half):
            for ox in range(-half, int(wpx) - half):
                xi = np.rint(x).astype(np.int64) + ox
                yi = np.rint(y).astype(np.int64) + oy
                ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
                img[yi[ok], xi[ok], :3] = col[ok]
    return n_seg


def render_frame(scene: RenderScene, cam: OrbitCamera, w: int, h: int,
                 quality: str = "full", budget_full=None, budget_fast=None,
                 style: RenderStyle | None = None):
    """Retourne (image RGBA uint8 (h,w,4), FrameStats)."""
    st = style or RenderStyle()
    t0 = time.perf_counter()
    img = np.empty((h, w, 4), dtype=np.uint8)
    img[:, :, 0], img[:, :, 1], img[:, :, 2], img[:, :, 3] = (*st.bg, 255)
    fast = quality == "fast"
    budget = ((budget_fast or st.budget_fast) if fast
              else (budget_full or st.budget_full))
    eye = cam.eye()
    eye_xy = eye[:2]
    f = cam._target_exag() - cam._eye_exag()
    vdir = f[:2] / (np.linalg.norm(f) + 1e-9)
    drawn = 0

    def project_buf(buf: SegmentBuffer, rows: np.ndarray):
        p = np.concatenate([buf.p0[rows], buf.p1[rows]], axis=0)
        sx, sy, dz, ok = cam.project(p, w, h)
        n = rows.size
        okb = ok[:n] & ok[n:]
        return (sx[:n], sy[:n], sx[n:], sy[n:], 0.5 * (dz[:n] + dz[n:]), okb)

    # 1) traces : grossières de loin / en mode rapide, complètes de près
    coarse = fast or cam.dist > 1500.0
    buf, idx = ((scene.trace_coarse, scene.idx_coarse) if coarse
                else (scene.trace_full, scene.idx_full))
    rows = select_rows(idx, eye_xy, budget, vdir)
    if rows.size:
        sx0, sy0, sx1, sy1, dz, ok = project_buf(buf, rows)
        if st.trace_px > 0:
            wpx = np.full(rows.size, int(st.trace_px), dtype=np.int64)
        else:
            wpx = np.clip(np.rint(cam.pixel_size(dz, h, 0.35)), 1, 2).astype(np.int64)
        trace_rgb = np.broadcast_to(np.array(st.trace_rgb, np.uint8), (rows.size, 3))
        k = np.nonzero(ok)[0]
        drawn += _raster(img, sx0[k], sy0[k], sx1[k], sy1[k], dz[k],
                         trace_rgb[k], wpx[k])

    # 2) couches actives (intervalles)
    for lay in scene.layers.values():
        rows = select_rows(lay.index, eye_xy, budget, vdir)
        if rows.size == 0:
            continue
        sx0, sy0, sx1, sy1, dz, ok = project_buf(lay.seg, rows)
        # plafond d'épaisseur écran : suit le réglage (borné : coût en w²)
        cap0 = min(10, max(st.tube_max_px, int(round(st.tube_max_px * st.tube_scale))))
        cap = min(cap0, 3 if fast else 99)
        wpx = np.clip(np.rint(cam.pixel_size(
            dz, h, lay.radius * 2 * st.tube_scale)), 1, max(cap, 1)).astype(np.int64)
        k = np.nonzero(ok)[0]
        drawn += _raster(img, sx0[k], sy0[k], sx1[k], sy1[k], dz[k],
                         lay.rgb[rows[k]], wpx[k])

    # 3) collets
    cx, cy, cd, cok = cam.project(scene.collars, w, h)
    k = np.nonzero(cok & (cx >= 0) & (cx < w) & (cy >= 0) & (cy < h))[0]
    if k.size:
        xi = np.rint(cx[k]).astype(np.int64)
        yi = np.rint(cy[k]).astype(np.int64)
        ch = max(int(st.collar_half), 0)
        span = (0,) if cam.dist > 1500.0 else tuple(range(-ch, ch + 1))
        for oy in span:
            for ox in span:
                xx = np.clip(xi + ox, 0, w - 1)
                yy = np.clip(yi + oy, 0, h - 1)
                img[yy, xx, :3] = st.collar_rgb
    return img, FrameStats(drawn, (time.perf_counter() - t0) * 1000.0, quality)
