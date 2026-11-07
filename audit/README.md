# Audit automatisé DrillMaster

Chaque "agent" est une fonction qui pose **une** question précise au code et
produit une fiche JSON avec preuves (fichier + ligne).

```bash
python3 tools/audit/agents.py            # tous les agents
python3 tools/audit/agents.py D6.1 D4.1  # une sélection
```

| Dossier | Contenu |
|---|---|
| `tools/audit/base.py` | socle : preuve, score calculé, rapport |
| `tools/audit/agents.py` | les 36 agents (un décorateur `@agent(id, direction, question)`) |
| `audit/reports/*.json` | une fiche par agent : score, métriques, constats |
| `docs/06_RAPPORT_AGENTS.md` | synthèse lisible + liste des faux positifs corrigés |

## Règles

1. **Aucun agent n'écrit dans les sources** : lecture seule.
2. **Un constat sans preuve n'est pas publié.**
3. **Le score est calculé** (pénalités par gravité), jamais déclaré à la main.
4. Un agent qui se trompe est corrigé, et la correction est **documentée** dans
   `docs/06_RAPPORT_AGENTS.md`.

## Ajouter un agent

```python
@agent("D5.5", "Coupe 2D", "Ma nouvelle question ?")
def d5_5(r):
    r.metrics = {"mesure": 42}
    r.findings.append(Finding("moyen", "catégorie", "titre", "fichier:ligne",
                              "détail", "correction proposée"))
```
