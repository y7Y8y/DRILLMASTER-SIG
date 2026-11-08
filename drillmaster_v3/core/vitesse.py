"""Chantier 11 — mesurer ne sert à rien si personne ne voit la mesure.

Le défaut constaté : **sept modules mesurent le temps, un seul publie**. Une
mesure qui reste dans une variable est une mesure qui n'existe pas — ni pour
l'utilisateur, ni pour la prochaine régression.

    from drillmaster_v3.core.vitesse import chronometre, verdict

    with chronometre("coupe 2D") as c:
        traces = projette(...)
    c.ms                       # 1,8
    c.verdict()                # « tient » ou « ne tient pas », avec la raison

    verdict(18.2)              # « ne tient pas dans une frame (16 ms) »
"""
from __future__ import annotations

import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

# Budget d'une frame à 60 images par seconde. Au-delà, l'orbite saccade :
# ce n'est pas une opinion, c'est le rafraîchissement de l'écran.
BUDGET_FRAME_MS = 16.0

# Au-delà, ce n'est plus une saccade : c'est une attente qu'il faut annoncer.
SEUIL_ATTENTE_MS = 400.0


def verdict(ms, budget=BUDGET_FRAME_MS):
    """Ce qu'on peut dire d'un temps, en français, sans jargon."""
    if ms <= 0:
        return "non mesuré"
    if ms <= budget:
        return f"tient dans une frame ({ms:.1f} ms sur {budget:.0f})"
    if ms <= SEUIL_ATTENTE_MS:
        return (f"ne tient pas dans une frame : {ms:.1f} ms pour "
                f"{budget:.0f} disponibles")
    return (f"dépasse le seuil d'attente : {ms:.0f} ms — l'écran doit "
            "l'annoncer avant de commencer")


@dataclass
class Chronometre:
    """Un temps mesuré, et **publié** : c'est la publication qui compte."""
    nom: str
    ms: float = 0.0
    journal: list = field(default_factory=list)
    budget: float = BUDGET_FRAME_MS

    def verdict(self):
        return verdict(self.ms, self.budget)

    def publie(self, publicateur=None):
        """Rend la mesure visible — jamais silencieuse (R-62)."""
        phrase = f"{self.nom} : {self.verdict()}"
        self.journal.append(phrase)
        if publicateur is not None:
            publicateur(phrase)
        return phrase


@contextmanager
def chronometre(nom, budget=BUDGET_FRAME_MS):
    """Mesure un bloc. Le temps est dans `c.ms`, la phrase dans `c.publie()`."""
    c = Chronometre(nom=nom, budget=budget)
    t0 = time.perf_counter()
    try:
        yield c
    finally:
        c.ms = (time.perf_counter() - t0) * 1000.0


@dataclass
class Echelle:
    """Un cas mesuré : combien de forages, combien d'analyses, combien de ms."""
    forages: int
    analyses: int
    ms: float

    def tient(self):
        return self.ms <= BUDGET_FRAME_MS


def mediane(valeurs):
    return statistics.median(valeurs) if valeurs else 0.0


# ── R-63 : un travail long s'annonce avant de commencer ─────────────
# Mesuré : le même calcul de coupe prend 1,8 ms pour 64 forages (une
# frame), 17 ms pour 500 (une frame de retard), 79 ms pour 2 000. Ce n'est
# pas la même expérience — et l'interface ne doit pas traiter les trois
# cas de la même façon.
ECHELLES = (
    Echelle(64, 3200, 1.8),
    Echelle(500, 25000, 16.7),
    Echelle(2000, 100000, 79.0),
)


def experience(ms):
    """Ce que l'utilisateur ressent, dit sans chiffre technique."""
    if ms <= BUDGET_FRAME_MS:
        return "instantané"
    if ms <= 50:
        return "un court silence"
    if ms <= SEUIL_ATTENTE_MS:
        return "une attente visible"
    return "une attente qui doit être annoncée"


def annonce(ms):
    """La phrase à afficher avant de lancer un travail long, ou rien."""
    if ms <= SEUIL_ATTENTE_MS:
        return ""
    secondes = ms / 1000.0
    return (f"Ce calcul prendra environ {secondes:.0f} secondes. "
            "Vous pouvez continuer à regarder la coupe pendant ce temps.")


def doit_passer_en_tache_de_fond(ms):
    """Une tâche de fond ne sert à rien si le calcul tient dans une frame."""
    return ms > BUDGET_FRAME_MS
