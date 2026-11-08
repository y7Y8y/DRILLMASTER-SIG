"""Chantier 5 en une commande : ce qu'un bouton annonce avant le clic.

    python3 tools/demo_gestes.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from drillmaster_v3.core.gestes import Geste, GesteRefuse            # noqa: E402
from drillmaster_v3.core.gestes_plugin import BARRES               # noqa: E402


def main():
    for nom, fabrique in BARRES.items():
        b = fabrique()
        print(f"── {b['titre']}")
        print(f"   principal   : {b['primaire']}")
        if b["secondaires"]:
            print(f"   secondaires : {', '.join(b['secondaires'])}")
        print(f"   discrets    : {', '.join(b['discrets'])}")
        if b["destructifs"]:
            print(f"   ⚠ peut détruire : {', '.join(b['destructifs'])}")
        print()

    from drillmaster_v3.core.gestes_plugin import gestes_projet
    suppr = gestes_projet()[-1]
    print("── ce que le bouton affiche avant le clic")
    print("  " + suppr.annonce())

    print("\n── ce qui est refusé")
    for essai in ({"signe": "", "motif": "x", "ecrit": True},
                  {"signe": "A. Koné", "motif": "", "ecrit": True},
                  {"signe": "A. Koné", "motif": "projet abandonné",
                   "ecrit": False}):
        try:
            suppr.verifie(**essai)
        except GesteRefuse as e:
            print("  refusé : " + str(e))

    print("\n── et le geste complet passe")
    suppr.verifie(signe="A. Koné", motif="projet abandonné", ecrit=True)
    print("  oui : nom, motif et confirmation écrite sont réunis")


if __name__ == "__main__":
    main()
