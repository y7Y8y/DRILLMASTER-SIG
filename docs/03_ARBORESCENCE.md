# 03 — Nouvelle arborescence fonctionnelle

> **Décision D-001.** Remplace les 7 groupes plats du panneau coupe et les 4 étapes de l'assistant.
> Principe : **une seule arborescence de modules**, deux façons de la traverser (Guidé / Expert).

---

## 1. Le diagnostic de l'existant

Aujourd'hui, un géologue doit savoir **où** est un réglage pour le trouver. Exemple réel : la largeur de la piste lithologie est dans *Pistes → Lithologie → Largeur*, la largeur de la piste RQD est dans *Pistes → Géotechnique* mais stockée ailleurs, la couleur de la lithologie n'est **pas** dans le panneau (elle est au Référentiel), et l'opacité globale de la coupe n'existe pas.

**Trois logiques concurrentes :** par objet (Pistes), par zone d'écran (Affichage de la coupe), par donnée (Topographie, Légendes). L'utilisateur ne peut pas deviner laquelle s'applique.

---

## 2. L'arborescence cible

```
DRILLMASTER
│
├── 1 · PROJET
│   ├── Identité (nom, auteur, dossier, dates)
│   ├── Référentiel spatial (CRS, unités, zone, convention de pendage)
│   ├── Bibliothèques (lithologie, altération, minéraux — édition)
│   ├── Profils d'affichage (types d'ouvrage RC/DD, AUGER, PUITS, CUSTOM)
│   └── Sauvegarde · restauration · archivage
│
├── 2 · DONNÉES
│   ├── Sources (12 types : collets, déviations, litho, teneurs, altérations,
│   │            minéralisations, structures, imagerie, RQD, récupération,
│   │            densité, topographie)
│   ├── Correspondances de colonnes (mappings appris, par source)
│   ├── Organisation (large / long / délimité, questions en attente)
│   ├── Validation (5 niveaux — voir doc 04)
│   └── Journal des imports (qui, quand, quoi, quelle version)
│
├── 3 · GÉOMÉTRIE
│   ├── Trajectoires (méthode, pas d'échantillonnage, subdivision)
│   ├── Contrôles de trajectoire (dérive, incohérences, hors-collet)
│   ├── Cache et recalcul (signature des entrées)
│   └── Emprise (bounds 3D, zones détectées, groupes de collets partagés)
│
├── 4 · COUPE 2D
│   ├── Ligne de coupe (tracé, orientation, longueur, buffer)
│   ├── Inclusion des forages (règle + exclusions nommées)
│   ├── Pistes  ←──────────────── LE CONTRAT (doc 02)
│   │   ├── Profondeurs      ├── Teneurs        ├── Structures
│   │   ├── Lithologie       ├── Intercepts     ├── Imagerie
│   │   ├── Altérations      ├── RQD            ├── Récupération
│   │   ├── Minéralisations  └── Densité
│   │   └── + Vue d'ensemble (tableau : 10 lignes × 14 colonnes)
│   ├── Cadre & axes (échelle, grille, fenêtre d'élévation, cartouche)
│   ├── Topographie (source MNT/CSV/collets, ancrage, QC)
│   └── Légendes (composition, ordre, visibilité)
│
├── 5 · VUE 3D
│   ├── Scène (zones, caméra, presets, exagération Z)
│   ├── Pistes 3D  ←──────────────── LE MÊME CONTRAT
│   ├── Surface (MNT, contours, couleurs hypsométriques)
│   ├── Coupe dans l'espace (plan + corridor)
│   └── Performance (budget de segments, qualité, rendu asynchrone)
│
├── 6 · ANALYSES
│   ├── Structures (rose des directions, stéréonet, densité de pôles)
│   ├── Intercepts (règles de seuil, multi-clauses, filtre litho)
│   ├── Statistiques de teneurs (par élément, par domaine, par zone)
│   └── Contrôles qualité (couverture, cohérence, lacunes)
│
├── 7 · EXPORT
│   ├── Coupe 2D (PNG, SVG, A4→A1, PDF, échelle fixe)
│   ├── Vue 3D (capture, série de vues)
│   ├── Données (GeoPackage, CSV dérivés — jamais les sources)
│   └── Cartouche & métadonnées (auteur, projet, date, SCR, échelle)
│
└── 8 · AIDE
    ├── Démarrage rapide
    ├── Glossaire FR/EN
    └── À propos · diagnostic · journal
```

**8 modules, 1 concept chacun.** Aucun réglage n'appartient à deux modules.

---

## 3. Les deux modes de navigation (la réponse à « débutant / expert »)

**Mode Guidé** — l'assistant actuel est **conservé**, pas jeté :

```
Projet → Données → Géométrie → Coupe
```
Il reste le parcours par défaut à l'ouverture d'un projet vide. Chaque étape valide avant de passer à la suivante. C'est ce qui accueille un débutant.

**Mode Expert** — l'arborescence complète, en 8 modules :

```
[Projet] [Données] [Géométrie] [Coupe 2D] [Vue 3D] [Analyses] [Export]
```
Accessible par un sélecteur unique (le stepper devient un onglet de modules). Aucune validation bloquante : tout est atteignable, l'état de chaque module est indiqué par un point de statut.

**Ce qui change concrètement :** les mêmes widgets, les mêmes builders, le même code. Seul **le conteneur** change — un `QStackedWidget` en mode Guidé, un `QTabWidget` de modules en mode Expert. Pas de double codebase.

**Décision D-001.1 :** le mode est mémorisé par projet, et bascule instantanément sans perdre l'état.

---

## 4. La règle de placement (pour trancher les futurs réglages)

> **Un réglage appartient au module qui possède la donnée qu'il modifie.**

| Question | Module |
|---|---|
| « La couleur du granite » | 1 Projet → Bibliothèques (c'est une donnée métier) |
| « L'opacité de la piste lithologie » | 4 Coupe 2D → Pistes (c'est une vue) |
| « Le rayon du tube en 3D » | 5 Vue 3D → Pistes 3D (c'est une vue 3D) |
| « Le pas des graduations de profondeur » | 4 Coupe 2D → Pistes → Profondeurs |
| « La méthode de calcul de trajectoire » | 3 Géométrie (c'est un calcul) |
| « L'échelle 1:N de la coupe » | 4 Coupe 2D → Cadre & axes (avec un override au niveau Projet si échelle commune) |

Cette règle est vérifiable automatiquement : chaque clé de paramètre déclare son module propriétaire, et un test refuse une clé sans propriétaire unique.

---

## 5. Ce que l'arborescence supprime

| Existant | Sort |
|---|---|
| Groupe « Affichage de la coupe » (149 lignes de builder) | Éclaté en *Cadre & axes* + *Annotations* + *Topographie* selon la règle §4 |
| Groupe « Historique des coupes » (dans le panneau coupe) | → module 4, en haut, comme sélecteur de coupe (pas un groupe de réglages) |
| Onglet « Interprétation » (déjà retiré en v2.9.210) | Reste hors périmètre. S'il revient : module 6, sous « Corrélations proposées » |
| Vue 3D legacy (7 778 lignes) | Supprimée du livrable |
| `geo_style` / `pattern_paint` (DEPRECATED, encore importés) | Supprimés, un seul moteur de motifs |
| `drillmaster_fr.ts` (2 489 messages vides) | Supprimé du livrable |
