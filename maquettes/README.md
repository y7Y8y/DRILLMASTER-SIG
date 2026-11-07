# Maquettes

## m3d_vue_et_panneau.py — la vue 3D cible

Dessine ce que doit **être** la 3D, dans le style minimal maîtrisé :

* **Espace principal** : la scène (forages, surface MNT, teneurs, collets, plan de coupe).
* **Panneau droit** : arbre de calques à trois groupes (Forages · Géologie · Analyses),
  cases à cocher et pastilles de couleur — jamais une pile de cases.
* **Bas** : une barre de statut discrète (64 forages · 2 410 segments · 12 ms).

Aucune ressemblance avec l'ancien panneau (QGroupBox empilés) ni avec la version actuelle.

```bash
python3 maquettes/m3d_vue_et_panneau.py
```
