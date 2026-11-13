"""
DrillMaster — Design Tokens (source de vérité unique)
======================================================
v2.9.395 — Lot DA-0 : tokens de design centralisés.

Un seul module définit la langue visuelle du plugin : couleurs,
échelle typographique, espacements, rayons. Toute constante codée en
dur dans un fichier UI est une dérive ; le bon chemin est
``from .design_tokens import COLORS, TYPE, SPACING, RADIUS``.

Principe directeur (inchangé depuis v2.9.225, révision DA-1) :
data-ink (Tufte). LA COULEUR EST UN CANAL D'INFORMATION RÉSERVÉ AUX
DONNÉES. Le chrome (boutons, panneaux, libellés) travaille en VALEUR
(blanc / gris / anthracite). Seuls les STATUTS et les DONNÉES
(litho, altération, teneurs) portent de la teinte.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Couleurs — chrome neutre + statuts sémantiques
# ---------------------------------------------------------------------------
COLORS = {
    # Primary / encre
    "primary":      "#17202A",
    "primary_lt":   "#5D6D7E",
    # Accent — anthracite plein (état actif), éclaircissement au survol
    "accent":       "#1C2833",
    "accent_hover": "#2A3C4D",
    # Statuts — seuls éléments chromés du chrome
    "success":      "#196F3D",
    "warning":      "#E67E22",
    "danger":       "#922B21",
    # Backgrounds
    "bg_main":      "#F8F9F9",
    "bg_card":      "#FFFFFF",
    "bg_header":    "#2C3E50",
    "bg_input":     "#FFFFFF",
    # Texte
    "text_dark":    "#2C3E50",
    "text_medium":  "#566573",
    "text_light":   "#95A5A6",
    "text_white":   "#FFFFFF",
    # Bordures
    "border":       "#D5DBDB",
    "border_dark":  "#AEB6BF",
    # v2.9.395 — états dérivés, ANTI-dérive : les anciens bleus
    # (#D6EAF8 survol, #AED6F1 désactivé) entraient en concurrence
    # avec les teintes de données. Tout état est une VALEUR du gris.
    "hover_subtle":   "#EDEFEF",
    "hover_strong":   "#D5DBDB",
    "disabled_bg":    "#ECF0F1",
    "disabled_ink":   "#95A5A6",
    # Surfaces sombres (logs, infobulles)
    "surface_dark":   "#1B2631",
    "surface_code":   "#1E1E1E",
    "ink_on_dark":    "#CCCCCC",
    "ink_on_dark_hi": "#FDFEFE",
}

# ---------------------------------------------------------------------------
# Typographie — échelle fermée (5 crans + display)
# ---------------------------------------------------------------------------
# Interdiction d'inventer une valeur hors échelle. Le corps de base est
# 9pt (densité QGIS) ; 7.5pt = annotations ; 8pt = secondaire ; 8.5pt =
# compact ; 11pt = titres ; 24pt = splash uniquement.
TYPE = {
    "annotation":  "7.5pt",
    "small":       "8pt",
    "compact":     "8.5pt",
    "body":        "9pt",
    "title":       "11pt",
    "display":     "24pt",
}

FONT_FAMILY = "'Segoe UI', 'Sans Serif'"
FONT_MONO = "'Consolas', 'Courier New', monospace"

# ---------------------------------------------------------------------------
# Espacement — échelle de 4 (px)
# ---------------------------------------------------------------------------
SPACING = {
    "xs": 2,
    "s": 4,
    "m": 8,
    "l": 12,
    "xl": 16,
    "xxl": 24,
}

# ---------------------------------------------------------------------------
# Rayons — 2 crans seulement (minimalisme maîtrisé)
# ---------------------------------------------------------------------------
RADIUS = {
    "s": 3,   # champs, boutons, tables
    "m": 6,   # cartes, groupes repliés
}
