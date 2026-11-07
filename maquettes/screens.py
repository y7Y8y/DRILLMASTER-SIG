"""Les 8 écrans de DRILLMASTER — maquettes haute fidélité.

Chaque écran est une image autonome, jugeable seule.
    python3 maquettes/screens.py
"""
from __future__ import annotations

import math
import os
import random

from ui import C, Dark, Tokens

W, H = 1600, 1000
OUT = os.path.dirname(os.path.abspath(__file__))

LITHO = {"LAT": "#C99A5B", "SAP": "#E0B56B", "SPR": "#8FA85A",
         "MTZ": "#5E8C4A", "PEG": "#E86A5E", "QTZ": "#E8E1C8", "MIS": "#9B79E3",
         "GRA": "#B58463", "SDS": "#A9A9A9"}
TEN = ("#7B61FF", "#3B8BEA", "#1FA97A", "#F5B335", "#E8623D")


# ══════════════════════════════════════════════════════════════════════
# 4 · COUPE 2D — l'écran le plus important du logiciel
# ══════════════════════════════════════════════════════════════════════
def coupe_2d(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Coupe 2D", dark_btn=dark)
    PX, PY, PW = 16, 70, 330          # panneau propriétés
    SX = PX + PW + 16                  # scène
    SW = W - SX - 16
    SH = H - 70 - 28 - 46              # hauteur scène

    # ── panneau gauche : le contrat de piste, unifié
    c.r(PX, PY, PW, H - PY - 40, fill=t.surface, stroke=t.border, rx=10)
    c.txt(PX + 16, PY + 20, "Propriétés de la coupe", size=12.5, bold=True)
    c.txt(PX + 16, PY + 36, "Issia · coupe 004", size=9.8)

    y = PY + 54
    # coupe active
    c.section_label(PX + 16, y, "Coupe active")
    c.r(PX + 12, y + 8, PW - 24, 30, fill=t.surface_2, stroke=t.border, rx=6)
    c.txt(PX + 24, y + 19, "Coupe 004 — N045° · 195 m", size=10.3, bold=True)
    c.txt(PX + 24 - PW + 20, y + 19, "▾", size=9)
    y += 46

    # inclusion
    c.section_label(PX + 16, y, "Inclusion")
    y += 10
    c.txt(PX + 16, y + 10, "14 forages inclus", size=10.3, bold=True)
    c.txt(PX + PW - 16, y + 10, "2 exclus", size=9.5, bold=True, anchor="rs")
    c.slider(PX + 16, y + 20, PW - 90, 0.42, "50 m")
    y += 52

    # PISTES — vue d'ensemble : c'est la réponse au problème
    c.l(PX, y, PX + PW, y, fill=t.border)
    c.section_label(PX + 16, y + 16, "Pistes — vue d'ensemble")
    c.txt(PX + PW - 16, y + 16, "10", size=9, bold=True, anchor="rs")
    y += 26
    rows = [
        ("Profondeurs", "●", t.ink_3, True, "12"),
        ("Trajectoire", "●", "#344054", True, "—"),
        ("Lithologie", "●", "#8FA85A", True, "6"),
        ("Teneurs", "●", "#3B8BEA", True, "Au"),
        ("Intercepts", "○", "#00E5FF", False, "—"),
        ("Altérations", "●", "#D9C6E8", True, "4"),
        ("Minéralisations", "●", "#5D6D7E", True, "3"),
        ("Structures", "●", "#B54708", True, "212"),
        ("Imagerie", "●", "#7F56D9", True, "18"),
        ("RQD", "●", t.ok, True, "88"),
        ("Récupération", "○", t.warn, False, "—"),
        ("Densité", "○", "#7F56D9", False, "—"),
    ]
    for i, (name, mark, col, on, val) in enumerate(rows):
        ry = y + i * 22
        if i == 2:
            c.r(PX + 8, ry - 4, PW - 16, 22, fill=t.accent_soft, rx=5)
            c.r(PX + 8, ry - 4, 3, 22, fill=t.accent)
        c.txt(PX + 18, ry + 8, mark, size=8)
        c.c(PX + 32, ry + 5, 0.1, col)
        c.txt(PX + 34, ry + 8, name, size=10)
        c.txt(PX + PW - 60, ry + 8, val, size=9, bold=False, anchor="rs")
        # largeur éditable directement dans le tableau (le contrat)
        if on:
            c.r(PX + PW - 54, ry + 1, 38, 9, fill=t.surface_3, rx=4)
            wfrac = 0.25 + (i % 5) * 0.16
            c.r(PX + PW - 54, ry + 1, 38 * wfrac, 9, fill=t.accent_line, rx=4)
    y += len(rows) * 22 + 8

    c.txt(PX + 16, y + 8, "Largeur · opacité · côté — sur chaque ligne", size=8.8)
    y += 26
    c.l(PX, y, PX + PW, y, fill=t.border)
    # replis
    for lbl, n in (("Cadre & axes", ""), ("Topographie", ""), ("Légendes", "6"),
                   ("Historique", "12 coupes")):
        y += 26
        c.txt(PX + 18, y, "▸", size=8.5)
        c.txt(PX + 32, y, lbl, size=10.2)
        if n:
            c.txt(PX + PW - 16, y, n, size=9, bold=False, anchor="rs")

    # ── scène de coupe
    c.r(SX, PY, SW, SH, fill=t.surface, stroke=t.border, rx=10)
    # barre d'outils de la scène
    c.txt(SX + 18, PY + 22, "Coupe 004", size=12.5, bold=True)
    c.chip(SX + 18 + c.tw("Coupe 004", 12.5, True) + 10, PY + 10, "N045°", "info")
    c.chip(SX + 18 + c.tw("Coupe 004", 12.5, True) + 66, PY + 10, "1:1000", "info")
    bx = SX + SW - 300
    c.segmented(bx, PY + 10, ["Ajuster", "Échelle fixe"], 1)
    c.button(bx + 190, PY + 9, "Exporter", primary=True, w=82)
    c.l(SX, PY + 46, SX + SW, PY + 46)

    # zone de dessin
    gx, gy = SX + 74, PY + 82
    gw, gh = SW - 130, SH - 200
    rnd = random.Random(11)

    # grille
    for i in range(0, 11):
        xx = gx + gw * i / 10
        c.l(xx, gy, xx, gy + gh, fill=t.border, w=0.7, dash=(3, 4))
        c.txt(xx, gy + gh + 16, f"{i*20}", size=8.5)
    for j in range(0, 12):
        yy = gy + gh * j / 11
        c.l(gx, yy, gx + gw, yy, fill=t.border, w=0.7, dash=(3, 4))
        c.txt(gx - 12, yy + 3, f"{420 - j*20}", size=8.5)

    # ligne de sol (MNT) + forages
    holes = 11
    tops = []
    for k in range(holes):
        fx = gx + gw * (0.045 + 0.91 * k / (holes - 1))
        surf = 12 + math.sin(k * 0.9) * 9
        ty = gy + surf
        tops.append((fx, ty))
    # ruban de surface
    c.path([(x, y) for x, y in tops], stroke="#B9C4B6", w=2.4)

    for k, (fx, ty) in enumerate(tops):
        depth = gh * (0.42 + 0.35 * rnd.random())
        lean = rnd.uniform(-8, 8)
        bx_ = fx + lean
        by_ = ty + depth
        # trajectoire
        c.l(fx, ty, bx_, by_, fill="#344054", w=1.4)
        c.c(fx, ty - 3, 3.2, "#101828")
        c.txt(fx, ty - 10, f"ISB{k+1:03d}", size=7.5, bold=False, anchor="ms")
        # lithologie : bande continue à GAUCHE du trou
        segs = 7
        for j in range(segs):
            a, b = j / segs, (j + 1) / segs
            c.l(fx + lean * a - 11, ty + depth * a, fx + lean * b - 11,
                ty + depth * b,
                fill=LITHO[rnd.choice(list(LITHO))], w=11)
        # teneurs : piste à DROITE, barres proportionnelles à la valeur
        c.l(fx + 4, ty, fx + 4, ty + depth, fill=t.border, w=1)
        for j in range(7):
            a = 0.1 + 0.72 * j / 6
            val = rnd.random() ** 1.6
            c.r(fx + 5, ty + depth * a, 3 + val * 20, 8.5,
                fill=TEN[j % len(TEN)], rx=1)
        # altérations : fine bande pastel
        for j in range(4):
            a = 0.2 + 0.6 * j / 3
            c.r(fx + lean * a - 19, ty + depth * a - 6, 8, 12,
                fill="#D9C6E8", rx=1)
        # structures : symboles
        for j in range(3):
            a = 0.3 + 0.4 * j / 2
            sy_ = ty + depth * a
            c.l(fx + lean * a - 26, sy_ - 3, fx + lean * a - 20, sy_ + 3,
                fill="#B54708", w=1.6)

    # règle de profondeur à gauche de chaque trou (graduations)
    c.l(gx - 32, gy, gx - 32, gy + gh, fill=t.border_strong, w=0.8)
    for j in range(0, 12):
        yy = gy + gh * j / 11
        c.l(gx - 36, yy, gx - 28, yy, fill=t.ink_3, w=0.8)

    # légende flottante en bas
    ly = PY + SH - 44
    c.l(SX, ly - 10, SX + SW, ly - 10, fill=t.border)
    codes = [("LAT", LITHO["LAT"]), ("SAP", LITHO["SAP"]), ("SPR", LITHO["SPR"]),
             ("MTZ", LITHO["MTZ"]), ("PEG", LITHO["PEG"])]
    lx = SX + 18
    for code, col in codes:
        c.r(lx, ly + 2, 12, 12, fill=col, rx=2)
        c.txt(lx + 17, ly + 12, code, size=9)
        lx += 17 + c.tw(code, 9) + 16
    c.l(lx + 6, ly, lx + 6, ly + 18, fill=t.border)
    lx += 18
    c.chip(lx, ly + 2, "Teneurs Au ppm", "info")
    c.chip(lx + 108, ly + 2, "4 règles de seuil", "quest")

    c.status_bar("Coupe 004 · 14 forages · 1 248 intervalles · 96 ms", "À jour")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 1 · PROJET
# ══════════════════════════════════════════════════════════════════════
def projet(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Projet", dark_btn=dark)
    c.page_title(24, 82, "Projet Issia",
                 "Créé le 12/09/2026 · modifié il y a 2 h · 64 forages · UTM 29N (EPSG:32629)")

    y = 136
    # ── identité + référentiel
    c.panel(24, y, 760, 236, "Identité du projet")
    c.field(44, y + 66, 344, "Nom du projet", "Projet Issia")
    c.field(408, y + 66, 344, "Auteur", "Yann Bonful")
    c.field(44, y + 132, 344, "Dossier", "~/QGIS/DrillMaster/Issia")
    c.field(408, y + 132, 344, "Convention de pendage", "Négatif vers le bas (−90°)")
    c.txt(44, y + 208, "6 fichiers sources · 12 types reconnus · 0 donnée modifiée",
          size=9.5, fill=t.ink_3)

    c.panel(804, y, W - 828, 236, "Référentiel spatial")
    c.field(824, y + 66, 344, "SCR du projet", "EPSG:32629 — UTM 29N")
    c.field(1188, y + 66, 344, "Unités de profondeur", "Mètres (m)")
    c.txt(824, y + 140, "MNT source", size=9.4, fill=t.ink_3, bold=True)
    c.r(824, y + 149, 708, 30, fill=t.surface_2, stroke=t.border, rx=6)
    c.txt(835, y + 161, "Copernicus DEM 30 m — EPSG:4326 reprojeté à la volée",
          size=10.3, fill=t.ink)
    c.chip(824, y + 192, "Conversion vérifiée", "ok")

    # ── bibliothèques / profils / santé
    y = 392
    c.panel(24, y, 490, 268, "Bibliothèques", "Jamais réécrites — suggestions seulement")
    libs = [("Lithologie", "30 familles · 212 codes utilisés", "#8FA85A"),
            ("Altération", "27 familles · 96 codes utilisés", "#D9C6E8"),
            ("Minéraux", "18 symboles · 42 minéraux cités", "#5D6D7E")]
    for i, (name, n, col) in enumerate(libs):
        ry = y + 72 + i * 60
        c.r(40, ry, 458, 50, fill=t.surface_2, stroke=t.border, rx=8)
        c.c(60, ry + 25, 6, col)
        c.txt(76, ry + 15, name, size=11, fill=t.ink, bold=True)
        c.txt(76, ry + 31, n, size=9.2, fill=t.ink_3)
        c.txt(482, ry + 29, "Ouvrir →", size=9.2, fill=t.accent, bold=True, anchor="rs")

    c.panel(530, y, 490, 268, "Profils d'affichage", "Par type d'ouvrage")
    profs = [("RC / DD", "Échelle réelle", True), ("AUGER", "0–15 m agrandi", False),
             ("PUITS", "0–5 m agrandi", False), ("CUSTOM", "Facteur 3,0", False)]
    for i, (name, desc, actif) in enumerate(profs):
        ry = y + 72 + i * 46
        c.r(546, ry, 458, 40,
            fill=t.accent_soft if actif else t.surface_2,
            stroke=t.accent_line if actif else t.border, rx=8)
        c.txt(562, ry + 13, name, size=10.5, fill=t.ink, bold=True)
        c.txt(562, ry + 27, desc, size=9, fill=t.ink_3)
        c.txt(988, ry + 21, "Actif" if actif else "Configurer", size=9,
              fill=t.accent, bold=True, anchor="rs")

    c.panel(1044, y, W - 1068, 268, "Santé du projet", "Ce qui bloque, ce qui manque")
    stats = [("Collets", "64", "ok", ""), ("Déviations", "61 / 64", "warn", "3 sans mesure"),
             ("Lithologie", "2 410", "ok", ""), ("Teneurs", "3 180", "ok", ""),
             ("Géotechnique", "absent", "block", "3 pistes vides"), ("Imagerie", "18", "ok", "")]
    for i, (k, v, kind, note) in enumerate(stats):
        ry = y + 72 + i * 31
        c.dot(1068, ry + 4, kind)
        c.txt(1082, ry + 8, k, size=10, fill=t.ink)
        c.txt(W - 44, ry + 8, v, size=10, fill=t.ink, bold=True, anchor="rs")
        if note:
            c.txt(1082 + c.tw(k, 10) + 10, ry + 8, note, size=8.4, fill=t.ink_3)

    # ── bas de page : dernières coupes + notes
    y = 684
    c.panel(24, y, 900, 268, "Dernières coupes", "3 sur 12")
    rows = [("Coupe 004", "N045°", "195 m", "14 forages", "1:1000", "il y a 18 min"),
            ("Coupe 003", "N135°", "224 m", "11 forages", "1:1000", "hier 16:12"),
            ("Coupe 002", "N090°", "258 m", "17 forages", "1:2000", "12/09/2026")]
    cx = 44
    for hd, ww in (("Nom", 200), ("Orientation", 140), ("Longueur", 120),
                   ("Forages", 140), ("Échelle", 120), ("Dernier calcul", 180)):
        c.txt(cx, y + 78, hd, size=9, fill=t.ink_3, bold=True)
        cx += ww
    c.l(24, y + 88, 924, y + 88, fill=t.border)
    for i, r in enumerate(rows):
        ry = y + 92 + i * 40
        if i % 2 == 1:
            c.r(24, ry, 900, 40, fill=t.surface_2)
        cx = 44
        for j, (val, ww) in enumerate(zip(r, (200, 140, 120, 140, 120, 180))):
            c.txt(cx, ry + 16, val, size=10, fill=t.ink if j == 0 else t.ink_2,
                  bold=(j == 0))
            cx += ww
        c.l(24, ry + 40, 924, ry + 40, fill=t.border)

    c.panel(940, y, W - 964, 268, "Notes du projet")
    notes = ["Passer la géotechnique sur les 12 forages du secteur Est",
             "Vérifier le pendage de ISBRC006 (azimut constant)",
             "Valider la palette d'altération avant le rendu final"]
    for i, n in enumerate(notes):
        ry = y + 74 + i * 46
        c.r(956, ry + 4, 5, 5, fill=t.warn, rx=2.5)
        # retour à la ligne manuel
        words, line, lines = n.split(), "", []
        for wd in words:
            if c.tw(line + " " + wd, 9.8) > 260:
                lines.append(line); line = wd
            else:
                line = (line + " " + wd).strip()
        lines.append(line)
        for k, ln in enumerate(lines):
            c.txt(972, ry + 4 + k * 15, ln, size=9.8, fill=t.ink_2)
    c.txt(956, y + 230, "+ Ajouter une note", size=9.5, fill=t.accent, bold=True)

    c.status_bar("Projet Issia · enregistré automatiquement", "Sain")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 2 · DONNÉES — les 5 niveaux d'état
# ══════════════════════════════════════════════════════════════════════
def donnees(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Données", dark_btn=dark)
    c.page_title(24, 82, "Données",
                 "12 types de sources · 6 fichiers importés · 87 contrôles · 2 blocages")
    x, y = 24, 132

    # filtres par niveau
    c.segmented(x, y, ["Tout 87", "Blocages 2", "Questions 1", "Attention 5",
                       "Info 79"], 0)
    c.txt(x + 470, y + 8, "Trier par", size=9.3)
    c.segmented(x + 546, y, ["Sévérité", "Type", "Fichier"], 0)

    # sources (colonne gauche)
    c.panel(x, y + 40, 430, 560, "Sources", "12 types · 6 fournis")
    srcs = [("Collets", "ISSIA_COLLAR.csv", 64, "ok", "3 218 int."),
            ("Déviations", "ISSIA_SURVEY.csv", 61, "warn", "1 288 int."),
            ("Lithologie", "ISSIA_LITHO.csv", 64, "ok", "2 410 int."),
            ("Teneurs", "ISSIA_ASSAY.csv", 64, "ok", "3 180 int."),
            ("Altérations", "ISSIA_ALT.csv", 64, "ok", "1 902 int."),
            ("Minéralisations", "ISSIA_MIN.csv", 64, "ok", "742 pts"),
            ("Structures", "ISSIA_STRUCT.csv", 64, "ok", "212 mes."),
            ("Imagerie", "ISSIA_IMG.csv", 64, "ok", "18 pho."),
            ("RQD", "—", 0, "block", ""),
            ("Récupération", "—", 0, "block", ""),
            ("Densité", "—", 0, "block", ""),
            ("Topographie", "DEM_Copernicus.tif", 0, "ok", "1 raster")]
    for i, (name, fichier, n, kind, rows) in enumerate(srcs):
        ry = y + 100 + i * 37
        if i == 2:
            c.r(x + 8, ry - 7, 414, 37, fill=t.accent_soft, rx=6)
            c.r(x + 8, ry - 7, 3, 37, fill=t.accent)
        c.dot(x + 22, ry + 7, kind)
        c.txt(x + 34, ry + 5, name, size=10.3, bold=True)
        c.clip_text(x + 34, ry + 19, fichier, 240, 8.8, t.ink_3)
        if rows:
            c.txt(x + 412, ry + 19, rows, size=8.6, fill=t.ink_3, anchor="rs")
        if n:
            c.txt(x + 412, ry + 6, f"{n}", size=9.5, bold=True, anchor="rs")

    # liste des messages (colonne centrale)
    c.panel(x + 450, y + 40, 660, 560, "Contrôles",
            "Chaque message dit pourquoi et comment résoudre")
    msgs = [
        ("block", "2 forages dupliqués", "Données · Collets", "lignes 45, 88", 2),
        ("block", "RQD et récupération absents", "Géotechnique", "3 pistes vides", 0),
        ("warn", "3 forages sans déviation", "Données · Déviations", "ISBRC003, 011, 027", 3),
        ("quest", "Cellule à 2 codes litho", "Données · Lithologie", "ligne 412 · LAT;SAP", 1),
        ("warn", "Teneur non numérique", "Données · Teneurs", "ligne 9031 · « nd »", 1),
        ("info", "62 lignes lues", "Données · Structures", "aucune anomalie", 0),
    ]
    ry = y + 102
    for i, (kind, title, where, detail, n) in enumerate(msgs):
        sel = i == 0
        hgt = 74
        if sel:
            c.r(x + 462, ry, 636, hgt - 8, fill=t.surface_2, rx=8)
            c.r(x + 462, ry, 3, hgt - 8, fill={"block": t.block, "warn": t.warn,
                                               "quest": t.quest, "info": t.info}[kind])
        c.dot(x + 486, ry + 18, kind)
        c.txt(x + 500, ry + 22, title, size=11, bold=True)
        if n:
            c.chip(x + 1040, ry + 8, str(n), kind)
        c.txt(x + 500, ry + 40, where, size=9.2)
        c.txt(x + 500, ry + 55, detail, size=9.2)
        if not sel:
            c.l(x + 462, ry + hgt - 6, x + 1098, ry + hgt - 6, fill=t.border)
        ry += hgt

    # détail du message sélectionné (colonne droite)
    dx = x + 1130
    dw = W - dx - 24
    c.panel(dx, y + 40, dw, 560, None)
    c.chip(dx + 16, y + 58, "BLOCAGE", "block", solid=True)
    c.txt(dx + 16, y + 96, "2 forages dupliqués", size=14, bold=True)
    c.txt(dx + 16, y + 120, "Données · Collets", size=9.5)
    c.l(dx + 16, y + 134, dx + dw - 16, y + 134, fill=t.border)

    blocks = [("POURQUOI",
               "Deux collets portent le même identifiant. La trajectoire, les\n"
               "intervalles et les teneurs de l'un seraient rattachés à l'autre :\n"
               "la coupe afficherait un forage fusionné, faux en profondeur."),
              ("CONCERNÉ", "ISBRC045 — ligne 45\nISBRC088 — ligne 88"),
              ("RÉSOUDRE",
               "1. Corriger l'identifiant dans le CSV source\n"
               "2. ou exclure l'un des deux forages du projet"),
              ("SI VOUS IGNOREZ",
               "Le blocage reste actif : la géométrie, la coupe et la 3D\n"
               "resteront indisponibles pour ces 2 forages. Rien n'est\n"
               "supprimé, rien n'est deviné.")]
    yy = y + 158
    for label, body in blocks:
        c.txt(dx + 16, yy + 8, label, size=8.8, bold=True, fill=t.ink_3, anchor="ls")
        yy += 26
        for line in body.split("\n"):
            c.txt(dx + 16, yy + 10, line, size=9.8, fill=t.ink_2, anchor="ls")
            yy += 17
        yy += 22
    c.button(dx + 16, y + 500, "Ouvrir la ligne 45", primary=True)
    c.button(dx + 16 + 140, y + 500, "Voir les 2 forages")
    c.button(dx + 16, y + 536, "Ignorer avec motif…")

    # journal
    c.panel(x, y + 616, W - 48, 138, "Journal des imports")
    cols = ["Quand", "Type", "Fichier", "Lignes", "Résultat", "Par"]
    widths = [150, 130, 380, 90, 300, 160]
    row = {"cells": ["il y a 2 h", "Collets", "ISSIA_COLLAR.csv", "64",
                     "2 blocages", "Y. Bonful"],
           "swatch": None}
    c.table(x + 16, y + 676, W - 80, cols, widths, [row],
            row_h=30, head_h=24, size=9.5)

    c.status_bar("87 contrôles · 2 blocages empêchent la géométrie", "2 blocages",
                 t.block)
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 3 · GÉOMÉTRIE
# ══════════════════════════════════════════════════════════════════════
def geometrie(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Géométrie", dark_btn=dark)
    c.page_title(24, 82, "Géométrie",
                 "64 trajectoires · méthode angle moyen · pas d'échantillonnage 1 m")

    # réglages
    y = 132
    c.panel(24, y, 400, 330, "Calcul")
    c.section_label(44, y + 62, "Méthode de calcul")
    c.segmented(44, y + 78, ["Angle moyen", "Minimum curvature"], 0)
    c.txt(44, y + 118, "Pas d'échantillonnage", size=10, fill=t.ink_2)
    c.slider(44, y + 132, 300, 0.3, "1,0 m")
    c.txt(44, y + 158, "Subdivision max par segment", size=10, fill=t.ink_2)
    c.slider(44, y + 172, 300, 0.5, "10 m")
    for i, (lbl, on) in enumerate((("Forcer les verticaux sans déviation", True),
                                   ("Recalculer au changement de CRS", True),
                                   ("Conserver le cache JSON", True))):
        ry = y + 198 + i * 26
        c.checkbox(44, ry, on, size=14)
        c.txt(68, ry + 11, lbl, size=10, fill=t.ink)
    c.button(44, y + 284, "Recalculer les 64 trajectoires", primary=True)

    # cache
    c.panel(440, y, 400, 155, "Cache")
    c.txt(460, y + 68, "Signature des entrées", size=9.5)
    c.r(460, y + 78, 360, 26, fill=t.surface_2, stroke=t.border, rx=6)
    c.txt(472, y + 87, "a7f3c9…e21b  ·  validée", size=9.8, fill="#475467")
    c.chip(460, y + 114, "Cache à jour", "ok")
    c.txt(580, y + 124, "dernier calcul il y a 2 h", size=9)

    # contrôles
    c.panel(856, y, W - 880, 330, "Contrôles de trajectoire")
    checks = [("Aucune dérive > 5 %", "ok", "64 / 64"),
              ("Forages sans déviation", "warn", "3"),
              ("Points hors collet", "ok", "0"),
              ("Dépassement de profondeur", "ok", "0"),
              ("Azimut constant suspect", "warn", "2")]
    for i, (lbl, kind, val) in enumerate(checks):
        ry = y + 68 + i * 40
        c.dot(880, ry + 6, kind)
        c.txt(896, ry + 10, lbl, size=10.3)
        c.txt(W - 44, ry + 10, val, size=10, bold=True, anchor="rs")
    c.button(880, y + 280, "Voir les 5 forages concernés")

    # tableau des forages
    y = 482
    c.panel(24, y, W - 48, 458, "Trajectoires",
            "64 forages · la colonne « état » explique chaque écart")
    cols = ["", "Forage", "X", "Y", "Z", "Prof.", "Az", "Dip", "Pts", "État"]
    widths = [34, 150, 120, 120, 100, 90, 80, 80, 80, 300]
    rows = []
    data = [("ISBRC001", 512340.2, 731880.4, 218.4, 120.0, 110, -55, 121, "ok", ""),
            ("ISBRC002", 512365.9, 731902.1, 221.0, 98.5, 110, -55, 99, "ok", ""),
            ("ISBRC003", 512402.7, 731930.8, 219.6, 84.0, 110, -90, 85,
             "warn", "Sans déviation · vertical supposé"),
            ("ISBRC004", 512431.5, 731955.2, 217.2, 150.0, 110, -60, 151, "ok", ""),
            ("ISBRC005", 512468.3, 731988.9, 215.8, 132.4, 110, -58, 133, "ok", ""),
            ("ISBRC006", 512501.1, 732014.6, 214.0, 61.0, 110, -50, 62,
             "warn", "Azimut identique sur 40 m"),
            ("ISBRC007", 512540.8, 732042.3, 212.5, 175.0, 110, -62, 176, "ok", ""),
            ("ISBRC008", 512579.4, 732070.1, 211.0, 90.0, 110, -55, 91, "ok", ""),
            ("ISBRC009", 512611.2, 732098.6, 209.8, 118.0, 111, -57, 119, "ok", ""),
            ("ISBRC010", 512648.0, 732126.4, 208.4, 96.5, 111, -56, 97, "ok", ""),
            ("ISBRC011", 512684.7, 732154.2, 207.1, 142.0, 111, -61, 143, "ok", ""),
            ("ISBRC012", 512721.3, 732182.9, 205.9, 88.0, 111, -90, 88,
             "warn", "Sans déviation · vertical supposé")]
    for d in data:
        rows.append({"cells": ["", d[0], f"{d[1]:.0f}", f"{d[2]:.0f}",
                               f"{d[3]:.1f}", f"{d[4]:.1f}", f"{d[5]}",
                               f"{d[6]}", f"{d[8]}", d[9]],
                     "bold": True, "dim": d[8] != "ok" and False})
    rr = y + 62
    for d in data:
        pass
    # dessin manuel pour placer les pastilles d'état
    c.r(24 + 16, rr, W - 48 - 32, 26, fill=t.surface_2)
    cx = 40
    for hd, ww in zip(cols, widths):
        c.txt(cx + 8, rr + 17, hd, size=9, bold=True)
        cx += ww
    c.l(40, rr + 26, W - 40, rr + 26, fill=t.border)
    for i, d in enumerate(data):
        ry = rr + 26 + i * 30
        if i % 2 == 1:
            c.r(40, ry, W - 80, 30, fill=t.surface_2)
        c.l(40, ry + 30, W - 40, ry + 30, fill=t.border)
        cx = 40
        c.dot(cx + 16, ry + 14, d[8])
        cx += widths[0]
        for val, ww in zip([d[0], f"{d[1]:.0f}", f"{d[2]:.0f}", f"{d[3]:.1f}",
                            f"{d[4]:.1f}", str(d[5]), str(d[6]), str(d[7])],
                           widths[1:9]):
            c.txt(cx + 8, ry + 19, val, size=9.8)
            cx += ww
        if d[9]:
            c.chip(cx + 8, ry + 5, "Attention", "warn")
            c.txt(cx + 8 + c.tw("Attention", 8.8, True) + 36, ry + 19, d[9], size=9,
                  fill=t.ink_2)
        else:
            c.txt(cx + 8, ry + 19, "Trajectoire valide", size=9, fill=t.ink_2)

    c.status_bar("64 trajectoires · 64 valides avec 3 réserves · dernier calcul 96 ms",
                 "Prêt")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 5 · VUE 3D
# ══════════════════════════════════════════════════════════════════════
def vue_3d(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Vue 3D", dark_btn=dark)
    SX, SY, SW = 16, 70, W - 16 - 300 - 16
    SH = H - 70 - 28 - 40
    c.r(SX, SY, SW, SH, fill=t.surface, stroke=t.border, rx=10)

    # scène
    x0, y0, w, h = SX + 1, SY + 46, SW - 2, SH - 47
    c.r(x0, y0, w, h, fill="#FBFCFD" if not dark else "#12151B")
    cx = x0 + w * .5
    horizon = y0 + h * .22
    for i in range(-8, 9):
        c.l(cx + i * (w / 40), horizon, cx + i * (w / 12), y0 + h, fill=t.border, w=.8)
    for i in range(1, 9):
        tt = (i / 8) ** 1.9
        c.l(x0, horizon + (y0 + h - horizon) * tt, x0 + w,
            horizon + (y0 + h - horizon) * tt, fill=t.border, w=.8)

    top, bot = [], []
    for i in range(61):
        tt = i / 60
        xx = x0 + w * tt
        ridge = math.sin(tt * 7.1 + .8) * 10 + math.sin(tt * 2.3) * 16
        yy = horizon - 34 + ridge
        top.append((xx, yy))
        bot.append((xx, yy + 26))
    c.poly(top + bot[::-1], fill="#E8EDE6" if not dark else "#1B2620")
    c.path(top, stroke="#C9D3C6" if not dark else "#2E4436", w=1.4)

    rnd = random.Random(7)
    for k in range(24):
        tt = k / 23
        xt = x0 + w * (.06 + .88 * tt) + rnd.uniform(-4, 4)
        tx = (xt - x0) / w
        ridge = math.sin(tx * 7.1 + .8) * 10 + math.sin(tx * 2.3) * 16
        yt = horizon - 34 + ridge + 4
        dep = rnd.uniform(.55, 1.0) * (h * .5)
        lean = rnd.uniform(-14, 14)
        c.l(xt, yt, xt + lean, yt + dep, fill="#344054" if not dark else "#8A94A6", w=1.5)
        for j in range(8):
            a, b = j / 8, (j + 1) / 8
            c.l(xt + lean * a, yt + dep * a, xt + lean * b, yt + dep * b,
                fill=LITHO[rnd.choice(list(LITHO))], w=5)
        for j in range(4):
            a = .2 + .6 * (j / 3)
            c.c(xt + lean * a + 7, yt + dep * a, rnd.uniform(4.5, 8.5),
                TEN[j % len(TEN)])
        c.c(xt, yt - 5, 3.2, "#101828" if not dark else "#E7EAEE")

    # corridor
    bx0 = x0 + w * .32
    bw = w * .15
    c.poly([(bx0, horizon - 60), (bx0 + bw, horizon - 60),
            (bx0 + bw * 1.1, y0 + h - 10), (bx0 - bw * .1, y0 + h - 10)],
           fill=(46, 91, 255, 16))
    c.l(bx0, horizon - 60, bx0 - bw * .1, y0 + h - 10, fill=(90, 122, 255, 120),
        w=1, dash=(5, 5))
    c.l(bx0 + bw, horizon - 60, bx0 + bw * 1.1, y0 + h - 10,
        fill=(90, 122, 255, 120), w=1, dash=(5, 5))

    # barre caméra
    labels = [("Perspective", 1), ("Plan", 0), ("Face N", 0), ("Face E", 0)]
    ws = [c.tw(l, 10.5, True) + 16 for l, _ in labels]
    total = sum(ws) + 8
    bx = x0 + w - total - 20
    c.r(bx, y0 + 14, total, 30, fill=t.surface, stroke=t.border, rx=8)
    xx = bx + 4
    for (lab, actif), wd in zip(labels, ws):
        if actif:
            c.r(xx, y0 + 18, wd, 22, fill=t.accent_soft, rx=5)
        c.txt(xx + wd / 2, y0 + 24, lab, size=10.5, anchor="ms")
        xx += wd
    c.r(x0 + 16, y0 + h - 42, 118, 26, fill=t.surface, stroke=t.border, rx=8)
    c.txt(x0 + 28, y0 + h - 25, "Exag. Z  ×1.5", size=10)

    gx, gy = x0 + w - 54, y0 + h - 52
    c.c(gx, gy, 25, t.surface, t.border)
    c.l(gx, gy, gx, gy - 19, fill=t.block, w=2)
    c.l(gx, gy, gx + 18, gy, fill=t.warn, w=2)
    c.txt(gx, gy - 27, "N", size=8.5, bold=True, anchor="ms")
    c.txt(gx + 24, gy + 3, "E", size=8.5, bold=True, anchor="ms")

    # barre de statut de la scène
    c.r(SX, SY, SW, 46, fill=t.surface, rx=10)
    c.txt(SX + 18, SY + 22, "Vue 3D", size=12.5, bold=True)
    c.txt(SX + 78, SY + 22, "64 forages · 2 410 segments · 12 ms", size=9.8)
    c.dot(SX + SW - 96, SY + 23, "ok")
    c.txt(SX + SW - 88, SY + 27, "Temps réel", size=9.5, fill=t.ink_2, bold=True)
    c.l(SX, SY + 46, SX + SW, SY + 46)

    # ── panneau de calques
    PX = W - 300 - 16
    c.panel(PX, SY, 300, SH, "Calques")
    c.txt(PX + 16, SY + 32, "4 domaines restent en 2D", size=8.8)
    yy = SY + 64
    groups = [
        ("Forages", [("Collets", True, "#101828", 0), ("Trajectoire", True, "#344054", 0),
                     ("Étiquettes", False, None, 1), ("Profondeurs", False, None, 1),
                     ("Déviations", True, None, 1)]),
        ("Géologie", [("Lithologie", True, "#8FA85A", 0), ("Altération", True, "#D9C6E8", 0),
                      ("Minéralisation", True, "#5D6D7E", 0), ("Structures", True, "#B54708", 0),
                      ("Imagerie", False, "#7F56D9", 0), ("Surface (MNT)", True, "#C9D3C6", 0)]),
        ("Analyses", [("Teneurs", True, "#3B8BEA", 0), ("Au ppm", True, None, 1),
                      ("Cu ppm", False, None, 1), ("Intercepts", True, "#00E5FF", 0),
                      ("RQD", True, t.ok, 0), ("Récupération", False, t.warn, 0),
                      ("Densité", False, "#7F56D9", 0)]),
    ]
    for gname, items in groups:
        c.txt(PX + 14, yy, "▾", size=8.5)
        c.txt(PX + 26, yy, gname.upper(), size=8.6, bold=True)
        yy += 14
        for name, on, col, ind in items:
            rh = 24
            if on:
                c.r(PX + 8, yy + 2, 284, rh - 2,
                    fill=t.accent_soft if dark else "#F7F9FF", rx=5)
            bx_ = PX + 16 + ind * 14
            c.checkbox(bx_, yy + 6, on, 13)
            tx = bx_ + 20
            if col:
                c.c(tx + 4, yy + 13, 4, col)
                tx += 14
            c.txt(tx, yy + 8, name, size=10.3 if not ind else 10,
                  fill=t.ink if on else t.ink_3, bold=not ind)
            yy += rh
        yy += 6
    c.l(PX, SY + SH - 44, PX + 300, SY + SH - 44)
    c.txt(PX + 16, SY + SH - 26, "Actualiser", size=10, bold=True)
    c.txt(PX + 284, SY + SH - 26, "Ctrl+R", size=9, bold=False, anchor="rs")

    c.status_bar("Vue 3D · 12 ms · qualité complète", "Prêt")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 6 · ANALYSES
# ══════════════════════════════════════════════════════════════════════
def analyses(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Analyses", dark_btn=dark)
    c.page_title(24, 82, "Analyses",
                 "Structures · intercepts · statistiques · contrôles qualité")
    c.segmented(24, 132, ["Structures", "Intercepts", "Statistiques", "Qualité"], 0)

    y = 176
    # rose des directions
    c.panel(24, y, 470, 470, "Rose des directions",
            "212 mesures · pendage > 30° · classes de 10°")
    cx, cy, rad = 24 + 235, y + 236, 138
    c.c(cx, cy, rad + 12, t.surface_2, t.border)
    for k in range(36):
        a = math.radians(k * 10 - 90)
        ln = 8 if k % 3 else 13
        c.l(cx + math.cos(a) * rad, cy + math.sin(a) * rad,
            cx + math.cos(a) * (rad + ln), cy + math.sin(a) * (rad + ln),
            fill=t.border_strong, w=1)
    rnd = random.Random(3)
    for k in range(36):
        a = math.radians(k * 10 - 90)
        r0 = rad * (0.15 + rnd.random() * 0.55)
        c.poly([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a + math.radians(10)) * r0,
                 cy + math.sin(a + math.radians(10)) * r0),
                (cx, cy)], fill="#2E5BFF22")
    for k in range(36):
        a0 = math.radians(k * 10 - 90)
        a1 = math.radians((k + 1) * 10 - 90)
        rr = 18 + (math.sin(k * .7) + 1) * 34 + rnd.random() * 26
        col = "#2E5BFF" if rr > 60 else "#8FA8FF"
        c.poly([(cx, cy), (cx + math.cos(a0) * rr, cy + math.sin(a0) * rr),
                (cx + math.cos(a1) * rr, cy + math.sin(a1) * rr)],
               fill=col, stroke=t.surface, w=0.6)
    c.txt(cx, cy - rad - 26, "N", size=9, bold=True, anchor="ms")
    c.txt(cx + rad + 26, cy + 3, "E", size=9, bold=True, anchor="ms")
    c.txt(cx, cy + rad + 34, "S", size=9, bold=True, anchor="ms")
    c.txt(cx - rad - 26, cy + 3, "O", size=9, bold=True, anchor="ms")
    c.txt(24 + 20, y + 448, "Direction dominante N045° · 38 % des mesures", size=9.5, fill=t.ink_2)
    c.txt(24 + 470 - 20, y + 448, "3 filtres actifs", size=9, bold=True, fill=t.accent, anchor="rs")

    # stéréonet
    c.panel(510, y, 470, 470, "Stéréonet (Schmidt)",
            "Hémisphère inférieur · densité de pôles")
    sx, sy, sr = 510 + 235, y + 250, 150
    c.c(sx, sy, sr, t.surface_2, t.border)
    c.c(sx, sy, sr * .5, None, t.border)
    c.l(sx - sr, sy, sx + sr, sy, fill=t.border, dash=(4, 4))
    c.l(sx, sy - sr, sx, sy + sr, fill=t.border, dash=(4, 4))
    from PIL import ImageDraw as _ID  # dégradé de densité simulé
    for i in range(220):
        a = rnd.random() * math.tau
        rr = (rnd.random() ** .6) * sr * .92
        px_, py_ = sx + math.cos(a) * rr, sy + math.sin(a) * rr
        v = max(0.0, 1 - rr / (sr * .95))
        col = (int(46 + 200 * v), int(60 + 90 * (1 - v)), int(255 - 180 * v))
        c.c(px_, py_, 2.6, col)
    c.txt(510 + 20, y + 430, "1 284 pôles · maximum 12,4 %", size=9.5)

    # à droite : intercepts + statistiques
    c.panel(1004, y, W - 1028, 220, "Intercepts", "4 règles de seuil actives")
    rules = [("Au > 1,0 ppm", "#00E5FF", 12), ("Au > 5,0 ppm", "#FF00D4", 4),
             ("Li > 500 ppm", "#FFB300", 7), ("Au+Cu cumulé", "#7F56D9", 2)]
    for i, (lbl, col, n) in enumerate(rules):
        ry = y + 62 + i * 38
        c.r(1020, ry, W - 1060, 32, fill=t.surface_2, stroke=t.border, rx=6)
        c.r(1020, ry, 3, 32, fill=col)
        c.txt(1036, ry + 20, lbl, size=10)
        c.chip(W - 76 - (c.tw(str(n), 8.8, True) + 16), ry + 8, f"{n}", "info")

    c.panel(1004, y + 240, W - 1028, 230, "Statistiques de teneurs",
            "Au · 3 180 analyses")
    stats = [("Minimum", "0,002"), ("Médiane", "0,41"), ("Moyenne", "1,28"),
             ("90ᵉ centile", "3,9"), ("Maximum", "24,7"), ("Valeurs « nd »", "12")]
    for i, (k, v) in enumerate(stats):
        rx = 1020 + (i % 3) * 190
        ry = y + 300 + (i // 3) * 56
        c.txt(rx, ry, k, size=9.2)
        c.txt(rx, ry + 20, v, size=16, bold=True)

    # ── histogramme des teneurs (l'analyse qui manquait)
    hy = y + 468
    c.panel(24, hy, W - 48, 300, "Distribution des teneurs — Au",
            "3 180 analyses · échelle log · seuils de coupure superposés")
    gx, gy, gw, gh = 96, hy + 92, W - 200, 132
    rnd2 = random.Random(11)
    # loi log-normale : la forme réelle d'une distribution de teneurs
    bars = [math.exp(-((i - 12.5) ** 2) / (2 * 5.2 ** 2)) *
            (0.55 + rnd2.random() * 0.45) for i in range(28)]
    mx = max(bars)
    for i, v in enumerate(bars):
        bh = max(2.0, gh * v / mx)
        bx = gx + i * (gw / 28)
        c.r(bx + 3, gy + gh - bh, gw / 28 - 6, bh,
            fill=t.accent if i >= 16 else t.accent_line, rx=2)
    # axes
    c.l(gx, gy + gh, gx + gw, gy + gh, fill=t.border_strong, w=1)
    for k, lbl in enumerate(["0,01", "0,1", "1", "10", "100"]):
        ax_ = gx + gw * k / 4
        c.l(ax_, gy + gh, ax_, gy + gh + 5, fill=t.border_strong, w=1)
        c.txt(ax_, gy + gh + 19, lbl, size=8.6, fill=t.ink_3, anchor="ms")
    c.txt(gx + gw / 2, gy + gh + 40, "Teneur Au (ppm, échelle log)", size=9, fill=t.ink_3, anchor="ms")
    c.txt(gx - 14, gy + gh - 4, "Nb", size=8.6, fill=t.ink_3, anchor="rs")
    # seuils
    for frac, lbl, col in ((0.34, "0,1 ppm", t.ink_3), (0.58, "1 ppm", t.warn),
                           (0.74, "5 ppm", t.block)):
        sx = gx + gw * frac
        c.l(sx, gy, sx, gy + gh, fill=col, w=1.2, dash=(4, 4))
        c.txt(sx + 5, gy + 12, lbl, size=8.4, fill=col, bold=True)
    c.txt(W - 44, hy + 74, "25 intercepts au-dessus de 1 ppm", size=9.2,
          fill=t.ink_2, anchor="rs")

    c.status_bar("212 mesures · 1 284 pôles · 25 intercepts", "Prêt")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 7 · RÉFÉRENTIEL
# ══════════════════════════════════════════════════════════════════════
def referentiel(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("", dark_btn=dark)
    c.page_title(24, 82, "Référentiel",
                 "Projet › Référentiel · libellés, couleurs et symboles — "
                 "les données sources ne sont jamais modifiées")
    c.segmented(24, 124, ["Lithologie 30", "Altération 27", "Minéralisations 18",
                          "Structures 12", "Teneurs 3"], 0)

    x, y = 24, 168
    # barre de recherche + actions
    c.r(x, y, 420, 30, fill=t.surface, stroke=t.border_strong, rx=7)
    c.txt(x + 12, y + 19, "Rechercher un code ou une famille…", size=10)
    c.button(x + 436, y, "Assigner les couleurs auto", w=None)
    c.button(x + 620, y, "Importer un CSV", w=None)
    c.button(W - 24 - 120, y, "Enregistrer", primary=True, w=120)

    # table
    ty = y + 46
    c.panel(x, ty, W - 48, 546, None)
    cols = ["", "Code", "Famille", "Libellé", "Motif", "Utilisé"]
    widths = [44, 130, 260, 400, 200, 140]
    c.r(x + 1, ty + 1, W - 50, 30, fill=t.surface_2, rx=10)
    cx = x + 16
    for hd, ww in zip(cols, widths):
        c.txt(cx + 6, ty + 20, hd, size=9.2, bold=True)
        cx += ww
    c.l(x, ty + 31, x + W - 48, ty + 31)
    data = [("#8FA85A", "SPR", "Saprolite", "Saprolite", "diagonal", "1 284 m"),
            ("#C99A5B", "LAT", "Latérite", "Latérite", "dots_moyen", "860 m"),
            ("#E0B56B", "SAP", "Saprolite altéré", "Saprolite altéré", "dots_fin", "642 m"),
            ("#5E8C4A", "MTZ", "Métasédiment", "Métasédiment", "horizontal", "398 m"),
            ("#E86A5E", "PEG", "Pegmatite", "Pegmatite", "cross", "210 m"),
            ("#9B79E3", "MIS", "Micaschiste", "Micaschiste", "diagonal_cross", "142 m"),
            ("#E8E1C8", "QTZ", "Quartz", "Quartz", "", "88 m"),
            ("#B58463", "GRA", "Granite", "Granite", "dots", "54 m"),
            ("#A9A9A9", "SDS", "Non défini", "Non défini", "", "12 m"),
            ("#7FA8C9", "GRS", "Grès", "Grès", "horizontal", "—"),
            ("#8C7A6B", "SCH", "Schiste", "Schiste", "diagonal", "—"),
            ("#C4A484", "ALU", "Altérite", "Altérite", "dots_fin", "—")]
    for i, (col, code, fam, lib, motif, used) in enumerate(data):
        ry = ty + 32 + i * 40
        if i == 1:
            c.r(x + 2, ry, W - 52, 40, fill=t.accent_soft)
            c.r(x + 2, ry, 3, 40, fill=t.accent)
        c.r(x + 26, ry + 11, 18, 18, fill=col, rx=4)
        c.txt(x + 16 + 44 + 6, ry + 25, code, size=10.2, bold=True)
        c.txt(x + 16 + 174 + 6, ry + 25, fam, size=10)
        c.txt(x + 16 + 434 + 6, ry + 25, lib, size=10)
        mx = x + 16 + 834 + 6
        if motif:
            for d in range(3):
                c.l(mx + d * 5, ry + 26, mx + 14 + d * 5, ry + 12, fill=col, w=1.3)
            c.txt(mx + 50, ry + 25, motif, size=9)
        else:
            c.txt(mx, ry + 25, "aplat", size=9)
        c.txt(W - 40, ry + 25, used, size=9.2, bold=False, anchor="rs")
        c.l(x, ry + 40, x + W - 48, ry + 40, fill=t.border)

    # détail / aperçu en bas
    by = ty + 566
    c.panel(x, by, 700, 150, "Aperçu sur la coupe", "Rendu réel des 6 codes les plus utilisés")
    bx = x + 20
    for i, (col, code, *_rest) in enumerate(data[:6]):
        c.r(bx + i * 76, by + 50, 62, 52, fill=col, rx=3)
        for d in range(4):
            c.l(bx + i * 76 + 5 + d * 15, by + 100, bx + i * 76 + 30 + d * 15,
                by + 54, fill="#00000033", w=1.4)
        c.txt(bx + i * 76 + 31, by + 122, code, size=8.8, bold=True,
              fill=t.ink_2, anchor="ms")
    c.panel(x + 716, by, W - 48 - 716, 150, "Règles de gamme",
            "Vérifiées à chaque modification")
    rules = ["Lithologie : aplats vifs · ΔE2000 ≥ 12 entre familles voisines",
             "Altération : pastels · aucun code hexadécimal partagé avec la lithologie",
             "Aucune couleur ne doit dépendre du thème clair ou sombre",
             "Les motifs restent lisibles en niveaux de gris (impression)"]
    for i, r_ in enumerate(rules):
        c.dot(x + 738, by + 62 + i * 22, "ok")
        c.txt(x + 752, by + 60 + i * 22, r_, size=9.4, fill=t.ink_2)

    c.status_bar("Référentiel du projet · 30 familles · aucune donnée source modifiée",
                 "Enregistré")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 8 · EXPORT
# ══════════════════════════════════════════════════════════════════════
def export(path, dark=False):
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Export", dark_btn=dark)
    c.page_title(24, 82, "Export",
                 "Profils d'export réutilisables · aperçu avant production")

    x, y = 24, 132
    # profils
    c.panel(x, y, 340, 356, "Profils", None)
    profs = [("Coupe · A1 paysage", "1:1000 · PDF vectoriel", True),
             ("Coupe · A3 ajustée", "PNG 300 dpi", False),
             ("Planche de plan", "A0 · cartouche complet", False),
             ("Capture 3D", "PNG 4K", False)]
    for i, (name, desc, actif) in enumerate(profs):
        ry = y + 62 + i * 58
        c.r(x + 12, ry, 316, 50,
            fill=t.accent_soft if actif else t.surface_2,
            stroke=t.accent_line if actif else t.border, rx=8)
        c.txt(x + 26, ry + 20, name, size=10.5, bold=True)
        c.txt(x + 26, ry + 35, desc, size=9.2)
        if actif:
            c.dot(x + 310, ry + 25, "ok")
    c.button(x + 12, y + 356 - 52, "Nouveau profil", w=316)

    # réglages
    c.panel(x + 356, y, 400, 356, "Réglages")
    c.txt(x + 376, y + 62, "Format", size=9.4, fill=t.ink_3, bold=True)
    c.segmented(x + 376, y + 74, ["PDF", "PNG", "SVG"], 0)
    c.txt(x + 376, y + 112, "Papier", size=9.4, fill=t.ink_3, bold=True)
    c.segmented(x + 376, y + 124, ["A4", "A3", "A2", "A1", "A0"], 3)
    c.txt(x + 376, y + 162, "Échelle", size=9.4, fill=t.ink_3, bold=True)
    c.segmented(x + 376, y + 174, ["Ajustée", "Fixe 1:N"], 1)
    c.txt(x + 376, y + 212, "Résolution", size=9.4, fill=t.ink_3, bold=True)
    c.slider(x + 376, y + 230, 260, 0.66, "300 dpi")
    c.txt(x + 376, y + 252, "Police, cartouche et légende hérités du profil",
          size=8.8, fill=t.ink_3)
    c.button(x + 376, y + 356 - 52, "Produire le PDF", primary=True)

    # aperçu
    c.panel(x + 772, y, W - 24 - x - 772, 356, "Aperçu")
    ax, ay = x + 792, y + 64
    aw, ah = W - 24 - x - 772 - 40, 256
    c.r(ax, ay, aw, ah, fill="#FFFFFF", stroke=t.border_strong, rx=2)
    # coupe en miniature
    for k in range(9):
        fx = ax + 30 + (aw - 60) * k / 8
        c.l(fx, ay + 52, fx + 4, ay + 200, fill="#344054", w=1)
        for j in range(6):
            c.l(fx, ay + 52 + j * 25, fx + 4, ay + 77 + j * 25,
                fill=LITHO[list(LITHO)[j]], w=4)
    c.l(ax + 20, ay + 50, ax + aw - 20, ay + 50, fill="#B9C4B6", w=1.6)
    c.r(ax + 12, ay + 12, aw - 24, 58, fill="#00000008")
    c.txt(ax + 20, ay + 26, "COUPE 004 — N045°", size=8.5, bold=True)
    c.txt(ax + 20, ay + 40, "Projet Issia · 1:1000", size=7.5)
    c.r(ax + aw - 90, ay + 14, 74, 26, fill=t.surface, stroke=t.border, rx=3)
    c.txt(ax + aw - 53, ay + 30, "1:1000", size=7, bold=True, anchor="ms")
    c.txt(ax + 20, ay + ah - 12, "A1 · 841 × 594 mm · 300 dpi · 9 933 × 7 016 px", size=8.2)

    # historique
    y2 = 512
    c.panel(x, y2, W - 48, 420, "Exports récents", None)
    cols = ["", "Fichier", "Profil", "Format", "Taille", "Quand", "Action"]
    widths = [40, 420, 300, 150, 140, 220, 200]
    c.r(x + 1, y2 + 1, W - 50, 30, fill=t.surface_2, rx=10)
    cx = x + 16
    for hd, ww in zip(cols, widths):
        c.txt(cx + 6, y2 + 20, hd, size=9.2, bold=True)
        cx += ww
    c.l(x, y2 + 31, x + W - 48, y2 + 31)
    hist = [("ok", "Issia_coupe_004_A1.pdf", "Coupe · A1 paysage", "PDF", "8,4 Mo",
             "il y a 12 min"),
            ("ok", "Issia_coupe_003_A3.png", "Coupe · A3 ajustée", "PNG", "24,1 Mo",
             "hier 16:40"),
            ("block", "Issia_planche_A0.pdf", "Planche de plan", "PDF", "—",
             "échec · papier indisponible")]
    for i, (kind, f, profil, fmt, size, when) in enumerate(hist):
        ry = y2 + 32 + i * 44
        if i % 2 == 1:
            c.r(x, ry, W - 48, 44, fill=t.surface_2)
        c.dot(x + 26, ry + 22, kind)
        c.txt(x + 56, ry + 26, f, size=10, bold=True)
        c.txt(x + 16 + 40 + 420 + 6, ry + 26, profil, size=9.8)
        c.txt(x + 16 + 40 + 420 + 300 + 6, ry + 26, fmt, size=9.8)
        c.txt(x + 16 + 40 + 420 + 300 + 150 + 6, ry + 26, size, size=9.8)
        c.txt(x + 16 + 40 + 420 + 300 + 150 + 140 + 6, ry + 26, when, size=9.5)
        c.txt(W - 60, ry + 26, "Ouvrir" if kind == "ok" else "Voir l'erreur", size=9.5, bold=True, anchor="rs")
        c.l(x, ry + 44, x + W - 48, ry + 44, fill=t.border)

    c.status_bar("Profil « Coupe · A1 paysage » · prêt", "Prêt")
    return c.save(path)


# ══════════════════════════════════════════════════════════════════════
# 9 · ÉCRANS 1-2-3 (le mode Guidé, adapté)
# ══════════════════════════════════════════════════════════════════════
def guide(path, dark=False):
    """Le mode Guidé : 3 étapes de mise en route, puis on travaille."""
    T = Dark if dark else Tokens
    t = T
    c = C(W, H, T)
    c.app_bar("Données", dark_btn=dark)

    # bandeau d'étapes (pas un stepper à bulles : une barre de progression sémantique)
    y = 74
    c.r(0, y, W, 58, fill=t.surface)
    c.l(0, y + 58, W, y + 58, fill=t.border)
    steps = [("1", "Projet", "ok", "Créé"),
             ("2", "Données", "block", "2 blocages"),
             ("3", "Géométrie", "off", "En attente"),
             ("4", "Coupe", "off", "En attente")]
    x = 24
    for i, (num, name, kind, state) in enumerate(steps):
        actif = i == 1
        wd = 190
        if actif:
            c.r(x, y + 10, wd, 38, fill=t.accent_soft, rx=8)
        col = {"ok": t.ok, "block": t.block, "off": t.ink_3}[kind]
        c.c(x + 22, y + 29, 12, t.surface if not actif else t.surface, col, 1.6)
        if kind == "ok":
            c.path([(x + 17, y + 29), (x + 20.5, y + 32.5), (x + 27, y + 25)],
                   stroke=t.ok, w=1.8)
        else:
            c.txt(x + 22, y + 25, num, size=9.5, bold=True, anchor="ms")
        c.txt(x + 42, y + 26, name, size=10.8, bold=True)
        c.txt(x + 42, y + 39, state, size=8.8)
        if i < 3:
            c.l(x + wd + 6, y + 29, x + wd + 30, y + 29, fill=t.border, w=1.4)
        x += wd + 36

    c.button(W - 24 - 172, y + 14, "Passer en mode expert", w=172, size=9.8)

    # contenu : la liste de contrôle de l'étape 2
    c.page_title(24, 158, "Étape 2 · Données",
                 "Déposez vos fichiers — DrillMaster reconnaît le type de chacun")
    # zone de dépôt
    c.r(24, 216, 520, 250, fill=t.surface, stroke=t.border_strong, rx=10,
        sw=1.2, dash=(6, 5))
    c.txt(284, 300, "Déposer un dossier ou des fichiers CSV", size=11.5, bold=True, anchor="ms")
    c.txt(284, 320, "Collets · déviations · lithologie · teneurs · altérations ·", size=9.5, bold=False, anchor="ms")
    c.txt(284, 334, "minéralisations · structures · imagerie · RQD · récup. · densité", size=9.5, bold=False, anchor="ms")
    c.button(284 - 70, 356, "Parcourir…", primary=True, w=140)

    # checklist des 12 types
    c.panel(564, 216, W - 588, 480, "Couverture des 12 types",
            "Un type non fourni est une information, pas une erreur")
    types = [("Collets", "ok", "64 lignes"), ("Déviations", "warn", "61 / 64 forages"),
             ("Lithologie", "ok", "2 410 intervalles"), ("Teneurs", "ok", "3 180 analyses"),
             ("Altérations", "ok", "1 902 intervalles"), ("Minéralisations", "ok", "742"),
             ("Structures", "ok", "212 mesures"), ("Imagerie", "ok", "18 photos"),
             ("RQD", "block", "non fourni"), ("Récupération", "block", "non fourni"),
             ("Densité", "block", "non fourni"), ("Topographie", "ok", "raster 30 m")]
    for i, (name, kind, detail) in enumerate(types):
        col_i, row_i = i % 3, i // 3
        rx = 584 + col_i * ((W - 588 - 40) / 3)
        ry = 286 + row_i * 100
        c.r(rx, ry, (W - 588 - 40) / 3 - 16, 84, fill=t.surface_2,
            stroke=t.border, rx=8)
        c.dot(rx + 16, ry + 20, kind)
        c.txt(rx + 28, ry + 24, name, size=10.3, bold=True)
        c.txt(rx + 16, ry + 44, detail, size=9.2)
        if kind == "block":
            c.txt(rx + 16, ry + 64, "Ajouter…", size=9, bold=True)
        elif kind == "warn":
            c.txt(rx + 16, ry + 64, "Voir les 3 forages", size=9, bold=True)

    # ── ce que fait DrillMaster de vos fichiers (rassure sans jargon)
    gy = 492
    c.panel(24, gy, 520, 236, "Ce que DrillMaster fait de vos fichiers",
            "Rien n'est modifié dans les fichiers d'origine")
    gestes = [("ok", "Lit et reconnaît le type", "12 types · par nom de colonne et contenu"),
              ("ok", "Contrôle chaque ligne", "87 contrôles · identifiants, bornes, unités"),
              ("warn", "Signale sans corriger", "2 blocages, 1 question, 5 avertissements"),
              ("quest", "Vous laisse décider", "corriger à la source, exclure, ou ignorer avec motif")]
    for i, (kind, titre, detail) in enumerate(gestes):
        ry = gy + 66 + i * 42
        c.dot(44, ry + 5, kind)
        c.txt(60, ry, titre, size=10.2, bold=True)
        c.txt(60, ry + 15, detail, size=9, fill=t.ink_3)

    # ── ce qui bloque l'étape 3
    by = 744
    c.r(564, by, W - 588, 120, fill=t.surface, stroke=t.block_line
        if hasattr(t, "block_line") else t.border, rx=10)
    c.r(564, by, 3, 120, fill=t.block, rx=0)
    c.txt(586, by + 22, "Ce qui bloque l'étape 3 — Géométrie", size=11.5, bold=True)
    bloc = ["2 forages dupliqués (ISBRC045, ISBRC088) : la trajectoire serait ambiguë",
            "RQD et récupération absents : 3 pistes resteront vides en coupe",
            "Densité absente : les colonnes de teneur ne peuvent pas être pondérées"]
    for i, b_ in enumerate(bloc):
        c.dot(590, by + 48 + i * 21, "block" if i == 0 else "warn")
        c.txt(604, by + 43 + i * 21, b_, size=9.6, fill=t.ink_2)
    c.button(W - 24 - 200, by + 44, "Voir les 2 forages", w=200)

    c.status_bar("2 blocages empêchent l'étape 3 · 4 types absents", "À compléter", t.block)
    return c.save(path)


SCREENS = {
    "01_projet": projet,
    "02_donnees": donnees,
    "03_geometrie": geometrie,
    "04_coupe_2d": coupe_2d,
    "05_vue_3d": vue_3d,
    "06_analyses": analyses,
    "07_referentiel": referentiel,
    "08_export": export,
    "09_guide": guide,
}


if __name__ == "__main__":
    for name, fn in SCREENS.items():
        p = fn(os.path.join(OUT, f"{name}.png"))
        print("écrit", os.path.basename(p))
    p = coupe_2d(os.path.join(OUT, "04_coupe_2d_sombre.png"), dark=True)
    print("écrit", os.path.basename(p))
    p = vue_3d(os.path.join(OUT, "05_vue_3d_sombre.png"), dark=True)
    print("écrit", os.path.basename(p))
