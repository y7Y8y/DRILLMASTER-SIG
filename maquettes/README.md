# Maquettes — la refonte de DrillMaster en images

Tout est dessiné avec **Pillow** (aucune dépendance à QGIS, aucun rendu SVG à rastériser),
aux mêmes jetons de couleur que le code final. Deux fichiers :

| Fichier | Rôle |
|---|---|
| `ui.py` | Bibliothèque de composants : `Tokens` (thème clair) / `Dark`, classe `C` (rectangles, texte, pilules, cases, curseurs, tableaux, barres). Super-échantillonnage ×2. |
| `screens.py` | Les 9 écrans + les 2 variantes sombres. `python3 maquettes/screens.py`. |
| `planche.py` | La planche contact (toutes les images sur une seule page). `python3 maquettes/planche.py`. |

## Les écrans

| # | Écran | Ce qui est démontré |
|---|---|---|
| 1 | **Projet** | identité, référentiel spatial, bibliothèques (jamais réécrites), profils d'affichage par type d'ouvrage, santé du projet, dernières coupes, notes |
| 2 | **Données** | 12 types de sources, filtres par **niveau d'état**, détail à 5 champs (pourquoi / concerné / résoudre / si vous ignorez), journal des imports |
| 3 | **Géométrie** | méthode de calcul, pas d'échantillonnage, cache **signé**, contrôles de trajectoire, colonne « état » qui explique chaque écart |
| 4 | **Coupe 2D** | **l'écran clé** : un seul panneau de pistes (largeur, opacité, côté éditables sur chaque ligne), inclusion réglable, légende et règles de seuil |
| 5 | **Vue 3D** | surface MNT, 64 forages, corridor, barre caméra, gizmo, badge d'exagération Z, **arbre de calques** à 3 groupes façon ArcGIS |
| 6 | **Analyses** | rose des directions, stéréonet de Schmidt, intercepts et seuils, statistiques, distribution des teneurs |
| 7 | **Référentiel** | codes, familles, motifs, utilisation réelle en mètres, aperçu sur la coupe, règles de gamme vérifiées |
| 8 | **Export** | profils réutilisables, réglages (format / papier / échelle / résolution), **aperçu avant production**, historique avec échec explicité |
| 9 | **Mode Guidé** | 4 étapes, couverture des 12 types, ce que DrillMaster fait de vos fichiers, ce qui bloque l'étape suivante |

Variantes sombres : `04_coupe_2d_sombre.png`, `05_vue_3d_sombre.png` — mêmes jetons inversés,
**aucune couleur métier ne dépend du thème**.

## Règles tenues partout

* Un seul accent de marque (`#2E5BFF`) ; **4 couleurs sémantiques réservées aux états** (Information, Avertissement, Question, Blocage) + une neutre pour l'erreur technique.
* Aucun état n'est masqué : un domaine absent est **affiché absent**, jamais vide et silencieux.
* Un type non fourni est une **information**, pas une erreur.
* Aucune fenêtre modale pour une validation : le détail s'ouvre dans un panneau.
* Fond `#F6F7F9`, surfaces blanches, bords `#E4E7EC`, texte `#101828` / `#475467` / `#98A2B3`.

## Châssis

Format **1600 × 1000**, pensé pour un dock QGIS : la barre d'onglets fait 54 px, la barre
d'état 32 px ; tout le reste va au canevas. Navigation = **onglets horizontaux**
(7 modules : Projet · Données · Géométrie · Coupe 2D · Vue 3D · Analyses · Export),
décision produit révisable — c'est la variante A des deux proposées.
