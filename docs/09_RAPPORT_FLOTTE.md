# 09 — Rapport de la flotte d'agents

> Généré par `python3 tools/flotte/rapport.py` le 2026-11-07.
> Ce rapport n'est pas une opinion : chaque constat cite un fichier, un
> chiffre et l'effet ressenti par l'utilisateur.

## Ce qui a été inspecté

| | |
|---|---|
| Périmètre | `DrillMaster/` — le plugin complet |
| Fichiers | **105** fichiers Python |
| Lignes | **56,577** |
| Agents | 50 répartis en 9 départements |
| Constats | **86** |

## Verdict en une ligne

| Gravité | Nombre | Ce que ça veut dire |
|---|---|---|
| **Bloquant** | 10 | empêche de promettre « simple et fiable » |
| **Majeur** | 46 | se voit à l'usage et fait perdre du temps |
| **Mineur** | 30 | donne l'impression de bricolage |
| **Note** | 0 | occasion manquée, pas un défaut |

## Les départements

| Département | Ce qu'il possède | Agents | Bloquant | Majeur |
|---|---|---|---|---|
| **Direction artistique** | couleur, typographie, espace, icônes | 6 | 0 | 3 |
| **Disposition** | rangement, hiérarchie, densité, alignement | 6 | 0 | 19 |
| **Réglages et partage** | un réglage = un propriétaire ; aucune copie dans une vue | 6 | 4 | 3 |
| **Messages et blocages** | 5 champs par message : ce qui s'est passé, pourquoi, qui est concerné, comment sortir, où | 7 | 1 | 7 |
| **Boutons et actions** | un bouton = un verbe ; une action destructrice = une confirmation | 4 | 4 | 2 |
| **Qualité et dette** | tests, duplication, fichiers monolithes, dépendances | 5 | 0 | 6 |
| **Données et vues** | une donnée, cinq vues ; aucun calcul dupliqué | 5 | 1 | 1 |
| **Cohérence et doctrine** | un mot = une chose ; une règle = un seul endroit | 3 | 0 | 0 |
| **Navigation et options cachées** | tout réglage est atteignable en 1 clic, aucun onglet muet | 8 | 0 | 5 |

---

## Les bloquants, un par un

Ce sont les seuls à traiter avant toute nouvelle maquette.

### B-02 · Actions destructrices sans confirmation claire

**Mesure** — `_on_project_layers_will_be_removed` supprime sans demander confirmation  ·  `DrillMaster/ui/main_dock.py`

**Le problème** — on peut perdre des données sans filet

**Ce que l'utilisateur ressent** — c'est l'erreur qu'on ne pardonne pas : un clic mal placé et le projet est amputé

**Ce qu'on fait** — confirmation qui dit ce qui sera perdu, avec une sortie « annuler » après coup

### B-02 · Actions destructrices sans confirmation claire

**Mesure** — `_remove_generated_layers` supprime sans demander confirmation  ·  `DrillMaster/ui/main_dock.py`

**Le problème** — on peut perdre des données sans filet

**Ce que l'utilisateur ressent** — c'est l'erreur qu'on ne pardonne pas : un clic mal placé et le projet est amputé

**Ce qu'on fait** — confirmation qui dit ce qui sera perdu, avec une sortie « annuler » après coup

### B-02 · Actions destructrices sans confirmation claire

**Mesure** — `_remove_project_group` supprime sans demander confirmation  ·  `DrillMaster/ui/main_dock.py`

**Le problème** — on peut perdre des données sans filet

**Ce que l'utilisateur ressent** — c'est l'erreur qu'on ne pardonne pas : un clic mal placé et le projet est amputé

**Ce qu'on fait** — confirmation qui dit ce qui sera perdu, avec une sortie « annuler » après coup

### B-02 · Actions destructrices sans confirmation claire

**Mesure** — `_delete_current_section` supprime sans demander confirmation  ·  `DrillMaster/ui/section_dock.py`

**Le problème** — on peut perdre des données sans filet

**Ce que l'utilisateur ressent** — c'est l'erreur qu'on ne pardonne pas : un clic mal placé et le projet est amputé

**Ce qu'on fait** — confirmation qui dit ce qui sera perdu, avec une sortie « annuler » après coup

### T-01 · Géométrie recalculée dans les vues

**Mesure** — trigonométrie présente dans 8 fichiers de vue (23 lignes)

**Le problème** — la position des forages est recalculée dans chaque vue

**Ce que l'utilisateur ressent** — la coupe et la 3D finissent par ne plus montrer la même chose ; c'est l'incohérence la plus difficile à croire pour un géologue

**Ce qu'on fait** — un seul calcul de trajectoire dans le noyau, importé par toutes les vues (R-09)

### M-05 · L'erreur technique brute atteint l'utilisateur

**Mesure** — 3 endroits qui peuvent afficher une erreur brute

**Le problème** — le message d'exception peut finir à l'écran

**Ce que l'utilisateur ressent** — l'utilisateur voit `KeyError: 'hole_id'` et n'a aucune action possible

**Ce qu'on fait** — filet unique : une erreur imprévue devient « DrillMaster n'a pas pu terminer cette action » + 3 sorties + le détail copiable

### F-01 · Le même réglage existe dans plusieurs écrans

**Mesure** — « etiquette » réglable dans 6 endroits de 4 fichiers

**Le problème** — le même réglage a plusieurs propriétaires

**Ce que l'utilisateur ressent** — changer la largeur dans la coupe ne change pas la largeur dans la 3D : l'utilisateur règle deux fois et croit que le logiciel est cassé

**Ce qu'on fait** — un objet de piste unique, cinq lecteurs ; les vues n'affichent qu'un miroir en lecture seule (R-09)

### F-01 · Le même réglage existe dans plusieurs écrans

**Mesure** — « largeur » réglable dans 12 endroits de 5 fichiers

**Le problème** — le même réglage a plusieurs propriétaires

**Ce que l'utilisateur ressent** — changer la largeur dans la coupe ne change pas la largeur dans la 3D : l'utilisateur règle deux fois et croit que le logiciel est cassé

**Ce qu'on fait** — un objet de piste unique, cinq lecteurs ; les vues n'affichent qu'un miroir en lecture seule (R-09)

### F-01 · Le même réglage existe dans plusieurs écrans

**Mesure** — « opacite » réglable dans 8 endroits de 4 fichiers

**Le problème** — le même réglage a plusieurs propriétaires

**Ce que l'utilisateur ressent** — changer la largeur dans la coupe ne change pas la largeur dans la 3D : l'utilisateur règle deux fois et croit que le logiciel est cassé

**Ce qu'on fait** — un objet de piste unique, cinq lecteurs ; les vues n'affichent qu'un miroir en lecture seule (R-09)

### F-01 · Le même réglage existe dans plusieurs écrans

**Mesure** — « cote » réglable dans 8 endroits de 6 fichiers

**Le problème** — le même réglage a plusieurs propriétaires

**Ce que l'utilisateur ressent** — changer la largeur dans la coupe ne change pas la largeur dans la 3D : l'utilisateur règle deux fois et croit que le logiciel est cassé

**Ce qu'on fait** — un objet de piste unique, cinq lecteurs ; les vues n'affichent qu'un miroir en lecture seule (R-09)

---

## Détail par département

### Direction artistique — couleur, typographie, espace, icônes

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| DA-01 | Couleurs écrites en dur au lieu d'un jeton | Majeur | 655 couleurs littérales dans 40 fichiers |
| DA-02 | Tailles de police en dur, échelle typographique absente | Majeur | 9 tailles de police distinctes : 9 pt (49×), 8 pt (37×), 8.5 pt (12×), 7.5 pt (5×), 10 pt (4×), 7 pt (3×), 15 pt (1×), 24 pt (1×), 11 pt (1×) |
| DA-03 | Feuilles de style écrites dans les widgets | Majeur | 320 appels `setStyleSheet` dans 28 fichiers |
| DA-01 | Couleurs écrites en dur au lieu d'un jeton | Mineur | 57 couleurs dans ce seul fichier (ex. #AF7AC5 ligne 29) · `genesis_palettes.py` |
| DA-01 | Couleurs écrites en dur au lieu d'un jeton | Mineur | 53 couleurs dans ce seul fichier (ex. #5D6D7E ligne 54) · `reference.py` |
| DA-01 | Couleurs écrites en dur au lieu d'un jeton | Mineur | 70 couleurs dans ce seul fichier (ex. #1A252F ligne 134) · `section_dock.py` |
| DA-01 | Couleurs écrites en dur au lieu d'un jeton | Mineur | 65 couleurs dans ce seul fichier (ex. #B0B8C0 ligne 179) · `section_export.py` |
| DA-01 | Couleurs écrites en dur au lieu d'un jeton | Mineur | 71 couleurs dans ce seul fichier (ex. #EAFAF1 ligne 226) · `step2_import.py` |
| DA-04 | Marges et espacements improvisés | Mineur | 40 combinaisons de marges/espacements |
| DA-05 | Icônes et symboles textuels mélangés | Mineur | 29 caractères utilisés comme icônes |

### Disposition — rangement, hiérarchie, densité, alignement

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `sample_raster_grid` : 216 lignes · `raster_surface.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `__init__` : 256 lignes · `section_dock.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `_draw_style_identity_track` : 672 lignes · `section_dock.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `_build_assay_group` : 213 lignes · `section_dock.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `_build_threshold_group` : 207 lignes · `section_dock.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `_update_legends` : 218 lignes · `section_dock.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `export_png_dialog` : 183 lignes · `section_export.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `paint_legends_image_impl` : 781 lignes · `section_export.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `paint_locator_map` : 297 lignes · `section_export.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `render_canvas_to_png` : 266 lignes · `section_export.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `sample_raster_along_line` : 286 lignes · `section_surface.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `_build` : 219 lignes · `step2_import.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `step2_validate_all` : 438 lignes · `step2_import.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `__init__` : 239 lignes · `view_3d_canvas.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `draw_floating_legend` : 241 lignes · `view_3d_overlays.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `build_side_panel` : 342 lignes · `view_3d_panel.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `draw_topography_surface` : 181 lignes · `view_3d_renderer.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `draw_drillhole` : 637 lignes · `view_3d_renderer.py` |
| D-01 | Fenêtres construites dans des méthodes géantes | Majeur | `compute_surface_grid` : 186 lignes · `view_3d_surface.py` |
| D-02 | Empilement trop profond | Mineur | imbrication de niveau 11 · `view_3d_canvas.py` |
| D-03 | Blocs sans titre : rien n'est annoncé | Mineur | 4 groupes, 0 avec un titre · `view_3d_panel.py` |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Lithologie » apparaît 26 fois dans 15 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Altérations » apparaît 13 fois dans 8 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Teneurs » apparaît 12 fois dans 9 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « SectionWidget » apparaît 12 fois dans 3 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Structures » apparaît 10 fois dans 6 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Minéralisations » apparaît 10 fois dans 7 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Altération » apparaît 10 fois dans 7 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Récupération » apparaît 9 fois dans 8 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Densité » apparaît 9 fois dans 8 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « Imagerie » apparaît 9 fois dans 5 fichiers |
| D-05 | Libellés dupliqués d'un écran à l'autre | Mineur | « DrillMaster » apparaît 8 fois dans 6 fichiers |

### Réglages et partage — un réglage = un propriétaire ; aucune copie dans une vue

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| F-01 | Le même réglage existe dans plusieurs écrans | Bloquant | « etiquette » réglable dans 6 endroits de 4 fichiers |
| F-01 | Le même réglage existe dans plusieurs écrans | Bloquant | « largeur » réglable dans 12 endroits de 5 fichiers |
| F-01 | Le même réglage existe dans plusieurs écrans | Bloquant | « opacite » réglable dans 8 endroits de 4 fichiers |
| F-01 | Le même réglage existe dans plusieurs écrans | Bloquant | « cote » réglable dans 8 endroits de 6 fichiers |
| F-02 | Champs du contrat reconnus mais non réglables | Majeur | 5 champ(s) sans contrôle éditable : maximum, couleur, motif, etiquette, ordre |
| F-03 | Sous-options mélangées dans les grands réglages | Majeur | 56 champs et 23 cases, aucun groupe titré · `section_dock.py` |
| F-04 | Réglages réinitialisés sans prévenir | Majeur | 108 endroits qui remettent des réglages à zéro |

### Messages et blocages — 5 champs par message : ce qui s'est passé, pourquoi, qui est concerné, comment sortir, où

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| M-05 | L'erreur technique brute atteint l'utilisateur | Bloquant | 3 endroits qui peuvent afficher une erreur brute |
| M-01 | Alertes modales qui bloquent le travail | Majeur | 29 boîtes de dialogue bloquantes dans 8 fichiers |
| M-03 | Jargon technique dans les textes affichés | Majeur | « None » dans 40 texte(s) affichable(s) · `csv_editor.py` |
| M-03 | Jargon technique dans les textes affichés | Majeur | « GeoPackage » dans 6 texte(s) affichable(s) · `main_dock.py` |
| M-03 | Jargon technique dans les textes affichés | Majeur | « CRS » dans 16 texte(s) affichable(s) · `main_dock.py` |
| M-03 | Jargon technique dans les textes affichés | Majeur | « object » dans 2 texte(s) affichable(s) · `section_imagery.py` |
| M-03 | Jargon technique dans les textes affichés | Majeur | « attribute » dans 1 texte(s) affichable(s) · `section_imagery.py` |
| M-03 | Jargon technique dans les textes affichés | Majeur | « EPSG » dans 2 texte(s) affichable(s) · `step1_config.py` |
| M-04 | États absents non annoncés (le silence) | Mineur | 212 mentions d'absence pour 1458 mentions de domaines |
| M-06 | Aucun moyen de copier le détail d'un problème | Mineur | aucune action de copie trouvée |

### Boutons et actions — un bouton = un verbe ; une action destructrice = une confirmation

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| B-02 | Actions destructrices sans confirmation claire | Bloquant | `_on_project_layers_will_be_removed` supprime sans demander confirmation · `main_dock.py` |
| B-02 | Actions destructrices sans confirmation claire | Bloquant | `_remove_generated_layers` supprime sans demander confirmation · `main_dock.py` |
| B-02 | Actions destructrices sans confirmation claire | Bloquant | `_remove_project_group` supprime sans demander confirmation · `main_dock.py` |
| B-02 | Actions destructrices sans confirmation claire | Bloquant | `_delete_current_section` supprime sans demander confirmation · `section_dock.py` |
| B-01 | Boutons sans rôle : tous dessinés pareil | Majeur | 10 boutons, 3 rôles nommés · `step2_import.py` |
| B-03 | Boutons muets : aucun retour après le clic | Majeur | `self.btn_set` n'est relié à aucune action · `view_3d_v2.py` |

### Qualité et dette — tests, duplication, fichiers monolithes, dépendances

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| Q-02 | Fichiers monolithes | Majeur | 2134 lignes dans un seul fichier · `validation.py` |
| Q-02 | Fichiers monolithes | Majeur | 11529 lignes dans un seul fichier · `section_dock.py` |
| Q-02 | Fichiers monolithes | Majeur | 2174 lignes dans un seul fichier · `section_export.py` |
| Q-02 | Fichiers monolithes | Majeur | 2860 lignes dans un seul fichier · `step2_import.py` |
| Q-02 | Fichiers monolithes | Majeur | 2614 lignes dans un seul fichier · `view_3d_renderer.py` |
| Q-05 | Réglages stockés hors du projet | Majeur | 31 usages de QSettings dans 8 fichiers |
| Q-03 | Duplication de code de dessin | Mineur | 5 groupes de fonctions de même forme et même taille |

### Données et vues — une donnée, cinq vues ; aucun calcul dupliqué

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| T-01 | Géométrie recalculée dans les vues | Bloquant | trigonométrie présente dans 8 fichiers de vue (23 lignes) |
| T-02 | Trois moteurs de rendu pour la même 3D | Majeur | 21 fichiers pour la vue 3D : camera3d.py, __init__.py, adapter.py, camera.py, geometry.py, model.py |

### Cohérence et doctrine — un mot = une chose ; une règle = un seul endroit

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| C-01 | Deux mots pour la même chose | Mineur | « coupe » 487 fois et « section » 687 fois |
| C-01 | Deux mots pour la même chose | Mineur | « piste » 208 fois et « track » 109 fois |
| C-01 | Deux mots pour la même chose | Mineur | « teneur » 170 fois et « assay » 413 fois |
| C-01 | Deux mots pour la même chose | Mineur | « forage » 326 fois et « hole » 790 fois |
| C-01 | Deux mots pour la même chose | Mineur | « altération » 103 fois et « alteration » 230 fois |
| C-03 | La doctrine n'est pas vérifiée par la machine | Mineur | un vérificateur existe hors du plugin |

### Navigation et options cachées — tout réglage est atteignable en 1 clic, aucun onglet muet

| Agent | Constat | Gravité | Mesure |
|---|---|---|---|
| N-01 | Réglages enfermés dans une fenêtre qu'on ne peut pas rouvrir | Majeur | `LithologyStructureDialog` enferme 6 réglages dans une fenêtre · `lithology_structure_dialog.py` |
| N-01 | Réglages enfermés dans une fenêtre qu'on ne peut pas rouvrir | Majeur | `ReferenceDialog` enferme 8 réglages dans une fenêtre · `reference_dialog.py` |
| N-02 | Onglets et barres d'onglets masqués | Majeur | 2 barres d'onglets masquées par le code |
| N-04 | Réglages conservés sur le poste, invisibles dans le projet | Majeur | 26 accès à des réglages de poste, 8 clés nommées |
| N-05 | Trop de fichiers d'interface pour un seul produit | Majeur | 39 fichiers d'interface : 3d 11, autres 9, section 9, dialog 6, step 4 |
| N-06 | Aucune aide contextuelle : tout dépend de la documentation | Mineur | 102 infobulles pour 235 contrôles (43 %) |

---

## Ce que la flotte n'a pas vu

Trois limites, dites franchement :

1. **Elle lit des fichiers, pas des pixels.** Un bouton mal aligné ou un
   contraste insuffisant ne se détecte pas dans le code : il faut une capture.
2. **Elle ne connaît pas le métier du géologue.** Elle repère un seuil
   recopié, pas un seuil *faux*. C'est la spec (31 règles) qui tranche.
3. **Elle juge la cohérence, pas le goût.** Le choix « Apple-like » est une
   décision de direction artistique, pas un constat mesurable.

## Ordre d'exécution proposé

1. Les bloquants de **Réglages et partage** et de **Données et vues** : c'est
   là que se trouvent les incohérences que l'utilisateur remarque en premier.
2. **Direction artistique** en un seul passage : thème unique, 6 tailles de
   police, 3 rôles de bouton, grille de 4 px.
3. Les **monolithes** (`section_dock.py`, 11 529 lignes) découpés par
   responsabilité, parce que toute correction d'écran passe par là.
4. Puis les écrans neufs (import, blocage, coupe, exclusions) déjà maquettés.

