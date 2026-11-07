# Maquettes — la refonte de DrillMaster en images

Tout est dessiné avec **Pillow** (aucune dépendance à QGIS, aucun rendu SVG à rastériser),
aux mêmes jetons de couleur que le code final. Deux fichiers :

| Fichier | Rôle |
|---|---|
| `ui.py` | Bibliothèque de composants : `Tokens` (thème clair) / `Dark`, classe `C` (rectangles, texte, pilules, cases, curseurs, tableaux, barres). Super-échantillonnage ×2. |
| `screens.py` | Les 9 écrans + les 2 variantes sombres. `python3 maquettes/screens.py`. |
| `planche.py` | La planche contact (toutes les images sur une seule page). `python3 maquettes/planche.py`. |
| `screens_v3.py` | Les 5 écrans de correction (`11` → `15`), puis `16_validation`. |
| `screens_v4.py` | Les 4 écrans neufs (`18` → `21`) : import, blocage, coupe finie, exclusions. |
| `planche_v4.py` | La planche contact des 4 écrans neufs → `22_planche_v4.png`. |

## Les écrans neufs (v4) — ceux qui répondent à « et le fonctionnel ? »

| # | Écran | Ce qu'il montre | D'où viennent les chiffres |
|---|---|---|---|
| 18 | **Importer un fichier** | zone de dépôt unique · 4 chiffres sur le fichier · 8 colonnes dont 2 à confirmer · **ce que l'import ne fait pas** · les 12 types avec 3 fournis et 9 absents affichés absents | 65 lignes, 1 doublon, 8 colonnes |
| 19 | **Un doublon, expliqué** | le blocage en une phrase · les 2 lignes avec leurs 2 numéros · pourquoi c'est grave en 25 mots · **3 sorties dont une recommandée** · motif obligatoire · **ce qui a déjà été vérifié avant de vous demander de décider** | ISBRC045, lignes 46 et 47 |
| 20 | **La coupe finie** | 14 forages, lithologie + barres de teneur, axes en altitudes, échelle de teneur fixe, **4 réglages seulement**, 2 forages écartés en pointillés | 14 forages, profondeurs 110 → 155 m |
| 21 | **Forages écartés** | une décision **valable partout**, avec motif, auteur, date, **réversible** · son journal · la même page en mode Guidé | 3 écartés sur 64, 214 analyses retirées |

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

---

# Corrections (J2) — après ta remarque

Tu as dit : mêmes problèmes, mauvaises catégories, éléments qui ne se partagent pas,
attributions fausses, plugin compliqué, termes incompréhensibles, pas de tests.
Chaque reproche a un écran :

| Reproche | Écran | Ce qui change |
|---|---|---|
| « mêmes trucs, mêmes problèmes » | `11_pistes.png` | la coupe n'a plus une liste plate de 12 lignes : **12 pistes en 4 familles**, une déclaration chacune |
| « les éléments qui se partagent pas » | `12_partages.png` | **un réglage, cinq lecteurs** (2D, 3D, légende, export, carte) ; chaque réglage a **un propriétaire** et aucune vue n'en garde une copie |
| « les mauvaises catégories / attributions » | `13_donnees_rangs.png` | 12 types en **3 rangs** ; les catégories (Saprolite, Latérite…) restent **avec leur type**, l'imagerie et les intercepts ne sont plus mélangés aux données |
| « on comprend pas les termes » | `14_message.png` + `15_etats.png` | une erreur racontée en trois phrases, avec **trois sorties** ; 5 états avec « ce qu'il veut dire » et « la suite », en voix Guidée et Experte |
| « pas eu des tests pour plusieurs cas » | `16_validation.png` | **17 cas d'usage** rejoués : projet vide, doublons, point-virgule, décimale, latin-1, forage horizontal, CRS, 500 forages, A1, sombre, zoom, contraste |

`10_planche_corrections.png` = les 6 écrans + la coupe corrigée sur une page.
Régénérer : `python3 maquettes/screens_v3.py` puis `python3 maquettes/planche_v3.py`.

## Ce qui a été supprimé de l'interface

* la liste plate des 10 pistes dans le panneau de coupe ;
* les doublons « largeur / opacité / côté » saisis piste par piste ;
* « Cellule à 2 codes litho », « Signature des entrées », « cache JSON », « a7f3c9… » et tout autre terme d'ingénieur ;
* les réglages 2D qui apparaissaient aussi dans les réglages 3D.
