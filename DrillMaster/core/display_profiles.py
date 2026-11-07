"""Types d'ouvrage & profils de visualisation (v2.9.289).

Concept « VisualizationProfile » (proposition validée) : le moteur
géologique reste en profondeurs RÉELLES ; seule la représentation
VERTICALE est transformée, par type d'ouvrage, via une fonction
strictement monotone real_depth → display_depth :

  RC/DD   → identité (l'exagération globale existante s'applique ensuite) ;
  AUGER   → petite ouvrages 0–15 m rendus lisibles ;
  PUITS   → transformation plus appuyée pour 0–5 m ;
  CUSTOM  → paramètres utilisateur.

RÈGLES (verrouillées) :
  - T(0) = 0 (le collet reste au collet) ;
  - strictement croissante : 0,6 < 1 < 2,3 < 5 reste vrai graphiquement ;
  - jamais par intervalle : on transforme l'AXE de profondeur du trou,
    puis traces, litho, teneurs, structures se placent dessus ;
  - aucune donnée réelle modifiée (max_depth, from/to, TrajectoryPoint).

Le type d'ouvrage est porté par CollarRecord.hole_type (optionnel,
rétrocompatible) ou CHOISI dans l'interface (v2.9.293+ : un seul choix
pour tout le projet).  Depuis v2.9.298 il n'y a PLUS d'option « Auto » :
sans choix explicite, RC/DD = échelle réelle, comportement inchangé.
"""
from __future__ import annotations

import math

PROFILES = ("RC_DD", "AUGER", "PUITS", "CUSTOM")

# Paramètres par profil : m = remontée visuelle mini (m affichés),
# c = profondeur de raccord (m), f = facteur linéaire au-delà.
# T(d) = m·(1 − e^(−d/c)) + f·d  → T(0)=0, dérivée > 0 partout.
DEFAULT_PARAMS = {
    "AUGER": {"min_visible": 2.0, "curve": 1.0, "factor": 2.0},
    "PUITS": {"min_visible": 3.0, "curve": 1.0, "factor": 4.0},
    "CUSTOM": {"min_visible": 2.0, "curve": 1.0, "factor": 3.0},
}

_TYPE_PREFIXES = (
    (("AUG",), "AUGER"),
    (("PIT", "PUIT",), "PUITS"),
    (("RC", "HRC", "RAB", "ISBRC", "ISPT"), "RC"),
    (("DD", "BH", "SOND"), "DD"),
)


def infer_hole_type(hole_id) -> "str | None":
    """Type d'ouvrage d'après le préfixe (« AUG004 » → AUGER), sinon None."""
    up = str(hole_id or "").strip().upper()
    for prefixes, typ in _TYPE_PREFIXES:
        if up.startswith(prefixes):
            return typ
    return None


def profile_for(hole_type) -> str:
    """Profil de visualisation pour un type d'ouvrage (défaut RC_DD)."""
    t = str(hole_type or "").strip().upper()
    if t in ("AUGER", "PUITS", "CUSTOM"):
        return t
    return "RC_DD"


def display_depth(real: float, profile: str, params=None) -> float:
    """Profondeur d'affichage ; identité pour RC_DD ; monotone sinon."""
    if profile in ("RC_DD", "", None):
        return float(real)
    p = dict(DEFAULT_PARAMS.get(profile, DEFAULT_PARAMS["CUSTOM"]))
    p.update(params or {})
    d = float(real)
    if d <= 0.0:
        return d
    m = float(p.get("min_visible", 0.0))
    c = max(float(p.get("curve", 1.0)), 1e-6)
    f = max(float(p.get("factor", 1.0)), 0.0)
    return m * (1.0 - math.exp(-d / c)) + f * d


def make_display_transform(drillhole, config=None):
    """z → z d'affichage pour un forage, ou None (RC/DD, désactivé…)."""
    cfg = config or {}
    if not cfg.get("enabled", True):
        return None
    collar = getattr(drillhole, "collar", None)
    if collar is None:
        return None
    hid = getattr(drillhole, "hole_id", "") or getattr(collar, "hole_id", "")
    typ = (cfg.get("overrides") or {}).get(hid)
    # v2.9.292 — mode global (« je choisis auger/dd et tout est automatisé »)
    typ = typ or cfg.get("global") or ""
    # v2.9.298 — « si l'option type de forage existe, enlever Auto » :
    # le préfixe ne décide PLUS.  Sans choix (global/override/colonne) :
    # RC_DD = échelle réelle.
    typ = typ or getattr(collar, "hole_type", None)
    profile = profile_for(typ)
    if profile == "RC_DD":
        return None
    params = dict(DEFAULT_PARAMS.get(profile, {}))
    params.update((cfg.get("params") or {}).get(profile, {}))
    cz = float(collar.z)

    def transform(z: float) -> float:
        return cz - display_depth(cz - float(z), profile, params)

    return transform
