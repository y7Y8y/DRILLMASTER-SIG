"""
scene3d.model — modèle de scène PARTAGÉ (coupe 2D + vue 3D).

Python pur + numpy, aucune dépendance QGIS : testable hors QGIS.

Principe : « structure of arrays ». Un projet de 20 000 trous et plusieurs
millions d'intervalles ne doit jamais devenir des millions d'objets Python.
Chaque domaine (lithologie, Li ppm, Rb ppm, altération…) est UNE table de
tableaux numpy ; la coupe et la 3D lisent les mêmes tables.

Coordonnées : tout est stocké en float64 réel (UTM), mais la scène expose
des positions RELATIVES à `origin` (float32) pour éviter le tremblement
des vertex sur GPU (UTM ~ 800 000 m ne tient pas en float32).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

# Clé globale (trou, profondeur) : permet d'interpoler les positions de
# TOUS les trous en un seul appel numpy (np.interp sur clé monotone).
DEPTH_KEY = 1.0e4  # profondeur max supportée par trou : 10 000 m


@dataclass
class HoleTable:
    ids: np.ndarray            # (H,) str
    x: np.ndarray              # (H,) float64  collet est
    y: np.ndarray              # (H,) float64  collet nord
    z: np.ndarray              # (H,) float64  collet élévation
    az: np.ndarray             # (H,) float32  azimut initial (deg)
    dip: np.ndarray            # (H,) float32  pendage initial (deg, négatif = vers le bas)
    length: np.ndarray         # (H,) float32  profondeur totale (m)
    zone: np.ndarray           # (H,) int8     zone / prospect
    # Trajectoire : stations à pas régulier, aplaties (tous trous).
    st_key: np.ndarray = field(default=None)   # (S,) float64  idx*DEPTH_KEY+depth
    st_xyz: np.ndarray = field(default=None)   # (S,3) float64 positions réelles

    @property
    def n(self) -> int:
        return int(self.x.shape[0])


@dataclass
class IntervalTable:
    """Un domaine : intervalles [d0, d1] le long des trous."""
    name: str
    kind: str                  # "cat" (litho, altération) | "num" (teneur)
    hole_idx: np.ndarray       # (N,) int32
    d0: np.ndarray             # (N,) float32
    d1: np.ndarray             # (N,) float32
    value: np.ndarray          # (N,) float32 : code catégorie OU teneur
    unit: str = ""
    categories: tuple = ()     # pour kind == "cat" : codes lisibles

    @property
    def n(self) -> int:
        return int(self.hole_idx.shape[0])


@dataclass
class SceneModel:
    origin: np.ndarray                         # (3,) float64
    holes: HoleTable
    domains: dict = field(default_factory=dict)  # name -> IntervalTable

    def add_domain(self, table: IntervalTable) -> None:
        self.domains[table.name] = table

    def summary(self) -> str:
        lines = [f"{self.holes.n:,} trous"]
        for name, t in self.domains.items():
            lines.append(f"  {name:<12} {t.n:>11,} intervalles")
        return "\n".join(lines)
