"""
DrillMaster — Fabriques de lignes d'option (Lot DA-1, v2.9.396)
================================================================
Tue le boilerplate répété ~8 lignes par option dans les panneaux
(55× ``setStyleSheet(INPUT_STYLE)`` dans section_dock.py seul).

Chaque fabrique applique systématiquement : style d'entrée unique
(``INPUT_STYLE``), connexion du signal de changement, suffixe/prefixe.
Les groupes deviennent déclaratifs : 1 ligne par option.
"""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLineEdit, QSpinBox,
    QWidget)

from ..styles_qt import INPUT_STYLE


def make_spin(parent=None, *, lo=0, hi=100, value=0, decimals=0,
              step=None, prefix="", suffix="", on_change=None):
    """Spinbox normalisée (QSpinBox, ou QDoubleSpinBox si ``decimals``>0)."""
    if decimals > 0:
        w = QDoubleSpinBox(parent)
        w.setDecimals(decimals)
        if step is not None:
            w.setSingleStep(step)
    else:
        w = QSpinBox(parent)
        if step is not None:
            w.setSingleStep(step)
    w.setRange(lo, hi)
    w.setValue(value)
    if prefix:
        w.setPrefix(prefix)
    if suffix:
        w.setSuffix(suffix)
    w.setStyleSheet(INPUT_STYLE)
    if on_change is not None:
        w.valueChanged.connect(on_change)
    return w


def make_combo(parent, items, *, on_change=None, current=None):
    """Combo normalisée ; ``items`` = [(libellé, data)], ``current`` = data."""
    w = QComboBox(parent)
    for label, data in items:
        w.addItem(label, data)
    if current is not None:
        idx = w.findData(current)
        if idx >= 0:
            w.setCurrentIndex(idx)
    w.setStyleSheet(INPUT_STYLE)
    if on_change is not None:
        w.currentIndexChanged.connect(on_change)
    return w


def make_check(parent, text, *, checked=False, on_change=None):
    """Case à cocher normalisée."""
    w = QCheckBox(text, parent)
    w.setChecked(checked)
    if on_change is not None:
        w.stateChanged.connect(on_change)
    return w


def make_line_edit(parent, *, max_length=None, placeholder="", text="",
                   on_edit_finished=None, on_text_edited=None):
    """Champ texte normalisé (cartouches, commentaires)."""
    w = QLineEdit(text, parent)
    if max_length is not None:
        w.setMaxLength(max_length)
    if placeholder:
        w.setPlaceholderText(placeholder)
    w.setStyleSheet(INPUT_STYLE)
    if on_edit_finished is not None:
        w.editingFinished.connect(on_edit_finished)
    if on_text_edited is not None:
        w.textEdited.connect(on_text_edited)
    return w


def make_xy_pair(parent, *, lo=-100, hi=100, value=0.0, decimals=1,
                 x_prefix="X ", y_prefix="Y ", suffix=" px", on_change=None):
    """Paire X/Y côte à côte (décalages, offsets) — pattern récurrent.

    Retourne ``(widget, spin_x, spin_y)``.
    """
    widget = QWidget(parent)
    row = QHBoxLayout(widget)
    row.setContentsMargins(0, 0, 0, 0)
    x_spin = make_spin(widget, lo=lo, hi=hi, value=value, decimals=decimals,
                       prefix=x_prefix, suffix=suffix, on_change=on_change)
    y_spin = make_spin(widget, lo=lo, hi=hi, value=value, decimals=decimals,
                       prefix=y_prefix, suffix=suffix, on_change=on_change)
    row.addWidget(x_spin)
    row.addWidget(y_spin)
    return widget, x_spin, y_spin
