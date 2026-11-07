# 04 — Système d'états : les 5 niveaux

> **Décision D-003.** Répond au « les réponses, les blocages, on ne comprend pas ».
> Aujourd'hui : 4 niveaux dans le code, rendus de façon ambiguë, et aucune trace des erreurs techniques.

---

## 1. Les 5 niveaux (au lieu de 4)

| Niveau | Signification | Bloque ? | Couleur | Icône | Exemple |
|---|---|:--:|---|---|---|
| **1 · Information** | Une donnée a été reconnue | non | neutre | point | « 1 240 collets lus, 12 colonnes reconnues » |
| **2 · Attention** | Une anomalie mérite un regard | non | ambre | ⚠ | « 3 forages sans déviation : trajectoire verticale supposée » |
| **3 · Question** | Une décision humaine est nécessaire | **oui** (bloquant tant que non répondue) | bleu | ? | « La cellule `LAT;SAP` porte 2 codes : large ou délimité ? » |
| **4 · Blocage métier** | L'opération ne peut pas continuer | **oui** | rouge | ⊘ | « Collet du forage ISBRC005 dupliqué (lignes 45 et 88) » |
| **5 · Erreur technique** | Le logiciel n'a pas pu exécuter | **oui**, + journal | rouge foncé | ! | « Transformation EPSG:4326→32629 impossible » |

**Ce qui change :** le niveau 5 **n'existe pas** dans le code actuel. Une exception avalée (377 endroits) produit un état vide, indistinguishable d'un « aucune donnée ». Le niveau 5 crée l'obligation d'afficher, et renvoie au journal.

---

## 2. Le contrat d'un message (obligatoire, les 5 champs)

Aucun message ne peut exister sans ces 5 champs :

```
┌────────────────────────────────────────────────────────────┐
│ ⚠  ATTENTION · Données / Déviations                        │
│                                                            │
│  3 forages n'ont aucune mesure de déviation.               │
│                                                            │
│  POURQUOI   Sans déviation, la trajectoire est calculée     │
│             verticale. Si le forage est incliné, la         │
│             coupe sera fausse en profondeur.                │
│                                                            │
│  CONCERNÉ   ISBRC003 · ISBRC011 · ISBRC027                  │
│                                                            │
│  RÉSOUDRE   • Ajouter les déviations au fichier survey      │
│             • ou marquer ces forages « verticaux » (assumé) │
│                                                            │
│  [ Voir les 3 forages ]  [ Marquer verticaux ]  [ Ignorer ] │
└────────────────────────────────────────────────────────────┘
```

| Champ | Rôle |
|---|---|
| `niveau` | 1 à 5 |
| `pourquoi` | la conséquence si on ne fait rien — **jamais** une reformulation du titre |
| `concerné` | les identifiants exacts, cliquables (jamais « quelques forages ») |
| `résoudre` | au moins une action concrète, jamais « vérifiez vos données » |
| `portée` | fichier + ligne source, pour retrouver la donnée d'origine |

**Test automatique possible :** un message dont `pourquoi` ou `résoudre` est vide ne compile pas.

---

## 3. Rendu visuel : une seule grammaire

- **Pastille** = l'état d'un domaine dans la navigation (couleur + compte).
- **Ligne de message** = dans la liste de validation (icône + titre + première localisation + compte).
- **Panneau de détail** = le contrat complet ci-dessus, à droite, jamais en popup.
- **Jamais** de `QMessageBox` pour une validation : une popup cache le contexte et interrompt le travail.

Règle : les 4 couleurs sémantiques sont **réservées aux états**. Aucune ne peut servir à une identité (piste, domaine, lithologie). L'accent de marque reste unique et n'exprime jamais un état.

---

## 4. Ce que ça corrige dans l'existant

| Existant | Problème | Correction |
|---|---|---|
| `family_status.py` — 4 niveaux | pas de niveau technique | ajout du niveau 5 |
| `step2_import.py` — 160 chaînes de statut | statuts en texte libre, non structurés | contrat `Message` unique |
| 377 `except Exception` | l'échec devient un état vide | tout `except` non trivial produit un niveau 5 ; un test vérifie que le nombre d'`except` nus reste à 0 |
| Messages de validation regroupés | regroupement par code OK | conservé, mais chaque groupe ouvre le panneau de détail à 5 champs |
