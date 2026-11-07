"""Palettes génétiques — v2.9.77 conflit-free litho≠altéro.

Litho = aplats vifs (géologue lit ROCHE). Altération = pastels clairs
(géologue lit ALTÉRATION). Aucun hex partagé. Suggestions seulement.

Base historique : 21/08/2026 (CM-05, arbitré).

Source : fichiers `litho_palette.json` et `alt_palette.json` déposés par
l'utilisateur à la racine du projet (palette conçue en espace OKLCH, 57
familles espacées en distance perceptuelle ΔE2000, clusters génétiques) +
page `palette_geologique.html` (règle des composites : dégradé des
couleurs parentes).

Rôle : une SEULE source de vérité pour les couleurs de base des familles
géologiques.  `lithology_taxonomy.LITHOLOGY_FAMILIES` et
`alteration_taxonomy.ALTERATION_FAMILIES` puisent leurs hex ici au lieu de
les dupliquer.  Les 8 compléments historiques altération v2.7.9 (hors
palette) gardent leurs couleurs — indiqués explicitement.

Pure Python, sans Qt ni QGIS — testable hors QGIS.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Palette lithologie (30 familles · aplats vifs) — verbatim litho_palette.json
# ---------------------------------------------------------------------------
LITHO_BASE = {
    # v2.9.77 — aplats VIFS (roche) ; 0 conflit avec ALTER
    "felsique": ("#AF7AC5", "Felsique"),
    "intermediaire": ("#148F77", "Intermédiaire"),
    "mafique": ("#1A5276", "Mafique"),
    "ultramafique": ("#145A32", "Ultramafique"),
    "intrusive_alcaline": ("#6C3483", "Intrusive alcaline"),
    "felsique_specialise": ("#5B2C6F", "Intrusive felsique spécialisé"),
    "pegmatitique": ("#8E44AD", "Pegmatitique"),
    "volcanique_felsique": ("#7D3C98", "Volcanique felsique"),
    "volcanique_intermediaire": ("#117A65", "Volcanique intermédiaire"),
    "volcanique_mafique": ("#1C2833", "Volcanique mafique"),
    "pyroclastique": ("#E67E22", "Pyroclastique"),
    "volcanoclastique": ("#D35400", "Roche volcanoclastique"),
    "sedimentaire_grossiere": ("#A04000", "Sédimentaire grossière"),
    "sedimentaire_detritique": ("#D4AC0D", "Sédimentaire détritique"),
    "carbonatee_litho": ("#2471A3", "Carbonatée"),
    "chimique_evaporitique": ("#B7950B", "Chimique / évaporitique"),
    "metam_pelitique": ("#2874A6", "Métamorphique pélitique"),
    "metam_felsique": ("#9B59B6", "Métamorphique felsique"),
    "metam_mafique": ("#196F3D", "Métamorphique mafique"),
    "metam_ultramafique": ("#0B5345", "Métamorphique ultramafique"),
    "quartzite": ("#5DADE2", "Quartzite"),
    "skarn_calcosilicatee": ("#A93226", "Skarn / calco-silicatée"),
    "veine": ("#F1C40F", "Veine / veinule"),
    "formation_fer": ("#922B21", "Formation de fer"),
    "roche_minerai": ("#C0392B", "Roche riche en minerai"),
    "roche_carbonee": ("#212F3C", "Roche carbonée"),
    "laterite_regolithe": ("#CA6F1E", "Latérite / régolithe"),
    "alluvion_colluvion": ("#884EA0", "Alluvion / colluvion"),
    "eluvion": ("#BA4A00", "Éluvion"),
    "inconnue_autre": ("#7F8C8D", "Inconnue / autre"),
}

# ---------------------------------------------------------------------------
# Palette altération (27 familles · bandes pastel) — verbatim alt_palette.json
# ---------------------------------------------------------------------------
ALTER_BASE = {
    # v2.9.77 — pastels CLAIRS (altération) ; 0 conflit avec LITHO
    "argileuse": ("#FCE4D6", "Argileuse"),
    "argilique_avancee": ("#FAD7A0", "Argilique avancée"),
    "argilique_intermediaire": ("#F5CBA7", "Argilique intermédiaire"),
    "chloritique": ("#D5F5E3", "Chloritique"),
    "sericitisee": ("#F5EEF8", "Séricite / Phyllique"),
    "siliceuse": ("#D6EAF8", "Siliceuse / Silicification"),
    "potassique": ("#FADBD8", "Potassique"),
    "carbonatee": ("#FCF3CF", "Carbonatée"),
    "epidotique": ("#ABEBC6", "Épidote"),
    "albitique": ("#EBF5FB", "Albitisation"),
    "tourmalinisee": ("#D4E6F1", "Tourmalinisation"),
    "propylitique": ("#E8F8F5", "Propylitique"),
    "phyllique_avancee": ("#EBDEF0", "Phyllique avancée"),
    "sodique": ("#AED6F1", "Sodique"),
    "calcosilicatee": ("#D0ECE7", "Calco-silicatée"),
    "skarn": ("#A9DFBF", "Skarn"),
    "greisen": ("#E8DAEF", "Greisen"),
    "sulfatee": ("#F9E79F", "Sulfatée"),
    "oxydee": ("#F5B7B1", "Oxydée"),
    "ferrifere": ("#F5C6CB", "Ferrifère"),
    "manganesifere": ("#F4ECF7", "Manganésifère"),
    "dolomitisation": ("#FEF9E7", "Dolomitisation"),
    "serpentinisation": ("#A3E4D7", "Serpentinisation"),
    "talc_carbonate": ("#D1F2EB", "Talc-carbonate"),
    "feldspathique": ("#FDEDEC", "Feldspathique"),
    "zeolitique": ("#F9EBEA", "Zéolitique"),
    "blanchiment": ("#F8F9F9", "Blanchiment / Bleaching"),
}

# Familles composites et leurs parents (règle du HTML : « issue de A+B »).
# Le dégradé suit l'ordre des parents tels qu'ils se lisent dans le texte.
COMPOSITE_PARENTS = {
    "propylitique": ("chloritique", "epidotique", "carbonatee"),
    "phyllique_avancee": ("sericitisee", "siliceuse"),
    "argilique_avancee": ("argileuse",),
    "argilique_intermediaire": ("argileuse",),
}


def family_base(domain: str, family_key: str) -> str | None:
    """Hex palette d'une famille, ou None si hors palette (compléments)."""
    table = ALTER_BASE if domain == "alteration" else LITHO_BASE
    entry = table.get(str(family_key or ""))
    return entry[0] if entry else None


def composite_stops(domain: str, family_key: str) -> list[str]:
    """Parents' hex for a composite family — [] when not composite or no
    parent has a palette colour (never invented)."""
    if domain != "alteration":
        return []
    stop_hexes = []
    for parent in COMPOSITE_PARENTS.get(str(family_key or ""), ()):
        hex_value = family_base(domain, parent)
        if hex_value:
            stop_hexes.append(hex_value)
    return stop_hexes
