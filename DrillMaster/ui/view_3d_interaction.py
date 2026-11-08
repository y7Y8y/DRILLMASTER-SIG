"""DrillMaster — Interaction 3D (volet 1, tranche 3, v2.9.148).

Couche INTERACTION extraite de ``ui/view_3d.py`` (SPEC) : traduit les
événements souris/molette en actions caméra (orbite, pan, zoom),
survol (hit-test via les segments du mesh) et sélection
``(hole_id, from, to)`` via l'espace de travail partagé.

Le canvas délègue chaque handler à une ligne.
"""

from __future__ import annotations

import math

from qgis.PyQt.QtCore import QPoint, QPointF, Qt
from qgis.PyQt.QtWidgets import QWidget


def mouse_press(canvas, event):
    canvas._mouse_press_pos = event.pos()
    canvas._mouse_button = event.button()
    canvas._is_dragging = False

    if event.button() == Qt.MouseButton.LeftButton:
        for r, code, _txt in canvas._legend_rects:
            if r.contains(QPointF(event.pos())):
                new_code = None if (canvas._highlight_code and canvas._highlight_code.upper() == code.upper()) else code
                canvas.workspace_state.set("highlight_code", new_code)
                event.accept()
                return

    QWidget.mousePressEvent(canvas, event)


def mouse_move(canvas, event):
    if canvas._mouse_press_pos and canvas._mouse_button:
        delta = event.pos() - canvas._mouse_press_pos
        if delta.manhattanLength() > 3:
            canvas._is_dragging = True

        if canvas._is_dragging:
            if canvas._mouse_button == Qt.MouseButton.LeftButton:
                canvas.yaw_deg = (canvas.yaw_deg + delta.x() * 0.5) % 360.0
                canvas.pitch_deg = max(-89.0, min(89.0, canvas.pitch_deg - delta.y() * 0.5))
                # v2.9.141 — l'orbite manuelle invalide le preset affiché
                canvas._clear_cam_preset()
            elif canvas._mouse_button in (Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
                canvas.pan_x += delta.x()
                canvas.pan_y += delta.y()
            canvas._mouse_press_pos = event.pos()
            canvas.update()
            return

    if not canvas._is_dragging:
        # v2.9.141 — survol de la légende : libellé complet (le nom est
        # tronqué à l'écran), prioritaire sur le survol des forages.
        tip = None
        for r, _code, hover_txt in canvas._legend_rects:
            if r.contains(QPointF(event.pos())):
                tip = hover_txt
                break
        if tip is None:
            tip = canvas._find_hover_tooltip(event.pos())
        # Ne repeindre QUE si le contenu change (plus de repaint complet
        # à chaque pixel survolé — gros gain de fluidité).
        changed = (tip != canvas._hover_text)
        canvas._hover_text = tip
        canvas._hover_pos = event.pos() if tip else None
        if changed:
            # Signal thottlé : la barre de statut n'est pas réécrite à
            # chaque mouvement de souris, seulement quand le survol change.
            canvas.hover_changed.emit(tip or "")
            canvas.update()

    QWidget.mouseMoveEvent(canvas, event)


def mouse_release(canvas, event):
    was_dragging = canvas._is_dragging
    if not canvas._is_dragging and event.button() == Qt.MouseButton.LeftButton:
        canvas._handle_click_selection(event.pos())
    canvas._mouse_press_pos = None
    canvas._mouse_button = None
    canvas._is_dragging = False
    # v2.9.175 — fin d'orbite : repeint en DETAIL COMPLET (le LOD de
    # mouvement a sauté motifs, légende, étiquettes — ils reviennent).
    if was_dragging:
        canvas.update()
    QWidget.mouseReleaseEvent(canvas, event)


def wheel(canvas, event):
    delta = event.angleDelta().y()
    factor = 1.15 if delta > 0 else 0.85
    canvas.zoom = max(0.05, min(50.0, canvas.zoom * factor))
    # v2.9.245 — la molette est un MOUVEMENT : drapeau LOD + minuterie
    # de fin AVANT le repaint (retour écran : « au zoom et dézoom de 3D
    # c'est grave lent » — chaque cran rendait la scène en détail
    # complet, l'orbite étant seule à bénéficier du LOD v2.9.175).  La
    # frame de défilement est allégée ; le détail complet revient
    # ~150 ms après le DERNIER cran (_end_wheel_motion).
    canvas._begin_wheel_motion()
    canvas.update()
    event.accept()


def _ref_point(canvas, pos):
    """v2.9.318 — souris → espace du pixmap caché (§2.1) + facteur s."""
    cam = getattr(canvas, "camera", None)
    if cam is None:  # harnais sans caméra : espace identité
        return float(pos.x()), float(pos.y()), 1.0
    return cam.screen_to_ref(
        pos.x(), pos.y(), canvas.width(), canvas.height(),
        getattr(canvas, "_render_zoom", 1.0),
        getattr(canvas, "_render_pan_x", 0.0),
        getattr(canvas, "_render_pan_y", 0.0))


def find_hover_tooltip(canvas, pos: QPoint):
    rx, ry, s_f = _ref_point(canvas, pos)
    click_pt = QPointF(rx, ry)
    reach = max(8.0, canvas.stroke_width * 0.8) / (s_f or 1.0)
    best_tip = None
    best_eff = None
    # v2.9.183 — HYSTÉRÉSIS : l'infobulle AFFICHÉE garde un léger
    # avantage (distance ×0.75).  En domaines simultanés, les tubes
    # principal/secondaires sont proches : sans cela, l'infobulle
    # clignotait d'un domaine à l'autre au moindre micro-mouvement
    # (retour écran : « au survol 3D ça bug beaucoup »).
    current = getattr(canvas, "_hover_text", None)
    for p0, p1, _, _, _, _, tip in canvas._hit_segments:
        line_vec = p1 - p0
        len_sq = line_vec.x() ** 2 + line_vec.y() ** 2
        if len_sq > 0:
            t = max(0.0, min(1.0, ((click_pt.x() - p0.x()) * line_vec.x() + (click_pt.y() - p0.y()) * line_vec.y()) / len_sq))
            proj = p0 + t * line_vec
            dist = math.hypot(click_pt.x() - proj.x(), click_pt.y() - proj.y())
            eff = dist * (0.75 if tip == current else 1.0)
            if eff <= reach and (best_eff is None or eff < best_eff):
                best_eff = eff
                best_tip = tip
    return best_tip


def handle_click_selection(canvas, pos: QPoint):
    rx, ry, s_f = _ref_point(canvas, pos)
    click_pt = QPointF(rx, ry)

    # v2.9.263 — badge Imagerie 3D : un clic OUVRE LA PHOTO en grand
    # (plus de ruban texturé).  Prioritaire sur la sélection d'intervalle.
    # Le badge le PLUS PROCHE gagne (deux intervalles d'un même trou
    # peuvent être proches à l'écran ; choisir le premier écraserait
    # l'intervalle voulu).
    best_badge = None
    best_dist = None
    for center, radius, hole_id, from_m, to_m, record in (
            getattr(canvas, "_imagery_badge_hits", None) or []):
        dist = math.hypot(click_pt.x() - center.x(),
                          click_pt.y() - center.y())
        if dist <= radius / (s_f or 1.0) and (
                best_dist is None or dist < best_dist):
            best_dist = dist
            best_badge = (hole_id, from_m, to_m, record)
    if best_badge is not None:
        hole_id, from_m, to_m, record = best_badge
        from .view_3d_imagery_viewer import show_imagery_photo
        # On passe l'enregistrement EXACT du badge cliqué : si deux lignes
        # du même forage ont les mêmes bornes (données réelles), le
        # visualiseur rappelle le bon enregistrement au lieu du premier
        # trouvé par intervalle.  Il re-valide ensuite ses bornes.
        show_imagery_photo(
            canvas, hole_id, from_m, to_m, record=record)
        return

    min_dist = max(8.0, canvas.stroke_width * 0.8) / (s_f or 1.0)
    closest = None
    for p0, p1, _, hole_id, from_m, to_m, _ in canvas._hit_segments:
        line_vec = p1 - p0
        len_sq = line_vec.x() ** 2 + line_vec.y() ** 2
        if len_sq > 0:
            t = max(0.0, min(1.0, ((click_pt.x() - p0.x()) * line_vec.x() + (click_pt.y() - p0.y()) * line_vec.y()) / len_sq))
            proj = p0 + t * line_vec
            dist = math.hypot(click_pt.x() - proj.x(), click_pt.y() - proj.y())
            if dist < min_dist:
                min_dist = dist
                closest = (hole_id, from_m, to_m)

    if closest:
        hole_id, from_m, to_m = closest
        # Toggle off si on reclique sur l'intervalle déjà sélectionné
        if (canvas._selected_hole_id == hole_id
                and canvas._selected_from_m is not None and abs(canvas._selected_from_m - from_m) < 1e-4
                and canvas._selected_to_m is not None and abs(canvas._selected_to_m - to_m) < 1e-4):
            canvas.workspace_state.clear_selection()
            canvas._selected_hole_id = None
            canvas._selected_from_m = None
            canvas._selected_to_m = None
            canvas.update()
            return

        canvas.workspace_state.select_interval(
            hole_id=hole_id,
            from_m=from_m,
            to_m=to_m,
            # v2.9.260 — MESURE PONCTUELLE : un clic 3D sur une structure
            # (from == to) doit porter le domaine `structure`, pas
            # ``geo_domain`` — sinon la coupe 2D reçoit une sélection
            # « litho » de longueur nulle et le contour de sélection peut
            # cibler le mauvais domaine en multi-domaines.
            domain=("structure" if abs(float(to_m) - float(from_m)) < 1e-4
                    else canvas.geo_domain),
            source="view_3d",
        )
        canvas.interval_clicked.emit(hole_id, from_m, to_m)
    else:
        # Clic dans le vide : désélectionne proprement
        if canvas._selected_hole_id or canvas._selected_from_m is not None:
            canvas.workspace_state.clear_selection()
            canvas._selected_hole_id = None
            canvas._selected_from_m = None
            canvas._selected_to_m = None
            canvas.update()
