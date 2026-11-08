# DrillMaster — conception UX/UI et architecture cible

**Document de travail à valider, pas une spécification d'implémentation.** Le [dossier de spécifications proposé](specifications-future-version.md) décline ces orientations en contrats et critères d'acceptation. Référence : archive V1 2.9.394. Les interfaces n'ont pas été observées en fonctionnement dans QGIS ; les difficultés ci-dessous sont des **risques déduits du code** ou des hypothèses, sauf mention explicite. L'inventaire des 36 éléments est fondé sur [le relevé statique](inventaire-statique.md) : il inclut des composants internes et une ancienne vue, pas 36 fenêtres indépendantes. Les dialogues dynamiques supplémentaires sont à vérifier. Pour les faits, risques scientifiques et limites, voir [diagnostic](diagnostic-initial.md) et [plan d'audit](mission-audit-plan.md).

## 1. Profils et parcours

Les profils sont des hypothèses de travail à valider par entretiens et observation ; une même personne peut changer de rôle selon la tâche. Ne pas enfermer un utilisateur dans un mode déterminé.

| Profil | But et fonctions essentielles | Difficulté potentielle | Réponse conceptuelle |
|---|---|---|---|
| Débutant | Créer un projet, importer des collets et comprendre une première coupe. | Choisir un SCR, une convention de dip et interpréter des avertissements. | Assistant conservé, exemples contextualisés, étapes explicites, explication des hypothèses, aide accessible sans masquer les erreurs. |
| Intermédiaire | Répéter un import, vérifier les correspondances, produire coupes et export. | Refaire les mappings et paramètres, perdre le contexte entre vues. | Réutilisation suggérée et confirmée des configurations ; résumé de projet et liens vers problèmes ; échelles visibles. |
| Avancé | Comparer domaines, ajuster pistes, gérer référentiel, utiliser 3D. | Passage répété entre réglages et visualisation, options réparties. | Accès direct aux paramètres de l'objet sélectionné, réglages avancés accessibles, profils nommés et portée explicite. |
| Expert | Contrôler conventions, calculs, choix d'algorithme et restitution. | Hypothèses implicites, perte de précision ou différences entre vues et export. | Provenance, méthode et unités visibles, contrôle des hypothèses et détails vérifiables ; aucun changement de méthode silencieux. |
| Données / contrôle qualité | Vérifier familles, anomalies, corrections et provenance. | Messages épars, ambiguïté entre original et copie, problèmes nombreux. | Vue de contrôle transversale avec filtres, lien vers cellule et résolution explicite, export du rapport si faisable. |

### Parcours cibles — schéma

1. **Démarrage** → projet existant ou nouveau → vérifier nom, dossier, SCR et unités → résumé. Toujours permettre de revenir en arrière ; signaler les décisions ayant un impact sur les calculs.
2. **Données** → ajouter fichier(s) → reconnaître famille et colonnes → confirmer les ambiguïtés et la convention de dip → contrôle qualité → corriger sur copie/identifier l'origine → validation et synthèse. Ajouter d'autres familles sans recommencer tout le parcours.
3. **Trajectoires** → récapitulatif des données, méthode et hypothèses → calcul avec progression/annulation → bilan, anomalies et couches produites → coupe/3D. Les déviations absentes et la direction utilisée sont indiquées par forage ou groupe.
4. **Explorer** → choisir coupe ou 3D → sélectionner forage/domaine → ajuster paramètres du contexte → comparer → enregistrer un profil si souhaité. L'état d'une autre vue ne doit pas être modifié silencieusement.
5. **Restituer** → choisir sortie et échelle → aperçu et vérification → export → emplacement et résultat. Le périmètre d'annulation et d'export doit être explicite.

Ces parcours ne garantissent pas que toutes les transitions existent déjà. Comparer systématiquement avec la V1 avant toute modification et tester avec les profils concernés.

## 2. Architecture de navigation proposée

Préserver le modèle V1 **dock assistant + espace de visualisation** plutôt qu'introduire un nouveau shell sans preuve. Les noms ci-dessous sont à valider avec les utilisateurs et la traduction anglaise.

```text
DRILLMASTER — projet actif / SCR / état des données
│
├─ Assistant :  Projet → Données & contrôle → Trajectoires → Coupe
│                  retour à toute étape, statut et prochaine action
├─ Projet : ouvrir / fermer / référentiel / profils / préférences
└─ Visualisation : [Coupe 2D] [Vue 3D]
   ├─ Données visibles et sélection
   ├─ Apparence et pistes propres à la vue
   ├─ Analyse contextuelle (structures, surface…)
   └─ Export de la vue ou de la coupe, portée indiquée
```

- **Données & contrôle** regroupe les familles et les anomalies par intention ; conserver leurs 11 domaines et leurs contraintes. Un contrôle transversal renvoie à la famille et à la ligne, sans remplacer l'édition spécialisée.
- **Référentiel** et **profils** restent distincts : identité des catégories et symboles pour le premier ; préférences d'affichage pour les seconds. Un lien contextuel peut les rapprocher sans les fusionner.
- **Coupe** et **3D** partagent sélection, données et styles résolus lorsque leurs contrats le permettent ; contrôles de projection, caméra, échelle papier et export restent spécifiques. Annuler/rétablir indique explicitement sa portée, actuellement coupe 2D dans `ui/visualization_dock.py`.
- **Accès rapides** proposés : ouvrir projet, ajouter des données, voir les anomalies, sélectionner un forage, créer une coupe ; raccourcis clavier configurables seulement après audit des conflits QGIS. La découverte de ces accès doit rester possible sans mémorisation.
- **Portées** : préférences utilisateur locales (langue, disposition si validée), projet (SCR, mappings, référentiel et paramètres de calcul), vue/objet (pistes, caméra, échelle) et opération (chemin et options d'export). Indiquer où chaque réglage est stocké et ne jamais changer automatiquement un projet existant.

## 3. Direction artistique et Design System proposé

### Principes

Identité « **atelier géologique clair** » : interface neutre, précision et lisibilité ; la couleur porte d'abord les données et les états, pas une décoration concurrente. Privilégier les contrôles natifs QGIS/Qt, les règles système et les conventions du système d'exploitation. Garder la richesse des palettes géologiques V1 et ne pas recolorer les données à des fins esthétiques. Les contrastes et thèmes doivent être testés, pas présumés conformes.

### Tokens candidats — thème clair, à valider

| Rôle | Valeur proposée | Usage et garde-fou |
|---|---|---|
| Surface principale | `#F6F7F8` | Fonds de panneaux ; préserver lisibilité des cartes et canevas. |
| Surface de contenu | `#FFFFFF` | Tableaux et cartes de réglages ; pas de sur-encadrement. |
| Texte principal | `#20262D` | Titres, champs, contenu ; contraste à mesurer selon état réel. |
| Texte secondaire | `#4B5563` | Aide et métadonnées, jamais information essentielle en gris faible. |
| Bordure | `#BCC4CC` | Séparation et contrôle ; vérifier contraste contre la surface. |
| Action / sélection | `#243849` | Bouton principal, indicateur sélection ; libellé explicite. |
| Information / succès / attention / erreur | `#245A81` / `#19643A` / `#835000` / `#9B2525` | Texte/icône d'état sur surface claire ; jamais couleur seule. |
| Focus | Couleur de focus système en priorité | Trait distinct et visible sur tous thèmes, non supprimé ; test clavier réel. |

Pour le thème sombre, **utiliser d'abord la palette native QGIS/Qt** et prévoir des rôles sémantiques adaptés après mesure ; ne pas inverser mécaniquement ces couleurs. Vérifier au minimum 4,5:1 pour texte courant et 3:1 pour grands textes et éléments graphiques pertinents, comme critères de conception à adapter aux exigences applicables ; mesurer chaque combinaison réelle, y compris désactivé/focus et textes sur couleurs de données. Ne pas revendiquer la conformité WCAG pour une application Qt sur la seule base des couleurs.

### Typographie, géométrie et composants

| Élément | Proposition de contrat |
|---|---|
| Police | Police système Qt/QGIS, pas de police embarquée imposée. Base = taille utilisateur ; titre principal ≈ 1,35×, titre de section ≈ 1,15×, libellé/contenu 1×, secondaire ≥ 0,9× lorsque lisible. Éviter les corps minuscules fixes. |
| Espacement | Échelle indicative 4 / 8 / 12 / 16 / 24 unités logiques ; marges de panneau typiquement 12–16, entre champs 8–12. Adaptation via layouts et métriques Qt, pas d'alignement figé en pixels physiques. |
| Dimensions | Viser une hauteur confortable, par exemple 28–32 unités logiques pour contrôles courants, **minimums adaptatifs et non tailles fixes** ; respecter `sizeHint`, police, DPI, plateforme et traduction. Petits échantillons de couleur ne sont pas nécessairement des cibles cliquables. |
| Boutons | Un principal par contexte, actions secondaires natives, destructive séparée et explicitée. `QDialogButtonBox` pour rôles standards et ordre système ; « … » si un dialogue s'ouvre. Désactivé avec explication accessible. |
| Saisie | Libellé persistant, type et unité explicites, contraintes proches du champ ; exemples seulement si utiles, validation sans effacer les données. Choix CRS avec identifiant et unité. |
| Listes et tableaux | En-têtes compréhensibles, colonnes redimensionnables, sélection et raccourcis clavier ; localisation d'erreur ligne/colonne sans couleur seule. Grands jeux : tester temps et mémoire avant virtualisation. |
| Menu / navigation | Termes par intention, actions regroupées sans niveaux inutiles ; état courant clair, pas de raccourci contradictoire avec QGIS. |
| Fenêtres | Parent Qt explicite, disposition redimensionnable, limites et défilement adaptés ; conserver l'état uniquement si utile. Respecter l'ordre des boutons natifs et éviter les onglets imbriqués lorsque possible. |
| Panneau repliable | Titre, état ouvert/fermé et nombre d'anomalies si pertinent ; action clavier et nom accessible ; un réglage actif reste résumé même replié. |
| État / erreur | Information : texte court et contexte ; avertissement : conséquence et vérification ; erreur : cause, localisation et action de récupération. Conserver détails techniques accessibles, ne jamais confondre avertissement et résultat validé. |
| Progression | Description, étape, progression déterminée si connue ; sinon indicateur indéterminé. Annuler seulement si réellement pris en charge et indiquer le résultat après annulation. |
| Icônes | Favoriser icônes QGIS ou Qt cohérentes avec le thème, texte ou nom accessible, taille pilotée par métriques système. Pas d'icône seule pour une action ambiguë. |

**Réalisation Qt/QGIS :** démarrer par `ui/styles_qt.py`, `CollapsibleGroup`, `ValidationIssue` et `QDialogButtonBox` existants ; inventorier les styles locaux et les états de focus avant unifier. Éviter une feuille de style globale qui écrase les thèmes QGIS, la police système ou l'indicateur de focus. Tester Qt/QGIS des versions supportées, traductions, mise à l'échelle et plateformes ; aucune faisabilité complète n'est encore démontrée.

## 4. Revue conceptuelle des 36 éléments

**Légende des colonnes** : I = indispensable ; S = secondaire ; A = avancé ; M = mutualisation ; Auto = automatisation suggérée, toujours contrôlable ; P = public principal (D débutant, I intermédiaire, A avancé, E expert, Q contrôle qualité). Les « risques » ne sont pas des défauts visuels observés. Les options réellement présentes doivent être vérifiées avant classement ; rien n'est supprimé. Les composants qui ne sont pas des fenêtres sont signalés. Les éléments de sécurité, hypothèses scientifiques, CRS et erreurs bloquantes ne doivent jamais être masqués simplement parce qu'ils sont « avancés ».

| Interface / rôle | P ; risque ou preuve statique | I / S / A | Organisation future ; M ; Auto |
|---|---|---|---|
| 1 `AboutDialog` — identité/licence | Tous ; contenu à vérifier en QGIS. | I version et licence ; S liens ; A dépendances. | Fiche compacte, détails accessibles ; M liens et bouton de fermeture ; Auto version lue des métadonnées. |
| 2 `CsvEditorDialog` — correction de données | Q/I ; risque de confusion source/copie à vérifier. | I fichier, cellules et anomalies ; S recherche ; A détails d'encodage. | Tableau + panneau de problème + actions explicites sur copie ; M validation ; Auto localisation sans correction silencieuse. |
| 3 `DisplayProfilesDialog` — profils | I/A ; risque de confusion avec référentiel. | I profil et portée ; S aperçu ; A valeurs détaillées. | Dialogue séparé, lien vers référentiel ; M champs et préférences ; Auto proposer profil existant sans écrasement. |
| 4 `DomainStructureDialog` — structure de domaine | I/A ; choix dépendant des données. | I organisation retenue ; S exemple ; A cas multi-codes. | Dialogue spécialisé avec aperçu ; M sélection d'organisation ; Auto détection proposée et confirmée. |
| 5 `LithologyStructureDialog` — structure lithologique | I/A ; règles différentes des autres domaines. | I colonnes et rôles ; S exemple ; A proportions/secondaires. | Même squelette que 4, règles lithologiques distinctes ; M aperçu/mapping ; Auto suggestion confirmée. |
| 6 `MainDock` — contrôleur assistant | Tous ; quatre étapes et état/footer attestés par le code. | I projet, étape, prochaine action ; S résumé ; A menu projet. | Dock compact, progression et retour prévisible ; M barre contexte et actions ; Auto reprise explicite. |
| 7 `_DomainColorPicker` — couleur | A ; composant interne, pas fenêtre autonome à compter comme parcours. | I couleur et aperçu ; S palette ; A valeur exacte. | Sélecteur natif avec aperçu et libellé ; M palette ; Auto suggestion modifiable. |
| 8 `ReferenceDialog` — codes et styles | I/A ; grand dialogue dans le code, densité visuelle non observée. | I domaine, code brut et libellé ; S symbole ; A règles et exceptions. | Liste domaines + détail sélection ; M sélecteurs ; Auto rapprochements proposés, sans modifier codes sources. |
| 9 `CollapsibleGroup` — section | Tous ; composant de `section_dock.py`. | I titre et état ; S résumé ; A contenu variable. | Un composant accessible partagé ; M focus/états ; Auto mémorisation de l'ouverture si utile. |
| 10 `SectionCanvas` — canevas de coupe | I/A ; classe de rendu importante, interaction réelle non observée. | I coupe, axes, forages ; S sélection/légende ; A annotations. | Canevas dominant, contrôle adjacent ; M sélection et légendes ; Auto ajustement de vue réversible. |
| 11 `SectionWidget` — poste de coupe | I/A/E ; nombreuses responsabilités dans le code. | I coupe, sélection et pistes ; S apparence ; A seuils, échelles, détails. | Regrouper par données/apparence/analyse/export, sans masquer réglage actif ; M sections ; Auto valeurs de vue réversibles. |
| 12 `_LocPreview` — aperçu de localisation | I/A ; composant interne de l'export. | I aperçu et emprise ; S légende ; A style. | Intégrer à l'export sans dialogue supplémentaire ; M rendu d'aperçu ; Auto cadrage proposé. |
| 13 `export_png_dialog` — image | I/A ; fabrique de dialogue, chemin distinct d'export à l'échelle. | I chemin et contenu ; S aperçu ; A résolution/ornements. | Export identifié « image » et aperçu ; M destination, erreurs ; Auto nom proposé sans écraser. |
| 14 `export_scaled_dialog` — échelle papier | A/E ; contraintes physiques différentes du PNG. | I échelle, format, unités ; S aperçu ; A marges/options. | Même squelette que 13 mais dialogue ou étape distincte tant que contrats diffèrent ; M destination ; Auto contrôle de dimensions. |
| 15 `PluginSplash` — démarrage | Tous ; dimensions fixes dans le code, impact non observé. | I progression si utile ; S version ; A aucun. | Discret, non bloquant si faisable ; M statut ; Auto uniquement quand démarrage réel est long. |
| 16 `Step1Config` — configuration | D/I ; SCR par défaut 32630 dans le code. | I projet, dossier, SCR ; S langue ; A échantillonnage si non essentiel au départ. | Formulaire clair + résumé SCR/unité ; M sélecteur de projet ; Auto proposer dernier SCR avec confirmation, jamais deviner la zone. |
| 17 `DropZone` — ajout de fichier | Tous ; composant interne. | I ajouter et types acceptés ; S glisser-déposer ; A aucun. | Bouton clavier équivalent au dépôt ; M zone fichier ; Auto reconnaître format avec confirmation. |
| 18 `ImportTab` — famille de données | I/Q ; mapping et convention dip présents dans le code. | I fichier, famille, état ; S aperçu et mapping ; A structures/colonnes. | Une famille à la fois, anomalie accessible directement ; M tableau/mapping ; Auto suggestion sans forcer. |
| 19 `GroupedValidationPanel` — contrôle | Q/Tous ; `ValidationIssue` structurée existe. | I gravité, description, localisation ; S filtres ; A détails techniques. | Liste groupée et action vers source ; M message et navigation ; Auto regrouper mêmes erreurs sans masquer occurrences. |
| 20 `FamilyChip` — statut de famille | Tous ; composant interne. | I nom et état textuel ; S nombre ; A aucun. | Indicateur cliquable accessible avec nom/état ; M badge ; Auto décompte issu de validation. |
| 21 `Step2Import` — parcours d'import | Tous ; 11 familles dans le code, charge réelle inconnue. | I collets, familles présentes, erreurs ; S autres familles ; A organisation et mapping. | Catégories métier existantes + résumé + détail au besoin ; M 17–20 ; Auto détecter et suggérer, confirmation en cas d'ambiguïté. |
| 22 `Step3Geometry` — trajectoires | D/I/E ; message de repli V1 à clarifier, voir mission 4. | I méthode, hypothèses, calcul et état ; S aperçu ; A échantillonnage. | Avant calcul, récapitulatif et hypothèses par forage ; M progression et bilan ; Auto calcul suggéré, jamais résultats silencieux. |
| 23 `SectionMapTool` — outil carte | I/A ; outil d'interaction, pas fenêtre. | I tracé et instruction ; S modification ; A contraintes. | Indication dans carte et alternative clavier/données à étudier ; M sélection ; Auto nom de coupe proposé. |
| 24 `Step4Section` — création de coupe | D/I/A ; dépend du tracé et des forages. | I ligne/coupe et corridor ; S nom/direction ; A réglages de projection. | Étapes tracer → vérifier → ouvrir ; M sélection et unités ; Auto préremplissage réversible. |
| 25 `StepIndicator` — état d'étape | Tous ; composant interne. | I nom et état ; S erreur ; A aucun. | Texte et état accessibles, navigation prévisible ; M badge ; Auto état calculé depuis workflow. |
| 26 `StepperWidget` — progression | Tous ; composant interne. | I étapes et position ; S accès retour ; A aucun. | Pas de parcours artificiellement linéaire après création ; M 25 ; Auto statut fiable. |
| 27 `_StructureRoseWidget` — rosace | A/E ; graphique spécialisé. | I orientation, effectif, convention ; S sélection ; A classes. | Graphique avec résumé textuel ; M légende/export ; Auto classes suggérées et modifiables. |
| 28 `_StructureStereonetWidget` — stéréonet | A/E ; graphique spécialisé. | I projection, orientation, nombre ; S sélection ; A densité. | Garder distinct de la rosace mais même contexte et commandes ; M légende/export ; Auto récapituler exclusions. |
| 29 `StructureAnalysisDialog` — analyse | A/E ; exclusions de certaines observations dans `core/structure_analysis.py`. | I jeu, convention et exclusions ; S rosace/stéréonet ; A filtres et densité. | Conserver les graphiques distincts dans un atelier d'analyse ; M filtres ; Auto signaler données non représentées sans les inventer. |
| 30 `View3DWidget` — ancienne vue | A ; présence dans l'archive, rôle actif non prouvé. | I données et caméra si accessible ; S légende ; A détails. | Ne pas supprimer : tracer usages et compatibilité avant décision ; M commandes avec 3D v2 seulement après comparaison ; Auto aucune tant que statut inconnu. |
| 31 `View3DCanvas` — ancien canevas | A ; statut d'exécution non prouvé. | I scène et interactions ; S sélection ; A rendu. | Même réserve que 30 ; M sélection éventuelle ; Auto cadrage réversible si actif. |
| 32 `_AssayElementDialog` — choix teneurs | I/A ; dialogue spécialisé. | I éléments et portée ; S ordre ; A limites d'affichage. | Sélecteur commun, signaler limites sans supprimer données ; M choix multisélection ; Auto présélection contrôlable. |
| 33 `_ImageryPhotoDialog` — image | I/A ; fenêtre spécialisée. | I photo, intervalle et chemin ; S navigation ; A métadonnées. | Visualiseur dédié et état manquant ; M navigation et message ; Auto résolution de chemin avec confirmation si ambigu. |
| 34 `_Viewport` — canevas 3D v2 | I/A ; interactions souris repérées dans le code. | I scène, sélection, orientation ; S contrôles caméra ; A détail rendu. | Rendre les alternatives clavier et orientation visibles ; M sélection ; Auto cadrage réversible. |
| 35 `View3DV2` — vue 3D | I/A/E ; construction asynchrone et repli 3D à investiguer. | I scène, domaines, hypothèses ; S affichage ; A caméra et performance. | Contrôles par intention sans masquer les données indisponibles ; M état/progression ; Auto qualité adaptative seulement si effet annoncé. |
| 36 `VisualizationDock` — espace de travail | Tous ; deux onglets et actions coupe spécifiques dans le code. | I vue active et contexte ; S raccourcis pertinents ; A disposition. | Conserver coupe/3D, afficher portée des commandes ; M contexte ; Auto restaurer disposition sans modifier le projet. |

Les dialogues de surface/raster et d'export créés indirectement, boîtes natives et variantes conditionnelles ne sont pas nécessairement couverts par ces 36 fiches : compléter après inspection dynamique. Fusionner des **squelettes et composants**, non des règles ni des fenêtres incompatibles ; les sorties image et échelle, analyses structurales et référentiel/profils gardent leurs responsabilités distinctes.

## 5. Maquettes conceptuelles textuelles

Ces schémas illustrent l'organisation de l'information, pas les dimensions ou un écran réellement observé. « Voir détail » reste accessible au clavier ; les états et valeurs sont des exemples, pas une capture de V1.

### A. Assistant / projet

```text
DrillMaster                          Projet ▾
Projet : Exemple     SCR : EPSG:32629
[1 Projet] — [2 Données] — [3 Trajectoires] — [4 Coupe]

Nom du projet      [ Exemple                    ]
Dossier            [ …                          ] [Choisir…]
SCR projeté        [ WGS 84 / UTM 29N          ] [Choisir…]
Unités : mètres    [Pourquoi ce choix ?]
▸ Options de projet  [résumé des valeurs actives]

État : prêt à importer                 [Suivant]
```

### B. Import et qualité

```text
Données et contrôle                         [Ajouter des fichiers…]
Géométrie     Collets  Prêt   | Déviations  À vérifier
Géologie      Lithologie Prêt | Altérations Non ajoutées
Géochimie     Teneurs Prêt    | … autres familles …

Déviations : fichier choisi
Convention : négatif = bas  [Modifier…]
2 erreurs · 1 avertissement   [Voir tous les problèmes]
  Erreur  Identifiant inconnu — ligne 8      [Atteindre]
▸ Colonnes et organisation  [résumé des choix actifs]
[Modifier la copie…]                   [Vérifier les données]
```

La convention n'est montrée que si elle est applicable ; la proposition n'affirme pas que tous les contrôles existent déjà ni que la copie est toujours utilisée dans la V1.

### C. Trajectoires

```text
Trajectoires
Forages prêts : 3       Données à vérifier : 0
Méthode : angles moyens       Unités : mètres
Sans déviation : direction du collet 2 · verticale 1 [Détails…]
▸ Options de calcul  [pas : …]
[Générer les trajectoires]
État : en attente / progression / terminé / annulé
```

Les nombres et catégories sont des propositions ; ils exigent un contrat de provenance et des tests métier.

### D. Coupe / 3D et export

```text
Projet : Exemple  | Coupe : C-01 | Forages : 3
[Coupe 2D] [Vue 3D]               [Exporter la coupe…]
┌────────────────────────────┬────────────────────────┐
│                            │ Données et sélection   │
│  CANEVAS DE COUPE          │ ▸ Pistes : 3 actives   │
│  axes, forages, légende    │ ▸ Apparence            │
│                            │ ▸ Analyse et surface   │
└────────────────────────────┴────────────────────────┘
Annuler / rétablir : réglages de coupe uniquement
```

```text
Exporter à l'échelle
Format [A4 ▾]  Échelle [1 : 1000]  Unités [m]
[Aperçu de la page et de son emprise]
Destination [ … ] [Choisir…]
▸ Options d'export  [résumé]
[Annuler]                                      [Exporter]
```

## 6. Composants communs et architecture cible

| Contrat proposé | Utilisateurs | Extension par domaine / précautions | Source existante à caractériser |
|---|---|---|---|
| `ProjectContext` | Assistant, coupe, 3D, export | Projet, SCR, version de données, état et provenance ; pas de widget dans le domaine. | `core/project.py`, `workspace.py` |
| `ValidationIssue` et panneau de problèmes | Import, CSV, calcul | Code, sévérité, localisations, suggestion ; les règles restent spécifiques à chaque famille. | `core/validation.py`, `GroupedValidationPanel` |
| Sélecteur fichier/CRS/unité | Configuration et import | Fournisseur QGIS pour CRS ; aucune conversion implicite ; mode fichier adapté aux usages. | `step1_config.py`, `DropZone` |
| Section repliable et résumé | Import, coupe, 3D | Focus, nom accessible, résumé d'options actives ; contenu propre à chaque domaine. | `CollapsibleGroup`, styles existants |
| Sélection et contexte | Coupe, carte, 3D, analyse | Identité stable, signalisation des objets absents ; pas d'hypothèse d'égalité entre projections. | `core/selection_model.py`, `workspace.py` |
| Référentiel et style résolu | Données, coupe, 3D, export | Code brut inchangé, sorties adaptées au support ; préserver styles et exceptions. | `reference.py`, `style_resolver.py` |
| Trajectoire et provenance | Géométrie, couches, coupe, 3D | Méthode, dip, CRS/unité, état et hypothèses ; secours explicites. Ne pas modifier les calculs historiques sans validation. | `geometry.py`, `geometry_cache.py`, `scene3d/adapter.py` |
| Tâche et résultat | Calculs longs, import, rendu | Données copiées si nécessaire ; annulation réelle, résultat immuable et mise à jour UI sur fil principal. | `GeometrisationTask`, `View3DV2` |
| Modèle d'export / aperçu | Exports image et à l'échelle | Séparer unités écran/papier et formats ; parité testée sans fusion artificielle. | `section_export.py`, `section_export_scaled.py` |

Dépendances proposées : **Qt/QGIS UI → contrôleurs de parcours → services métier et calculs** ; adaptateurs en périphérie pour QGIS, CSV, GeoPackage, rendu, tâches et préférences. Les classes existantes restent en place jusqu'à tests de caractérisation et migration contrôlée. Les paramètres projet et utilisateur passent par des contrats distincts ; pas de registre global unique qui efface la provenance.

## 7. Catalogue d'automatisations à arbitrer

| Proposition | Bénéfice | Contrôle et limite | Priorité / dépendance |
|---|---|---|---|
| Suggestions de familles et de colonnes | Réduit la saisie répétée. | Montrer confiance/ambiguïtés, accepter correction ; pas de changement source. Des mécanismes existent déjà. | P1 ; parseur, règles et tests de mapping. |
| Réutiliser profils de mapping | Accélère les imports comparables. | Proposition par projet, résumé et confirmation si colonnes diffèrent. | P1 ; persistance et migrations. |
| Préremplir SCR à partir du projet | Réduit une répétition. | Toujours afficher identifiant/unité ; ne pas inférer une zone depuis des coordonnées ambiguës. | P1 ; règles CRS. |
| Bilan des directions de repli | Rend explicite une hypothèse influant les résultats. | Signaler par forage, distinction collet vs verticale ; ne pas modifier données. | P1 ; provenance et validation métier. |
| Regrouper et localiser les erreurs | Accélère le contrôle qualité. | Garder toutes les occurrences et différences de sévérité ; accès direct à la ligne. | P1 ; `ValidationIssue` et éditeur. |
| Noms et chemins d'export proposés | Réduit les saisies. | Prévenir écrasement, choix utilisateur final, respect de la portée. | P2 ; audit I/O. |
| Aperçu avant export | Évite sorties incorrectes. | Indiquer taille réelle, unités, échelle et différences éventuelles ; rendu vérifié. | P2 ; contrat de rendu et test physique. |
| Profils de vue nommés | Facilite comparaison et reprise. | Projet/utilisateur explicite, pas d'écrasement des réglages existants. | P2 ; inventaire des préférences. |
| Traitements par lots | Gain sur nombreuses coupes/exportations. | À proposer seulement après mesure d'usage ; aperçu, progression, annulation et rapport d'échec. | P3 ; contrats d'export et tâches. |
| Historique d'opérations | Audit et reproductibilité. | Enregistrer provenance et paramètres sans données sensibles inutiles ; ne pas promettre annulation complète. | P2/P3 ; définition de persistance et stockage. |

## 8. Décisions et validation avant développement

1. **Navigation** : conserver assistant et visualisation séparés ? Quels accès rapides sont les plus importants ?
2. **Direction artistique** : valider l'idée de chrome neutre et de police système, sous réserve des essais QGIS/thèmes ; les couleurs ne sont pas définitives.
3. **Organisation des données** : regrouper le contrôle qualité transversal tout en gardant les spécificités des onze familles ?
4. **Portée des préférences** : quels réglages doivent suivre le projet, et lesquels rester propres à l'utilisateur ?
5. **Hypothèses scientifiques** : valider avec un géologue la manière d'afficher méthode, convention et direction de repli ; ne pas approuver une nouvelle méthode sur cette seule base.
6. **Prochain contrôle** : tester en QGIS réel les 36 éléments, dialogues indirects, thèmes, langues, petites fenêtres, focus et parcours représentatifs ; compléter les jeux géologiques. Les maquettes et priorités changent si les observations les contredisent.

La validation de cette direction n'autorise **ni modification du plugin ni refonte** : une décision séparée sera nécessaire après audit opérationnel, validation scientifique et plan de non-régression.

---

# Consolidation des arbitrages — mission 6

**Statut : direction recommandée comme référence de conception, sous réserve de validation du propriétaire, de l'inspection QGIS et d'une revue scientifique.** Elle remplace les indications moins précises qui précèdent en cas de contradiction. Les alternatives ne sont pas des solutions testées : les critères sont déduits des parcours et du code de la V1, pas de mesures utilisateurs. Aucune modification du plugin n'est autorisée par cette proposition.

## 9. Comparaison des organisations et décision N1

| Option | Atouts | Inconvénients / risques | Compatibilité et décision |
|---|---|---|---|
| **A. Deux docks coordonnés** : assistant compact + visualisation coupe/3D, tous deux ancrables ou flottants | Cohérent avec `MainDock` et `VisualizationDock` actuels ; assistant visible pendant l'exploration ; QGIS garde sa carte et ses couches. | Sur petit écran, concurrence spatiale ; synchronisation nécessaire ; deux panneaux peuvent être perçus comme deux produits. | **Recommandée** : faire du dock assistant un contrôleur de contexte et du dock visualisation un espace de travail. Valider l'encombrement et la disposition avec DPI et petits écrans réels. |
| B. Fenêtre unique plein écran | Grande zone de travail, cohésion interne. | Masque la carte et les outils QGIS, change les habitudes, fenêtre modale possible et friction multitâche. | Non retenue par défaut ; éventuellement pour une tâche très spécifique après essai. |
| C. Panneau unique avec assistant et visualisation en pages | Peu de docks, navigation apparemment simple. | Aller-retour constant, paramètres et résultat rarement visibles simultanément ; les changements de contexte deviennent coûteux. | Non retenue comme organisation principale ; une disposition réduite peut rester utile sur écran étroit. |
| D. Multiples fenêtres indépendantes par fonction | Flexibilité pour experts et double écran. | Perte de contexte, prolifération et conflits de sélection/paramètres ; fermeture difficile à comprendre. | Réserver aux tâches spécialisées et non destructives ; pas comme structure globale. |

### Contrat entre les espaces

- **Une autorité de contexte par projet** : identifiant de projet, révision des données, SCR, forages, coupe active et sélection stable appartiennent au contexte partagé ; les docks s'y abonnent et ne maintiennent pas chacun une vérité scientifique différente. `core/workspace.py` et `core/selection_model.py` sont à étudier avant création d'un nouveau service.
- **Partagé versus local** : données, géométrie calculée, référentiel et sélection sont partagés ; caméra 3D, zoom, filtres purement visuels et disposition restent propres à la vue sauf action explicite « appliquer à… ». La sélection partagée ne signifie pas synchroniser automatiquement tous les filtres ou styles. Signaler les objets filtrés ou absents dans l'autre vue.
- **Changement de contexte** : avant changement de projet ou fermeture, signaler les modifications non enregistrées et tâches en cours ; choisir enregistrer, abandonner ou revenir. Invalider les aperçus/calculs liés à l'ancienne révision ; empêcher un résultat tardif de l'ancien projet de remplacer le nouveau. Les mécanismes et garanties réels restent à tester.
- **Prévisualisation** : utiliser un état de travail distinct des valeurs enregistrées. Pour un style, aperçu local réversible ; pour un calcul ou export, aperçu identifié comme non validé, avec méthode, paramètres et données de référence. Appliquer écrit uniquement dans la portée annoncée ; annuler restaure l'état précédent. Une prévisualisation coûteuse peut être explicite plutôt qu'automatique.
- **Résultats vers paramètres** : sélectionner une anomalie ouvre le contexte et la ligne concernés ; sélectionner un objet dans une vue informe l'autre par identifiant, sans modifier les données. Un réglage ayant rendu un résultat obsolète doit afficher « à recalculer » plutôt que masquer l'ancien résultat ou le présenter comme à jour.
- **Fenêtres** : privilégier panneaux contextuels et sections repliables ; réserver les dialogues aux choix complexes, aux éditeurs spécialisés et à l'export. Une fenêtre doit avoir parent, portée, état de modifications et chemin de retour explicites. Pas de synchronisation en boucle : un changement effectif produit une notification avec origine et révision, les vues s'actualisent sans réémettre un changement identique.
- **Intégration QGIS** : exploiter `QgsDockWidget`, les actions, couches et conventions du projet QGIS ; éviter tout changement global de palette/fontes de l'application. Les opérations Qt/QGIS sur objets du fil principal restent sur ce fil ; les calculs longs reçoivent des données isolées et renvoient des résultats contrôlés. Vérification sous QGIS 3 requise.

### Scénarios de validation obligatoires

1. Modifier un seuil dans la coupe : seule la portée annoncée change ; 3D et export ne suivent que si la liaison est explicitement activée ou contractuellement prévue.
2. Sélectionner un forage filtré dans une autre vue : afficher une indication et proposer de l'afficher, sans changer silencieusement le filtre.
3. Lancer une génération, changer de projet puis recevoir le résultat tardif : aucun résultat de l'ancien projet ne s'applique au nouveau.
4. Ouvrir un aperçu de style, annuler puis rouvrir : les valeurs enregistrées ne changent pas ; appliquer ne modifie que la portée annoncée.
5. Réduire la largeur, flotter/réancrer les docks et redémarrer QGIS : contrôle qualité, action principale et focus restent accessibles. Ces scénarios ne sont pas encore exécutés.

## 10. Direction artistique proposée comme référence D1

**Nom de travail : « Atelier géologique »**. Personnalité fondée sur trois choix : chrome calme, données géologiques expressives, et lisibilité des décisions techniques. La distinction n'est pas une peau isolée : elle s'exprime par une barre de contexte reconnaissable, des titres sobres, un rythme d'espacement constant, des panneaux à en-têtes précis et des états cohérents. Elle ne doit jamais entrer en concurrence avec les couleurs des lithologies ou les conventions de carte.

### Règles d'application

- **Conserver natif** : sélecteur de fichiers/CRS, contrôles numériques et de texte, menus, raccourcis, `QDialogButtonBox`, navigation clavier et conventions système. Ne pas remplacer un contrôle accessible par un dessin sans gain démontré.
- **Personnaliser de façon bornée** : en-têtes de dock, barre de contexte, progression d'étapes, cartes d'état, sections repliables, badges de qualité, tableaux de validation et légendes. Les éléments Qt gardent leur nom accessible, état, focus et rôle ; les visuels de données géologiques restent spécifiques.
- **Couleurs** : utiliser les rôles et valeurs de la section 3 comme proposition claire ; thème sombre dérivé des rôles et de la palette QGIS, non d'une inversion automatique. Pour distinction d'état : couleur + icône + texte ; utiliser couleurs de données issues du référentiel, non celles des états. Test préalable clair/sombre et fort contraste obligatoire.
- **Contrastes calculés pour les paires proposées**, calcul sRGB relatif sur couleurs opaques : texte principal `#20262D` / blanc 15,26:1 ; secondaire `#4B5563` / `#F6F7F8` 7,05:1 ; texte blanc / action `#243849` 12,09:1 ; information, succès, attention et erreur sur blanc respectivement 7,36 / 7,18 / 6,75 / 7,82:1. La bordure `#BCC4CC` sur blanc ne vaut que **1,76:1** : décorative uniquement, ne pas l'utiliser comme seul indicateur des limites d'un contrôle ou du focus. Ces chiffres ne valident ni le rendu Qt ni les autres états.
- **Typographie et mesures** : police et taille système ; échelle relative 1 / 1,15 / 1,35, styles secondaire et gras mesurés à la police réelle ; espacement logique 4/8/12/16/24 ; contrôles selon métriques natives, marges adaptatives. Les 28–32 unités de la section 3 sont des cibles indicatives, jamais une hauteur fixe ni une garantie d'accessibilité.
- **Focus et états** : indicateur visible sur le contrôle et son voisinage ; ne pas appliquer `outline: none` sans remplacement effectivement vérifié. L'état désactivé est expliqué ; ne pas communiquer un problème seulement par couleur, infobulle ou emoji.
- **Iconographie** : réutiliser les icônes de QGIS lorsque leur sens correspond ; les compléments propres à DrillMaster respectent une même épaisseur, surface optique et sémantique, tailles pilotées par DPI. Tester l'apparence à petite taille et dans les deux thèmes ; noms accessibles indépendants des infobulles.
- **Textures et cartes** : maintenir la distinction entre chrome et symboles géologiques ; utiliser motifs/légendes et libellés pour les catégories proches en couleur. Les cartes et sorties imprimées ne sont pas recolorées pour s'accorder au thème de l'interface.

### Alternatives graphiques et garde-fous

Une **interface entièrement native** minimise le risque de compatibilité mais ne résout pas à elle seule la cohérence des messages et de la hiérarchie ; une **peau Qt globale fortement personnalisée** a plus de personnalité mais risque de casser thèmes, focus et mises à l'échelle. D1 recommande un système de rôles et composants localisés, au-dessus des contrôles natifs. La V1 possède déjà `styles_qt.py` : son remplacement n'est ni présupposé ni immédiat. Valider un échantillon représentatif (import, erreur, panneau de coupe, dialogue d'export) dans QGIS 3 clair/sombre, avec agrandissement, clavier et FR/EN avant d'en faire une norme d'implémentation.

## 11. Architecture du contrôle qualité Q1

### Flux et responsabilités

```text
Source / copie + mapping + conventions confirmées
       ↓
Parseur et provenance → contrôles génériques → règles de famille
       ↓                         ↓                     ↓
contrôles inter-familles → bilan structuré versionné → panneau commun
                                                    ↙             ↘
                                      aller à la source       plan de correction
                                                            aperçu → confirmation
                                                            → copie → revalidation
```

1. **Parsing et provenance** : chaque résultat référence une source, une révision, la famille, l'emplacement (ligne/colonne si disponible), l'encodage et les choix de mapping/convention pertinents. Ne pas supposer que tous ces champs existent déjà en V1.
2. **Règles génériques** : champs requis, identité, nombres finis, bornes et relations simples sont partagés lorsqu'ils ont exactement la même sémantique. Les règles de profondeur et d'identifiant peuvent s'appuyer sur l'existant, pas sur une deuxième implémentation concurrente.
3. **Règles spécialisées** : lithologie et proportions, teneurs et valeurs spéciales, géotechnique et unités, structures et orientations, imagerie et chemins gardent chacune leurs règles. Les contrôles inter-familles (par exemple RQD/récupération) déclarent explicitement leurs conditions de comparabilité.
4. **Résultat** : faire évoluer le contrat `core/validation.py:ValidationIssue` existant, qui fournit déjà code, sévérité, message, suggestion et localisations. Cible : code stable + version de règle, paramètres de message traduisibles, référence de données, portée, cause et proposition de résolution ; séparer le détail technique de la présentation. Préserver les listes et consommateurs historiques par adaptateur pendant la migration.
5. **Gravités** : erreur bloquante si l'opération concernée ne peut pas produire un résultat sûr ; avertissement si le traitement reste possible avec une réserve explicite ; information pour les décisions ou faits à connaître. La sévérité est attribuée par règle **et contexte d'opération**, pas un niveau universel inventé pour toutes les familles. Aucun avertissement ne doit devenir une correction automatique.
6. **Rapport** : résumé par famille et sévérité, filtre, regroupement sans perdre les occurrences, lien vers cellule ou objet. Un rapport exporté inclut versions, provenance, conventions et réserves ; données sensibles et chemins sont traités selon choix utilisateur.
7. **Correction assistée** : proposer une action avec ancien/nouveau contenu et conséquence, vérifier qu'elle s'applique à la bonne révision, confirmer avant écriture, opérer sur copie de travail, journaliser et revalider. Pas de correction automatique des valeurs scientifiques ambiguës, du CRS ou du dip. L'absence de possibilité d'annuler doit être annoncée ; modification de source originale uniquement après décision explicite future et preuve de sécurité.
8. **Exceptions** : distinguer une exception technique d'une anomalie de données. Une donnée non vérifiée n'est jamais marquée comme valide ; rapporter les contrôles non exécutés ou impossibles. Tester groupes, traduction, localisation, accès clavier et révalidation.

**Alternative écartée** : un validateur unique à règles uniformes pour toutes les familles simplifierait l'interface mais écraserait les différences de sémantique ; des validateurs sans contrat commun empêcheraient une vue transversale. Q1 partage le contrat et les primitives, tout en gardant les règles métier indépendantes. Dépendances : caractériser les codes et comportements V1, approuver les règles avec un géologue, bâtir les tests avant extraction.

## 12. Architecture des paramètres C1

### Types et autorités

Une même clé a une **portée autorisée déclarée**, un type, une unité si pertinente, une valeur par défaut versionnée, des règles de validation et une politique de migration. « Module », « scientifique » et « affichage » décrivent le rôle ; projet, utilisateur et exécution décrivent où la valeur vit. Une clé ne migre pas d'une catégorie à l'autre implicitement.

| Paramètre / exemple | Autorité proposée | Portée et validation | Réinitialisation |
|---|---|---|---|
| SCR, unités de données et convention de dip | Projet et données importées | Convention scientifique explicite par projet ou source si nécessaire, avec provenance et confirmation. Interdire un override utilisateur implicite. | Action distincte, avertissement sur résultats dépendants, recalcul et conservation de l'ancienne décision. |
| Méthode de trajectoire et pas d'échantillonnage | Projet, éventuellement opération selon contrat | Méthode/version et unité persistées avec résultats ; changement contrôlé avec invalidation. Le pas existe dans `default_sampling_step`. | Restaurer la valeur de projet ou un défaut documenté, avec recalcul annoncé. |
| Mapping, organisation d'une famille et référentiel | Projet / source | Valider colonnes et version ; garder codes bruts. Les suggestions utilisateur ne deviennent projet qu'après confirmation. | Remise à zéro ciblée avec aperçu de conséquence, sans réécriture des sources. |
| Style de coupe et options d'une section | Projet / module / objet selon effet | Le projet peut définir un style de base, la coupe une exception explicite ; indiquer l'origine effective. | Réinitialiser l'exception vers le style du projet, ou restaurer style projet par action séparée. |
| Préférences personnelles de langue et disposition | Utilisateur (`QSettings` ou équivalent QGIS) | N'affectent ni données, ni calculs, ni configuration scientifique. | Réinitialisation locale, sans toucher au projet. |
| Caméra, zoom, panneau ouvert | Vue / session ; sauvegarde optionnelle | Pas de changement scientifique ; restaurer si l'objet existe encore. | Réinitialiser la vue uniquement. |
| Chemin et options d'un export en cours | Opération | Valeurs de travail temporaires ; enregistrer un préréglage seulement par action explicite. | Annuler abandonne le brouillon, jamais les données du projet. |

### Priorité et héritage — par classe de clé

- **Scientifique** : valeur explicite confirmée pour la source ou l'opération, seulement si cette variation est autorisée et enregistrée avec le résultat ; sinon valeur projet confirmée ; sinon défaut de création versionné présenté à l'utilisateur. **Aucune préférence utilisateur ne surpasse une convention scientifique d'un projet existant.** Si valeur manquante ou ambiguë : demander confirmation ou bloquer l'opération concernée ; ne pas déduire silencieusement une convention.
- **Affichage** : exception explicite d'objet/vue → style du projet → préférence personnelle autorisée pour ce rôle → défaut système/plugin. Une préférence personnelle n'écrase pas une valeur de projet explicite. Afficher l'origine et permettre de supprimer l'exception pour revenir au niveau précédent.
- **Session/aperçu** : brouillon temporaire au-dessus de l'état affiché pour cette vue seulement, clairement marqué non enregistré ; appliquer écrit dans une portée désignée, annuler détruit le brouillon. Un résultat scientifique ne doit jamais dépendre d'un brouillon non enregistré sans en porter la provenance.
- **Création d'un projet** : des préférences peuvent suggérer des valeurs initiales (par exemple dernier SCR), mais la confirmation les copie dans le projet ; aucune modification ultérieure de préférence personnelle ne modifie les projets déjà créés. La valeur en cache ou absente ne devient jamais automatiquement un choix validé.

Validation aux frontières : type, plage, unité, disponibilité et compatibilité croisée avant sauvegarde/exécution ; ne pas remplacer silencieusement une valeur illisible par un défaut scientifique. Signaler l'erreur et garder la configuration d'origine. Sauvegarde : valeur + portée + version ; pour calculs, enregistrer la révision des données et les paramètres effectifs. Écritures atomiques/sauvegardes et récupération sont des exigences à étudier selon les formats et API, pas des capacités V1 prouvées.

### Migration depuis la V1

Faits repérés : `core/project.py` définit `CONFIG_VERSION`, `default_sampling_step` et `section_style` ; `core/i18n.py` utilise `DrillMaster/language` dans `QSettings` ; `ui/view_3d_v2.py` utilise `DrillMaster/view3d/…` dans `QSettings`. La localisation effective de chaque option doit être inventoriée avant migration. Procédure proposée : copies de projets et préférences représentatifs → lecture de l'ancien format sans modification → table explicite ancien/nouveau et valeurs ambiguës → validation de l'utilisateur pour les ambiguïtés scientifiques → sauvegarde de secours → écriture versionnée seulement après approbation → réouverture, comparaison des résultats et retour arrière documenté. Ne pas promettre qu'une ancienne version saura relire un nouveau projet ; tester et préciser la compatibilité réelle.

## 13. Vérification de cohérence et arbitrages restants

| Décision recommandée | Conséquence UI + architecture | Alternative / compromis | Validation nécessaire |
|---|---|---|---|
| N1 deux docks coordonnés | Contexte commun, vue locale et état périmé explicite. | Un seul panneau économise la place mais rend la comparaison plus difficile. | Parcours en QGIS, petits écrans et double écran. |
| D1 identité localisée sur socle natif | Style cohérent sans écraser thèmes/focus QGIS. | Skin global plus distinctif mais plus fragile. | Revue visuelle et accessibilité sur versions, thèmes et DPI. |
| Q1 contrat qualité commun + règles spécialisées | Résumé unique ; règles géologiques restent responsables de leur domaine. | Validateur monolithique plus simple en apparence mais inadapté aux exceptions. | Géologue, compatibilité des codes V1 et tests de non-régression. |
| C1 paramètres à autorité et portée déclarées | Origine visible ; aucune préférence ne modifie une convention scientifique. | Priorité universelle plus simple mais dangereuse. | Inventaire complet des clés, formats et projets historiques. |
| Prévisualisation explicite et réversible | Confiance et comparaison sans modifier les données. | Mise à jour immédiate plus rapide mais risque de confusion entre aperçu et résultat. | Mesures de performance et tests annulation/états. |

**Questions ouvertes avant figer la référence :** règles exactes de synchronisation de sélection et de styles 2D/3D ; portées préférées pour profils et réglages de coupe ; granularité des conventions par source ou projet ; modalités d'accès à QGIS pour observation ; versions et plateformes cibles ; besoins réels d'experts et de débutants ; méthode d'export et conservation de ses dimensions ; validation des données de forage montant et méthodes de trajectoire. La réponse à ces questions peut invalider certains arbitrages.

**Points de contrôle proposés** : (1) valider la direction conceptuelle ; (2) réaliser l'audit opérationnel et scientifique restant ; (3) tester les maquettes et les contrats avec utilisateurs et géologue ; (4) établir compatibilité, tests et migration ; (5) présenter un plan détaillé pour autorisation séparée de développement. Les choix proposés sont cohérents entre eux, mais ne sont pas encore prouvés réalisables sur toutes les plateformes QGIS déclarées.
