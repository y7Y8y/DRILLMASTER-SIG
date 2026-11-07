"""Département D — Messages, blocages, réponses à l'utilisateur."""
from __future__ import annotations

import re
from collections import Counter

from noyau import Constat, agent, compte, departement

D = departement("Messages et blocages",
                "5 champs par message : ce qui s'est passé, pourquoi, "
                "qui est concerné, comment sortir, où")

JARGON = ["Qgs", "EPSG", "CRS", "GPKG", "GeoPackage", "SQLite", "None",
          "Traceback", "IndexError", "KeyError", "TypeError", "ValueError",
          "attribute", "object", "layer_id", "wkb", "geometry_type",
          "pyqtSignal", "NULL", "NaN", "nan"]


@agent(D, "M-01", "Alertes modales qui bloquent le travail", "majeur")
def modales(ctx):
    lieux = compte(r"QMessageBox\.(information|warning|critical|question)\(", ctx)
    if len(lieux) < 10:
        return []
    par_fichier = Counter(f for f, _, _ in lieux)
    return [Constat(
        gravite="majeur",
        mesure=f"{len(lieux)} boîtes de dialogue bloquantes dans "
                f"{len(par_fichier)} fichiers",
        probleme="le logiciel interrompt au lieu d'informer",
        pourquoi="une fenêtre à fermer casse le geste : au 10e import, "
                 "l'utilisateur clique « OK » sans lire — donc il ne verra "
                 "pas le message qui comptait",
        action="un bandeau dans l'écran (5 champs) ; la modale réservée à "
               "ce qui exige vraiment une décision",
    )]


@agent(D, "M-02", "Messages sans les 5 champs obligatoires", "majeur")
def cinq_champs(ctx):
    """R-20 : ce qui s'est passé, pourquoi, concerné, comment sortir, où."""
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            m = re.search(r"QMessageBox\.(warning|critical|information)\(\s*"
                          r"[^,]+,\s*[\"']([^\"']{0,80})[\"']", ligne)
            if m and len(m.group(2)) < 18:
                constats.append(Constat(
                    gravite="mineur", fichier=rel, ligne=no,
                    mesure=f"titre de {len(m.group(2))} caractères : "
                            f"« {m.group(2)} »",
                    probleme="le message n'annonce pas ce qui s'est passé",
                    pourquoi="un titre court et vague (« Erreur ») oblige à "
                             "lire un paragraphe technique",
                    action="titre = le fait, en une phrase ; le reste en 4 "
                           "champs (R-20)",
                ))
    return constats[:10]


@agent(D, "M-03", "Jargon technique dans les textes affichés", "bloquant")
def jargon(ctx):
    constats = []
    for mot in JARGON:
        lieux = compte(rf"[\"'][^\"']*\b{re.escape(mot)}\b[^\"']*[\"']", ctx)
        affiches = [(f, n, l) for f, n, l in lieux
                    if re.search(r"/ui/|messages", f)
                    and not re.search(r"import |from |#|\blog\b|logger|logging",
                                      l)]
        if affiches:
            f, n, _ = affiches[0]
            constats.append(Constat(
                gravite="majeur", fichier=f, ligne=n,
                mesure=f"« {mot} » dans {len(affiches)} texte(s) affichable(s)",
                probleme="un terme que le géologue n'a pas à connaître",
                pourquoi="« EPSG:32629 » ou « None » dans un message, c'est "
                         "le logiciel qui parle de lui-même au lieu de parler "
                         "du forage",
                action="le mot simple à l'écran, le terme technique dans le "
                       "détail dépliable",
            ))
    return constats


@agent(D, "M-04", "États absents non annoncés (le silence)", "bloquant")
def silence(ctx):
    """Un domaine vide qui ne dit rien est un mensonge par omission."""
    tout = "\n".join(ctx.sources[f] for f in ctx.fichiers_de(r"/ui/"))
    gestes = len(re.findall(r"(absent|non fourni|manquant|vide|aucune? "
                            r"donn[ée]e)", tout, re.I))
    domaines = len(re.findall(r"(litholog|alt[ée]ration|min[ée]ral|structure|"
                              r"rqd|r[ée]cup[ée]ration|densit[ée]|imagerie)",
                              tout, re.I))
    return [Constat(
        gravite="majeur" if gestes < 20 else "mineur",
        mesure=f"{gestes} mentions d'absence pour {domaines} mentions de "
                f"domaines",
        probleme="l'absence est peu annoncée par rapport au nombre de "
                 "domaines possibles",
        pourquoi="un panneau vide laisse croire qu'il n'y a rien à voir, "
                 "alors que la donnée n'a simplement pas été fournie",
        action="chaque domaine a trois états affichés : fourni, non fourni, "
               "en réserve",
    )]


@agent(D, "M-05", "L'erreur technique brute atteint l'utilisateur", "bloquant")
def traceback(ctx):
    lieux = compte(r"(traceback\.|format_exc\(|repr\(e\)|str\(e\))", ctx)
    if not lieux:
        return []
    return [Constat(
        gravite="bloquant",
        mesure=f"{len(lieux)} endroits qui peuvent afficher une erreur brute",
        probleme="le message d'exception peut finir à l'écran",
        pourquoi="l'utilisateur voit `KeyError: 'hole_id'` et n'a aucune "
                 "action possible",
        action="filet unique : une erreur imprévue devient « DrillMaster n'a "
               "pas pu terminer cette action » + 3 sorties + le détail "
               "copiable",
    )]


@agent(D, "M-06", "Aucun moyen de copier le détail d'un problème", "mineur")
def copie(ctx):
    tout = "\n".join(ctx.sources[f] for f in ctx.fichiers)
    if re.search(r"clipboard|QApplication\.clipboard", tout, re.I):
        return []
    return [Constat(
        gravite="mineur",
        mesure="aucune action de copie trouvée",
        probleme="le détail technique n'est pas transmissible",
        pourquoi="pour demander de l'aide, l'utilisateur doit recopier à la "
                 "main un message qu'il ne comprend pas",
        action="bouton « Copier le détail » : chemin, ligne, cause, version",
    )]


@agent(D, "M-07", "Pas de retour après une action longue", "majeur")
def progression(ctx):
    tout = "\n".join(ctx.sources[f] for f in ctx.fichiers_de(r"/ui/"))
    barres = len(re.findall(r"QProgressBar|QProgressDialog", tout))
    imports = len(re.findall(r"def .*import|read_csv|load_", tout))
    if barres >= 2 or imports < 5:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{imports} opérations de lecture pour {barres} barres de "
                f"progression",
        probleme="rien ne dit que le travail avance",
        pourquoi="sur 500 forages, l'utilisateur croit que le logiciel a "
                 "planté et clique à nouveau",
        action="progression chiffrée (« 312 forages sur 500 ») + bouton "
               "Annuler qui annule vraiment",
    )]
