# DrillMaster — dossier de spécifications fonctionnelles et techniques

**Version : projet de cahier des charges, 8 novembre 2026. Statut : à examiner, non approuvé pour développement.** Référence V1 : archive `DrillMaster_v2_9_394.zip`, SHA-256 `15a3dd133feb3efcc7fe29e13c59ecddc206c6825484192cbf8337de248efc9d`. Aucune modification de cette archive n'est autorisée dans cette mission.

Ce dossier traduit les choix proposés, **pas des décisions déjà validées**. Les faits V1 et limites de preuve sont documentés dans [diagnostic initial](diagnostic-initial.md), [inventaire statique et interfaces](inventaire-statique.md), [audit et essais](mission-audit-plan.md) et [conception UX/UI](conception-ux-ui.md). QGIS n'a pas été exécuté ici ; les calculs hors QGIS couvrent seulement des cas isolés. Le catalogue couvre les domaines et 36 éléments recensés ; il ne prouve pas que tous les chemins dynamiques ou toutes les fonctions V1 ont été caractérisés. Compléter le registre après inspection réelle **avant de déclarer ce dossier complet ou d'autoriser un lot**.

### Statuts et niveaux de confiance

- **Fait V1** : vérifiable par chemin dans les documents d'audit ; ne signifie pas résultat validé scientifiquement.
- **Proposé** : comportement cible à arbitrer ; une exigence formulée « doit » est une exigence *si la proposition est adoptée*, pas une promesse de la V1.
- **[QGIS]** : nécessite essai dans QGIS ; **[GÉO]** : nécessite validation par un géologue ; **[DÉC]** : décision propriétaire requise ; **[COMPAT]** : projet ou format historique à tester.
- Statut de migration **Conserver / Améliorer / Reconcevoir / Mutualiser** : orientation provisoire, pas autorisation de changement. **Remplacer / Déprécier : aucun décidé.** Les doublons présumés restent en place tant que leur usage n'est pas établi.

## 1. Périmètre produit et catalogue fonctionnel

Contrats transversaux proposés : chaque opération expose son projet, sa source, sa version de données et son état ; ne modifie pas silencieusement les sources ; explicite unités, conventions et hypothèses influant sur les résultats ; restitue les erreurs et une action possible. Les sorties visibles ou enregistrées ne doivent pas être présentées comme à jour si les entrées ont changé. Les identifiants ci-dessous relient modules, interfaces, dépendances et critères.

| ID / module et public | Objectif et fonctionnement attendu [proposé] | Entrées → sorties ; paramètres | Dépendances, contrôles, automatisation et interactions | V1 / orientation |
|---|---|---|---|---|
| F01 Projet — tous | Créer, ouvrir, fermer et réinitialiser avec portée explicite ; reprise sans confusion de projet. | Nom, dossier, SCR, préférences → projet, configuration et état ouvert/fermé ; pas d'échantillonnage. | P01 contexte, P02 configuration ; existence/écriture, SCR valide et adapté ; proposer dernières valeurs sans imposer. Réinitialisation explicite et confirmation ; interagit avec toutes les vues. | `ui/step1_config.py`, `core/project.py`, `main_dock.py` ; **améliorer**, [QGIS][COMPAT]. |
| F02 Import/mapping — débutant, données | Charger et associer les fichiers à leur famille et colonnes, puis confirmer les ambiguïtés avant traitement. | CSV, encodage, séparateur, structure et mapping → `ParseResult`, données et provenance ; convention selon famille. | P03 import, P04 qualité, P02 ; détecter format et mapping avec revue, conserver original ; transmet données à F03–F08. | `csv_parser.py`, `import_detect.py`, `ui/step2_import.py` ; **améliorer/mutualiser**, [QGIS]. |
| F03 Collets et déviations — géologue/données | Lier forages et mesures d'orientation, rendre la convention et les directions de repli explicites. | ID, X/Y/Z, profondeur, azimut/dip → records liés ; SCR, unités et convention. | P04 validation ; vérifier identifiants, profondeur, plages, liens ; suggérer convention sans supposer le sens. Alimentent F09. | `core/validation.py:332,415`, `step2_import.py` ; **améliorer**, [GÉO][QGIS]. |
| F04 Lithologie — géologue | Importer et organiser les intervalles et composants lithologiques sans perdre les codes. | ID, de/à, code, rôles/proportions → intervalles ; profil d'organisation. | P04, P06 référentiel ; vérifier bornes, associations, multiplicités ; suggestions confirmées ; rendu F11/F13. | `validate_lithology`, `lithology_structure_dialog.py` ; **améliorer**, [GÉO]. |
| F05 Teneurs — géochimie/données | Importer mesures numériques par intervalle, sélectionner et représenter éléments. | ID, de/à, colonnes de teneur → intervalles et attributs ; unité, sélection, classes/seuils. | P04, P06 ; reconnaître colonnes avec confirmation, traiter explicitement absences/valeurs spéciales ; F11–F14. | `validation.py:validate_intervals`, `multi_assay.py` ; **améliorer**, [GÉO][QGIS]. |
| F06 Altérations/minéralisations — géologue | Gérer domaines catégoriels et leurs organisations propres. | ID, de/à, codes et attributs → intervalles ; organisation, intensité, symboles. | P04/P06 ; vérifier bornes, structure et multiplicité ; réutiliser le mapping sans fusionner règles ; F11/F13. | `domain_structure_dialog.py`, `track_bands.py` ; **améliorer/mutualiser**, [GÉO]. |
| F07 Structures — géologue avancé | Importer observations et explorer orientations sans inventer une orientation manquante. | ID, profondeur, type, dip/direction ou alpha/bêta → observations, rosace et stéréonet ; filtres et convention. | P04, `structure_analysis.py` ; signaler exclusions et nombres ; F11/F15. Les alpha/bêta seuls ne sont pas orientés par `resolve_orientation` V1. | `ui/structure_analysis_dialog.py` ; **améliorer**, [GÉO][QGIS]. |
| F08 Géotechnique et imagerie — géotechnique/données | Exploiter RQD, récupération, densité et images avec unités et provenance. | Intervalles/valeurs/unités, chemins → résultats validés et pistes / visualiseur. | P04 ; vérifier limites, liens, unités, disponibilité ; comparer RQD/récupération uniquement selon règles validées ; F11/F13. | `core/geotech.py`, `validation.py`, `ui/section_geotech.py`, `section_imagery.py` ; **améliorer**, [GÉO][QGIS]. |
| F09 Géométrisation — tous, expert pour méthodes | Calculer trajectoires, présenter méthode et hypothèses, produire résultat traçable. | Collets, déviations, SCR, méthode et pas → `DrillHole`, trajectoires, état et couches/cache. | P01/P02/P04/P05 ; vérifier entrées, annulation, révision et résultat ; indiquer prolongements et absence de mesures ; F10–F13. | `geometry.py`, `step3_geometry.py`, `geometry_cache.py` ; **conserver/améliorer**, [GÉO][QGIS]. Aucun changement de méthode approuvé. |
| F10 Couches et persistance — tous | Créer et réouvrir couches et projets sans perte de données. | Trajectoires, attributs, SCR, chemins → couches et GeoPackage, cache, état de reprise. | P02/P05 ; contrôler erreurs d'écriture/lecture et verrouillage ; ne jamais annoncer succès partiel comme complet ; F01/F09/F11. | `core/layers.py`, `project.py` ; **conserver/améliorer**, [QGIS][COMPAT]. |
| F11 Coupes et pistes — géologue | Tracer une coupe, choisir corridor, afficher forages, domaines et légendes. | Ligne/corridor, forages, référentiel, style → projection et vue ; échelle, exagération, pistes. | P01/P06 ; contrôler unités/projection, informer sélection hors corridor ; aperçu réversible ; liens F12–F14. | `core/section.py`, `ui/section_dock.py` ; **améliorer/reconcevoir interface**, [GÉO][QGIS]. |
| F12 Surface/topographie — géologue | Consulter et associer un profil ou surface ; expliciter interpolation, ancrage et limites. | Raster/collets, SCR, ligne/emprise → profil/grille ; méthode, lissage, échantillonnage. | P04/P05 ; tester CRS, valeurs manquantes, extrapolation ; aperçu identifié ; F11/F13. | `core/topography.py`, `ui/section_surface.py`, `raster_surface.py` ; **améliorer**, [GÉO][QGIS]. |
| F13 Visualisation 3D — géologue | Explorer données et trajectoires, sélectionner et naviguer sans modifier les calculs. | Forages/trajectoires, domaines et styles → scène ; caméra, visibilité, qualité. | P01/P05/P06 ; protéger contre résultat périmé, expliciter forages exclus ; l'usage effectif du secours divergeant reste à vérifier ; synchronisation avec F11 selon accord. | `visualization_dock.py`, `view_3d_v2.py`, `core/scene3d/` ; **améliorer**, [QGIS][GÉO]. |
| F14 Export — tous | Exporter image ou document à l'échelle avec aperçu et portée explicites. | Vue, format, résolution/échelle et chemin → fichier et résultat d'opération. | P07 export, P06 ; vérifier chemin/écrasement, dimension et unités, rapport d'échec ; image et impression gardent leurs contrats. | `section_export.py`, `section_export_scaled.py` ; **améliorer/mutualiser**, [QGIS]. |
| F15 Analyse structurale — expert | Produire rosace/stéréonet et indiquer échantillons exclus et conventions. | Structures, filtres, projection/classe → graphiques et résumé ; paramètres d'analyse. | F07/P06 ; dénombrer exclusions et tester contre oracle ; pas de conversion d'alpha/bêta implicite. | `core/structure_analysis.py`, `ui/structure_analysis_dialog.py` ; **conserver/améliorer**, [GÉO]. |
| F16 Référentiel et profils — géologue/avancé | Gérer codes, libellés, couleurs et profils sans modifier le code brut. | Catégories, symboles et paramètres de vue → référentiel/profils sauvegardés. | P02/P06 ; contrôler conflits, origine et portée ; suggestion modifiable ; F04–F15. | `core/reference.py`, `display_profiles.py` ; **améliorer/mutualiser**, [COMPAT]. |
| F17 Cycle de vie, langue, aide — tous | Charger/décharger proprement, changer langue, présenter version/licence et état. | QGIS, préférences, métadonnées → actions, docks, aide, logs. | P02/P05/P08 ; vérifier ressources, signalement des erreurs et nettoyage ; conserver conventions QGIS. | `drillmaster.py`, `core/i18n.py`, `ui/about_dialog.py` ; **conserver/améliorer**, [QGIS]. |

Sous-familles à préserver et tester individuellement : collets, déviations, lithologie, teneurs, altérations, minéralisations, structures, imagerie, RQD, récupération, densité. Une cellule du tableau ne vaut pas preuve que tous leurs paramètres V1 ont été identifiés.

## 2. Spécification générale des interfaces

### Contrat commun UI-U1 [proposé]

Toutes les interfaces concernées doivent : (1) afficher contexte et portée de l'action ; (2) présenter les informations essentielles avant options secondaires ; (3) conserver champs/commandes V1 jusqu'à inventaire et décision, y compris si déplacés ; (4) proposer texte et focus accessibles, navigation clavier et mise en page adaptable ; (5) distinguer vide, prêt, en cours, succès, avertissement, erreur, annulé et périmé lorsque ces états sont applicables ; (6) afficher cause, localisation et récupération pour toute erreur connue, et conserver un détail technique consultable ; (7) ne jamais masquer un réglage actif sans résumé ; (8) marquer aperçu et modification non enregistrée ; (9) restaurer ou annuler selon la portée annoncée. Les messages spécifiques ci-dessous sont des exemples cible, pas des textes réellement observés.

### Contrats particuliers par parcours

- **Projet F01** : champs nom, dossier, SCR projeté, unité affichée ; langue et pas restent accessibles. Commandes choisir dossier/SCR, ouvrir, créer, annuler. Nom vide, dossier non accessible ou SCR invalide donnent une erreur près du champ ; une collision n'écrase rien. Changement/fermeture demande décision si des modifications non enregistrées existent. Ne pas présumer qu'un SCR projeté utilise des mètres. [QGIS][DÉC]
- **Import F02–F08** : sélection de fichiers et famille, liste d'états, tableau colonnes source/cible, structure, aperçu, panneau d'anomalies et action vers ligne. Pour les déviations, convention proposée puis confirmée si ambiguë. États fichier absent/chargé/mapping incomplet/validation en cours/anomalies/prêt ; messages par code et contexte. Une correction assistée montre l'avant/après et la cible avant confirmation. [QGIS][GÉO]
- **Trajectoires F09** : résumé nombre de forages, SCR et unités, méthode, pas et nombre d'hypothèses par catégorie ; commande calcul et annulation si prise en charge. États non calculé/en cours/annulé/échec/succès/périmé ; un résultat tardif d'une révision précédente ne s'applique pas. Exemple : « Déviation absente : direction du collet utilisée » ou « direction verticale par défaut utilisée », selon les données effectives. [QGIS][GÉO]
- **Coupe F11/F12** : sélection de ligne, corridor et unité, liste de forages, canevas, pistes/visibilité, échelles et exagération, paramètres de surface et accès export ; sélection et focus accessibles. Cas coupe absente, aucun forage dans corridor, projection invalide ou surface manquante : message indiquant comment vérifier le choix. Les paramètres de vue n'altèrent pas silencieusement le calcul de trajectoire. [QGIS][GÉO]
- **3D F13** : domaine et éléments visibles, canevas, commandes de caméra, sélection, état du modèle, qualité de rendu et options de vue ; affichage des trous ignorés et de toute hypothèse si le chemin est utilisé. Cas absence de trajectoire, chargement et scène obsolète présentés sans masquer un résultat ancien comme s'il était courant. [QGIS][GÉO]
- **Export F14** : choisir image ou sortie à l'échelle, destination, aperçu et propriétés pertinentes ; indiquer unité/résolution/échelle et contenu ; contrôle chemin, écrasement et limites avant écriture. Échec indique destination et raison si connue ; succès uniquement après écriture complète. Les paramètres papier restent distincts des paramètres de vue. [QGIS]
- **Référentiel/profils F16** : domaine, code brut, libellé, symbole et aperçu ; portée et héritage des profils ; recherche et détail. Prévenir conflit de code et perte de modifications non enregistrées. Le style ne réécrit pas le code source. [QGIS][COMPAT]

### Fiches des 36 éléments recensés

La table complète chaque fiche de [conception UX/UI §4](conception-ux-ui.md#4-revue-conceptuelle-des-36-éléments) par son contrat d'interaction. UI-U1 et les contrats de parcours s'appliquent ; les composants internes ne sont pas traités comme des fenêtres autonomes. « Échec » indique l'état ou message à prévoir ; les commandes et champs existants doivent être inventoriés en QGIS avant de figer le détail.

| # Élément | Contenu et contrôles cibles ; commande/interaction | État, validation et échec à prévoir |
|---|---|---|
| 1 `AboutDialog` | Nom, version, licence, liens ; fermer. | Métadonnée absente : texte explicite, lien indisponible. |
| 2 `CsvEditorDialog` | Nom et origine, tableau éditable, recherche, anomalies ; modifier/annuler/enregistrer selon portée. | Erreur localisée ; confirmer modification, gérer fichier inaccessible et conflit de révision. |
| 3 `DisplayProfilesDialog` | Profil, type, propriétés, portée ; sélectionner, prévisualiser, enregistrer/annuler. | Nom ou valeur invalide, doublon ; annuler aperçu sans écraser profil. |
| 4 `DomainStructureDialog` | Exemple de données, structure et choix colonnes ; valider/annuler. | Ambiguïté ou association manquante : garder brouillon et expliquer. |
| 5 `LithologyStructureDialog` | Rôles, colonnes, proportions et aperçu ; confirmer/annuler. | Valeurs ou organisation incohérentes signalées selon règle métier. |
| 6 `MainDock` | Contexte, étape active, menu projet, précédent/suivant. | Étape bloquée : raison accessible ; modifications en attente signalées. |
| 7 `_DomainColorPicker` | Couleur et aperçu ; sélectionner/confirmer/annuler. | Couleur invalide : conserver ancienne valeur et expliquer. |
| 8 `ReferenceDialog` | Domaines, codes bruts, libellés, couleurs et symboles ; recherche, éditer, enregistrer/annuler. | Conflit ou modifications non enregistrées à la fermeture : expliquer et proposer choix. |
| 9 `CollapsibleGroup` | Titre, résumé, contrôle ouvrir/fermer au clavier. | État ouvert/fermé annoncé ; erreur active résumée même repliée. |
| 10 `SectionCanvas` | Vue, axes, forages, sélection, légende ; zoom/sélection. | Pas de coupe/données hors corridor : état vide actionnable ; alternatives clavier à valider. |
| 11 `SectionWidget` | Canevas et groupes données/apparence/analyse ; sélectionner, ajuster, exporter. | Options non applicables désactivées avec raison ; état obsolète signalé. |
| 12 `_LocPreview` | Emprise et aperçu de localisation ; actualisation depuis options. | Aperçu indisponible : raison, sans bloquer silencieusement l'export. |
| 13 `export_png_dialog` | Chemin, contenu, résolution et aperçu ; choisir/exporter/annuler. | Destination invalide ou écrasement : explication et confirmation. |
| 14 `export_scaled_dialog` | Format, échelle, unités, marges, aperçu ; choisir/exporter/annuler. | Échelle/format invalide ou contenu débordant : message et correction. |
| 15 `PluginSplash` | Nom et progression si connue ; pas de saisie. | Chargement long/échec : ne pas laisser un indicateur bloqué sans explication. |
| 16 `Step1Config` | Nom, dossier, SCR, langue et pas ; choisir et poursuivre. | Voir F01 ; unités affichées ; conserver entrées invalides pour correction. |
| 17 `DropZone` | Zone et bouton choisir fichier ; glisser-déposer ou clavier. | Type/chemin non accepté : message avec action alternative. |
| 18 `ImportTab` | Fichier, colonnes, aperçu, organisation et convention pertinente ; association/correction. | Mapping incomplet ou ambigu : état et aide contextuelle. |
| 19 `GroupedValidationPanel` | Gravité, nombre, problème, localisation et filtres ; ouvrir occurrence. | Aucune anomalie ou contrôle non exécuté : distinguer les deux états. |
| 20 `FamilyChip` | Famille, état texte/icône et nombre ; activer par clavier. | État inconnu ou erreur : ne pas représenter comme réussite. |
| 21 `Step2Import` | Familles, résumé, import, panneau qualité ; ajouter/contrôler/corriger. | Voir F02–F08 ; aucun passage automatique malgré ambiguïté scientifique. |
| 22 `Step3Geometry` | Méthode, hypothèses, pas, progression ; calculer/annuler. | Voir F09 ; indiquer cause et résultats partiels éventuels. |
| 23 `SectionMapTool` | Consigne de tracé, ligne et indication de fin ; sélectionner/tracer/annuler. | Tracé invalide ou annulé : ne pas créer une coupe fantôme. |
| 24 `Step4Section` | Nom, ligne, direction, corridor ; vérifier/créer/ouvrir. | Ligne absente ou paramètres invalides : signaler champ et correction. |
| 25 `StepIndicator` | Numéro, nom, état ; accès approprié. | Étape verrouillée : raison accessible ; focus visible. |
| 26 `StepperWidget` | Ordre et étape courante ; revenir à étape autorisée. | Validation non faite : ne pas afficher étape comme terminée. |
| 27 `_StructureRoseWidget` | Graphique, effectif, convention ; sélection et accès textuel. | Aucune observation admissible : expliquer exclusions. |
| 28 `_StructureStereonetWidget` | Projection, effectif, graphique ; sélection et accès textuel. | Données insuffisantes/non orientables : indiquer limites. |
| 29 `StructureAnalysisDialog` | Filtres, rosace, stéréonet, exclusions ; appliquer/fermer. | Paramètre invalide ou absence de résultats : explication et révision des filtres. |
| 30 `View3DWidget` | Contrat de la vue historique **à inventorier si accessible**. | Aucun retrait ou migration avant comparaison des fonctionnalités et réglages. |
| 31 `View3DCanvas` | Contrat du canevas historique **à inventorier si accessible**. | Conserver compatibilité et interactions jusqu'à preuve de remplacement. |
| 32 `_AssayElementDialog` | Liste d'éléments, sélection/ordre et limite de rendu ; confirmer/annuler. | Aucun élément ou limite atteinte : expliquer sans supprimer données. |
| 33 `_ImageryPhotoDialog` | Photo, forage, intervalle et navigation ; ouvrir/fermer. | Fichier manquant/illisible : chemin et résolution proposée sans écraser. |
| 34 `_Viewport` | Scène, orientation, sélection ; orbite/pan/zoom et alternatives à définir. | Chargement/absence de scène : état lisible ; focus conservé. |
| 35 `View3DV2` | Vue, domaines, caméra, filtres et état ; ajuster et sélectionner. | Cas F13 ; travail obsolète ne remplace pas scène récente. |
| 36 `VisualizationDock` | Contexte projet/coupe et onglets 2D/3D ; commandes propres à la vue active. | Projet fermé ou vue indisponible : message et action adaptée, pas de commande à portée ambiguë. |

Des boîtes construites en cours d'exécution sont recensées dans `inventaire-statique.md` ; leur inventaire et leurs spécifications individuelles restent ouverts. Ne pas considérer cette table comme preuve qu'aucune autre fenêtre n'existe.

## 3. Référentiel des composants et contrats

Les noms ci-dessous sont conceptuels, non des API existantes ou définitives. Un contrat doit être testable indépendamment de la présentation lorsque possible.

| ID / composant | Responsabilité et opérations proposées | Entrées → sorties / erreurs et consommateurs |
|---|---|---|
| P01 `ProjectContext` | Identifier projet, révision des données, SCR, coupe et sélection ; notifier un changement effectif. | ID et révision → instantané lisible ; événement avec projet, révision et origine. Abonnements détachés à fermeture. F01/F09/F11/F13 ; ne contient pas de widgets. |
| P02 `Configuration` | Lire/valider paramètres et origine ; résoudre selon politique scientifique ou affichage ; sauvegarde ciblée. | Clé typée + portée → valeur, unité, origine et version ; échec explicite si ambigu/invalide. F01–F17 ; règles détaillées dans `conception-ux-ui.md` §12. |
| P03 `ImportService` | Détecter/lire/matcher, proposer structure et produire données avec provenance ; ne pas enregistrer silencieusement une correction. | Source + mapping confirmé → données/diagnostics ; E/S et format remontés de façon structurée. F02–F08. |
| P04 `QualityEngine` | Exécuter règles génériques, de famille et inter-familles ; produire rapport par révision. | Données + conventions + profil de règles → problèmes codés, localisations et contrôles non exécutés. F02–F09, F15 ; conserver `ValidationIssue` et règles existantes via adaptateurs. |
| P05 `OperationRunner` | Orchestrer calculs longs, progression, annulation et publication du résultat. | Instantané entrées + ID opération → progression et résultat/succès/annulé/échec ; rejeter résultats anciens. F09/F10/F12/F13/F14. |
| P06 `ReferenceAndSelection` | Résoudre styles sans changer codes bruts ; sélectionner objets par ID stable. | Référentiel + code/ID → style ou sélection, origine et absence éventuelle ; F04–F16. Ne pas imposer synchronisation de filtres. |
| P07 `ExportService` | Préparer aperçu et écrire une sortie selon contrat de format ; garantir signalement d'échec. | Instantané de vue + paramètres + destination → fichier et compte rendu ; pas d'écrasement sans confirmation. F14 ; unités écran et papier distinctes. |
| P08 `NotificationsAndDiagnostics` | Présenter événements et erreurs, journaliser contexte utile sans fuite inutile. | Problème/opération → message utilisateur + détail technique accessible ; ne transforme pas une erreur en succès. Tous modules. |
| P09 `History` | Proposition différée : tracer opérations et paramètres effectifs ; distinct de l'annulation. | Événement approuvé + provenance → entrée consultable ; conservation et confidentialité à définir. F01/F02/F09/F14 ; pas de promesse d'undo généralisé. |
| P10 `UIComponents` | Sections repliables, états, formulaires, tableaux qualité, dialogues et barre de contexte selon Design System. | État + actions → composants accessibles, sans logique géologique. Tous modules ; adapter Qt/QGIS et thème. |

## 4. Architecture technique et flux cible

Organisation **illustrative**, à adapter aux frontières déjà présentes après caractérisation, et non plan de déplacement immédiat :

```text
plugin/entry.py                 cycle QGIS, actions et docks
application/                   cas d'usage : projet, import, validation,
                               trajectoires, vues et export ; orchestration
 domain/                       modèles, identités, règles, conventions,
                               géométrie/sections et résultats structurés
adapters/                      QGIS couches/SCR/tâches, CSV, GeoPackage,
                               projet/config, rendu et fichiers
presentation/                  docks, dialogues, contrôleurs, composants Qt
shared/                        erreurs, journalisation et contrats sans UI
```

Ne pas créer un fichier par fonction : les unités réelles seront choisies selon cohésion, utilisations et tests. `core/` et `ui/` V1 possèdent déjà des parties de ces responsabilités ; des adaptateurs doivent préserver leur comportement pendant la transition.

### Dépendances autorisées et événements

- Présentation dépend de contrats applicatifs et adaptateurs Qt/QGIS ; domaine ne dépend ni de widgets, ni de `iface`, ni de `QgsProject` global. Les adaptateurs de données et QGIS implémentent les ports requis par l'application. Les conversions spécifiques QGIS restent à la périphérie.
- Les opérations prennent un instantané et un identifiant projet/révision ; les événements portent type, projet, révision et origine. Les abonnements ont un cycle de vie explicite ; ne pas renvoyer les changements identiques en boucle. L'UI ne publie un résultat que s'il correspond au projet et à la révision actifs.
- Les objets Qt/QGIS attachés au fil principal ne sont pas utilisés directement dans une tâche de fond ; préparer des données appropriées, émettre progression/résultat et appliquer côté UI. Tester annulation et fermeture ; ne pas présumer de sûreté du `QThread` V1.
- Flux nominal : fichier → parsing/mapping confirmé → validation structurée → bundle versionné → calcul avec provenance → couche/cache → sélection/projection → coupe/3D → aperçu/export. Si une étape échoue, conserver les données antérieures, identifier les sorties partielles et ne pas marquer l'opération réussie.
- État et paramètres : voir P01/P02 et [conception §12](conception-ux-ui.md#12-architecture-des-paramètres-c1). Pas de précédence unique permettant à `QSettings` de surcharger une convention scientifique. Les aperçus restent temporaires jusqu'à application explicite.

## 5. Matrice de migration et dépendances

| Lot proposé | F / capacités concernées | Orientation et prérequis | Risques et vérification avant passage |
|---|---|---|---|
| M0 Référence | Toutes | Conserver ZIP, inventorier comportements et formats ; QGIS réel + données ; définir versions cibles et oracles. | Référence incomplète ; captures, fixtures, résultats et contraintes signés. |
| M1 Qualité et contrats | F02–F08, P04/P08 | Mutualiser le contrat de résultats autour de `ValidationIssue` sans changer les règles ; après M0. | Codes, sévérités ou corrections régressent ; comparer chaque famille et projet historique. |
| M2 Configuration et contexte | F01/F16/F17, P01/P02 | Caractériser les clés V1, définir portées, migration réversible ; après M0. | Valeur scientifique changée ou projet illisible ; ouverture et sauvegarde sur copies, tests retour arrière. |
| M3 Trajectoires et persistance | F03/F09/F10, P05 | Stabiliser conventions, tests indépendants, cache et couches avant extraction ; après M0–M2. | Altération géométrique, hypothèse silencieuse, divergence secours 3D ; résultats et géologue requis. |
| M4 Interface import / qualité | F02–F08, P03/P04/P10 | Reconcevoir progressivement l'organisation après M1/M2, sans suppression d'options. | Mappings oubliés ou validation inaccessible ; essais 11 familles et accessibilité. |
| M5 Coupe, surface, export | F11/F12/F14, P06/P07 | Extraire contrats de rendu/échelle après caractérisation ; prévoir unités écran/papier. | Perte de pistes, échelle fausse, styles incohérents ; tests numériques, images et sortie physique. |
| M6 3D et synchronisation | F13, P01/P05/P06 | Tracer les chemins et l'ancienne vue ; après M2/M3. | Résultat périmé, échec de threads ou écart 2D/3D ; essais de cycle et comparaisons. |
| M7 Stabilisation et documentation | Toutes | Compatibilité, performance, migration et revue utilisateur ; après lots retenus. | Faux sentiment de conformité ; matrice d'environnements et limites connues. |

**Ordre non figé** : M4 peut progresser en parallèle de la conception M3 une fois ses contrats M1/M2 validés ; M5 et M6 peuvent être caractérisés séparément mais dépendent d'une trajectoire et d'identités stables avant migration. Aucun lot n'autorise une réécriture globale. Les fonctionnalités de F01–F17 ont toutes une orientation dans le catalogue ; aucun remplacement ou retrait décidé. Pour l'ancienne 3D (`View3DWidget`/`View3DCanvas`), conserver le code et les accès éventuels jusqu'à inventaire dynamique, comparaison, migration et décision explicite.

### Matrice de dépendances

| Élément | Dépend de | Débloque |
|---|---|---|
| Référence QGIS, données et oracles (M0) | environnement, jeu synthétique et expert | Tous les lots et tests scientifiques. |
| Qualité P04 | parsing/provenance P03, règles métier | Import, validation géométrique et rapports. |
| Configuration P02 / contexte P01 | inventaire V1, formats, politique de portée | Calcul traçable, état des vues, migration. |
| Trajectoire F09 | F03, P02/P04/P05, conventions approuvées | F10, F11, F13 et leurs exports. |
| Référentiel P06 | codes bruts et persistance F16 | Cohérence coupe, 3D, légendes et export. |
| Export P07 | coupe/vue stabilisée, unité/échelle, écriture | F14 ; non requis pour valider parsing seul. |
| UI P10 | design validé, Qt/QGIS et contrats métier | Interfaces harmonisées sans changer les règles. |

## 6. Stratégie de tests et critères d'acceptation

### Règles générales

- **Référence** : exécuter V1 et cible sur copies des mêmes projets et jeux, avec versions QGIS/Qt/Python, OS, langue, thème, DPI et chemins consignés. Tester la version minimale déclarée et les versions/plateformes choisies ; une sélection limitée ne certifie pas toute la plage 3.28–3.99.
- **Couches de test** : unitaires hors QGIS pour parseurs, règles, formules, configuration et résolution ; intégration QGIS pour couches/CRS, fichiers et cycle de vie ; parcours UI incluant clavier, focus, taille/zoom, états et traductions ; résultats de calcul par oracle indépendant et examen métier ; performance sur jeux fixés et matériel renseigné.
- **Comparaison** : tolérances numériques définies par grandeur et approuvées par expert, pas de tolérance universelle arbitraire. Images : comparer géométries, texte et métadonnées d'abord, puis captures avec tolérance adaptée à la plateforme ; inspection humaine pour éléments visuels. Les limites de temps/mémoire sont fixées après mesure de la V1 sur jeux et matériel convenus.
- **Sécurité et migration** : copies immuables de sources, annulation, écriture refusée, accès indisponible, panne et rechargement ; conserver sauvegarde de référence et résultat détaillé. Couvrir les projets historiques fournis et documenter ceux non testés.
- Un lot n'est « terminé » que si critères, tests automatiques et manuels, revues UX/métier et compatibilité convenues sont satisfaits ; exceptions enregistrées et acceptées explicitement. Aucune de ces validations n'est déclarée acquise ici.

### Critères objectifs par domaine prioritaire

| ID | Critères d'acceptation [proposés, à valider] |
|---|---|
| A01 Projet / paramètres | Sur une copie de projet V1, ouvrir puis sauvegarder/reouvrir conserve SCR, conventions, mappings, profils et données attendues ; changer langue/disposition ne modifie aucun paramètre scientifique ; annuler une modification non enregistrée la restitue à son état précédent. Vérifier erreurs de dossier et collision sans écrasement. [QGIS][COMPAT] |
| A02 Import / qualité | Les 11 familles de la matrice de référence produisent enregistrements et anomalies attendus ; chaque problème localisable mène à la bonne ligne/colonne ; nombre de problèmes regroupés égale le nombre d'occurrences ; fichiers source inchangés après simple import et correction sur copie. Conventions ambiguës nécessitent confirmation. [QGIS][GÉO] |
| A03 Géométrie | Pour chaque cas de référence validé (droit montant, descendant, horizontal, vertical ; courbe, 359°/1°, station manquante), coordonnées et profondeur concordent avec l'oracle de la méthode déclarée selon tolérance approuvée ; les hypothèses de repli sont présentées fidèlement ; annulation ou changement de révision ne publie pas un résultat ancien. [GÉO][QGIS] |
| A04 Couches et reprise | Les couches créées ont SCR, identifiants, attributs et géométries attendus ; la réouverture sur copie conserve les résultats ; échec d'écriture ou GeoPackage verrouillé produit un diagnostic sans annoncer un succès complet. [QGIS][COMPAT] |
| A05 Coupe / surface | Les forages, intervalles et sélections attendus sont présents pour corridor de référence ; les positions et graduations correspondent à l'oracle et unités convenus ; absence raster et CRS incompatible sont expliqués. Comparer états, styles et captures à la référence V1. [GÉO][QGIS] |
| A06 3D | Pour une trajectoire existante, mêmes coordonnées métier que référence à la tolérance convenue ; cas sans trajectoire et forages montants testés séparément, exclusions signalées ; fermeture/rechargement pendant construction ne publie pas un ancien résultat. La résolution de la divergence G2 requiert décision scientifique préalable. [QGIS][GÉO] |
| A07 Export | Contenu, légende et sélection correspondent aux paramètres annoncés ; la mesure physique de la sortie à l'échelle est correcte selon tolérance d'impression convenue ; écrasement et erreurs d'écriture exigent décision ou produisent un message explicite. [QGIS] |
| A08 Référentiel / structures | Modifier un libellé/style ne modifie pas code brut ; les styles se propagent seulement aux vues prévues ; rosace/stéréonet et exclusions correspondent à un jeu vérifié par expert ; réouverture conserve les valeurs. [GÉO][QGIS][COMPAT] |
| A09 Accessibilité et stabilité | Sur scénarios critiques, commandes accessibles au clavier, focus visible, dialogue fermé avec retour du focus, textes sans troncature à tailles et langues convenues ; activer/désactiver/recharger et fermer pendant une tâche ne provoque ni doublon d'action ni crash. Vérifier thèmes et contrastes réels, pas seulement les tokens. [QGIS] |

## 7. Feuille de route et décisions avant exécution

1. **Observation et référence** : installer/utiliser QGIS 3 dans environnement accessible ; compléter inventaire des dialogues, capturer les parcours et définir données, versions et jeux historiques. Aucun résultat visuel n'est actuellement disponible.
2. **Validation métier** : conventions, cas géologiques et tolérances ; analyser G2 et le message de trajectoire sans supposer l'impact utilisateur.
3. **Arbitrages produit** : confirmer navigation à deux docks, Design System, portées de paramètres et règles de synchronisation ; établir le catalogue définitif des fonctionnalités et réglages V1.
4. **Préparation technique** : approuver contrats, stratégies de tests et migrations ; mesurer performance ; définir les lots selon dépendances et capacité réelle.
5. **Demande d'autorisation distincte** : présenter plan, risques, tests, retour arrière et critères par lot. Ne pas développer avant accord explicite.

Questions bloquantes : accès à un QGIS représentatif et ses versions cibles ; liste complète des fonctions actives et interfaces dynamiques ; jeux réels anonymisés ou validation d'oracles synthétiques ; référent géologue ; tolérances et conventions ; format et projets historiques à migrer ; décision sur portées des profils et synchronisation ; budgets de performance. Les propositions demeurent provisoires jusqu'à résolution ou acceptation explicite des limites.
