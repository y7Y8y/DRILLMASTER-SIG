"""Les deux Qt, éprouvés sur des données réelles — pas sur promesse.

    python3 tools/verifie_qt6.py [--ecrit]

`migre_qt6.py` réécrit selon une table, et une table peut se tromper : elle
s'est trompée. `Qt.TextInteractionFlag.TextWordWrap` n'existe sur aucune des
deux versions ; la vraie forme est `Qt.TextFlag.TextWordWrap`, valable sur Qt 5
comme sur Qt 6. Une migration qui casse Qt 5 pour faire plaisir à Qt 6 rend le
plugin inutilisable chez ceux qui l'emploient aujourd'hui.

D'où deux épreuves, sur deux sources distinctes :

1. **Qt 5, à l'exécution.** PyQt5 est installé dans un environnement jetable
   (`/tmp`, hors du dépôt) et chaque forme employée y est résolue pour de vrai.
   QtGui et QtWidgets ne s'importent pas ici (`libGL` absent) : l'outil le dit
   et mesure ce qu'il peut mesurer.
2. **Les deux, dans les déclarations livrées.** PyQt5 et PyQt6 publient des
   fichiers `.pyi` qui déclarent chaque classe et chaque membre. On y vérifie
   que la classe existe, que l'énumération y est imbriquée, et que le membre y
   figure — côté 5 comme côté 6.

Ce que cet outil ne dit jamais : « ça tourne sur QGIS 4 ». Aucun QGIS 4 n'a
été ouvert ici ; `specs/data/qt6.json` le consigne noir sur blanc.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
SORTIE = RACINE / "specs" / "data" / "qt6.json"

# classe → (module PyQt, module PyQt6)
CLASSES = {
    "Qt": "QtCore",
    "QDialog": "QtWidgets",
    "QDialogButtonBox": "QtWidgets",
    "QMessageBox": "QtWidgets",
    "QPainter": "QtGui",
    "QFont": "QtGui",
    "QFrame": "QtWidgets",
    "QHeaderView": "QtWidgets",
    "QAbstractItemView": "QtWidgets",
    "QSizePolicy": "QtWidgets",
    "QStyle": "QtWidgets",
    "QKeySequence": "QtGui",
    "QComboBox": "QtWidgets",
}

SONDE = r'''# -*- coding: utf-8 -*-
"""Rejoue chaque forme dans le PyQt5 réellement installé (QtCore seulement :
QtGui et QtWidgets exigent libGL, absent ici)."""
import json, sys
formes = json.load(sys.stdin)
from PyQt5 import QtCore
sortie = {}
for forme in formes:
    premier = forme.split(".")[0]
    try:
        objet = QtCore.Qt if premier == "Qt" else getattr(QtCore, premier)
        for morceau in forme.split(".")[1:]:
            objet = getattr(objet, morceau)
        sortie[forme] = "ok"
    except Exception as exc:
        sortie[forme] = type(exc).__name__
json.dump(sortie, sys.stdout)
'''


def formes_employees():
    """Toutes les formes à trois niveaux employées par le plugin."""
    formes = set()
    for f in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in str(f):
            continue
        try:
            arbre = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, ast.Attribute):
                texte = ast.unparse(n)
                if texte.split(".")[0] in CLASSES and texte.count(".") >= 2:
                    formes.add(texte)
    return sorted(formes)


# ── lecture des déclarations .pyi ───────────────────────────────────
BLOC = re.compile(r"^(?P<indent>\s*)class (?P<nom>\w+)\((?P<bases>[^)]*)\):")
MEMBRE = re.compile(r"^(?P<indent>\s*)(?P<nom>\w+)\s*(?::|=)")


def declarations(chemin: Path) -> dict:
    """{"Qt", "Qt.Orientation", …, "QDialog", …} → {membres, classes}.

    La clé est le **chemin complet** : plusieurs classes Qt s'appellent
    `Orientation` (`Qt.Orientation`, `QPageLayout.Orientation`). Les confondre
    ferait refuser un membre valable — c'est arrivé à la première version de
    cet outil, et un constat faux est pire qu'aucun constat (R-47).
    """
    if not chemin.is_file():
        return {}
    arbre = {}
    pile = []          # (indentation du bloc, indentation des membres, chemin)
    for ligne in chemin.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not ligne.strip() or ligne.lstrip().startswith("#"):
            continue
        m = BLOC.match(ligne)
        if m:
            indent = len(m.group("indent"))
            while pile and pile[-1][0] >= indent:
                pile.pop()
            nom = m.group("nom")
            chemin_complet = ".".join([c for _, _, c in pile] + [nom])
            arbre.setdefault(chemin_complet, {"membres": set(),
                                              "classes": set()})
            if pile:
                arbre[pile[-1][2]]["classes"].add(nom)
            # les membres d'une classe sont exactement à indent + 4 ; une
            # ligne plus indentée appartient à la classe imbriquée
            pile.append((indent, indent + 4, chemin_complet))
            continue
        m = MEMBRE.match(ligne)
        if m and pile and len(m.group("indent")) == pile[-1][1]:
            arbre[pile[-1][2]]["membres"].add(m.group("nom"))
    return arbre


def verifie_forme(arbre: dict, forme: str) -> str:
    """« ok » ou la raison du refus, dans une déclaration .pyi."""
    morceaux = forme.split(".")
    classe = arbre.get(morceaux[0])
    if classe is None:
        return f"classe {morceaux[0]} absente"
    if len(morceaux) == 2:
        return "ok" if morceaux[1] in classe["membres"] else \
            f"{morceaux[1]} absent de {morceaux[0]}"
    enum, valeur = morceaux[1], morceaux[2]
    if enum not in classe["classes"]:
        return f"énumération {enum} absente de {morceaux[0]}"
    sous = arbre.get(f"{morceaux[0]}.{enum}")
    if sous is None:
        return f"énumération {enum} non déclarée"
    return "ok" if valeur in sous["membres"] else \
        f"{valeur} absent de {morceaux[0]}.{enum}"


def eprouve_a_l_execution(formes):
    """Qt 5 à l'exécution, dans un environnement jetable hors du dépôt."""
    venv = Path(tempfile.mkdtemp(prefix="qt5-"))
    if subprocess.run([sys.executable, "-m", "venv", str(venv)],
                      capture_output=True).returncode:
        return "environnement impossible", {}
    python = str(venv / "bin" / "python")
    if subprocess.run([python, "-m", "pip", "install", "--quiet", "PyQt5"],
                      capture_output=True).returncode:
        return "PyQt5 non installable ici", {}
    r = subprocess.run([python, "-c", SONDE], input=json.dumps(formes),
                       capture_output=True, text=True)
    if r.returncode:
        return "sonde en échec : " + r.stderr.strip()[-160:], {}
    version = subprocess.run(
        [python, "-c", "from PyQt5.QtCore import QT_VERSION_STR;"
                       "print(QT_VERSION_STR)"],
        capture_output=True, text=True).stdout.strip()
    return f"PyQt5 dans un environnement jetable (Qt {version})", \
        json.loads(r.stdout)


def main(argv):
    formes = formes_employees()
    etat, execution = eprouve_a_l_execution(formes)

    # À l'exécution, QtCore seul est importable ici : QtGui et QtWidgets
    # exigent libGL, absent du bac à sable. Un « AttributeError » sur ces
    # classes veut donc dire « non éprouvable ici », jamais « refusé ».
    import importlib.util
    spec_core = importlib.util.find_spec("PyQt5.QtCore")
    formes_qtcore = [f for f in formes if f.split(".")[0] == "Qt"]
    refus_execution = {f: e for f, e in execution.items()
                       if e != "ok" and f in formes_qtcore}
    non_eprouvees = len(execution) - len(formes_qtcore)

    print("── Qt 5, à l'exécution")
    print(f"  {etat}")
    print(f"  {len(formes_qtcore)} forme(s) éprouvée(s) pour de vrai dans "
          f"QtCore · {len(refus_execution)} refusée(s)")
    print(f"  {non_eprouvees} forme(s) non éprouvables ici : leurs classes "
          f"vivent dans QtGui et QtWidgets, qui exigent libGL (absent)")
    for forme, erreur in sorted(refus_execution.items())[:10]:
        print(f"    REFUS {erreur} {forme}")

    # Les déclarations livrées : la seule source qui couvre QtGui et
    # QtWidgets sans bibliothèque graphique — et la seule qui dise ce que
    # Qt 6 accepte.
    import importlib.util
    racines = {}
    for nom, module in (("qt5", "PyQt5"), ("qt6", "PyQt6")):
        spec = importlib.util.find_spec(module)
        racines[nom] = Path(spec.submodule_search_locations[0]) if spec else None
    if racines["qt5"] is None or racines["qt6"] is None:
        print("\n── déclarations indisponibles : ni PyQt5 ni PyQt6 ici")
        print("  rien n'est affirmé sur Qt 6")
        return 2

    declarations5, declarations6 = {}, {}
    for classe, module in CLASSES.items():
        declarations5.setdefault(classe, []).append(
            declarations(racines["qt5"] / f"{module}.pyi"))
        declarations6.setdefault(classe, []).append(
            declarations(racines["qt6"] / f"{module}.pyi"))
    fusion5 = {}
    fusion6 = {}
    for source, cible in ((declarations5, fusion5), (declarations6, fusion6)):
        for classe, arbres in source.items():
            for arbre in arbres:
                cible.update(arbre)

    print("\n── les déclarations livrées par les deux PyQt")
    print(f"  PyQt5 : {racines['qt5'].parent}")
    print(f"  PyQt6 : {racines['qt6'].parent}")
    refus5, refus6 = [], []
    for forme in formes:
        r5 = verifie_forme(fusion5, forme)
        r6 = verifie_forme(fusion6, forme)
        if r5 != "ok":
            refus5.append((forme, r5))
        if r6 != "ok":
            refus6.append((forme, r6))
    print(f"  {len(formes)} formes employées par le plugin")
    print(f"  acceptées par Qt 5 : {len(formes) - len(refus5)} · "
          f"refusées : {len(refus5)}")
    print(f"  acceptées par Qt 6 : {len(formes) - len(refus6)} · "
          f"refusées : {len(refus6)}")
    for forme, raison in refus5[:8]:
        print(f"    Qt 5 REFUSE  {forme} — {raison}")
    for forme, raison in refus6[:8]:
        print(f"    Qt 6 REFUSE  {forme} — {raison}")

    print("\n── le verdict, forme par forme")
    verdicts = []
    for forme in formes:
        v5 = forme not in dict(refus5)
        v6 = forme not in dict(refus6)
        if v5 and v6:
            continue
        verdicts.append({"forme": forme, "qt5": v5, "qt6": v6,
                         "execution": execution.get(forme, "non éprouvable ici")})
        etat = "les deux" if v5 else ("Qt 6 seulement" if v6 else "AUCUN")
        print(f"    {etat:16} {forme}")
        if not v6 and forme.endswith("AdjustToMinimumContentsLength"):
            print("                     → retirée de Qt 6 : employer "
                  "AdjustToMinimumContentsLengthWithIcon")
        if not v5 and not v6:
            print("                     → à remplacer à la main : "
                  "l'outil ne devine pas")
    print(f"    {len(formes) - len(verdicts)} formes valables sur les deux")

    print("\n  « ça tourne sur QGIS 4 » n'est PAS prouvé ici : aucun QGIS 4 "
          "n'a été ouvert.")

    if "--ecrit" in argv:
        SORTIE.write_text(json.dumps({
            "execution_qt5": {"etat": etat, "formes": len(execution),
                              "refusees": refus_execution},
            "declarations": {
                "formes": len(formes),
                "qt5_refusees": {f: r for f, r in refus5},
                "qt6_refusees": {f: r for f, r in refus6},
                "qt5_acceptees": len(formes) - len(refus5),
                "qt6_acceptees": len(formes) - len(refus6),
                "verdicts": verdicts,
            },
            "epreuve_reelle_qgis4": False,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("\nécrit specs/data/qt6.json")
    return 0 if not (refus5 or refus6) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
