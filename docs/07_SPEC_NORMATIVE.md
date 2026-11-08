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

### R-36 · Aucun réglage dans une fenêtre
Une fenêtre ne sert qu'à **choisir un fichier**. Un réglage vit dans le
panneau, visible en permanence, ou derrière le repli « réglages avancés ».
Constat d'origine : `ReferenceDialog` enferme 8 réglages, `LithologyStructureDialog`
en enferme 6 (agent N-01).

### R-37 · Pas de barre d'onglets masquée
Soit un panneau unique assumé, soit des onglets **nommés et visibles**.
Constat d'origine : 2 barres masquées (agent N-02).

### R-38 · Deux catégories de réglages, nommées
*Préférences de poste* (thème, langue, géométrie des panneaux) et
*réglages de projet* (pistes, seuils, couleurs, exclusions). Les seconds
voyagent avec le projet. Constat d'origine : 26 accès à des réglages de poste
(agent N-04).

### R-39 · Une infobulle par contrôle, qui dit quoi et où
Ce que ça change, et sur quoi ça s'applique (coupe, 3D, légende, export,
carte). Constat d'origine : 102 infobulles pour 235 contrôles (agent N-06).

## 12. Les règles d'architecture (chantier 9)

Le département Architecture a mesuré le code, pas l'écran. Quatre règles en
découlent, toutes vérifiables par un agent.

### R-40 · Le noyau ne connaît pas l'interface
`core/` ne doit jamais importer `ui/`. Aujourd'hui c'est vrai (0 import) :
c'est ce qui permet de calculer et d'exporter sans QGIS. **À conserver, pas à
reconstruire.**

### R-41 · Une classe d'affichage ne calcule pas
`SectionWidget` fait 5 295 lignes et 45 opérations de calcul. Un widget
affiche ; le calcul appartient au noyau (A-02).

### R-42 · Un seul point d'entrée par geste
Une seule lecture de fichier, une seule gestion d'erreur, un seul chargement
de projet. Aujourd'hui : 13 lectures dans 5 fichiers, 15 affichages d'erreur
sans point central (A-05, A-07).

### R-43 · Ajouter un domaine = ajouter une ligne
Un type de données est aujourd'hui cité dans 30 fichiers en moyenne. Il doit
être lu dans la table des domaines (`lexique.json`), jamais recopié (A-06).

## 13. Chantier 2 livré — un réglage, un propriétaire

Le défaut mesuré (F-01) : la largeur est réglable dans **12 endroits de
5 fichiers**. Voici ce qui le remplace, et ce qui le prouve.

### Le code

`drillmaster_v3/core/reglages.py` — un seul objet, `Reglages`, porté par le
projet (`Projet.reglages`). Aucune vue ne garde de copie.

| Geste | Ce qui se passe | Test qui le prouve |
|---|---|---|
| `modifie(piste, champ, valeur, par=…)` | une valeur, un journal, cinq vues | `test_regler_une_fois_change_les_cinq_vues` |
| sans nom d'auteur | **refusé** | `test_sans_nom_pas_de_changement` |
| hors bornes | refusé, **avec les bornes du contrat** | `test_hors_bornes_refuse_avec_les_bornes_du_contrat` |
| même valeur | rien n'est écrit | `test_meme_valeur_n_ecrit_pas_au_journal` |
| `retablit()` | retour à la valeur de la famille | `test_retablit_revient_a_la_famille` |
| une vue n'utilise pas le champ | elle **le dit et pourquoi** | `test_une_vue_sans_objet_le_dit_et_ne_ment_pas` |

### La règle qui en découle

**R-44 · Un réglage n'a qu'un écrivain.** Toute modification passe par
`Reglages.modifie()`, qui exige **qui** modifie et journalise le changement.
Une vue qui voudrait écrire directement est un défaut de livraison.

**R-45 · Les bornes viennent du contrat, jamais du code.** Le validateur lit
`specs/data/tracks.json` (`min`, `max`, `valeurs`). Un nombre écrit en dur dans
la validation est un défaut : `test_les_bornes_viennent_du_contrat_pas_du_code`
échoue s'il en apparaît un.

### Ce que la vérification a attrapé

En écrivant ce chantier, j'avais codé `width` entre **4 et 64** et `side` en
« gauche/droite ». Le contrat dit **4 à 120** et `left/right/overlay`. Sans le
test, j'aurais livré une contrainte inventée — exactement le défaut que la
flotte reproche au plugin.

## 14. Chantier 4 livré — le bandeau remplace 30 fenêtres

Le défaut mesuré (M-01) : **29 fenêtres modales** (30 appels `QMessageBox`
réels) interrompent le travail. Voici ce qui les remplace, et ce qui le prouve.

### Les deux pièces

| Fichier | Rôle |
|---|---|
| `core/bandeau.py` | la zone d'annonce : empile, trie, résume, ne bloque pas le clic |
| `core/messages_plugin/catalogue.py` | **30 messages à 5 champs, un par fenêtre**, identifiés par `fichier:ligne` |

Le bandeau **n'accepte que** des messages à 5 champs. On ne peut pas y écrire
une chaîne libre : `test_on_n_ecrit_pas_dans_le_bandeau_autre_chose_qu_un_message`.

### Ce qui est garanti par les tests

| Garantie | Test |
|---|---|
| aucune fenêtre oubliée | `test_aucune_fenetre_n_est_oubliee` |
| aucun message inventé (l'identifiant cite un appel réel) | `test_chaque_identifiant_correspond_a_un_appel_reel` |
| un blocage propose au moins 2 sorties | `test_un_blocage_propose_au_moins_deux_sorties` |
| **aucun mot interdit** dans les 30 messages | `test_aucun_mot_interdit` |
| une réussite ne mérite pas de message | `test_aucune_information_ne_dit_simplement_que_ca_a_reussi` |
| même contenu en Guidé et en Expert | `test_deux_voix_meme_contenu` |
| la couleur vient du thème, pas d'une maquette | `test_la_couleur_vient_du_theme` |

### La règle qui en découle

**R-46 · Une réussite ne fait pas de message.** Si l'action a marché, l'écran
le montre (la ligne apparaît, le fichier est listé). Un message ne sert qu'à
annoncer *ce que l'utilisateur ne peut pas voir* : ce qui manque, ce qui
bloque, ce qui demande une décision. Constat d'origine : trois exports
annonçaient leur succès par une fenêtre.

### L'état exact du chantier

| | |
|---|---|
| Messages écrits | **30 / 30** |
| Fenêtres encore dans le code | **30** — la conversion des appels est le prochain geste |
| Démonstration | `python3 tools/demo_messages.py` |

Le contenu est prêt ; il reste à remplacer les appels dans `DrillMaster/ui/`
par `bandeau.ajoute(par_id("fichier.py:ligne"))`. C'est un remplacement
mécanique, vérifiable ligne à ligne — et le test de comptabilité refusera
toute fenêtre laissée sans message.

## 15. Chantier 5 livré — boutons et gestes

### D'abord : deux constats de la flotte étaient faux

Le département Boutons avait classé **4 actions « bloquantes : supprime sans
demander confirmation »**. Vérification faite dans le code :

| Fonction signalée | Ce qu'elle fait réellement | Verdict |
|---|---|---|
| `_on_project_layers_will_be_removed` | oublie des couches que QGIS détruit lui-même | rien à confirmer |
| `_remove_generated_layers` | retire les couches **régénérables** | rien à confirmer |
| `_remove_project_group` | retire le groupe racine des couches de coupe | rien à confirmer |
| `delete_project_folder` | **supprime vraiment** — et demande déjà : dialogue, seconde confirmation, case à cocher, « Supprimer » grisé | déjà protégé |

Le détecteur cherchait le mot « supprim » dans un nom de fonction : il
mesurait **la forme**, pas le risque. Deux leçons en découlent.

**R-47 · Un agent qui se trompe est corrigé, pas écouté.** Un constat de la
flotte qui ne résiste pas à la lecture du code est retiré du rapport avec sa
raison. Le rapport est un outil, pas un juge.

**R-48 · Une couche régénérable n'est pas une donnée.** Retirer une couche
recalculable ne demande aucune confirmation ; supprimer un fichier en demande
trois.

### Le vrai défaut, celui qui reste

Ce n'est pas la suppression : c'est que **l'utilisateur ne sait pas ce qu'un
bouton va changer avant de cliquer**. `core/gestes.py` répond à ça.

| Garantie | Test |
|---|---|
| un bouton dit ce qu'il fait (« OK » refusé) | `test_un_mot_creux_est_refuse` |
| une destruction annonce **ce qui sera perdu** | `test_une_action_destructrice_dit_ce_qui_sera_perdu` |
| une destruction propose une sortie | `test_sans_sortie_une_destruction_est_refusee` |
| une destruction n'est **jamais** le bouton principal | `test_une_destruction_n_est_jamais_le_bouton_principal` |
| un seul bouton principal par barre | `test_un_seul_primaire_par_barre` |
| rien ne s'exécute sans nom, ni sans motif si exigé, ni sans écrit | 3 tests |
| les gestes réels du plugin (10 boutons) passent ces règles | `demo_gestes.py` |

**R-49 · Une action qui peut détruire n'est jamais le bouton principal**, et
elle exige un nom, un motif et une confirmation écrite.

### État

| | |
|---|---|
| Geste implémenté | `core/gestes.py` (14 tests) |
| Gestes du plugin réécrits | **10 boutons** en 3 barres (`core/gestes_plugin.py`) |
| Démonstration | `python3 tools/demo_gestes.py` |
| Planche | `maquettes/25_gestes.png` |

## 16. Chantier 1 livré (socle) — une couleur se nomme par son rôle

### Le défaut, mesuré avant d'être corrigé

Le plugin portait **deux palettes vivantes** qui se contredisaient :

| Foyer | Contenu | Problème |
|---|---|---|
| `specs/data/theme.json` | 18 rôles neutres × 2 modes | la DA décidée, jamais lue par Qt |
| `DrillMaster/ui/styles_qt.py` | 17 teintes « géologiques » | une deuxième vérité, éditée à la main |
| 30 feuilles de style | **417 couleurs littérales** | changer le fond obligeait à corriger 30 fichiers |

Deux teintes se ressemblaient jusqu'à l'ambiguïté : l'ancien accent teal du
chrome et le teal d'une lithologie. Une couleur d'interface **ne doit pas**
pouvoir se confondre avec une couleur de donnée.

### Ce qui est livré

| Pièce | Rôle | Preuve |
|---|---|---|
| `tools/genere_palette.py` | génère la copie Qt depuis le thème | sort en 1 si dérive |
| `DrillMaster/ui/palette_jetons.py` | **seul** foyer de chrome du plugin | 18 rôles × 2 modes, `couleur()`, `paire()` |
| `tools/audit_couleurs.py` | mesure les trois catégories, à chaque passage | `specs/data/audit_couleurs.json` |
| `specs/tests/test_palette.py` | 7 tests : dérive, couverture, rôle inconnu, unicité du foyer | verts |
| `maquettes/26_socle.py` + `.png` | la chaîne de vérité et la correspondance rôle par rôle | relue |

### La règle qui en découle

**R-50 · Une couleur se nomme par son rôle, jamais par sa teinte.** Le code
écrit `couleur("border")`, pas `"#E4E7EC"`. Une teinte n'existe qu'à un seul
endroit — `theme.json` — et sa copie Qt est **générée**, donc jamais éditée.
Un rôle inconnu lève au lieu de rendre du vide : une couleur qui disparaît
silencieusement est un défaut, pas un cas par défaut.

**R-51 · Une couleur de chrome ne peut pas ressembler à une couleur de
donnée.** Le chrome travaille en valeur (noir, gris, blanc) ; la couleur est
un canal réservé aux données et aux cinq états. La correspondance de la
planche 26 mesure l'écart en Lab, rôle par rôle.

### Ce qui reste, chiffré et non maquillé

| Reste | Mesure | Pourquoi ce n'est pas fait d'un coup |
|---|---|---|
| jetons de `styles_qt.COLORS` | **44** déclarations | la table est le point d'entrée de 304 usages ; elle sera **réécrite en façade** sur `palette_jetons`, pas supprimée |
| couleurs dans les feuilles de style | **417** dans 30 fichiers | une couleur au milieu d'une feuille de style ne se remplace pas par un littéral : la chaîne doit devenir une f-string |

Une migration automatique a été tentée **trois fois** (`tools/migre_couleurs.py`,
conservé comme trace) : elle casse le code dès qu'une couleur est au milieu
d'un texte (`"QLabel { color: #5D6D7E; ..."`), et un `re.sub` global produit
`"TOKENS["nom"]"` — du code invalide. **Décision : la conversion se fait
fichier par fichier, avec compilation vérifiée après chacun.** L'outil de
mesure reste, lui, définitif.

## 17. Chantier 6 — les rangements (tranche 1 livrée)

### Ce que la mesure a dit, avant de toucher au code

`ui/section_dock.py` pesait **11 529 lignes** : deux classes
(`SectionCanvas` 122 méthodes, `SectionWidget` 172) et **40 % du plugin à lui
seul** dans les six fichiers de plus de 1 500 lignes. Mais le défaut le plus
coûteux n'était pas la taille : c'étaient les **801 lignes de journal de
versions** en docstring — un bug corrigé en v2.7.4, relu à chaque ouverture du
fichier pour comprendre du code qui n'existe plus.

### Les deux tranches

| Sortie | Lignes | Nature |
|---|---|---|
| `ui/coupe_socle.py` | 288 | couleurs d'interaction, motifs, encres, petites capitales, items graphiques |
| `docs/HISTORIQUE_section_dock.md` | 801 | le journal de versions, intégral, hors du code |

`section_dock.py` : **11 529 → 10 515 lignes**, sans qu'un seul appelant
change. `from .section_dock import SELECTION_HIGHLIGHT_COLOR` fonctionne
toujours (ré-export assumé) ; aucun nom n'est défini deux fois ; aucun nom
n'a disparu.

### La règle qui en découle

**R-52 · Une tranche sort, un cliquet baisse.** On ne découpe pas « un jour » :
chaque extraction abaisse le plafond de lignes **dans le même commit**, et un
test refuse que le fichier remonte. Le monolithe ne peut donc que maigrir.

**R-53 · Une extraction ne change aucun comportement.** Mêmes noms, mêmes
signatures, ré-exportés depuis le fichier d'origine. Ce qui change est
l'endroit où l'on lit, jamais ce qui s'exécute.

### Le cliquet, tel qu'il est posé

| Test | Ce qu'il empêche |
|---|---|
| `test_le_monolithe_ne_remonte_pas` | `section_dock.py` > 10 560 lignes |
| `test_un_seul_fichier_geant` | un 2ᵉ fichier au-delà de 3 000 lignes |
| `test_les_noms_vivent_dans_le_socle` | une tranche qui se défait |
| `test_le_monolithe_les_reexporte` | un import cassé chez un appelant |
| `test_aucun_nom_defini_deux_fois` | deux vérités pour un même nom |
| `test_le_journal_de_versions_a_quitte_le_code` | le retour du journal |

### Ce qui reste, chiffré

6 fichiers au-delà de 1 500 lignes · **996 lignes** de commentaire
d'historique encore dans le code · **39 noms** de fonctions présents dans
plusieurs fichiers (invitation à regarder, pas une duplication prouvée).
Le prochain candidat mesuré est `ui/step2_import.py` (2 860 lignes).

## 18. Chantier 7 — les écrans neufs confrontés au code

### La méthode : un registre, pas une planche

Les planches `18` à `21` montraient quatre écrans qui n'existaient pas encore.
La tentation était de les déclarer « faits » parce qu'ils sont beaux. On a
fait l'inverse : chaque phrase montrée à l'utilisateur est devenue une **entrée
de registre** (`drillmaster_v3/core/ecrans/promesses.py`), avec trois états
seulement — jamais deux :

| État | Sens | Ce qu'il exige |
|---|---|---|
| **tenu** | le comportement existe | un cas réel en face, nommé |
| **bloqué** | le comportement est refusé exprès | la raison, en clair |
| **à faire** | la maquette promet, le code ne sait pas | le travail numéroté |

### La confrontation, chiffrée

**4 écrans · 28 promesses · 23 tenues · 5 à faire.**

Trois promesses qui n'étaient que des images sont devenues du code, parce
qu'elles ne demandaient aucune décision de produit :

| Promesse | Ce qui a été écrit |
|---|---|
| « les colonnes du fichier, une par une, avec un exemple » | `Lecture.colonnes` · `Colonne(nom, exemple, rôle)` — une colonne non reconnue est dite « à confirmer », jamais devinée |
| « qui décide » est gardé avec la décision | `projet.exclut(..., par=…)` et `projet.decisions` : action, forage, motif, auteur, date |
| « 5 contrôles avant de vous demander de décider » | `lecture.verifie()` : identifiants, coordonnées, profondeurs, analyses, dates — chacun avec son compte réel, et « rien à vérifier » quand c'est le cas |

Et une promesse fausse a été **corrigée dans la maquette** : `18_import.png`
annonçait « CSM, TXT, Excel, LAS, Shapefile — 12 formats reconnus ». La
lecture ne sait lire que du texte séparé. La planche dit désormais ce qui est
vrai (tableur, décimale et accents compris) et ce qui reste à écrire (Excel,
LAS, Shapefile).

### La règle qui en découle

**R-54 · « Écarté » veut dire absent des calculs, pas caché de l'écran.** Un
forage exclu reste disponible au dessin, en pointillés, avec son motif
(`projet.forages_ecartes()`). Une exclusion qui disparaît fait croire que le
forage n'a jamais existé — et c'est exactement ainsi qu'on perd la confiance
dans une coupe.

**R-55 · Une maquette promet, un cas réel prouve.** Aucune phrase affichée à
l'utilisateur ne peut exister sans une entrée de registre avec sa preuve, ou
son état « à faire ». Un écran ne montre jamais une promesse que rien ne tient.

### Ce qui reste, nommé

| Reste | Pourquoi ce n'est pas fait |
|---|---|
| 11 types de données sans lecteur | un lecteur par type : analyses, lithologie, altérations… |
| Excel, LAS, Shapefile | trois formats, trois lecteurs |
| couleurs et motifs de la coupe peints par le noyau | le rendu vit encore dans l'ancien module |
| export branché sur le noyau | la promesse « ce que vous voyez sera l'export » n'est pas tenue |
| forages écartés dessinés en pointillés | la donnée existe (R-54), le dessin reste à faire |

## 19. Chantier 8 — la navigation : une action, un chemin

### Ce que la mesure a trouvé

`tools/audit_navigation.py` lit le plugin par arbre et compte ce qu'un
utilisateur peut atteindre :

| Mesure | Résultat |
|---|---|
| écrans | **27** (11 fenêtres, 16 panneaux) |
| fenêtres sans porte | **0** — chacune est ouverte quelque part |
| réglages mémorisés | 8 lus, 11 écrits · **0 fantôme** |
| réglages morts | **3** — écrits à la fermeture, jamais relus |
| raccourcis clavier | **6**, dont **4 muets** |

**Deux constats de la première version de l'outil étaient faux**, et c'est ce
qui a coûté le plus de temps : il annonçait « 11 dialogues jamais ouverts »
(il ne comptait que `exec_`/`show`, pas l'instanciation) et « 3 valeurs
fantômes » (il cherchait `setValue(` en début de ligne, ce qui rate un appel
écrit sur deux lignes). Corrigé en analyse par arbre. **Un constat faux est
pire qu'aucun constat** — R-47 s'applique aussi aux outils, pas seulement
aux agents.

### Les quatre touches que personne ne voit

| Touche | Où | Effet |
|---|---|---|
| `Undo` | `section_dock.py:7890` | annuler |
| `Redo` | `section_dock.py:7892` | rétablir |
| `Ctrl+Y` | `section_dock.py:7894` | rétablir (bis) |
| `Ctrl+E` | `section_dock.py:7896` | exporter |

Poseés par `QShortcut` sur un widget, donc **jamais affichés** : celui qui
les connaît va deux fois plus vite, l'autre ne saura jamais qu'elles
existent. `setShortcut()` (utilisé par l'éditeur de fichiers) affiche sa
touche d'office — c'est la bonne façon.

### Les trois réglages morts

`DrillMaster/view3d/bg`, `DrillMaster/view3d/detail`, `DrillMaster/view3d_enabled`
sont écrits à la fermeture. Aucun n'est relu : l'utilisateur règle, puis le
réglage disparaît. Ce sont des promesses que l'interface fait et ne tient pas.

### Les règles

**R-56 · Une action a exactement un chemin.** Deux entrées pour la même
chose dans la même zone sont refusées à la construction du registre.

**R-57 · Ce qui n'est pas atteignable n'est pas écrit.** Un écran qu'aucun
geste n'ouvre est du code mort ; un geste qu'aucun écran ne déclare est une
trappe. Les deux sont mesurés, jamais supposés.

**R-58 · Un raccourci n'existe que s'il est écrit sur le bouton.** Une touche
affichée nulle part est un pouvoir invisible. Tant qu'un geste n'a pas sa
touche imprimée à côté de son libellé, il n'a pas de raccourci.

### Ce qui reste, nommé

| Reste | Pourquoi ce n'est pas fait ici |
|---|---|
| 4 raccourcis muets | il faut les **afficher** sur les boutons (travail d'interface), pas les retirer |
| 3 réglages morts | la vue 3D doit relire ce qu'elle écrit — c'est du code de la vue, pas de la navigation |
| la zone « menu contextuel » est vide au registre | le plugin a des menus contextuels (`section_dock`, `main_dock`) : leur contenu doit entrer au registre |

## 20. Chantier 9 — l'architecture : un pont à sens unique

### Ce que la mesure a trouvé — et les trois erreurs de mon propre outil

`tools/audit_architecture.py` résout les imports comme Python le fait. Il a
d'abord annoncé **0 module du noyau** et **99 orphelins** : trois fautes de
résolution, toutes corrigées (imports relatifs `..` comptés dans le mauvais
sens, séparateurs de chemin, noms d'objets importés confondus avec des
modules). Après correction :

| Mesure | Résultat |
|---|---|
| modules du noyau | **57** |
| fuites du noyau vers l'interface | **0** |
| modules du noyau qui touchent à Qt | **5** — dessin et traduction, permis et mesuré |
| calculs écrits dans les vues | **77**, dans 8 fichiers |
| modules que rien n'importe | **5** — trois outils, deux points d'entrée |

**R-40 est donc tenu** : aucun module de calcul n'importe un widget. Ce qui
n'existe pas n'est pas un défaut — et il ne faut pas inventer un chantier
pour une fuite qui n'a pas lieu.

### Là où le calcul est encore dans la vue

| Fichier | Calculs |
|---|---|
| `ui/view_3d_renderer` | 28 |
| `ui/section_dock` | 21 |
| `ui/section_structure` | 11 |
| `ui/view_3d_overlays` | 9 |
| `ui/view_3d_interaction` | 3 |
| `ui/section_export`, `ui/structure_analysis_dialog` | 2 chacun |
| `ui/section_holes` | 1 |

Ce ne sont pas des erreurs : c'est de la géométrie d'écran (normales,
longueurs, ombrage) écrite à l'endroit où elle s'affiche. Le risque est
connu et chiffré : **la coupe et la 3D peuvent calculer la même chose
différemment**. Le noyau sait déjà faire les trajectoires
(`drillmaster_v3/core/geometrie/trajectoire.py`, trois méthodes, testé).

### Les règles

**R-40 · Le noyau ne connaît pas l'interface.** Aucun import de widget dans
les 57 modules de calcul. Vérifié par `test_aucun_module_du_noyau_n_importe_un_widget`.

**R-41 · Une vue ne calcule pas.** Le plafond est posé à **77** : il ne peut
que diminuer. Un calcul ajouté dans une vue fait échouer le test.

**R-59 · Ce que rien ne branche est nommé, jamais oublié.** Les 5 modules
sans appelant sont listés dans le test : trois outils (`core.benchmark`,
`core.scene3d.synthetic`, `core.ui_audit`) et deux points d'entrée
(`ui.view_3d`, `ui.palette_jetons`, lu par le thème). Aucun n'est du code
mort oublié — et si l'un le devient, le test s'en aperçoit.

### Ce qui reste, nommé

| Reste | Pourquoi ce n'est pas fait ici |
|---|---|
| 77 calculs dans les vues | les sortir est un travail par fichier (chantier 3), pas un déplacement en masse : chaque calcul doit être comparé à son équivalent du noyau |
| `ui/section_structure` (11) | la géométrie des marqueurs a un équivalent partiel côté noyau : à rapprocher |

## 21. Chantier 10 — un mot par chose

### Ce que la mesure a trouvé

`tools/audit_vocabulaire.py` lit les **textes réellement affichés** (chaînes
passées à `setText`, `setToolTip`, `tr`, aux boîtes de message) — pas les
identifiants. Résultat sur **1 857 textes** :

| Objet | Façons de le dire à l'écran |
|---|---|
| forage | `forage` 78 · `trou` 11 (autre sens) · `hole` 3 |
| teneur | `teneur` 27 · `analyse` 8 (autre sens) · `assay` 1 |
| coupe | `coupe` 133 · `section` 24 (autre sens) · `profil` 7 (autre sens) |
| collet | `collet` 43 · `collar` 1 |
| pendage | `dip` 9 · `pendage` 4 |
| piste | `piste` 30 · `voie` 7 |

**Le lexique du dépôt n'était lu par aucun fichier du plugin.** Le chiffre
était déjà connu ; ce que la mesure ajoute, c'est la nuance : une bonne
partie des « doublons » sont des mots qui ont un **autre sens** (`profil
d'affichage`, `trou de forage`, `analyse` pour les valeurs). Les supprimer
aurait été une faute. L'outil les compte à part — 50 occurrences.

### Trois défauts réels trouvés en chemin

| Ce que l'utilisateur voyait | Pourquoi c'est grave |
|---|---|
| `lecture terminée en utf-8-sig` | un nom d'encodage à l'écran |
| `Le fichier n'était pas en UTF-8` | idem, présenté comme un reproche |
| `Afficher azimut / dip` | un mot anglais dans une phrase française |

Corrigés : « lecture terminée », « Les accents du fichier étaient abîmés »,
« Afficher azimut / pendage ». Les maquettes qui montraient `EPSG:32629`
disent maintenant « UTM 29N (mètres) ».

### Un garde-fou qui se trompait

`lexique.verifie()` cherchait les mots bannis **en sous-chaîne** : « cache »
refusait « cach **é** », et le mot banni « sig » refusait « **sig** ne ».
Un garde-fou qui se trompe est pire que pas de garde-fou (R-47). Corrigé :
la comparaison se fait sur des mots entiers.

Et le fichier des mots bannis ne contenait ni `EPSG`, ni `CRS`, ni `None`
alors que le cahier des charges les refuse explicitement depuis le début :
ajoutés. En revanche `csv` et `utf-8` ont été **retirés** — ce sont des
formats que le géologue connaît, pas du vocabulaire de développeur.

### Les règles

**R-60 · Un mot par chose.** Le mot se choisit une fois, se documente, et
un test vérifie qu'aucune variante ne revient. Le critère : le mot que le
géologue emploie quand il parle à un confrère.

**R-61 · Un lexique que personne ne lit n'existe pas.** `specs/data/lexique.json`
est la source ; le plugin en embarque une copie (`DrillMaster/core/lexique.json`)
et `tools/synchronise_lexique.py` refuse la dérive. Mesure avant : **0**
fichier du plugin le lisait. Après : **1**, et la copie est comparée au
fichier source par un test.

### Ce qui reste, nommé

| Reste | Pourquoi ce n'est pas fait ici |
|---|---|
| 9 `dip` dans les textes affichés | chaque cas demande de lire la phrase : « dip » seul dans une infobulle n'est pas « pendage » partout |
| 24 `section` | c'est un nom de classe passé à l'affichage : la correction est un nettoyage d'appels, pas un remplacement de mot |
| `core.vocabulaire` sans appelant d'écran | il attend le premier écran réécrit ; son absence d'appelant est nommée dans le test d'architecture |
