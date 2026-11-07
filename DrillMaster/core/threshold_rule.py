"""Règle de seuil teneurs — v2.9.102+ (fusion, légende, multi-litho, multi-ET).

Lot isolé : règle d'affichage uniquement (pas d'écriture sources).

- clauses teneurs : 1..3, combinateur **ET** strict
- valeur manquante / non numérique → clause fausse → non-match
- même intervalle (mêmes attributs / From–To) — pas de jointure floue
- filtre litho : 0..N codes, sémantique **OU**
- rétrocompat : element/operator/value → une clause
- v2.9.116 — multi-règles (max 3) + couleurs fixes distinctes
  (cyan / magenta / ambre) ; une règle = un contour coloré
- v2.9.121 — plage de valeur = min/max réels de l'élément ;
  contours : mêmes traits (dock + export) pour les 3 couleurs ;
  dessin reporté sur la 1ʳᵉ piste teneurs affichée si besoin
- v2.9.122 — piste **intercepts** dédiée (blocs pleins) : plus de
  contour peint sur les teneurs ; apparition = règle ON (pas match)

Pure Python, testable hors QGIS.
"""
from __future__ import annotations

from typing import Any, Optional

OPERATORS = (">", ">=", "<", "<=")
MAX_CLAUSES = 3
MAX_RULES = 3

# Couleurs fixes par slot (index 0..2) — distinctes, lisibles coupe + PNG
RULE_COLOR_SLOTS: tuple = (
    {"hex": "#00E5FF", "name": "cyan"},      # règle 1
    {"hex": "#FF00AA", "name": "magenta"},   # règle 2
    {"hex": "#FFB000", "name": "ambre"},     # règle 3
)

DEFAULT_RULE: dict = {
    "enabled": False,
    "element": "",
    "operator": ">",
    "value": None,
    "clauses": [],
    "litho_filter": [],
    "color": "#00E5FF",
    "color_name": "cyan",
}


def rule_color_for_index(index: int) -> dict:
    """Couleur fixe du slot i (0..MAX_RULES-1)."""
    i = int(index) if index is not None else 0
    if i < 0:
        i = 0
    if i >= len(RULE_COLOR_SLOTS):
        i = len(RULE_COLOR_SLOTS) - 1
    slot = RULE_COLOR_SLOTS[i]
    return {"hex": slot["hex"], "name": slot["name"]}


def _normalize_color_hex(raw, *, fallback: str = "#00E5FF") -> str:
    s = str(raw or "").strip()
    if not s:
        return fallback
    if not s.startswith("#"):
        s = "#" + s
    s = s.upper()
    if len(s) == 4:  # #RGB → #RRGGBB
        s = "#" + "".join(ch * 2 for ch in s[1:])
    if len(s) != 7:
        return fallback
    try:
        int(s[1:], 16)
    except ValueError:
        return fallback
    return s


def color_name_for_hex(hex_color: str) -> str:
    """Nom lisible pour légende (cyan / magenta / ambre / custom)."""
    h = _normalize_color_hex(hex_color)
    for slot in RULE_COLOR_SLOTS:
        if slot["hex"].upper() == h:
            return slot["name"]
    return "personnalisé"


def _normalize_litho_filter(raw) -> list:
    """Normalise filtre litho en liste de codes (ordre stable, uniques)."""
    if raw is None or raw is False:
        return []
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        parts = [p.strip() for p in s.replace(";", ",").split(",")]
        codes = [p for p in parts if p]
    elif isinstance(raw, (list, tuple, set)):
        codes = []
        for item in raw:
            if item is None:
                continue
            t = str(item).strip()
            if t:
                codes.append(t)
    else:
        t = str(raw).strip()
        codes = [t] if t else []
    seen = set()
    out = []
    for c in codes:
        k = c.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    return out


def _parse_clause_value(val):
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _normalize_clause(raw) -> Optional[dict]:
    """Une clause {element, operator, value} ou None si invalide/vide."""
    if not isinstance(raw, dict):
        return None
    elem = str(raw.get("element") or "").strip()
    if not elem:
        return None
    op = str(raw.get("operator") or ">").strip()
    if op not in OPERATORS:
        op = ">"
    value = _parse_clause_value(raw.get("value", None))
    if value is None:
        return None
    return {"element": elem, "operator": op, "value": value}


def _normalize_clauses(raw_rule: dict) -> list:
    """Extrait 1..MAX_CLAUSES clauses ; rétrocompat element/op/value."""
    clauses: list = []
    raw_list = raw_rule.get("clauses")
    if isinstance(raw_list, (list, tuple)):
        for item in raw_list:
            c = _normalize_clause(item)
            if c is not None:
                clauses.append(c)
            if len(clauses) >= MAX_CLAUSES:
                break
    if not clauses:
        # legacy single fields
        c = _normalize_clause({
            "element": raw_rule.get("element"),
            "operator": raw_rule.get("operator"),
            "value": raw_rule.get("value"),
        })
        if c is not None:
            clauses = [c]
    # dédup par élément (1ère occurrence gagne)
    seen = set()
    out = []
    for c in clauses:
        k = c["element"].casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
        if len(out) >= MAX_CLAUSES:
            break
    return out


def normalize_rule(raw: Optional[dict], *, slot_index: int = 0) -> dict:
    """Normalise un dict règle (rétrocompat / projets anciens).

    ``slot_index`` assigne la couleur fixe du slot (0=cyan, 1=magenta, 2=ambre)
    si ``color`` absente. Une couleur explicite est respectée.
    """
    slot = rule_color_for_index(slot_index)
    out = {
        "enabled": False,
        "element": "",
        "operator": ">",
        "value": None,
        "clauses": [],
        "litho_filter": [],
        "color": slot["hex"],
        "color_name": slot["name"],
    }
    if not isinstance(raw, dict):
        return out
    out["enabled"] = bool(raw.get("enabled", False))
    clauses = _normalize_clauses(raw)
    out["clauses"] = clauses
    # miroir legacy = 1ʳᵉ clause (ancre dessin + rétrocompat)
    if clauses:
        out["element"] = clauses[0]["element"]
        out["operator"] = clauses[0]["operator"]
        out["value"] = clauses[0]["value"]
    else:
        out["element"] = str(raw.get("element") or "").strip()
        op = str(raw.get("operator") or ">").strip()
        out["operator"] = op if op in OPERATORS else ">"
        out["value"] = _parse_clause_value(raw.get("value", None))
    if "litho_filter" in raw:
        out["litho_filter"] = _normalize_litho_filter(raw.get("litho_filter"))
    else:
        out["litho_filter"] = []
    # couleur : explicite > slot
    if raw.get("color"):
        out["color"] = _normalize_color_hex(raw.get("color"), fallback=slot["hex"])
        out["color_name"] = (
            str(raw.get("color_name") or "").strip()
            or color_name_for_hex(out["color"]))
    else:
        out["color"] = slot["hex"]
        out["color_name"] = slot["name"]
    if out["enabled"] and not clauses:
        out["enabled"] = False
    return out


def is_active(rule: Optional[dict]) -> bool:
    r = normalize_rule(rule)
    return bool(r["enabled"] and r.get("clauses"))


def empty_rule(slot_index: int = 0) -> dict:
    """Règle vide (désactivée) pour le slot donné."""
    return normalize_rule(None, slot_index=slot_index)


def normalize_rules(raw) -> list:
    """Liste 0..MAX_RULES de règles normalisées (couleurs de slot).

    Rétrocompat :
    - ``threshold_rules`` (liste) prioritaire
    - sinon ``threshold_rule`` (dict unique) → [rule]
    - sinon []
    """
    items = None
    if isinstance(raw, dict) and "threshold_rules" not in raw and (
            "enabled" in raw or "clauses" in raw or "element" in raw):
        # un seul dict règle passé directement
        items = [raw]
    elif isinstance(raw, dict):
        items = raw.get("threshold_rules")
        if items is None and raw.get("threshold_rule") is not None:
            items = [raw.get("threshold_rule")]
    elif isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        items = None
    if not isinstance(items, (list, tuple)):
        return []
    out = []
    for i, item in enumerate(items):
        if i >= MAX_RULES:
            break
        if not isinstance(item, dict):
            continue
        out.append(normalize_rule(item, slot_index=i))
    return out


def migrate_threshold_payload(style: Optional[dict]) -> dict:
    """Assure ``threshold_rules`` + miroir ``threshold_rule`` (= 1ʳᵉ active/1ʳᵉ).

    Entrée = assay_style (ou fragment). Sortie = même dict muté + normalisé.
    """
    s = dict(style or {})
    rules = None
    if isinstance(s.get("threshold_rules"), (list, tuple)):
        rules = normalize_rules(s.get("threshold_rules"))
    elif s.get("threshold_rule") is not None:
        rules = normalize_rules([s.get("threshold_rule")])
    else:
        rules = []
    s["threshold_rules"] = rules
    # miroir legacy : 1ʳᵉ active, sinon 1ʳᵉ, sinon vide slot 0
    primary = None
    for r in rules:
        if is_active(r):
            primary = r
            break
    if primary is None and rules:
        primary = rules[0]
    if primary is None:
        primary = empty_rule(0)
    s["threshold_rule"] = primary
    return s


def intercept_lane_offsets(n_rules: int) -> list[float]:
    """Positions normalisées des voies d'intercepts (v2.9.144/D5).

    Une voie PAR règle active, centrées sur l'axe du forage — la règle k
    garde TOUJOURS la même voie d'un forage (et d'une vue) à l'autre :

        n=1 → [0.0] ; n=2 → [-0.5, +0.5] ; n=3 → [-1.0, 0.0, +1.0]

    Source unique partagée coupe 2D / vue 3D : la 3D multiplie par son
    écartement écran (``lane_gap``), la 2D par la largeur de sa piste
    (cf. ``intercept_slot_layout`` pour les colonnes du dock).
    Décision D5 de la SPEC_RESTRUCTURATION_3D (validée).
    """
    n = max(1, int(n_rules))
    return [(k - (n - 1) / 2.0) for k in range(n)]


def active_rules(rules) -> list:
    """Sous-liste des règles actives (enabled + clauses)."""
    return [r for r in normalize_rules(rules) if is_active(r)]


def legend_labels_multi(
    rules,
    *,
    units: Optional[dict] = None,
) -> list:
    """Une entrée légende par règle active (texte + couleur hex)."""
    out = []
    units = dict(units or {})
    for r in active_rules(rules):
        name = r.get("color_name") or color_name_for_hex(r.get("color"))
        text = legend_label(r, color_name=name, units=units)
        if text:
            out.append({
                "text": text,
                "color": r.get("color") or RULE_COLOR_SLOTS[0]["hex"],
                "color_name": name,
                "rule": r,
            })
    return out

def compare(value: float, operator: str, threshold: float) -> bool:
    if operator == ">":
        return value > threshold
    if operator == ">=":
        return value >= threshold
    if operator == "<":
        return value < threshold
    if operator == "<=":
        return value <= threshold
    return False


def clause_value_ok(value: Any) -> bool:
    """True si valeur comparable (manquant / texte → False)."""
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        # reject NaN
        try:
            if value != value:  # NaN
                return False
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("threshold_rule : clause_value_ok", _exc)
            return False
        return True
    return False


def clause_matches(clause: dict, value: Any) -> bool:
    """Une clause vs une valeur d'intervalle. Manquant = faux."""
    if not isinstance(clause, dict):
        return False
    if not clause_value_ok(value):
        return False
    op = clause.get("operator") or ">"
    thr = clause.get("value")
    if thr is None:
        return False
    try:
        return compare(float(value), op, float(thr))
    except (TypeError, ValueError):
        return False


def _litho_codes_for_interval(hole, from_depth: float, to_depth: float) -> set:
    codes: set = set()
    lithos = getattr(hole, "litho", None) or []
    mid = 0.5 * (float(from_depth) + float(to_depth))
    for liv in lithos:
        try:
            a = float(liv.from_depth)
            b = float(liv.to_depth)
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Piste lithologie : _litho_codes_for_interval", _exc)
            continue
        if b < from_depth or a > to_depth:
            if not (a <= mid <= b):
                continue
        comps = getattr(liv, "components", None) or []
        if comps:
            for c in comps:
                raw = getattr(c, "raw_code", None) or ""
                if raw:
                    codes.add(str(raw).strip().casefold())
        else:
            attrs = getattr(liv, "attributes", None) or {}
            raw = attrs.get("lithology") or attrs.get("lithology_primary") or ""
            if raw:
                codes.add(str(raw).strip().casefold())
    return codes


def litho_filter_matches(rule: dict, hole, from_depth: float, to_depth: float) -> bool:
    """True si filtre litho vide OU au moins un code (OU) chevauche."""
    r = normalize_rule(rule)
    filt = r.get("litho_filter") or []
    if not filt:
        return True
    want = {str(c).strip().casefold() for c in filt if str(c).strip()}
    if not want:
        return True
    have = _litho_codes_for_interval(hole, from_depth, to_depth)
    return bool(want & have)


def interval_matches(
    rule: dict,
    *,
    element: str = "",
    value: Any = None,
    attributes: Optional[dict] = None,
    hole=None,
    from_depth: float = 0.0,
    to_depth: float = 0.0,
) -> bool:
    """True si l'intervalle matche la règle (ET de toutes les clauses).

    Préférer ``attributes`` (dict élément→valeur du même intervalle).
    Rétrocompat : ``element`` + ``value`` seuls (1 clause / test unitaire).
    Valeur manquante sur une clause → non-match.
    """
    r = normalize_rule(rule)
    if not is_active(r):
        return False
    clauses = r.get("clauses") or []
    if not clauses:
        return False

    attrs = dict(attributes or {})
    # rétrocompat : injecter element/value si fournis
    if element and element not in attrs and value is not None:
        attrs[str(element).strip()] = value
    # si seul element+value et une clause : mode legacy strict
    if not attributes and element and len(clauses) == 1:
        if str(element or "").strip() != clauses[0]["element"]:
            return False

    for cl in clauses:
        el = cl["element"]
        v = attrs.get(el)
        # aussi tenter clé exacte strip
        if v is None:
            for k, kv in attrs.items():
                if str(k).strip() == el:
                    v = kv
                    break
        if not clause_matches(cl, v):
            return False

    if not litho_filter_matches(r, hole, from_depth, to_depth):
        return False
    return True


def _as_numeric(value: Any) -> Optional[float]:
    """Float fini ou None (texte « 1,2 » accepté)."""
    if not clause_value_ok(value):
        if value is None or isinstance(value, bool):
            return None
        try:
            parsed = float(str(value).strip().replace(",", "."))
        except (TypeError, ValueError):
            return None
        if parsed != parsed:  # NaN
            return None
        return parsed
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iter_assay_attribute_maps(holes_or_intervals) -> list:
    """Dicts d'attributs depuis des forages, des intervalles, ou des dicts."""
    out = []
    for obj in holes_or_intervals or []:
        assays = getattr(obj, "assays", None)
        if assays is not None:
            for iv in assays:
                out.append(dict(getattr(iv, "attributes", None) or {}))
            continue
        attrs = getattr(obj, "attributes", None)
        if attrs is not None:
            out.append(dict(attrs or {}))
        elif isinstance(obj, dict):
            out.append(dict(obj))
    return out


def collect_element_values(element: str, holes_or_intervals) -> list:
    """Valeurs numériques présentes pour ``element`` (projet / coupe)."""
    el = str(element or "").strip()
    if not el:
        return []
    values = []
    for attrs in _iter_assay_attribute_maps(holes_or_intervals):
        raw = attrs.get(el)
        if raw is None:
            for key, val in attrs.items():
                if str(key).strip() == el:
                    raw = val
                    break
        num = _as_numeric(raw)
        if num is not None:
            values.append(num)
    return values


def element_value_range(element: str, holes_or_intervals):
    """``(vmin, vmax)`` des valeurs réelles, ou None si rien."""
    vals = collect_element_values(element, holes_or_intervals)
    if not vals:
        return None
    return (min(vals), max(vals))


def outline_draw_elements(clause_elements, displayed_elements) -> list:
    """Pistes où dessiner le contour.

    Intersection règle ∩ pistes affichées. Si vide (ex. règle Cu alors
    que seule Fe est à l'écran) → 1ʳᵉ piste affichée, pour que le hit
    reste visible. Le *match* (ET des clauses) ne change pas.
    """
    clauses = []
    for raw in clause_elements or []:
        el = str(raw or "").strip()
        if el and el not in clauses:
            clauses.append(el)
    displayed = []
    for raw in displayed_elements or []:
        el = str(raw or "").strip()
        if el and el not in displayed:
            displayed.append(el)
    hit = [el for el in clauses if el in displayed]
    if hit:
        return hit
    if displayed:
        return [displayed[0]]
    return []


# ---------------------------------------------------------------------------
# v2.9.122 — piste Intercepts (blocs pleins, hors teneurs)
# ---------------------------------------------------------------------------
INTERCEPT_SLOT_WIDTH = 8.0
INTERCEPT_SLOT_GAP = 1.5
INTERCEPT_GUTTER_FILL = "#F4F6F7"
INTERCEPT_GUTTER_STROKE = "#D5DBDB"
INTERCEPT_BLOCK_STROKE = "#1A252F"


def intercept_track_wanted(rules) -> bool:
    """True dès qu'une règle est active — indépendant des matchs."""
    return bool(active_rules(rules))


def intercept_track_width(n_active: int) -> float:
    """Largeur scène de la piste (N colonnes + gaps). 0 si aucune règle."""
    try:
        n = int(n_active or 0)
    except (TypeError, ValueError):
        n = 0
    n = max(0, min(n, MAX_RULES))
    if n <= 0:
        return 0.0
    if n == 1:
        return float(INTERCEPT_SLOT_WIDTH)
    return (float(n) * INTERCEPT_SLOT_WIDTH
            + float(n - 1) * INTERCEPT_SLOT_GAP)


def intercept_slot_layout(
    n_active: int,
    track_inner: float,
    track_width: float,
    side: str = "left",
) -> list:
    """Sous-voies de la piste intercepts.

    Slot 0 (cyan) = plus proche du trou / des teneurs (inner).
    2 règles actives = 2 colonnes même si l'une n'a aucun match.
    """
    try:
        n = int(n_active or 0)
    except (TypeError, ValueError):
        n = 0
    n = max(0, min(n, MAX_RULES))
    if n <= 0:
        return []
    sign = 1.0 if str(side) == "right" else -1.0
    inner0 = float(track_inner)
    total = max(float(track_width or 0.0), 0.0)
    gap = float(INTERCEPT_SLOT_GAP)
    if n == 1:
        width = total if total > 0.0 else float(INTERCEPT_SLOT_WIDTH)
        outer = inner0 + sign * width
        return [{"index": 0, "inner": inner0, "outer": outer, "width": width}]
    usable = max(total - gap * (n - 1), 0.0)
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
        cursor = outer + sign * gap
    return out


def anchor_element(rule: Optional[dict]) -> str:
    """Élément ancre pour la géométrie de contour (1ʳᵉ clause)."""
    r = normalize_rule(rule)
    clauses = r.get("clauses") or []
    if clauses:
        return str(clauses[0].get("element") or "")
    return str(r.get("element") or "")


def explain_match(
    rule: dict,
    *,
    element: str = "",
    value: float = 0.0,
    attributes: Optional[dict] = None,
    unit: str = "",
) -> str:
    """Texte de justification tooltip (dock)."""
    r = normalize_rule(rule)
    parts = []
    attrs = dict(attributes or {})
    if element and element not in attrs:
        attrs[str(element).strip()] = value
    u = f" {unit}" if unit else ""
    for cl in (r.get("clauses") or []):
        el = cl["element"]
        v = attrs.get(el)
        try:
            thr_s = f"{float(cl['value']):g}"
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("threshold_rule : explain_match", _exc)
            thr_s = str(cl.get("value"))
        if clause_value_ok(v):
            try:
                val_s = f"{float(v):g}"
            except Exception as _exc:
                from .diagnostics import log_swallowed
                log_swallowed("threshold_rule : explain_match", _exc)
                val_s = str(v)
            ok = clause_matches(cl, v)
            mark = "OK" if ok else "non"
            parts.append(f"{el} = {val_s}{u} {cl['operator']} {thr_s}{u} ({mark})")
        else:
            parts.append(f"{el} : non mesuré → ET non satisfait")
    base = "  ET  ".join(parts) if parts else ""
    filt = r.get("litho_filter") or []
    if filt:
        base = (base + f"  ·  litho {', '.join(filt)}").strip(" ·")
    return base


def operator_label(op: str) -> str:
    return {
        ">": ">  (supérieur)",
        ">=": "≥  (supérieur ou égal)",
        "<": "<  (inférieur)",
        "<=": "≤  (inférieur ou égal)",
    }.get(op, op)


def group_contiguous_matches(
    matches: list,
    *,
    tol: float = 1e-6,
) -> list:
    """Regroupe matchs adjacents (même trou + élément ancre)."""
    if not matches:
        return []
    buckets: dict = {}
    for m in matches:
        if not isinstance(m, dict):
            continue
        key = (str(m.get("hole_id") or ""), str(m.get("element") or ""))
        buckets.setdefault(key, []).append(m)

    groups: list = []
    for _key, items in buckets.items():
        items = sorted(
            items,
            key=lambda d: (
                float(d.get("from_depth", 0.0) or 0.0),
                float(d.get("to_depth", 0.0) or 0.0),
            ),
        )
        cur: list = []
        cur_to = None
        for m in items:
            try:
                a = float(m.get("from_depth", 0.0) or 0.0)
                b = float(m.get("to_depth", 0.0) or 0.0)
            except (TypeError, ValueError):
                if cur:
                    groups.append(cur)
                    cur = []
                    cur_to = None
                groups.append([m])
                continue
            if b < a:
                a, b = b, a
            if cur and cur_to is not None and a <= float(cur_to) + float(tol):
                cur.append(m)
                cur_to = max(float(cur_to), b)
            else:
                if cur:
                    groups.append(cur)
                cur = [m]
                cur_to = b
        if cur:
            groups.append(cur)
    return groups


def _legend_element_name(element: str) -> str:
    """Fe_pct → Fe (même règle que les libellés de piste)."""
    raw = str(element or "").strip()
    if not raw:
        return ""
    try:
        from .multi_assay import _split_element_unit
        symbol, _inf = _split_element_unit(raw)
        return symbol or raw
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("Légende : _legend_element_name", _exc)
        # module multi_assay optionnel
        return raw


def legend_label(
    rule: dict | None,
    *,
    color_name: str = "cyan",
    unit: str = "",
    units: Optional[dict] = None,
) -> str:
    """Texte unique légende seuil (dock + export PNG).

    v2.9.129 — plus « Contour … » : les matches sont des blocs pleins
    (piste Intercepts). Une clause : cyan · Fe > 10 %
    Multi ET : cyan · Fe > 10 % ET Cu >= 1 ppm
    + (litho : QMAG, GMS) si filtre.
    """
    r = normalize_rule(rule)
    if not is_active(r):
        return ""
    color = str(color_name or "cyan").strip() or "cyan"
    units = dict(units or {})
    clauses = r.get("clauses") or []
    # v2.9.111 — unit globale seulement si 1 clause (évite Fe % ET Cu %)
    global_unit = str(unit or "").strip() if len(clauses) <= 1 else ""
    parts = []
    for cl in clauses:
        el = _legend_element_name(cl["element"])
        try:
            thr_s = f"{float(cl['value']):g}"
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Légende : legend_label", _exc)
            thr_s = str(cl.get("value"))
        u = str(units.get(cl["element"]) or global_unit or "").strip()
        if u == "%":
            val_part = f"{thr_s} %"
        elif u:
            val_part = f"{thr_s} {u}"
        else:
            val_part = thr_s
        parts.append(f"{el} {cl['operator']} {val_part}")
    body = " ET ".join(parts)
    text = f"{color} · {body}"
    filt = r.get("litho_filter") or []
    if filt:
        text += f" (litho : {', '.join(filt)})"
    return text
