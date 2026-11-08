# Registre de couverture V1 — itération cinq espaces

Statuts : **simulé partiellement** = uniquement le scénario décrit, pas une fonctionnalité QGIS ; **repéré** = accès, nom ou contexte affiché sans parcours complet ; **non maquetté** = réservé pour plus tard. Aucun statut ne signifie suppression ou remplacement d'une fonction V1. Le catalogue des 36 éléments reste dans `../docs/specifications-future-version.md` et `../docs/inventaire-statique.md` ; cette itération ne les reproduit pas individuellement.

| Domaine de référence | Couverture dans cette itération | Limites / suite |
|---|---|---|
| F01 Projet | Repéré : projet fictif, SCR déclaré, accès au contexte. | Création, ouverture, sauvegarde, réinitialisation et préférences non maquettées en profondeur. |
| F02 Import/mapping | Simulé partiellement : collets, mapping, aperçu, erreurs prédéfinies, confirmation/annulation. | Pas de vrai fichier, pas de détection automatique ; autres familles non traitées. |
| F03 Collets/déviations | Partiellement simulés : identifiants, collet, azimut/dip et scénarios de déviation. | Import des déviations et choix des conventions non opérationnels. |
| F04 Lithologie | Repérée dans le schéma de coupe et les familles. | Organisation, proportions et référentiel non maquettés. |
| F05 Teneurs | Repérées dans les familles et pistes. | Mapping, unités, classes et seuils non maquettés. |
| F06 Altérations/minéralisations | Repérées comme familles/pistes. | Règles et organisation spécifiques non maquettées. |
| F07 Structures | Repérées comme famille/piste. | Formulaires et règles d'orientation non maquettés. |
| F08 Géotechnique/imagerie | Repérées dans les familles. | RQD, récupération, densité et visualiseur d'images non maquettés. |
| F09 Géométrisation | Simulation d'états et cas limites, sans calcul réel. | Méthode, résultats et trajectoire nécessitent validation scientifique/QGIS. |
| F10 Couches/persistance | Options de couches illustratives en mémoire ; contexte de projet. | Pas de couches QGIS, stockage, cache ni GeoPackage. |
| F11 Coupes/pistes | Choix de forages, réglages, aperçu graphique schématique et états simulés. | Pas de tracé sur vraie carte, ni calcul de projection ou rendu fidèle des domaines. |
| F12 Surface/topographie | Mentionnée dans le périmètre du projet. | Pas d'outil raster, MNT, topographie ou échantillonnage. |
| F13 Visualisation 3D | Schéma statique et navigation de vues, sélection partagée simulée. | Pas de scène géométrique ni interaction caméra réelle. |
| F14 Export | Action simulée, confirmation qu'aucun fichier n'est créé. | Aucun dialogue complet, échelle papier ou fichier produit. |
| F15 Analyse structurale | Famille structure repérée. | Rosace et stéréonet non maquettés. |
| F16 Référentiel/profils | Repérés dans les textes de contexte. | Éditeurs, palettes, profils et exceptions non maquettés. |
| F17 Cycle de vie/langue/aide | Aide et Design System dans le tableau de bord. | Pas de cycle QGIS, langues ou aide métier détaillée. |

Dans les cinq espaces eux-mêmes, les boîtes de dialogue spécifiques, états de reprise persistants, données réelles et scénarios scientifiques exhaustifs restent à concevoir et tester. Le registre doit évoluer avec les observations QGIS et l'accord du propriétaire.
