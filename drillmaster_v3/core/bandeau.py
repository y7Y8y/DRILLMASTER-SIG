"""Chantier 4 — le bandeau qui remplace les fenêtres d'alerte.

Le défaut mesuré (M-01) : 29 fenêtres bloquent le travail. Une fenêtre à
fermer casse le geste ; au dixième import, on clique « OK » sans lire.

Ici : un bandeau dans l'écran, qui porte les 5 champs (R-20) et se comporte
comme un message, pas comme une interruption.

    b = Bandeau()
    b.ajoute(blocage(...))
    b.visible("guidee")      # ce que voit le débutant
    b.visible("experte")     # ce que voit l'expert
    b.doit_arreter()         # vrai si un blocage est présent
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .messages import Message, MessageIncomplet, Niveau

# l'ordre d'affichage : ce qui arrête passe devant ce qui informe
PRIORITE = {Niveau.BLOCAGE: 0, Niveau.ERREUR_TECHNIQUE: 1,
            Niveau.QUESTION: 2, Niveau.AVERTISSEMENT: 3, Niveau.INFO: 4}

LONGUEUR_TITRE = 90          # au-delà, le titre n'est plus un titre


@dataclass
class Bandeau:
    """Une zone d'annonce, pas une fenêtre. Elle ne bloque jamais le clic."""

    messages: list = field(default_factory=list)
    modele: type = Message

    # ── alimentation ──────────────────────────────────────────────
    def ajoute(self, message):
        if not isinstance(message, Message):
            raise MessageIncomplet(
                "un bandeau n'accepte que des messages à 5 champs (R-20)")
        if len(message.titre) > LONGUEUR_TITRE:
            raise MessageIncomplet(
                f"titre de {len(message.titre)} caractères : un titre annonce "
                f"un fait en une phrase ({LONGUEUR_TITRE} max)")
        self.messages.append(message)
        return message

    def remplace(self, message):
        """Le même sujet remplace l'ancien : un bandeau ne s'empile pas."""
        self.messages = [m for m in self.messages
                         if m.portee != message.portee]
        return self.ajoute(message)

    def vide(self):
        self.messages.clear()

    # ── lecture ───────────────────────────────────────────────────
    def tries(self):
        return sorted(self.messages,
                      key=lambda m: (PRIORITE[m.niveau], m.titre))

    def par_niveau(self, niveau):
        return [m for m in self.messages if m.niveau == niveau]

    def doit_arreter(self):
        return bool(self.par_niveau(Niveau.BLOCAGE)
                    or self.par_niveau(Niveau.ERREUR_TECHNIQUE))

    def doit_demander(self):
        return bool(self.par_niveau(Niveau.QUESTION))

    def compte(self):
        return {n.value: len(self.par_niveau(n)) for n in Niveau}

    def visible(self, voix="guidee"):
        """Même contenu, deux longueurs — jamais deux produits (R-16)."""
        if voix not in ("guidee", "experte"):
            raise ValueError("voix inconnue : « guidee » ou « experte »")
        sortie = []
        for m in self.tries():
            bloc = m.rendu(voix)
            bloc["couleur"] = m.couleur
            bloc["arrete"] = m.niveau in (Niveau.BLOCAGE,
                                          Niveau.ERREUR_TECHNIQUE)
            sortie.append(bloc)
        return sortie

    # ── résumé pour la barre d'état : une seule ligne ─────────────
    def resume(self):
        if not self.messages:
            return "aucun message"
        compte = {k: v for k, v in self.compte().items() if v}
        if len(self.messages) == 1:
            return self.tries()[0].titre
        return (f"{len(self.messages)} messages · "
                + " · ".join(f"{v} {k}" for k, v in compte.items()))

    # ── sortie pour le support : copiable, sans jargon ajouté ─────
    def pour_le_support(self, version="", chemin=""):
        lignes = [f"DrillMaster {version}".strip()]
        if chemin:
            lignes.append(f"Fichier : {chemin}")
        for m in self.tries():
            lignes.append(f"[{m.label}] {m.titre}")
            lignes.append(f"  pourquoi : {m.pourquoi}")
            lignes.append(f"  concerné : {', '.join(m.concernes)}")
            lignes.append(f"  sorties : {'; '.join(m.resoudre)}")
        lignes.append("Copiez ce texte pour le support : il contient tout ce "
                      "qu'il faut, rien de plus.")
        return "\n".join(lignes)
