# 07 — Spécification normative (à suivre à la lettre)

> **Principe directeur** — *La puissance d'un logiciel professionnel ne doit jamais se
> traduire par une complexité imposée à son utilisateur.*
>
> Un géologue débutant doit pouvoir travailler sans rien comprendre à la mécanique ;
> un géologue expérimenté doit pouvoir régler chaque paramètre dont il a besoin.
> Les deux utilisent **le même logiciel, les mêmes mots, les mêmes données**.

Ce document n'est pas une intention : c'est le **contrat de développement**.
Chaque règle porte un identifiant (`R-xx`), un **critère d'acceptation vérifiable**,
et — quand c'est possible — un test automatique qui la fait respecter.

> **Règle zéro.** Un développeur ne choisit **jamais** un comportement, un mot, une
> valeur par défaut ou une disposition. Si ce n'est pas écrit ici ou dans
> `specs/data/*.json`, il demande ; il n'invente pas.

---

## 0 · Les deux sources de vérité (et elles sont uniques)

| Fichier | Ce qu'il gèle | Consommé par |
|---|---|---|
| `specs/data/tracks.json` | les 12 pistes, leurs 4 familles, les **15 champs communs**, les réglages autorisés par famille, les valeurs par défaut | coupe 2D, 3D, légende, export, carte |
| `specs/data/lexique.json` | **tous les mots affichés** (niveaux, familles, rangs, types, modules) + la liste des mots interdits | interface, messages, aide, export |

**R-01.** Aucune chaîne affichée à l'utilisateur n'est écrite en dur dans le code.
Elle est lue dans `lexique.json`.
*Acceptation :* `python3 tools/spec_check.py` → 0 chaîne hors lexique, 0 mot interdit.

**R-02.** Aucune piste n'existe en dehors de `tracks.json`.
*Acceptation :* le nombre de pistes du code = `len(tracks.json.pistes)` = 12.

**R-03.** Ajouter une piste = **éditer le JSON uniquement**. Si l'ajout oblige à
toucher un fichier Python de vue, la conception est refusée en revue.

---

## 1 · Pistes — 12 pistes, 4 familles, 15 champs

### 1.1 Les familles (fermées)

| Famille | Pistes | Ce que la famille décide | Réglages propres autorisés |
|---|---|---|---|
| **Structurelle** | Profondeurs, Trajectoire, Intercepts | position, épaisseur, trait | `tick_step`, `label_every`, `line_style`, `dash`, `rule_ids`, `label_position` |
| **Catégorielle** | Lithologie, Altérations, Minéralisations, Structures | couleur et motif viennent du **Référentiel** | `pattern`, `legend_order`, `hatch_scale` |
| **Quantitative** | Teneurs, RQD, Récupération, Densité | échelle, classes, rampe | `method`, `n_classes`, `breaks`, `ramp`, `scale_scope`, `range`, `unit` |
| **Média** | Imagerie | vignette | `thumb_size`, `resolution`, `alt_text` |

**R-04.** Une piste **ne peut pas** appartenir à deux familles, ni à aucune.
*Acceptation :* `family` ∈ {structurelle, categorielle, quantitative, media}.

### 1.2 Le contrat : 15 champs, jamais 14 ni 16

`id` · `label` · `family` · `visible` · `order` · `side` · `width` · `gap` ·
`opacity` · `fill` · `stroke` · `label_text` · `tooltip` · `filter` · `export` · `family`

**R-05.** Une piste possède **exactement** ces 15 champs. (`family` a été ajouté aux 14 emplacements d'origine par D-017 : sans lui, l'héritage type → piste est impossible.) Tout champ supplémentaire est
un bug, pas une extension.
**R-06.** Un champ commun ne peut **jamais** être redéclaré dans `specific`.
*Acceptation :* `specific ∩ contrat = ∅` pour les 12 pistes.

### 1.3 L'héritage (et son affichage)

```
Famille (défaut)  ──►  Piste (valeur explicite, optionnelle)
```

**R-07.** Trois états possibles pour une valeur : **héritée**, **forcée**, **sans objet**.
L'interface doit montrer lequel. Une valeur forcée est signalée par une écriture
normale ; une valeur héritée par un **rond gris devant** la valeur.
**R-08.** « sans objet » n'existe que si le champ est listé comme tel pour la famille,
et **la raison est toujours écrite** (ex. « côté » en 3D : « la scène tourne »).

### 1.4 Une seule déclaration, cinq lecteurs

**R-09.** 2D, 3D, légende, export et carte lisent le **même objet résolu**. Aucune vue
ne conserve de copie, aucun `QSettings` parallèle, aucun magasin secondaire.
*Acceptation :* un test écrit une valeur, la relit depuis les 5 lecteurs, et échoue
si l'une des 5 diffère. Un test échoue si un second magasin de réglages est créé.

**R-10.** Le côté (`side`) et la largeur (`width`) peuvent avoir **deux unités**
(px à l'écran, unité monde en 3D) mais **un seul propriétaire** : la piste.
Deux champs distincts, jamais deux magasins.

### 1.5 Ce qui est supprimé, définitivement

* les clés plates `alter_width`, `structure_opacity`, `assay_max_width`… ;
* les noms multiples pour une même notion ;
* tout réglage de piste présent dans le panneau de la coupe.

**R-11.** Le panneau de la coupe ne contient que : coupe active, inclusion,
**3 familles repliables**, et 4 réglages de coupe (cadre & axes, topographie,
légende & cartouche, coupes enregistrées).
*Acceptation :* revue visuelle contre `maquettes/04_coupe_2d.png` — aucun réglage de
piste n'y figure.

---

## 2 · Données — 12 types, 3 rangs, des catégories qui restent chez elles

| Rang | Sens | Types | Règle |
|---|---|---|---|
| **1 — Socle** | ce qui situe le forage | Collets, Déviations, Topographie, Profils d'ouvrage | **lu**, jamais recalculé, jamais écrasé |
| **2 — Observé** | ce que vous saisissez ou importez | Lithologie, Altérations, Minéralisations, Structures, Teneurs, Imagerie | les **catégories** sont nommées par l'utilisateur et vivent au Référentiel **de ce type** |
| **3 — Calculé** | ce que DrillMaster déduit | RQD, Récupération | jamais importé en direct ; un fichier RQD fourni devient « RQD mesuré » du rang 2 |

**R-12.** Un type appartient à **un seul rang**. Le rang ne change jamais en cours de route.
**R-13.** Une catégorie (Saprolite, Latérite, Faille…) **ne quitte jamais son type**.
Aucune liste de catégories n'est partagée entre deux types.
**R-14.** Une donnée absente est **affichée absente**, avec sa raison. Jamais une piste
vide et muette, jamais un zéro inventé.
**R-15.** Les 12 types de `lexique.json` sont la liste **fermée** des types de données.
Un 13ᵉ type ne peut pas apparaître dans un menu.

---

## 3 · Les mots — un seul vocabulaire, deux voix

**R-16.** Le vocabulaire des **niveaux** est identique en mode Guidé et en mode Expert :
*Information · Avertissement · Question · Blocage · Erreur technique*. Seule la
**longueur des phrases** change.
**R-17.** Les mots de `lexique.json → interdits` sont **bannis de l'interface** :
« clé », « cache », « signature », « contrat », « JSON », « index », « callback »…
Un terme technique peut exister dans les journaux, jamais à l'écran.
**R-18.** Chaque niveau dit trois choses, dans cet ordre : **ce qui se passe**,
**ce que vous pouvez faire**, **si la suite continue**.
**R-19.** Une couleur d'état ne sert **jamais** à identifier une donnée. L'accent de
marque (`#2E5BFF`) n'exprime **jamais** un état.

---

## 4 · Les états — 5 niveaux, 5 champs obligatoires

| Niveau | Ce qu'il veut dire | La suite |
|---|---|---|
| Information | un fait, rien à décider | poursuit seul |
| Avertissement | ça marche, mais il manque quelque chose | poursuit |
| Question | DrillMaster ne peut pas décider à votre place | met la ligne en attente |
| Blocage | rien ne peut continuer sur cette donnée | arrête l'étape suivante |
| Erreur technique | DrillMaster lui-même a échoué | arrête l'action en cours |

**R-20.** Tout message porte **les 5 champs** : `niveau`, `pourquoi`,
`concerné` (identifiants exacts, cliquables), `résoudre` (au moins une action
concrète), `portée` (fichier + ligne).
*Acceptation :* un message dont `pourquoi` ou `résoudre` est vide **ne peut pas être
construit** — le constructeur lève une erreur, un test le vérifie.

**R-21.** Aucune fenêtre modale pour une validation. Le détail s'ouvre dans un panneau.
*Acceptation :* `grep` de `QMessageBox` dans les modules de validation = **0**.

**R-22.** Un blocage ne disparaît **jamais** sans une décision explicite de l'utilisateur.
Trois sorties sont toujours proposées : corriger à la source, fusionner, exclure.
Chaque sortie dit **ce qui se passe après**.

**R-23.** DrillMaster n'écrit **jamais** dans les fichiers sources. Jamais.

---

## 5 · La complexité progressive — la règle qui rend le principe exécutable

C'est ici que « simple pour le débutant, précis pour l'expert » devient du code.

**R-24.** **6 réglages visibles au maximum** par piste. Le reste est derrière un
bouton nommé **« Avancé »**, jamais caché silencieusement.
**R-25.** Le mode **Guidé** n'affiche que les réglages marqués `essentiel` dans
`tracks.json`. Le mode **Expert** affiche *essentiel* + *avancé*. **Les valeurs sont
identiques** : changer de mode ne change aucun réglage, seulement ce qui est montré.
**R-26.** Aucune fonctionnalité n'est **réservée** au mode Expert. Un débutant peut
tout faire ; il est seulement guidé.
**R-27.** Toute valeur calculée automatiquement affiche **d'où elle vient** et
**comment la changer** (« 5 classes : quantiles, calculées sur 3 180 analyses —
modifier »).

---

## 6 · Les tests — la preuve, pas la promesse

**R-28.** Les **17 cas d'usage** de `maquettes/16_validation.png` sont des tests
obligatoires, pas des illustrations : projet vide, projet complet, 4 types manquants,
2 forages dupliqués, CSV point-virgule, décimale à virgule, encodage latin-1, forages
inclinés, forage horizontal, pendage inversé, MNT dans un autre CRS, MNT absent,
500 forages, export A1 300 dpi, mode sombre, zoom 400 %, contraste 4,5:1.
**R-29.** Un cas qui échoue **bloque la livraison**. Il n'existe pas de « à vérifier
plus tard ».
**R-30.** Chaque règle `R-xx` de ce document a **soit** un test automatique, **soit**
une ligne dans la revue visuelle, nommée. Une règle sans vérification est réputée
non appliquée.
**R-31.** Une fonctionnalité n'est pas « faite » parce que le bouton existe : elle est
faite quand le cas d'usage associé passe.

---

## 7 · Ce que le développeur n'a pas le droit d'inventer

| Sujet | Interdit | Ce qu'il fait à la place |
|---|---|---|
| un libellé | écrire un nouveau mot | le prendre dans `lexique.json`, ou demander |
| une valeur par défaut | « ça me semble mieux à 20 » | lire `tracks.json` |
| un nouvel état | ajouter une couleur/un niveau | utiliser les 5 niveaux existants |
| un réglage | ajouter une clé au panel | vérifier s'il appartient au contrat, sinon demander |
| un magasin de réglages | créer un `QSettings` | lire l'objet commun |
| une fenêtre modale | `QMessageBox` | panneau de détail à 5 champs |
| une correction de donnée | compléter une valeur manquante | afficher l'absence + 3 sorties |
| un comportement au clic | décider soi-même | suivre la maquette correspondante |

---

## 8 · Définition de « terminé »

Une tâche est terminée quand **les sept** sont vrais :

1. `python3 tools/spec_check.py` passe (JSON, lexique, interdits, unicité).
2. `python3 -m unittest discover specs/tests` passe.
3. Les cas d'usage touchés passent (R-28).
4. Aucun mot interdit dans l'interface (R-17).
5. Aucun réglage dupliqué, une seule déclaration (R-09).
6. Le rendu correspond à la maquette nommée dans le ticket (± 2 px).
7. Aucun fichier source de données modifié (R-23).

---

## 9 · Journal des règles

| Date | Règle | Pourquoi |
|---|---|---|
| J3 | R-01 → R-31 | traduction du principe directeur en contraintes vérifiables : les développeurs reçoivent des ordres et des valeurs, pas des intentions |

---

## 10 · État d'avancement des règles (mis à jour à chaque ticket)

| Règle | Sujet | État | Preuve |
|---|---|---|---|
| R-01 | mots issus du lexique | **en vigueur** | `lexique.py` + `spec_check` R-17 |
| R-02 → R-10 | contrat de piste, 5 lecteurs | **en vigueur** | `tracks.py`, 10 tests |
| R-11 | panneau de coupe maigre | à faire (T-05) | maquette 04 |
| R-12 → R-15 | 3 rangs de données | **spécifié** | `lexique.json`, `spec_check` R-12/R-15 |
| R-16 → R-19 | vocabulaire, 5 états | **en vigueur** | `messages.py`, 8 tests |
| R-20 → R-23 | message complet, 3 sorties | **en vigueur** | `messages.py`, 5 tests |
| R-24 → R-27 | complexité progressive | **en vigueur** | `visibilite.py`, 6 tests |
| R-28 → R-31 | 17 cas, définition de « terminé » | à faire (T-09) | maquette 16 |

**Chiffres du jour** : 62 vérifications de spécification, **32 tests**, 0 écart,
2 écrans produits **par le contrat** (Guidé / Expert) sans une seule piste codée en dur.

### Deux fautes attrapées par les gardes, et corrigées dans la spécification

1. **Le garde des 6 réglages** a refusé ma propre spécification : Teneurs en montrait 7,
   RQD en montrait 7. `ramp` et `range` sont passés en « avancé » — pas la règle.
2. **Le test « aucune piste codée en dur »** a trouvé `detail="assays"` dans l'écran.
   La piste de détail est maintenant choisie par `cat.par_famille(...)[0]["id"]`.

---

## 11. Les deux nouvelles règles issues du rapport de la flotte

Le rapport `09_RAPPORT_FLOTTE.md` a mesuré 655 couleurs littérales, 320 feuilles
de style en ligne et 9 tailles de police. Deux règles en découlent, et elles
sont vérifiées par `tools/spec_check.py` + `specs/tests/test_charte.py`.

### R-32 · Une couleur n'a qu'un foyer
Toute couleur vient de `specs/data/theme.json` (chrome, états) ou de
`specs/data/referentiel.json` (lithologie, teneurs). Un littéral `#RRGGBB` dans
un écran est un défaut de livraison. **Preuve** : `test_aucune_couleur_en_dur_dans_la_charte`.

### R-33 · L'échelle typographique est fermée
Six tailles, pas une de plus : 20 · 16 · 12,5 · 10 · 9 · 8,4 pt. Toute autre
valeur est un défaut. **Preuve** : `test_six_tailles_de_police_exactement`.

### R-34 · La grille d'espacement est un multiple de 4
4 · 8 · 12 · 16 · 24 · 32. Un 14 ou un 18 px est un défaut.
**Preuve** : `test_grille_de_4px`.

### R-35 · Trois rôles de bouton, un seul primaire par écran
`primaire` (l'action attendue), `secondaire` (une alternative), `discret`
(sortir sans rien changer). Plus d'un primaire visible = défaut.
**Preuve** : `test_trois_roles_de_bouton_documentes`.
