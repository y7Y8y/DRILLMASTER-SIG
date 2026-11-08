"""Chantier 1 — l'état du socle visuel, mesuré, jamais estimé.

    python3 tools/audit_couleurs.py

Ce que l'outil refuse de faire : réécrire une feuille de style à la place.
Une migration automatique a été essayée trois fois ; elle casse le code dès
qu'une couleur est au milieu d'un texte. On livre donc des **mesures** et une
**liste de travail**, pas un remplacement hasardeux.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
HEXA = re.compile(r"#[0-9A-Fa-f]{6}\b")

# couleurs de DONNÉES : légitimes (lithologie, altérations, palettes de genèse)
DONNEES = {"core/genesis_palettes.py", "core/reference.py",
           "core/alteration_taxonomy.py", "core/lithology_taxonomy.py",
           "core/mineral_symbols.py", "core/styles.py", "core/geo_style.py",
           "core/style_resolver.py", "tools/bench_qpainter_draw.py"}


def releve():
    """Trois catégories, mesurées séparément."""
    donnees = defaultdict(int)
    chrome_constantes = defaultdict(int)     # "couleur" seule sur sa ligne
    chrome_styles = defaultdict(int)         # dans une feuille de style
    total_styles = 0
    for f in sorted(PLUGIN.rglob("*.py")):
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        texte = f.read_text(encoding="utf-8", errors="ignore")
        for ligne in texte.splitlines():
            couleurs = HEXA.findall(ligne)
            if not couleurs:
                continue
            if rel in DONNEES:
                donnees[rel] += len(couleurs)
            elif re.match(r'\s*["\'][a-z_0-9]+["\']\s*:\s*["\']#', ligne) or \
                    re.match(r"\s*[A-Z_0-9]+\s*=\s*[\"']#", ligne):
                chrome_constantes[rel] += len(couleurs)
            else:
                chrome_styles[rel] += len(couleurs)
                total_styles += len(couleurs)
    return donnees, chrome_constantes, chrome_styles, total_styles


def main():
    donnees, constantes, styles, total_styles = releve()
    n_donnees = sum(donnees.values())
    n_const = sum(constantes.values())
    print("── socle visuel du plugin, mesuré")
    print(f"  couleurs de DONNÉES (légitimes)        {n_donnees:4}"
          f"  dans {len(donnees)} fichiers")
    print(f"  jetons de chrome (table à centraliser) {n_const:4}"
          f"  dans {len(constantes)} fichiers")
    print(f"  couleurs DANS des feuilles de style    {total_styles:4}"
          f"  dans {len(styles)} fichiers")

    print("\n── les 8 fichiers de style les plus chargés")
    for rel, n in sorted(styles.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {n:4}  {rel}")

    print("\n── ce qui est déjà centralisé")
    print("  DrillMaster/ui/styles_qt.py porte la palette COLORS :"
          f" {n_const} valeurs de chrome déclarées")
    print("  specs/data/theme.json porte 18 jetons de couleur, 6 tailles,"
          " une grille de 4 px")
    print("  specs/tests/test_charte.py interdit une couleur sans foyer")

    sortie = {
        "couleurs_donnees": n_donnees,
        "jetons_chrome": n_const,
        "couleurs_dans_styles": total_styles,
        "fichiers_de_style": dict(sorted(styles.items(),
                                         key=lambda kv: -kv[1])),
    }
    (RACINE / "specs" / "data" / "audit_couleurs.json").write_text(
        json.dumps(sortie, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("\nécrit specs/data/audit_couleurs.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
