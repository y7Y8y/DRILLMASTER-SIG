"""Mesure la forme des fonctions du plugin (le pendant de test_forme.py)."""
from __future__ import annotations
import ast, json, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
SORTIE = RACINE / "specs" / "data" / "formes.json"
SEUILS = (80, 150, 250, 400)


def fonctions(chemin):
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    vues = []
    def descendre(noeud, profondeur=1):
        for e in ast.iter_child_nodes(noeud):
            if isinstance(e, (ast.FunctionDef, ast.AsyncFunctionDef)):
                vues.append((e, profondeur))
                descendre(e, profondeur + 1)
            else:
                descendre(e, profondeur)
    descendre(arbre)
    return vues


def mesure():
    fichiers = sorted(p for p in PLUGIN.rglob("*.py") if "__pycache__" not in str(p))
    total = courtes = 0
    compte = {str(s): 0 for s in SEUILS}
    plus_grandes, repliees = [], []
    classes_pire, methodes_pire = ("", "", 0), ("", "", 0)
    for f in fichiers:
        rel = str(f.relative_to(PLUGIN))
        source = f.read_text(encoding="utf-8")
        arbre = ast.parse(source)
        for c in [n for n in arbre.body if isinstance(n, ast.ClassDef)]:
            l = c.end_lineno - c.lineno + 1
            if l > classes_pire[2]:
                classes_pire = (c.name, rel, l)
            n = sum(1 for e in c.body if isinstance(e, (ast.FunctionDef, ast.AsyncFunctionDef)))
            if n > methodes_pire[2]:
                methodes_pire = (c.name, rel, n)
        for noeud, profondeur in fonctions(f):
            total += 1
            l = noeud.end_lineno - noeud.lineno + 1
            if l < 40:
                courtes += 1
            for s in SEUILS:
                if l >= s:
                    compte[str(s)] += 1
            if l >= 80:
                plus_grandes.append({"nom": noeud.name, "fichier": rel,
                                     "ligne": noeud.lineno, "lignes": l})
            imbriquees = [e for e in ast.walk(noeud)
                          if isinstance(e, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and e is not noeud
                          and not e.name.startswith(("genexpr", "lambda",
                                                     "listcomp", "setcomp", "dictcomp"))]
            if imbriquees:
                repliees.append({"nom": noeud.name, "fichier": rel,
                                 "ligne": noeud.lineno, "lignes": l,
                                 "fonctions_nommees": len(imbriquees)})
    plus_grandes.sort(key=lambda d: -d["lignes"])
    repliees.sort(key=lambda d: -d["fonctions_nommees"])
    return {
        "fonctions": total,
        "courtes_moins_de_40": courtes,
        "part_courtes": round(courtes / total, 4),
        "par_seuil": compte,
        "plus_grandes": plus_grandes[:12],
        "plus_grosse_classe": {"nom": classes_pire[0], "fichier": classes_pire[1],
                               "lignes": classes_pire[2]},
        "classe_la_plus_de_methodes": {"nom": methodes_pire[0],
                                       "fichier": methodes_pire[1],
                                       "methodes": methodes_pire[2]},
        "fonctions_repliees": repliees[:10],
    }


def main(argv):
    d = mesure()
    print(f"── {d['fonctions']} fonctions dans le plugin")
    print(f"   {d['courtes_moins_de_40']} de moins de 40 lignes "
          f"({d['part_courtes']:.1%})")
    for s in SEUILS:
        print(f"   {d['par_seuil'][str(s)]:3} fonction(s) de {s} lignes et plus")
    print(f"\n── la plus grosse classe : {d['plus_grosse_classe']['nom']} "
          f"({d['plus_grosse_classe']['fichier']}, "
          f"{d['plus_grosse_classe']['lignes']} lignes)")
    print(f"── la classe qui porte le plus de méthodes : "
          f"{d['classe_la_plus_de_methodes']['nom']} "
          f"({d['classe_la_plus_de_methodes']['methodes']})")
    print("\n── les 8 plus grandes fonctions")
    for g in d["plus_grandes"][:8]:
        print(f"   {g['lignes']:4} l.  {g['nom']:32} {g['fichier']}:{g['ligne']}")
    print("\n── le code replié : fonctions nommées à l'intérieur d'une fonction")
    for r in d["fonctions_repliees"][:6]:
        print(f"   {r['fonctions_nommees']:2}  {r['nom']:32} "
              f"{r['fichier']}:{r['ligne']} ({r['lignes']} l.)")
    if "--ecrit" in argv:
        SORTIE.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print(f"\nécrit {SORTIE.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
