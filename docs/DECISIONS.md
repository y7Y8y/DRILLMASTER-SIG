# DRILLMASTER — Registre des décisions

> Une décision est **immuable**. Une révision crée `D-xxx-bis` et laisse l'historique lisible.
> Statut : `proposée` · `entérinée` · `rejetée` · `remplacée`

| # | Décision | Portée | Statut | Source |
|---|---|---|---|---|
| **D-001** | **Plugin QGIS obligatoire** — jamais d'application autonome. Le châssis se conçoit dans les contraintes QGIS (docks autour du canevas, menu, barres). | Châssis | **entérinée** | ta réponse |
| **D-001.1** | ~~Guidé + Expert~~ → **remplacée par D-014**. Je n'aurais pas dû imposer ce choix seul : c'est une décision **produit**. | UX | **remplacée** | ta remarque |
| **D-002** | **Contrat de Piste** : 3 étages (global projet / commun 14 emplacements / spécifique), héritage Projet → Type → Piste. | Data, 2D, 3D, export | **entérinée** | [02](02_CONTRAT_PISTE.md) |
| **D-002.1** | Les pistes géotechniques rejoignent le magasin commun. | Data | **entérinée** | 02 §6 |
| **D-002.2** | La 3D lit les **mêmes** réglages que la 2D. | 3D | **entérinée** | 02 §6 |
| **D-002.3** | Seules exceptions 2D/3D : `side` et `width` → champs distincts, **pas** deux magasins. | 3D | **entérinée** | 02 §6 |
| **D-002.4** | Réglages 3D **par projet** ; le global ne garde que caméra et thème. | 3D, data | **entérinée** | 02 §6 |
| **D-002.6** | Une piste non affichable dans une vue est **annoncée**, jamais silencieuse. | UX, 3D | **entérinée** | 02 §6 |
| **D-003** | **5 niveaux d'état**, dont **erreur technique**. | Validation, UX | **entérinée** | [04](04_ETATS.md) |
| **D-003.1** | Tout message porte 5 champs : niveau, pourquoi, concerné, résoudre, portée. | Validation | **entérinée** | 04 §2 |
| **D-003.2** | Aucune `QMessageBox` pour une validation : panneau de détail. | UX | **entérinée** | 04 §3 |
| **D-004** | **Filet de test obligatoire avant les maquettes** : harnais `core/`, projet de référence figé, coupes témoins. | Qualité | **entérinée** | [05](05_ORGANISATION.md) |
| **D-005** | Suppression du code inatteignable — **mais seulement après portage** (voir D-010). | Architecture | **révisée** | [06](06_RAPPORT_AGENTS.md) |
| **D-006** | **Un seul moteur de motifs**, les deux DEPRECATED disparaissent. | 2D, données | **entérinée** | 01 |
| **D-007** | **Mode sombre** conçu sur les mêmes tokens, pas une inversion. | DA | **entérinée** | 05 |
| **D-008** | **4 couleurs sémantiques réservées aux états** ; l'accent de marque n'exprime jamais un état. | DA | **entérinée** | 04 §3 |
| **D-009** | Logique de spécification : fiche à 9 rubriques, critère d'acceptation obligatoire. | Pilotage | **entérinée** | 05 §5 |
| **D-010** | **La 3D legacy n'est PAS conservée.** Elle est un **donneur temporaire** : on en extrait les capacités manquantes (surface MNT, corridor, structures, imagerie, géotechnique), on les réécrit dans `core/scene3d`, puis **on la supprime**. Aucune ligne de son rendu ni de son panneau ne survit. | 3D | **révisée** | ta remarque |
| **D-010.1** | **L'esthétique de la 3D legacy est rejetée** : ni son panneau de `QGroupBox` à cases empilées, ni son rendu. Seules ses **algorithmes métier** sont récupérés. | 3D, DA | **entérinée** | ta remarque |
| **D-014** | **Navigation = décision produit, pas technique.** Deux options présentées en images (A : onglets horizontaux / B : rail vertical). Le choix t'appartient ; l'implémentation suit, quel qu'il soit. | UX | **à trancher par toi** | maquettes ci-jointes |
| **D-015** | **Panneau de calques de la 3D** : la 3D adopte un **arbre de jeux de données** (groupes + cases à cocher + pastille de couleur), comme la référence ArcGIS — pas une pile de cases. | 3D, UX | **entérinée** | ta référence |
| **D-011** | **Parité 3D obligatoire sur les 9 domaines** du contrat avant toute suppression. | 3D | **entérinée** | 06 B2 |
| **D-012** | Les noms de domaines **ne sont plus testés dans la vue** : le contrat fournit le domaine, la vue l'affiche par généricité. | 3D | **entérinée** | 06 B3 |
| **D-013** | Le modèle de scène 3D porte le style (opacité, largeur, côté, visibilité, ordre). | 3D, data | **entérinée** | 06 B4 |
| **D-016** | **Navigation = onglets horizontaux** (variante A) : 7 modules `Projet · Données · Géométrie · Coupe 2D · Vue 3D · Analyses · Export` + `Référentiel` et `Mode Guidé` en accès secondaire. Appliquée dans les maquettes parce qu'un rail vertical mange le canevas dans un dock QGIS. **Révisable** : si tu préfères la variante B, seule la barre change. | UX | **appliquée, révisable** | maquettes |

| **D-017** | **Le contrat de piste remplace la liste plate.** Les pistes sont rangées en **4 familles** — *structurelles* (Profondeurs, Trajectoire, Intercepts), *catégorielles* (Lithologie, Altérations, Minéralisations, Structures), *quantitatives* (Teneurs, RQD, Récupération, Densité), *médias* (Imagerie). La famille porte les valeurs ; la piste les hérite et peut les forcer. **Fini les 10 lignes à égalité** et les réglages répétés. | Paramètres, 2D | **entérinée** | maquette 11 | 
| **D-018** | **Trois rangs de données, et des catégories qui restent à leur type.** Rang 1 *socle* (collets, déviations, topographie, profils d'ouvrage) — lu, jamais recalculé. Rang 2 *observé* (lithologie, altérations, minéralisations, structures, teneurs, imagerie) — les catégories sont nommées par l'utilisateur et vivent au Référentiel de **leur** type. Rang 3 *calculé* (RQD, récupération) — déduit, jamais importé en direct. **Intercepts, RQD, récupération, densité, imagerie ne sont plus des « types de données » mélangés aux autres : ce sont des pistes ou des calculs.** | Données, paramètres | **entérinée** | maquettes 13 et 11 |
| **D-019** | **Un seul jeu de mots pour tout le monde.** Chaque état dit : *ce qui se passe*, *ce que vous pouvez faire*, *si la suite continue*. Deux voix (Guidée = phrases courtes, Experte = détail) partagent **exactement le même vocabulaire de niveau** (Information · Avertissement · Question · Blocage · Erreur technique). Aucun jargon d'ingénieur dans l'interface : ni « clé », ni « signature », ni « contrat ». | UX, langue | **entérinée** | maquettes 14 et 15 |
| **D-020** | **17 cas d'usage rejoués à chaque modification** (projet vide, projet complet, types manquants, doublons, séparateur, décimale, encodage, forages inclinés et horizontaux, pendage inversé, CRS du MNT, MNT absent, 500 forages, export A1, sombre, zoom 400 %, contraste). Un cas qui ne passe pas bloque la livraison. | Qualité | **entérinée** | maquette 16 |
| **D-021** | **Écran « Pistes » dédié** (Coupe 2D → Pistes) : la liste des 12 pistes avec visibilité, largeur, opacité, côté ; le détail d'une piste montre *commune à toutes / propre à sa famille / où le réglage s'applique*. Le panneau de la coupe ne contient plus que 3 familles + 4 réglages de coupe. | 2D, UX | **appliquée** | maquettes 11 et 7 |

---

## Questions restantes

**Aucune bloquante.** Les 5 questions précédentes sont tranchées :
1. Contrat de piste (D-002) → **adopté**, c'est la forme validée.
2. Guidé + Expert (D-001.1) → **adopté** : on garde le parcours qui fonctionne.
3. Tests avant maquettes (D-004) → **adopté** : le filet est construit en phase 2.
4. Périmètre 3D (D-011) → **parité complète** sur les 9 domaines. Une seule vue 3D, pas deux.
5. Châssis (D-001) → **plugin QGIS**, verrouillé.

**Seules questions qui resteront ouvertes** (elles se poseront en phase 4, pas maintenant) :
le nom exact des 8 modules dans l'interface, et le choix typographique final (deux familles candidates, présentées avec des rendus).

---

## Journal

| Date | Événement |
|---|---|
| J2 | **Corrections après ta remarque** : contrat en 4 familles, rangs de données, message explicable, 2 voix d'états, 17 cas de validation. `maquettes/10_planche_corrections.png`. |
| J1 | **Jeu complet de maquettes** (9 écrans + 2 variantes sombres + planche contact) : `maquettes/*.png`, D-016 appliquée. |
| J0 | Audit d'apparence produit (doc 01), contrat de piste proposé (02), arborescence (03), états (04), organisation (05). 15 décisions proposées. |
