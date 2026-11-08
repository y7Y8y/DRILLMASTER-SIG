"""Planche 29 — la navigation : un écran, quatre chemins, zéro trappe.

    python3 maquettes/29_navigation.py

Les chemins sont lus dans le registre (drillmaster_v3/core/navigation.py) ;
les chiffres du plugin dans specs/data/navigation.json. Rien n'est recopié.
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
AUDIT = json.load(open(os.path.join(DONNEES, "navigation.json"),
                       encoding="utf-8"))
from drillmaster_v3.core.navigation import navigation_du_plugin   # noqa: E402

T = THEME["clair"]
S = 2
W, H = 1600, 880
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


n = navigation_du_plugin()
resume = n.resume()

txt(40, 28, "La navigation", 22, T["ink"], True)
txt(40, 60, "Une action, un chemin. Ce qui n'est pas atteignable n'est pas "
    "écrit — et ce qui est écrit s'atteint.", 10.2, T["ink_2"])

# ══ 1 · les cinq zones
y = 112
txt(40, y, "1 · Cinq zones, jamais six", 13, T["ink"], True)
txt(40, y + 22, "Tout geste appartient à une zone nommée. Une zone vide est "
    "un endroit où l'utilisateur regarde pour rien.", 9.4, T["ink_2"])
y += 52
from drillmaster_v3.core.navigation import ZONES            # noqa: E402
x = 40
for zone in ZONES:
    n_chemins = sum(len(e.par_zone(zone)) for e in n.ecrans.values())
    vide = n_chemins == 0
    rect(x, y, 148, 74, T["surface"], T["border"], 10)
    txt(x + 12, y + 12, zone, 8.8, T["ink"] if not vide else T["ink_3"], True)
    txt(x + 12, y + 32, f"{n_chemins} chemin(s)" if n_chemins else "aucun",
        8.6, T["ink_2"] if not vide else T["ink_3"])
    if vide:
        txt(x + 12, y + 50, "à remplir", 7.8, T["block"])
        txt(x + 12, y + 60, "ou à retirer", 7.8, T["block"])
    x += 156

# ══ 2 · les quatre écrans et leurs chemins
y += 100
txt(40, y, "2 · Les quatre écrans, chemin par chemin", 13, T["ink"], True)
y += 30
GAUCHE_W = 760
for e in n.ecrans.values():
    txt(40, y, e.nom, 11, T["ink"], True)
    txt(40 + 150, y + 2, f"{len(e.chemins)} chemins", 8.8, T["ink_3"])
    y += 20
    for c in e.chemins:
        rect(48, y - 1, 128, 15, T["surface_2"], T["border"], 7)
        txt(112, y + 1, c.zone, 7.6, T["ink_2"], False, "ma")
        txt(186, y + 1, c.geste, 7.6, T["accent"], False)
        txt(300, y + 1, c.quoi, 8.6, T["ink"])
        y += 17
    y += 8

# ══ 3 · ce que l'outil trouve dans le plugin
D = 860
y = 112
txt(D, y, "3 · Ce que le plugin fait vraiment", 13, T["ink"], True)
total_ecrans = sum(AUDIT["ecrans"].values())
txt(D, y + 22, "Mesuré par tools/audit_navigation.py — "
    f"{AUDIT['ecrans'].get('QDialog', 0)} fenêtres, "
    f"{AUDIT['ecrans'].get('QWidget', 0)} panneaux", 9.2, T["ink_2"])
y += 52

constats = [
    (str(total_ecrans), "écrans",
     "fenêtres et panneaux, tous genres", T["ink_2"]),
    (str(len(AUDIT["dialogues_jamais_ouverts"])), "fenêtres sans porte",
     "aucune n'existe ouverte : du code que personne ne peut atteindre",
     T["ok"] if not AUDIT["dialogues_jamais_ouverts"] else T["block"]),
    (str(AUDIT["raccourcis_muets"]), "raccourcis muets",
     "une touche qui agit sans être écrite nulle part (R-58)", T["block"]),
    (str(len(AUDIT["morts"])), "réglages sans lecteur",
     "écrits à la fermeture, jamais relus : ils ne reviennent pas", T["warn"]),
]
for val, quoi, note, col in constats:
    rect(D, y, 700, 56, T["surface"], T["border"], 9)
    rect(D, y, 4, 56, col, None, 0)
    txt(D + 18, y + 10, quoi, 9.8, T["ink"], True)
    txt(D + 18, y + 30, note, 8.2, T["ink_3"])
    txt(D + 684, y + 14, val, 18, col, True, "ra")
    y += 64

# les 4 raccourcis muets, nommés
y += 4
txt(D, y, "Les quatre touches que personne ne voit", 9.8, T["ink"], True)
y += 22
for r in AUDIT["raccourcis"]:
    if r["affiche"]:
        continue
    txt(D + 8, y, r["touche"], 9, T["ink"], True)
    txt(D + 90, y, r["fichier"] + ":" + str(r["ligne"]), 8, T["ink_3"])
    y += 16

# ══ 4 · la règle
y += 14
rect(D, y, 700, 132, T["accent_soft"], T["accent_line"], 10)
txt(D + 18, y + 12, "R-56 · un seul chemin   R-57 · pas d'écran sans porte",
    9.8, T["ink"], True)
txt(D + 18, y + 34, "R-58 · un raccourci n'existe que s'il est écrit "
    "sur le bouton", 9.8, T["ink"], True)
for k, phrase in enumerate([
        "Deux entrées pour la même action : refusé à la construction.",
        "Un écran qu'aucun geste n'ouvre : mesuré, nommé, corrigé.",
        "Une touche qui agit sans être affichée : c'est un pouvoir invisible.",
        "Le registre est la référence ; le plugin est comparé à lui."]):
    txt(D + 18, y + 58 + k * 17, "· " + phrase, 8.4, T["ink_2"])

# ── pied
ligne(40, H - 44, 1560, H - 44)
txt(40, H - 34, "Chemin lu dans drillmaster_v3/core/navigation.py · "
    "plugin mesuré par tools/audit_navigation.py", 8.6, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "29_navigation.png"))
print("écrit maquettes/29_navigation.png")
