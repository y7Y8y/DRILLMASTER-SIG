"""
Vue 3D v2 — nouveau moteur (sans OpenGL), sans aucun code de l'ancienne 3D.

* Données : `main_dock.drillholes` — LES MÊMES forages que la coupe 2D
  (trajectoires, intervalles, couleurs du référentiel projet).
* Moteur : core/scene3d (numpy) — rendu logiciel, budget de segments,
  mode rapide pendant l'interaction, plein détail au repos.
* Interface compatible avec l'ancien widget (sync_with_project,
  reset_after_project_close, canvas._get_visible_drillholes) : le reste du
  plugin n'a rien à changer.
"""
from __future__ import annotations

import numpy as np
from qgis.PyQt.QtCore import QSettings, Qt, QThread, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QColor, QFont, QImage, QPainter, QPen
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..core.scene3d.adapter import ERR_NO_TRAJECTORY, scene_from_drillholes
from ..core.scene3d.camera import OrbitCamera
from ..core.scene3d.zones import detect_zones
from ..core.scene3d.render import (
    GRADE_RAMP, RenderScene, RenderStyle, categorical_colors, hex_to_rgb, numeric_breaks,
    numeric_colors, render_frame,
)

# Un couloir par domaine : décalage latéral (m) et rayon du tube (m).
LANES = {"Lithologie": (0.0, 1.1), "Altération": (-2.6, 0.8)}
ASSAY_LANES = ((2.6, 0.8), (4.4, 0.8), (6.2, 0.8))


class _BuildThread(QThread):
    """Construit modèle + index hors du fil d'interface."""
    done = pyqtSignal(int, object, object, str)

    def __init__(self, gen, drillholes, elements, parent=None):
        super().__init__(parent)
        self._gen = gen
        self._dhs = list(drillholes)
        self._elements = list(elements)

    def run(self):
        try:
            model = scene_from_drillholes(self._dhs, self._elements)
            scene = RenderScene(model)
            self.done.emit(self._gen, model, scene, "")
        except Exception as exc:  # message affiché dans la vue, pas de crash
            self.done.emit(self._gen, None, None, str(exc))


class _Viewport(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setMinimumSize(320, 240)
        self.setMouseTracking(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._last = None
        self._moved = False
        self._frame = None

    # --- interaction -----------------------------------------------------
    def mousePressEvent(self, ev):
        self._last = ev.pos()
        self._moved = False

    def mouseMoveEvent(self, ev):
        if self._last is None:
            return
        dx = ev.x() - self._last.x()
        dy = ev.y() - self._last.y()
        self._last = ev.pos()
        self._moved = True
        cam = self.owner.cam
        pan = (ev.buttons() & (Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton)
               or (ev.modifiers() & Qt.KeyboardModifier.ShiftModifier))
        if pan:
            cam.pan(dx, dy, self.height())
        else:
            cam.orbit(dx, dy)
        self.owner._request(fast=True)

    def mouseReleaseEvent(self, ev):
        if not self._moved:
            self.owner._pick(ev.x(), ev.y())
        self._last = None

    def wheelEvent(self, ev):
        steps = ev.angleDelta().y() / 120.0
        self.owner.cam.zoom(0.88 ** steps)
        self.owner._request(fast=True)

    def mouseDoubleClickEvent(self, ev):
        if not self.owner.focus_at(ev.x(), ev.y()):
            self.owner.fit_all()

    def resizeEvent(self, ev):
        self.owner._request(fast=False)

    # --- dessin ----------------------------------------------------------
    def paintEvent(self, ev):
        p = QPainter(self)
        o = self.owner
        w, h = max(self.width(), 2), max(self.height(), 2)
        if o.scene is None:
            p.fillRect(self.rect(), QColor(*o.style.bg))
            p.setPen(QColor(*o.style.text_rgb))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                       o.status_text())
            p.end()
            return
        fast = o._quality == "fast"
        rw, rh = (w // 2, h // 2) if fast else (w, h)
        img, st = render_frame(o.scene, o.cam, rw, rh, o._quality, style=o.style)
        self._frame = np.ascontiguousarray(img)
        qimg = QImage(self._frame.data, rw, rh, rw * 4, QImage.Format_RGBA8888)
        p.drawImage(self.rect(), qimg)
        o._last_stats = st
        o._paint_overlays(p, w, h)
        p.end()
        o._update_status()


class View3DV2(QWidget):
    """Remplace View3DWidget : même interface publique, nouveau moteur."""

    def __init__(self, workspace_state=None, main_dock=None, parent=None):
        super().__init__(parent)
        self.workspace_state = workspace_state
        self.main_dock = main_dock
        self._project = None
        self.cam = OrbitCamera()
        self.scene = None
        self.model = None
        self._gen = 0
        self._sig = None
        self._thread = None
        self._error = ""
        self._quality = "full"
        self._last_stats = None
        self._picked = ""
        self._active: dict[str, QCheckBox] = {}
        self.style = RenderStyle()
        self.spacing = 1.0          # écart entre pistes (multiplicateur)
        self.show_names = True      # noms de forages proches
        self.name_pt = 8            # taille des noms (pt)
        self._loading = False
        self._zones: list = []
        self._zone_labels = None
        self._layer_cache: dict[str, tuple] = {}   # nom -> (rgb, legend)
        self._legend: dict[str, list] = {}
        # compat ancien widget : `canvas._get_visible_drillholes()`
        self.canvas = self
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self._request(fast=False))
        self._build_ui()

    # ------------------------------------------------------------- UI
    def _label(self, name: str) -> str:
        """Nom de domaine affiché (traduit) ; les éléments (Li, Rb…) restent tels quels."""
        if name == "Lithologie":
            return self.tr("Lithologie")
        if name == "Altération":
            return self.tr("Altération")
        return name

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(3)
        # ligne 1 : domaines affichés + navigation entre zones
        row1 = QHBoxLayout()
        self.dom_box = QHBoxLayout()
        row1.addLayout(self.dom_box)
        row1.addStretch(1)
        self.zone_combo = QComboBox()
        self.zone_combo.setToolTip(self.tr("Aller à une zone du projet "
                                           "(Nord, Centre, Est…)"))
        self.zone_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.zone_combo.setMinimumContentsLength(14)
        self.zone_combo.currentIndexChanged.connect(self._on_zone)
        row1.addWidget(self.zone_combo)
        b_prev, b_next = QPushButton("◀"), QPushButton("▶")
        b_prev.setFixedWidth(28)
        b_next.setFixedWidth(28)
        b_prev.clicked.connect(lambda: self._step_zone(-1))
        b_next.clicked.connect(lambda: self._step_zone(1))
        row1.addWidget(b_prev)
        row1.addWidget(b_next)
        root.addLayout(row1)
        # ligne 2 : vues, exagération, cadrage, actualisation, réglages
        row2 = QHBoxLayout()
        for label, yaw, pitch in ((self.tr("Perspective"), 20, 35),
                                  (self.tr("Plan"), 0, 89),
                                  (self.tr("Face N"), 0, 0),
                                  (self.tr("Face E"), 90, 0)):
            b = QPushButton(label)
            b.clicked.connect(lambda _c=False, y=yaw, p=pitch: self._preset(y, p))
            row2.addWidget(b)
        row2.addStretch(1)
        row2.addWidget(QLabel(self.tr("Exag. Z")))
        self.exag = QDoubleSpinBox()
        self.exag.setRange(0.5, 10.0)
        self.exag.setSingleStep(0.5)
        self.exag.setValue(1.0)
        self.exag.valueChanged.connect(self._on_exag)
        row2.addWidget(self.exag)
        btn_fit = QPushButton(self.tr("Cadrer"))
        btn_fit.clicked.connect(self.fit_all)
        row2.addWidget(btn_fit)
        btn_ref = QPushButton(self.tr("Actualiser"))
        btn_ref.setToolTip(self.tr("Reconstruit la scène depuis les forages "
                                   "du projet."))
        btn_ref.clicked.connect(lambda: self.rebuild(force=True))
        row2.addWidget(btn_ref)
        self.btn_set = QPushButton(self.tr("Réglages"))
        self.btn_set.setCheckable(True)
        self.btn_set.toggled.connect(lambda on: self.panel.setVisible(on))
        row2.addWidget(self.btn_set)
        root.addLayout(row2)
        self._build_panel(root)
        self.view = _Viewport(self)
        root.addWidget(self.view, 1)
        self.lbl = QLabel("")
        self.lbl.setStyleSheet("color:#5a6470;")
        self.lbl.setWordWrap(False)
        self.lbl.setMinimumWidth(50)
        root.addWidget(self.lbl)

    # --------------------------------------------------------- réglages
    DETAIL = (("Léger", 80_000, 25_000), ("Normal", 220_000, 40_000),
              ("Élevé", 450_000, 70_000))

    def _build_panel(self, root):
        self.panel = QWidget()
        g = QGridLayout(self.panel)
        g.setContentsMargins(2, 2, 2, 2)
        g.setHorizontalSpacing(10)

        def spin(lo, hi, val, step=1, dec=None):
            if dec is None:
                w = QSpinBox()
                w.setRange(lo, hi)
                w.setValue(val)
            else:
                w = QDoubleSpinBox()
                w.setDecimals(dec)
                w.setRange(lo, hi)
                w.setSingleStep(step)
                w.setValue(val)
            return w

        self.s_trace = spin(0, 4, 0)
        self.s_trace.setSpecialValueText(self.tr("auto"))
        self.s_trace.setToolTip(self.tr("Épaisseur des trajectoires en pixels "
                                        "(auto = selon la distance)."))
        self.s_tube = spin(0.3, 4.0, 1.0, 0.1, 1)
        self.s_tube.setToolTip(self.tr("Épaisseur des intervalles "
                                       "(lithologie, teneurs…), ×."))
        self.s_gap = spin(0.5, 3.0, 1.0, 0.1, 1)
        self.s_gap.setToolTip(self.tr("Écart latéral entre les pistes "
                                      "d'un même forage, ×."))
        self.s_collar = spin(0, 4, 1)
        self.s_collar.setToolTip(self.tr("Taille des collets (0 = 1 pixel)."))
        self.s_name = spin(6, 14, 8)
        self.s_name.setToolTip(self.tr("Taille du texte des noms de forages."))
        self.c_detail = QComboBox()
        for lab, _a, _b in self.DETAIL:
            self.c_detail.addItem(self.tr(lab))
        self.c_detail.setCurrentIndex(1)
        self.c_detail.setToolTip(self.tr(
            "Nombre maximal de segments dessinés : « Léger » est plus fluide, "
            "« Élevé » plus complet."))
        self.c_bg = QComboBox()
        self.c_bg.addItem(self.tr("Clair"))
        self.c_bg.addItem(self.tr("Sombre"))
        self.k_names = QCheckBox(self.tr("Noms des forages"))
        self.k_names.setChecked(True)
        b_reset = QPushButton(self.tr("Réinitialiser"))
        b_reset.clicked.connect(self._reset_settings)

        cells = ((self.tr("Trajectoires"), self.s_trace),
                 (self.tr("Intervalles ×"), self.s_tube),
                 (self.tr("Écart pistes ×"), self.s_gap),
                 (self.tr("Collets"), self.s_collar),
                 (self.tr("Texte"), self.s_name),
                 (self.tr("Détail"), self.c_detail),
                 (self.tr("Fond"), self.c_bg))
        for i, (lab, w) in enumerate(cells):
            r0, col = (0, i) if i < 4 else (2, i - 4)
            g.addWidget(QLabel(lab), r0, col)
            g.addWidget(w, r0 + 1, col)
        g.addWidget(self.k_names, 3, 3)
        g.addWidget(b_reset, 2, 3)
        for w in (self.s_trace, self.s_tube, self.s_collar, self.s_name):
            w.valueChanged.connect(self._on_settings)
        self.s_gap.valueChanged.connect(self._on_gap)
        self.c_detail.currentIndexChanged.connect(self._on_settings)
        self.c_bg.currentIndexChanged.connect(self._on_settings)
        self.k_names.toggled.connect(self._on_settings)
        root.addWidget(self.panel)
        self.panel.setVisible(False)
        self._load_settings()

    def _apply_settings(self):
        st = self.style
        st.trace_px = int(self.s_trace.value())
        st.tube_scale = float(self.s_tube.value())
        st.collar_half = int(self.s_collar.value())
        st.dark = self.c_bg.currentIndex() == 1
        _lab, full, fast = self.DETAIL[max(self.c_detail.currentIndex(), 0)]
        st.budget_full, st.budget_fast = full, fast
        self.name_pt = int(self.s_name.value())
        self.show_names = self.k_names.isChecked()
        self.spacing = float(self.s_gap.value())

    def _on_settings(self, *_a):
        if self._loading:
            return
        self._apply_settings()
        self._save_settings()
        self._request(fast=False)

    def _on_gap(self, *_a):
        if self._loading:
            return
        self._apply_settings()
        self._save_settings()
        self._reapply_layers()
        self._request(fast=False)

    def _reapply_layers(self):
        """L'écart entre pistes change les positions : on reconstruit les couches."""
        if self.scene is None:
            return
        for name, cb in self._active.items():
            if cb.isChecked():
                self.scene.layers.pop(name, None)
                self._apply_layer(name, True)

    _KEYS = (("trace", "s_trace"), ("tube", "s_tube"), ("gap", "s_gap"),
             ("collar", "s_collar"), ("name", "s_name"))

    def _load_settings(self):
        q = QSettings()
        self._loading = True
        try:
            for key, attr in self._KEYS:
                w = getattr(self, attr)
                v = q.value("DrillMaster/view3d/" + key)
                if v is not None:
                    try:
                        w.setValue(type(w.value())(v))
                    except (TypeError, ValueError):
                        pass
            for key, w in (("detail", self.c_detail), ("bg", self.c_bg)):
                v = q.value("DrillMaster/view3d/" + key)
                try:
                    if v is not None and 0 <= int(v) < w.count():
                        w.setCurrentIndex(int(v))
                except (TypeError, ValueError):
                    pass
            v = q.value("DrillMaster/view3d/names")
            if v is not None:
                self.k_names.setChecked(str(v).lower() in ("1", "true"))
        finally:
            self._loading = False
        self._apply_settings()

    def _save_settings(self):
        q = QSettings()
        for key, attr in self._KEYS:
            q.setValue("DrillMaster/view3d/" + key, getattr(self, attr).value())
        q.setValue("DrillMaster/view3d/detail", self.c_detail.currentIndex())
        q.setValue("DrillMaster/view3d/bg", self.c_bg.currentIndex())
        q.setValue("DrillMaster/view3d/names", int(self.k_names.isChecked()))

    def _reset_settings(self):
        self._loading = True
        try:
            self.s_trace.setValue(0)
            self.s_tube.setValue(1.0)
            self.s_gap.setValue(1.0)
            self.s_collar.setValue(1)
            self.s_name.setValue(8)
            self.c_detail.setCurrentIndex(1)
            self.c_bg.setCurrentIndex(0)
            self.k_names.setChecked(True)
        finally:
            self._loading = False
        self._apply_settings()
        self._save_settings()
        self._reapply_layers()
        self._request(fast=False)

    def status_text(self) -> str:
        if self._error:
            return self.tr("Vue 3D : {}").format(self._error)
        if self._thread is not None and self._thread.isRunning():
            return self.tr("Construction de la scène 3D…")
        return self.tr("Aucun forage chargé — importez les données "
                       "(étapes 2 et 3) puis revenez ici.")

    def _update_status(self):
        st = self._last_stats
        if not st or not self.model:
            return
        txt = self.tr("{} forages · {} segments · {:.0f} ms ({})").format(
            self.model.holes.n, f"{st.segments:,}".replace(",", " "), st.ms,
            self.tr("rapide") if st.quality == "fast" else self.tr("complet"))
        if self._picked:
            txt = self._picked + "   |   " + txt
        self.lbl.setText(txt)

    # ----------------------------------------------- interface compatible
    def _get_visible_drillholes(self):
        return list(getattr(self.main_dock, "drillholes", None) or [])

    def reset_after_project_close(self):
        self._gen += 1
        self.scene = None
        self.model = None
        self._sig = None
        self._layer_cache.clear()
        self._legend.clear()
        self._error = ""
        self._clear_checks()
        self._zones, self._zone_labels = [], None
        self.zone_combo.blockSignals(True)
        self.zone_combo.clear()
        self.zone_combo.blockSignals(False)
        self.view.update()

    def sync_with_project(self, project, active_section_line=None):
        if not project:
            return
        self._project = project
        self.rebuild(force=False)

    # ---------------------------------------------------------- données
    def _wanted_elements(self):
        try:
            from ..core.multi_assay import active_elements
            return list(active_elements(self._project.get_assay_style()))
        except Exception:
            return []

    def rebuild(self, force=False):
        dhs = self._get_visible_drillholes()
        elems = self._wanted_elements()
        sig = (id(self._project), id(getattr(self.main_dock, "drillholes", None)),
               len(dhs), tuple(elems))
        if not force and sig == self._sig and self.scene is not None:
            self.view.update()
            return
        self._sig = sig
        self._error = ""
        if not dhs:
            self.scene = None
            self.model = None
            self.view.update()
            return
        self._gen += 1
        self.scene = None
        self._thread = _BuildThread(self._gen, dhs, elems, self)
        self._thread.done.connect(self._on_built)
        self._thread.start()
        self.view.update()

    def _on_built(self, gen, model, scene, err):
        if gen != self._gen:
            return                                   # résultat périmé
        if err:
            self._error = (self.tr("Aucun forage avec trajectoire exploitable.")
                           if err == ERR_NO_TRAJECTORY else err)
            self.view.update()
            return
        self.model, self.scene = model, scene
        self._layer_cache.clear()
        self._legend.clear()
        self._rebuild_checks()
        self._build_zones()
        self.fit_all()

    # ----------------------------------------------------- domaines/couches
    def _clear_checks(self):
        for cb in self._active.values():
            cb.setParent(None)
            cb.deleteLater()
        self._active.clear()

    def _rebuild_checks(self):
        self._clear_checks()
        for name in self.model.domains:
            cb = QCheckBox(self._label(name))
            cb.setChecked(name == "Lithologie" or name == self._first_assay())
            cb.toggled.connect(lambda _v, n=name: self._on_domain(n))
            self.dom_box.addWidget(cb)
            self._active[name] = cb
        if not any(cb.isChecked() for cb in self._active.values()) and self._active:
            next(iter(self._active.values())).setChecked(True)
        for name, cb in self._active.items():
            if cb.isChecked():
                self._apply_layer(name, True)

    def _first_assay(self):
        for name, t in self.model.domains.items():
            if t.kind == "num":
                return name
        return None

    def _lane(self, name):
        if name in LANES:
            off, rad = LANES[name]
        else:
            nums = [n for n, t in self.model.domains.items() if t.kind == "num"]
            k = nums.index(name) if name in nums else 0
            off, rad = ASSAY_LANES[min(k, len(ASSAY_LANES) - 1)]
        return off * self.spacing, rad

    def _colors_for(self, name):
        if name in self._layer_cache:
            return self._layer_cache[name]
        t = self.model.domains[name]
        if t.kind == "cat":
            dom_key = "lithology" if name == "Lithologie" else "alteration"
            pal, legend = {}, []
            for code_idx, code in enumerate(t.categories):
                col = ""
                try:
                    col = self._project.resolve_category_style(
                        dom_key, code).color
                except Exception:
                    col = ""
                rgb = hex_to_rgb(col, default=(150, 150, 150))
                pal[code_idx] = rgb
                legend.append((rgb, code or "?"))
            rgb_arr = categorical_colors(t.value, pal)
        else:
            br = numeric_breaks(t.value, len(GRADE_RAMP))
            rgb_arr = numeric_colors(t.value, br)
            legend = []
            for i in range(len(br) + 1):
                if i == 0:
                    lab = f"< {br[0]:.3g}" if br.size else "—"
                elif i == len(br):
                    lab = f"≥ {br[-1]:.3g}"
                else:
                    lab = f"{br[i-1]:.3g} – {br[i]:.3g}"
                legend.append((GRADE_RAMP[min(i, len(GRADE_RAMP) - 1)], lab))
        self._layer_cache[name] = (rgb_arr, legend)
        return self._layer_cache[name]

    def _apply_layer(self, name, on):
        if self.scene is None:
            return
        if not on:
            self.scene.layers.pop(name, None)
            self._legend.pop(name, None)
            return
        rgb, legend = self._colors_for(name)
        off, rad = self._lane(name)
        if name not in self.scene.layers:
            self.scene.set_layer(name, rgb, rad, off)
        self._legend[name] = legend

    def _on_domain(self, name):
        self._apply_layer(name, self._active[name].isChecked())
        self._request(fast=False)

    # ---------------------------------------------------------- caméra
    def fit_all(self):
        if self.scene is None:
            return
        self.cam.z_exag = float(self.exag.value())
        lo, hi = self.scene.lo.copy(), self.scene.hi.copy()
        self.cam.fit(lo, hi)
        self._request(fast=False)

    def _build_zones(self):
        h = self.model.holes
        o = self.model.origin
        xy = np.stack([h.x - o[0], h.y - o[1]], axis=1)
        self._zone_labels, self._zones = detect_zones(xy)
        self.zone_combo.blockSignals(True)
        self.zone_combo.clear()
        self.zone_combo.addItem(self.tr("Toutes les zones"))
        for z in self._zones:
            self.zone_combo.addItem(self.tr("{} · {} forages").format(
                z["name"], z["count"]))
        self.zone_combo.setEnabled(len(self._zones) > 1)
        self.zone_combo.blockSignals(False)

    def _zone_box(self, zid):
        hidx = (self.model.holes.st_key // 1.0e4).astype(np.int64)
        pts = (self.model.holes.st_xyz - self.model.origin)[
            self._zone_labels[hidx] == zid]
        return pts.min(axis=0), pts.max(axis=0)

    def _on_zone(self, idx):
        if self.scene is None or not self._zones:
            return
        if idx <= 0:
            self.fit_all()
            return
        lo, hi = self._zone_box(idx - 1)
        self.cam.z_exag = float(self.exag.value())
        self.cam.fit(lo, hi)
        self._request(fast=False)

    def _step_zone(self, d):
        n = self.zone_combo.count()
        if n > 1:
            self.zone_combo.setCurrentIndex((self.zone_combo.currentIndex() + d) % n)

    def focus_at(self, x, y) -> bool:
        """Double-clic sur un forage : on se recentre dessus."""
        if self.scene is None:
            return False
        w, h = self.view.width(), self.view.height()
        sx, sy, dz, ok = self.cam.project(self.scene.collars, w, h)
        d = np.hypot(sx - x, sy - y)
        d[~ok] = 1e9
        i = int(np.argmin(d))
        if d[i] > 30:
            return False
        L = float(self.model.holes.length[i])
        self.cam.target = self.scene.collars[i].astype(float) + np.array([0, 0, -L * 0.4])
        self.cam.dist = max(L * 2.2, 60.0)
        self.cam.near = 0.5
        self._request(fast=False)
        return True

    def _preset(self, yaw, pitch):
        self.cam.set_view(yaw, pitch)
        self._request(fast=False)

    def _on_exag(self, v):
        self.cam.z_exag = float(v)
        self._request(fast=False)

    def _request(self, fast):
        self._quality = "fast" if fast else "full"
        self.view.update()
        if fast:
            self._timer.start(160)       # plein détail au repos

    # -------------------------------------------------------- overlays
    def _paint_overlays(self, p, w, h):
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        small = QFont(p.font())
        small.setPointSizeF(float(self.name_pt))
        p.setFont(small)
        ink = QColor(*self.style.text_rgb)
        # légende (calculée d'abord : les libellés l'évitent)
        leg_h = 8 + sum(14 + 13 * min(len(it), 12) + 8
                        for it in self._legend.values())
        taken = [(w - 155, 0, 155, leg_h)]
        # libellés des collets proches, sans chevauchement
        if self.show_names and self.cam.dist < 700 and self.scene is not None:
            sx, sy, dz, ok = self.cam.project(self.scene.collars, w, h)
            k = np.nonzero(ok & (sx > 0) & (sx < w - 40) & (sy > 12) & (sy < h))[0]
            k = k[np.argsort(dz[k])][:80]
            fm = p.fontMetrics()
            p.setPen(ink)
            shown = 0
            for i in k:
                txt = str(self.model.holes.ids[i])
                tw, th = fm.horizontalAdvance(txt), fm.height()
                x0, y0 = int(sx[i]) + 5, int(sy[i]) - th
                if any(x0 < rx + rw and x0 + tw > rx and y0 < ry + rh
                       and y0 + th > ry for rx, ry, rw, rh in taken):
                    continue
                taken.append((x0, y0, tw, th))
                p.drawText(x0, y0 + th - 3, txt)
                shown += 1
                if shown >= 30:
                    break
        # légende des domaines affichés
        y = 8
        for name, items in self._legend.items():
            p.setPen(ink)
            p.drawText(w - 150, y + 10, self._label(name))
            y += 14
            for rgb, lab in items[:12]:
                p.fillRect(w - 150, y, 12, 10, QColor(*rgb))
                p.setPen(QPen(QColor(120, 128, 138), 1))
                p.drawRect(w - 150, y, 12, 10)
                p.setPen(ink)
                p.drawText(w - 133, y + 9, str(lab))
                y += 13
            y += 8

    def _pick(self, x, y):
        """Clic = identifie le forage le plus proche du curseur."""
        if self.scene is None:
            return
        w, h = self.view.width(), self.view.height()
        sx, sy, dz, ok = self.cam.project(self.scene.collars, w, h)
        d = np.hypot(sx - x, sy - y)
        d[~ok] = 1e9
        i = int(np.argmin(d))
        if d[i] < 14:
            self._picked = self.tr("{} · profondeur {:.0f} m").format(
                self.model.holes.ids[i], float(self.model.holes.length[i]))
        else:
            self._picked = ""
        self._update_status()
