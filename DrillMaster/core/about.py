"""DrillMaster — fiche d'identité et attribution du plugin (v2.9.272).

Pourquoi ce module existe
-------------------------
Jusqu'à la v2.9.271 l'auteur n'apparaissait NULLE PART : ``metadata.txt``
disait « DrillMaster Team », il n'y avait ni ``LICENSE`` ni ``README``, et
aucun dialogue « À propos ».  Résultat : ni l'utilisateur du plugin, ni un
visiteur du dépôt ne pouvait savoir qui l'a écrit ni sous quels droits il
pouvait l'utiliser (audit forensique, PASS 9 — attribution inexistante).

Règles de ce module
-------------------
1. **Source unique** : la version vient de ``metadata.txt`` (comme
   ``drillmaster.py`` pour le démarreur et ``build_release.py`` pour le
   zip) — jamais recopiée en dur dans une vue.
2. **Aucune dépendance Qt** : importable et testable hors QGIS.
3. **Ne lève jamais** : une fiche d'identité illisible ne doit pas
   empêcher le plugin de démarrer (même contrat que ``make_splash``).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Chemins (le paquet vit dans DrillMaster/, le dépôt au-dessus)
# ---------------------------------------------------------------------------
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(PLUGIN_DIR)


def license_file(plugin_dir: str | None = None) -> str:
    """Le `LICENSE` **du paquet**, sinon celui du dépôt (v2.9.394·chantier 12).

    Le défaut mesuré : le chemin était calculé AU-DESSUS du dossier du
    plugin. Dans le dépôt, cela tombait sur le `LICENSE` de la racine —
    donc « trouvé » pour l'auteur, et **introuvable pour tout le monde** :
    une fois installé, `plugins/DrillMaster/` n'a rien au-dessus de lui, et
    la fenêtre « À propos » annonçait « Fichier LICENSE introuvable » à
    chaque utilisateur alors que la licence était bien livrée.
    """
    ici = os.path.join(plugin_dir or PLUGIN_DIR, "LICENSE")
    if os.path.isfile(ici):
        return ici
    return os.path.join(REPO_DIR, "LICENSE")

# ---------------------------------------------------------------------------
# Attribution — valeurs de repli si metadata.txt est muet
# ---------------------------------------------------------------------------
AUTHOR = "Yann BONFUL"
COPYRIGHT = "Copyright © 2026 Yann BONFUL"

# ---------------------------------------------------------------------------
# Licence — GPL-2.0-or-later (choix de l'auteur, v2.9.272).  Compatible avec
# le dépôt officiel des extensions QGIS.  Le texte intégral est le fichier
# LICENSE, livré DANS le paquet (texte gnu.org/gpl-2.0 verbatim).
# ---------------------------------------------------------------------------
LICENSE_ID = "GPL-2.0-or-later"
LICENSE_NAME = "GNU General Public License version 2 ou ultérieure"

REPOSITORY = "https://github.com/y7Y8y/DrillMaster"

#: Avis court de licence, tel que recommandé par la GPL §« How to Apply ».
#: En anglais : c'est le texte canonique de la licence, jamais traduit.
LICENSE_NOTICE = """\
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""


def read_metadata(plugin_dir: str | None = None) -> dict:
    """``metadata.txt`` → dictionnaire (clés en minuscules).

    Ne lève jamais : fichier absent ou ligne malformée → clé absente.
    """
    path = os.path.join(plugin_dir or PLUGIN_DIR, "metadata.txt")
    out: dict = {}
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.startswith("[") and line.endswith("]"):
                    continue  # en-tête de section [general]
                key, value = line.split("=", 1)
                out[key.strip().lower()] = value.strip()
    except Exception as _exc:
        from .diagnostics import log_swallowed
        log_swallowed("Fiche d'identité : lecture de metadata.txt "
                      "(valeurs de repli)", _exc)
        return {}
    return out


def about_info(plugin_dir: str | None = None) -> dict:
    """Fiche d'identité complète du plugin (une seule source de vérité).

    Clés garanties présentes (valeurs éventuellement vides, jamais None).
    """
    meta = read_metadata(plugin_dir)
    return {
        "name": meta.get("name") or "DrillMaster",
        "version": meta.get("version") or "",
        "author": meta.get("author") or AUTHOR,
        "copyright": COPYRIGHT,
        "license_id": LICENSE_ID,
        "license_name": LICENSE_NAME,
        "license_file": license_file(plugin_dir),
        "license_installed": os.path.isfile(license_file(plugin_dir)),
        "repository": meta.get("repository") or REPOSITORY,
        "description": meta.get("description") or "",
        "about": meta.get("about") or "",
        "qgis_minimum": meta.get("qgisminimumversion") or "",
        "qgis_maximum": meta.get("qgismaximumversion") or "",
    }


def version_text() -> str:
    """Version lisible (``v2.9.272``) — vide si metadata.txt est muet."""
    version = about_info().get("version") or ""
    return f"v{version}" if version else ""
