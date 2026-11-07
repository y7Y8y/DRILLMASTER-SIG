"""Planche de charte — la direction artistique en une image.

    python3 maquettes/23_charte.py

Couleur, typographie, espace, boutons, états : tout est lu dans
specs/data/theme.json (la source unique), jamais réécrit ici.
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(OUT))
DONNEES = os.path.join(OUT, "..", "specs", "data")
THEME = json.load(open(os.path.join(DONNEES, "theme.json"), encoding="utf-8"))
REF = json.load(open(os.path.join(DONNEES, "referentiel.json"), encoding="utf-8"))
CLAIR, SOMBRE = THEME["clair"], THEME["sombre"]
TYPO = THEME["typographie"]
S = 2
W, H = 1600, 1360

POLICE = {False: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
          True: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}


def f(taille, gras=False):
    return ImageFont.truetype(POLICE[gras], int(taille * S))


img = Image.new("RGB", (W * S, H * S), CLAIR["bg"])
d = ImageDraw.Draw(img)


def txt(x, y, t, taille=10, col=None, gras=False, ancre=None):
    d.text((x * S, y * S), t, font=f(taille, gras), fill=col or CLAIR["ink"],
           anchor=ancre)


def rect(x, y, w, h, rempli=None, bord=None, r=8, ep=1):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                        radius=int(r * S), fill=rempli, outline=bord,
                        width=max(1, int(ep * S)))


def trait(x1, y1, x2, y2, col=None):
    d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=col or CLAIR["border"],
           width=S)


# ── en-tête
txt(40, 30, "DrillMaster — charte visuelle", 22, CLAIR["ink"], True)
txt(40, 62, "Un seul jeu de décisions. Ce qui n'est pas ici n'existe pas à l'écran.",
    10.5, CLAIR["ink_2"])

GAUCHE, DROITE = 40, 820
y = 108

# ══ 1 · COULEUR
txt(GAUCHE, y, "1 · Couleur", 13, CLAIR["ink"], True)
txt(GAUCHE, y + 20, "Le chrome travaille en valeur. La couleur est réservée "
    "aux données et aux états.", 9.6, CLAIR["ink_2"])
y += 46
chrome = [("fond", "bg"), ("surface", "surface"), ("surface 2", "surface_2"),
          ("bord", "border"), ("bord fort", "border_strong"),
          ("texte", "ink"), ("texte 2", "ink_2"), ("texte 3", "ink_3")]
for i, (nom, cle) in enumerate(chrome):
    x = GAUCHE + i * 80
    rect(x, y, 68, 44, CLAIR[cle], CLAIR["border"], 8)
    txt(x, y + 50, nom, 8.4, CLAIR["ink_3"])
    txt(x, y + 61, CLAIR[cle], 8, CLAIR["ink_3"])

txt(GAUCHE + 676, y + 2, "Réservé à l'action", 8.8, CLAIR["ink_2"], True)
rect(GAUCHE + 676, y + 14, 68, 30, CLAIR["accent"], None, 7)
txt(GAUCHE + 676, y + 50, "accent — un seul", 8.4, CLAIR["ink_3"])

y += 82
txt(GAUCHE, y, "Les 5 états — jamais l'accent, toujours la même couleur", 9.4,
    CLAIR["ink_2"], True)
y += 14
etats = [("Information", "info"), ("Avertissement", "warn"),
         ("Question", "quest"), ("Blocage", "block"), ("Erreur techn.", "tech")]
for i, (nom, cle) in enumerate(etats):
    x = GAUCHE + i * 148
    rect(x, y, 138, 34, CLAIR["surface"], CLAIR["border"], 8)
    d.ellipse([(x + 10) * S, (y + 13) * S, (x + 20) * S, (y + 23) * S],
              fill=CLAIR[cle])
    txt(x + 27, y + 12, nom, 9, CLAIR["ink"], True)

y += 48
txt(GAUCHE, y, "Les données ont leurs propres couleurs — et seulement elles :",
    9.4, CLAIR["ink_2"])
y += 14
litho = list(REF["lithologie"].items())[:7]
for i, (code, col) in enumerate(litho):
    x = GAUCHE + i * 70
    rect(x, y, 60, 20, col, None, 5)
    txt(x + 7, y + 3, code, 8.2, CLAIR["ink"], True)
txt(GAUCHE + 500, y + 2, "Teneur", 8.4, CLAIR["ink_2"], True)
teneurs = REF["teneur"]
for i, col in enumerate(teneurs):
    rect(GAUCHE + 556 + i * 30, y, 28, 20, col, None, 4)

# ══ 2 · TYPOGRAPHIE
y += 52
txt(GAUCHE, y, "2 · Typographie", 13, CLAIR["ink"], True)
txt(GAUCHE, y + 20, "Six tailles, pas une de plus. Une seule famille.",
    9.6, CLAIR["ink_2"])
y += 44
echelle = [("Titre d'écran", TYPO["titre"], True, "« Pistes » — une fois par écran"),
           ("Chiffre", TYPO["chiffre"], True, "« 3 180 » — la donnée qui compte"),
           ("Titre de bloc", TYPO["section"], True, "« Teneurs » — un par panneau"),
           ("Corps", TYPO["corps"], False, "le texte courant, jamais en dessous"),
           ("Secondaire", TYPO["secondaire"], False, "légendes, unités, aides"),
           ("Micro", TYPO["micro"], False, "étiquettes de colonne, en majuscules")]
for nom, taille, gras, exemple in echelle:
    txt(GAUCHE, y + 4, nom, 8.8, CLAIR["ink_3"])
    txt(GAUCHE + 130, y, exemple, taille, CLAIR["ink"], gras)
    txt(DROITE - 60, y + 4, f"{taille} pt", 8.8, CLAIR["ink_3"], ancre="ra")
    y += 34

# ══ 3 · ESPACE
y += 14
txt(GAUCHE, y, "3 · Espace", 13, CLAIR["ink"], True)
txt(GAUCHE, y + 20, "Une grille de 4 px : 4 · 8 · 12 · 16 · 24 · 32. "
    "Rien d'autre, jamais 14 ou 18.", 9.6, CLAIR["ink_2"])
y += 44
for i, v in enumerate([4, 8, 12, 16, 24, 32]):
    x = GAUCHE + i * 62
    rect(x, y, max(v, 6), 18, CLAIR["accent_soft"], CLAIR["accent_line"], 3)
    txt(x, y + 24, f"{v}", 8.4, CLAIR["ink_3"])
y += 46
txt(GAUCHE, y, "Un bloc = un titre, une phrase qui dit à quoi il sert, puis "
    "ses champs.", 9.2, CLAIR["ink_2"])

# ══ 4 · BOUTONS
y += 34
txt(GAUCHE, y, "4 · Boutons", 13, CLAIR["ink"], True)
txt(GAUCHE, y + 20, "Trois rôles. Un seul primaire par écran — "
    "s'il y en a deux, c'est un défaut.", 9.6, CLAIR["ink_2"])
y += 46
rect(GAUCHE, y, 130, 30, CLAIR["accent"], None, 7)
txt(GAUCHE + 65, y + 8, "Importer", 9.8, "#FFFFFF", True, "ma")
txt(GAUCHE, y + 36, "primaire", 8.2, CLAIR["ink_3"])
rect(GAUCHE + 180, y, 120, 30, CLAIR["surface"], CLAIR["border_strong"], 7)
txt(GAUCHE + 240, y + 8, "Comparer", 9.8, CLAIR["ink"], True, "ma")
txt(GAUCHE + 180, y + 36, "secondaire", 8.2, CLAIR["ink_3"])
txt(GAUCHE + 340, y + 8, "Plus tard", 9.8, CLAIR["ink_2"])
txt(GAUCHE + 340, y + 36, "discret", 8.2, CLAIR["ink_3"])
rect(GAUCHE + 480, y, 140, 30, CLAIR["surface_3"], None, 7)
txt(GAUCHE + 550, y + 8, "Indisponible", 9.8, CLAIR["ink_3"], True, "ma")
txt(GAUCHE + 480, y + 36, "désactivé + raison", 8.2, CLAIR["ink_3"])

# ══ colonne de droite
y = 108
txt(DROITE, y, "5 · Message", 13, CLAIR["ink"], True)
txt(DROITE, y + 20, "Un bandeau, pas une fenêtre. Cinq champs, dans cet ordre.",
    9.6, CLAIR["ink_2"])
y += 44
rect(DROITE, y, 740, 70, CLAIR["surface"], CLAIR["block"], 10, 1.4)
d.ellipse([(DROITE + 14) * S, (y + 14) * S, (DROITE + 26) * S, (y + 26) * S],
          fill=CLAIR["block"])
txt(DROITE + 36, y + 10, "ISBRC045 existe deux fois", 10.2, CLAIR["ink"], True)
txt(DROITE + 36, y + 28, "Sa trajectoire serait fausse de 2 mètres. Rien n'a "
    "été supprimé.", 8.8, CLAIR["ink_2"])
txt(DROITE + 36, y + 42, "Lignes 46 et 47  ·  trois sorties possibles", 8.8,
    CLAIR["ink_2"])
txt(DROITE + 36, y + 56, "Données › Colliers", 8.2, CLAIR["ink_3"])

# ══ 6 · INTERDITS
y += 96
txt(DROITE, y, "6 · Ce qui est interdit", 13, CLAIR["ink"], True)
txt(DROITE, y + 20, "Chaque interdiction vient d'un défaut mesuré dans le "
    "plugin actuel (rapport 09).", 9.6, CLAIR["ink_2"])
y += 44
interdits = [
    ("Une couleur écrite en dur", "655 couleurs littérales, 40 fichiers"),
    ("Une taille de police inventée", "9 tailles cohabitent"),
    ("Deux propriétaires pour un réglage", "la largeur se règle dans 5 fichiers"),
    ("Un groupe de champs sans titre", "on ne sait pas ce qu'il rassemble"),
    ("Une fenêtre d'alerte pour informer", "29 modales bloquent le geste"),
    ("Un terme technique à l'écran", "EPSG, CRS, None dans 16 textes"),
    ("Une suppression sans rideau", "4 actions coupent sans demander"),
]
for regle, preuve in interdits:
    d.line([(DROITE * S, (y + 9) * S), (DROITE + 10, ) and
            ((DROITE + 10) * S, (y + 9) * S)], fill=CLAIR["block"],
           width=int(1.6 * S))
    txt(DROITE + 18, y, regle, 9.4, CLAIR["ink"])
    txt(DROITE + 330, y, preuve, 8.6, CLAIR["ink_3"])
    y += 24

# ══ 7 · SOMBRE
y += 16
txt(DROITE, y, "7 · Le même écran, en sombre", 13, CLAIR["ink"], True)
txt(DROITE, y + 20, "Mêmes jetons, inversés. Aucune couleur de donnée ne change.",
    9.6, CLAIR["ink_2"])
y += 44
rect(DROITE, y, 740, 118, SOMBRE["surface"], SOMBRE["border"], 10)
txt(DROITE + 20, y + 14, "Pistes", 12.5, SOMBRE["ink"], True)
txt(DROITE + 20, y + 36, "12 pistes en 4 familles · 6 réglages visibles",
    9.2, SOMBRE["ink_2"])
rect(DROITE + 566, y + 14, 154, 28, SOMBRE["accent"], None, 7)
txt(DROITE + 643, y + 21, "Appliquer", 9.4, "#FFFFFF", True, "ma")
for i, (nom, cle) in enumerate([("fond", "bg"), ("surface", "surface"),
                                ("bord", "border"), ("texte", "ink")]):
    x = DROITE + 20 + i * 178
    rect(x, y + 56, 168, 26, SOMBRE[cle], SOMBRE["border"], 6)
    txt(x + 8, y + 60, f"{nom} {SOMBRE[cle]}", 7.8, SOMBRE["ink_2"])

# ══ 8 · COMPOSITION
y = 900
txt(GAUCHE, y, "8 · Composition d'un écran", 13, CLAIR["ink"], True)
txt(GAUCHE, y + 20, "Les mêmes cinq zones dans tous les écrans. "
    "Rien d'autre ne flotte.", 9.6, CLAIR["ink_2"])
y += 40
cx, cw = GAUCHE, 740
zones = [("Barre haute", 22, "toujours : modules · langue · projet"),
         ("Titre", 30, "une phrase : ce que fait l'écran"),
         ("Zone de travail", 150, "panneau principal + panneau de détail"),
         ("Barre basse", 22, "l'état, et une seule action de sortie")]
yy = y
for nom, h, desc in zones:
    rect(cx, yy, cw, h, CLAIR["surface"], CLAIR["border"], 6)
    txt(cx + 10, yy + 6, nom, 8.6, CLAIR["ink"], True)
    txt(cx + 130, yy + 6, desc, 8.2, CLAIR["ink_3"])
    if nom == "Zone de travail":
        rect(cx + 8, yy + 22, cw - 180, h - 30, CLAIR["surface_2"],
             CLAIR["border"], 5)
        txt(cx + 18, yy + 34, "principal", 8, CLAIR["ink_3"])
        rect(cx + cw - 164, yy + 22, 156, h - 30, CLAIR["surface_2"],
             CLAIR["border"], 5)
        txt(cx + cw - 154, yy + 34, "détail", 8, CLAIR["ink_3"])
    yy += h + 6

# ══ 9 · HIÉRARCHIE
txt(DROITE, 900, "9 · Hiérarchie : deux niveaux, jamais trois", 13,
    CLAIR["ink"], True)
txt(DROITE, 920, "Un groupe = une décision. Ses champs en dessous, indentés "
    "de 16 px.", 9.6, CLAIR["ink_2"])
y = 962
rect(DROITE, y, 740, 96, CLAIR["surface"], CLAIR["border"], 8)
txt(DROITE + 16, y + 12, "Teneurs", 10.2, CLAIR["ink"], True)
txt(DROITE + 640, y + 12, "actif", 8.4, CLAIR["ok"], True, "ra")
for i, (lab, val) in enumerate([("Largeur", "15 px"), ("Opacité", "90 %"),
                                ("Côté", "Droite")]):
    yy = y + 34 + i * 20
    txt(DROITE + 32, yy, lab, 8.8, CLAIR["ink_2"])
    txt(DROITE + 320, yy, val, 8.8, CLAIR["ink"], True)
txt(DROITE + 16, y + 98, "Ce qui est indenté appartient au groupe. "
    "Ce qui ne l'est pas est un autre groupe.", 8.4, CLAIR["ink_3"])

# ── pied
trait(40, 1300, 1560, 1300)
txt(40, 1312, "Cette planche est générée depuis le thème du projet — "
    "la maquette et le plugin lisent le même fichier.", 9.2, CLAIR["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "23_charte.png"))
print("écrit maquettes/23_charte.png")
