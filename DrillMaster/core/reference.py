"""Open project reference for codes, measured elements and shared symbols."""
from __future__ import annotations

import colorsys
import hashlib
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field


PATTERN_LABELS = {
    "": "Aucun (plein)",
    "none": "Aucun (plein)",
    "diagonal": "Diagonale \u2571",
    "backward_diagonal": "Diagonale \u2572",
    "cross": "Quadrillage +",
    "diagonal_cross": "Quadrillage \u00d7",
    "horizontal": "Lignes ⊥ axe (horizontales sur log)",
    "vertical": "Lignes // axe (verticales sur log)",
    "dots": "Pointillés clairsemés",
    # v2.7.8.2 — la famille de pointillés s'élargit : trois densités
    # réellement discernables sur une bande de 8 px (retour écran :
    # « on ne peut pas proposer autre chose ? »). Les familles
    # géométriques restent inchangées.
    "dots_fin": "Pointillés fins",
    "dots_moyen": "Pointillés moyens",
    "dots_dense": "Pointillés denses",
}
# v2.7.5 — every offered pattern is unmistakable on a 12 px band
# (feedback 18/08/2026 : « points » ressemblait à « dense »).  The old
# "dense" key is retired from the offered list and now reads as "dots"
# (the two were visually indiscernible by design : 75 % vs 37 % of the
# SAME dot grid — see normalise_pattern).
# v2.7.8.2 — trois densités de pointillés ajoutées (Dense3/Dense5/Dense7
# du jeu Qt, discernables sur 8 px).
PATTERN_KEYS = (
    "", "diagonal", "backward_diagonal", "cross", "diagonal_cross",
    "horizontal", "vertical", "dots", "dots_moyen", "dots_fin",
    "dots_dense")

# Fraction of the opacity applied to the SOLID underlay drawn beneath a
# pattern (v2.7.5) : the colour identity survives any motif choice, the
# motif rides on top.  35 % keeps the band clearly tinted without
# competing with the strokes.
# v2.7.10.26 — 35 % → 55 % : le motif n'est plus « la couleur de base »
# (les hachures passent en encre contrastée) ; la sous-couche renforcée
# garde la couleur de famille nettement présente sous le motif.
PATTERN_UNDERLAY_ALPHA_RATIO = 0.55

# v2.7.8 — the mineralization track is coded by TEXTURE, not colour :
# a single neutral ink + a deterministic hatch per style. This removes
# the colour competition between lithology / alteration / assays and the
# mineralization band on the same section.
MINERALIZATION_INK = "#5D6D7E"
_MINERALIZATION_PATTERN_POOL = (
    "diagonal", "backward_diagonal", "cross", "diagonal_cross",
    "horizontal", "vertical", "dots",
)


# v2.9.156 — palette pour l'assignation auto des couleurs de STYLE :
# 12 couleurs franchement distinctes (retour écran : « chaque style une
# couleur différente, je veux pas de pareil » — géré par le RÉFÉRENTIEL,
# source unique pour la coupe 2D ET la vue 3D).
DISTINCT_PALETTE = (
    "#E74C3C",  # rouge
    "#3498DB",  # bleu
    "#27AE60",  # vert
    "#F39C12",  # orange
    "#9B59B6",  # violet
    "#1ABC9C",  # turquoise
    "#E91E63",  # rose
    "#8D6E63",  # brun
    "#CDDC39",  # citron
    "#5D6D7E",  # gris acier
    "#16A085",  # vert profond
    "#D35400",  # orangé brûlé
)


def distinct_auto_colors(existing, count):
    """Couleurs DISTINCTES pour l'assignation auto (v2.9.156).

    Retourne ``count`` couleurs prises dans :data:`DISTINCT_PALETTE`
    DANS L'ORDRE, en SAUTANT celles déjà posées (``existing`` —
    comparaison hex insensible à la casse) ; si la palette est épuisée,
    passes suivantes en variantes assombries/éclaircies.  Pur (testé).
    """
    used = {str(c or "").strip().upper() for c in (existing or []) if c}
    count = int(count)
    out = []

    def _variant(base, factor):
        try:
            r, g, b = (int(base[i:i + 2], 16) for i in (1, 3, 5))
            return "#{:02X}{:02X}{:02X}".format(
                *(min(255, max(0, int(v * factor))) for v in (r, g, b)))
        except (ValueError, IndexError):
            return base

    for cycle in range(0, 26):
        # passe 0 : palette telle quelle ; passes suivantes : variantes
        factor = 1.0
        if cycle > 0:
            factor = 1.0 + 0.16 * ((cycle + 1) // 2) * (1 if cycle % 2 else -1)
            factor = max(0.4, min(1.6, factor))
        for base in DISTINCT_PALETTE:
            if len(out) >= count:
                return out
            color = base if cycle == 0 else _variant(base, factor)
            if color.upper() not in used:
                used.add(color.upper())
                out.append(color)
    return out


def cycle_pattern_list(values, count):
    """Répète ``values`` pour couvrir ``count`` éléments (ordre stable).

    v2.9.151 — assignation DÉTERMINISTE des motifs auto du Référentiel :
    le i-ᵉ code (ordre alphabétique) reçoit ``values[i % len(values)]``.
    Pur (testable sans Qt).
    """
    values = list(values or [])
    if not values or not count or count <= 0:
        return []
    return [values[i % len(values)] for i in range(int(count))]


def normalise_pattern(value: str) -> str:
    """Return a supported stable pattern key; old labels remain readable."""
    folded = unicodedata.normalize("NFKD", str(value or ""))
    folded = "".join(
        char for char in folded if not unicodedata.combining(char))
    folded = folded.strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        # v2.7.9 — « none » est préservé tel quel : c'est la valeur
        # explicite « transparent » de la minéralisation. Le normaliser en
        # vide (comme avant) le faisait revenir à « Auto » à la
        # réouverture — cause racine du bug remonté à l'écran.
        "": "", "none": "none", "aucun": "none", "rien": "none",
        "vide": "none", "transparent": "none",
        "solid": "", "plein": "",
        "diagonal": "diagonal", "forward_diagonal": "diagonal",
        "hachures": "diagonal", "hachures_diagonales": "diagonal",
        "diagonale": "diagonal",
        "backward_diagonal": "backward_diagonal",
        "diagonal_inverse": "backward_diagonal",
        "diagonale_inversee": "backward_diagonal",
        "cross": "cross", "croise": "cross", "croisee": "cross",
        "quadrillage": "cross",
        "diagonal_cross": "diagonal_cross", "croise_diagonal": "diagonal_cross",
        "quadrillage_x": "diagonal_cross", "diagcross": "diagonal_cross",
        "x": "diagonal_cross",
        "horizontal": "horizontal", "horizontales": "horizontal",
        "lignes_horizontales": "horizontal",
        "vertical": "vertical", "verticales": "vertical",
        "lignes_verticales": "vertical",
        "points": "dots", "dots": "dots", "pointille": "dots",
        "pointilles": "dots", "pointe": "dots",
        # v2.7.8.2 — densités de pointillés
        "dots_fin": "dots_fin", "pointilles_fins": "dots_fin",
        "points_fins": "dots_fin",
        "dots_moyen": "dots_moyen", "pointilles_moyens": "dots_moyen",
        "points_moyens": "dots_moyen",
        "dots_dense": "dots_dense", "pointilles_denses": "dots_dense",
        "points_denses": "dots_dense",
        # v2.7.5 — "dense" was visually indiscernible from "dots" by
        # design; it now reads as sparse dots everywhere (documented in
        # AUDIT_V2.7.5, never a silent semantic change of stored data).
        "dense": "dots", "dense_pattern": "dots",
    }
    return aliases.get(folded, "")


# v2.7.10.20 — presets VIFS du sélecteur de couleur (lithologie) :
# proposés en tête du QColorDialog du Référentiel, jamais imposés
# (arbitrage écran : guidé-libre, le choix explicite gagne toujours).
# v2.7.10.22 — source unique déplacée : les 30 couleurs vives de famille
# de la bibliothèque lithologique (core/lithology_taxonomy).
from .lithology_taxonomy import LITHO_PRESETS as VIVID_PRESETS


# ---------------------------------------------------------------------------
# Gammes de couleur référentiel (v2.9.88) — séparation litho VIF / altéro PASTEL
# ---------------------------------------------------------------------------
# Objectif produit : éviter les conflits de lecture coupe (litho = identité
# vive, altération = voile pastel).  Le sélecteur du Référentiel ne propose
# QUE la gamme du domaine ; un choix hors gamme est ramené (clamp).

def _hex_to_hsv(hexcode: str) -> tuple[float, float, float]:
    c = (hexcode or "#CCCCCC").strip().lstrip("#")
    if len(c) != 6:
        c = "CCCCCC"
    try:
        r, g, b = (int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        r = g = b = 0.8
    return colorsys.rgb_to_hsv(r, g, b)


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(
        h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return "#{:02X}{:02X}{:02X}".format(*(round(x * 255) for x in (r, g, b)))


NAMED_COLOR_PRESETS: tuple = (
    "#FFFFFF", "#F5F5F5", "#DDDDDD", "#AAAAAA", "#777777", "#333333",
    "#8B0000", "#C0392B", "#E74C3C", "#FF6B6B",
    "#FF8C00", "#E67E22", "#F39C12",
    "#FFD700", "#F1C40F", "#FFF3A0", "#EEDC82",
    "#9ACD32", "#27AE60", "#1E8449", "#0B5345",
    "#00CED1", "#17A2B8", "#1F618D", "#0B3D91",
    "#4B0082", "#6C3483", "#8E44AD", "#B39DDB", "#D7BDE2",
    "#FF69B4", "#F8C8DC",
    "#8B4513", "#A0522D", "#D2B48C", "#F5DEB3",
)


def is_neutral_tone(hexcode: str) -> bool:
    """v2.9.313 — blanc/gris/noir : hors clamp (utilisables partout)."""
    _h, s, _v = _hex_to_hsv(hexcode)
    return s <= 0.15


def is_pastel_tone(hexcode: str) -> bool:
    """Pastel affirmé : chroma modérée, valeur claire (altération)."""
    _h, s, v = _hex_to_hsv(hexcode)
    return s <= 0.55 and v >= 0.62


def is_vivid_tone(hexcode: str) -> bool:
    """Vif : saturation franche, valeur ni lavée ni noire (lithologie).

    v2.9.313 — le plafond 0.92 refusait les jaunes/rouges francs
    (#FFD700, #FF6B6B) : accepté jusqu'à 1.0."""
    _h, s, v = _hex_to_hsv(hexcode)
    return s >= 0.42 and 0.28 <= v


def clamp_to_pastel(hexcode: str) -> str:
    """Ramène une couleur dans la gamme pastel altération."""
    h, s, v = _hex_to_hsv(hexcode)
    s = min(max(s, 0.18), 0.52)
    v = min(max(v, 0.68), 0.94)
    if s < 0.18:
        s = 0.22
    return _hsv_to_hex(h, s, v)


def clamp_to_vivid(hexcode: str) -> str:
    """Ramène une couleur dans la gamme vive lithologie."""
    h, s, v = _hex_to_hsv(hexcode)
    s = min(max(s, 0.50), 0.95)
    v = min(max(v, 0.38), 0.88)
    return _hsv_to_hex(h, s, v)


def clamp_domain_color(domain_key: str, hexcode: str) -> str:
    """Clamp selon le domaine ; autres domaines inchangés."""
    value = (hexcode or "").strip().upper()
    if not value.startswith("#") or len(value) != 7:
        return value or "#CCCCCC"
    if is_neutral_tone(value):
        return value
    if domain_key == "alteration":
        return clamp_to_pastel(value) if not is_pastel_tone(value) else value
    if domain_key == "lithology":
        return clamp_to_vivid(value) if not is_vivid_tone(value) else value
    return value


def domain_color_palette(domain_key: str) -> list[str]:
    """Pastilles proposées au sélecteur (uniquement la gamme du domaine)."""
    seen: set[str] = set()
    out: list[str] = []

    def _add(hexcode: str):
        h = (hexcode or "").strip().upper()
        if not h.startswith("#") or len(h) != 7:
            return
        if not is_neutral_tone(h):
            if domain_key == "alteration":
                h = h if is_pastel_tone(h) else clamp_to_pastel(h)
            elif domain_key == "lithology":
                h = h if is_vivid_tone(h) else clamp_to_vivid(h)
        if h not in seen:
            seen.add(h)
            out.append(h)

    for c in NAMED_COLOR_PRESETS:
        _add(c)
    if domain_key == "alteration":
        try:
            from .alteration_taxonomy import PASTEL_PRESETS, ALTERATION_FAMILIES
            for c in PASTEL_PRESETS:
                _add(c)
            for _k, _l, c, *_rest in ALTERATION_FAMILIES:
                _add(c)
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Couleur : domain_color_palette", _exc)
            # taxonomy optionnelle hors plugin packagé
            pass
        for hi in range(18):
            for s in (0.28, 0.38, 0.48):
                for v in (0.78, 0.88):
                    _add(_hsv_to_hex(hi / 18.0, s, v))
    elif domain_key == "lithology":
        try:
            from .lithology_taxonomy import LITHO_PRESETS, LITHOLOGY_FAMILIES
            for c in LITHO_PRESETS:
                _add(c)
            for _k, _l, c, *_rest in LITHOLOGY_FAMILIES:
                _add(c)
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("Couleur : domain_color_palette", _exc)
            # taxonomy optionnelle hors plugin packagé
            pass
        for hi in range(18):
            for s in (0.55, 0.72, 0.88):
                for v in (0.45, 0.62, 0.78):
                    _add(_hsv_to_hex(hi / 18.0, s, v))
    return out



def automatic_code_color(domain_key: str, raw_code: str) -> str:
    """Stable neutral colour for an unknown code; never implies a standard.

    v2.7.9 — the alteration families own their colours exclusively : any
    OTHER domain regenerates its automatic colour until it falls outside
    the reserved set (bounded loop, deterministic per code).
    """
    reserved = None
    if domain_key != "alteration":
        try:
            from .alteration_taxonomy import RESERVED_ALTERATION_COLORS
            reserved = RESERVED_ALTERATION_COLORS
        except ImportError:  # pragma: no cover — defensive
            reserved = None
    for attempt in range(8):
        digest = hashlib.sha1(
            f"{domain_key}:{raw_code}:{attempt}".encode("utf-8")).digest()
        hue = int.from_bytes(digest[:2], "big") / 65535.0
        # v2.7.10.20 — conventions validées à l'écran (arbitrage) :
        # lithologie = couleurs VIVES, altération = PASTEL, autres
        # domaines = rampe neutre historique. Déterministe par code,
        # comme toujours ; les choix existants ne sont jamais retouchés.
        if domain_key == "lithology":
            saturation = 0.62 + digest[2] / 255.0 * 0.23
            value = 0.62 + digest[3] / 255.0 * 0.18
        elif domain_key == "alteration":
            # v2.7.10.24 — pastel AFFIRMÉ (retour écran : le pastel vaporeux
            # n'était pas visible) : plus de chroma, un cran moins clair.
            saturation = 0.34 + digest[2] / 255.0 * 0.14
            value = 0.64 + digest[3] / 255.0 * 0.14
        else:
            saturation = 0.42 + digest[2] / 255.0 * 0.22
            value = 0.70 + digest[3] / 255.0 * 0.16
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colour = "#{:02X}{:02X}{:02X}".format(
            *(round(component * 255) for component in rgb))
        if reserved is None or colour.casefold() not in reserved:
            return colour
    return colour


@dataclass
class DomainEntry:
    raw_code: str
    label: str = ""
    normalized_code: str = ""
    rank: float | None = None
    color: str = ""
    # Kept for backward-compatible loading. Visibility and opacity are no
    # longer edited as reference semantics; views own them.
    opacity: int = 100
    pattern: str = ""
    visible: bool = True
    automatic: bool = True
    description: str = ""
    usage_count: int = 0
    newly_discovered: bool = False
    # Quantitative-field metadata (used by the assay_elements domain).
    symbol: str = ""
    source_unit: str = ""
    display_unit: str = ""
    precision: int | None = None
    # v2.7.9 — « piste par piste » :
    #   symbol_id : glyphe minéral (domaine minerals) ou texture de style
    #               (domaine mineralization_style) ; "none" = transparent.
    #   family    : famille d'altération suggérée (domaine alteration).
    symbol_id: str = ""
    family: str = ""
    detection_limit: float | None = None

    def __post_init__(self):
        self.pattern = normalise_pattern(self.pattern)
        try:
            self.usage_count = max(0, int(self.usage_count or 0))
        except (TypeError, ValueError):
            self.usage_count = 0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        allowed = set(cls.__dataclass_fields__)
        return cls(**{key: value for key, value in (data or {}).items()
                      if key in allowed})


@dataclass
class DomainDefinition:
    key: str
    label: str
    kind: str = "categorical"  # categorical | ordinal | multi_label | quantitative_fields
    entries: dict[str, DomainEntry] = field(default_factory=dict)

    def to_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            "kind": self.kind,
            "entries": {key: entry.to_dict()
                        for key, entry in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        domain = cls(
            key=data.get("key", ""),
            label=data.get("label", data.get("key", "")),
            kind=data.get("kind", "categorical"))
        domain.entries = {
            key: (value if isinstance(value, DomainEntry)
                  else DomainEntry.from_dict(value))
            for key, value in data.get("entries", {}).items()
        }
        return domain


@dataclass(frozen=True)
class ResolvedCategoryStyle:
    raw_code: str
    label: str
    color: str
    pattern: str = ""
    # v2.7.9.2 — le symbole du Référentiel voyage avec la résolution :
    # la coupe, la légende et les vues futures lisent TOUJOURS le même
    # symbol_id que celui affiché/choisi dans le Référentiel.
    symbol_id: str = ""
    # v2.7.9.7 — la VISIBILITÉ voyage aussi : décocher une entrée du
    # Référentiel la retire de la coupe, des légendes ET des couches QGIS.
    visible: bool = True
    automatic: bool = True


DEFAULT_DOMAINS = {
    "lithology": ("Lithologie", "categorical"),
    "alteration": ("Altération", "categorical"),
    "alteration_intensity": ("Intensité d’altération", "ordinal"),
    "mineralization_style": ("Style de minéralisation", "categorical"),
    "minerals": ("Minéraux", "multi_label"),
    "assay_elements": ("Éléments mesurés", "quantitative_fields"),
    # v2.9.258-rendu — structure types are open and editable in the same
    # Référentiel; the QGIS layer, (later) 2D and 3D all read this domain.
    "structure": ("Type de structure", "categorical"),
}

# v2.7.4 — domains where colour/pattern is intentionally NOT offered.
# These values drive something else than a colour (band width, tooltip
# label): proposing a colour control there would be a fake function
# (feedback 18/08/2026: "on peut changer couleurs alors qu'elle n'est
# même pas utilisée").  The day a future rendering consumes their colour,
# the entry is removed here — never silently.
SYMBOL_FREE_DOMAINS = {
    "alteration_intensity": (
        "La valeur règle la LARGEUR des bandes d’altération "
        "(faible → étroite, forte → pleine largeur) — la couleur "
        "n’est pas utilisée pour ce domaine."),
    "minerals": (
        "Les minéraux servent de libellés lisibles dans les infobulles "
        "des minéralisations (aucune bande automatique, AM-05) — la "
        "couleur n’est pas utilisée pour ce domaine."),
}


_FRENCH_LABEL_WORDS = {
    "alteration": "altération",
    "alteree": "altérée",
    "dissemine": "disséminé",
    "disseminee": "disséminée",
    "epidote": "épidote",
    "fiabilite": "fiabilité",
    "fort": "fort",
    "forte": "forte",
    "intensite": "intensité",
    "magnetite": "magnétite",
    "mineralisation": "minéralisation",
    "mineralisee": "minéralisée",
    "mineraux": "minéraux",
    "modere": "modéré",
    "moderee": "modérée",
    "qualite": "qualité",
    "sterile": "stérile",
}


def automatic_display_label(raw_code: str) -> str:
    """Create a readable French label while preserving the raw code."""
    raw = str(raw_code or "").strip()
    if not raw:
        return ""
    words = raw.replace("_", " ").split()
    rendered = []
    for word in words:
        folded = unicodedata.normalize("NFKD", word).casefold()
        folded = "".join(
            char for char in folded if not unicodedata.combining(char))
        rendered.append(_FRENCH_LABEL_WORDS.get(folded, word.casefold()))
    label = " ".join(rendered)
    return label[:1].upper() + label[1:] if label else raw


def _suggest_element_metadata(raw_code: str) -> dict:
    """Extract explicit unit suffixes without converting numeric values."""
    raw = str(raw_code or "").strip()
    parts = raw.replace("-", "_").split("_")
    unit_aliases = {
        "ppm": "ppm", "ppb": "ppb", "pct": "%", "percent": "%",
        "pourcent": "%", "%": "%", "gpt": "g/t", "gt": "g/t",
        "g/t": "g/t", "mgkg": "mg/kg", "ugg": "µg/g",
        "ozt": "oz/t",
    }
    compound_aliases = {
        "g_t": "g/t", "mg_kg": "mg/kg", "ug_g": "µg/g",
        "oz_t": "oz/t",
    }
    unit = ""
    suffix_parts = 0
    if len(parts) > 2:
        unit = compound_aliases.get(
            "_".join(part.casefold() for part in parts[-2:]), "")
        suffix_parts = 2 if unit else 0
    if not unit and len(parts) > 1:
        unit = unit_aliases.get(parts[-1].casefold(), "")
        suffix_parts = 1 if unit else 0
    element_parts = parts[:-suffix_parts] if suffix_parts else parts
    element = " ".join(element_parts) or raw
    symbol_source = element_parts[0] if element_parts else raw
    symbol = (
        symbol_source[:1].upper() + symbol_source[1:].lower()
        if symbol_source else "")
    return {
        "label": automatic_display_label(element),
        "symbol": symbol,
        "source_unit": unit,
    }


class ReferenceRepository:
    """Dynamic project reference; no closed list and no forced normalization."""

    def __init__(self, domains=None):
        self.domains: dict[str, DomainDefinition] = {}
        for key, (label, kind) in DEFAULT_DOMAINS.items():
            self.domains[key] = DomainDefinition(key, label, kind)
        for key, value in (domains or {}).items():
            domain = (value if isinstance(value, DomainDefinition)
                      else DomainDefinition.from_dict(value))
            if not domain.key:
                domain.key = key
            self.domains[key] = domain
        # v2.9.159 — styles de minéralisation : couleurs DISTINCTES par
        # défaut (retour écran : « il n'utilise pas les couleurs
        # différentes en 3D, j'aime pas »).  Les entrées AUTOMATIQUES
        # (jamais personnalisées) reçoivent la palette distincte dans
        # l'ordre des codes — les couleurs choisies manuellement sont
        # conservées et servent d'anti-collision.  La coupe 2D ET la
        # vue 3D résolvent via ce référentiel → mêmes couleurs partout.
        try:
            self.assign_distinct_style_colors()
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed("reference : __init__", _exc)
            pass  # le référentiel ne doit jamais empêcher l'ouverture
        # Improve only entries that are still automatic. User-written labels,
        # including deliberate unaccented forms, are never replaced.
        for domain in self.domains.values():
            for entry in domain.entries.values():
                if not entry.automatic:
                    continue
                if domain.kind == "quantitative_fields":
                    metadata = _suggest_element_metadata(entry.raw_code)
                    entry.label = metadata.get("label") or entry.label
                    entry.symbol = metadata.get("symbol") or entry.symbol
                    entry.source_unit = (
                        metadata.get("source_unit") or entry.source_unit)
                else:
                    entry.label = automatic_display_label(entry.raw_code)

    def assign_distinct_style_colors(self, domain_key="mineralization_style"):
        """Couleurs DISTINCTES pour les styles auto (v2.9.159).

        Les entrées ``automatic`` du domaine reçoivent la palette
        distincte dans l'ordre (tri des codes) ; les couleurs
        EXPLICITES (automatic=False) sont conservées et évitées.
        Appelée au chargement du référentiel (migration des anciennes
        couleurs hash) et utilisable à la demande (bouton « Couleurs
        auto »).  Pur côté données — aucune vue n'est impliquée.
        """
        domain = self.domains.get(domain_key)
        if domain is None:
            return
        kept = [str(e.color or "").strip().upper()
                for e in domain.entries.values()
                if str(e.color or "").strip()
                and not getattr(e, "automatic", True)]
        targets = sorted(
            code for code, e in domain.entries.items()
            if getattr(e, "automatic", True))
        if not targets:
            return
        colors = distinct_auto_colors(kept, len(targets))
        for code, color in zip(targets, colors):
            domain.entries[code].color = color

    def ensure_domain(self, key, label=None, kind="categorical"):
        if key not in self.domains:
            self.domains[key] = DomainDefinition(key, label or key, kind)
        else:
            if label and not self.domains[key].label:
                self.domains[key].label = label
            if kind and self.domains[key].kind == "categorical" and kind != "categorical":
                self.domains[key].kind = kind
        return self.domains[key]

    def discover(self, domain_key, values, label=None, kind="categorical"):
        """Add unknown raw values and refresh usage; never reject a value.

        v2.7.9.4 — pour le domaine « minerals », une valeur composite
        (``MAGNETITE_CHALCOPYRITE``) est éclatée en entrées PAR MINÉRAL :
        c'est exactement la granularité que la coupe dessine. Le
        Référentiel et les vues parlent enfin la même langue — un symbole
        choisi s'applique toujours, fini le « pas appliqué ».
        """
        domain = self.ensure_domain(domain_key, label, kind)
        raw_values = [str(value).strip() for value in values
                      if value is not None and str(value).strip()]
        if domain_key == "minerals":
            import re as _re
            expanded = []
            for value in raw_values:
                tokens = [
                    token for token in _re.split(r"[^A-Za-z0-9]+", value)
                    if token]
                expanded.extend(tokens or [value])
            raw_values = expanded
        counts = Counter(raw_values)
        for entry in domain.entries.values():
            entry.usage_count = counts.get(entry.raw_code, 0)
        added = []
        for raw, count in counts.items():
            metadata = (_suggest_element_metadata(raw)
                        if domain.kind == "quantitative_fields" else {})
            if raw in domain.entries:
                entry = domain.entries[raw]
                entry.usage_count = count
                if entry.automatic:
                    entry.label = (
                        metadata.get("label") or automatic_display_label(raw))
                    if metadata.get("symbol"):
                        entry.symbol = metadata["symbol"]
                    if metadata.get("source_unit"):
                        entry.source_unit = metadata["source_unit"]
                _apply_domain_suggestions(entry, domain_key, raw)
                continue
            # v2.9.159 — minéralisations : le NOUVEAU style prend la
            # première couleur DISTINCTE libre du domaine (les couleurs
            # des styles existants ne permutent jamais).
            if domain_key == "mineralization_style":
                used = {str(e.color or "").strip().upper()
                        for e in domain.entries.values() if e.color}
                color = next(
                    (c for c in DISTINCT_PALETTE if c.upper() not in used),
                    automatic_code_color(domain_key, raw))
            else:
                color = automatic_code_color(domain_key, raw)
            entry = DomainEntry(
                raw_code=raw,
                label=metadata.get("label") or automatic_display_label(raw),
                symbol=metadata.get("symbol", ""),
                source_unit=metadata.get("source_unit", ""),
                color=color,
                automatic=True,
                usage_count=count,
                newly_discovered=True)
            _apply_domain_suggestions(entry, domain_key, raw)
            domain.entries[raw] = entry
            added.append(entry)
        return added

    def get_entry(self, domain_key, raw_code):
        domain = self.domains.get(domain_key)
        return domain.entries.get(str(raw_code)) if domain else None

    def unused_entry_codes(self, domain_key) -> list[str]:
        """Codes with zero usage in a domain (v2.7.9.6).

        SAME definition as the « Non utilisées » filter of the
        Référentiel : ``usage_count == 0``, whatever the customisation
        state. The removal action and the filter can never disagree
        again (bug remonté : entrées marquées non utilisées mais
        « aucune entrée non utilisée » au retrait).
        """
        domain = self.domains.get(domain_key)
        if not domain:
            return []
        return sorted(
            (code for code, entry in domain.entries.items()
             if not entry.usage_count),
            key=str.casefold)


    def update_entry(self, domain_key, raw_code, **updates):
        domain = self.ensure_domain(domain_key)
        entry = domain.entries.get(str(raw_code))
        if entry is None:
            self.discover(domain_key, [raw_code])
            entry = domain.entries[str(raw_code)]
        for key, value in updates.items():
            if key in DomainEntry.__dataclass_fields__ and key != "raw_code":
                if key == "pattern":
                    value = normalise_pattern(value)
                setattr(entry, key, value)
        editable = {
            "label", "normalized_code", "rank", "color", "pattern",
            "description", "symbol", "source_unit", "display_unit",
            "precision", "detection_limit",
            # v2.7.9.3 — les symboles et familles font partie des choix
            # utilisateur : les passer par update_entry marque l'entrée
            # comme personnalisée (jamais ré-écrasée par une suggestion).
            "symbol_id", "family",
        }
        if editable.intersection(updates):
            entry.automatic = False
        return entry

    def reset_entry_style(self, domain_key, raw_code, fallback_color=""):
        entry = self.get_entry(domain_key, raw_code)
        if not entry:
            return None
        entry.color = fallback_color or automatic_code_color(domain_key, raw_code)
        entry.pattern = ""
        # Text metadata may still be customised; automatic here means the
        # symbol was reset, not that source values were changed.
        entry.automatic = not any((entry.normalized_code, entry.description))
        return entry

    def resolve(self, domain_key, raw_code, fallback_color="") -> ResolvedCategoryStyle:
        raw = str(raw_code or "")
        entry = self.get_entry(domain_key, raw)
        if entry:
            effective = entry
            visited = {raw}
            target_code = entry.normalized_code.strip()
            while target_code and target_code not in visited:
                visited.add(target_code)
                target = self.get_entry(domain_key, target_code)
                if target is None:
                    break
                effective = target
                target_code = target.normalized_code.strip()
            return ResolvedCategoryStyle(
                raw_code=raw,
                label=effective.label or entry.label or raw,
                color=effective.color or entry.color or fallback_color
                      or automatic_code_color(domain_key, raw),
                pattern=normalise_pattern(
                    effective.pattern or entry.pattern),
                symbol_id=effective.symbol_id or entry.symbol_id,
                visible=bool(effective.visible and entry.visible),
                automatic=entry.automatic and effective.automatic)
        return ResolvedCategoryStyle(
            raw_code=raw,
            label=raw,
            color=fallback_color or automatic_code_color(domain_key, raw),
            pattern="",
            symbol_id="",
            visible=True,
            automatic=True)

    def to_dict(self):
        return {key: domain.to_dict() for key, domain in self.domains.items()}

    @classmethod
    def from_dict(cls, data):
        return cls(data or {})


def _apply_domain_suggestions(entry, domain_key: str, raw_code: str):
    """v2.7.9 — « piste par piste » : suggestions automatiques par domaine.

    These are SUGGESTIONS in the Référentiel only — they never rewrite
    the source data and never reclassify a value into another table.
    Explicit user choices (entry.automatic == False) are always kept.
    """
    if entry is None:
        return
    if domain_key == "alteration":
        try:
            from .alteration_taxonomy import (
                suggest_alteration_family, suggest_alteration_pattern)
            family = suggest_alteration_family(raw_code)
        except ImportError:  # pragma: no cover — defensive
            family = None
        if family:
            # v2.7.9.4 — les suggestions ne jouent qu'une seule fois :
            # famille vide = jamais suggérée (nouvelle entrée OU ancienne
            # à migrer) → famille + couleur appliquées ensemble. Une
            # entrée déjà suggérée (ou personnalisée) n'est plus touchée.
            if entry.automatic and not entry.family:
                entry.family = family["label"]
                entry.color = family["color"]
            # v2.7.9.3 — motif intra-famille : la couleur de famille est
            # partagée, le motif différencie les sous-codes (CHLORITE vs
            # CHLORITE_MAGNETITE vs CHLORITE_EPIDOTE…).
            if entry.automatic and not entry.pattern:
                try:
                    entry.pattern = suggest_alteration_pattern(raw_code)
                except Exception as _exc:  # pragma: no cover — defensive
                    from .diagnostics import log_swallowed
                    log_swallowed("reference : _apply_domain_suggestions", _exc)
                    pass
        return
    # v2.7.10.4 — le domaine « minerals » n'a plus d'éditeur ni de rendu
    # (décision écran : on verra plus tard) : aucune suggestion de symbole.
    if domain_key == "mineralization_style":
        try:
            from .mineral_symbols import suggest_style_key
            key = suggest_style_key(raw_code)
        except ImportError:  # pragma: no cover — defensive
            key = None
        # Suggestion = le code 2 lettres du style reconnu (MA, VN…).
        # Valeur inconnue (STERILE…) : rien, jamais de code inventé.
        if key and entry.automatic and not entry.symbol_id:
            entry.symbol_id = key
        return
    if domain_key == "lithology":
        # v2.9.74 — MÊME flux que l'altération : suggestion famille =
        # aide à l'utilisateur, une seule fois ; choix explicite
        # (automatic=False) jamais réécrit. Pas de contrainte table vs
        # famille : la bibliothèque propose, l'utilisateur décide.
        try:
            from .lithology_taxonomy import suggest_lithology_family
            family = suggest_lithology_family(raw_code)
        except ImportError:  # pragma: no cover — defensive
            family = None
        if family and entry.automatic and not entry.family:
            entry.family = family["family"]
            entry.color = family["color"]
        return
