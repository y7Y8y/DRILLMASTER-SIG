"""DrillMaster — Caméra orbitale 3D pure (volet 1 de la SPEC, condition D1-2).

100 % AGNOSTIQUE DU RENDU : aucun import ni appel QPainter/Qt ici —
uniquement l'état de la caméra (orbite, pivot, zoom, pan, exagération Z)
et la transformation de projection.  Réutilisable tel quel si le moteur
de rendu change un jour (QPainter → OpenGL/Three.js…).

Contrat mathématique (inchangé par rapport à l'implémentation historique
de ``View3DCanvas`` — v2.9.141, précalcul par frame) :

- ``x, y, z`` entrants = coordonnées sources RÉELLES, jamais modifiées ;
- l'exagération verticale ne scale QUE l'écart relatif à ``pivot.z`` ;
- ``project()`` renvoie ``(screen_x, screen_y, depth)`` — ``depth`` =
  distance caméra (grand = loin) pour le tri du peintre.

Extraction v2.9.145 : les maths vivaient dans ``ui/view_3d.py``
(``_setup_frame``/``project_3d``) ; elles vivent désormais ICI, testables
sans QGIS (tests/test_view3d.py, CAM-145).
"""

from __future__ import annotations

import math


class OrbitCamera:
    """Caméra orbitale : yaw/pitch autour d'un pivot en coordonnées réelles."""

    def __init__(self):
        # Orientation (degrés).
        self.yaw_deg: float = 45.0      # azimut autour de Z, [0, 360[
        self.pitch_deg: float = 30.0    # élévation au-dessus du plan XY, [-89, 89]
        # Zoom / pan (pixels).
        self.zoom: float = 1.0
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0
        # Exagération verticale (RENDU uniquement — jamais les données).
        self.v_exag: float = 1.0
        # Centre de rotation en coordonnées réelles (X, Y, Z).
        self.pivot: tuple[float, float, float] = (0.0, 0.0, 0.0)
        # Transformation précalculée (une fois par frame).
        self._fc_cx = self._fc_cy = self._fc_cz = 0.0
        self._fc_cos_y = self._fc_sin_y = 1.0
        self._fc_cos_p = self._fc_sin_p = 0.0
        self._fc_scale = None
        self._fc_hw = self._fc_hh = 0.0
        self._fc_v_exag = 1.0

    # ------------------------------------------------------------------
    # Présélections de vue
    # ------------------------------------------------------------------
    def set_view_preset(self, yaw: float, pitch: float):
        """Applique une orientation (bornée), sans toucher au reste."""
        self.yaw_deg = float(yaw) % 360.0
        self.pitch_deg = max(-89.0, min(89.0, float(pitch)))

    # ------------------------------------------------------------------
    # Transformation par frame
    # ------------------------------------------------------------------
    def setup_frame(self, scale: float, width: float, height: float):
        """Précalcule la trigonométrie UNE fois par frame.

        ``scale`` = facteur monde→pixels ; ``width``/``height`` = viewport
        (pour centrer + appliquer le pan).  ``project()`` peut ensuite
        s'appeler des milliers de fois par frame sans recalculer.
        """
        self._fc_cx, self._fc_cy, self._fc_cz = self.pivot
        yaw_rad = math.radians(self.yaw_deg)
        pitch_rad = math.radians(self.pitch_deg)
        self._fc_cos_y = math.cos(yaw_rad)
        self._fc_sin_y = math.sin(yaw_rad)
        self._fc_cos_p = math.cos(pitch_rad)
        self._fc_sin_p = math.sin(pitch_rad)
        self._fc_scale = scale * self.zoom
        self._fc_hw = width / 2.0 + self.pan_x
        self._fc_hh = height / 2.0 - self.pan_y
        self._fc_v_exag = self.v_exag

    def _ensure_frame(self, scale: float, width: float, height: float):
        """Repli : calcule la frame si elle n'a pas été préparée."""
        if self._fc_scale is None:
            self.setup_frame(scale, width, height)

    def project(self, x: float, y: float, z: float,
                scale: float, width: float = 0.0, height: float = 0.0
                ) -> tuple[float, float, float]:
        """Projette un point réel ``(x, y, z)`` → ``(sx, sy, depth)``.

        ``depth`` : distance caméra le long de l'axe de visée (grand =
        loin) — sert au tri en profondeur (peintre).  Les coordonnées
        sources ne sont JAMAIS modifiées ; l'exagération Z ne scale que
        l'écart au pivot.
        """
        self._ensure_frame(scale, width, height)
        dx = x - self._fc_cx
        dy = y - self._fc_cy
        dz = (z - self._fc_cz) * self._fc_v_exag
        rx = dx * self._fc_cos_y - dy * self._fc_sin_y
        ry = dx * self._fc_sin_y + dy * self._fc_cos_y
        px = rx
        py = ry * self._fc_sin_p + dz * self._fc_cos_p
        depth = ry * self._fc_cos_p - dz * self._fc_sin_p
        screen_x = self._fc_hw + px * self._fc_scale
        screen_y = self._fc_hh - py * self._fc_scale
        return screen_x, screen_y, depth

    # ------------------------------------------------------------------
    # v2.9.318 — pan/zoom = transformation 2D pure APPLIQUÉE AU PIXMAP
    # ------------------------------------------------------------------
    def view_blit(self, width: float, height: float, render_zoom: float,
                  render_pan_x: float, render_pan_y: float
                  ) -> tuple[float, float, float]:
        """(s, tx, ty) tel que ``écran = t + s × ref``.

        ``ref`` = coordonnées du pixmap rendu avec (render_zoom,
        render_pan). La projection est PARALLÈLE : pan/zoom n'agissent
        qu'après la rotation (translation + échelle uniforme) — ils
        peuvent donc s'appliquer au pixmap déjà rendu, sans aucune
        reprojection (plan de correctifs §2.1)."""
        rz = float(render_zoom or 1.0) or 1.0
        s = self.zoom / rz
        tx = (width / 2.0) * (1.0 - s) + self.pan_x - s * float(render_pan_x)
        ty = ((height / 2.0) * (1.0 - s) - self.pan_y
              + s * float(render_pan_y))
        return s, tx, ty

    def screen_to_ref(self, sx: float, sy: float, width: float,
                      height: float, render_zoom: float,
                      render_pan_x: float, render_pan_y: float
                      ) -> tuple[float, float, float]:
        """Inverse de ``view_blit`` — picking dans l'espace caché.

        Renvoie ``(ref_x, ref_y, s)`` : s permet de convertir un rayon
        écran en rayon ref (les segments de hit vivent dans ref)."""
        s, tx, ty = self.view_blit(width, height, render_zoom,
                                   render_pan_x, render_pan_y)
        if not s:
            return sx, sy, 1.0
        return (sx - tx) / s, (sy - ty) / s, s
