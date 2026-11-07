"""Alteration taxonomy (v2.7.9 — « piste par piste », phase 1).

La BIBLIOTHÈQUE DES 27 GRANDES FAMILLES (v2.7.10.20, arbitrage écran
20/08/2026) avec couleurs PASTEL de base et indicateurs/enfants enrichis,
plus huit compléments historiques v2.7.9 en pastel. Le moteur de mots-clés
SUGGÈRE une famille pour un code brut. Suggestions feed the project
Référentiel only (colour + family label) — the source data is never
rewritten, a value is never reclassified into another table, et un choix
de couleur existant gagne toujours (défauts seulement, guidé-libre).

Hierarchy convention (user decision, 19/08/2026) :
    Famille principale → sous-type → minéral associé
The family drives the band colour ; the raw value keeps its detail ;
l'intensité n'est portée QUE par la largeur de bande (jamais la couleur).

Priority rule : multi-mineral families (skarn, propylitique, greisen…)
require at least 2 of their keywords ; single-mineral families match on
1. Families are tested most-specific first, so CHLORITE_EPIDOTE reads
Propylitique while EPIDOTE alone reads Épidote.
"""

from __future__ import annotations

# Each family : (key, label, colour, identity_keywords, mineral_keywords, min_matches)
# v2.7.9.2 — « identity_keywords » : le nom de la famille lui-même (et ses
# variantes) suffit à lui seul (PROPYLITIQUE_FAIBLE → Propylitique, le bug
# remonté où il retombait sur une couleur violette automatique). Les
# couleurs Argileuse / Potassique / Tourmalinisée suivent les ajustements
# de contraste validés à l'écran (#E0C048 / #D87093 / #333333).
ALTERATION_FAMILIES: tuple = (
    # =====================================================================
    # v2.7.10.20 — BIBLIOTHÈQUE DES 27 GRANDES FAMILLES (arbitrage écran
    # 20/08/2026) : couleurs PASTEL de base, indicateurs/enfants enrichis.
    # Principes actés :
    #   - la COULEUR identifie la grande famille ; les indicateurs/enfants
    #     servent À L'AUTOMATISME de suggestion ; l'intensité reste portée
    #     par la largeur de bande, jamais par la couleur ;
    #   - la bibliothèque n'est qu'un DÉFAUT de suggestion : un choix de
    #     couleur existant ou explicite dans le Référentiel gagne toujours
    #     (« défauts seulement », guidé-libre) — aucune valeur du projet
    #     n'est réécrite.
    # Ordre = plus spécifique d'abord : les familles multi-minéraux
    # (min_matches ≥ 2) devancent les familles simples.
    # =====================================================================
    # --- familles composites / avancées (table 11-17, 22, 24, 27) ---------
    ("phyllique_avancee", "Phyllique avancée", "#EBDEF0",
     ("phyllique_avancee", "phyllique avancee", "advanced_phyllic",
      "phyllique avancee", "phyllique avancée", "advanced phyllic",
      "phyllic advanced"),
     ("sericite", "séricite", "quartz", "pyrite"), 2),
    ("argilique_avancee", "Argilique avancée", "#FAD7A0",
     ("argilique_avancee", "argilique avancee", "advanced_argillic", "=al",
      "alunitisation",
      "argilique avancee", "argilique avancée", "advanced argillic",
      "argillic advanced"),
     ("kaolinite", "dickite", "alunite", "pyrophyllite"), 2),
    ("argilique_intermediaire", "Argilique intermédiaire", "#F5CBA7",
     ("argilique_intermediaire", "argilique intermediaire",
      "intermediate_argillic", "argilique intermédiaire",
      "intermediate argillic"),
     ("illite", "smectite", "montmorillonite", "kaolinite"), 2),
    ("greisen", "Greisen", "#E8DAEF",
     ("greisen", "greisenisee", "greisenisée", "greisenisation"),
     ("quartz", "muscovite", "sericite", "séricite", "topaze", "topaz",
      "tourmaline", "fluorite", "fluorine"), 2),
    ("skarn", "Skarn", "#A9DFBF",
     ("skarn", "=gt", "garnet_alt"),
     ("grenat", "garnet", "pyroxene", "pyroxène", "diopside",
      "hedenbergite", "wollastonite", "vesuvianite", "vesuvian"), 2),
    ("propylitique", "Propylitique", "#E8F8F5",
     ("propylitique", "propilitique", "propylitisation", "propylitic", "=pr"),
     ("chlorite", "epidote", "épidote", "carbonate", "calcite", "albite"), 2),
    ("calcosilicatee", "Calco-silicatée", "#D0ECE7",
     ("calco-silicatee", "calcosilicatee", "calco_silicatee",
      "calco-silicates", "calc-silicate", "=cs"),
     ("actinolite", "actinote", "tremolite", "trémolite", "diopside",
      "wollastonite", "epidote", "épidote", "vesuvianite"), 2),
    ("talc_carbonate", "Talc-carbonate / magnésienne", "#D1F2EB",
     ("talc-carbonate", "talc_carbonate", "talcqueuse", "talcqueux",
      "magnesienne", "magnésienne"),
     ("talc", "magnesite", "magnésite", "carbonate"), 2),
    ("sodique", "Sodique", "#AED6F1",
     ("sodique", "sodisation", "sodic"),
     ("albite", "jadeite", "jadéite", "feldspath_sodique", "sodic_feldspar"), 2),
    ("dolomitisation", "Dolomitisation", "#FEF9E7",
     ("dolomitisation", "dolomitisee"),
     ("dolomite",), 1),
    ("blanchiment", "Blanchiment / bleaching", "#F8F9F9",
     ("blanchiment", "bleaching", "bleached"),
     ("bleaching",), 1),
    # --- familles simples (table 01-09, 18-21, 23-26) ----------------------
    ("sericitisee", "Séricite / phyllique", "#F5EEF8",
     ("sericitisee", "séricitisée", "phyllique", "sericite phyllite",
     "phyllic", "=se", "=sc", "=ph"),
     ("sericite", "séricite", "muscovite", "white mica", "mica"), 1),
    ("siliceuse", "Siliceuse / silicification", "#D6EAF8",
     ("siliceuse", "silicification", "silicifiee", "siliceous", "=si"),
     ("silicif", "silice", "quartzif", "quartz", "opal", "opale",
      "chalcedony", "calcédoine", "chert"), 1),
    ("potassique", "Potassique", "#FADBD8",
     ("potassique", "potassifere", "potassic", "=pb", "=pk"),
     ("k-feldspath", "k-feldspar", "k_feldspath", "k_feldspar",
      "orthoclase", "orthose", "microcline",
      "adularia", "adulaire", "biotite", "phlogopite"), 1),
    ("carbonatee", "Carbonatée", "#FCF3CF",
     ("carbonatee", "carbonatée", "carbonatation", "=ad", "=as", "=ca",
      "=cu", "=dc"),
     ("calcite", "ankerite", "ankérite", "siderite", "sidérite",
      "magnesite", "magnésite", "rhodochrosite", "carbonate"), 1),
    ("epidotique", "Épidote", "#ABEBC6",
     ("epidotique", "épidotique", "epidotisation", "=ep"),
     ("epidote", "épidote", "clinozoisite", "zoisite"), 1),
    ("albitique", "Albitisation", "#EBF5FB",
     ("albitique", "albitisation", "albitique", "=ab"),
     ("albite",), 1),
    ("tourmalinisee", "Tourmalinisation", "#D4E6F1",
     ("tourmalinisee", "tourmalinisée", "tourmalinisation"),
     ("tourmaline",), 1),
    ("chloritique", "Chloritique", "#D5F5E3",
     ("chloritique", "chloritisation", "=ch"),
     ("chlorite", "chloritized"), 1),
    ("argileuse", "Argileuse", "#FCE4D6",
     ("argileuse", "argilique", "argilisation", "clay_alteration",
      "argillic", "=ka", "=ar"),
     ("kaolinite", "illite", "smectite", "montmorillonite", "argile",
      "clay", "dickite", "pyrophyllite"), 1),
    ("sulfatee", "Sulfatée", "#F9E79F",
     ("sulfatee", "sulfatée", "sulfatisation", "sulphidic", "=su"),
     ("gypse", "gypsum", "anhydrite", "barytine", "barite", "jarosite",
      "alunite"), 1),
    ("oxydee", "Oxydée", "#F5B7B1",
     ("oxydee", "oxydée", "oxydation", "limonitisation", "=go", "=lm"),
     ("goethite", "hematite", "hématite", "limonite", "maghemite",
      "martite", "iron oxide", "oxyde de fer"), 1),
    ("ferrifere", "Ferrifère", "#F5C6CB",
     ("ferrifere", "ferrifère", "ferruginisation", "hematisation", "=he", "=ci"),
     ("magnetite", "magnétite", "goethite", "limonite"), 1),
    ("manganesifere", "Manganésifère", "#F4ECF7",
     ("manganesifere", "manganésifère", "manganesiferes", "=mn"),
     ("manganese", "manganèse", "manganite", "psilomelane", "psilomélane",
      "wad", "mn oxide", "carbonate de mn"), 1),
    ("serpentinisation", "Serpentinisation", "#A3E4D7",
     ("serpentinisation", "serpentinisee", "serpentinisée", "=sp"),
     ("serpentine", "antigorite", "chrysotile", "talc"), 1),
    ("feldspathique", "Feldspathique", "#FDEDEC",
     ("feldspathique", "feldspatisation"),
     ("feldspath", "feldspar", "plagioclase", "microcline", "orthoclase",
      "orthose"), 1),
    ("zeolitique", "Zéolitique", "#F9EBEA",
     ("zeolitique", "zéolitique", "zeolitisation"),
     ("zeolite", "zéolite", "laumontite", "prehnite", "préhnite"), 1),
    # --- compléments historiques v2.7.9 (pastels) ---------------------------
    # Familles conservées au-delà des 27 : elles ne tirent leur couleur que
    # si aucune association de la bibliothèque ne correspond (jamais
    # d'invention sur les données, jamais de réécriture).
    ("hematitique", "Hématitique", "#E59866",
     ("hematitique", "hématitique", "hematitisation"),
     ("speculaire",), 1),
    ("biotitique", "Biotitique", "#F1E3E3",
     ("biotitique", "biotitisation"), (), 1),
    ("fluoritee", "Fluoritée", "#F1EEE3",
     ("fluoritee", "fluoritée", "fluoritisation"),
     ("fluorite", "fluorine"), 1),
    ("phosphatee", "Phosphatée", "#E9F1E3",
     ("phosphatee", "phosphatée", "phosphatisation"),
     ("apatite", "phosphate"), 1),
    ("amphibolitique", "Amphibolitique / actinolitique", "#58D68D",
     ("amphibolitique", "actinolitique"),
     ("amphibole",), 1),
    ("sodique_calcique", "Sodique-calcique", "#E3F1E8",
     ("calcique", "sodique-calcique", "sodique_calcique"), (), 2),
    ("supergene", "Supergène", "#E3F0F1",
     ("supergene", "supergène", "supergen", "=sg"),
     ("chrysocolle", "malachite", "azurite"), 1),
    ("hydrothermale", "Hydrothermale indifférenciée", "#AAB7B8",
     ("hydrothermal", "hydrothermale", "steam-heated", "steam heated",
     "steam_heated", "=sh"),
     ("alteration", "altération"), 1),
)


# The alteration track owns these colours exclusively (user decision).
RESERVED_ALTERATION_COLORS: frozenset[str] = frozenset(
    colour.casefold() for (_key, _label, colour, _id, _kw, _n) in ALTERATION_FAMILIES)

# v2.7.10.20 — presets PASTEL du sélecteur de couleur du Référentiel
# (guidé-libre : proposés en tête, tout choix explicite reste accepté).
PASTEL_PRESETS: tuple = tuple(
    colour for (_key, _label, colour, _id, _kw, _n) in ALTERATION_FAMILIES[:27])

def _contains(code_folded: str, keyword: str) -> bool:
    # v2.7.10.24 — « =xyz » = correspondance EXACTE (codes abrégés
    # d'utilisateur : PR, CH, GRA…), sinon sous-chaîne (historique).
    if keyword.startswith("="):
        return code_folded == keyword[1:]
    return keyword in code_folded


def suggest_alteration_family(raw_code: str) -> dict | None:
    """Suggest ``{"key", "label", "color"}`` for a raw alteration code.

    v2.7.9.2 — deux niveaux :
    1. **identité** : le nom de la famille lui-même dans la valeur
       (PROPYLITIQUE_FAIBLE → Propylitique) suffit à lui seul ;
    2. sinon, les familles multi-minéraux exigent ``min_matches``
       minéraux, les mono-minéraux une seule correspondance.
    L'ordre de recherche reste « famille spécifique d'abord ».
    """
    value = str(raw_code or "").strip()
    if not value:
        return None
    folded = unicodedata_normalize(value).casefold()
    for key, label, colour, identity, keywords, minimum in ALTERATION_FAMILIES:
        if any(_contains(folded, marker) for marker in identity):
            return {"key": key, "label": label, "color": colour}
    for key, label, colour, _identity, keywords, minimum in ALTERATION_FAMILIES:
        hits = sum(1 for keyword in keywords if _contains(folded, keyword))
        if hits >= minimum:
            return {"key": key, "label": label, "color": colour}
    return None


def suggest_alteration_pattern(raw_code: str) -> str:
    """Suggested intra-family hatch pattern (v2.7.9.3).

    The FAMILY drives the band colour ; several raw codes sharing a family
    (CHLORITE, CHLORITE_MAGNETITE, CHLORITE_EPIDOTE…) would otherwise read
    as identical green bands — the « collision verte » remontée à l'écran.
    The pattern differentiates the sub-codes :

    - marqueurs minéraux : magnétite → pointillés, épidote → lignes
      verticales, chlorite → base pleine ; combinaisons : deux marqueurs
      → croix, trois → croix en X ;
    - qualificatif d'intensité dans le code (FAIBLE / MOYEN / FORT…) →
      pointillés fins / moyens / denses (l'intensité s'exprime aussi en
      largeur de bande via le champ Intensité, AM-03) ;
    - code de famille seul → base pleine (le rang des sous-codes reste
      lisible par le libellé, l'infobulle et la légende).

    Suggestions uniquement : le Référentiel reste la source unique et
    chaque motif est modifiable.
    """
    value = unicodedata_normalize(str(raw_code or "")).casefold()
    if not value:
        return ""
    has_magnetite = "magnetite" in value
    has_epidote = "epidote" in value or "épidote" in value
    has_chlorite = "chlorite" in value
    markers = sum((has_magnetite, has_epidote, has_chlorite))
    if markers >= 2:
        if has_magnetite and has_epidote and has_chlorite:
            return "diagonal_cross"
        if has_magnetite and has_epidote:
            return "cross"
    if has_magnetite:
        return "dots"
    if has_epidote:
        return "vertical"
    if has_chlorite:
        return ""  # base pleine de la famille Chloritique
    # Qualificatifs d'intensité (aucun marqueur minéral).
    if any(token in value for token in ("faible", "weak", "legere", "légère")):
        return "dots_fin"
    if any(token in value for token in
           ("moyen", "moyenne", "modere", "modérée", "moderate")):
        return "dots_moyen"
    if any(token in value for token in ("fort", "forte", "strong", "intense")):
        return "dots_dense"
    return ""


def unicodedata_normalize(value: str) -> str:
    import unicodedata
    folded = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in folded if not unicodedata.combining(char))
