"""Rapport de la flotte — 8 départements, 1 rapport par exécution.

    python3 tools/flotte/rapport.py            # écrit docs/09_RAPPORT_FLOTTE.md
    python3 tools/flotte/rapport.py --resume   # résumé à l'écran seulement

Le rapport est le compte rendu des chefs de département au chef de projet :
chaque constat porte un chiffre, un fichier, un effet ressenti et une action.
"""
from __future__ import annotations

import collections
import sys
from datetime import date
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

import noyau                                    # noqa: E402
import agents_da, agents_ui, agents_fonctionnel  # noqa: E402,F401
import agents_messages, agents_qualite, agents_donnees  # noqa: E402,F401
from noyau import ORDRE, Contexte                # noqa: E402

SORTIE = noyau.RACINE / "docs" / "09_RAPPORT_FLOTTE.md"
LIBELLE = {"bloquant": "Bloquant", "majeur": "Majeur",
           "mineur": "Mineur", "note": "Note"}


def execute():
    ctx = Contexte.charge()
    resultats = []
    for d in noyau.FLOTTE:
        for a in d.agents:
            for c in a(ctx):
                if not c.agent:
                    c.agent = a.agent_id
                if not c.departement:
                    c.departement = d.nom
                if not c.gravite:
                    c.gravite = a.gravite
                c.titre = a.titre
                resultats.append(c)
    resultats.sort(key=lambda c: c.cle())
    return ctx, resultats


def resume(ctx, constats):
    par_gravite = collections.Counter(c.gravite for c in constats)
    lignes = [f"{len(ctx.fichiers)} fichiers inspectés · "
              f"{sum(len(d.agents) for d in noyau.FLOTTE)} agents · "
              f"{len(constats)} constats"]
    for g in ("bloquant", "majeur", "mineur", "note"):
        lignes.append(f"  {LIBELLE[g]:9} {par_gravite[g]:4}")
    print("\n".join(lignes))
    return par_gravite


def ecrit(ctx, constats):
    par_gravite = collections.Counter(c.gravite for c in constats)
    par_dep = collections.defaultdict(list)
    for c in constats:
        par_dep[c.departement].append(c)

    out = [f"""# 09 — Rapport de la flotte d'agents

> Généré par `python3 tools/flotte/rapport.py` le {date.today().isoformat()}.
> Ce rapport n'est pas une opinion : chaque constat cite un fichier, un
> chiffre et l'effet ressenti par l'utilisateur.

## Ce qui a été inspecté

| | |
|---|---|
| Périmètre | `DrillMaster/` — le plugin complet |
| Fichiers | **{len(ctx.fichiers)}** fichiers Python |
| Lignes | **{sum(s.count(chr(10)) for s in ctx.sources.values()):,}** |
| Agents | {sum(len(d.agents) for d in noyau.FLOTTE)} répartis en {len(noyau.FLOTTE)} départements |
| Constats | **{len(constats)}** |

## Verdict en une ligne

| Gravité | Nombre | Ce que ça veut dire |
|---|---|---|
| **Bloquant** | {par_gravite['bloquant']} | empêche de promettre « simple et fiable » |
| **Majeur** | {par_gravite['majeur']} | se voit à l'usage et fait perdre du temps |
| **Mineur** | {par_gravite['mineur']} | donne l'impression de bricolage |
| **Note** | {par_gravite['note']} | occasion manquée, pas un défaut |

## Les départements

| Département | Ce qu'il possède | Agents | Bloquant | Majeur |
|---|---|---|---|---|"""]
    for d in noyau.FLOTTE:
        ses = par_dep[d.nom]
        n_b = sum(1 for c in ses if c.gravite == "bloquant")
        n_m = sum(1 for c in ses if c.gravite == "majeur")
        out.append(f"| **{d.nom}** | {d.chef} | {len(d.agents)} | {n_b} | {n_m} |")

    out.append("""
---

## Les bloquants, un par un

Ce sont les seuls à traiter avant toute nouvelle maquette.""")
    vus = set()
    for c in [x for x in constats if x.gravite == "bloquant"]:
        cle = (c.agent, c.fiche if False else c.mesure) if False else (c.agent, c.mesure)
        if cle in vus:
            continue
        vus.add(cle)
        out.append(f"""
### {c.agent} · {c.titre}

**Mesure** — {c.mesure}{f'  ·  `{c.fichier}`' if c.fichier else ''}

**Le problème** — {c.probleme}

**Ce que l'utilisateur ressent** — {c.pourquoi}

**Ce qu'on fait** — {c.action}""")

    out.append("""
---

## Détail par département""")
    for d in noyau.FLOTTE:
        ses = par_dep[d.nom]
        if not ses:
            continue
        out.append(f"\n### {d.nom} — {d.chef}\n")
        out.append("| Agent | Constat | Gravité | Mesure |")
        out.append("|---|---|---|---|")
        for c in ses:
            mes = c.mesure.replace("|", "/")
            if c.fichier:
                mes += f" · `{c.fichier.split('/')[-1]}`"
            out.append(f"| {c.agent} | {c.titre} | {LIBELLE[c.gravite]} | "
                       f"{mes[:180]} |")

    out.append("""
---

## Ce que la flotte n'a pas vu

Trois limites, dites franchement :

1. **Elle lit des fichiers, pas des pixels.** Un bouton mal aligné ou un
   contraste insuffisant ne se détecte pas dans le code : il faut une capture.
2. **Elle ne connaît pas le métier du géologue.** Elle repère un seuil
   recopié, pas un seuil *faux*. C'est la spec (31 règles) qui tranche.
3. **Elle juge la cohérence, pas le goût.** Le choix « Apple-like » est une
   décision de direction artistique, pas un constat mesurable.

## Ordre d'exécution proposé

1. Les bloquants de **Réglages et partage** et de **Données et vues** : c'est
   là que se trouvent les incohérences que l'utilisateur remarque en premier.
2. **Direction artistique** en un seul passage : thème unique, 6 tailles de
   police, 3 rôles de bouton, grille de 4 px.
3. Les **monolithes** (`section_dock.py`, 11 529 lignes) découpés par
   responsabilité, parce que toute correction d'écran passe par là.
4. Puis les écrans neufs (import, blocage, coupe, exclusions) déjà maquettés.
""")

    SORTIE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"écrit {SORTIE.relative_to(noyau.RACINE)}")
    return SORTIE


if __name__ == "__main__":
    ctx, constats = execute()
    resume(ctx, constats)
    if "--resume" not in sys.argv:
        ecrit(ctx, constats)
