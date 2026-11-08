"""DrillMaster — jetons de couleur. FICHIER GÉNÉRÉ, ne pas éditer.

Source : `specs/data/theme.json`. Régénérer avec
`python3 tools/genere_palette.py --ecrit`.

Une couleur ne se nomme jamais par sa teinte mais par son **rôle** :
`couleur("border")`, pas `"#E4E7EC"`. Cela permet au thème sombre de
suivre sans qu'une ligne d'interface soit réécrite.
"""
from __future__ import annotations

ROLES = (
    "bg",
    "surface",
    "surface_2",
    "surface_3",
    "border",
    "border_strong",
    "ink",
    "ink_2",
    "ink_3",
    "accent",
    "accent_soft",
    "accent_line",
    "ok",
    "warn",
    "block",
    "quest",
    "info",
    "tech",
)

CLAIR = {
    "bg": "#F6F7F9",
    "surface": "#FFFFFF",
    "surface_2": "#F9FAFB",
    "surface_3": "#F2F4F7",
    "border": "#E4E7EC",
    "border_strong": "#D0D5DD",
    "ink": "#101828",
    "ink_2": "#475467",
    "ink_3": "#98A2B3",
    "accent": "#2E5BFF",
    "accent_soft": "#EEF2FF",
    "accent_line": "#C7D4FF",
    "ok": "#12B76A",
    "warn": "#F79009",
    "block": "#D92D20",
    "quest": "#7F56D9",
    "info": "#667085",
    "tech": "#93370D",
}

SOMBRE = {
    "bg": "#0F1115",
    "surface": "#16191F",
    "surface_2": "#1B1F26",
    "surface_3": "#22272F",
    "border": "#262B33",
    "border_strong": "#39404A",
    "ink": "#E7EAEE",
    "ink_2": "#9AA4B2",
    "ink_3": "#6B7482",
    "accent": "#5B7CFF",
    "accent_soft": "#1B2340",
    "accent_line": "#2B3A6B",
    "ok": "#12B76A",
    "warn": "#F79009",
    "block": "#D92D20",
    "quest": "#7F56D9",
    "info": "#667085",
    "tech": "#F79009",
}

# Rôles sémantiques : « avertissement » → « warn ». Le code parle le
# vocabulaire de l'utilisateur, le thème garde ses noms courts.
SEMANTIQUE = {
    "info": "info",
    "avertissement": "warn",
    "question": "quest",
    "blocage": "block",
    "erreur_technique": "tech",
}

TAILLES = {
    "titre": 20,
    "section": 12.5,
    "corps": 10,
    "secondaire": 9,
    "micro": 8.4,
    "chiffre": 16,
}

RAYONS = {
    "surface": 10,
    "champ": 6,
    "pilule": 10,
    "bouton": 7,
}

GRILLE = 4


def couleur(role: str, mode: str = "clair") -> str:
    """Rend un hexadécimal par rôle. Lève KeyError si le rôle n'existe pas.

    Un rôle inconnu est une faute de frappe, pas un cas par défaut : le
    lever tôt évite une couleur qui disparaît silencieusement à l'écran.
    """
    table = SOMBRE if mode == "sombre" else CLAIR
    return table[role]


def paire(role: str) -> tuple:
    """(clair, sombre) — pour les tracés 2D/3D qui peignent hors des widgets."""
    return CLAIR[role], SOMBRE[role]
