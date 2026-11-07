"""R-20 → R-22 — un message porte 5 champs, ou n'existe pas."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .lexique import lexique


class Niveau(str, Enum):
    INFO = "info"
    AVERTISSEMENT = "avertissement"
    QUESTION = "question"
    BLOCAGE = "blocage"
    ERREUR_TECHNIQUE = "erreur_technique"


SUITE = {
    Niveau.INFO: "poursuit seul",
    Niveau.AVERTISSEMENT: "poursuit",
    Niveau.QUESTION: "met la ligne en attente",
    Niveau.BLOCAGE: "arrête l'étape suivante",
    Niveau.ERREUR_TECHNIQUE: "arrête l'action en cours",
}


class MessageIncomplet(ValueError):
    """R-20 : un message sans pourquoi ni résoudre ne peut pas être construit."""


@dataclass(frozen=True)
class Message:
    niveau: Niveau
    titre: str
    pourquoi: str
    concernes: tuple
    resoudre: tuple
    portee: str
    actions: tuple = ()
    detail: dict = field(default_factory=dict)

    def __post_init__(self):
        manquants = [
            nom for nom, val in (("pourquoi", self.pourquoi),
                                 ("concernes", self.concernes),
                                 ("resoudre", self.resoudre),
                                 ("portee", self.portee))
            if not val
        ]
        if manquants:
            raise MessageIncomplet(
                f"message « {self.titre} » sans {manquants} (R-20)")
        for texte in (self.titre, self.pourquoi, self.portee):
            lexique.verifie(texte)
        for action in self.resoudre:
            lexique.verifie(action)

    # ── rendu : même vocabulaire, deux longueurs (R-16, R-18) ───────
    @property
    def label(self):
        return lexique.niveau(self.niveau.value, "label")

    @property
    def couleur(self):
        return lexique.niveau(self.niveau.value, "couleur")

    @property
    def suite(self):
        return SUITE[self.niveau]

    def rendu(self, voix="guidee"):
        if voix not in ("guidee", "experte"):
            raise ValueError("voix inconnue")
        bloc = {
            "niveau": self.label,
            "titre": self.titre,
            "ce_qui_se_passe": self.pourquoi,
            "ce_que_vous_pouvez_faire": "; ".join(self.resoudre),
            "ce_qui_continue": self.suite,
        }
        if voix == "experte":
            bloc["concerne"] = list(self.concernes)
            bloc["portee"] = self.portee
            bloc["actions"] = list(self.actions)
        return bloc


# ── fabriques : le niveau impose sa forme (R-22) ────────────────────
def information(titre, pourquoi, portee, concernes=("-",)):
    return Message(Niveau.INFO, titre, pourquoi, concernes, ("aucune action",),
                   portee)


def avertissement(titre, pourquoi, concernes, resoudre, portee, actions=()):
    return Message(Niveau.AVERTISSEMENT, titre, pourquoi, tuple(concernes),
                   tuple(resoudre), portee, tuple(actions))


def question(titre, pourquoi, concerne, choix, portee):
    return Message(Niveau.QUESTION, titre, pourquoi, (concerne,), tuple(choix),
                   portee)


def blocage(titre, pourquoi, concernes, resoudre, portee, actions=()):
    if len(resoudre) < 2:
        raise MessageIncomplet(
            "un blocage propose au moins deux sorties (R-22)")
    return Message(Niveau.BLOCAGE, titre, pourquoi, tuple(concernes),
                   tuple(resoudre), portee, tuple(actions))


def erreur_technique(titre, pourquoi, portee, detail=""):
    m = Message(Niveau.ERREUR_TECHNIQUE, titre, pourquoi, ("poste de travail",),
                ("copier le détail pour le support",), portee)
    return m
