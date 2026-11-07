"""Planche : où vivent les options, et où elles devraient vivre.

    python3 maquettes/24_options.py
"""
from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
THEME = json.load(open(os.path.join(OUT, "..", "specs", "data", "theme.json"),
                       encoding="utf-8"))
T = THEME["clair"]
S = 2
W, H = 1600, 900
POL = {False: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
       True: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}


def f(t, g=False):
    return ImageFont.truetype(POL[g], int(t * S))


img = Image.new("RGB", (W * S, H * S), T["bg"])
d = ImageDraw.Draw(img)


def txt(x, y, t, sz=10, col=None, g=False, a=None):
    d.text((x * S, y * S), t, font=f(sz, g), fill=col or T["ink"], anchor=a)


def rect(x, y, w, h, fill=None, stroke=None, r=8, ep=1, dash=None):
    if dash:
        d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                            radius=int(r * S), outline=stroke,
                            width=max(1, int(ep * S)))
        return
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                        radius=int(r * S), fill=fill, outline=stroke,
                        width=max(1, int(ep * S)))


txt(40, 30, "Où vivent vos options", 22, T["ink"], True)
txt(40, 62, "Mesuré sur le plugin actuel : 8 réglages enfermés dans une "
    "fenêtre, 2 barres d'onglets masquées, 43 % d'infobulles.",
    10.2, T["ink_2"])

# ══ AUJOURD'HUI
y = 116
txt(40, y, "Aujourd'hui", 13, T["ink"], True)
txt(40, y + 20, "Une partie des réglages n'existe que le temps d'une fenêtre.",
    9.6, T["ink_2"])
y += 46

# écran principal
rect(40, y, 620, 330, T["surface"], T["border"], 10)
txt(60, y + 16, "Coupe 2D", 12, T["ink"], True)
zones = [("Pistes", "largeur · opacité · côté", 96),
         ("Inclusion", "tolérance · forages", 60)]
yy = y + 48
for nom, detail, h in zones:
    rect(60, yy, 580, h, T["surface_2"], T["border"], 6)
    txt(74, yy + 10, nom, 9.4, T["ink"], True)
    txt(74, yy + 28, detail, 8.6, T["ink_3"])
    yy += h + 10
rect(60, yy, 580, 40, T["surface_2"], T["border_strong"], 6, dash=True)
txt(74, yy + 12, "« Référentiel… »  ouvre une fenêtre", 9.2, T["ink_2"])
txt(74, yy + 26, "8 réglages enfermés — refermée, ils disparaissent", 8.4,
    T["block"])

# la fenêtre par-dessus
rect(300, y + 96, 340, 216, T["surface"], T["block"], 10, 1.6)
txt(316, y + 112, "Référentiel", 11, T["ink"], True)
txt(624, y + 112, "✕", 10, T["ink_3"], a="ra")
for i, (lab, val) in enumerate([("Couleur lithologie", "profil A"),
                                ("Motif", "hachures"),
                                ("Épaisseur trait", "1,2 px"),
                                ("Étiquettes", "à droite"),
                                ("Palette teneur", "5 classes"),
                                ("Seuils", "0,1 / 1 / 5"),
                                ("Ordre des pistes", "par famille"),
                                ("Sens de lecture", "haut → bas")]):
    yy = y + 134 + i * 18
    txt(316, yy, lab, 8.4, T["ink_2"])
    txt(624, yy, val, 8.8, T["ink"], True, a="ra")
txt(316, y + 330, "Fenêtre modale : on ne peut rien régler en la voyant",
    8.4, T["ink_3"])

# ══ DEMAIN
x2 = 740
txt(x2, 116, "Demain", 13, T["ink"], True)
txt(x2, 136, "Les mêmes réglages, visibles en permanence, rangés en deux "
    "niveaux.", 9.6, T["ink_2"])
yy = 182
rect(x2, yy, 820, 330, T["surface"], T["border"], 10)
txt(x2 + 20, yy + 16, "Pistes", 12, T["ink"], True)
txt(x2 + 800, yy + 16, "6 réglages visibles", 8.8, T["ink_3"], a="ra")
# un groupe ouvert : teneurs
rect(x2 + 16, yy + 44, 500, 120, T["surface_2"], T["border"], 6)
txt(x2 + 30, yy + 56, "Teneurs", 9.8, T["ink"], True)
txt(x2 + 500, yy + 56, "actif", 8.4, T["ok"], True, a="ra")
for i, (lab, val) in enumerate([("Largeur", "15 px"), ("Opacité", "90 %"),
                                ("Côté", "Droite")]):
    txt(x2 + 46, yy + 80 + i * 20, lab, 8.8, T["ink_2"])
    txt(x2 + 240, yy + 80 + i * 20, val, 8.8, T["ink"], True)
rect(x2 + 532, yy + 44, 268, 120, T["surface_2"], T["border"], 6)
txt(x2 + 546, yy + 56, "Lithologie", 9.8, T["ink"], True)
txt(x2 + 786, yy + 56, "actif", 8.4, T["ok"], True, a="ra")
for i, (lab, val) in enumerate([("Largeur", "18 px"), ("Côté", "Gauche"),
                                ("Motif", "hachures")]):
    txt(x2 + 562, yy + 80 + i * 20, lab, 8.8, T["ink_2"])
    txt(x2 + 720, yy + 80 + i * 20, val, 8.8, T["ink"], True)

# repli avancés
rect(x2 + 16, yy + 174, 780, 30, T["surface_3"], None, 6)
txt(x2 + 30, yy + 182, "▸  Réglages avancés (12)", 9.2, T["ink"], True)
txt(x2 + 790, yy + 182, "se souvient d'un coup", 8.4, T["ink_3"], a="ra")
rect(x2 + 16, yy + 214, 780, 46, T["surface_2"], T["border"], 6)
txt(x2 + 30, yy + 226, "Aucune fenêtre, aucun onglet caché, "
    "aucun réglage hors de portée.", 9.2, T["ink"])
txt(x2 + 30, yy + 242, "Ce que vous voyez ici est tout ce qui existe : "
    "rien n'apparaît ailleurs.", 8.6, T["ink_3"])

# trois principes
yy += 350
principes = [("Aucun réglage dans une fenêtre", "la fenêtre choisit un "
              "fichier, rien d'autre"),
             ("Un repli, pas par option", "6 visibles, le reste derrière un "
              "seul bouton qui garde son état"),
             ("Deux catégories nommées", "préférences de poste (thème, "
              "langue) · réglages de projet (pistes, seuils)")]
for i, (titre, sous) in enumerate(principes):
    x = 40 + i * 520
    rect(x, yy, 490, 78, T["surface"], T["border"], 8)
    d.ellipse([(x + 16) * S, (yy + 20) * S, (x + 28) * S, (yy + 32) * S],
              fill=T["accent"])
    txt(x + 40, yy + 16, titre, 9.8, T["ink"], True)
    txt(x + 40, yy + 36, sous, 8.6, T["ink_2"])
    txt(x + 40, yy + 54, "vérifié par l'agent N-01" if i == 0 else
        ("N-07" if i == 1 else "N-04"), 8, T["ink_3"])

# ══ ONGLETS
yy = 660
txt(40, yy, "Onglets : assumés, ou supprimés", 13, T["ink"], True)
txt(40, yy + 20, "Deux barres d'onglets sont masquées par le code : un seul "
    "panneau est atteignable.", 9.6, T["ink_2"])
yy += 46
for i, (etat, desc, col, texte) in enumerate([
        ("Aujourd'hui", "une barre masquée, un panneau visible", T["block"],
         "si un second onglet est ajouté, il sera invisible"),
        ("Demain", "des onglets nommés et visibles", T["ok"],
         "modules en haut : Données · Coupe · 3D · Analyses · Export")]):
    x = 40 + i * 780
    rect(x, yy, 760, 92, T["surface"], T["border"], 8)
    txt(x + 16, yy + 14, etat, 9.6, col, True)
    txt(x + 16, yy + 34, desc, 9.2, T["ink"])
    txt(x + 16, yy + 52, texte, 8.6, T["ink_3"])
    if i == 0:
        r = 0
        for j, nom in enumerate(["Données"]):
            rect(x + 16, yy + 66, 90, 18, T["surface_3"], T["border"], 4)
            txt(x + 61, yy + 68, nom, 8, T["ink_2"], a="ma")
        txt(x + 120, yy + 68, "+ 4 onglets présents mais sans barre", 8,
            T["block"])
    else:
        for j, nom in enumerate(["Données", "Coupe", "3D", "Analyses",
                                 "Export"]):
            rect(x + 16 + j * 96, yy + 66, 88, 18,
                 T["accent_soft"] if j == 1 else T["surface_3"],
                 T["accent_line"] if j == 1 else T["border"], 4)
            txt(x + 60 + j * 96, yy + 68, nom, 8,
                T["ink"] if j == 1 else T["ink_2"], a="ma")

d.line([(40 * S, 862 * S), (1560 * S, 862 * S)], fill=T["border"], width=S)
txt(40, 872, "Planche générée depuis le thème du projet · constats mesurés par "
    "le département Navigation (agents N-01 à N-08)", 8.8, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "24_options.png"))
print("écrit maquettes/24_options.png")
