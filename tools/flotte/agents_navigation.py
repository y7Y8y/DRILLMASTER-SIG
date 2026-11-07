"""Département I — Navigation, options cachées, construction des écrans.

Répond à trois questions précises :
  1. y a-t-il des réglages qu'on ne peut atteindre que par un dialogue ?
  2. y a-t-il des onglets muets, des panneaux qui s'ouvrent sans dire pourquoi ?
  3. la construction des écrans permet-elle d'ajouter une option sans casser
     les autres ?
"""
from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict

from noyau import Constat, agent, compte, departement

N = departement("Navigation et options cachées",
                "tout réglage est atteignable en 1 clic, aucun onglet muet")


@agent(N, "N-01", "Réglages enfermés dans une fenêtre qu'on ne peut pas rouvrir", "bloquant")
def options_cachees(ctx):
    """Un dialogue = un aller-retour. S'il porte des réglages, ils sont cachés."""
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        arbre = ctx.arbres.get(rel)
        if arbre is None:
            continue
        for n in ast.walk(arbre):
            if not isinstance(n, ast.ClassDef):
                continue
            bases = " ".join(ast.unparse(b) for b in n.bases)
            if "Dialog" not in bases:
                continue
            corps = ast.get_source_segment(ctx.sources[rel], n) or ""
            reglages = len(re.findall(
                r"Q(?:CheckBox|ComboBox|SpinBox|DoubleSpinBox|Slider|LineEdit)\(",
                corps))
            if reglages >= 6:
                constats.append(Constat(
                    gravite="bloquant" if reglages >= 15 else "majeur",
                    fichier=rel, ligne=n.lineno,
                    mesure=f"`{n.name}` enferme {reglages} réglages dans une "
                            f"fenêtre",
                    probleme="ces options n'existent que le temps d'un "
                             "aller-retour ; la fenêtre fermée, elles sont "
                             "introuvables",
                    pourquoi="c'est exactement l'option cachée : l'utilisateur "
                             "a réglé sa coupe une fois, il ne retrouve plus "
                             "où le refaire",
                    action="les réglages vivent dans le panneau (ou dans "
                           "« réglages avancés »), jamais dans une fenêtre "
                           "modale ; la fenêtre ne sert qu'à choisir un "
                           "fichier",
                ))
    return constats


@agent(N, "N-02", "Onglets et barres d'onglets masqués", "majeur")
def onglets_muets(ctx):
    lieux = compte(r"tabBar\(\)\.(hide|setVisible)", ctx)
    if not lieux:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(lieux)} barres d'onglets masquées par le code",
        probleme="des onglets existent mais leur barre est cachée : une seule "
                 "page est atteignable",
        pourquoi="si une deuxième page est ajoutée un jour, elle sera "
                 "invisible — et personne ne comprendra pourquoi",
        action="soit un seul panneau assumé (pas de QTabWidget), soit des "
               "onglets visibles avec un nom et une icône",
    )]


@agent(N, "N-03", "Panneaux qui apparaissent sans annonce", "majeur")
def panneaux_muets(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        montres = len(re.findall(r"\.show\(\)|setVisible\(True\)", txt))
        caches = len(re.findall(r"\.hide\(\)|setVisible\(False\)", txt))
        if montres + caches < 15:
            continue
        if not re.search(r"setToolTip|setStatusTip|QToolTip|aide|astuce",
                         txt, re.I):
            constats.append(Constat(
                gravite="majeur", fichier=rel,
                mesure=f"{montres} apparitions et {caches} disparitions, "
                        f"aucune infobulle",
                probleme="l'interface se réorganise toute seule sans dire "
                         "pourquoi",
                pourquoi="l'utilisateur voit un panneau surgir et croit avoir "
                         "fait une fausse manœuvre",
                action="chaque apparition est annoncée (une phrase dans la "
                       "barre d'état) et chaque panneau a une infobulle",
            ))
    return constats


@agent(N, "N-04", "Réglages conservés sur le poste, invisibles dans le projet", "majeur")
def reglages_invisibles(ctx):
    lieux = compte(r"QSettings", ctx, ctx.fichiers_de(r"/(ui|core)/"))
    if not lieux:
        return []
    cles = set()
    for rel, _, _ in lieux:
        for m in re.finditer(r'["\'](DrillMaster/[\w/]+)["\']', ctx.sources[rel]):
            cles.add(m.group(1))
    return [Constat(
        gravite="majeur",
        mesure=f"{len(lieux)} accès à des réglages de poste"
                f"{f', {len(cles)} clés nommées' if cles else ''}",
        probleme="une partie des réglages est stockée dans le poste, pas dans "
                 "le projet",
        pourquoi="un collègue ouvre le même projet et ne retrouve ni la "
                 "langue, ni les largeurs, ni les profils d'affichage : ce "
                 "sont des options cachées par construction",
        action="deux catégories nommées : préférences de poste (thème, "
               "langue) et réglages de projet (pistes, seuils, couleurs) — "
               "ces derniers voyagent avec le projet",
    )]


@agent(N, "N-05", "Trop de fichiers d'interface pour un seul produit", "majeur")
def eclatement(ctx):
    ui = ctx.fichiers_de(r"/ui/")
    if len(ui) < 30:
        return []
    familles = Counter()
    for f in ui:
        nom = f.split("/")[-1]
        for cle in ("3d", "section", "step", "export", "dialog", "reference",
                    "struct", "import"):
            if cle in nom:
                familles[cle] += 1
                break
        else:
            familles["autres"] += 1
    return [Constat(
        gravite="majeur",
        mesure=f"{len(ui)} fichiers d'interface : "
                + ", ".join(f"{k} {v}" for k, v in familles.most_common()),
        probleme="l'interface est découpée par écran, pas par responsabilité",
        pourquoi="le même réglage est réécrit dans plusieurs de ces fichiers "
                 "(c'est le constat F-01) et personne ne sait lequel fait foi",
        action="découper par responsabilité (dessin, réglages, messages, "
               "export) et supprimer les fichiers de la 3D redondants",
    )]


@agent(N, "N-06", "Aucune aide contextuelle : tout dépend de la documentation", "majeur")
def aide(ctx):
    tous = "\n".join(ctx.sources[f] for f in ctx.fichiers_de(r"/ui/"))
    bulles = len(re.findall(r'setToolTip\(\s*(?:self\.tr\()?\s*["\'][^"\']{6,}', tous))
    controles = len(re.findall(
        r"Q(CheckBox|ComboBox|SpinBox|DoubleSpinBox|Slider|LineEdit|"
        r"PushButton)\(", tous))
    if not controles:
        return []
    ratio = bulles / controles
    return [Constat(
        gravite="majeur" if ratio < 0.2 else "mineur",
        mesure=f"{bulles} infobulles pour {controles} contrôles "
                f"({ratio * 100:.0f} %)",
        probleme="la plupart des contrôles n'expliquent pas ce qu'ils font",
        pourquoi="un débutant doit deviner, puis ouvrir la documentation — "
                 "c'est-à-dire arrêter de travailler",
        action="100 % des contrôles ont une infobulle qui dit : ce que ça "
               "change, et où ça s'applique (coupe, 3D, légende, export, carte)",
    )]


@agent(N, "N-07", "Pas de « réglages avancés » : tout est au même niveau", "majeur")
def tout_visible(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        avances = len(re.findall(r"(QToolButton|collaps|repli|d[ée]plier|"
                                 r"plus d'options|r[ée]glages avanc)", txt, re.I))
        controles = len(re.findall(
            r"Q(CheckBox|ComboBox|SpinBox|DoubleSpinBox|Slider|LineEdit)\(", txt))
        if controles >= 20 and avances == 0:
            constats.append(Constat(
                gravite="majeur", fichier=rel,
                mesure=f"{controles} réglages, aucun repli « avancés »",
                probleme="le débutant et l'expert voient exactement la même "
                         "liste, donc le débutant voit tout",
                pourquoi="c'est la définition de la complexité imposée : "
                         "6 réglages utiles noyés dans 25",
                action="6 réglages visibles (R-24), le reste derrière un seul "
                       "repli nommé, dont le contenu se souvient d'un coup",
            ))
    return constats


@agent(N, "N-08", "Interface qui s'ouvre sans dire où l'on est", "mineur")
def contexte(ctx):
    tous = "\n".join(ctx.sources[f] for f in ctx.fichiers
                     if re.search(r"/ui/|stepper", f))
    if re.search(r"fil d'Ariane|breadcrumb|étape \d sur|Étape \d|step_index|"
                 r"current_step", tous, re.I):
        return []
    return [Constat(
        gravite="mineur",
        mesure="aucun fil d'Ariane, aucune indication d'étape",
        probleme="on ne sait pas où l'on est dans le travail",
        pourquoi="après 20 minutes, l'utilisateur ne sait plus s'il est dans "
                 "les données, la coupe ou l'export",
        action="un en-tête constant : module › objet › état, plus la barre "
               "d'étapes de l'assistant",
    )]
