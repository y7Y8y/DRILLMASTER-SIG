"""
DrillMaster — Widgets réutilisables (Lot DA-1, v2.9.396)
=========================================================
Composants partagés : accordéon normalisé (``CollapsibleGroup``) et
fabriques de lignes d'option (``option_rows``).

Règle DA (docs/DESIGN.md, principe 4 — récurrence des catégories) :
une même catégorie d'option (taille, décalage, couleur…) se présente
TOUJOURS de la même façon, quel que soit le groupe qui l'héberge.
Toute nouvelle option passe par ces fabriques — plus de boilerplate
QSpinBox + setStyleSheet(INPUT_STYLE) copié-collé.
"""

from .collapsible_group import CollapsibleGroup
from .option_rows import (
    make_check, make_combo, make_line_edit, make_spin, make_xy_pair)

__all__ = [
    "CollapsibleGroup",
    "make_spin",
    "make_combo",
    "make_check",
    "make_line_edit",
    "make_xy_pair",
]
