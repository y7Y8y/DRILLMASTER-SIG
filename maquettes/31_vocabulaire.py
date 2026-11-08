"""Planche 31 — un mot par chose.

    python3 maquettes/31_vocabulaire.py

Les couples viennent de `specs/data/vocabulaire.json`, produit par
`tools/audit_vocabulaire.py` sur les **textes réellement affichés**.
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(OUT)
sys.path.insert(0, RACINE)
DONNEES = os.path.join(RACINE, "specs", "data")
THEME = json.load(open(os.path.join(DONNEES, "theme.json"), encoding="utf-8"))
AUDIT = json.load(open(os.path.join(DONNEES, "vocabulaire.json"),
                       encoding="utf-8"))
from drillmaster_v3.core.vocabulaire import MOTS, VARIANTES, remplace  # noqa

T = THEME["clair"]
S = 2
W, H = 1600, 620
POL = {False: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
       True: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}


def f(t, g=False):
    return ImageFont.truetype(POL[g], int(t * S))


img = Image.new("RGB", (W * S, H * S), T["bg"])
d = ImageDraw.Draw(img)


def txt(x, y, t, sz=10, col=None, g=False, a=None):
    d.text((x * S, y * S), t, font=f(sz, g), fill=col or T["ink"], anchor=a)


def rect(x, y, w, h, fill=None, stroke=None, r=8, ep=1):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                        radius=int(r * S), fill=fill, outline=stroke,
                        width=max(1, int(ep * S)))


def ligne(x1, y1, x2, y2, col=None, ep=1):
    d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=col or T["border"],
           width=int(ep * S))


txt(40, 28, "Un mot par chose", 22, T["ink"], True)
txt(40, 60, f"{AUDIT['textes_affiches']} textes affichés analysés. Une chose "
    "se nomme d'une seule façon ; ce qui reste mélangé est mesuré, "
    "pas contourné.", 10.2, T["ink_2"])

# ══ 1 · les mots retenus
y = 108
txt(40, y, "1 · Le mot retenu", 13, T["ink"], True)
txt(40, y + 22, "Le critère : le mot que le géologue emploie quand il parle "
    "à un confrère.", 9.4, T["ink_2"])
y += 52
x = 40
for k, (cle, formes) in enumerate(MOTS.items()):
    if k % 4 == 0 and k:
        y += 52
        x = 40
    rect(x, y, 178, 44, T["surface"], T["border"], 9)
    txt(x + 12, y + 7, formes["label"], 9.4, T["ink"], True)
    txt(x + 12, y + 25, formes["pluriel"], 8.2, T["ink_3"])
    x += 186

# ══ 2 · les variantes corrigées, avec avant / après
y += 74
txt(40, y, "2 · Ce que le code disait, ce qu'il dit maintenant", 13,
    T["ink"], True)
y += 28
exemples = [("Afficher azimut / dip", "Afficher azimut / pendage"),
            ("Largeur de voie", "Largeur de piste"),
            ("lecture terminée en utf-8-sig", "lecture terminée"),
            ("Le fichier n'était pas en UTF-8",
             "Les accents du fichier étaient abîmés"),
            ("EPSG:32629 — UTM 29N", "UTM 29N (mètres)")]
txt(40, y, "avant", 8.4, T["ink_3"], True)
txt(430, y, "après", 8.4, T["ink_3"], True)
y += 18
for avant, apres in exemples:
    txt(40, y, avant, 9, T["block"])
    txt(414, y, "→", 9, T["ink_3"])
    txt(434, y + 1, apres, 9, T["ok"], True)
    ligne(40, y + 16, 800, y + 16, T["surface_3"])
    y += 26

# mots qui gardent leur sens : la nuance qui évite une bêtise
y += 6
rect(40, y, 760, 104, T["surface_2"], T["border"], 10)
txt(58, y + 12, "Quatre mots ressemblent à des doublons et n'en sont pas",
    9.6, T["ink"], True)
for k, (mot_, raison) in enumerate([
        ("profil", "« profil d'affichage » : un réglage, pas une coupe"),
        ("trou", "« trou de forage » : le trou, pas le forage entier"),
        ("analyse", "les valeurs mesurées, pas la piste des teneurs"),
        ("section", "un nom de classe ; s'il s'affiche, c'est un défaut")]):
    txt(58, y + 32 + k * 16, f"· {mot_:10} {raison}", 8.4, T["ink_2"])

# ══ 3 · les couples restants
D = 840
y = 108
txt(D, y, "3 · Ce qui se dit encore de deux façons", 13, T["ink"], True)
txt(D, y + 22, "Compté dans les textes affichés. Le bruit (autre sens) est "
    "compté à part.", 9.2, T["ink_2"])
y += 52
calculs = AUDIT["couples"]
maxi = max(max(formes.values()) for formes in calculs.values())
for chef, formes in list(calculs.items())[:6]:
    txt(D, y, chef, 9.4, T["ink"], True)
    txt(D + 96, y, f"{len(formes)} façons", 8.2, T["ink_3"])
    yy = y + 16
    for rang, (mot_, n) in enumerate(sorted(formes.items(),
                                            key=lambda kv: -kv[1])):
        col = T["accent"] if rang == 0 else T["block"]
        txt(D + 8, yy + 1, mot_, 8.4, T["ink"] if rang == 0 else T["ink_2"])
        rect(D + 96, yy + 2, max(4, n / maxi * 300), 9,
             T["accent_soft"] if rang == 0 else T["surface_3"],
             T["accent_line"] if rang == 0 else None, 4)
        txt(D + 96 + max(4, n / maxi * 300) + 8, yy + 1, str(n), 8,
            col, rang == 0)
        yy += 17
    y = yy + 10

# ══ 4 · le lexique est lu
y += 6
rect(D, y, 720, 120, T["accent_soft"], T["accent_line"], 10)
txt(D + 18, y + 12, "R-61 · un lexique que personne ne lit n'existe pas",
    10.2, T["ink"], True)
txt(D + 18, y + 34, "Avant : 0 fichier du plugin lisait le lexique. "
    "Maintenant : le plugin embarque", 8.8, T["ink_2"])
txt(D + 18, y + 50, "une copie du lexique et un outil refuse la dérive "
    "(comme pour la palette).", 8.8, T["ink_2"])
txt(D + 18, y + 74, "R-60 · un mot par chose  ·  R-17 · aucun mot du code "
    "à l'écran", 8.8, T["ink"], True)
txt(D + 18, y + 94, "Le garde-fou compare des mots ENTIERS : trois lettres "
    "au milieu d'un mot", 8.2, T["ink_3"])
txt(D + 18, y + 106, "ne déclenchent plus un refus à tort.", 8.2, T["ink_3"])

# ── pied
ligne(40, H - 44, 1560, H - 44)
txt(40, H - 34, "Couples et chiffres produits par tools/audit_vocabulaire.py "
    "· relancé à chaque passage.", 8.6, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "31_vocabulaire.png"))
print("écrit maquettes/31_vocabulaire.png")
