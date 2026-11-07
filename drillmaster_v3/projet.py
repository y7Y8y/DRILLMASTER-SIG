"""Projet — le seul objet qui porte les réglages et les données.

R-09 : aucune vue ne détient de copie. Une exclusion est décidée **une fois**
et s'applique partout, parce qu'elle vit ici et nulle part ailleurs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .core.donnees.lecture import Forage, Lecture, lit_collets
from .core.tracks import TrackCatalog, TrackStyle


@dataclass
class Projet:
    nom: str = "sans titre"
    crs: str = "EPSG:32629"
    colliers: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    exclusions: dict = field(default_factory=dict)   # id_forage -> motif
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
    def exclut(self, id_forage, motif):
        if not motif:
            raise ValueError("une exclusion exige un motif : rien n'est exclu sans raison")
        self.exclusions[id_forage] = motif
        self.version += 1

    def reintegre(self, id_forage):
        self.exclusions.pop(id_forage, None)
        self.version += 1

    def exclu(self, id_forage):
        return id_forage in self.exclusions

    # ── lecture des forages : filtrée, jamais modifiée ───────────────
    def forages_actifs(self):
        return [f for f in self.colliers if f.id not in self.exclusions]

    def style(self, pid) -> TrackStyle:
        return self.catalogue.resout(pid)

    # ── bascule de mode : aucune valeur ne bouge (R-25) ─────────────
    def bascule_mode(self, mode):
        if mode not in ("guidee", "experte"):
            raise ValueError("mode inconnu")
        self.mode = mode
        return self.mode
