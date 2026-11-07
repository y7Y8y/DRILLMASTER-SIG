"""DRILLMASTER — bibliothèque de composants pour les maquettes.

Tokens + widgets dessinés en Pillow. Aucun texte ne déborde : toutes les
largeurs sont mesurées sur la police réelle avant placement.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

S = 2  # super-échantillonnage

FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_cache = {}


def font(size, bold=False):
    key = (round(size * S), bold)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONT_B if bold else FONT_R, key[0])
    return _cache[key]


class Tokens:
    """Thème clair (défaut) — le sombre dérive des mêmes clés."""
    bg = "#F6F7F9"
    surface = "#FFFFFF"
    surface_2 = "#F9FAFB"
    surface_3 = "#F2F4F7"
    border = "#E4E7EC"
    border_strong = "#D0D5DD"
    ink = "#101828"
    ink_2 = "#475467"
    ink_3 = "#98A2B3"
    accent = "#2E5BFF"
    accent_soft = "#EEF2FF"
    accent_line = "#C7D4FF"
    ok = "#12B76A"
    warn = "#F79009"
    block = "#D92D20"
    quest = "#7F56D9"
    info = "#667085"


class Dark(Tokens):
    bg = "#0F1115"
    surface = "#16191F"
    surface_2 = "#1B1F26"
    surface_3 = "#22272F"
    border = "#262B33"
    border_strong = "#39404A"
    ink = "#E7EAEE"
    ink_2 = "#9AA4B2"
    ink_3 = "#6B7482"
    accent = "#5B7CFF"
    accent_soft = "#1B2340"
    accent_line = "#2B3A6B"


class C:
    """Canevas : primitives + widgets. Toutes les coordonnées en px logiques."""

    def __init__(self, w, h, t=Tokens):
        self.w, self.h, self.th = w, h, t
        self.img = Image.new("RGB", (w * S, h * S), t.bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    # ── primitives ────────────────────────────────────────────────────
    def tw(self, text, size, bold=False):
        return self.d.textlength(text, font=font(size, bold)) / S

    def r(self, x, y, w, h, fill=None, stroke=None, sw=1, rx=0, dash=None):
        box = [x * S, y * S, (x + w) * S, (y + h) * S]
        if dash:
            self._dash_rect(x, y, w, h, stroke, sw, dash, rx)
            if fill:
                self.d.rounded_rectangle(box, radius=rx * S, fill=fill)
            return
        if rx:
            self.d.rounded_rectangle(box, radius=rx * S, fill=fill,
                                     outline=stroke, width=max(1, int(sw * S)))
        else:
            self.d.rectangle(box, fill=fill, outline=stroke,
                             width=max(1, int(sw * S)))

    def _dash_rect(self, x, y, w, h, col, sw, dash, rx):
        self.l(x, y, x + w, y, fill=col, w=sw, dash=dash)
        self.l(x + w, y, x + w, y + h, fill=col, w=sw, dash=dash)
        self.l(x + w, y + h, x, y + h, fill=col, w=sw, dash=dash)
        self.l(x, y + h, x, y, fill=col, w=sw, dash=dash)

    def l(self, x1, y1, x2, y2, fill=None, w=1, dash=None):
        fill = fill or self.th.border
        if not dash:
            self.d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=fill,
                        width=max(1, int(w * S)))
            return
        ln = math.hypot(x2 - x1, y2 - y1) or 1
        a = 0.0
        while a < 1:
            b = min(1.0, a + dash[0] / ln)
            self.d.line([(x1 + (x2 - x1) * a) * S, (y1 + (y2 - y1) * a) * S,
                         (x1 + (x2 - x1) * b) * S, (y1 + (y2 - y1) * b) * S],
                        fill=fill, width=max(1, int(w * S)))
            a = b + dash[1] / ln

    def c(self, cx, cy, rad, fill, stroke=None, sw=1):
        self.d.ellipse([(cx - rad) * S, (cy - rad) * S,
                        (cx + rad) * S, (cy + rad) * S],
                       fill=fill, outline=stroke, width=max(1, int(sw * S)))

    def poly(self, pts, fill=None, stroke=None, w=1):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
        if stroke:
            self.d.line([(x * S, y * S) for x, y in pts + [pts[0]]],
                        fill=stroke, width=max(1, int(w * S)), joint="curve")

    def path(self, pts, fill=None, stroke=None, w=1):
        self.d.line([(x * S, y * S) for x, y in pts], fill=stroke,
                    width=max(1, int(w * S)), joint="curve")
        if fill is not None:
            self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)

    def txt(self, x, y, text, size=11, fill=None, bold=False, anchor=None):
        """anchor Omis = coin haut-gauche (comportement le plus simple)."""
        self.d.text((x * S, y * S), str(text), font=font(size, bold),
                    fill=fill or self.th.ink, anchor=anchor)

    def clip_text(self, x, y, text, maxw, size=11, fill=None, bold=False):
        if self.tw(text, size, bold) <= maxw:
            self.txt(x, y, text)
            return
        ell = "…"
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.tw(text[:mid] + ell, size, bold) <= maxw:
                lo = mid
            else:
                hi = mid - 1
        self.txt(x, y, text[:lo] + ell)

    def save(self, path):
        self.img.resize((self.w * S, self.h * S), Image.LANCZOS).save(path)
        return path

    # ── chrome d'application ──────────────────────────────────────────
    MODULES = ["Projet", "Données", "Géométrie", "Coupe 2D", "Vue 3D",
               "Analyses", "Export"]

    def app_bar(self, active="Vue 3D", project="Projet Issia", dark_btn=False):
        t = self.th
        self.r(0, 0, self.w, 54, fill=t.surface)
        self.l(0, 54, self.w, 54, fill=t.border)
        # logo
        self.r(18, 14, 26, 26, fill=t.ink, rx=7)
        self.txt(31, 20, "D", size=13, fill="#FFFFFF", bold=True, anchor="ms")
        x = 56
        self.txt(x, 20, "DRILLMASTER", size=9, bold=True)
        x += self.tw("DRILLMASTER", 9, True) + 18
        for i, m in enumerate(self.MODULES):
            actif = m == active
            wd = self.tw(m, 11.5, True) + 22
            if actif:
                self.r(x, 12, wd, 30, fill=t.accent_soft, rx=7)
            self.txt(x + 11, 22, m, size=11.5)
            x += wd + 4
        # à droite : projet + thème
        rw = 150
        self.r(self.w - rw - 16, 13, rw, 28, fill=t.surface_2, stroke=t.border, rx=7)
        self.c(self.w - rw - 2, 27, 4, t.ok)
        self.txt(self.w - rw + 8, 22, project, size=10.5, bold=True)
        self.r(self.w - rw - 16 - 34, 13, 30, 28, fill=t.surface_2,
               stroke=t.border, rx=7)
        self.txt(self.w - rw - 16 - 23, 22, "FR", size=9.5, bold=True, anchor="ms")
        self.r(self.w - rw - 16 - 34 - 34, 13, 30, 28, fill=t.surface_2,
               stroke=t.border, rx=7)
        self.c(self.w - rw - 16 - 34 - 19, 27, 6, t.surface_3, t.border_strong)
        self.txt(self.w - rw - 16 - 34 - 19, 24, "◐", size=9)

    def status_bar(self, left, right="Prêt", right_col=None):
        t = self.th
        y = self.h - 28
        self.r(0, y, self.w, 28, fill=t.surface)
        self.l(0, y, self.w, y, fill=t.border)
        self.txt(18, y + 8, left, size=9.8)
        col = right_col or t.ok
        rx = self.w - 18
        self.txt(rx, y + 8, right, size=9.8, bold=True, anchor="rs")
        self.c(rx - self.tw(right, 9.8, True) - 10, y + 13, 3.4, col)

    # ── composants ────────────────────────────────────────────────────
    def page_title(self, x, y, title, sub=None):
        self.txt(x, y, title, size=20, bold=True)
        if sub:
            self.txt(x, y + 24, sub, size=10.5)

    def panel(self, x, y, w, h, title=None, sub=None, icon=None):
        t = self.th
        self.r(x, y, w, h, fill=t.surface, stroke=t.border, rx=10)
        if title:
            self.txt(x + 16, y + 20, title, size=12.5, bold=True)
            if sub:
                self.txt(x + 16, y + 36, sub, size=9.8)
            self.l(x, y + 50, x + w, y + 50)
        return y + (58 if title else 0)

    def section_label(self, x, y, text):
        """y = ligne de base supérieure du libellé (occupe y-9 … y+1)."""
        self.txt(x, y + 8, text.upper(), size=8.8, bold=True, anchor="ls")

    def chip(self, x, y, text, kind="info", solid=False):
        t = self.th
        col = {"info": t.info, "ok": t.ok, "warn": t.warn,
               "block": t.block, "quest": t.quest}[kind]
        wd = self.tw(text, 8.8, True) + 28
        if solid:
            self.r(x, y, wd, 20, fill=col, rx=10)
            self.txt(x + 10, y + 14, text, size=8.8, fill="#FFFFFF", bold=True, anchor="ls")
        else:
            self.r(x, y, wd, 20, fill=t.surface, stroke=col, sw=1, rx=10)
            self.c(x + 9, y + 10, 2.4, col)
            self.txt(x + 16, y + 14, text, size=8.8, fill=col, bold=True, anchor="ls")
        return wd

    def dot(self, x, y, kind="ok", rad=3.4):
        t = self.th
        col = {"info": t.info, "ok": t.ok, "warn": t.warn,
               "block": t.block, "quest": t.quest, "off": t.ink_3}[kind]
        self.c(x, y, rad, col)

    def checkbox(self, x, y, checked, size=13, disabled=False):
        t = self.th
        if checked and not disabled:
            self.r(x, y, size, size, fill=t.accent, rx=3.5)
            self.path([(x + size * .24, y + size * .52),
                       (x + size * .43, y + size * .72),
                       (x + size * .76, y + size * .30)],
                      stroke="#FFFFFF", w=1.7)
        else:
            self.r(x, y, size, size, fill=t.surface,
                   stroke=t.border_strong, sw=1.3, rx=3.5)

    def button(self, x, y, text, primary=False, w=None, size=10.5, icon=None):
        t = self.th
        wd = w or (self.tw(text, size, True) + 26)
        h = 28
        if primary:
            self.r(x, y, wd, h, fill=t.accent, rx=7)
            self.txt(x + wd / 2, y + 19, text, size=size, fill="#FFFFFF", bold=True, anchor="ms")
        else:
            self.r(x, y, wd, h, fill=t.surface, stroke=t.border_strong, sw=1.1, rx=7)
            self.txt(x + wd / 2, y + 19, text, size=size, bold=True, anchor="ms")
        return wd

    def field(self, x, y, w, label, value, hint=None, mono=False):
        t = self.th
        self.txt(x, y, label, size=9.5)
        self.r(x, y + 8, w, 28, fill=t.surface, stroke=t.border_strong, sw=1, rx=6)
        self.txt(x + 10, y + 18, value, size=10.5)
        if hint:
            self.txt(x + 10, y + 42, hint, size=8.8)

    def segmented(self, x, y, options, active=0, w_each=None, size=9.8):
        t = self.th
        ws = [w_each or (self.tw(o, size, True) + 20) for o in options]
        total = sum(ws) + 4
        self.r(x, y, total, 24, fill=t.surface_3, rx=6)
        xx = x + 2
        for i, (o, wd) in enumerate(zip(options, ws)):
            if i == active:
                self.r(xx, y + 2, wd, 20, fill=t.surface, stroke=t.border, rx=5)
                self.txt(xx + wd / 2, y + 17, o, bold=True, anchor="ms")
            else:
                self.txt(xx + wd / 2, y + 17, o, bold=False, anchor="ms")
            xx += wd + 2
        return total

    def slider(self, x, y, w, frac=0.5, label=None):
        t = self.th
        self.r(x, y + 3, w, 3, fill=t.surface_3, rx=2)
        self.r(x, y + 3, w * frac, 3, fill=t.accent, rx=2)
        self.c(x + w * frac, y + 4.5, 5.5, t.surface, t.accent, 1.8)
        if label:
            self.txt(x + w + 10, y - 1, label, size=9.8)

    def table(self, x, y, w, headers, widths, rows, row_h=28, head_h=26,
              selected=None, size=10, align=None):
        """rows = liste de dicts {cells:[...], swatch:[idx,color], bold, dim}"""
        t = self.th
        # en-tête
        self.r(x, y, w, head_h, fill=t.surface_2, rx=0)
        cx = x
        align = align or ["l"] * len(headers)
        for hd, ww, al in zip(headers, widths, align):
            self.txt(cx + (10 if al == "l" else ww - 10), y + 17, hd, size=9, bold=True)
            cx += ww
        self.l(x, y + head_h, x + w, y + head_h, fill=t.border)
        # lignes
        for i, row in enumerate(rows):
            ry = y + head_h + i * row_h
            sel = (selected == i)
            if sel:
                self.r(x, ry, w, row_h, fill=t.accent_soft)
                self.r(x, ry, 3, row_h, fill=t.accent)
            elif i % 2 == 1:
                self.r(x, ry, w, row_h, fill=t.surface_2)
            self.l(x, ry + row_h, x + w, ry + row_h, fill=t.border)
            cx = x
            dim = row.get("dim")
            for j, (cell, ww, al) in enumerate(zip(row["cells"], widths, align)):
                col = t.ink if not dim else t.ink_3
                if j == 0 and row.get("bold"):
                    col = t.ink
                if al == "l":
                    px = cx + 10
                    if row.get("swatch") and row["swatch"][0] == j:
                        self.c(px + 4, ry + row_h / 2, 4, row["swatch"][1])
                        px += 15
                    if row.get("check") and j == row.get("check"):
                        self.checkbox(px - 2, ry + row_h / 2 - 6.5,
                                      row.get("checked", True),
                                      size=13, disabled=dim)
                        px += 19
                    self.clip_text(px, ry + row_h / 2 + 3.6,
                                   str(cell), ww - (px - cx) - 12, size,
                                   col, j == 0)
                else:
                    self.txt(cx + ww - 10, ry + row_h / 2 + 3.6, str(cell), bold=False, anchor="rs")
                cx += ww
        return y + head_h + len(rows) * row_h


def switch(c, x, y, on, w=34, h=19):
    """Interrupteur — préféré à la case quand il n'y a qu'un seul choix."""
    t = c.th
    c.r(x, y, w, h, fill=t.accent if on else t.surface_3, rx=h / 2)
    if not on:
        c.r(x, y, w, h, fill=None, stroke=t.border_strong, sw=1, rx=h / 2)
    c.c(x + (w - h / 2 - 2) if on else (x + h / 2 + 2), y + h / 2, h / 2 - 2.5,
        "#FFFFFF")
