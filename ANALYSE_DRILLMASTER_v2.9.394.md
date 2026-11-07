# DRILL MASTER — Analyse complète du code (v2.9.394)

> Lecture intégrale de `DrillMaster_v2_9_394.zip` — 115 fichiers, **~56 600 lignes de Python**, 3,1 Mo.
> Aucune ligne de code n'a été modifiée. Les sources décompressées sont dans `DrillMaster/`.
> Tous les modules Python compilent (`python -m compileall` → 0 erreur de syntaxe).

---

## 1. Ce qu'est le projet

**DrillMaster** est une **extension QGIS** (dépôt `y7Y8y/DrillMaster`) de **modélisation et visualisation de forages miniers / géotechniques**.

| | |
|---|---|
| Nature | Plugin QGIS Python (PyQGIS), GPL-2.0 |
| Auteur | Yann BONFUL |
| Version | 2.9.394 (lue depuis `metadata.txt`, jamais en dur) |
| QGIS | minimum 3.28 → maximum 3.99 |
| Langue source | **français** (traductions EN fournies) |
| Dépendance externe | `numpy` uniquement (moteur 3D v2) — tout le reste = stdlib + PyQGIS |
| Point d'entrée | `__init__.py` → `classFactory(iface)` → `drillmaster.DrillMasterPlugin` |

Ce n'est pas une app web : c'est un **plugin lourd de bureau**, greffé dans QGIS, avec deux docks (un contrôleur compact à droite + un grand atelier de visualisation en haut), un assistant en 4 étapes, une coupe 2D vectorielle très riche, une vue 3D logicielle, et une persistance de projet en GeoPackage + JSON.

---

## 2. Volumétrie réelle

```
ui/   : 36 184 lignes  (13 fichiers > 500 lignes)
core/ : 19 693 lignes  (dont core/scene3d/ ~2 000)
racine:    435 lignes  (drillmaster.py 413 + __init__.py 22)
```

Top 12 des fichiers :

| Lignes | Fichier | Rôle |
|---:|---|---|
| **11 530** | `ui/section_dock.py` | **Le monolithe** : 2 classes = `SectionCanvas` (122 méthodes) + `SectionWidget` (172 méthodes) |
| 2 861 | `ui/step2_import.py` | Étape 2 : import, onglets, détection, validation, éditeur CSV |
| 2 615 | `ui/view_3d_renderer.py` | Ancien renderer 3D (**legacy, non branché**) |
| 2 175 | `ui/section_export.py` | Export PNG/SVG de la coupe + cartouche + mini-carte |
| 2 135 | `core/validation.py` | Validation métier de tous les domaines |
| 1 524 | `ui/view_3d_canvas.py` | Ancien canvas 3D (**legacy**) |
| 1 458 | `ui/main_dock.py` | Dock contrôleur, orchestration, projet, couches QGIS |
| 1 144 | `core/project.py` | Projet : dossiers, `config.json`, référentiel, sections |
| 1 133 | `ui/reference_dialog.py` | Référentiel du projet (libellés/couleurs/motifs) |
| 1 048 | `core/section.py` | Projection 2D, Jenks, rampes de couleurs |

**Constat n°1 : le ratio UI/core est de 65/35, et un seul fichier pèse 20 % du projet.**

---

## 3. Architecture

```
DrillMaster/
├── __init__.py          classFactory(iface) — point d'entrée QGIS
├── drillmaster.py       Cycle de vie du plugin (initGui/unload), 2 docks, splash, layout
├── metadata.txt         Manifeste QGIS
├── icon.png / LICENSE   GPL-2.0
│
├── core/                MÉTIER — très majoritairement sans Qt (testable hors QGIS)
│   ├── data_model.py         Collar / Survey / Interval / Structure / Geotech / CoreImage / DrillHole
│   ├── csv_parser.py         Détection encodage, séparateur, décimale + matching flou Levenshtein
│   ├── import_detect.py      Reconnaissance du TYPE de fichier par signature d'en-têtes (12 types)
│   ├── validation.py         Validation par domaine + contrôles croisés (RQD vs récupération…)
│   ├── validation_groups.py  Groupement des erreurs (1 type = 1 ligne + compte exact)
│   ├── geometry.py           Trajectoires 3D par angle moyen (dip/azimut signés)
│   ├── section.py            Projection sur plan de coupe, Jenks, rampes, style litho
│   ├── section_scale.py      Échelle commune de projet (1:N) — 1 mm papier = N/1000 m
│   ├── topography.py         Ligne de sol : MNT → CSV → collets, ancrage, lissage, isocontours
│   ├── project.py            Dossiers projet, config.json, registre de données, sections
│   ├── data_registry.py      Catalogue des sources + profils de structure d'import
│   ├── reference.py          RÉFÉRENTIEL : domaines, couleurs, motifs, clamps pastel/vif
│   ├── style_resolver.py     Source unique couleur/libellé/code court
│   ├── layers.py             Création des couches mémoire QGIS + écriture GeoPackage
│   ├── styles.py             Styles QGIS (catégorisés, motifs, tiretés)
│   ├── threshold_rule.py     Règles de seuil teneurs (jusqu'à 3 règles, clauses ET, filtre litho)
│   ├── multi_assay.py        Jusqu'à 3 éléments de teneurs côte à côte sur la même piste
│   ├── track_layout.py       Positions/largeurs des pistes de la coupe (source unique)
│   ├── track_bands.py        Bandes d'intervalles multi-phénomènes (proportions)
│   ├── geotech.py            RQD / récupération / densité — rampes et règles
│   ├── structure_analysis.py Rose des directions, projection de Schmidt, densité de pôles
│   ├── structure_classify.py Famille d'une mesure (planar / linear / composite / non-orientable)
│   ├── taxonomy                 3 bibliothèques : lithologie (30 familles), altération (27), minéraux
│   ├── genesis_palettes.py   Palettes OKLCH (litho vif / altéro pastel, ΔE2000)
│   ├── i18n.py               QTranslator custom lisant les .ts SANS lrelease
│   ├── diagnostics.py        Journal des exceptions avalées + timings (>250 ms → WARNING)
│   ├── display_profiles.py   Types d'ouvrage RC/DD, AUGER, PUITS, CUSTOM (z d'affichage monotone)
│   ├── workspace.py          État observable partagé carte / coupe / 3D
│   ├── spatial_model.py      Autorité spatiale (requêtes 3D, bounds, sélections)
│   ├── selection_model.py    Sélection unifiée (IntervalSelection / EntitySelection)
│   ├── geometry_cache.py     Cache JSON des trajectoires (indépendant de QGIS)
│   ├── crs_math.py           Repli WGS84 ↔ UTM si la transformation QGIS échoue
│   ├── component_caps.py     Plafonds d'organisation par domaine
│   ├── family_status.py      Badge ⚠ générique par famille de données
│   ├── image_paths.py        Résolution des chemins d'imagerie
│   └── scene3d/              NOUVEAU MOTEUR 3D (numpy pur, sans Qt)
│       ├── model.py          HoleTable / IntervalTable / SceneModel
│       ├── geometry.py       Trajectoires vectorisées, SegmentBuffer, index spatial, LOD
│       ├── camera.py         Caméra orbitale + projection perspective
│       ├── render.py         Rastériseur logiciel numpy (image RGBA)
│       ├── adapter.py        DrillHole → SceneModel (point de partage coupe/3D)
│       ├── zones.py          Détection auto des zones (campagnes/prospects)
│       ├── synthetic.py      Mine fictive 600 → 50 000 trous (benchmark)
│       └── render/tests
│
├── ui/                  QT — docks, dialogues, canvas, exports
│   ├── main_dock.py          Dock contrôleur : stepper 4 étapes, orchestration, couches
│   ├── visualization_dock.py Dock atelier : onglets Coupe 2D / Vue 3D + barre de contexte
│   ├── step1_config.py       Projet : nom, dossier, CRS, unités, pas d'échantillonnage, langue
│   ├── step2_import.py       Import : 11 onglets, glisser-déposer, pastilles de statut
│   ├── step3_geometry.py     Génération des trajectoires (QgsTask, annulable)
│   ├── step4_section.py      Tracé de la ligne de coupe sur la carte (QgsMapTool)
│   ├── section_dock.py       Coupe 2D + panneau Propriétés (8 groupes repliables)
│   ├── section_export.py     Export PNG HD / SVG, cartouche, mini-carte
│   ├── section_export_scaled.py  Export A4→A1, échelle fixe 1:N, PDF
│   ├── section_holes/…       Sous-modules de la coupe : trous, structures, géotech, imagerie, surface
│   ├── reference_dialog.py   Référentiel : couleurs, motifs, symboles, auto-assignation
│   ├── structure_analysis_dialog.py  Rose des directions + stéréonet
│   ├── view_3d_v2.py         NOUVELLE vue 3D (moteur scene3d, thread de build)
│   ├── view_3d*.py (9 files) ANCIENNE vue 3D QPainter — **legacy, non branchée**
│   ├── csv_editor.py         Éditeur CSV complet (undo/redo, erreurs, sauvegarde sûre)
│   ├── styles_qt.py          Palette et feuilles de style du plugin
│   ├── splash.py / about_dialog.py / stepper.py
│   └── display_profiles_dialog.py, lithology_structure_dialog.py, domain_structure_dialog.py
│
├── i18n/                 drillmaster_en.ts (2 487 messages traduits) / drillmaster_fr.ts (vide = source)
├── bibliotheques/        bibliotheque_lithologie.csv (30 familles), bibliotheque_alteration.csv (27)
├── palettes/             litho_palette.json, alt_palette.json (OKLCH), palette_geologique.html
└── tools/                9 scripts de benchmark / test jetables (chemins /home/claude/…)
```

### Flux de données réel

```
CSV (12 types possibles)
  → import_detect (type auto par en-têtes)  → csv_parser (encodage/séparateur/décimale + fuzzy)
  → validation (par domaine, puis croisée)  → ImportBundle
  → geometry (trajectoires)                 → DrillHole (collet + trajectoire + intervalles)
  → GeoPackage (2 fichiers : geometry + data) + config.json + cache JSON trajectoires
  → layers.py (couches QGIS mémoire→gpkg)   → carte QGIS
  → section.generate_section (projection)   → SectionCanvas (QGraphicsScene)
  → scene3d.scene_from_drillholes           → View3DV2 (image numpy → QImage)
```

Les 4 étapes de l'assistant : **1 Projet → 2 Données → 3 Géométrie 3D → 4 Coupes**.

### Modèle de données

- `CollarRecord`, `SurveyRecord`, `StructureRecord` (mesure ponctuelle), `CoreImageRecord` (intervalle photo), `GeotechRecord`, `LithologyComponent`, `IntervalRecord` (générique : litho **ou** teneur **ou** altération…), `TrajectoryPoint`, `DrillHole` (agrégat).
- Pas de base SQL : la persistance = **`config.json` + 2 GeoPackage** (`drillmaster_geometry.gpkg`, `drillmaster_data.gpkg`) + un **cache JSON** des trajectoires (`geometry_cache.py`, ajouté en 2.9.322 pour éviter de régénérer).
- Projets par défaut dans `~/QGIS/DrillMaster/<nom_projet>/`.

---

## 4. Ce que le plugin sait faire (fonctionnel)

**Import (12 types)** — collets, déviations, lithologie, teneurs, altérations, minéralisations, structures, topographie/MNT, imagerie de trou, RQD, récupération, densité.
Détection automatique du type par signature d'en-têtes pondérée, lecture d'un échantillon seulement (jamais le fichier entier), matching flou des colonnes (Levenshtein + synonymes **appris par le projet**), questions d'organisation bloquantes quand une cellule porte plusieurs codes, éditeur CSV intégré avec surlignage des erreurs et sauvegarde atomique.

**Validation** — par domaine + croisée (RQD > récupération, teneur non numérique, hiérarchie litho, plafonds de composants), messages **groupés** (un type d'erreur = une ligne + compte exact + première localisation), 3 sévérités, translation des messages FR/EN.

**Géologie / référentiel** — 30 familles lithologiques (aplats vifs) et 27 familles d'altération (pastels) avec mots-clés et couleurs issues d'une palette OKLCH espacée en ΔE2000 ; 11 motifs de hachures ; 8 symboles de minéraux ; un **Référentiel de projet** éditable (couleur, motif, libellé, code court) qui **ne réécrit jamais** les données sources. Règle structurante : la couleur = identité, le motif = signal secondaire, la minéralisation = texture neutre (pas de compétition chromatique).

**Coupe 2D** — le cœur du produit. Pistes : profondeur, lithologie, teneurs (jusqu'à 3 éléments côte à côte), intercepts/seuils, altérations, minéralisations, structures, imagerie, géotechnique (3), surface. Échelle commune de projet (1:N) optionnelle, fenêtre d'élévation commune, exagération verticale, ligne de sol (MNT raster QGIS / CSV x;y;z / interpolation collets avec **ancrage exact aux collets** et ligne pointillée quand la source est dégradée), inclusion/exclusion des forages (buffer collet ou trajectoire), légende interactive avec surbrillance croisée, infobulles, édition de texte, exports PNG HD / SVG / A4→A1 / PDF avec cartouche, mini-carte et barre d'échelle.

**Vue 3D** — nouvelle implémentation (`core/scene3d`, numpy) : rastériseur logiciel, caméra orbitale, index spatial + LOD, budget de segments, rendu dans un thread, jusqu'à 50 000 trous en benchmark, motifs tubulaires, badges d'imagerie, légende flottante, gizmo, badge d'exagération.

**Extras** — analyse de structures (rose 16 secteurs, stéréonet de Schmidt, densité de pôles, filtres), profils d'affichage par type d'ouvrage (AUGER/PUITS compressés en profondeur d'affichage), bilingue FR/EN à chaud, splash avec progression réelle, journal de diagnostic, « À propos ».

---

## 5. Qualité du code — ce qui est très bon

1. **Séparation core/ui globalement respectée.** `core/` est majoritairement du Python pur (aucun import Qt) : csv_parser, geometry, section, topography, track_layout, geology, structure_analysis, scene3d sont testables sans QGIS. C'est rare et précieux.
2. **Commentaires d'architecture d'excellente qualité.** Chaque module explique *pourquoi* il existe, ce qu'il garantit, et cite les décisions (« arbitrage écran du 20/08/2026 »). La doctrine produit est écrite dans le code.
3. **Doctrine « données sources intactes » appliquée partout** : suggestions de couleur/famille, mappings, réorganisation → jamais de réécriture du CSV source. Très cohérent.
4. **`diagnostics.log_swallowed()`** : 715 appels — chaque exception avalée laisse une trace dans l'onglet Messages QGIS, avec timings (>250 ms = WARNING). Réponse intelligente au problème « ~250 `except: pass` silencieux ».
5. **i18n sans `lrelease`** : `QTranslator` custom qui lit directement les `.ts`. 2 487 messages traduits, 0 non fini.

## 6. Dettes techniques & risques (par gravité)

### 🔴 Bloquant / structurel

| # | Problème | Détail |
|---|---|---|
| **A1** | **`ui/section_dock.py` = 11 530 lignes, 2 classes, 294 méthodes** | Un seul fichier = 20 % du projet. Le commentaire parle d'un « BUD-160 line budget » mais il est dépassé d'un facteur 70. Toute modification de la coupe = risque de régression sur 300 méthodes. Déjà 5 sous-modules extraits (`section_surface`, `section_holes`, `section_structure`, `section_geotech`, `section_imagery`, `section_export`) — le mouvement est commencé, non terminé. |
| **A2** | **~7 800 lignes de code mort** (`ui/view_3d*.py` ×9, `core/mesh_builder.py`, `core/camera3d.py`, `core/benchmark.py`, `core/ui_audit.py`) | L'ancienne vue 3D QPainter n'est plus importée par personne (seul `view_3d.py` s'auto-référence). `benchmark.py` mesure un pipeline qui n'est plus utilisé. Représente **14 % du code**. Les garder coûte : confusion, faux positifs d'audit, poids du paquet. |
| **A3** | **Import circulaire fragile** | `ui/section_export.py` importe `ui/section_dock.py`, qui importe `section_export` en local (dans les fonctions) pour casser le cycle. Ça marche, mais c'est le signe que la frontière canvas/export est mal placée. |
| **A4** | **Aucun test automatisé réel** | `tools/` contient 9 scripts qui **ne sont pas des tests** : ils codent en dur `/home/claude/dm/DrillMaster/...`, impriment des tableaux et `exec()` du code extrait par AST. Ils ne peuvent pas tourner ailleurs que sur la machine d'origine ni échouer. Aucun `pytest`, aucune CI, aucun `unittest`. Sur 56 k lignes de géométrie et de projection, c'est le risque n°1 pour toute reprise. |

### 🟠 Dette moyenne

| # | Problème | Détail |
|---|---|---|
| **B1** | **377 `except Exception`** | Beaucoup sont journalisés (bien), mais 10 sont totalement nus (`except Exception:`) et certains englobent des blocs métier entiers. Combiné au style « on continue quand même », les bugs silencieux restent possibles côté logique (pas seulement UI). |
| **B2** | **`i18n/drillmaster_fr.ts` = 2 489 messages vides** | Le français est la langue source : le fichier est un squelette sans traduction. Il est livré dans le paquet et ne sert à rien (le code retombe légitimement sur la source). Faux signal pour un traducteur. |
| **B3** | **Trois moteurs de motifs coexistent** | Chemin actif = `_LITHO_BRUSH_PATTERNS` + QBrush Dense* + lignes custom dans `section_dock` ; `core/geo_style.py` et `core/pattern_paint.py` sont marqués DEPRECATED mais toujours importés par `section_dock` (`from ..core.pattern_paint import paint_style`, ligne 1165) ; `pattern_engine` est mentionné mais **absent du paquet**. Confusion garantie pour la prochaine évolution. |
| **B4** | **Deux vues 3D, deux philosophies** | L'ancienne (QPainter, ~7 k lignes) et la nouvelle (numpy, ~2 k lignes) coexistent. Le flag `DRILLMASTER_3D=0` bascule sur « la coupe » (diagnostic), pas sur l'ancienne vue : l'ancienne est donc orpheline mais toujours livrée. |
| **B5** | **Doc de référence externe absente** | Le code cite `docs/PLAN_LANGUE.md`, `docs/DICO_TERMES_FR_EN.md`, `docs/PROPOSITION_EXCLUSION_FORAGES_2D.md`, `docs/AUDIT_V2.7.7.md` et ~46 fichiers citent une « SPEC » — **aucun `docs/`, ni README, ni CHANGELOG dans le ZIP**. Les décisions sont traçables dans les commentaires, pas dans un document vivant. |
| **B6** | **Commentaires d'historique massifs** | 1 263 mentions de version (`v2.9.x`) dans le code, des blocs de 20 lignes décrivant l'historique d'un bug dans `section_dock.py` (les 130 premières lignes = journal de versions). Utile pour comprendre, coûteux pour lire. Le vrai CHANGELOG est éparpillé dans les sources. |
| **B7** | **Pas de `requirements.txt` ni de CI, pas de `setup.py`/`pyproject`** | `numpy` est requis par la 3D v2 mais n'est déclaré nulle part. QGIS l'embarque souvent, mais l'absence de déclaration empêche tout environnement reproductible. |

### 🟡 Détails / finitions

- **C1** — `metadata.txt` dit `qgisMinimumVersion=3.28` mais le code utilise `QgsTask`, `QgsDockWidget`, `QgsProjectionSelectionWidget` et un mix `exec_()` (13×) / `exec()` (1×) : compatible, mais l'absence de `Qgis.QGIS_VERSION_INT` signifie que **rien ne garde les versions**.
- **C2** — Aucun secret, aucune clé API, aucun chemin absolu dans le code livré (les seuls `/home/claude/…` sont dans `tools/`, non utilisé à l'exécution). ✅
- **C3** — `bibliotheques/*.csv` et `palettes/*.json` sont des données métier **embarquées dans le paquet** : modification = nouvelle version du plugin (pas de mise à jour découplée).
- **C4** — `icon.png` + `splash` + `about_dialog` : l'attribution a été ajoutée tardivement (v2.9.272) et le code le dit explicitement.
- **C5** — Le dock de contrôle et l'atelier sont reconstruits (`_rebuild_docks`) à chaque changement de langue : efficace, mais destructeur d'état (sauvegarde/restauration de layout à chaque fois).
- **C6** — `core/scene3d/synthetic.py` évoque un « camp minier ivoirien » avec des hypothèses « à ajuster » — donc le benchmark 50 000 trous est mesuré sur des données fictives, pas sur les données réelles de l'utilisateur.

---

## 7. Synthèse en 10 lignes

1. Le projet est **mature et très spécialisé** : plugin QGIS de forages, v2.9.394, 56 k lignes, écrit par un seul auteur avec une vraie doctrine produit.
2. La **coupe 2D** est le produit ; la 3D est en cours de réécriture (numpy) et l'ancienne est encore livrée.
3. Le **métier est propre** : modèle de données clair, core sans Qt, validation structurée, référentiel non destructif.
4. Le **point de rupture est `section_dock.py`** (11 530 lignes) — tout le reste en dépend.
5. **14 % du code est mort** (ancienne 3D, benchmarks, audit).
6. **0 test automatisé exécutable** : les 9 scripts de `tools/` sont des one-shots liés à `/home/claude`.
7. **0 documentation** dans le paquet, alors que le code cite 5 documents et une SPEC.
8. **i18n quasi complet en EN**, `fr.ts` vide inutile.
9. **Aucun secret, aucun chemin absolu** dans le code livré ; tout compile.
10. La dette n'est pas « du mauvais code », c'est de la **dette d'échelle** : un bon code qui a grossi sans être découpé ni testé.

---

## 8. Ordre de priorité que je recommande (à valider)

| Priorité | Action | Pourquoi |
|---|---|---|
| 1 | **Harnais de test + CI** sur `core/` (pytest, données de référence) avant **toute** modification | Rien ne protège aujourd'hui les 20 k lignes de métier. C'est le prérequis absolu. |
| 2 | **Découper `section_dock.py`** par domaine (canvas / rendu litho / rendu teneurs / panneau) | Débloque toute évolution future de la coupe. |
| 3 | **Supprimer l'ancienne 3D** (`view_3d*.py`, `mesh_builder`, `camera3d`, `benchmark`, `ui_audit`) ou la mettre derrière un flag explicite | −7 800 lignes, −14 % de surface de bug. |
| 4 | **Unifier les motifs** (un seul moteur) et retirer `geo_style` / `pattern_paint` | Supprime trois chemins concurrents. |
| 5 | **`requirements.txt` + CHANGELOG + README** | Rendre le projet reprenable par un tiers. |
| 6 | **Nettoyer `tools/`** (vrais tests) et `i18n/*.fr.ts` | Faux signaux. |

---

*Document généré après lecture complète des 115 fichiers. Sources : `DrillMaster/` (branche `arena/f723b9e1-drillmaster-sig`). Aucune modification fonctionnelle effectuée.*
