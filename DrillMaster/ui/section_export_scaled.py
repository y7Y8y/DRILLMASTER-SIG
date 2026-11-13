"""
Export de la coupe sur page A4 / A3 / A2 / A1 — mise en page automatique.

Deux modes (aucune retouche de l'export PNG existant) :

  * « Ajusté à la page » (défaut) : la coupe est agrandie au maximum dans la
    zone utile ; l'orientation (paysage / portrait) est choisie automatiquement
    selon la forme de la coupe. Échelle affichée : « ≈ 1:N » (exacte, mais
    pas forcément ronde).
  * « Échelle fixe 1:N » : échelle ronde exacte, reportable sur papier
    millimétré. Sur la feuille imprimée à 100 %, 1 mm = N/1000 m.

Dans les deux cas : marges régulières de 10 mm, MÊME cartouche que l'export
habituel (barre de titre, pied de page projet/date/SCR/auteur), légendes et
mini-carte (colonne de droite en paysage, bande basse en portrait), cadre fin,
« Échelle 1:N » et, en option, une barre de contrôle de 100 mm.

Principe technique : le canevas est re-rendu avec une échelle IMPOSÉE
(`canvas._fixed_sx`, px scène / unité) ; 1 px scène = 1/96 pouce = 0,2646 mm ;
la scène est peinte sur une page de taille PHYSIQUE exacte via un peintre mis
à l'échelle dpi/96. Les consignes d'impression restent dans la fenêtre
d'export : elles s'adressent à celui qui imprime, pas à celui qui lit la carte.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qgis.PyQt.QtCore import QMarginsF, QPointF, QRectF, Qt
from qgis.PyQt.QtGui import (
    QColor, QFont, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QPen,
)
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

SCENE_PX_MM = 25.4 / 96.0           # 1 px scène = 1/96 pouce
PAPERS = {                          # paysage : (largeur, hauteur) en mm
    "A4": (297.0, 210.0, "A4"),
    "A3": (420.0, 297.0, "A3"),
    "A2": (594.0, 420.0, "A2"),
    "A1": (841.0, 594.0, "A1"),
}
STD_SCALES = (200, 250, 500, 1000, 1500, 2000, 2500, 5000, 10000, 20000)
UNIT_FACTOR = {"m": 1.0, "km": 1000.0, "ft": 0.3048, "feet": 0.3048,
               "pi": 0.3048, "pieds": 0.3048}
MARGIN_MM = 10.0
HEADER_MM = 17.0            # barre de titre (cartouche) + air
FOOTER_BASE_MM = 17.0       # pied de page (cartouche) + air
CONTROL_MM = 7.0            # barre de contrôle 100 mm (optionnelle)
RIGHT_MM = 74.0             # colonne de droite : légendes + mini-carte
SCALE_TXT_MM = 62.0         # place réservée à « Échelle 1:N » à droite du pied
NATURAL = 1.25              # échelle « naturelle » des images du cartouche
MAX_PIXELS = 80_000_000


def _tr(text):
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("SectionExportScaled", text)


def unit_factor(unit: str) -> float:
    return UNIT_FACTOR.get(str(unit or "m").strip().lower(), 1.0)


def sx_for_scale(n: int, factor: float = 1.0) -> float:
    """px scène par unité de distance pour que 1 mm papier = n/1000 unités."""
    return (1000.0 * factor / float(n)) / SCENE_PX_MM


def page_size(paper: str, orient: str):
    """(largeur, hauteur) en mm ; orient = « landscape » ou « portrait »."""
    w, h, _ = PAPERS[paper]
    return (w, h) if orient == "landscape" else (h, w)


# ------------------------------------------------------------ plan de page
@dataclass
class Layout:
    pw: float
    ph: float
    orient: str
    title: tuple            # (x, y, w, h) mm
    plot: tuple             # zone utile de la coupe
    legend: tuple | None
    locator: tuple | None
    footer: tuple
    scale_txt: tuple
    control_y: float | None


def plan_layout(pw: float, ph: float, legend_mm=None, locator_mm=None,
                control: bool = False) -> Layout:
    """Plan de page en mm (aucun Qt : testable). legend_mm / locator_mm =
    taille NATURELLE (w, h) des images du cartouche, ou None.

    Paysage : colonne de droite (légendes en haut, mini-carte en bas).
    Portrait : bande basse (légendes à gauche, mini-carte à droite).
    """
    m = MARGIN_MM
    inner_w = pw - 2 * m
    landscape = pw >= ph
    title = (m, m, inner_w, HEADER_MM - 2.5)
    foot_y = ph - m - FOOTER_BASE_MM + 2.0
    footer = (m, foot_y, inner_w - SCALE_TXT_MM, 14.5)
    scale_txt = (pw - m - SCALE_TXT_MM, foot_y, SCALE_TXT_MM, 14.5)
    body_top = m + HEADER_MM
    ctl = CONTROL_MM if control else 0.0
    body_h = ph - m - FOOTER_BASE_MM - ctl - body_top
    legend = locator = None
    if landscape:
        col_w = RIGHT_MM if (legend_mm or locator_mm) else 0.0
        x_r = pw - m - col_w
        loc_h = 0.0
        if locator_mm:
            lw = min(col_w, locator_mm[0])
            lh = lw * locator_mm[1] / max(locator_mm[0], 1e-6)
            locator = (x_r + col_w - lw, body_top + body_h - lh, lw, lh)
            loc_h = lh + 3.0
        if legend_mm:
            r = min(1.0, col_w / legend_mm[0], (body_h - loc_h) / legend_mm[1])
            legend = (x_r, body_top, legend_mm[0] * r, legend_mm[1] * r)
        plot = (m, body_top, inner_w - (col_w + 4.0 if col_w else 0.0), body_h)
    else:
        band_h = 0.0
        loc_w = loc_h = 0.0
        lw = lh = 0.0
        if locator_mm:
            loc_w = min(58.0, locator_mm[0])
            loc_h = loc_w * locator_mm[1] / max(locator_mm[0], 1e-6)
        if legend_mm:
            leg_w_max = inner_w - (loc_w + 6.0 if loc_w else 0.0)
            r = min(1.0, leg_w_max / legend_mm[0], 0.34 * body_h / legend_mm[1])
            lw, lh = legend_mm[0] * r, legend_mm[1] * r
        band_h = max(lh, loc_h)
        band_top = body_top + body_h - band_h
        if legend_mm:
            legend = (m, band_top, lw, lh)
        if locator_mm:
            locator = (pw - m - loc_w, band_top + band_h - loc_h, loc_w, loc_h)
        plot = (m, body_top, inner_w, body_h - (band_h + 4.0 if band_h else 0.0))
    control_y = (ph - m - FOOTER_BASE_MM - 2.0) if control else None
    return Layout(pw, ph, "landscape" if landscape else "portrait", title,
                  plot, legend, locator, footer, scale_txt, control_y)


def fits_area(src_w_px: float, src_h_px: float, plot: tuple) -> bool:
    return (src_w_px * SCENE_PX_MM <= plot[2] + 0.01
            and src_h_px * SCENE_PX_MM <= plot[3] + 0.01)


def effective_dpi(paper: str, dpi: int) -> int:
    """Réduit le DPI si l'image dépasserait la mémoire raisonnable."""
    w, h, _ = PAPERS[paper]
    d = int(dpi)
    while (w / 25.4 * d) * (h / 25.4 * d) > MAX_PIXELS and d > 100:
        d = int(d * 0.9)
    return d


def nice_ratio(n: float) -> int:
    """Arrondi d'affichage de « ≈ 1:N » (jamais utilisé pour dessiner)."""
    step = 10 if n < 1000 else (50 if n < 5000 else 100)
    return int(round(n / step) * step)


# ------------------------------------------------------------- composition
def _draw_fit(p, img, rect_mm, mm):
    """Dessine `img` (haute résolution) dans rect_mm (x, y, w, h)."""
    if img is None or img.isNull() or rect_mm is None:
        return
    x, y, w, h = rect_mm
    p.drawImage(QRectF(mm(x), mm(y), mm(w), mm(h)), img)


def compose_scaled_page(scene, src: QRectF, paper: str, ratio_text: str,
                        dpi: int, v_exag: float, layout: Layout,
                        title_img=None, footer_img=None, legend_img=None,
                        locator_img=None, control_bar: bool = False,
                        v_ratio_text: str = "") -> QImage:
    """Page de taille physique exacte ; la scène y est peinte à l'échelle,
    centrée dans la zone utile."""
    pw, ph = layout.pw, layout.ph
    px_w = int(round(pw / 25.4 * dpi))
    px_h = int(round(ph / 25.4 * dpi))
    img = QImage(px_w, px_h, QImage.Format_RGB32)
    img.fill(QColor("#FFFFFF"))
    # 96 ppp pendant le dessin : les polices de la scène gardent leur taille.
    img.setDotsPerMeterX(int(96 / 0.0254))
    img.setDotsPerMeterY(int(96 / 0.0254))
    z = dpi / 96.0
    p = QPainter(img)
    try:
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        p.scale(z, z)                           # unités = px CSS (1/96 po)
        mm = lambda v: v / SCENE_PX_MM          # noqa: E731  mm -> px CSS
        # --- cartouche : barre de titre (identique à l'export habituel) --
        _draw_fit(p, title_img, layout.title, mm)
        # --- coupe, centrée dans la zone utile --------------------------
        px, py, pwid, phei = layout.plot
        sw_mm, sh_mm = src.width() * SCENE_PX_MM, src.height() * SCENE_PX_MM
        ox = px + max(pwid - sw_mm, 0.0) / 2.0
        oy = py + max(phei - sh_mm, 0.0) / 2.0
        scene.render(p, QRectF(mm(ox), mm(oy), src.width(), src.height()), src,
                     Qt.IgnoreAspectRatio)
        # --- légendes + mini-carte -----------------------------------------
        _draw_fit(p, legend_img, layout.legend, mm)
        if locator_img is not None and layout.locator is not None:
            lx, ly, lw, lh = layout.locator
            p.setPen(QPen(QColor("#B0B8C0"), 0.8))
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(mm(lx) - 1, mm(ly) - 1, mm(lw) + 2, mm(lh) + 2))
            _draw_fit(p, locator_img, layout.locator, mm)
        # --- barre de contrôle 100 mm (optionnelle, sans phrase) ----------
        if control_bar and layout.control_y is not None:
            x0 = mm(MARGIN_MM)
            by = mm(layout.control_y)
            p.setPen(QPen(QColor("#1b2430"), 1.0))
            p.drawLine(QPointF(x0, by), QPointF(x0 + mm(100.0), by))
            for kk in range(0, 101):
                tl = 3.6 if kk % 10 == 0 else (2.4 if kk % 5 == 0 else 1.3)
                p.drawLine(QPointF(x0 + mm(kk), by),
                           QPointF(x0 + mm(kk), by - mm(tl)))
            fc = QFont("Segoe UI")
            fc.setPixelSize(int(mm(2.8)))
            p.setFont(fc)
            p.drawText(QPointF(x0 + mm(102.0), by), "100 mm")
        # --- cartouche : pied de page (projet · date · SCR · auteur) -----
        _draw_fit(p, footer_img, layout.footer, mm)
        # --- seule info d'échelle sur la carte -----------------------------
        f = QFont("Segoe UI")
        f.setPixelSize(int(mm(4.4)))
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#1b2430"))
        sx_, sy_, sw_, sh_ = layout.scale_txt
        p.drawText(QRectF(mm(sx_), mm(sy_), mm(sw_), mm(7.0)),
                   Qt.AlignRight | Qt.AlignVCenter,
                   _tr("Échelle {r}").format(r=ratio_text))
        exag = float(v_exag or 1.0)
        if abs(exag - 1.0) > 1e-6 and v_ratio_text:
            f.setBold(False)
            f.setPixelSize(int(mm(3.4)))
            p.setFont(f)
            p.drawText(QRectF(mm(sx_), mm(sy_ + 7.0), mm(sw_), mm(6.0)),
                       Qt.AlignRight | Qt.AlignVCenter,
                       _tr("Vertical {r} (exagération ×{e:g})").format(
                           r=v_ratio_text, e=exag))
        # --- cadre fin autour de la page ---------------------------------
        p.setPen(QPen(QColor("#9aa4b0"), 0.8))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(mm(MARGIN_MM / 2), mm(MARGIN_MM / 2),
                          mm(pw - MARGIN_MM), mm(ph - MARGIN_MM)))
    finally:
        p.end()
    d = int(dpi / 0.0254 + 0.5)
    img.setDotsPerMeterX(d)
    img.setDotsPerMeterY(d)
    return img


def save_page(img: QImage, base: str, paper: str, orient: str, dpi: int,
              want_pdf: bool, want_png: bool):
    """Écrit PDF (page à la taille exacte) et/ou PNG (DPI intégré)."""
    out = []
    if want_png:
        pth = base + ".png"
        if not img.save(pth, "PNG"):
            raise OSError(_tr("Écriture PNG impossible : {}").format(pth))
        out.append(pth)
    if want_pdf:
        pth = base + ".pdf"
        w = QPdfWriter(pth)
        w.setResolution(int(dpi))
        w.setPageLayout(QPageLayout(
            QPageSize(getattr(QPageSize, PAPERS[paper][2])),
            QPageLayout.Landscape if orient == "landscape"
            else QPageLayout.Portrait, QMarginsF(0, 0, 0, 0)))
        pp = QPainter(w)
        try:
            pp.drawImage(QRectF(0, 0, w.width(), w.height()), img)
        finally:
            pp.end()
        out.append(pth)
    return out


# ------------------------------------------------------------- orchestration
def _cartouche_images(dock, paper, dpi, legends, locator):
    """Titre / pied / légendes / mini-carte : les MÊMES fonctions que l'export
    habituel, générées à haute résolution (nettes à 300 ppp). Les largeurs
    de titre/pied sont fixées plus tard (on regénère selon l'orientation)."""
    g = min(3.4, max(1.4, dpi / 96.0))           # résolution de génération
    out = {"gen": g, "legend": None, "locator": None}
    if legends:
        try:
            out["legend"] = dock._paint_legends_image(
                col_w=int(240 * g / NATURAL), scale=g, target_height=0)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export page : légendes", _exc)
    if locator:
        try:
            out["locator"] = dock._paint_locator_map(size=700, scale=1.0)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export page : mini-carte", _exc)
    return out


def _natural_mm(img, gen):
    """Taille (mm) d'une image du cartouche à son échelle naturelle."""
    if img is None or img.isNull():
        return None
    k = NATURAL / max(float(gen), 1e-6)
    return (img.width() * k * SCENE_PX_MM, img.height() * k * SCENE_PX_MM)


def _locator_mm(img):
    """La mini-carte est générée à scale=1.0 : 1 px = 1 px CSS."""
    if img is None or img.isNull():
        return None
    return (img.width() * SCENE_PX_MM * NATURAL, img.height() * SCENE_PX_MM * NATURAL)


def _title_footer(dock, layout, gen):
    k = NATURAL / gen
    tw = int(layout.title[2] / SCENE_PX_MM / k)
    fw = int(layout.footer[2] / SCENE_PX_MM / k)
    t = f = None
    try:
        t = dock._paint_export_title(tw, scale=gen)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export page : titre", _exc)
    try:
        f = dock._paint_export_footer(fw, scale=gen)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export page : pied de page", _exc)
    return t, f


def run_scaled_export(dock, base: str, paper: str, n, dpi: int,
                      want_pdf: bool, want_png: bool, legends: bool,
                      locator: bool = True, control_bar: bool = False,
                      orientation: str = "auto"):
    """Retourne (ok, message).

    n = "fit"  → ajusté à la page (agrandi au maximum) ;
    n = None   → échelle ronde automatique (la plus grande qui tient) ;
    n = entier → échelle fixe 1:n (refuse si la coupe ne tient pas).
    orientation : « auto » (choisie selon la forme), « landscape », « portrait ».
    """
    from .section_export import export_scene_rect
    canvas = dock.canvas
    if canvas is None or not getattr(canvas, "_result", None):
        return False, _tr("Aucune coupe générée.")
    factor = unit_factor(getattr(canvas, "_distance_unit", "m"))
    eff = effective_dpi(paper, dpi)
    imgs = _cartouche_images(dock, paper, eff, legends, locator)
    leg_mm = _natural_mm(imgs["legend"], imgs["gen"])
    loc_mm = _locator_mm(imgs["locator"])
    orients = (["landscape", "portrait"] if orientation == "auto"
               else [orientation])
    layouts = {o: plan_layout(*page_size(paper, o), leg_mm, loc_mm, control_bar)
               for o in orients}
    prev_fixed = getattr(canvas, "_fixed_sx", None)
    prev_txt = getattr(canvas, "_scale_ratio_text", "")

    def measure(sx, label):
        canvas._fixed_sx = float(sx)
        canvas._scale_ratio_text = label
        canvas._render()
        return export_scene_rect(dock, canvas)

    def ratio_of(sx):                        # N équivalent (1 mm = N/1000 unités)
        return 1000.0 * factor / (sx * SCENE_PX_MM)

    try:
        if hasattr(canvas, "set_outline_export_mode"):
            canvas.set_outline_export_mode(True)
        chosen_o, chosen_sx, label, ratio_txt = None, None, "", ""
        if n == "fit":
            # modèle linéaire (2 rendus) → orientation → affinage par dichotomie
            sxa, sxb = sx_for_scale(2000, factor), sx_for_scale(500, factor)
            ra, rb = measure(sxa, ""), measure(sxb, "")
            wk = (rb.width() - ra.width()) / (sxb - sxa)
            hk = (rb.height() - ra.height()) / (sxb - sxa)
            w0, h0 = ra.width() - wk * sxa, ra.height() - hk * sxa
            if wk <= 0 or hk <= 0:
                return False, _tr("Mise en page automatique impossible pour "
                                  "cette coupe.")
            est = {}
            for o, lay in layouts.items():
                aw, ah = lay.plot[2] / SCENE_PX_MM, lay.plot[3] / SCENE_PX_MM
                est[o] = min((aw - w0) / wk, (ah - h0) / hk)
            chosen_o = max(est, key=lambda o: est[o])
            lay = layouts[chosen_o]
            lo, hi = est[chosen_o] * 0.6, est[chosen_o] * 1.5
            r = measure(lo, "")
            while not fits_area(r.width(), r.height(), lay.plot) and lo > 0.05:
                lo *= 0.7
                r = measure(lo, "")
            for _ in range(8):
                mid = 0.5 * (lo + hi)
                r = measure(mid, "")
                if fits_area(r.width(), r.height(), lay.plot):
                    lo = mid
                else:
                    hi = mid
            chosen_sx = lo
            ratio_txt = "≈ 1:{}".format(nice_ratio(ratio_of(lo)))
            label = ratio_txt
        else:
            cands = [n] if n else list(STD_SCALES)
            if n:
                cands += [c for c in STD_SCALES if c > n]
            first = None
            for cand in cands:
                r = measure(sx_for_scale(cand, factor), f"1:{cand}")
                for o in orients:
                    if fits_area(r.width(), r.height(), layouts[o].plot):
                        first, chosen_o = cand, o
                        break
                if first is not None:
                    break
            if first is None:
                return False, _tr(
                    "La coupe ne tient sur aucune échelle standard en {p} — "
                    "choisissez un format plus grand.").format(p=paper)
            if n and first != n:
                return False, _tr(
                    "À 1:{n} la coupe ne tient pas sur une page {p}. "
                    "Échelle la plus grande possible : 1:{s}.").format(
                        n=n, p=paper, s=first)
            chosen_sx = sx_for_scale(first, factor)
            ratio_txt = f"1:{first}"
            label = ratio_txt
        # rendu final (échelle retenue) + cartouche à la largeur de l'orientation
        lay = layouts[chosen_o]
        src = measure(chosen_sx, label)
        title_img, footer_img = _title_footer(dock, lay, imgs["gen"])
        exag = float(getattr(canvas, "_v_exag", 1.0) or 1.0)
        nn = ratio_of(chosen_sx)
        v_txt = ("≈ " if n == "fit" else "") + "1:{}".format(
            nice_ratio(nn / exag) if n == "fit" else f"{nn / exag:g}")
        img = compose_scaled_page(
            canvas.scene, src, paper, ratio_txt, eff, exag, lay, title_img,
            footer_img, imgs["legend"], imgs["locator"], control_bar, v_txt)
        files = save_page(img, base, paper, chosen_o, eff, want_pdf, want_png)
        orient_txt = _tr("paysage") if chosen_o == "landscape" else _tr("portrait")
        msg = _tr("Export sur {p} {o} — échelle {r} ({d} ppp) :\n{f}").format(
            p=paper, o=orient_txt, r=ratio_txt, d=eff, f="\n".join(files))
        if eff != dpi:
            msg += _tr("\n(résolution réduite de {a} à {b} ppp : page très "
                       "grande)").format(a=dpi, b=eff)
        msg += _tr("\n\nPour que 1 mm de papier = {m:g} m de terrain, "
                   "imprimez à 100 % (« taille réelle »), sans « ajuster à "
                   "la page ».").format(m=ratio_of(chosen_sx) / 1000.0)
        return True, msg
    finally:
        try:
            if hasattr(canvas, "set_outline_export_mode"):
                canvas.set_outline_export_mode(False)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export page : retour mode écran", _exc)
        canvas._fixed_sx = prev_fixed
        canvas._scale_ratio_text = prev_txt
        try:
            canvas._render()          # retour à l'affichage écran
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export page : re-rendu écran", _exc)


# ------------------------------------------------------------------ dialogue
def export_scaled_dialog(dock):
    canvas = getattr(dock, "canvas", None)
    if canvas is None or not getattr(canvas, "_result", None):
        QMessageBox.information(
            dock, _tr("Export en page"),
            _tr("Aucune coupe générée. Tracez et générez une coupe d'abord."))
        return
    name = "coupe"
    line = getattr(dock, "_line", None)
    if line is not None and getattr(line, "name", None):
        name = "".join(c if c.isalnum() or c in "-_" else "_"
                       for c in str(line.name)) or name
    start_dir = ""
    try:
        project = dock._project() if hasattr(dock, "_project") else None
        if project is not None:
            start_dir = str(getattr(project.paths, "project_dir", "") or "")
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export page : dossier projet", _exc)
    base0 = str(Path(start_dir) / f"{name}_page") if start_dir else f"{name}_page"

    dlg = QDialog(dock)
    dlg.setWindowTitle(_tr("Exporter en page (A4 / A3 / échelle)"))
    dlg.setMinimumWidth(500)
    lay = QVBoxLayout(dlg)
    info = QLabel(_tr(
        "Mise en page automatique sur une page de taille exacte, avec les "
        "mêmes titre, pied de page, légendes et mini-carte que l'export "
        "habituel. En « échelle fixe », imprimez à 100 % (« taille réelle ») "
        ": 1 mm de papier = N/1000 m de terrain."))
    info.setWordWrap(True)
    lay.addWidget(info)

    row = QHBoxLayout()
    row.addWidget(QLabel(_tr("Papier")))
    paper_box = QComboBox()
    for k in ("A3", "A4", "A2", "A1"):
        paper_box.addItem(f"{k}  ({int(PAPERS[k][0])}×{int(PAPERS[k][1])} mm)", k)
    row.addWidget(paper_box)
    row.addWidget(QLabel(_tr("Orientation")))
    orient_box = QComboBox()
    orient_box.addItem(_tr("Automatique"), "auto")
    orient_box.addItem(_tr("Paysage"), "landscape")
    orient_box.addItem(_tr("Portrait"), "portrait")
    row.addWidget(orient_box)
    lay.addLayout(row)

    row1 = QHBoxLayout()
    row1.addWidget(QLabel(_tr("Échelle")))
    scale_box = QComboBox()
    # 391 — échelle de projet commune (config « section_scale ») : proposée
    # et choisie par défaut → toutes les coupes exportées sont comparables.
    proj_ratio = 0
    try:
        cfg = (getattr(getattr(getattr(dock, "main_dock", None), "project", None),
                       "config", None) or {})
        proj_ratio = int((cfg.get("section_scale") or {}).get("ratio") or 0)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export page : échelle de projet", _exc)
    if proj_ratio:
        scale_box.addItem(_tr("Échelle du projet (1:{n})").format(n=proj_ratio),
                          proj_ratio)
    scale_box.addItem(_tr("Ajustée à la page (échelle variable)"), "fit")
    scale_box.addItem(_tr("Ronde automatique (la plus grande qui tient)"), 0)
    for sc in STD_SCALES:
        scale_box.addItem(f"1:{sc}", sc)
    row1.addWidget(scale_box, 1)
    lay.addLayout(row1)

    row2 = QHBoxLayout()
    row2.addWidget(QLabel(_tr("Format")))
    fmt_box = QComboBox()
    fmt_box.addItem(_tr("PDF + PNG"), "both")
    fmt_box.addItem("PDF", "pdf")
    fmt_box.addItem("PNG", "png")
    row2.addWidget(fmt_box)
    row2.addWidget(QLabel(_tr("Résolution")))
    dpi_box = QComboBox()
    for d in (300, 200, 600):
        dpi_box.addItem(f"{d} ppp", d)
    row2.addWidget(dpi_box)
    row2.addStretch(1)
    lay.addLayout(row2)

    chk_leg = QCheckBox(_tr("Inclure les légendes"))
    chk_leg.setChecked(True)
    lay.addWidget(chk_leg)
    chk_map = QCheckBox(_tr("Inclure la mini-carte (localisation)"))
    chk_map.setChecked(True)
    lay.addWidget(chk_map)
    chk_ctl = QCheckBox(_tr(
        "Ajouter une barre de contrôle de 100 mm (pour vérifier l'impression)"))
    chk_ctl.setChecked(False)
    lay.addWidget(chk_ctl)

    prow = QHBoxLayout()
    path_edit = QLineEdit(base0)
    prow.addWidget(path_edit, 1)
    browse = QPushButton(_tr("Parcourir…"))

    def _browse():
        pth, _ = QFileDialog.getSaveFileName(
            dlg, _tr("Nom de base du fichier"), path_edit.text(), "")
        if pth:
            for ext in (".pdf", ".png"):
                if pth.lower().endswith(ext):
                    pth = pth[:-len(ext)]
            path_edit.setText(pth)

    browse.clicked.connect(_browse)
    prow.addWidget(browse)
    lay.addLayout(prow)

    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    lay.addWidget(bb)
    if dlg.exec_() != QDialog.Accepted:
        return

    base = path_edit.text().strip()
    for ext in (".pdf", ".png"):
        if base.lower().endswith(ext):
            base = base[:-len(ext)]
    fmt = fmt_box.currentData()
    sc = scale_box.currentData()
    try:
        ok, msg = run_scaled_export(
            dock, base, paper_box.currentData(), ("fit" if sc == "fit" else (sc or None)),
            int(dpi_box.currentData()), fmt in ("both", "pdf"),
            fmt in ("both", "png"), chk_leg.isChecked(),
            chk_map.isChecked(), chk_ctl.isChecked(), orient_box.currentData())
    except Exception as exc:                      # jamais de crash silencieux
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export en page", exc)
        ok, msg = False, str(exc)
    (QMessageBox.information if ok else QMessageBox.warning)(
        dock, _tr("Export en page"), msg)
