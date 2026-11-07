"""Département B — Disposition et rangement (« y'a peu de rangement »)."""
from __future__ import annotations

import ast
import re
from collections import Counter

from noyau import Constat, agent, departement

D = departement("Disposition", "rangement, hiérarchie, densité, alignement")

# noms Qt qui sont des surcharges : jamais « morts »
SURCHARGES = ("paint", "mouse", "key", "wheel", "resize", "event", "show",
              "hide", "enter", "leave", "drag", "drop", "focus", "close",
              "size", "minimum", "update", "retranslate", "change", "init",
              "setup", "context", "draw", "hover", "scroll", "input", "before",
              "after", "header", "data", "flags")


@agent(D, "D-01", "Fenêtres construites dans des méthodes géantes", "majeur")
def methodes_geantes(ctx):
    constats = []
    for rel in ctx.fichiers:
        arbre = ctx.arbres.get(rel)
        if arbre is None or "/ui/" not in rel:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                taille = (n.end_lineno or n.lineno) - n.lineno
                if taille > 180:
                    constats.append(Constat(
                        gravite="majeur", fichier=rel, ligne=n.lineno,
                        mesure=f"`{n.name}` : {taille} lignes",
                        probleme="un seul bloc construit toute une zone "
                                 "d'écran, sans sous-partie nommée",
                        pourquoi="c'est exactement ce qui produit « les "
                                 "catégories sont mal rangées » : personne ne "
                                 "peut retrouver où commence ni où finit un "
                                 "groupe",
                        action="découper en sections nommées (une fonction par "
                               "groupe), et une fonction = un titre à l'écran",
                    ))
    return constats


@agent(D, "D-02", "Empilement trop profond", "mineur")
def imbrication(ctx):
    constats = []
    for rel in ctx.fichiers:
        arbre = ctx.arbres.get(rel)
        if arbre is None:
            continue
        for n in ast.walk(arbre):
            if not isinstance(n, ast.If):
                continue
            p, prof = n, 0
            while p is not None and prof < 40:
                prof += 1
                p = getattr(p, "parent", None)
            break
    # mesure simple : profondeur d'indentation maximale des blocs UI
    pire = (0, "", 0)
    for rel in ctx.fichiers:
        if "/ui/" not in rel:
            continue
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if ligne.strip().startswith(("if ", "for ", "with ", "try")):
                d = (len(ligne) - len(ligne.lstrip())) // 4
                if d > pire[0]:
                    pire = (d, rel, no)
    if pire[0] >= 7:
        constats.append(Constat(
            gravite="mineur", fichier=pire[1], ligne=pire[2],
            mesure=f"imbrication de niveau {pire[0]}",
            probleme="des conditions dans des conditions dans des conditions",
            pourquoi="impossible d'expliquer à l'utilisateur quand une option "
                     "apparaît ou disparaît",
            action="extraire des fonctions nommées : "
                   "`afficher(condition)` remplace trois `if`",
        ))
    return constats


@agent(D, "D-03", "Blocs sans titre : rien n'est annoncé", "majeur")
def sans_titre(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        groupes = len(re.findall(r"QGroupBox\(", txt))
        titres = len(re.findall(r"QGroupBox\([^)]*self\.tr\(\s*[\"'][^\"']+", txt))
        if groupes and titres < groupes:
            constats.append(Constat(
                gravite="mineur", fichier=rel,
                mesure=f"{groupes} groupes, {titres} avec un titre",
                probleme="des groupes de champs sans titre",
                pourquoi="on ne sait pas ce que rassemble le bloc, donc on ne "
                         "sait pas s'il faut y toucher",
                action="tout groupe porte un titre court + une phrase qui dit "
                       "à quoi il sert",
            ))
    return constats


@agent(D, "D-04", "Écrans trop denses : 25 contrôles ou plus dans un bloc", "majeur")
def densite(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        arbre = ctx.arbres.get(rel)
        if arbre is None:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, (ast.FunctionDef,)) and (n.end_lineno or 0) - n.lineno > 60:
                corps = ast.get_source_segment(ctx.sources[rel], n) or ""
                controles = len(re.findall(
                    r"\bQ(CheckBox|ComboBox|SpinBox|DoubleSpinBox|RadioButton|"
                    r"PushButton|LineEdit|Slider)\(", corps))
                if controles >= 25:
                    constats.append(Constat(
                        gravite="majeur", fichier=rel, ligne=n.lineno,
                        mesure=f"`{n.name}` crée {controles} contrôles",
                        probleme="un seul écran propose 40 décisions à la fois",
                        pourquoi="c'est la définition d'une complexité imposée : "
                                 "l'utilisateur ne sait pas par où commencer "
                                 "et ferme le panneau",
                        action="garder 6 réglages visibles, le reste derrière "
                               "« réglages avancés » (règle R-24)",
                    ))
    return constats


@agent(D, "D-05", "Libellés dupliqués d'un écran à l'autre", "majeur")
def libelles_dupliques(ctx):
    """Le même mot pour deux choses différentes, ou deux mots pour la même."""
    textes = Counter()
    lieux = {}
    for rel in ctx.fichiers:
        for m in re.finditer(r"""(?:tr\(\s*)?["']([A-ZÉÀ][^"']{3,42})["']""",
                             ctx.sources[rel]):
            t = m.group(1)
            textes[t] += 1
            lieux.setdefault(t, []).append(rel)
    constats = []
    for t, n in textes.most_common(20):
        if (n >= 4 and len(set(lieux[t])) >= 3
                and "UI" not in t and not t.isupper()
                and not any(k in t.lower() for k in
                            ("segoe", "px", ".png", ".csv", ".py", ".qml"))):
            constats.append(Constat(
                gravite="mineur", mesure=f"« {t} » apparaît {n} fois dans "
                f"{len(set(lieux[t]))} fichiers",
                probleme="le même mot est réécrit à la main partout",
                pourquoi="il finit par désigner deux choses "
                "différentes selon l'écran",
                action="un seul lexique (`lexique.json`) : le mot est défini "
                       "une fois, et chaque écran le lit",
            ))
    return constats


@agent(D, "D-06", "Aucune place pour le vide : pas de respiration", "mineur")
def respiration(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        blocs = len(re.findall(r"addLayout\(|addWidget\(", txt))
        stretches = len(re.findall(r"addStretch\(", txt))
        if blocs > 120 and stretches * 12 < blocs:
            constats.append(Constat(
                gravite="mineur", fichier=rel,
                mesure=f"{blocs} ajouts pour {stretches} respirations",
                probleme="les éléments sont empilés sans marge de respiration",
                pourquoi="un écran plein à ras bord paraît plus compliqué "
                         "qu'il ne l'est, même quand il est bien organisé",
                action="une respiration entre chaque groupe, et un vide "
                       "assumé en bas de panneau",
            ))
    return constats
