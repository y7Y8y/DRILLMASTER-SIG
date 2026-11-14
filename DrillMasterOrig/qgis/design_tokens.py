"""
DrillMaster ORIG — tokens de design (coquille QGIS).

Mêmes valeurs que le v2 (ui/design_tokens.py) tant que les deux
cohabitent ; ORIG deviendra la référence quand le v2 sera retiré.
Règles : docs/DESIGN.md + ARCHITECTURE.md (data-ink, échelles fermées).
"""

from __future__ import annotations

COLORS = {
    "primary":      "#17202A",
    "primary_lt":   "#5D6D7E",
    "accent":       "#1C2833",
    "accent_hover": "#2A3C4D",
    "success":      "#196F3D",
    "warning":      "#E67E22",
    "danger":       "#922B21",
    "bg_main":      "#F8F9F9",
    "bg_card":      "#FFFFFF",
    "bg_input":     "#FFFFFF",
    "text_dark":    "#2C3E50",
    "text_medium":  "#566573",
    "text_light":   "#95A5A6",
    "text_white":   "#FFFFFF",
    "border":       "#D5DBDB",
    "border_dark":  "#AEB6BF",
    "hover_subtle": "#EDEFEF",
    "disabled_bg":  "#ECF0F1",
    "disabled_ink": "#95A5A6",
    "surface_dark": "#1B2631",
    "surface_code": "#1E1E1E",
    "ink_on_dark":  "#CCCCCC",
}

TYPE = {
    "annotation": "7.5pt",
    "small":      "8pt",
    "compact":    "8.5pt",
    "body":       "9pt",
    "title":      "11pt",
    "display":    "24pt",
}

FONT_FAMILY = "'Segoe UI', 'Sans Serif'"

SPACING = {"xs": 2, "s": 4, "m": 8, "l": 12, "xl": 16, "xxl": 24}
RADIUS = {"s": 3, "m": 6}
