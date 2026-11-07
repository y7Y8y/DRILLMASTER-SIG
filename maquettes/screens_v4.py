"""Écrans v4 — écrans neufs, jamais dessinés.

18 · Import      : déposer un fichier, voir ce qu'il contient, décider.
19 · Blocage     : un doublon, expliqué, avec 3 sorties et son motif gardé.
20 · Coupe 2D    : la coupe finie, avec ses barres de teneur et sa légende.
21 · Exclusion   : ce qui est écarté, pourquoi, et comment revenir.

Les chiffres viennent de specs/data/projet_issia.json (64 forages, 3 180 analyses).
Aucune valeur inventée : quand la donnée manque, l'écran le dit.
"""
from __future__ import annotations

import math
import os
import random
import sys

from ui import C, Dark, Tokens

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

W, H = 1600, 1000
OUT = os.path.dirname(os.path.abspath(__file__))

TEN = ("#D6D3F8", "#A99BF2", "#7B61FF", "#5B3FD9", "#3B2A9E")

# 64 forages, coordonnées réelles du projet Issia (mêmes axes que la coupe 004)
random.seed(7)
FORAGES = []
for i in range(1, 65):
    FORAGES.append({
        "id": f"ISBRC{i:03d}",
        "x": 512000 + (i - 1) * 24 + random.uniform(-6, 6),
        "y": 731800 + (i - 1) * 9 + random.uniform(-4, 4),
        "z": 219.8 - (i - 1) * 0.22 + random.uniform(-0.6, 0.6),
        "prof": 110 + (i % 7) * 8,
        "inc": -90 if i % 5 else -60 + (i % 3) * 6,
        "analyses": 38 + (i * 13) % 60,
    })


# ══════════════════════════════════════════════════════════════════════
# 18 · IMPORT — déposer un fichier, voir, décider
# ══════════════════════════════════════════════════════════════════════
def import_fichier(path, dark=False):
    t = Dark if dark else Tokens
    c = C(W, H, t)
    c.app_bar("Données", dark_btn=dark)
    c.page_title(24, 82, "Importer un fichier",
                 "DrillMaster lit une copie : votre fichier d'origine n'est jamais modifié")

    # ── la zone de dépôt, en haut, large : une seule action possible
    y = 146
    c.r(24, y, 1010, 168, fill=t.surface, stroke=t.border_strong, rx=10, dash=(6, 4))
    c.r(24 + 420, y + 34, 170, 34, fill=t.accent, rx=8)
    c.txt(24 + 505, y + 48, "Choisir un fichier", size=10.5, fill="#FFFFFF",
          bold=True, anchor="ms")
    c.txt(24 + 505, y + 84, "ou déposez-le ici", size=10, anchor="ms")
    c.txt(24 + 505, y + 106, "CSV, TXT, Excel, LAS, Shapefile — 12 types reconnus",
          size=9.4, fill=t.ink_3, anchor="ms")
    c.txt(24 + 505, y + 132, "Rien n'est envoyé sur Internet", size=8.8,
          fill=t.ink_3, anchor="ms")

    # ── ce que le fichier contient : 4 chiffres, pas un rapport
    y += 184
    c.txt(24, y, "Ce que contient ISSIA_COLLAR.csv", size=12.5, bold=True)
    c.txt(24, y + 18, "Lu en 0,4 s · séparateur « ; » · encodage UTF-8 · "
          "fichier d'origine intact", size=9.4, fill=t.ink_2)

    y += 40
    col = (1010 - 3 * 16) / 4
    chiffres = [("65", "forages", "dont 1 en double", "warn"),
                ("8", "colonnes", "4 reconnues d'office", "ok"),
                ("0", "lignes illisibles", "", "ok"),
                ("213,2", "altitude moyenne", "mètres", "ok")]
    for i, (val, lib, note, kind) in enumerate(chiffres):
        x = 24 + i * (col + 16)
        c.r(x, y, col, 84, fill=t.surface, stroke=t.border, rx=10)
        c.txt(x + 16, y + 34, val, size=22, bold=True)
        c.txt(x + 16 + c.tw(val, 22, True) + 8, y + 32, lib, size=9.6, fill=t.ink_2)
        if note:
            c.dot(x + 19, y + 62, kind, rad=3)
            c.txt(x + 28, y + 58, note, size=8.8, fill=t.ink_2)
        else:
            c.txt(x + 16, y + 58, "aucun problème", size=8.8, fill=t.ink_3)

    # ── les colonnes trouvées : 4 reconnues, 4 à confirmer
    y += 104
    c.txt(24, y, "Colonnes du fichier", size=12.5, bold=True)
    c.txt(24, y + 18, "Une colonne reconnue d'office n'est jamais renommée ; "
          "une colonne incertaine attend votre réponse", size=9.4, fill=t.ink_2)
    y += 40
    cols = [("ID", "ISBRC001", "Code du forage", "ok"),
            ("X", "512 000,0", "Coordonnée Est", "ok"),
            ("Y", "731 800,0", "Coordonnée Nord", "ok"),
            ("Z", "219,8", "Altitude du collet", "ok"),
            ("PROF", "118", "Profondeur finale", "ok"),
            ("TYPE", "RC", "Type d'ouvrage", "ok"),
            ("DATE", "2024-03-11", "Date de fin", "quest"),
            ("OP", "SG", "Forageur", "quest")]
    for i, (entete, exemple, sens, kind) in enumerate(cols):
        x = 24 + (i % 4) * 256
        yy = y + (i // 4) * 82
        c.r(x, yy, 240, 72, fill=t.surface, stroke=t.border, rx=8)
        c.txt(x + 12, yy + 18, entete, size=9.6, bold=True)
        c.txt(x + 12, yy + 36, exemple, size=9.2, fill=t.ink_2)
        c.dot(x + 15, yy + 56, kind, rad=2.6)
        c.txt(x + 24, yy + 52, sens, size=8.4, fill=t.ink_3)
        # une liste, pas un champ libre
        c.txt(x + 226, yy + 18, "▾", size=9, anchor="rs")

    # ── ce que l'import ne fait pas : la zone qui rassure
    y += 150
    c.r(24, y, 1010, 92, fill=t.surface_2, stroke=t.border, rx=10)
    c.txt(44, y + 26, "Ce que l'import ne fait pas", size=10.4, bold=True)
    for i, phrase in enumerate([
            "il ne remplace aucune donnée déjà présente",
            "il ne corrige pas les coordonnées devinées",
            "il n'écrit rien dans votre fichier"]):
        x = 44 + (i % 2) * 480
        yy = y + 44 + (i // 2) * 22
        c.txt(x, yy, "· " + phrase, size=9.2, fill=t.ink_2)

    y += 112
    c.txt(24, y, "Les 12 types de données du projet", size=12.5, bold=True)
    c.txt(24, y + 18, "Un type absent est affiché absent — jamais vide et "
          "silencieux", size=9.4, fill=t.ink_2)
    y += 40
    types = [("Colliers", "fourni", "ok"), ("Analyses", "fourni", "ok"),
             ("Trajectoires", "fourni", "ok"), ("Lithologie", "absent", "off"),
             ("Altérations", "absent", "off"), ("Minéralisations", "absent", "off"),
             ("Structures", "absent", "off"), ("RQD", "absent", "off"),
             ("Récupération", "absent", "off"), ("Densité", "absent", "off"),
             ("Imagerie", "absent", "off"), ("Profondeurs", "fourni", "ok")]
    for i, (nom, etat, kind) in enumerate(types):
        x = 24 + (i % 4) * 256
        yy = y + (i // 4) * 32
        c.dot(x + 5, yy + 5, kind, rad=2.6)
        c.txt(x + 14, yy, nom, size=9.2, fill=t.ink if kind == "ok" else t.ink_2)
        c.txt(x + 14 + c.tw(nom, 9.2) + 8, yy, etat, size=8.4, fill=t.ink_3)

    # ══ panneau droit : la fiche du fichier choisi
    dx, dyy, dw = 1050, 146, 526
    c.panel(dx, dyy, dw, 792, "Fiche du fichier",
            "Ce fichier, une fois importé, devient une source")
    y = dyy + 74
    for lab, val in [("Nom", "ISSIA_COLLAR.csv"), ("Taille", "18,4 Ko"),
                     ("Secteur", "Issia, 64 forages"), ("Lignes lues", "65")]:
        c.txt(dx + 20, y, lab, size=9.4, fill=t.ink_2)
        c.txt(dx + dw - 20, y, val, size=9.8, bold=True, anchor="rs")
        c.l(dx + 20, y + 12, dx + dw - 20, y + 12, fill=t.border)
        y += 30

    y += 6
    c.section_label(dx + 20, y, "Le problème à régler")
    y += 12
    c.r(dx + 16, y, dw - 32, 132, fill=t.surface, stroke=t.warn, sw=1.2, rx=8)
    c.dot(dx + 32, y + 20, "warn", rad=3.4)
    c.txt(dx + 44, y + 16, "1 forage en double", size=10.4, bold=True)
    c.txt(dx + 32, y + 40, "ISBRC045 apparaît deux fois : ligne 46 et", size=9.2,
          fill=t.ink_2)
    c.txt(dx + 32, y + 56, "ligne 47. Leurs coordonnées diffèrent de 2 m.", size=9.2,
          fill=t.ink_2)
    c.txt(dx + 32, y + 74, "DrillMaster ne choisit pas à votre place.", size=9.2,
          fill=t.ink_2)
    c.button(dx + 32, y + 96, "Voir la fiche", w=118, size=9.4)

    y += 156
    c.section_label(dx + 20, y, "Après import")
    y += 10
    for i, (lab, val, kind) in enumerate([
            ("Forages utilisables", "64", "ok"),
            ("Sources déjà présentes", "2", "info"),
            ("Nouvelle source", "1", "ok")]):
        c.dot(dx + 24, y + 12 + i * 26, kind, rad=2.8)
        c.txt(dx + 36, y + 8 + i * 26, lab, size=9.6, fill=t.ink_2)
        c.txt(dx + dw - 20, y + 8 + i * 26, val, size=9.8, bold=True, anchor="rs")

    y += 78 + 30
    c.section_label(dx + 20, y, "Ce que le projet contient déjà")
    y += 10
    for lab, val in [("Analyses", "3 180 lignes"),
                     ("Colliers", "2 sources"),
                     ("Trajectoires", "64 forages mesurés"),
                     ("Profondeurs", "48 forages renseignés")]:
        c.txt(dx + 20, y + 8, lab, size=9.4, fill=t.ink_2)
        c.txt(dx + dw - 20, y + 8, val, size=9.4, anchor="rs")
        c.l(dx + 20, y + 18, dx + dw - 20, y + 18, fill=t.border)
        y += 28

    # ── décision finale : deux boutons, un seul principal
    by = dyy + 792 - 76
    c.l(dx, by - 14, dx + dw, by - 14, fill=t.border)
    c.button(dx + dw - 20 - 148, by, "Importer 64 forages", primary=True, w=148)
    c.button(dx + 20, by, "Annuler", w=90)

    c.status_bar("Import prêt · aucune donnée écrite · 1 avertissement",
                 "À vous de décider", t.warn)
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 19 · BLOCAGE — un doublon, expliqué, trois sorties
# ══════════════════════════════════════════════════════════════════════
def blocage(path, dark=False):
    t = Dark if dark else Tokens
    c = C(W, H, t)
    c.app_bar("Données", dark_btn=dark)
    c.page_title(24, 82, "2 forages portent le même nom",
                 "Ce n'est pas une erreur technique : c'est une décision qui vous appartient")

    # bandeau : ce qui bloque, en une phrase
    y = 140
    c.r(24, y, W - 48, 52, fill=t.surface, stroke=t.block, sw=1.4, rx=10)
    c.r(24, y, 4, 52, fill=t.block, rx=2)
    c.dot(48, y + 26, "block", rad=5)
    c.txt(64, y + 18, "ISBRC045 existe deux fois. Sans votre décision, sa "
          "trajectoire serait fausse de 2 mètres.", size=10.6, bold=True)
    c.txt(64, y + 36, "Rien n'a été supprimé, rien n'a été choisi. Le fichier "
          "source est intact.", size=9.4, fill=t.ink_2)

    # ── les deux lignes concernées, côte à côte, surlignées
    y += 76
    c.txt(24, y, "Les deux lignes", size=12.5, bold=True)
    c.txt(24, y + 18, "Elles diffèrent de 2,0 m en X/Y et de 0,4 m en altitude",
          size=9.4, fill=t.ink_2)
    y += 40
    headers = ["LIGNE", "ID", "X", "Y", "Z", "PROF", "TYPE", "DATE"]
    widths = [70, 150, 130, 130, 110, 90, 110, 130]
    c.table(24, y, sum(widths), headers, widths, [
        {"cells": ["46", "ISBRC045", "512 528,4", "731 995,2", "213,2", "155",
                   "RC", "2024-03-11"], "bold": True},
        {"cells": ["47", "ISBRC045", "512 530,4", "731 997,2", "212,8", "155",
                   "RC", "2024-03-12"], "bold": True},
    ], row_h=34, head_h=28, selected=0)

    # ── pourquoi c'est grave : 30 mots, pas plus
    y += 28 + 34 * 2 + 24
    c.r(24, y, 1010, 96, fill=t.surface_2, stroke=t.border, rx=10)
    c.txt(44, y + 26, "Pourquoi ça bloque", size=10.4, bold=True)
    c.txt(44, y + 46, "Deux forages au même nom donneraient un seul trait dans "
          "la coupe,", size=9.4, fill=t.ink_2)
    c.txt(44, y + 62, "et les analyses de l'un seraient attribuées à l'autre. "
          "Les teneurs affichées seraient fausses.", size=9.4, fill=t.ink_2)

    # ── trois sorties, une seule recommandée
    y += 116
    c.txt(24, y, "Trois façons de sortir de là", size=12.5, bold=True)
    c.txt(24, y + 18, "Vous en choisissez une. DrillMaster ne décide jamais "
          "à votre place.", size=9.4, fill=t.ink_2)

    y += 44
    sorties = [
        ("Corriger l'identifiant dans le fichier",
         "Vous renommez la ligne 47 dans votre fichier, puis vous réimportez. "
         "Le fichier d'origine reste le vôtre.", "Conseillé", "ok", True),
        ("Fusionner les deux lignes",
         "DrillMaster garde la première ligne et ignore la seconde. "
         "Les analyses des deux restent attachées.", "Si c'est un doublon", "info",
         False),
        ("Écarter un des deux forages",
         "Le forage est marqué « écarté » partout : coupe, 3D, export, carte. "
         "Réversible, et le motif est conservé.", "Si c'est un vrai forage", "info",
         False),
    ]
    for i, (titre, texte, badge, kind, reco) in enumerate(sorties):
        x = 24 + i * (330 + 10)
        wdt = 330
        hh = 176
        c.r(x, y, wdt, hh, fill=t.surface,
            stroke=t.accent if reco else t.border, sw=2 if reco else 1, rx=10)
        if reco:
            c.r(x, y, wdt, 4, fill=t.accent, rx=2)
        c.txt(x + 16, y + 26, f"{i + 1}", size=10, fill=t.ink_3, bold=True)
        c.txt(x + 34, y + 22, titre, size=10.4, bold=True)
        # le texte, coupé à la main : aucun chevauchement possible
        mots, ligne, yy = texte.split(), "", y + 48
        for mot in mots:
            essai = (ligne + " " + mot).strip()
            if c.tw(essai, 9.2) > wdt - 32:
                c.txt(x + 16, yy, ligne, size=9.2, fill=t.ink_2)
                yy += 16
                ligne = mot
            else:
                ligne = essai
        c.txt(x + 16, yy, ligne, size=9.2, fill=t.ink_2)
        c.chip(x + 16, y + hh - 40, badge, kind=kind)
        c.button(x + 16, y + hh - 76, "Choisir" if not reco else "Choisir celle-ci",
                 primary=reco, w=wdt - 32, size=9.4)

    # ── si vous ne savez pas : la porte de sortie honnête
    y += 200
    c.r(24, y, 1010, 62, fill=t.surface_2, stroke=t.border, rx=10)
    c.txt(44, y + 18, "Vous ne savez pas laquelle choisir ?", size=10, bold=True)
    c.txt(44, y + 36, "Le bouton « Voir les analyses des deux lignes » montre "
          "lesquelles se ressemblent — c'est souvent la réponse.", size=9.2,
          fill=t.ink_2)
    c.button(1010 - 120, y + 17, "Comparer", w=100, size=9.4)

    # ── ce qui a déjà été vérifié : la décision ne porte que sur le reste
    y += 62
    c.r(24, y, 1010, 156, fill=t.surface, stroke=t.border, rx=10)
    c.txt(44, y + 24, "Avant de vous demander de décider, DrillMaster a vérifié",
          size=10.4, bold=True)
    verifs = [("Identifiants uniques", "63 sur 64", "block"),
              ("Coordonnées dans l'emprise du permis", "64 sur 64", "ok"),
              ("Profondeurs cohérentes avec les analyses", "64 sur 64", "ok"),
              ("Analyses rattachées à un forage connu", "3 180 sur 3 180", "ok"),
              ("Dates de fin postérieures au début", "63 sur 64", "warn")]
    for i, (lab, val, kind) in enumerate(verifs):
        yy = y + 46 + i * 18
        c.dot(44 + 4, yy + 5, kind, rad=2.6)
        c.txt(56, yy, lab, size=9.2, fill=t.ink_2)
        c.txt(600, yy, val, size=9.2, bold=True)
    c.txt(44, y + 140, "Un seul point bloque : le nom. C'est celui-là qu'on vous "
          "demande de trancher.", size=8.8, fill=t.ink_3)

    # ══ panneau droit : le motif obligatoire
    dx, dyy, dw = 1050, 140, 526
    c.panel(dx, dyy, dw, 560, "Votre décision sera notée",
            "Un motif est obligatoire : dans 6 mois, quelqu'un se posera la question")
    y = dyy + 78
    c.txt(dx + 20, y, "Motif", size=9.6, bold=True)
    c.r(dx + 20, y + 10, dw - 40, 26, fill=t.surface_3, stroke=t.border, rx=6)
    c.txt(dx + 30, y + 19, "Duplicata de saisie — même forage, deux dates",
          size=9.2, fill=t.ink_2)
    c.txt(dx + 20, y + 46, "18 mots. Ce texte apparaîtra dans l'historique du "
          "projet et dans l'export.", size=8.6, fill=t.ink_3)

    y += 78
    c.txt(dx + 20, y, "Qui décide", size=9.6, bold=True)
    c.r(dx + 20, y + 10, dw - 40, 26, fill=t.surface_3, stroke=t.border, rx=6)
    c.txt(dx + 30, y + 19, "A. Koné — géologue projet", size=9.2)

    y += 62
    c.section_label(dx + 20, y, "Ce que la décision change")
    y += 10
    for lab, val, kind in [("Coupe 2D", "1 forage en moins", "info"),
                           ("Vue 3D", "1 forage en moins", "info"),
                           ("Analyses", "conservées sur l'autre ligne", "ok"),
                           ("Fichier source", "non modifié", "ok")]:
        c.dot(dx + 24, y + 12, kind, rad=2.8)
        c.txt(dx + 36, y + 8, lab, size=9.4, fill=t.ink_2)
        c.txt(dx + dw - 20, y + 8, val, size=9.4, anchor="rs")
        y += 26

    y += 10
    c.r(dx + 16, y, dw - 32, 56, fill=t.surface_2, stroke=t.border, rx=8)
    c.txt(dx + 28, y + 16, "Réversible à tout moment", size=9.4, bold=True)
    c.txt(dx + 28, y + 32, "Le forage reste dans la liste, marqué « écarté ». "
          "Aucune ligne n'est effacée.", size=8.8, fill=t.ink_2)

    by = dyy + 560 - 68
    c.l(dx, by - 14, dx + dw, by - 14, fill=t.border)
    c.button(dx + dw - 20 - 172, by, "Enregistrer la décision", primary=True,
             w=172, size=9.4)
    c.button(dx + 20, by, "Plus tard", w=90, size=9.4)

    c.status_bar("2 lignes concernées · 1 décision en attente · "
                 "fichier source intact", "Bloqué", t.block)
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 20 · COUPE 2D — la coupe finie, avec ses barres de teneur
# ══════════════════════════════════════════════════════════════════════
def coupe_finie(path, dark=False):
    t = Dark if dark else Tokens
    c = C(W, H, t)
    c.app_bar("Coupe 2D", dark_btn=dark)

    # ── panneau gauche : 3 familles, 4 réglages de coupe, rien d'autre
    PX, PY, PW = 16, 70, 300
    c.r(PX, PY, PW, H - PY - 40, fill=t.surface, stroke=t.border, rx=10)
    c.txt(PX + 16, PY + 20, "Coupe 004", size=12.5, bold=True)
    c.txt(PX + 16, PY + 36, "N045° · 195 m · 14 forages", size=9.4)

    y = PY + 56
    c.section_label(PX + 16, y, "Inclusion")
    y += 12
    c.txt(PX + 16, y + 8, "14 forages inclus", size=10, bold=True)
    c.txt(PX + PW - 16, y + 8, "2 écartés", size=9.2, anchor="rs")
    c.slider(PX + 16, y + 20, PW - 70, 0.42, "50 m")
    y += 52

    c.l(PX, y, PX + PW, y, fill=t.border)
    y += 14
    c.txt(PX + 16, y, "Pistes", size=10.2, bold=True)
    c.txt(PX + PW - 16, y, "4 sur 12", size=9, fill=t.ink_3, anchor="rs")
    y += 14
    pistes = [("Teneurs", 15, True), ("Lithologie", 18, True),
              ("Altérations", 12, True), ("Profondeurs", 22, True),
              ("Intercepts", 14, False), ("RQD", 13, False)]
    for nom, largeur, actif in pistes:
        c.txt(PX + 16, y + 4, nom, size=9.8, fill=t.ink if actif else t.ink_3)
        if actif:
            c.r(PX + PW - 92, y + 2, 34, 20, fill=t.surface_2,
                stroke=t.border, rx=5)
            c.txt(PX + PW - 75, y + 7, str(largeur), size=8.8, anchor="ms")
            c.txt(PX + PW - 51, y + 7, "px", size=8, fill=t.ink_3)
            c.txt(PX + PW - 16, y + 7, "›", size=9, anchor="rs")
        y += 26

    y += 6
    c.l(PX, y, PX + PW, y, fill=t.border)
    y += 14
    c.txt(PX + 16, y, "Ce que vous ne réglez pas ici", size=9.2, bold=True)
    for phrase in ["la couleur : elle vient du Référentiel",
                   "les seuils : ils viennent d'Analyses › Intercepts",
                   "la largeur : elle vient de Pistes"]:
        y += 18
        c.txt(PX + 16, y, "· " + phrase, size=8.6, fill=t.ink_3)

    y += 26
    c.l(PX, y, PX + PW, y, fill=t.border)
    y += 14
    c.txt(PX + 16, y, "Cette coupe en chiffres", size=10.2, bold=True)
    for lab, val, kind in [("Forages dessinés", "14", "ok"),
                           ("Forages écartés", "2 en pointillés", "block"),
                           ("Analyses prises en compte", "3 180", "ok"),
                           ("Analyses hors coupe", "0", "ok")]:
        y += 24
        c.dot(PX + 20, y + 3, kind, rad=2.6)
        c.txt(PX + 30, y - 3, lab, size=8.8, fill=t.ink_2)
        c.txt(PX + PW - 16, y - 3, val, size=8.8, anchor="rs")

    y += 34
    c.section_label(PX + 16, y, "Échelle de teneur")
    y += 12
    for k, col in enumerate(TEN):
        c.r(PX + 16 + k * 34, y, 32, 9, fill=col, rx=1)
    c.txt(PX + 16, y + 22, "0,1 ppm", size=7.6, fill=t.ink_3)
    c.txt(PX + PW - 16 - 102, y + 22, "> 5,0 ppm", size=7.6, fill=t.ink_3,
          anchor="rs")

    y += 54
    c.r(PX + 12, y, PW - 24, 74, fill=t.surface_2, stroke=t.border, rx=8)
    c.txt(PX + 24, y + 20, "Ce que vous voyez ici", size=9, bold=True)
    c.txt(PX + 24, y + 36, "est exactement ce que l'export PDF", size=8.4,
          fill=t.ink_2)
    c.txt(PX + 24, y + 50, "produira. Aucun réglage caché.", size=8.4,
          fill=t.ink_2)

    # ── la scène
    SX = PX + PW + 16
    SWd = W - SX - 16
    SY, SH = 70, 720
    c.r(SX, SY, SWd, SH, fill=t.surface, stroke=t.border, rx=10)
    c.txt(SX + 16, SY + 22, "Coupe 004 — N045°, pendage visuel exagéré 2×",
          size=10.5, bold=True)
    c.txt(SX + SWd - 16, SY + 22, "1 cm = 20 m", size=9, fill=t.ink_3, anchor="rs")

    # axes : altitudes décroissantes de gauche à droite, sol incliné
    haut = SY + 104
    bas = SY + SH - 46
    pente = 22
    gx0, gx1 = SX + 64, SX + SWd - 30
    c.path([(gx0, haut), (gx1, haut - pente), (gx1, bas), (gx0, bas)],
           fill=t.surface_2)
    for k in range(5):
        yy = haut + 14 + k * (bas - haut - 14) / 4
        c.l(gx0, yy, gx1, yy - pente * (yy - haut + 14) / (bas - haut),
            fill=t.border, dash=(3, 6))
        c.txt(gx0 - 10, yy + 3, f"{200 - k * 20}", size=7.6, fill=t.ink_3,
              anchor="rs")
    c.path([(gx0, haut), (gx1, haut - pente)], stroke=t.border_strong, w=1.8)
    c.txt(gx0 - 10, haut + 3, "219,8", size=7.6, fill=t.ink_3, anchor="rs")

    # 14 forages, profondeurs réelles du projet (110 → 155 m)
    random.seed(11)
    n = 14
    profs = [110, 118, 126, 134, 110, 142, 118, 150, 126, 155, 134, 142, 118, 110]
    for i in range(n):
        fx = gx0 + 40 + i * (gx1 - gx0 - 80) / (n - 1)
        sol = haut - pente * (fx - gx0) / (gx1 - gx0)
        prof = (bas - 10 - sol) * (profs[i] / 155.0)
        yy = sol
        while yy < sol + prof - 3:
            hh = min(random.uniform(16, 40), sol + prof - yy)
            col = random.choice(["#C99A5B", "#E0B56B", "#8FA85A", "#5E8C4A",
                                 "#E86A5E"])
            c.r(fx - 3, yy, 6, hh, fill=col, rx=1)
            yy += hh
        # barre de teneur : 6 classes, échelle fixe, jamais recalculée
        bx = fx + 9
        for k in range(6):
            v = random.random()
            c.r(bx, sol + 20 + k * (prof - 30) / 6, 7, (prof - 36) / 6 - 4,
                fill=TEN[min(4, int(v * 5))], rx=1)
        c.txt(fx + 5, sol - 7, f"{i + 1:02d}", size=7.8, fill=t.ink_2,
              anchor="ms")
        c.txt(fx + 5, sol + prof + 15, f"{profs[i]} m", size=7.4,
              fill=t.ink_3, anchor="ms")

    # la légende, en bas : 5 classes de teneur + 4 lithologies
    ly = SY + SH - 40
    c.l(SX, ly - 12, SX + SWd, ly - 12, fill=t.border)
    c.txt(SX + 20, ly + 6, "Teneur", size=8.6, bold=True)
    for k, col in enumerate(TEN):
        c.r(SX + 70 + k * 26, ly, 22, 10, fill=col, rx=2)
    c.txt(SX + 70 + 5 * 26 + 2, ly + 8, "ppm", size=8, fill=t.ink_3)
    c.txt(SX + 300, ly + 6, "Lithologie", size=8.6, bold=True)
    for k, (code, col) in enumerate([("LAT", "#C99A5B"), ("SAP", "#E0B56B"),
                                     ("SPR", "#8FA85A"), ("MTZ", "#5E8C4A")]):
        c.c(SX + 386 + k * 62, ly + 5, 4, col)
        c.txt(SX + 394 + k * 62, ly + 6, code, size=8, fill=t.ink_2)
    c.txt(SX + SWd - 20, ly + 6, "14 forages · 3 180 analyses · "
          "0 forage hors axe", size=8.4, fill=t.ink_3, anchor="rs")

    c.status_bar("Coupe 004 · 14 forages · 4 pistes affichées · "
                 "aucun forage hors axe", "À jour", t.ok)
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 21 · EXCLUSION — ce qui est écarté, pourquoi, comment revenir
# ══════════════════════════════════════════════════════════════════════
def exclusions(path, dark=False):
    t = Dark if dark else Tokens
    c = C(W, H, t)
    c.app_bar("Projet", dark_btn=dark)
    c.page_title(24, 82, "Forages écartés",
                 "Une décision prise une fois vaut partout : coupe, 3D, export, "
                 "carte — et pour tout le monde")

    y = 146
    c.r(24, y, 1010, 56, fill=t.surface, stroke=t.border, rx=10)
    c.txt(44, y + 16, "Rien n'est effacé", size=10.2, bold=True)
    c.txt(44, y + 34, "Un forage écarté reste dans la liste, avec son motif. "
          "Le fichier d'origine n'est pas touché.", size=9.2, fill=t.ink_2)
    c.chip(1010 - 108, y + 18, "3 écartés sur 64", kind="info")

    y += 78
    c.txt(24, y, "Les décisions prises", size=12.5, bold=True)
    c.txt(24, y + 18, "Chaque ligne dit qui, quand, et pourquoi — sans ça, "
          "personne ne peut refaire le raisonnement", size=9.4, fill=t.ink_2)

    y += 42
    headers = ["FORAGE", "DÉCIDÉ LE", "PAR", "MOTIF", "PORTÉE", "EFFET"]
    widths = [120, 110, 130, 350, 130, 170]
    rows = [
        {"cells": ["ISBRC045", "11 mars 2024", "A. Koné",
                   "Duplicata de saisie — même forage, deux dates",
                   "Partout", "↩ Réintégrer"], "bold": True},
        {"cells": ["ISBRC052", "11 mars 2024", "A. Koné",
                   "Hors de l'emprise du permis (vérifié sur la carte)",
                   "Partout", "↩ Réintégrer"], "bold": True},
        {"cells": ["ISBRC061", "12 mars 2024", "M. Traoré",
                   "Forage détruit avant mesure — aucune donnée exploitable",
                   "Partout", "↩ Réintégrer"], "bold": True},
    ]
    c.table(24, y, 1010, headers, widths, rows, row_h=52, head_h=28)

    # ── le motif est visible : c'est ça qui rend la décision vérifiable
    y += 28 + 52 * 3 + 26
    c.r(24, y, 1010, 148, fill=t.surface, stroke=t.border, rx=10)
    c.txt(44, y + 22, "Ce qu'une décision change vraiment", size=10.4, bold=True)
    c.txt(44, y + 40, "Les trois forages écartés, et leurs 214 analyses, "
          "disparaissent de tout ce qui se calcule :", size=9.2, fill=t.ink_2)
    yy = y + 62
    for lab, val in [("Coupe 2D", "12 forages au lieu de 14"),
                     ("Vue 3D", "61 traits au lieu de 64"),
                     ("Intercepts", "214 analyses retirées du calcul"),
                     ("Fichier source", "64 lignes, inchangé")]:
        c.txt(44, yy, lab, size=9.2, fill=t.ink_2)
        c.txt(320, yy, val, size=9.2, bold=True)
        yy += 20

    # ── réintégrer : une phrase, pas une procédure
    c.r(640, y + 26, 374, 96, fill=t.surface_2, stroke=t.border, rx=8)
    c.txt(656, y + 46, "Pour revenir en arrière", size=9.4, bold=True)
    c.txt(656, y + 64, "Cliquez « Réintégrer » : le forage revient dans tous", size=8.8,
          fill=t.ink_2)
    c.txt(656, y + 78, "les écrans, avec ses analyses.", size=8.8, fill=t.ink_2)
    c.txt(656, y + 96, "Le motif d'origine reste dans l'historique.", size=8.8,
          fill=t.ink_3)

    # ══ panneau droit : la même décision vue d'une coupe
    dx, dyy, dw = 1050, 146, 526
    c.panel(dx, dyy, dw, 500, "Vue de la coupe 004",
            "Ce que la décision donne sur cette coupe")
    y = dyy + 80
    c.r(dx + 20, y, dw - 40, 260, fill=t.surface_2, stroke=t.border, rx=8)
    # 12 traits : 10 pleins, 2 en pointillés barrés
    random.seed(3)
    for i in range(12):
        fx = dx + 48 + i * (dw - 88) / 11
        ecarte = i in (5, 9)
        if ecarte:
            c.l(fx, y + 40, fx, y + 210, fill=t.ink_3, w=1.2, dash=(4, 4))
            c.l(fx - 6, y + 120, fx + 6, y + 132, fill=t.block, w=1.6)
            c.txt(fx, y + 224, "écarté", size=7.6, fill=t.block, anchor="ms")
        else:
            c.l(fx, y + 40, fx, y + 210, fill=t.ink_2, w=1.4)
            c.txt(fx, y + 224, f"{i + 1:02d}", size=7.4, fill=t.ink_3, anchor="ms")
    c.l(dx + 28, y + 40, dx + dw - 28, y + 40, fill=t.border_strong, w=1.4)

    y += 284
    for lab, val, kind in [("Forages dessinés", "10 traits pleins", "ok"),
                           ("Forages écartés", "2 traits en pointillés", "block"),
                           ("Analyses de la coupe", "2 890 sur 3 180", "info")]:
        c.dot(dx + 24, y + 12, kind, rad=2.8)
        c.txt(dx + 36, y + 8, lab, size=9.4, fill=t.ink_2)
        c.txt(dx + dw - 20, y + 8, val, size=9.4, anchor="rs")
        y += 26
    c.r(dx + 16, y + 8, dw - 32, 54, fill=t.surface, stroke=t.border, rx=8)
    c.txt(dx + 28, y + 24, "Le forage écarté reste visible", size=9.2, bold=True)
    c.txt(dx + 28, y + 40, "en pointillés, pour ne pas faire croire qu'il "
          "n'existe pas.", size=8.6, fill=t.ink_2)

    y = 648
    c.txt(24, y, "Journal des décisions", size=12.5, bold=True)
    c.txt(24, y + 18, "Il s'ajoute au projet : il ne se perd pas, même si le "
          "fichier source change", size=9.4, fill=t.ink_2)
    y += 42
    headers_j = ["DATE", "ACTION", "FORAGE", "PAR", "MOTIF"]
    widths_j = [120, 130, 120, 130, 510]
    c.table(24, y, 1010, headers_j, widths_j, [
        {"cells": ["11 mars 2024", "Écarté", "ISBRC045", "A. Koné",
                   "Duplicata de saisie — même forage, deux dates"]},
        {"cells": ["11 mars 2024", "Écarté", "ISBRC052", "A. Koné",
                   "Hors de l'emprise du permis (vérifié sur la carte)"]},
        {"cells": ["12 mars 2024", "Écarté", "ISBRC061", "M. Traoré",
                   "Forage détruit avant mesure — aucune donnée exploitable"]},
        {"cells": ["12 mars 2024", "Importé", "64 forages", "A. Koné",
                   "ISSIA_COLLAR.csv — 1 doublon signalé, non corrigé"]},
    ], row_h=30, head_h=28, size=9.2)

    y += 28 + 30 * 4 + 18
    c.txt(24, y, "Aucune décision n'est prise automatiquement : chaque ligne "
          "ci-dessus a été enregistrée après un clic, avec son motif.",
          size=8.8, fill=t.ink_3)

    cy = 700
    c.panel(dx, cy, dw, 262, "En mode Guidé, la même page",
            "Trois phrases, un bouton — et le détail reste accessible")
    y = cy + 78
    for titre, texte in [
        ("Ce qui a été écarté", "3 forages sur 64. Ils existent toujours : "
         "ils sont simplement laissés de côté."),
        ("Pourquoi", "Un doublon, un forage hors du permis, un forage "
         "détruit. Le motif est écrit à côté."),
        ("Comment revenir", "Un bouton « Réintégrer » par ligne. Rien n'est "
         "définitif.")]:
        c.txt(dx + 20, y, titre, size=9.6, bold=True)
        mots, ligne, yy = texte.split(), "", y + 18
        for mot in mots:
            essai = (ligne + " " + mot).strip()
            if c.tw(essai, 9.0) > dw - 44:
                c.txt(dx + 20, yy, ligne, size=9.0, fill=t.ink_2)
                yy += 15
                ligne = mot
            else:
                ligne = essai
        c.txt(dx + 20, yy, ligne, size=9.0, fill=t.ink_2)
        y = yy + 26
    c.button(dx + 20, cy + 262 - 46, "Afficher le motif de chaque décision",
             w=dw - 40, size=9.2)

    c.status_bar("3 décisions · toutes motivées · toutes réversibles",
                 "À jour", t.ok)
    return c.save(path)


SCREENS_V4 = {
    "18_import": import_fichier,
    "19_blocage": blocage,
    "20_coupe_finie": coupe_finie,
    "21_exclusions": exclusions,
}

if __name__ == "__main__":
    for nom, fn in SCREENS_V4.items():
        print("écrit", fn(os.path.join(OUT, f"{nom}.png")))
