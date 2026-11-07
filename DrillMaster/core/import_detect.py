"""
DrillMaster — Détection automatique du type de fichier (v2.7.6, IMP-01)
========================================================================

L'utilisateur dépose un dossier ou des fichiers nommés arbitrairement ;
le plugin reconnaît le type de chaque fichier par la **signature de ses
en-têtes** (et, pour les teneurs, par le contenu numérique des colonnes
non reconnues) puis le place dans le bon onglet de l'étape 2.

Règles du projet respectées :
- détection **annoncée** (chaque répartition donne ses raisons) ;
- en cas de doute réel entre deux types, le fichier est marqué
  « ambigu » avec les deux candidats — jamais de placement silencieux
  sans recours ;
- aucune valeur source n'est modifiée : on ne lit que les en-têtes et un
  échantillon de lignes.

Pure Python, sans Qt ni QGIS — testable hors QGIS.
"""

from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass, field
from typing import Optional

from .csv_parser import detect_encoding, detect_separator, header_match_details

# ---------------------------------------------------------------------------
# Signatures d'en-têtes par type de fichier
# ---------------------------------------------------------------------------
FILE_TYPE_LABELS = {
    "collar": "Collets",
    "survey": "Déviations",
    "litho": "Lithologie",
    "assays": "Teneurs",
    "alterations": "Altérations",
    "mineralizations": "Minéralisations",
    "structure": "Structures observées",
    "topography": "Topographie",
    "imagery": "Imagerie de trou",
    "rqd": "RQD",
    "recovery": "Récupération",
    "density": "Densité",
}

# Poids des colonnes dans la reconnaissance d'un type : la colonne de
# contenu (lithologie, code d'altération…) pèse le plus lourd.
_COLUMN_WEIGHTS: dict[str, dict[str, float]] = {
    "collar": {
        "hole_id": 3.0, "collar_x": 3.0, "collar_y": 3.0, "collar_z": 1.5,
        "depth": 1.0, "azimuth": 0.5, "dip": 0.5,
    },
    "survey": {
        "hole_id": 3.0, "depth": 2.0, "azimuth": 2.0, "dip": 2.0,
    },
    "litho": {
        "hole_id": 2.0, "from": 2.0, "to": 2.0, "lithology": 3.0,
        "lithology_primary": 2.0, "lithology_secondary": 1.5,
        "lithology_role": 1.0, "lithology_proportion": 1.0,
        "secondary_proportion": 1.0,
    },
    "alterations": {
        "hole_id": 2.0, "from": 2.0, "to": 2.0, "alteration": 3.0,
        "intensity": 1.5,
    },
    "mineralizations": {
        "hole_id": 2.0, "from": 2.0, "to": 2.0, "mineralization_style": 3.0,
        "minerals": 2.5, "intensity": 1.0, "confidence": 1.0,
    },
    "structure": {
        "hole_id": 3.0, "depth": 3.0, "type": 3.0,
        "dip": 1.5, "dip_direction": 2.0, "alpha": 2.0, "beta": 2.0,
        "confidence": 1.0,
    },
    "assays": {
        "hole_id": 2.0, "from": 2.0, "to": 2.0,
    },
    # v2.9.262 — imagerie : id + bornes + chemin image (poids fort),
    # material/orientation restent optionnels.
    "imagery": {
        "hole_id": 2.0, "from": 2.0, "to": 2.0, "image_path": 3.0,
        "material": 1.0, "orientation": 0.5, "comment": 0.5,
    },
    # v2.9.264 — géotechnique groupée (valeurs numériques, pas de code
    # catégoriel : RQD et récup partagent from/to/value, la densité porte
    # depth + unité).
    "rqd": {"hole_id": 2.0, "from": 2.0, "to": 2.0, "value": 3.0,
            "comment": 0.5},
    "recovery": {"hole_id": 2.0, "from": 2.0, "to": 2.0, "value": 3.0,
                 "comment": 0.5},
    "density": {"hole_id": 2.0, "depth": 3.0, "value": 3.0, "unit": 1.5,
                "from": 1.5, "to": 1.5, "comment": 0.5},
    # v2.9.0 — topographie : points x;y;z de la surface (pas de forage).
    "topography": {
        "collar_x": 3.0, "collar_y": 3.0, "collar_z": 3.0,
    },
}

# Score de référence = « fichier typique complet » (identifiant + géométrie
# + la colonne de contenu du domaine). On ne divise pas par la somme de tous
# les poids pour ne pas pénaliser un fichier minimal mais complet.
_REFERENCE_SCORES = {
    "collar": 3.0 + 3.0 + 3.0 + 1.5,     # id + X + Y + Z
    "survey": 3.0 + 2.0 + 2.0,           # id + prof + azimut
    "litho": 2.0 + 2.0 + 2.0 + 3.0,      # id + from + to + code
    "alterations": 2.0 + 2.0 + 2.0 + 3.0,
    "mineralizations": 2.0 + 2.0 + 2.0 + 3.0,
    "structure": 3.0 + 3.0 + 3.0,        # id + prof + type (mesures ponctuelles)
    "assays": 2.0 + 2.0 + 2.0 + 3.0,     # id + from + to + colonnes chiffrées
    "imagery": 2.0 + 2.0 + 2.0 + 3.0,    # id + from + to + chemin image
    "rqd": 2.0 + 2.0 + 2.0 + 3.0,       # id + from + to + value
    "recovery": 2.0 + 2.0 + 2.0 + 3.0,  # id + from + to + value
    "density": 2.0 + 2.0 + 3.0 + 1.5,   # id + depth + value + unit
    "topography": 3.0 + 3.0 + 3.0,       # x + y + z (pas d'identifiant)
}

# Colonnes obligatoires de la signature : des coordonnées X+Y excluent une
# déviation ; FROM/TO excluent un collet…
_REQUIRED_ALL = {
    "collar": ("collar_x", "collar_y"),
    "survey": ("depth",),
    "litho": ("from", "to"),
    "alterations": ("from", "to"),
    "mineralizations": ("from", "to"),
    "structure": ("depth", "type"),
    "assays": ("from", "to"),
    "imagery": ("from", "to", "image_path"),
    # v2.9.264 — géotechnique : une colonne valeur + un mode de profondeur
    # (from/to pour RQD/CR ; depth OU from/to pour densité).
    "rqd": ("from", "to", "value"),
    "recovery": ("from", "to", "value"),
    "density": ("value",),
    # v2.9.0 — topographie : X+Y+Z SANS identifiant de forage (présence
    # d'un hole_id la disqualifie : c'est un fichier de forage).
    "topography": ("collar_x", "collar_y", "collar_z"),
}
# Certaines signatures acceptent une alternative (déviation : azimut OU
# pendage — une deviation peut n'être mesurée que d'une seule façon).
_REQUIRED_ANY_OF = {
    "survey": ("azimuth", "dip"),
}

# Bonus maximal des colonnes numériques non reconnues (signature des
# teneurs : AU_PPM, CU_PCT…) — borne éviter qu'un fichier litho avec une
# colonne de longueur ne bascule en teneurs.
_ASSAY_NUMERIC_BONUS = 3.0
# Un score ≥ ce seuil → le fichier part dans l'onglet sans question.

# ---------------------------------------------------------------------------
# v2.7.10.37 — CM-01 : organisation « LARGE » hors lithologie (registre
# arbitré le 20/08/2026 — fichiers terrain avec alt1/alt2/int1/int2,
# min1/min2, ou cellule « SIL/EPI/HE »). Détection HONNÊTE uniquement :
# on repère des colonnes candidates (alias du domaine + suffixe chiffré),
# on ne décide jamais à la place de l'utilisateur.
# ---------------------------------------------------------------------------
_WIDE_BASE_ALIASES = {
    "alterations": ("alt", "alteration"),
    "mineralizations": ("style", "mineralisation", "mineralization"),
}
_WIDE_INTENSITY_ALIASES = ("int", "intens")
# CM-01 (clarification écran 20/08/2026) : « min1/min2 » sont des colonnes
# de MINÉRAUX — elles nourrissent la liste « Minéraux » de l'intervalle
# (infobulle), JAMAIS la bande de style (AM-05). Seules les colonnes de
# style (Style1, Style_Mineralisation_2…) sont des composants.
_WIDE_MINERALS_ALIASES = ("min",)


def detect_wide_component_columns(raw_headers, file_type):
    """Repère les colonnes candidates d'une organisation large.

    Une colonne est candidate si son « socle » contient un alias du domaine
    ET qu'elle se termine par un groupe de chiffres (Alt1, Alt_2,
    Style 1, Style_Mineralisation_2…). Les colonnes d'intensité (alias
    ``int``) servent à l'appairage par suffixe (Int1 ≡ Alt1). Colonnes de
    minéraux (alias ``min`` + chiffre) rapportées à part pour nourrir
    « Minéraux » — jamais des styles.

    Retourne ``(component_candidates, intensity_candidates,
    minerals_candidates)``, chacun sous la forme ``[(header, suffix)]`` —
    jamais de décision.
    """
    import re
    bases = _WIDE_BASE_ALIASES.get(file_type, ())
    if not bases:
        return [], [], []
    component_candidates = []
    intensity_candidates = []
    minerals_candidates = []
    for header in raw_headers or []:
        folded = str(header).strip().casefold()
        match = re.match(r"^(.*?)[_\- ]?([0-9]+)$", folded)
        if not match:
            continue
        base = match.group(1).strip("_- ")
        suffix = match.group(2)
        if any(alias in base for alias in _WIDE_INTENSITY_ALIASES):
            intensity_candidates.append((header, suffix))
            continue
        if (file_type == "mineralizations"
                and any(base.startswith(alias) or base.endswith(alias)
                        for alias in _WIDE_MINERALS_ALIASES)
                and not any(alias in base for alias in bases)):
            minerals_candidates.append((header, suffix))
            continue
        if any(alias in base for alias in bases):
            component_candidates.append((header, suffix))
    for bucket in (component_candidates, intensity_candidates,
                   minerals_candidates):
        bucket.sort(key=lambda pair: (pair[1], str(pair[0])))
    if len(component_candidates) < 2:
        return [], intensity_candidates, minerals_candidates
    return component_candidates, intensity_candidates, minerals_candidates


_CONFIDENT_SCORE = 0.55
# Deux candidats séparés de moins que cette marge → ambiguïté déclarée.
_AMBIGUITY_MARGIN = 0.12

_REASON_LABELS = {
    "hole_id": "identifiant de forage",
    "collar_x": "coordonnée X",
    "collar_y": "coordonnée Y",
    "collar_z": "altitude Z",
    "depth": "profondeur",
    "azimuth": "azimut",
    "dip": "pendage",
    "from": "FROM",
    "to": "TO",
    "lithology": "colonne lithologie",
    "lithology_primary": "lithologie principale",
    "lithology_secondary": "lithologie secondaire",
    "lithology_role": "rôle du composant",
    "lithology_proportion": "proportion",
    "secondary_proportion": "proportion secondaire",
    "alteration": "colonne altération",
    "intensity": "intensité",
    "mineralization_style": "style de minéralisation",
    "minerals": "minéraux",
    "confidence": "confiance",
    "type": "type de structure",
    "dip_direction": "direction du pendage",
    "alpha": "angle alpha",
    "beta": "angle bêta",
    "comment": "commentaire",
    # v2.9.262 — imagerie : le libellé manquait et faisait planter la
    # détection automatique (KeyError) dès qu'un imagery.csv était proposé.
    "image_path": "chemin photo/scan",
    "material": "matériau",
    "orientation": "orientation de l'image",
    "value": "valeur numérique",
    "unit": "unité de mesure",
    # v2.9.264 — géotechnique (labels de raison de détection).
}

# Indices de nom de fichier (n'ouvrent jamais une porte seuls, +0,05
# maximum, pour départager deux scores proches).
_FILENAME_HINTS = {
    "collar": ("collar", "collet"),
    "survey": ("survey", "deviation", "déviation", "sondage_dev"),
    "litho": ("litho", "geolog", "géolog"),
    "alterations": ("alter", "altér"),
    "mineralizations": ("mineral", "minéral"),
    "structure": ("structure", "struct", "discontinu", "mesure_struct"),
    "assays": ("assay", "teneur", "analys", "echantill", "échantill"),
    "topography": ("topo", "mnt", "dem", "élev", "ele", "surface"),
    "imagery": ("imag", "image", "photo", "scan", "carotte", "core_img"),
    "rqd": ("rqd", "rock_quality", "rock_quality_designation",
            "qualite_roche", "qualité_roche"),
    "recovery": ("recovery", "recup", "recuperation", "récupération",
                 "carotte_recovery", "core_recovery"),
    "density": ("density", "densite", "densité", "rho", "specific_gravity",
                "poids_volumique"),
}


@dataclass
class FileTypeGuess:
    """Résultat de la détection d'un type de fichier."""

    file_type: Optional[str] = None
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)
    alternatives: list[tuple[str, float]] = field(default_factory=list)
    ambiguous: bool = False
    error: str = ""
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def confident(self) -> bool:
        return (
            self.file_type is not None
            and self.confidence >= _CONFIDENT_SCORE
            and not self.ambiguous)

    @property
    def label(self) -> str:
        return FILE_TYPE_LABELS.get(self.file_type, "?") if self.file_type else "?"


@dataclass
class FileSample:
    """En-têtes + premières lignes, lus une seule fois par fichier."""

    path: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    encoding: str = "utf-8"
    separator: str = ";"
    error: str = ""


def read_header_sample(path: str, max_rows: int = 30) -> FileSample:
    """Read only the first rows of a CSV — never loads the whole file."""
    sample = FileSample(path=path)
    if not os.path.isfile(path):
        sample.error = f"Fichier introuvable : {path}"
        return sample
    try:
        sample.encoding = detect_encoding(path)
        with open(path, "r", encoding=sample.encoding, newline="") as handle:
            text = handle.read(16384)
    except (OSError, UnicodeDecodeError) as exc:
        sample.error = f"Lecture impossible : {exc}"
        return sample
    lines = text.splitlines()
    if not lines:
        sample.error = "Fichier vide."
        return sample
    sample.separator = detect_separator(lines[:20])
    try:
        reader = csv.reader(io.StringIO(text), delimiter=sample.separator)
        rows = list(reader)
    except csv.Error as exc:
        sample.error = f"Lecture impossible : {exc}"
        return sample
    if not rows or not any(cell.strip() for cell in rows[0]):
        sample.error = "Fichier vide."
        return sample
    sample.headers = [cell.strip() for cell in rows[0]]
    sample.rows = [row for row in rows[1:max_rows + 1] if any(
        cell.strip() for cell in row)]
    if not sample.rows:
        sample.error = "Aucune ligne de données sous l'en-tête."
    return sample


def _match_headers(headers: list[str], extra_synonyms=None) -> dict[str, float]:
    """Best match confidence per canonical (each canonical counted once)."""
    matched: dict[str, float] = {}
    for header in headers:
        if not header:
            continue
        details = header_match_details(header, extra_synonyms=extra_synonyms)
        canonical = details.get("canonical")
        confidence = float(details.get("confidence", 0.0))
        if canonical and confidence > matched.get(canonical, 0.0):
            matched[canonical] = confidence
    return matched


def _numeric_fraction(rows: list[list[str]], index: int) -> float:
    """Share of non-empty cells of column `index` that parse as numbers."""
    values = [row[index].strip() for row in rows
              if index < len(row) and row[index].strip()]
    if not values:
        return 0.0
    numeric = 0
    for value in values:
        text = value.replace(",", ".")
        try:
            float(text)
            numeric += 1
        except ValueError:
            # Not a number: it just does not count towards the share.
            pass
    return numeric / len(values)


def _numeric_extra_columns(sample: FileSample, matched_headers: set[str]) -> int:
    """Count unrecognised columns whose content is mostly numbers."""
    count = 0
    for index, header in enumerate(sample.headers[:64]):
        if not header or header in matched_headers:
            continue
        if _numeric_fraction(sample.rows, index) >= 0.8:
            count += 1
    return count


def _gates_ok(
        file_type: str, matched: dict[str, float],
        gate_confidence: float) -> bool:
    """Mandatory signature columns for the type (with real confidence)."""
    if file_type == "topography":
        # v2.9.0 — points de surface x;y;z : l'identifiant de forage est
        # un signal NÉGATIF (un fichier avec hole_id est un fichier de
        # forage — la signature X+Y+Z seule ne suffit pas).
        if matched.get("hole_id", 0.0) >= gate_confidence:
            return False
        return all(
            matched.get(canonical, 0.0) >= gate_confidence
            for canonical in ("collar_x", "collar_y", "collar_z"))
    if file_type == "survey" and (
            matched.get("collar_x", 0.0) >= gate_confidence
            and matched.get("collar_y", 0.0) >= gate_confidence):
        return False  # X+Y présents → collets, pas déviations
    # v2.9.258 — structures : une colonne « type » n'est pas une station
    # de déviation, même si Dip est présent (la déviation ne porte jamais
    # le type d'une structure).
    if file_type == "survey" and matched.get("type", 0.0) >= gate_confidence:
        return False
    # v2.9.258 — structures : dommaine ponctuel, jamais un intervalle.
    if file_type == "structure" and (
            matched.get("from", 0.0) >= gate_confidence
            or matched.get("to", 0.0) >= gate_confidence):
        return False
    if matched.get("hole_id", 0.0) < gate_confidence:
        return False
    if not all(
            matched.get(canonical, 0.0) >= gate_confidence
            for canonical in _REQUIRED_ALL[file_type]):
        return False
    any_of = _REQUIRED_ANY_OF.get(file_type)
    if any_of and not any(
            matched.get(canonical, 0.0) >= gate_confidence
            for canonical in any_of):
        return False
    return True


def guess_file_type(
        headers: list[str], rows=None,
        file_name: str = "", extra_synonyms=None) -> FileTypeGuess:
    """Guess the DrillMaster file type from a header signature.

    ``rows`` (optional first data lines) only feeds the assays signature
    (unrecognised **numeric** columns). ``file_name`` is a weak tie-break.
    """
    guess = FileTypeGuess()
    headers = [header.strip() for header in headers if header and header.strip()]
    if not headers:
        guess.error = "Aucune en-tête exploitable."
        return guess

    matched = _match_headers(headers, extra_synonyms=extra_synonyms)
    if not matched:
        guess.error = "Aucune colonne reconnue dans l'en-tête."
        guess.ambiguous = True
        guess.alternatives = []
        return guess

    gate_confidence = 0.6
    matched_headers = {
        header for header in headers
        if header_match_details(header, extra_synonyms=extra_synonyms)
        .get("canonical")
    }
    numeric_extras = (
        _numeric_extra_columns(
            FileSample(
                path="", headers=headers, rows=list(rows or [])),
            matched_headers)
        if rows else 0)

    scores: dict[str, float] = {}
    reasons_by_type: dict[str, list[str]] = {}
    for file_type, weights in _COLUMN_WEIGHTS.items():
        if not _gates_ok(file_type, matched, gate_confidence):
            scores[file_type] = 0.0
            reasons_by_type[file_type] = []
            continue
        raw = sum(
            weight * matched.get(canonical, 0.0)
            for canonical, weight in weights.items())
        reasons = [
            _REASON_LABELS[canonical]
            for canonical in weights
            if matched.get(canonical, 0.0) >= gate_confidence]
        if file_type == "assays":
            raw += min(_ASSAY_NUMERIC_BONUS, float(numeric_extras))
            if numeric_extras:
                reasons.append(
                    f"{numeric_extras} colonne(s) chiffrée(s) non reconnue(s)")
        scores[file_type] = min(1.0, raw / _REFERENCE_SCORES[file_type])
        reasons_by_type[file_type] = reasons

    # Indice de nom de fichier : simple départage, jamais une porte ouverte.
    lowered_name = os.path.basename(file_name).casefold() if file_name else ""
    for file_type, hints in _FILENAME_HINTS.items():
        if scores.get(file_type) and any(
                hint in lowered_name for hint in hints):
            scores[file_type] = min(1.0, scores[file_type] + 0.05)

    ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    best_type, best_score = ranked[0]
    if best_score < _CONFIDENT_SCORE:
        guess.scores = scores
        guess.ambiguous = True
        guess.alternatives = [
            (candidate, score) for candidate, score in ranked
            if score > 0.0]
        guess.error = (
            "Signature trop faible — choisissez l'onglet vous-même.")
        return guess

    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    ambiguous = (
        second_score >= _CONFIDENT_SCORE
        and best_score - second_score < _AMBIGUITY_MARGIN)
    guess.file_type = best_type
    guess.confidence = round(best_score, 3)
    guess.scores = scores
    guess.ambiguous = ambiguous
    # v2.7.11.5 — retour écran (capture « le type hésite ») : en cas
    # d'ambiguïté, le MEILLEUR candidat fait partie des choix proposés,
    # en tête de liste.  Avant, les boutons commençaient au second choix :
    # l'utilisateur devait arbitrer ENTRE LES MAUVAIS TYPES pendant que le
    # plugin connaissait la réponse la plus probable (ex. alteration_Alt
    # → « Altérations » détectée à 72 % mais sans bouton « Altérations »).
    guess.alternatives = (
        [(best_type, best_score)] + [
            (candidate, score) for candidate, score in ranked[1:]
            if score >= _CONFIDENT_SCORE]
        if ambiguous else [])
    guess.reasons = reasons_by_type.get(best_type, [])
    return guess


def detect_file_type(path: str, extra_synonyms=None) -> FileTypeGuess:
    """Full one-shot helper : read a sample then guess the type."""
    sample = read_header_sample(path)
    if sample.error:
        return FileTypeGuess(error=sample.error)
    guess = guess_file_type(
        sample.headers, rows=sample.rows, file_name=os.path.basename(path),
        extra_synonyms=extra_synonyms)
    return guess


def expand_dropped_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    """Expand folders into their CSV/TXT files (sorted, stable).

    Returns ``(files, ignored)`` — ``ignored`` lists what was dropped but
    cannot be an import file (explicit, never silent).
    """
    _accepted = (".csv", ".txt")
    files: list[str] = []
    ignored: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if os.path.isdir(path):
            folder_files = [
                os.path.join(path, name) for name in sorted(os.listdir(path))
                if name.casefold().endswith(_accepted)]
            if not folder_files:
                ignored.append(f"{os.path.basename(path)}/ (aucun CSV)")
            for candidate in folder_files:
                if candidate not in seen:
                    files.append(candidate)
                    seen.add(candidate)
        elif os.path.isfile(path):
            if path.casefold().endswith(_accepted):
                if path not in seen:
                    files.append(path)
                    seen.add(path)
            else:
                ignored.append(os.path.basename(path))
        else:
            ignored.append(f"{os.path.basename(path)} (introuvable)")
    return files, ignored
