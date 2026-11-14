# DrillMaster ORIG — Architecture de référence (v0.1)

Refonte de A à Z du plugin DrillMaster, mieux pensée, mieux écrite,
mieux catégorisée. Ce document est la loi du projet : tout module doit
pouvoir citer la règle qu'il applique.

## Positionnement

L'alternative libre et maîtrisée à Micromine/Leapfrog pour le workflow
80 % : import → validation QC → trajectoires 3D → coupes 2D → vue 3D →
export auditables. Minimalisme maîtrisé (docs/DESIGN.md du v2, charte
reprise ici).

## Règles absolues (héritées du v2, éprouvées)

1. **Une seule convention de coordonnées, déclarée une seule fois**
   (`core/units.py`) : X=Est, Y=Nord, Z=élévation positive vers le haut,
   profondeur >= 0 depuis le collet, azimut [0°, 360°[ depuis le Nord,
   **dip signé, POSITIF VERS LE BAS** (0° horizontal, +90° vertical bas).
   Le v2 documentait deux conventions contradictoires (geometry.py vs
   spatial_model.py) — interdit ici.
2. **L'exagération verticale est un paramètre de rendu** : elle ne
   modifie JAMAIS les coordonnées sources.
3. **Le cœur est pur** : `core/` n'importe ni QGIS ni Qt. Testable
   standalone (les tests tournent ici, sans QGIS).
4. **Data-ink** : la couleur est réservée aux données et aux statuts ;
   le chrome travaille en valeurs de gris.
5. **Auditabilité** : tout export embarque ses paramètres complets ;
   toute valeur affichée est traçable au CSV source (TRUST-1).

## Couches

```
DrillMasterOrig/
├── metadata.txt          Plugin QGIS (experimental=True tant que v0.x)
├── __init__.py           classFactory → qgis/plugin.py
├── core/                 PUR — zéro QGIS/Qt, testé standalone
│   ├── units.py          Conventions, conversions, constantes
│   ├── model.py          Collar, SurveyStation, Interval, DrillHole
│   └── trajectory.py     Trajectoires : courbure minimale (défaut),
│                         angle moyen (compat v2), validation
├── qgis/                 COQUILLE FINE — tout ce qui touche QGIS/Qt
│   ├── plugin.py         Cycle de vie plugin, docks, menus
│   ├── design_tokens.py  Tokens DA (mêmes valeurs que le v2)
│   └── dock.py           Dock principal (squelette wizard)
└── tests/                pytest, cœur pur uniquement
```

## Ce qu'on prend du v2 / ce qu'on refait

| Domaine | Décision |
|---|---|
| Conventions spatiales, modèle de données | **Pris** (adapté, une seule doc de convention) |
| Trajectoires | **Amélioré** : courbure minimale en défaut (le v2 : angle moyen), angle moyen conservé pour compatibilité |
| Parsing CSV, validation QC | **Pris** à la tranche suivante (adaptation API propre) |
| UI (docks, panneaux, wizard) | **Refait** — fabriques de composants dès le premier écran, pas de monstre 11 000 lignes : 1 fichier = 1 département |
| Rendu 2D/3D | **Refait** par tranches, après le cœur données |

## Discipline de croissance

- Une tranche = un lot testé, livré, documenté. Jamais deux tranches
  entremêlées.
- Toute nouvelle option UI passe par les fabriques ; toute nouvelle
  couleur passe par `design_tokens.py`.
- 1 fichier = 1 responsabilité. Un fichier qui dépasse ~800 lignes est
  signalé et découpé.
