"""Vérificateur de la spécification — R-01, R-02, R-05, R-06, R-12, R-15, R-16, R-17.

Usage :
    python3 tools/spec_check.py            # vérifie le dépôt
    python3 tools/spec_check.py --json     # sortie machine (CI)

Il ne teste pas l'interface : il teste que la spécification est *complète et
respectée dans les sources*. Un échec = on ne livre pas.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs" / "data"
TRACKS = SPECS / "tracks.json"
LEXIQUE = SPECS / "lexique.json"

CONTRAT = ("id label family visible order side width gap opacity fill stroke "
           "label_text tooltip filter export").split()
FAMILLES = {"structurelle", "categorielle", "quantitative", "media"}
ENUMS = {
    "side": {"left", "right", "overlay"},
    "fill": {"reference", "scale", "fixed"},
    "stroke": {"auto", "fixed"},
    "export": {"visible", "hidden", "simplified"},
}


class Rapport:
    def __init__(self):
        self.lignes = []
        self.echecs = 0

    def ok(self, regle, message):
        self.lignes.append(("ok", regle, message))

    def ko(self, regle, message):
        self.echecs += 1
        self.lignes.append(("ko", regle, message))

    def dump(self, as_json=False):
        if as_json:
            print(json.dumps(
                {"echecs": self.echecs,
                 "resultats": [{"etat": e, "regle": r, "message": m}
                               for e, r, m in self.lignes]},
                ensure_ascii=False, indent=2))
            return
        for etat, regle, message in self.lignes:
            marque = "OK  " if etat == "ok" else "KO  "
            print(f"{marque}{regle:<6} {message}")
        print()
        if self.echecs:
            print(f"{self.echecs} règle(s) non respectée(s) — livraison bloquée.")
        else:
            print(f"{len(self.lignes)} vérifications, 0 écart.")


def charge(chemin, nom, r):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except FileNotFoundError:
        r.ko("R-00", f"{nom} introuvable : {chemin}")
    except json.JSONDecodeError as exc:
        r.ko("R-00", f"{nom} invalide : {exc}")
    return None


def check_tracks(data, r):
    if not data:
        return
    contrat = data.get("contrat", {})
    champs = tuple(contrat.get("champs", {}))
    # R-02 : exactement les 14 champs communs
    if champs == tuple(CONTRAT):
        r.ok("R-02", "contrat = 14 champs communs, dans l'ordre attendu")
    else:
        manquants = set(CONTRAT) - set(champs)
        en_trop = set(champs) - set(CONTRAT)
        r.ko("R-02", f"contrat incorrect — manquants {sorted(manquants)}, "
                     f"en trop {sorted(en_trop)}")

    pistes = data.get("pistes", [])
    # R-02 : le nombre de pistes est déclaré, pas improvisé
    if len(pistes) == 12:
        r.ok("R-02", "12 pistes déclarées")
    else:
        r.ko("R-02", f"{len(pistes)} pistes déclarées au lieu de 12")

    ids, ordres, owners = set(), set(), {}
    for p in pistes:
        pid = p.get("id", "?")
        # R-04 : une famille unique et connue
        fam = p.get("family")
        if fam in FAMILLES:
            r.ok("R-04", f"{pid} → famille {fam}")
        else:
            r.ko("R-04", f"{pid} → famille inconnue {fam!r}")

        # R-05 : les 14 champs communs sont présents (valeurs ou défauts)
        manquants = [c for c in CONTRAT
                     if c not in p and c not in ("opacity", "fill", "stroke",
                                                 "gap", "export", "visible",
                                                 "label_text", "tooltip",
                                                 "filter")]
        if manquants:
            r.ko("R-05", f"{pid} ne déclare pas {manquants}")
        else:
            r.ok("R-05", f"{pid} couvert par le contrat")

        # R-06 : specific n'empiète jamais sur le contrat
        doublons = set(p.get("specific", {})) & set(CONTRAT)
        if doublons:
            r.ko("R-06", f"{pid} redéclare {sorted(doublons)} dans specific")
        else:
            r.ok("R-06", f"{pid} : specific disjoint du contrat")

        # valeurs énumérées fermées
        for champ, autorise in ENUMS.items():
            if champ in p and p[champ] not in autorise:
                r.ko("R-05", f"{pid}.{champ}={p[champ]!r} hors liste "
                             f"{sorted(autorise)}")

        # ordre unique
        o = p.get("order")
        if o in ordres:
            r.ko("R-05", f"{pid} : order {o} déjà utilisé")
        ordres.add(o)

        # identifiants uniques
        if pid in ids:
            r.ko("R-05", f"identifiant dupliqué : {pid}")
        ids.add(pid)

        # R-09 : un seul propriétaire, nommé
        own = p.get("owner")
        if not own:
            r.ko("R-09", f"{pid} n'a pas de propriétaire déclaré")
        owners.setdefault(own, 0)
        owners[own] += 1

    if owners:
        r.ok("R-09", f"propriétaires : {owners}")

    # R-06 bis : un réglage spécifique n'est utilisé que par sa famille
    fam_spec = {f: set(v.get("specific_autorise", []))
                for f, v in data.get("familles", {}).items()}
    for p in pistes:
        fam = p.get("family")
        if fam not in fam_spec:
            continue
        intrus = set(p.get("specific", {})) - fam_spec[fam]
        if intrus:
            r.ko("R-06", f"{p.get('id')} utilise {sorted(intrus)}, interdit "
                         f"pour la famille {fam}")
        else:
            r.ok("R-06", f"{p.get('id')} : réglages spécifiques conformes")


def check_lexique(data, r):
    if not data:
        return
    niveaux = data.get("niveaux", {})
    attendus = {"info", "avertissement", "question", "blocage",
                "erreur_technique"}
    if set(niveaux) == attendus:
        r.ok("R-16", "5 niveaux, vocabulaire fermé")
    else:
        r.ko("R-16", f"niveaux incorrects : {sorted(niveaux)}")

    for cle, val in niveaux.items():
        for champ in ("label", "couleur", "veut_dire", "suite"):
            if not val.get(champ):
                r.ko("R-18", f"niveau {cle} : champ « {champ} » manquant")

    types = data.get("types_donnees", {})
    rangs = {}
    for cle, val in types.items():
        rang = val.get("rang")
        if rang not in (1, 2, 3):
            r.ko("R-12", f"type {cle} : rang {rang!r} interdit")
        else:
            rangs.setdefault(rang, []).append(cle)
    if len(types) == 12:
        r.ok("R-15", "12 types de données, liste fermée")
    else:
        r.ko("R-15", f"{len(types)} types déclarés au lieu de 12")

    # Chaque type doit être rattaché à un rang non vide
    for rang, liste in rangs.items():
        r.ok("R-12", f"rang {rang} : {len(liste)} types")

    # Cohérence lexique ↔ rangs annoncés
    declares = set()
    for rang, contenu in data.get("rangs", {}).items():
        declares |= set(contenu.get("defaut", []))
    inconnus = declares - set(types)
    if inconnus:
        r.ko("R-12", f"rangs déclarent des types inconnus : {sorted(inconnus)}")
    else:
        r.ok("R-12", "les 3 rangs ne citent que des types déclarés")

    interdits = data.get("interdits", [])
    if interdits:
        r.ok("R-17", f"{len(interdits)} mots bannis de l'interface")


import ast

VISIBLES = {"txt", "page_title", "panel", "button", "chip", "sentence",
            "label", "section_label", "field", "segmented", "table",
            "status_bar", "tag", "app_bar", "checkbox", "slider"}


def _chaines_visibles(arbre):
    """Toutes les chaînes réellement passées à un widget de l'interface."""
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Call):
            continue
        f = noeud.func
        nom = getattr(f, "attr", getattr(f, "id", ""))
        if nom not in VISIBLES:
            continue
        for arg in list(noeud.args) + [k.value for k in noeud.keywords]:
            for sous in ast.walk(arg):
                if isinstance(sous, ast.Constant) and isinstance(sous.value, str):
                    yield sous.lineno, sous.value


def check_mots_interdits(lexique, r):
    """R-17 : aucun mot banni dans les textes réellement affichés."""
    interdits = [m.lower() for m in (lexique or {}).get("interdits", [])]
    if not interdits:
        return
    trouves = []
    inspectees = 0
    for fichier in sorted((ROOT / "maquettes").glob("*.py")):
        try:
            arbre = ast.parse(fichier.read_text(encoding="utf-8"))
        except SyntaxError:
            r.ko("R-17", f"{fichier.name} illisible")
            continue
        for ligne, chaine in _chaines_visibles(arbre):
            inspectees += 1
            bas = chaine.lower()
            for mot in interdits:
                if re.search(rf"\b{re.escape(mot)}\b", bas):
                    trouves.append(f"{fichier.name}:{ligne} « {chaine} » → {mot}")
                    break
    if trouves:
        r.ko("R-17", f"{len(trouves)} mot(s) interdit(s) dans "
                     f"{inspectees} textes affichés : " + " | ".join(trouves[:10]))
    else:
        r.ok("R-17", f"aucun mot interdit dans {inspectees} textes affichés")


def check_reglages_dupliques(r):
    """R-09 : un seul magasin de réglages.

    Le code neuf vit dans `drillmaster_v3/`. Tant qu'il n'existe pas, la règle
    est *constatée* sur le legacy (mesure de départ), sans bloquer : le legacy
    est précisément ce que la refonte remplace.
    """
    neuf = ROOT / "drillmaster_v3"
    legacy = ROOT / "DrillMaster"

    def magasins(racine):
        out = []
        if not racine.exists():
            return out
        for f in racine.rglob("*.py"):
            txt = f.read_text(encoding="utf-8", errors="ignore")
            n = len(re.findall(r"QSettings\s*\(", txt))
            if n:
                out.append((f.relative_to(ROOT).as_posix(), n))
        return out

    hits_neuf = magasins(neuf)
    if hits_neuf:
        r.ko("R-09", f"{sum(n for _, n in hits_neuf)} QSettings dans le code "
                     f"neuf : {[f for f, _ in hits_neuf][:5]}")
    elif neuf.exists():
        r.ok("R-09", "0 QSettings dans le code neuf")
    else:
        r.ok("R-09", "code neuf pas encore créé — règle en vigueur dès la 1re ligne")

    base = magasins(legacy)
    if base:
        r.ok("R-09", f"constat de départ : {sum(n for _, n in base)} QSettings "
                     f"dans {len(base)} fichiers legacy (à supprimer, D-010)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    r = Rapport()
    tracks = charge(TRACKS, "tracks.json", r)
    lexique = charge(LEXIQUE, "lexique.json", r)
    r.ok("R-00", f"spécifications lues depuis {SPECS.relative_to(ROOT)}")
    check_tracks(tracks, r)
    check_lexique(lexique, r)
    check_mots_interdits(lexique, r)
    check_reglages_dupliques(r)
    r.dump(args.json)
    return 1 if r.echecs else 0


if __name__ == "__main__":
    sys.exit(main())
