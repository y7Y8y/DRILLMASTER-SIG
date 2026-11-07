"""Département C — Options, réglages, ce qui se partage et ce qui se répète.

C'est le département qui répond à : « taille doit se répéter et rien »,
« des options manquent », « des sous-options mélangées dans les grands ».
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from noyau import Constat, agent, departement

D = departement("Réglages et partage",
                "un réglage = un propriétaire ; aucune copie dans une vue")

# les 15 champs du contrat de piste (specs/data/tracks.json)
CHAMPS = ["id", "label", "famille", "visible", "largeur", "opacite", "cote",
          "unite", "minimum", "maximum", "couleur", "motif", "etiquette",
          "ordre", "source"]

CATEGORIES = {
    "largeur": r"largeur|width|_w\b|setFixedWidth|setMinimumWidth",
    "opacite": r"opacit|alpha|setOpacity",
    "cote": r"\bcote\b|side|droite|gauche",
    "couleur": r"couleur|color|palette|colormap",
    "motif": r"motif|pattern|hachure",
    "etiquette": r"etiquette|label|text_|legende|legend",
}


@agent(D, "F-01", "Le même réglage existe dans plusieurs écrans", "bloquant")
def reglage_duplique(ctx):
    """Un réglage défini deux fois finit par avoir deux valeurs."""
    constats = []
    occurrences = defaultdict(list)
    for rel in ctx.fichiers_de(r"/ui/"):
        for cat, motif in CATEGORIES.items():
            for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
                if re.search(motif, ligne, re.I) and re.search(
                        r"Q(SpinBox|DoubleSpinBox|ComboBox|Slider|CheckBox)\(", ligne):
                    occurrences[cat].append((rel, no))
    for cat, lieux in occurrences.items():
        fichiers = {f for f, _ in lieux}
        if len(fichiers) >= 3:
            constats.append(Constat(
                gravite="bloquant",
                mesure=f"« {cat} » réglable dans {len(lieux)} endroits de "
                        f"{len(fichiers)} fichiers",
                probleme="le même réglage a plusieurs propriétaires",
                pourquoi="changer la largeur dans la coupe ne change pas la "
                         "largeur dans la 3D : l'utilisateur règle deux fois "
                         "et croit que le logiciel est cassé",
                action="un objet de piste unique, cinq lecteurs ; les vues "
                       "n'affichent qu'un miroir en lecture seule (R-09)",
            ))
        elif len(fichiers) == 2:
            constats.append(Constat(
                gravite="majeur",
                mesure=f"« {cat} » réglable dans {len(fichiers)} fichiers",
                probleme="réglage à deux endroits",
                pourquoi="deux valeurs peuvent diverger sans que personne ne "
                         "le remarque",
                action="désigner un propriétaire, l'autre devient un affichage",
            ))
    return constats


@agent(D, "F-02", "Champs du contrat reconnus mais non réglables", "majeur")
def champs_manquants(ctx):
    """Un champ qu'on lit mais qu'on ne peut pas régler est une option qui
    manque — exactement ce que l'utilisateur cherche sans le trouver."""
    alias = {"largeur": r"largeur|width", "opacite": r"opacit|alpha",
             "cote": r"cote|side", "couleur": r"couleur|color",
             "motif": r"motif|pattern", "etiquette": r"etiquette|label_pos",
             "unite": r"unite|unit", "minimum": r"minimum", "maximum": r"maximum",
             "ordre": r"ordre|order", "famille": r"famille|family",
             "source": r"source", "label": r"label", "visible": r"visible"}
    editable = {}
    for rel in ctx.fichiers_de(r"/ui/"):
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if not re.search(r"Q(SpinBox|DoubleSpinBox|ComboBox|Slider|LineEdit|"
                             r"CheckBox)\(|setFixedWidth|setValue\(", ligne):
                continue
            for champ, motif in alias.items():
                if re.search(motif, ligne, re.I):
                    editable.setdefault(champ, (rel, no))
    manquants = [c for c in CHAMPS if c not in editable and c not in
                 ("id", "label", "famille", "source")]
    if not manquants:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(manquants)} champ(s) sans contrôle éditable : "
                + ", ".join(manquants),
        probleme="le champ existe dans les données, il n'existe pas à l'écran",
        pourquoi="c'est « des options qui manquent » : on cherche le réglage, "
                 "il n'a jamais été dessiné",
        action="un contrôle par champ du contrat, au même endroit pour les 12 "
               "pistes, avec la valeur héritée affichée (R-07)",
    )]


@agent(D, "F-03", "Sous-options mélangées dans les grands réglages", "majeur")
def melange(ctx):
    """Une case à cocher qui cache cinq champs : personne ne les trouve."""
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        cases = len(re.findall(r"QCheckBox\(", txt))
        groupes = len(re.findall(r"QGroupBox\(", txt))
        champs = len(re.findall(r"Q(SpinBox|DoubleSpinBox|LineEdit)\(",
                                txt)) + len(re.findall(r"QComboBox\(", txt))
        if champs > 0 and groupes == 0 and champs >= 12:
            constats.append(Constat(
                gravite="majeur", fichier=rel,
                mesure=f"{champs} champs et {cases} cases, aucun groupe titré",
                probleme="tout est au même niveau : pas de parent, pas d'enfant",
                pourquoi="« des sous-options mélangées dans les grands » : "
                         "impossible de deviner qu'un champ appartient à une "
                         "autre option",
                action="arbre à deux niveaux maximum : un groupe = une "
                       "décision, ses champs en dessous, indentés",
            ))
    return constats


@agent(D, "F-04", "Réglages réinitialisés sans prévenir", "majeur")
def reinit(ctx):
    lieux = []
    for rel in ctx.fichiers:
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if re.search(r"(reset|réinitial|reinit|clear_settings|"
                         r"QSettings\(\)\.clear)", ligne, re.I):
                lieux.append((rel, no, ligne.strip()))
    if len(lieux) < 5:
        return []
    return [Constat(
        gravite="majeur",
        mesure=f"{len(lieux)} endroits qui remettent des réglages à zéro",
        probleme="la remise à zéro est éparpillée",
        pourquoi="l'utilisateur perd sa configuration sans savoir ce qui l'a "
                 "effacée",
        action="une seule action « Rétablir les réglages d'origine », qui "
               "annonce ce qu'elle change avant de le faire",
    )]


@agent(D, "F-05", "Pas de valeur par défaut explicite : l'option est muette", "majeur")
def defaut_muet(ctx):
    """Un réglage dont on ne sait pas d'où vient la valeur (R-27)."""
    constats = []
    for rel in ctx.fichiers_de(r"/ui/"):
        txt = ctx.sources[rel]
        spins = re.findall(r"(self\.\w+)\s*=\s*Q(Double)?SpinBox\(", txt)
        for nom, _ in spins:
            suite = txt.split(nom + " = ", 1)[-1][:400]
            if not re.search(r"setValue\(|setRange\(", suite):
                constats.append(Constat(
                    gravite="mineur", fichier=rel,
                    mesure=f"`{nom}` créé sans valeur initiale visible",
                    probleme="le champ démarre sur une valeur que rien "
                             "n'explique",
                    pourquoi="l'utilisateur ne sait pas si le 0 est un choix "
                             "ou un oubli",
                    action="chaque réglage affiche d'où vient sa valeur "
                           "(héritée, par défaut, calculée)",
                ))
    return constats[:8]


@agent(D, "F-06", "Aucun lien entre un réglage et ce qu'il change", "mineur")
def lien_reglage(ctx):
    tout = "\n".join(ctx.sources[f] for f in ctx.fichiers_de(r"/ui/"))
    connexions = len(re.findall(r"\.connect\(", tout))
    reglages = len(re.findall(r"Q(CheckBox|ComboBox|SpinBox|DoubleSpinBox|"
                              r"Slider|LineEdit)\(", tout))
    if not reglages:
        return []
    ratio = connexions / reglages
    if ratio > 1.5:
        return []
    return [Constat(
        gravite="mineur",
        mesure=f"{reglages} contrôles pour {connexions} connexions "
                f"(ratio {ratio:.1f})",
        probleme="des contrôles qui n'annoncent pas ce qu'ils changent",
        pourquoi="on bouge un curseur et rien ne se passe à l'écran : "
                 "l'utilisateur doute du logiciel",
        action="chaque contrôle indique sa portée (coupe, 3D, légende, "
               "export, carte) avant d'être modifié",
    )]
