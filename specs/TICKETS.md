# Tickets de développement — ordre imposé

> Un ticket n'est **pas** une intention. Il contient : ce qui est attendu,
> les fichiers autorisés, les règles `R-xx` concernées, et la preuve qui le clôt.
>
> **Règle zéro.** Le développeur n'ouvre **pas** un ticket qu'il n'a pas compris mot
> pour mot. S'il manque une valeur, il écrit la question dans le ticket et attend.
> Il n'improvise jamais un comportement, un mot ou une valeur par défaut.

Les tickets se font **dans cet ordre**. Aucun démarrage de `T-05` avant que `T-02`
et `T-03` soient clos : c'est ce qui a fait échouer la v2 (3 magasins de réglages).

---

## T-00 · Harnais de vérification — *fait*

**But.** Rendre la spécification exécutable.
**Livré.** `tools/spec_check.py` (62 vérifications), `specs/tests/` (21 tests).
**Preuve.** `python3 tools/spec_check.py` → 0 écart ; `python3 -m unittest
discover -s specs/tests` → OK.
**Règles.** R-01, R-02, R-17.

---

## T-01 · Lexique et interdits

**But.** Aucune décision de mot laissée au développeur.
**Attendu.**
1. `drillmaster_v3/core/lexique.py` charge `specs/data/lexique.json` (déjà fait).
2. Toute chaîne affichée passe par `lexique.type_donnee()`, `.niveau()`,
   `.famille()` ou `.module()`.
3. Un `MotInterdit` levé = l'écran ne s'affiche pas. C'est voulu.

**Fichiers autorisés.** `drillmaster_v3/core/lexique.py`, `specs/data/lexique.json`.
**Interdit.** Écrire une chaîne littérale dans un widget.
**Preuve.** `spec_check` R-17 = 0 mot interdit ; un test ajoutant un mot au lexique
doit faire échouer `spec_check`.
**Règles.** R-01, R-16, R-17, R-18.

---

## T-02 · Contrat de piste — le magasin unique

**But.** 1 objet, 5 lecteurs, 0 copie. C'est la correction de la cause racine.
**Attendu.**
1. `TrackStyle` est le **seul** type de style transmis aux vues.
2. `TrackCatalog.resout(id)` applique l'héritage famille → piste.
3. `TrackCatalog.lit(id, lecteur, champ)` renvoie soit la valeur, soit
   `{applique: False, raison: "..."}`.
4. **Aucun** `QSettings` dans `drillmaster_v3/`.

**Fichiers autorisés.** `drillmaster_v3/core/tracks.py`, `specs/data/tracks.json`.
**Interdit.** Un `dict` de réglages ad hoc, une clé `*_width`, un second magasin.
**Preuve.** `test_R09_les_cinq_lecteurs_lisent_la_meme_valeur`,
`test_R07_heritage_est_explicite`, `spec_check` R-09 → 0 `QSettings` neuf.
**Règles.** R-02 → R-10.

---

## T-03 · Messages et états

**But.** Un message qui se comprend, et qui ne peut pas exister incomplet.
**Attendu.**
1. `Message.__post_init__` refuse un message sans `pourquoi`, `concernes`,
   `resoudre` ou `portee`.
2. Un `blocage` propose **au moins deux** sorties.
3. `rendu("guidee")` et `rendu("experte")` partagent le même vocabulaire de niveau.

**Fichiers autorisés.** `drillmaster_v3/core/messages.py`.
**Interdit.** `QMessageBox`, un message construit à la main dans une vue.
**Preuve.** `specs/tests/test_messages.py` (12 tests) passe.
**Règles.** R-16 → R-23.

---

## T-04 · Écran « Pistes » (Coupe 2D → Pistes)

**But.** Montrer le contrat sans le rendre compliqué.
**Attendu.**
1. Les 12 pistes **groupées en 4 familles**, dans l'ordre de `tracks.json.order`.
2. Colonnes visibles : Visible, Piste, Largeur, Opacité, Côté, État.
3. Une valeur héritée affiche un **rond gris** devant ; une valeur forcée, non.
4. Le détail d'une piste montre : *commune aux 15 réglages* / *propre à sa famille* /
   *où ce réglage s'applique* (les 5 lecteurs, avec la raison du non-usage).

**Maquette de référence.** `maquettes/11_pistes.png` (± 2 px).
**Fichiers autorisés.** `drillmaster_v3/ui/page_pistes.py`.
**Interdit.** Un réglage de piste dans le panneau de la coupe ;
un libellé qui ne vient pas du lexique.
**Preuve.** Revue visuelle contre la maquette + `TrackCatalog` branché (aucune
valeur codée en dur dans l'écran).
**Règles.** R-05 → R-11, R-24, R-27.

---

## T-05 · Coupe 2D — le panneau maigre

**But.** La coupe ne contient plus de réglages de piste.
**Attendu.** Le panneau contient : Coupe active · Inclusion · **3 familles
repliables** · 4 réglages de coupe (Cadre & axes, Topographie, Légende & cartouche,
Coupes enregistrées). Rien d'autre.
**Maquette.** `maquettes/04_coupe_2d.png`.
**Interdit.** Toute liste plate de pistes ; tout doublon de largeur/opacité/côté.
**Preuve.** Comparaison à la maquette + `grep *_width` dans le panneau = 0.
**Règles.** R-09, R-11.

---

## T-06 · Données — 3 rangs

**Attendu.** Trois colonnes (Socle / Observé / Calculé), les 12 types du lexique,
les catégories **dans leur type**, un type absent **affiché absent avec sa raison**.
**Maquette.** `maquettes/13_donnees_rangs.png`.
**Interdit.** Un 13ᵉ type ; une catégorie partagée entre deux types ; un zéro inventé.
**Preuve.** `spec_check` R-12/R-15 ; revue visuelle.
**Règles.** R-12 → R-15.

---

## T-07 · Fiche de blocage

**Attendu.** Ce que j'ai vu (les lignes du fichier) · pourquoi (3 phrases) ·
**3 sorties** avec « ce qui se passe après » · aucune écriture dans le fichier source.
**Maquette.** `maquettes/14_message.png`.
**Interdit.** Une décision automatique ; une fenêtre modale ; modifier le CSV.
**Preuve.** `test_R22_blocage_trois_sorties` + test « fichier source inchangé »
(empreinte avant/après).
**Règles.** R-20 → R-23.

---

## T-08 · Complexité progressive (Guidé / Expert)

**Attendu.**
1. Max **6 réglages visibles** par piste ; le reste derrière **« Avancé »**.
2. Le mode Guidé n'affiche que les réglages `essentiel`.
3. **Changer de mode ne change aucune valeur** — test obligatoire.
4. Aucune fonction réservée au mode Expert.

**Preuve.** Test « basculer 10 fois de mode ne modifie aucune valeur de
`TrackCatalog` » ; revue : 0 réglage caché sans bouton.
**Règles.** R-24 → R-27.

---

## T-09 · Les 17 cas d'usage

**Attendu.** Chaque cas de `maquettes/16_validation.png` devient un test nommé,
avec un projet de référence figé. Un cas rouge = pas de livraison.
**Preuve.** `specs/tests/test_cas_usage.py` → 17 OK.
**Règles.** R-28 → R-31.

---

## Ce qu'un ticket ne peut jamais demander

| Formulation refusée | Pourquoi | À la place |
|---|---|---|
| « améliorer l'ergonomie » | non vérifiable | nommer la règle `R-xx` et la maquette |
| « rendre plus simple » | non mesurable | « max 6 réglages visibles, R-24 » |
| « gérer les cas particuliers » | flou | lister les cas, un par test |
| « utiliser les bonnes couleurs » | subjectif | `lexique.json` + `#2E5BFF` unique |
| « au besoin, ajouter un réglage » | ouvre la porte à l'invention | ouvrir une question, attendre l'arbitrage |
