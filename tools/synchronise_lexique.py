"""Le lexique : une source, une copie, zéro dérive.

    python3 tools/synchronise_lexique.py           # vérifie
    python3 tools/synchronise_lexique.py --ecrit    # recopie

`specs/data/lexique.json` est la source. Le plugin a besoin du fichier à
côté de lui une fois installé dans QGIS : il en garde donc une copie dans
`DrillMaster/core/lexique.json`. Deux fichiers, une seule vérité — et un
outil qui refuse la dérive, comme pour la palette (R-50).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SOURCE = RACINE / "specs" / "data" / "lexique.json"
COPIE = RACINE / "DrillMaster" / "core" / "lexique.json"


def main(argv):
    if not SOURCE.exists():
        print(f"source absente : {SOURCE}")
        return 1
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    if "--ecrit" in argv:
        shutil.copy(SOURCE, COPIE)
        print(f"copié → {COPIE.relative_to(RACINE)}")
        return 0
    if not COPIE.exists():
        print("la copie du plugin n'existe pas")
        return 1
    if json.loads(COPIE.read_text(encoding="utf-8")) != source:
        print("dérive : la copie du plugin ne correspond plus au lexique")
        print("  python3 tools/synchronise_lexique.py --ecrit")
        return 1
    print(f"à jour — {len(source['interdits'])} mots bannis, "
          f"{len(source['types_donnees'])} types de données")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
