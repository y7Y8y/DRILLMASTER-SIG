# ORIG — Audit IA : fin du wizard, atelier à 3 zones

Audit d'expert (géologie + data) du parcours v2, preuves à l'appui.
Décision d'architecture pour ORIG : **pas de wizard**.

## Preuves collectées dans le v2

1. **L'étape 3 « Géométrie 3D » est un calcul, pas une étape.**
   Contenu réel : bouton + progression + table. Et `main_dock.py` contient
   déjà `_auto_generate_trajectories` (calcul auto en arrière-plan) — le v2
   possède les deux chemins et les impose tous les deux. La trajectoire est
   un artefact calculé : elle se recalcule quand les données changent.
2. **L'étape 1 « Projet » bloque la découverte.** CRS/unités servent à la
   sauvegarde et à l'export, pas à regarder ses données. Le géologue arrive
   avec un CSV : il veut voir, pas administrer.
3. **Catégorisation géologique (9 onglets plats) au lieu de structurelle.**
   La taxonomie correcte est à DEUX axes — support × nature :

   | Domaine | Support | Nature |
   |---|---|---|
   | Collets | trou | géométrie |
   | Survey | point (station) | géométrie |
   | Litho, Alté, Miné | intervalle | codé (référentiel) |
   | Géotech | intervalle | codé + quantitatif (RQD, recovery) |
   | Teneurs | intervalle (support échantillon) | quantitatif (éléments, unités, QA/QC) |
   | Structures | point (plan mesuré α/β) | géométrique orienté |

   Le socle commun est l'enregistrement ancré en profondeur (trou existe,
   from<to, recouvrements) ; les validateurs se spécialisent par NATURE —
   codé → référentiel ; quantitatif → unités, limites de détection, QA/QC
   (blancs, standards, doublons). Chaque onglet v2 re-valide ses intervalles
   à sa façon : origine des redondances.
4. **Blocages au mauvais endroit.** Seules les erreurs QC bloquantes
   (profondeurs dupliquées, trou sans collet…) doivent bloquer — affichées
   sur la donnée, pas comme une porte d'étape.

## Décision ORIG : l'atelier à 3 zones

```
┌────────────┬──────────────────────────────┬─────────────┐
│  DONNÉES   │            VUES              │ PROPRIÉTÉS  │
│ (rail G)   │  Carte · Coupe 2D · Vue 3D   │  (rail D)   │
│            │  vues du MÊME objet projet   │  contextuel │
├────────────┴──────────────────────────────┴─────────────┤
│  Parcours guidé optionnel : checklist qui s'allume      │
│  collets ✓ · survey ✓ · trajectoires ✓ · tracez une coupe│
└─────────────────────────────────────────────────────────┘
```

- **Rail Données** : glisser-déposer unique, détection auto
  (`import_detect` adapté), groupage par SUPPORT puis NATURE :
  - *Forage* : collets (trou) + survey (points station)
  - *Logs codés* : litho, alté, miné, géotech — machine d'intervalle
    partagée + validateur référentiel
  - *Teneurs* : même support intervalle, nature quantitative propre —
    éléments (wide-format), unités, QA/QC
  - *Structures* : points orientés (α/β), pas des intervalles
  - *Surfaces* : MNT, imagerie
- **Zone Vues** : la trajectoire se calcule seule en arrière-plan dès que
  collets+survey sont valides (le worker v2 `_TrajWorker334` prouve la
  faisabilité) ; les vues se rafraîchissent, aucune étape n'existe.
- **Rail Propriétés** : les options du sélectionné — remplace les 24
  groupes empilés du v2.
- **Projet** (nom, CRS, unités) : tiroir, pas porte. CRS proposé par
  défaut, exigé à la première sauvegarde/export.

## Règles qui en découlent pour ORIG

- `core/` expose un service de trajectoires réactif (recalcul sur
  changement de données), pas une commande.
- La validation d'intervalle est UNE implémentation, paramétrée par
  domaine — jamais recopiée.
- Aucune étape ne bloque la suivante ; seules les erreurs QC bloquantes
  bloquent, là où la donnée vit.
- La checklist guidée est un composant (allumé/éteint), jamais une
  structure d'application.
