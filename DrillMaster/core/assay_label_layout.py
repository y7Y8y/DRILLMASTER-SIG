"""
Placement des noms de pistes de teneurs (« Li ppm », « Rb ppm »…) en fin de trou.

Fonction PURE (aucun Qt) : testable seule, sous tous les angles de trous.

Contraintes garanties
---------------------
1. Chaque nom est COUCHÉ (horizontal) et s'étend vers la DROITE de son trait
   (loin des cotes de profondeur / « eoh », posés du côté gauche du trou).
2. Le trait de rappel PROLONGE la trajectoire du trou (jamais en arrière :
   il ne peut pas passer sur les pistes de teneurs).
3. Les traits d'un même trou sont parallèles, donc leur écart horizontal est
   constant : en rangeant les pistes pour que les traits LES PLUS LONGS soient
   à GAUCHE des plus courts, puis en DÉCALANT le début de chaque texte juste
   assez pour passer à droite des traits plus longs (calcul exact, pas
   d'approximation), aucun trait ne traverse un nom.
4. Les noms d'un même trou sont étagés verticalement (jamais superposés).
5. Aucun nom ne dépasse `y_limit` (axe des distances) ; sinon un 2ᵉ essai
   plus compact, puis abandon propre du nom (jamais de nom sur l'axe).

Repère : pixels scène, y vers le BAS. `u` = tangente unitaire (sens des
profondeurs croissantes), `n` = normale droite (sens des décalages de pistes).
"""
from __future__ import annotations

TEXT_GAP = 2.5          # px entre la fin du trait et le début du texte


def rects_intersect(a, b, pad: float = 0.0) -> bool:
    return not (a[0] + a[2] + pad <= b[0] or b[0] + b[2] + pad <= a[0]
                or a[1] + a[3] + pad <= b[1] or b[1] + b[3] + pad <= a[1])


def segment_hits_rect(x0, y0, x1, y1, r, pad: float = 0.0) -> bool:
    """Segment ∩ rectangle (Liang–Barsky)."""
    xmin, ymin = r[0] - pad, r[1] - pad
    xmax, ymax = r[0] + r[2] + pad, r[1] + r[3] + pad
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - xmin), (dx, xmax - x0),
                 (-dy, y0 - ymin), (dy, ymax - y0)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                if t > t1:
                    return False
                t0 = max(t0, t)
            else:
                if t < t0:
                    return False
                t1 = min(t1, t)
    return t0 <= t1


def label_order(anchors, u, n):
    """Indices rangés du trait le plus COURT au plus LONG, de sorte que les
    traits plus longs passent, à tout niveau y, à GAUCHE des plus courts."""
    ux, uy = u
    nx, ny = n
    c = nx * uy - ny * ux                 # ±1 (n ⟂ u)
    if abs(uy) > 1e-3:
        key = [t * c / uy for (_x, _y, t) in anchors]
    else:                                  # trou ~horizontal : repli sur t
        key = [t * c for (_x, _y, t) in anchors]
    return sorted(range(len(anchors)), key=lambda i: -key[i])


def _plan_once(anchors, u, order, sizes, occupied, base, gap, min_uy,
               y_limit, max_tries):
    ux, uy = u
    sgn = 1.0 if uy >= 0.0 else -1.0
    slope = (ux / uy) if abs(uy) > 1e-6 else 0.0      # dx par dy le long du trait
    out = [None] * len(anchors)
    placed: list = []
    last_len = None
    for rank, i in enumerate(order):
        ax, ay, _t = anchors[i]
        w, h = sizes[i]
        longer = [anchors[j] for j in order[rank + 1:]]   # traits plus longs
        step = (h + gap) / max(abs(uy), min_uy)
        length = base if last_len is None else last_len + step
        found = None
        for _ in range(max_tries):
            ex, ey = ax + ux * length, ay + uy * length
            by = ey + 1.0 if sgn > 0 else ey - 1.0 - h
            # début du texte : à droite de la fin du trait ET des traits plus
            # longs (leur x à la hauteur du texte, prolongés exactement).
            bx = ex + TEXT_GAP
            for (jx, jy, _jt) in longer:
                for yy in (by, by + h):
                    bx = max(bx, jx + (yy - jy) * slope + 1.5)
            rect = (bx, by, w, h)
            if y_limit is not None and sgn > 0 and rect[1] + rect[3] > y_limit:
                break                       # plus bas = pire : on arrête
            if (not any(rects_intersect(rect, o) for o in occupied)
                    and not any(rects_intersect(rect, o) for o in placed)):
                found = (ex, ey, rect)
                break
            length += step
        if found is None:
            continue
        ex, ey, rect = found
        out[i] = {"leader": (ax + ux * 1.5, ay + uy * 1.5, ex, ey),
                  "rect": rect}
        placed.append(rect)
        last_len = length                   # les suivants restent plus longs
    return out


def plan_end_labels(anchors, u, n, sizes, occupied=(), base: float = 9.0,
                    gap: float = 1.5, min_uy: float = 0.35,
                    y_limit=None, max_tries: int = 14):
    """anchors : [(ax, ay, t)] fin de piste (axe) + décalage latéral t (px).
    sizes : [(w, h)] ; occupied : rectangles (x, y, w, h) déjà pris.
    Retourne une liste alignée sur `anchors` : None ou
    {"leader": (x0, y0, x1, y1), "rect": (x, y, w, h)}."""
    if not anchors:
        return []
    order = label_order(anchors, u, n)
    res = _plan_once(anchors, u, order, sizes, occupied, base, gap, min_uy,
                     y_limit, max_tries)
    if y_limit is not None and any(r is None for r in res):
        compact = _plan_once(anchors, u, order, sizes, occupied, 5.0, 0.5,
                             min_uy, y_limit, max_tries)
        if sum(r is not None for r in compact) > sum(r is not None for r in res):
            res = compact
    return res


def stack_extent(n_labels: int, text_h: float, uy: float, base: float = 9.0,
                 gap: float = 1.5, min_uy: float = 0.35) -> float:
    """Hauteur (px, vers le bas) occupée sous la fin du trou par la pile de
    noms — sert à réserver la marge basse de la coupe."""
    if n_labels <= 0:
        return 0.0
    step = (text_h + gap) / max(abs(uy), min_uy)
    return abs(uy) * (base + (n_labels - 1) * step) + text_h + 1.0
