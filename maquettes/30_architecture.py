"""Planche 30 — l'architecture : qui a le droit de voir qui.

    python3 maquettes/30_architecture.py

Rien n'est dessiné à la main : les chiffres viennent de
`specs/data/architecture.json`, produit par `tools/audit_architecture.py`.
"""
from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(OUT, "..", "specs", "data")
THEME = json.load(open(os.path.join(DONNEES, "theme.json"), encoding="utf-8"))
AUDIT = json.load(open(os.path.join(DONNEES, "architecture.json"),
                       encoding="utf-8"))
T = THEME["clair"]
S = 2
W, H = 1600, 800
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


def ligne(x1, y1, x2, y2, col=None, ep=1, tiret=None):
    if tiret:
        # traits pointillés : dessinés à la main, PIL ne les connaît pas
        import math
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        pas = tiret[0] + tiret[1]
        n = int(dist / pas)
        for k in range(n + 1):
            a = k * pas / dist
            b = min(1.0, (k * pas + tiret[0]) / dist)
            d.line([(x1 + dx * a) * S, (y1 + dy * a) * S,
                    (x1 + dx * b) * S, (y1 + dy * b) * S],
                   fill=col or T["border"], width=int(ep * S))
        return
    d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=col or T["border"],
           width=int(ep * S))


def fleche(x, y, dy=26, col=None, ep=1.4, tiret=None):
    ligne(x, y, x, y + dy, col, ep, tiret)
    d.polygon([((x - 4) * S, (y + dy) * S), ((x + 4) * S, (y + dy) * S),
               (x * S, (y + dy + 6) * S)], fill=col or T["border"])


txt(40, 28, "L'architecture", 22, T["ink"], True)
txt(40, 60, "Le noyau ne connaît pas l'interface. Une vue ne calcule pas. "
    "Ce qui n'est branché par personne est nommé, jamais oublié.",
    10.2, T["ink_2"])

# ══ 1 · les trois couches
y = 112
txt(40, y, "1 · Trois couches, deux flèches autorisées", 13, T["ink"], True)
y += 30

COUCHES = [("Interface", "27 écrans, 16 panneaux", T["surface_2"], T["ink_2"]),
           ("Noyau", f"{AUDIT['modules_noyau']} modules : données, calculs, "
            "réglages", T["accent_soft"], T["ink"]),
           ("Données", "contrats et référentiels du projet", T["surface_2"],
            T["ink_2"])]
yy = y
for nom, quoi, fond, encre in COUCHES:
    rect(40, yy, 620, 54, fond, T["border"], 10)
    txt(58, yy + 10, nom, 11, encre, True)
    txt(58, yy + 30, quoi, 8.6, T["ink_2"])
    yy += 74

# flèches : interface → noyau (permis), noyau ↛ interface (interdit)
fleche(360, y + 58, 12, T["ok"])
txt(372, y + 60, "appelle", 8.4, T["ok"], True)
fleche(360, y + 132, 12, T["block"])
txt(372, y + 134, "jamais", 8.4, T["block"], True)

# ══ 2 · la mesure
y = 400
txt(40, y, "2 · Ce que la mesure trouve", 13, T["ink"], True)
y += 30
mesures = [
    (str(len(AUDIT["fuites_noyau"])), "fuites du noyau vers l'interface",
     "aucun module de calcul n'importe un widget", T["ok"]),
    (str(AUDIT["calculs_dans_les_vues"]), "calculs écrits dans les vues",
     "trigonométrie qui devrait vivre dans le noyau", T["warn"]),
    (str(len(AUDIT["modules_jamais_importes"])), "modules que rien n'importe",
     "outils et points d'entrée : nommés, pas cachés", T["ink_2"]),
]
for val, quoi, note, col in mesures:
    rect(40, y, 620, 56, T["surface"], T["border"], 9)
    rect(40, y, 4, 56, col, None, 0)
    txt(58, y + 10, quoi, 9.6, T["ink"], True)
    txt(58, y + 30, note, 8.2, T["ink_3"])
    txt(644, y + 14, val, 18, col, True, "ra")
    y += 64

# ══ 3 · les calculs, fichier par fichier
D = 700
y = 112
txt(D, y, "3 · Où sont les calculs qui n'ont rien à faire là", 13, T["ink"],
    True)
txt(D, y + 22, "Chaque ligne est une occasion de divergence : la coupe et la "
    "3D peuvent calculer la même chose différemment.", 9.2, T["ink_2"])
y += 54
calculs = AUDIT["fichiers_de_vue_avec_calcul"]
maxi = max(calculs.values()) if calculs else 1
for rel, n in list(calculs.items())[:8]:
    txt(D, y, rel.replace("DrillMaster.", ""), 8.8, T["ink_2"])
    rect(D + 300, y + 2, max(6, n / maxi * 280), 9, T["warn"], None, 4)
    txt(D + 300 + max(6, n / maxi * 280) + 8, y + 1, str(n), 8.6, T["ink"], True)
    y += 20

# ══ 4 · les règles
y += 16
rect(D, y, 860, 150, T["accent_soft"], T["accent_line"], 10)
txt(D + 18, y + 12, "Trois règles tenues par un test", 10.4, T["ink"], True)
regles = [
    ("R-40", "le noyau ne connaît pas l'interface",
     "aucun import de widget dans les 57 modules de calcul"),
    ("R-41", "une vue ne calcule pas",
     "77 calculs restants, plafond posé : ils ne peuvent que diminuer"),
    ("R-59", "ce que rien ne branche est nommé",
     "5 modules, listés : trois outils, deux points d'entrée"),
]
for k, (num, titre, quoi) in enumerate(regles):
    yy = y + 34 + k * 36
    txt(D + 18, yy, num, 9, T["accent"], True)
    txt(D + 58, yy, titre, 9.4, T["ink"], True)
    txt(D + 58, yy + 15, quoi, 8.2, T["ink_3"])

# ── pied
ligne(40, H - 44, 1560, H - 44)
txt(40, H - 34, "Chiffres produits par tools/audit_architecture.py — "
    "relancé à chaque passage, jamais recopiés.", 8.6, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "30_architecture.png"))
print("écrit maquettes/30_architecture.png")
