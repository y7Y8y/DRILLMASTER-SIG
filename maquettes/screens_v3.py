"""Écrans v3 — ceux qui répondent aux cinq reproches.

1 · Pistes        : une seule déclaration par piste, héritage type → piste.
2 · Partages      : un réglage, cinq lecteurs (2D, 3D, légende, export, carte).
3 · Données       : 12 types hiérarchisés en 3 rangs, catégories rattachées.
4 · Message       : une erreur expliquée en mots simples, avec 3 sorties.
5 · États         : les 5 états, en voix Guidée et en voix Experte.

Aucun de ces écrans ne reprend l'ancien panneau : ni groupe « Affichage de la
coupe », ni case empilée, ni réglage dupliqué.
"""
from __future__ import annotations

import math
import random

from ui import C, Dark, Tokens, switch

W, H = 1600, 1000

RANG = {
    1: ("#0F766E", "Rang 1 · socle"),
    2: ("#2E5BFF", "Rang 2 · observation"),
    3: ("#7F56D9", "Rang 3 · calculé"),
}


# ══════════════════════════════════════════════════════════════════════
# petits utilitaires de mise en page
# ══════════════════════════════════════════════════════════════════════
def tag(c, x, y, text, col, soft=True):
    """Étiquette de catégorie, plus discrète qu'une pilule d'état."""
    t = c.th
    wd = c.tw(text, 8.6, True) + 16
    c.r(x, y, wd, 17, fill=(col + "14") if soft else col, rx=4)
    c.txt(x + 8, y + 12, text, size=8.6, fill=col, bold=True, anchor="ls")
    return wd


def field(c, x, y, w, value, unit="", inherited=False):
    """Champ compact : la valeur éditable, et « hérité » quand elle vient du type."""
    t = c.th
    c.r(x, y, w, 26, fill=t.surface_2 if inherited else t.surface,
        stroke=t.border_strong, rx=6)
    if inherited:
        c.c(x + 10, y + 13, 2.2, t.ink_3)
        c.txt(x + 17, y + 17, value, size=9.6, fill=t.ink_3, anchor="ls")
    else:
        c.txt(x + 9, y + 17, value, size=9.8, fill=t.ink, anchor="ls")
    if unit:
        c.txt(x + w - 9, y + 17, unit, size=8.8, fill=t.ink_3, anchor="rs")
    return w


def label(c, x, y, text, col=None):
    c.txt(x, y, text.upper(), size=8.4, fill=col or c.th.ink_3, bold=True,
          anchor="ls")
    return y + 10


def sentence(c, x, y, text, maxw, size=10, fill=None, lh=15):
    """Retour à la ligne manuel — jamais de débordement."""
    t = c.th
    fill = fill or t.ink_2
    words, line, out = text.split(), "", []
    for wd in words:
        cand = (line + " " + wd).strip()
        if c.tw(cand, size) > maxw and line:
            out.append(line)
            line = wd
        else:
            line = cand
    if line:
        out.append(line)
    for i, ln in enumerate(out):
        c.txt(x, y + i * lh, ln, size=size, fill=fill, anchor="ls")
    return y + len(out) * lh


# ══════════════════════════════════════════════════════════════════════
# 1 · PISTES — le contrat, une déclaration par piste
# ══════════════════════════════════════════════════════════════════════
PISTES = [
    # (famille, nom, détail, visible, largeur, opacité, côté, hérité, état)
    ("STRUCTURELLES", "Profondeurs", "graduations tous les 20 m", True, "22",
     "100", "Gauche", True, "ok"),
    ("STRUCTURELLES", "Trajectoire", "64 forages", True, "20", "100",
     "Gauche", True, "ok"),
    ("STRUCTURELLES", "Intercepts", "25 intercepts · 4 règles", True, "14",
     "100", "Gauche", True, "ok"),
    ("CATÉGORIELLES", "Lithologie", "30 familles · 2 410 int.", True, "18",
     "100", "Gauche", False, "ok"),
    ("CATÉGORIELLES", "Altérations", "27 familles · 1 902 int.", True, "12",
     "100", "Gauche", True, "ok"),
    ("CATÉGORIELLES", "Minéralisations", "3 codes · 742 points", True, "10",
     "100", "Gauche", True, "ok"),
    ("CATÉGORIELLES", "Structures", "212 mesures", True, "10", "100",
     "Gauche", True, "warn"),
    ("QUANTITATIVES", "Teneurs", "Au · 3 180 analyses", True, "15", "90",
     "Droite", True, "ok"),
    ("QUANTITATIVES", "RQD", "88 mesures", True, "13", "100", "Droite", True,
     "ok"),
    ("QUANTITATIVES", "Récupération", "non fourni", False, "13", "100",
     "Droite", True, "info"),
    ("QUANTITATIVES", "Densité", "non fourni", False, "13", "100", "Droite",
     True, "info"),
    ("MÉDIAS", "Imagerie", "18 clichés de carotte", True, "16", "100",
     "Droite", True, "ok"),
]


def pistes(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Coupe 2D", dark_btn=dark)
    c.page_title(24, 82, "Pistes",
                 "12 pistes en 4 familles · une seule déclaration chacune · "
                 "les mêmes réglages partout")

    # barre d'outils
    y = 132
    c.segmented(24, y, ["Par type", "Vue d'ensemble"], 0)
    c.txt(300, y + 16, "Réglage de groupe", size=9.2, fill=t.ink_3, anchor="ls")
    c.button(430, y - 2, "Appliquer à la famille…", w=170, size=9.6)
    c.button(612, y - 2, "Tout remettre à zéro", w=180, size=9.6)
    c.chip(W - 24 - 236, y + 2, "Aucun réglage dupliqué", "ok")

    # ── liste
    lx, ly, lw, lh = 24, 172, 1010, 792
    c.panel(lx, ly, lw, lh, "Les 12 pistes",
            "La famille donne les valeurs ; la piste peut surcharger · le rond = valeur héritée")
    yy = ly + 66
    # entêtes de colonnes
    for hd, xx in (("Visible", lx + 20), ("Piste", lx + 96),
                   ("Largeur", lx + 430), ("Opacité", lx + 540),
                   ("Côté", lx + 648), ("État", lx + 800)):
        c.txt(xx, yy, hd.upper(), size=8.4, fill=t.ink_3, bold=True,
              anchor="ls")
    c.l(lx + 12, yy + 10, lx + lw - 12, yy + 10, fill=t.border)
    yy += 22

    group = None
    for type_, nom, detail, vis, largeur, opac, cote, herite, etat in PISTES:
        if type_ != group:
            group = type_
            # ligne de groupe = les valeurs héritées, éditables une seule fois
            c.r(lx + 12, yy, lw - 24, 30, fill=t.surface_3, rx=7)
            c.txt(lx + 22, yy + 20, type_.title(), size=9.2, fill=t.ink_2,
                  bold=True, anchor="ls")
            n = sum(1 for p in PISTES if p[0] == type_)
            c.txt(lx + 22 + c.tw(type_.title(), 9.2, True) + 10, yy + 20,
                  f"{n} pistes · les valeurs ci-dessous sont héritées",
                  size=8.8, fill=t.ink_3, anchor="ls")
            c.txt(lx + 620, yy + 20, "même réglage pour la famille", size=8.6,
                  fill=t.ink_3, anchor="ls")
            yy += 34

        rh = 42
        c.r(lx + 12, yy, lw - 24, rh - 4,
            fill=t.accent_soft if nom == "Teneurs" else None, rx=7)
        if nom == "Teneurs":
            c.r(lx + 12, yy, 3, rh - 4, fill=t.accent, rx=1)
        switch(c, lx + 20, yy + 11, vis)
        c.txt(lx + 96, yy + 10, nom, size=10.2, bold=True,
              fill=t.ink if vis else t.ink_3, anchor="ls")
        c.txt(lx + 96, yy + 25, detail, size=8.4, fill=t.ink_3, anchor="ls")
        field(c, lx + 430, yy + 5, 80, largeur, "px", herite)
        field(c, lx + 536, yy + 5, 80, opac, "%", herite)
        field(c, lx + 642, yy + 5, 100, cote, "", herite)
        c.dot(lx + 806, yy + 15, etat)
        c.txt(lx + 818, yy + 10, {"ok": "à jour", "warn": "3 réserves",
                                  "info": "en attente"}[etat], size=9,
              fill=t.ink_3, anchor="ls")
        c.txt(lx + lw - 34, yy + 10, "›", size=13, fill=t.ink_3, anchor="ls")
        yy += rh

    c.txt(lx + 20, ly + lh - 16,
          "Cliquez sur une valeur pour forcer cette piste seule.", size=8.6,
          fill=t.ink_3, anchor="ls")

    # ── détail
    dx, dy, dw = 1050, 176, 526
    c.panel(dx, dy, dw, 792, "Teneurs (Au)",
            "Quantitative · 1 des 4 de sa famille")

    yy = dy + 72
    yy = label(c, dx + 16, yy, "Commune aux 12 pistes")
    commun = [("Visible", "oui", False), ("Largeur", "15 px", True),
              ("Opacité", "90 %", True), ("Côté", "droite", True),
              ("Filtre", "aucun", False), ("Export", "visible", False)]
    for nom, val, herite in commun:
        c.txt(dx + 16, yy + 12, nom, size=9.8, fill=t.ink, anchor="ls")
        if herite:
            c.c(dx + 340, yy + 8, 2.2, t.ink_3)
            c.txt(dx + 348, yy + 12, "hérité", size=8.6, fill=t.ink_3,
                  anchor="ls")
        c.txt(dx + dw - 16, yy + 12, val, size=9.8, fill=t.ink_2,
              anchor="rs")
        yy += 24

    yy += 12
    yy = label(c, dx + 16, yy, "Propre à cette piste")
    propres = [("Méthode de classes", "quantiles"), ("Nombre de classes", "5"),
               ("Rampe", "YlOrRd"), ("Seuils", "0,1 · 1 · 5 ppm")]
    for nom, val in propres:
        c.r(dx + 16, yy + 2, dw - 32, 30, fill=t.surface_2, stroke=t.border,
            rx=6)
        c.txt(dx + 26, yy + 15, nom, size=9.6, fill=t.ink, anchor="ls")
        c.txt(dx + dw - 26, yy + 15, val, size=9.6, fill=t.ink_2,
              anchor="rs")
        yy += 34

    yy += 10
    yy = label(c, dx + 16, yy, "Où ce réglage s'applique")
    for i, (nom, actif) in enumerate([("Coupe 2D", True), ("Vue 3D", True),
                                     ("Légende", True), ("Export PDF", True),
                                     ("Carte QGIS", False)]):
        xx = dx + 16 + (i % 2) * 250
        ry = yy + (i // 2) * 26
        c.dot(xx + 4, ry + 8, "ok" if actif else "off")
        c.txt(xx + 16, ry + 12, nom, size=9.4,
              fill=t.ink if actif else t.ink_3, anchor="ls")
        if not actif:
            c.txt(xx + 16, ry + 24, "vue d'ensemble, pas de piste", size=8,
                  fill=t.ink_3, anchor="ls")
    yy += 84

    # aperçu de la piste
    ry = yy + 30
    c.panel(dx + 16, ry, dw - 32, 116, "Aperçu dans la coupe",
            "Ce que vous voyez est ce qui sortira à l'export")
    ax, aw = dx + 34, dw - 68
    for k in range(8):
        fx = ax + 26 + (aw - 60) * k / 7
        c.l(fx, ry + 62, fx + 2, ry + 104, fill=t.ink_3, w=1)
        for j in range(4):
            v = 0.25 + ((k * 7 + j * 3) % 10) / 14
            c.r(fx + 4, ry + 62 + j * 10, 4 + v * 26, 7.5,
                fill=["#B42318", "#DC6803", "#F79009", "#FDB022"][j], rx=1)

    c.status_bar("Coupe 004 · 12 pistes · 1 contrat · dernier calcul il y a 18 min",
                 "À jour")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 2 · UN RÉGLAGE, CINQ LECTEURS
# ══════════════════════════════════════════════════════════════════════
LECTEURS = ["Coupe 2D", "Vue 3D", "Légende", "Export PDF", "Carte QGIS"]

# ok = appliqué · herite = vient du type · non = sans objet (+ raison)
MATRICE = [
    ("Largeur", "Coupe 2D → Pistes", [("ok", "17 px"), ("ok", "0,8 m"),
                                      ("ok", "idem"), ("ok", "idem"),
                                      ("herite", "hérité")]),
    ("Opacité", "Coupe 2D → Pistes", [("ok", "90 %"), ("ok", "90 %"),
                                      ("ok", "90 %"), ("ok", "90 %"),
                                      ("non", "aplat")]),
    ("Côté", "Coupe 2D → Pistes", [("ok", "gauche"), ("non", "la scène tourne"),
                                   ("ok", "gauche"), ("ok", "gauche"),
                                   ("non", "vue de dessus")]),
    ("Remplissage", "Projet → Référentiel", [("ok", "référentiel"),
                                             ("ok", "référentiel"),
                                             ("ok", "référentiel"),
                                             ("ok", "référentiel"),
                                             ("ok", "référentiel")]),
    ("Motif", "Projet → Référentiel", [("ok", "30 motifs"), ("non", "masqué"),
                                       ("ok", "30 motifs"), ("ok", "30 motifs"),
                                       ("non", "trop petit")]),
    ("Échelle de teneur", "Coupe 2D → Pistes", [("herite", "hérité"),
                                                ("herite", "hérité"),
                                                ("ok", "4 classes"),
                                                ("ok", "4 classes"),
                                                ("ok", "4 classes")]),
    ("Seuils de coupure", "Analyse → Intercepts", [("ok", "3 seuils"),
                                                    ("ok", "3 seuils"),
                                                    ("ok", "3 seuils"),
                                                    ("ok", "3 seuils"),
                                                    ("ok", "3 seuils")]),
    ("Étiquettes", "Coupe 2D → Pistes", [("ok", "9 pt"), ("ok", "9 pt"),
                                         ("ok", "9 pt"), ("ok", "9 pt"),
                                         ("non", "confetti")]),
]

CELL = {"ok": ("✓", "#12B76A"), "herite": ("↺", "#98A2B3"),
        "non": ("—", "#D0D5DD")}


def partages(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Coupe 2D", dark_btn=dark)
    c.page_title(24, 82, "Un réglage, cinq lecteurs",
                 "Le même objet est lu par la coupe, la 3D, la légende, "
                 "l'export et la carte — jamais recopié")

    # bandeau avant / après
    y = 132
    c.r(24, y, 760, 66, fill="#FFF4F2", stroke="#F9D6D0", rx=9)
    c.txt(40, y + 20, "Avant", size=9, fill="#B42318", bold=True, anchor="ls")
    c.txt(40, y + 38, "3 magasins de réglages · 78 clés plates · "
          "9 clés manquantes (RQD, récupération, densité)", size=9.6,
          fill="#7A271A", anchor="ls")

    c.r(800, y, 776, 66, fill="#EEF9F2", stroke="#C7EFDA", rx=9)
    c.txt(816, y + 20, "Maintenant", size=9, fill="#067647", bold=True,
          anchor="ls")
    c.txt(816, y + 38, "1 magasin · 14 emplacements communs + les réglages "
          "propres à chaque type de piste", size=9.6, fill="#05603A",
          anchor="ls")

    # matrice
    ty = 214
    c.panel(24, ty, W - 48, 556, "Qui lit quoi",
            "Une ligne = un réglage. Une colonne = une vue. Aucune case vide "
            "sans raison écrite.")

    cx0 = 470
    colw = (W - 48 - cx0 - 20) / len(LECTEURS)
    hy = ty + 80
    for i, l in enumerate(LECTEURS):
        c.txt(cx0 + colw * i + colw / 2, hy, l.upper(), size=8.6, fill=t.ink_3,
              bold=True, anchor="ms")
    c.txt(44, hy, "RÉGLAGE", size=8.6, fill=t.ink_3, bold=True, anchor="ls")
    c.txt(260, hy, "QUI LE POSSÈDE", size=8.6, fill=t.ink_3, bold=True,
          anchor="ls")
    c.l(40, hy + 10, W - 40, hy + 10, fill=t.border)

    ry = hy + 22
    for nom, proprio, cells in MATRICE:
        c.l(40, ry + 54, W - 40, ry + 54, fill=t.border)
        c.txt(44, ry + 24, nom, size=10.2, fill=t.ink, bold=True, anchor="ls")
        c.txt(260, ry + 24, proprio, size=9, fill=t.ink_3, anchor="ls")
        for i, (kind, val) in enumerate(cells):
            xx = cx0 + colw * i + colw / 2
            glyph, col = CELL[kind]
            c.txt(xx, ry + 24, glyph, size=11, fill=col, bold=True,
                  anchor="ms")
            c.txt(xx, ry + 40, val, size=8.6,
                  fill=t.ink_3 if kind != "ok" else t.ink_2, anchor="ms")
        ry += 54

    # légende + règle anti-rechute
    ly = 794
    for i, (glyph, col, txt_) in enumerate([
            ("✓", "#12B76A", "appliqué"), ("↺", "#98A2B3", "hérité du type"),
            ("—", "#D0D5DD", "sans objet, la raison est écrite")]):
        xx = 44 + i * 250
        c.txt(xx, ly, glyph, size=11, fill=col, bold=True, anchor="ms")
        c.txt(xx + 12, ly, txt_, size=9, fill=t.ink_3, anchor="ls")

    ry2 = 818
    c.r(24, ry2, W - 48, 130, fill=t.surface, stroke=t.border, rx=9)
    c.txt(44, ry2 + 26, "La règle qui empêche la rechute", size=11, bold=True,
          anchor="ls")
    regles = [
        ("Si un réglage apparaît dans deux vues, il remonte dans le contrat.",
         "Il n'est plus réglable vue par vue."),
        ("S'il n'apparaît que dans une vue, il reste au module propriétaire.",
         "Un seul endroit, nommé dans la colonne « qui le possède »."),
        ("Aucune vue ne stocke sa propre copie.",
         "Elle lit l'objet commun ; c'est vérifié par un test."),
    ]
    for i, (a, b) in enumerate(regles):
        xx = 44 + i * 508
        c.dot(xx + 4, ry2 + 58, "ok")
        sentence(c, xx + 16, ry2 + 62, a, 460, 9.2, t.ink)
        sentence(c, xx + 16, ry2 + 94, b, 460, 8.8, t.ink_3)

    c.status_bar("Aucun réglage n'est saisi deux fois · "
                 "les 3 domaines non fournis restent vides et signalés", "Cohérent")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 3 · DONNÉES — 12 types, 3 rangs, des catégories qui restent à leur place
# ══════════════════════════════════════════════════════════════════════
RANGS = {
    1: ("Socle — vos repères", "Ce qui situe le forage. Jamais recalculé, "
        "jamais écrasé."),
    2: ("Ce que vous observez", "Ce que vous saisissez ou importez, avec des "
        "catégories nommées par vous."),
    3: ("Ce qui se calcule", "Jamais importé directement : DrillMaster le "
        "déduit des rangs 1 et 2."),
}

TYPES = [
    # rang, nom, nature, catégories montrées, nombre total, quantité, état
    (1, "Collets", "le point d'entrée du forage en surface",
     ["ISBRC001…064"], 1, "60 forages", "ok"),
    (1, "Déviations", "l'écart du forage, mesuré tous les 30 m",
     ["61 forages sur 64"], 1, "3 sans mesure", "warn"),
    (1, "Topographie", "le relief, en raster ou en points", ["MNT 30 m"], 1,
     "1 source", "ok"),
    (1, "Profils d'ouvrage", "l'échelle d'affichage par type de sonde",
     ["RC/DD", "AUGER", "PUITS", "CUSTOM"], 4, "", "ok"),
    (2, "Lithologie", "la roche traversée",
     ["Saprolite", "Latérite", "Métasédiment", "Pegmatite"], 30, "2 410 int.",
     "ok"),
    (2, "Altérations", "l'état de la roche",
     ["Sain", "Saprolitisé", "Altéré", "Très altéré"], 27, "1 902 int.", "ok"),
    (2, "Minéralisations", "ce qui est visible à l'œil",
     ["Quartz", "Sulfures", "Oxydes"], 3, "742 points", "ok"),
    (2, "Structures", "les plans, les failles, les veines",
     ["Foliation", "Faille", "Veine"], 6, "212 mesures", "ok"),
    (2, "Teneurs", "les analyses chimiques",
     ["Au", "Cu", "Li", "Ag"], 4, "3 180 analyses", "ok"),
    (2, "Imagerie", "les photos de carotte", ["18 clichés"], 1, "18 photos",
     "ok"),
    (3, "RQD", "la qualité de la roche, déduite des fractures", [], 0,
     "non fourni", "info"),
    (3, "Récupération", "le rendement du carottage, déduit", [], 0,
     "non fourni", "info"),
]


def donnees_rangs(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Données", dark_btn=dark)
    c.page_title(24, 82, "Données",
                 "12 types rangés par nature — un type ne peut pas changer de "
                 "rang en cours de route")

    # compteur de contrôles, en clair
    y = 132
    c.r(24, y, W - 48, 52, fill=t.surface, stroke=t.border, rx=9)
    c.dot(44, y + 26, "block")
    c.txt(58, y + 21, "2 lignes bloquent la suite", size=10.4, bold=True,
          anchor="ls")
    c.txt(58, y + 38, "elles concernent 1 fichier sur 6 · rien n'a été "
          "modifié dans vos fichiers", size=9, fill=t.ink_3, anchor="ls")
    c.txt(W - 44, y + 30, "Voir le détail", size=9.4, fill=t.accent, bold=True,
          anchor="rs")
    c.txt(W - 180, y + 30, "1 question · 5 avertissements · 79 informations",
          size=9, fill=t.ink_3, anchor="rs")

    # trois colonnes de rangs
    ty = 202
    colw = (W - 48 - 2 * 16) / 3
    for i, (rang, (titre, sous)) in enumerate(RANGS.items()):
        x = 24 + i * (colw + 16)
        col = RANG[rang][0]
        c.r(x, ty, colw, 700, fill=t.surface, stroke=t.border, rx=10)
        c.r(x, ty, colw, 3, fill=col, rx=0)
        c.txt(x + 18, ty + 30, titre, size=12.6, bold=True, anchor="ls")
        yy = sentence(c, x + 18, ty + 52, sous, colw - 36, 9.2, t.ink_3)
        c.l(x, yy + 12, x + colw, yy + 12, fill=t.border)

        yy += 26
        for r_, nom, nature, cats, ntot, quant, etat in TYPES:
            if r_ != rang:
                continue
            c.dot(x + 22, yy + 13, etat)
            c.txt(x + 36, yy + 6, nom, size=10.4, bold=True, anchor="ls")
            if quant:
                c.txt(x + colw - 18, yy + 6, quant, size=8.6, fill=t.ink_3,
                      anchor="rs")
            yy = sentence(c, x + 36, yy + 24, nature, colw - 60, 8.8, t.ink_3,
                          13) + 6

            if cats:
                cx, cy = x + 36, yy
                for cat in cats:
                    wdt = c.tw(cat, 8.6, True) + 16
                    if cx + wdt > x + colw - 18:
                        cx, cy = x + 36, cy + 21
                    tag(c, cx, cy, cat, col)
                    cx += wdt + 6
                reste = ntot - len(cats)
                if reste > 0:
                    txt_ = f"+ {reste}"
                    wdt = c.tw(txt_, 8.6, True) + 14
                    if cx + wdt > x + colw - 18:
                        cx, cy = x + 36, cy + 21
                    c.txt(cx, cy + 12, txt_, size=8.6, fill=t.ink_3,
                          anchor="ls")
                    cx += wdt
                yy = cy + 26

            c.l(x + 18, yy, x + colw - 18, yy, fill=t.border)
            yy += 14

        pied = {
            1: "Lu, jamais recalculé.\nPour le corriger, on corrige le fichier source.",
            2: "Les catégories que vous nommez\nsont à vous : elles vivent au Référentiel.",
            3: "Un RQD mesuré qui arriverait serait reçu\ncomme un type du rang 2, sans rien casser.",
        }[rang]
        for k, ln in enumerate(pied.split("\n")):
            c.txt(x + 18, ty + 700 - 46 + k * 14, ln, size=8.6, fill=t.ink_3)

    c.status_bar("12 types · 6 fournis · 2 lignes bloquantes · "
                 "aucun fichier source modifié", "2 blocages", t.block)
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 4 · UN MESSAGE QUI SE COMPREND
# ══════════════════════════════════════════════════════════════════════
def message(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Données", dark_btn=dark)
    c.page_title(24, 82, "2 forages portent le même nom",
                 "Ligne 45 et ligne 88 de ISSIA_COLLAR.csv · fichier non "
                 "modifié")

    # bandeau de niveau, en mots
    y = 132
    c.r(24, y, W - 48, 58, fill="#FFF4F2", stroke="#F9D6D0", rx=9)
    c.dot(46, y + 29, "block")
    c.txt(60, y + 20, "Blocage — la suite ne peut pas démarrer", size=10.6,
          bold=True, fill="#B42318", anchor="ls")
    c.txt(60, y + 39, "Un blocage n'est pas une erreur de l'application : "
          "c'est une donnée que DrillMaster refuse de deviner.", size=9.2,
          fill="#7A271A", anchor="ls")

    # ce que j'ai vu
    ly = 214
    c.panel(24, ly, 940, 320, "Ce que j'ai vu",
            "Les deux lignes du fichier, telles qu'elles sont écrites")
    rows = [(43, "ISBRC044", "512310,8", "731854,2", "219,1", ""),
            (45, "ISBRC045", "512340,2", "731880,4", "218,4", "doublon"),
            (46, "ISBRC046", "512368,9", "731907,7", "217,8", ""),
            (87, "ISBRC087", "512948,1", "732404,3", "206,2", ""),
            (88, "ISBRC088", "512340,2", "731880,4", "218,4", "doublon")]
    hy = ly + 72
    for hd, xx in (("Ligne", 44), ("Identifiant", 120), ("X", 380),
                   ("Y", 520), ("Z", 660), ("", 760)):
        c.txt(xx, hy, hd.upper(), size=8.4, fill=t.ink_3, bold=True, anchor="ls")
    c.l(40, hy + 10, 948, hy + 10, fill=t.border)
    ry = hy + 16
    for num, ident, X, Yv, Z, flag in rows:
        if flag:
            c.r(40, ry - 8, 908, 40, fill="#FFF4F2", rx=6)
            c.r(40, ry - 8, 3, 40, fill="#D92D20", rx=1)
        c.txt(44, ry + 12, str(num), size=9.6, fill=t.ink_3, anchor="ls")
        c.txt(120, ry + 12, ident, size=9.8, bold=bool(flag), anchor="ls")
        c.txt(380, ry + 12, X, size=9.8, fill=t.ink_2, anchor="ls")
        c.txt(520, ry + 12, Yv, size=9.8, fill=t.ink_2, anchor="ls")
        c.txt(660, ry + 12, Z, size=9.8, fill=t.ink_2, anchor="ls")
        if flag:
            c.chip(752, ry - 1, "doublon", "block")
        ry += 40
    c.txt(44, ly + 296, "Aucune autre ligne ne pose problème dans ce fichier "
          "(64 lignes lues, 2 signalées). Les deux lignes ont exactement les "
          "mêmes coordonnées.", size=9, fill=t.ink_3, anchor="ls")

    # pourquoi
    py = 530
    c.panel(24, py, 460, 416, "Pourquoi ça bloque", "En trois phrases")
    phrases = [
        ("1", "Un identifiant de forage est unique."),
        ("2", "Deux lignes avec le même identifiant et les mêmes coordonnées "
              "décrivent un seul forage."),
        ("3", "Tant que ce n'est pas tranché, la trajectoire de ce forage est "
              "ambiguë : la coupe afficherait un forage fusionné, faux dès "
              "la profondeur."),
    ]
    yy = py + 74
    for num, txt_ in phrases:
        c.c(46, yy + 8, 10, t.surface_3)
        c.txt(46, yy + 13, num, size=9, bold=True, anchor="ms")
        yy = sentence(c, 68, yy + 12, txt_, 396, 9.8, t.ink_2) + 18

    # ce que je ne fais pas
    c.r(46, py + 300, 416, 96, fill=t.surface_2, stroke=t.border, rx=8)
    c.txt(60, py + 320, "Ce que DrillMaster ne fera pas tout seul",
          size=9.6, bold=True, anchor="ls")
    inter = ["supprimer une des deux lignes", "inventer un identifiant",
             "choisir laquelle garder"]
    for k, txt_ in enumerate(inter):
        c.txt(60, py + 340 + k * 16, "— " + txt_, size=9, fill=t.ink_3,
              anchor="ls")

    # trois sorties
    dx, dw = 500, W - 500 - 24
    c.panel(dx, py, dw, 416, "Trois façons de régler, choisissez-en une")
    sorties = [
        ("Corriger dans le fichier", "Vous renommez ISBRC088 en ISBRC089.",
         "Les deux forages sont conservés. Rien d'autre ne change.",
         "Recommandé", "ok"),
        ("Fusionner les deux lignes", "Vous confirmez que c'est un seul "
         "forage.", "Les intervalles et teneurs des deux lignes sont "
         "réunis sous ISBRC045.", "Si c'est bien le cas", "quest"),
        ("Exclure un des deux forages", "Il reste dans le fichier mais "
         "n'entre pas dans le projet.",
         "Signalé dans la liste des exclusions, réversible à tout moment.",
         "Si vous n'êtes pas sûr", "info"),
    ]
    yy = py + 72
    for i, (titre, quoi, apres, quand, kind) in enumerate(sorties):
        hgt = 96
        c.r(dx + 16, yy, dw - 32, hgt, fill=t.surface_2, stroke=t.border, rx=9)
        c.dot(dx + 34, yy + 20, kind)
        c.txt(dx + 48, yy + 15, titre, size=10.6, bold=True, anchor="ls")
        c.txt(dx + dw - 32, yy + 15, quand, size=8.4, fill=t.ink_3,
              anchor="rs")
        sentence(c, dx + 48, yy + 36, quoi, dw - 110, 9.2, t.ink_2)
        c.txt(dx + 48, yy + 62, "Après : " + apres, size=8.8, fill=t.ink_3,
              anchor="ls")
        c.button(dx + dw - 32 - 96, yy + 56, "Choisir", w=96, size=9.2,
                 primary=(i == 0))
        yy += hgt + 10

    c.status_bar("Rien n'est enregistré tant que vous n'avez pas choisi · "
                 "vos fichiers restent intacts", "En attente de vous", t.block)
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 5 · LES 5 ÉTATS, EN DEUX VOIX
# ══════════════════════════════════════════════════════════════════════
ETATS = [
    # clé, nom, « ce qu'il veut dire », guidé, expert, la suite, ce qui continue
    ("info", "Information", "Un fait, rien à décider",
     "« 64 forages lus, 2 410 intervalles de lithologie. »",
     "Bandeau en bas d'écran. Jamais de fenêtre qui s'ouvre.",
     "Poursuit seul", "Rien à faire", "#667085"),
    ("warn", "Avertissement", "Ça marche, mais il manque quelque chose",
     "« 3 forages sans déviation : supposés verticaux. »",
     "Ligne ambrée dans la liste, avec le nombre de forages concernés.",
     "Poursuit", "Vérifier, ou accepter tel quel", "#F79009"),
    ("quest", "Question", "DrillMaster ne peut pas décider à votre place",
     "« Cette cellule contient deux codes (LAT;SAP). On garde lequel ? »",
     "Une seule question à la fois, avec les deux réponses possibles.",
     "Met la ligne en attente", "Répondre", "#7F56D9"),
    ("block", "Blocage", "Rien ne peut continuer sur cette donnée",
     "« 2 forages portent le même nom. »",
     "Fiche de détail : ce que j'ai vu, pourquoi, trois sorties.",
     "Arrête l'étape suivante", "Trancher", "#D92D20"),
    ("tech", "Erreur technique", "DrillMaster lui-même a échoué",
     "« DEM illisible : droit de lecture refusé. »",
     "Message court, avec « Copier le détail » pour le support.",
     "Arrête l'action en cours", "Signaler", "#B54708"),
]


def etats(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Données", dark_btn=dark)
    c.page_title(24, 82, "Les 5 états",
                 "Un état dit toujours : ce qui se passe, ce que vous pouvez "
                 "faire, et si la suite continue")

    y = 132
    c.r(24, y, W - 48, 56, fill=t.surface, stroke=t.border, rx=9)
    c.txt(44, y + 22, "Une couleur ne veut dire qu'une chose.", size=10.4,
          bold=True, anchor="ls")
    c.txt(44, y + 40, "L'accent bleu de DrillMaster n'exprime jamais un état. "
          "Le vocabulaire est le même au mode Guidé et au mode Expert — seule "
          "la longueur des phrases change.", size=9, fill=t.ink_3, anchor="ls")

    ty = 208
    c.panel(24, ty, W - 48, 590, None)
    hy = ty + 34
    cols = (("", 44, 0), ("État", 92, 190), ("Ce qu'il veut dire", 316, 290),
            ("Voix Guidée", 630, 350), ("Voix Experte", 1010, 330),
            ("La suite", 1360, 190))
    for hd, xx, _w in cols:
        c.txt(xx, hy, hd.upper(), size=8.4, fill=t.ink_3, bold=True, anchor="ls")
    c.l(40, hy + 10, W - 40, hy + 10, fill=t.border)

    ry = hy + 26
    for kind, nom, sens, guide, expert, suite, quoi, col in ETATS:
        c.l(40, ry + 100, W - 40, ry + 100, fill=t.border)
        c.c(52, ry + 16, 6, col)
        c.txt(70, ry + 10, nom, size=10.4, bold=True, anchor="ls")
        sentence(c, 92, ry + 30, sens, 190, 9, t.ink_3, 12)
        sentence(c, 316, ry + 10, guide, 286, 9.2, t.ink_2)
        sentence(c, 630, ry + 10, expert, 346, 9.2, t.ink_2)
        sentence(c, 1010, ry + 10, quoi, 322, 9.2, t.ink_2)
        wch = c.tw(suite, 8.6, True) + 20
        c.r(1360, ry + 8, wch, 20, fill=col + "14", rx=5)
        c.txt(1360 + wch / 2, ry + 22, suite, size=8.6, fill=col, bold=True,
              anchor="ms")
        sentence(c, 1360, ry + 38, {"Poursuit seul": "la suite démarre",
                                    "Poursuit": "la suite démarre",
                                    "Met la ligne en attente": "le reste avance",
                                    "Arrête l'étape suivante": "l'étape suivante attend",
                                    "Arrête l'action en cours": "seule l'action s'arrête"}[suite],
                 190, 8.4, t.ink_3, 12)
        ry += 100

    # ce que ça change pour l'utilisateur
    ly = 828
    c.r(24, ly, 760, 116, fill=t.surface, stroke=t.border, rx=9)
    c.txt(44, ly + 24, "Ce que ça supprime", size=10.4, bold=True, anchor="ls")
    for k, txt_ in enumerate([
            "31 fenêtres modales qui interrompaient le travail",
            "des messages sans la ligne concernée",
            "des avertissements confondus avec des erreurs"]):
        c.dot(48, ly + 52 + k * 20, "ok")
        c.txt(62, ly + 47 + k * 20, txt_, size=9.2, fill=t.ink_2, anchor="ls")

    c.r(800, ly, W - 824, 116, fill=t.surface, stroke=t.border, rx=9)
    c.txt(820, ly + 24, "Ce que ça garantit", size=10.4, bold=True, anchor="ls")
    for k, txt_ in enumerate([
            "aucun blocage ne disparaît sans une décision de votre part",
            "chaque message dit où : fichier, ligne, forage",
            "le même mot veut dire la même chose partout"]):
        c.dot(824, ly + 52 + k * 20, "ok")
        c.txt(838, ly + 47 + k * 20, txt_, size=9.2, fill=t.ink_2, anchor="ls")

    c.status_bar("5 états · 2 voix · 1 vocabulaire", "Stable")
    return c.save(path)


SCREENS_V3 = {
    "11_pistes": pistes,
    "12_partages": partages,
    "13_donnees_rangs": donnees_rangs,
    "14_message": message,
    "15_etats": etats,
}


if __name__ == "__main__":
    import os
    out = os.path.dirname(os.path.abspath(__file__))
    for name, fn in SCREENS_V3.items():
        print("écrit", fn(os.path.join(out, f"{name}.png")))


# ══════════════════════════════════════════════════════════════════════
# 6 · VALIDATION — la preuve que ça tient dans plusieurs cas
# ══════════════════════════════════════════════════════════════════════
CAS = [
    # cas, ce qu'il vérifie, résultat, détail
    ("Projet vide", "aucun fichier : que voit-on ?", "ok",
     "une page, 3 phrases, un bouton"),
    ("Projet complet", "16 sources : tout doit rester lisible", "ok",
     "0 régression · 42 s de calcul"),
    ("4 types manquants", "RQD, récup., densité, imagerie absents", "ok",
     "3 pistes annoncées vides, jamais muettes"),
    ("2 forages dupliqués", "le blocage du cas réel", "ok",
     "fiche + 3 sorties, aucune décision auto"),
    ("CSV en point-virgule", "séparateur différent", "ok",
     "reconnu, 64 lignes lues"),
    ("Décimale à virgule", "« 512 340,2 » au lieu de « 512340.2 »", "ok",
     "converti, l'original n'est pas touché"),
    ("Encodage latin-1", "accents cassés (AltÃ©ration)", "ok",
     "réparé + signalé"),
    ("Forages inclinés", "déviation forte, dip variable", "ok",
     "2 410 segments, 0 point hors coupe"),
    ("Forage horizontal", "cas limite à 90°", "ok",
     "trajectoire tracée, piste tournée"),
    ("Pendage positif", "convention inversée (-90 / +90)", "warn",
     "avertissement, pas de correction"),
    ("MNT dans un autre CRS", "EPSG:4326 vs projet 32629", "ok",
     "reprojeté à la volée, notifié"),
    ("MNT absent", "coupe sans topographie", "ok",
     "ligne de sol linéaire + mention"),
    ("500 forages", "performance et lisibilité", "ok",
     "1,9 s · 12 000 intervalles"),
    ("Export A1 à 300 dpi", "ce que la coupe contient", "ok",
     "9 933 × 7 016 px, 42 s"),
    ("Mode sombre", "toutes les vues", "ok",
     "aucune couleur métier modifiée"),
    ("Zoom 400 %", "texte et traits", "ok",
     "pas de flou, pas de chevauchement"),
    ("Contraste 4,5:1", "lisibilité y compris daltonisme", "ok",
     "5 états distingués sans couleur"),
]


def validation(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Données", dark_btn=dark)
    c.page_title(24, 82, "Est-ce que ça tient ?",
                 "17 cas réels rejoués à chaque modification · projet de "
                 "référence figé « Issia »")

    # bandeau de synthèse
    y = 132
    c.r(24, y, 500, 92, fill="#EEF9F2", stroke="#C7EFDA", rx=9)
    c.txt(44, y + 28, "17 cas sur 17 passent", size=15, bold=True,
          fill="#05603A", anchor="ls")
    c.txt(44, y + 50, "dernier passage il y a 4 min · après la modification "
          "« talles des pistes »", size=9, fill="#067647", anchor="ls")
    c.txt(44, y + 68, "aucun cas ignoré, aucun cas « à vérifier plus tard »",
          size=9, fill="#067647", anchor="ls")

    c.r(540, y, 500, 92, fill=t.surface, stroke=t.border, rx=9)
    c.txt(560, y + 26, "3 cas passent, mais avec une marge mince", size=10.4,
          bold=True, anchor="ls")
    c.txt(560, y + 46, "forage au-delà de 92° · 3 000 forages dans une coupe "
          "· MNT 5 m sur 20 km", size=8.6, fill=t.ink_3, anchor="ls")
    c.txt(560, y + 66, "à surveiller au prochain passage", size=8.6,
          fill=t.warn, bold=True, anchor="ls")

    c.r(1056, y, W - 1080, 92, fill=t.surface, stroke=t.border, rx=9)
    c.txt(1076, y + 28, "Ce qui n'est pas encore testé", size=10.6,
          bold=True, anchor="ls")
    for i, txt_ in enumerate(["QGIS 3.34 et 3.40 sur macOS",
                              "écran 4K à 200 % de mise à l'échelle"]):
        c.dot(1080, y + 52 + i * 20, "info")
        c.txt(1094, y + 47 + i * 20, txt_, size=9, fill=t.ink_2, anchor="ls")

    # table des cas
    ty = 244
    c.panel(24, ty, W - 48, 664, "Les 17 cas",
            "Un cas = une situation d'usage, pas un test technique")
    cols = (("Cas", 44), ("Ce qu'il vérifie", 300), ("Résultat", 700),
            ("Ce qui se passe", 860))
    for hd, xx in cols:
        c.txt(xx, ty + 78, hd.upper(), size=8.4, fill=t.ink_3, bold=True,
              anchor="ls")
    c.l(40, ty + 88, W - 40, ty + 88, fill=t.border)

    ry = ty + 104
    for i, (cas, verif, res, detail) in enumerate(CAS):
        if i % 2 == 1:
            c.r(32, ry - 8, W - 64, 32, fill=t.surface_2, rx=5)
        c.txt(44, ry + 12, cas, size=9.8, fill=t.ink, bold=True, anchor="ls")
        c.txt(300, ry + 12, verif, size=9.4, fill=t.ink_2, anchor="ls")
        good = res == "ok"
        c.r(700, ry + 2, 74, 20, fill=("#EEF9F2" if good else "#FFFAEB"),
            rx=5)
        c.txt(737, ry + 16, "passe" if good else "passable", size=8.6,
              fill=("#067647" if good else "#B54708"), bold=True, anchor="ms")
        c.txt(860, ry + 12, detail, size=9.2, fill=t.ink_3, anchor="ls")
        ry += 32

    c.button(W - 24 - 180, ty + 578, "Rejouer maintenant", w=180, size=9.6)
    c.txt(W - 24 - 200, ty + 624, "38 s sur 64 forages · archivé avec "
          "chaque version", size=8.6, fill=t.ink_3, anchor="rs")

    c.status_bar("17 cas · 17 passent · 3 marges minces · "
                 "2 environnements non testés", "Passé", t.ok)
    return c.save(path)


SCREENS_V3["16_validation"] = validation
