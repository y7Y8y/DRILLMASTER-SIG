"""Chantier 1 — le pont entre la DA et le plugin.

`specs/data/theme.json` est la source unique (18 jetons de couleur, 6 tailles,
grille de 4 px). Le plugin Qt ne peut pas lire un fichier du dépôt au moment
de tourner : on lui **génère** donc un module qui ne contient que des
littéraux, plus une fonction `couleur(role, mode)`.

    python3 tools/genere_palette.py           # vérifie, n'écrit rien
    python3 tools/genere_palette.py --ecrit    # réécrit le module

Le module généré est le SEUL endroit du plugin où un hexadécimal de chrome
peut vivre. `specs/tests/test_palette.py` vérifie qu'il n'a pas dérivé.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
THEME = RACINE / "specs" / "data" / "theme.json"
CIBLE = RACINE / "DrillMaster" / "ui" / "palette_jetons.py"

ENTETE = '''"""DrillMaster — jetons de couleur. FICHIER GÉNÉRÉ, ne pas éditer.

Source : `specs/data/theme.json`. Régénérer avec
`python3 tools/genere_palette.py --ecrit`.

Une couleur ne se nomme jamais par sa teinte mais par son **rôle** :
`couleur("border")`, pas `"#E4E7EC"`. Cela permet au thème sombre de
suivre sans qu'une ligne d'interface soit réécrite.
"""
from __future__ import annotations

ROLES = (
{roles}
)

CLAIR = {{
{clair}
}}

SOMBRE = {{
{sombre}
}}

# Rôles sémantiques : « avertissement » → « warn ». Le code parle le
# vocabulaire de l'utilisateur, le thème garde ses noms courts.
SEMANTIQUE = {{
{semantique}
}}

TAILLES = {{
{tailles}
}}

RAYONS = {{
{rayons}
}}

GRILLE = {grille}


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
'''


def construire(theme: dict) -> str:
    def bloc(table):
        return "\n".join(f'    "{k}": "{v}",' for k, v in table.items())

    roles = "\n".join(f'    "{k}",' for k in theme["clair"])
    semantique = "\n".join(f'    "{k}": "{v}",'
                           for k, v in theme["semantique"].items())
    tailles = "\n".join(f'    "{k}": {v},'
                        for k, v in theme["typographie"].items())
    rayons = "\n".join(f'    "{k}": {v},' for k, v in theme["rayons"].items())
    return ENTETE.format(
        roles=roles,
        clair=bloc(theme["clair"]),
        sombre=bloc(theme["sombre"]),
        semantique=semantique,
        tailles=tailles,
        rayons=rayons,
        grille=theme["espacements"]["grille"],
    )


def main(argv):
    theme = json.loads(THEME.read_text(encoding="utf-8"))
    neuf = construire(theme)
    if "--ecrit" in argv:
        CIBLE.write_text(neuf, encoding="utf-8")
        print(f"écrit {CIBLE.relative_to(RACINE)} "
              f"({len(theme['clair'])} rôles × 2 modes)")
        return 0
    actuel = CIBLE.read_text(encoding="utf-8") if CIBLE.exists() else ""
    if actuel == neuf:
        print(f"à jour — {len(theme['clair'])} rôles × 2 modes")
        return 0
    print("dérive : le module généré ne correspond plus au thème")
    print("  python3 tools/genere_palette.py --ecrit")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
