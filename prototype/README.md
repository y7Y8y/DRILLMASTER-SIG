# DrillMaster — prototype UX/UI V02

**Maquette de conception indépendante du plugin QGIS.** Cinq espaces sont simulés : importation, contrôle qualité, trajectoires, coupes et visualisation. Données fictives, états prédéfinis et schémas illustratifs : aucun fichier n'est importé, aucune validation scientifique ni trajectoire n'est calculée et aucun export n'est créé. Aucun traitement V1 n'est exécuté.

## Lancer localement

Ouvrir `index.html` dans un navigateur récent. Ou, depuis ce dossier :

```sh
python3 -m http.server 8000
```

Puis ouvrir `http://localhost:8000`. HTML/CSS/JavaScript autonomes, sans dépendance externe ni abonnement. Toutes les modifications sont en mémoire et disparaissent au rechargement.

## Parcours de démonstration

1. Depuis la vue d'ensemble, cliquer **Importation**. Choisir `collets_doublon.csv` dans la liste des exemples, examiner les colonnes et les premières lignes. Modifier une association pour voir l'état manquant ; la rétablir, puis confirmer l'import **simulé**. Le choix d'autres familles n'exécute pas un import fictif : seul le scénario collets est détaillé dans cette itération.
2. Ouvrir **Contrôle qualité**. Examiner l'erreur de doublon, filtrer/rechercher, afficher l'aperçu `DM-001 → DM-002`, annuler ou appliquer. La correction et son historique ne concernent que la mémoire du navigateur. Le bouton « Examiner » ouvre la proposition dans ce même panneau ; il ne navigue pas vers un vrai éditeur CSV.
3. Dans **Trajectoires**, choisir un forage vertical, incliné, sans déviation, avec station au-delà de la profondeur ou profondeur nulle. Simuler un calcul, son annulation ou son échec ; modifier le pas après succès pour voir l'état périmé. La figure est illustrative et ne montre pas le résultat d'un calcul.
4. Dans **Coupes**, sélectionner des forages et la piste lithologie pour masquer/afficher leurs éléments sur le schéma. Modifier les autres paramètres, simuler la génération, rendre le résultat périmé et essayer l'export simulé. Les paramètres d'orientation et les autres pistes ne modifient pas le schéma ; aucune coupe ni sortie n'est produite.
5. Dans **Visualisation**, basculer Carte / Coupe 2D / Vue 3D, choisir un forage et appliquer un filtre. La sélection est partagée, mais les options sont conservées séparément par vue. Les cases ne masquent que les éléments illustratifs disponibles ; la 3D n'est ni interactive spatialement, ni calculée.

Chaque espace est directement accessible sans suivre l'assistant. Les boutons au-dessus des panneaux permettent de masquer ou réafficher l'assistant et le contexte. L'option « fichier indisponible » illustre l'état manquant ; une liste vide de forages empêche la simulation de coupe.

## Données et représentations

DM-001 à DM-003 reprennent les exemples de `../donnees_fictives/normal/`. DM-004 à DM-006 sont des scénarios supplémentaires fictifs pour les cas limites. La référence de projet déclarée EPSG:32629 concerne les coordonnées de ces exemples ; **les cartes, coupes et vues dessinées sont des schémas non géoréférencés, sans échelle ni résultat scientifique**. Aucun résultat de contrôle qualité de la V1 n'est revendiqué par les badges de cette maquette.

## Fichiers

- `index.html`, `styles.css`, `app.js` : tableau de bord et composants initiaux.
- `workspaces.css`, `workspaces.js` : composants et interactions des cinq espaces.
- `DESIGN-SYSTEM.md` : identité et règles de conception.
- `REGISTRE.md` : couverture par domaine V1 et surfaces reportées.
- `REVUE.md` : vérifications réellement effectuées, limites et décisions à valider.

Le prototype navigateur n'établit pas la faisabilité, la fidélité ou l'accessibilité de la future interface Qt/QGIS. Aucune déclinaison individuelle des 36 interfaces ni modification du plugin n'est autorisée par ce livrable.
