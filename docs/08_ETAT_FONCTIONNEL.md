# 08 — Ce qui fonctionne réellement (pas ce qui est dessiné)

> Une maquette prouve une intention. Cette page prouve un **comportement** :
> tout ce qui est listé ici s'exécute, et est couvert par un test.

## Vérifier soi-même, en deux commandes

```bash
python3 tools/spec_check.py                 # 62 vérifications de spécification
python3 -m unittest discover -s specs/tests  # 56 tests exécutés
python3 tools/demo_fonctionnel.py           # démonstration bout en bout
```

## Ce qui marche, module par module

| Domaine | Ce qui est réellement fait | Preuve |
|---|---|---|
| **Lecture** | encodage UTF-8 / cp1252 réparé et signalé · séparateur `;`, `,`, tabulation détecté · décimale à virgule ou à point, milliers compris (`512.340,2` → `512340.2`) · colonnes reconnues même renommées (`HOLEID`, `east`, `forage`…) · ligne illisible écartée et signalée · **fichier source jamais modifié** | `Cas5`, `Cas6`, `Cas7`, `Cas15` |
| **Validation** | doublon d'identifiant = **blocage** avec 2 lignes concernées et 3 sorties · fichier vide = blocage · fichier sans coordonnées = blocage · type absent = annoncé, jamais inventé | `Cas1`, `Cas3`, `Cas4` |
| **Géométrie** | angle moyen **et** courbure minimale, calculées · forage vertical supposé quand aucune mesure · forage horizontal · convention de pendage · **écart entre méthodes chiffré** et averti au-delà de 0,5 m | `Cas8` → `Cas11` |
| **Coupe 2D** | projection sur un axe (orientation et longueur calculées) · inclusion avec tolérance · hors-coupe **annoncé** avec la distance · fond de forage projeté en altitude · coupe vide signalée | `Cas12` |
| **Analyses** | intercepts multi-seuils, longueur minimale, teneur manquante qui n'invente rien · analyse orpheline (identifiant inconnu) signalée | `Cas13`, `rattachement` |
| **Décisions** | **exclure un forage s'applique partout** (une décision, un seul endroit) · exclusion sans motif refusée · réintégration possible | `Cas14` |
| **Modes** | Guidé / Expert : **aucune valeur ne change** quand on bascule | `Cas16` |

## Ce que la démonstration affiche, à l'exécution

```
── import : {'forages': 65, 'messages': 2, 'bloquant': True}
   [Blocage] Deux forages portent le même nom
      pourquoi : la trajectoire de ce forage deviendrait ambiguë…
      concerné : ISBRC045, ligne 46, ligne 47
      résoudre : corriger l'identifiant / fusionner / exclure
── après décision : 63 forages actifs, 1 exclusion
── coupe à 85,6° (782 m) : 39 inclus, 24 exclus (hors axe)
── fichier source intact : True
```

## La maquette et le plugin lisent le MÊME thème

Avant T-10, une source unique a été créée : `specs/data/theme.json`.

| Ce qu'il contient | Qui le lit |
|---|---|
| 18 jetons de couleur (clair **et** sombre) | `maquettes/ui.py` **et** `drillmaster_v3/theme.py` |
| typographie (6 tailles), rayons, espacements | idem |
| disposition : fenêtre 1600 × 1000, barre haute 54, barre bas 32, marge 24, panneaux 1010 + 526 | idem |
| correspondance état → couleur | `Message.couleur` (plus de couleur dans le lexique) |

`drillmaster_v3/theme.py` sait aussi produire la **feuille de style Qt** (`theme.qss()`),
donc les couleurs ne seront pas retapées dans le plugin : elles seront générées.

**Preuve.** `test_R19_les_couleurs_ne_sont_pas_dans_le_lexique`,
`test_R19_le_theme_a_un_jeton_par_niveau`, et la coupe et l'écran Pistes ont été
régénérés **après** ce changement, à l'identique.

## Réponse à la question laissée ouverte

**Une exclusion est globale au projet, pas locale à la coupe.** Elle porte un motif,
elle est réversible, et elle est visible partout (coupe, 3D, export, carte) — parce
qu'elle vit dans `Projet`, et qu'aucune vue n'en garde de copie (R-09).
Si tu veux une exclusion *par coupe*, c'est `Inclusion.exclus` — la liste des forages
hors axe — qui joue ce rôle : elle est calculée, jamais décidée.

## Ce qui n'existe pas encore (et ne doit pas être annoncé comme fait)

| Sujet | État | Ticket |
|---|---|---|
| Interface Qt réelle dans QGIS | **non commencé** — le cœur est testé hors QGIS | T-10 |
| Légende, export PDF, carte QGIS | non commencé | T-11 |
| Vue 3D | non commencé | T-12 |
| Altérations, minéralisations, structures, imagerie (lecture) | non commencé | T-13 |
| Référentiel (couleurs, motifs) | non commencé | T-14 |
| Performance 500 forages | non mesuré | T-15 |
