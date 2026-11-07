"""Noyau de la flotte : un agent = une fonction qui inspecte le code et rend
des constats. Un département = un chef qui regroupe ses agents.

Aucun constat n'est une opinion : chacun porte un fichier, une ligne quand
c'est possible, et une mesure. Le rapport est reproductible : deux exécutions
sur le même code donnent exactement le même résultat.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PLUGIN = RACINE / "DrillMaster"

ORDRE = {"bloquant": 0, "majeur": 1, "mineur": 2, "note": 3}


@dataclass
class Constat:
    gravite: str = ""       # bloquant | majeur | mineur | note
    agent: str = ""
    departement: str = ""
    fichier: str = ""
    ligne: int = 0
    mesure: str = ""       # le chiffre, la preuve
    probleme: str = ""
    pourquoi: str = ""     # ce que l'utilisateur ressent
    action: str = ""       # ce qu'on fait, concrètement

    def cle(self):
        return (ORDRE[self.gravite], self.departement, self.agent, self.fichier,
                self.ligne)


@dataclass
class Departement:
    nom: str
    chef: str                       # ce que ce département possède
    agents: list = field(default_factory=list)

    def recrute(self, agent):
        self.agents.append(agent)
        return agent


@dataclass
class Contexte:
    """Ce que les agents ont le droit de lire : le code, rien d'autre."""
    fichiers: list
    sources: dict        # chemin relatif -> texte
    arbres: dict         # chemin relatif -> ast.Module (None si non parsable)

    @classmethod
    def charge(cls):
        fichiers, sources, arbres = [], {}, {}
        for f in sorted(PLUGIN.rglob("*.py")):
            rel = str(f.relative_to(RACINE))
            if "__pycache__" in rel:
                continue
            txt = f.read_text(encoding="utf-8", errors="ignore")
            fichiers.append(rel)
            sources[rel] = txt
            try:
                arbres[rel] = ast.parse(txt)
            except SyntaxError:
                arbres[rel] = None
        return cls(fichiers, sources, arbres)

    def lignes(self, rel):
        return self.sources[rel].splitlines()

    def fichiers_de(self, motif):
        return [f for f in self.fichiers if re.search(motif, f)]


FLOTTE: list[Departement] = []


def departement(nom, chef):
    d = Departement(nom, chef)
    FLOTTE.append(d)
    return d


def agent(departement_obj, identifiant, titre, gravite="mineur"):
    """Décorateur : enregistre un agent dans son département."""
    def enveloppe(fn):
        fn.agent_id = identifiant
        fn.titre = titre
        fn.gravite = gravite
        fn.departement = departement_obj.nom

        def lance(ctx):
            constats = fn(ctx) or []
            for c in constats:
                c.agent = identifiant
                c.departement = departement_obj.nom
                if not c.gravite:
                    c.gravite = gravite
            return constats
        lance.agent_id = identifiant
        lance.titre = titre
        lance.gravite = gravite
        departement_obj.recrute(lance)
        return enveloppe
    return enveloppe


def compte(motif, ctx, fichiers=None):
    """Nombre d'occurrences d'un motif dans les sources (avec les lieux)."""
    trouves = []
    for rel in (fichiers or ctx.fichiers):
        for no, ligne in enumerate(ctx.sources[rel].splitlines(), 1):
            if re.search(motif, ligne):
                trouves.append((rel, no, ligne.strip()))
    return trouves


def ligne_de(texte, extrait):
    for no, ligne in enumerate(texte.splitlines(), 1):
        if extrait in ligne:
            return no
    return 0
