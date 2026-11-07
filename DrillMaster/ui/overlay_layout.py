"""DrillMaster — Layout des overlays 3D (pure, sans Qt).

Règle anti-chevauchement de la SPEC (B-4) : les positions des overlays
FIXES de la vue 3D (légende, gizmo, badge) sont déclarées dans UNE
SEULE fonction, pure et testée — pas des coordonnées codées en dur un
peu partout.

Ordre de résolution (le bord droit de la légende est ancré à 14 px du
bord, donc elle peut chevaucher le badge en haut-droite quand elle est
haute, et le gizmo en bas-gauche quand elle est large) :

1. position naturelle : bas-droite (marge 14, dégagement bas 60) ;
2. si la légende chevauche le BADGE → descendue sous lui (y ≥ 75) ;
3. si elle chevauche le GIZMO → remontée au-dessus — seulement si ça
   reste sous le badge (une légende quasi pleine largeur sur un petit
   canvas ne peut pas tout éviter : cas pathologique documenté, le
   rendu devra un jour réduire la légende).
"""

from __future__ import annotations


def _overlap(a, b) -> bool:
    """Rectangles (x, y, w, h) : chevauchement strict ?"""
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0]
                or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


def overlay_layout(width: float, height: float,
                   legend_w: float, legend_h: float) -> dict:
    """Positions des overlays fixes — UNE SEULE source (règle B-4).

    Retourne un dict de rectangles ``(x, y, w, h)`` :
    ``legend``, ``gizmo`` (bas-gauche), ``badge`` (haut-droite).
    """
    gx, gy = 45.0, height - 35.0
    gizmo_rect = (gx - 26.0, gy - 26.0, 52.0, 40.0)
    badge_rect = (width - 85.0, 45.0, 75.0, 22.0)

    lx = max(14.0, width - legend_w - 14.0)
    ly = max(45.0, height - legend_h - 60.0)
    legend_rect = (lx, ly, legend_w, legend_h)

    # 1. badge (haut-droite) : passer dessous.
    if _overlap(legend_rect, badge_rect):
        ly = max(ly, badge_rect[1] + badge_rect[3] + 8.0)
        legend_rect = (lx, ly, legend_w, legend_h)

    # 2. gizmo (bas-gauche) : remonter au-dessus, sans replonger dans
    #    la zone du badge (y ≥ 75) — sinon on garde la position sûre
    #    pour le badge (cas pathologique quasi pleine largeur).
    if _overlap(legend_rect, gizmo_rect):
        raised = max(75.0, gizmo_rect[1] - legend_h - 10.0)
        if raised >= 75.0 and raised + legend_h <= gizmo_rect[1] + 1e-9:
            ly = raised
            legend_rect = (lx, ly, legend_w, legend_h)

    return {"legend": legend_rect, "gizmo": gizmo_rect,
            "badge": badge_rect}
