"""Classification of structure measurement codes into render families.

v2.9.260 patch — the 2D section must show the *orientation* of a structure
when the data allows it, while never inventing one.  The renderer and the
QC share exactly one classifier so a "non-orientable" type is never
penalised, and a "composite" type is never drawn with a misleading
tadpole/arrow.
"""

from __future__ import annotations

_NON_ORIENTABLE = {
    "nodule",
    "nodules",
    "concretion",
    "concretions",
    "concrétion",
    "concrétions",
    "geode",
    "geodes",
    "géode",
    "géodes",
    "lens",
    "lentille",
    "lentilles",
    "lentille tectonique",
    "boudin",
    "boudins",
    "boudinage",
    "boudiné",
    "boudinée",
    "stylolite",
    "stylolites",
    "stylolithe",
    "stylolithes",
    "stylolithic",
}

_COMPOSITE = {
    "strie",
    "stries",
    "stries de faille",
    "stries sur miroir de faille",
    "fault striation",
    "fault striations",
    "slickenside",
    "slickensides",
    "slickenside striation",
}

_LINEAR = {
    "lineation",
    "linéation",
    "lineations",
    "linéations",
    "linéation d'étirement",
    "stretching lineation",
    "plunging lineation",
    "fold axis",
    "fold axes",
    "axe de pli",
    "axe du pli",
    "axes de pli",
    "axe de plissement",
    "axe des plis",
    "axe pli",
    "axe plis",
}

_PLANAR = {
    "foliation",
    "foliée",
    "folié",
    "schistosite",
    "schistosity",
    "schiste",
    "schist",
    "clivage",
    "cleavage",
    "clivage ardoisier",
    "slaty cleavage",
    "clivage de crénulation",
    "crenulation cleavage",
    "gneissosité",
    "gneissosity",
    "litage",
    "bedding",
    "stratification",
    "layering",
    "fabric",
    "fracture",
    "diaclase",
    "joint",
    "joint set",
    "famille de diaclases",
    "fissure",
    "fissuration",
    "crack",
    "cassure",
    "veine",
    "vein",
    "veinule",
    "veinlet",
    "filon",
    "filonnet",
    "quartz vein",
    "veine de quartz",
    "veine de pegmatite",
    "pegmatite vein",
    "gash vein",
    "veine en échelon",
    "en echelon vein",
    "veine de calcite",
    "calcite vein",
    "veine de sulfures",
    "sulfide vein",
    "vein de tension",
    "tension vein",
    "faille",
    "fault",
    "faille normale",
    "normal fault",
    "faille inverse",
    "reverse fault",
    "faille de décrochement",
    "strike-slip fault",
    "chevauchement",
    "thrust",
    "thrust fault",
    "cisaillement",
    "shear",
    "zone de cisaillement",
    "shear zone",
    "mylonite",
    "mylonitic",
    "mylonitique",
    "cataclasite",
    "cataclastique",
    "brèche",
    "breccia",
    "brèche de faille",
    "fault breccia",
    "brèche tectonique",
    "tectonic breccia",
    "miroir de faille",
    "fault mirror",
    "gouge de faille",
    "fault gouge",
    "pli",
    "fold",
    "anticlinal",
    "anticline",
    "synclinal",
    "syncline",
    "plissement",
    "folding",
    "plis en genou",
    "kink band",
    "bande de kink",
    "kink",
    "schistosité de flux",
    "flow cleavage",
    "contact",
    "contact intrusif",
    "intrusive contact",
    "contact sédimentaire",
    "sedimentary contact",
    "contact magmatique",
    "magmatic contact",
    "discordance",
    "unconformity",
    "surface de discordance",
    "angular unconformity",
    "discordance angulaire",
    "contact fautif",
    "fault contact",
}


def _normalize(text: str) -> str:
    return " ".join(str(text or "").strip().casefold().split())


def _contains_any(text: str, values: set) -> bool:
    for value in values:
        if value in text:
            return True
    return False


def structure_family(type_text: str) -> str:
    """Return ``planar``, ``linear``, ``composite`` or ``non_orientable``.

    Unknown or empty codes default to ``unknown`` (the caller keeps the old
    behaviour: draw like a planar if it has a dip pair, and let QC warn if
    no orientation is supplied).
    """
    text = _normalize(type_text)
    if not text:
        return "unknown"
    if _contains_any(text, _NON_ORIENTABLE):
        return "non_orientable"
    if _contains_any(text, _COMPOSITE):
        return "composite"
    if _contains_any(text, _LINEAR):
        return "linear"
    if _contains_any(text, _PLANAR):
        return "planar"
    return "unknown"


def orientation_expected(type_text: str) -> bool:
    """True when the QC expects a dip/dip_direction or alpha/beta pair."""
    return structure_family(type_text) != "non_orientable"
