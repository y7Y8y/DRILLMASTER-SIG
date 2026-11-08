"""Planche : ce qu'un bouton annonce avant le clic.

    python3 maquettes/25_gestes.py
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
W, H = 1600, 830
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


txt(40, 30, "Ce qu'un bouton annonce", 22, T["ink"], True)
txt(40, 62, "Trois poids, un seul principal. Une action qui détruit dit ce "
    "qu'elle détruit — avant le clic.", 10.2, T["ink_2"])

# ══ les 3 rôles
y = 118
txt(40, y, "Les trois poids", 13, T["ink"], True)
y += 40
rect(40, y, 168, 34, T["accent"], None, 7)
txt(124, y + 10, "Importer", 10.4, "#FFFFFF", True, "ma")
txt(40, y + 44, "principal · l'action attendue", 8.6, T["ink_3"])

rect(236, y, 148, 34, T["surface"], T["border_strong"], 7)
txt(310, y + 10, "Comparer", 10.2, T["ink"], True, "ma")
txt(236, y + 44, "secondaire · une alternative", 8.6, T["ink_3"])

txt(412, y + 11, "Plus tard", 10.2, T["ink_2"])
txt(412, y + 44, "discret · sortir sans rien changer", 8.6, T["ink_3"])

rect(660, y, 44, 34, T["surface_3"], None, 7)
txt(682, y + 10, "…", 11, T["ink_3"], True, "ma")
txt(660, y + 44, "un seul principal par barre", 8.6, T["ink_3"])

# ══ l'annonce
y = 236
txt(40, y, "Une action ordinaire", 13, T["ink"], True)
y += 34
rect(40, y, 700, 68, T["surface"], T["border"], 8)
txt(58, y + 14, "Calculer la coupe", 10.6, T["ink"], True)
txt(58, y + 36, "La coupe affichée ; les réglages ne changent pas.", 9.2,
    T["ink_2"])

y += 92
txt(40, y, "Une action qui peut détruire", 13, T["ink"], True)
y += 34
rect(40, y, 700, 120, T["surface"], T["block"], 8, 1.4)
d.ellipse([(58) * S, (y + 16) * S, (70) * S, (y + 28) * S], fill=T["block"])
txt(80, y + 12, "Supprimer définitivement le projet", 10.6, T["ink"], True)
txt(80, y + 34, "Sera perdu :", 9.2, T["ink_2"], True)
for i, perte in enumerate(["les fichiers importés", "les coupes enregistrées",
                           "l'historique du projet"]):
    txt(94, y + 52 + i * 16, "· " + perte, 9, T["ink_2"])
txt(400, y + 34, "Sortie possible :", 9.2, T["ink_2"], True)
txt(400, y + 52, "· confirmer par écrit", 9, T["ink_2"])
txt(400, y + 68, "· choisir « fermer » pour conserver", 9, T["ink_2"])
txt(80, y + 98, "Le bouton est gris tant que la phrase n'est pas écrite.",
    8.8, T["ink_3"])

# ══ ce qui est refusé
x2 = 800
y2 = 118
txt(x2, y2, "Ce que le code refuse", 13, T["ink"], True)
y2 += 34
refus = [("Sans nom", "« demande qui agit : sans nom, personne ne peut "
          "expliquer ce qui s'est passé »"),
         ("Sans motif", "« demande un motif : dans six mois, quelqu'un se "
          "demandera pourquoi »"),
         ("Sans écrit", "« demande une confirmation écrite : c'est le seul "
          "moyen de distinguer un clic d'une décision »"),
         ("Destruction en principal", "« une action qui peut détruire n'est "
          "jamais le bouton principal »"),
         ("Deux principaux", "« l'utilisateur ne sait plus quelle est "
          "l'action attendue »"),
         ("« OK »", "« est un mot creux : un bouton dit ce qu'il fait »")]
for i, (titre, phrase) in enumerate(refus):
    yy = y2 + i * 64
    rect(x2, yy, 760, 56, T["surface"], T["border"], 8)
    d.line([(x2 * S, (yy + 28) * S), ((x2 + 12) * S, (yy + 28) * S)],
           fill=T["block"], width=int(1.8 * S))
    txt(x2 + 24, yy + 10, titre, 9.6, T["ink"], True)
    txt(x2 + 24, yy + 28, phrase, 8.4, T["ink_2"])

# ══ la séquence
SEQ_Y = 616
txt(40, SEQ_Y, "La séquence, dans l'ordre", 13, T["ink"], True)
etapes = [("1", "Le bouton annonce", "ce qui sera perdu, et la sortie"),
          ("2", "Le bouton attend", "gris tant que la phrase n'est pas écrite"),
          ("3", "L'action signe", "nom + motif, écrits dans le journal"),
          ("4", "Le résultat se voit", "aucun message de réussite : la "
           "liste a changé")]
for i, (num, titre, sous) in enumerate(etapes):
    y = SEQ_Y + 30
    x = 40 + i * 380
    rect(x, y, 360, 76, T["surface"], T["border"], 8)
    d.ellipse([(x + 16) * S, (y + 16) * S, (x + 40) * S, (y + 40) * S],
              fill=T["accent_soft"], outline=T["accent"], width=int(1.4 * S))
    txt(x + 28, y + 23, num, 10, T["accent"], True, "ma")
    txt(x + 52, y + 16, titre, 9.8, T["ink"], True)
    mots, ligne, yy = sous.split(), "", y + 38
    for mot in mots:
        essai = (ligne + " " + mot).strip()
        if f(8.6).getlength(essai) / S > 290:
            txt(x + 52, yy, ligne, 8.6, T["ink_2"])
            yy += 14
            ligne = mot
        else:
            ligne = essai
    txt(x + 52, yy, ligne, 8.6, T["ink_2"])

d.line([(40 * S, 780 * S), (1560 * S, 780 * S)], fill=T["border"], width=S)
txt(40, 792, "Les 4 « suppressions sans filet » signalées par la flotte "
    "n'en étaient pas : vérification faite, elles retirent des couches "
    "régénérables. Le vrai défaut était l'annonce.", 8.8, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "25_gestes.png"))
print("écrit maquettes/25_gestes.png")
