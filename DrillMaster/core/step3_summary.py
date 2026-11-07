"""Step-3 summary builder (v2.7.4).

Pure, QGIS-free text composition for the "trajectories computed" recap.

Why this exists — feedback 18/08/2026: the recap grew one appended
sentence per feature and would become unreadable as new domains arrive
(structures, free tables…).  The recap is now built from DATA (lists),
so adding a future domain is a one-line change at the call site and the
output always keeps the same 3 short lines :

    line 1 : forage count (+ persistence status)
    line 2 : geometry layers
    line 3 : data layers with real interval counts
    line 4 : at most ONE optional note (components rendering)
"""
from __future__ import annotations


def _tr(text):
    """v2.9.252 — Lot i18n : le récap vert de l'étape 3 est visible à
    l'écran (contexte Step3Geometry — les mêmes textes que l'étape).
    Module PUR : repli texte source hors QGIS (harnais de test)."""
    try:
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("Step3Geometry", text)
    except ImportError:
        return text


def build_step3_summary(hole_count, geometry_layers=(), data_layers=(),
                        interval_counts=(), verb="", suffix="",
                        extra_note=""):
    """Compose the compact recap text.

    ``interval_counts`` is a display-ordered list of ``(label, count)``;
    zero counts are skipped (never fake a domain that has no data).
    Data layers without an associated count (e.g. survey stations) are
    still listed by name so nothing created stays invisible.
    """
    verb = verb or _tr("traités")
    lines = [_tr("{} forages {} ✓{}").format(hole_count, verb, suffix)]

    geometry = ", ".join(name for name in geometry_layers if name)
    if geometry:
        lines.append(_tr("Géométrie : {}").format(geometry))

    counted = [f"{name} ({count})" for name, count in interval_counts
               if count]
    counted_names = {name for name, count in interval_counts if count}
    others = [name for name in data_layers
              if name and name not in counted_names]
    body = counted + others
    if body:
        lines.append(_tr("Données : {}").format(", ".join(body)))

    if extra_note:
        lines.append(extra_note)
    return "\n".join(lines)
