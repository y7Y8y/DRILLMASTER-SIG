# Jeu de forage fictif — WGS 84 / UTM zone 29N

**Données entièrement inventées**, pour des essais logiciels uniquement : ni données de terrain, ni interprétation géologique, ni estimation de ressources. Coordonnées en mètres dans **EPSG:32629 — WGS 84 / UTM zone 29N** ; X = est, Y = nord, Z = altitude fictive en mètres. Sélectionner explicitement EPSG:32629 lors de la configuration du projet : les CSV ne contiennent pas eux-mêmes de CRS. Attention : la V1 propose EPSG:32630 par défaut, qui ne convient pas à ce jeu. Les profondeurs sont des longueurs mesurées le long du forage en mètres. Azimut en degrés depuis le nord vers l'est ; inclinaison signée en degrés, négative vers le bas, conformément à la convention du code de cette V1. Les valeurs et unités de teneur sont fictives : Au en ppm et Cu en pourcentage.

## Utilisation

Dans un nouveau projet DrillMaster de test, importer les quatre fichiers du dossier `normal` dans les familles correspondantes : collets, déviations, lithologie et teneurs. Vérifier les associations de colonnes et le CRS proposés avant de poursuivre. Les codes de lithologie sont inventés à des fins de test : les associer au référentiel si nécessaire, sans supposer qu'ils soient reconnus automatiquement. La reconnaissance automatique dans l'interface et le rendu n'ont pas été vérifiés dans QGIS.

Ces données contiennent trois forages droits, dont un vertical. Elles permettent de tester l'import, les trajectoires, quelques intervalles et une coupe proche de la ligne des collets. Elles ne couvrent pas les trajectoires courbes, les autres familles, l'export ou toutes les limites scientifiques ; elles devront être complétées progressivement.

## Repères indépendants pour les trajectoires

Pour un forage rectiligne de longueur L, d'azimut A et de pendage D : ΔX = L cos(D) sin(A), ΔY = L cos(D) cos(A), ΔZ = L sin(D). Ainsi, à la profondeur finale :

| Forage | X attendu (m) | Y attendu (m) | Z attendu (m) |
|---|---:|---:|---:|
| DM-001 | 500000.000 | 800000.000 | 100.000 |
| DM-002 | 500170.711 | 800000.000 | 139.289 |
| DM-003 | 500200.000 | 800060.000 | 101.077 |

Ces résultats sont arrondis au millimètre ; comparer avec une tolérance raisonnable (par exemple 0,01 m). Ils ne constituent pas une validation générale de l'algorithme pour les forages déviés.

## Cas d'erreur séparés

Ne pas mélanger ces fichiers au jeu normal. `erreurs/collets_doublon.csv` contient un identifiant en double. `erreurs/deviations_invalides.csv` s'utilise avec les collets normaux : station au-delà de la profondeur, identifiant inconnu et azimut hors plage. Ces fichiers servent à observer les messages et la correction, pas à générer un projet de production.

## Vérification effectuée

Le parseur et les fonctions de validation Python de l'archive 2.9.394 ont été exécutés directement, hors QGIS : les quatre fichiers normaux n'ont produit ni erreur ni avertissement de validation ; les deux jeux d'erreur ont produit respectivement les codes `DUPLICATE_HOLE_ID`, puis `SURVEY_BEYOND_HOLE_DEPTH`, `UNKNOWN_HOLE_ID` et `AZIMUTH_OUT_OF_RANGE`. Les coordonnées finales calculées par le moteur correspondent aux valeurs ci-dessus à l'arrondi indiqué. Ceci ne vérifie pas l'interface, les exports, les CRS dans QGIS ni l'exactitude scientifique d'autres situations.
