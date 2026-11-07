# tools/bench_qpainter_draw.py — mesure le dessin QPainter hors calcul.
# Annexe du plan de correctifs moteur 3D (§4) — v2.9.318.
# Usage : xvfb-run -a python3 tools/bench_qpainter_draw.py
import sys
import time

try:
    from qgis.PyQt.QtWidgets import QApplication
    from qgis.PyQt.QtGui import (QPainter, QPixmap, QColor, QPen, QBrush,
                                 QPolygonF)
    from qgis.PyQt.QtCore import QPointF
except ImportError:  # hors QGIS : PyQt5 direct
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QPainter, QPixmap, QColor, QPen, QBrush, QPolygonF
    from PyQt5.QtCore import QPointF

app = QApplication(sys.argv)


def make_scene(n_holes, intervals_per_hole, W=1400, H=900):
    quads, lines = [], []
    colors = [QColor(120, 90, 60), QColor(90, 140, 90),
              QColor(160, 100, 40), QColor(100, 100, 160)]
    for h in range(n_holes):
        x0, y0 = 50 + (h % 30) * 40, 50 + (h // 30) * 15
        for i in range(intervals_per_hole):
            y, w = y0 + i * 3, 6
            quads.append((QPolygonF([QPointF(x0 - w, y), QPointF(x0 + w, y),
                                     QPointF(x0 + w, y + 3),
                                     QPointF(x0 - w, y + 3)]),
                          colors[i % 4]))
            lines.append((QPointF(x0 - w, y), QPointF(x0 + w, y)))
    return quads, lines, W, H


def bench(n_holes, intervals_per_hole, antialias, label):
    quads, lines, W, H = make_scene(n_holes, intervals_per_hole)
    pix = QPixmap(W, H)
    pix.fill(QColor("#171D22"))
    painter = QPainter(pix)
    if antialias:
        painter.setRenderHint(QPainter.Antialiasing)
    t0 = time.perf_counter()
    pen = QPen(QColor(20, 20, 20), 1)
    for poly, color in quads:
        painter.setPen(pen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(poly)
    painter.setPen(QPen(QColor(230, 230, 230), 1))
    for a, b in lines:
        painter.drawLine(a, b)
    painter.end()
    dt = (time.perf_counter() - t0) * 1000.0
    print(f"{label:45s} | {len(quads):6d} quads+lignes | "
          f"AA={antialias!s:5s} | {dt:8.2f} ms")


bench(50, 50, True, "50 forages, avec AA")
bench(50, 50, False, "50 forages, sans AA")
bench(500, 50, True, "500 forages, avec AA")
bench(500, 50, False, "500 forages, sans AA")
