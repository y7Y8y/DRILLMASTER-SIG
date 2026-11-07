"""Socle commun des agents d'audit DrillMaster.

Chaque agent est un script autonome qui produit un rapport JSON + Markdown.
Aucun agent n'écrit dans les sources : lecture seule, sortie dans audit/reports/.

Conventions
-----------
* Un agent = une question. S'il ne trouve rien, il le dit (pas de faux positif).
* Toute conclusion porte au moins une preuve : fichier + ligne.
* Le score est calculé, jamais déclaré.
"""
from __future__ import annotations

import ast
import json
import os
from dataclasses import dataclass, field, asdict

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "DrillMaster")
SRC = os.path.abspath(SRC)
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "audit", "reports"))


def py_files():
    for root, _dirs, files in os.walk(SRC):
        if "__pycache__" in root:
            continue
        for f in sorted(files):
            if f.endswith(".py"):
                yield os.path.join(root, f)


def rel(path):
    return os.path.relpath(path, SRC).replace(os.sep, "/")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def tree(path):
    try:
        return ast.parse(read(path))
    except SyntaxError:
        return None


@dataclass
class Finding:
    severite: str          # bloquant | majeur | moyen | mineur
    categorie: str
    titre: str
    preuve: str            # fichier:ligne
    detail: str = ""
    correction: str = ""


@dataclass
class Report:
    agent: str
    direction: str
    question: str
    findings: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    note_max: int = 10

    @property
    def score(self):
        poids = {"bloquant": 3, "majeur": 2, "moyen": 1, "mineur": 0.4}
        penalite = sum(poids.get(f.severite, 1) for f in self.findings)
        return max(0, round(self.note_max - penalite, 1))

    def save(self):
        os.makedirs(OUT, exist_ok=True)
        slug = self.agent.lower().replace(" ", "_")
        payload = {
            "agent": self.agent,
            "direction": self.direction,
            "question": self.question,
            "score": self.score,
            "metrics": self.metrics,
            "findings": [asdict(f) for f in self.findings],
        }
        with open(os.path.join(OUT, slug + ".json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        return payload
