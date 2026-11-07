"""Démonstration exécutable : un fichier réel entre, un résultat réel sort.

    python3 tools/demo_fonctionnel.py

Écrit un CSV de 64 forages, l'importe, calcule la coupe, les intercepts, exclut
un forage, et affiche ce que l'utilisateur verrait — messages compris.
Le fichier source est vérifié intact à la fin.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.coupe2d.coupe import (Ligne, controle_couverture,
                                               inclusion, intercepts, projette)
from drillmaster_v3.core.geometrie.trajectoire import fond
from drillmaster_v3.projet import Projet


def fabrique(chemin):
    lignes = ["ID;X;Y;Z;PROF"]
    for i in range(1, 65):
        x = 512000 + i * 12
        y = 731800 + i * 4
        z = 220 - i * 0.15
        lignes.append(f"ISBRC{i:03d};{x};{y};{z:.1f};{110 + i}")
    lignes.insert(45, "ISBRC045;512540;731980;213.2;155")   # doublon réel
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "ISSIA_COLLAR.csv"
        fabrique(src)
        avant = hashlib.sha256(src.read_bytes()).hexdigest()

        p = Projet(nom="Issia")
        lec = p.importe(src)
        print(f"── import : {lec.resume()}")
        for m in lec.messages:
            print(f"   [{m.label}] {m.titre}")
            print(f"      pourquoi : {m.pourquoi}")
            print(f"      concerné : {', '.join(m.concernes)}")
            print(f"      résoudre : {' / '.join(m.resoudre)}")

        # décision : on exclut le doublon (une fois, partout)
        if p.exclusions or any(f.id == "ISBRC045" for f in p.colliers):
            p.exclut("ISBRC045", "doublon signalé par l'import")
        print(f"── après décision : {len(p.forages_actifs())} forages actifs, "
              f"{len(p.exclusions)} exclusion(s)")

        ligne = Ligne(512000, 731800, 512780, 731860)
        inc = inclusion(p.forages_actifs(), ligne, buffer=120)
        print(f"── coupe à {ligne.orientation}° ({ligne.longueur:.0f} m) : "
              f"{inc.resume()}")

        traces = projette(inc.inclus, ligne)
        for t in traces[:3]:
            print(f"   {t.id:10} abscisse {t.abscisse:6.1f} m · collet "
                  f"{t.altitude_collet:7.2f} · fond {t.altitude_fond:7.2f}")
        for m in controle_couverture(traces, ligne.longueur):
            print(f"   [{m.label}] {m.titre}")

        # trajectoires calculées et comparées
        mes = {f.id: [(0, 110, -60), (50, 112, -68), (100, 113, -70)]
               for f in inc.inclus[:5]}
        for fid, m in list(mes.items())[:2]:
            a = fond(0, 0, 100, m, "angle_moyen", 100)
            b = fond(0, 0, 100, m, "courbure_minimale", 100)
            print(f"── {fid} : fond angle moyen ({a.x:6.1f}, {a.y:6.1f}, "
                  f"{a.z:6.1f}) · courbure min ({b.x:6.1f}, {b.y:6.1f}, "
                  f"{b.z:6.1f})")

        # intercepts
        from drillmaster_v3.core.coupe2d.coupe import rattachement
        ids_coupes = {t.id for t in traces}
        for orphelin in ("ISBRC999",):
            m = rattachement(orphelin, ids_coupes)
            if m:
                print(f"── [{m.label}] {m.titre}")
                print(f"   concerné : {m.concernes[0]} · "
                      f"{m.resoudre[0]}")
        ana = [("ISBRC001", 0, 2, 0.05), ("ISBRC001", 2, 6, 1.8),
               ("ISBRC002", 0, 3, 0.4), ("ISBRC002", 3, 4, 2.2)]
        print("── intercepts > 1 ppm :")
        for i in intercepts(ana, [0.1, 1.0], longueur_min=1.0):
            print(f"   {i['forage']} {i['de']:.0f}–{i['a']:.0f} m "
                  f"(seuil {i['seuil']} ppm)")

        apres = hashlib.sha256(src.read_bytes()).hexdigest()
        print(f"── fichier source intact : {avant == apres}")


if __name__ == "__main__":
    main()
