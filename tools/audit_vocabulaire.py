"""Chantier 10 — le vocabulaire : deux noms pour un objet, mesuré.

    python3 tools/audit_vocabulaire.py [--ecrit]

Le lexique du dépôt ne compte que s'il est **lu par le code qui affiche**.
On mesure donc séparément :

1. les textes **réellement affichés** (chaînes passées à un widget, à
   `tr(...)`, à une infobulle) — c'est là que le mélange des mots se voit ;
2. les **identifiants** (`hole`, `assay`…) — ils n'ont pas à suivre le
   lexique, mais deux noms pour la même chose y sont un signe de dette ;
3. la **traduction** : un texte affiché en anglais dans une interface
   française est un mot que l'utilisateur ne comprend pas.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"

# Couples de mots qui veulent dire la même chose pour le géologue.
COUPLES = [
    ("forage", "trou", "hole"),
    ("teneur", "analyse", "assay", "grade"),
    ("coupe", "section", "profil"),
    ("collet", "collier", "collar"),
    ("pendage", "inclinaison", "dip"),
    ("piste", "voie", "track"),
]
# Mots qui ressemblent à des variantes mais qui veulent dire autre chose :
# « profil » = profil d'affichage, « trou » = dans « trou de forage »,
# « section » = SectionWidget (un nom de classe passé par erreur à
# l'affichage), « analyse » = les valeurs analysées, pas la piste.
EXCEPTIONS = {"profil", "trou", "section", "analyse", "collier"}

# Les méthodes Qt qui reçoivent un texte affiché.
AFFICHAGE = {
    "setText", "setTitle", "setToolTip", "setPlaceholderText", "setWindowTitle",
    "setWhatsThis", "setStatusTip", "addItem", "addItems", "setLabel",
    "setSuffix", "setPrefix", "setHtml", "showMessage", "information",
    "warning", "critical", "question", "translate", "tr",
}


def textes_affiches(f: Path):
    """Les chaînes réellement montrées : argument d'un appel d'affichage."""
    out = []
    try:
        arbre = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return out
    for n in ast.walk(arbre):
        if not isinstance(n, ast.Call):
            continue
        nom = getattr(n.func, "attr", getattr(n.func, "id", ""))
        if nom not in AFFICHAGE:
            continue
        for a in list(n.args) + [k.value for k in n.keywords]:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.append((n.lineno, a.value))
            elif isinstance(a, ast.Constant) is False:
                for sous in ast.walk(a):
                    if isinstance(sous, ast.Constant) and isinstance(sous.value, str) \
                            and len(sous.value) > 3:
                        out.append((n.lineno, sous.value))
    return out


def identifiants(f: Path):
    texte = f.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"\b[a-z][a-z_]{2,}\b", texte.lower()))


def main(argv):
    textes = []
    ids = Counter()
    for f in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in str(f):
            continue
        textes.extend(textes_affiches(f))
        ids.update(identifiants(f))

    # ── 1 · les couples de mots dans les textes affichés
    print(f"── {len(textes)} textes affichés, analysés")
    bruit = 0
    for groupe in COUPLES:
        compte = Counter()
        exemples = {}
        for no, t in textes:
            bas = t.lower()
            for mot in groupe:
                if re.search(rf"\b{mot}\w*\b", bas):
                    compte[mot] += 1
                    exemples.setdefault(mot, t[:50])
        if len(compte) > 1:
            print(f"\n  « {groupe[0]} » se dit de {len(compte)} façons :")
            for mot, n in compte.most_common():
                # Un mot qui vit dans une phrase (« profil » de la coupe,
                # « trou » dans « trou de forage ») n'est pas une variante :
                # il faut le compter comme du bruit, pas comme une dette.
                doute = mot in EXCEPTIONS
                if doute:
                    bruit += n
                print(f"    {n:4}×  {mot:12} "
                      f"{'(autre sens — bruit)' if doute else '(variante)'}"
                      f" ex. « {exemples[mot]} »")
    print(f"\n  dont {bruit} occurrence(s) d'un mot qui a un AUTRE sens : "
          "ce n'est pas un synonyme à supprimer.")

    # ── 2 · les identifiants
    print("\n── identifiants (le code, pas l'écran) : la même dette en miroir")
    for groupe in COUPLES:
        presents = {m: ids[m] for m in groupe if ids.get(m)}
        if len(presents) > 1:
            print("    " + " · ".join(f"{m} {n}×" for m, n in
                                      sorted(presents.items(), key=lambda kv: -kv[1])))

    # ── 3 · le lexique est-il lu ?
    lit = 0
    for f in PLUGIN.rglob("*.py"):
        if "lexique" in f.read_text(encoding="utf-8", errors="ignore").lower():
            lit += 1
    print(f"\n── fichiers du plugin qui lisent le lexique : {lit}")

    if "--ecrit" in argv:
        sortie = {"textes_affiches": len(textes), "fichiers_lisant_le_lexique": lit,
                  "couples": {}}
        for groupe in COUPLES:
            compte = Counter()
            for no, t in textes:
                for mot in groupe:
                    if re.search(rf"\b{mot}\w*\b", t.lower()):
                        compte[mot] += 1
            if len(compte) > 1:
                sortie["couples"][groupe[0]] = dict(compte)
        (RACINE / "specs" / "data" / "vocabulaire.json").write_text(
            json.dumps(sortie, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("\nécrit specs/data/vocabulaire.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
