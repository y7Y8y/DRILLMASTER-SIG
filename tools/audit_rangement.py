"""Chantier 6 — les rangements, mesurés.

    python3 tools/audit_rangement.py            # tableau
    python3 tools/audit_rangement.py --ecrit    # écrit specs/data/rangement.json

Trois questions, trois mesures :

1. **Quel fichier est trop gros pour être relu ?** Un fichier au-delà de
   1 500 lignes ne se tient plus en tête ; au-delà de 3 000, personne ne le
   relit avant de le modifier.
2. **Quelle part est un journal de versions plutôt que du code ?** Les
   commentaires d'historique (`v2.9.x`) racontent un bug passé : utile une
   fois, coûteux à chaque lecture. On mesure, on ne juge pas à l'œil.
3. **Quelles fonctions sont écrites plusieurs fois ?** Même nom, même
   intention, fichiers différents : la promesse « un seul propriétaire »
   (R-44) ne tient plus.

Aucune de ces mesures ne modifie quoi que ce soit. C'est une balance.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
SEUIL_GROS = 1500          # au-delà : ne se relit plus d'un trait
SEUIL_CRITIQUE = 3000      # au-delà : personne ne le relit avant de le toucher
VERSION = re.compile(r"\bv\d+\.\d+(\.\d+)*\b")


def tailles():
    out = []
    for f in sorted(PLUGIN.rglob("*.py")):
        texte = f.read_text(encoding="utf-8", errors="ignore")
        lignes = texte.splitlines()
        out.append({
            "fichier": str(f.relative_to(PLUGIN)).replace("\\", "/"),
            "lignes": len(lignes),
            "commentaires_de_version": sum(
                1 for l in lignes if VERSION.search(l)
                and l.lstrip().startswith("#")),
        })
    return sorted(out, key=lambda d: -d["lignes"])


def doublons():
    """Même nom de fonction dans plusieurs fichiers — pas une preuve de
    duplication, une invitation à regarder. On ne compte que les fonctions
    de plus de 5 lignes pour éviter les `_tr` et les accesseurs."""
    noms = defaultdict(list)
    for f in PLUGIN.rglob("*.py"):
        try:
            arbre = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, ast.FunctionDef) and n.end_lineno - n.lineno > 5:
                noms[n.name].append(
                    str(f.relative_to(PLUGIN)).replace("\\", "/"))
    return {k: sorted(set(v)) for k, v in noms.items()
            if len(set(v)) > 1}


def main(argv):
    t = tailles()
    d = doublons()
    total = sum(x["lignes"] for x in t)
    gros = [x for x in t if x["lignes"] >= SEUIL_GROS]
    critiques = [x for x in t if x["lignes"] >= SEUIL_CRITIQUE]
    journal = sum(x["commentaires_de_version"] for x in t)

    print(f"── {len(t)} fichiers · {total} lignes")
    print(f"  au-delà de {SEUIL_GROS} lignes : {len(gros)}"
          f"  ({sum(x['lignes'] for x in gros)} lignes, "
          f"{100*sum(x['lignes'] for x in gros)/total:.0f} % du plugin)")
    print(f"  au-delà de {SEUIL_CRITIQUE} lignes : {len(critiques)}"
          f"  ({sum(x['lignes'] for x in critiques)} lignes)")
    print(f"  commentaires d'historique : {journal} lignes")
    print("\n── les 8 plus gros")
    for x in t[:8]:
        barre = "█" * max(1, round(x["lignes"] / 200))
        print(f"  {x['lignes']:6}  {barre:<60} {x['fichier']}")
    print(f"\n── {len(d)} noms de fonctions présents dans plusieurs fichiers")
    for nom, fichiers in sorted(d.items(), key=lambda kv: -len(kv[1]))[:10]:
        print(f"  {nom:32} {' / '.join(f.split('/')[-1] for f in fichiers)}")

    if "--ecrit" in argv:
        sortie = {
            "fichiers": len(t), "lignes": total,
            "gros_fichiers": [x["fichier"] for x in gros],
            "critiques": [x["fichier"] for x in critiques],
            "lignes_de_journal": journal,
            "plus_gros": t[:8],
            # Trié par nom : sans cela, la moindre insertion de ligne
            # réordonne le fichier produit et le rend illisible en diff.
            "noms_partages": {k: d[k] for k in sorted(d)},
        }
        (RACINE / "specs" / "data" / "rangement.json").write_text(
            json.dumps(sortie, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("\nécrit specs/data/rangement.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
