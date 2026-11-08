"""Chantier 9 — ce que le noyau ne peut pas voir, écrit une fois pour toutes.

R-40 dit « le noyau ne connaît pas l'interface ». Une règle qu'on récite ne
tient pas ; une règle qu'un test vérifie, si. Ce module porte la liste, et
`specs/tests/test_architecture.py` la fait respecter sur les imports réels.

Trois niveaux, parce que tout confondre serait faux :

- **interdit** — un module du noyau qui importe un widget : le noyau
  deviendrait impossible à tester sans écran ;
- **permis et mesuré** — Qt pour peindre et traduire (couleurs, polices,
  textes) : le noyau en a besoin, on le compte au lieu de l'interdire ;
- **à surveiller** — un calcul de trigonométrie écrit dans une vue : c'est
  là que la coupe et la 3D peuvent diverger (chantier 3).
"""
from __future__ import annotations

# Ce qu'un module du noyau n'importe jamais.
INTERDITS = (
    "qgis.PyQt.QtWidgets",
    "..ui",
    "DrillMaster.ui",
)

# Ce qu'il a le droit de toucher, et qu'on mesure pour ne pas dériver.
PERMIS_MESURES = (
    "qgis.PyQt.QtCore",
    "qgis.PyQt.QtGui",
    "math",
)

# Ce qui trahit un calcul : à sortir des vues vers le noyau.
SIGNAUX_DE_CALCUL = (
    "math.atan2", "math.atan", "math.sin", "math.cos", "math.tan",
    "math.sqrt", "math.hypot", "math.degrees", "math.radians",
    "math.asin", "math.acos", "statistics.mean", "statistics.median",
)


def est_du_noyau(module: str) -> bool:
    return module.startswith("DrillMaster.core") or module.endswith(".core")


def import_interdit(module: str, cible: str):
    """Rend la raison du refus, ou None si l'import est permis."""
    if not est_du_noyau(module):
        return None
    for interdit in INTERDITS:
        if cible == interdit or cible.startswith(interdit + "."):
            return (f"{module} importe {cible} : un module du noyau ne "
                    "connaît pas l'interface (R-40)")
    return None


def calculs(texte: str) -> int:
    """Combien de calculs géométriques sont écrits dans ce texte."""
    return sum(texte.count(signal) for signal in SIGNAUX_DE_CALCUL)
