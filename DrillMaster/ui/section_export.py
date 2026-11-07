"""DrillMaster — Export PNG/SVG de la coupe 2D (volet 3, v2.9.160).

Toute la MÉCANIQUE d'export extraite de ``ui/section_dock.py``
(SPEC de restructuration — retour écran : « alléger les fonctions pour
mieux les gérer quand y'aura les bugs ») : dialogue, rendu de scène,
rognage des marges, légendes peintes, cartouche, mini-carte de
localisation, composition de page, tampon locator, PNG haute
résolution et SVG.

Le dock délègue à une ligne — comportement identique, code séparé.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from qgis.PyQt.QtCore import QPointF, QRectF, Qt, QTimer
from qgis.PyQt.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QImage, QPainter, QPen, QPolygonF,
    QPixmap,
)
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QDialog, QDialogButtonBox, QFileDialog,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSlider,
    QSpinBox, QVBoxLayout,
)

from ..core import multi_assay as multi_assay_mod
from ..core import threshold_rule as threshold_rule_mod
from ..core.structure_classify import structure_family
from ..core.section import (
    ASSAY_RAMPS, assay_ramp_rgb, assay_scale_classes, classify_assay,
    get_all_litho_codes, get_litho_style,
)
from .section_dock import (
    SELECTION_HIGHLIGHT_COLOR, SectionCanvas, _export_smallcaps_font,
    make_collapsible_help,
)
from .styles_qt import COLORS


def _tr(text):
    """v2.9.233 — Lot 1c : traduction (fonctions module — pas de self)."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("SectionExport", text)



def export_view_png(dock, *_args):
    """v2.9.67+ — export PNG uniquement (plus de SVG)."""
    canvas = getattr(dock, "canvas", None)
    if canvas is None or getattr(canvas, "scene", None) is None:
        QMessageBox.warning(
            dock, _tr("Exporter"), _tr("Aucune vue coupe à exporter."))
        return
    if not getattr(canvas, "_result", None):
        QMessageBox.information(
            dock, _tr("Exporter"),
            _tr("Aucune coupe générée. Tracez et générez une coupe d'abord."))
        return

    default_name = _tr("coupe")
    line = getattr(dock, "_line", None)
    if line is not None and getattr(line, "name", None):
        safe = "".join(
            c if c.isalnum() or c in "-_" else "_"
            for c in str(line.name))
        default_name = safe or default_name
    start_dir = ""
    project = dock._project() if hasattr(dock, "_project") else None
    if project is not None:
        try:
            start_dir = str(getattr(project.paths, "project_dir", "") or "")
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : entrée du dialogue PNG", _exc)
            # dossier projet indisponible
            start_dir = ""
    start_path = (
        str(Path(start_dir) / f"{default_name}.png")
        if start_dir else f"{default_name}.png")

    dlg_res = dock._export_png_dialog(start_path)
    # compat : 2 / 4 valeurs
    if not dlg_res or not dlg_res[0]:
        return
    if len(dlg_res) == 2:
        path, include_legends = dlg_res
        include_map = True
    else:
        path, include_legends = dlg_res[0], dlg_res[1]
        include_map = dlg_res[3] if len(dlg_res) > 3 else (
            dlg_res[2] if len(dlg_res) == 3 and isinstance(dlg_res[2], bool)
            else True)
        # ancien 4-tuple (path, legends, fmt, map) — ignorer fmt
        if len(dlg_res) >= 4:
            include_map = bool(dlg_res[3])

    dock._export_pending_path = path
    dock._export_pending_legends = bool(include_legends)
    dock._export_pending_fmt = "png"
    dock._export_pending_map = bool(include_map)
    QTimer.singleShot(50, dock._run_deferred_export)


def run_deferred_export(dock):
    """Rendu différé — isole le travail du clic UI."""
    path = getattr(dock, "_export_pending_path", None)
    include_legends = bool(getattr(dock, "_export_pending_legends", False))
    include_map = bool(getattr(dock, "_export_pending_map", True))
    dock._export_pending_path = None
    dock._export_pending_fmt = "png"
    if not path:
        return
    # toujours .png
    if not str(path).lower().endswith(".png"):
        path = str(path) + ".png"
    ok, err = False, "inconnu"
    try:
        from qgis.PyQt.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.setOverrideCursor(Qt.WaitCursor)
            app.processEvents()
        ok, err = dock._render_canvas_to_png(
            path, include_legends=include_legends,
            fmt="png", include_map=include_map)
    except BaseException as exc:  # noqa: BLE001 — y compris SystemExit?
        # Ne pas laisser remonter : log + message
        ok, err = False, repr(exc)
        try:
            log_p = Path(path).with_suffix(".export_error.txt")
            log_p.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : rendu différé (QTimer)", _exc)
            # log impossible
            pass
    finally:
        try:
            from qgis.PyQt.QtWidgets import QApplication
            app = QApplication.instance()
            if app is not None:
                app.restoreOverrideCursor()
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : rendu différé (QTimer)", _exc)
            # curseur
            pass
    try:
        if ok:
            QMessageBox.information(
                dock, _tr("Exporter"),
                _tr("Image enregistrée :\n{}").format(path))
        else:
            QMessageBox.warning(
                dock, _tr("Exporter"),
                _tr("Échec export (QGIS reste ouvert) :\n{}").format(err))
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : rendu différé (QTimer)", _exc)
        # message box échoue — ignorer
        pass


class _LocPreview(QLabel):
    """v2.9.321 — aperçu glissable de la carte en plan (dialogue
    d'export) : déplacer la souris = centrer la zone exportée."""

    def __init__(self, state, span_fn, sync_fn):
        super().__init__()
        self._last = None
        self.state = state
        self.span_cb = span_fn
        self.sync_cb = sync_fn
        self.setFixedSize(190, 208)
        self.setStyleSheet("border:1px solid #B0B8C0;background:#FFFFFF;")

    def mousePressEvent(self, ev):
        self._last = (ev.x(), ev.y())

    def mouseMoveEvent(self, ev):
        if self._last is None:
            return
        dxp, dyp = ev.x() - self._last[0], ev.y() - self._last[1]
        self._last = (ev.x(), ev.y())
        mpp = self.span_cb() / 134.0
        self.state["off"][0] -= dxp * mpp
        self.state["off"][1] += dyp * mpp
        self.sync_cb()


def export_png_dialog(dock, start_path: str):
    """Dialogue : chemin PNG + légendes + mini-carte.

    Retourne (path, include_legends, "png", include_map).
    PNG uniquement (pas de SVG).
    """
    dlg = QDialog(dock)
    dlg.setWindowTitle(_tr("Exporter la coupe (PNG)"))
    dlg.setMinimumWidth(460)
    lay = QVBoxLayout(dlg)
    lay.addWidget(make_collapsible_help(
        _tr("Export PNG haute définition de la coupe. "
            "Options : légendes à droite, mini-carte de localisation.")))

    base = start_path
    for ext in (".png", ".svg", ".PNG", ".SVG"):
        if base.lower().endswith(ext.lower()):
            base = base[: -len(ext)]
            break

    path_row = QHBoxLayout()
    path_edit = QLineEdit(base + ".png")
    path_row.addWidget(path_edit, 1)
    browse = QPushButton(_tr("Parcourir…"))

    def _browse():
        pth, _ = QFileDialog.getSaveFileName(
            dlg, _tr("Exporter la coupe (PNG)"),
            path_edit.text() or (base + ".png"),
            _tr("Image PNG (*.png)"))
        if pth:
            if not pth.lower().endswith(".png"):
                pth = pth + ".png"
            path_edit.setText(pth)

    browse.clicked.connect(_browse)
    path_row.addWidget(browse)
    lay.addLayout(path_row)

    chk = QCheckBox(_tr("Inclure les légendes (à droite)"))
    chk.setChecked(True)
    lay.addWidget(chk)
    chk_map = QCheckBox(_tr("Inclure la mini-carte (localisation + buffer)"))
    chk_map.setChecked(True)
    lay.addWidget(chk_map)

    # v2.9.321 — cadrage de la carte en plan (EXPORT seulement) :
    # curseur de zoom (100 % = cadrage initial sobre v316 → 300 % =
    # vue élargie « miniaturisée ») + aperçu que l'on GLISSE pour
    # centrer la zone voulue.  Le buffer et les étiquettes suivent,
    # anti-chevauchement conservé.
    init_zoom = max(1.0, min(10.0, float(
        getattr(dock, "_locator_zoom", 1.0) or 1.0)))
    init_all = bool(getattr(dock, "_locator_all", False))
    init_off = tuple(getattr(dock, "_locator_off", (0.0, 0.0))
                     or (0.0, 0.0))
    state = {"off": [float(init_off[0]), float(init_off[1])]}

    map_title = QLabel(_tr("Carte en plan — cadrage (export) :"))
    lay.addWidget(map_title)

    zoom_row = QHBoxLayout()
    zoom_row.addWidget(QLabel(_tr("Zoom")))
    zoom_slider = QSlider(Qt.Horizontal)
    zoom_slider.setRange(100, 1000)  # 329 : cadrer soi-même au secteur
    zoom_slider.setSingleStep(10)
    zoom_slider.setValue(int(round(init_zoom * 100)))
    zoom_row.addWidget(zoom_slider, 1)
    zoom_pct = QLabel("%i %%" % zoom_slider.value())
    zoom_row.addWidget(zoom_pct)
    reset_btn = QPushButton(_tr("Recadrer"))
    zoom_row.addWidget(reset_btn)
    lay.addLayout(zoom_row)
    chk_all = QCheckBox(_tr("Tous les forages (zone entière)"))
    chk_all.setToolTip(_tr(
        "Défaut : cadre sobre + alentours proches.  Coché : l'emprise "
        "englobe TOUS les forages du projet."))
    chk_all.setChecked(init_all)
    lay.addWidget(chk_all)
    # 339 — « il affiche souvent en portrait ? » : page PAYSAGE par
    # défaut quand la coupe est plus haute que large (coupe courte et
    # profonde) — rien n'est déformé, la page est élargie et la coupe
    # centrée, comme à l'écran.
    init_land = bool(getattr(dock, "_export_landscape", True))
    chk_land = QCheckBox(_tr(
        "Page paysage si la coupe est plus haute que large"))
    chk_land.setToolTip(_tr(
        "Une coupe courte et profonde (ex. 60 m de long, 80 m de "
        "profond) donne sinon une page portrait.  La page est "
        "élargie au format paysage et la coupe centrée — aucune "
        "déformation des échelles."))
    chk_land.setChecked(init_land)
    lay.addWidget(chk_land)

    def _span_est():
        try:
            ln = float(getattr(dock, "_line", None).length)
        except Exception as exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : estimation fenêtre carte", exc)
            ln = 250.0
        try:
            bf = max(1.0, float(dock.buffer_spin.value()))
        except Exception as exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : buffer pour fenêtre carte", exc)
            bf = 50.0
        return (ln + 2.0 * bf) * 1.22 * (zoom_slider.value() / 100.0)

    def _sync():
        dock._locator_zoom = zoom_slider.value() / 100.0
        dock._locator_off = (state["off"][0], state["off"][1])
        dock._locator_all = chk_all.isChecked()
        dock._export_landscape = chk_land.isChecked()
        zoom_pct.setText("%i %%" % zoom_slider.value())
        try:
            img = paint_locator_map(dock, size=150, scale=1.0)
            if img is not None and not img.isNull():
                preview.setPixmap(QPixmap.fromImage(img))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : aperçu du cadrage carte", _exc)

    preview = _LocPreview(state, _span_est, _sync)
    zoom_slider.valueChanged.connect(lambda _v: _sync())

    def _reset():
        zoom_slider.setValue(100)
        state["off"] = [0.0, 0.0]
        _sync()

    reset_btn.clicked.connect(_reset)
    map_row = QHBoxLayout()
    map_row.addWidget(preview)
    map_row.addWidget(QLabel(_tr(
        "Glissez la carte pour centrer la zone à exporter.\n"
        "Le cadrage s'applique à la mini-carte de l'export\n"
        "uniquement — l'écran reste au cadrage initial.")), 1)
    lay.addLayout(map_row)
    _sync()

    # 331 — l'auteur se rentre ICI, au moment de l'export (il est
    # aussi dans le panneau Orientation, groupe « Orientation »).
    author_row = QHBoxLayout()
    author_row.addWidget(QLabel(_tr("Auteur (cartouche)")))
    author_edit = QLineEdit()
    author_edit.setMaxLength(80)
    try:
        author_edit.setText(str(
            dock.orientation_author.text() or "").strip())
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : auteur pré-rempli", _exc)
    author_row.addWidget(author_edit, 1)
    lay.addLayout(author_row)

    buttons = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    # 341 — boutons standards FORCÉS dans notre langue : sinon Qt
    # branche sa propre locale et l'on obtient le franglais vu à
    # l'écran (« OK » / « Annuler » en mode ENG).
    buttons.button(QDialogButtonBox.Ok).setText(_tr("OK"))
    buttons.button(QDialogButtonBox.Cancel).setText(_tr("Annuler"))
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    lay.addWidget(buttons)
    if dlg.exec_() != QDialog.Accepted:
        # Annuler = rien ne change (cadrage antérieur restauré)
        dock._locator_zoom = init_zoom
        dock._locator_off = init_off
        dock._locator_all = init_all
        dock._export_landscape = init_land
        return "", False, "png", True
    try:
        dock.orientation_author.setText(author_edit.text().strip())
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : auteur recopié vers le panneau", _exc)
    path = path_edit.text().strip()
    if not path:
        return "", False, "png", True
    if not path.lower().endswith(".png"):
        path = path + ".png"
    return path, chk.isChecked(), "png", chk_map.isChecked()


def export_scene_rect(dock, canvas):
    """Emprise items (pas viewport)."""
    scene = canvas.scene
    if scene is None:
        return QRectF()
    try:
        br = scene.itemsBoundingRect()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : rectangle de scène à rendre", _exc)
        br = QRectF()
    if br.isValid() and br.width() > 2 and br.height() > 2:
        # v2.9.57 — marge un peu plus haute pour topo / étiquettes
        return br.adjusted(-6.0, -10.0, 6.0, 10.0)  # v2.9.68 : air vertical = 2 m plot
    try:
        sr = scene.sceneRect()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : rectangle de scène à rendre", _exc)
        return QRectF()
    if sr.isValid() and sr.width() > 2 and sr.height() > 2:
        return QRectF(sr)
    return QRectF()


def crop_white_margins(img, bg_rgb = (255, 255, 255), tol = 14, pad = 4):
    """Rogner le blanc des bords — scan depuis les bords (sûr).

    v2.9.46 : ``QImage.pixel()`` uniquement (pas constBits/memoryview).
    On avance depuis chaque bord avec un pas ; pas de parcours total.
    """
    if img is None or img.isNull():
        return img
    try:
        w, h = img.width(), img.height()
        if w < 16 or h < 16:
            return img
        # éviter travail monstre (ultra-HD : seuil relevé)
        if w * h > 40_000_000:
            return img
        br, bg, bb = bg_rgb
        step = 2 if w * h > 2_000_000 else 1

        def is_bg_px(x, y):
            c = img.pixel(x, y)
            # qRgb packed: use QColor for portability
            qc = QColor(c)
            return (abs(qc.red() - br) <= tol
                    and abs(qc.green() - bg) <= tol
                    and abs(qc.blue() - bb) <= tol)

        def row_bg(y, x0, x1):
            for x in range(x0, x1 + 1, step):
                if not is_bg_px(x, y):
                    return False
            return True

        def col_bg(x, y0, y1):
            for y in range(y0, y1 + 1, step):
                if not is_bg_px(x, y):
                    return False
            return True

        top, bottom = 0, h - 1
        left, right = 0, w - 1
        # max trim : bas moins agressif (pied + mini-carte)
        max_trim_top = h * 30 // 100
        # bas : peu agressif — protège eoh + axe distance (marge OK)
        max_trim_bottom = h * 8 // 100
        max_trim_x = w * 30 // 100
        while top < bottom and top < max_trim_top and row_bg(top, left, right):
            top += step
        while bottom > top and (h - 1 - bottom) < max_trim_bottom and row_bg(bottom, left, right):
            bottom -= step
        while left < right and left < max_trim_x and col_bg(left, top, bottom):
            left += step
        while right > left and (w - 1 - right) < max_trim_x and col_bg(right, top, bottom):
            right -= step

        top = max(0, top - pad)
        left = max(0, left - pad)
        bottom = min(h - 1, bottom + pad)
        right = min(w - 1, right + pad)
        cw = right - left + 1
        ch = bottom - top + 1
        if cw < 32 or ch < 32:
            return img
        if cw >= w - 2 and ch >= h - 2:
            return img
        return img.copy(left, top, cw, ch)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : rognage des marges blanches", _exc)
        # crop optionnel — image non rognée si échec
        return img


def grab_legends_image(dock):
    return dock._paint_legends_image()


def paint_legends_image(dock, col_w = 240, scale = 1.25, target_height = 0):
    """Légendes export : motifs + altérations, sans crash."""
    try:
        return dock._paint_legends_image_impl(col_w, scale)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : légendes (image)", _exc)
        # légendes optionnelles — export coupe seule
        return None


def paint_legends_image_impl(dock, col_w = 260, scale = 1.5):
    """Légende export fidèle au panneau (symboles + petites caps).

    v2.9.45 :
      - forage = trait fin couleur trajectoire (#393939 défaut) ;
      - collet = POINT rouge seul (pas de trait + pastille) ;
      - barrette secondaire + veine comme panneau ;
      - libellés SmallCaps.
    """
    s = max(min(float(scale), 4.5), 1.0)
    pad = int(8 * s)
    # v2.9.65 — lignes un peu plus hautes pour le corps +1 pt
    row_h = int(21 * s)
    sec_h = int(21 * s)
    title_h = int(25 * s)
    sw_w, sw_h = int(32 * s), int(18 * s)
    # v2.9.65 — un cran plus lisible (SmallCaps lit plus petit) ;
    # planchers + coeffs un peu plus hauts, sans élargir la colonne.
    font_title = _export_smallcaps_font(
        max(15, int(13 * s * 0.78)), bold=True)
    font_sec = _export_smallcaps_font(
        max(13, int(11 * s * 0.78)), bold=True)
    font_body = _export_smallcaps_font(
        max(12, int(10 * s * 0.78)), bold=False)
    font_badge = _export_smallcaps_font(
        max(12, int(9 * s * 0.78)), bold=True)
    primary = QColor(COLORS.get("primary", "#2C3E50"))
    ink = QColor(COLORS.get("text_dark", "#2C3E50"))
    if not ink.isValid():
        ink = QColor("#2C3E50")

    blocks = []  # (title, rows, kind)

    # 1 Symboles — MÊME jeu que _fill_symbols_legend
    sym = []
    if getattr(dock.canvas, "_show_trajectory", True):
        traj_c = getattr(dock.canvas, "_trajectory_color", "#393939") or "#393939"
        traj_w = max(0.8, float(getattr(dock.canvas, "_trajectory_width", 0.5) or 0.5))
        sym.append(("traj", _tr("Forage (trajectoire)"), traj_c, traj_w))
    if dock.canvas._result and dock.canvas._result.holes:
        sym.append(("collar", _tr("Collet (point de forage)"), None, None))
    if getattr(dock.canvas, "_show_litho", True):
        # v2.9.320 — comme le PANNEAU (v2.9.277) : barrette/veine
        # seulement si la coupe en contient (retour écran : « elle
        # place barette alors que ya pas, elle place veine alors que
        # y a pas »).
        _lh = (getattr(dock.canvas, "_result", None)
               and dock.canvas._result.holes) or []
        _has_sec = any(
            getattr(c, "role", "") == "secondary"
            for h in _lh for iv in (h.litho or []) for c in (iv.components or []))
        _has_vein = any(
            getattr(c, "role", "") in ("vein", "accessory")
            for h in _lh for iv in (h.litho or []) for c in (iv.components or []))
        if _has_sec:
            sym.append(("litho_sec", _tr("Litho · secondaire (barrette)"),
                        None, None))
        if _has_vein:
            sym.append(("litho_vein", _tr("Litho · veine / accessoire"),
                        None, None))
    if (getattr(dock.canvas, "_show_surface", True)
            and dock.canvas._result
            and getattr(dock.canvas._result, "surface", None)
            and getattr(dock.canvas, "_surface_source", None)):
        src = dock.canvas._surface_source
        labels = {
            "dem": _tr("Ligne de sol — MNT (mesurée)"),
            "csv": _tr("Ligne de sol — points mesurés (CSV)"),
            "collars": _tr("Ligne de sol — interpolée aux collets"),
        }
        dash = (src == "collars")
        col = getattr(dock.canvas, "_surface_color", "#8B6F52") or "#8B6F52"
        sym.append(("surface", labels.get(src, _tr("Ligne de sol")),
                    col, dash))
    if sym:
        blocks.append((_tr("Symboles de la coupe"), sym, "sym"))

    # 2 Teneurs — multi-éléments en groupes (v2.9.94 : 2 col export)
    if getattr(dock.canvas, "_show_assays", False):
        elems = multi_assay_mod.normalize_elements(
            getattr(dock.canvas, "_assay_elements", None)
            or ([dock.canvas._element]
                if getattr(dock.canvas, "_element", None) else []))
        scales = getattr(dock.canvas, "_assay_scales", None) or {}
        if not scales and getattr(dock.canvas, "_assay_scale", None):
            if elems:
                scales = {elems[0]: dock.canvas._assay_scale}
        pals = dict(getattr(dock.canvas, "_assay_element_palettes", None) or {})
        default_pal = getattr(dock.canvas, "_assay_palette", "grade") or "grade"
        # groups = [(header_label, [(class_lab, color|None), ...]), ...]
        groups = []
        for code in elems:
            scale_as = scales.get(code)
            if not scale_as:
                continue
            try:
                element = dock._element_display_label(code)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export : légendes (peinture)", _exc)
                element = str(code or _tr("Élément"))
            if not element:
                element = str(code or _tr("Élément"))
            palette = pals.get(code) or default_pal
            method = scale_as.get("method", "linear")
            class_rows = []
            if method in ("linear", "log"):
                try:
                    lo = dock._format_assay_value(
                        scale_as.get("vmin"), code)
                    hi = dock._format_assay_value(
                        scale_as.get("vmax"), code)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Export : légendes (peinture)", _exc)
                    lo = f"{scale_as.get('vmin', ''):g}"
                    hi = f"{scale_as.get('vmax', ''):g}"
                for i, ratio in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
                    lab = lo if i == 0 else (hi if i == 4 else "")
                    class_rows.append(
                        (lab or "·", assay_ramp_rgb(ratio, palette)))
            else:
                for lower, upper, ratio in assay_scale_classes(scale_as):
                    try:
                        lo = dock._format_assay_value(lower, code)
                        hi = dock._format_assay_value(upper, code)
                    except Exception as _exc:
                        from ..core.diagnostics import log_swallowed
                        log_swallowed("Export : légendes (peinture)", _exc)
                        lo, hi = f"{lower:g}", f"{upper:g}"
                    class_rows.append(
                        (f"{lo} – {hi}", assay_ramp_rgb(ratio, palette)))
            if class_rows:
                groups.append((str(element), class_rows))
        if groups:
            # flag note unique (Jenks + arrondi intelligent)
            dock._export_assay_rounded_note = any(
                (scales.get(c) or {}).get("method") == "jenks"
                and (scales.get(c) or {}).get("rounding_step")
                for c in elems)
            blocks.append(
                (_tr("Teneurs — échelle quantitative"), groups, "assay"))

    # 2b Intercepts = bloc légende propre (pas un sous-groupe Teneurs)
    try:
        thr_src = (getattr(dock.canvas, "_threshold_rules", None)
                   or getattr(dock.canvas, "_threshold_rule", None))
        units = dock._threshold_units_map(thr_src)
        thr_entries = threshold_rule_mod.legend_labels_multi(
            thr_src, units=units)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : légendes (peinture)", _exc)
        thr_entries = []
    if thr_entries and getattr(dock.canvas, "_show_intercepts", True):
        rows = [(e["text"], e.get("color") or SELECTION_HIGHLIGHT_COLOR)
                for e in thr_entries]
        blocks.append((_tr("Intercepts"), rows, "threshold"))
    # 3 Lithologie
    if getattr(dock.canvas, "_show_litho", True):
        codes = []
        try:
            # v2.9.307 — la légende exportée décode la COUPE affichée,
            # pas tout le projet (retour : « plein d'éléments, tu cliques,
            # tu vois rien, ça existe pas »).
            _sr = getattr(dock.canvas, "_result", None)
            codes = (get_all_litho_codes(list(_sr.holes))
                     if _sr and getattr(_sr, "holes", None)
                     else (get_all_litho_codes(dock._drillholes)
                           if dock._drillholes else []))
            codes = [
                c for c in codes
                if get_litho_style(c, dock._litho_styles).get(
                    "visible", True)]
            codes = sorted(
                codes,
                key=lambda c: (
                    get_litho_style(c, dock._litho_styles).get("label", c)
                    or c).casefold())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : légendes (peinture)", _exc)
            codes = []
        rows = []
        for code in codes:
            st = get_litho_style(code, dock._litho_styles)
            rows.append((st.get("label") or code, st))
        if rows:
            blocks.append((_tr("Lithologie — catégories"), rows, "litho"))

    # 4 Altérations (types seulement — pas de clé largeur=intensité)
    if getattr(dock.canvas, "_show_alterations", True):
        try:
            a_codes = dock._export_domain_codes(
                "alteration", "alterations", "alteration", True)
            rows = []
            for code in a_codes:
                st = dock.canvas._style_for("alteration", code)
                rows.append((st.get("label") or code, st))
            if rows:
                # même rendu 2-col que litho (compact)
                blocks.append(
                    (_tr("Altérations — catégories"), rows, "alter"))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : légendes (peinture)", _exc)
            # styles altéro absents
            pass

    # 5 Minéralisations
    if getattr(dock.canvas, "_show_mineralizations", True):
        try:
            from ..core.mineral_symbols import style_display_code
            m_codes = dock._export_domain_codes(
                "mineralization_style", "mineralizations",
                "mineralization_style", True)
            rows = []
            for code in m_codes:
                st = dock.canvas._style_for(
                    "mineralization_style", code)
                key = style_display_code(
                    code, st.get("symbol_id"), st.get("pattern"))
                lab = st.get("label") or code
                rows.append((key or code, lab))
            if rows:
                blocks.append(
                    (_tr("Minéralisations — styles"), rows, "mineral"))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : légendes (peinture)", _exc)
            # miné optionnel
            pass

    # 6 Structures (v2.9.260 — étape 2 : pastilles point par type)
    if getattr(dock.canvas, "_show_structures", True):
        try:
            s_codes = []
            for dh in (dock._drillholes or []):
                for st in (getattr(dh, "structure", None) or []):
                    code = str(getattr(st, "structure_type", None)
                               or getattr(st, "type", None) or "").strip()
                    if code and code not in s_codes:
                        s_codes.append(code)
            s_codes = sorted(
                s_codes,
                key=lambda code: (
                    (dock.canvas._style_for("structure", code).get("label")
                     or code).casefold(),
                    code.casefold()))
            s_codes = [
                code for code in s_codes
                if dock.canvas._style_for("structure", code).get(
                    "visible", True) is not False]
            rows = []
            for code in s_codes:
                st = dock.canvas._style_for("structure", code)
                rows.append((code, st.get("label") or code, st))
            if rows:
                blocks.append(
                    (_tr("Structures — catégories"), rows, "structure"))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : légendes (peinture)", _exc)
            # structures optionnelles
            pass

    # 7 Imagerie — matériaux (Chantier 2). Une ligne par matériau
    # réellement présent sur les forages : le rendu de la coupe pose le
    # même badge-lettre sur les bandes photo, la légende colle donc à
    # ce que l'image montre.
    if getattr(dock.canvas, "_show_imagery", True):
        try:
            from .section_imagery import _IMAGERY_MATERIAL_FR
            materials = set()
            for dh in (dock._drillholes or []):
                for rec in (getattr(dh, "imagery", None) or []):
                    mat = str(getattr(
                        rec, "material_label", None) or "").strip()
                    if mat:
                        materials.add(mat.casefold())
            rows = []
            for material in ("core", "rc", "auger", "pit", "other"):
                if material not in materials:
                    continue
                from .section_imagery import _material_badge_letter
                letter = _material_badge_letter(material) or material[:1]
                label = dock.tr(_IMAGERY_MATERIAL_FR.get(material, material))
                rows.append((f"{letter} — {label}", material))
            if rows:
                # le titre passe par dock.tr pour utiliser la même paire
                # i18n que la légende du panneau (contexte SectionWidget).
                blocks.append((dock.tr("Imagerie — matériaux"), rows, "imagery"))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : légendes imagerie", _exc)
            pass

    if not blocks:
        return None

    def block_rows_h(rows, kind):
        if kind == "threshold":
            # une ligne de texte (peut wrap → 2 rows budget)
            n = max(1, len(rows or []))
            return sec_h + n * row_h + 4
        if kind == "assay":
            # rows = groups [(header, class_rows), ...]
            groups = rows or []
            n_g = len(groups)
            note_h = (row_h if getattr(
                dock, "_export_assay_rounded_note", False) else 0)
            if n_g <= 1:
                g0 = groups[0] if groups else ("", [])
                # header + classes
                n_lines = 1 + len(g0[1] if isinstance(g0, (tuple, list)) and len(g0) > 1 else [])
                return sec_h + n_lines * row_h + 4 + note_h
            # 2 colonnes : paires de groupes côte à côte
            h = sec_h + 4
            i = 0
            while i < n_g:
                g_a = groups[i]
                rows_a = g_a[1] if isinstance(g_a, (tuple, list)) and len(g_a) > 1 else []
                ha = (1 + len(rows_a)) * row_h
                if i + 1 < n_g:
                    g_b = groups[i + 1]
                    rows_b = g_b[1] if isinstance(g_b, (tuple, list)) and len(g_b) > 1 else []
                    hb = (1 + len(rows_b)) * row_h
                    h += max(ha, hb) + 6
                    i += 2
                else:
                    h += ha + 6
                    i += 1
            return h + note_h
        n = len(rows)
        if kind in ("litho", "alter", "structure") and n > 3:
            h = sec_h + ((n + 1) // 2) * row_h + 4
        else:
            h = sec_h + n * row_h + 4
        if kind == "alter":
            h += int(row_h * 1.4)  # phrase d'aide panneau
        return h

    H = pad * 2 + title_h + sum(
        block_rows_h(rows, kind) for _, rows, kind in blocks) + pad
    need_wide = any(
        (kind in ("litho", "alter", "structure") and len(rows) > 3)
        or (kind == "assay" and len(rows) >= 2)
        for _, rows, kind in blocks)
    # multi-teneurs 2 col : un peu plus large pour classes lisibles
    extra_w = 40 if need_wide else 0
    if any(kind == "assay" and len(rows) >= 2 for _, rows, kind in blocks):
        extra_w = max(extra_w, 70)
    W = int((col_w + extra_w) * s) + pad * 2
    H = min(max(int(H), 80), 14000)

    img = QImage(W, H, QImage.Format_RGB32)
    if img.isNull():
        return None
    img.fill(QColor("#FFFFFF"))
    painter = QPainter(img)
    if not painter.isActive():
        return None

    def draw_style_swatch(st, x, y):
        if st is None:
            painter.fillRect(x, y, sw_w, sw_h, QColor("#CCCCCC"))
            painter.setPen(QPen(QColor("#888"), 1))
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawRect(x, y, sw_w - 1, sw_h - 1)
            return
        try:
            pix = dock._lithology_symbol_pixmap(st)
            if pix is None or pix.isNull():
                raise ValueError("empty")
            if pix.width() != sw_w or pix.height() != sw_h:
                pix = pix.scaled(
                    sw_w, sw_h, Qt.IgnoreAspectRatio,
                    Qt.FastTransformation)
            painter.drawPixmap(x, y, pix)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : pastille de style", _exc)
            try:
                colr = QColor(st.get("color") or "#CCCCCC")
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export : pastille de style", _exc)
                colr = QColor("#CCCCCC")
            painter.fillRect(x, y, sw_w, sw_h, colr)
            painter.setPen(QPen(QColor("#888"), 1))
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawRect(x, y, sw_w - 1, sw_h - 1)

    def draw_point_swatch(st, x, y, code=None):
        """v2.9.260 — pastille légende PNG fidèle au rendu coupe.

        planaire/inconnu = point + queue sans pointe (mini-tadpole) ;
        linéaire = flèche sans point de base (trait + pointe, comme la
        coupe) ; composite / non-orientable = point simple.
        """
        try:
            colr = QColor(str(st.get("color") or "#808080"))
            opacity = getattr(dock.canvas, "_structure_opacity", 100)
            try:
                opacity = int(opacity)
            except (TypeError, ValueError):
                opacity = 100
            if 0 <= opacity < 100:
                colr.setAlpha(round(255 * opacity / 100.0))
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : pastille point", _exc)
            colr = QColor("#808080")
        cy = y + row_h // 2
        cx = x + sw_w / 2.0
        # v2.9.260 (légende export) — le glyphe est mis à l'ÉCHELLE de la
        # pastille : rayon, queue et pointe grandissent avec ``s`` pour
        # rester lisibles sur l'export HD (avant, la queue fixe de 6 px
        # laissait un point minuscule au milieu d'une grande case).
        marker_r = float(getattr(dock.canvas, "_structure_marker_size", 5.0)) / 2.0
        r = max(2.5, min(
            marker_r * max(1.0, s * 0.9),
            sw_h * 0.28))
        family = structure_family(str(code)) if code else "unknown"
        tail = max(8.0, min(sw_w * 0.42, sw_h * 0.62))
        ux0, uy0 = 0.82, 0.57
        n0 = math.hypot(ux0, uy0) or 1.0
        ex = cx + ux0 / n0 * tail
        ey = cy + uy0 / n0 * tail
        ex = min(ex, x + sw_w - 2.0)
        ey = min(ey, y + row_h - 2.0)
        vx, vy = ex - cx, ey - cy
        norm = math.hypot(vx, vy) or 1.0
        vx, vy = vx / norm, vy / norm
        if family in ("planar", "unknown"):
            painter.setPen(QPen(colr, max(1.2, 1.0 * s)))
            painter.drawLine(QPointF(cx, cy), QPointF(ex, ey))
        elif family == "linear":
            painter.setPen(QPen(colr, max(1.2, 1.0 * s)))
            painter.drawLine(QPointF(cx, cy), QPointF(ex, ey))
            head = max(6.0, 4.0 * s)
            side = max(3.0, 2.4 * s)
            bx, by = ex - vx * head, ey - vy * head
            painter.setBrush(QBrush(colr))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawPolygon(QPolygonF([
                QPointF(ex, ey),
                QPointF(bx - vy * side, by + vx * side),
                QPointF(bx + vy * side, by - vx * side)]))
        if family != "linear":
            # Point de base pour tadpole et point simple ; la mini-flèche
            # linéaire reste un trait + pointe, sans pastille parasite.
            painter.setBrush(QBrush(colr))
            painter.setPen(QPen(QColor("#202020"), max(0.5, 0.45 * s)))
            painter.drawEllipse(QPointF(cx, cy), r, r)

    def draw_sym_swatch(kind, payload, x, y0):
        """Pastille symbole = panneau (pas trait+point collés)."""
        cy = y0 + row_h // 2
        sx = x
        if kind == "traj":
            _lab, colr, width = payload
            pen_w = max(1.0, float(width) * s * 0.9)
            painter.setPen(QPen(QColor(colr), pen_w, Qt.SolidLine))
            painter.drawLine(sx + 2, cy, sx + sw_w - 2, cy)
        elif kind == "collar":
            # POINT seul — pas de trait
            painter.setBrush(QBrush(QColor("#C0392B")))
            painter.setPen(QPen(QColor("#000000"), max(0.5, 0.5 * s)))
            r = max(2.5, 3.0 * s * 0.55)
            painter.drawEllipse(QPointF(sx + sw_w / 2.0, cy), r, r)
        elif kind == "litho_sec":
            painter.setPen(QPen(QColor("#566573"), 0.5 * s))
            painter.setBrush(QBrush(QColor("#AED6F1")))
            painter.drawRect(sx + 1, y0 + 2, sw_w - 3, sw_h - 2)
            painter.setBrush(QBrush(QColor("#F5B041")))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(sx + 2, y0 + 3, int((sw_w - 4) * 0.3), sw_h - 4)
        elif kind == "litho_vein":
            painter.setPen(QPen(QColor("#566573"), 0.5 * s))
            painter.setBrush(QBrush(QColor("#D5D8DC")))
            painter.drawRect(sx + 1, y0 + 2, sw_w - 3, sw_h - 2)
            painter.setPen(QPen(QColor("#5D6D7E"), max(1.2, 1.4 * s * 0.6)))
            painter.drawLine(sx + 3, y0 + 3, sx + sw_w - 4, y0 + sw_h - 2)
        elif kind == "surface":
            _lab, colr, dash = payload
            style = Qt.DashLine if dash else Qt.SolidLine
            painter.setPen(QPen(QColor(colr), max(1.2, 1.3 * s * 0.6), style))
            painter.drawLine(sx + 2, cy, sx + sw_w - 2, cy)

    try:
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        y = pad
        painter.setFont(font_title)
        painter.setPen(primary)
        painter.drawText(pad, y, W - 2 * pad, title_h,
                         Qt.AlignLeft | Qt.AlignVCenter, _tr("Légendes"))
        y += title_h + 2

        for title, rows, kind in blocks:
            painter.setFont(font_sec)
            painter.setPen(primary)
            painter.drawText(pad, y, W - 2 * pad, sec_h,
                             Qt.AlignLeft | Qt.AlignVCenter, title)
            y += sec_h

            if kind == "threshold":
                # v2.9.129 — pastille PLEINE (blocs intercepts),
                # pas un cadre pointillé « Contour ».
                painter.setFont(font_body)
                for entry in (rows or []):
                    if isinstance(entry, (tuple, list)) and len(entry) >= 2:
                        line, col_hex = entry[0], entry[1]
                    else:
                        line, col_hex = entry, SELECTION_HIGHLIGHT_COLOR
                    cx = pad
                    fill = QColor(str(col_hex or SELECTION_HIGHLIGHT_COLOR))
                    painter.setBrush(QBrush(fill))
                    painter.setPen(QPen(
                        QColor(threshold_rule_mod.INTERCEPT_BLOCK_STROKE),
                        max(0.6, 0.45 * s)))
                    painter.drawRect(cx, y + 3, sw_w - 2, sw_h - 4)
                    painter.setPen(ink)
                    painter.drawText(
                        cx + sw_w + 4, y, W - 2 * pad - sw_w - 4, row_h,
                        Qt.AlignLeft | Qt.AlignVCenter, str(line))
                    y += row_h
                y += 4
                continue

            if kind == "assay":
                # v2.9.94 — groupes multi en 2 colonnes (gain de place)
                groups = rows or []
                n_g = len(groups)
                gap_c = 8
                cell_w = (W - 2 * pad - gap_c) // 2 if n_g >= 2 else (W - 2 * pad)

                def _draw_assay_group(gx, gy, g_header, g_rows, g_w):
                    yy = gy
                    painter.setPen(primary)
                    painter.setFont(font_sec)
                    painter.drawText(
                        gx, yy, g_w, row_h,
                        Qt.AlignLeft | Qt.AlignVCenter, str(g_header))
                    yy += row_h
                    for lab, colr in g_rows:
                        if colr:
                            painter.fillRect(
                                gx, yy + 1, sw_w, sw_h, QColor(colr))
                            painter.setPen(QPen(QColor("#777"), 1))
                            painter.setBrush(QBrush(Qt.NoBrush))
                            painter.drawRect(
                                gx, yy + 1, sw_w - 1, sw_h - 1)
                            tx = gx + sw_w + 4
                        else:
                            tx = gx
                        painter.setPen(ink)
                        painter.setFont(font_body)
                        painter.drawText(
                            tx, yy, g_w - (tx - gx), row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(lab))
                        yy += row_h
                    return yy

                gi = 0
                while gi < n_g:
                    hdr_a, rows_a = groups[gi][0], groups[gi][1]
                    if n_g >= 2 and gi + 1 < n_g:
                        hdr_b, rows_b = groups[gi + 1][0], groups[gi + 1][1]
                        ya = _draw_assay_group(
                            pad, y, hdr_a, rows_a, cell_w)
                        yb = _draw_assay_group(
                            pad + cell_w + gap_c, y, hdr_b, rows_b, cell_w)
                        y = max(ya, yb) + 6
                        gi += 2
                    else:
                        y = _draw_assay_group(
                            pad, y, hdr_a, rows_a,
                            W - 2 * pad if n_g < 2 else cell_w) + 6
                        gi += 1
                # v2.9.95 — une seule note sous le bloc (pas par colonne)
                if getattr(dock, "_export_assay_rounded_note", False):
                    painter.setPen(QColor(
                        COLORS.get("text_medium", "#566573")))
                    hf = QFont(font_body)
                    hf.setItalic(True)
                    hf.setPointSize(max(8, font_body.pointSize() - 1))
                    painter.setFont(hf)
                    note = "Bornes de classes arrondies"
                    painter.drawText(
                        pad, y, W - 2 * pad, row_h,
                        Qt.AlignLeft | Qt.AlignVCenter, note)
                    y += row_h
                y += 2
                continue

            if kind == "structure" and len(rows) > 3:
                # v2.9.260 — structures : pastille POINT (pas patte litho).
                cell_w = (W - 2 * pad - 4) // 2
                col = 0
                row_y = y
                for code, label, st in rows:
                    x = pad + col * (cell_w + 4)
                    draw_point_swatch(st, x, row_y, code)
                    painter.setPen(ink)
                    painter.setFont(font_body)
                    painter.drawText(
                        x + sw_w + 4, row_y, cell_w - sw_w - 6, row_h,
                        Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    col += 1
                    if col >= 2:
                        col = 0
                        row_y += row_h
                y = row_y + (row_h if col else 0) + 4
                continue

            if kind in ("litho", "alter") and len(rows) > 3:
                cell_w = (W - 2 * pad - 4) // 2
                col = 0
                row_y = y
                for label, st in rows:
                    x = pad + col * (cell_w + 4)
                    draw_style_swatch(st, x, row_y + 1)
                    painter.setPen(ink)
                    painter.setFont(font_body)
                    painter.drawText(
                        x + sw_w + 4, row_y, cell_w - sw_w - 6, row_h,
                        Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    col += 1
                    if col >= 2:
                        col = 0
                        row_y += row_h
                y = row_y + (row_h if col else 0) + 4
                if kind == "alter":
                    # phrase panneau légende (export = plugin)
                    hint = _tr(
                        "La largeur des bandes reflète l'intensité "
                        "(faible < modérée < forte), la couleur "
                        "identifie le type.")
                    painter.setPen(QColor(
                        COLORS.get("text_medium", "#566573")))
                    hf = QFont(font_body)
                    hf.setItalic(True)
                    # un peu plus petit
                    hf.setPointSize(max(8, font_body.pointSize() - 1))
                    painter.setFont(hf)
                    hr = painter.boundingRect(
                        pad, y, W - 2 * pad, int(row_h * 1.4),
                        Qt.AlignLeft | Qt.TextWordWrap, hint)
                    painter.drawText(hr, Qt.AlignLeft | Qt.TextWordWrap, hint)
                    y += hr.height() + 4
            else:
                for item in rows:
                    if kind == "sym":
                        sk = item[0]
                        if sk == "traj":
                            label = item[1]
                            draw_sym_swatch("traj", (item[1], item[2], item[3]), pad, y)
                        elif sk == "collar":
                            label = item[1]
                            draw_sym_swatch("collar", None, pad, y)
                        elif sk == "litho_sec":
                            label = item[1]
                            draw_sym_swatch("litho_sec", None, pad, y)
                        elif sk == "litho_vein":
                            label = item[1]
                            draw_sym_swatch("litho_vein", None, pad, y)
                        elif sk == "surface":
                            label = item[1]
                            draw_sym_swatch(
                                "surface", (item[1], item[2], item[3]), pad, y)
                        else:
                            label = str(item)
                        painter.setPen(ink)
                        painter.setFont(font_body)
                        painter.drawText(
                            pad + sw_w + 4, y, W - pad * 2 - sw_w, row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    elif kind == "assay":
                        label, colr = item
                        if colr:
                            painter.fillRect(
                                pad, y + 1, sw_w, sw_h, QColor(colr))
                            painter.setPen(QPen(QColor("#777"), 1))
                            painter.setBrush(QBrush(Qt.NoBrush))
                            painter.drawRect(pad, y + 1, sw_w - 1, sw_h - 1)
                            tx = pad + sw_w + 4
                            painter.setPen(ink)
                            painter.setFont(font_body)
                        else:
                            # en-tête élément + unité (ex. Fe — %)
                            tx = pad
                            painter.setPen(primary)
                            painter.setFont(font_sec)
                        painter.drawText(
                            tx, y, W - tx - pad, row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    elif kind in ("litho", "alter"):
                        label, st = item
                        draw_style_swatch(st, pad, y + 1)
                        painter.setPen(ink)
                        painter.setFont(font_body)
                        painter.drawText(
                            pad + sw_w + 4, y, W - pad * 2 - sw_w, row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    elif kind == "mineral":
                        key, lab = item
                        painter.setPen(QPen(QColor("#AAB7B8"), 1))
                        painter.setBrush(QBrush(Qt.NoBrush))
                        painter.drawRect(pad, y + 1, sw_w - 1, sw_h - 1)
                        painter.setPen(QColor("#5D6D7E"))
                        painter.setFont(font_body)
                        painter.drawText(
                            pad, y + 1, sw_w, sw_h,
                            Qt.AlignCenter, str(key)[:4])
                        painter.setPen(ink)
                        painter.drawText(
                            pad + sw_w + 4, y, W - pad * 2 - sw_w, row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(lab))
                    elif kind == "structure":
                        code, label, st = item
                        draw_point_swatch(st, pad, y, code)
                        painter.setPen(ink)
                        painter.setFont(font_body)
                        painter.drawText(
                            pad + sw_w + 4, y, W - pad * 2 - sw_w, row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    elif kind == "imagery":
                        label, material = item
                        from .section_imagery import _material_badge_letter
                        badge_letter = _material_badge_letter(material)
                        bg = QColor("#2C3E50")
                        bg.setAlpha(215)
                        painter.fillRect(
                            pad, y + 1, sw_w, sw_h, bg)
                        painter.setPen(QPen(QColor("#FFFFFF"), 1))
                        painter.setBrush(QBrush(Qt.NoBrush))
                        painter.drawRect(pad, y + 1, sw_w - 1, sw_h - 1)
                        painter.setPen(QColor("#FFFFFF"))
                        painter.setFont(font_badge)
                        painter.drawText(
                            pad, y + 1, sw_w, sw_h,
                            Qt.AlignCenter, str(badge_letter or "?"))
                        painter.setPen(ink)
                        painter.setFont(font_body)
                        painter.drawText(
                            pad + sw_w + 4, y, W - pad * 2 - sw_w, row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    else:
                        label = item[0] if isinstance(item, (tuple, list)) else item
                        painter.setPen(ink)
                        painter.setFont(font_body)
                        painter.drawText(
                            pad, y, W - 2 * pad, row_h,
                            Qt.AlignLeft | Qt.AlignVCenter, str(label))
                    y += row_h
                if kind == "alter":
                    hint = _tr(
                        "La largeur des bandes reflète l'intensité "
                        "(faible < modérée < forte), la couleur "
                        "identifie le type.")
                    painter.setPen(QColor(
                        COLORS.get("text_medium", "#566573")))
                    hf = QFont(font_body)
                    hf.setItalic(True)
                    hf.setPointSize(max(8, font_body.pointSize() - 1))
                    painter.setFont(hf)
                    hr = painter.boundingRect(
                        pad, y, W - 2 * pad, int(row_h * 1.4),
                        Qt.AlignLeft | Qt.TextWordWrap, hint)
                    painter.drawText(
                        hr, Qt.AlignLeft | Qt.TextWordWrap, hint)
                    y += hr.height() + 2
                y += 4
    finally:
        painter.end()

    final_h = min(y + pad, img.height())
    if final_h > 40 and final_h < img.height() - 2:
        return img.copy(0, 0, img.width(), final_h)
    return img


def export_domain_codes(dock, domain, hole_attribute, attribute, use_components):
    # v2.9.307 — même règle : altérations/minéralisations de la coupe.
    _sr = getattr(dock.canvas, "_result", None)
    _src = list(_sr.holes) if _sr and getattr(_sr, "holes", None) else (
        dock._drillholes or [])
    codes = {
        code for dh in _src
        for iv in getattr(dh, hole_attribute, [])
        for code in SectionCanvas._interval_codes(
            iv, attribute, use_components)
        if dock.canvas._style_for(domain, code).get("visible", True)}
    return sorted(
        codes,
        key=lambda code: (
            (dock.canvas._style_for(domain, code).get("label") or code)
            .casefold(),
            code.casefold()))


def export_meta_dict(dock):
    from datetime import datetime
    project = dock._project() if hasattr(dock, "_project") else None
    cfg = {}
    if project is not None:
        try:
            cfg = dict(getattr(project, "config", {}) or {})
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : métadonnées du cartouche", _exc)
            cfg = {}
    line = getattr(dock, "_line", None) or getattr(dock.canvas, "_line", None)
    name = ""
    if line is not None and getattr(line, "name", None):
        name = str(line.name)
    if not name:
        name = _tr("Coupe")
    proj_name = str(cfg.get("project_name") or "").strip()
    crs = str(cfg.get("crs") or "").strip()
    crs_desc = str(cfg.get("crs_description") or "").strip()
    crs_label = crs_desc or crs
    n_holes = 0
    if getattr(dock.canvas, "_result", None) and dock.canvas._result.holes:
        n_holes = len(dock.canvas._result.holes)
    # 329 — champ « Auteur » du panneau Orientation (sinon config).
    author = ""
    try:
        author = str(getattr(dock, "orientation_author", None).text()
                     or "").strip()
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : auteur du cartouche", _exc)
        author = ""
    if not author:
        author = str(cfg.get("author") or "").strip()
    return {
        "project_name": proj_name,
        "section_name": name,
        "crs": crs_label,
        "n_holes": n_holes,
        "author": author,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def paint_export_title(dock, width: int, scale: float = 1.25):
    """v2.9.66 — titre de section centré, gras, bien visible.

    Nom de la coupe seul (ex. Section_001), au centre de la page,
    police grasse plus grande que le pied de page / légende.
    """
    s = max(min(float(scale), 3.5), 1.0)
    meta = dock._export_meta_dict()
    # barre un peu plus haute pour un titre marqué
    h = int(44 * s)
    w = max(int(width), 200)
    img = QImage(w, h, QImage.Format_RGB32)
    if img.isNull():
        return None
    img.fill(QColor("#FFFFFF"))
    painter = QPainter(img)
    if not painter.isActive():
        return None
    try:
        # Gras natif (pas SmallCaps) : plus lisible et plus « titre »
        pt = max(18, int(17 * s * 0.85))
        f = QFont("Segoe UI", pt)
        f.setBold(True)
        f.setWeight(QFont.Bold)
        painter.setFont(f)
        painter.setPen(QColor(COLORS.get("primary", "#1A252F")))
        title = (meta.get("section_name") or _tr("Coupe")).strip()
        # centré horizontalement + verticalement sur toute la largeur page
        painter.drawText(
            0, 0, w, h,
            Qt.AlignHCenter | Qt.AlignVCenter,
            title)
    finally:
        painter.end()
    return img


def paint_export_footer(dock, width: int, scale: float = 1.25):
    """329 — cartouche d'infos AGRANDI : projet · date · SCR · forages
    · auteur, sur deux lignes lisibles (retour écran : « augmenter la
    taille, WGS 84 29N, autoriser auteur »)."""
    s = max(min(float(scale), 3.5), 1.0)
    meta = dock._export_meta_dict()
    h = int(44 * s)
    w = max(int(width), 200)
    img = QImage(w, h, QImage.Format_RGB32)
    if img.isNull():
        return None
    img.fill(QColor("#FFFFFF"))
    painter = QPainter(img)
    if not painter.isActive():
        return None
    try:
        f = QFont("Segoe UI", max(11, int(11 * s * 0.8)))
        painter.setFont(f)
        painter.setPen(QColor(COLORS.get("text_medium", "#566573")))
        l1, l2 = [], []
        if meta.get("project_name"):
            l1.append(str(meta["project_name"]))
        if meta.get("section_name"):
            l1.append(str(meta["section_name"]))
        if meta.get("date"):
            l1.append(str(meta["date"]))
        if meta.get("crs"):
            l2.append(_tr("SCR {}").format(meta['crs']))
        if meta.get("n_holes"):
            l2.append(_tr("{} forage(s)").format(meta['n_holes']))
        if meta.get("author"):
            l2.append(_tr("Auteur : {}").format(meta['author']))
        painter.drawText(8, 0, w - 16, h // 2,
                         Qt.AlignLeft | Qt.AlignVCenter,
                         "  ·  ".join(l1))
        painter.drawText(8, h // 2, w - 16, h // 2,
                         Qt.AlignLeft | Qt.AlignVCenter,
                         "  ·  ".join(l2))
    finally:
        painter.end()
    return img


def paint_export_cartouche(dock, width: int, scale: float = 1.25):
    return dock._paint_export_title(width, scale)


def paint_locator_map(dock, size: int = 200, scale: float = 1.25):
    """Mini-carte v2.9.57 : ligne, buffer, collets, N, échelle, anti-chevauchement."""
    line = getattr(dock, "_line", None) or getattr(dock.canvas, "_line", None)
    if line is None:
        return None
    try:
        x1, y1 = float(line.x1), float(line.y1)
        x2, y2 = float(line.x2), float(line.y2)
        length = float(line.length)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : mini-carte de localisation", _exc)
        return None
    if length < 1e-6:
        return None
    s = max(min(float(scale), 2.0), 1.0)
    side = max(int(size * s), 180)
    pad = max(20, int(side * 0.13))
    # v2.9.94 — bandeau titre « Carte en plan » au-dessus du cadre
    title_band = max(18, int(side * 0.09))
    img_h = side + title_band
    img = QImage(side, img_h, QImage.Format_RGB32)
    if img.isNull():
        return None
    img.fill(QColor("#FFFFFF"))
    painter = QPainter(img)
    if not painter.isActive():
        return None
    try:
        f_title = QFont("Segoe UI", max(8, side // 28))
        f_title.setBold(True)
        painter.setFont(f_title)
        painter.setPen(QColor("#1A252F"))
        painter.drawText(
            4, 2, side - 8, title_band - 2,
            Qt.AlignHCenter | Qt.AlignVCenter, _tr("Carte en plan"))
        # décale tout le dessin carte sous le bandeau
        painter.translate(0, title_band)
        try:
            buf = float(dock.buffer_spin.value())
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export : mini-carte de localisation", _exc)
            buf = float(getattr(dock.canvas, "_buffer", 50) or 50)
        buf = max(float(buf), 1.0)
        unit = getattr(dock, "_buffer_unit", None) or "m"

        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        nx, ny = -uy, ux

        def _dist_to_segment(px, py):
            wx, wy = px - x1, py - y1
            tt = max(0.0, min(length, wx * ux + wy * uy))
            cx, cy = x1 + tt * ux, y1 + tt * uy
            return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5

        def _short_hole_label(hid):
            text = str(hid or "").strip()
            if not text:
                return ""
            digits = "".join(c for c in text if c.isdigit())
            if len(digits) >= 3:
                return digits[-3:]
            if digits:
                return digits
            return text[-4:] if len(text) > 4 else text

        collars = []
        others = []
        result = getattr(dock.canvas, "_result", None)
        hole_ids = []
        if result and getattr(result, "holes", None):
            hole_ids = [getattr(ph, "hole_id", None) for ph in result.holes]
        id_set = {h for h in hole_ids if h}
        for d in (dock._drillholes or []):
            try:
                hid = getattr(d.collar, "hole_id", None)
                cx = float(d.collar.x)
                cy = float(d.collar.y)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export : mini-carte de localisation", _exc)
                continue
            if id_set and hid not in id_set:
                # 328 — hors section : point gris quand même (vue de
                # zone) ; l'étiquette reste réservée à la coupe.
                others.append((cx, cy))
                continue
            if _dist_to_segment(cx, cy) <= buf * 1.001:
                collars.append((cx, cy, _short_hole_label(hid)))
            else:
                others.append((cx, cy))

        # 321/329 — cadrage choisi (slider 100–1000 % + glisser).
        zoom = max(1.0, min(10.0, float(
            getattr(dock, "_locator_zoom", 1.0) or 1.0)))
        all_h = bool(getattr(dock, "_locator_all", False))
        off = getattr(dock, "_locator_off", (0.0, 0.0)) or (0.0, 0.0)
        factor = 1.22 * zoom

        # 329 — défaut : alentours PROCHES (<= 3 buffers) dans le
        # cadre ; « tous les forages » englobe tout (case du dialogue).
        near_o = [o for o in others
                  if all_h or _dist_to_segment(o[0], o[1]) <= buf * 3.0]
        xs = [x1, x2] + [c[0] for c in collars + near_o]
        ys = [y1, y2] + [c[1] for c in collars + near_o]
        min_x = min(xs) - buf * 0.55
        max_x = max(xs) + buf * 0.55
        min_y = min(ys) - buf * 0.55
        max_y = max(ys) + buf * 0.55
        dx0 = max(max_x - min_x, 1.0)
        dy0 = max(max_y - min_y, 1.0)
        span = max(dx0, dy0) * factor
        cx0 = (min_x + max_x) / 2.0 + float(off[0])
        cy0 = (min_y + max_y) / 2.0 + float(off[1])
        min_x, max_x = cx0 - span / 2, cx0 + span / 2
        min_y, max_y = cy0 - span / 2, cy0 + span / 2
        dx = max_x - min_x
        dy = max_y - min_y

        def to_pix(x, y):
            px = pad + (x - min_x) / dx * (side - 2 * pad)
            py = pad + (max_y - y) / dy * (side - 2 * pad)
            return QPointF(px, py)

        painter.setPen(QPen(QColor("#B0B8C0"), max(1, side // 160)))
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawRect(2, 2, side - 5, side - 5)

        if others:  # 325 : alentours (gris, sans étiquette)
            r_o = max(2, side // 110)
            painter.setBrush(QBrush(QColor("#95A5A6")))
            painter.setPen(QPen(QColor("#7F8C8D"), 1))
            for oc in others:
                painter.drawEllipse(to_pix(*oc), r_o, r_o)

        corners = [
            to_pix(x1 + nx * buf, y1 + ny * buf),
            to_pix(x2 + nx * buf, y2 + ny * buf),
            to_pix(x2 - nx * buf, y2 - ny * buf),
            to_pix(x1 - nx * buf, y1 - ny * buf),
        ]
        fill = QColor("#5DADE2")
        fill.setAlpha(40)
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(QColor("#3498DB"), max(1, side // 200), Qt.DashLine))
        painter.drawPolygon(QPolygonF(corners))

        lw = max(2, side // 110)
        painter.setPen(QPen(QColor("#1A252F"), lw))
        p1p, p2p = to_pix(x1, y1), to_pix(x2, y2)
        painter.drawLine(p1p, p2p)

        occupied = []

        def _fm_w(fm, text):
            if hasattr(fm, "horizontalAdvance"):
                return fm.horizontalAdvance(text)
            return fm.width(text)

        def _fits(rect):
            for o in occupied:
                if rect.intersects(o):
                    return False
            return True

        def _place_label(px, py, text, font):
            painter.setFont(font)
            fm = QFontMetrics(font)
            tw = _fm_w(fm, text)
            th = fm.height()
            cands = [
                (10, -th // 2), (-tw - 10, -th // 2),
                (10, 6), (-tw - 10, 6),
                (-tw // 2, -th - 8), (-tw // 2, 12),
                (12, -th - 4), (-tw - 12, -th - 4),
            ]
            for ox, oy in cands:
                rx = max(5, min(side - tw - 5, px + ox))
                ry = max(5, min(side - th - 18, py + oy))
                rect = QRectF(rx - 1, ry - 1, tw + 2, th + 2)
                if _fits(rect):
                    occupied.append(rect)
                    return rx, ry, fm
            # 330 — pas de place libre : PAS d'étiquette (le point
            # reste) — jamais de texte posé sur un autre.
            return None

        r_pt = max(3, side // 60)
        f_p = QFont("Segoe UI", max(6, side // 44))  # 330 : plus fin
        f_p.setBold(True)
        for lab, pt in (("P1", p1p), ("P2", p2p)):
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.setPen(QPen(QColor("#1A252F"), max(1, lw // 2)))
            painter.drawEllipse(pt, r_pt, r_pt)
            occupied.append(QRectF(
                pt.x() - r_pt - 2, pt.y() - r_pt - 2,
                2 * r_pt + 4, 2 * r_pt + 4))
            placed = _place_label(pt.x(), pt.y(), lab, f_p)
            if placed is None:
                # 337 — P1/P2 doivent TOUJOURS sortir (retour écran :
                # « à l'export P1 sort pas ») : pose forcée, lisible
                # grâce à un fond blanc opaque (propre sur fond blanc).
                painter.setFont(f_p)
                fm = QFontMetrics(f_p)
                tw = _fm_w(fm, lab)
                th = fm.height()
                rx = max(3, min(side - tw - 3, int(pt.x()) + 8))
                ry = max(3, min(side - th - 3, int(pt.y()) - th // 2))
                painter.setPen(QPen(Qt.NoPen))
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.drawRect(QRectF(rx - 1, ry - 1, tw + 2, th + 2))
                occupied.append(QRectF(rx - 1, ry - 1, tw + 2, th + 2))
                placed = (rx, ry, fm)
            lx, ly, fm = placed
            painter.setPen(QColor("#1A252F"))
            painter.setFont(f_p)
            painter.drawText(int(lx), int(ly + fm.ascent()), lab)

        r_c = max(2, side // 90)
        # 337 — petites ET plafonnées : ne surchargent plus la carte,
        # quel que soit le zoom ou la taille d'export.
        f_c = QFont("Segoe UI", max(5, min(9, side // 70)))
        for cx, cy, lab in collars:
            pt = to_pix(cx, cy)
            painter.setBrush(QBrush(QColor("#C0392B")))
            painter.setPen(QPen(QColor("#922B21"), 1))
            painter.drawEllipse(pt, r_c, r_c)
            occupied.append(QRectF(
                pt.x() - r_c - 2, pt.y() - r_c - 2,
                2 * r_c + 4, 2 * r_c + 4))
            if lab:
                placed = _place_label(pt.x(), pt.y(), lab, f_c)
                if placed is not None:
                    lx, ly, fm = placed
                    painter.setPen(QColor("#1A252F"))
                    painter.setFont(f_c)
                    painter.drawText(int(lx), int(ly + fm.ascent()), lab)

        # Nord — rentré dans le cadre (v2.9.64 : plus de N / flèche coupés)
        f_n = QFont("Segoe UI", max(10, side // 22))  # v321 agrandi
        f_n.setBold(True)
        painter.setFont(f_n)
        fm_n = QFontMetrics(f_n)
        n_letter_h = fm_n.ascent()
        n_letter_w = (fm_n.horizontalAdvance("N")
                      if hasattr(fm_n, "horizontalAdvance")
                      else fm_n.width("N"))
        n_len = max(16, side // 10)
        # marge intérieure sous le trait du cadre (border ~2–3 px)
        inset = max(8, int(pad * 0.35))
        n_cx = side - inset - max(n_letter_w, n_len * 0.4) * 0.5
        # place le N d'abord, flèche SOUS le N (tout dans le cadre)
        n_ty = inset + n_letter_h  # baseline du N
        painter.setPen(QColor("#1A252F"))
        painter.drawText(int(n_cx - n_letter_w / 2), int(n_ty), "N")
        # flèche pointant vers le N (haut), corps sous la lettre
        tip_y = n_ty + max(2, side // 90)
        mid_y = tip_y + n_len * 0.42
        base_y = tip_y + n_len * 0.95
        painter.setPen(QPen(QColor("#1A252F"), max(1, side // 140)))
        painter.setBrush(QBrush(QColor("#1A252F")))
        painter.drawLine(QPointF(n_cx, base_y), QPointF(n_cx, mid_y))
        tip = QPolygonF([
            QPointF(n_cx, tip_y),
            QPointF(n_cx - n_len * 0.18, mid_y),
            QPointF(n_cx + n_len * 0.18, mid_y),
        ])
        painter.drawPolygon(tip)

        # Échelle
        usable = side - 2 * pad
        m_per_px = span / max(usable, 1.0)
        target_m = usable * 0.30 * m_per_px
        nice = [5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]
        scale_m = min(nice, key=lambda v: abs(v - target_m))
        bar_px = max(24.0, min(usable * 0.42, scale_m / m_per_px))
        # recalcule scale_m affiché depuis bar_px arrondi
        shown = min(nice, key=lambda v: abs(v - bar_px * m_per_px))
        bar_px = max(24.0, min(usable * 0.42, shown / m_per_px))
        bx0 = float(pad)
        by0 = float(side - max(16, int(pad * 0.45)))
        painter.setPen(QPen(QColor("#1A252F"), max(2, side // 120)))
        painter.drawLine(QPointF(bx0, by0), QPointF(bx0 + bar_px, by0))
        painter.drawLine(QPointF(bx0, by0 - 4), QPointF(bx0, by0 + 4))
        painter.drawLine(QPointF(bx0 + bar_px, by0 - 4),
                         QPointF(bx0 + bar_px, by0 + 4))
        f_s = QFont("Segoe UI", max(8, side // 30))  # v321 agrandi
        painter.setFont(f_s)
        painter.setPen(QColor("#1A252F"))
        painter.drawText(int(bx0), int(by0 - 6), f"{shown:g} {unit}")
        painter.setPen(QColor("#566573"))
        painter.setFont(QFont("Segoe UI", max(7, side // 34)))
        painter.drawText(int(bx0 + bar_px + 8), int(by0 + 4),
                         f"±{buf:g} {unit}")
    finally:
        painter.end()
    return img


def compose_export_page(dock, section_img, legend_img = None, cartouche_img = None, locator_img = None, gap = 8, footer_img = None):
    """Compose page export v2.9.56.

    Coupe à gauche. Colonne droite : légende en haut, mini-carte
    calée en bas alignée sur le bas de la coupe (pas de carte qui
    flotte toute seule sous un grand vide blanc).
    """
    if section_img is None or section_img.isNull():
        return section_img
    sh, sw = section_img.height(), section_img.width()
    lh = legend_img.height() if legend_img is not None and not legend_img.isNull() else 0
    lw = legend_img.width() if legend_img is not None and not legend_img.isNull() else 0
    loc_h = locator_img.height() if locator_img is not None and not locator_img.isNull() else 0
    loc_w = locator_img.width() if locator_img is not None and not locator_img.isNull() else 0
    car_h = cartouche_img.height() if cartouche_img is not None and not cartouche_img.isNull() else 0
    foot_h = footer_img.height() if footer_img is not None and not footer_img.isNull() else 0

    # largeur colonne droite
    right_w = max(lw, loc_w) if (lw or loc_w) else 0
    # hauteur utile droite dans l'emprise coupe : légende + carte
    # si légende+carte > coupe → on garde la hauteur max (légende longue)
    # mais la carte est collée au bas de la coupe quand elle rentre
    right_content_h = lh
    if loc_h:
        # espace mini pour carte sous légende
        right_content_h = max(lh + (gap if lh else 0) + loc_h, sh)
    else:
        right_content_h = max(lh, sh) if lh else sh

    left_w = sw
    body_h = max(sh, lh if not loc_h else min(
        max(sh, lh + gap + loc_h),
        max(sh, lh) + (0 if lh + gap + loc_h <= sh else gap + loc_h)))
    # plus simple et stable :
    # - body_h = max(section, legend)  si pas de carte ou carte dans emprise
    # - si légende + carte dépassent la coupe : body = legend + gap + map
    if loc_h and lh:
        if lh + gap + loc_h <= sh:
            body_h = sh  # carte dans le blanc sous légende, alignée bas coupe
        else:
            body_h = lh + gap + loc_h  # légende longue : carte juste dessous
    elif loc_h:
        body_h = max(sh, loc_h)
    else:
        body_h = max(sh, lh)

    body_w = left_w + (gap + right_w if right_w else 0)
    margin = 6
    page_w = body_w + margin * 2
    page_h = (car_h + body_h + foot_h + margin * 2
              + (6 if car_h else 0) + (6 if foot_h else 0))

    if page_w * page_h > 100_000_000:
        return section_img

    out = QImage(page_w, page_h, QImage.Format_RGB32)
    if out.isNull():
        return section_img
    out.fill(QColor("#FFFFFF"))
    painter = QPainter(out)
    if not painter.isActive():
        return section_img
    try:
        y = margin
        x0 = margin
        if car_h:
            painter.drawImage(x0, y, cartouche_img)
            y += car_h + 4
        body_top = y
        painter.drawImage(x0, y, section_img)
        if right_w:
            rx = x0 + left_w + gap
            # légende en haut de la colonne
            if lh:
                painter.drawImage(rx, body_top, legend_img)
            # mini-carte : bas-alignée sur le bas de la COUPE si possible
            if loc_h:
                if lh and (lh + gap + loc_h <= sh):
                    # place sous légende, collée au bas de la coupe
                    ly = body_top + sh - loc_h
                    # ne pas chevaucher la légende
                    ly = max(ly, body_top + lh + gap)
                elif lh:
                    # légende longue : juste sous la légende
                    ly = body_top + lh + gap
                else:
                    ly = body_top + sh - loc_h
                lx = rx + max(0, (right_w - loc_w) // 2)
                # cadre discret
                painter.fillRect(
                    lx - 2, ly - 2, loc_w + 4, loc_h + 4,
                    QColor("#FFFFFF"))
                painter.setPen(QPen(QColor("#B0B8C0"), 1))
                painter.setBrush(QBrush(Qt.NoBrush))
                painter.drawRect(lx - 2, ly - 2, loc_w + 3, loc_h + 3)
                painter.drawImage(lx, ly, locator_img)
        y = body_top + body_h + 4
        if foot_h:
            painter.drawImage(x0, y, footer_img)
    finally:
        painter.end()
    return out


def stamp_locator_on_section(dock, section_img, size_px = 400):
    """Colle la mini-carte en bas-gauche de la coupe (toujours visible).

    v2.9.54 — ``size_px`` est la taille CIBLE sur la page export
    (plus de plafond 220 px qui rendait la carte invisible en HD).
    """
    if section_img is None or section_img.isNull():
        return section_img
    sw = section_img.width()
    sh = section_img.height()
    # cible : size_px demandé, bornée à ~22 % largeur / 28 % hauteur
    target = int(size_px)
    target = max(280, min(target, int(sw * 0.22), int(sh * 0.28)))
    try:
        # peindre déjà à la bonne taille (texte net)
        loc = dock._paint_locator_map(size=target, scale=1.0)
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export : tampon locator sur coupe", _exc)
        loc = None
    if loc is None or loc.isNull():
        return section_img
    if loc.width() != target:
        loc = loc.scaled(target, target, Qt.KeepAspectRatio,
                         Qt.SmoothTransformation)
    out = QImage(section_img)
    painter = QPainter(out)
    if not painter.isActive():
        return section_img
    try:
        margin = max(10, target // 40)
        x = margin
        y = out.height() - loc.height() - margin
        # fond + cadre un peu plus marqué
        border = max(2, target // 100)
        painter.fillRect(
            x - border, y - border,
            loc.width() + 2 * border, loc.height() + 2 * border,
            QColor("#FFFFFF"))
        painter.setPen(QPen(QColor("#5D6D7E"), max(1, border)))
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawRect(
            x - border, y - border,
            loc.width() + 2 * border - 1, loc.height() + 2 * border - 1)
        painter.drawImage(x, y, loc)
    finally:
        painter.end()
    return out


def render_canvas_to_png(dock, path: str, max_edge_px: int = 20000, include_legends: bool = False, min_scale: float = 4.0, fmt: str = 'png', include_map: bool = True):
    """Rendu page export PNG ultra-HD.

    v2.9.95 — PNG seul (~20 000 px grand côté, scale↑).
    Plus de branche SVG. Sans constBits/memoryview.

    v2.9.115 — exagération verticale forcée à **1.0** pendant l'export
    (précaution géométrique) : le slider dock n'est pas touché ; la
    scène est re-rendue en ×1 le temps du PNG, puis restaurée.
    """
    fmt = "png"  # SVG retiré (v2.9.67)
    if (fmt or "").lower() == "svg":
        return False, _tr("Export SVG retiré — utilisez le PNG.")

    painter = None
    # v2.9.115 — snapshot exag. dock (slider non modifié)
    _saved_v_exag = None
    _exag_forced = False
    try:
        canvas = dock.canvas

        # Forcer ×1 pour l'export (géométrie réelle) sans toucher l'UI.
        try:
            _saved_v_exag = float(getattr(canvas, "_v_exag", 1.0) or 1.0)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export PNG : rendu du canvas", _exc)
            _saved_v_exag = 1.0
        # v2.9.307 — l'export GARDE l'exagération de l'écran (annotée par
        # la barre d'échelle « Exag. V: ×N ») : les puits restent visibles
        # dans le PNG ; le ×1 forcé de la v2.9.115 est retiré.

        # Scène après éventuel re-render ×1 (pas le handle pré-export)
        scene = getattr(canvas, "scene", None)
        if scene is None:
            return False, _tr("Scène absente.")

        source = dock._export_scene_rect(canvas)
        if (not source.isValid()
                or source.width() < 2 or source.height() < 2):
            return False, _tr("Emprise de coupe vide.")

        # Ultra-HD : ~20k grand côté, plafonds mémoire relevés
        max_edge_px = max(int(max_edge_px), 20000)
        min_scale = max(float(min_scale), 4.0)
        max_scale = 5.0
        max_pixels = 100_000_000

        scale = max(float(min_scale), 1.0)
        scale = min(scale, max_scale)
        longest = max(float(source.width()), float(source.height()))
        if longest * scale > max_edge_px:
            scale = max_edge_px / longest
        out_w = max(int(source.width() * scale + 0.5), 1)
        out_h = max(int(source.height() * scale + 0.5), 1)
        if out_w * out_h > max_pixels:
            r = (max_pixels / float(out_w * out_h)) ** 0.5
            out_w = max(int(out_w * r), 100)
            out_h = max(int(out_h * r), 100)

        img = QImage(out_w, out_h, QImage.Format_RGB32)
        if img.isNull():
            return False, _tr("Mémoire insuffisante ({0}×{1})."
                              ).format(out_w, out_h)
        img.fill(QColor("#FFFFFF"))

        painter = QPainter(img)
        if not painter.isActive():
            return False, "QPainter inactif."
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            target = QRectF(0, 0, float(out_w), float(out_h))
            # v2.9.89 — export SANS surbrillance légende (état par défaut)
            _hl_state = None
            try:
                # v2.9.114 — pen contour fin pour PNG (0.9), dock reste 1.85
                if hasattr(canvas, "set_outline_export_mode"):
                    canvas.set_outline_export_mode(True)
                # 349 — l'exergue est un ÉTAT DE COUPE (réglé dans
                # le panneau propriétés) : le PNG montre l'écran tel
                # quel, surbrillance et estompage compris.  Plus de
                # case dans ce dialogue (348 retirée).
                canvas.highlight_hole(
                    getattr(canvas, "_selected", None))
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export PNG : rendu du canvas", _exc)
                # highlight optionnel
                _hl_state = None
            try:
                # v2.9.345 — parité écran/export : l'ordre « trou
                # sélectionné devant » (bandes +60) et « teneurs
                # au-dessus » sont réappliqués juste avant le rendu,
                # jamais perdus par un re-render intermédiaire.
                try:
                    canvas.highlight_hole(
                        getattr(canvas, "_selected", None))
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Export PNG : parité sélection", _exc)
                scene.render(painter, target, source, Qt.IgnoreAspectRatio)
            finally:
                try:
                    canvas.highlight_hole(
                        getattr(canvas, "_selected", None))
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Export PNG : rendu du canvas", _exc)
                    # restore best-effort
                    pass
                try:
                    if hasattr(canvas, "set_outline_export_mode"):
                        canvas.set_outline_export_mode(False)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Export PNG : rendu du canvas", _exc)
                    # restore pen dock best-effort
                    pass
        finally:
            painter.end()
            painter = None

        legend = None
        if include_legends:
            try:
                # v2.9.57 — légende plus grande : vise ~85 % hauteur coupe
                # (remplit la colonne dédiée, plus "trop petite")
                # v2.9.65 — scale un cran plus haut, plafond inchangé
                leg_scale = max(2.15, min(3.4, img.height() / 1050.0))
                col_w = max(300, min(480, int(105 * leg_scale)))
                legend = dock._paint_legends_image(
                    col_w=col_w, scale=leg_scale,
                    target_height=img.height())
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export PNG : rendu du canvas", _exc)
                legend = None

        # mini-carte : carré lisible sous légende (nord + échelle)
        locator = None
        if include_map:
            try:
                leg_w0 = (legend.width() if legend is not None
                          and not legend.isNull() else 0)
                leg_h0 = (legend.height() if legend is not None
                          and not legend.isNull() else 0)
                room = max(200, img.height() - leg_h0 - 20) if leg_h0 else (
                    img.height() // 4)
                # largeur ≈ légende, hauteur dans room
                loc_px = min(
                    leg_w0 if leg_w0 >= 220 else max(240, out_w // 6),
                    room,
                    max(220, img.height() // 4),
                    640,
                )
                loc_px = max(220, int(loc_px))
                locator = dock._paint_locator_map(size=loc_px, scale=1.0)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export PNG : rendu du canvas", _exc)
                locator = None

        leg_w = (legend.width()
                 if legend is not None and not legend.isNull() else 0)
        loc_w = (locator.width()
                 if locator is not None and not locator.isNull() else 0)
        right_w = max(leg_w, loc_w)
        page_w_est = img.width() + (6 + right_w if right_w else 0) + 8
        try:
            tf_scale = max(1.4, min(3.0, img.height() / 1400.0))
            title_bar = dock._paint_export_title(
                page_w_est, scale=tf_scale)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export PNG : rendu du canvas", _exc)
            title_bar = None
        try:
            tf_scale = max(1.4, min(3.0, img.height() / 1400.0))
            footer_bar = dock._paint_export_footer(
                page_w_est, scale=tf_scale)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export PNG : rendu du canvas", _exc)
            footer_bar = None

        try:
            page = dock._compose_export_page(
                img, legend, title_bar, locator, gap=6,
                footer_img=footer_bar)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export PNG : rendu du canvas", _exc)
            # compose échoue → coupe seule
            page = img

        try:
            page = dock._crop_white_margins(page, pad=6)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export PNG : rendu du canvas", _exc)
            # crop optionnel
            pass

        # 339 — page paysage : si le contenu est plus haut que large,
        # élargir au ratio A4 (√2) et centrer — échelles intactes.
        if bool(getattr(dock, "_export_landscape", True)):
            try:
                if page.height() > page.width():
                    w2 = int(page.height() * 1.414)
                    big = QImage(w2, page.height(), QImage.Format_RGB32)
                    if not big.isNull():
                        big.fill(QColor("#FFFFFF"))
                        _pp = QPainter(big)
                        if _pp.isActive():
                            _pp.drawImage(
                                (w2 - page.width()) // 2, 0, page)
                            _pp.end()
                            page = big
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export PNG : page paysage", _exc)

        if page is None or page.isNull():
            return False, _tr("Image finale vide.")
        if not page.save(path, "PNG"):
            return False, _tr("Écriture fichier impossible.")
        return True, None
    except MemoryError:
        return False, _tr("Mémoire insuffisante (MemoryError).")
    except Exception as exc:  # noqa: BLE001
        # L'erreur remonte déjà au dialogue (repr) — le journal garde
        # la trace complète pour le diagnostic post-mortem.
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export PNG : échec du rendu (message remonté au "
                      "dialogue)", exc)
        return False, repr(exc)
    finally:
        if painter is not None:
            try:
                if painter.isActive():
                    painter.end()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export PNG : rendu du canvas", _exc)
                # painter mort
                pass
        # v2.9.115 — restaurer exag. dock après export (slider intact)
        if _exag_forced and _saved_v_exag is not None:
            try:
                canvas = getattr(dock, "canvas", None)
                if canvas is not None:
                    canvas._v_exag = float(_saved_v_exag)
                    if canvas._result is not None:
                        canvas._render()
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export PNG : rendu du canvas", _exc)
                # restore best-effort — dock reste utilisable
                try:
                    if getattr(dock, "canvas", None) is not None:
                        dock.canvas._v_exag = float(_saved_v_exag)
                except Exception as _exc:
                    from ..core.diagnostics import log_swallowed
                    log_swallowed("Export PNG : rendu du canvas", _exc)
                    # attr write best-effort
                    pass


def get_svg_generator_class(dock):
    """QSvgGenerator selon stack QGIS/PyQt."""
    try:
        from qgis.PyQt.QtSvg import QSvgGenerator
        return QSvgGenerator
    except Exception as _exc:
        from ..core.diagnostics import log_swallowed
        log_swallowed("Export SVG : classe générateur", _exc)
        try:
            from PyQt5.QtSvg import QSvgGenerator
            return QSvgGenerator
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("Export SVG : classe générateur", _exc)
            try:
                from PyQt6.QtSvg import QSvgGenerator
                return QSvgGenerator
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("Export SVG : classe générateur", _exc)
                return None


def render_canvas_to_svg(dock, path: str, include_legends: bool = True, include_map: bool = True, max_edge_px: int = 4800):
    """SVG retiré — bascule vers PNG."""
    return False, (
        _tr("Export SVG retiré. Exportez en PNG."))
