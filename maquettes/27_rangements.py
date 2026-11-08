"""Planche 27 — les rangements : pourquoi la coupe tient sur 14 000 lignes.

    python3 maquettes/27_rangements.py

Les chiffres sont lus dans ``specs/data/rangement.json`` (produit par
``tools/audit_rangement.py``), jamais recopiés à la main.
"""
from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(OUT, "..", "specs", "data")
THEME = json.load(open(os.path.join(DONNEES, "theme.json"), encoding="utf-8"))
AUDIT = json.load(open(os.path.join(DONNEES, "rangement.json"),
                       encoding="utf-8"))
T = THEME["clair"]
S = 2
W, H = 1600, 700
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


txt(40, 30, "Les rangements", 22, T["ink"], True)
txt(40, 62, "Un fichier qu'on ne peut pas relire d'un trait est un fichier "
    "qu'on ne modifie plus sans peur.", 10.2, T["ink_2"])

# ══ 1 · ce qui a bougé
y = 112
txt(40, y, "1 · Ce que la tranche a changé", 13, T["ink"], True)
y += 26
chemins = [("avant", 11529, T["block"], "section_dock.py — 2 classes, 294 méthodes"),
           ("après", 10515, T["ok"], "mêmes classes, moins de poids mort")]
yy = y
for nom, n, col, quoi in chemins:
    txt(40, yy + 4, nom, 9.4, T["ink_2"], True)
    largeur = n / 11529 * 620
    rect(96, yy, largeur, 22, col, None, 4)
    txt(104 + largeur, yy + 4, f"{n} lignes", 9, col, True)
    txt(40, yy + 26, quoi, 8.4, T["ink_3"])
    yy += 56

# ══ 2 · ce qui est sorti
y += 116
txt(40, y, "2 · Sorti du monolithe, sans changer un comportement", 13,
    T["ink"], True)
txt(40, y + 22, "Chaque tranche est une extraction pure : mêmes noms, "
    "ré-exportés. Les appelants n'ont pas bougé.", 9.4, T["ink_2"])
y += 52
sortis = [("ui/coupe_socle.py", "288", "couleurs d'interaction, motifs, "
          "encres, items graphiques"),
          ("docs/HISTORIQUE_section_dock.md", "801", "le journal de versions, "
           "sorti de la docstring"),
          ("ui/section_export.py", "2174", "la mécanique d'export"),
          ("ui/section_surface.py", "848", "la lecture du sol"),
          ("ui/section_holes.py", "377", "l'exclusion des forages"),
          ("ui/section_structure.py", "675", "mesures et marqueurs"),
          ("ui/section_geotech.py", "553", "pistes géotechniques"),
          ("ui/section_imagery.py", "760", "imagerie et matériaux")]
for nom, n, quoi in sortis:
    encadre = nom == "ui/coupe_socle.py"
    rect(40, y, 740, 34, T["surface"] if encadre else None,
         T["accent_line"] if encadre else None, 8)
    txt(56, y + 9, nom, 9.2, T["ink"], True)
    txt(56, y + 22, quoi, 7.8, T["ink_3"])
    txt(764, y + 9, n, 9, T["accent"] if encadre else T["ink_3"], True, "ra")
    y += 40

txt(40, y + 2, "les deux premières entrées sont la tranche 1 de ce passage ; les "
    "suivantes étaient sorties avant, sans jamais être mesurées.", 8.2, T["ink_3"])

# ══ 3 · LE CLIQUET
D = 820
y = 112
txt(D, y, "3 · Le cliquet", 13, T["ink"], True)
txt(D, y + 22, "Un test refuse que le monolithe remonte. Il ne dit pas "
    "« c'est rangé » : il dit « ça ne peut pas empirer en silence ».", 9.4,
    T["ink_2"])
y += 62

rect(D, y, 740, 108, T["surface"], T["border"], 10)
txt(D + 18, y + 12, "specs/tests/test_rangement.py — 7 tests", 10, T["ink"],
    True)
regles = [("le monolithe ne dépasse pas 10 560 lignes", "cliquet"),
          ("un seul fichier du plugin au-delà de 3 000 lignes", "cliquet"),
          ("les 16 noms sortis vivent dans le socle ET restent ré-exportés",
           "contrat"),
          ("aucun nom défini dans les deux fichiers", "contrat"),
          ("le journal de versions ne revient pas dans le code", "contrat")]
yy = y + 32
for r, genre in regles:
    col = T["accent"] if genre == "cliquet" else T["ok"]
    txt(D + 18, yy, "· " + r, 8.6, T["ink_2"])
    txt(D + 720, yy, genre, 7.8, col, True, "ra")
    yy += 14

# ══ 4 · LE DÉFAUT QUI RESTE
y += 128
txt(D, y, "4 · Ce que la mesure dit du reste", 13, T["ink"], True)
y += 30
mesures = [(len(AUDIT["gros_fichiers"]), "fichiers au-delà de 1 500 lignes",
            "40 % du plugin"),
           (AUDIT["lignes_de_journal"], "lignes de commentaire d'historique",
            "un bug corrigé relu à chaque fois"),
           (len(AUDIT["noms_partages"]),
            "noms de fonctions dans plusieurs fichiers",
            "pas une duplication prouvée — une invitation à regarder")]
for n, quoi, note in mesures:
    rect(D, y, 740, 52, T["surface"], T["border"], 9)
    txt(D + 18, y + 9, quoi, 9.2, T["ink"], True)
    txt(D + 18, y + 27, note, 8.2, T["ink_3"])
    txt(D + 720, y + 12, str(n), 17, T["ink_2"], True, "ra")
    y += 60

# ══ 5 · LA RÈGLE
y += 6
rect(D, y, 740, 92, T["accent_soft"], T["accent_line"], 10)
txt(D + 18, y + 12, "R-52 · Une tranche sort, un cliquet baisse", 10.4,
    T["ink"], True)
txt(D + 18, y + 34, "On ne découpe pas « un jour » : chaque tranche sortie "
    "baisse le plafond", 8.8, T["ink_2"])
txt(D + 18, y + 50, "dans le même commit. Le monolithe ne peut donc que "
    "maigrir.", 8.8, T["ink_2"])
txt(D + 18, y + 70, "Et une extraction ne change aucun comportement : "
    "mêmes noms, ré-exportés.", 8.4, T["ink_3"])

# ── pied
ligne(40, H - 44, 1560, H - 44)
txt(40, H - 34, "Chiffres produits par tools/audit_rangement.py — "
    "relancer après chaque tranche.", 8.8, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "27_rangements.png"))
print("écrit maquettes/27_rangements.png")
