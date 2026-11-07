"""Où en est la conversion des fenêtres d'alerte en messages ?"""
from __future__ import annotations

import ast
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
PLUGIN = RACINE / "DrillMaster"
from .catalogue import CATALOGUE                                # noqa: E402


def restants():
    """Les `QMessageBox` encore présents dans le plugin, avec leur lieu."""
    trouves = []
    for f in sorted(PLUGIN.rglob("*.py")):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        try:
            arbre = ast.parse(txt)
        except SyntaxError:
            continue
        rel = str(f.relative_to(RACINE)).replace("\\", "/")
        for n in ast.walk(arbre):
            if isinstance(n, ast.Call) and \
                    ast.unparse(n.func).startswith("QMessageBox."):
                trouves.append((f"{rel}:{n.lineno}",
                                ast.unparse(n.func).split(".")[-1]))
    return sorted(trouves)


def convertis():
    """Ceux qui ont un message à 5 champs, avec le lieu d'origine."""
    return sorted(CATALOGUE)


def resume():
    n_restants = len(restants())
    n_conv = len(convertis())
    return {
        "fenetres_restantes": n_restants,
        "messages_ecrits": n_conv,
    }
