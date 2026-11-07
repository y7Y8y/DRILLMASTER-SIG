"""Chantier 4 en une commande : les fenêtres d'alerte deviennent un bandeau.

    python3 tools/demo_messages.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from drillmaster_v3.core.bandeau import Bandeau                    # noqa: E402
from drillmaster_v3.core.messages_plugin import (convertis,        # noqa: E402
                                                 par_id, resume)


def main():
    b = Bandeau()
    # trois cas réels, pris dans les 30 fenêtres du plugin
    b.ajoute(par_id("main_dock.py:491"))        # blocage : dossier
    b.ajoute(par_id("lithology_structure_dialog.py:337"))   # avertissement
    b.ajoute(par_id("reference_dialog.py:892"))            # information

    print("── ce que voit un débutant")
    for bloc in b.visible("guidee"):
        print(f"  [{bloc['niveau']}] {bloc['titre']}")
        print(f"     {bloc['ce_qui_se_passe']}")
        print(f"     → {bloc['ce_que_vous_pouvez_faire']}")
        print(f"     suite : {bloc['ce_qui_continue']}")

    print("\n── ce que voit un expert (même message, plus de contexte)")
    bloc = b.visible("experte")[0]
    print(f"  concerne : {', '.join(bloc['concerne'])}")
    print(f"  portee   : {bloc['portee']}")

    print(f"\n── l'étape suivante est-elle arrêtée ? {b.doit_arreter()}")
    print(f"── barre d'état : {b.resume()}")

    print("\n── bouton « copier le détail »")
    print(b.pour_le_support(version="3.0.0", chemin="ISSIA_COLLAR.csv"))

    r = resume()
    print(f"\n── comptabilité : {r['messages_ecrits']} messages écrits pour "
          f"{r['fenetres_restantes']} fenêtres encore dans le plugin")


if __name__ == "__main__":
    main()
