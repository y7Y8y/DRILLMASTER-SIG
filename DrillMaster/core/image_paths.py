"""Résolution des chemins d'imagerie (Chantier 2).

Cette logique est volontairement sans Qt pour être testable dans la suite
« noyau » : `section_imagery.py` ne fait que l'appeler.
"""

from __future__ import annotations

import os
from pathlib import Path


def base_candidates(project, source_dir: str) -> list[str]:
    """Dossiers projet dans lesquels on cherche une image relative."""
    bases = []
    if project is not None:
        paths = getattr(project, "paths", None)
        if paths is not None:
            for attr in ("project_dir", "data_import_dir", "assets_dir"):
                value = getattr(paths, attr, None)
                if value:
                    bases.append(value)
    if source_dir:
        bases.append(source_dir)
    return bases


def _resolve_basename(raw, project, source_dir: str) -> str:
    # Accepte les séparateurs \ et / même hors Windows (le test/débogage
    # tourne aussi sous Linux avec un chemin issu d'un vieux CSV Windows).
    basename = raw.replace("\\", "/").rstrip("/").split("/")[-1]
    if not basename:
        return ""
    for base in base_candidates(project, source_dir):
        candidate = os.path.join(base, basename)
        if os.path.isfile(candidate):
            return candidate
    return ""


def resolve_image_path(project, raw, source_dir: str = "") -> str:
    """First existing file for ``raw`` following the Chantier 2 order.

    Returns an absolute path, or ``""`` when nothing exists.  Never
    raises: the renderer treats an empty result as a missing file.
    """
    raw = str(raw or "").strip()
    if not raw:
        return ""
    p = Path(raw)
    if p.is_absolute():
        if os.path.isfile(p):
            return str(p)
        # Projet déplacé (ex. C:→E:) : un chemin absolu périmé ne doit
        # pas faire disparaître la photo. On retente par son basename
        # dans les dossiers projet actifs, comme pour un lien relatif.
        return _resolve_basename(raw, project, source_dir)
    # 1) as-is (in the current working dir); 2) project dirs; 3) CSV dir.
    if os.path.isfile(raw):
        return os.path.abspath(raw)
    for base in base_candidates(project, source_dir):
        candidate = os.path.join(base, raw)
        if os.path.isfile(candidate):
            return candidate
    # dossier déplacé / colonne historique : même dernière chance par
    # basename dans les dossiers projet actifs.
    return _resolve_basename(raw, project, source_dir)
