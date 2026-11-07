"""Chantier 2 en une commande : un réglage, cinq lecteurs.

    python3 tools/demo_reglages.py

Chaque ligne affichée est une valeur réellement calculée.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from drillmaster_v3.core.reglages import RefusReglage, Reglages   # noqa: E402


def montre(r, piste, champ):
    lu = r.lecture(piste, champ)
    parts = []
    for vue, d in lu["vues"].items():
        parts.append(f"{vue}={d['valeur']}" if d["raison"] is None
                     else f"{vue}=— ({d['raison']})")
    print(f"  {piste}.{champ:8} {' · '.join(parts)}")


def main():
    r = Reglages()
    for vue in ("2d", "3d", "legende", "export", "carte"):
        r.abonne(vue)

    print("── avant toute décision (valeurs du contrat)")
    montre(r, "assays", "width")
    montre(r, "assays", "side")

    print("\n── une décision, une seule fois")
    c = r.modifie("assays", "width", 28, par="A. Koné",
                  motif="écran du bureau, pas l'imprimante")
    print(" ", c.phrase())

    print("\n── les cinq vues, sans rien régler ailleurs")
    montre(r, "assays", "width")

    print("\n── un champ qu'une vue n'utilise pas : elle le dit")
    montre(r, "assays", "side")

    print("\n── ce qui est refusé, et pourquoi (en mots simples)")
    for essai in (("assays", "width", 900), ("assays", "width", 22)):
        try:
            r.modifie(*essai, par="" if essai[2] == 22 else "A. Koné")
        except RefusReglage as e:
            print(f"  refusé : {e}")
    try:
        r.modifie("couleurs_pistes", "width", 20, par="A. Koné")
    except RefusReglage as e:
        print(f"  refusé : {e}")

    print("\n── retour à la valeur de la famille")
    r.retablit("assays", "width")
    montre(r, "assays", "width")

    print("\n── journal")
    for ch in r.journal():
        print("  " + ch.phrase() + (f"  · motif : {ch.motif}" if ch.motif else ""))
    print("\n" + r.resume())


if __name__ == "__main__":
    main()
