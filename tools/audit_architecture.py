"""Chantier 9 — l'architecture, mesurée : qui importe qui, et qui calcule quoi.

    python3 tools/audit_architecture.py [--ecrit]

R-40 : le noyau ne connaît pas l'interface. On le vérifie par les imports,
pas par la bonne intention. R-41 : une classe d'affichage ne calcule pas —
on cherche la trigonométrie dans les vues.

Les imports relatifs sont résolus contre le paquet du fichier, comme le fait
Python : sans ça, `from .styles_qt import COLORS` ne veut rien dire et l'on
compte des orphelins qui n'existent pas.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
PAQUET = "DrillMaster"

from drillmaster_v3.core.vocabulaire_interdit import SIGNAUX_DE_CALCUL


def calculs_dans(texte):
    """Le MÊME compte que les tests : une seule définition du calcul."""
    return sum(texte.count(s) for s in SIGNAUX_DE_CALCUL)


def modules():
    """nom pointé → chemin, en ignorant le banc d'essai."""
    out = {}
    for f in sorted(PLUGIN.rglob("*.py")):
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        if rel.startswith("tools/") or "__pycache__" in rel:
            continue
        nom = rel[:-3]
        if nom.endswith("/__init__"):
            nom = nom[: -len("/__init__")]
        out[PAQUET + "." + nom.replace("/", ".")] = f
    return out


def _resout(paquet_courant, niveau, mod, nom=None):
    """Résout `from ..core.x import y` depuis le paquet du fichier."""
    base = paquet_courant.split(".")
    if niveau > 1:
        # `from .x` = le paquet du fichier ; `from ..x` = son PARENT.
        # C'est la règle de Python, et l'inverser fait croire que tout le
        # noyau est orphelin — l'erreur exacte de la première version.
        base = base[: len(base) - (niveau - 1)]
    cible = ".".join(base)
    if mod:
        cible = cible + "." + mod
    if nom:
        cible = cible + "." + nom
    return cible


def analyse(f):
    """(imports, Qt, widgets) d'un fichier, imports déjà résolus."""
    texte = f.read_text(encoding="utf-8", errors="ignore")
    rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
    paquet = (PAQUET + "." + rel[:-3].replace("/", ".")).rsplit(".", 1)[0]
    imports, qt, widgets = set(), set(), set()
    try:
        arbre = ast.parse(texte)
    except SyntaxError:
        return imports, qt, widgets
    for n in ast.walk(arbre):
        if isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if n.level:
                imports.add(_resout(paquet, n.level, mod))
                for a in n.names:
                    imports.add(_resout(paquet, n.level, mod, a.name))
            elif mod.startswith(PAQUET):
                imports.add(mod)
                for a in n.names:
                    imports.add(mod + "." + a.name)
            if mod.startswith("qgis.PyQt.QtWidgets"):
                widgets.add(mod)
            elif mod.startswith("qgis.PyQt"):
                qt.add(mod)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith(PAQUET):
                    imports.add(a.name)
                if a.name.startswith("qgis.PyQt.QtWidgets"):
                    widgets.add(a.name)
                elif a.name.startswith("qgis.PyQt"):
                    qt.add(a.name)
    return imports, qt, widgets


def main(argv):
    mods = modules()
    infos = {nom: analyse(f) for nom, f in mods.items()}

    # ── 1 · le noyau connaît-il l'interface ?
    noyau = {n: v for n, v in infos.items() if ".core." in n or n.endswith(".core")}
    fuites = []
    for nom, (imports, qt, widgets) in noyau.items():
        court = nom.replace(PAQUET + ".", "")
        for i in sorted(imports):
            if ".ui." in i or i.endswith(".ui"):
                fuites.append((court, "importe l'interface", i.replace(PAQUET + ".", "")))
        for w in sorted(widgets):
            fuites.append((court, "importe des widgets", w))
    print(f"── le noyau : {len(noyau)} modules")
    print(f"  {len(fuites)} fuite(s) vers l'interface ou les widgets")
    for rel, genre, quoi in fuites[:12]:
        print(f"    {rel:46} {genre:22} {quoi}")
    # Qt n'est pas interdit dans le noyau — les couleurs et le dessin en ont
    # besoin. Ce qui EST interdit, c'est un widget. On mesure les deux
    # séparément plutôt que de confondre « touche à Qt » et « touche à l'UI ».
    peinture = [n.replace(PAQUET + ".", "") for n, (_, qt, _) in noyau.items()
                if qt or _.get(n, (0, 0, 0))[2]] if False else \
        [n.replace(PAQUET + ".", "") for n, (_, qt, widgets) in noyau.items()
         if qt or widgets]
    print(f"  {len(peinture)} module(s) du noyau touchent à Qt (dessin, "
          f"traduction) — permis, mesuré :")
    for r in peinture:
        print(f"    {r}")

    # ── 2 · les calculs dans les vues
    calculs = {}
    for nom, f in mods.items():
        if ".ui." not in nom:
            continue
        n = calculs_dans(f.read_text(encoding="utf-8", errors="ignore"))
        if n:
            calculs[nom.replace(PAQUET + ".", "")] = n
    total = sum(calculs.values())
    print(f"\n── les calculs dans les vues : {total} expressions "
          f"dans {len(calculs)} fichiers")
    for rel, n in sorted(calculs.items(), key=lambda kv: -kv[1])[:8]:
        print(f"    {n:4}  {rel}")

    # ── 3 · le graphe
    importes = set()
    for imports, _, _ in infos.values():
        for i in imports:
            importes.add(i)
    importes_par = {}
    for nom, (imports, _, _) in infos.items():
        for i in imports:
            importes_par.setdefault(i, []).append(nom)
    # un module est importé si son nom EXACT apparaît comme cible d'import
    # (les noms d'objets importés, ex. `core.section.generate_section`,
    # ne doivent pas faire croire qu'un module est branché).
    cibles = set(importes)
    jamais_importes = [n for n in mods
                       if n not in cibles
                       and not any(c.startswith(n + ".") for c in cibles)
                       and n != PAQUET + ".__init__"
                       and n != PAQUET]

    print(f"\n── {len(jamais_importes)} module(s) importé(s) par personne")
    for r in sorted(jamais_importes)[:10]:
        print(f"    {r.replace(PAQUET + '.', '')}")

    if "--ecrit" in argv:
        sortie = {
            "modules": len(mods),
            "modules_noyau": len(noyau),
            "fuites_noyau": [{"module": a, "genre": b, "cible": c}
                             for a, b, c in fuites],
            "calculs_dans_les_vues": total,
            "fichiers_de_vue_avec_calcul": dict(
                sorted(calculs.items(), key=lambda kv: -kv[1])),
            "modules_jamais_importes": sorted(
                r.replace(PAQUET + ".", "") for r in jamais_importes),
        }
        (RACINE / "specs" / "data" / "architecture.json").write_text(
            json.dumps(sortie, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("\nécrit specs/data/architecture.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
