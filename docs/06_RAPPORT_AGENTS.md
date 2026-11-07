# 06 — Rapport des 36 agents d'audit

> **Généré par `tools/audit/agents.py`** — rejouable à tout moment : `python3 tools/audit/agents.py`
> Sorties brutes : `audit/reports/*.json` (une fiche par agent, avec preuves).
> 36 agents · constats : 9 bloquants · 37 majeurs · 30 moyens · 11 mineurs.

---

## Note par direction (calculée, pas déclarée)

| Score | Direction | Agents | Lecture |
|---:|---|---:|---|
| **3,0** | **Paramètres** | 5 | Le contrat de piste n'existe pas. C'est la racine de tout le reste. |
| **4,8** | **Architecture** | 4 | 13,8 % du code est inatteignable ; monolithe de 10 335 lignes. |
| **4,8** | **Vue 3D** | 4 | La 3D v2 est une **régression fonctionnelle**, pas une amélioration. |
| 6,9 | Qualité | 4 | 0 test exécutable. |
| 7,3 | Langue & doc | 2 | 3 documents cités, 0 présents. |
| 7,5 | Coupe 2D | 4 | Fonctionnelle, mal hiérarchisée. |
| 8,0 | Validation | 4 | Bonne base (4 niveaux, regroupement), il manque le 5ᵉ. |
| 8,7 | Interactions | 3 | 1 101 libellés, 10 raccourcis. |
| 9,3 | Géologie | 2 | Le métier est sain. |
| 9,3 | Export | 2 | Complet, dispersé. |
| 9,5 | Données de référence | 2 | Litho/altéro OK, aucun hex partagé. |

---

## LES 9 CONSTATS BLOQUANTS

### B1 · La 3D v2 a **supprimé** la surface topographique — `D6.1`

| | Ancienne 3D | Nouvelle 3D v2 |
|---|---|---|
| Surface MNT | **39 références** | **0** |
| Plan de coupe / corridor | 14 | **0** |
| Structures (89) | **89** | **0** |
| Imagerie | 65 | **0** |
| Géotechnique | 40 | **0** |
| Gizmo / boussole | 15 | 0 |
| Lignes de code | 6 889 | 1 762 |

**Ce que ça veut dire concrètement :** la vue 3D que l'utilisateur voit aujourd'hui **n'a plus de sol**. Un géologue ouvre la 3D et voit des tubes flottant dans le vide — alors que la coupe 2D, à côté, affiche une ligne de sol soignée. Ce n'est pas une « simplification assumée » : c'est une perte de fonctionnalité non annoncée.

**Correction :** porter `view_3d_surface.py` + `raster_surface.py` dans `core/scene3d` avant de supprimer l'ancienne vue. Supprimer l'ancienne **maintenant** serait une faute.

### B2 · 3 domaines affichables sur 9 — `D6.1`
Profondeurs, minéralisations, structures, imagerie, intercepts, géotechnique : **absents**. Aucun message ne le dit.

### B3 · Noms de domaines codés en dur dans la 3D — `D6.1`
```python
ui/view_3d_v2.py:31   LANES = {"Lithologie": (0.0, 1.1), "Altération": (-2.6, 0.8)}
ui/view_3d_v2.py:165  if name == "Lithologie": ...
ui/view_3d_v2.py:530  dom_key = "lithology" if name == "Lithologie" else "alteration"
```
Ajouter une 3ᵉ catégorie (minéralisation…) **oblige à modifier le code**. Ce n'est pas un moteur, c'est un cas particulier.

### B4 · Le modèle 3D ne transporte aucun style — `D6.2`
`IntervalTable(name, kind, hole, d0, d1, value, categories)` : **ni opacité, ni largeur, ni côté, ni visibilité, ni ordre**. Le rendu décide seul.

### B5 · Trois magasins de réglages pour une seule vue — `D4.3`
`config.json` (projet) + `QSettings` (machine) + magasin ad hoc géotech.

### B6 · Les réglages 3D sont globaux, pas projet — `D4.4`
7 réglages en `QSettings`. Tu changes de projet : la 3D garde les réglages du précédent.

### B7 · Les 3 pistes géotechniques sont hors du modèle — `D4.5`
`show_rqd`, `rqd_width`, `show_recovery`, `show_density` : **absents de `core/project.py`**. Réglables nulle part où l'utilisateur les cherche.

### B8 · 13,8 % du code est inatteignable — `D2.1`
7 808 lignes, sur 20 fichiers : `view_3d*.py` (10 fichiers, 6 889 l.), `raster_surface.py` (496), `overlay_layout.py` (59), 7 scripts `tools/`. **Aucun chemin d'import** depuis `__init__.py`.

### B9 · 0 test exécutable — `D10.1`
7 scripts, 363 lignes : chemins `/home/…` en dur, **aucun `assert`**. Ils impriment, ils ne vérifient pas.

---

## Les constats majeurs, par thème

**Monolithe** — `SectionCanvas` : 122 méthodes / 5 040 lignes. `SectionWidget` : 172 méthodes / 5 295 lignes. Un fichier = 20 % du projet.

**Contrat de piste** — 4 pistes sur 8 ont un contrat partiel : `trajectory` (pas d'opacité, pas de côté), `depth` (pas de largeur), `litho` (pas de côté), `assays` (largeur nommée `assay_max_width`). **Couverture 83 %**, jamais 100 %.

**Nommage** — 6 radicaux incohérents : `alter_width` / `mineral_side` au lieu de `alteration_*` / `mineralization_*`.

**Hiérarchie** — 7 groupes racine, 3 sous-groupes → un seul niveau de repli utile. `_build_assay_group` : 213 lignes. `_build_threshold_group` : 207 lignes.

**Surface de commandes** — **1 101 chaînes distinctes**, 10 raccourcis clavier, 31 `QMessageBox` bloquantes.

**États** — 4 niveaux, pas de 5ᵉ (erreur technique) ; 98 messages de validation en texte libre sans « pourquoi / comment résoudre ».

**Documentation** — 3 documents cités dans le code (`PLAN_LANGUE.md`, `DICO_TERMES_FR_EN.md`, `PROPOSITION_EXCLUSION_FORAGES_2D.md`) : **0 présent**. Aucun README, aucun CHANGELOG.

---

## Ce qui va bien (et qu'il ne faut pas casser)

- **Géologie 9,3/10** : conventions documentées (dip signé, azimut nord), contrôles croisés existants.
- **Données de référence 9,5/10** : 30 familles litho, 27 altérations, **aucun hex partagé** entre les deux palettes (vérifié par calcul d'intersection).
- **Validation 8,0/10** : regroupement par type d'erreur, comptes exacts, 4 niveaux déjà modélisés.
- **Export 9,3/10** : PNG, SVG, PDF paginé, A4→A1, échelle fixe.
- **Séparation noyau/UI** : 5 ponts Qt assumés et documentés, pas de fuite anarchique.

---

## Les 6 faux positifs que mes agents ont produits — et que j'ai corrigés

Un audit qui se trompe discrédite tout le reste. Voici ce que j'ai retiré :

| Constat initial | Pourquoi c'était faux | Correction apportée |
|---|---|---|
| « 10 fichiers 3D legacy morts » | `view_3d.py` n'était pas dans la liste | Analyse d'**atteignabilité** depuis le point d'entrée : 20 modules, 7 808 lignes |
| « 122 accès sur 3 magasins » | Comptage d'occurrences, pas de magasins | Comptage par magasin réel : **3 magasins** |
| « 1 373 commandes » | Occurrences, pas libellés distincts | **1 101 libellés distincts** |
| « 10 groupes racine » | Regex cassée sur saut de ligne | AST : **7 racines, 3 sous-groupes** |
| « 5 attributs morts » (`alter_width`…) | Testais le mauvais radical | Test de complétude : **4 pistes sur 8 partielles** |
| « `fr.ts` : 2 489 messages vides » | Le fichier fait 409 octets et **documente** qu'il est vide volontairement | Retiré. Le vrai défaut est ailleurs (aucun README) |

**Un constat de plus, que je n'avais pas vu au premier audit et qui est le plus grave :** la 3D v2 a **perdu la surface MNT, les structures, l'imagerie, la géotechnique et le plan de coupe**. C'est le constat B1. Il change la stratégie : on ne peut pas supprimer l'ancienne 3D avant d'avoir porté ces fonctionnalités.
