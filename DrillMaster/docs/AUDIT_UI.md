# DrillMaster — Audit UI/UX multi-départements (v2.9.394)

Audit complet de la base extraite de `DrillMaster_v2_9_394.zip` — 56 577 lignes
de Python, 123 fichiers. Chaque département rend compte à la direction unique.

## Méthodologie

Inspection statique exhaustive : structure de classes, constantes de style,
échelle typographique, points d'entrée, redondances inter-modules.

## Rapports par département

### Département Design System

**Constat majeur : le système existe mais n'est pas appliqué.**

| Métrique | Valeur | Verdict |
|---|---|---|
| Couleurs hex hors `styles_qt.py` | **656 occurrences, 166 teintes uniques** | Dérive massive |
| Tailles de police distinctes | **14 valeurs** (7pt → 24pt) | Hors échelle |
| Fichiers UI avec `setStyleSheet` inline | **28 / 31** | Contournement du système |
| `setPointSize` / `setPixelSize` directs | 17 | Double source de vérité |

Incohérences internes du système lui-même (corrigées en Lot DA-0) :

1. Survol des listes déroulantes `#D6EAF8` (bleu) : entre en concurrence avec
   les teintes de données, viole le principe data-ink posé en v2.9.225.
2. Bouton primaire désactivé `#AED6F1` (bleu clair) : rupture du chrome neutre.
3. `BUTTON_SUCCESS` en gras alors que `BUTTON_PRIMARY` ne l'est pas : deux
   hiérarchies concurrentes.
4. `LOG_STYLE` : bordure sur `primary` (couleur d'encre) au lieu d'une couleur
   de bordure.
5. Couleurs d'état codées en dur dans les QSS au lieu de tokens nommés.

### Département Navigation / Architecture de l'information

- `main_dock.py` : structure saine (stepper 4 étapes + stack). Le stepper est
  correct (cercles numérotés, libellés, bulles traduites).
- `section_dock.py` : **11 529 lignes, ~24 groupes de panneaux** construits à
  la main (`_build_tracks_group`, `_build_display_group`, `_build_geometry_group`,
  `_build_collars_group`, `_build_trajectory_group`, `_build_depth_group`,
  `_build_litho_group`, `_build_domain_track_group`, `_build_alteration_group`,
  `_build_mineralization_group`, `_build_structure_group`, `_build_assay_group`,
  `_build_threshold_group`, `_build_grid_advanced_group`, `_build_frame_axes_group`,
  `_build_topography_group`, `_build_legend_group`…). C'est le cœur du problème
  décrit par le porteur : sous-options mélangées aux grands groupes, redondances
  (chaque groupe recrée ses propres contrôles couleur/échelle), aucune
  récurrence de catégories homogènes (ex. « taille » réapparaît différemment
  dans chaque groupe).
- Recommandation : extraire un panneau à onglets sémantiques stables
  (Pistes / Affichage / Échelle & Grille / Légende / Export) avec des
  constructeurs de lignes d'option réutilisables (label + contrôle + unité),
  puis déléguer chaque groupe à un sous-module.

### Département Données / Validation

- `core/validation.py` (2 134 lignes) + `validation_groups.py` : cohérents.
- `core/` bien découpé (49 modules, responsabilités claires). Aucun défaut
  bloquant détecté à ce niveau.

### Département 2D (Coupes)

- Rendu mature : motifs anti-ambiguïté (v2.9.152), échelle commune, fenêtre
  d'élévation, z-order des trous, seuils multi-règles.
- Point de friction : les styles de piste vivent dans `section_dock.py` alors
  que la résolution de style est dans `core/style_resolver.py` + `core/geo_style.py`
  — à regrouper lors du chantier IA.

### Département 3D

- `view_3d*.py` : **8 fichiers, ~2 700 lignes** avec plusieurs générations
  coexistantes (`view_3d.py`, `view_3d_v2.py`, `view_3d_canvas.py`,
  `view_3d_renderer.py`…). Redondance structurelle : identifier la génération
  canonique et retirer les anciennes.

### Département i18n / QA

- `drillmaster_en.ts` : 383 Ko — la traduction suit. `drillmaster_fr.ts` : 409
  octets (vide) : le français est la langue source, cohérent.
- 7 scripts de test dans `tools/` — couverture mince pour 56 K lignes ; les
  tests ciblent la géométrie, pas l'UI.

## Plan d'exécution proposé (lots)

- **Lot DA-0 (fait)** : tokens centralisés (`ui/design_tokens.py`),
  `styles_qt.py` refacturé sur les tokens, états corrigés (survol/désactivé
  neutres), échelle typographique fermée, stepper aligné.
- **Lot DA-1** : composants réutilisables (ligne d'option, groupe repliable
  normalisé, barre de statut) dans un `ui/widgets/` commun.
- **Lot IA-1** : restructuration du panneau de coupe en onglets sémantiques ;
  récurrence des catégories (taille/espacement/couleur identiques d'un groupe
  à l'autre).
- **Lot 3D-1** : consolidation des générations `view_3d*`.
- **Lot QA-1** : tests de non-régression visuelle (snapshots) + lint anti-dérive
  (interdire les hex hors `design_tokens.py`).
