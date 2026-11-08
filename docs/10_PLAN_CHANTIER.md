# 10 — Le chantier, dans l'ordre

> La flotte (42 agents, 8 départements) a rendu son rapport : `09_RAPPORT_FLOTTE.md`.
> **108 constats**, dont 10 bloquants. Voici ce qu'on fait, et dans quel ordre.

## Où on en est

| | |
|---|---|
| Plugin lu | **105 fichiers**, 56 577 lignes |
| Agents | 67, dans 13 départements |
| Constats | 108 — 10 bloquants · 55 majeurs · 40 mineurs · 3 notes |
| Maquettes | 22 planches, dont **4 écrans neufs** et **1 charte** |
| Tests | **63 tests**, 62 vérifications de spec, 0 écart |

## Les 10 bloquants, et ce qu'ils coûtent à l'utilisateur

| # | Constat | Mesure | Ce que ça casse |
|---|---|---|---|
| F-01 | Un réglage, plusieurs propriétaires | la largeur se règle dans 12 endroits | règle la coupe, la 3D ne change pas |
| F-01 | idem opacité | 8 endroits, 4 fichiers | idem |
| F-01 | idem côté | 8 endroits, 6 fichiers | idem |
| F-01 | idem étiquettes | 6 endroits, 4 fichiers | deux légendes différentes |
| T-01 | Géométrie recalculée dans les vues | 8 fichiers, 23 calculs trigo | la coupe et la 3D divergent |
| M-05 | Erreur technique à l'écran | 3 endroits | `KeyError` face à l'utilisateur |
| B-02 | Suppressions sans confirmation | 4 actions | une coupe disparaît d'un clic |
| M-03 | Jargon dans les textes | EPSG, CRS, None… | le géologue décroche |
| M-01 | Modales bloquantes | 29 fenêtres | on clique « OK » sans lire |
| M-04 | Absences non annoncées | 212 mentions pour 1 458 | un panneau vide laisse croire « rien à voir » |

## Le plan : 2 programmes, 7 chantiers

Les 108 constats sont tous affectés, aucun orphelin.

### Programme A — Rendre le socle cohérent (chantiers 1 à 3)
Rien de nouveau à l'écran. On supprime les doublons : 12 propriétaires pour une
largeur deviennent 1, 8 calculs de géométrie deviennent 1, 655 couleurs
deviennent 21 jetons.

### Programme B — Rendre l'interface utilisable (chantiers 4 à 7)
Messages, boutons, rangements, écrans neufs. C'est ce que l'utilisateur voit.

### Répartition des 80 constats

| Chantier | Constats | dont bloquants |
|---|---|---|
| 1 · Socle visuel | 10 | 0 |
| 2 · Un réglage, un propriétaire | 7 | **4** |
| 3 · Un seul calcul de géométrie | 2 | 1 |
| 4 · Les messages | 10 | 1 |
| 5 · Boutons et gestes | 6 | **4** |
| 6 · Les rangements | **38** | 0 |
| 7 · Écrans neufs | 7 | 0 |
| **8 · Navigation et options cachées** | **7** | **1** |
| **9 · Architecture du code** | **8** | 0 |
| **10 · Vocabulaire** | **4** | 0 |
| **11 · Vitesse et robustesse** | **9** | 0 |
| **12 · Installation dans QGIS** | **2** | 0 |
| **Total** | **108** | **10** |

## Chantier 8 — Navigation et options cachées (nouveau)

Réponse mesurée à « y a-t-il des options cachées, des onglets mal gérés ? »
Oui, quatre cas, et un point rassurant.

| Constat | Mesure | Verdict |
|---|---|---|
| **N-01** Réglages enfermés dans une fenêtre | `ReferenceDialog` : **8 réglages** ; `LithologyStructureDialog` : 6 | **bloquant** : la fenêtre fermée, les options sont introuvables |
| **N-02** Barres d'onglets masquées | **2** endroits (`main_dock`, `step2_import`) | un seul panneau est atteignable ; un second deviendrait invisible |
| **N-04** Réglages sur le poste, pas dans le projet | **26 accès**, 8 clés nommées | un collègue ne retrouve pas la configuration |
| **N-05** 39 fichiers d'interface | 3d 11 · section 9 · dialog 6 · step 4 | aucune frontière par responsabilité |
| **N-06** Aide contextuelle | **102 infobulles pour 235 contrôles (43 %)** | plus d'un contrôle sur deux n'explique rien |
| N-08 Fil d'Ariane | présent (`stepper`) | **rien à faire** |

**Le point rassurant** : l'aide contextuelle n'est pas absente, elle est à
43 %. Ce n'est donc pas un chantier de création, c'est un chantier de
complètement — beaucoup moins cher que prévu.

### Les meilleures options, concrètement

Ce que la flotte recommande pour rendre les options **optimales** :

1. **Zéro fenêtre porteuse de réglages.** Une fenêtre ne sert qu'à choisir un
   fichier. Tout réglage vit dans le panneau, ou dans un repli « avancés ».
2. **Un repli « avancés » par écran, pas par option.** 6 visibles, le reste
   derrière un seul bouton qui se souvient de son état.
3. **Deux catégories de réglages nommées** : *préférences de poste* (thème,
   langue) et *réglages de projet* (pistes, seuils, couleurs). Les seconds
   voyagent avec le projet.
4. **Onglets assumés ou supprimés.** Pas de barre masquée : soit un panneau
   unique, soit des onglets nommés et visibles.
5. **100 % d'infobulles utiles** : ce que ça change + où ça s'applique.

## Chantier 9 — Architecture du code (nouveau)

C'est le département que tu as demandé : celui qui juge le **code**, pas
l'écran. Huit agents, huit réponses.

| Constat | Mesure | Ce que ça veut dire |
|---|---|---|
| **A-01** Le noyau dépend-il de l'interface ? | **non, 0 import** | bonne nouvelle : le calcul peut vivre sans QGIS |
| **A-02** Calcul mélangé à l'affichage | `SectionWidget` : **5 295 lignes, 172 méthodes, 45 calculs** | la moitié du plugin tient dans une classe |
| **A-04** Infos partagées | attributs recopiés dans 3+ fichiers | deux vues peuvent avoir deux versions |
| **A-05** Gestion des erreurs | **15 affichages dispersés, 0 point central** | le même incident donne 3 messages |
| **A-06** Coût d'une extension | un domaine est cité dans **30 fichiers en moyenne** (« structure » : 42) | ajouter un type de données = une semaine |
| **A-07** Chargement des fichiers | **13 lectures dans 5 fichiers** | deux imports du même fichier, deux résultats |
| **A-03** Noms | **39 fonctions de 1 à 4 lettres** (`mk`, `n`, `run`) | le prochain développeur relit tout |
| **A-08** Constantes | 4 redéfinies (`PROFILES`, `MAX_ASSAY_ELEMENTS`…) | une correction n'atteint qu'une copie |

**La réponse à ta question sur les extensions** : aujourd'hui, ajouter un
domaine de données coûte cher — non pas parce que le calcul est difficile, mais
parce que son nom est écrit dans **30 fichiers**. La correction ne demande pas
de réécrire : elle demande de faire lire au code la table des domaines qui
existe déjà (`specs/data/lexique.json`).

## Chantier 10 — Vocabulaire

| Constat | Mesure |
|---|---|
| V-01 Deux noms pour le même objet | `hole` 790× / `forage` 326× · `assay` 413× / `teneur` 170× |
| V-02 Le lexique existe, le code ne le lit pas | **0 fichier** du plugin importe `lexique.json` |
| V-03 Textes trop longs | paragraphes de plus de 140 caractères dans des panneaux de 300 px |

## Chantier 11 — Vitesse et robustesse

| Constat | Mesure |
|---|---|
| P-01 Mesure de temps | 3 modules de mesure existent — mais rien n'est publié |
| P-02 Calcul sur le fil d'affichage | `section_dock.py` : **196 boucles** sans tâche de fond |
| P-03 Garde-fou sur les gros fichiers | présent (2 seuils) — rien à faire |

## Chantier 12 — Installation dans QGIS

| Constat | Mesure |
|---|---|
| E-01 Fiche d'installation incomplète | le champ `email` manque dans `metadata.txt` |
| E-03 Compatibilité | maximum déclaré `3.99` — QGIS 4 / Qt 6 non couvert |
| E-02 Désinstallation | **propre** : `unload()` retire le dock et les actions |

## Le détail des chantiers

### Chantier 1 — Le socle visuel — 🟡 **le pont est livré, la conversion continue**

`theme.json` existait mais **rien ne le lisait**. Le plugin avait sa propre
palette (`styles_qt.COLORS`, 17 teintes terreuses) : **deux vérités**. La DA a
donc été câblée au plugin, et pas seulement documentée.

| Livré | Preuve |
|---|---|
| `tools/genere_palette.py` — génère la copie Qt du thème | sort en 1 si le module a dérivé |
| `DrillMaster/ui/palette_jetons.py` — 18 rôles × 2 modes, `couleur()`, `paire()` | seul foyer de chrome du plugin |
| `tools/audit_couleurs.py` — mesure les trois catégories | `specs/data/audit_couleurs.json` |
| `specs/tests/test_palette.py` — 7 tests | dérive, couverture, rôle inconnu, unicité |
| `maquettes/26_socle.png` — chaîne de vérité + correspondance rôle par rôle | relue |
| R-50, R-51 (docs/07 §16) | — |

**Ce qui reste, chiffré** : 44 déclarations dans `styles_qt.COLORS` (304 usages
à repointer en façade) et **417 couleurs dans 30 feuilles de style**. Une
migration automatique a été tentée trois fois et **échoue** : une couleur au
milieu d'une feuille de style exige que la chaîne devienne une f-string ; un
`re.sub` produit du code invalide. **Décision : fichier par fichier, avec
compilation vérifiée après chacun.** Rien n'est maquillé.

### Chantier 2 — Un réglage, un propriétaire — ✅ **livré (cœur)**

`drillmaster_v3/core/reglages.py` + 12 tests. Un seul écrivain, cinq lecteurs,
journal, bornes lues dans le contrat. Preuve : `python3 tools/demo_reglages.py`.

C'est **le** défaut qui explique « taille doit se répéter et rien ».
Aujourd'hui : largeur, opacité, côté et étiquettes sont réglables dans 4 à 6
fichiers. On crée **une** structure `Piste` (15 champs, déjà spécifiée en
`specs/data/tracks.json`), et les vues n'en gardent qu'un miroir en lecture
seule. Modifier la largeur une fois change la coupe, la 3D, la légende,
l'export et la carte.

### Chantier 3 — Un seul calcul de géométrie

8 fichiers de vue font de la trigonométrie. On branche toutes les vues sur
`drillmaster_v3/core/geometrie/` (déjà écrit et testé : 63 tests verts).
La coupe et la 3D ne peuvent plus diverger.

### Chantier 4 — Les messages — ✅ **contenu livré (30/30)**

`core/bandeau.py` + `core/messages_plugin/` : 30 messages à 5 champs, un par
fenêtre du plugin, identifiés par `fichier:ligne`. 23 tests. Reste la
conversion des 30 appels dans `DrillMaster/ui/` (mécanique).
Preuve : `python3 tools/demo_messages.py`.

- Supprimer les 29 modales d'information → bandeau à 5 champs (R-20).
- 4 textes techniques réécrits en mots simples.
- Un filet unique pour les erreurs imprévues + bouton « Copier le détail ».
- Les absences annoncées : chaque domaine a trois états (fourni, non fourni,
  en réserve).

### Chantier 5 — Boutons et gestes — ✅ **livré**

`core/gestes.py` + 10 gestes réels réécrits (3 barres) + 14 tests.
**Deux constats de la flotte étaient faux** : les 4 « suppressions sans filet »
ne détruisent rien (couches régénérables), et la suppression réelle de projet
demandait déjà trois protections. Le vrai défaut — l'annonce avant le clic —
est corrigé. Preuve : `python3 tools/demo_gestes.py`.

- 3 rôles, un seul primaire par écran.
- Toute suppression : confirmation qui dit **ce qui sera perdu**, puis
  « annuler » après coup.
- Tout bouton est relié, ou il n'existe pas ; un bouton désactivé dit pourquoi.

### Chantier 6 — Les rangements — 🟡 **tranche 1 livrée, le cliquet est posé**

`section_dock.py` pesait **11 529 lignes**. Il en fait **10 515** : le socle
de la coupe (couleurs d'interaction, motifs, encres, items graphiques) est
sorti dans `ui/coupe_socle.py`, et les **801 lignes de journal de versions**
ont quitté la docstring pour `docs/HISTORIQUE_section_dock.md`. Aucun appelant
n'a changé : tout est ré-exporté.

| Livré | Preuve |
|---|---|
| `ui/coupe_socle.py` (288 lignes, 16 noms) | `test_les_noms_vivent_dans_le_socle` |
| `docs/HISTORIQUE_section_dock.md` | journal intégral, hors du code |
| `tools/audit_rangement.py` | `specs/data/rangement.json`, relancé à chaque tranche |
| `specs/tests/test_rangement.py` — 7 tests | cliquets : 10 560 lignes max, 1 seul fichier géant |
| `maquettes/27_rangements.png` | relue |
| R-52, R-53 (docs/07 §17) | — |

**Ce qui reste, chiffré** : 6 fichiers > 1 500 lignes · 996 lignes de
commentaire d'historique encore dans le code · 39 noms partagés entre
fichiers. Prochain candidat mesuré : `ui/step2_import.py` (2 860 lignes).

### Chantier 7 — Les écrans neufs — 🟡 **confrontés au code, 23 promesses sur 28**

Les planches `18` à `21` sont devenues un **registre** : chaque phrase
montrée est une promesse avec sa preuve ou son état « à faire »
(`drillmaster_v3/core/ecrans/promesses.py`). Mesure : **4 écrans · 28
promesses · 23 tenues · 5 à faire**.

| Livré | Preuve |
|---|---|
| `Lecture.colonnes` — nom, exemple, rôle ; une colonne incertaine est dite telle | `test_colonnes_montrees_avec_exemple_et_role` |
| `lecture.verifie()` — les 5 contrôles avant toute décision | `test_cinq_controles_sont_calcules` |
| `projet.decisions` — qui, quand, pourquoi ; réintégrer n'efface rien | 3 tests |
| `projet.forages_ecartes()` — R-54, écarté ≠ caché | `test_le_forage_ecarte_reste_disponible_au_dessin` |
| `tools/confronte_ecrans.py` | la liste, relancée à chaque passage |
| `specs/tests/test_ecrans.py` — 18 tests sur des fichiers réels | verts |
| `maquettes/28_ecrans.png` | relue |
| R-54, R-55 (docs/07 §18) | — |

**Reste, nommé** : 11 types de données sans lecteur · Excel, LAS, Shapefile ·
rendu de la coupe par le noyau · export branché · écartés en pointillés.

## Ce qui n'est pas dans ce plan, et pourquoi

| Sujet | Pourquoi il attend |
|---|---|
| Nouveaux modules (structures, imagerie) | on ne construit pas sur un socle qui duplique les réglages |
| Nouvelles options | d'abord finir les 5 champs du contrat qui n'ont aucun contrôle |
| Refonte 3D | 21 fichiers pour une seule vue : il faut d'abord en supprimer |

## Ordre imposé

1 → 2 → 3 → 4 → 5 → 6 → 7. Les chantiers 1 à 3 ne changent **aucune**
fonctionnalité : ils rendent les suivants possibles. C'est pour ça qu'ils
passent en premier, même s'ils ne se voient pas.
