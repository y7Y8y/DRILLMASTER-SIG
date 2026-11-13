"""Banc d'essai scene3d : python tools/bench_scene3d.py [petit|moyen|grand|enorme ...]
Mesure le COÛT CPU de préparation (pas la fluidité GPU : à mesurer chez l'utilisateur)."""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import numpy as np
from scene3d.synthetic import make_mine
from scene3d import (interval_segments, build_spatial_index, lod_selection,
                     expand_tubes)

def mb(b): return b / 1e6

def run(profile):
    print(f"\n=== Profil « {profile} » ===")
    t = time.perf_counter(); m = make_mine(profile)
    print(f"génération mine fictive : {time.perf_counter()-t:6.2f} s")
    print(m.summary())
    tot_rows = tot_bytes = 0
    t_seg = 0.0; segs = {}
    for name in m.domains:
        t = time.perf_counter()
        off = 1.5 if m.domains[name].kind == "num" else 0.0
        s = interval_segments(m, name, lateral_offset=off)
        dt = time.perf_counter() - t
        t_seg += dt; segs[name] = s
        tot_rows += s.n; tot_bytes += s.nbytes
        print(f"segments {name:<11} {s.n:>10,} lignes  {dt:6.2f} s  {mb(s.nbytes):7.1f} Mo")
    print(f"TOTAL instances GPU : {tot_rows:,} lignes, {mb(tot_bytes):.0f} Mo, "
          f"préparation {t_seg:.2f} s")
    big = max(segs.values(), key=lambda s: s.n)
    t = time.perf_counter(); idx = build_spatial_index(m, big); dt = time.perf_counter()-t
    print(f"index spatial (domaine max) : {dt:5.2f} s, {idx.counts.size} cellules")
    # caméra au centre de la zone Centre, zoom serré puis large
    for label, near, view in (("zoom sur une zone", 600, 2500),
                              ("vue d'ensemble", 3000, 12000)):
        c = np.array([0.0, 0.0]) - m.origin[:2] + np.array([250000.0, 800000.0])
        sel = lod_selection(idx, c, near, view)
        print(f"LOD {label:<18}: {sel['rows_near']:>9,} lignes détaillées "
              f"+ {sel['rows_mid_decimated']:>8,} décimées "
              f"({sel['cells_near']}/{sel['cells_total']} cellules proches)")
    # repli CPU (maillage tubes 6 faces) mesuré sur 300 000 segments
    n = min(300_000, big.n)
    t = time.perf_counter(); v = expand_tubes(big.p0[:n], big.p1[:n], 0.4, 6)
    dt = time.perf_counter() - t
    full_mb = mb(v.nbytes) * big.n / n
    print(f"REPLI maillage CPU (sans instanciation) : {dt:.2f} s pour {n:,} segments "
          f"→ extrapolé {big.n:,} : {dt*big.n/n:.1f} s et {full_mb:.0f} Mo "
          f"(vs {mb(big.nbytes):.0f} Mo en instances)")

if __name__ == "__main__":
    for p in (sys.argv[1:] or ["petit", "moyen", "grand"]):
        run(p)
