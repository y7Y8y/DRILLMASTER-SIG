"""DrillMaster — StyleResolver : source unique de résolution visuelle.

Volet 1 de la SPEC de restructuration (condition D1-1, validée
28/08/2026) : la coupe 2D et la vue 3D
doivent consommer LE MÊME résolveur pour la couleur, le libellé et le
code court d'un code géologique — « une seule source de vérité
visuelle ».  Si l'onglet Interprétation doit écrire de la logique de
couleur, c'est que ce module a raté son travail.

Avant v2.9.145 : la vue 3D portait ses propres replis de couleur
(``min_map``/``alt_map`` codés en dur dans ``ui/view_3d.py``) qui
DIVERGEAIENT du référentiel partagé — la 2D utilisait
``automatic_code_color`` (core.reference) pour les codes inconnus, la 3D
ses cartes privées.  Désormais les replis sont CANONIQUES :

  code connu   → entrée du Référentiel (chaîne ``normalized_code`` suivie) ;
  code inconnu → ``suggested_litho_color`` (litho) ou
                 ``automatic_code_color`` (autres domaines) ;
  libellé      → entrée du Référentiel, repli code brut ;
  code court   → ``mineral_symbols.style_display_code`` (minéralisations),
                 abréviation par segments (altérations), tel quel
                 (teneurs/intercepts = libellé numérique).

Pur Python, zéro Qt : les méthodes renvoient des chaînes hex — la vue
appelle QColor() dessus.
"""

from __future__ import annotations

import re
from typing import Optional

# Domaine « vue » (2D/3D) → clé du Référentiel partagé.
DOMAIN_KEYS = {
    "litho": "lithology",
    "alterations": "alteration",
    "mineralizations": "mineralization_style",
    # v2.9.260-3D — les mesures `structure` ont leur propre famille du
    # Référentiel (codes `type`, libellés/couleurs du domaine `structure`).
    "structure": "structure",
}

# Couleur neutre quand tout a échoué (code vide).
UNKNOWN_COLOR = "#7F8C8D"


class StyleResolver:
    """Résolveur canonique couleur / libellé / code court par domaine."""

    def __init__(self, project=None):
        self._project = project

    def set_project(self, project):
        """Branche le projet courant (source du Référentiel)."""
        self._project = project

    # ------------------------------------------------------------------
    # Chemin canonique (identique coupe 2D / vue 3D)
    # ------------------------------------------------------------------
    def _resolve(self, code: str, domain: str):
        """Style résolu via le projet (Référentiel), ou None sans projet.

        Suit EXACTEMENT ``DrillMasterProject.resolve_category_style`` :
        lithologie avec repli ``suggested_litho_color``, le reste avec
        ``automatic_code_color`` — plus de cartes privées par vue.
        """
        if self._project is None:
            return None
        resolver = getattr(self._project, "resolve_category_style", None)
        if resolver is None:
            return None
        repo_domain = DOMAIN_KEYS.get(domain, "lithology")
        try:
            return resolver(repo_domain, str(code or "").strip())
        except Exception as _exc:
            from .diagnostics import log_swallowed
            log_swallowed(f"Résolveur de style : code {code!r} du domaine "
                          f"{domain} non résolu (repli canonique)", _exc)
            return None

    # ------------------------------------------------------------------
    # Couleur
    # ------------------------------------------------------------------
    def code_color(self, code: str, domain: str) -> str:
        """Couleur hex canonique d'un code (voie partagée 2D/3D)."""
        c = str(code or "").strip()
        if not c:
            return UNKNOWN_COLOR
        st = self._resolve(c, domain)
        if st is not None:
            color = getattr(st, "color", None)
            if color:
                return str(color)
        # Repli CANONIQUE (même règle que la coupe 2D) :
        repo_domain = DOMAIN_KEYS.get(domain, "lithology")
        if repo_domain == "lithology":
            from .section import suggested_litho_color
            return suggested_litho_color(c)
        from .reference import automatic_code_color
        return automatic_code_color(repo_domain, c)

    # ------------------------------------------------------------------
    # Motif (v2.9.150 — SPEC B-2/D2 : motifs sur les tubes 3D)
    # ------------------------------------------------------------------
    def code_pattern(self, code: str, domain: str) -> str:
        """Motif du Référentiel pour un code (ex. « diagonal »), ou "".

        Même chemin que la couleur/libellé : entrée du Référentiel,
        repli vide (pas de motif → tube plein).
        """
        c = str(code or "").strip()
        if not c:
            return ""
        st = self._resolve(c, domain)
        if st is not None:
            pattern = getattr(st, "pattern", None)
            if pattern:
                return str(pattern).strip()
        return ""

    # ------------------------------------------------------------------
    # Libellé
    # ------------------------------------------------------------------
    def code_label(self, code: str, domain: str) -> str:
        """Libellé résolu du Référentiel (ex. « Hématisation » pour HEM),
        repli sur le code brut."""
        c = str(code or "").strip()
        if not c:
            return c
        st = self._resolve(c, domain)
        if st is not None:
            label = getattr(st, "label", None)
            if label:
                return str(label).strip()
        return c

    # ------------------------------------------------------------------
    # Code court (légendes)
    # ------------------------------------------------------------------
    @staticmethod
    def short_code(code: str, domain: str) -> str:
        """Code COURT affiché en légende (cohérent coupe 2D / vue 3D).

        - minéralisations → code 2 lettres (MASSIVE→MA, FILONIENNE→FI…)
          via ``mineral_symbols.style_display_code`` ;
        - altérations / repli → 3 premières lettres de chaque segment
          (ARGILIQUE→ARG, CHLORITE_MAGNETITE→CHL_MAG) ;
        - teneurs / intercepts → libellé numérique TEL QUEL (ne jamais
          abréger : le point décimal serait avalé — « 5.15 – 10.99 ») ;
        - sinon le code brut majuscule.
        """
        raw = str(code or "").strip()
        if not raw:
            return raw
        # v2.9.267 — géotechnique 3D : la légende affiche des VALEURS
        # (« 2.6 g/cm³ »), jamais des codes — même règle que les teneurs,
        # sinon l'abréviation avale l'unité et le point décimal.
        if domain in ("assays", "intercepts", "rqd", "recovery", "density"):
            return raw
        if domain == "mineralizations":
            try:
                from .mineral_symbols import style_display_code
                sc = style_display_code(raw)
                if sc:
                    return sc.upper()
            except ImportError:
                # module symbole absent (pack réduit) — repli abréviation.
                # SILENCE JUSTIFIÉ : fonctionnalité optionnelle.
                pass
        segs = []
        for part in re.split(r"[_\s\-]+", raw):
            letters = "".join(ch for ch in part if ch.isalnum())
            if letters:
                segs.append(letters[:3].upper())
        if segs:
            return "_".join(segs)
        return raw.upper()
