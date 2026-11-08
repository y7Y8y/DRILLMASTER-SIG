"""Planche 32 — la vitesse : ce qui tient dans une frame, et ce qu'on annonce.

    python3 maquettes/32_vitesse.py

Les temps viennent de `specs/data/vitesse.json`, mesurés sur le vrai calcul
de coupe par `tools/audit_vitesse.py`.
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
AUDIT = json.load(open(os.path.join(DONNEES, "vitesse.json"), encoding="utf-8"))
from drillmaster_v3.core.vitesse import (ECHELLES, experience,   # noqa: E402
                                         annonce)

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


txt(40, 28, "La vitesse, mesurée sur le vrai travail", 22, T["ink"], True)
txt(40, 60, "« 196 boucles » ne dit rien. Ce qui compte : combien de "
    "millisecondes pour dessiner la coupe que l'utilisateur regarde.",
    10.2, T["ink_2"])

# ══ 1 · le calcul de la coupe
y = 112
txt(40, y, "1 · Le calcul d'une coupe", 13, T["ink"], True)
txt(40, y + 22, f"{AUDIT['coupe']['forages']} forages · "
    f"{AUDIT['coupe']['analyses']} analyses · {AUDIT['coupe']['intercepts']} "
    "intercepts, sur le projet de référence.", 9.4, T["ink_2"])
y += 52

# la jauge : 16 ms = une frame
larg = 560
rect(40, y, larg, 26, T["surface_3"], T["border"], 6)
part = min(1.0, AUDIT["coupe"]["median_ms"] / 16.0)
rect(40, y, max(4, larg * part), 26, T["ok"], None, 6)
txt(40 + larg + 14, y + 5, f"{AUDIT['coupe']['median_ms']} ms", 12, T["ok"],
    True)
txt(40, y + 34, "médiane sur 7 essais · une frame à 60 images par seconde "
    "dure 16 ms", 8.4, T["ink_3"])
y += 70

mesures = [(str(AUDIT["boucles_imbriquees_total"]), "boucles imbriquées",
            "dans " + str(len(AUDIT["boucles_imbriquees"])) + " fichiers de vue",
            T["warn"]),
           (str(len(AUDIT["modules_qui_mesurent"])), "modules qui mesurent",
            "le temps est chronométré à sept endroits", T["ink_2"]),
           (str(len(AUDIT["modules_qui_publient"])), "qui le publient",
            "une mesure gardée pour soi n'existe pas (R-62)", T["block"])]
for val, quoi, note, col in mesures:
    rect(40, y, larg + 40, 52, T["surface"], T["border"], 9)
    rect(40, y, 4, 52, col, None, 0)
    txt(58, y + 9, quoi, 9.6, T["ink"], True)
    txt(58, y + 27, note, 8.2, T["ink_3"])
    txt(40 + larg + 24, y + 12, val, 17, col, True, "ra")
    y += 60

# ══ 2 · trois échelles, trois expériences
D = 700
y = 112
txt(D, y, "2 · Le même calcul, trois tailles de projet", 13, T["ink"], True)
txt(D, y + 22, "Et trois expériences différentes : on ne traite pas les trois "
    "de la même façon.", 9.4, T["ink_2"])
y += 52
for e in ECHELLES:
    col = T["ok"] if e.ms <= 16 else (T["warn"] if e.ms <= 100 else T["block"])
    rect(D, y, 860, 70, T["surface"], T["border"], 10)
    rect(D, y, 4, 70, col, None, 0)
    txt(D + 20, y + 12, f"{e.forages} forages", 10.4, T["ink"], True)
    txt(D + 20, y + 32, f"{e.analyses} analyses", 8.6, T["ink_3"])
    txt(D + 200, y + 14, f"{e.ms} ms", 13, col, True)
    txt(D + 300, y + 16, experience(e.ms), 9.4, T["ink_2"])
    ann = annonce(e.ms)
    if ann:
        txt(D + 20, y + 52, ann, 8.2, T["block"])
    elif e.ms <= 16:
        txt(D + 20, y + 52, "aucune annonce, aucune tâche de fond : "
            "plus court qu'une frame", 8.2, T["ink_3"])
    else:
        txt(D + 20, y + 52, "passe en tâche de fond ; l'écran reste "
            "utilisable, sans annonce", 8.2, T["warn"])
    y += 78

# ══ 3 · la règle
y += 6
rect(D, y, 860, 96, T["accent_soft"], T["accent_line"], 10)
txt(D + 18, y + 12, "R-62 · une mesure non publiée n'existe pas", 10.4,
    T["ink"], True)
txt(D + 18, y + 34, "R-63 · un travail long s'annonce avant de commencer",
    10.4, T["ink"], True)
txt(D + 18, y + 58, "Sept modules chronométraient le temps ; un seul le "
    "disait. Le module `vitesse` rend la mesure", 8.6, T["ink_2"])
txt(D + 18, y + 74, "visible et dicte le comportement : tâche de fond "
    "seulement au-delà d'une frame.", 8.6, T["ink_2"])

# ── pied
ligne(40, H - 44, 1560, H - 44)
txt(40, H - 34, "Temps mesurés par tools/audit_vitesse.py sur le vrai calcul "
    "de coupe · budget 16 ms (60 images par seconde).", 8.6, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "32_vitesse.png"))
print("écrit maquettes/32_vitesse.png")
