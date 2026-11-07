"""Planche contact des quatre écrans v4.

    python3 maquettes/planche_v4.py
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
S = 2
COLW, COLH = 1100, 735
GAP = 46
NOMS = [
    ("18_import", "1 · Importer un fichier",
     "déposer, voir ce qu'il contient, décider — sans jamais modifier l'original"),
    ("19_blocage", "2 · Un doublon, expliqué",
     "ce qui bloque, pourquoi, et trois sorties dont une recommandée"),
    ("20_coupe_finie", "3 · La coupe finie",
     "14 forages, lithologie et barres de teneur, échelle fixe, 4 réglages"),
    ("21_exclusions", "4 · Forages écartés",
     "une décision valable partout, motivée, réversible — et son journal"),
]
W = 2 * COLW + 3 * GAP
H = 2 * (COLH + 76) + 3 * GAP + 40


def police(taille, gras=False):
    fichier = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if gras
               else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(fichier, int(taille * S))


img = Image.new("RGB", (W * S, H * S), "#F0F1F3")
d = ImageDraw.Draw(img)
d.text((GAP * S, 34 * S), "DrillMaster — quatre écrans neufs", font=police(26, True),
       fill="#0B1220")
d.text((GAP * S, 68 * S),
       "import · blocage · coupe · exclusions — les chiffres viennent du projet "
       "Issia (64 forages, 3 180 analyses)", font=police(11.5), fill="#475467")

for i, (nom, titre, sous) in enumerate(NOMS):
    x = GAP + (i % 2) * (COLW + GAP)
    y = 110 + (i // 2) * (COLH + 76 + GAP)
    im = Image.open(os.path.join(OUT, nom + ".png")).convert("RGB")
    im = im.resize((COLW * S, int(COLH * S)), Image.LANCZOS)
    img.paste(im, (x * S, y * S))
    d.rectangle([x * S, y * S, (x + COLW) * S, (y + COLH) * S],
                outline="#D0D5DD", width=2 * S)
    d.text((x * S, (y + COLH + 14) * S), titre, font=police(13, True), fill="#0B1220")
    d.text((x * S, (y + COLH + 36) * S), sous, font=police(10), fill="#475467")

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "22_planche_v4.png"))
print("écrit maquettes/22_planche_v4.png")
