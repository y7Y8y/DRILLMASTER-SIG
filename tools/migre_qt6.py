"""Migration Qt 5 → Qt 6 : la seule mécanique du chantier 12.

    python3 tools/migre_qt6.py            # montre ce qui changerait (aucune écriture)
    python3 tools/migre_qt6.py --ecrit    # réécrit les fichiers concernés
    python3 tools/migre_qt6.py --vers 3   # annule : remet la forme Qt 5

Pourquoi une mécanique et pas une réécriture
--------------------------------------------
692 sites dans 37 fichiers : personne ne les corrige à la main sans se
tromper. La correspondance vit dans `drillmaster_v3/core/installation.py`
(`ENUMS_QT6`) : la même table sert à **mesurer** (`audit_installation.py`)
et à **corriger** (cet outil). Une table qui ne sert qu'à constater ne vaut
pas mieux que pas de table.

Ce que cet outil ne fait pas
----------------------------
Il ne touche ni les chaînes de caractères (les feuilles de style ne sont
pas du code Qt), ni les commentaires. Il ne décide rien : chaque
correspondance est écriture littérale de la table. Et il ne dit **jamais**
que le plugin tourne sur QGIS 4 — il dit combien de sites restent.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.installation import ENUMS_QT6  # noqa: E402

# Les classes dont les membres sont cherchés quand la table ne donne qu'un
# nom court (`AlignCenter` → `Qt.AlignmentFlag.AlignCenter`).
CLASSES = ("Qt", "QDialog", "QDialogButtonBox", "QMessageBox", "QPainter",
           "QFont", "QFrame", "QHeaderView", "QAbstractItemView",
           "QSizePolicy", "QStyle", "QKeySequence", "QComboBox")

CORRESPONDANCES = {}
for _cle, _cible in ENUMS_QT6.items():
    CORRESPONDANCES[_cle] = _cible
for _classe in CLASSES:
    for _cle, _cible in ENUMS_QT6.items():
        if "." not in _cle and "." not in _cible:
            CORRESPONDANCES[f"{_classe}.{_cle}"] = f"{_classe}.{_cible}.{_cle}"


def _sites(texte: str):
    """Les sites mesurés par `ast` : (ligne, début, fin, remplacement)."""
    arbre = ast.parse(texte)
    sites = []
    for n in ast.walk(arbre):
        if not hasattr(n, "end_col_offset"):
            continue
        if isinstance(n, ast.Attribute):
            forme = ast.unparse(n)
            cible = CORRESPONDANCES.get(forme)
            if cible and n.lineno == n.end_lineno:
                sites.append((n.lineno, n.col_offset, n.end_col_offset, cible))
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "exec_"):
            f = n.func
            if f.lineno == f.end_lineno:
                fin = f.end_col_offset
                sites.append((f.lineno, fin - len("exec_"), fin, "exec"))
    return sites


def corriger(texte: str):
    """Réécrit les sites mesurés. Retourne (texte, nombre de corrections).

    On remplace **exactement** les bornes que `ast` a désignées : une chaîne
    de caractères qui parle de `Qt.AlignCenter` n'est pas du code Qt, elle
    n'est pas touchée. C'est la différence entre corriger et réécrire.
    """
    sites = _sites(texte)
    if not sites:
        return texte, 0
    lignes = texte.splitlines(keepends=True)
    n = 0
    for ligne, debut, fin, remplacement in sorted(sites, reverse=True):
        source = lignes[ligne - 1]
        lignes[ligne - 1] = source[:debut] + remplacement + source[fin:]
        n += 1
    return "".join(lignes), n


INVERSE = {}
for _cle, _cible in CORRESPONDANCES.items():
    INVERSE.setdefault(_cible, _cle)


def inverse(texte: str):
    """--vers 3 : remet la forme Qt 5, par les mêmes bornes mesurées."""
    arbre = ast.parse(texte)
    sites = []
    for n in ast.walk(arbre):
        if isinstance(n, ast.Attribute) and hasattr(n, "end_col_offset"):
            forme = ast.unparse(n)
            ancienne = INVERSE.get(forme)
            if ancienne and n.lineno == n.end_lineno:
                sites.append((n.lineno, n.col_offset, n.end_col_offset,
                              ancienne))
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "exec"):
            f = n.func
            if f.lineno == f.end_lineno:
                sites.append((f.lineno, f.end_col_offset - len("exec"),
                              f.end_col_offset, "exec_"))
    if not sites:
        return texte
    lignes = texte.splitlines(keepends=True)
    for ligne, debut, fin, remplacement in sorted(sites, reverse=True):
        source = lignes[ligne - 1]
        lignes[ligne - 1] = source[:debut] + remplacement + source[fin:]
    return "".join(lignes)


def main(argv):
    ecrit = "--ecrit" in argv
    vers3 = "--vers" in argv and argv[argv.index("--vers") + 1] == "3"
    total = 0
    fichiers = 0
    par_fichier = {}
    for f in sorted(PLUGIN.rglob("*.py")):
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        if "__pycache__" in rel:
            continue
        texte = f.read_text(encoding="utf-8")
        if vers3:
            neuf = inverse(texte)
            n = sum(texte.count(c) for c in CORRESPONDANCES.values())
        else:
            try:
                neuf, n = corriger(texte)
            except SyntaxError as exc:
                print(f"  illisible : {rel} ({exc})")
                continue
        if n:
            par_fichier[rel] = n
            total += n
            fichiers += 1
            if ecrit and neuf != texte:
                f.write_text(neuf, encoding="utf-8")
    for nom, n in sorted(par_fichier.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {n:4}  {nom}")
    print(f"\n{total} site(s) dans {fichiers} fichier(s)"
          + (" — écrits" if ecrit else " — mesure seule, rien n'est écrit"))
    if not ecrit:
        print("relancer avec --ecrit pour appliquer")

    # L'état après migration, mesuré par l'audit — pas par la table seule.
    sys.path.insert(0, str(RACINE / "tools"))
    import audit_installation
    enums, exec_restants, champs = audit_installation.sites_qt6()
    print(f"reste, mesuré par l'audit : {len(enums)} forme(s) ancienne(s) · "
          f"{len(exec_restants)} exec_() · {len(champs)} type(s) de champ")
    print("QGIS 4 ne se promet pas sur ce seul chiffre : il s'éprouve dans "
          "un QGIS 4 réel.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
