"""Profils d'affichage par type d'ouvrage (v2.9.289 → v2.9.294).

v2.9.294 — dialogue SIMPLIFIÉ (retour écran « quel table encore ?? ») :
la table par forage est SUPPRIMÉE.  Il reste l'essentiel :

  - une case « Activer les profils » ;
  - UN choix « Type de forage » (RC/DD · Auger · Puits) qui traite
    TOUS les trous ;
  - une phrase explicative ;
  - v2.9.308 : fond blanc des étiquettes de profondeur (case) ;
  - v2.9.310 : encart « zone » dans la vue (case).

Écrit dans ``project.config["display_profiles"]``, lu par
generate_section() (2D + export PNG).
"""
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QCheckBox, QDoubleSpinBox,
    QDialogButtonBox, QLabel, QComboBox)


class DisplayProfilesDialog(QDialog):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        cfg = (project.config.get("display_profiles") or {}) if project else {}
        params = cfg.get("params") or {}
        self.setWindowTitle(self.tr("Profils d'affichage par type d'ouvrage"))
        lay = QVBoxLayout(self)
        self.enabled = QCheckBox(self.tr(
            "Activer les profils (AUGER/PUITS agrandis, RC-DD inchangés)"))
        self.enabled.setChecked(bool(cfg.get("enabled", True)))
        lay.addWidget(self.enabled)
        # v2.9.293/294 — « l'utilisateur dit puits → on traite puits ».
        # v2.9.299 — même nom partout : « Type de forage ».
        lay.addWidget(QLabel(self.tr("Type de forage :")))
        self.global_combo = QComboBox()
        self.global_combo.addItem(self.tr("RC / DD"), "RC")
        self.global_combo.addItem(self.tr("Auger"), "AUGER")
        self.global_combo.addItem(self.tr("Puits"), "PUITS")
        # v2.9.298 — plus d'option « Auto » : le choix fait foi.
        cur_g = str(cfg.get("global") or "")
        idx = {"RC": 0, "AUGER": 1, "PUITS": 2}.get(cur_g, 0)
        self.global_combo.setCurrentIndex(idx)
        lay.addWidget(self.global_combo)
        # v2.9.308 — fond blanc des étiquettes de profondeur au choix ;
        # par défaut : halo blanc simple (lisible, discret).
        self.label_bg_chk = QCheckBox(self.tr(
            "Fond blanc derrière les étiquettes de profondeur"))
        self.label_bg_chk.setChecked(bool(cfg.get("label_bg", False)))
        lay.addWidget(self.label_bg_chk)
        # v2.9.310 — encart « zone » (plan des trous + fenêtre) dans la vue.
        self.zone_chk = QCheckBox(self.tr("Encart zone dans la vue"))
        self.zone_chk.setChecked(bool(cfg.get("zone_inset", False)))  # v315 défaut OFF
        lay.addWidget(self.zone_chk)
        note = QLabel(self.tr(
            "Le type choisi s'applique à TOUS les trous. Transformation "
            "monotone : AUGER/PUITS sont étirés pour rester lisibles, "
            "l'ordre des profondeurs est conservé, les étiquettes gardent "
            "les valeurs réelles."))
        note.setWordWrap(True)
        lay.addWidget(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def accept(self):
        if self.project:
            self.project.config["display_profiles"] = {
                "enabled": bool(self.enabled.isChecked()),
                "global": str(self.global_combo.currentData() or ""),
                "label_bg": bool(self.label_bg_chk.isChecked()),
                "zone_inset": bool(self.zone_chk.isChecked()),
            }
            self.project.save_config()
        # v2.9.301 — même aide : type étiré => exagération auto.
        sw = getattr(self.parent(), "section_widget", None)
        if str(self.global_combo.currentData() or "") in ("AUGER",
                                                          "PUITS"):
            if sw is not None and hasattr(sw, "_auto_vertical_exag"):
                sw._auto_vertical_exag()
        super().accept()
def attach_hole_type_row(section_widget, form):
    """v2.9.296 — « Type de forage » direct dans les propriétés de la coupe.

    Même choix, même config que le dialogue du menu Outils : écrire ici
    met à jour ``display_profiles.global``, sauvegarde et régénère la
    coupe immédiatement (le cache inclut les profils depuis v2.9.295).
    """
    main_dock = getattr(section_widget, "main_dock", None)
    project = getattr(main_dock, "project", None)
    cfg = {}
    if project is not None:
        cfg = (project.config.get("display_profiles") or {})
    combo = QComboBox()
    combo.addItem(section_widget.tr("RC / DD"), "RC")
    combo.addItem(section_widget.tr("Auger"), "AUGER")
    combo.addItem(section_widget.tr("Puits"), "PUITS")
    idx = {"RC": 0, "AUGER": 1, "PUITS": 2}.get(
        str(cfg.get("global") or ""), 0)
    combo.setCurrentIndex(idx)

    def _apply(_i=0):
        md = getattr(section_widget, "main_dock", None)
        proj = getattr(md, "project", None)
        if proj is None:
            return
        d = dict(proj.config.get("display_profiles") or {})
        if combo.currentData():
            d["enabled"] = True
        d["global"] = str(combo.currentData() or "")
        proj.config["display_profiles"] = d
        proj.save_config()
        # v2.9.301 — « pq aucune agissement, toujours petit ??? » : sur
        # une coupe de 2 km, un trou étiré à ~23 m reste ≈ 1 px à 1.0x.
        # Choisir Auger/Puits ajuste donc l'exagération verticale auto.
        if combo.currentData() in ("AUGER", "PUITS"):
            if hasattr(section_widget, "_auto_vertical_exag"):
                section_widget._auto_vertical_exag()
        cnv = getattr(section_widget, "canvas", None)
        if cnv is not None and hasattr(cnv, "_regenerate"):
            cnv._regenerate()
            cnv.update()

    combo.currentIndexChanged.connect(_apply)
    section_widget._hole_type_combo = combo  # v2.9.306 sync au chargement
    form.addRow(section_widget.tr("Type de forage"), combo)


def attach_surface_anchor_row(section_widget, form):
    """v2.9.314 — « Ancrer la ligne de sol aux collets » (propriétés coupe).

    OFF : la ligne de sol reste le MNT mesuré seul (DEM/CSV), stable
    quel que soit le jeu de trous affichés ; ON (défaut) : elle repasse
    exactement par chaque collet de la coupe (règle historique)."""
    main_dock = getattr(section_widget, "main_dock", None)
    project = getattr(main_dock, "project", None)
    cfg = {}
    if project is not None:
        cfg = (project.config.get("section_surface") or {})
    chk = QCheckBox(section_widget.tr(
        "Ancrer la ligne de sol aux collets"))
    chk.setChecked(bool(cfg.get("anchor_collars", True)))
    chk.setToolTip(section_widget.tr(
        "Décoché : ligne de sol = MNT mesuré seul, inchangée quand on "
        "ajoute/retire un trou ; coché : elle repasse par les collets."))

    def _apply(_state=0):
        md = getattr(section_widget, "main_dock", None)
        proj = getattr(md, "project", None)
        if proj is None:
            return
        d = dict(proj.config.get("section_surface") or {})
        d["anchor_collars"] = bool(chk.isChecked())
        proj.config["section_surface"] = d
        proj.save_config()
        cnv = getattr(section_widget, "canvas", None)
        if cnv is not None and hasattr(cnv, "_regenerate"):
            cnv._regenerate()
            cnv.update()

    chk.toggled.connect(_apply)
    form.addRow("", chk)


def attach_common_scale_row(section_widget, form):
    """v391/392/394 — « Échelle » et « Fenêtre d'élévation » des coupes.

    Par DÉFAUT : une échelle de projet automatique (la même 1:N pour toutes les
    coupes, 1 m horizontal = 1 m vertical) et une fenêtre d'élévation commune,
    comme le repère orthonormé de la vue 3D : 20 m d'altitude font la même
    hauteur sur toutes les coupes et les graduations tombent aux mêmes valeurs.
    L'ancien comportement (chaque coupe ajustée à la fenêtre) reste au choix.
    Mémorisé dans le projet (config « section_scale »).
    """
    from ..core.section_scale import (
        AUTO_RATIOS, COMMON_RATIOS, auto_project_ratio, unit_factor)
    project = getattr(getattr(section_widget, "main_dock", None), "project", None)
    cfg = (project.config.get("section_scale") or {}) if project is not None else {}
    raw = cfg.get("ratio", -1)
    try:
        cur = int(raw if raw is not None else -1)
    except (TypeError, ValueError):
        cur = -1
    # N que l'AUTO donnerait pour ce projet (affiché dans le libellé)
    lengths = []
    if project is not None:
        for sec in (project.config.get("sections") or []):
            try:
                lengths.append(float(sec.get("length") or 0.0))
            except (TypeError, ValueError):
                pass
    cnv0 = getattr(section_widget, "canvas", None)
    line0 = getattr(cnv0, "_line", None) if cnv0 is not None else None
    if line0 is not None:
        lengths.append(float(line0.length))
    n_auto = auto_project_ratio(max(lengths, default=0.0) or 1.0, 1.0) if lengths else None

    combo = QComboBox()
    combo.addItem(
        section_widget.tr("Projet (auto) — 1:{n}").format(n=n_auto)
        if n_auto else section_widget.tr("Projet (auto)"), -1)
    combo.addItem(section_widget.tr("Fenêtre (chaque coupe ajustée)"), 0)
    for n in sorted(set(COMMON_RATIOS) | set(AUTO_RATIOS)):
        combo.addItem(f"1:{n}", n)
    i = combo.findData(cur)
    combo.setCurrentIndex(i if i >= 0 else 0)
    combo.setToolTip(section_widget.tr(
        "« Projet (auto) » : la MÊME échelle pour toutes les coupes (choisie "
        "pour que la plus longue tienne à l'écran), 1 m horizontal = 1 m "
        "vertical, comme le repère de la vue 3D. « Fenêtre » ajuste chaque "
        "coupe à la fenêtre (échelles différentes, non comparables)."))

    def _save(**kv):
        proj = getattr(getattr(section_widget, "main_dock", None), "project", None)
        if proj is None:
            return
        d = dict(proj.config.get("section_scale") or {})
        d.update(kv)
        proj.config["section_scale"] = d
        proj.save_config()
        cnv = getattr(section_widget, "canvas", None)
        if cnv is not None and hasattr(cnv, "_render"):
            cnv._render()
            cnv.update()

    combo.currentIndexChanged.connect(lambda _i=0: _save(ratio=int(combo.currentData())))
    section_widget._common_scale_combo = combo
    form.addRow(section_widget.tr("Échelle"), combo)

    ecombo = QComboBox()
    ecombo.addItem(section_widget.tr("Commune au projet"), "project")
    ecombo.addItem(section_widget.tr("Propre à chaque coupe"), "auto")
    j = ecombo.findData(str(cfg.get("elev_window") or "project"))
    ecombo.setCurrentIndex(j if j >= 0 else 0)
    ecombo.setToolTip(section_widget.tr(
        "« Commune au projet » : toutes les coupes montrent la même plage "
        "d'altitudes avec les mêmes graduations, comme la vue 3D : un même "
        "horizon se retrouve à la même hauteur d'une coupe à l'autre."))
    ecombo.currentIndexChanged.connect(
        lambda _i=0: _save(elev_window=str(ecombo.currentData())))
    section_widget._elev_window_combo = ecombo
    form.addRow(section_widget.tr("Fenêtre d'élévation"), ecombo)
