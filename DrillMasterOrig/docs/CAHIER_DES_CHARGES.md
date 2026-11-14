# DrillMaster ORIG — Cahier des charges (vivant)

CDC léger, versionné, mis à jour à chaque tranche. Une exigence sans
critère d'acceptation testable n'entre pas dans ce document.

## 1. Vision

L'alternative libre et maîtrisée à Micromine/Leapfrog pour le workflow
80 % du géologue de mine : importer, valider, visualiser, exporter.
Minimalisme maîtrisé (docs/DESIGN.md), confiance par preuve
(tests + auditabilité), zéro dépendance hors QGIS.

## 2. Utilisateurs cibles

- **Géologue de mine** : arrive avec des CSV (base de données forages),
  veut voir ses coupes en minutes, pas administrer un logiciel.
- **Géotechnicien** : logs géotech, structures, stérilité.
- **Chef de projet** : exportables auditables à mettre dans un rapport.

## 3. Périmètre v1.0

**Dedans :**
- Import CSV glisser-déposer, détection auto (collets, survey, logs
  codés, teneurs, structures, MNT)
- Validation par nature (socle + codé + quantitatif + QA/QC teneurs)
- Trajectoires 3D courbure minimale, recalcul réactif
- Coupes 2D : litho, alté, miné, teneurs classées, structures,
  profondeurs, grille/axes, légende, cartouche
- Vue 3D : trous colorés par domaine, topographie
- Projet QGIS (sauvegarde/chargement des réglages)
- Export PNG/SVG auditable (métadonnées complètes embarquées)
- Référentiel codes/symboles partagé entre vues

**Dehors (v1) — assumé :**
- Modélisation implicite RBF / iso-surfaces (lot MOD-1, post-v1)
- Estimation de ressources / variographie
- Édition de données (le v2 édite ; ORIG v1 reste lecture seule,
  l'édition retourne au CSV — décision TRUST)
- Multi-projets simultanés

## 4. Tranches et critères d'acceptation

| # | Tranche | Critère d'acceptation (testable) |
|---|---|---|
| 1 | Conventions + modèle + trajectoires | 8 tests, arc analytique au mm — **fait** |
| 2 | Validation par nature | 6 tests (socle, codé, assays QA/QC) — **fait** |
| 3 | Import CSV + détection auto | Un CSV assays réel (virgules FR, colonnes hétérogènes) → enregistrements + rapport de validation ; détection du type de fichier ≥ 90 % sur échantillon de jeux de test |
| 4 | Atelier 3 zones (squelette) | Rail données fonctionnel (drop → détection → validation affichée), vues commutables, checklist guidée optionnelle |
| 5 | Coupe 2D v1 | Une coupe litho+teneurs rendue, réglages persistés dans le projet QGIS |
| 6 | Export auditable | PNG contenant cartouche + métadonnées complètes relisibles |
| 7 | Vue 3D v1 | Trous 3D colorés par domaine, caméra libre |
| 8 | Parité de migration | Un projet v2 s'ouvre dans ORIG (réglages essentiels) |

## 5. Règles de gouvernance

- Une tranche commence quand la précédente a son critère vert.
- Toute nouvelle exigence entre au CDC avec son critère, sinon elle
  n'existe pas.
- Le CDC prime sur l'audit IA en cas de conflit ; il est mis à jour
  avec justification.

## 6. Risques connus

- **Périmètre qui gonfle** : la section « Dehors » est un engagement.
- **Parité v2** : le v2 reste l'outil de production tant qu'ORIG n'a pas
  la tranche 8 ; aucune migration forcée.
- **Dépendance QGIS** : le cœur reste pur ; toute fuite QGIS dans
  `core/` est une régression.
