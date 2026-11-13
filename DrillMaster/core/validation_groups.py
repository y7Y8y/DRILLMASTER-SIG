"""
DrillMaster — Regroupement des problèmes de validation (v2.7.6, VAL-01)
=======================================================================

Remarque utilisateur : « des milliers de messages étouffent le panneau ».
Réponse : le panneau de validation affiche **une ligne par type de
problème** avec son compteur exact (« FROM ≥ TO — 342 occurrences »), un
filtre par gravité, et chaque ligne mène à la première cellule fautive
dans l'éditeur CSV. Le détail complet reste disponible dans l'éditeur ;
rien n'est jamais tronqué silencieusement (le panneau annonce
« … et N autres types » quand il borne son affichage).

Pure Python, sans Qt ni QGIS — testable hors QGIS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Libellés courts et stables par code de problème (clé = ValidationIssue.code)
# ---------------------------------------------------------------------------
GROUP_LABELS: dict[str, str] = {
    "ASSAY_LONG_FORMAT_NOT_ENABLED": "Structure longue des teneurs non prise en charge",
    "ASSAY_TEXT_COLUMNS_IGNORED": "Colonnes de métadonnées texte ignorées comme éléments",
    "ASSAY_CENSORED_VALUES": "Valeurs censurées (seuil de détection) conservées",
    "ASSAY_UNREADABLE_VALUES": "Valeurs non numériques ignorées dans une colonne de teneur",
    "QAQC_SAMPLES_SET_ASIDE": "Lignes de contrôle qualité (blancs, standards, duplicatas) écartées des teneurs",
    "AUTO_VERTICAL_SURVEY": "Trajectoire verticale automatique",
    "AZIMUTH_OUT_OF_RANGE": "Azimut hors plage [0–360]",
    "COMPOSITE_VALUE_PRESERVED": "Valeur composite conservée telle quelle",
    "DIP_OUT_OF_RANGE": "Pendage hors plage [-90–90]",
    "DUPLICATE_COLLAR_POSITION": "Positions de collets très proches",
    "DUPLICATE_COMPONENT": "Composant en double dans l'intervalle",
    "DUPLICATE_COMPONENT_COLUMN": "Colonne utilisée par plusieurs composants",
    "DUPLICATE_HOLE_ID": "Identifiant de forage en double",
    "DUPLICATE_INTERVAL": "Intervalles identiques",
    "DUPLICATE_MAPPING": "Deux colonnes associées au même champ",
    "DUPLICATE_SURVEY_DEPTH": "Profondeur de déviation répétée",
    "EMPTY_DELIMITED_COMPONENT": "Code vide dans une valeur séparée",
    "EMPTY_HOLE_ID": "Identifiant de forage vide",
    "EMPTY_LITHOLOGY": "Code lithologique vide",
    "EMPTY_NUMERIC_VALUE": "Valeur numérique vide",
    "FROM_GE_TO": "FROM supérieur ou égal à TO",
    "INTERVAL_BEYOND_HOLE_DEPTH": "Intervalle au-delà de la profondeur du forage",
    "INVALID_ASSAY_VALUE": "Teneur non numérique",
    "INVALID_NUMBER": "Valeur numérique illisible",
    "INVALID_PROPORTION": "Proportion non numérique",
    "LITHOLOGY_COLUMN_MISSING": "Colonne de lithologie manquante",
    "LONG_FORMAT_RETIRED": "Format long retiré (règle du projet : large uniquement)",
"LONG_COMPONENT_COLUMN_MISSING": "Colonne de code manquante (format long)",
    "MULTIPLE_PRIMARY_COMPONENTS": "Plusieurs composants principaux",
    "NEGATIVE_FROM": "FROM négatif",
    "NEGATIVE_SURVEY_DEPTH": "Profondeur de déviation négative",
    "NON_POSITIVE_DEPTH": "Profondeur totale nulle ou négative",
    "PRIMARY_INTERVAL_GAP": "Trou entre intervalles",
    "PRIMARY_INTERVAL_OVERLAP": "Recouvrement d'intervalles",
    "PROPORTION_OUT_OF_RANGE": "Proportion hors plage",
    "PROPORTION_SUM_OVER_100": "Somme des proportions > 100 %",
    "PROPORTION_SUM_UNDER_100": "Somme des proportions < 100 %",
    "REQUIRED_MAPPING_MISSING": "Colonne obligatoire non associée",
    "ROW_WIDTH_MISMATCH": "Nombre de cellules différent de l'en-tête",
    "SIMILAR_HOLE_IDS": "Identifiants de forages presque identiques",
    "STERILE_WITH_MINERALS": "Intervalle « stérile » avec minéraux déclarés",
    "SURVEY_BEYOND_HOLE_DEPTH": "Station au-delà de la profondeur totale",
    "SURVEY_DOES_NOT_START_AT_ZERO": "Première station de déviation après 0",
    "UNKNOWN_COMPONENT_ROLE": "Rôle de composant non reconnu (conservé)",
    "UNKNOWN_HOLE_ID": "Forage absent du fichier Collets",
    "UNKNOWN_PROPORTION_UNIT": "Unité de proportion inconnue",
    "UNSORTED_SURVEY": "Stations de déviation non triées",
    "WIDE_COMPONENTS_MISSING": "Aucun groupe de composants (format large)",
    # Geotech group — RQD / recovery / density (v2.9.264)
    "GEOTECH_FROM_GT_TO": "FROM supérieur à TO en géotechnique",
    "GEOTECH_MISSING_INTERVAL": "Bornes FROM/TO manquantes en géotechnique",
    "GEOTECH_MISSING_DEPTH_OR_INTERVAL": "Profondeur ou bornes manquantes en géotechnique",
    "GEOTECH_VALUE_OUT_OF_RANGE": "Valeur géotechnique hors plage physique",
    "GEOTECH_DEPTH_OUTSIDE_HOLE": "Profondeur géotechnique au-delà du forage",
    "GEOTECH_DUPLICATE": "Mesure géotechnique dupliquée",
    "GEOTECH_MIXED_DEPTH_INTERVAL": "Profondeur et bornes mélangées (mode ponctuel conservé)",
    "GEOTECH_UNKNOWN_UNIT": "Unité géotechnique inconnue",
    "GEOTECH_UNUSUAL_DENSITY": "Densité inhabituelle (non bloquante)",
    "GEOTECH_RQD_GT_RECOVERY": "RQD supérieur à la récupération de carotte",
    # Structure point-wise domain (v2.9.258)
    "EMPTY_STRUCTURE_TYPE": "Type de structure vide",
    "UNKNOWN_STRUCTURE_TYPE": "Type de structure non préconnu",
    "INCOMPLETE_DIP_PAIR": "Paire pendage / direction incomplète",
    "INCOMPLETE_ALPHA_BETA_PAIR": "Paire alpha / bêta incomplète",
    "NO_STRUCTURE_ORIENTATION": "Aucune orientation de structure",
    "DUPLICATE_STRUCTURE": "Mesure de structure dupliquée",
    "STRUCTURE_DIP_OUT_OF_RANGE": "Pendage de structure hors plage [0–90]",
    "STRUCTURE_DIP_DIRECTION_OUT_OF_RANGE": "Direction du pendage hors plage [0–360]",
    "NEGATIVE_STRUCTURE_DEPTH": "Profondeur de structure négative",
    "STRUCTURE_BEYOND_HOLE_DEPTH": "Mesure au-delà de la profondeur totale",
    # Messages historiques sans code structuré : regroupés par texte.
    "LEGACY_ERROR": "Erreur",
    "LEGACY_WARNING": "Avertissement",
    "INFO": "Information",
}

_SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
SEVERITY_LABELS = {
    "error": "erreur", "warning": "avertissement", "info": "information"}

# Nombre de types affichés par fichier avant le bornage « … et N autres ».
MAX_GROUPS_SHOWN = 12


@dataclass
class IssueGroup:
    """Un type de problème + le nombre exact d'occurrences."""

    file_type: str
    severity: str
    code: str
    label: str
    count: int
    sample_message: str = ""
    suggestion: str = ""
    locations: list[dict] = field(default_factory=list)

    @property
    def headline(self) -> str:
        if self.count <= 1:
            return self.label
        return f"{self.label} — {self.count} occurrence(s)"

    @property
    def first_location(self) -> tuple[Optional[int], Optional[int]]:
        for location in self.locations:
            if location.get("row") is not None:
                return location.get("row"), location.get("column")
        return None, None


def _group_key(issue) -> tuple:
    code = getattr(issue, "code", "") or "INFO"
    # The historical text lists (errors/warnings without codes) share one
    # LEGACY_* code; regroup them on their message, not on the placeholder.
    if code.startswith("LEGACY_"):
        return (issue.file_type, issue.severity, "LEGACY", issue.message)
    return (issue.file_type, issue.severity, code)


def group_issues(issues: list, labels: Optional[dict] = None) -> list[IssueGroup]:
    """Regroup validation issues per (file, severity, code).

    Order: errors first, then warnings, then info; within each severity the
    most frequent problems come first. Counts are always exact.
    """
    labels = GROUP_LABELS if labels is None else labels
    buckets: dict[tuple, list] = {}
    for issue in issues:
        buckets.setdefault(_group_key(issue), []).append(issue)

    groups: list[IssueGroup] = []
    for (_file_type, severity, _code, *_rest), bucket in buckets.items():
        first = bucket[0]
        code = first.code or "INFO"
        label = labels.get(code, code.replace("_", " ").capitalize())
        if code.startswith("LEGACY_"):
            label = first.message
        locations: list[dict] = []
        for issue in bucket:
            locations.extend(issue.locations or [])
        groups.append(IssueGroup(
            file_type=first.file_type,
            severity=severity,
            code=code,
            label=label,
            count=len(bucket),
            sample_message=first.message,
            suggestion=getattr(first, "suggestion", "") or "",
            locations=locations))

    groups.sort(key=lambda group: (
        _SEVERITY_ORDER.get(group.severity, 3), -group.count, group.label))
    return groups


def filter_by_severity(groups: list[IssueGroup], severity: str) -> list[IssueGroup]:
    """``severity`` : 'all', 'error', 'warning' ou 'info'."""
    if severity in ("all", "", None):
        return list(groups)
    return [group for group in groups if group.severity == severity]


def cap_groups(groups: list[IssueGroup],
               max_shown: int = MAX_GROUPS_SHOWN) -> tuple[list[IssueGroup], int, int]:
    """Bound the display while keeping totals exact.

    Returns ``(shown, hidden_groups, hidden_occurrences)`` — the caller MUST
    display the hidden figures whenever they are non-zero (never truncate
    silently).
    """
    if len(groups) <= max_shown:
        return list(groups), 0, 0
    shown = list(groups[:max_shown])
    rest = groups[max_shown:]
    return shown, len(rest), sum(group.count for group in rest)


def count_by_severity(groups: list[IssueGroup]) -> dict[str, int]:
    totals = {"error": 0, "warning": 0, "info": 0}
    for group in groups:
        totals[group.severity] = totals.get(group.severity, 0) + group.count
    return totals


# ---------------------------------------------------------------------------
# v2.7.6.2 (VAL-02) — le filtre s'applique à TOUT le panneau
# ---------------------------------------------------------------------------
# Revue écran du 18/08/2026 : « tu es sur erreurs et tu vois ceux qui sont
# corrects, pourquoi ? ». Les lignes de succès (« ✅ Teneurs : 342
# intervalles ») sont des informations : elles ne doivent apparaître que
# lorsque les informations sont demandées. Le bornage « … et N autres »
# doit lui aussi porter la gravité filtrée, sinon une ligne bleue
# réapparaît au milieu d'une liste d'erreurs.

SEVERITY_FILTERS: tuple[tuple[str, str], ...] = (
    ("Tout afficher", "all"),
    ("Erreurs seules", "error"),
    ("Avertissements seuls", "warning"),
    ("Informations seules", "info"),
)

_SEVERITY_NOUNS = {
    "error": ("type(s) d'erreur", "erreur(s)"),
    "warning": ("type(s) d'avertissement", "avertissement(s)"),
    "info": ("type(s) d'information", "information(s)"),
}


def normalise_severity(severity) -> str:
    """'all' pour toute valeur non reconnue (jamais d'exception UI)."""
    if severity in ("error", "warning", "info"):
        return severity
    return "all"


def show_info_lines(severity) -> bool:
    """Les lignes d'information ne survivent qu'aux filtres qui les demandent."""
    return normalise_severity(severity) in ("all", "info")


def overflow_summary(hidden_groups: int, hidden_occurrences: int,
                     severity="all") -> tuple[str, str]:
    """Ligne « … et N autres types » : gravité et vocabulaire cohérents.

    Renvoie ``(severity_of_row, text)``. La gravité de la ligne suit le
    filtre actif afin de ne jamais réintroduire une ligne d'information
    dans une liste filtrée sur les erreurs.
    """
    if hidden_groups <= 0:
        return normalise_severity(severity), ""
    key = normalise_severity(severity)
    types_word, occ_word = _SEVERITY_NOUNS.get(
        key, ("type(s) de problème", "occurrence(s)"))
    row_severity = key if key != "all" else "info"
    return row_severity, (
        f"… et {hidden_groups} autre(s) {types_word} — "
        f"{hidden_occurrences} {occ_word} au total pour ce fichier")


def filter_labels(totals: dict) -> list[tuple[str, str]]:
    """Libellés du sélecteur enrichis du compte exact par gravité."""
    totals = totals or {}
    labels: list[tuple[str, str]] = []
    for label, key in SEVERITY_FILTERS:
        if key == "all":
            total = sum(int(totals.get(name, 0))
                        for name in ("error", "warning", "info"))
        else:
            total = int(totals.get(key, 0))
        labels.append((f"{label} ({total})" if total else label, key))
    return labels
