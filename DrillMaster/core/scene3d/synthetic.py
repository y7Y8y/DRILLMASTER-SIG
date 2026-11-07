"""
scene3d.synthetic — mine fictive réaliste (type camp minier ivoirien).

Hypothèses (à ajuster avec les vrais chiffres du projet) :
- 3 zones : Nord, Centre, Est (campagnes RC + carottés) ;
- trous Az 110 / 290, pendage -50 à -60 (comme les coupes du projet) ;
- profondeur 60 à 250 m, légère dérive de trajectoire ;
- litho loguée ~1 intervalle / 3 m ; teneurs 1 échantillon / m, 2 éléments
  (Li, Rb ppm) ; altération ~1 intervalle / 8 m ;
- profil d'altération latéritique : LAT/SAP/SPR en tête, puis roche saine.
- UTM zone 29N, origine locale pour éviter la perte de précision float32.
"""
from __future__ import annotations

import numpy as np

from .model import HoleTable, IntervalTable, SceneModel
from .geometry import build_trajectories

PROFILES = {          # nombre total de trous
    "petit":   600,   # un prospect
    "moyen":   4_000, # un gisement
    "grand":   20_000,# une mine en exploitation
    "enorme":  50_000,# camp minier multi-décennies
}

LITHO = ("LAT", "SAP", "SPR", "MTZ", "MIS", "SDS", "PEG", "QTZ", "NS")
ALTER = ("NONE", "SER", "CHL", "SIL", "CARB")


def _intervals(rng, length, mean_len):
    """Intervalles contigus couvrant [0, length] pour tous les trous, vectorisé."""
    H = length.size
    n = np.maximum(2, (length / mean_len).astype(np.int64))
    hidx = np.repeat(np.arange(H, dtype=np.int32), n)
    starts = np.r_[0, np.cumsum(n)[:-1]]
    w = rng.gamma(2.0, 1.0, size=hidx.size)
    sums = np.add.reduceat(w, starts)
    w = w / sums[hidx] * length[hidx]
    c = np.cumsum(w)
    base = np.r_[0.0, c[starts[1:] - 1]]
    d1 = c - base[hidx]
    d0 = d1 - w
    return hidx, d0.astype(np.float32), d1.astype(np.float32)


def make_mine(profile: str = "moyen", seed: int = 7) -> SceneModel:
    rng = np.random.default_rng(seed)
    H = PROFILES[profile]

    # ---- zones : Nord / Centre / Est, rectangles allongés NNE (Birimien)
    share = np.array([0.35, 0.40, 0.25])
    counts = np.round(share * H).astype(int)
    counts[1] += H - counts.sum()
    centers = np.array([[0.0, 6000.0], [0.0, 0.0], [5500.0, 1500.0]])
    zone = np.repeat(np.arange(3, dtype=np.int8), counts)
    x = np.empty(H); y = np.empty(H)
    pos = 0
    strike = np.radians(20.0)
    for zi in range(3):
        n = counts[zi]
        area = n * 1600.0                   # 1 trou / 1 600 m² (≈ 40 m)
        Lz, Wz = np.sqrt(2 * area), np.sqrt(area / 2)
        u = rng.uniform(-Lz / 2, Lz / 2, n)
        v = rng.uniform(-Wz / 2, Wz / 2, n)
        x[pos:pos + n] = centers[zi, 0] + u * np.sin(strike) + v * np.cos(strike)
        y[pos:pos + n] = centers[zi, 1] + u * np.cos(strike) - v * np.sin(strike)
        pos += n
    z = 210.0 + 14 * np.sin(x / 450.0) * np.cos(y / 600.0) + rng.normal(0, 0.6, H)

    az = np.where(rng.random(H) < 0.5, 110.0, 290.0).astype(np.float32)
    dip = -rng.choice([50.0, 55.0, 60.0], H).astype(np.float32)
    length = np.clip(rng.gamma(6.0, 22.0, H), 60, 250).astype(np.float32)

    utm_origin = np.array([250_000.0, 800_000.0, 0.0])   # zone 29N (fictif)
    ids = np.array([f"{('N','C','E')[int(zi)]}{i:05d}"
                    for i, zi in enumerate(zone)])
    holes = HoleTable(ids, x + utm_origin[0], y + utm_origin[1], z,
                      az, dip, length, zone)
    build_trajectories(holes, step=10.0,
                       drift_az=rng.normal(0, 1.5, H),
                       drift_dip=rng.normal(-1.0, 0.6, H))
    model = SceneModel(origin=utm_origin + np.array([0.0, 0.0, 200.0]),
                       holes=holes)

    # ---- lithologie (catégorielle) : profil latéritique puis roche saine
    h, d0, d1 = _intervals(rng, length, 3.0)
    mid = 0.5 * (d0 + d1)
    code = np.empty(h.size, dtype=np.float32)
    r = rng.random(h.size)
    top = mid < 12
    code[top] = np.where(r[top] < 0.5, 0, 1)                    # LAT / SAP
    sap = (mid >= 12) & (mid < 35)
    code[sap] = np.where(r[sap] < 0.6, 2, 3)                    # SPR / MTZ
    rock = mid >= 35
    cuts = np.array([0.55, 0.75, 0.87, 0.94, 1.0])
    code[rock] = np.array([4, 5, 6, 7, 8])[np.searchsorted(cuts, r[rock])]
    model.add_domain(IntervalTable("Lithologie", "cat", h, d0, d1, code,
                                   categories=LITHO))

    # ---- altération (catégorielle)
    h, d0, d1 = _intervals(rng, length, 8.0)
    model.add_domain(IntervalTable(
        "Altération", "cat", h, d0, d1,
        rng.integers(0, len(ALTER), h.size).astype(np.float32),
        categories=ALTER))

    # ---- teneurs 1 m (numériques) : Li et Rb ppm, lognormales
    n_m = np.maximum(1, length.astype(np.int64))
    h = np.repeat(np.arange(H, dtype=np.int32), n_m)
    starts = np.r_[0, np.cumsum(n_m)[:-1]]
    d0 = (np.arange(h.size) - starts[h]).astype(np.float32)
    d1 = d0 + 1.0
    for name, med, sig in (("Li ppm", 150.0, 1.1), ("Rb ppm", 90.0, 0.9)):
        val = rng.lognormal(np.log(med), sig, h.size).astype(np.float32)
        model.add_domain(IntervalTable(name, "num", h, d0, d1, val, unit="ppm"))
    return model
