"""
DrillMaster — Étape 4 : coupes 2D
"""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QMessageBox,
)
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsPointXY, QgsWkbTypes
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapCanvas

from ..core.section import SectionLine
from .styles_qt import COLORS, BUTTON_PRIMARY


class SectionMapTool(QgsMapTool):
    """v2.9.25 — tracé annulable : Escape / clic droit = abandon."""
    line_created = pyqtSignal(float, float, float, float)
    draw_cancelled = pyqtSignal()

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self._points = []
        self._rubber = None
        self.setCursor(Qt.CursorShape.CrossCursor)

    def canvasPressEvent(self, event):
        # Clic droit = annuler le tracé en cours
        if event.button() == Qt.MouseButton.RightButton:
            self._cancel()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pt = self.toMapCoordinates(event.pos())
        self._points.append(QgsPointXY(pt.x(), pt.y()))
        if len(self._points) == 1:
            if self._rubber:
                self._rubber.reset()
            else:
                self._rubber = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
                self._rubber.setColor(QColor("#C0392B"))
                self._rubber.setWidth(2)
                self._rubber.setLineStyle(Qt.PenStyle.DashLine)
            self._rubber.addPoint(pt)
        elif len(self._points) == 2:
            p1 = self._points[0]
            if self._rubber:
                self._rubber.addPoint(pt)
            self.line_created.emit(p1.x(), p1.y(), pt.x(), pt.y())
            self._points.clear()
            self.canvas.unsetMapTool(self)

    def canvasMoveEvent(self, event):
        if len(self._points) == 1 and self._rubber:
            pt = self.toMapCoordinates(event.pos())
            self._rubber.reset()
            self._rubber.addPoint(self._points[0])
            self._rubber.addPoint(pt)

    def keyPressEvent(self, event):
        # Escape = annuler
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()
            event.accept()
            return
        super().keyPressEvent(event)

    def _cancel(self):
        if self._rubber:
            self._rubber.reset()
            self._rubber = None
        self._points.clear()
        self.draw_cancelled.emit()
        try:
            self.canvas.unsetMapTool(self)
        except Exception as _exc:
            from ..core.diagnostics import log_swallowed
            log_swallowed("step4_section : _cancel", _exc)
            # canvas déjà détruit / outil déjà retiré — sans effet
            pass

    def deactivate(self):
        if self._rubber:
            self._rubber.reset()
            self._rubber = None
        self._points.clear()
        super().deactivate()


class Step4Section(QWidget):
    validity_changed = pyqtSignal(bool)

    def __init__(self, main_dock, parent=None):
        super().__init__(parent)
        self.main_dock = main_dock
        self._tool = None
        self._line = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel(self.tr("Gestion des coupes"))
        title.setObjectName("label_title")
        layout.addWidget(title)

        desc = QLabel(self.tr(
            "Créez, générez et organisez les coupes du projet."))
        desc.setObjectName("label_subtitle")
        layout.addWidget(desc)

        dg = QGroupBox(self.tr("Nouvelle coupe"))
        dl = QVBoxLayout(dg)
        dl.setContentsMargins(6, 6, 6, 6)
        self.draw_btn = QPushButton(
            self.tr("Tracer une ligne sur la carte"))
        self.draw_btn.setStyleSheet(BUTTON_PRIMARY)
        self.draw_btn.setMinimumHeight(28)
        self.draw_btn.setToolTip(
            self.tr("2 clics gauche sur la carte. Escape ou clic droit = annuler."))
        self.draw_btn.clicked.connect(self._start)
        dl.addWidget(self.draw_btn)
        # v2.9.25 — annuler le tracé en cours / la dernière ligne
        from qgis.PyQt.QtWidgets import QHBoxLayout
        row = QHBoxLayout()
        self.cancel_draw_btn = QPushButton(self.tr("Annuler le tracé"))
        self.cancel_draw_btn.setEnabled(False)
        self.cancel_draw_btn.setToolTip(self.tr(
            "Abandonner le tracé en cours (Escape / clic droit)"))
        self.cancel_draw_btn.clicked.connect(self._cancel_draw)
        row.addWidget(self.cancel_draw_btn)
        self.undo_line_btn = QPushButton(
            self.tr("Annuler la dernière ligne"))
        self.undo_line_btn.setEnabled(False)
        self.undo_line_btn.setToolTip(self.tr(
            "Supprimer la dernière ligne de coupe créée (Ctrl+Z)"))
        self.undo_line_btn.clicked.connect(self._undo_last_line)
        row.addWidget(self.undo_line_btn)
        dl.addLayout(row)
        self.line_status = QLabel(self.tr("Aucune ligne tracée."))
        self.line_status.setObjectName("label_hint")
        dl.addWidget(self.line_status)
        layout.addWidget(dg)

        gg = QGroupBox(self.tr("Génération"))
        gl = QVBoxLayout(gg)
        gl.setContentsMargins(6, 6, 6, 6)
        self.gen_btn = QPushButton(self.tr("Générer et afficher"))
        # v2.7.12.13 — REVUE ÉCRAN : blanc sur #ABEBC6 ≈ illisible
        # (contraste ~1,6) — l'état « désactivé » se lit avec une encre
        # vert-ardoise. (Pas de commentaire « # » DANS le CSS : le CSS ne
        # connaît que /* … */, le « # » cassait la règle :disabled.)
        self.gen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']}; color: white; border: none;
                border-radius: 3px; padding: 4px 12px; font-size: 9pt; font-weight: bold;
                min-height: 24px; outline: none;
            }}
            QPushButton:hover {{ background-color: #229954; }}
            QPushButton:focus {{ outline: none; border: none;
                background-color: {COLORS['success']}; }}
            QPushButton:pressed {{ outline: none; background-color: #1E8449; border: none; }}
            QPushButton:disabled {{ background-color: #ABEBC6; color: #46685A; }}
        """)
        self.gen_btn.setMinimumHeight(28)
        self.gen_btn.setEnabled(False)
        self.gen_btn.setToolTip(self.tr("Générer la coupe 2D"))
        self.gen_btn.clicked.connect(self._generate)
        gl.addWidget(self.gen_btn)
        layout.addWidget(gg)

        # v2.7.12.13 — REVUE ÉCRAN (étape 4) : le stretch poussait
        # l'historique en bas et laissait une ZONE MORTE au milieu de
        # l'étape (le grand vide entre « Génération » et « Historique
        # des coupes »). L'historique occupe désormais TOUT l'espace
        # restant : sa table (plus de hauteur max) le remplit, et avec
        # beaucoup de coupes elle défile à l'intérieur.
        self.history_host = QWidget()
        self.history_layout = QVBoxLayout(self.history_host)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.history_host, 1)

        note = QLabel(self.tr(
            "La vue Coupe 2D s’ouvre automatiquement."))
        note.setObjectName("label_hint")
        layout.addWidget(note)

    def attach_history_widget(self, widget):
        """Place the single shared history under Assistant step 4."""
        widget.setParent(self.history_host)
        widget.setVisible(True)
        self.history_layout.addWidget(widget)

    def _start(self, *_args):
        canvas = self.main_dock.get_map_canvas()
        if not canvas:
            return
        # Retirer un éventuel outil précédent
        if self._tool is not None:
            try:
                canvas.unsetMapTool(self._tool)
            except Exception as _exc:
                from ..core.diagnostics import log_swallowed
                log_swallowed("step4_section : _start", _exc)
                # outil déjà retiré / canvas fermé — sans effet
                pass
        self._tool = SectionMapTool(canvas)
        self._tool.line_created.connect(self._on_line)
        self._tool.draw_cancelled.connect(self._on_draw_cancelled)
        canvas.setMapTool(self._tool)
        self.cancel_draw_btn.setEnabled(True)
        self.line_status.setText(
            self.tr("Cliquez 2 points…  (Escape / clic droit = annuler)"))
        self.line_status.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 9pt;")

    def _on_draw_cancelled(self):
        """v2.9.25 — Escape / clic droit / bouton Annuler le tracé."""
        self.cancel_draw_btn.setEnabled(False)
        self._tool = None
        if self._line is None:
            self.line_status.setText(
                self.tr("Tracé annulé. Aucune ligne."))
            self.line_status.setStyleSheet(
                f"color: {COLORS['text_light']}; font-size: 9pt;")
        else:
            name = self._line.name or self.tr("Coupe")
            self.line_status.setText(self.tr(
                "Tracé annulé. Ligne active : {}.").format(name))
            self.line_status.setStyleSheet(
                f"color: {COLORS['accent']}; font-size: 9pt;")

    def _cancel_draw(self, *_args):
        if self._tool is not None and hasattr(self._tool, "_cancel"):
            self._tool._cancel()
        else:
            self._on_draw_cancelled()

    def _undo_last_line(self, *_args):
        """v2.9.25 — annuler la dernière ligne de coupe créée."""
        line = self._line
        if line is None or not getattr(line, "section_id", None):
            # Essayer la dernière de l'historique section widget
            sw = self.main_dock.get_section_widget()
            if sw is not None and sw.section_table.rowCount() > 0:
                sw.section_table.selectRow(sw.section_table.rowCount() - 1)
                sw._delete_current_section()
            self.undo_line_btn.setEnabled(False)
            self.gen_btn.setEnabled(False)
            self._line = None
            self.line_status.setText(
                self.tr("Dernière ligne annulée."))
            self.line_status.setStyleSheet(
                f"color: {COLORS['text_light']}; font-size: 9pt;")
            self.validity_changed.emit(False)
            return
        section_id = line.section_id
        section_name = line.name or ""
        sw = self.main_dock.get_section_widget()
        if sw is not None:
            row = sw._history_row_for_id(section_id)
            if row >= 0:
                sw.section_table.selectRow(row)
                sw._delete_current_section()
            else:
                # fallback project + layer
                project = self.main_dock.project
                if project:
                    project.delete_section(section_id)
                self.main_dock.section_widget.section_generated.emit(
                    f"DELETE:{section_name}")
        self._line = None
        self.gen_btn.setEnabled(False)
        self.undo_line_btn.setEnabled(False)
        self.line_status.setText(self.tr(
            "Ligne « {} » annulée (supprimée).").format(section_name))
        self.line_status.setStyleSheet(
            f"color: {COLORS['text_light']}; font-size: 9pt;")
        self.validity_changed.emit(False)

    def _on_line(self, x1, y1, x2, y2):
        self.cancel_draw_btn.setEnabled(False)
        self._tool = None
        # v2.7.8 — le buffer se CHOISIT au tracé.
        # v2.9.25 — Annuler le dialogue = ANNULER TOUTE la ligne
        # (plus de ligne fantôme / couche orpheline).
        section_widget = self.main_dock.get_section_widget()
        default_buffer = (
            section_widget.buffer_spin.value()
            if section_widget is not None else 50.0)
        from qgis.PyQt.QtWidgets import QInputDialog
        buffer_value, accepted = QInputDialog.getDouble(
            self, self.tr("Buffer de la coupe"),
            self.tr("Corridor de sélection autour de la ligne "
                    "(dans les unités du SCR) :\n"
                    "(Annuler = abandonner ce tracé)"),
            default_buffer, 0.0, 1000000000.0, 1)
        if not accepted:
            self.line_status.setText(
                self.tr("Tracé annulé (buffer refusé). Aucune ligne créée."))
            self.line_status.setStyleSheet(
                f"color: {COLORS['text_light']}; font-size: 9pt;")
            return
        self._line = SectionLine(x1, y1, x2, y2)
        self._line.buffer = buffer_value
        if section_widget is not None:
            section_widget.buffer_spin.setValue(buffer_value)
        # Auto-name: Section 001, 002, etc.
        section_name = ""
        section_id = 0
        if self.main_dock.project:
            section_name = self.main_dock.project.get_next_section_display_name()
            section_id = self.main_dock.project.save_section(
                x1, y1, x2, y2, section_name,
                self._line.direction_label,
                self._line.azimuth,
                self._line.length,
                buffer_value
            )
        self._line.name = section_name
        self._line.section_id = section_id
        self.line_status.setText(
            f"{section_name}  |  {self._line.summary}  |  Buffer ±{buffer_value:g}")
        self.line_status.setStyleSheet(
            f"color: {COLORS['success']}; font-size: 9pt; font-weight: bold;")
        self.gen_btn.setEnabled(True)
        self.undo_line_btn.setEnabled(True)
        self.main_dock.create_section_line_layer(
            (x1, y1), (x2, y2), name=section_name)

    def keyPressEvent(self, event):
        # v2.9.25 — Ctrl+Z annule la dernière ligne de coupe créée
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier
                and event.key() == Qt.Key.Key_Z):
            if getattr(self, "undo_line_btn", None) is not None \
                    and self.undo_line_btn.isEnabled():
                self._undo_last_line()
                event.accept()
                return
        super().keyPressEvent(event)

    def _generate(self, *_args):
        if not self._line:
            return
        dhs = self.main_dock.get_drillholes()
        if not dhs:
            return
        sw = self.main_dock.get_section_widget()
        sw.set_litho_styles(self.main_dock.project.get_litho_styles() if self.main_dock.project else {})
        # v2.7.10.34 — plus jamais un échec SILENCIEUX : si la création
        # ou la (re)génération tombe en exception, la cause est posée dans
        # le statut (et remontée dans la console QGIS), au lieu du
        # « ça ne passe pas » constaté à l'écran sans aucun indice.
        try:
            if self._line.name and self._line.section_id:
                sw.add_section(dhs, self._line, self._line.section_id, self._line.name)
            else:
                sw.update_section(dhs, self._line)
        except Exception as error:  # noqa: BLE001 — surface, jamais avaler
            from ..core.diagnostics import log_swallowed
            log_swallowed("Étape 4 : génération de la coupe", error)
            self.line_status.setText(self.tr(
                "Échec de génération : {} — voir la console Python de "
                "QGIS.").format(repr(error)))
            self.line_status.setStyleSheet(
                f"color: {COLORS['danger']}; font-size: 9pt; font-weight: bold;")
            import traceback
            traceback.print_exc()
            return
        self.main_dock.show_section_tab()
        name = self._line.name or self.tr("Coupe")
        self.line_status.setText(self.tr("{} générée. Onglet « Coupe 2D » affiché.").format(name))
        self.validity_changed.emit(True)

    def reset(self):
        # v2.7.10.34 — ne touche pas l'historique : il vit en permanence
        # dans l'étape 4 depuis la v2.7.10.34 (bug « historique absent »
        # corrigé à sa source, côté SectionWidget).
        self._line = None
        self.gen_btn.setEnabled(False)
        if hasattr(self, "undo_line_btn"):
            self.undo_line_btn.setEnabled(False)
        if hasattr(self, "cancel_draw_btn"):
            self.cancel_draw_btn.setEnabled(False)
        self.line_status.setText(
                self.tr("Aucune ligne tracée."))
        self.line_status.setObjectName("label_hint")
        self.line_status.setStyleSheet(
            f"color: {COLORS['text_light']}; font-size: 9pt;")
        self.validity_changed.emit(False)
