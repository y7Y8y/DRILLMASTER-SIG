"""Départements E et F — Boutons et actions ; Qualité et dette."""
from __future__ import annotations

import ast
import re
from collections import Counter

from noyau import RACINE, Constat, agent, compte, departement


def ctx_fichiers_hors_plugin():
    """Les tests vivent à côté du plugin (specs/tests), pas dedans."""
    return [str(p.relative_to(RACINE)) for p in (RACINE / "specs" / "tests")
            .rglob("test_*.py")]

E = departement("Boutons et actions",
                "un bouton = un verbe ; une action destructrice = une "
                "confirmation")
F = departement("Qualité et dette",
                "tests, duplication, fichiers monolithes, dépendances")


@agent(E, "B-01", "Boutons sans rôle : tous dessinés pareil", "majeur")
def roles(ctx):
    lieux = compte(r"QPushButton\(", ctx, ctx.fichiers_de(r"/ui/"))
    constats = []
    par_fichier = Counter(f for f, _, _ in lieux)
    for rel, n in par_fichier.most_common(4):
        txt = ctx.sources[rel]
        objets = len(re.findall(r"setObjectName\(", txt))
        if n >= 8 and objets < n / 3:
            constats.append(Constat(
                gravite="majeur", fichier=rel,
                mesure=f"{n} boutons, {objets} rôles nommés",
                probleme="aucun bouton ne déclare son importance",
                pourquoi="« Enregistrer » et « Fermer » ont le même poids "
                         "visuel : l'action principale ne se distingue pas",
                action="3 rôles seulement : primaire (1 par écran), "
                       "secondaire, discret — la feuille de style fait le reste",
            ))
    return constats


@agent(E, "B-02", "Actions destructrices sans confirmation claire", "bloquant")
def destructif(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        lignes = ctx.sources[rel].splitlines()
        for no, ligne in enumerate(lignes, 1):
            if not re.search(r"(supprim|effac|remov|delete|r[ée]initialis)", ligne, re.I):
                continue
            if not re.search(r"def |#|\"\"\"|'", ligne):
                continue
            if not re.search(r"def .*(supprim|delete|effac|remov|reset|"
                             r"r[ée]initialis)", ligne, re.I):
                continue
            bloc = "\n".join(lignes[no - 1:no + 60])
            if not re.search(r"confirmer|confirm|QMessageBox|undo|annul|"
                             r"corbeille", bloc, re.I):
                entete = re.search(r"def\s+(\w+)", ligne)
                nom = entete.group(1) if entete else "?"
                constats.append(Constat(
                    gravite="bloquant", fichier=rel, ligne=no,
                    mesure=f"`{nom}` supprime sans demander confirmation",
                    probleme="on peut perdre des données sans filet",
                    pourquoi="c'est l'erreur qu'on ne pardonne pas : un clic "
                             "mal placé et le projet est amputé",
                    action="confirmation qui dit ce qui sera perdu, avec une "
                           "sortie « annuler » après coup",
                ))
    vus, uniques = set(), []
    for c in constats:
        cle = (c.fichier, c.mesure)
        if cle not in vus:
            vus.add(cle)
            uniques.append(c)
    return uniques[:12]


@agent(E, "B-03", "Boutons muets : aucun retour après le clic", "majeur")
def muets(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        boutons = re.findall(r"(self\.(?:btn|button)_?\w*)\s*=\s*QPushButton\(", txt)
        branches = set(re.findall(r"(self\.(?:btn|button)_?\w*)\.(?:clicked|"
                                  r"pressed)\.connect", txt))
        for nom in boutons:
            if nom not in branches:
                constats.append(Constat(
                    gravite="majeur", fichier=rel,
                    mesure=f"`{nom}` n'est relié à aucune action",
                    probleme="le bouton existe mais ne fait rien (ou est relié "
                             "ailleurs, sans lien visible)",
                    pourquoi="l'utilisateur clique et rien ne se passe : il "
                             "recommence, puis abandonne",
                    action="tout bouton est soit relié, soit absent ; "
                           "un bouton désactivé dit pourquoi",
                ))
    return constats[:12]


@agent(E, "B-04", "Deux boutons pour la même chose", "majeur")
def doublons_boutons(ctx):
    textes = Counter()
    for rel in ctx.fichiers_de(r"/ui/"):
        for m in re.finditer(r"QPushButton\(\s*(?:self\.tr\()?[\"']([^\"']{2,30})",
                             ctx.sources[rel]):
            textes[m.group(1)] += 1
    constats = []
    for t, n in textes.most_common(6):
        if n >= 6:
            constats.append(Constat(
                gravite="mineur",
                mesure=f"« {t} » apparaît {n} fois comme bouton",
                probleme="le même verbe est réécrit dans plusieurs fichiers",
                pourquoi="un libellé qui change d'un écran à l'autre empêche "
                         "de reconnaître le geste qu'on connaît déjà",
                action="un lexique des verbes d'action (6 verbes max), "
                       "réutilisé partout",
            ))
    return constats


@agent(F, "Q-01", "Aucun test automatisé sur le plugin", "bloquant")
def tests(ctx):
    trouve = [f for f in ctx.fichiers if "test" in f.lower()]
    if not trouve and (RACINE_TESTES := ctx_fichiers_hors_plugin()) :
        trouve = RACINE_TESTES
    if trouve:
        return []
    return [Constat(
        gravite="bloquant",
        mesure=f"0 fichier de test pour {len(ctx.fichiers)} fichiers de code",
        probleme="rien ne prouve que le plugin fonctionne encore",
        pourquoi="chaque correction peut casser un autre écran sans que "
                 "personne ne s'en aperçoive avant la livraison",
        action="tests de bout en bout sur les 17 cas déjà écrits dans la spec",
    )]


@agent(F, "Q-02", "Fichiers monolithes", "majeur")
def monolithes(ctx):
    constats = []
    for rel in ctx.fichiers:
        n = len(ctx.sources[rel].splitlines())
        if n > 2000:
            constats.append(Constat(
                gravite="majeur", fichier=rel,
                mesure=f"{n} lignes dans un seul fichier",
                probleme="un fichier contient une dizaine de responsabilités",
                pourquoi="aucun développeur ne peut tenir l'ensemble en tête : "
                         "les corrections se marchent dessus",
                action="découper par responsabilité (dessin, réglages, "
                       "messages, export)",
            ))
    return constats


@agent(F, "Q-03", "Duplication de code de dessin", "majeur")
def duplication(ctx):
    """Deux fonctions qui dessinent presque la même chose."""
    signatures = Counter()
    lieux = {}
    for rel in ctx.fichiers:
        arbre = ctx.arbres.get(rel)
        if arbre is None:
            continue
        for n in ast.walk(arbre):
            if isinstance(n, ast.FunctionDef):
                cle = (len(n.args.args), len(n.body))
                signatures[cle] += 1
                lieux[cle] = (rel, n.lineno, n.name)
    doublons = [(k, v) for k, v in signatures.items() if v >= 3 and k[1] >= 20]
    if not doublons:
        return []
    return [Constat(
        gravite="mineur",
        mesure=f"{len(doublons)} groupes de fonctions de même forme et même "
                f"taille",
        probleme="le même dessin est réécrit plusieurs fois",
        pourquoi="une correction de rendu doit être appliquée à la main dans "
                 "chaque copie, donc elle l'est à moitié",
        action="un seul composant de dessin par élément (piste, en-tête, "
               "message) réutilisé",
    )]


@agent(F, "Q-04", "Dépendances lourdes dans l'interface", "mineur")
def dependances(ctx):
    lourds = []
    for rel in ctx.fichiers_de(r"/ui/"):
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if re.match(r"\s*(import|from)\s+(numpy|scipy|pandas|matplotlib|"
                        r"requests)", ligne):
                lourds.append((rel, no, ligne.strip()))
    if len(lourds) < 3:
        return []
    return [Constat(
        gravite="mineur",
        mesure=f"{len(lourds)} imports lourds dans les écrans",
        probleme="l'interface charge des bibliothèques de calcul",
        pourquoi="le panneau met plusieurs secondes à apparaître sur un "
                 "ordinateur de terrain",
        action="les calculs restent dans le noyau, chargés à la demande",
    )]


@agent(F, "Q-05", "Réglages stockés hors du projet", "majeur")
def qsettings(ctx):
    lieux = compte(r"QSettings", ctx)
    par_fichier = Counter(f for f, _, _ in lieux)
    return [Constat(
        gravite="majeur",
        mesure=f"{len(lieux)} usages de QSettings dans "
                f"{len(par_fichier)} fichiers",
        probleme="la configuration vit sur le poste, pas dans le projet",
        pourquoi="un collègue ouvre le même projet et ne retrouve ni les "
                 "couleurs, ni les largeurs, ni les seuils",
        action="réglages dans le projet (versionnés, exportables), QSettings "
               "réservé aux préférences de poste (thème, langue)",
    )]
