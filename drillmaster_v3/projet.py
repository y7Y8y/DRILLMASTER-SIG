"""Projet — le seul objet qui porte les réglages et les données.

R-09 : aucune vue ne détient de copie. Une exclusion est décidée **une fois**
et s'applique partout, parce qu'elle vit ici et nulle part ailleurs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .core.donnees.lecture import Forage, Lecture, lit_collets
from .core.reglages import Reglages
from .core.tracks import TrackCatalog, TrackStyle


@dataclass
class Projet:
    nom: str = "sans titre"
    crs: str = "EPSG:32629"
    colliers: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    exclusions: dict = field(default_factory=dict)   # id_forage -> motif
    # Le journal des décisions : qui, quand, pourquoi. Il ne se perd pas,
    # même si le fichier source change (écran 21).
    decisions: list = field(default_factory=list)
    profondeurs: dict = field(default_factory=dict)
    mesures: dict = field(default_factory=dict)      # id -> [(prof, az, dip)]
    empreintes: dict = field(default_factory=dict)   # fichier -> empreinte
    catalogue: TrackCatalog = field(default_factory=TrackCatalog)
    mode: str = "guidee"
    version: int = 1

    # ── import ──────────────────────────────────────────────────────
    def importe(self, chemin, texte=None) -> Lecture:
        lec = lit_collets(chemin, texte=texte)
        self.colliers.extend(lec.colliers)
        self.messages.extend(lec.messages)
        for f in lec.colliers:
            if f.profondeur:
                self.profondeurs.setdefault(f.id, f.profondeur)
        self.empreintes[Path(chemin).name] = lec.journal.get("empreinte_source")
        return lec

    # ── exclusions : une décision, valable partout (réponse à ta question) ──
    def exclut(self, id_forage, motif, par="", quand=None):
        """Écarter un forage. Le motif est obligatoire ; l'auteur, recommandé."""
        if not motif:
            raise ValueError("une exclusion exige un motif : rien n'est exclu sans raison")
        self.exclusions[id_forage] = motif
        self._note("écarté", id_forage, motif, par, quand)
        self.version += 1

    def reintegre(self, id_forage, par="", motif="", quand=None):
        """Réintégrer : le forage revient partout, le motif d'origine reste au journal."""
        ancien = self.exclusions.pop(id_forage, "")
        self._note("réintégré", id_forage, motif or ancien, par, quand)
        self.version += 1

    def _note(self, action, id_forage, motif, par, quand):
        """Une ligne de journal, jamais muette : l'action, le forage, le motif."""
        self.decisions.append({
            "action": action, "forage": id_forage, "motif": motif or "",
            "par": par or "non précisé",
            "quand": quand or datetime.now(timezone.utc).isoformat(
                timespec="seconds"),
        })

    def journal_des_decisions(self):
        """Ce que l'écran « Forages écartés » affiche, dans l'ordre."""
        return list(self.decisions)

    def exclu(self, id_forage):
        return id_forage in self.exclusions

    # ── lecture des forages : filtrée, jamais modifiée ───────────────
    def forages_actifs(self):
        return [f for f in self.colliers if f.id not in self.exclusions]

    def forages_ecartes(self):
        """Les forages écartés, avec le motif : **disponibles au dessin**.

        R-54 — « écarté » veut dire absent des **calculs**, pas caché de
        l'écran. Un géologue doit voir ce qu'il a mis de côté, en pointillés,
        sinon une exclusion ressemble à un forage qui n'a jamais existé.
        """
        return [(f, self.exclusions[f.id]) for f in self.colliers
                if f.id in self.exclusions]

    @property
    def reglages(self):
        """Un seul propriétaire des réglages de piste, porté par le projet."""
        if not hasattr(self, "_reglages"):
            self._reglages = Reglages(self.catalogue)
        return self._reglages

    def style(self, pid) -> TrackStyle:
        return self.catalogue.resout(pid)

    # ── bascule de mode : aucune valeur ne bouge (R-25) ─────────────
    def bascule_mode(self, mode):
        if mode not in ("guidee", "experte"):
            raise ValueError("mode inconnu")
        self.mode = mode
        return self.mode
