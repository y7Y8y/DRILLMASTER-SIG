"""DrillMaster — la rose de localisation de la coupe (chantier 6, tranche 4).

Extrait de ``ui/section_dock.py``. Ce module dessine le **badge du nord** :
un disque en haut à gauche de la coupe, la trace P1→P2 à son azimut réel,
l'aiguille nord, les deux étiquettes P1 et P2, et la légende en toutes
lettres (« coupe N290° · WNW → ESE »).

Pourquoi elle sort maintenant
-----------------------------
C'est la plus petite des fonctions de dessin qui restaient dans la classe :
95 lignes pour **trois** lectures d'état seulement — ``self._line`` (la
ligne de coupe), ``self.scene`` (la scène) et ``self.tr`` (la traduction).
Rien de la vue n'est modifié : la fonction pose des items dans la scène et
n'en retire aucun. On peut donc lui passer ces trois choses et la sortir
sans qu'aucun pixel ne change.

Ce que ce module possède
------------------------
- ``_draw_north_badge`` : la rose entière, items et infobulles comprises.
  ``widget`` sert uniquement à ``widget.tr(...)`` ; ``line`` est un objet
  portant ``x1``, ``y1``, ``x2``, ``y2`` (la ``SectionLine`` du noyau).

Ce qui reste dans ``section_dock``
----------------------------------
L'appel ``if self._show_orientation: self._draw_north_badge()`` — le nom
reste attaché à ``SectionCanvas``, donc aucun appelant ne change.
"""
from __future__ import annotations

from qgis.PyQt.QtCore import QPointF
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QPen, QPolygonF

# Les couleurs de la charte : `styles_qt` ne dépend de rien d'autre que Qt,
# il n'y a donc pas de cycle à craindre en l'important ici.
from .styles_qt import COLORS

# Le modèle de la rose et son étiquette vivent dans le noyau, qui ne
# connaît pas Qt : ils se rangent en tête, pas au milieu du dessin.
from ..core.geometry import (
    azimuth_label, section_azimuth_degrees, section_rose_model)
from ..core.section import compass16


def _draw_north_badge(widget, scene, line) -> None:
    """v2.7.6.3 (ORI-03) — rose de localisation en vue de plan.

    Le nord reste en haut et la trace de la coupe est fléchée à son
    azimut réel, de P1 vers P2. Faire tourner une aiguille dans le plan
    d'une coupe verticale était trompeur : ce plan n'a pas de nord.

    ``widget`` ne sert qu'à traduire les deux textes (``widget.tr``).
    """
    if not line:
        return
    az = section_azimuth_degrees(line.x1, line.y1, line.x2, line.y2)
    radius = 11.0
    cx, cy = 30.0, 32.0
    model = section_rose_model(az, cx, cy, radius)
    items = []

    disc = scene.addEllipse(
        cx - radius * 1.35, cy - radius * 1.35,
        radius * 2.7, radius * 2.7,
        QPen(QColor(COLORS['border']), 0.7),
        QBrush(QColor(255, 255, 255, 232)))
    disc.setZValue(14)
    items.append(disc)

    trace_pen = QPen(QColor("#B03A2E"), 1.4)
    trace = scene.addLine(
        model["p1"][0], model["p1"][1], model["p2"][0], model["p2"][1],
        trace_pen)
    trace.setZValue(15)
    head = scene.addPolygon(
        QPolygonF([QPointF(*point) for point in model["arrow"]]),
        QPen(QColor("#B03A2E"), 0.5), QBrush(QColor("#B03A2E")))
    head.setZValue(16)
    items.extend([trace, head])

    needle = model["needle"]
    south = scene.addPolygon(
        QPolygonF([QPointF(*point) for point in needle["south"]]),
        QPen(QColor(COLORS['primary']), 0.6), QBrush(QColor(255, 255, 255)))
    south.setZValue(16)
    north = scene.addPolygon(
        QPolygonF([QPointF(*point) for point in needle["north"]]),
        QPen(QColor(COLORS['primary']), 0.6),
        QBrush(QColor(COLORS['primary'])))
    north.setZValue(17)
    items.extend([south, north])

    label = scene.addText("N", QFont("Segoe UI", 7, QFont.Weight.Bold))
    label.setDefaultTextColor(QColor(COLORS['primary']))
    label_x, label_y = needle["label"]
    label.setPos(label_x - label.boundingRect().width() / 2,
                 label_y - label.boundingRect().height() / 2)
    label.setZValue(17)
    items.append(label)

    for key, text in (("p1_label", "P1"), ("p2_label", "P2")):
        mark = scene.addText(text, QFont("Segoe UI", 6))
        mark.setDefaultTextColor(QColor("#B03A2E"))
        mx, my = model[key]
        mark.setPos(mx - mark.boundingRect().width() / 2,
                    my - mark.boundingRect().height() / 2)
        mark.setZValue(17)
        items.append(mark)

    # 361 — la direction EN TOUTES LETTRES sous l'azimut : plus
    # personne ne confond l'axe de la ligne et le sens de lecture
    # (retour « WNW / ESE ? » + chef « pourquoi 290° »).
    sens = f"{compass16(az + 180)} → {compass16(az)}"
    caption = scene.addText(
        widget.tr("coupe {} · {}").format(azimuth_label(az), sens),
        QFont("Segoe UI", 6))
    # 361 — infobulle pédagogique : azimut coupe = P1→P2 ; un
    # forage à ±180° suit le MÊME axe, lu en sens inverse.
    disc.setToolTip(widget.tr(
        "Nord en haut · flèche rouge = ligne de coupe, sens P1→P2 "
        "({}).  Un forage dont l'azimut diffère d'environ 180° est "
        "foré LE LONG de la coupe, en sens inverse : même axe, lu "
        "P2→P1 — ce n'est pas une erreur.").format(sens))
    caption.setDefaultTextColor(QColor(COLORS['text_medium']))
    caption.setPos(cx - caption.boundingRect().width() / 2,
                   cy + radius * 1.35 + 2)
    caption.setZValue(17)
    items.append(caption)

    # 332 — « et ça c'est quoi ? » : la boussole s'explique
    # elle-même au survol.
    tip = widget.tr(
        "Boussole de la coupe — flèche noire : Nord ; ligne rouge : "
        "ta ligne de coupe P1→P2 vue de dessus ; « coupe N…° » : "
        "azimut de P1 vers P2.")
    for it in items:
        it.setToolTip(tip)
