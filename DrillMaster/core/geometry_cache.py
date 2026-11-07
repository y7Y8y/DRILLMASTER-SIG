"""DrillMaster — cache JSON des trajectoires (v2.9.322).

Retour écran : « une fois générées, les trajectoires sont sauvées et
en rouvrant le projet ça vient sur les sections — mais on nous demande
à chaque fois de régénérer ».  La restauration passait UNIQUEMENT par
le GeoPackage géométrie ; si ce fichier est absent ou illisible
(ancien projet, copie partielle, verrou antivirus sous Windows…),
l'ouverture retombait sur « Cliquez sur Générer les trajectoires 3D ».

Ce module ajoute une persistance JSON **indépendante de QGIS** :

* écrite à chaque génération réussie (``step3._done``) ;
* relue à l'ouverture si le GeoPackage manque — signature SHA-256 des
  collets+déviations : des données modifiées invalident le cache (pas
  de trajectoire périmée sur des données neuves — même classe de bug
  que v2.9.190) ;
* et si même le cache manque, l'ouverture GÉNÈRE silencieusement en
  mémoire (collets+déviations suffisent) — plus jamais de demande.

Format : ``geometry_cache.json`` dans le dossier projet,
``{"signature": ..., "holes": [{hole_id, collar, survey,
trajectory [[x, y, z, depth], ...]}]}``.  Les domaines (litho,
teneurs…) ne sont PAS dupliqués ici : ils sont réattachés depuis les
copies CSV du projet, exactement comme le chemin GeoPackage.
"""

from __future__ import annotations

import hashlib
import json
import os

from dataclasses import asdict, fields

from .data_model import (
    CollarRecord, DrillHole, SurveyRecord, TrajectoryPoint,
)

_CACHE_NAME = "geometry_cache.json"


def _from_dict(cls, data: dict):
    keep = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in (data or {}).items() if k in keep})


def _canonical(collars: dict, surveys: dict) -> bytes:
    """Signature stable des DONNÉES d'entrée (collets + déviations)."""
    parts = []
    for hid in sorted(collars or {}):
        c = collars[hid]
        parts.append((
            str(hid),
            round(float(getattr(c, "x", 0.0)), 4),
            round(float(getattr(c, "y", 0.0)), 4),
            round(float(getattr(c, "z", 0.0)), 4),
            round(float(getattr(c, "max_depth", 0.0)), 4),
        ))
        for s in sorted(
                surveys.get(hid, []) or [],
                key=lambda s: float(getattr(s, "depth", 0.0))):
            parts.append((
                str(hid),
                round(float(getattr(s, "depth", 0.0)), 4),
                round(float(getattr(s, "azimuth", 0.0)), 4),
                round(float(getattr(s, "dip", 0.0)), 4),
            ))
    return json.dumps(parts, sort_keys=True).encode("utf-8")


def geometry_signature(collars: dict, surveys: dict) -> str:
    return hashlib.sha256(_canonical(collars, surveys)).hexdigest()


def cache_path(project) -> str:
    return os.path.join(project.paths.project_dir, _CACHE_NAME)


def save_geometry_cache(project, drillholes) -> bool:
    """Écrit le cache (appelé après génération réussie). Jamais levant."""
    try:
        payload = {
            "signature": geometry_signature(
                {d.hole_id: d.collar for d in drillholes},
                {d.hole_id: d.survey for d in drillholes}),
            "holes": [
                {
                    "hole_id": d.hole_id,
                    "collar": asdict(d.collar),
                    "survey": [asdict(sv) for sv in (d.survey or [])],
                    "trajectory": [
                        [p.x, p.y, p.z, p.depth]
                        for p in (d.trajectory or [])],
                }
                for d in drillholes],
        }
        with open(cache_path(project), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        return True
    except Exception as _exc:
        # le cache est un confort, pas une condition de sauvegarde
        from .diagnostics import log_swallowed
        log_swallowed("Cache trajectoires : écriture", _exc)
        return False


def load_geometry_cache(project, collars: dict, surveys: dict):
    """Relit le cache si la signature correspond, sinon None.

    Retourne une liste de DrillHole AVEC trajectoires (domaines vides,
    réattachés par l'appelant depuis les copies CSV du projet).
    """
    try:
        path = cache_path(project)
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        if payload.get("signature") != geometry_signature(
                collars, surveys):
            return None  # données modifiées → trajectoires périmées
        out = []
        for h in payload.get("holes", []):
            if h.get("hole_id") not in (collars or {}):
                continue  # forage retiré des données depuis
            traj = [TrajectoryPoint(
                        float(p[0]), float(p[1]), float(p[2]),
                        float(p[3]))
                    for p in h.get("trajectory", []) if len(p) >= 4]
            if len(traj) < 2:
                continue
            out.append(DrillHole(
                hole_id=h["hole_id"],
                collar=_from_dict(CollarRecord, h.get("collar")),
                survey=[_from_dict(SurveyRecord, sv)
                        for sv in h.get("survey", [])],
                trajectory=traj,
            ))
        return out or None
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("Cache trajectoires : lecture", _exc)
        return None
