"""Lithology taxonomy (v2.7.10.22 — bibliothèque validée à l'écran).

Bibliothèque hiérarchique des 30 familles lithologiques avec couleur VIVE
de base et indicateurs/enfants.  Miroir de la bibliothèque d'altération
(v2.7.9/2.7.10.20), mêmes règles actées le 20/08/2026 :

- la FAMILLE pilote la couleur vive ; l'enfant reçoit une NUANCE
  déterministe autour d'elle (jamais 30 couleurs disjointes, jamais
  d'aléatoire) ;
- rendu APLAT partout par défaut : un motif éventuel reste un choix
  manuel dans le Référentiel ;
- ce ne sont que des SUGGESTIONS posées à l'acceptation d'un code
  nouveau : le choix existant ou explicite n'est jamais réécrit
  (« défauts seulement »).

Ordre de la table = plus spécifique d'abord : une « quartz vein » n'est
pas une quartzite, une « monzonite alcaline » n'est pas l'intermédiaire
générique, « rhyolite » lit Volcanique felsique (sa famille volcanique
devance la famille intrusive).
"""

from __future__ import annotations

import colorsys
import hashlib

from .alteration_taxonomy import unicodedata_normalize


# (key, label, couleur vive de base, marqueurs d'identité, indicateurs
# d'enfants, min_matches)
LITHOLOGY_FAMILIES: tuple = (
    # --- spécifiques / à précéder absolument -------------------------------
    ("veine", "Veine / veinule", "#F1C40F",
     ("veine", "vein", "veinule", "veinlet", "filon", "=vqz", "=stw",
     "=hvb"),
     ("quartz_vein", "carbonate_vein", "quartz vein", "carbonate vein"), 1),
    ("felsique_specialise", "Intrusive felsique spécialisé", "#5B2C6F",
     ("greisen", "greisenisee", "greisenisée", "albitite", "=grs"),
     ("albitite", "episyenite", "épisyénite"), 1),
    ("formation_fer", "Formation de fer (BIF)", "#922B21",
     ("bif", "iron formation", "=qmag"),
     ("iron_formation", "itabirite", "banded iron", "banded_iron",
      "chert-magnetite", "chert_magnetite"), 1),
    ("skarn_calcosilicatee", "Skarn / calco-silicatée", "#A93226",
     ("skarn", "=gmag", "garnet_rock", "gmag"),
     ("calc-silicate", "calc_silicate", "calcosilicate", "calco-silicate",
      "hornfels calco-silicate", "hornfels_calco-silicate"), 1),
    ("metam_ultramafique", "Métamorphique ultramafique", "#0B5345",
     ("serpentinite", "metaperidotite", "métapéridotite"),
     ("serpentinite", "metaperidotite", "métapéridotite"), 1),
    ("metam_felsique", "Métamorphique felsique", "#9B59B6",
     ("gneiss", "orthogneiss", "migmatite", "=gns", "=mig", "=fma"),
     ("orthogneiss", "migmatite"), 1),
    ("metam_mafique", "Métamorphique mafique", "#196F3D",
     ("amphibolite", "metabasite", "métabasite", "=amt"),
     ("metagabbro", "métagabbro", "metabasite", "métabasite"), 1),
    ("intrusive_alcaline", "Intrusive alcaline", "#6C3483",
     ("alcaline", "alkali", "alcalin", "=sye"),
     ("syenite", "syénite", "nepheline", "néphéline", "nepheline_syenite",
      "nepheline syenite"), 1),
    ("pegmatitique", "Pegmatitique", "#8E44AD",
     ("pegmatite", "pégmatite", "aplite", "leucogranite", "léucogranite",
     "=peg", "=apg", "=apl"),
     ("aplite", "leucogranite", "léucogranite"), 1),
    # --- volcaniques (devancent les familles intrusives homonymes) ---------
    ("volcanique_felsique", "Volcanique felsique", "#7D3C98",
     ("rhyolite", "rhyolithe", "ignimbrite", "=dac", "=rhy", "=fvo"),
     ("dacite", "ignimbrite", "tuff_felsique", "tuff felsique",
      "felsic tuff"), 1),
    ("volcanique_intermediaire", "Volcanique intermédiaire", "#117A65",
     ("andesite", "andésite", "trachyte", "latite", "=and", "=ivo"),
     ("trachyte", "latite"), 1),
    ("volcanique_mafique", "Volcanique mafique", "#1C2833",
     ("basalt", "basalte", "komatiite", "=bba", "=bas", "=bap", "=mvo"),
     ("komatiite", "basaltic_andesite", "basaltic andesite"), 1),
    ("pyroclastique", "Pyroclastique", "#E67E22",
     ("tuff", "=mtu"),
     ("ash_tuff", "ash tuff", "lapilli_tuff", "lapilli tuff",
      "lapilli-tuff"), 1),
    ("volcanoclastique", "Roche volcanoclastique", "#D35400",
     ("volcanoclastique", "volcanoclastic", "=anb", "=voc", "=vob", "=vcc",
     "=vst", "=vsh", "=vsl"),
     ("volcanic breccia", "volcanic_breccia", "agglomerate", "agglomérat",
      "lapillistone"), 1),
    # --- sédimentaires ------------------------------------------------------
    ("sedimentaire_grossiere", "Sédimentaire grossière", "#A04000",
     ("conglomerat", "conglomérat", "diamictite", "=cog", "=mco"),
     ("breccia", "brèche", "diamictite"), 1),
    ("sedimentaire_detritique", "Sédimentaire détritique", "#D4AC0D",
     ("gres", "grès", "siltstone", "mudstone", "argilite", "graywacke",
     "=sds", "=sha", "=mus", "=sil", "=grw"),
     ("shale", "graywacke"), 1),
    ("carbonatee_litho", "Sédimentaire carbonatée", "#2471A3",
     ("limestone", "calcaire", "dolostone", "dolomie", "=dol", "=lim"),
     ("marble", "marbre", "marble carbonate", "marble_carbonate"), 1),
    ("chimique_evaporitique", "Chimique / évaporitique", "#B7950B",
     ("evaporite", "évaporite", "=cht"),
     # « chert » est un indicateur, pas une identité : une « chert à
     # magnétite » lit la Formation de fer (précédence, v2.7.10.22).
     ("chert", "gypsum", "gypse", "anhydrite", "halite", "sel gemme"), 1),
    # --- métamorphiques restantes ------------------------------------------
    ("metam_pelitique", "Métamorphique pélitique", "#2874A6",
     ("schiste", "phyllite", "slate", "ardoise", "hornfels", "=gms",
     "=fsh", "=mis", "=msh", "=mar", "=pel", "=phy", "=shu"),
     ("phyllite", "slate", "ardoise"), 1),
    # --- roches ciblées ------------------------------------------------------
    ("quartzite", "Quartzite", "#5DADE2",
     ("quartzite", "=qzt", "=qzl", "=qtz", "=qms"), ("quartz-rich", "quartz_rich"), 1),
    ("roche_carbonee", "Roche carbonée", "#212F3C",
     ("graphite", "graphitic", "coal", "charbon", "carbonaceous",
      "carbonee", "carbonée"),
     ("coal", "charbon"), 1),
    ("roche_minerai", "Roche riche en minerai", "#C0392B",
     ("minerai", "ore", "massive sulphide", "massive_sulphide"),
     ("oxide ore", "oxide_ore"), 1),
    ("laterite_regolithe", "Latérite / régolithe", "#CA6F1E",
     ("laterite", "latérite", "regolithe", "régolithe", "=reg", "=ldc",
     "=latsoil"),
     ("ferricrete", "saprolite", "duricrust"), 1),
    ("alluvion_colluvion", "Alluvion / colluvion", "#884EA0",
     ("alluvium", "alluvion", "colluvium", "colluvion"),
     ("gravel", "gravier", "sand", "sable", "colluvium"), 1),
    ("eluvion", "Éluvion", "#BA4A00",
     ("eluvium", "éluvion"),
     ("residual soil", "residual_soil", "transported_soil",
      "transported soil", "soil"), 1),
    # --- familles intrusives génériques --------------------------------------
    ("felsique", "Felsique", "#AF7AC5",
     ("granite", "granodiorite", "tonalite", "granitoide", "granitoïde",
     "=fiu", "=afi", "=fdp", "=fsp", "=gra", "=grd", "=qzp", "=ton",
     "=g2m"),
     ("tonalite", "granodiorite"), 1),
    ("intermediaire", "Intermédiaire", "#148F77",
     ("diorite", "monzonite", "quartz-diorite", "quartz_diorite",
      "quartzdiorite", "=iiu", "=dio", "=hbp", "=ifp", "=gmz"),
     ("monzonite", "quartz-diorite", "quartz_diorite"), 1),
    ("mafique", "Mafique", "#1A5276",
     ("gabbro", "dolerite", "dolérite", "diabase", "norite", "=dlt",
     "=gab", "=maf", "=mff"),
     ("norite", "gabbronorite"), 1),
    ("ultramafique", "Ultramafique", "#145A32",
     ("peridotite", "péridotite", "dunite", "harzburgite", "lherzolite",
      "pyroxenite", "pyroxénite", "=pyr", "=per", "=dun"),
     ("dunite", "harzburgite", "lherzolite"), 1),
    # --- attrape-tout explicite UNIQUEMENT ------------------------------------
    ("inconnue_autre", "Inconnue / autre", "#7F8C8D",
     ("unknown", "inconnue", "inconnu", "undifferentiated",
      "indifferenciee", "indifférenciée", "mixed", "autre", "other",
      "=xcm", "=cot", "=nor"),
     (), 1),
)

# Couleurs vives de base des 30 familles — presets du sélecteur de
# couleur du Référentiel (source unique ; core.reference les aliasse).
LITHO_PRESETS: tuple = tuple(
    colour for (_key, _label, colour, _id, _kw, _n) in LITHOLOGY_FAMILIES)


def _contains(code_folded: str, keyword: str) -> bool:
    # v2.7.10.24 — « =xyz » = correspondance EXACTE (codes abrégés
    # d'utilisateur : GRA, DIO, VQZ…), sinon sous-chaîne (historique).
    if keyword.startswith("="):
        return code_folded == keyword[1:]
    return keyword in code_folded


def nuance_to_family(family_color: str, raw_code: str) -> str:
    """Nuance DÉTERMINISTE d'un enfant autour de la couleur de famille.

    La famille pilote la couleur vive ; l'enfant n'en dérive que par un
    petit décalage de teinte (±~2 %), saturation (±2 %) et valeur
    (±8 %) fonction du code brut — traçable, stable d'un rendu à l'autre,
    et jamais une couleur disjointe (arbitrage écran 20/08/2026).
    """
    folded = unicodedata_normalize(str(raw_code or "")).casefold().strip()
    digest = hashlib.sha1(f"lithology-nuance:{folded}".encode()).digest()
    r = int(family_color[1:3], 16) / 255.0
    g = int(family_color[3:5], 16) / 255.0
    b = int(family_color[5:7], 16) / 255.0
    hue, sat, val = colorsys.rgb_to_hsv(r, g, b)
    # v2.9.69 — écart enfant plus marqué (lisibilité coupe)
    hue = (hue + (digest[0] / 255.0 - 0.5) * 0.14) % 1.0
    sat = min(max(sat + (digest[1] / 255.0 - 0.5) * 0.12, 0.35), 1.0)
    val = min(max(val + (digest[2] / 255.0 - 0.5) * 0.22, 0.40), 0.95)
    r2, g2, b2 = colorsys.hsv_to_rgb(hue, sat, val)
    return "#{:02X}{:02X}{:02X}".format(
        *(round(component * 255) for component in (r2, g2, b2)))


def suggest_lithology_family(raw_code: str) -> dict | None:
    """Suggest ``{"key", "label", "family", "color"}`` for a raw lithology.

    Même moteur que l'altération : identité d'abord, puis indicateurs
    (``min_matches`` souvent 1 — une lithologie est un nom de roche),
    plus spécifique d'abord.  La couleur retournée est la NUANCE de
    l'enfant autour de la couleur vive de la famille ; aplat — aucun
    motif n'est suggéré (choix manuel, arbitrage).
    """
    value = str(raw_code or "").strip()
    if not value:
        return None
    folded = unicodedata_normalize(value).casefold()
    for key, label, colour, identity, keywords, minimum in LITHOLOGY_FAMILIES:
        if any(_contains(folded, marker) for marker in identity):
            return {"key": key, "label": label, "family": label,
                    "color": nuance_to_family(colour, value)}
    for key, label, colour, _identity, keywords, minimum in LITHOLOGY_FAMILIES:
        hits = sum(1 for keyword in keywords if _contains(folded, keyword))
        if minimum and hits >= minimum:
            return {"key": key, "label": label, "family": label,
                    "color": nuance_to_family(colour, value)}
    return None
