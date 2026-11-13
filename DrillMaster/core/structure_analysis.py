"""Analyse des mesures ``structure`` — math pure (aucun Qt, aucun QGIS).

v2.9.261 — Incrément A du chantier Roses / stéréonets.

Ce module ne dessine rien : il résout une mesure en orientation réellement
interprétable (monde N/E/vertical), projette un point sur un stéréonet
hémisphère inférieur (projection équivalente de Schmidt/Lambert) et découpe
les directions en classes pour une rose.

Règles non négociables :
- une mesure ``alpha``/``beta`` SEULES n'est jamais convertie en tendance /
  plongée « monde » (pas de référence d'orientation de carotte) ;
- une famille non-orientable n'est jamais tracée ;
- les classes de rose utilisent la convention **``[start, end[``** : 10° appartient
  à ``[10, 20)``, jamais compté deux fois ;
- 360° est normalisé à 0°.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .structure_classify import structure_family

_MODE_DIRECTION = "direction"
_MODE_ORIENTATION = "orientation"
_VALID_ROSE_MODES = (_MODE_DIRECTION, _MODE_ORIENTATION)


@dataclass(frozen=True)
class StructureSample:
    """Une mesure de structure importée, normalisée pour l'analyse."""

    hole_id: str
    depth: float
    code: str = ""

    # Orientation renseignée de façon « monde » (dip/dip_direction) ou
    # borehole (alpha/beta).  Les deux couples ne sont pas mélangés.
    dip: Optional[float] = None
    dip_direction: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None

    confidence: Optional[str] = None
    comment: str = ""


@dataclass(frozen=True)
class Orientation:
    """Une direction orientée dans le repère monde (N=0°, sens horaire)."""

    trend: float  # 0 <= trend < 360
    plunge: float  # 0 <= plunge <= 90 (positive, vers le bas)


@dataclass
class RoseBin:
    """Une classe de rose avec la convention ``[start, end[``."""

    start: float
    end: float
    count: int = 0
    indices: list[int] = field(default_factory=list)


def _has_dip_pair(sample: StructureSample) -> bool:
    return (
        sample.dip is not None
        and sample.dip_direction is not None
    )


def _has_alpha_beta_pair(sample: StructureSample) -> bool:
    return (
        sample.alpha is not None
        and sample.beta is not None
    )


def sample_family(sample: StructureSample) -> str:
    """Famille de la mesure via le classificteur partagé."""
    if sample is None:
        return "unknown"
    return structure_family(str(sample.code or ""))


def plane_strike(dip_direction: float) -> float:
    """Azimut 0–180° de la direction de frappe d'un plan.

    Convention : la frappe est perpendiculaire à la direction du pendage.
    180° est normalisé à 0°.
    """
    value = float(dip_direction or 0.0) % 360.0
    strike = (value + 90.0) % 180.0
    return strike if strike < 180.0 else 0.0


def is_alpha_beta_only(sample: StructureSample) -> bool:
    """True si la mesure ne porte QUE le couple alpha/bêta (pas dip)."""
    return not _has_dip_pair(sample) and _has_alpha_beta_pair(sample)


def resolve_orientation(sample: StructureSample) -> Optional[Orientation]:
    """Orientation réelle exploitable, ou ``None`` si elle ne doit pas être tracée.

    Règles :
    - planaire (famille inconnue comprise) avec dip/dip_direction → pôle de plan ;
    - linéaire avec dip/dip_direction → plongée/direction de la linéation ;
    - non-orientable (nodule, géode, stylolite…) → jamais tracé ;
    - composite → jamais tracé ;
    - alpha/bêta seuls → jamais tracé.
    """
    family = sample_family(sample)
    if family == "non_orientable":
        return None
    if family == "composite":
        return None
    if not _has_dip_pair(sample):
        return None

    dip = float(sample.dip)
    dip_direction = float(sample.dip_direction)
    if family == "linear":
        return Orientation(
            trend=dip_direction % 360.0,
            plunge=min(90.0, max(0.0, dip)),
        )
    # planaire ou inconnu orienté : même convention que le tadpole 2D.
    pole_trend = (dip_direction + 180.0) % 360.0
    pole_plunge = min(90.0, max(0.0, 90.0 - dip))
    return Orientation(trend=pole_trend, plunge=pole_plunge)


def rose_value(sample: StructureSample, mode: str = _MODE_DIRECTION) -> Optional[float]:
    """Valeur angulaire d'une mesure pour la rose (déjà normalisée)."""
    if mode not in _VALID_ROSE_MODES:
        raise ValueError(f"Mode de rose inconnu : {mode!r}")

    family = sample_family(sample)
    if family in ("non_orientable", "composite"):
        return None
    if sample.dip_direction is None:
        return None

    if family == "linear":
        direction = float(sample.dip_direction) % 360.0
        return direction % 180.0 if mode == _MODE_ORIENTATION else direction

    # planaire / inconnu orienté
    direction = float(sample.dip_direction) % 360.0
    if mode == _MODE_DIRECTION:
        return direction
    return plane_strike(direction)


def rose_index(value: float, span: float, bin_size: float = 10.0) -> int:
    """Index de classe ``[start, end[`` pour une valeur normalisée.

    - ``span`` : 360 (direction) ou 180 (orientation).
    - ``bin_size`` : largeur de classe (défaut 10°).
    - 10° → classe 1, jamais classe 0 ; 360° → 0° → classe 0.
    """
    if span <= 0 or bin_size <= 0:
        raise ValueError("span et bin_size doivent être strictement positifs")

    normalized = float(value) % float(span)
    n = int(round(float(span) / float(bin_size)))
    if n <= 0:
        raise ValueError("span/bin_size doit produire au moins une classe")

    index = int(math.floor(normalized / float(bin_size)))
    if index >= n:
        index = n - 1
    return index


def rose_bins(
    samples: list[StructureSample],
    mode: str = _MODE_DIRECTION,
    bin_size: float = 10.0,
) -> list[RoseBin]:
    """Classes de la rose, ordre ``[0, span[``, avec indices porteuses."""
    if mode not in _VALID_ROSE_MODES:
        raise ValueError(f"Mode de rose inconnu : {mode!r}")

    span = 360.0 if mode == _MODE_DIRECTION else 180.0
    count_bins = int(round(span / bin_size))
    if abs(span - count_bins * bin_size) > 1e-9:
        raise ValueError(
            "bin_size doit diviser exactement la plage (360 ou 180)")
    bins = [
        RoseBin(
            start=float(i * bin_size),
            end=float((i + 1) * bin_size),
        )
        for i in range(count_bins)
    ]

    for sample_index, sample in enumerate(samples):
        value = rose_value(sample, mode)
        if value is None:
            continue
        index = rose_index(value, span, bin_size)
        bins[index].indices.append(sample_index)
        bins[index].count += 1

    return bins


def project_schmidt(
    trend: float,
    plunge: float,
    radius: float = 1.0,
) -> tuple[float, float]:
    """Projection hémisphère inférieure, équivalente (Schmidt/Lambert).

    ``trend`` est en degrés depuis le Nord (sens horaire), ``plunge`` en
    degrés (0 = horizontal, 90 = vertical).  Retourne ``(x, y)`` dans un
    repère **Est → droite, Nord → haut**.
    """
    if radius <= 0:
        raise ValueError("radius doit être strictement positif")

    trend_n = float(trend) % 360.0
    plunge_n = min(90.0, max(0.0, float(plunge)))

    phase = math.radians(90.0 - plunge_n)
    r = float(radius) * math.sqrt(2.0) * math.sin(phase / 2.0)
    theta = math.radians(trend_n)
    return (
        r * math.sin(theta),
        r * math.cos(theta),
    )


def filter_structure_samples(
    samples: list[StructureSample],
    families: Optional[set[str]] = None,
    codes: Optional[set[str]] = None,
) -> list[StructureSample]:
    """Filtre les échantillons par famille et/ou code (pur, sans Qt).

    Le filtre ne touche jamais aux angles : il sélectionne les mesures qui
    restent visibles, donc c'est la SEULE porte d'entrée du dialogue pour
    reconstruire ``_hit_buckets`` (aucune sélection fantôme).
    """
    families = {str(f).strip().casefold() for f in (families or [])
                if str(f).strip()}
    codes = {str(c).strip() for c in (codes or []) if str(c).strip()}
    if not families and not codes:
        return list(samples or [])
    result = []
    for sample in samples or []:
        if families and sample_family(sample) not in families:
            continue
        if codes and str(sample.code or "").strip() not in codes:
            continue
        result.append(sample)
    return result


def sample_codes(samples: list[StructureSample]) -> list[str]:
    """Codes distincts, triés, présents dans le jeu (pour le filtre Type)."""
    codes = {str(sample.code or "").strip() for sample in samples or []}
    return sorted(codes)


def collect_samples_from_holes(drillholes) -> list[StructureSample]:
    """Transforme les ``DrillHole.structure`` en échantillons d'analyse."""
    samples: list[StructureSample] = []
    for hole in drillholes or []:
        hole_id = str(getattr(hole, "hole_id", "") or "")
        for record in getattr(hole, "structure", None) or []:
            code = str(
                getattr(record, "structure_type", "")
                or getattr(record, "type", "")
                or ""
            ).strip()
            samples.append(StructureSample(
                hole_id=hole_id,
                depth=float(getattr(record, "depth", 0.0) or 0.0),
                code=code,
                dip=getattr(record, "dip", None),
                dip_direction=getattr(record, "dip_direction", None),
                alpha=getattr(record, "alpha", None),
                beta=getattr(record, "beta", None),
                confidence=getattr(record, "confidence", None),
                comment=str(getattr(record, "comment", "") or ""),
            ))
    return samples


def analysis_counts(samples: list[StructureSample]) -> dict[str, int]:
    """Compteurs d'analyse (l'écran de v1 ne suppose jamais une orientation)."""
    counts = {
        "total": len(samples),
        "planar": 0,
        "linear": 0,
        "composite": 0,
        "non_orientable": 0,
        "unknown": 0,
        "oriented": 0,
        "no_orientation": 0,
        "alpha_beta_only": 0,
    }
    for sample in samples:
        family = sample_family(sample)
        if family == "planar":
            counts["planar"] += 1
        elif family == "linear":
            counts["linear"] += 1
        elif family == "composite":
            counts["composite"] += 1
        elif family == "non_orientable":
            counts["non_orientable"] += 1
        else:
            counts["unknown"] += 1

        if is_alpha_beta_only(sample):
            counts["alpha_beta_only"] += 1
        if resolve_orientation(sample) is None:
            counts["no_orientation"] += 1
        else:
            counts["oriented"] += 1
    return counts


_POLE_DENSITY_DEFAULT_GRID = 64
_POLE_DENSITY_DEFAULT_BLUR = 2
_POLE_DENSITY_EPSILON = 1e-9


def pole_density_grid(
    unit_points,
    grid_size: int = _POLE_DENSITY_DEFAULT_GRID,
    blur_passes: int = _POLE_DENSITY_DEFAULT_BLUR,
) -> list[list[float]]:
    """Densité de pôles sur le disque unité — grille lisse, sans dépendance.

    `unit_points` = itérables ``(ux, uy)`` déjà projetés (projet Schmidt
    hémisphère inférieur), ``ux⊥uy`` dans le disque unité (Est→droite,
    Nord→haut).  La fonction retourne une matrice ``grid_size x grid_size``
    de valeurs 0..1 (sans décor 0, indice 0 = ligne Nord/haut).

    Méthode : histogramme 2D + ``blur_passes`` passages d'un noyau box
    3×3, puis masque hors disque et normalisation au max.  C'est volontairement
    une approximation légère (aucun numpy/scipy) mais très rapide même à
    5000 pôles.
    """
    if grid_size <= 0:
        raise ValueError("grid_size doit être strictement positif")
    if blur_passes < 0:
        raise ValueError("blur_passes doit être >= 0")

    counts = [[0.0] * grid_size for _ in range(grid_size)]
    denom = float(grid_size - 1)
    for point in unit_points:
        ux = float(point[0])
        uy = float(point[1])
        if ux * ux + uy * uy > 1.0:
            continue
        ix = int((ux * 0.5 + 0.5) * denom + 0.5)
        # indice 0 = Nord (uy = +1)
        iy = int(((1.0 - uy) * 0.5) * denom + 0.5)
        ix = max(0, min(grid_size - 1, ix))
        iy = max(0, min(grid_size - 1, iy))
        counts[iy][ix] += 1.0

    for _ in range(blur_passes):
        previous = [row[:] for row in counts]
        for iy in range(grid_size):
            for ix in range(grid_size):
                acc = 0.0
                used = 0
                for dy in (-1, 0, 1):
                    yy = iy + dy
                    if yy < 0 or yy >= grid_size:
                        continue
                    for dx in (-1, 0, 1):
                        xx = ix + dx
                        if xx < 0 or xx >= grid_size:
                            continue
                        acc += previous[yy][xx]
                        used += 1
                counts[iy][ix] = acc / float(used) if used else 0.0

    # Masque hors disque (les bords de la grille carrée)
    center = (grid_size - 1) / 2.0
    radius = float(grid_size - 1) / 2.0
    radius_sq = radius * radius
    for iy in range(grid_size):
        yy = (iy - center) / radius if radius else 0.0
        for ix in range(grid_size):
            xx = (ix - center) / radius if radius else 0.0
            # Tolérance de bord : une cellule cardinale au bord du disque
            # doit rester visible (sinon N/E/S/O disparaissent de la heatmap).
            if xx * xx + yy * yy > 1.05:
                counts[iy][ix] = 0.0

    maximum = max(max(row) for row in counts) if counts else 0.0
    if maximum <= _POLE_DENSITY_EPSILON:
        return [[0.0] * grid_size for _ in range(grid_size)]
    return [[value / maximum for value in row] for row in counts]
