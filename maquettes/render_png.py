"""Rendu PNG de la maquette 3D — Pillow (aucune dépendance système).

Dessine la même direction artistique que m3d_vue_et_panneau.py, mais en
rastérisation directe : le PNG est garanti, sur n'importe quelle machine.
Super-échantillonnage ×2 pour un tracé net.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFont

S = 2  # super-échantillonnage
W, H = 1600, 980
PANEL = 300

FOND = "#F6F7F9"
SURFACE = "#FFFFFF"
BORDURE = "#E4E7EC"
BORDURE_FORTE = "#D0D5DD"
TEXTE = "#101828"
TEXTE_MOYEN = "#475467"
TEXTE_FAIBLE = "#98A2B3"
ACCENT = "#2E5BFF"
SEM_INFO, SEM_ATT, SEM_BLOC, SEM_OK = "#667085", "#F79009", "#D92D20", "#12B76A"
ACCENT_CLAIR = "#EEF2FF"
LIGNE_ACTIVE = "#F7F9FF"

LITHO = {"LAT": "#C99A5B", "SAP": "#E0B56B", "SPR": "#8FA85A",
         "MTZ": "#5E8C4A", "PEG": "#E86A5E", "QTZ": "#E8E1C8", "MIS": "#9B79E3"}
TENEUR = ("#7B61FF", "#3B8BEA", "#1FA97A", "#F5B335", "#E8623D")

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, int(size * S))


class Canvas:
    def __init__(self, w, h, bg):
        self.img = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def r(self, x, y, w, h, fill=None, stroke=None, sw=1, rx=0):
        box = [x * S, y * S, (x + w) * S, (y + h) * S]
        if rx:
            self.d.rounded_rectangle(box, radius=rx * S, fill=fill,
                                     outline=stroke, width=max(1, int(sw * S)))
        else:
            self.d.rectangle(box, fill=fill, outline=stroke,
                             width=max(1, int(sw * S)))

    def l(self, x1, y1, x2, y2, fill=BORDURE, w=1, dash=None):
        if not dash:
            self.d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=fill,
                        width=max(1, int(w * S)))
        else:
            ln = math.hypot(x2 - x1, y2 - y1)
            steps = max(1, int(ln / (dash[0] + dash[1])))
            for i in range(steps + 1):
                a = i * (dash[0] + dash[1]) / ln
                b = min(1.0, a + dash[0] / ln)
                if a >= 1:
                    break
                self.d.line([(x1 + (x2 - x1) * a) * S, (y1 + (y2 - y1) * a) * S,
                             (x1 + (x2 - x1) * b) * S, (y1 + (y2 - y1) * b) * S],
                            fill=fill, width=max(1, int(w * S)))

    def c(self, cx, cy, r, fill, stroke=None, sw=1):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
                       fill=fill, outline=stroke, width=max(1, int(sw * S)))

    def poly(self, pts, fill=None, stroke=None, w=1):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
        if stroke:
            self.d.line([(x * S, y * S) for x, y in pts + [pts[0]]],
                        fill=stroke, width=max(1, int(w * S)), joint="curve")

    def line_pts(self, pts, fill, w=1):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill,
                    width=max(1, int(w * S)), joint="curve")

    def t(self, x, y, text, size=12, fill=TEXTE, bold=False, anchor="left"):
        a = {"left": "ls", "right": "rs", "middle": "ms"}.get(anchor, anchor)
        self.d.text((x * S, y * S), text, font=font(size, bold), fill=fill,
                    anchor=a)

    def save(self, path):
        self.img.resize((W * S, H * S), Image.LANCZOS).save(path)


def scene(c, x0, y0, w, h, seed=7):
    rnd = random.Random(seed)
    cx = x0 + w * 0.5
    horizon = y0 + h * 0.22
    c.r(x0, y0, w, h, fill="#FBFCFD")

    # grille de sol
    for i in range(-8, 9):
        c.l(cx + i * (w / 40), horizon, cx + i * (w / 12), y0 + h,
            fill=BORDURE, w=0.8)
    for i in range(1, 9):
        t = (i / 8) ** 1.9
        y = horizon + (y0 + h - horizon) * t
        c.l(x0, y, x0 + w, y, fill=BORDURE, w=0.8)

    # surface MNT
    n = 90
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        x = x0 + w * t
        ridge = (math.sin(t * 7.1 + .8) * 10 + math.sin(t * 2.3) * 16
                 + math.sin(t * 13.7) * 3)
        y = horizon - 34 + ridge
        top.append((x, y))
        bot.append((x, y + 26))
    c.poly(top + bot[::-1], fill="#E8EDE6")
    c.line_pts(top, "#C9D3C6", 1.4)

    # forages
    holes = 26
    for k in range(holes):
        t = k / (holes - 1)
        x_top = x0 + w * (0.06 + 0.88 * t) + rnd.uniform(-4, 4)
        tx = (x_top - x0) / w
        ridge = (math.sin(tx * 7.1 + .8) * 10 + math.sin(tx * 2.3) * 16
                 + math.sin(tx * 13.7) * 3)
        y_top = horizon - 34 + ridge + 4
        depth = rnd.uniform(.55, 1.0) * (h * .50)
        lean = rnd.uniform(-14, 14)
        c.l(x_top, y_top, x_top + lean, y_top + depth, fill="#344054", w=1.5)
        segs = 9
        for j in range(segs):
            a, b = j / segs, (j + 1) / segs
            c.l(x_top + lean * a, y_top + depth * a,
                x_top + lean * b, y_top + depth * b,
                fill=LITHO[rnd.choice(list(LITHO))], w=5.0)
        for j in range(5):
            a = .18 + .62 * (j / 4)
            c.c(x_top + lean * a + 7, y_top + depth * a,
                rnd.uniform(4.5, 9.0), TENEUR[j % len(TENEUR)])
        c.c(x_top, y_top - 5, 3.2, "#101828")

    # corridor de coupe
    bx0 = x0 + w * .30
    bw = w * .16
    c.poly([(bx0, horizon - 60), (bx0 + bw, horizon - 60),
            (bx0 + bw * 1.10, y0 + h - 10), (bx0 - bw * .10, y0 + h - 10)],
           fill=(46, 91, 255, 16))
    c.l(bx0, horizon - 60, bx0 - bw * .10, y0 + h - 10, fill=(46, 91, 255, 90),
        w=1, dash=(5, 5))
    c.l(bx0 + bw, horizon - 60, bx0 + bw * 1.10, y0 + h - 10,
        fill=(46, 91, 255, 90), w=1, dash=(5, 5))

    # barre caméra — largeurs calculées sur le texte réel
    ty = y0 + 18
    labels = [("Perspective", 1), ("Plan", 0), ("Face N", 0), ("Face E", 0)]
    fnt = font(10.5, False)
    widths = [c.d.textlength(lab, font=fnt) / S + 16 for lab, _ in labels]
    total = sum(widths) + 10
    bx = x0 + w - total - 12
    c.r(bx, ty, total + 8, 32, fill=SURFACE, stroke=BORDURE, rx=8)
    xx = bx + 8
    for (lab, actif), wd in zip(labels, widths):
        if actif:
            c.r(xx - 2, ty + 6, wd - 2, 20, fill=ACCENT_CLAIR, rx=5)
        c.t(xx + 6, ty + 20, lab, size=10.5,
            fill=ACCENT if actif else TEXTE_MOYEN, bold=bool(actif))
        xx += wd

    # badge exagération
    c.r(x0 + 16, y0 + h - 44, 122, 28, fill=SURFACE, stroke=BORDURE, rx=8)
    c.t(x0 + 28, y0 + h - 25, "Exag. Z  ×1.5", size=11, fill=TEXTE_MOYEN)

    # gizmo
    gx, gy = x0 + w - 56, y0 + h - 56
    c.c(gx, gy, 26, SURFACE, stroke=BORDURE)
    c.l(gx, gy, gx, gy - 20, fill=SEM_BLOC, w=2)
    c.l(gx, gy, gx + 19, gy, fill=SEM_ATT, w=2)
    c.t(gx, gy - 25, "N", size=9, fill=SEM_BLOC, bold=True, anchor="ms")
    c.t(gx + 25, gy + 2, "E", size=9, fill=SEM_ATT, bold=True, anchor="ms")


def row(c, x, y, w, label, checked=True, swatch=None, sub=False, count=None,
        dispo=True):
    h = 26
    if checked and dispo:
        c.r(x, y, w, h, fill=LIGNE_ACTIVE, rx=5)
    bx = x + 10
    c.r(bx, y + 7, 13, 13, fill=ACCENT if (checked and dispo) else SURFACE,
        stroke=ACCENT if (checked and dispo) else BORDURE_FORTE, sw=1.4, rx=3.5)
    if checked and dispo:
        c.line_pts([(bx + 3.2, y + 13.2), (bx + 5.6, y + 15.6),
                    (bx + 9.6, y + 10.4)], "#FFFFFF", 1.7)
    tx = bx + 21
    if swatch:
        c.c(tx + 4, y + 13.5, 4, swatch)
        tx += 14
    c.t(tx, y + 18, label, size=11 if sub else 11.5,
        fill=TEXTE if dispo else TEXTE_FAIBLE, bold=not sub)
    if not dispo:
        c.t(x + w - 12, y + 18, "2D seul.", size=9, fill=TEXTE_FAIBLE, anchor="rs")
    elif count:
        c.t(x + w - 12, y + 18, count, size=10.5, fill=TEXTE_FAIBLE, anchor="rs")


def group(c, x, y, w, label, n=None):
    c.t(x + 8, y + 15, "▾", size=9, fill=TEXTE_MOYEN)
    c.t(x + 20, y + 15, label, size=9.5, fill=TEXTE_MOYEN, bold=True)
    if n:
        c.t(x + w - 12, y + 15, n, size=9.5, fill=TEXTE_FAIBLE, anchor="rs")


def panel(c, x, y, w, h):
    c.r(x, y, w, h, fill=SURFACE, stroke=BORDURE)
    c.t(x + 20, y + 18, "Calques", size=13, fill=TEXTE, bold=True)
    c.t(x + 20, y + 38, "Vue 3D · 64 forages", size=10.5, fill=TEXTE_FAIBLE)
    c.t(x + 20, y + 51, "4 domaines restent en 2D (signalé, jamais masqué)",
        size=8.8, fill=TEXTE_FAIBLE)
    c.r(x + w - 34, y + 16, 18, 18, fill="#F2F4F7", rx=5)
    c.t(x + w - 25, y + 22, "+", size=13, fill=TEXTE_MOYEN, anchor="ms")
    yy = y + 58
    c.l(x, yy, x + w, yy)

    yy += 14
    group(c, x + 8, yy, w, "Forages", "64"); yy += 24
    row(c, x, yy, w, "Collets", True, swatch="#101828"); yy += 26
    row(c, x, yy, w, "Trajectoire", True, swatch="#344054"); yy += 26
    row(c, x, yy, w, "Étiquettes de trou", False, sub=True); yy += 26
    row(c, x, yy, w, "Profondeurs", False, sub=True); yy += 26
    row(c, x, yy, w, "Déviations", True, sub=True); yy += 30

    group(c, x + 8, yy, w, "Géologie"); yy += 24
    row(c, x, yy, w, "Lithologie", True, swatch="#8FA85A"); yy += 26
    row(c, x, yy, w, "Altération", True, swatch="#D9C6E8"); yy += 26
    row(c, x, yy, w, "Minéralisation", True, swatch="#5D6D7E"); yy += 26
    row(c, x, yy, w, "Structures", True, swatch="#B54708"); yy += 26
    row(c, x, yy, w, "Imagerie", False, swatch="#7F56D9", dispo=False); yy += 26
    row(c, x, yy, w, "Surface (MNT)", True, swatch="#C9D3C6"); yy += 30

    group(c, x + 8, yy, w, "Analyses"); yy += 24
    row(c, x, yy, w, "Teneurs", True, swatch=TENEUR[1]); yy += 26
    row(c, x, yy, w, "Au ppm", True, sub=True); yy += 26
    row(c, x, yy, w, "Cu ppm", False, sub=True); yy += 26
    row(c, x, yy, w, "Intercepts", True); yy += 26
    row(c, x, yy, w, "RQD", True, swatch=SEM_OK); yy += 26
    row(c, x, yy, w, "Récupération", False, swatch=SEM_ATT); yy += 26
    row(c, x, yy, w, "Densité", False, swatch="#7F56D9"); yy += 30


    c.l(x, y + h - 52, x + w, y + h - 52)
    c.t(x + 20, y + h - 38, "Actualiser la scène", size=11, fill=ACCENT, bold=True)
    c.t(x + w - 20, y + h - 38, "Ctrl+R", size=10, fill=TEXTE_FAIBLE, anchor="rs")


def nav(c, y):
    c.t(48, y - 22, "D-014 · Navigation — le choix t'appartient", size=13,
        fill=TEXTE, bold=True)
    mods = ["Projet", "Données", "Géométrie", "Coupe 2D", "Vue 3D",
            "Analyses", "Export"]

    # Variante A
    ax, ay, aw = 48, y, 740
    c.r(ax, ay, aw, 78, fill=SURFACE, stroke=BORDURE, rx=10)
    c.t(ax + 16, ay + 10, "VARIANTE A · onglets horizontaux", size=9.5,
        fill=TEXTE_FAIBLE, bold=True)
    c.r(ax + 16, ay + 24, 22, 22, fill=TEXTE, rx=6)
    c.t(ax + 27, ay + 28, "D", size=12, fill="#FFFFFF", bold=True, anchor="ms")
    c.t(ax + 45, ay + 31, "DRILLMASTER", size=8.6, fill=TEXTE, bold=True)
    xx = ax + 158
    for m in mods:
        actif = m == "Vue 3D"
        wd = 12 + len(m) * 6.6
        if actif:
            c.r(xx - 8, ay + 24, wd + 6, 24, fill=ACCENT_CLAIR, rx=6)
        c.t(xx, ay + 32, m, size=10.5,
            fill=ACCENT if actif else TEXTE_MOYEN, bold=bool(actif))
        xx += wd + 8
    c.t(ax + 16, ay + 62, "Un seul niveau, tout visible, hiérarchie par la couleur.",
        size=10, fill=TEXTE_FAIBLE)

    # Variante B
    bx, by, bw = 828, y, 340
    c.r(bx, by, bw, 78, fill=SURFACE, stroke=BORDURE, rx=10)
    c.t(bx + 16, by + 10, "VARIANTE B · rail vertical", size=9.5,
        fill=TEXTE_FAIBLE, bold=True)
    c.r(bx + 12, by + 22, 40, 50, fill="#F9FAFB", stroke=BORDURE, rx=7)
    for i in range(7):
        actif = i == 4
        yy = by + 30 + i * 6.4
        if actif:
            c.r(bx + 18, yy - 3, 28, 6, fill=ACCENT_CLAIR, rx=3)
        c.c(bx + 32, yy, 2.4, ACCENT if actif else TEXTE_FAIBLE)
    c.t(bx + 64, by + 30, "Vue 3D", size=11.5, fill=TEXTE, bold=True)
    c.t(bx + 64, by + 48, "Scène · calques · caméra", size=10, fill=TEXTE_FAIBLE)
    c.t(bx + 64, by + 64, "7 modules, place pour 12+ sans rien casser.",
        size=10, fill=TEXTE_FAIBLE)


def build(path="maquettes/m3d_vue_et_panneau.png"):
    c = Canvas(W, H, FOND)
    c.t(48, 26, "DRILLMASTER", size=10, fill=TEXTE, bold=True)
    c.t(48, 46, "Vue 3D — direction artistique cible", size=21, fill=TEXTE, bold=True)
    c.t(48, 76, "Minimal Professional Workstation · fond #F6F7F9 · accent unique #2E5BFF",
        size=10.5, fill=TEXTE_MOYEN)
    c.t(48, 94, "Les 4 couleurs sémantiques (ci-contre) sont réservées aux états — jamais à une donnée.",
        size=10.5, fill=TEXTE_FAIBLE)

    fpill = font(9.5, True)
    labels = [("Information", SEM_INFO), ("Attention", SEM_ATT),
              ("Blocage", SEM_BLOC), ("Validation", SEM_OK)]
    pills = [(c.d.textlength(l, font=fpill) / S + 22, l, col) for l, col in labels]
    px = W - 40 - sum(p[0] + 8 for p in pills)
    for wd, lab, col in pills:
        c.r(px, 32, wd, 20, fill="#FFFFFF", stroke=BORDURE, rx=10)
        c.c(px + 10, 42, 3.4, col)
        c.t(px + 18, 37, lab, size=9.5, fill=TEXTE_MOYEN, bold=True)
        px += wd + 8

    top = 108
    sc_w = W - PANEL - 96
    scene(c, 48, top, sc_w, H - top - 200)
    panel(c, W - PANEL - 48, top, PANEL, H - top - 200)

    sy = H - 200 + 10
    c.r(48, sy, sc_w, 26, fill=SURFACE, stroke=BORDURE, rx=6)
    c.t(62, sy + 7, "64 forages · 2 410 segments · 12 ms (complet)", size=10.5,
        fill=TEXTE_FAIBLE)
    c.c(48 + sc_w - 96, sy + 13, 3.5, SEM_OK)
    c.t(48 + sc_w - 86, sy + 8, "Prêt", size=10.5, fill=TEXTE_MOYEN, bold=True)

    nav(c, H - 104)
    c.save(path)
    return path


if __name__ == "__main__":
    print("écrit :", build())
