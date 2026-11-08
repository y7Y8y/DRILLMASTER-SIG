"""Chantier 7 — la maquette confrontée au code, écran par écran.

    python3 tools/confronte_ecrans.py

Ce que ce n'est pas : une capture d'écran (Qt ne tourne pas dans ce
bac à sable). Ce que c'est : la liste des promesses de chaque planche,
et pour chacune, la preuve que le code la tient, ou le travail qui reste.
Rien n'est coché « fait » sans un cas réel en face.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from drillmaster_v3.core.ecrans import ECRANS, ecarts          # noqa: E402


def main():
    print("── les quatre écrans neufs, confrontés au code")
    total = sum(len(e.promesses) for e in ECRANS)
    tenues = sum(len(e.tenues()) for e in ECRANS)
    print(f"  {len(ECRANS)} écrans · {total} promesses · {tenues} tenues "
          f"· {total - tenues} à faire\n")
    for e in ECRANS:
        print(f"  {e.numero} · {e.nom:12} ({e.maquette})")
        for p in e.promesses:
            marque = {"tenu": "✓", "bloque": "■", "sans_code": "·"}[p.etat]
            print(f"     {marque} {p.phrase[:78]}")
            if p.etat != "tenu":
                print(f"       ↳ reste : {p.preuve[:100]}")
        print()
    reste = ecarts()
    print(f"── {len(reste)} travail(x) numéroté(s) pour la prochaine tranche")
    return 0


if __name__ == "__main__":
    sys.exit(main())
