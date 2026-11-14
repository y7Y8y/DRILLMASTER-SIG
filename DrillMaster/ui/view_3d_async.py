"""DrillMaster — rendu asynchrone de la scène 3D (v2.9.319, tranche 2.4).

Le détail « posé » (~144 ms pour 500 forages, mesuré
``tools/run_benchmark.py``) part dans un ``QThread`` : le thread GUI
blitte l'ancienne scène pendant le calcul, puis adopte l'image rendue
si — et seulement si — la clé de scène n'a pas bougé entre-temps.

Règles de sécurité (plan de correctifs §2.4) :

* **Zéro ``QPixmap`` dans ce module** : ``QPixmap`` vit dans le thread
  GUI (sinon plantage Windows).  Le worker rend dans une ``QImage``
  (``Format_ARGB32_Premultiplied`` — le format natif du raster Qt,
  donc conversion en pixmap côté GUI sans perte : diff pixel nul) ;
  la conversion a lieu dans le thread GUI, à l'arrivée du signal.
* **Proxy de canvas** : le worker ne lit la taille/le ratio d'écran
  qu'au LANCEMENT (accesseurs liés au thread GUI, figés) ; tout le
  reste est délégué au canvas vivant (lecture d'attributs protégée
  par le GIL), et les ÉCRITURES du renderer (``_ipt_cache_persist``,
  diagnostics…) retombent sur le canvas — le cache d'interpolation
  de la v2.9.318 survit donc au rendu asynchrone.
* **Course données/clé** : si les données mutent pendant le rendu, la
  clé recalculée à l'arrivée diffère → l'image est jetée (jamais de
  scène périmée affichée comme fraîche — classe de bug v2.9.190).
* **Repli synchrone automatique** : toute exception du worker est
  journalisée (``log_swallowed``) et l'image rendue ``None`` → le
  prochain paint repasse par le chemin synchrone historique.

Drapeau de secours (UNE version, v2.9.319) : variable d'environnement
``DRILLMASTER_3D_ASYNC=0`` ou ``canvas._async_render = False`` →
comportement 100 % synchrone d'avant 319.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import QThread, pyqtSignal


class _CanvasProxy:
    """Lecture/écriture du canvas vivant depuis le thread worker.

    Seuls les accesseurs liés au thread GUI (``width``/``height``/
    ``rect``/``devicePixelRatioF``) sont FIGÉS au lancement — les
    appeler depuis un autre thread n'est pas garanti par Qt (surtout
    sous Windows).  Tout le reste est délégué : lecture via
    ``__getattr__``, ÉCRITURE via ``__setattr__`` (write-through, pour
    que ``_ipt_cache_persist`` et les diagnostics atterrissent sur le
    canvas, pas sur le proxy).
    """

    _FROZEN = ("_c", "_w", "_h", "_dpr")

    def __init__(self, canvas, width, height, dpr):
        object.__setattr__(self, "_c", canvas)
        object.__setattr__(self, "_w", int(width))
        object.__setattr__(self, "_h", int(height))
        object.__setattr__(self, "_dpr", float(dpr))

    # ── accesseurs figés (thread GUI uniquement dans Qt) ──────────
    def width(self):
        return self._w

    def height(self):
        return self._h

    def rect(self):
        from qgis.PyQt.QtCore import QRectF
        return QRectF(0.0, 0.0, float(self._w), float(self._h))

    def devicePixelRatioF(self):
        return self._dpr

    # ── délégation au canvas vivant ───────────────────────────────
    def __getattr__(self, name):
        return getattr(self._c, name)

    def __setattr__(self, name, value):
        if name in self._FROZEN:
            object.__setattr__(self, name, value)
        else:
            setattr(self._c, name, value)


class SceneRenderWorker(QThread):
    """Rend la scène complète dans une QImage, hors thread GUI.

    Signal ``scene_ready`` : (clé, QImage ou None, zoom, pan_x, pan_y
    du LANCEMENT).  ``None`` = échec journalisé → repli synchrone.
    Les valeurs caméra du lancement sont renvoyées pour servir de
    référence au blit (§2.1) : le pixmap correspond à la caméra du
    début de rendu, pas à celle de l'arrivée.
    """

    scene_ready = pyqtSignal(object, object, float, float, float)

    def __init__(self, canvas, key, parent=None):
        super().__init__(parent)
        dpr = 1.0
        try:
            dpr = float(canvas.devicePixelRatioF())
        except Exception as exc:  # écran sans ratio : rendu 1:1
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : ratio d'écran du worker asynchrone "
                          "(rendu 1:1)", exc)
            dpr = 1.0
        import math
        if not (dpr and math.isfinite(dpr)) or dpr <= 0.0:
            dpr = 1.0
        self._proxy = _CanvasProxy(canvas, canvas.width(), canvas.height(),
                                   dpr)
        self._key = key
        # référence blit (§2.1) : caméra AU LANCEMENT du worker
        self._ref_zoom = float(getattr(canvas, "zoom", 1.0))
        self._ref_pan_x = float(getattr(canvas, "pan_x", 0.0))
        self._ref_pan_y = float(getattr(canvas, "pan_y", 0.0))

    def run(self):
        """Corps du thread : QImage + le MÊME ``_render_scene``.

        Même pipeline, mêmes hints (pas d'AA global — v2.9.318) :
        l'image est pixel-identique au rendu synchrone (protocole
        diff pixel du plan §6).
        """
        img = None
        try:
            from qgis.PyQt.QtGui import QImage, QPainter
            from .view_3d_renderer import _render_scene
            dpr = self._proxy.devicePixelRatioF()
            w = max(1, int(self._proxy.width() * dpr))
            h = max(1, int(self._proxy.height() * dpr))
            img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
            if dpr != 1.0:
                img.setDevicePixelRatio(dpr)
            painter = QPainter(img)
            _render_scene(self._proxy, painter)
            painter.end()
        except Exception as exc:  # noqa: BLE001 — repli synchrone
            from ..core.diagnostics import log_swallowed
            log_swallowed("Vue 3D : rendu asynchrone (repli synchrone)",
                          exc)
            img = None
        self.scene_ready.emit(self._key, img, self._ref_zoom,
                              self._ref_pan_x, self._ref_pan_y)
