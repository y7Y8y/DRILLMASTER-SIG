"""
DrillMaster ORIG — validation par nature (pur, testé standalone).

Taxonomie IA_AUDIT.md : support × nature. Le SOCLE commun valide ce qui
est vrai pour tout enregistrement ancré en profondeur ; les validateurs
spécialisés ajoutent ce que leur NATURE exige :
  - codé       → le code existe dans le référentiel du domaine
  - quantitatif → valeurs numériques, unités déclarées, QA/QC
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .model import Interval


@dataclass(frozen=True, slots=True)
class ElementSpec:
    """Un élément mesuré : nom, unité, limites de détection optionnelles."""

    name: str
    unit: str
    lower_dl: Optional[float] = None
    upper_dl: Optional[float] = None


@dataclass(slots=True)
class ValidationReport:
    """Erreurs bloquantes + avertissements, prêts pour l'UI (français)."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def blocking(self) -> bool:
        return bool(self.errors)

    def extend(self, other: "ValidationReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def _overlap_pairs(records: list[Interval]) -> list[tuple[Interval, Interval]]:
    """Paires d'intervalles qui se recouvrent (même trou, tri par from)."""
    ordered = sorted(records, key=lambda r: (r.hole_id, r.from_depth))
    pairs = []
    for a, b in zip(ordered, ordered[1:]):
        if a.hole_id == b.hole_id and b.from_depth < a.to_depth:
            pairs.append((a, b))
    return pairs


def validate_depth_anchored(
    records: list[Interval],
    known_hole_ids: set[str] | None = None,
) -> ValidationReport:
    """SOCLE : trou connu, bornes cohérentes, recouvrements signalés."""
    report = ValidationReport()
    for r in records:
        if known_hole_ids is not None and r.hole_id not in known_hole_ids:
            report.errors.append(
                f"{r.hole_id} · trou inconnu (ligne {r.source_row})")
        if r.from_depth < 0:
            report.errors.append(
                f"{r.hole_id} · from négatif ({r.from_depth}, "
                f"ligne {r.source_row})")
        if r.to_depth <= r.from_depth:
            report.errors.append(
                f"{r.hole_id} · to <= from ({r.from_depth}→{r.to_depth}, "
                f"ligne {r.source_row})")
    for a, b in _overlap_pairs(records):
        report.warnings.append(
            f"{a.hole_id} · recouvrement {a.from_depth}→{a.to_depth} / "
            f"{b.from_depth}→{b.to_depth}")
    return report


def validate_coded_log(
    records: list[Interval],
    referential_codes: set[str],
    known_hole_ids: set[str] | None = None,
) -> ValidationReport:
    """NATURE codée : le socle + l'existence du code en référentiel."""
    report = validate_depth_anchored(records, known_hole_ids)
    for r in records:
        if r.code and r.code not in referential_codes:
            report.errors.append(
                f"{r.hole_id} · code « {r.code} » absent du référentiel "
                f"« {r.domain} » (ligne {r.source_row})")
    return report


def validate_assays(
    records: list[Interval],
    elements: dict[str, ElementSpec],
    values_by_row: dict[int, dict[str, str]],
    known_hole_ids: set[str] | None = None,
) -> ValidationReport:
    """NATURE quantitative : le socle + valeurs numériques, unités, QA/QC.

    ``values_by_row`` : ligne source -> {élément: valeur brute}. Une valeur
    vide est admise (absence d'analyse) ; une valeur non numérique est une
    erreur ; sous la limite de détection : avertissement.
    """
    report = validate_depth_anchored(records, known_hole_ids)
    for r in records:
        row_values = values_by_row.get(r.source_row, {})
        for element, raw in row_values.items():
            spec = elements.get(element)
            if spec is None:
                report.errors.append(
                    f"{r.hole_id} · élément « {element} » non déclaré "
                    f"(ligne {r.source_row})")
                continue
            text = (raw or "").strip().replace(",", ".")
            if not text:
                continue
            try:
                value = float(text)
            except ValueError:
                report.errors.append(
                    f"{r.hole_id} · {element}: valeur non numérique "
                    f"« {raw} » (ligne {r.source_row})")
                continue
            if value < 0:
                report.errors.append(
                    f"{r.hole_id} · {element}: concentration négative "
                    f"({raw}, ligne {r.source_row})")
            elif spec.lower_dl is not None and value < spec.lower_dl:
                report.warnings.append(
                    f"{r.hole_id} · {element}: {raw} sous la limite de "
                    f"détection ({spec.lower_dl} {spec.unit})")
            elif spec.upper_dl is not None and value > spec.upper_dl:
                report.warnings.append(
                    f"{r.hole_id} · {element}: {raw} au-dessus de la "
                    f"limite haute ({spec.upper_dl} {spec.unit})")
    return report
