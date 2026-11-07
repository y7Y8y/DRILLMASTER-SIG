# 10 — Le chantier, dans l'ordre

> La flotte (42 agents, 8 départements) a rendu son rapport : `09_RAPPORT_FLOTTE.md`.
> **86 constats**, dont 10 bloquants. Voici ce qu'on fait, et dans quel ordre.

## Où on en est

| | |
|---|---|
| Plugin lu | **105 fichiers**, 56 577 lignes |
| Agents | 50, dans 9 départements |
| Constats | 86 — 10 bloquants · 46 majeurs · 30 mineurs |
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

Les 86 constats sont tous affectés, aucun orphelin.

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
| Continu · qualité et doctrine | — | — |
| **Total** | **86** | **10** |

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

## Le détail des chantiers

### Chantier 1 — Le socle visuel (1 passage, mécanique)

Créer `theme.json` dans le plugin et remplacer les 655 couleurs littérales et
les 320 feuilles de style par des rôles. **Aucune décision de goût** : la charte
`maquettes/23_charte.png` a déjà tout fixé.

- Couleur : 8 jetons de chrome + 1 accent + 5 états + couleurs de données.
- Typographie : 6 tailles (R-33).
- Espace : grille de 4 px (R-34).
- Boutons : 3 rôles (R-35).
- **Preuve** : `spec_check` refuse un littéral `#RRGGBB` dans `DrillMaster/ui/`.

### Chantier 2 — Un réglage, un propriétaire (le cœur du problème)

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

### Chantier 4 — Les messages

- Supprimer les 29 modales d'information → bandeau à 5 champs (R-20).
- 4 textes techniques réécrits en mots simples.
- Un filet unique pour les erreurs imprévues + bouton « Copier le détail ».
- Les absences annoncées : chaque domaine a trois états (fourni, non fourni,
  en réserve).

### Chantier 5 — Les boutons et les gestes

- 3 rôles, un seul primaire par écran.
- Toute suppression : confirmation qui dit **ce qui sera perdu**, puis
  « annuler » après coup.
- Tout bouton est relié, ou il n'existe pas ; un bouton désactivé dit pourquoi.

### Chantier 6 — Les rangements

`section_dock.py` fait **11 529 lignes** : il contient à lui seul la moitié des
défauts de rangement. On le découpe par responsabilité (dessin, réglages,
export, historique) avant toute nouvelle fonctionnalité dessus.

### Chantier 7 — Les écrans neufs

Ceux déjà maquettés, qui n'existent pas encore dans le plugin :
**Import** (`18`), **Blocage** (`19`), **Coupe finie** (`20`),
**Exclusions** (`21`).

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
