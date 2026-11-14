# DrillMaster — Direction artistique (charte v1)

Objectif : un plugin **révolutionnaire mais évident** — minimalisme maîtrisé
à la Apple/HIG, adapté à la densité d'un outil géologique dans QGIS.

## Principes

1. **Data-ink (Tufte)** — la couleur est un canal d'information réservé aux
   DONNÉES (lithologie, altération, teneurs, structures). Le chrome
   (boutons, panneaux, libellés, cadres) travaille en VALEUR : blanc, gris,
   anthracite. Aucune teinte de chrome ne peut concurrencer une teinte de
   donnée.
2. **Hiérarchie par le poids, pas par la couleur** — un titre se distingue par
   la taille et le graisse, jamais par une teinte.
3. **Échelles fermées** — aucune valeur hors échelle pour la typographie,
   l'espacement, les rayons. L'inventaire de valeurs est un actif : on
   l'appauvrit volontairement.
4. **Récurrence des catégories** — une même catégorie d'option (taille,
   espacement, couleur) se présente TOUJOURS de la même façon, quel que soit
   le groupe qui l'héberge. Un utilisateur apprend une fois, reconnaît partout.
5. **Progressive disclosure** — l'aide est repliée (`make_collapsible_help`),
   les options avancées dans des groupes secondaires, jamais noyées au premier
   niveau.

## Tokens (source de vérité : `ui/design_tokens.py`)

### Couleurs

| Rôle | Token | Valeur |
|---|---|---|
| Encre principale | `primary` | `#17202A` |
| État actif | `accent` | `#1C2833` |
| État actif survolé | `accent_hover` | `#2A3C4D` |
| Succès | `success` | `#196F3D` |
| Avertissement | `warning` | `#E67E22` |
| Danger | `danger` | `#922B21` |
| Fond principal | `bg_main` | `#F8F9F9` |
| Carte | `bg_card` | `#FFFFFF` |
| Survol discret | `hover_subtle` | `#EDEFEF` |
| Survol marqué | `hover_strong` | `#D5DBDB` |
| Désactivé (fond / encre) | `disabled_bg` / `disabled_ink` | `#ECF0F1` / `#95A5A6` |
| Surface sombre (logs) | `surface_code` | `#1E1E1E` |

Interdits : tout bleu de chrome (`#D6EAF8`, `#AED6F1`, …), toute teinte
saturée hors statuts.

### Typographie — échelle fermée

| Token | Taille | Usage |
|---|---|---|
| `annotation` | 7.5pt | libellés du stepper, micro-annotations |
| `small` | 8pt | tableaux, onglets, hints, sous-titres |
| `compact` | 8.5pt | boutons compacts, cases à cocher |
| `body` | 9pt | corps, boutons, champs |
| `title` | 11pt | titres de panneaux |
| `display` | 24pt | splash uniquement |

Police : `Segoe UI` (fallback Sans Serif). Monospace : `Consolas` (logs).

### Espacement (px) : 2 / 4 / 8 / 12 / 16 / 24 — Rayons : 3 (champs) / 6 (cartes)

## Règles de composants

- **Bouton primaire** : anthracite plein, encre blanche, non gras. Un seul par
  vue.
- **Bouton secondaire** : carte blanche, bordure `border_dark`.
- **Bouton de statut** (succès/danger) : réservé aux actions qui confirment ou
  détruisent ; jamais décoratif.
- **Désactivé** : fond `disabled_bg`, encre `disabled_ink` — jamais une teinte.
- **Survol** : éclaircissement de la même valeur, jamais un changement de teinte.
- **Infobulles** : surface sombre, encre `ink_on_dark_hi`, portées par
  `TOOLTIP_STYLE` sur chaque contexte stylé (règle v2.7.12.8 inchangée).

## Gouvernance anti-dérive

- Toute nouvelle couleur/typographie passe par `design_tokens.py`.
- Interdit d'écrire un hex littéral dans un module UI hors tokens (cible
  QA-1 : lint dédié).
- Toute dérogation se justifie dans le commentaire de version du module.
