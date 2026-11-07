# DRILLMASTER — Registre des décisions

> Une décision est **immuable**. Une révision crée `D-xxx-bis` et laisse l'historique lisible.
> Statut : `proposée` · `entérinée` · `rejetée` · `remplacée`

| # | Décision | Portée | Statut | Source |
|---|---|---|---|---|
| **D-001** | **Plugin QGIS obligatoire** — jamais d'application autonome. Le châssis se conçoit dans les contraintes QGIS (docks autour du canevas, menu, barres). | Châssis | **entérinée** | ta réponse |
| **D-001.1** | Une seule arborescence de modules (8), **deux modes** : Guidé (assistant 4 étapes conservé) + Expert. Même code, seul le conteneur change. | UX | **entérinée** | 03 |
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
| **D-010** | **Ne pas supprimer la 3D legacy avant portage.** La 3D v2 a perdu : surface MNT, plan de coupe, structures, imagerie, géotechnique, gizmo. L'ancienne vue reste la référence fonctionnelle jusqu'à parité. | 3D | **entérinée** | 06 B1 |
| **D-011** | **Parité 3D obligatoire sur les 9 domaines** du contrat avant toute suppression. | 3D | **entérinée** | 06 B2 |
| **D-012** | Les noms de domaines **ne sont plus testés dans la vue** : le contrat fournit le domaine, la vue l'affiche par généricité. | 3D | **entérinée** | 06 B3 |
| **D-013** | Le modèle de scène 3D porte le style (opacité, largeur, côté, visibilité, ordre). | 3D, data | **entérinée** | 06 B4 |

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
| J0 | Audit d'apparence produit (doc 01), contrat de piste proposé (02), arborescence (03), états (04), organisation (05). 15 décisions proposées. |
