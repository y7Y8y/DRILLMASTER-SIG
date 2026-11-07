"""DrillMaster — Forages de la coupe : exclusion (v2.9.179).

PROPOSITION VALIDÉE (docs/PROPOSITION_EXCLUSION_FORAGES_2D.md) :

- **Geste** : clic droit sur un forage de la coupe → « Exclure de la
  coupe » (régénération immédiate) ;
- **Gestion** : ligne compacte « Forages de la coupe : 12/14 [Gérer…] »
  dans le groupe Buffer — repliée par défaut (zéro encombrement),
  déplie la liste avec la distance au trait, les exclus barrés et
  « Tout inclure » ;
- **Sémantique** (D1–D3 validés) : exclu = ABSENT (échelles et ligne
  de sol recalculées sans lui) ; la 3D « Coupe active » suit (même
  ensemble via ``_result.holes``) ; PAS de liste blanche — le buffer
  sélectionne, l'exclusion retire ;
- **Persistance** : par coupe (``excluded_holes`` dans les paramètres
  sauvegardés, ``core/project.update_section``).

Le dock (``ui/section_dock.py``) délègue ici — le monolithe reste
sous son cliquet de lignes (BUD-160).
"""

from __future__ import annotations

import math
import re

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import (
    QFrame, QHBoxLayout, QListWidgetItem, QMenu, QPushButton,
    QListWidget, QVBoxLayout,
)

from .styles_qt import BUTTON_SECONDARY


def _tr(text):
    """v2.9.233 — Lot 1c : traduction (fonctions module — pas de self)."""
    from qgis.PyQt.QtCore import QCoreApplication
    return QCoreApplication.translate("SectionHolesPanel", text)


# Regex des infobulles d'intervalles — MÊME source que le clic-sélection
# (ui/section_dock.SectionCanvas._handle_interval_click).
_HOLE_TIP_RE = re.compile(
    r"([A-Za-z0-9_\-\.]+)\s*[·\:]\s*[0-9\.\,]+\s*[–\-]\s*[0-9\.\,]+\s*m")


def hole_id_at(canvas, pos):
    """Hit-test : le forage sous ``pos``, ou None.

    v2.9.180 — DEUX passes (retour écran : « il faut cliquer droit
    où ? ») :

    1. infobulle d'intervalle (précise — même convention que le clic
       gauche, même regex) ;
    2. **proximité** : n'importe quel item du forage (étiquette d'ID,
       symbole de collet, bande, trajectoire) à moins de 18 px — le
       clic droit marche donc PRES DU forage, pas seulement pile sur
       une bande colorée.
    """
    scene_pos = canvas.mapToScene(pos)
    for item in canvas.items(pos):
        if (hasattr(item, "acceptedMouseButtons")
                and item.acceptedMouseButtons() == Qt.NoButton):
            continue
        tip = item.toolTip() or ""
        m = _HOLE_TIP_RE.search(tip)
        if not m:
            continue
        is_inside = True
        if hasattr(item, "polygon"):
            is_inside = item.polygon().containsPoint(
                scene_pos, Qt.OddEvenFill)
        elif hasattr(item, "path"):
            is_inside = item.path().contains(scene_pos)
        if is_inside:
            return m.group(1)
    # v2.9.180 — repli proximité sur les items de chaque forage
    best_id = None
    best_d = 18.0
    for hole_id, items in (getattr(canvas, "_hole_items", None) or {}).items():
        for item in items or []:
            try:
                rect = item.sceneBoundingRect()
            except Exception as _exc:
                # item déjà détruit par la scène (rare) — règle de
                # l'audit C : capturé et journalisé, jamais silencieux.
                from ..core.diagnostics import log_swallowed
                log_swallowed(f"Forages de la coupe : hit-test de "
                              f"{hole_id!r} (item ignoré)", _exc)
                continue
            dx = max(rect.left() - scene_pos.x(), 0.0,
                     scene_pos.x() - rect.right())
            dy = max(rect.top() - scene_pos.y(), 0.0,
                     scene_pos.y() - rect.bottom())
            d = math.hypot(dx, dy)
            if d < best_d:
                best_d = d
                best_id = hole_id
    return best_id


def canvas_context_menu(canvas, event):
    """Menu contextuel du canvas 2D : exclusion du forage sous le curseur.

    Appelé par ``SectionCanvas.contextMenuEvent`` (délégation une
    ligne).  Rien sous le curseur → comportement par défaut.
    """
    dock = getattr(canvas, "_parent_section", None)
    if dock is None:
        event.ignore()
        return
    hole_id = hole_id_at(canvas, event.pos())
    if not hole_id:
        event.ignore()
        return
    menu = QMenu(canvas)
    exclude_action = menu.addAction(
        _tr("Exclure {} de la coupe").format(hole_id))
    # 351 — si ce trou est déjà devant, on propose de rendre la place.
    is_sel = getattr(canvas, "_selected", None) == hole_id
    if is_sel:
        select_action = menu.addAction(
            _tr("Libérer {} (ordre normal)").format(hole_id))
    else:
        select_action = menu.addAction(
            _tr("Sélectionner {} (passer devant)").format(hole_id))
    chosen = menu.exec_(event.globalPos())
    if chosen is exclude_action:
        exclude_hole(dock, hole_id)
    elif chosen is select_action:
        ws = getattr(getattr(dock, "main_dock", None),
                     "workspace_state", None)
        if ws is not None:
            ws.set("selected_hole_id", None if is_sel else hole_id)
        # 359 — effet VISIBLE : ordre explicite de superposition.
        canvas = getattr(dock, "canvas", None)
        if canvas is not None:
            if is_sel:
                canvas.send_hole_to_back(hole_id)
            else:
                canvas.bring_hole_to_front(hole_id)


# ────────────────────────────────────────────────────────────────────
# État + persistance
# ────────────────────────────────────────────────────────────────────
def _auto_expand_inclusion(dock):
    """v2.9.181 — le groupe « Inclusion des forages » s'ouvre TOUT SEUL
    dès qu'il y a des exclusions : le compteur « 12/14 » devient visible
    au moment précis où l'utilisateur se demande « où est passé DD003 ? »
    (retour écran : la bonne place est le groupe Inclusion — encore
    fallait-il le voir)."""
    group = getattr(dock, "inclusion_group", None)
    if group is not None and not group.header.isChecked():
        group.header.setChecked(True)   # déclenche _toggle → ouvre


def set_excluded(dock, hole_ids, regenerate=True):
    """Applique l'ensemble des forages exclus (état + coupe + projet)."""
    ids = {str(h) for h in (hole_ids or []) if h}
    changed = ids != set(dock._excluded_holes)
    dock._excluded_holes = ids
    if ids:
        _auto_expand_inclusion(dock)
    sid = getattr(dock, "_current_section_id", None)
    if sid is not None:
        dock._excluded_by_section[sid] = set(ids)
        project = dock._project()
        if project is not None:
            project.update_section(sid, excluded_holes=sorted(ids))
    if changed:
        dock.canvas._excluded_hole_ids = set(ids)
        if regenerate:
            dock._generate_and_display()
    refresh_hole_filter_ui(dock)


def exclude_hole(dock, hole_id):
    """Geste : exclure UN forage (clic droit sur la coupe)."""
    set_excluded(dock, set(dock._excluded_holes) | {str(hole_id)})


def include_hole(dock, hole_id):
    """Réinclure UN forage (case de la liste)."""
    set_excluded(dock, set(dock._excluded_holes) - {str(hole_id)})


def include_all(dock):
    """« Tout inclure » : vide les exclusions."""
    set_excluded(dock, set())


def restore_for_section(dock, section_id):
    """Activation d'une coupe : ses exclusions reviennent (historique)."""
    dock._excluded_holes = set(
        dock._excluded_by_section.get(section_id, set()))
    dock.canvas._excluded_hole_ids = set(dock._excluded_holes)
    if dock._excluded_holes:
        _auto_expand_inclusion(dock)   # v2.9.181


def parse_record(dock, record):
    """Lecture d'un enregistrement d'historique → exclusions par coupe."""
    try:
        ids = {str(h) for h in (record.get("excluded_holes") or []) if h}
    except AttributeError:
        ids = set()
    sid = record.get("id")
    if sid is not None:
        dock._excluded_by_section[int(sid)] = ids
    return ids


# ────────────────────────────────────────────────────────────────────
# Interface : ligne « Forages de la coupe : 12/14 [Gérer…] »
# ────────────────────────────────────────────────────────────────────
def build_hole_filter_row(dock) -> QFrame:
    """Construit la ligne compacte + la liste repliable (groupe Buffer)."""
    frame = QFrame()
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)

    from qgis.PyQt.QtWidgets import QLabel
    row = QHBoxLayout()
    dock.btn_hole_filter = QPushButton(_tr("Forages de la coupe : — · Gérer…"))
    dock.btn_hole_filter.setStyleSheet(BUTTON_SECONDARY)
    dock.btn_hole_filter.setToolTip(_tr(
        "Forages du corridor du buffer · déplie la liste · clic droit "
        "sur un forage de la coupe pour l'exclure"))
    dock.btn_hole_filter.clicked.connect(
        lambda: _toggle_list(dock))
    row.addWidget(dock.btn_hole_filter, 1)
    dock.btn_hole_filter_all = QPushButton(_tr("Tout inclure"))
    dock.btn_hole_filter_all.setStyleSheet(BUTTON_SECONDARY)
    dock.btn_hole_filter_all.setToolTip(_tr(
        "Réinclut tous les forages exclus de cette coupe"))
    dock.btn_hole_filter_all.clicked.connect(lambda: include_all(dock))
    row.addWidget(dock.btn_hole_filter_all)
    lay.addLayout(row)

    # v2.9.180 — l'astuce du clic droit, VISIBLE quand la liste est
    # ouverte (retour écran : « il faut cliquer droit où ? »).
    dock.lbl_hole_filter_hint = QLabel(
        _tr("Astuce : clic droit sur un forage de la coupe = exclusion immédiate"))
    dock.lbl_hole_filter_hint.setStyleSheet(
        "color: #95A5A6; font-size: 7.5pt; font-style: italic;")
    dock.lbl_hole_filter_hint.setVisible(False)
    lay.addWidget(dock.lbl_hole_filter_hint)

    dock.list_hole_filter = QListWidget()
    dock.list_hole_filter.setMaximumHeight(150)
    dock.list_hole_filter.setToolTip(_tr(
        "Coché = forage dessiné · décoché = exclu (échelles et ligne "
        "de sol recalculées sans lui)"))
    dock.list_hole_filter.itemChanged.connect(
        lambda item: _on_item_changed(dock, item))
    dock.list_hole_filter.setVisible(False)
    dock.btn_hole_filter_all.setVisible(False)
    lay.addWidget(dock.list_hole_filter)
    return frame


def _toggle_list(dock):
    show = not dock.list_hole_filter.isVisible()
    dock.list_hole_filter.setVisible(show)
    dock.btn_hole_filter_all.setVisible(show)
    dock.lbl_hole_filter_hint.setVisible(show)
    if show:
        refresh_hole_filter_ui(dock)


def _on_item_changed(dock, item):
    hole_id = item.data(Qt.UserRole)
    if hole_id is None:
        return
    if item.checkState() == Qt.Checked:
        include_hole(dock, hole_id)
    else:
        exclude_hole(dock, hole_id)


def refresh_hole_filter_ui(dock):
    """Met à jour le compteur « 12/14 » et la liste (distances au trait).

    Liste = les forages du CORRIDOR (candidats du buffer) — un forage
    hors buffer ne peut pas être inclus à la main (D3 : une règle par
    concept).
    """
    btn = getattr(dock, "btn_hole_filter", None)
    if btn is None:
        return
    candidates = _corridor_holes(dock)
    excluded = set(getattr(dock, "_excluded_holes", set()) or set())
    n_drawn = sum(1 for _hid, _d in candidates if _hid not in excluded)
    btn.setText(_tr("Forages de la coupe : {} / {}").format(
        n_drawn, len(candidates)))

    lst = dock.list_hole_filter
    lst.blockSignals(True)
    lst.clear()
    for hole_id, dist in candidates:
        item = QListWidgetItem(f"{hole_id} · {dist:.0f} m")
        item.setData(Qt.UserRole, hole_id)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(
            Qt.Unchecked if hole_id in excluded else Qt.Checked)
        if hole_id in excluded:
            f = QFont(item.font())
            f.setStrikeOut(True)
            item.setFont(f)
        lst.addItem(item)
    lst.blockSignals(False)
    getattr(dock, "btn_hole_filter_all", lst).setVisible(
        lst.isVisible() and bool(excluded))


def _corridor_holes(dock):
    """[(hole_id, distance)] des forages inclus par le buffer."""
    line = getattr(dock, "_line", None)
    dhs = getattr(dock, "_drillholes", None) or []
    if line is None or not dhs:
        return []
    try:
        buffer = float(dock.buffer_spin.value())
    except AttributeError:
        return []
    try:
        mode = dock.buffer_mode_combo.currentData() or "collar"
    except AttributeError:
        mode = "collar"
    from ..core.section import compute_buffer_diagnostics
    out = []
    for status in compute_buffer_diagnostics(dhs, line, buffer, mode):
        if status.get("included"):
            out.append((str(status.get("hole_id", "?")),
                        float(status.get("distance", 0.0) or 0.0)))
    out.sort(key=lambda e: e[0])
    return out


def legend_source_holes(widget):
    """v2.9.303 — la légende décode la COUPE courante, pas le projet.

    « pq la legende nest pas en adequat avec la section » : la légende
    listait les codes de TOUS les trous du projet ; elle ne liste plus
    que ceux des trous réellement projetés dans la coupe affichée.
    """
    cnv = getattr(widget, "canvas", None)
    res = getattr(cnv, "_result", None) if cnv else None
    if res is not None and getattr(res, "holes", None):
        return list(res.holes)
    return list(getattr(widget, "_drillholes", None) or [])


def sync_hole_type_combo(widget):
    """v2.9.306 — le combo du panneau suit le projet chargé/créé.

    « appliqué dans config1 mais pas dans propriétés de la coupe » :
    le combo était construit une fois et ne relisait jamais la config.
    """
    combo = getattr(widget, "_hole_type_combo", None)
    if combo is None:
        return
    md = getattr(widget, "main_dock", None)
    proj = getattr(md, "project", None)
    cfg = {}
    if proj is not None:
        cfg = (getattr(proj, "config", None) or {}).get(
            "display_profiles") or {}
    idx = {"RC": 0, "AUGER": 1, "PUITS": 2}.get(
        str(cfg.get("global") or ""), 0)
    combo.blockSignals(True)
    combo.setCurrentIndex(idx)
    combo.blockSignals(False)
