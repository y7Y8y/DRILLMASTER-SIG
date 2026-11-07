# 01 — Audit d'apparence : ce qui est réellement cassé

> Chaque constat ci-dessous est **vérifié dans le code**, avec fichier et ligne.
> Ce n'est pas une opinion de design : c'est la cause des symptômes que tu décris.

---

## Constat A — Tu as raison sur « taille doit se répéter et rien ne se répète »

Le panneau de la coupe a **78 réglages plats** dans **un seul dictionnaire** (`default_section_style`, `core/project.py`), construits par **76 widgets** dans **19 méthodes** (`ui/section_dock.py`, 1 336 lignes à elles seules).

Mais ces 78 clés ne suivent **aucun contrat commun**. Matrice réelle des attributs par piste :

| Piste | visible | largeur | opacité | côté | couleur | police | marqueur |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Trajectoire | ✓ | ✓ | — | — | ✓ | — | — |
| Profondeurs | ✓ | — | ✓ | ✓ | — | ✓ | — |
| Lithologie | ✓ | ✓ | ✓ | — | — | — | — |
| Teneurs | ✓ | ✓* | ✓ | ✓ | — | — | — |
| Altérations | ✓ | ✓ | ✓ | ✓ | — | — | — |
| Minéralisations | ✓ | ✓ | ✓ | ✓ | — | — | — |
| Structures | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| Imagerie | ✓ | ✓ | ✓ | ✓ | — | — | — |
| **Intercepts** | ✓* | — | — | — | — | — | — |
| **RQD / Récup. / Densité** | **absent du modèle** | | | | | | |

(\* via une clé au nom différent : `assay_max_width`, `show_intercepts`)

**Traduction :** la largeur existe pour 7 pistes sur 10, l'opacité pour 7, le côté pour 6, la couleur pour 1. Ce n'est pas un choix éditorial — c'est un accident d'historique. Chaque piste a été ajoutée à une date différente avec ses propres clés.

**Et le géotechnique n'est même pas là** : `show_rqd`, `rqd_width`, `show_density`… **0 occurrence** dans `default_section_style`. Les 3 pistes géotechniques rangent leurs réglages **dans un autre magasin** (`ui/section_geotech.py` lignes 326/380/404/512). Un utilisateur ne peut pas deviner que « largeur RQD » ne se règle pas là où se règlent les autres largeurs.

---

## Constat B — La dérive de nommage rend l'ajout d'une piste coûteux

La même notion porte **deux noms différents** selon la piste :

```python
show_alterations   alter_width    alter_opacity    alter_side      # radical court
show_mineralizations mineral_width mineral_opacity mineral_side   # radical court
show_structures    structure_width structure_opacity                # radical long
show_imagery       imagery_width  imagery_side    imagery_opacity   # radical long
```

**Conséquence mesurable :** ajouter une piste aujourd'hui demande de toucher
`core/project.py` (défauts + migration) + `ui/section_dock.py` (`set_display_style`, 78 affectations `_attr`) + un builder de panneau + la légende + l'export + la 3D. **6 endroits pour 1 piste.** C'est exactement ce que tu ressens comme « il faut tout refaire à chaque fois ».

---

## Constat C — 2D et 3D ne partagent aucun réglage (le plus grave)

| | Coupe 2D | Vue 3D |
|---|---|---|
| Où sont sauvés les réglages | `config.json` du projet | `QSettings` **global** |
| Portée | **par projet** | **pour toute la machine** |
| Nombre de réglages | 78 | 10 (`DrillMaster/view3d/*`) |
| Domaines affichables | 9 pistes | **3** (Lithologie, Altération, Teneurs) |
| Largeur d'une bande | réglable | **figée dans le code** : `LANES = {"Lithologie": (0.0, 1.1), "Altération": (-2.6, 0.8)}` |
| Opacité | réglable | **inexistante** |
| Couleur | Référentiel | Référentiel (OK) |
| Côté | réglable | figé (`-2.6`, `+2.6`) |

**Preuves :** `ui/view_3d_v2.py` lignes 31–32 (constantes figées), 348–366 (`QSettings`), `core/scene3d/adapter.py` lignes 179–184 (seulement 3 domaines produits).

**Deux conséquences concrètes :**
1. Tu règles l'opacité de la litho dans la coupe à 60 %. La 3D l'ignore : elle affiche 100 %. Tu changes de projet : la 3D garde les réglages du projet précédent.
2. **6 pistes sur 9 n'existent pas en 3D** (profondeurs, minéralisations, structures, imagerie, intercepts, géotechnique) — **sans aucun message**. L'utilisateur croit que la 3D est incomplète ; c'est vrai.

---

## Constat D — Le modèle de scène 3D ne transporte aucun style

`core/scene3d/model.py` — un intervalle 3D est :

```python
IntervalTable(name, kind, hole_idx, d0, d1, value, categories)
```

Ni largeur, ni opacité, ni côté, ni visibilité, ni ordre. **Le rendu décide seul.** Donc même en branchant les 6 pistes manquantes, elles ne pourraient pas être réglées : le contrat de données n'a pas de place pour ça.

Le même problème existe côté 2D : `SectionCanvas.set_display_style()` recopie **78 paramètres nommés à la main** dans 78 attributs `_privés`. Il n'y a pas de « contrat de piste » des deux côtés. **C'est ça, la racine du problème — pas la mise en page.**

---

## Constat E — Le panneau est plat là où il faudrait une hiérarchie

7 groupes de niveau 0 : *Coupe active · Inclusion des forages · Pistes · Affichage de la coupe · Topographie · Légendes · Historique*.

Mais **seulement 3 sous-groupes de niveau 1** dans tout le panneau. Résultat : « Pistes » contient 8 sous-pages, et « Affichage de la coupe » mélange dans **un seul groupe de 149 lignes** le cadre, les axes, l'échelle, l'orientation, les annotations de forages et la grille avancée.

Le groupe « Pistes » (142 lignes) affiche une liste + une page conditionnelle : **on ne voit qu'une piste à la fois**, sans vue d'ensemble. Pour comparer la largeur de 3 pistes, il faut cliquer 3 fois et mémoriser.

---

## Constat F — Les états ne sont pas traités comme des états

Le code distingue déjà 4 niveaux (`core/family_status.py`) : vide, avertissement, blocage, question. C'est bon. Mais :
- il n'existe **pas** de niveau « erreur technique » distinct de « blocage » ;
- les 4 niveaux sont rendus par des pastilles avec bordures et couleurs mélangées à la navigation (`step2_import.py`, 160 chaînes de statut) ;
- `377 except Exception` dont 10 nus : une **erreur technique peut disparaître en silence** et l'utilisateur voit un état « vide » au lieu d'une erreur.

---

## Constat G — La surface de commandes est énorme et non extensible

- **1 373 chaînes visibles uniques**, dont **802 libellés courts** = autant de commandes potentielles, sur **9 fenêtres**.
- `section_dock.py` seul : 360 libellés, 76 widgets, 11 529 lignes.
- Aucun raccourci clavier centralisé, aucune palette de commandes, aucune notion de « commande » réutilisable. Chaque bouton est construit à la main, une fois.

---

## Verdict

Tes trois phrases se traduisent en trois causes techniques :

| Ce que tu ressens | Cause réelle |
|---|---|
| « les options limites, ce qui est nécessaire n'y est pas » | Le contrat de piste n'existe pas : 10 pistes, 10 jeux de clés différents, 1 piste sans aucun réglage |
| « ça ne se partage pas, trop de redondances » | 2D en `config.json`, 3D en `QSettings` global, géotech dans un 3ᵉ magasin |
| « les sous-options sont mélangées dans les grands » | 7 groupes plats, 3 sous-niveaux, 8 pistes dans une page unique |

**Conclusion : une refonte graphique seule ne corrigera rien. Il faut d'abord un contrat — ensuite l'interface devient simple à dessiner.**
