"""Full CSV editor used by import tabs without cluttering the main dock."""
from __future__ import annotations

import copy
import os
import re

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QColor, QBrush, QKeySequence
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QFileDialog, QHBoxLayout,
    QHeaderView, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from ..core.csv_parser import normalise_editor_rows, write_csv_file
from .styles_qt import (
    BUTTON_PRIMARY, BUTTON_SECONDARY, COLORS, TABLE_STYLE, TOOLTIP_STYLE,
)
from .validation_i18n import validation_english_mode, validation_issue_text, \
    validation_issue_tooltip


class CsvEditorDialog(QDialog):
    """Edit every raw CSV row with validation, undo/redo and safe saves."""

    def __init__(self, import_tab, parent=None):
        super().__init__(parent or import_tab)
        # v2.7.12.8 — infobulles lisibles (dialogue = fenêtre propre, hors
        # du dock) : la règle TOOLTIP_STYLE cascade sur toute l'arborescence.
        self.setStyleSheet(TOOLTIP_STYLE)
        self.import_tab = import_tab
        self.pr = import_tab.parse_result
        self.rows = normalise_editor_rows(
            self.pr.rows, len(self.pr.raw_headers))
        self._initial_rows = copy.deepcopy(self.rows)
        self._undo_stack = []
        self._redo_stack = []
        self._updating = False
        self._dirty = False
        self._locations = []
        self._issues = []
        self._validation_timer = QTimer(self)
        self._validation_timer.setSingleShot(True)
        self._validation_timer.setInterval(250)
        self._validation_timer.timeout.connect(self._validate_now)
        self._build()
        self._fill_table()
        self.set_validation_result(
            getattr(import_tab, "validation_result", None))

    def _build(self):
        file_name = os.path.basename(self.pr.file_path or "CSV")
        self.setWindowTitle(self.tr("Éditeur CSV — {}").format(file_name))
        self.resize(1100, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.format_label = QLabel(
            self.tr("{}  |  Encodage: {}  |  Séparateur: {}  |  "
                    "Décimale: {}  |  Lignes: {}").format(
                file_name, self.pr.encoding, repr(self.pr.separator),
                self.pr.decimal_sep, len(self.rows)))
        self.format_label.setWordWrap(True)
        self.format_label.setStyleSheet(
            f"color:{COLORS['text_medium']}; font-size:9pt;")
        layout.addWidget(self.format_label)

        toolbar = QHBoxLayout()
        self.undo_btn = self._button(self.tr("Annuler"), self._undo, "Ctrl+Z")
        self.redo_btn = self._button(self.tr("Rétablir"), self._redo, "Ctrl+Y")
        self.add_btn = self._button(self.tr("Ajouter une ligne"),
                                    self._add_row)
        self.delete_btn = self._button(self.tr("Supprimer la sélection"),
                                       self._delete_rows)
        for button in (self.undo_btn, self.redo_btn, self.add_btn, self.delete_btn):
            toolbar.addWidget(button)
        toolbar.addSpacing(8)
        self.errors_only = QCheckBox(self.tr("Problèmes uniquement"))
        self.errors_only.stateChanged.connect(self._apply_error_filter)
        toolbar.addWidget(self.errors_only)
        self.previous_error_btn = self._button(
            self.tr("Problème précédent"), self._previous_error)
        self.next_error_btn = self._button(
            self.tr("Problème suivant"), self._next_error)
        toolbar.addWidget(self.previous_error_btn)
        toolbar.addWidget(self.next_error_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Vertical)
        self.table = QTableWidget(0, len(self.pr.raw_headers))
        self.table.setHorizontalHeaderLabels(self.pr.raw_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setDefaultSectionSize(130)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.itemChanged.connect(self._on_item_changed)
        splitter.addWidget(self.table)

        self.error_panel = QWidget()
        error_layout = QVBoxLayout(self.error_panel)
        error_layout.setContentsMargins(0, 0, 0, 0)
        error_layout.addWidget(QLabel(self.tr("Problèmes de validation — cliquez pour atteindre la cellule")))
        self.error_list = QListWidget()
        self.error_list.setMaximumHeight(130)
        self.error_list.itemClicked.connect(self._go_to_error_item)
        error_layout.addWidget(self.error_list)
        splitter.addWidget(self.error_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        layout.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel(self.tr("Aucune modification."))
        self.status_label.setWordWrap(True)
        footer.addWidget(self.status_label, 1)
        self.save_project_btn = QPushButton(self.tr("Enregistrer la copie du projet"))
        self.save_project_btn.setStyleSheet(BUTTON_PRIMARY)
        self.save_project_btn.setShortcut(QKeySequence.Save)
        self.save_project_btn.clicked.connect(self._save_project_copy)
        footer.addWidget(self.save_project_btn)
        self.save_as_btn = QPushButton(self.tr("Enregistrer sous..."))
        self.save_as_btn.setStyleSheet(BUTTON_SECONDARY)
        self.save_as_btn.clicked.connect(self._save_as)
        footer.addWidget(self.save_as_btn)
        close_btn = QPushButton(self.tr("Fermer"))
        close_btn.setStyleSheet(BUTTON_SECONDARY)
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)
        layout.addLayout(footer)
        self._update_actions()

    def _button(self, text, callback, shortcut=None):
        button = QPushButton(text)
        button.setStyleSheet(BUTTON_SECONDARY)
        button.clicked.connect(callback)
        if shortcut:
            button.setShortcut(QKeySequence(shortcut))
        return button

    def _fill_table(self):
        self._updating = True
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        for row_index, values in enumerate(self.rows):
            self.table.insertRow(row_index)
            self._fill_table_row(row_index, values)
        self.table.setUpdatesEnabled(True)
        self._updating = False

    def _fill_table_row(self, row_index, values):
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, value)
            self.table.setItem(row_index, column, item)

    def _normalise_numeric_text(self, column, text):
        """Keep edited numeric cells in the file's original decimal format."""
        value = text.strip()
        if not self.import_tab.is_numeric_column(column):
            return text
        if self.pr.decimal_sep == "," and re.fullmatch(r"-?\d+\.\d+", value):
            return value.replace(".", ",")
        if self.pr.decimal_sep == "." and re.fullmatch(r"-?\d+,\d+", value):
            return value.replace(",", ".")
        return text

    def _on_item_changed(self, item):
        if self._updating:
            return
        row, column = item.row(), item.column()
        old_value = item.data(Qt.UserRole)
        old_value = "" if old_value is None else str(old_value)
        new_value = self._normalise_numeric_text(column, item.text())
        if new_value != item.text():
            self._updating = True
            item.setText(new_value)
            self._updating = False
        if old_value == new_value:
            return
        self._undo_stack.append(("edit", row, column, old_value, new_value))
        self._redo_stack.clear()
        self.rows[row][column] = new_value
        self._updating = True
        item.setData(Qt.UserRole, new_value)
        self._updating = False
        self._mark_dirty()

    def _set_cell(self, row, column, value):
        self.rows[row][column] = value
        item = self.table.item(row, column)
        self._updating = True
        item.setText(value)
        item.setData(Qt.UserRole, value)
        self._updating = False

    def _insert_row(self, row, values):
        values = normalise_editor_rows([values], len(self.pr.raw_headers))[0]
        self.rows.insert(row, values)
        self._updating = True
        self.table.insertRow(row)
        self._fill_table_row(row, values)
        self._updating = False

    def _remove_row(self, row):
        values = self.rows.pop(row)
        self._updating = True
        self.table.removeRow(row)
        self._updating = False
        return values

    def _add_row(self):
        row = self.table.currentRow()
        row = len(self.rows) if row < 0 else row + 1
        values = [""] * len(self.pr.raw_headers)
        self._insert_row(row, values)
        self._undo_stack.append(("add", row, copy.deepcopy(values)))
        self._redo_stack.clear()
        self.table.setCurrentCell(row, 0)
        self.table.editItem(self.table.item(row, 0))
        self._mark_dirty()

    def _delete_rows(self):
        selected = sorted({index.row() for index in self.table.selectedIndexes()})
        if not selected and self.table.currentRow() >= 0:
            selected = [self.table.currentRow()]
        if not selected:
            return
        deleted = [(row, copy.deepcopy(self.rows[row])) for row in selected]
        for row in reversed(selected):
            self._remove_row(row)
        self._undo_stack.append(("delete", deleted))
        self._redo_stack.clear()
        self._mark_dirty()

    def _undo(self):
        if not self._undo_stack:
            return
        command = self._undo_stack.pop()
        kind = command[0]
        if kind == "edit":
            _, row, column, old, new = command
            self._set_cell(row, column, old)
        elif kind == "add":
            _, row, _values = command
            self._remove_row(row)
        elif kind == "delete":
            for row, values in command[1]:
                self._insert_row(row, values)
        self._redo_stack.append(command)
        self._mark_dirty()

    def _redo(self):
        if not self._redo_stack:
            return
        command = self._redo_stack.pop()
        kind = command[0]
        if kind == "edit":
            _, row, column, _old, new = command
            self._set_cell(row, column, new)
        elif kind == "add":
            _, row, values = command
            self._insert_row(row, values)
        elif kind == "delete":
            for row, _values in reversed(command[1]):
                self._remove_row(row)
        self._undo_stack.append(command)
        self._mark_dirty()

    def _mark_dirty(self):
        self._dirty = self.rows != self._initial_rows
        self._sync_parse_result()
        self.status_label.setText(self.tr("Modifications non enregistrées — validation en cours..."))
        self.status_label.setStyleSheet(f"color:{COLORS['warning']};")
        self._validation_timer.start()
        self._update_actions()

    def _sync_parse_result(self):
        self.pr.rows = copy.deepcopy(self.rows)
        self.pr.num_rows = len(self.rows)
        self.pr.preview_rows = copy.deepcopy(self.rows[:10])
        self.format_label.setText(
            self.tr("{}  |  Encodage: {}  |  Séparateur: {}  |  "
                    "Décimale: {}  |  Lignes: {}").format(
                os.path.basename(self.pr.file_path or 'CSV'),
                self.pr.encoding, repr(self.pr.separator),
                self.pr.decimal_sep, len(self.rows)))

    def _validate_now(self, *_args):
        self._sync_parse_result()
        self.import_tab.on_editor_data_changed()

    def set_validation_result(self, validation_result):
        self.validation_result = validation_result
        self._issues = (
            validation_result.get_issues(self.pr) if validation_result else [])
        self._locations = []
        for issue_index, issue in enumerate(self._issues):
            payload = issue.to_dict()
            locations = payload.get("locations") or [{
                "row": payload.get("row"),
                "column": payload.get("column"),
            }]
            for location in locations:
                self._locations.append({
                    **payload,
                    "row": location.get("row"),
                    "column": location.get("column"),
                    "issue_index": issue_index,
                })
        self._paint_errors()
        self.error_list.clear()
        icons = {"error": "✗", "warning": "⚠", "info": "ℹ"}
        # v2.9.258 — en anglais la liste n'expose plus les messages
        # français de core.validation : elle affiche le libellé court du
        # code (ValidationMessages) et la ligne CSV concernée.
        en_mode = validation_english_mode()
        for issue in self._issues:
            payload = issue.to_dict()
            prefix = icons.get(payload["severity"], "•")
            text = f"{prefix} {validation_issue_text(payload)}"
            if (not en_mode and payload.get("suggestion")):
                text += f" — {payload['suggestion']}"
            locations = payload.get("locations") or [{
                "row": payload.get("row"),
                "column": payload.get("column"),
            }]
            primary = locations[0] if locations else {"row": None, "column": None}
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, (
                primary.get("row"), primary.get("column")))
            self.error_list.addItem(item)
        self.error_panel.setVisible(bool(self._issues))
        error_count = sum(issue.severity == "error" for issue in self._issues)
        warning_count = sum(issue.severity == "warning" for issue in self._issues)
        if error_count:
            self.status_label.setText(
                self.tr("{} erreur(s), {} avertissement(s) — corrigez "
                        "les cellules rouges puis enregistrez.").format(
                    error_count, warning_count))
            self.status_label.setStyleSheet(f"color:{COLORS['danger']};")
        elif warning_count:
            self.status_label.setText(
                self.tr("Validation sans erreur — {} avertissement(s).").format(warning_count))
            self.status_label.setStyleSheet(f"color:{COLORS['warning']};")
        elif self._dirty:
            self.status_label.setText(self.tr("Validation OK — modifications non enregistrées."))
            self.status_label.setStyleSheet(f"color:{COLORS['warning']};")
        else:
            self.status_label.setText(self.tr("Validation OK — copie du projet à jour."))
            self.status_label.setStyleSheet(f"color:{COLORS['success']};")
        self._apply_error_filter()
        self._update_actions()

    def _paint_errors(self):
        white = QBrush(QColor("#FFFFFF"))
        brushes = {
            "info": QBrush(QColor("#D6EAF8")),
            "warning": QBrush(QColor("#FDEBD0")),
            "error": QBrush(QColor("#F5B7B1")),
        }
        priorities = {"info": 0, "warning": 1, "error": 2}
        for row in range(self.table.rowCount()):
            self.table.setVerticalHeaderItem(
                row, QTableWidgetItem(f"{row + 2} ✓"))
            for column in range(self.table.columnCount()):
                self.table.item(row, column).setBackground(white)
                self.table.item(row, column).setToolTip(self.tr(""))
        ordered = sorted(
            self._locations,
            key=lambda location: priorities.get(location["severity"], 0))
        row_severity = {}
        for location in ordered:
            row, column = location["row"], location["column"]
            severity = location.get("severity", "error")
            if row is None or not (0 <= row < self.table.rowCount()):
                continue
            row_severity[row] = severity
            # v2.9.258 — infobulle localisée : en anglais, libellé court
            # + ligne CSV ; en français, message complet + suggestion.
            tooltip = validation_issue_tooltip(location)
            if column is not None and 0 <= column < self.table.columnCount():
                self.table.item(row, column).setBackground(brushes[severity])
                self.table.item(row, column).setToolTip(tooltip)
            else:
                for col in range(self.table.columnCount()):
                    self.table.item(row, col).setBackground(brushes[severity])
                    self.table.item(row, col).setToolTip(tooltip)
        icons = {"error": "✗", "warning": "⚠", "info": "ℹ"}
        header_colours = {
            "error": ("#C0392B", "#FFFFFF"),
            "warning": ("#D68910", "#FFFFFF"),
            "info": ("#2471A3", "#FFFFFF"),
        }
        labels = {
            "error": self.tr("Erreur"), "warning": self.tr("Avertissement"),
            "info": self.tr("Information"),
        }
        for row, severity in row_severity.items():
            header = QTableWidgetItem(f"{row + 2}  {icons[severity]}")
            header.setToolTip(
                self.tr("Ligne CSV {} — {}").format(
                    row + 2, labels.get(severity, severity)))
            background, foreground = header_colours[severity]
            header.setBackground(QBrush(QColor(background)))
            header.setForeground(QBrush(QColor(foreground)))
            self.table.setVerticalHeaderItem(row, header)

    def _error_rows(self):
        return {
            location["row"] for location in self._locations
            if location["row"] is not None
        }

    def _apply_error_filter(self, *_args):
        only_errors = self.errors_only.isChecked()
        error_rows = self._error_rows()
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, only_errors and row not in error_rows)

    def _go_to_error_item(self, item):
        row, column = item.data(Qt.UserRole)
        if row is None or not (0 <= row < self.table.rowCount()):
            return
        self.table.setRowHidden(row, False)
        column = column if column is not None else 0
        self.table.setCurrentCell(row, column)
        self.table.scrollToItem(self.table.item(row, column))
        self.table.setFocus()

    def focus_location(self, row, column=None):
        """Focus a cell from an outside caller (v2.7.6 panneau groupé)."""
        if row is None or not (0 <= row < self.table.rowCount()):
            self.raise_()
            self.activateWindow()
            return
        column = column if column is not None and 0 <= column \
            < self.table.columnCount() else 0
        self.table.setRowHidden(row, False)
        self.table.setCurrentCell(row, column)
        item = self.table.item(row, column)
        if item is not None:
            self.table.scrollToItem(item)
        self.table.setFocus()
        self.raise_()
        self.activateWindow()

    def _current_error_index(self):
        if not self.error_list.count():
            return -1
        selected = self.error_list.currentRow()
        if selected >= 0:
            return selected
        row = self.table.currentRow()
        if row < 0:
            return -1
        for index in range(self.error_list.count()):
            issue_row, _column = self.error_list.item(index).data(Qt.UserRole)
            if issue_row is not None and issue_row >= row:
                return index
        return 0

    def _next_error(self):
        count = self.error_list.count()
        if not count:
            return
        index = (self._current_error_index() + 1) % count
        self._go_to_error_item(self.error_list.item(index))
        self.error_list.setCurrentRow(index)

    def _previous_error(self):
        count = self.error_list.count()
        if not count:
            return
        current = self._current_error_index()
        index = (current - 1) % count if current >= 0 else count - 1
        self._go_to_error_item(self.error_list.item(index))
        self.error_list.setCurrentRow(index)

    def _save(self, path, project_copy):
        self._validate_now()
        try:
            saved = write_csv_file(
                path, self.pr.raw_headers, self.rows,
                encoding=self.pr.encoding,
                separator=self.pr.separator,
                line_ending=self.pr.line_ending,
                quotechar=self.pr.quotechar,
                make_backup=True,
            )
        except (OSError, UnicodeError, ValueError) as error:
            QMessageBox.critical(
                self, self.tr("Enregistrement impossible"), str(error))
            return False
        if project_copy:
            self.pr.file_path = saved
            self._initial_rows = copy.deepcopy(self.rows)
            self._dirty = False
            self._undo_stack.clear()
            self._redo_stack.clear()
            self.import_tab.on_project_copy_saved(saved)
            self.status_label.setText(self.tr(
                "Copie du projet enregistrée : {}").format(saved))
            self.status_label.setStyleSheet(f"color:{COLORS['success']};")
        else:
            self.status_label.setText(self.tr(
                "Export enregistre : {} — la copie du projet reste "
                "modifiée.").format(saved))
            self.status_label.setStyleSheet(f"color:{COLORS['accent']};")
        self._update_actions()
        return True

    def _save_project_copy(self, *_args):
        path = self.import_tab.get_project_copy_path()
        if not path:
            QMessageBox.warning(
                self, self.tr("Copie du projet indisponible"),
                self.tr("Aucun projet actif ne contient ce fichier."))
            return False
        return self._save(path, project_copy=True)

    def _save_as(self, *_args):
        base = self.import_tab.get_project_copy_path() or self.pr.file_path
        suggested = os.path.splitext(
            base or self.tr("données.csv"))[0] + self.tr("_corrigé.csv")
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Enregistrer le CSV corrigé"), suggested,
            self.tr("CSV (*.csv);;Texte (*.txt);;Tous fichiers (*)"))
        if path:
            self._save(path, project_copy=False)

    def _restore_initial(self):
        self.rows = copy.deepcopy(self._initial_rows)
        self._fill_table()
        self._dirty = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._sync_parse_result()
        self.import_tab.on_editor_data_changed()

    def _update_actions(self):
        self.undo_btn.setEnabled(bool(self._undo_stack))
        self.redo_btn.setEnabled(bool(self._redo_stack))
        has_errors = bool(self._locations)
        self.previous_error_btn.setEnabled(has_errors)
        self.next_error_btn.setEnabled(has_errors)
        self.save_project_btn.setEnabled(
            bool(self.import_tab.get_project_copy_path()) and self._dirty)

    def closeEvent(self, event):
        if not self._dirty:
            event.accept()
            return
        answer = QMessageBox.question(
            self, self.tr("Modifications non enregistrées"),
            self.tr("Enregistrer les modifications dans la copie du projet avant de fermer ?"),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save)
        if answer == QMessageBox.Save:
            if self._save_project_copy():
                event.accept()
            else:
                event.ignore()
        elif answer == QMessageBox.Discard:
            self._restore_initial()
            event.accept()
        else:
            event.ignore()
