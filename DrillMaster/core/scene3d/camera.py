"""
scene3d.camera — caméra orbitale + projection perspective (numpy pur).

Espace scène : x = est, y = nord, z = élévation, RELATIFS à model.origin.
`z_exag` est l'exagération verticale (partagée avec la coupe 2D).
"""
from __future__ import annotations

import math
import numpy as np


class OrbitCamera:
    def __init__(self) -> None:
        self.target = np.zeros(3, dtype=np.float64)
        self.yaw = math.radians(20.0)      # rotation autour de Z
        self.pitch = math.radians(35.0)    # élévation de la caméra
        self.dist = 500.0
        self.fov = 45.0                    # degrés (vertical)
        self.z_exag = 1.0
        self.near = 1.0

    # ------------------------------------------------------------ pose
    def eye(self) -> np.ndarray:
        cp = math.cos(self.pitch)
        off = np.array([math.sin(self.yaw) * cp,
                        -math.cos(self.yaw) * cp,
                        math.sin(self.pitch)]) * self.dist
        return self.target + off

    def _basis(self):
        eye = self._eye_exag()
        tgt = self._target_exag()
        f = tgt - eye
        f /= np.linalg.norm(f)
        up = np.array([0.0, 0.0, 1.0])
        r = np.cross(f, up)
        n = np.linalg.norm(r)
        r = r / n if n > 1e-9 else np.array([1.0, 0.0, 0.0])
        u = np.cross(r, f)
        return eye, f, r, u

    def _eye_exag(self):
        e = self.eye().copy()
        e[2] = self.target[2] * self.z_exag + (e[2] - self.target[2])
        return e

    def _target_exag(self):
        t = self.target.copy()
        t[2] *= self.z_exag
        return t

    # ------------------------------------------------------ projection
    def project(self, pts: np.ndarray, w: int, h: int):
        """pts (N,3) → (sx, sy, depth, ok). ok = devant le plan proche."""
        eye, f, r, u = self._basis()
        p = np.asarray(pts, dtype=np.float64).copy()
        p[:, 2] *= self.z_exag
        d = p - eye
        xc = d @ r
        yc = d @ u
        zc = d @ f
        ok = zc > self.near
        z = np.where(ok, zc, 1.0)
        focal = 0.5 * h / math.tan(math.radians(self.fov) / 2.0)
        sx = w * 0.5 + focal * xc / z
        sy = h * 0.5 - focal * yc / z
        return sx, sy, zc, ok

    def pixel_size(self, depth: np.ndarray, h: int, world: float) -> np.ndarray:
        focal = 0.5 * h / math.tan(math.radians(self.fov) / 2.0)
        return world * focal / np.maximum(depth, self.near)

    # ----------------------------------------------------- interaction
    def orbit(self, dx: float, dy: float) -> None:
        self.yaw -= dx * 0.008
        self.pitch = float(np.clip(self.pitch + dy * 0.008,
                                   math.radians(-89), math.radians(89)))

    def pan(self, dx: float, dy: float, h: int) -> None:
        _, _, r, u = self._basis()
        focal = 0.5 * h / math.tan(math.radians(self.fov) / 2.0)
        k = self.dist / focal
        move = (-dx * k) * r + (dy * k) * u
        move[2] /= max(self.z_exag, 1e-6)
        self.target += move

    def zoom(self, factor: float) -> None:
        self.dist = float(np.clip(self.dist * factor, 5.0, 1.0e6))

    def fit(self, lo: np.ndarray, hi: np.ndarray) -> None:
        """Cadre une boîte englobante (lo, hi) en coordonnées scène."""
        self.target = 0.5 * (np.asarray(lo) + np.asarray(hi))
        size = float(np.linalg.norm(np.asarray(hi) - np.asarray(lo)))
        self.dist = max(size * 1.1, 50.0)
        self.near = max(self.dist * 0.002, 0.5)

    def set_view(self, yaw_deg: float, pitch_deg: float) -> None:
        self.yaw = math.radians(yaw_deg)
        self.pitch = math.radians(pitch_deg)
