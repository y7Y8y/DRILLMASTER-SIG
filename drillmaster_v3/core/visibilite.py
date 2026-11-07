"""R-24 / R-25 — la complexité progressive, mesurée et non promise.

- au plus `max_essentiels` réglages visibles à la fois (6) ;
- le mode Guidé ne montre que l'essentiel ;
- changer de mode ne change **aucune valeur**.
"""
from __future__ import annotations

from .tracks import CHAMPS, TrackCatalog

MODES = ("guidee", "experte")


class TropDeReglages(ValueError):
    """R-24 : plus de 6 réglages visibles = refus de construire l'écran."""


class Visibilite:
    def __init__(self, catalog: TrackCatalog, max_essentiels=None):
        self.cat = catalog
        self.regles = catalog.spec_reglages
        self.max = max_essentiels or self.regles.get("max_essentiels", 6)

    # ── un réglage est-il essentiel pour cette piste ? ──────────────
    def niveau(self, pid, champ):
        p = self.cat.declare(pid)
        propres = self.regles["propres"].get(p["family"], {})
        if champ in p.get("specific", {}):
            return propres.get(champ, "avance")
        return self.regles["communs"].get(champ, "avance")

    def essentiels(self, pid, mode="guidee"):
        p = self.cat.declare(pid)
        champs = [c for c in CHAMPS if c not in ("id", "label", "family")]
        champs += list(p.get("specific", {}))
        if mode == "experte":
            return champs
        return [c for c in champs if self.niveau(pid, c) == "essentiel"]

    def avances(self, pid):
        return [c for c in self.essentiels(pid, "experte")
                if self.niveau(pid, c) != "essentiel"]

    # ── la garde : on refuse de dessiner trop ───────────────────────
    def verifie_affichage(self, pid, champs):
        if len(champs) > self.max:
            raise TropDeReglages(
                f"{pid} : {len(champs)} réglages visibles, maximum {self.max} (R-24)")
        return champs

    # ── la preuve que les modes ne divergent pas (R-25) ─────────────
    def empreinte(self, pid):
        """Valeurs résolues, indépendantes du mode."""
        s = self.cat.resout(pid)
        return {k: v for k, v in s.to_dict().items() if k != "herite"}

    def modes_ne_changent_rien(self):
        avant = {pid: self.empreinte(pid) for pid in self.cat.ids()}
        for _ in ("guidee", "experte", "guidee"):
            for pid in self.cat.ids():
                self.essentiels(pid, "guidee")
                self.essentiels(pid, "experte")
        apres = {pid: self.empreinte(pid) for pid in self.cat.ids()}
        return avant == apres
