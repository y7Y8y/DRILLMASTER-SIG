"""DrillMaster — Mesh builder : géométrie 3D PURE (volet 1, tranche 2).

Extrait de ``ui/view_3d.py`` (SPEC de restructuration) : tout ce qui
calcule des GÉOMÉTRIES à partir des données de forage vit ici —
zéro notion de caméra, de pixels ou de QPainter.  Le renderer peint ce
que ce module produit ; l'interaction s'appuie sur les mêmes segments
pour le picking.

Contenu (v2.9.146, tranche 2 — démarrage) :
- ``interpolate_dh_point`` : point exact d'un forage à une profondeur
  (interpolation linéaire entre points de trajectoire) ;
- ``segment_frame`` : repère écran d'un segment (normale perpendiculaire
  + longueur) — sert aux voies parallèles (intercepts, multi-codes) ;
- ``lane_point`` : point décalé le long de la normale (voies côte à
  côte) ;
- ``interval_segments`` : segments (profondeur → points 3D) d'un
  forage pour un domaine, sans AUCUN rendu.

Pur Python : testable sans QGIS (tests/test_view3d.py, MESH-146).
"""

from __future__ import annotations

import math

from typing import Optional


def interpolate_dh_point(dh, depth: float):
    """Point exact (``TrajectoryPoint``) d'un forage à ``depth``.

    Interpolation linéaire entre les points de trajectoire ; bornes
    clampées au premier/dernier point.  ``None`` sans trajectoire.

    v2.9.164 — ``bisect`` C + cache des profondeurs (avant : scan
    linéaire O(n) = 1188 ms pour 500 forages ; bisect Python = 131 ms ;
    bisect C + cache = ~15 ms, ÷80).
    """
    if not dh.trajectory:
        return None
    if depth <= dh.trajectory[0].depth:
        return dh.trajectory[0]
    if depth >= dh.trajectory[-1].depth:
        return dh.trajectory[-1]

    # Cache des profondeurs (une liste par forage — construite une fois,
    # réutilisée par TOUTES les interpolations du forage).
    depths = getattr(dh, "_depth_cache", None)
    if depths is None or len(depths) != len(dh.trajectory):
        depths = [p.depth for p in dh.trajectory]
        try:
            dh._depth_cache = depths
        except (AttributeError, TypeError):
            pass  # dataclass figée — pas de cache, bisect direct

    # bisect (C) : trouve le segment en O(log n)
    import bisect as _bisect
    hi = _bisect.bisect_right(depths, depth)
    lo = hi - 1
    if lo < 0:
        lo, hi = 0, 1
    if hi >= len(dh.trajectory):
        lo, hi = len(dh.trajectory) - 2, len(dh.trajectory) - 1

    p0, p1 = dh.trajectory[lo], dh.trajectory[hi]
    t = (depth - p0.depth) / max(p1.depth - p0.depth, 1e-6)
    return type(p0)(
        x=p0.x + t * (p1.x - p0.x),
        y=p0.y + t * (p1.y - p0.y),
        z=p0.z + t * (p1.z - p0.z),
        depth=depth,
    )


def segment_frame(p_top, p_bot) -> tuple[float, float, float]:
    """Repère écran d'un segment : ``(nx, ny, longueur)``.

    ``(nx, ny)`` = normale unitaire perpendiculaire au segment (dans le
    plan écran) — sert à décaler des voies PARALLÈLES côte à côte
    (intercepts par règle, multi-codes minéralisations/altérations).
    """
    dx = p_bot.x() - p_top.x()
    dy = p_bot.y() - p_top.y()
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 1e-4:
        return 0.0, 1.0, length
    return -dy / length, dx / length, length


def lane_point(point, nx: float, ny: float, offset: float):
    """Point décalé de ``offset`` le long de la normale ``(nx, ny)``.

    Retourne un tuple ``(x, y)`` — conversion QPointF à la charge du
    renderer (ce module ne connaît pas Qt).
    """
    return (point.x() + nx * offset, point.y() + ny * offset)


def mineralization_style_codes(inv):
    """TOUS les styles de minéralisation d'un intervalle (v2.9.154).

    Source unique partagée : en organisation LARGE (colonnes Style_1…
    Style_N, marqueur ``_wide_styles`` posé à l'IMPORT), les styles
    vivent dans les COMPOSANTS — jusqu'à 4, comme la coupe 2D les lit.
    Sinon repli sur l'attribut de style unique.

    Retour écran : « le code s'affiche mais que pour deux éléments or
    le référentiel en a 4 — ils ne se partagent pas les infos ? » →
    les données SONT partagées (mêmes IntervalRecord) ; c'est un seuil
    d'AFFICHAGE qui masquait les courts intervalles.  Cette fonction,
    testée, verrouille la lecture des 4 styles.
    """
    attrs = getattr(inv, "attributes", None) or {}
    if getattr(inv, "components", None) and attrs.get("_wide_styles"):
        codes = [c.raw_code for c in inv.components if c.raw_code]
        if codes:
            return [str(c).strip() for c in codes]
    value = (attrs.get("mineralization_style")
             or attrs.get("style_mineralisation")
             or attrs.get("style"))
    return [str(value).strip()] if value not in (None, "") else []


    """Angle (degrés) pour écrire un libellé LE LONG d'un segment écran.

    v2.9.153 — codes de style le long des tubes 3D (comme la coupe 2D
    écrit ses codes dans les bandes).  Le texte suit la direction du
    segment mais n'est JAMAIS à l'envers : l'angle est ramené dans
    ]-90°, +90°] (retourné de 180° si besoin).
    """
    angle = math.degrees(math.atan2(dy, dx))
    while angle > 90.0:
        angle -= 180.0
    while angle <= -90.0:
        angle += 180.0
    return angle


def interval_segments(dh, intervals):
    """Segments ``(from_m, to_m, pt_top, pt_bot)`` d'une liste d'intervalles.

    Prépare la géométrie de dessin SANS rendu : les points 3D sont
    interpolés sur la trajectoire réelle ; les intervalles dont les
    bornes ne s'interpolent pas sont sautés (comportement historique du
    canvas).
    """
    segments = []
    for inv in intervals or []:
        pt_top = interpolate_dh_point(dh, inv.from_depth)
        pt_bot = interpolate_dh_point(dh, inv.to_depth)
        if pt_top is not None and pt_bot is not None:
            segments.append((inv.from_depth, inv.to_depth, pt_top, pt_bot))
    return segments
