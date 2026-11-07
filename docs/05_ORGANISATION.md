# 05 — Organisation du chantier

> Ce document rend le travail **vérifiable**. Il ne prétend pas que des milliers d'agents tournent en parallèle : il décrit une équipe de conception organisée par responsabilités, avec des livrables contrôlables et un critère d'acceptation par livrable.

---

## 1. Structure (12 directions, pas 10)

Ta note en proposait 10. J'en ajoute 2 qui manquent cruellement au vu du code :

| # | Direction | Responsabilité | Livrable vérifiable |
|---|---|---|---|
| **D0** | **Direction produit** | vision, arbitrage, cohérence, validation finale | registre des décisions (`DECISIONS.md`) |
| **D1** | **Direction artistique** | UI, UX, design system, typographie, thème clair/sombre | tokens + composants + 8 maquettes |
| **D2** | **Architecture logicielle** | modules, dépendances, stabilité, découpage de `section_dock` | graphe de dépendances sans cycle |
| **D3** | **Géologie & métier** | données, forages, coupes, interprétation, justesse scientifique | règles métier testables |
| **D4** | **Data engineering** | schémas, relations, **contrat de piste**, traçabilité | doc 02 implémenté + migration |
| **D5** | **Cartographie 2D** | coupe, symboles, annotations, échelle, légendes | coupe de référence conforme |
| **D6** | **Visualisation 3D** | scène, caméra, surfaces, couches, performance | les 9 pistes affichables ou déclarées |
| **D7** | **Import & validation** | 12 formats, 5 niveaux d'état, blocages | 0 message sans « pourquoi/résoudre » |
| **D8** | **Interactions & commandes** | boutons, menus, raccourcis, palette de commandes | inventaire 1 373 → registre unifié |
| **D9** | **Export & publication** | PDF, PNG, SVG, mise en page, cartouche | 4 formats reproductibles |
| **D10** | **Qualité & tests** | régressions, performances, accessibilité | CI verte + 3 coupes de référence |
| **D11** | **Documentation & langue** | FR/EN, glossaire, aide, journal de version | 0 chaîne non traduite, glossaire complet |
| **D12** | **Données de référence** | bibliothèques litho/altéro, palettes OKLCH, profils | bibliothèques versionnées et validées |

**Pourquoi D11 et D12 :** le code contient déjà 30 familles litho, 27 altérations, 2 489 traductions et 2 palettes OKLCH — c'est un actif métier. Sans direction propriétaire, il dérive (et il dérive déjà : `fr.ts` vide).

---

## 2. Les 6 sous-directions concrètes (exemples, pas des titres)

### D6 · 3D — 6 spécialistes
1. Topographie & surfaces (MNT, contours, hypsométrie, ancrage collets)
2. Rendu & rastériseur numpy (budget de segments, LOD, ordre de profondeur)
3. Trajectoires & géométrie (déviation, subdivision, tubes, bandes)
4. Pose des pistes 3D (côté, écart, rayon — le pendant 3D du contrat)
5. Performance (asynchrone, cache, 1 000 / 10 000 / 50 000 trous)
6. Ergonomie caméra (presets, gizmo, hover, sélection, retour d'état)

### D5 · Coupe 2D — 6 spécialistes
1. Échelle & cadre (échelle commune, fenêtre d'élévation, axes)
2. Pistes catégorielles (motifs, proportions, débordement)
3. Pistes quantitatives (Jenks, rampes, classes, sous-pistes multi-éléments)
4. Annotations (collets, profondeurs, étiquettes de fin, anti-collision)
5. Légendes & interaction (surbrillance, sélection croisée)
6. Exclusions & inclusion (buffer, corridor, forages écartés)

### D7 · Import & validation — 4 spécialistes
1. Détection (signatures, encodages, séparateurs, décimale)
2. Organisation (large/long/délimité, questions bloquantes)
3. Contrôles métier (cohérence croisée : RQD vs récupération, hiérarchie litho)
4. Expérience d'erreur (les 5 niveaux, navigation vers la ligne source)

### D1 · Direction artistique — 4 spécialistes
1. Design system (tokens couleur/espace/rayon/ombre/typographie)
2. Composants (champ, liste, panneau, barre, dialogue, tableau)
3. Thème sombre (conçu, pas inversé)
4. Accessibilité & densité (contraste, taille de cible, zoom, densité compacte/confort)

---

## 3. Règle de fonctionnement (comment un chef arbitre)

1. Une direction produit **une proposition**, jamais un document de 40 pages.
2. Elle est **confrontée** aux directions impactées (au minimum D2 architecte + D10 qualité).
3. Elle passe un **test de cohérence** contre les décisions déjà prises (`DECISIONS.md`).
4. D0 **entérine ou rejette** en une ligne.
5. Tout refus est motivé et **journalisé** — on ne rejette jamais deux fois pour la même raison.

**Ce que je refuse de simuler :** je ne vais pas produire 300 rapports d'agents fictifs. Ce qui est utile, c'est **un document par direction, court, sourcé, avec un critère d'acceptation**. C'est ce que je produis, dans l'ordre, en commençant par D4 (le contrat) parce qu'il bloque D1, D5, D6 et D9.

---

## 4. Phases (version corrigée)

La note plaçait les maquettes (phase 4) avant l'architecture des données (phase 6). **Inversion corrigée** — le modèle de paramètres décide de la forme des écrans.

| Phase | Contenu | Livrable | Porte de sortie |
|---|---|---|---|
| **0** · Audit | inventaire commandes, paramètres, états, dépendances | ✅ docs 01 | fait |
| **1** · Contrat | contrat de piste, arborescence, états | ✅ docs 02/03/04 | validé par toi |
| **2** · Filet | harnais de test `core/` + projet de référence + 3 coupes témoins | CI verte | **obligatoire avant maquettes** |
| **3** · Design system | tokens, typographie, composants, thème sombre | D1 | |
| **4** · Maquettes | 8 modules + panneau pistes unifié + dialogues | écrans | |
| **5** · Spécifications | fiche par fonctionnalité (9 rubriques, voir §5) | cahier des charges | |
| **6** · Revue technique | découpage `section_dock`, suppression legacy | plan d'exécution | |
| **7** · Validation | cahier des charges définitif signé | GO développement | |

---

## 5. La fiche de conception (le livrable de phase 5)

Une fonctionnalité n'existe que si ces **9 rubriques** sont remplies. Sinon, elle n'est pas spécifiée.

1. **Emplacement** — module, panneau, niveau de profondeur
2. **Objectif** — le problème utilisateur résolu (une phrase)
3. **Commandes** — boutons, menus, raccourcis
4. **Options principales** — 6 maximum visibles
5. **Sous-options** — derrière « Avancé », avec la condition d'apparition
6. **Règles** — ce que fait le système, cas limites inclus
7. **Données lues / modifiées** — source, destination, jamais la source métier
8. **Dépendances** — modules amont/aval, effet d'un changement
9. **États** — les 5 niveaux, avec leur message exact

**Critère d'acceptation :** une fiche est recevable si un développeur peut l'implémenter **sans poser de question de comportement**. Une formulation du type « options avancées » sans liste est refusée.

---

## 6. Suivi hebdomadaire

`DECISIONS.md` (registre) + un récapitulatif par semaine :
- décisions entérinées (numéro, portée, impact)
- livrables produits (fichier, direction, critère de sortie)
- points bloqués et qui peut les débloquer
- dette ajoutée / dette remboursée (en lignes ou en clés supprimées)

Chaque décision porte un identifiant (`D-001`, `D-002`…) et reste immuable : une révision crée `D-002-bis`, elle ne réécrit pas l'histoire.
