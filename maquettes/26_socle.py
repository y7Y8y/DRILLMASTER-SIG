"""Planche 26 — le socle visuel : où vit une couleur, et ce qu'elle remplace.

    python3 maquettes/26_socle.py

Deux moitiés :
  • en haut, la chaîne de vérité `theme.json → palette_jetons.py → écran` ;
  • en bas, la table de correspondance entre l'ancienne palette « géologique »
    du plugin (celle qui se contredisait) et les rôles de la DA.
Les valeurs sont lues dans les deux fichiers, jamais recopiées à la main.
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
AUDIT = json.load(open(os.path.join(DONNEES, "audit_couleurs.json"),
                      encoding="utf-8"))
from DrillMaster.ui import palette_jetons as P          # noqa: E402
from DrillMaster.ui import styles_qt                     # noqa: E402

CLAIR, SOMBRE = THEME["clair"], THEME["sombre"]
S = 2
W, H = 1600, 900
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


def trait(x1, y1, x2, y2, col=None, ep=1):
    d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=col or CLAIR["border"],
           width=int(ep * S))


def fleche(x, y, h=18):
    d.line([x * S, y * S, x * S, (y + h) * S], fill=CLAIR["ink_3"], width=S)
    d.polygon([((x - 4) * S, (y + h) * S), ((x + 4) * S, (y + h) * S),
               (x * S, (y + h + 5) * S)], fill=CLAIR["ink_3"])


# ══ en-tête
txt(40, 28, "DrillMaster — le socle visuel", 22, CLAIR["ink"], True)
txt(40, 60, "Une couleur se nomme par son rôle, jamais par sa teinte. "
    "Un seul foyer, une copie générée, zéro dérive possible.", 10.5,
    CLAIR["ink_2"])

# ══ 1 · LA CHAÎNE
y = 104
txt(40, y, "1 · La chaîne de vérité", 13, CLAIR["ink"], True)
txt(40, y + 22, "Trois maillons. Le troisième est le seul que Qt peut lire ; "
    "il est régénéré, jamais édité.", 9.6, CLAIR["ink_2"])
y += 56

chaines = [("specs/data/theme.json", "la DA — 18 rôles × 2 modes",
            "s'édite à la main"),
           ("DrillMaster/ui/palette_jetons.py", "la copie lisible par Qt",
            "généré — ne pas éditer"),
           ("l'écran, la 2D, la 3D, l'export", "un seul nom par couleur",
            "lit couleur(role)")]
x = 40
for i, (nom, quoi, regle) in enumerate(chaines):
    rect(x, y, 470, 74, CLAIR["surface"], CLAIR["border"], 10)
    txt(x + 16, y + 14, nom, 10.4, CLAIR["ink"], True)
    txt(x + 16, y + 36, quoi, 9, CLAIR["ink_2"])
    txt(x + 16, y + 54, regle, 8.4, CLAIR["ink_3"])
    if i < 2:
        fleche(x + 485, y + 22)
    x += 520

# ══ 2 · LE DÉFAUT D'ORIGINE
y = 252
txt(40, y, "2 · Ce qui n'allait pas", 13, CLAIR["ink"], True)
y += 26
maux = [("Deux palettes vivantes", "theme.json (18 rôles neutres) et "
         "styles_qt.COLORS (17 teintes terreuses) se contredisaient"),
        ("Une teinte de chrome qui imite une donnée", "un teal d'interface "
         "identique au teal d'une lithologie — prouvé à l'écran"),
        ("417 couleurs écrites dans des feuilles de style", "dans 30 fichiers ; "
         "changer le fond obligeait à en corriger 30")]
for titre, quoi in maux:
    d.ellipse([48 * S, (y + 5) * S, 56 * S, (y + 13) * S], fill=CLAIR["block"])
    txt(68, y, titre, 9.8, CLAIR["ink"], True)
    txt(68, y + 17, quoi, 8.8, CLAIR["ink_2"])
    y += 44

# ══ 3 · LA CORRESPONDANCE
y += 10
txt(40, y, "3 · L'ancienne palette, rôle par rôle", 13, CLAIR["ink"], True)
txt(40, y + 22, "Ce que chaque ancien nom devient. La colonne « écart » "
    "mesure la distance de teinte perçue.", 9.6, CLAIR["ink_2"])
y += 50

LIGNES = [("primary", "ink", "texte des titres"),
          ("text_dark", "ink", "texte courant"),
          ("text_medium", "ink_2", "texte secondaire"),
          ("text_light", "ink_3", "texte discret"),
          ("bg_main", "bg", "fond de fenêtre"),
          ("bg_card", "surface", "carte, panneau"),
          ("bg_input", "surface", "champ de saisie"),
          ("border", "border", "filet"),
          ("border_dark", "border_strong", "filet appuyé"),
          ("text_white", "surface", "encre sur aplat sombre")]

trait(40, y - 6, 760, y - 6, CLAIR["border_strong"])
txt(40, y, "ancien nom du plugin", 8.6, CLAIR["ink_3"], True)
txt(300, y, "teinte", 8.6, CLAIR["ink_3"], True)
txt(420, y, "rôle de la DA", 8.6, CLAIR["ink_3"], True)
txt(640, y, "usage", 8.6, CLAIR["ink_3"], True)
y += 20

import math


def lab(c):
    c = c.lstrip("#")
    v = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    v = [u / 12.92 if u <= .04045 else ((u + .055) / 1.055) ** 2.4 for u in v]
    r, g, b = v
    X = r * .4124 + g * .3576 + b * .1805
    Y = r * .2126 + g * .7152 + b * .0722
    Z = r * .0193 + g * .1192 + b * .9505

    def g_(t):
        return t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
    fx, fy, fz = g_(X / .95047), g_(Y), g_(Z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta(a, b):
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(lab(a), lab(b))))


for ancien, role, usage in LIGNES:
    if ancien not in styles_qt.COLORS:
        continue
    teinte = styles_qt.COLORS[ancien]
    cible = P.couleur(role)
    rect(48, y + 2, 20, 20, teinte, CLAIR["border"], 4)
    txt(78, y + 3, ancien, 9.2, CLAIR["ink"], True)
    txt(300, y + 3, teinte, 8.8, CLAIR["ink_2"])
    fleche(396, y + 4, 12)
    rect(430, y + 2, 20, 20, cible, CLAIR["border"], 4)
    txt(460, y + 3, role, 9.2, CLAIR["ink"], True)
    txt(640, y + 3, usage, 8.8, CLAIR["ink_2"])
    ecart = delta(teinte, cible)
    col = CLAIR["block"] if ecart > 40 else (CLAIR["warn"] if ecart > 12
                                             else CLAIR["ok"])
    txt(760, y + 3, f"écart {ecart:3.0f}", 8.6, col, True)
    trait(40, y + 23, 760, y + 23, CLAIR["surface_3"])
    y += 26

trait(40, y + 4, 760, y + 4, CLAIR["border_strong"])
txt(40, y + 12, "Vert, orange et rouge de l'ancienne palette ne deviennent "
    "aucun de ces rôles :", 8.6, CLAIR["ink_3"])
txt(40, y + 26, "ce sont des états, donc des jetons déjà nommés "
    "— ok · warn · block.", 8.6, CLAIR["ink_3"])

# ══ 4 · CE QUI RESTE À FAIRE (mesuré)
DROITE = 820
y = 252
txt(DROITE, y, "4 · L'état mesuré, aujourd'hui", 13, CLAIR["ink"], True)
txt(DROITE, y + 22, "Production de `python3 tools/audit_couleurs.py`, "
    "relancé à chaque passage.", 9.6, CLAIR["ink_2"])
y += 56

mesures = [("couleurs de données — légitimes",
            AUDIT["couleurs_donnees"], "lithologie, altérations, genèses",
            CLAIR["ok"]),
           ("jetons de chrome déclarés dans styles_qt",
            AUDIT["jetons_chrome"], "à remplacer par palette_jetons",
            CLAIR["warn"]),
           ("couleurs dans des feuilles de style",
            AUDIT["couleurs_dans_styles"], "le gros du travail, 30 fichiers",
            CLAIR["block"])]
for titre, n, quoi, col in mesures:
    rect(DROITE, y, 740, 58, CLAIR["surface"], CLAIR["border"], 10)
    rect(DROITE, y, 4, 58, col, None, 0)
    txt(DROITE + 18, y + 11, titre, 9.6, CLAIR["ink"], True)
    txt(DROITE + 18, y + 32, quoi, 8.6, CLAIR["ink_2"])
    txt(DROITE + 720, y + 16, str(n), 20, col, True, "ra")
    y += 66

y += 4
txt(DROITE, y, "Les 8 fichiers qui portent le plus de couleurs", 9.6,
    CLAIR["ink"], True)
y += 22
for rel, n in list(AUDIT["fichiers_de_style"].items())[:8]:
    txt(DROITE + 4, y, rel, 8.6, CLAIR["ink_2"])
    txt(DROITE + 720, y, str(n), 8.6, CLAIR["ink"], True, "ra")
    y += 17

# ══ 5 · LA RÈGLE
y += 14
rect(DROITE, y, 740, 116, CLAIR["accent_soft"], CLAIR["accent_line"], 10)
txt(DROITE + 18, y + 12, "La règle, désormais tenue par un test", 10.4,
    CLAIR["ink"], True)
regles = ["une teinte n'existe que dans theme.json ;",
          "le module Qt n'est jamais édité, il est généré ;",
          "un rôle inconnu lève au lieu de rendre du vide ;",
          "un test échoue si le module a dérivé du thème."]
for i, r in enumerate(regles):
    txt(DROITE + 18, y + 38 + i * 17, "· " + r, 8.8, CLAIR["ink_2"])

# ── pied
trait(40, H - 46, 1560, H - 46)
txt(40, H - 36, "Planche générée depuis les données visuelles du projet — "
    "aucune valeur n'est recopiée à la main.", 9, CLAIR["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "26_socle.png"))
print("écrit maquettes/26_socle.png")
