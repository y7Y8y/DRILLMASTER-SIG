"""Planche 28 — les quatre écrans neufs, promesse par promesse.

    python3 maquettes/28_ecrans.py

Ce n'est pas une planche d'écran : c'est le **registre** des promesses.
Chaque ligne est une phrase montrée à l'utilisateur, et son état réel.
Les chiffres viennent de `tools/confronte_ecrans.py` et de la vraie lecture.
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(OUT)
sys.path.insert(0, RACINE)
THEME = json.load(open(os.path.join(RACINE, "specs", "data", "theme.json"),
                       encoding="utf-8"))
from drillmaster_v3.core.ecrans import ECRANS, fiche_source       # noqa: E402

T = THEME["clair"]
S = 2
W, H = 1600, 1090
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


def coupe(mots, largeur, taille=8.6):
    """Coupe un texte à la main : aucun chevauchement possible."""
    out, ligne_courante = [], ""
    for mot in mots.split():
        essai = (ligne_courante + " " + mot).strip()
        if d.textlength(essai, font=f(taille)) / S > largeur:
            out.append(ligne_courante)
            ligne_courante = mot
        else:
            ligne_courante = essai
    if ligne_courante:
        out.append(ligne_courante)
    return out


txt(40, 28, "Les écrans neufs, promesse par promesse", 22, T["ink"], True)
txt(40, 60, "Aucune promesse n'est cochée sans une preuve dans le code. "
    "Là où le code ne sait pas encore, c'est écrit : c'est un travail, pas un mensonge.",
    10.2, T["ink_2"])

# ── les chiffres, calculés par la vraie lecture d'un fichier réel
exemple = fiche_source("ISSIA_COLLAR.csv", texte=(
    "ID;X;Y;Z;PROF;DATE\n"
    "ISBRC001;512000,5;731800,2;219,8;110;2024-03-11\n"
    "ISBRC002;512024,1;731809,3;219,6;118;2024-03-12\n"
    "ISBRC002;512026,1;731811,3;219,2;118;2024-03-12\n"))

y = 106
bande = [("chiffres lus sur un fichier réel", str(exemple.forages), "forages"),
         ("colonnes reconnues", f"{exemple.colonnes_reconnues}/{exemple.colonnes}", ""),
         ("identifiants en double", str(len(exemple.doublons)), "à décider"),
         ("types de données absents", str(len(exemple.types_absents)), "dits absents")]
x = 40
for titre, val, note in bande:
    rect(x, y, 372, 62, T["surface"], T["border"], 10)
    txt(x + 16, y + 12, titre, 8.6, T["ink_3"], True)
    txt(x + 16, y + 34, val, 17, T["ink"], True)
    if note:
        txt(x + 16 + d.textlength(val, font=f(17, True)) / S + 8, y + 42, note,
            8.4, T["ink_3"])
    x += 380

# ── le registre
y = 196
tenues = sum(len(e.tenues()) for e in ECRANS)
total = sum(len(e.promesses) for e in ECRANS)
txt(40, y, "Le registre", 13, T["ink"], True)
txt(40 + 120, y + 2, f"{tenues} tenues · {total - tenues} à faire · {total} promesses",
    9.4, T["ink_2"])
y += 26
ligne(40, y, 1560, y, T["border_strong"])
y += 10

for e in ECRANS:
    txt(44, y + 2, f"{e.numero}", 11, T["accent"], True)
    txt(76, y + 2, e.nom, 11, T["ink"], True)
    txt(240, y + 4, e.maquette, 8.4, T["ink_3"])
    y += 22
    for p in e.promesses:
        if p.etat == "tenu":
            marque, col = "tenu", T["ok"]
        elif p.etat == "bloque":
            marque, col = "bloqué", T["warn"]
        else:
            marque, col = "à faire", T["block"]
        rect(76, y - 1, 52, 14, None, col, 7)
        txt(102, y + 1, marque, 7.4, col, True, "ma")
        txt(142, y, p.phrase[:96], 8.8, T["ink"] if p.etat == "tenu" else T["ink_2"])
        y += 15
        if p.etat != "tenu":
            for morceau in coupe("reste — " + p.preuve, 1240):
                txt(152, y, morceau, 7.8, T["ink_3"])
                y += 12
        y += 3
    y += 8

# ── la règle
rect(40, H - 134, 1520, 74, T["accent_soft"], T["accent_line"], 10)
txt(60, H - 118, "R-55 · Une maquette promet, un cas réel prouve", 10.6,
    T["ink"], True)
txt(60, H - 98, "Chaque phrase montrée à l'utilisateur est une entrée de "
    "registre avec sa preuve, ou son état « à faire ». Un écran ne peut pas "
    "afficher une promesse que rien ne tient.", 8.8, T["ink_2"])

ligne(40, H - 44, 1560, H - 44)
txt(40, H - 34, "Registre lu dans drillmaster_v3/core/ecrans/promesses.py — "
    "le même que celui que les tests vérifient.", 8.6, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "28_ecrans.png"))
print("écrit maquettes/28_ecrans.png")
