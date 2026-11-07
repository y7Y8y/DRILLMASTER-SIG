"""DrillMaster — Visualiseur photo Imagerie 3D (v2.9.263).

La vue 3D n'affiche plus de ruban texturé le long de la trajectoire.
Le repère-badge (lettre matériau, coloré) reste posé sur le trou ; un
clic dessus ouvre ici la photo en grand.  Le chargement est adaptatif :
toute image, toute taille de fichier, est décodée via QImageReader
(repli QImage) puis réduite à une taille d'écran raisonnable — jamais
un décodage complet d'un panoramique géant dans la boucle de rendu.

Le mécanisme est générique : aucun nom de forage, plage de profondeur,
matériau, organisation de fichier ni taille d'image n'est supposé.
"""

from __future__ import annotations

import os
import re

from qgis.PyQt.QtCore import QSize, Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QImage, QImageReader, QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QScrollArea, QSizePolicy,
    QVBoxLayout,
)

from ..core.image_paths import resolve_image_path
from ..core.diagnostics import log_swallowed


# Taille cible d'affichage : bornée pour rester fluide sur n'importe
# quelle photo, assez grande pour rester « en grand » et lisible.
_VIEWER_MAX_PX = 1600


def _load_photo_any_size(path: str) -> QPixmap | None:
    """Charge une photo de n'importe quelle taille en bornant le décodage.

    QImageReader permet de réduire AVANT décodage (mémoire bornée pour
    les très grandes images) ; le repli QImage couvre les décodeurs que
    QImageReader refuse silencieusement.  Ne lève jamais : retourne
    None si le fichier ne peut pas être lu.
    """
    if not path:
        return None
    path_str = str(path)
    try:
        reader = QImageReader(path_str)
        reader.setAutoTransform(True)
        src_size = reader.size()
        target = QSize(_VIEWER_MAX_PX, _VIEWER_MAX_PX)
        if (src_size.isValid()
                and (src_size.width() > _VIEWER_MAX_PX
                     or src_size.height() > _VIEWER_MAX_PX)):
            reader.setScaledSize(src_size.scaled(
                target, Qt.KeepAspectRatio))
        image = reader.read()
        if image is not None and not image.isNull():
            pixmap = QPixmap.fromImage(image)
            if not pixmap.isNull():
                return pixmap
    except Exception as _exc:
        log_swallowed("view_3d_imagery_viewer : lecture QImageReader", _exc)

    # Repli Qt direct (mêmes chemins que la 2D).
    try:
        image = QImage(path_str)
        if image is not None and not image.isNull():
            scaled = image
            if (image.width() > _VIEWER_MAX_PX
                    or image.height() > _VIEWER_MAX_PX):
                scaled = image.scaled(
                    _VIEWER_MAX_PX, _VIEWER_MAX_PX,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(scaled)
            if not pixmap.isNull():
                return pixmap
    except Exception as _exc:
        log_swallowed("view_3d_imagery_viewer : lecture QImage", _exc)
    return None


def _filename_depth_ranges(path: str) -> list[tuple[float, float]]:
    """Plages numériques repérables dans un nom de fichier image.

    v2.9.263 — garde-fou de diagnostic : si le nom du fichier CSV évoque
    des bornes (``0-8``, ``0_8``, ``0–8 m``…), le visualiseur le signale
    quand elles ne correspondent PAS à l'intervalle cliqué.  Fonction
    générique : aucun forage / plage / organisation n'est supposé ; elle
    se contente de lire des paires numériques triées dans le basename.
    C'est un AVERTISSEMENT (on n'interdit pas d'ouvrir une photo dont le
    nom ne suit aucune convention), jamais un blocage.
    """
    if not path:
        return []
    name = str(os.path.basename(str(path)))
    ranges: list[tuple[float, float]] = []
    for low_s, high_s in re.findall(
            r"(\d+(?:[.,]\d+)?)\s*(?:[-–—_]\s*)(\d+(?:[.,]\d+)?)", name):
        try:
            low = float(low_s.replace(",", "."))
            high = float(high_s.replace(",", "."))
        except Exception as _rng_exc:
            # Jeton numérique mal formé (trop grand/overflow…) : on ignore
            # ce fragment, le reste du nom reste analysé ; jamais bloquant.
            log_swallowed(
                "view_3d_imagery_viewer : intervalle dans nom de fichier",
                _rng_exc)
            continue
        if low < 0 or high < 0 or high > 1000000 or low > high:
            continue
        ranges.append((low, high))
    return ranges


def _imagery_source_dir(canvas) -> str:
    provider = getattr(canvas, "imagery_source_dir_provider", None)
    if callable(provider):
        try:
            return str(provider() or "")
        except Exception as _exc:
            log_swallowed("view_3d_imagery_viewer : dossier source", _exc)
    return str(getattr(canvas, "_imagery_source_dir", "") or "")


class _ImageryPhotoDialog(QDialog):
    """Fenêtre « photo en grand » pour un intervalle d'imagerie 3D."""

    def __init__(self, parent, canvas, hole_id, from_m, to_m, record=None):
        super().__init__(parent)
        self.canvas = canvas
        self._record = record
        self._from_m = from_m
        self._to_m = to_m
        self._hole_id = hole_id
        self._resolved_path = ""

        self.setWindowTitle(self.tr(
            "Imagerie — {} · {}–{} m").format(
                hole_id, f"{from_m:g}", f"{to_m:g}"))
        self.setMinimumSize(360, 280)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self._info = QLabel()
        self._info.setWordWrap(True)
        self._info.setStyleSheet("color:#34495E; font-size:9pt;")
        layout.addWidget(self._info)

        self._image_label = QLabel(self.tr("Chargement de l'image…"))
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet(
            "color:#7F8C8D; background:#F4F6F7; border:1px solid #D5DBDB;")
        self._image_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignCenter)
        self._scroll.setWidget(self._image_label)
        layout.addWidget(self._scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self._open_external = buttons.addButton(
            self.tr("Ouvrir dans le visualiseur système"),
            QDialogButtonBox.ActionRole)
        self._open_external.clicked.connect(self._open_system_viewer)
        self._open_external.setEnabled(False)

        self._load()

    def _record_for_selection(self):
        f = float(self._from_m)
        t = float(self._to_m)
        # L'enregistrement du badge cliqué est prioritaire MAIS on vérifie
        # toujours ses bornes : s'il est périmé (les données ont changé
        # depuis le rendu), on retombe sur la recherche par intervalle.
        if self._record is not None:
            try:
                if (abs(float(self._record.from_m) - f) < 1e-4
                        and abs(float(self._record.to_m) - t) < 1e-4):
                    return self._record
            except Exception as _rec_exc:
                # Enregistrement passé incohérent (bornes non numériques,
                # objet périmé…) : on retombe sur la recherche par bornes.
                log_swallowed(
                    "view_3d_imagery_viewer : enregistrement du badge",
                    _rec_exc)
        for dh in (getattr(self.canvas, "_drillholes", None) or []):
            if dh.hole_id != self._hole_id:
                continue
            for rec in (getattr(dh, "imagery", None) or []):
                if (abs(float(rec.from_m) - f) < 1e-4
                        and abs(float(rec.to_m) - t) < 1e-4):
                    self._record = rec
                    return rec
        return None

    def _load(self):
        rec = self._record_for_selection()
        if rec is None:
            self._show_error(self.tr("Enregistrement imagerie introuvable."))
            return
        material = str(getattr(rec, "material_label", "") or "")
        header = self.tr("Forage : {} · {}–{} m · Matériau : {}").format(
            self._hole_id,
            f"{float(rec.from_m):g}", f"{float(rec.to_m):g}",
            material if material else self.tr("Non renseigné"))
        project = getattr(self.canvas, "_project_ref", None)
        source_dir = _imagery_source_dir(self.canvas)
        raw_path = str(getattr(rec, "image_path", "") or "")
        path = resolve_image_path(project, raw_path, source_dir)
        self._resolved_path = path
        # Chemin CSV affiché quand il diffère du fichier résolu : un
        # écart devient visible immédiatement (donnée erronée ≠ bug 3D).
        path_line = self.tr("Chemin CSV : {}").format(
            raw_path if raw_path else self.tr("(vide)"))
        # Garde-fou : le nom du fichier peut évoquer un autre intervalle
        # que celui cliqué — on le SIGNALE (jamais sans bruit).
        ranges = _filename_depth_ranges(raw_path)
        if ranges:
            clicked = (float(rec.from_m), float(rec.to_m))
            if not any(abs(a - clicked[0]) < 1.0
                       and abs(b - clicked[1]) < 1.0 for a, b in ranges):
                listed = " · ".join(
                    f"{a:g}–{b:g} m" for a, b in ranges[:4])
                path_line += "\n" + self.tr(
                    "⚠ Le nom du fichier CSV contient l'intervalle {} — "
                    "ne correspond pas à {}–{} m. Vérifiez la ligne du "
                    "CSV.").format(
                        listed, f"{clicked[0]:g}", f"{clicked[1]:g}")
        if not path:
            self._info.setText(
                header + "\n" + path_line
                + "\n" + self.tr("⚠ Image introuvable"))
            self._image_label.setText(
                self.tr("Aucune image à afficher.\n"
                        "Le badge reste orange sur la trajectoire 3D."))
            return
        pixmap = _load_photo_any_size(path)
        if pixmap is None:
            self._info.setText(
                header + "\n" + path_line
                + "\n" + self.tr("⚠ Image illisible — fichier : {}").format(
                    path))
            self._image_label.setText(
                self.tr("Le fichier existe mais n'a pas pu être décodé."))
            return
        self._open_external.setEnabled(True)
        self._info.setText(
            header + "\n" + self.tr("Fichier : {}").format(path)
            + ("\n" + path_line if raw_path != path else ""))
        self._image_label.setPixmap(pixmap)
        self._image_label.adjustSize()

    def _show_error(self, message: str):
        self._info.setText(message)
        self._image_label.setText(message)

    def _open_system_viewer(self):
        if self._resolved_path and os.path.isfile(self._resolved_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._resolved_path))


def show_imagery_photo(canvas, hole_id, from_m, to_m, record=None):
    """Ouvre la photo en grand (fenêtre modale) pour un intervalle 3D."""
    try:
        parent = canvas.window() if hasattr(canvas, "window") else None
        dialog = _ImageryPhotoDialog(
            parent, canvas, hole_id, from_m, to_m, record=record)
        dialog.exec_()
    except Exception as _exc:
        log_swallowed("view_3d_imagery_viewer : ouverture photo", _exc)
