# Revue critique — itération UX/UI V02

## Périmètre et preuves

Les cinq espaces demandés sont présents comme simulations locales. Les données DM-001 à DM-003 proviennent du jeu fictif ; d'autres cas d'essai sont inventés. Les résultats, les dessins, l'erreur de doublon et sa correction sont scénarisés. Aucun fichier ou calcul scientifique n'est produit. Les autres modules et les 36 éléments de référence ne sont pas reproduits individuellement : voir `REGISTRE.md`.

Contrôles effectués : `node --check` sur les deux scripts ; test DOM jsdom du parcours import avec champ manquant, confirmation, anomalie, aperçu/annulation/application, cas de profondeur incohérente et de déviation absente, simulation en cours et périmée, coupe, sélection partagée, masquage d'une couche sur la carte et des panneaux, retour à l'accueil. Le serveur local répond HTTP 200. Les tests DOM utilisent une simulation des dialogues et ne vérifient pas le rendu ni le clavier natif. Un précédent essai Chromium n'a pas démarré faute de bibliothèques système ; **aucune revue visuelle réelle dans un navigateur ni dans QGIS n'est revendiquée**. Le ZIP V1 n'a pas été modifié.

## Revue transversale

1. **Navigation et densité** : les cinq espaces sont accessibles directement par onglets, assistant facultatif et depuis l'accueil. Le rail, les onglets et l'assistant peuvent se répéter ; mesurer leur utilité avec de vrais utilisateurs avant conservation dans QGIS. Sur écran étroit les panneaux passent verticalement : tester si le nombre de défilements reste acceptable.
2. **Visibilité de l'espace de travail** : l'assistant et le contexte sont masquables, mais l'espace ne garde pas cette préférence après rechargement. Le prototype ne démontre pas la faisabilité des docks flottants QGIS.
3. **Import** : le mapping et les aperçus sont centraux, mais seul le scénario collets est détaillé. Les autres familles affichées ne sont pas fonctionnelles ; leurs structures, unités et exceptions devront être étudiées avant généralisation. Une association en double est signalée par la simulation, non par le moteur V1.
4. **Qualité et correction** : le détail est en ligne plutôt que modal ; l'historique n'existe qu'en mémoire. Le lien « Examiner » ouvre un aperçu de correction, pas l'enregistrement dans un véritable éditeur. La suggestion `DM-001 → DM-002` est un scénario fictif à confirmer ; ne jamais appliquer une telle correction automatiquement à des données réelles.
5. **Trajectoires** : méthode et dip signé reflètent la convention décrite dans la V1. La visualisation est indépendante des paramètres et n'est pas une trajectoire ; la divergence de secours 3D identifiée dans l'audit reste à investiguer dans QGIS. Le prototype ne permet pas de valider une méthode scientifique.
6. **Coupe et export** : seules la sélection de forage et la visibilité de la piste lithologie affectent le dessin. Le positionnement, l'orientation, les autres pistes, les couleurs et l'export sont des propositions ou états simulés, pas une coupe calculée. L'export ne crée pas de fichier. Une vraie prévisualisation nécessitera le moteur validé et les unités correctes.
7. **2D/3D** : le choix de forage est partagé dans les contrôles ; les filtres sont distincts selon la vue. Sur le schéma, le filtre et les couches agissent uniquement sur les symboles explicitement dessinés ; la sélection de cas DM-004 à DM-006 ne possède pas de symbole et déclenche une indication. La caméra 3D n'existe pas encore.
8. **Géoréférencement** : le projet d'exemple déclare EPSG:32629, mais tous les dessins sont indiqués comme schématiques et non géoréférencés. Les coordonnées exactes des collets ne doivent pas être déduites de leur position graphique.
9. **Lisibilité** : plusieurs textes secondaires ont été assombris. Contrast ratios, langues, focus, mise à l'échelle système, lecture d'écran et thèmes QGIS restent non mesurés. Les choix verts demeurent un arbitrage, pas un Design System de production approuvé.
10. **Synchronisation et invalidation** : la maquette marque périmés certains résultats lorsque leurs paramètres changent. Elle ne modélise pas toutes les dépendances réelles entre données, résultats, projets et scènes ; ne pas réutiliser cet état simulé comme contrat technique définitif.

## Décisions et questions à valider

- L'accès direct par cinq onglets doit-il remplacer ou compléter l'assistant et le rail ?
- Quels panneaux doivent être masqués par défaut sur écran portable ?
- La correction assistée doit-elle rester en ligne ou ouvrir un éditeur de données avec prévisualisation ?
- Quelles associations et familles nécessitent une interface spécialisée plutôt qu'un tableau générique ?
- Quels paramètres de coupe et de visualisation sont partagés, locaux ou enregistrés dans le projet ?
- À quel moment une donnée modifiée doit-elle invalider une trajectoire, une coupe, un cache ou un export ?
- Quels cas de forages, unités et conventions un géologue doit-il approuver avant un aperçu calculé ?
- Le vert foncé identifie-t-il suffisamment DrillMaster sans concurrencer les couleurs géologiques ?

Étapes avant extension : inspection réelle de l'aperçu, retours du propriétaire sur ces cinq espaces, tests clavier/contraste et revue scientifique. Aucune autorisation de développement du plugin n'est accordée par cette maquette.
