"""Chantier 11 — la vitesse, mesurée sur le vrai travail, pas sur le nombre de boucles.

    python3 tools/audit_vitesse.py [--ecrit]

Un chiffre comme « 196 boucles » ne dit rien : une boucle sur 14 forages est
gratuite, une boucle sur 3 180 analyses dans un `paintEvent` coûte 16 ms —
soit une frame. On mesure donc trois choses :

1. **le temps réel** du calcul d'une coupe sur les chiffres du projet de
   référence (64 forages, 3 180 analyses) ;
2. **les boucles imbriquées** des vues (le signe d'un calcul en O(n²)) ;
3. **les points de mesure** : combien de modules mesurent le temps, et
   combien **publient** leur mesure (défaut constaté : trois modules de
   mesure, aucune publication).

Ce que ce n'est *pas* : un benchmark de Qt (impossible ici). Le calcul pur se
mesure ; le rendu graphique, non — et on le dit au lieu de l'inventer.
"""
from __future__ import annotations

import ast
import json
import statistics
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PLUGIN = RACINE / "DrillMaster"
sys.path.insert(0, str(RACINE))


def boucles_imbriquees(arbre):
    """Nombre de boucles qui contiennent une autre boucle."""
    n = 0
    for noeud in ast.walk(arbre):
        if isinstance(noeud, (ast.For, ast.While)):
            for sous in ast.walk(noeud):
                if isinstance(sous, (ast.For, ast.While)) and sous is not noeud:
                    n += 1
                    break
    return n


def mesure_coupe(essais=7):
    """Le temps réel : projeter une coupe de 64 forages, 3 180 analyses."""
    from drillmaster_v3.core.coupe2d.coupe import (Ligne, inclusion, intercepts,
                                                   projette)
    from drillmaster_v3.core.donnees.lecture import Forage

    # Coupe 004 : 195 m, orientée N045°. Les colliers du projet de référence
    # sont posés LE LONG de cette ligne (à ±10 m), comme une vraie coupe :
    # une ligne posée au hasard ne contiendrait que 10 forages sur 64 et la
    # mesure ne dirait rien du cas réel.
    import math
    a = math.radians(45)
    ligne = Ligne(512000, 731800,
                  512000 + 195 * math.sin(a), 731800 + 195 * math.cos(a))
    forages = [Forage(id=f"ISBRC{i:03d}",
                      x=512000 + (i * 3.0) * math.sin(a) + (i % 5 - 2),
                      y=731800 + (i * 3.0) * math.cos(a) + (i % 3 - 1),
                      z=219.8 - i * 0.2, profondeur=110 + i % 7 * 8)
                 for i in range(1, 65)]
    # 3 180 analyses réparties : ~50 par forage du projet
    analyses = []
    for k, f in enumerate(forages):
        for j in range(50):
            # 3 180 analyses au total : ~50 par forage, 2 m chacune
            analyses.append((f.id, j * 2.0, j * 2.0 + 2.0,
                             0.1 + ((k * 7 + j * 3) % 90) / 10.0))

    temps = []
    for _ in range(essais):
        t0 = time.perf_counter()
        inc = inclusion(forages, ligne, 60.0)
        retenus = inc.inclus if hasattr(inc, "inclus") else inc
        traces = projette(retenus, ligne)
        inter = intercepts(analyses, [1.0, 5.0])
        temps.append((time.perf_counter() - t0) * 1000.0)
    return {
        "median_ms": round(statistics.median(temps), 2),
        "min_ms": round(min(temps), 2),
        "max_ms": round(max(temps), 2),
        "forages": len(traces),
        "intercepts": len(inter) if not isinstance(inter, tuple) else len(inter[0]),
        "analyses": len(analyses),
    }


def points_de_mesure():
    """Qui mesure le temps, et qui publie ce qu'il mesure."""
    mesureurs, publieurs = [], []
    for f in sorted(PLUGIN.rglob("*.py")):
        texte = f.read_text(encoding="utf-8", errors="ignore")
        rel = str(f.relative_to(PLUGIN)).replace("\\", "/")
        if "perf_counter" in texte or "QElapsedTimer" in texte:
            mesureurs.append(rel)
        if any(m in texte for m in ("log_message(", "qgsMessageLog", "QgsMessageLog",
                                    "self.status", "status_bar")):
            if "perf_counter" in texte or "elapsed" in texte:
                publieurs.append(rel)
    return mesureurs, publieurs


def main(argv):
    print("── le calcul d'une coupe, mesuré sur le projet de référence")
    try:
        coupe = mesure_coupe()
        print(f"  {coupe['forages']} forages · {coupe['analyses']} analyses "
              f"· {coupe['intercepts']} intercepts")
        print(f"  médiane {coupe['median_ms']} ms "
              f"(min {coupe['min_ms']} · max {coupe['max_ms']})")
        budget = 16.0
        verdict = "tient dans une frame" if coupe["median_ms"] < budget \
            else "NE TIENT PAS dans une frame"
        print(f"  budget d'une frame à 60 fps : {budget} ms → {verdict}")
    except Exception as exc:                       # noqa: BLE001
        coupe = {"erreur": str(exc)}
        print(f"  mesure impossible : {exc}")

    print("\n── les boucles imbriquées des vues (signe de calcul en O(n²))")
    imbriquees = {}
    for f in sorted((PLUGIN / "ui").rglob("*.py")):
        try:
            arbre = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        n = boucles_imbriquees(arbre)
        if n:
            imbriquees[f.name] = n
    total = sum(imbriquees.values())
    for nom, n in sorted(imbriquees.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {n:4}  {nom}")
    print(f"  total : {total} dans {len(imbriquees)} fichiers")

    mesureurs, publieurs = points_de_mesure()
    print(f"\n── la mesure du temps : {len(mesureurs)} module(s) mesurent")
    for m in mesureurs:
        print(f"    {m}")
    print(f"  {len(publieurs)} publie(nt) la mesure à l'utilisateur")

    if "--ecrit" in argv:
        sortie = {"coupe": coupe, "budget_frame_ms": 16.0,
                  "boucles_imbriquees": imbriquees,
                  "boucles_imbriquees_total": total,
                  "modules_qui_mesurent": mesureurs,
                  "modules_qui_publient": publieurs}
        (RACINE / "specs" / "data" / "vitesse.json").write_text(
            json.dumps(sortie, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("\nécrit specs/data/vitesse.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
