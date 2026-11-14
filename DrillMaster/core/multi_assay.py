"""Multi-assay lanes for the 2D section (v2.9.92).

Isolated lot: up to 3 grade elements side-by-side on the SAME side of the
section, fixed order, independent colour ramp + scale per element.

section_dock / SectionCanvas CALL this module — they do not re-implement
lane packing, style migration, or per-element scale assembly here.

Backward compatible:
  - legacy ``assay_style["element"]`` alone still works (single lane);
  - ``elements`` list is derived from ``element`` when missing;
  - first element mirrors ``element`` for QGIS map / undo / older code.
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional

# v1 product caps (do not raise without a new product decision)
MAX_ASSAY_ELEMENTS = 3
DEFAULT_SUBLANE_GAP_PX = 1.5


def hole_has_values(assays, elems) -> bool:
    """v2.9.286 — ce trou porte-t-il au moins une valeur chiffrée ?

    Un trou SANS teneur ne doit recevoir ni ruban ni libellé de piste
    (retour écran : « trous sans teneur mais étiquette et voix quand
    même »).  Partagé dock/export.
    """
    for iv in assays or []:
        attrs = getattr(iv, "attributes", None) or {}
        for e in elems or []:
            if isinstance(attrs.get(e), (int, float)):
                return True
    return False


def numeric_fraction(rows, index: int) -> float:
    """v2.9.285 — part de valeurs numériques d'une colonne d'analyse.

    « <5 », « >10 », « ~0,4 » tolérés (limites de détection courantes en
    RC) ; une colonne texte (commentaire, litho, échantillon…) score ~0
    et n'est donc JAMAIS proposée comme élément de teneur — référentiel
    compris (« détection des colonnes numériques », retour écran).
    """
    values = []
    for row in rows or []:
        if isinstance(row, (list, tuple)) and index < len(row):
            text = str(row[index]).strip()
            if text:
                values.append(text)
    if not values:
        return 0.0
    ok = 0
    for text in values:
        try:
            float(text.lstrip("<>~≤≥ "))
            ok += 1
        except ValueError:
            continue
    return ok / len(values)


def format_grade_value(val: float) -> str:
    """Formate une valeur de teneur sans notation scientifique.

    v2.9.147 — déménagée depuis ``ui/view_3d.py`` : c'est un formateur
    NUMÉRIQUE pur, partagé par la vue 3D et sa couche overlays (la
    légende teneurs).  ``ui/view_3d.py`` la réimporte pour tous ses
    appelants historiques.
    """
    if abs(val) >= 1000:
        return f"{val:,.0f}".replace(",", " ")
    elif abs(val) >= 10:
        return f"{val:.1f}".rstrip("0").rstrip(".")
    elif abs(val) >= 0.01:
        return f"{val:.2f}".rstrip("0").rstrip(".")
    else:
        return f"{val:.3f}".rstrip("0").rstrip(".")

# Fallback ramp cycle when a slot has no explicit palette
_PALETTE_CYCLE = ("grade", "viridis", "blue_red")


# Suffixes collés aux en-têtes CSV (Cu_ppm, Fe_pct…) — une seule unité
# dans le libellé, jamais « Cu_ppm ppm ».
_UNIT_SUFFIXES = (
    ("_ppm", "ppm"),
    ("_ppb", "ppb"),
    ("_pct", "%"),
    ("_pc", "%"),
    ("_percent", "%"),
    ("_pourcent", "%"),
    ("_gpt", "g/t"),
    ("_g_t", "g/t"),
    ("_opt", "oz/t"),
)
_UNIT_ALIASES = {
    "pct": "%", "pc": "%", "percent": "%",
    "pourcent": "%", "pourcentage": "%", "%": "%",
    "ppm": "ppm", "ppb": "ppb",
    "g/t": "g/t", "gpt": "g/t", "oz/t": "oz/t", "opt": "oz/t",
}
_TRAILING_UNIT_TOKENS = (
    (" ppm", "ppm"), (" ppb", "ppb"), (" %", "%"),
    (" pct", "%"), (" g/t", "g/t"),
)


def _canonical_unit(unit: str) -> str:
    u = str(unit or "").strip()
    if not u:
        return ""
    return _UNIT_ALIASES.get(u.casefold(), u)


def _split_element_unit(element: str) -> tuple[str, str]:
    """Cu_ppm → (Cu, ppm) ; Fe_pct → (Fe, %) ; Au → (Au, '')."""
    raw = str(element or "").strip()
    if not raw:
        return "", ""
    low = raw.casefold()
    for suf, canon in _UNIT_SUFFIXES:
        if low.endswith(suf):
            symbol = raw[:len(raw) - len(suf)].rstrip("_ ").strip()
            return (symbol or raw), canon
    for token, canon in _TRAILING_UNIT_TOKENS:
        if low.endswith(token):
            symbol = raw[:len(raw) - len(token)].strip()
            return (symbol or raw), canon
    return raw, ""


def column_caption(element: str, unit: str = "") -> str:
    """Court libellé de piste teneur : « Fe % », « Cu ppm ».

    v2.9.123 — dock et export lisent la même fonction.
    v2.9.127 — ôte le suffixe d'unité déjà dans le code CSV
    (``Cu_ppm`` + ppm → « Cu ppm », plus « Cu_ppm ppm »).
    """
    symbol, inferred = _split_element_unit(element)
    if not symbol:
        return ""
    u = _canonical_unit(unit) or inferred
    if u and symbol.casefold().endswith(u.casefold()):
        u = ""
    return f"{symbol} {u}".strip() if u else symbol


def normalize_elements(raw) -> list[str]:
    """Unique, non-empty element codes, order preserved, max MAX_ASSAY_ELEMENTS."""
    out: list[str] = []
    seen: set[str] = set()
    if raw is None:
        return out
    if isinstance(raw, str):
        raw = [raw]
    try:
        seq = list(raw)
    except TypeError:
        return out
    for item in seq:
        code = str(item or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(code)
        if len(out) >= MAX_ASSAY_ELEMENTS:
            break
    return out


def clamp_display_elements(candidates, max_count: int = MAX_ASSAY_ELEMENTS):
    """Éléments d'affichage teneurs, bornés au plafond (v2.9.146).

    Filtre doublons/vide et coupe à ``max_count`` (3, comme la coupe 2D),
    ordre préservé.  Utilisé par le choix d'éléments de la vue 3D.
    """
    out = []
    for raw in (candidates or []):
        code = str(raw or "").strip()
        if not code or code in out:
            continue
        out.append(code)
        if len(out) >= int(max_count):
            break
    return out


def assay_selection_summary(elements, mirror_label: str) -> str:
    """Libellé résumé de la sélection d'éléments teneurs 3D (v2.9.146).

    - sélection vide → le libellé miroir (« Comme la coupe 2D (2
      éléments) ») ;
    - 1 élément → son code ;
    - 2-3 → « 2 éléments : Cu_ppm, Fe_pct » (codes tronqués à 14 car.).
    """
    elems = [str(e) for e in (elements or []) if str(e or "").strip()]
    if not elems:
        return str(mirror_label or "Comme la coupe 2D")
    short = [e if len(e) <= 14 else e[:13] + "…" for e in elems]
    if len(short) == 1:
        return short[0]
    return f"{len(short)} éléments : " + ", ".join(short)


def assay_legend_columns(elements, scales, palettes,
                         default_palette: str = "grade"):
    """Colonnes de légende teneurs : UNE PAR ÉLÉMENT (v2.9.142).

    Même principe que la légende de la coupe 2D : un en-tête par élément
    (« Cu ppm »), puis les classes de bornes seules — plus le nom de
    l'élément répété sur chaque ligne (« Cu ppm 5 – 10 », « Cu ppm 10 –
    20 »…) qui chargeait visuellement la légende 3D.

    Retourne ``[(caption, rows), …]`` avec ``rows = [(b0, b1, frac,
    palette), …]`` — ``frac`` = position dans la rampe [0, 1] pour la
    pastille couleur.  Les éléments sans échelle valide sont sautés.
    """
    columns = []
    for el in elements or []:
        scale = (scales or {}).get(el)
        if not scale or "boundaries" not in scale:
            continue
        cap = column_caption(el) or str(el)
        pal = str((palettes or {}).get(el) or default_palette or "grade")
        bounds = scale["boundaries"]
        n = len(bounds) - 1
        if n < 1:
            continue
        rows = []
        for i in range(n):
            b0, b1 = bounds[i], bounds[i + 1]
            frac = i / max(1, n - 1)
            rows.append((b0, b1, frac, pal))
        columns.append((cap, rows))
    return columns


def migrate_assay_style(style: Optional[dict]) -> dict:
    """Return a copy of assay_style with ``elements`` / palettes filled.

    Never drops legacy keys.  ``element`` stays the first active code.
    """
    base = dict(style or {})
    elements = normalize_elements(base.get("elements"))
    legacy = str(base.get("element") or "").strip()
    if not elements and legacy:
        elements = [legacy]
    if elements and not legacy:
        legacy = elements[0]
    if elements and legacy and legacy not in elements:
        # Keep explicit multi-list; still expose first as element for map.
        legacy = elements[0]
    if elements and not legacy:
        legacy = elements[0]
    base["elements"] = list(elements)
    base["element"] = legacy
    palettes = dict(base.get("element_palettes") or {})
    default_pal = str(base.get("palette") or "grade")
    for i, code in enumerate(elements):
        if code not in palettes or not str(palettes.get(code) or "").strip():
            if i == 0:
                palettes[code] = default_pal
            else:
                palettes[code] = _PALETTE_CYCLE[i % len(_PALETTE_CYCLE)]
    # drop stale keys not in elements
    palettes = {k: str(v) for k, v in palettes.items() if k in set(elements)}
    base["element_palettes"] = palettes
    return base


def primary_element(style: Optional[dict]) -> str:
    """First active element (legacy ``element`` field)."""
    m = migrate_assay_style(style)
    elems = m.get("elements") or []
    if elems:
        return str(elems[0])
    return str(m.get("element") or "")


def active_elements(style: Optional[dict]) -> list[str]:
    return list(migrate_assay_style(style).get("elements") or [])


def palette_for(style: Optional[dict], element: str) -> str:
    m = migrate_assay_style(style)
    pals = m.get("element_palettes") or {}
    code = str(element or "").strip()
    if code in pals and pals[code]:
        return str(pals[code])
    return str(m.get("palette") or "grade")


def total_track_width(n_elements: int, lane_width: float,
                      gap: float = DEFAULT_SUBLANE_GAP_PX) -> float:
    """Full assays track width for ``n`` side-by-side sub-lanes."""
    n = max(0, min(int(n_elements or 0), MAX_ASSAY_ELEMENTS))
    w = max(float(lane_width or 0.0), 0.0)
    g = max(float(gap), 0.0)
    if n <= 0 or w <= 0.0:
        return 0.0
    if n == 1:
        return w
    return n * w + (n - 1) * g


def sublane_layout(n_elements: int, track_inner: float, track_width: float,
                   side: str = "left",
                   gap: float = DEFAULT_SUBLANE_GAP_PX) -> list[dict]:
    """Pack N equal sub-lanes inside one assays track.

    Returns list of dicts ``{index, inner, outer, width}`` in fixed order
    (element 0 closest to the hole trace).  Offsets are trace-relative
    (same convention as TrackLane.inner_edge).
    """
    n = max(0, min(int(n_elements or 0), MAX_ASSAY_ELEMENTS))
    if n <= 0:
        return []
    sign = 1.0 if str(side) == "right" else -1.0
    inner0 = float(track_inner)
    total = max(float(track_width), 0.0)
    g = max(float(gap), 0.0)
    if n == 1:
        width = total
        outer = inner0 + sign * width
        return [{"index": 0, "inner": inner0, "outer": outer, "width": width}]
    # Equal share of usable width after gaps between sub-lanes
    usable = max(total - g * (n - 1), 0.0)
    width = usable / float(n) if n else 0.0
    out = []
    cursor = inner0
    for i in range(n):
        outer = cursor + sign * width
        out.append({
            "index": i,
            "inner": cursor,
            "outer": outer,
            "width": width,
        })
        cursor = outer + sign * g
    return out


def collect_element_values(intervals: Iterable, element: str) -> list[float]:
    """Numeric values for one assay attribute from interval records."""
    code = str(element or "").strip()
    vals: list[float] = []
    if not code:
        return vals
    for iv in intervals or []:
        attrs = getattr(iv, "attributes", None) or {}
        value = attrs.get(code)
        if isinstance(value, (int, float)):
            try:
                fv = float(value)
            except (TypeError, ValueError):
                continue
            if fv == fv:  # not NaN
                vals.append(fv)
    return vals


def build_scales(
    elements: list[str],
    *,
    intervals_for_scope,
    compute_scale: Callable,
    method: str = "jenks",
    n_classes: int = 7,
    manual_breaks: Optional[list] = None,
    round_breaks: bool = True,
    manual_breaks_by_element: Optional[dict] = None,
) -> dict[str, dict]:
    """``{element: scale_dict}`` — one independent scale per element.

    370 — seuils manuels PAR ÉLÉMENT (retour « pourquoi un seul
    élément ? ») : chaque élément utilise SES propres seuils
    (``manual_breaks_by_element``) ; un élément SANS seuils saisis
    repart sur Jenks (grille ronde).  La clé "" (saisie sans code)
    s'applique au premier élément."""
    scales: dict[str, dict] = {}
    elems = normalize_elements(elements)
    for pos, code in enumerate(elems):
        vals = collect_element_values(intervals_for_scope, code)
        if not vals:
            continue
        m = method
        mb: list = []
        if manual_breaks_by_element is not None:
            mb = list(manual_breaks_by_element.get(code) or [])
            if not mb and pos == 0:
                mb = list(manual_breaks_by_element.get("") or [])
        elif manual_breaks:
            mb = list(manual_breaks) if pos == 0 else []
        if m == "manual" and not mb:
            m = "jenks"
        scales[code] = compute_scale(vals, m, n_classes, mb, round_breaks)
    return scales


def style_snapshot_for_canvas(style: Optional[dict]) -> dict:
    """Compact payload the canvas stores after a style apply."""
    m = migrate_assay_style(style)
    return {
        "elements": list(m.get("elements") or []),
        "element": str(m.get("element") or ""),
        "element_palettes": dict(m.get("element_palettes") or {}),
        "method": m.get("method", "jenks"),
        "n_classes": int(m.get("n_classes", 7) or 7),
        "manual_breaks": list(m.get("manual_breaks") or []),
        "round_breaks": bool(m.get("round_breaks", True)),
        "scale_scope": m.get("scale_scope", "project"),
        "palette": m.get("palette", "grade"),
        "opacity": int(m.get("opacity", 100) or 100),
    }
