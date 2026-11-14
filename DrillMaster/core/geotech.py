"""Géométrie commune aux trois indicateurs géotechniques (v2.9.264).

Ce module porte UNIQUEMENT des règles métier partagées entre validation
et rendu : constantes, plages physiques, unités connues, rampe de couleur
et libellés.  Il ne touche ni à QGIS, ni à la vue : logic pure data /
presentation helpers, avec une seule dépendance à ``math``.

Important — Généricité (règle transverse) : aucun seuil, aucun nom de
fichier, aucune valeur de test utilisateur n'est codé ici.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Constantes métier
# ---------------------------------------------------------------------------
GEOTECH_KINDS = ("rqd", "recovery", "density")
GEOTECH_RANGE = {
    "rqd": (0.0, 100.0),
    "recovery": (0.0, 100.0),
}
GEOTECH_DENSITY_UNIT = "g/cm³"
# RQD / récupération sont DES POURCENTAGES par définition métier (bornes
# 0–100) : « % » n'est pas une unité inventée, c'est la borne elle-même.
GEOTECH_PERCENT_UNIT = "%"

# Écart minimal de la rampe densité (unité des données).  Sans lui, une
# seule mesure donnerait une rampe plate (2,7–2,7) et 0,01 d'écart réel
# serait étalé sur toute la rampe — illisible dans les deux cas.
GEOTECH_DENSITY_MIN_SPAN = 0.5

# Seuil d'alerte (jamais bloquant) pour les densités très élevées.
# Générique : aucune référence à un matériau/fichier de l'utilisateur.
GEOTECH_UNUSUAL_DENSITY_THRESHOLD = 6.0

# Plage physique de référence de la densité (jamais nommée) : utilisée
# quand aucune donnée n'est à l'écran, pour ne jamais inventer de bornes.
GEOTECH_DENSITY_REFERENCE_RANGE = (1.0, 4.0)

# Gris « aucune mesure » — bande hachurée 2D ET pastille de légende (2D/3D).
# Une seule constante : la légende 3D ne redéfinit pas son gris (v2.9.267).
GEOTECH_MISSING_COLOUR = "#9E9E9E"

# Unités de densité reconnues (affichées telles quelles, jamais converties).
DENSITY_KNOWN_UNITS = frozenset({
    "g/cm3", "g/cm³", "g/cm^3", "t/m3", "t/m³", "g/cc",
})


def geotech_kind(file_type: str) -> str:
    """Normalise un type de fichier vers une clé géotechnique connue."""
    value = str(file_type or "").casefold()
    return value if value in GEOTECH_KINDS else ""


def geotech_default_unit(kind: str) -> str:
    """Unité par défaut du domaine (celle des bornes métier, pas du CSV).

    Densité : ``g/cm³``.  RQD / récupération : ``%`` — les bornes 0–100
    sont des pourcentages, donc l'infobulle et la légende disent la même
    chose même si le CSV n'a pas de colonne ``unit``.
    """
    if geotech_kind(kind) == "density":
        return GEOTECH_DENSITY_UNIT
    if geotech_kind(kind) in GEOTECH_RANGE:
        return GEOTECH_PERCENT_UNIT
    return ""


def geotech_known_unit(unit: str, kind: str) -> bool:
    """Vrai si l'unité est reconnue pour la densité (vide acceptée)."""
    if geotech_kind(kind) != "density":
        return True
    return not str(unit or "").strip() or (str(unit).casefold() in DENSITY_KNOWN_UNITS)


def _value_of(item) -> float | None:
    """Valeur numérique d'un élément : ``GeotechRecord`` ou nombre nu.

    Le rendu passe des records, mais un appelant peut passer des valeurs
    déjà extraites : les deux formes sont lues correctement (un nombre nu
    n'a pas d'attribut ``value`` — le traiter comme 0 fausserait la rampe).
    """
    if isinstance(item, bool) or item is None:
        return None
    if isinstance(item, (int, float)):
        return float(item)
    raw = getattr(item, "value", None)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def geotech_range(kind: str, records=None) -> tuple[float, float]:
    """Plage d'affichage de la rampe.

    RQD / récupération : plage physique fixe 0–100 % (bornes métier).
    Densité : bornes observées sur les données à l'écran (records ou
    valeurs nues, les deux acceptées), avec un écart minimal de
    ``GEOTECH_DENSITY_MIN_SPAN`` pour que la rampe ne soit jamais plate
    (une seule valeur) ni étirée sur un écart infinitésimal.  Sans donnée,
    plage physique de référence ``GEOTECH_DENSITY_REFERENCE_RANGE``.
    """
    if geotech_kind(kind) in GEOTECH_RANGE:
        return GEOTECH_RANGE[geotech_kind(kind)]
    values = [
        value for value in
        (_value_of(record) for record in (records or []))
        if value is not None
    ]
    ref_lo, ref_hi = GEOTECH_DENSITY_REFERENCE_RANGE
    if not values:
        return (ref_lo, ref_hi)
    lo, hi = min(values), max(values)
    if hi - lo < GEOTECH_DENSITY_MIN_SPAN:
        centre = (lo + hi) / 2.0
        lo = centre - GEOTECH_DENSITY_MIN_SPAN / 2.0
        hi = centre + GEOTECH_DENSITY_MIN_SPAN / 2.0
    return (lo, hi)


def geotech_legend_scale(kind: str, records=None) -> tuple[float, float, str]:
    """Échelle UNIQUE du domaine : ``(lo, hi, unité)`` — rendu + légende.

    Le dessin des bandes/points et le texte sous la rampe appellent cette
    même fonction : les bornes affichées dans la légende sont exactement
    celles qui ont servi à colorer.  L'unité vient des données (jamais
    convertie, jamais inventée) ; à défaut, unité par défaut du domaine.
    """
    kind = geotech_kind(kind)
    lo, hi = geotech_range(kind, records)
    if kind not in GEOTECH_RANGE:
        # Seuls les domaines à unité libre (densité) lisent l'unité des
        # données : RQD / récupération sont des pourcentages par bornes.
        for record in records or []:
            unit = str(getattr(record, "unit", "") or "").strip()
            if unit:
                return (lo, hi, unit)
    return (lo, hi, geotech_default_unit(kind))


def geotech_unit_for(kind: str, record=None) -> str:
    """Unité affichée : celle du record si fournie, sinon unité par défaut."""
    kind = geotech_kind(kind)
    if record is not None:
        unit = str(getattr(record, "unit", "") or "").strip()
        if unit:
            return unit
    return geotech_default_unit(kind)


def _lerp(a: float, b: float, t: float) -> float:
    t = min(1.0, max(0.0, float(t)))
    return a + (b - a) * t


def geotech_colour(value, kind: str, lo=None, hi=None) -> str:
    """Couleur de la rampe pour une valeur géotechnique.

    RQD / récupération : bornes 0–100 % (rouge → orange → jaune → vert).
    Densité : bornes de la plage d'affichage (bleu clair → bleu foncé).
    Retourne une couleur hex #RRGGBB, jamais None.
    """
    kind = geotech_kind(kind)
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    lo = float(lo) if lo is not None else None
    hi = float(hi) if hi is not None else None
    if kind in GEOTECH_RANGE:
        geotechnic_lo, geotechnic_hi = GEOTECH_RANGE[kind]
        lo = geotechnic_lo if lo is None else lo
        hi = geotechnic_hi if hi is None else hi
        ratio = 0.0 if hi <= lo else (value - lo) / (hi - lo)
        ratio = min(1.0, max(0.0, ratio))
        if ratio < 0.5:
            t = ratio / 0.5
            r, g, b = (255, 40 + int(round(110 * t)), 40)
        else:
            t = (ratio - 0.5) / 0.5
            r = int(round(_lerp(220, 60, t)))
            g = int(round(_lerp(150, 180, t)))
            b = int(round(_lerp(40, 40, t)))
        return f"#{r:02X}{g:02X}{b:02X}"
    # densité
    default_lo, default_hi = GEOTECH_DENSITY_REFERENCE_RANGE
    lo = default_lo if lo is None else float(lo)
    hi = default_hi if hi is None else float(hi)
    ratio = 0.0 if hi <= lo else (value - lo) / (hi - lo)
    ratio = min(1.0, max(0.0, ratio))
    r = int(round(_lerp(80, 20, ratio)))
    g = int(round(_lerp(140, 60, ratio)))
    b = int(round(_lerp(220, 180, ratio)))
    return f"#{r:02X}{g:02X}{b:02X}"


def geotech_ramp_rgb(kind: str, lo=None, hi=None) -> list[str]:
    """Six couleurs de la rampe (pour légende / aperçu)."""
    if hi is None or lo is None:
        lo, hi = geotech_range(kind)
    lo, hi = float(lo), float(hi)
    return [
        geotech_colour(lo + (hi - lo) * ratio, kind, lo, hi)
        for ratio in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    ]


def geotech_label(kind: str) -> str:
    """Libellé court du domaine (source, traduit ensuite par la vue)."""
    return {
        "rqd": "RQD",
        "recovery": "Récupération",
        "density": "Densité",
    }.get(geotech_kind(kind), str(kind or ""))


def geotech_value_text(value, kind: str, unit: str = "") -> str:
    """Texte compact ``valeur + unité`` (jamais d'unité inventée)."""
    try:
        value_text = f"{float(value):g}"
    except (TypeError, ValueError):
        value_text = str(value or "")
    unit = str(unit or "").strip()
    return f"{value_text} {unit}".strip()


def geotech_depth_text(record) -> str:
    """Libellé de position (intervalle ou point) d'un enregistrement."""
    from_m = getattr(record, "from_m", None)
    to_m = getattr(record, "to_m", None)
    depth = getattr(record, "depth", None)
    if from_m is not None and to_m is not None:
        return f"{float(from_m):g}–{float(to_m):g} m"
    if depth is not None:
        return f"{float(depth):g} m"
    return ""


def geotech_anchor(record) -> float | None:
    """Profondeur d'ancrage pour le rendu (point ou borne TO)."""
    if getattr(record, "depth", None) is not None:
        return float(record.depth)
    if getattr(record, "to_m", None) is not None:
        return float(record.to_m)
    return None


def geotech_missing(record) -> bool:
    """Vrai si l'enregistrement ne porte pas de position exploitable."""
    return geotech_anchor(record) is None


# ---------------------------------------------------------------------------
# Contrôles croisés et aide à la lecture
# ---------------------------------------------------------------------------
# Tolérances du contrôle RQD ≤ récupération (jamais bloquant).
GEOTECH_RQD_CR_TOLERANCE = 0.5     # points — arrondi des deux tables
GEOTECH_INTERVAL_MATCH_TOL = 0.01  # m — « mêmes bornes » à l'arrondi près


def _interval_key(record) -> tuple | None:
    """Clé d'intervalle arrondie (``hole, from, to``) ou ``None``."""
    from_m = getattr(record, "from_m", None)
    to_m = getattr(record, "to_m", None)
    if from_m is None or to_m is None:
        return None
    return (
        str(getattr(record, "hole_id", "")),
        round(min(float(from_m), float(to_m)) / GEOTECH_INTERVAL_MATCH_TOL),
        round(max(float(from_m), float(to_m)) / GEOTECH_INTERVAL_MATCH_TOL),
    )


def geotech_rqd_over_recovery(rqd_records, recovery_records) -> list[dict]:
    """RQD supérieur à la récupération = incohérence physique.

    Le RQD ne compte que de la carotte **réellement remontée** : il est
    donc toujours ≤ la récupération.  Comparaison uniquement à **bornes
    identiques** (à ``GEOTECH_INTERVAL_MATCH_TOL`` près) : deux runs de
    longueurs différentes ne sont pas comparables (une perte hors de
    l'intervalle RQD suffit à expliquer l'écart) — aucun faux positif.

    Retourne une liste de ``{hole_id, from_m, to_m, rqd, recovery}``
    triée par forage puis profondeur ; liste vide si tout est cohérent.
    """
    by_interval = {}
    for record in recovery_records or []:
        key = _interval_key(record)
        if key is not None:
            by_interval[key] = _value_of(record)
    mismatches = []
    for record in rqd_records or []:
        key = _interval_key(record)
        recovery = by_interval.get(key) if key is not None else None
        rqd = _value_of(record)
        if recovery is None or rqd is None:
            continue
        if rqd - recovery > GEOTECH_RQD_CR_TOLERANCE:
            from_m = min(float(record.from_m), float(record.to_m))
            to_m = max(float(record.from_m), float(record.to_m))
            mismatches.append({
                "hole_id": str(getattr(record, "hole_id", "")),
                "from_m": from_m,
                "to_m": to_m,
                "rqd": rqd,
                "recovery": recovery,
            })
    mismatches.sort(key=lambda item: (item["hole_id"], item["from_m"]))
    return mismatches


def geotech_link_pairs(records) -> list[tuple]:
    """Paires de mesures voisines à relier (courbe de tendance densité).

    Une courbe ne se lit que si les mesures se suivent : deux points
    séparés par un grand vide ne décrivent aucune tendance, et tracer le
    segment **inventerait** une donnée.  Règles :
    - moins de 3 mesures → aucune paire (rien à trend-relier) ;
    - un segment n'est tracé que si l'écart est ≤ 1,5 × l'écart médian
      du forage (vide réel → rupture de la courbe, jamais comblée).

    Retourne des couples ``(record, record)`` triés par profondeur.
    """
    placed = sorted(
        (record for record in (records or [])
         if geotech_anchor(record) is not None
         and _value_of(record) is not None),
        key=geotech_anchor)
    if len(placed) < 3:
        return []
    anchors = [geotech_anchor(record) for record in placed]
    gaps = sorted(
        anchors[index + 1] - anchors[index]
        for index in range(len(anchors) - 1))
    median = gaps[len(gaps) // 2]
    if median <= 0:
        return []
    limit = median * 1.5
    return [
        (placed[index], placed[index + 1])
        for index in range(len(placed) - 1)
        if anchors[index + 1] - anchors[index] <= limit
    ]

