"""Chantier 8 — la navigation : ce qui est atteignable, et par où.

    python3 tools/audit_navigation.py [--ecrit]

Trois questions, mesurées dans le code réel :

1. **Combien d'écrans, combien de chemins ?** Un écran qui ne s'ouvre que par un
   chemin est un écran caché. On compte les entrées par écran.
2. **Y a-t-il des réglages sans porte ?** Un `QSettings` lu mais jamais écrit
   (ou l'inverse) est un réglage fantôme : il existe pour le développeur,
   pas pour l'utilisateur.
3. **Que peut-on faire sans savoir ?** Un raccourci clavier non documenté est
   un pouvoir invisible ; un bouton sans texte d'aide est un pari.

Sortie lisible par un humain, plus `specs/data/navigation.json` avec `--ecrit`.
"""
from __future__ import annotations

import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"


def noeuds_classes():
    """Toutes les classes de fenêtre/dialogue du plugin, avec leur nature."""
    out = []
    for f in sorted(PLUGIN.rglob("*.py")):
        texte = f.read_text(encoding="utf-8", errors="ignore")
        try:
            arbre = ast.parse(texte)
        except SyntaxError:
            continue
        for n in ast.walk(arbre):
            if not isinstance(n, ast.ClassDef):
                continue
            bases = " ".join(ast.unparse(b) for b in n.bases)
            genre = None
            for mot in ("QDialog", "QDockWidget", "QMainWindow", "QWidget"):
                if mot in bases:
                    genre = mot
                    break
            if genre:
                out.append({"classe": n.name, "genre": genre,
                            "fichier": str(f.relative_to(PLUGIN))
                            .replace("\\", "/"), "ligne": n.lineno})
    return out


def entrees():
    """Les endroits qui ouvrent un écran.

    On compte DEUX façons d'ouvrir : instancier la classe
    (`XxxDialog(...)`) et appeler dessus `exec_` / `show` / `popup`.
    Compter une seule des deux produit de faux « jamais ouvert » — c'est
    arrivé à la première version de cet outil, et un constat faux est pire
    qu'aucun constat.
    """
    par_cible = defaultdict(list)
    for f in sorted(PLUGIN.rglob("*.py")):
        texte = f.read_text(encoding="utf-8", errors="ignore")
        try:
            arbre = ast.parse(texte)
        except SyntaxError:
            continue
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        for n in ast.walk(arbre):
            if not isinstance(n, ast.Call):
                continue
            nom = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if nom in ("exec_", "exec", "show", "showMaximized", "popup"):
                if isinstance(n.func, ast.Attribute):
                    par_cible[ast.unparse(n.func.value).split(".")[-1]].append(
                        {"fichier": rel, "ligne": n.lineno, "geste": nom})
            elif nom and nom.lstrip("_")[:1].isupper():   # instanciation
                par_cible[nom].append({"fichier": rel, "ligne": n.lineno,
                                       "geste": "instance"})
    return par_cible


def reglages_fantomes():
    """QSettings : une valeur lue mais jamais écrite n'existe pas pour l'usager.

    Analyse par arbre, pas ligne à ligne : un appel écrit sur deux lignes
    (`setValue(\n "DrillMaster/x", …)`) échappe à une expression régulière.
    La première version de cet outil l'a fait et a annoncé trois « valeurs
    fantômes » qui n'existaient pas.
    """
    lus, ecrits = Counter(), Counter()
    for f in sorted(PLUGIN.rglob("*.py")):
        texte = f.read_text(encoding="utf-8", errors="ignore")
        try:
            arbre = ast.parse(texte)
        except SyntaxError:
            continue
        for n in ast.walk(arbre):
            if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Attribute):
                continue
            if n.func.attr not in ("value", "setValue") or not n.args:
                continue
            premier = n.args[0]
            if not (isinstance(premier, ast.Constant)
                    and isinstance(premier.value, str)):
                continue
            cible = lus if n.func.attr == "value" else ecrits
            cible[premier.value] += 1
    return lus, ecrits


def _nom_touche(texte):
    """`QKeySequence("Ctrl+E")` → « Ctrl+E ». Lisible, sans jargon."""
    import re
    m = re.search(r'["\']([^"\']+)["\']', texte)
    if m:
        return m.group(1)
    return texte.split(".")[-1].strip("()")


def raccourcis():
    """Chaque raccourci, et s'il est écrit quelque part sur le bouton.

    R-58 : une touche qui n'est affichée nulle part est un pouvoir invisible.
    Un `setShortcut(...)` de Qt est affiché d'office (dans son infobulle) ;
    un `QShortcut(...)` posé sur un widget, jamais.
    """
    out = []
    for f in sorted(PLUGIN.rglob("*.py")):
        texte = f.read_text(encoding="utf-8", errors="ignore")
        try:
            arbre = ast.parse(texte)
        except SyntaxError:
            continue
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        for n in ast.walk(arbre):
            if not isinstance(n, ast.Call):
                continue
            nom = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if nom not in ("QShortcut", "setShortcut"):
                continue
            touche = ast.unparse(n.args[0]) if n.args else "?"
            out.append({"fichier": rel, "ligne": n.lineno,
                        "genre": "posé sur un widget" if nom == "QShortcut"
                        else "attaché au bouton",
                        "touche": _nom_touche(touche),
                        "affiche": nom == "setShortcut"})
    return out


def main(argv):
    classes = noeuds_classes()
    ouv = entrees()
    lus, ecrits = reglages_fantomes()
    racc = raccourcis()

    genres = Counter(c["genre"] for c in classes)
    jamais_ouverts = [c for c in classes
                      if c["genre"] == "QDialog"
                      and not ouv.get(c["classe"])]
    fantomes = sorted(set(lus) - set(ecrits))
    orphelins = sorted(set(ecrits) - set(lus))

    print("── les écrans du plugin")
    for g, n in genres.most_common():
        print(f"  {g:14} {n:3}")
    print(f"\n── {len(jamais_ouverts)} dialogue(s) jamais ouvert(s) dans le code")
    for c in jamais_ouverts[:10]:
        print(f"  {c['classe']:38} {c['fichier']}:{c['ligne']}")
    print(f"\n── réglages mémorisés : {len(lus)} lus, {len(ecrits)} écrits")
    print(f"  {len(fantomes)} lus mais jamais écrits (valeur fantôme)")
    for k in fantomes[:8]:
        print(f"    {k}")
    print(f"  {len(orphelins)} écrits mais jamais relus (réglage mort)")
    for k in orphelins[:8]:
        print(f"    {k}")
    muets = [r for r in racc if not r["affiche"]]
    print(f"\n── {len(racc)} raccourcis clavier")
    for r in racc:
        etat = "affiché sur le bouton" if r["affiche"] else "MUET (R-58)"
        print(f"  {r['touche']:10} {etat:22} {r['fichier']}:{r['ligne']}")
    print(f"  {len(muets)} raccourci(s) sans touche écrite à l'écran")

    if "--ecrit" in argv:
        sortie = {"ecrans": dict(genres),
                  "dialogues_jamais_ouverts": [c["classe"] for c in jamais_ouverts],
                  "reglages_lus": len(lus), "reglages_ecrits": len(ecrits),
                  "fantomes": fantomes, "morts": orphelins,
                  "raccourcis": racc,
                  "raccourcis_muets": len(muets)}
        (RACINE / "specs" / "data" / "navigation.json").write_text(
            json.dumps(sortie, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("\nécrit specs/data/navigation.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
