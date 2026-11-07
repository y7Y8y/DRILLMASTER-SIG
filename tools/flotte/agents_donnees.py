"""Départements G et H — Données (2D, 3D, carte) ; Cohérence et doctrine."""
from __future__ import annotations

import re
from collections import Counter

from noyau import Constat, agent, compte, departement

G = departement("Données et vues",
                "une donnée, cinq vues ; aucun calcul dupliqué")
H = departement("Cohérence et doctrine",
                "un mot = une chose ; une règle = un seul endroit")


@agent(G, "T-01", "Géométrie recalculée dans les vues", "bloquant")
def geometrie_dupliquee(ctx):
    fichiers = [f for f in ctx.fichiers
                if re.search(r"(section|view_3d|renderer|topograph|"
                             r"track_layout|scale)", f)]
    calculs = []
    for rel in fichiers:
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if re.search(r"(math\.(sin|cos|tan|atan2|sqrt)|np\.(sin|cos|"
                         r"tan|arctan2|sqrt))", ligne):
                calculs.append((rel, no))
    par_fichier = Counter(f for f, _ in calculs)
    if len(par_fichier) < 4:
        return []
    return [Constat(
        gravite="bloquant",
        mesure=f"trigonométrie présente dans {len(par_fichier)} fichiers de "
                f"vue ({len(calculs)} lignes)",
        probleme="la position des forages est recalculée dans chaque vue",
        pourquoi="la coupe et la 3D finissent par ne plus montrer la même "
                 "chose ; c'est l'incohérence la plus difficile à croire "
                 "pour un géologue",
        action="un seul calcul de trajectoire dans le noyau, importé par "
               "toutes les vues (R-09)",
    )] + [Constat(gravite="mineur", fichier=f, mesure=f"{n} calculs "
                   f"trigonométriques dans cette vue",
                   probleme="vue qui calcule au lieu d'afficher",
                   pourquoi="deux vues peuvent diverger sans qu'aucun test "
                            "ne le voie",
                   action="déplacer le calcul dans le noyau")
          for f, n in par_fichier.most_common(3) if n >= 8]


@agent(G, "T-02", "Trois moteurs de rendu pour la même 3D", "majeur")
def moteurs_3d(ctx):
    fichiers = [f for f in ctx.fichiers if "3d" in f.lower()]
    if len(fichiers) < 4:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(fichiers)} fichiers pour la vue 3D : "
                + ", ".join(f.split('/')[-1] for f in fichiers[:6]),
        probleme="plusieurs implémentations de la même vue coexistent",
        pourquoi="une correction n'est faite que dans l'une : selon le chemin "
                 "d'ouverture, l'utilisateur ne voit pas la même 3D",
        action="une seule vue 3D livrée, les autres supprimées ou rangées "
               "hors du plugin",
    )]


@agent(G, "T-03", "Le même export réimplémenté", "majeur")
def exports(ctx):
    fichiers = [f for f in ctx.fichiers if "export" in f.lower()]
    if len(fichiers) < 3:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(fichiers)} modules d'export : "
                + ", ".join(f.split('/')[-1] for f in fichiers),
        probleme="PDF, image et échelle sont dessinés plusieurs fois",
        pourquoi="l'aperçu et le fichier produit ne se ressemblent pas, ce "
                 "qui est la pire surprise possible avant impression",
        action="un seul dessinateur de coupe, utilisé par l'aperçu, l'écran "
               "et l'export",
    )]


@agent(G, "T-04", "Aucune gestion du très grand nombre de forages", "majeur")
def performance(ctx):
    tout = "\n".join(ctx.sources[f] for f in ctx.fichiers_de(r"/(ui|core)/"))
    caches = len(re.findall(r"cache|lru_cache|memo", tout, re.I))
    boucles = len(re.findall(r"for .* in .*\bfor .* in ", tout))
    if caches >= 10:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{caches} mécanismes de cache détectés",
        probleme="le rendu recalcule tout à chaque changement de réglage",
        pourquoi="sur 500 forages, bouger un curseur devient saccadé : "
                 "l'utilisateur croit que le logiciel est cassé",
        action="calculer une fois par changement de données, redessiner "
               "seulement ce qui change ; mesure publiée (forages/seconde)",
    )]


@agent(G, "T-05", "Aucune vue carte alors que QGIS en fournit une", "note")
def carte(ctx):
    tout = "\n".join(ctx.sources.values())
    if re.search(r"QgsMapLayer|carte|map_canvas", tout, re.I):
        return []
    return [Constat(
        gravite="note",
        mesure="aucune intégration de la carte QGIS trouvée",
        probleme="le projet ne se voit pas sur une carte",
        pourquoi="un géologue situe toujours un forage sur une carte avant "
                 "de regarder une coupe",
        action="un onglet Carte qui réutilise les mêmes réglages de piste "
               "(R-09) — la carte est déjà là, il suffit de s'y brancher",
    )]


@agent(H, "C-01", "Deux mots pour la même chose", "majeur")
def vocabulaire(ctx):
    paires = [("forage", "trou"), ("coupe", "section"), ("piste", "track"),
              ("teneur", "teneur"), ("altération", "alteration"),
              ("écarté", "exclu"), ("profondeur", "profondeur finale")]
    constats = []
    for fr, en in [("coupe", "section"), ("piste", "track"),
                   ("teneur", "assay"), ("forage", "hole"),
                   ("altération", "alteration")]:
        n_fr = len(compte(rf"\b{fr}", ctx, [f for f in ctx.fichiers]))
        n_en = len(compte(rf"\b{en}", ctx, [f for f in ctx.fichiers]))
        if n_fr >= 5 and n_en >= 5:
            constats.append(Constat(
                gravite="mineur",
                mesure=f"« {fr} » {n_fr} fois et « {en} » {n_en} fois",
                probleme="le code et l'écran n'emploient pas le même mot",
                pourquoi="la documentation, les messages et l'interface "
                         "finissent par parler deux langues",
                action="un lexique (déjà écrit : `specs/data/lexique.json`) "
                       "utilisé aussi par le code",
            ))
    return constats


@agent(H, "C-02", "Règle de gestion présente à deux endroits", "bloquant")
def regles(ctx):
    # un seuil numérique recopié est une règle qui va diverger
    seuils = Counter()
    lieux = {}
    for rel in [f for f in ctx.fichiers if re.search(r"/(core|ui)/", f)]:
        for m in re.finditer(r"(?:seuil|threshold|tol[ée]rance|min_|max_)"
                             r"\w*\s*[=:]\s*([\d.]+)", ctx.sources[rel]):
            v = m.group(1)
            seuils[v] += 1
            lieux.setdefault(v, rel)
    recopies = [(v, n) for v, n in seuils.items()
                if n >= 4 and v not in ("0", "0.0", "1", "1.0")]
    if not recopies:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(recopies)} valeur(s) de seuil recopiée 4 fois ou plus "
                f"(ex. {recopies[0][0]} ×{recopies[0][1]}, dans "
                f"{lieux[recopies[0][0]].split('/')[-1]})",
        probleme="une règle métier est écrite en dur à plusieurs endroits",
        pourquoi="changer un seuil à un endroit produit deux vérités, donc "
                 "deux résultats différents pour la même donnée",
        action="les seuils vivent dans le projet, une seule définition, "
               "affichée avec sa provenance (R-27)",
    )]


@agent(H, "C-03", "La doctrine n'est pas vérifiée par la machine", "majeur")
def doctrine(ctx):
    import noyau
    gardes = (noyau.RACINE / "tools" / "spec_check.py").exists()
    return [Constat(
        gravite="mineur" if gardes else "majeur",
        mesure="la spec est écrite, mais rien dans le plugin ne la relit" if
                not gardes else "un vérificateur existe hors du plugin",
        probleme="les règles vivent dans un document que le code ignore",
        pourquoi="une règle non vérifiée est une intention : elle sera "
                 "oubliée à la troisième correction",
        action="exécuter les 31 règles à chaque livraison, et refuser une "
               "livraison qui en viole une",
    )]
