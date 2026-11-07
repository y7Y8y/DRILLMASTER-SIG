"""Maquette DRILLMASTER — Vue 3D cible + panneau de calques.

Dessine la direction artistique « Minimal Professional Workstation » :
fond très légèrement teinté, surfaces blanches, bordures discrètes,
une seule couleur d'accent, typographie hiérarchisée.

Ce fichier ne dépend d'aucune bibliothèque : il produit un SVG lisible
et un PNG si `cairosvg` est disponible.
"""
from __future__ import annotations

import html
import math
import random

# ── Tokens (design system) ──────────────────────────────────────────────
FOND = "#F6F7F9"          # fond de l'application, gris très légèrement teinté
SURFACE = "#FFFFFF"       # panneaux
BORDURE = "#E4E7EC"       # bordures discrètes
BORDURE_FORTE = "#D0D5DD"
TEXTE = "#101828"         # titres
TEXTE_MOYEN = "#475467"   # libellés
TEXTE_FAIBLE = "#98A2B3"  # secondaire
ACCENT = "#2E5BFF"        # UNE seule couleur d'accent (actions principales)
SEM_INFO = "#667085"
SEM_ATTENTION = "#F79009"
SEM_BLOCAGE = "#D92D20"
SEM_OK = "#12B76A"

# Palette géologique (extrait de litho_palette.json — aplats vifs)
LITHO = {
    "LAT": "#C99A5B", "SAP": "#E0B56B", "SPR": "#8FA85A",
    "MTZ": "#5E8C4A", "PEG": "#E86A5E", "QTZ": "#E8E1C8", "MIS": "#9B79E3",
}
TENEUR = ("#7B61FF", "#3B8BEA", "#1FA97A", "#F5B335", "#E8623D")

W, H = 1600, 980
PANEL = 300


def esc(t):
    return html.escape(str(t))


class SVG:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke="none", rx=0, sw=1, op=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                 f'opacity="{op}"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=BORDURE, sw=1, op=1, dash=None, cap="butt"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}" '
                 f'stroke-linecap="{cap}"{d}/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=1, op=1):
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')

    def poly(self, pts, fill="none", stroke="none", sw=1, op=1, close=False):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.add(f'<{tag} points="{p}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" opacity="{op}"/>')

    def path(self, d, fill="none", stroke="none", sw=1, op=1):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" opacity="{op}"/>')

    def text(self, x, y, t, size=12, fill=TEXTE, weight=400, anchor="start",
             spacing=None, family="Inter, -apple-system, 'Segoe UI', Roboto, sans-serif"):
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
                 f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
                 f'text-anchor="{anchor}"{ls}>{esc(t)}</text>')

    def render(self, bg):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="{self.w}" height="{self.h}" fill="{bg}"/>')
        return head + "".join(self.parts) + "</svg>"


# ══════════════════════════════════════════════════════════════════════
# La scène 3D — projection isométrique simple, lisible
# ══════════════════════════════════════════════════════════════════════
def scene(s: SVG, x0, y0, w, h, seed=7):
    rnd = random.Random(seed)
    cx = x0 + w * 0.5
    horizon = y0 + h * 0.30

    # fond de scène : dégradé très doux (pas de noir, pas de dégradé criard)
    s.rect(x0, y0, w, h, fill="#FBFCFD")
    for i in range(12):
        t = i / 11
        s.rect(x0, y0 + h * t, w, h / 11 + 1,
               fill="#FFFFFF", op=0.5 * (1 - t) * 0.5)

    # grille de sol (perspective), discrète
    for i in range(-8, 9):
        x_bot = cx + i * (w / 12)
        x_top = cx + i * (w / 40)
        s.line(x_top, horizon, x_bot, y0 + h, stroke=BORDURE, sw=0.8, op=0.55)
    for i in range(1, 9):
        t = (i / 8) ** 1.9
        y = horizon + (y0 + h - horizon) * t
        s.line(x0, y, x0 + w, y, stroke=BORDURE, sw=0.8, op=0.45)

    # ── surface topographique (MNT) : ruban ondulé, gris-vert très doux
    n = 90
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        x = x0 + w * t
        ridge = (math.sin(t * 7.1 + 0.8) * 10 + math.sin(t * 2.3) * 16
                 + math.sin(t * 13.7) * 3)
        y = horizon - 34 + ridge
        top.append((x, y))
        bot.append((x, y + 26))
    s.poly(top + bot[::-1], fill="#E8EDE6", stroke="none", close=True, op=1)
    s.poly(top, stroke="#C9D3C6", sw=1.4)

    # ── foragege : chaque trou = trajectoire + bandes litho + bulles de teneur
    holes = 26
    for k in range(holes):
        t = k / (holes - 1)
        x_top = x0 + w * (0.06 + 0.88 * t) + rnd.uniform(-4, 4)
        ridge = (math.sin((x_top - x0) / w * 7.1 + 0.8) * 10
                 + math.sin((x_top - x0) / w * 2.3) * 16
                 + math.sin((x_top - x0) / w * 13.7) * 3)
        y_top = horizon - 34 + ridge + 4
        depth = rnd.uniform(0.55, 1.0) * (h * 0.50)
        lean = rnd.uniform(-14, 14)
        x_bot = x_top + lean
        y_bot = y_top + depth

        # trajectoire
        s.line(x_top, y_top, x_bot, y_bot, stroke="#344054", sw=1.5, op=0.85)

        # bandes lithologiques : segments courts colorés le long du trou
        segs = 9
        for j in range(segs):
            a = j / segs
            b = (j + 1) / segs
            ya, yb = y_top + depth * a, y_top + depth * b
            xa = x_top + lean * a
            xb = x_top + lean * b
            code = rnd.choice(list(LITHO))
            col = LITHO[code]
            s.line(xa, ya, xb, yb, stroke=col, sw=5.0, op=0.95, cap="round")

        # bulles de teneur : grosses, colorées, le long du trou (côté droit)
        for j in range(5):
            a = 0.18 + 0.62 * (j / 4)
            ya = y_top + depth * a
            xa = x_top + lean * a + 7
            r = rnd.uniform(4.5, 9.0)
            s.circle(xa, ya, r, TENEUR[j % len(TENEUR)], op=0.88)

        # collet : petit disque net
        s.circle(x_top, y_top - 5, 3.2, "#101828", op=0.9)

    # ── plan de coupe (corridor translucide) : bleu accent très clair
    bx0 = x0 + w * 0.30
    bw = w * 0.16
    s.poly([(bx0, horizon - 60), (bx0 + bw, horizon - 60),
            (bx0 + bw * 1.10, y0 + h - 10), (bx0 - bw * 0.10, y0 + h - 10)],
           fill=ACCENT, op=0.055, close=True)
    s.line(bx0, horizon - 60, bx0 - bw * 0.10, y0 + h - 10, stroke=ACCENT, sw=1, op=0.25, dash="5 5")
    s.line(bx0 + bw, horizon - 60, bx0 + bw * 1.10, y0 + h - 10, stroke=ACCENT, sw=1, op=0.25, dash="5 5")

    # ── barre d'outils flottante (caméra) : pastilles discrètes
    ty = y0 + 18
    s.rect(x0 + w - 232, ty, 214, 32, fill=SURFACE, stroke=BORDURE, rx=8)
    labels = ["Perspective", "Plan", "Face N", "Face E"]
    xx = x0 + w - 222
    for i, lab in enumerate(labels):
        actif = i == 0
        wd = 50 if i < 2 else 46
        if actif:
            s.rect(xx - 6, ty + 6, wd + 4, 20, fill="#EEF2FF", rx=5)
        s.text(xx, ty + 20, lab, size=10.5, fill=ACCENT if actif else TEXTE_MOYEN,
               weight=600 if actif else 400)
        xx += wd + 8

    # ── badge d'exagération Z, bas gauche
    s.rect(x0 + 16, y0 + h - 44, 116, 28, fill=SURFACE, stroke=BORDURE, rx=8)
    s.text(x0 + 28, y0 + h - 25, "Exag. Z  ×1.5", size=11, fill=TEXTE_MOYEN, weight=500)

    # ── gizmo d'orientation, bas droite de la scène
    gx, gy = x0 + w - 56, y0 + h - 56
    s.circle(gx, gy, 26, SURFACE, stroke=BORDURE, sw=1)
    s.line(gx, gy, gx, gy - 20, stroke=SEM_BLOCAGE, sw=2)      # N
    s.line(gx, gy, gx + 19, gy, stroke=SEM_ATTENTION, sw=2)    # E
    s.text(gx, gy - 24, "N", size=9, fill=SEM_BLOCAGE, weight=700, anchor="middle")
    s.text(gx + 24, gy + 3.5, "E", size=9, fill=SEM_ATTENTION, weight=700, anchor="middle")


# ══════════════════════════════════════════════════════════════════════
# Le panneau de calques — arbre, pas une pile de cases
# ══════════════════════════════════════════════════════════════════════
def calque_row(s, x, y, w, label, checked=True, swatch=None, indent=0, sub=False,
               count=None, dispo=True):
    row_h = 26
    if checked and dispo:
        s.rect(x, y, w, row_h, fill="#F7F9FF", rx=5)
    bx = x + 10 + indent * 14
    # case à cocher
    s.rect(bx, y + 7, 13, 13, fill=ACCENT if (checked and dispo) else SURFACE,
           stroke=ACCENT if (checked and dispo) else BORDURE_FORTE, rx=3.5)
    if checked and dispo:
        s.path(f"M {bx+3.2} {y+13.2} L {bx+5.6} {y+15.8} L {bx+9.8} {y+10.4}",
               stroke="#FFFFFF", sw=1.7)
    tx = bx + 20
    if swatch:
        s.circle(tx + 4, y + 13.5, 4, swatch)
        tx += 14
    col = TEXTE if dispo else TEXTE_FAIBLE
    s.text(tx, y + 17.5, label, size=11.5 if not sub else 11,
           fill=col, weight=500 if not sub else 400)
    if count is not None:
        s.text(x + w - 12, y + 17.5, count, size=10.5, fill=TEXTE_FAIBLE,
               anchor="end")
    if not dispo:
        s.text(x + w - 12, y + 17.5, "2D seulement", size=9, fill=TEXTE_FAIBLE, anchor="end")


def group_header(s, x, y, w, label, n=None):
    s.text(x + 8, y + 15, "▾", size=9, fill=TEXTE_MOYEN)
    s.text(x + 20, y + 15, label.upper(), size=9.5, fill=TEXTE_MOYEN,
           weight=700, spacing="0.6")
    if n:
        s.text(x + w - 12, y + 15, n, size=9.5, fill=TEXTE_FAIBLE, anchor="end")


def panel(s: SVG, x, y, w, h):
    s.rect(x, y, w, h, fill=SURFACE, stroke=BORDURE)
    s.line(x, y, x, y + h, stroke=BORDURE)

    # en-tête
    s.text(x + 20, y + 30, "Calques", size=13, fill=TEXTE, weight=650)
    s.text(x + 20, y + 48, "Vue 3D · 64 forages", size=10.5, fill=TEXTE_FAIBLE)
    s.rect(x + w - 34, y + 18, 18, 18, fill="#F2F4F7", rx=5)
    s.text(x + w - 25, y + 31, "+", size=13, fill=TEXTE_MOYEN, weight=500, anchor="middle")

    yy = y + 66
    s.line(x, yy, x + w, yy, stroke=BORDURE)

    # ── groupe Forages
    yy += 14
    group_header(s, x + 8, yy, w - 16, "Forages", "64")
    yy += 24
    calque_row(s, x, yy, w, "Collets", True, swatch="#101828"); yy += 26
    calque_row(s, yy * 0 + yy, w, "x", False) if False else None
    calque_row(s, x, yy, w, "Trajectoire", True, swatch="#344054"); yy += 26
    calque_row(s, x, yy, w, "Profondeurs", False, sub=True); yy += 26
    calque_row(s, x, yy, w, "Déviations", True, sub=True, count="128"); yy += 30

    # ── groupe Géologie
    group_header(s, x + 8, yy, w - 16, "Géologie")
    yy += 24
    calque_row(s, x, yy, w, "Lithologie", True, swatch="#8FA85A", count="7"); yy += 26
    calque_row(s, x, yy, w, "Altération", True, swatch="#D9C6E8", count="5"); yy += 26
    calque_row(s, x, yy, w, "Minéralisation", True, swatch="#5D6D7E", count="4"); yy += 26
    calque_row(s, x, yy, w, "Structures", True, swatch="#B54708", count="212"); yy += 26
    calque_row(s, x, yy, w, "Imagerie", False, swatch="#7F56D9", dispo=False); yy += 26
    calque_row(s, x, yy, w, "Surface (MNT)", True, swatch="#C9D3C6"); yy += 30

    # ── groupe Analyses
    group_header(s, x + 8, yy, w - 16, "Analyses")
    yy += 24
    calque_row(s, x, yy, w, "Teneurs", True, swatch=TENEUR[1]); yy += 26
    calque_row(s, x, yy, w, "Au ppm", True, sub=True, count="3 180"); yy += 26
    calque_row(s, x, yy, w, "Cu ppm", False, sub=True); yy += 26
    calque_row(s, x, yy, w, "Intercepts", True); yy += 26
    calque_row(s, x, yy, w, "RQD", True, swatch=SEM_OK); yy += 26
    calque_row(s, x, yy, w, "Récupération", False, swatch=SEM_ATTENTION); yy += 26
    calque_row(s, x, yy, w, "Densité", False, swatch="#7F56D9"); yy += 34

    # ── pied : action unique, discrète
    s.line(x, y + h - 52, x + w, y + h - 52, stroke=BORDURE)
    s.text(x + 20, y + h - 28, "Actualiser la scène", size=11, fill=ACCENT, weight=600)
    s.text(x + w - 20, y + h - 28, "⌘R", size=10, fill=TEXTE_FAIBLE, anchor="end")


# ══════════════════════════════════════════════════════════════════════
# Variante A / B de la barre de navigation (question D-014)
# ══════════════════════════════════════════════════════════════════════
def nav_variants(s: SVG):
    y = H - 128
    # bandeau de contexte
    s.text(48, y - 18, "D-014 · Navigation — le choix t'appartient", size=13,
           fill=TEXTE, weight=650)

    mods = ["Projet", "Données", "Géométrie", "Coupe 2D", "Vue 3D",
            "Analyses", "Export"]

    # ── Variante A : onglets horizontaux (Linear / Apple)
    ax, ay = 48, y + 6
    aw = 740
    s.rect(ax, ay - 4, aw, 78, fill=SURFACE, stroke=BORDURE, rx=10)
    s.text(ax + 16, ay + 16, "VARIANTE A · onglets horizontaux", size=10,
           fill=TEXTE_FAIBLE, weight=700, spacing="0.6")
    # logo
    s.rect(ax + 16, ay + 26, 22, 22, fill=TEXTE, rx=6)
    s.text(ax + 27, ay + 42, "D", size=13, fill="#FFFFFF", weight=700, anchor="middle")
    s.text(ax + 46, ay + 42, "DRILLMASTER", size=9.5, fill=TEXTE, weight=700, spacing="0.8")
    xx = ax + 118
    for i, m in enumerate(mods):
        actif = m == "Vue 3D"
        wd = 12 + len(m) * 6.3
        if actif:
            s.rect(xx - 8, ay + 26, wd + 4, 26, fill="#EEF2FF", rx=6)
        s.text(xx, ay + 44, m, size=11, fill=ACCENT if actif else TEXTE_MOYEN,
               weight=600 if actif else 450)
        xx += wd + 10
    s.text(ax + 16, ay + 68, "Un seul niveau, tout visible d'un coup, hiérarchie par la couleur.",
           size=10, fill=TEXTE_FAIBLE)

    # ── Variante B : rail vertical (ArcGIS / Photoshop)
    bx, by = 828, y + 6
    bw = 340
    s.rect(bx, by - 4, bw, 78, fill=SURFACE, stroke=BORDURE, rx=10)
    s.text(bx + 16, by + 16, "VARIANTE B · rail vertical", size=10,
           fill=TEXTE_FAIBLE, weight=700, spacing="0.6")
    s.rect(bx + 12, by + 22, 40, 54, fill="#F9FAFB", stroke=BORDURE, rx=7)
    icons = ["P", "D", "G", "2", "3", "A", "E"]
    for i, ic in enumerate(icons):
        actif = ic == "3"
        if actif:
            s.rect(bx + 18, by + 26 + i * 7.2, 28, 6.2, fill="#EEF2FF", rx=3)
        s.circle(bx + 32, by + 32 + i * 7.2, 2.4,
                 ACCENT if actif else TEXTE_FAIBLE, op=1 if actif else 0.55)
    s.text(bx + 62, by + 40, "Vue 3D", size=11.5, fill=TEXTE, weight=600)
    s.text(bx + 62, by + 56, "Scène · calques · caméra", size=10, fill=TEXTE_FAIBLE)
    s.text(bx + 62, by + 70, "7 modules, place pour 12+ sans rien casser.",
           size=10, fill=TEXTE_FAIBLE)


def legend(s: SVG):
    x, y = 48, 40
    s.text(x, y, "DRILLMASTER", size=11, fill=TEXTE, weight=800, spacing="2.2")
    s.text(x, y + 26, "Vue 3D — direction artistique cible", size=22, fill=TEXTE, weight=650)
    s.text(x, y + 48, "Minimal Professional Workstation · fond #F6F7F9 · accent unique #2E5BFF",
           size=11.5, fill=TEXTE_MOYEN)
    # légende des 4 couleurs sémantiques
    items = [("Information", SEM_INFO), ("Attention", SEM_ATTENTION),
             ("Blocage", SEM_BLOCAGE), ("Validation", SEM_OK)]
    xx = W - 48 - 4 * 116
    for i, (lab, col) in enumerate(items):
        s.circle(xx + i * 116, y + 12, 4, col)
        s.text(xx + i * 116 + 12, y + 15.5, lab, size=10, fill=TEXTE_MOYEN)


def build():
    s = SVG(W, H)
    s.rect(0, 0, W, H, fill=FOND)
    legend(s)

    top = 78
    sc_w = W - PANEL - 96
    scene(s, 48, top, sc_w, H - top - 148)
    panel(s, W - PANEL - 48, top, PANEL, H - top - 148)

    # barre de statut sous la scène
    sy = H - 148 + 8
    s.rect(48, sy, sc_w, 26, fill=SURFACE, stroke=BORDURE, rx=6)
    s.text(62, sy + 17, "64 forages · 2 410 segments · 12 ms (complet)", size=10.5,
           fill=TEXTE_FAIBLE)
    s.circle(48 + sc_w - 96, sy + 13, 3.5, SEM_OK)
    s.text(48 + sc_w - 86, sy + 17, "Prêt", size=10.5, fill=TEXTE_MOYEN, weight=500)

    nav_variants(s)
    return s.render(FOND)


if __name__ == "__main__":
    svg = build()
    with open("maquettes/m3d_vue_et_panneau.svg", "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("maquettes/m3d_vue_et_panneau.svg écrit")
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(), write_to="maquettes/m3d_vue_et_panneau.png",
                         output_width=W * 2, output_height=H * 2)
        print("maquettes/m3d_vue_et_panneau.png écrit")
    except Exception as exc:
        print("PNG non généré (cairosvg absent) :", exc)
