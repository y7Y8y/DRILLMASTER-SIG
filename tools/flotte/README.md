# La flotte — comment elle marche

13 départements, 67 agents. Chaque agent est une **fonction qui inspecte le
code et rend des constats chiffrés**. Aucun constat n'est une opinion.

```
python3 tools/flotte/rapport.py           # écrit docs/09_RAPPORT_FLOTTE.md
python3 tools/flotte/rapport.py --resume  # juste les chiffres
```

| Fichier | Départements |
|---|---|
| `agents_da.py` | Couleurs et typographie |
| `agents_ui.py` | Rangement des écrans |
| `agents_fonctionnel.py` | Options et partage |
| `agents_messages.py` | Messages et blocages |
| `agents_qualite.py` | Boutons · Qualité du code |
| `agents_donnees.py` | Données et vues · Cohérence |
| `agents_navigation.py` | Navigation et options cachées |
| `agents_architecture.py` | Architecture du code |
| `agents_metier.py` | Vocabulaire · Vitesse · Installation QGIS |

## Ajouter un agent

```python
from noyau import Constat, agent, departement

D = departement("Mon département", "ce qu'il possède")

@agent(D, "X-01", "Ce que je vérifie", "majeur")
def mon_agent(ctx):
    lieux = ctx.fichiers_de(r"/ui/")
    return [Constat(mesure="12 cas", probleme="…", pourquoi="…",
                    action="…")]
```

Puis l'import dans `rapport.py`. Un constat sans mesure chiffrée sera refusé en
relecture : c'est la règle du département.
