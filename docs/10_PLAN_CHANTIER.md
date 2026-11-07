# 10 — Le chantier, dans l'ordre

> La flotte (42 agents, 8 départements) a rendu son rapport : `09_RAPPORT_FLOTTE.md`.
> **80 constats**, dont 10 bloquants. Voici ce qu'on fait, et dans quel ordre.

## Où on en est

| | |
|---|---|
| Plugin lu | **105 fichiers**, 56 577 lignes |
| Agents | 42, dans 8 départements |
| Constats | 80 — 10 bloquants · 41 majeurs · 29 mineurs |
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

## Le plan, en 7 chantiers

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
