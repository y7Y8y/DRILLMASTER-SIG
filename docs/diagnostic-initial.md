# DrillMaster — diagnostic initial et cadrage de la transformation

**État : prédiagnostic statique, non approuvé pour implémentation.** Base examinée : archive `DrillMaster_v2_9_394.zip`, SHA-256 `15a3dd133feb3efcc7fe29e13c59ecddc206c6825484192cbf8337de248efc9d`, métadonnées version 2.9.394, QGIS 3.28–3.99. Le dépôt ne contient que cette archive et un README minimal. Les chemins ci-dessous sont relatifs au répertoire `DrillMaster/` **dans l'archive**. Le propriétaire a confirmé que cette archive installable via le gestionnaire d'extensions QGIS est la dernière version et constitue la référence appelée « V1 » dans la mission.

## 1. Méthode et limites

L'archive a été extraite temporairement pour examiner son arborescence, ses points d'entrée, des interfaces, la validation et des métriques syntaxiques Python (AST). Recherche documentaire ciblée : références en fin de document. Aucun code du plugin n'a été modifié. Il ne s'agit pas encore d'un audit exhaustif : absence de QGIS et du module Python `qgis` dans cet environnement, donc aucune interface réelle, interaction, sortie géologique, performance ou compatibilité QGIS n'a été vérifiée. Les constats de code ne prouvent ni un défaut ressenti ni la correction scientifique. Il n'y a pas eu de sous-agents : les « départements » ci-dessous structurent les responsabilités, pas des interventions réalisées par des personnes distinctes.

Les hypothèses sont indiquées comme telles ; elles doivent être confirmées par inspection dynamique et par un géologue. Ne pas lancer de refonte avant validation de la référence, de la couverture et des critères de sortie de la phase 0.

## 2. Cartographie initiale du produit

| Domaine / parcours | Points de départ dans l'archive | Ce que le code indique / contrôle à compléter |
|---|---|---|
| Intégration QGIS | `__init__.py`, `drillmaster.py`, `metadata.txt` | Action, cycle de vie et docks ; tester activation, désactivation et rechargement. Aucun fournisseur Processing déclaré. |
| Projet et assistant | `ui/main_dock.py`, `ui/stepper.py`, `ui/step1_config.py`, `core/project.py`, `core/workspace.py` | Assistant à quatre étapes, menu projet, fermeture et réinitialisation. Vérifier reprise et protection des fichiers. |
| Import et qualité | `ui/step2_import.py`, `ui/csv_editor.py`, `core/csv_parser.py`, `core/import_detect.py`, `core/validation.py` | Onze familles : collets, déviations, lithologie, teneurs, altérations, minéralisations, structures, imagerie, RQD, récupération, densité. Vérifier correspondance des colonnes, corrections et intégrité des sources. |
| Géométrie | `ui/step3_geometry.py`, `core/geometry.py`, `core/crs_math.py`, `core/layers.py` | Calcul de trajectoires et création de couches ; tâche `QgsTask`, progression et annulation dans le code. Vérifier résultats et annulation de bout en bout. |
| Coupes | `ui/step4_section.py`, `ui/section_dock.py`, `core/section.py`, `core/section_scale.py` | Création, affichage et échelles ; vérifier projection, unités, exagération et persistance. |
| Contenu des coupes | `ui/section_holes.py`, `section_geotech.py`, `section_structure.py`, `section_imagery.py`, `section_surface.py`, `core/track_layout.py`, `core/threshold_rule.py` | Forages, pistes, géotechnique, structures, médias, surfaces et seuils. Examiner chaque groupe en situation. |
| Export | `ui/section_export.py`, `ui/section_export_scaled.py` | Plusieurs chemins de rendu/export, dont export à l'échelle ; comparer contenu, légendes et mesures imprimées. |
| Visualisation 3D | `ui/visualization_dock.py`, `ui/view_3d.py`, `ui/view_3d_v2.py`, `ui/view_3d_canvas.py`, `ui/view_3d_renderer.py`, `core/scene3d/` | Deux ensembles de vue coexistent ; déterminer précisément activation, couverture et rôle avant toute consolidation. |
| Référentiel et styles | `ui/reference_dialog.py`, `ui/display_profiles_dialog.py`, `ui/domain_structure_dialog.py`, `ui/lithology_structure_dialog.py`, `core/reference.py`, `core/display_profiles.py`, `core/style_resolver.py`, `palettes/`, `bibliotheques/` | Libellés, symboles, organisation et profils ; vérifier portée projet/utilisateur et conservation des identités. |
| Analyse et surfaces | `ui/structure_analysis_dialog.py`, `core/structure_analysis.py`, `ui/raster_surface.py`, `core/topography.py` | Analyse structurale et surfaces ; confirmer conventions d'orientation, limites, précision et usages. |
| Transversal | `ui/styles_qt.py`, `core/i18n.py`, `core/diagnostics.py`, `core/ui_audit.py`, `i18n/` | Styles et traductions, diagnostic, préférences ; vérifier langues, focus, thèmes, erreurs et journalisation. |

### Registre de couverture UI à compléter dans QGIS

Toutes les surfaces identifiées ci-dessous restent **à observer** : assistant et menu projet ; configuration ; import, onglets de familles, panneau de validation et éditeur CSV ; géométrisation ; sélection de coupe sur carte ; panneau et canevas de coupe, réglages des forages, pistes, géotechnique, structures, imagerie et surface ; dialogues d'export et aperçu ; dock de visualisation et vues 3D, panneau latéral, interactions, overlays, choix de teneurs, visualiseur d'images et surface ; référentiel, sélecteur de couleur, organisation de domaine et lithologie, profils d'affichage ; analyse structurale ; raster ; démarrage et À propos. Les fonctions qui créent des `QDialog` directement doivent aussi être inventoriées, pas seulement les classes nommées.

Pour chacune : chemin d'accès, capture, taille minimale réelle, données utilisées, contrôles essentiels/avancés, navigation clavier et focus, DPI/zoom, thème clair/sombre, langue FR/EN, états vide/chargement/erreur, persistance et actions destructives. Statut à consigner : non observé, observé, validé ou anomalie, avec scénario et preuve. Aucun statut « validé » à ce stade.

## 3. Constats et risques priorisés

| ID | Constat vérifiable | Risque / suite, pas un défaut confirmé |
|---|---|---|
| A1 | Analyse AST : 105 fichiers Python, 56 577 lignes ; `ui/section_dock.py` compte 11 529 lignes. Les classes `SectionCanvas` et `SectionWidget` occupent respectivement 5 041 et 5 296 lignes. | P1 : forte concentration de responsabilités et risque de régression ; cartographier dépendances et contrats avant extraction. La taille ne mesure pas à elle seule la complexité. |
| A2 | Plus longues fonctions identifiées : `paint_legends_image_impl` 782 lignes (`ui/section_export.py:493`), `_draw_style_identity_track` 673 (`ui/section_dock.py:3930`), `draw_drillhole` 638 (`ui/view_3d_renderer.py:1829`), `validate_intervals` 520 (`core/validation.py:1555`), `step2_validate_all` 439 (`ui/step2_import.py:2353`). | P1 : caractériser comportements avant séparation rendu, orchestration et règles ; ne pas refactorer sur la seule métrique. |
| A3 | `ui/styles_qt.py` centralise déjà palette et styles ; `ui/main_dock.py` applique aussi des styles locaux. `CollapsibleGroup` existe dans `ui/section_dock.py:994`. | P2 : inventorier usages, variantes et contrastes avant de mutualiser ; conserver les composants existants qui répondent au besoin. |
| A4 | `ui/styles_qt.py` contient des règles `outline: none` et `suppress_button_focus_rects`, appelé par `ui/main_dock.py`. | P1 accessibilité : risque de focus clavier peu visible, à vérifier sur OS et thèmes réels ; ne pas conclure que tous les indicateurs sont absents sans test. |
| A5 | `ValidationIssue` (`core/validation.py:26`) possède sévérité, code, localisation et suggestion ; validations par famille et inter-familles existent. | Atout à préserver ; auditer couverture, présentation et traçabilité, plutôt que reconstruire une validation parallèle. |
| A6 | `GeometrisationTask` vérifie l'annulation et la progression ; en absence de déviation, elle appelle `auto_survey_for_vertical` (`ui/step3_geometry.py:21`). | P1 scientifique : rendre l'hypothèse verticale explicite et vérifier sa provenance, son acceptation et ses conséquences ; ne pas modifier la convention sans validation métier. |
| A7 | Langue, réouverture et options 3D utilisent déjà `QSettings` ; des paramètres de projet existent également. | P2 : inventorier portée, priorité, migration et données sensibles ; ne pas écraser les choix existants. |
| A8 | `tools/test_common_scale.py` utilise `/home/claude/dm/...` ; lancé depuis l'archive extraite ici, il échoue à l'import de `section_scale`. L'archive contient aussi d'autres scripts de test/benchmark dans `tools/`. | P1 : rendre la suite reproductible et évaluer chaque script ; cet échec n'établit pas une erreur d'échelle et ne signifie pas absence de tests. |
| A9 | Deux implémentations 3D et plusieurs chemins d'export sont présents. | P2 : hypothèse de duplication ou coexistence intentionnelle ; tracer les appels, les différences et les configurations avant décision. |
| A10 | Métadonnées déclarent QGIS 3.28–3.99 ; présence de traductions FR/EN. | P1 : revendications à tester sur versions et systèmes représentatifs, y compris chargement des traductions ; elles ne sont pas prouvées par les métadonnées. |
| A11 | `ui/step1_config.py:70` propose EPSG:32630 par défaut ; la validation rejette les SCR géographiques (`:245`). | Pour le jeu fictif zone 29N, sélectionner EPSG:32629 explicitement. Vérifier l'information de l'utilisateur et les unités des autres SCR projetés ; le rejet des coordonnées géographiques ne garantit pas à lui seul l'emploi de mètres. |
| A12 | `ui/visualization_dock.py:25,158,326` utilise `View3DV2`, activée par défaut sauf variable d'environnement ; son implémentation importe NumPy. | La coexistence de l'ancienne vue n'implique pas qu'elle soit active. Vérifier les chemins d'appel restants, les dépendances et la fermeture pendant un calcul avant retrait éventuel. |
| A13 | Quatre scripts de `tools/` contiennent des chemins absolus `/home/claude/` (`test_common_scale.py`, `test_default_scale.py`, `test_elev_window.py`, `test_window_room.py`). | Leur exécution ne peut être considérée comme portable en l'état ; inventorier aussi les dépendances et assertions des autres scripts. |

## 4. Revue géologique et fonctionnelle à mener

Pour chaque famille, documenter entrées obligatoires/facultatives, unités, système de coordonnées, conventions et hypothèses, données manquantes, comportement sur doublons, erreurs et avertissements, sortie, provenance et impact aval. Cas prioritaires à construire avec un expert : identifiants inconnus ou dupliqués ; profondeur négative, intervalles inversés, chevauchants, lacunaires ou hors trou ; déviations manquantes ou incohérentes ; ambiguïtés d'azimut/inclinaison et unités ; transformations CRS ; teneurs sous limite de détection sans substitution implicite ; RQD/récupération/densité et unités ; imagerie manquante ; intersection et échelles des coupes. Ces cas sont des **questions à tester**, non des erreurs constatées dans DrillMaster.

Pour les calculs sensibles : jeu synthétique petit avec résultats calculés indépendamment, tolérances et unités explicites, cas limites et validation d'un géologue ; compléter par un jeu réel anonymisé autorisé. Tracer les hypothèses et transformations sans jamais modifier silencieusement les données sources. Comparer écran/export et données générées, pas uniquement des captures. Ne pas promettre une fiabilité scientifique sans ces vérifications.

## 5. Cible UX et identité — proposition à valider

- **Identité** : chrome neutre cohérent avec la palette existante, couleur en priorité pour les données géologiques et états, jamais comme unique porteur de sens. Respecter thèmes et conventions QGIS ; éviter de transformer la carte en décor.
- **Typographie et rythme** : police système et échelle relative, titres, sous-titres et texte secondaire distincts ; grille d'espacement proposée 4/8/12/16/24, sans dimensions fixes bloquant la traduction ou le DPI. Tester avec les réglages système.
- **Composants** : boutons natifs et rôles cohérents, groupes repliables accessibles au clavier, champs avec unité et aide contextuelle, validation à proximité du champ et résumé navigable, progression/annulation et états vides explicites. Toute action destructive indique portée et récupération possible.
- **Divulgation progressive** : afficher les entrées requises et résultats d'abord ; placer les paramètres rares sous « Options avancées » lorsqu'ils ont été identifiés par observation. Un assistant pour les décisions réellement complexes, pas trois modes artificiels pour chaque écran. Un réglage masqué actif doit rester identifiable.
- **Accessibilité** : focus visible, ordre de tabulation logique, noms accessibles, absence de dépendance à la couleur, contraste vérifié, zoom/DPI et traduction testés. Ne pas supprimer les fonctionnalités pour alléger l'écran.
- **Persistance** : distinguer préférences locales, paramètres projet et valeurs propres à une opération ; migration et bouton de restauration explicites. Ne jamais mémoriser aveuglément des chemins ou choix sensibles.

Ces règles sont une direction initiale, pas une maquette validée. Construire une bibliothèque de spécimens Qt/QGIS et tester les parcours avec débutants et experts avant adoption.

## 6. Architecture cible et mutualisation proposée

Schéma de dépendances visé : **interfaces Qt/QGIS → orchestration de cas d'usage → domaine et calculs** ; adaptateurs en périphérie pour fichiers, QGIS, stockage, rendu et tâches. Les objets métier et résultats structurés ne doivent pas dépendre des widgets ; les adaptateurs traduisent les erreurs en messages actionnables. La persistance distingue clairement les trois portées ci-dessus. Les traitements longs définissent progression, annulation, sécurité des threads et publication des résultats.

Candidats à étudier : contrat de validation existant ; sélection et mapping de colonnes ; unités et CRS ; préférences et profils ; sections repliables ; messages et progression ; modèles de pistes/légendes partagés entre écran et export ; géométrie et projections communes 2D/3D. Chaque extraction exige inventaire des usages, différences, tests de caractérisation et migration compatible. Les variations de domaine (géotechnique, teneurs, lithologie, structures) restent explicites ; ne pas unifier les règles scientifiques par simple ressemblance des contrôles. Maintenir formats, API et projets existants jusqu'à définition d'un plan de migration réversible.

## 7. Gouvernance et feuille de route

| Lot / responsabilité | Livrables et dépendances | Critère de passage |
|---|---|---|
| 0 — supervision, audit code et qualité | Confirmer archive et environnement ; inventaire complet des fonctions, fenêtres et dépendances, jeu de données et scripts reproductibles ; mesurer couverture réelle. | Référence V1, périmètre et environnement validés ; registre de couverture sans surfaces oubliées. |
| 1 — UX, ergonomie et métier | Observer tous les écrans, workflows débutant/expert, audit clavier/DPI/langue ; valider conventions scientifiques et catalogue de problèmes. | Chaque constat a scénario, preuve, gravité et responsable ; hypothèses restantes identifiées. |
| 2 — architecture et design | Définir contrats, inventaire de mutualisation, maquettes, composants et décisions (ADR), risques et migration. | Revue croisée géologue/UX/technique, approbation des choix et critères de non-régression. |
| 3 — qualité puis socle | Tests de caractérisation, CI QGIS, jeux de référence, conventions ; rendre les tests existants portables avant de restructurer. | Suite reproductible et référence enregistrée ; cycle chargement/déchargement et chemins critiques couverts. |
| 4 — lots métier progressifs | Un parcours vertical à la fois, par exemple import/validation, puis géométrie, coupes/export et 3D ; découpage final selon audit. | Démonstration, revue métier et accessibilité, comparaison avec référence, documentation et retour arrière par lot. |
| 5 — stabilisation | Tests de performance, compatibilité et migration ; documentation et notes de version. | Seuils convenus respectés sur environnements cibles ; anomalies bloquantes levées ou arbitrées. |

P0 = perte/corruption de données ou résultat scientifique dangereux confirmé ; P1 = risque important de fiabilité, accessibilité ou testabilité ; P2 = amélioration après caractérisation. Les priorités ci-dessus sont provisoires, sans délais inventés. Supervision centrale : journal des décisions, arbitrages, dépendances, anomalies et points de contrôle ; aucune modification fonctionnelle sans validation des lots précédents.

## 8. Plan de non-régression et mesures

1. Installer l'archive de référence dans un profil QGIS isolé ; noter OS, version QGIS/Qt/Python, langue, DPI, thème et dépendances. Tester au minimum la version minimale déclarée et une version cible maintenue, sous les plateformes convenues ; la plage entière ne sera pas certifiée par deux tests.
2. Capturer les parcours : création/ouverture/fermeture, import des 11 familles, erreurs et corrections, génération/annulation, coupe, 3D, référentiel/profils, sauvegarde/réouverture et export. Vérifier aussi absence de projet, fichiers manquants et annulation.
3. Ajouter tests unitaires pour parseurs, validation, calculs et règles ; tests d'intégration QGIS pour couches, fichiers, cycle de vie et tâches ; tests UI pour clavier et états. Comparer sorties métier, géométries et métadonnées avec tolérances justifiées ; comparer images avec tolérance adaptée à la plateforme et inspection humaine.
4. Tester réouverture de projets historiques et absence d'écriture inattendue des sources, erreurs d'E/S, interruptions et retour arrière. Mesurer temps d'import, génération, interaction et export sur tailles de données fixes ; convenir de budgets après mesure de la référence, avec matériel et méthode consignés.
5. Chaque lot doit avoir résultats automatiques, checklist manuelle, limites connues, approbation métier et possibilité de retour arrière. Aucun test ci-dessus n'est déclaré réussi ici.

## 9. Recherche et benchmark initial

- [QGIS Human Interface Guidelines](https://docs.qgis.org/3.44/en/docs/developers_guide/hig.html) : boutons standards, prévention des actions nuisibles, langage clair, listes défilantes et cohérence ; cadrage à adapter aux versions supportées et aux docks, pas règles de pixels appliquées aveuglément.
- [QGIS — publication d'un plugin](https://plugins.qgis.org/publish/) : documentation minimale, dépendances, exemples de données, compatibilité et métadonnées ; vérifier les règles actualisées au moment d'une publication.
- [Qt — principes UI et accessibilité](https://doc.qt.io/agentictools/skills/qt-ui-design/) : divulgation progressive, clavier, contraste et indépendance de la couleur. À confronter aux usages Qt/QGIS réels.
- [Esri — accessibilité Qt](https://developers.arcgis.com/qt/reference/accessibility/) : noms accessibles, ordre de navigation, focus et adaptation de police ; référence de pratiques, pas preuve de conformité de DrillMaster.
- [Seequent — validation de modèle](https://www.seequent.com/technical-tuesday-validating-your-geological-model-with-leapfrog/) : regroupement des erreurs de forage et validation visuelle ; inspiration pour relier problèmes, lignes et visualisation, sans présumer des capacités actuelles.
- [Seequent — plusieurs jeux de forage](https://www.seequent.com/import-multiple-drillhole-borehole-and-well-data-sets-into-your-leapfrog-project/) : valider des jeux distincts avant leur intégration ; piste pour préserver la provenance et éviter des recalculs inutiles, à évaluer selon le modèle de DrillMaster.

Ce benchmark documentaire n'est ni une comparaison pratique des produits ni une revue exhaustive du secteur. Ajouter notamment QGIS natif et d'autres outils pertinents après définition de scénarios comparables, versions, critères, limites et conditions d'accès.

## 10. Décisions requises pour continuer

1. Référence confirmée par le propriétaire : l'archive installable 2.9.394 est la V1. Fournir le dépôt source complet s'il existe séparément.
2. Fournir un environnement QGIS représentatif et, si possible, un projet et des données anonymisés autorisés, avec résultats attendus et conventions géologiques.
3. Identifier les plateformes, langues, utilisateurs et parcours critiques prioritaires ainsi que l'interlocuteur métier habilité à valider les calculs.
4. Valider ce cadrage, puis compléter les observations réelles et les tests avant toute implémentation.
