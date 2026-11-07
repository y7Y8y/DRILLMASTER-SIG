"""Organisation des intervalles — source unique de vérité (v2.7.12.3).

Revue d'architecture « commune ou spécifique » (demande du 22/08/2026) :
la lithologie et les pistes codées (altérations, minéralisations) partagent
la MÊME machine d'organisation — mêmes modes (standard / large / cellule
délimitée), même profil (ImportStructureProfile), même registre de
décision (CM-01 du 20/08/2026) :

    une structure qui lit PLUSIEURS codes par intervalle est jamais
    appliquée automatiquement ; détectée mais non confirmée => question
    explicite + validation bloquée, jusqu'à la réponse de l'utilisateur.

Avant cette version, la règle n'était appliquée qu'aux pistes codées :
le large litho (colonnes de rôles litho1/litho2) était détecté au parsing
et LUS sans question ni blocage — deux régimes d'état pour la même
logique. Ce module est désormais l'unique endroit où la question existe ;
l'interface (affichage + badge ⚠) et la validation (blocage) en relèvent,
donc plus jamais deux calculs divergents.

Les familles gardent ce qui DIFFÈRE réellement : rôles et proportions
(litho), intensité et minéraux (altérations/minéralisations), plafonds
CM-03 par domaine (component_caps) — ce que les dialogues et la
validation continuent de traiter chacun à leur niveau.

Pure Python, sans Qt ni QGIS — partageable entre parsing, validation,
interface et tests (invariante du projet).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .data_registry import ImportStructureProfile
from .import_detect import detect_wide_component_columns
from .track_bands import SPLIT_CONTENT_FIELDS

# Familles dont l'organisation d'intervalles fait l'objet d'une question
# explicite : lithologie + pistes codées (mêmes clés que l'interface).
STRUCTURE_FAMILY = ("litho",) + tuple(SPLIT_CONTENT_FIELDS.keys())


@dataclass(frozen=True)
class OrganisationQuestion:
    """Question d'organisation en attente, avec ses preuves.

    kind:     "none"      — rien à demander (profil confirmé, lecture
                               standard non ambiguë, ou hors famille)
              "delimited" — cellule multi-codes détectée dans la colonne
                               de codes (« CH/EP/SI »)
              "wide"      — plusieurs colonnes portent un code par
                               intervalle (colonnes de rôles litho, ou
                               suffixes Alt1/Alt2, Style1/2, Min1/2)
    evidence: valeurs d'exemple (delimited) ou noms de colonnes (wide) —
              toujours ce qui sera AFFICHÉ à l'utilisateur, jamais un
              état interne.
    """

    kind: str = "none"
    evidence: tuple = field(default_factory=tuple)

    @property
    def pending(self) -> bool:
        return self.kind != "none"


def delimited_examples(raw_headers, rows, column, delimiter="/",
                       limit=3) -> list:
    """Exemples de cellules portant plusieurs codes (jamais interprétés).

    Mêmes sémantiques que ``csv_parser.find_delimited_values`` (mêmes
    règles : cases vides ignorées, exemples distincts, borne), sur des
    en-têtes/lignes bruts — c'est la forme dont a besoin la source unique
    (l'interface ne doit pas recalculer ses preuves elle-même).
    """
    if not column or not delimiter or limit <= 0:
        return []
    try:
        index = list(raw_headers).index(column)
    except ValueError:
        return []
    examples = []
    for row in (rows or []):
        if index >= len(row):
            continue
        value = str(row[index]).strip()
        if delimiter in value and value not in examples:
            examples.append(value)
        if len(examples) >= limit:
            break
    return examples


def organisation_question(file_type, profile, raw_headers, rows=None,
                          code_column="", delimiter="/") -> OrganisationQuestion:
    """EST-CE QU'UNE QUESTION D'ORGANISATION EST EN ATTENTE — source
    unique, lue par l'interface (cadre de question + badge ⚠ de l'onglet)
    et par la validation (blocage CM-01).

    Règle d'or (registre CM-01) : rien n'est deviné. Deux formes de
    détection alimentent la MÊME question :

    1. large MATÉRIALISÉ dans le profil — litho : le parsing a reconnu des
       colonnes de rôles (litho1/litho2 → ``wide_components`` non
       confirmé). Preuves : les colonnes du profil lui-même.
    2. large RECONNU par suffixe — pistes codées : le profil reste
       ``standard``, les colonnes Alt1/Alt2, Style1/2, Min1/2 sont
       détectées dans les en-têtes. Preuves : les candidats détectés.

    Priorisation inchangée depuis la v2.7.10.37 : cellule délimitée
    d'abord (l'ambiguïté de la valeur prime), large ensuite. Un profil
    confirmé ne pose JAMAIS de question (c'est la réponse enregistrée).
    """
    if str(file_type or "") not in STRUCTURE_FAMILY:
        return OrganisationQuestion("none")
    profile = ImportStructureProfile.from_dict(profile)
    if profile.confirmed:
        return OrganisationQuestion("none")
    # (1) large déjà matérialisé dans le profil (colonnes de rôles litho,
    #     ou large choisi puis annulé — jamais lu sans question).
    if profile.mode == "wide_components" and profile.component_columns:
        return OrganisationQuestion(
            "wide",
            tuple(str(c.code_column)
                  for c in profile.component_columns if c.code_column))
    if profile.mode != "standard":
        return OrganisationQuestion("none")
    # (2) cellule multi-codes dans la colonne de codes (toutes familles).
    column = code_column or profile.code_column
    if column:
        examples = delimited_examples(raw_headers, rows, column, delimiter)
        if examples:
            return OrganisationQuestion("delimited", tuple(examples))
    # (3) colonnes parallèles par suffixe (pistes codées ; le large litho
    #     vient des rôles, déjà couvert au point 1).
    if file_type in ("alterations", "mineralizations"):
        candidates, _intensities, _minerals = detect_wide_component_columns(
            raw_headers, file_type)
        if candidates:
            return OrganisationQuestion(
                "wide", tuple(str(header) for header, _suffix in candidates))
    return OrganisationQuestion("none")


def unconfirmed_wide_error_code(file_type) -> str:
    """Code de validation bloquante pour un large non confirmé.

    Un seul régime d'état, deux libellés (le code machine distingue la
    famille dans les journaux ; le registre de décision est le même).
    """
    if str(file_type or "") == "litho":
        return "LITHO_WIDE_ORGANISATION_UNCONFIRMED"
    return "WIDE_ORGANISATION_UNCONFIRMED"
