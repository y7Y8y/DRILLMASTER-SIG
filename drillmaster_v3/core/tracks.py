"""R-02 → R-10 — les 12 pistes, 4 familles, 14 champs, un seul magasin.

Résolution : famille (défaut) → piste (valeur explicite).
Toute vue lit `TrackStyle` résolu ; aucune vue ne garde de copie.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
FICHIER = RACINE / "specs" / "data" / "tracks.json"

CHAMPS = ("id label family visible order side width gap opacity fill stroke "
          "label_text tooltip filter export").split()
HERITABLES = {"visible", "side", "width", "gap", "opacity", "fill", "stroke",
              "label_text", "tooltip", "filter", "export"}


@dataclass(frozen=True)
class TrackStyle:
    """L'objet unique lu par 2D, 3D, légende, export et carte (R-09)."""
    id: str
    label: str
    family: str
    order: int
    visible: bool
    side: str
    width: int
    gap: int
    opacity: int
    fill: str
    stroke: str
    label_text: dict
    tooltip: dict
    filter: Any
    export: str
    specific: dict = field(default_factory=dict)
    herite: tuple = ()          # champs pris à la famille (R-07)

    def to_dict(self):
        return asdict(self)


class TrackCatalog:
    def __init__(self, chemin=FICHIER):
        data = json.loads(Path(chemin).read_text(encoding="utf-8"))
        self.contrat = data["contrat"]["champs"]
        self.familles = data["familles"]
        self.spec_reglages = data.get("reglages_visibles", {})
        self._pistes = {p["id"]: p for p in data["pistes"]}
        if len(self._pistes) != 12:
            raise ValueError("le catalogue doit déclarer exactement 12 pistes")
        for p in self._pistes.values():
            intrus = set(p.get("specific", {})) & set(CHAMPS)
            if intrus:
                raise ValueError(
                    f"{p['id']} redéclare {sorted(intrus)} dans specific (R-06)")
            if not p.get("owner"):
                raise ValueError(f"{p['id']} sans propriétaire (R-09)")

    # ── lecture ─────────────────────────────────────────────────────
    def ids(self):
        return list(self._pistes)

    def par_famille(self, famille):
        return [p for p in self._pistes.values() if p["family"] == famille]

    def declare(self, pid):
        return self._pistes[pid]

    # ── résolution de l'héritage (R-07) ─────────────────────────────
    def resout(self, pid) -> TrackStyle:
        p = self._pistes[pid]
        fam = self.familles[p["family"]]["defauts"]
        herite = []
        valeurs = {}
        for champ in CHAMPS:
            if champ in ("id", "label", "family", "order"):
                valeurs[champ] = p[champ]
            elif champ in p:
                valeurs[champ] = p[champ]
            elif champ in fam:
                valeurs[champ] = fam[champ]
                if champ in HERITABLES:
                    herite.append(champ)
            else:
                raise ValueError(f"{pid}.{champ} : aucune valeur ni défaut")
        return TrackStyle(specific=dict(p.get("specific", {})),
                          herite=tuple(herite), **valeurs)

    # ── les 5 lecteurs (R-09) ───────────────────────────────────────
    LECTEURS = ("2d", "3d", "legende", "export", "carte")

    def lit(self, pid, lecteur, champ):
        """Chaque vue lit le MÊME objet ; certaines n'utilisent pas un champ.

        Le non-usage est déclaré et motivé (R-08), jamais silencieux.
        """
        if lecteur not in self.LECTEURS:
            raise ValueError(f"lecteur inconnu : {lecteur}")
        sans_objet = {
            ("3d", "side"): "la scène tourne",
            ("carte", "side"): "vue de dessus",
            ("carte", "opacity"): "aplat",
            ("3d", "opacity"): None,
        }
        if (lecteur, champ) in sans_objet:
            raison = sans_objet[(lecteur, champ)]
            if raison:
                return {"applique": False, "raison": raison}
        return {"applique": True, "valeur": getattr(self.resout(pid), champ)}

    def coherents(self, pid, champ):
        """Vrai si tous les lecteurs qui appliquent le champ ont la même valeur."""
        valeurs = set()
        for lect in self.LECTEURS:
            v = self.lit(pid, lect, champ)
            if v["applique"]:
                valeurs.add(json.dumps(v["valeur"], sort_keys=True,
                                       ensure_ascii=False))
        return len(valeurs) <= 1
