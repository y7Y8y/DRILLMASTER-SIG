"""Départements K, L, M — Vocabulaire, Performance, Empaquetage QGIS."""
from __future__ import annotations

import json
import re
from collections import Counter

from noyau import RACINE, Constat, agent, compte, departement

K = departement("Vocabulaire et lisibilité",
                "des mots que le métier reconnaît, partout les mêmes")
L = departement("Performance et robustesse",
                "rapide sur 500 forages, jamais bloquant")
M = departement("Empaquetage QGIS",
                "installable, compatible, désinstallable proprement")


def lexique():
    chemin = RACINE / "specs" / "data" / "lexique.json"
    if not chemin.exists():
        return {}
    return json.loads(chemin.read_text(encoding="utf-8"))


@agent(K, "V-01", "Les mots de l'écran ne sont pas ceux du métier", "majeur")
def mots_metier(ctx):
    """« track », « assay », « hole » : un géologue dit piste, teneur, forage."""
    paires = [("track", "piste"), ("assay", "teneur"), ("hole", "forage"),
              ("section", "coupe"), ("dip", "pendage"), ("azimuth", "azimut"),
              ("collar", "collet"), ("overburden", "mort-terrain")]
    constats = []
    tous = "\n".join(ctx.sources[f] for f in ctx.fichiers_de(r"/(ui|core)/"))
    for en, fr in paires:
        n_en = len(re.findall(rf"\b{en}", tous, re.I))
        n_fr = len(re.findall(rf"\b{fr}", tous, re.I))
        if n_en >= 30 and n_fr >= 15:
            constats.append(Constat(
                gravite="mineur",
                mesure=f"« {en} » {n_en}× et « {fr} » {n_fr}×",
                probleme="le même objet a un nom anglais dans le code et un "
                         "nom français à l'écran",
                pourquoi="le message d'erreur finit par employér le mot "
                         "anglais, et l'utilisateur ne le reconnaît pas",
                action="l'écran emploie toujours le mot du lexique ; le code "
                       "peut garder l'anglais à condition que la traduction "
                       "soit centralisée",
            ))
    return constats


@agent(K, "V-02", "Le lexique existe mais le code ne le lit pas", "majeur")
def lexique_ignore(ctx):
    lex = lexique()
    if not lex:
        return []
    lus = [f for f in ctx.fichiers
           if re.search(r"lexique|lexicon", ctx.sources[f], re.I)]
    if lus:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(lex.get('interdits', []))} mots interdits et "
                f"{len(lex.get('niveaux', {}))} niveaux définis, "
                f"0 fichier du plugin ne les lit",
        probleme="la source des mots est écrite mais pas branchée",
        pourquoi="deux écrans peuvent nommer différemment le même état sans "
                 "qu'aucun contrôle ne le voie",
        action="le plugin importe le lexique ; un mot absent du lexique ne "
               "peut pas être affiché",
    )]


@agent(K, "V-03", "Textes trop longs pour un panneau", "mineur")
def longueur_textes(ctx):
    longs = []
    for rel in ctx.fichiers_de(r"/ui/"):
        for m in re.finditer(r'["\']([^"\']{140,})["\']', ctx.sources[rel]):
            longs.append((rel, m.group(1)))
    if len(longs) < 5:
        return []
    rel, exemple = longs[0]
    return [Constat(
        gravite="mineur", fichier=rel,
        mesure=f"{len(longs)} textes de plus de 140 caractères dans un panneau",
        probleme="des paragraphes là où une phrase suffit",
        pourquoi="personne ne lit un paragraphe dans un panneau latéral de "
                 "300 px : il est rogné, donc inutile",
        action="une phrase à l'écran, le détail dans une infobulle ou un "
               "« en savoir plus » dépliable",
    )]


@agent(L, "P-01", "Pas de mesure de performance", "majeur")
def mesure_perf(ctx):
    outils = [f for f in ctx.fichiers if re.search(r"bench|perf|timer", f, re.I)]
    return [Constat(
        gravite="majeur" if not outils else "note",
        mesure=(f"{len(outils)} module(s) de mesure" if outils
                else "aucune mesure de temps dans le plugin"),
        probleme=("le temps de rendu n'est ni mesuré ni publié" if not outils
                  else "la mesure existe mais n'est pas publiée"),
        pourquoi="sur 500 forages, une lenteur ne se voit qu'à l'usage — "
                 "donc trop tard",
        action="mesurer et afficher : forages/s au chargement, ms par "
               "redessin. Refuser une livraison qui double le temps",
    )]


@agent(L, "P-02", "Travail long sur le fil d'affichage", "bloquant")
def fil_affichage(ctx):
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        threads = len(re.findall(r"(QThread|QRunnable|QThreadPool|"
                                 r"concurrent\.futures|ProcessPool)", txt))
        if threads:
            continue
        lourds = len(re.findall(r"for .{0,60} in .{0,80}:", txt))
        if lourds >= 40:
            constats.append(Constat(
                gravite="majeur", fichier=rel,
                mesure=f"{lourds} boucles de calcul dans un fichier sans "
                        f"thread ni tâche de fond",
                probleme="le calcul s'exécute pendant que l'écran attend",
                pourquoi="QGIS se fige, l'utilisateur clique trois fois, et "
                         "trois calculs se lancent",
                action="calcul dans une tâche de fond avec progression et "
                       "bouton Annuler qui annule vraiment",
            ))
    return constats


@agent(L, "P-03", "Aucune limite sur les gros fichiers", "majeur")
def gros_fichiers(ctx):
    tous = "\n".join(ctx.sources.values())
    limite = len(re.findall(r"(MAX_ROWS|max_rows|taille_max|LIMITE_|"
                            r"if len\(rows\) >)", tous))
    if limite >= 2:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{limite} garde-fou sur la taille des fichiers lus",
        probleme="rien n'arrête un fichier de 2 Go",
        pourquoi="l'utilisateur attend, croit avoir planté, et relance : "
                 "la mémoire sature",
        action="seuil annoncé avant lecture (« 12 000 forages : continuer ? ») "
               "plutôt que blocage silencieux",
    )]


@agent(M, "E-01", "Métadonnées d'installation incomplètes", "majeur")
def metadata(ctx):
    fichier = RACINE / "DrillMaster" / "metadata.txt"
    if not fichier.exists():
        return [Constat(gravite="bloquant",
                        mesure="metadata.txt absent : le plugin ne s'installe pas",
                        probleme="pas de fiche d'installation",
                        pourquoi="QGIS refuse le paquet",
                        action="créer metadata.txt avec nom, version, "
                               "versions QGIS min/max, auteur, catégorie")]
    contenu = fichier.read_text(encoding="utf-8", errors="ignore")
    obligatoires = ["name", "version", "qgisMinimumVersion", "author",
                    "email", "description", "about", "category", "experimental"]
    manquants = [k for k in obligatoires if f"{k}=" not in contenu]
    if not manquants:
        return []
    return [Constat(
        gravite="majeur", fichier="DrillMaster/metadata.txt",
        mesure=f"{len(manquants)} champ(s) manquant(s) : {', '.join(manquants)}",
        probleme="la fiche d'installation est incomplète",
        pourquoi="le dépôt de plugins QGIS refuse, ou l'utilisateur ne peut "
                 "pas joindre l'auteur en cas de problème",
        action="compléter les champs obligatoires de la fiche",
    )]


@agent(M, "E-02", "Pas de désinstallation propre", "majeur")
def unload(ctx):
    fichier = RACINE / "DrillMaster" / "drillmaster.py"
    if not fichier.exists():
        return []
    txt = fichier.read_text(encoding="utf-8", errors="ignore")
    if "def unload" in txt and re.search(r"removeDockWidget|deleteLater", txt):
        return []
    return [Constat(
        gravite="majeur", fichier="DrillMaster/drillmaster.py",
        mesure="`unload()` incomplet ou absent",
        probleme="désactiver le plugin laisse des panneaux et des actions",
        pourquoi="QGIS garde le dock fantôme et l'utilisateur doit redémarrer : "
                 "c'est le premier signe d'un plugin mal fini",
        action="`unload()` retire le dock, les actions de barre et les "
               "raccourcis, et vide les caches",
    )]


@agent(M, "E-03", "Compatibilité QGIS non bornée", "mineur")
def compat(ctx):
    fichier = RACINE / "DrillMaster" / "metadata.txt"
    if not fichier.exists():
        return []
    txt = fichier.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"qgisMaximumVersion=([\d.]+)", txt)
    if not m:
        return [Constat(gravite="mineur", fichier="DrillMaster/metadata.txt",
                        mesure="aucune version QGIS maximale",
                        probleme="le plugin sera proposé sur des versions "
                                "qu'il ne connaît pas",
                        pourquoi="au mieux il ne s'affiche pas, au pire il "
                                "plante QGIS",
                        action="borner la version maximale et la tester")]
    major = int(m.group(1).split(".")[0])
    if major < 4:
        return [Constat(
            gravite="note", fichier="DrillMaster/metadata.txt",
            mesure=f"maximum déclaré : {m.group(1)} (QGIS 3.x)",
            probleme="QGIS 4 / Qt 6 n'est pas couvert",
            pourquoi="à la sortie de la version suivante, le plugin "
                     "disparaîtra du dépôt faute de compatibilité",
            action="prévoir Qt 6 : éviter `exec_()`, les API dépréciées, "
                   "et tester sur les deux",
        )]
    return []
