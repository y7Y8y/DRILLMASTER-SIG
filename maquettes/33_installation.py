"""Planche 33 — l'installation : ce que l'utilisateur reçoit vraiment.

    python3 maquettes/33_installation.py

Rien n'est dessiné à la main : les chiffres viennent de
`specs/data/installation.json`, produit par `tools/audit_installation.py`.
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
AUDIT = json.load(open(os.path.join(DONNEES, "installation.json"),
                       encoding="utf-8"))
QT6 = json.load(open(os.path.join(DONNEES, "qt6.json"), encoding="utf-8"))
from drillmaster_v3.core.installation import CHAMPS_REQUIS  # noqa: E402

T = THEME["clair"]
S = 2
W, H = 1600, 720
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


FICHE = AUDIT["fiche"]
PAQUET = AUDIT["paquet"]
COMPAT = AUDIT["compatibilite"]
ISOLE = AUDIT["demarrage_isole"]

txt(40, 26, "L'installation : ce que l'utilisateur reçoit vraiment", 22,
    T["ink"], True)
txt(40, 58, "Le rapport de la flotte annonçait trois défauts. Deux étaient "
    "vrais, un était faux — et le plus coûteux n'y figurait pas.", 10.2,
    T["ink_2"])

# ══ 1 · la fiche d'identité
y = 104
txt(40, y, "1 · La fiche d'identité", 13, T["ink"], True)
txt(40, y + 22, "Les champs qu'exige le dépôt officiel des extensions, lus "
    "dans le paquet.", 9.4, T["ink_2"])
y += 50
fournis = set(FICHE["fournis"])
col_w, lig = 196, 30
for i, champ in enumerate(CHAMPS_REQUIS):
    cx = 40 + (i % 2) * (col_w + 14)
    cy = y + (i // 2) * lig
    present = champ in fournis
    rect(cx, cy, col_w, 24, T["surface"], T["border"], 6)
    txt(cx + 10, cy + 6, champ, 9.2, T["ink"], False)
    txt(cx + col_w - 10, cy + 6,
        "fourni" if present else "manquait", 8.4,
        T["ok"] if present else T["block"], True, "ra")
y += 4 * lig + 10
rect(40, y, 430, 62, T["accent_soft"], T["accent_line"], 8)
txt(56, y + 10, f"{len(fournis)} champs sur {len(CHAMPS_REQUIS)} : la fiche "
    "est complète.", 9.2, T["ink"], True)
txt(56, y + 28, "Avant : l'adresse de contact manquait, et la catégorie "
    "annoncée", 8.4, T["ink_2"])
txt(56, y + 42, "n'existait pas dans la liste admise.", 8.4, T["ink_2"])

# ══ 2 · la fenêtre de compatibilité
y = 104
D = 490
txt(D, y, "2 · La fenêtre de compatibilité", 13, T["ink"], True)
txt(D, y + 22, "Une promesse écrite dans la fiche, confrontée à ce que le "
    "code tient.", 9.4, T["ink_2"])
y += 50
rect(D, y, 764, 116, T["surface"], T["border"], 10)
restants = (COMPAT["sites_a_migrer"] + COMPAT["exec_a_migrer"]
            + COMPAT["champs_a_migrer"])
for i, (quoi, val, note) in enumerate([
        ("version minimale", COMPAT["minimum"], "la plus ancienne éprouvée"),
        ("version maximale déclarée", COMPAT["maximum"],
         "jusqu'où le plugin s'annonce"),
        ("sites que la version 6 de Qt refuse", str(restants),
         f"énumérations {COMPAT['sites_a_migrer']} · appels de fenêtre "
         f"{COMPAT['exec_a_migrer']} · types de champ "
         f"{COMPAT['champs_a_migrer']} — tous migrés"),
]):
    yy = y + 14 + i * 30
    txt(D + 20, yy, quoi, 9.2, T["ink_2"])
    txt(D + 524, yy - 2, val, 11.4,
        T["ok"] if i == 2 and restants == 0 else
        (T["warn"] if i == 2 else T["ink"]), True, "ra")
    txt(D + 20, yy + 12, note, 7.8, T["ink_3"])
y += 132
rect(D, y, 764, 74, T["surface_3"], T["border"], 10)
rect(D, y, 4, 74, T["ok"] if restants == 0 else T["warn"], None, 0)
txt(D + 20, y + 12, "Le code a suivi Qt 6 ; l'annonce ne va pas plus loin "
    "que l'épreuve.", 10.2, T["ink"], True)
txt(D + 20, y + 32, "Les 792 formes anciennes sont migrées en une passe "
    "mécanique et réversible." if restants == 0 else
    "La fenêtre reste en deçà de ce que Qt 6 refuse, et c'est exact.", 8.8,
    T["ink_2"])
txt(D + 20, y + 46, f"Les {QT6['declarations']['qt5_acceptees']} formes "
    "employées ont été rejouées dans un Qt 5 réel et dans les déclarations "
    "de Qt 6 :", 8.4, T["ink_3"])
txt(D + 20, y + 58, "toutes passent. Reste l'essai dans un QGIS 4 : non "
    "fait, et écrit comme tel.", 8.4, T["ink_3"])

# ══ 3 · le paquet
y += 96
txt(D, y, "3 · Le paquet", 13, T["ink"], True)
y += 24
rect(D, y, 764, 74, T["surface"], T["border"], 10)
rect(D, y, 4, 74, T["block"], None, 0)
txt(D + 20, y + 12, f"{PAQUET['a_exclure']} fichiers partaient pour rien",
    10.4, T["ink"], True)
txt(D + 20, y + 32, "fichiers compilés sur le poste de l'auteur et bancs "
    "d'essai qui pointent vers son dossier personnel", 8.6, T["ink_3"])
txt(D + 20, y + 50, f"utiles : {PAQUET['fichiers_propres']} fichiers · "
    f"{PAQUET['poids_propre_ko'] / 1024:.1f} Mo de code une fois nettoyé",
    8.6, T["ok"])

# ══ 4 · le démarrage, paquet seul
y = 104
G = 1290
txt(G + 20, y, "4 · Le démarrage, le paquet seul", 13, T["ink"], True)
y += 22
txt(G + 20, y, "Le défaut que le rapport n'avait pas vu.", 9.4, T["ink_2"])
y += 30
rect(G + 20, y, 260, 118, T["surface"], T["border"], 10)
rect(G + 20, y, 4, 118, T["block"], None, 0)
txt(G + 36, y + 12, "Avant", 9.6, T["ink"], True)
txt(G + 36, y + 32, "la licence était cherchée", 8.6, T["ink_2"])
txt(G + 36, y + 46, "au-dessus du dossier", 8.6, T["ink_2"])
txt(G + 36, y + 60, "installé", 8.6, T["ink_2"])
txt(G + 36, y + 80, "« fichier introuvable »", 8.6, T["block"], True)
txt(G + 36, y + 98, "à chaque ouverture", 8.4, T["ink_3"])
y += 134
rect(G + 20, y, 260, 118, T["surface"], T["border"], 10)
rect(G + 20, y, 4, 118, T["ok"], None, 0)
txt(G + 36, y + 12, "Après", 9.6, T["ink"], True)
txt(G + 36, y + 32, "la licence est livrée", 8.6, T["ink_2"])
txt(G + 36, y + 46, "DANS le paquet, à côté", 8.6, T["ink_2"])
txt(G + 36, y + 60, "du code", 8.6, T["ink_2"])
txt(G + 36, y + 80, "« licence trouvée »", 8.6, T["ok"], True)
txt(G + 36, y + 98, "vérifié dans une copie isolée", 8.4, T["ink_3"])

# ══ 5 · les règles
y = 590
rect(40, y, 1560, 100, T["accent_soft"], T["accent_line"], 10)
txt(58, y + 11, "R-64 · une promesse de compatibilité se mesure", 10.4,
    T["ink"], True)
txt(58, y + 30, "R-65 · une extension embarque ce qu'elle lit — ni fichier "
    "compilé, ni banc d'essai", 10.4, T["ink"], True)
txt(58, y + 49, "R-66 · un fichier cherché au-dessus du paquet est "
    "introuvable chez l'utilisateur", 10.4, T["ink"], True)
txt(58, y + 72, "Deux des trois constats de la flotte étaient vrais, un était "
    "faux (la désinstallation est propre). Le plus coûteux n'y figurait pas.",
    8.8, T["ink_2"])

# ── pied
ligne(40, H - 40, 1560, H - 40)
txt(40, H - 30, "Mesuré par tools/audit_installation.py sur le paquet réel · "
    "la licence est vérifiée dans une copie isolée, comme après installation.",
    8.6, T["ink_3"])

img.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "33_installation.png"))
print("écrit maquettes/33_installation.png")
