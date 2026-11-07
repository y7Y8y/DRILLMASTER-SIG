# 02 — Modèle de paramètres : le Contrat de Piste

> **Décision D-002.** C'est le document le plus important du chantier.
> Il doit être tranché **avant** les maquettes, sinon les maquettes gravent la duplication actuelle.

---

## Le principe en une phrase

> **Une piste se déclare une fois. Toutes les vues (2D, 3D, légende, export, carte QGIS) la lisent.**

Aujourd'hui : 10 pistes × 10 jeux de clés faits main = 78 clés plates.
Demain : **1 déclaration par piste** + **3 réglages globaux** + **N réglages spécifiques déclarés par le module propriétaire**.

---

## 1. Les trois étages (et rien d'autre)

```
┌─ ÉTAGE 1 · GLOBAL PROJET ──────────────────────────────┐
│  Ce qui définit la vue, pas la piste.                  │
│  unités · CRS · exagération · échelle · buffer         │
│  fenêtre d'élévation · thème clair/sombre · tolérances │
└────────────────────────────────────────────────────────┘
┌─ ÉTAGE 2 · CONTRAT DE PISTE ───────────────────────────┐
│  Ce que TOUTE piste possède, sans exception.           │
│  14 emplacements — identiques pour les 10 pistes.       │
└────────────────────────────────────────────────────────┘
┌─ ÉTAGE 3 · SPÉCIFIQUE (déclaré par le module) ─────────┐
│  Ce qui n'appartient qu'à une piste.                   │
│  Le cœur ne les connaît pas ; il les range et les rend. │
└────────────────────────────────────────────────────────┘
```

**Règle d'or :** si un réglage apparaît dans 2 pistes, il **monte** à l'étage 2. S'il n'apparaît que dans une, il **reste** à l'étage 3. Il n'existe pas de 4ᵉ cas.

---

## 2. Étage 2 — le Contrat de Piste (14 emplacements)

| # | Emplacement | Type | Commun à | Défaut |
|---|---|---|---|---|
| 1 | `id` | texte stable | toutes | — |
| 2 | `label` | texte traduit | toutes | — |
| 3 | `visible` | booléen | toutes | hérité |
| 4 | `order` | entier | toutes | ordre déclaré |
| 5 | `side` | `left` / `right` / `overlay` | toutes | déclaré |
| 6 | `width` | réel (px écran) | toutes | hérité du type |
| 7 | `gap` | réel (px) | toutes | 4 |
| 8 | `opacity` | 0–100 | toutes | 100 |
| 9 | `fill` | `reference` / `scale` / `fixed` | toutes | selon type |
| 10 | `stroke` | `auto` / couleur / épaisseur | toutes | auto |
| 11 | `label_text` | `font_size`, `color`, `position`, `offset` | toutes | hérité |
| 12 | `tooltip` | gabarit de champs | toutes | champs par défaut |
| 13 | `filter` | expression de domaine | toutes | aucun |
| 14 | `export` | `visible` / `hidden` / `simplified` | toutes | visible |

**Ce que ça corrige immédiatement :**
- la largeur existe pour les 10 pistes (y compris RQD) ;
- l'opacité existe pour les 10 ;
- le côté existe pour les 10 ;
- les noms sont **uniques** (`side`, jamais `alter_side` / `structure_side`) ;
- l'export cesse d'être un cas particulier.

### Héritage (le vrai gain)

Chaque emplacement peut prendre la valeur `hérité`. Trois niveaux de cascade :

```
Projet  ──►  Type de piste  ──►  Piste
(opacité 90)   (catégorielle: 100)   (Lithologie: 70)
```

Régler « opacité » une fois au niveau **type** l'applique aux 6 pistes catégorielles, sauf celles qui ont une valeur explicite. **C'est la réponse à « taille doit se répéter » : on ne la répète plus, on l'hérite — et on peut la forcer par piste.**

---

## 3. Étage 3 — les types de piste (5, pas 10)

Les 10 pistes actuelles tombent dans **5 types** ; le type décide des réglages spécifiques.

| Type | Pistes actuelles | Réglages spécifiques autorisés |
|---|---|---|
| **Catégorielle** | Lithologie, Altération, Minéralisation, Structures | motif, légende, couleur = Référentiel |
| **Quantitative** | Teneurs, RQD, Récupération, Densité | échelle, classes, rampe, méthode (Jenks/linéaire/manuel) |
| **Ponctuelle** | Structures (mesures), Collets | forme du marqueur, taille, espacement minimal |
| **Média** | Imagerie | vignette, résolution, texte alternatif |
| **Structurelle** | Profondeurs, Trajectoire, Intercepts | pas de contenu : position et géométrie seulement |

**Bénéfice mesurable :** « classe de teneur » se règle **une fois par piste quantitative**, et le géotechnique en profite automatiquement — au lieu d'un magasin séparé.

---

## 4. Ce que ça donne dans le code

```python
# core/tracks/registry.py  — UNE déclaration par piste
TRACKS = (
    TrackSpec(
        id="lithology", type=CATEGORICAL, side=LEFT, width=17,
        fill="reference",            # couleur lue au Référentiel
        pattern="reference",         # motif lu au Référentiel
        specific=(),                 # rien de plus
    ),
    TrackSpec(
        id="assays", type=QUANTITATIVE, side=RIGHT, width=15,
        fill="scale",                # couleur = rampe calculée
        specific=("method", "n_classes", "breaks", "ramp", "scale_scope"),
    ),
    TrackSpec(
        id="rqd", type=QUANTITATIVE, side=RIGHT, width=13,
        fill="scale", specific=("ramp", "range"),
    ),
)
```

Les vues ne demandent plus « donne-moi `alter_width` » :

```python
style = project.track_style("alterations")   # → TrackStyle
canvas.draw(track, style)                    # 2D
scene.add_layer(track.id, style)             # 3D
legend.render(track, style)                  # légende
export.render(track, style)                  # export
```

**Une piste, un style, quatre vues.** Le même objet. Toujours.

---

## 5. Migration des 78 clés (aucune perte)

| Groupe actuel | Nb | Destination |
|---|---:|---|
| `show_*` (10) | 10 | Étage 2 · `visible` |
| `*_width` / `*_opacity` / `*_side` | 18 | Étage 2 · `width` / `opacity` / `side` |
| `*_font_size` (6) + couleurs | 10 | Étage 2 · `label_text` |
| `structure_marker_size`, `structure_min_spacing`, `depth_tick_*`, `depth_label_every`, `depth_step` | 8 | Étage 3 · spécifique du type |
| `assay_max_width`, `assay_width_mode`, seuils, rampes | 2 + `assay_style` | Étage 3 · spécifique quantitative |
| `grid_*`, `axis_*`, `show_*_values` (17) | 17 | Étage 1 · global (cadre/axes) |
| `collar_*` annotations (11) | 11 | Étage 2 · `label_text` d'une pseudo-piste « annotations » |
| `orientation_*`, `scale_*` | 6 | Étage 1 · cartouche |
| `show_surface`, `surface_color`, `surface_qc_threshold` | 3 | Étage 3 · type média/spécifique topographie |
| `buffer_mode`, `shared_collar_tolerance`, `show_buffer_on_map` | 3 | Étage 1 · global |
| **Total** | **78** | **0 perdue** |

Ajout obligatoire : `show_rqd`, `rqd_width`, `show_recovery`, `recovery_width`, `show_density`, `density_width` + opacité/côté → **9 clés manquantes** entrent dans le contrat.

### Compatibilité
Un lecteur de configuration traduit l'ancien → nouveau au chargement, et **écrit dans l'ancien format tant que le projet n'est pas ouvert par la v3**. Aucun projet existant ne casse : c'est la règle déjà appliquée par `get_section_style()` (4 migrations legacy) — on la systématise.

---

## 6. Décisions à entériner

| # | Question | Recommandation |
|---|---|---|
| D-002.1 | Les pistes géotechniques rejoignent-elles le modèle commun ? | **Oui**, type quantitative, même magasin |
| D-002.2 | La 3D doit-elle lire les mêmes réglages que la 2D ? | **Oui**, aux exceptions près (voir ci-dessous) |
| D-002.3 | Quelles exceptions 2D/3D sont légitimes ? | Uniquement : **le côté** (la 3D tourne, « gauche » n'a pas de sens) et **la largeur** (px écran vs rayon monde) → deux champs distincts, pas deux magasins |
| D-002.4 | Portée des réglages 3D | **Par projet**, comme la 2D. Le global ne garde que la caméra et le thème |
| D-002.5 | Combien de réglages maximum visibles à la fois ? | **6** par piste, le reste derrière « Avancé » |
| D-002.6 | Une piste absente d'une vue : on la cache ou on l'annonce ? | **On l'annonce** (« non affichable en 3D »), jamais silencieux |
