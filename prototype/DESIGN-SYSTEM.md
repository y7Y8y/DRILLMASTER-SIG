# Design System — Atelier géologique · prototype V01

Proposition à évaluer dans le navigateur avant toute adaptation Qt/QGIS. Ne pas confondre les éléments d'interface avec les couleurs scientifiques des données.

## Identité

Une surface claire et silencieuse, une navigation vert profond et un accent minéral doux composent un environnement de travail géologique sans concurrencer les données. La marque graphique évoque les strates et le forage ; c'est une proposition, pas une identité définitive. Le canevas cartographique fictif est une illustration, pas un résultat scientifique.

## Tokens appliqués

| Rôle | Valeur | Usage |
|---|---|---|
| Encre | `#202c28` | Texte principal |
| Surface | `#f5f6f3` / `#ffffff` | Fond général / panneaux |
| Navigation | `#263c32` | Rail latéral |
| Action | `#315c48` | Action principale |
| Accents de carte | `#c48d5c` | Tracé illustratif, jamais seul porteur d'information |
| Limites | `#e7ebe5` | Séparation décorative ; pas le seul indicateur du focus |

Typographie : police système, base 13 px CSS pour le prototype, titres 16–27 px selon rôle. Ces valeurs ne sont pas des tailles figées pour Qt. Espacements récurrents : 4/8/12/16/24/32 px, avec ajustements optiques. Panneaux blancs à angles sobres et séparations légères ; boutons, états, étiquettes, dialogues et tableaux partagent le même vocabulaire. Icônes SVG simples, associées à des noms accessibles.

Focus clavier : contour contrasté, sans dépendre de la couleur d'état. États : sélection du rail, étape et onglet ; survol, focus, badges textuels ; dialogues natifs HTML. L'accessibilité complète, les contrastes de toutes les couleurs secondaires et la traduction, ainsi que les thèmes sombres et gros caractères, restent à tester et affiner. Les grisés légers de cette première maquette peuvent être insuffisants et ne sont pas une palette de production validée.

## Passage éventuel à Qt/QGIS

Conserver les contrôles natifs et personnaliser localement contexte, étapes, panneaux et statuts. Utiliser métriques de police, DPI et palette QGIS ; éviter une feuille de style globale ou la suppression du focus. Les dimensions du prototype ne sont pas à recopier mécaniquement. Une revue QGIS claire/sombre et clavier reste obligatoire.

## V02 — cinq espaces de travail

Les écrans de travail réemploient le vert profond, les surfaces neutres, les boutons, tableaux et panneaux de contexte. Les textes secondaires principaux ont été assombris ; les états qualité utilisent systématiquement un libellé en plus de la couleur. Les panneaux assistant et contexte peuvent être masqués. Les réglages de vue et la sélection ont des portées distinctes ; les schémas affichent explicitement leur caractère fictif et non géoréférencé. Les critères de contraste, de navigation clavier et de compatibilité Qt/QGIS restent à vérifier en conditions réelles : cette déclinaison n'est pas une certification d'accessibilité.
