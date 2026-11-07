"""Département J — Architecture, code, cohérence, extensions.

Le seul département qui juge le code et pas l'écran : les couches, les
frontières, les noms, les infos partagées, la gestion globale, et la capacité
à accueillir une extension sans tout casser.
"""
from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict

from noyau import Constat, agent, compte, departement

J = departement("Architecture et code",
                "couches, frontières, noms, état partagé, extensibilité")


def _classes(ctx, motif):
    """(fichier, ligne, nom, base) pour les classes dont le fichier correspond."""
    out = []
    for rel in ctx.fichiers_de(motif):
        arbre = ctx.arbres.get(rel)
        if arbre is None:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, ast.ClassDef):
                base = " ".join(ast.unparse(b) for b in n.bases)
                out.append((rel, n.lineno, n.name, base))
    return out


@agent(J, "A-01", "Le noyau dépend de l'interface", "bloquant")
def couches(ctx):
    violations = []
    for rel in ctx.fichiers_de(r"/core/"):
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if re.search(r"^\s*(from|import)\s+.*\bui\b", ligne) and \
                    not re.search(r"#|isinstance", ligne):
                violations.append((rel, no, ligne.strip()))
    if violations:
        f, n, l = violations[0]
        return [Constat(
            gravite="bloquant", fichier=f, ligne=n,
            mesure=f"{len(violations)} import(s) de l'interface depuis le noyau",
            probleme="le calcul dépend de l'affichage",
            pourquoi="on ne peut plus calculer sans ouvrir QGIS : les tests "
                     "deviennent impossibles et l'export ne peut pas être "
                     "utilisé seul",
            action="le noyau ne connaît que des données ; l'interface "
                   "l'appelle, jamais l'inverse",
        )]
    return [Constat(
        gravite="note",
        mesure="aucun import de l'interface depuis le noyau",
        probleme="la frontière est propre",
        pourquoi="c'est la condition pour tester et exporter sans QGIS",
        action="la conserver : interdire tout `from ..ui` dans `core/`",
    )]


@agent(J, "A-02", "Classes qui mélangent calcul et affichage", "majeur")
def god_classes(ctx):
    constats = []
    for rel, no, nom, base in _classes(ctx, r"/ui/"):
        if not re.search(r"QWidget|QDialog|QgsDockWidget|QGraphicsItem|QObject",
                         base):
            continue
        arbre = ctx.arbres[rel]
        taille = (ast.get_source_segment(ctx.sources[rel],
                next(n for n in ast.walk(arbre)
                     if isinstance(n, ast.ClassDef) and n.name == nom)) or "")
        lignes = tail = taille.count("\n")
        methodes = len(re.findall(r"\n    def ", taille))
        calculs = len(re.findall(r"(math\.|np\.|numpy|sum\(|len\(|sorted\()",
                                 taille))
        if lignes > 900 and calculs > 40:
            constats.append(Constat(
                gravite="majeur", fichier=rel, ligne=no,
                mesure=f"`{nom}` : {lignes} lignes, {methodes} méthodes, "
                        f"{calculs} opérations de calcul",
                probleme="une classe d'affichage contient aussi le calcul",
                pourquoi="la même règle est donc invisible pour la 3D, "
                         "l'export et les tests",
                action="la classe ne garde que le dessin ; le calcul va dans "
                       "le noyau, appelé par un seul point d'entrée",
            ))
    return constats


@agent(J, "A-03", "Noms abrégés ou illisibles", "mineur")
def noms(ctx):
    constats = Counter()
    lieux = {}
    for rel in ctx.fichiers:
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            m = re.match(r"\s*def ([a-z_]{1,4})\(", ligne)
            if m and not m.group(1).startswith("__"):
                constats[m.group(1)] += 1
                lieux.setdefault(m.group(1), (rel, no))
    if not constats:
        return []
    total = sum(constats.values())
    return [Constat(
        gravite="mineur",
        mesure=f"{len(constats)} fonctions portent un nom de 1 à 4 lettres "
                f"({total} occurrences)",
        probleme="des noms comme `mk`, `n`, `run`, `get` ne disent rien",
        pourquoi="le prochain développeur doit lire le corps pour comprendre, "
                 "donc l'extension coûte trois fois plus cher",
        action="un nom = un verbe + un objet (`calculer_trajectoire`, "
               "`afficher_piste`) ; les abréviations de 2 lettres interdites",
    )]


@agent(J, "A-04", "Aucun état global nommé : les infos se passent de main en main", "majeur")
def etat_partage(ctx):
    """Les données partagées doivent vivre dans un objet, pas dans des attributs."""
    attributs = Counter()
    fichiers = defaultdict(set)
    for rel in ctx.fichiers_de(r"/ui/"):
        for m in re.finditer(r"self\.(\w+)\s*=", ctx.sources[rel]):
            nom = m.group(1)
            if re.search(r"(data|project|section|holes|tracks|assays|"
                         r"config|settings|params|state|model)", nom, re.I):
                attributs[nom] += 1
                fichiers[nom].add(rel)
    partages = [(n, c) for n, c in attributs.items() if len(fichiers[n]) >= 3]
    if not partages:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(partages)} attributs de données partagés dans 3 fichiers "
                f"ou plus (ex. `{partages[0][0]}` dans {len(fichiers[partages[0][0]])} fichiers)",
        probleme="les informations circulent par copies d'attributs",
        pourquoi="deux vues peuvent avoir deux versions de la même donnée, "
                 "et rien ne le signale",
        action="un seul objet de projet, passé par référence ; les vues "
               "écoutent ses changements au lieu de recopier",
    )]


@agent(J, "A-05", "Pas de gestion globale : chacun fait son propre filet", "majeur")
def gestion_globale(ctx):
    tous = "\n".join(ctx.sources.values())
    hooks = len(re.findall(r"(sys\.excepthook|try:\s*\n\s*\.\.\.|"
                           r"installExceptionHandler|class .*Error\()", tous))
    affichages = len(re.findall(r"QMessageBox\.(critical|warning)", tous))
    if affichages < 10:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{affichages} affichages d'erreur dispersés, {hooks} point(s) "
                f"central(s)",
        probleme="chaque écran gère ses erreurs à sa façon",
        pourquoi="le même incident donne trois messages différents selon le "
                 "bouton utilisé, et aucun ne dit quoi faire",
        action="un gestionnaire unique : toutes les erreurs passent par lui et "
               "deviennent un message à 5 champs",
    )]


@agent(J, "A-06", "Une extension obligerait à modifier 5 fichiers", "majeur")
def extensibilite(ctx):
    """Ajouter un domaine de données : combien d'endroits faut-il toucher ?"""
    domaines = ["litholog", "alt[ée]ration", "min[ée]ral", "structure",
                "rqd", "r[ée]cup[ée]ration", "densit[ée]", "imagerie",
                "teneur"]
    par_domaine = Counter()
    lieux = defaultdict(set)
    for rel in ctx.fichiers:
        txt = ctx.sources[rel].lower()
        for d in domaines:
            if re.search(d, txt):
                par_domaine[d] += 1
                lieux[d].add(rel)
    moy = sum(len(v) for v in lieux.values()) / max(1, len(lieux))
    if moy < 8:
        return []
    pire = max(lieux.items(), key=lambda kv: len(kv[1]))
    return [Constat(
        gravite="majeur",
        mesure=f"chaque domaine est cité dans {moy:.0f} fichiers en moyenne "
                f"(« {pire[0]} » : {len(pire[1])} fichiers)",
        probleme="ajouter un domaine de données exige de toucher des dizaines "
                 "d'endroits",
        pourquoi="c'est pour ça que 9 des 12 types ne sont pas encore "
                 "exploitables : chaque ajout coûte une semaine",
        action="une table des domaines (déjà écrite : `lexique.json`) que le "
               "code lit ; ajouter un domaine = ajouter une ligne",
    )]


@agent(J, "A-07", "Pas de point d'entrée unique pour charger un projet", "majeur")
def point_entree(ctx):
    chargements = []
    for rel in ctx.fichiers:
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if re.search(r"(read_csv|csv\.reader|loadtxt|read_file|"
                         r"open\(.*['\"]r)", ligne):
                chargements.append((rel, no))
    fichiers = {f for f, _ in chargements}
    if len(fichiers) < 5:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(chargements)} lectures de fichier dans {len(fichiers)} "
                f"fichiers",
        probleme="chaque écran sait lire un fichier à sa manière",
        pourquoi="deux imports du même fichier donnent deux résultats "
                 "différents, et les erreurs sont traitées deux fois",
        action="un seul lecteur (déjà écrit et testé : "
               "`drillmaster_v3/core/donnees/lecture.py`)",
    )]


@agent(J, "A-08", "Duplication de constantes métier", "mineur")
def constantes(ctx):
    noms = Counter()
    lieux = defaultdict(set)
    for rel in ctx.fichiers_de(r"/(core|ui)/"):
        for m in re.finditer(r"^([A-Z][A-Z0-9_]{3,})\s*=",
                             ctx.sources[rel], re.M):
            noms[m.group(1)] += 1
            lieux[m.group(1)].add(rel)
    dupes = [n for n in noms if len(lieux[n]) >= 2]
    if not dupes:
        return []
    return [Constat(
        gravite="mineur",
        mesure=f"{len(dupes)} constantes redéfinies dans plusieurs fichiers "
                f"(ex. {', '.join(dupes[:5])})",
        probleme="la même valeur est écrite deux fois",
        pourquoi="une correction n'est appliquée qu'à une copie",
        action="un module de constantes unique, importé",
    )]
