"""Département A — Direction artistique (minimalisme maîtrisé, Apple-like).

Chef de département : il possède la couleur, la typographie, l'espace.
Ses agents ne jugent pas le goût : ils comptent ce qui est décidé deux fois.
"""
from __future__ import annotations

import re
from collections import Counter

from noyau import Constat, agent, compte, departement

D = departement("Direction artistique", "couleur, typographie, espace, icônes")


@agent(D, "DA-01", "Couleurs écrites en dur au lieu d'un jeton", "majeur")
def couleurs_en_dur(ctx):
    """Une couleur littérale ne peut pas être changée partout d'un coup."""
    hexa = re.compile(r"#[0-9A-Fa-f]{6}\b")
    par_fichier = Counter()
    exemples = {}
    for rel in ctx.fichiers:
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            for m in hexa.finditer(ligne):
                par_fichier[rel] += 1
                exemples.setdefault(rel, (no, m.group(0)))
    total = sum(par_fichier.values())
    constats = []
    constats.append(Constat(
        gravite="majeur", mesure=f"{total} couleurs littérales dans "
        f"{len(par_fichier)} fichiers",
        probleme="la palette est recopiée au lieu d'être nommée",
        pourquoi="changer le bleu de sélection oblige à modifier 60 endroits, "
                 "donc on ne le change jamais : les écrans divergent",
        action="une seule source `theme.json` + `COLORS` généré ; "
               "interdiction d'un littéral `#RRGGBB` dans l'interface",
    ))
    for rel, n in par_fichier.most_common(5):
        no, val = exemples[rel]
        constats.append(Constat(
            gravite="mineur", fichier=rel, ligne=no,
            mesure=f"{n} couleurs dans ce seul fichier (ex. {val} ligne {no})",
            probleme="fichier le plus coloré du plugin",
            pourquoi="c'est ici que la direction artistique se perd",
            action="extraire les constantes vers `styles_qt.py`",
        ))
    return constats


@agent(D, "DA-02", "Tailles de police en dur, échelle typographique absente", "majeur")
def typographie(ctx):
    tailles = Counter()
    for rel in ctx.fichiers:
        for m in re.finditer(r"font-size\s*:\s*([\d.]+)\s*(pt|px)", ctx.sources[rel]):
            tailles[m.group(1) + " " + m.group(2)] += 1
    if len(tailles) <= 6:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(tailles)} tailles de police distinctes : "
                + ", ".join(f"{k} ({v}×)" for k, v in tailles.most_common(10)),
        probleme="aucune échelle typographique : chaque écran choisit sa taille",
        pourquoi="sur une même fenêtre, un titre et un libellé se ressemblent ; "
                 "l'œil ne sait plus ce qui est important",
        action="6 tailles maximum imposées par le thème "
               "(titre 20 · section 12,5 · corps 10 · secondaire 9 · micro 8,4 · "
               "chiffre 16) — toute autre valeur est un écart de contrôle",
    )]


@agent(D, "DA-03", "Feuilles de style écrites dans les widgets", "majeur")
def styles_inline(ctx):
    lieux = compte(r"setStyleSheet\(", ctx)
    par_fichier = Counter(f for f, _, _ in lieux)
    return [Constat(
        gravite="majeur",
        mesure=f"{len(lieux)} appels `setStyleSheet` dans "
                f"{len(par_fichier)} fichiers",
        probleme="la mise en forme est décidée dans le code de chaque écran",
        pourquoi="deux boutons du même rôle ne se ressemblent pas, et "
                 "aucun changement global n'est possible",
        action="une feuille unique générée depuis le thème, appliquée à la "
               "racine ; les widgets ne portent plus que des rôles "
               "(`#primaire`, `#danger`…)",
    )]


@agent(D, "DA-04", "Marges et espacements improvisés", "mineur")
def espaces(ctx):
    marges = Counter()
    for rel in ctx.fichiers:
        for m in re.finditer(r"setContentsMargins\(([^)]*)\)", ctx.sources[rel]):
            marges[m.group(1).replace(" ", "")] += 1
        for m in re.finditer(r"setSpacing\(([^)]*)\)", ctx.sources[rel]):
            marges["spacing " + m.group(1)] += 1
    distinctes = {k for k in marges}
    if len(distinctes) <= 8:
        return []
    return [Constat(
        gravite="mineur",
        mesure=f"{len(distinctes)} combinaisons de marges/espacements",
        probleme="pas de grille : 4, 6, 8, 10, 12, 14 cohabitent",
        pourquoi="les blocs ne s'alignent pas d'un écran à l'autre, ce qui "
                 "donne une impression de bricolage même quand c'est propre",
        action="grille de 4 px : 4 · 8 · 12 · 16 · 24 · 32 uniquement",
    )]


@agent(D, "DA-05", "Icônes et symboles textuels mélangés", "mineur")
def icones(ctx):
    symboles = compte(r"[\"'][▸▾✓✗⚠●○◦→←↑↓≡⌄⌃✕✔⏵⏷]", ctx)
    return [Constat(
        gravite="mineur",
        mesure=f"{len(symboles)} caractères utilisés comme icônes",
        probleme="des glyphes de police jouent le rôle d'icônes",
        pourquoi="ils changent de dessin selon la police et la plateforme, "
                 "et ne s'alignent pas avec le texte",
        action="jeu d'icônes unique (trait 1,5 px, 16/20 px), ou aucune icône",
    )] if symboles else []


@agent(D, "DA-06", "Aucun mode sombre, aucune échelle système", "note")
def theme(ctx):
    a_sombre = any("dark" in ctx.sources[f].lower() and "theme" in ctx.sources[f].lower()
                   for f in ctx.fichiers)
    return [Constat(
        gravite="note",
        mesure="mode sombre absent du plugin (présent dans les maquettes)",
        probleme="le thème existe en maquette, pas dans le code livré",
        pourquoi="un géologue en camion ou en salle sombre ne peut pas réduire "
                 "la luminosité de son écran sans perdre la lisibilité",
        action="deux thèmes dans `theme.json`, choisis par le système",
    )] if not a_sombre else []
