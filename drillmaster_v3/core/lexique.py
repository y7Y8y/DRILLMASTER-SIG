"""R-01 / R-17 — tout mot affiché vient du lexique, aucun mot technique à l'écran."""
from __future__ import annotations

import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
FICHIER = RACINE / "specs" / "data" / "lexique.json"


class MotInterdit(ValueError):
    """Levée dès qu'une chaîne affichée contient un mot banni (R-17)."""


class Lexique:
    def __init__(self, chemin=FICHIER):
        self.donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
        self.interdits = [m.lower() for m in self.donnees["interdits"]]

    # ── accès par clé, jamais par chaîne libre ───────────────────────
    def niveau(self, cle, champ):
        return self.donnees["niveaux"][cle][champ]

    def famille(self, cle):
        return self.donnees["familles"][cle]["label"]

    def type_donnee(self, cle, champ="label"):
        return self.donnees["types_donnees"][cle][champ]

    def module(self, cle):
        return self.donnees["modules"][cle]

    def rang(self, numero, champ="label"):
        return self.donnees["rangs"][str(numero)][champ]

    # ── garde-fou ───────────────────────────────────────────────────
    def verifie(self, texte):
        """À appeler sur toute chaîne destinée à l'écran.

        La comparaison se fait sur des **mots entiers** : chercher « cache »
        dans le texte refusait « caché », et « sig » refusait « signe ». Un
        garde-fou qui se trompe est pire que pas de garde-fou — c'est
        exactement le reproche que R-47 adresse aux agents.
        """
        import re
        bas = str(texte).lower()
        for mot in self.interdits:
            if re.search(rf"\b{re.escape(mot)}\b", bas):
                raise MotInterdit(
                    f"« {texte} » contient « {mot} », banni de l'interface (R-17)")
        return texte


lexique = Lexique()
