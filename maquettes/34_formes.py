"""Planche 34 — la forme des fonctions : la moitié qu'on ne voyait pas.

    python3 maquettes/34_formes.py

Le rangement par fichiers ne dit que la moitié de l'histoire : un fichier de
2 000 lignes fait de vingt fonctions de 100 lignes se lit ; un fichier de
600 lignes contenant une fonction de 500 lignes ne se lit pas. Cette planche
montre la seconde moitié.

Rien n'est dessiné à la main : les chiffres viennent de
`specs/data/formes.json`, produit par `tools/audit_formes.py`.
"""
from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(OUT, "..", "specs", "data")
THEME = json.load(open(os.path.join(DONNEES, "theme.json"), encoding="utf-8"))
FORMES = json.load(open(os.path.join(DONNEES, "formes.json"), encoding="utf-8"))
T = THEME["clair"]
S = 2
W, H = 1600, 918
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


def chiffre(x, y, valeur, legende, col=None, largeur=250):
    rect(x, y, largeur, 92, T["surface"], T["border"], 10)
    txt(x + 16, y + 12, str(valeur), 30, col or T["ink"], True)
    txt(x + 16, y + 58, legende, 8.8, T["ink_2"])


txt(40, 26, "La forme des fonctions", 22, T["ink"], True)
txt(40, 58, "Une fonction se juge à sa taille, pas à celle de son fichier. "
    "Ce que le rangement par fichiers ne voyait pas.", 10.2, T["ink_2"])

# ══ 1 · les quatre chiffres, sur toute la largeur
y = 104
txt(40, y, "1 · L'état mesuré, au 8 novembre 2026", 13, T["ink"], True)
y += 26
chiffre(40, y, FORMES["fonctions"], "fonctions dans le plugin", largeur=360)
chiffre(420, y, f"{FORMES['part_courtes']:.1%}",
        f"tiennent en moins de 40 lignes "
        f"({FORMES['courtes_moins_de_40']})", T["ok"], largeur=360)
chiffre(800, y, FORMES["par_seuil"]["80"], "dépassent 80 lignes",
        T["warn"], largeur=360)
chiffre(1180, y, FORMES["par_seuil"]["400"], "dépassent 400 lignes",
        T["block"], largeur=360)

# ══ 2 · la répartition par seuil (gauche)
y2 = 250
txt(40, y2, "2 · La répartition par seuil", 13, T["ink"], True)
seuils = [("80", "80 l. et plus", T["ok"]),
          ("150", "150 l. et plus", T["warn"]),
          ("250", "250 l. et plus", T["warn"]),
          ("400", "400 l. et plus", T["block"])]
maxi = FORMES["par_seuil"]["80"] or 1
for k, (cle, libelle, col) in enumerate(seuils):
    n = FORMES["par_seuil"][cle]
    yy = y2 + 30 + k * 24
    txt(40, yy, libelle, 9, T["ink_2"])
    largeur = max(4, n / maxi * 240)
    rect(180, yy + 1, largeur, 11, col, None, 4)
    txt(180 + largeur + 8, yy, str(n), 9, T["ink"], True)
txt(40, y2 + 130, "80 lignes : au-delà, une fonction ne tient plus d'un "
    "coup d'œil.", 8.6, T["ink_3"])

# ══ 3 · la classe monolithe (droite)
D = 520
txt(D, y2, "3 · Une classe porte la moitié du plugin", 13, T["ink"], True)
c = FORMES["plus_grosse_classe"]
rect(D, y2 + 26, 1040, 128, T["surface_2"], T["border"], 10)
txt(D + 18, y2 + 40, c["nom"], 13, T["ink"], True)
txt(D + 18, y2 + 60, f"{c['fichier']} · {c['lignes']} lignes", 9, T["ink_2"])
m = FORMES["classe_la_plus_de_methodes"]
txt(D + 18, y2 + 84, f"{m['methodes']} méthodes dans une seule classe", 10.4,
    T["block"], True)
txt(D + 18, y2 + 104, "Chaque méthode est courte : le défaut n'est pas la "
    "taille des fonctions, c'est le nombre de voisines.", 9, T["ink_2"])

# ══ 4 · le code replié (gauche, sous la répartition)
y3 = 432
txt(40, y3, "4 · Le code replié : des fonctions nommées dans une fonction",
    13, T["ink"], True)
txt(40, y3 + 20, "Ce ne sont pas des générateurs : ce sont des fonctions "
    "écrites sur place, faute de les avoir nommées.", 9, T["ink_2"])
yy = y3 + 44
for r in FORMES["fonctions_repliees"][:3]:
    rect(40, yy, 460, 42, T["surface"], T["border"], 8)
    txt(54, yy + 6, r["nom"], 9.6, T["ink"], True)
    txt(54, yy + 22, f"{r['fichier']}:{r['ligne']} · {r['lignes']} lignes",
        8.2, T["ink_3"])
    txt(420, yy + 8, f"{r['fonctions_nommees']} fonctions", 9, T["block"],
        True, "ra")
    yy += 50

# ══ 5 · les grandes fonctions (droite)
txt(D, y3, "5 · Les cinq fonctions de 400 lignes et plus", 13, T["ink"], True)
yy = y3 + 28
for g in FORMES["plus_grandes"][:5]:
    txt(D, yy, f"{g['lignes']} l.", 9.6, T["block"], True)
    txt(D + 58, yy, g["nom"], 9.4, T["ink"])
    txt(D + 58, yy + 14, f"{g['fichier']}:{g['ligne']}", 8, T["ink_3"])
    yy += 34

# ══ 6 · les règles
y4 = H - 250
rect(40, y4, 1520, 150, T["accent_soft"], T["accent_line"], 10)
txt(58, y4 + 12, "Quatre cliquets, tenus par specs/tests/test_forme.py",
    10.6, T["ink"], True)
regles = [
    ("F-01", "le nombre de grandes fonctions ne monte pas",
     "106 au-dessus de 80 lignes · 31 au-dessus de 150 · 12 au-dessus de 250"),
    ("F-02", "les fonctions courtes restent la règle",
     f"{FORMES['part_courtes']:.1%} du plugin tient en moins de 40 lignes"),
    ("F-03", "aucune classe ne porte plus de 172 méthodes",
     "SectionWidget est le plafond, pas la permission de l'imiter"),
    ("F-04", "aucune fonction ne replie plus de 9 fonctions nommées",
     "_draw_style_identity_track est le plafond mesuré"),
]
for k, (num, titre, quoi) in enumerate(regles):
    yyy = y4 + 34 + k * 28
    txt(58, yyy, num, 9, T["accent"], True)
    txt(98, yyy, titre, 9.4, T["ink"], True)
    txt(410, yyy, quoi, 8.8, T["ink_2"])

ligne(40, H - 54, 1560, H - 54)
txt(40, H - 44, "Chiffres produits par tools/audit_formes.py — relancé à "
    "chaque passage, jamais recopiés. Un cliquet n'est pas un vœu : il fait "
    "échouer la suite s'il est franchi.", 8.6, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "34_formes.png"))
print("écrit maquettes/34_formes.png")
