# DRILLMASTER — Registre des décisions

> Une décision est **immuable**. Une révision crée `D-xxx-bis` et laisse l'historique lisible.
> Statut : `proposée` · `entérinée` · `rejetée` · `remplacée`

| # | Décision | Portée | Statut | Source |
|---|---|---|---|---|
| **D-001** | Une seule arborescence de modules (8), deux modes de navigation (Guidé / Expert). L'assistant 4 étapes est conservé comme mode Guidé. | UX, navigation | proposée | [03](03_ARBORESCENCE.md) |
| **D-001.1** | Mode mémorisé par projet, bascule sans perte d'état. | UX | proposée | 03 |
| **D-002** | **Contrat de Piste** : 3 étages (global projet / contrat commun 14 emplacements / spécifique déclaré), héritage Projet → Type → Piste. | Data, 2D, 3D, export | proposée | [02](02_CONTRAT_PISTE.md) |
| **D-002.1** | Les pistes géotechniques (RQD, récupération, densité) rejoignent le magasin commun. | Data | proposée | 02 §6 |
| **D-002.2** | La 3D lit les **mêmes** réglages que la 2D. | 3D | proposée | 02 §6 |
| **D-002.3** | Seules exceptions 2D/3D : `side` (3D tourne) et `width` (px écran vs rayon monde) → champs distincts, **pas** deux magasins. | 3D | proposée | 02 §6 |
| **D-002.4** | Réglages 3D **par projet**. Le global ne garde que caméra et thème. | 3D, data | proposée | 02 §6 |
| **D-002.6** | Une piste non affichable dans une vue est **annoncée**, jamais silencieuse. | UX, 3D | proposée | 02 §6 |
| **D-003** | **5 niveaux d'état** (information, attention, question, blocage métier, **erreur technique**). | Validation, UX | proposée | [04](04_ETATS.md) |
| **D-003.1** | Tout message porte 5 champs obligatoires : niveau, pourquoi, concerné, résoudre, portée. Un message sans « pourquoi » ou « résoudre » est invalide. | Validation | proposée | 04 §2 |
| **D-003.2** | Aucune `QMessageBox` pour une validation : panneau de détail, jamais de popup. | UX | proposée | 04 §3 |
| **D-004** | **Filet de test obligatoire avant les maquettes** : harnais `core/`, projet de référence ivoirien figé, 3 coupes témoins. | Qualité | proposée | [05](05_ORGANISATION.md) |
| **D-005** | **Suppression du code mort** au livrable : vue 3D legacy (9 fichiers), `mesh_builder`, `camera3d`, `benchmark`, `ui_audit`, `geo_style`, `pattern_paint`, `drillmaster_fr.ts`. −7 778 lignes. | Architecture | proposée | 01, 05 |
| **D-006** | **Un seul moteur de motifs** (chemin actif actuel), les deux moteurs DEPRECATED disparaissent. | 2D, données | proposée | 01 |
| **D-007** | Le **mode sombre** est conçu à partir des mêmes tokens que le clair (pas une inversion). | DA | proposée | 05 |
| **D-008** | Les **4 couleurs sémantiques** sont réservées aux états ; l'accent de marque n'exprime jamais un état. | DA | proposée | 04 §3 |
| **D-009** | **Décalage de phases corrigé** : contrat de paramètres (1) et filet de test (2) **avant** maquettes (4). | Pilotage | proposée | 05 §4 |

---

## Décisions à trancher en priorité (bloquantes pour la suite)

| # | Question | Pourquoi c'est bloquant |
|---|---|---|
| **Q1** | D-002 : le contrat de piste (14 emplacements, héritage à 3 niveaux) est-il la bonne forme ? | Décide la forme de **toutes** les maquettes de panneaux |
| **Q2** | D-001 : Guidé + Expert, ou Expert seul ? | Décide la navigation entière |
| **Q3** | D-004 : acceptes-tu la porte « tests avant maquettes » (2 à 3 jours de travail non visible) ? | Sans filet, chaque maquette devient une régression invisible |
| **Q4** | Périmètre 3D : les 9 pistes doivent-elles **toutes** être affichables en 3D, ou certaines restent-elles 2D par nature ? | Décide l'effort D6 (×3 si tout doit passer) |
| **Q5** | Le plugin doit-il rester un **plugin QGIS** (docks autour du canevas) ou devenir une **application autonome** lisant les formats QGIS ? | Décide tout le châssis de fenêtres — la plus lourde des cinq |

---

## Journal

| Date | Événement |
|---|---|
| J0 | Audit d'apparence produit (doc 01), contrat de piste proposé (02), arborescence (03), états (04), organisation (05). 15 décisions proposées. |
