"""Étiquettes de forage compactes (v2.9.285).

Retour écran : « ISBRC0005 partout = surchargé ».  On ne garde que le
NUMÉRO terminal de l'identifiant, cadré sur l'ordre de grandeur du plus
grand numéro du jeu affiché :

  - 1–99     → 2 chiffres  (« ISBRC0005 » → « 05 ») ;
  - 100–999  → 3 chiffres  (« ISPT000450 » → « 450 ») ;
  - ≥ 1000   → 4 chiffres   (« DH00001 » → « 0001 »).

Même règle en 2D, 3D et export (source unique partagée).  En cas
d'ambiguïté (deux préfixes différents, même numéro) l'identifiant
complet est conservé pour les trous concernés.
"""
from __future__ import annotations

import re

_TRAILING = re.compile(r"(\d+)\s*$")


def trailing_number(hole_id) -> "int | None":
    """Numéro terminal de l'identifiant (« ISBRC0005 » → 5), sinon None."""
    m = _TRAILING.search(str(hole_id or "").strip())
    return int(m.group(1)) if m else None


def label_width(hole_ids) -> int:
    """Largeur (chiffres) adaptée au plus grand numéro ; minimum 2."""
    nums = [n for n in map(trailing_number, hole_ids) if n is not None]
    return max(2, len(str(max(nums)))) if nums else 0


def compact_label(hole_id, width: int) -> str:
    """Étiquette courte d'un trou pour une largeur donnée."""
    n = trailing_number(hole_id)
    if n is None or not width:
        return str(hole_id)
    return str(n).zfill(width)


def compact_labels(hole_ids) -> dict:
    """id → étiquette courte ; ambiguïtés → identifiant complet conservé."""
    width = label_width(hole_ids)
    out = {h: compact_label(h, width) for h in hole_ids}
    seen: "dict[str, list]" = {}
    for h, lab in out.items():
        seen.setdefault(lab, []).append(h)
    for lab, ids in seen.items():
        if len(ids) > 1:
            for h in ids:
                out[h] = str(h)
    return out
