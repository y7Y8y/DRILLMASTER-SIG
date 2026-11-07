"""
DrillMaster — CSV Parser with Auto-Detection
=============================================
Detects separator, encoding, decimal separator, and maps headers
using Levenshtein-distance fuzzy matching.

Pure Python (stdlib only) — testable standalone.
"""

from __future__ import annotations

import csv
import os
import re
import shutil
import tempfile
import unicodedata
from typing import Optional

from .data_model import (
    FIELD_SYNONYMS,
    CollarRecord,
    SurveyRecord,
    IntervalRecord,
)

# ---------------------------------------------------------------------------
# Levenshtein distance (iterative, O(n*m) time, O(min(n,m)) space)
# ---------------------------------------------------------------------------
def levenshtein(s1: str, s2: str) -> int:
    """Compute the Levenshtein edit distance between two strings.

    Classic two-row dynamic programming: cell (i, j) is the cost to turn
    ``s1[:i]`` into ``s2[:j]``.  The insertion cost reads the cell to the
    LEFT in the previous row (``previous_row[j + 1]``), the deletion cost
    the cell to the LEFT in the current row, the substitution cost the
    DIAGONAL.  (An earlier revision read ``previous_row[j]`` for insertions,
    which silently destroyed every non-exact similarity score — the fuzzy
    matcher then only ever matched exact normalised synonyms.)
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def _normalise_header(h: str) -> str:
    """Fold case/accents/separators for matching, never for source storage."""
    h = unicodedata.normalize("NFKD", str(h or ""))
    h = "".join(char for char in h if not unicodedata.combining(char))
    h = h.strip().casefold()
    return re.sub(r"[^a-z0-9]", "", h)


# Pre-normalise the synonym lists once at import time
_NORMALISED_SYNONYMS: dict[str, list[str]] = {
    canonical: [_normalise_header(syn) for syn in syns]
    for canonical, syns in FIELD_SYNONYMS.items()
}

# Header vocabulary is shared, but automatic mappings must remain specific to
# the imported dataset. In particular, ``Fe_pct`` is a measured assay column,
# not a lithological proportion merely because it ends with ``pct``.
_ALLOWED_CANONICAL_BY_FILE_TYPE = {
    "collar": {
        "hole_id", "collar_x", "collar_y", "collar_z", "depth",
        "azimuth", "dip"},
    "survey": {"hole_id", "depth", "azimuth", "dip"},
    "litho": {
        "hole_id", "from", "to", "lithology", "lithology_primary",
        "lithology_secondary", "lithology_role",
        "lithology_proportion", "secondary_proportion"},
    "assays": {"hole_id", "from", "to"},
    "alterations": {"hole_id", "from", "to", "alteration", "intensity"},
    "mineralizations": {
        "hole_id", "from", "to", "mineralization_style", "minerals",
        "intensity", "confidence"},
    "structure": {
        "hole_id", "depth", "type", "dip", "dip_direction",
        "alpha", "beta", "confidence", "comment"},
    # v2.9.262 — imagerie : chemin photo/scan obligatoire, étiquettes
    # matériau/orientation et commentaire optionnels.
    "imagery": {
        "hole_id", "from", "to", "image_path", "material",
        "orientation", "comment"},
    # v2.9.264 — géotechnique groupée.  RQD/récupération = intervalles ;
    # densité = depth OU from/to (acceptés pour la commodité).
    "rqd": {"hole_id", "from", "to", "value", "comment"},
    "recovery": {"hole_id", "from", "to", "value", "comment"},
    "density": {"hole_id", "from", "to", "depth", "value", "unit",
                "comment"},
}


def allowed_mapping(file_type: str, canonical: str) -> bool:
    allowed = _ALLOWED_CANONICAL_BY_FILE_TYPE.get(file_type)
    return canonical in allowed if allowed is not None else True


def sanitise_user_mappings(file_type: str, mappings) -> dict[str, str]:
    """Discard stale cross-domain mappings while preserving source headers."""
    return {
        raw: canonical for raw, canonical in (mappings or {}).items()
        if canonical == "" or allowed_mapping(file_type, canonical)
    }


def _merged_synonyms(extra_synonyms=None) -> dict:
    """Built-in synonyms + synonyms learned by the project (v2.7.6).

    A correction made by the user teaches the project: the raw header becomes
    an exact synonym of the chosen canonical field for the next imports.
    """
    if not extra_synonyms:
        return _NORMALISED_SYNONYMS
    merged = {
        canonical: list(synonyms)
        for canonical, synonyms in _NORMALISED_SYNONYMS.items()}
    for canonical, raw_headers in (extra_synonyms or {}).items():
        if not canonical:
            continue
        target = merged.setdefault(canonical, [])
        if isinstance(raw_headers, str):
            raw_headers = [raw_headers]
        for raw_header in raw_headers:
            norm = _normalise_header(str(raw_header))
            if norm and norm not in target:
                target.append(norm)
    return merged


def fuzzy_match_header(raw_header: str, threshold: float = 0.6,
                       extra_synonyms=None) -> Optional[str]:
    """
    Match a raw CSV header to a canonical field name.

    Returns the canonical name if the normalised header matches a synonym
    with similarity >= threshold, otherwise None.

    Similarity = 1 - levenshtein / max(len(a), len(b))
    """
    norm = _normalise_header(raw_header)
    if not norm:
        return None

    best_canonical = None
    best_score = 0.0

    for canonical, synonyms in _merged_synonyms(extra_synonyms).items():
        for syn in synonyms:
            if norm == syn:
                return canonical  # exact match — short circuit
            max_len = max(len(norm), len(syn))
            if max_len == 0:
                continue
            dist = levenshtein(norm, syn)
            score = 1.0 - (dist / max_len)
            if score > best_score:
                best_score = score
                best_canonical = canonical

    if best_score >= threshold:
        return best_canonical
    return None


def header_match_details(raw_header: str, threshold: float = 0.6,
                         allowed_canonicals=None,
                         extra_synonyms=None) -> dict:
    """Return the best mapping, confidence and possible ambiguity."""
    norm = _normalise_header(raw_header)
    allowed_canonicals = (
        set(allowed_canonicals) if allowed_canonicals is not None else None)
    scores = {}
    for canonical, synonyms in _merged_synonyms(extra_synonyms).items():
        if allowed_canonicals is not None and canonical not in allowed_canonicals:
            continue
        best = 0.0
        # v2.9.280 — retour écran MRE : « Regolith_Code » (regolith_code ≈
        # lith_code à 0,77) était auto-mappé en 2e lithologie → une fausse
        # « secondaire » et le symbole barrette toujours présent.  Le regolith
        # est une classification différente : jamais une lithologie.
        if canonical == "lithology" and "regolith" in norm:
            scores[canonical] = 0.0
            continue
        for synonym in synonyms:
            if norm == synonym:
                best = 1.0
                break
            # v2.7.11.7 — garde anti-bruit : pour un en-tête de 3 lettres
            # ou moins, un match EXACT seulement (« Min » fuzzy-matchait
            # « to » à 0,67 et une colonne de minéraux devenait une
            # profondeur TO — retour écran).
            if len(norm) > 3:
                width = max(len(norm), len(synonym))
                if width:
                    best = max(
                        best, 1.0 - levenshtein(norm, synonym) / width)
        scores[canonical] = best
    ordered = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    best_name, best_score = ordered[0] if ordered else (None, 0.0)
    second_score = ordered[1][1] if len(ordered) > 1 else 0.0
    return {
        "canonical": best_name if best_score >= threshold else None,
        "confidence": best_score,
        "ambiguous": bool(
            best_score >= threshold and second_score >= threshold
            and best_score - second_score < 0.08),
        "alternative": ordered[1][0] if len(ordered) > 1 else None,
    }


# ---------------------------------------------------------------------------
# Encoding detection
# ---------------------------------------------------------------------------
def detect_encoding(file_path: str) -> str:
    """
    Try to read the file with each candidate encoding.
    Return the first that decodes without error.
    Falls back to 'latin-1' which never fails.
    """
    with open(file_path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    # cp1252 must be attempted before latin-1: latin-1 decodes every byte but
    # would expose Windows punctuation as control characters.
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"  # never fails


# ---------------------------------------------------------------------------
# Separator detection
# ---------------------------------------------------------------------------
_SEPARATORS = [';', ',', '\t', '|']


def detect_separator(sample_lines: list[str]) -> str:
    """
    Detect the most likely delimiter by counting occurrences in the first
    few lines. The delimiter with the highest consistent count wins.
    """
    best_sep = ';'
    best_score = 0

    for sep in _SEPARATORS:
        counts = []
        for line in sample_lines:
            line = line.strip()
            if not line:
                continue
            # If separator is comma, avoid counting commas inside quotes
            # Simple heuristic: count outside quotes
            count = _count_outside_quotes(line, sep)
            counts.append(count)
        if not counts:
            continue
        # Score = consistency (min count > 0) + total count
        min_count = min(counts)
        total = sum(counts)
        if min_count > 0:
            score = total + min_count * 10  # consistency bonus
        else:
            score = total * 0.1
        if score > best_score:
            best_score = score
            best_sep = sep

    return best_sep


def _count_outside_quotes(line: str, sep: str) -> int:
    """Count separator occurrences outside double-quoted segments."""
    count = 0
    in_quote = False
    for ch in line:
        if ch == '"':
            in_quote = not in_quote
        elif ch == sep and not in_quote:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Decimal separator detection
# ---------------------------------------------------------------------------
def detect_decimal_separator(rows: list[list[str]], numeric_col_indices: list[int]) -> str:
    """
    Determine whether the file uses comma or period as decimal separator.
    Looks at numeric-looking values in the given column indices.
    """
    comma_count = 0
    period_count = 0
    for row in rows[:50]:  # sample first 50 rows
        for idx in numeric_col_indices:
            if idx >= len(row):
                continue
            val = row[idx].strip()
            if not val:
                continue
            # Pattern: digits with a comma or period as decimal
            if re.match(r'^-?\d+,\d+$', val):
                comma_count += 1
            elif re.match(r'^-?\d+\.\d+$', val):
                period_count += 1

    if comma_count > period_count:
        return ','
    return '.'  # default to period


# ---------------------------------------------------------------------------
# Parsing a value with a known decimal separator
# ---------------------------------------------------------------------------
def parse_number(val: str, decimal_sep: str) -> Optional[float]:
    """Parse one number without silently accepting a mixed decimal style.

    Thousands separators are accepted only when their grouping is
    unambiguous.  Thus ``18,9`` in a dot-decimal file is rejected instead of
    becoming ``189``.
    """
    if val is None:
        return None
    text = str(val).strip().replace("\u00a0", " ")
    if not text or text.casefold() in ("nan", "na", "n/a", "null", "-"):
        return None
    compact = text.replace(" ", "")
    signless = compact[1:] if compact[:1] in "+-" else compact
    decimal_sep = "," if decimal_sep == "," else "."
    thousands_sep = "." if decimal_sep == "," else ","

    if decimal_sep in signless:
        # There may be at most one decimal separator.
        if signless.count(decimal_sep) != 1:
            return None
        integer, fraction = signless.split(decimal_sep, 1)
        if not fraction.isdigit():
            return None
        if thousands_sep in integer:
            groups = integer.split(thousands_sep)
            if (not groups[0].isdigit() or not 1 <= len(groups[0]) <= 3
                    or any(len(group) != 3 or not group.isdigit()
                           for group in groups[1:])):
                return None
        elif integer and not integer.isdigit():
            return None
    elif thousands_sep in signless:
        # The other punctuation is a thousands separator only for exact
        # groups of three; otherwise it is a mixed decimal convention.
        groups = signless.split(thousands_sep)
        if (not groups[0].isdigit() or not 1 <= len(groups[0]) <= 3
                or any(len(group) != 3 or not group.isdigit()
                       for group in groups[1:])):
            return None
    elif not signless.isdigit():
        return None

    canonical = compact.replace(thousands_sep, "")
    if decimal_sep == ",":
        canonical = canonical.replace(",", ".")
    try:
        return float(canonical)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------
class ParseResult:
    """Holds the result of parsing a CSV file."""

    def __init__(self):
        self.file_type: str = ""           # collar, survey, litho, assays, alterations
        self.file_path: str = ""
        self.encoding: str = ""
        self.separator: str = ""
        self.decimal_sep: str = "."
        self.line_ending: str = "\n"
        self.quotechar: str = '"'
        self.raw_headers: list[str] = []
        self.source_headers: list[str] = []          # exact cells from line 1
        self.mapped_headers: dict[str, str] = {}     # raw_header -> canonical (auto)
        self.user_mappings: dict[str, str] = {}      # raw_header -> canonical (user override)
        self.mapping_details: dict[str, dict] = {}
        self.rows: list[list[str]] = []              # raw data rows (strings)
        self.preview_rows: list[list[str]] = []      # first 10 rows for display
        self.num_rows: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.row_width_issues: list[dict] = []
        self.detected_layout: str = ""
        from .data_registry import ImportStructureProfile
        self.structure = ImportStructureProfile()

    @property
    def effective_mappings(self) -> dict[str, str]:
        """User mappings override auto-detected ones."""
        merged = dict(self.mapped_headers)
        merged.update(self.user_mappings)
        return merged


def parse_csv_file(
    file_path: str,
    file_type: str,
    user_mappings: Optional[dict[str, str]] = None,
    structure=None,
    extra_synonyms=None,
) -> ParseResult:
    """
    Parse a CSV file with auto-detection of encoding, separator, decimal
    separator, and header mapping.

    Args:
        file_path: Path to the CSV file.
        file_type: One of 'collar', 'survey', 'litho', 'assays', 'alterations'.
        user_mappings: Optional dict of raw_header -> canonical field overrides.
        extra_synonyms: Optional dict canonical -> raw headers learned by the
            project (a user correction teaches the next imports).

    Returns:
        ParseResult with detected metadata and raw rows.
    """
    result = ParseResult()
    result.file_path = file_path
    result.file_type = file_type
    result.user_mappings = sanitise_user_mappings(file_type, user_mappings)
    if structure is not None:
        from .data_registry import ImportStructureProfile
        result.structure = ImportStructureProfile.from_dict(structure)

    if not os.path.isfile(file_path):
        result.errors.append(f"Fichier introuvable : {file_path}")
        return result

    # 1. Detect encoding
    result.encoding = detect_encoding(file_path)

    # 2. Read raw lines for separator detection
    with open(file_path, "r", encoding=result.encoding, newline='') as f:
        sample_text = f.read(8192)  # first 8KB
    result.line_ending = (
        "\r\n" if "\r\n" in sample_text
        else "\r" if "\r" in sample_text
        else "\n")
    sample_lines = sample_text.splitlines()

    if not sample_lines:
        result.errors.append("Fichier vide.")
        return result

    # 3. Detect separator and quoting dialect
    result.separator = detect_separator(sample_lines[:20])
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=";,\t|")
        result.quotechar = dialect.quotechar or '"'
    except csv.Error:
        result.quotechar = '"'

    # 4. Parse with csv module
    with open(file_path, "r", encoding=result.encoding, newline='') as f:
        reader = csv.reader(
            f, delimiter=result.separator, quotechar=result.quotechar)
        all_rows = list(reader)

    if not all_rows:
        result.errors.append("Fichier vide (aucune ligne).")
        return result

    # 5. Preserve exact header cells while exposing compatibility keys stripped
    # of surrounding whitespace. Duplicate semantic headers are unsafe because
    # dictionary-based mappings cannot distinguish them.
    result.source_headers = list(all_rows[0])
    result.raw_headers = [header.strip() for header in result.source_headers]
    folded = {}
    for index, header in enumerate(result.raw_headers):
        key = _normalise_header(header)
        if key in folded:
            result.errors.append(
                f"En-tête dupliqué '{header}' aux colonnes "
                f"{folded[key] + 1} et {index + 1}.")
        elif key:
            folded[key] = index

    # v2.9.262 — retour écran imagerie : les correspondances mémorisées
    # du projet (csv_mappings) peuvent contenir des en-têtes d'un fichier
    # PRÉCÉDENT (ex. Photo, puis Image). Si on les conserve, elles entrent
    # dans effective_mappings et déclenchent un faux
    # « Deux colonnes associées au même champ » alors que le fichier
    # courant est propre. On ne garde que les en-têtes réellement présents.
    # C'est un filtre GÉNÉRAL dans parse_csv_file : il s'applique à tous
    # les types (litho, alterations, mineralizations, structure, etc.),
    # pas seulement à l'imagerie.
    if result.user_mappings:
        result.user_mappings = {
            raw_header: canonical
            for raw_header, canonical in result.user_mappings.items()
            if raw_header in result.raw_headers}

    result.rows = all_rows[1:]
    expected_width = len(result.raw_headers)
    for line_no, row in enumerate(result.rows, start=2):
        # v2.9.263 — lignes VIDE : un CSV réel peut contenir des sauts de
        # ligne entre blocs (fréquent avec les exports depuis Excel/Google
        # Sheets).  Une ligne entièrement vide ne porte AUCUNE donnée : elle
        # n'est pas un défaut de largeur, elle est simplement ignorée.  Les
        # validateurs savent déjà les ignorer ; on ne doit pas rejeter tout
        # le fichier pour cela.
        if (not row or (len(row) == 1 and not str(row[0]).strip())
                or all(str(cell).strip() == "" for cell in row)):
            continue
        if len(row) != expected_width:
            issue = {
                "line": line_no, "actual": len(row),
                "expected": expected_width,
            }
            result.row_width_issues.append(issue)
            result.errors.append(
                f"Ligne {line_no}: {len(row)} cellule(s) pour "
                f"{expected_width} en-tête(s). Aucune valeur ne sera tronquée.")
    result.num_rows = len(result.rows)
    result.preview_rows = result.rows[:10]

    # 6. Auto-map headers and expose confidence. Ambiguous fuzzy matches are not
    # accepted silently; exact matches remain automatic.
    allowed_canonicals = _ALLOWED_CANONICAL_BY_FILE_TYPE.get(file_type)
    for raw_h in result.raw_headers:
        details = header_match_details(
            raw_h, allowed_canonicals=allowed_canonicals,
            extra_synonyms=extra_synonyms)
        canonical = details["canonical"]
        result.mapping_details[raw_h] = details
        if canonical and not details["ambiguous"]:
            result.mapped_headers[raw_h] = canonical
        elif details["ambiguous"]:
            result.warnings.append(
                f"Correspondance ambiguë pour l’en-tête '{raw_h}' : "
                f"{canonical} ou {details['alternative']}.")

    # 7. Detect decimal separator — check ALL columns (file-level property)
    if result.rows:
        all_indices = list(range(len(result.raw_headers)))
        result.decimal_sep = detect_decimal_separator(result.rows, all_indices)

    if file_type == "litho" and structure is None:
        result.structure = infer_lithology_structure(result)
    if file_type == "assays":
        normalized_headers = {_normalise_header(header)
                              for header in result.raw_headers}
        element_names = {"element", "analyte", "analytecode", "elementname"}
        value_names = {"value", "result", "valeur", "resultat", "assayvalue"}
        if normalized_headers.intersection(element_names) and normalized_headers.intersection(value_names):
            result.detected_layout = "long_values"
            result.warnings.append(
                "Format LONG des Teneurs détecté (Élément/Valeur). Ce "
                "plugin n'accepte que le format large : une colonne par "
                "élément (règle du projet, 20/08/2026).")
        else:
            result.detected_layout = "wide_values"
    return result

def infer_lithology_structure(pr: ParseResult):
    """Infer only explicit structural headers; repeated rows never select long."""
    from .data_registry import ComponentColumn, ImportStructureProfile
    mappings = pr.effective_mappings
    by_canonical = {
        canonical: raw for raw, canonical in mappings.items() if canonical
    }
    components = []
    primary = by_canonical.get("lithology_primary")
    secondary = by_canonical.get("lithology_secondary")
    if primary:
        components.append(ComponentColumn(
            primary, "primary",
            by_canonical.get("lithology_proportion", "")))
    if secondary:
        components.append(ComponentColumn(
            secondary, "secondary",
            by_canonical.get("secondary_proportion", "")))
    if components:
        return ImportStructureProfile(
            mode="wide_components", component_columns=components,
            proportion_unit="percent", confidence=1.0, confirmed=False)

    return ImportStructureProfile(
        mode="standard", code_column=by_canonical.get("lithology", ""),
        proportion_unit="unknown",
        confidence=1.0 if by_canonical.get("lithology") else 0.0,
        confirmed=False)


def find_delimited_values(pr: ParseResult, header: str, delimiter="/",
                          limit=3) -> list[str]:
    """Return distinct ambiguous cell examples without interpreting them."""
    if not header or not delimiter or limit <= 0:
        return []
    try:
        column = pr.raw_headers.index(header)
    except ValueError:
        return []
    examples = []
    for row in pr.rows:
        if column >= len(row):
            continue
        value = str(row[column]).strip()
        if delimiter in value and value not in examples:
            examples.append(value)
        if len(examples) >= limit:
            break
    return examples


def canonical_lithology_role(raw_role: str) -> str:
    """Map known role vocabulary for logic while preserving the raw value."""
    folded = _normalise_header(raw_role)
    aliases = {
        "primary": "primary", "principal": "primary",
        "principale": "primary", "main": "primary", "host": "primary",
        "secondary": "secondary", "secondaire": "secondary",
        "minor": "secondary",
        "vein": "vein", "veine": "vein", "veinlet": "vein",
        "veinule": "vein",
        "accessory": "accessory", "accessoire": "accessory",
        "trace": "accessory",
    }
    return aliases.get(folded, "")


def normalise_editor_rows(rows: list[list[str]], width: int) -> list[list[str]]:
    """Return editable rows padded/truncated to the CSV header width."""
    width = max(int(width), 0)
    return [
        [str(value) for value in row[:width]] + [""] * max(width - len(row), 0)
        for row in rows
    ]


def write_csv_file(
    file_path: str,
    headers: list[str],
    rows: list[list[str]],
    encoding: str = "utf-8",
    separator: str = ";",
    line_ending: str = "\n",
    quotechar: str = '"',
    make_backup: bool = True,
) -> str:
    """Atomically save edited CSV data while preserving its detected dialect.

    Existing files receive a ``.bak`` copy before replacement. Values remain
    strings, so decimal commas/periods and original textual representations are
    preserved exactly as entered in the editor.
    """
    target = os.path.abspath(os.path.expanduser(file_path))
    parent = os.path.dirname(target) or os.getcwd()
    os.makedirs(parent, exist_ok=True)
    safe_separator = separator if separator in _SEPARATORS else ";"
    safe_ending = line_ending if line_ending in ("\n", "\r\n", "\r") else "\n"
    safe_quote = quotechar if isinstance(quotechar, str) and len(quotechar) == 1 else '"'
    normalised = normalise_editor_rows(rows, len(headers))

    fd, temp_path = tempfile.mkstemp(prefix=".drillmaster_", suffix=".csv", dir=parent)
    os.close(fd)
    try:
        with open(temp_path, "w", encoding=encoding or "utf-8", newline="") as stream:
            writer = csv.writer(
                stream, delimiter=safe_separator, quotechar=safe_quote,
                quoting=csv.QUOTE_MINIMAL, lineterminator=safe_ending)
            writer.writerow(headers)
            writer.writerows(normalised)
        if make_backup and os.path.isfile(target):
            shutil.copy2(target, target + ".bak")
        os.replace(temp_path, target)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return target


def extract_validation_locations(
    errors: list[str], raw_headers: list[str], mappings: dict[str, str]
) -> list[dict]:
    """Map validation messages to zero-based editor row/column locations."""
    locations = []
    canonical_to_raw = {}
    for raw, canonical in (mappings or {}).items():
        if canonical and canonical not in canonical_to_raw:
            canonical_to_raw[canonical] = raw
    folded_headers = {header.casefold(): i for i, header in enumerate(raw_headers)}

    for message in errors or []:
        line_match = re.search(r"Ligne\s+(\d+)", message, flags=re.IGNORECASE)
        row = max(int(line_match.group(1)) - 2, 0) if line_match else None
        column_match = re.search(
            r"colonne\s+['\"]([^'\"]+)['\"]", message,
            flags=re.IGNORECASE)
        column = None
        if column_match:
            key = column_match.group(1)
            raw_key = canonical_to_raw.get(key, key)
            column = folded_headers.get(raw_key.casefold())
        locations.append({
            "message": message,
            "row": row,
            "column": column,
        })
    return locations


# ---------------------------------------------------------------------------
# Convert ParseResult -> typed records
# ---------------------------------------------------------------------------


def organisation_columns(structure) -> set:
    """v2.9.311 — colonnes adoptées par une réponse d'organisation
    confirmée (colonnes de code/composantes + code_column). Elles ont un
    rôle : ni « ambiguës », ni « en doublon » sur un champ."""
    if structure is None or not getattr(structure, "confirmed", False):
        return set()
    if getattr(structure, "mode", "") not in {
            "wide_components", "delimited_components"}:
        return set()
    cols = {c.code_column for c in (structure.component_columns or [])}
    if getattr(structure, "code_column", None):
        cols.add(structure.code_column)
    return cols


def live_mapping_conflicts(parse_result) -> list:
    """v2.9.311 — conflits de mappage ACTUELS (source unique du badge).

    (1) ambiguïté fuzzy NON tranchée (ni choix utilisateur, ni colonne
    d'une organisation confirmée) ; (2) deux colonnes mappées sur le même
    champ cible — hors colonnes d'une organisation confirmée (ce sont
    des colonnes de codes, pas un doublon de champ)."""
    if parse_result is None:
        return []
    org_cols = organisation_columns(getattr(parse_result, "structure", None))
    decided = parse_result.user_mappings or {}
    conf = [h for h, d in (parse_result.mapping_details or {}).items()
            if isinstance(d, dict) and d.get("ambiguous")
            and h not in decided and h not in org_cols]
    from collections import Counter
    eff = {h: v for h, v in (parse_result.effective_mappings or {}).items()
           if h not in org_cols}
    cnt = Counter(v for v in eff.values() if v)
    dupes = sorted({h for h, v in eff.items() if v and cnt[v] > 1})
    return sorted(set(conf) | set(dupes))
