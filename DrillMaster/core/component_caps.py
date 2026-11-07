"""Plafonds d'organisation par domaine (CM-03, arbitré le 21/08/2026).

Après la revue écran « nombre adaptatif de colonnes », les plafonds sont
FIXES et fondés sur les réalités géologiques (un intervalle porte une
roche hôte plus quelques composants ; un assemblage d'altération ne
dépasse pas une poignée de types ; un style de minéralisation dominant,
parfois deux) et sur la lisibilité de la coupe (piste de 8 unités,
plancher de lisibilité ~1,2 px par bande).

Règle §10 respectée : un dépassement est une ERREUR DE VALIDATION
bloquante qui nomme les colonnes ou codes en trop — aucune valeur n'est
tronquée ni lue à moitié, aucune donnée source n'est modifiée.

Pure Python, sans Qt ni QGIS — partagé par le parsing, la validation,
l'interface et les tests.
"""
from __future__ import annotations

# --- Plafonds (composants d'UN intervalle) -----------------------------------
MAX_LITHOLOGY_COMPONENTS = 4      # 1 primaire + 3 secondaires/veines/accessoires
MAX_ALTERATION_CODES = 5          # codes par intervalle (colonnes ou cellule « / »)
MAX_MINERALIZATION_STYLES = 2     # style dominant + subordonné
MAX_MINERALS = 5                  # colonnes min1…min5 jointes dans « Minéraux »
MAX_INTENSITY_COLUMNS = 5         # colonnes Int_k appariées (altérations)

# Domaines d'affichage concernés par une piste codée (clé = type de fichier).
DOMAIN_CAPS = {
    "litho": MAX_LITHOLOGY_COMPONENTS,
    "alterations": MAX_ALTERATION_CODES,
    "mineralizations": MAX_MINERALIZATION_STYLES,
}


def cap_for(file_type: str) -> int:
    """Plafond du domaine, ou 0 quand le domaine n'est pas plafonné ici."""
    return DOMAIN_CAPS.get(str(file_type or ""), 0)


def cap_excess(names, cap: int) -> list[str]:
    """Return the names beyond ``cap`` (display order), never the kept ones.

    The caller turns them into ONE blocking validation issue that names
    exactly what the file must drop or restructure — règle d'arrêt §10.
    """
    if cap <= 0:
        return []
    ordered = [str(name) for name in (names or [])]
    return ordered[cap:]
