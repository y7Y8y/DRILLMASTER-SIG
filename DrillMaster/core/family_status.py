"""État d'attention des familles — système de badge générique (v2.7.12.5).

Principe de la revue d'architecture du 22/08/2026 : le badge d'une famille
ne se lit JAMAIS sur une liste de cas particuliers (« si litho… si
altération… si minéralisation… »). Il se lit sur l'ÉTAT DE LA FAMILLE :

    Famille  →  État de la famille  →  Attention nécessaire ?  →  ⚠

Toutes les familles — collars, déviations, lithologie, altérations,
minéralisations, teneurs, et celles qui seront ajoutées plus tard —
traversent le MÊME mécanisme en trois temps :

1. ``ImportTab.family_status()`` (interface) rassemble les sources
   d'attention en un ``FamilyStatus``. L'implémentation de base couvre
   déjà les sources GÉNÉRIQUES (question d'organisation, colonnes
   requises/ambiguës, erreurs de validation, avertissements) : une
   nouvelle famille hérite du badge SANS rien ajouter.
2. ``FamilyStatus`` est l'unique représentation de l'état — gravité,
   codes machine, compteurs. Aucune connaissance du contenu de la
   famille n'y figure.
3. ``badge_rendu()`` est l'unique endroit qui traduit un état en
   titre/couleur/infobulle. Le code Qt ne fait que poser le résultat.

Si une famille a un besoin RÉELLEMENT différent (un état propre qu'aucune
autre n'a), elle SURCHARGE ``family_status()`` et y combine son état
spécifique avec ``combine(super().family_status(), ...)`` — le rendu,
la priorité et l'infobulle restent partagés. C'est le seul point
d'extension : ni plus, ni moins.

Pure Python, sans Qt ni QGIS — testable hors plugin (invariante du
projet).
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Gravité croissante : c'est elle qui décide du rendu — jamais la
# provenance de l'information. Une question sans réponse l'emporte sur
# tout (on ne valide pas par-dessus une question) ; une erreur l'emporte
# sur un avertissement ; un avertissement signale ; le reste est propre.
EMPTY = "empty"        # pas de fichier dans cette famille
READY = "ready"        # fichier présent, rien à signaler
WARNING = "warning"    # avertissement(s) non bloquant(s)
BLOCKING = "blocking"  # donnée manquante / ambiguïté / incohérence / erreur
QUESTION = "question"  # une question attend une réponse explicite

SEVERITY_ORDER = {EMPTY: 0, READY: 1, WARNING: 2, BLOCKING: 3, QUESTION: 4}

# Codes machine des sources d'attention (stables : lisibles dans les
# journaux et les tests ; les familles futures déclarent les leurs).
QUESTION_ORGANISATION = "QUESTION_ORGANISATION"
MAPPING = "MAPPING"
ERRORS = "ERRORS"
WARNINGS = "WARNINGS"


@dataclass(frozen=True)
class FamilyStatus:
    """État machine d'une famille — tout ce que le badge (et toute autre
    vue d'attention) doit savoir, et rien d'autre."""

    severity: str = READY
    codes: tuple = field(default_factory=tuple)
    count: int = 0

    @property
    def needs_attention(self) -> bool:
        return SEVERITY_ORDER[self.severity] >= SEVERITY_ORDER[WARNING]

    @property
    def is_blocking(self) -> bool:
        return SEVERITY_ORDER[self.severity] >= SEVERITY_ORDER[BLOCKING]


def combine(*statuses: FamilyStatus) -> FamilyStatus:
    """Agrège les sources d'attention d'une famille.

    Règle : la gravité la plus HAUTE l'emporte (question > bloquant >
    avertissement > propre > vide) ; les codes machine s'additionnent
    (sans doublon, ordre stable) ; les compteurs s'additionnent.
    ``combine()`` sans argument = famille propre."""
    best = None
    codes: list = []
    count = 0
    for status in statuses:
        if best is None or SEVERITY_ORDER[status.severity] > SEVERITY_ORDER[best.severity]:
            best = status
        for code in status.codes:
            if code not in codes:
                codes.append(code)
        count += status.count
    if best is None:
        return FamilyStatus(READY, (), 0)
    return FamilyStatus(best.severity, tuple(codes), count)


def badge_count(status: FamilyStatus) -> int:
    """Compte affiché à côté du ⚠ (revue écran du 22/08/2026, P2) :
    0 = rien à afficher.

    Règle : seuls les problèmes COMPTABLES se comptent — erreurs et
    avertissements de validation. La question ne se compte pas (ses
    preuves sont déjà NOMMÉES dans le cadre de question) ; l'état
    « colonnes à vérifier » non plus (le tableau de mapping est
    l'affichage)."""
    if not status.needs_attention:
        return 0
    if QUESTION_ORGANISATION in status.codes:
        return 0
    if ERRORS in status.codes or WARNINGS in status.codes:
        return status.count
    return 0


# v2.7.12.6 — pastilles de familles (sélecteur enroulant) : couleurs de
# gravité en hex, SANS Qt — le widget les applique, les tests les
# vérifient. La gravité décide, jamais la provenance (règle FS-0x).
SEVERITY_BORDER = {
    EMPTY: "",
    READY: "#A9DFBF",
    WARNING: "#D68910",
    BLOCKING: "#E74C3C",
    QUESTION: "#B8770E",
}
SEVERITY_TEXT = {
    EMPTY: "#839192",
    READY: "#1E8449",
    WARNING: "#D68910",
    BLOCKING: "#E74C3C",
    QUESTION: "#B8770E",
}


def badge_rendu(status: FamilyStatus, base: str) -> tuple:
    """TRADUIT un état en (titre d'onglet, couleur ou « », infobulle).

    SEUL endroit de ce projet qui écrit la forme du badge : toute la
    sémantique « attention visible sans ouvrir le panneau » (criteres
    v2.7.6, v2.7.10.27, v2.7.12.4) se lit ici.

    v2.9.18 — infobulles d'onglet en BLOC COURT (retour écran : trop
    bavardes sur les pastilles / onglets des étapes 1–4).
    """
    if status.severity == QUESTION:
        return (
            f"⚠ {base}",
            "#B8770E",
            f"{base} · question à répondre",
        )
    if status.severity == BLOCKING:
        return (
            f"{base} ⚠",
            "",
            f"{base} · bloquant · voir validation",
        )
    if status.severity == WARNING:
        n = int(status.count or 0)
        return (
            f"{base} ⚠",
            "",
            f"{base} · {n} avert. · non bloquant" if n
            else f"{base} · avert. · non bloquant",
        )
    if status.severity == READY:
        return (f"{base} ✓", "", f"{base} · OK")
    return (base, "", f"{base} · vide")
